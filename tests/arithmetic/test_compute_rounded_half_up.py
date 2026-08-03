"""`ROUNDED` is the annotated EXCEPTION, never a mode.

File 7 of 14 in `tests/arithmetic/`. Its single subject is the store DIRECTION:
exactly five statements in the whole migrated cycle round half away from zero, every
other store truncates toward zero, and three of those five are IMMEDIATELY FOLLOWED
by an un-`ROUNDED` store. That last fact is the whole argument for a per-call
`rounded=` keyword: a module-level flag, a context-level rounding mode or an
"accounting rounding" helper would round the successor too, and would therefore be
wrong at three of five sites the moment it was right at the other two.

Agent Action Plan section 0.1.1, verbatim, is the sentence this file exists to
honour: "Every other store truncates. GETTING THIS BACKWARDS WOULD CORRUPT
ESSENTIALLY EVERY POSTED FIGURE, so truncation is the default and rounding is the
annotated exception."

THE FIVE LIVE `ROUNDED` SITES, verified by exhaustive census over all twelve
in-scope programs - a grep for `rounded` returns seven hits, of which two are
commented out, leaving exactly five:

    1  [general/gl051.cbl:L791]        compute  vat-amount rounded =
                                        post-amount * ws-vat-rate / 100.
                                      GL VAT from NET, in paragraph `net.`
                                      [general/gl051.cbl:L788].
    2  [general/gl051.cbl:L796]        compute  vat-amount rounded =
                                        post-amount - (post-amount /
                                        ((ws-vat-rate + 100) / 100)).
                                      GL VAT from GROSS, in paragraph `gross.`
                                      [general/gl051.cbl:L793].
    3  [general/gl080.cbl:L328]        divide   scycle by period giving a rounded.
                                      THE ONLY `ROUNDED` DIVIDE. The other four are
                                      COMPUTEs.
    4  [irs/irs030.cbl:L1551]          compute  vat-amount rounded =
                                        post-amount * WS-Vat-Current / 100.
                                      IRS VAT from NET, in `Net section.`
                                      [irs/irs030.cbl:L1544] - the structural mirror
                                      of site 1's paragraph.
    5  [irs/irs030.cbl:L1562-L1563]    compute  vat-amount rounded =
                                        post-amount - (post-amount /
                                        ( (WS-Vat-Current + 100) / 100)).
                                      IRS VAT from GROSS, in `Gross section.`
                                      [irs/irs030.cbl:L1556] - the mirror of site 2.
                                      ONE statement across TWO physical lines.

THE THREE `ROUNDED` -> UN-`ROUNDED` ADJACENCY PAIRS, each asserted in one test with
BOTH members:

    A  [general/gl051.cbl:L796] rounded, then
       [general/gl051.cbl:L797]  subtract vat-amount  from  post-amount.
    B  [general/gl080.cbl:L328] rounded, then
       [general/gl080.cbl:L329]  multiply a  by  period  giving  y.
    C  [irs/irs030.cbl:L1562-L1563] rounded, then
       [irs/irs030.cbl:L1564]    subtract vat-amount from post-amount.

CITATION CORRECTION, recorded rather than silently fixed. The Agent Action Plan body
cites "the net-of-VAT subtraction [irs/irs030.cbl:L1565]". The subtraction is at
L1564; L1565 is a `*>` comment line. Verified verbatim against the frozen file. This
file cites L1564 throughout.

ANOMALY A-19, mentioned so that no reader concludes a variant was lost. Two
SUPERSEDED, COMMENTED-OUT `ROUNDED` computes sit immediately above sites 4 and 5, at
[irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561]. Both spell the rate `vat` where
the live statements spell it `WS-Vat-Current`. They are DEAD CODE in the frozen
source and are therefore NOT implemented and NOT asserted here; they are recorded in
the anomaly register as A-19 and nowhere else.

THE SIX BINDING RULES, as they apply to this file.

    R-1  No COBOL at runtime. This file touches neither COBOL nor a database: it
         imports `acas_posting.cobol` and `acas_posting.dictionary` and nothing else,
         opens no connection, spawns no subprocess, and does not read a `.cbl` or
         `.scb` file even to count its own census - the census below is DECLARED
         DATA, transcribed once by hand from the frozen source and cited line by
         line. It runs on a host with no Docker, no MariaDB and no GnuCOBOL.
    R-2  Zero binary floating point. Every value here is `decimal.Decimal`, `int` or
         `str`. There is no binary float literal anywhere in the module, no
         approximate-comparison helper, no tolerance and no epsilon; every assertion
         is an EXACT equality. The ambient `decimal` context is never read and never
         mutated - the only context this file names is
         `arithmetic.INTERMEDIATE_CONTEXT`, and it is inspected precisely to prove it
         was NOT mutated. Nothing from `numpy` or `pandas` is imported, and neither
         appears in the dependency inventory this migration installs.
    R-3  No new validations, fields or schema changes; no concurrency. `ON SIZE
         ERROR` occurs ZERO times across all twelve in-scope programs, so a store
         that overflows its receiver is SILENT, and this file asserts that silence
         rather than adding a guard. `REMAINDER` likewise occurs zero times, so no
         divide here asks for one. Strictly sequential.
    R-4  Legacy anomalies reproduced, never fixed. Verbatim, Agent Action Plan
         section 0.8.2: "There is no test suite: compiled COBOL execution is the
         behavioral specification, defects included. A DEFECT REPRODUCED IS CORRECT;
         A DEFECT FIXED IS A FAILURE." Verbatim, section 0.7.2 R-4: the anomaly-
         locking tests exist "so that a future well-intentioned correction fails the
         suite rather than passing unnoticed." Every expected value below carries a
         provenance comment naming its COBOL locator, per section 0.7.4 C-3.
    R-5  Full traceability. Every test names the `[path:Lnnn]` of the site it
         asserts, and every `FieldDescriptor` arrives either from a dictionary key or
         from a `<path>:L<n>` locator into the frozen source. `pytest-cov` is
         evidence, never a gate.
    R-6  Compiled behaviour is the tie-breaker. Expected values come from the
         compiled oracle, never from reading the COBOL and reasoning about what it
         ought to produce. Where a value depends on something the oracle has not
         measured, the expectation is recorded as a STRICT xfail against a named
         `Q-` id rather than asserted as fact.

Also binding, Agent Action Plan section 0.8.4: no timing assertion and no
performance measurement appears anywhere in this file.

THE TWO `Q-` IDS THIS FILE CARRIES, and why each is a strict xfail:

    Q-2                        The intermediate-precision question. The `cobol`
                               layer records it as MEASURED against GnuCOBOL 3.2.0
                               [acas_posting/cobol/arithmetic.py:L96]: an expression
                               is evaluated at extended precision and quantized
                               EXACTLY ONCE, at the store. The rejected alternative -
                               quantizing each sub-expression to the receiver's scale,
                               which is what a reduced default intermediate precision
                               would amount to - is asserted under
                               `xfail(strict=True)` so that adopting it later XPASSes
                               and FAILS the suite.
    Q-ROUNDED-OVERFLOW-ORDER   Whether a `ROUNDED` store whose rounded result exceeds
                               the receiver's capacity discards the carry AFTER
                               rounding or BEFORE it. This layer rounds first and then
                               discards, silently. ISO leaves the receiver's content
                               undefined when a size error occurs with no `ON SIZE
                               ERROR` phrase, and there is no such phrase anywhere in
                               the twelve programs, so the boundary is open until the
                               oracle measures it. The alternative order is recorded
                               under `xfail(strict=True)`. This id is registered by
                               this file and belongs in
                               `docs/migration/ambiguity-resolutions.md`; it is
                               deliberately NOT given a number, because the numeric
                               `Q-n` space is owned by the per-program registers and
                               appropriating a free number would create a collision
                               nobody could see.

WHAT THIS FILE DELIBERATELY DOES NOT DUPLICATE. `gl080`'s COMPOSED behaviour - the
`if scycle not = y` round-trip gate at [general/gl080.cbl:L331], the read-before-write
of `a` at [general/gl080.cbl:L324] and the unbounded quarter subscript at
[general/gl080.cbl:L345] - is locked by `test_gl080_cycle_divide_rounded.py`. The
compound VAT formula's own semantics, and the destructive post-condition its
successor imposes on `post-amount`, are locked by `test_irs_vat_from_gross.py` and
`test_irs_vat_from_net.py`. This file asserts ONLY the rounding at each site and the
truncation at each successor, and it implements no VAT helper of its own.

THERE IS NO USER RULES DOCUMENT FOR THIS PROJECT. `review_rules` reports that none
was provided, so no reader should look for an on-disk rules file. The six rules above
live in the Agent Action Plan itself, section 0.7.2, and their exact wording is
retrievable from the requirements via `review_prompt`.
"""

from __future__ import annotations

import decimal
from decimal import Decimal

import pytest

from acas_posting.cobol import arithmetic, field as cobol_field, usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  SECTION 1  -  THE TWO NAMED `Q-` IDS
#
#  Named constants rather than inline strings, so that a `grep` for either id finds
#  every test that bears on it and so that the xfail reasons cannot drift apart.
# ---------------------------------------------------------------------------

#: The intermediate-precision question, MEASURED for the `cobol` layer against
#: GnuCOBOL 3.2.0 [acas_posting/cobol/arithmetic.py:L96]. Evaluate at extended
#: precision, quantize once at the store.
Q_INTERMEDIATE_PRECISION: str = "Q-2"

#: Whether the high-order carry of an overflowing `ROUNDED` store is discarded after
#: rounding (what this layer does) or before it. Open: ISO leaves the receiver
#: undefined on a size error with no `ON SIZE ERROR` phrase, and the twelve in-scope
#: programs contain no such phrase.
Q_ROUNDED_OVERFLOW_ORDER: str = "Q-ROUNDED-OVERFLOW-ORDER"


# ---------------------------------------------------------------------------
#  SECTION 2  -  THE CENSUS, AS DECLARED DATA
#
#  R-1 forbids this tier from touching COBOL, so the census is transcribed by hand
#  from the frozen source ONCE, here, with a locator per row, and asserted as data.
#  Every row was read out of the frozen file and is reproduced verbatim.
# ---------------------------------------------------------------------------

#: One row per live `ROUNDED` site: (locator, COBOL verb, receiving field, the
#: statement verbatim). Transcribed from the frozen source; see the module docstring
#: for the full listing and the paragraph each site sits in.
ROUNDED_SITES: tuple[tuple[str, str, str, str], ...] = (
    (
        "general/gl051.cbl:L791",
        "COMPUTE",
        "vat-amount",
        "compute  vat-amount rounded = post-amount * ws-vat-rate / 100.",
    ),
    (
        "general/gl051.cbl:L796",
        "COMPUTE",
        "vat-amount",
        "compute  vat-amount rounded = post-amount - (post-amount / "
        "((ws-vat-rate + 100) / 100)).",
    ),
    (
        "general/gl080.cbl:L328",
        "DIVIDE",
        "a",
        "divide   scycle by period giving a rounded.",
    ),
    (
        "irs/irs030.cbl:L1551",
        "COMPUTE",
        "vat-amount",
        "compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.",
    ),
    (
        "irs/irs030.cbl:L1562-L1563",
        "COMPUTE",
        "vat-amount",
        "compute  vat-amount rounded = post-amount - (post-amount / "
        "( (WS-Vat-Current + 100) / 100)).",
    ),
)

#: The three adjacency pairs: (pair, ROUNDED locator, successor locator, the
#: successor statement verbatim). The successor carries NO `ROUNDED`, which is the
#: whole point.
ADJACENT_UNROUNDED_SUCCESSORS: tuple[tuple[str, str, str, str], ...] = (
    (
        "A",
        "general/gl051.cbl:L796",
        "general/gl051.cbl:L797",
        "subtract vat-amount  from  post-amount.",
    ),
    (
        "B",
        "general/gl080.cbl:L328",
        "general/gl080.cbl:L329",
        "multiply a  by  period  giving  y.",
    ),
    (
        "C",
        "irs/irs030.cbl:L1562-L1563",
        "irs/irs030.cbl:L1564",
        "subtract vat-amount from post-amount.",
    ),
)

#: Anomaly A-19: the two superseded, commented-out variants. Recorded so a reader
#: sees that they were found and deliberately left unimplemented; they spell the rate
#: `vat` where the live sites spell it `WS-Vat-Current`.
A19_COMMENTED_OUT_VARIANTS: tuple[tuple[str, str], ...] = (
    (
        "irs/irs030.cbl:L1550",
        " *>     compute  vat-amount rounded =  post-amount *  vat  /  100.",
    ),
    (
        "irs/irs030.cbl:L1561",
        " *>    compute  vat-amount rounded = post-amount - (post-amount / "
        "( (vat + 100) / 100)).",
    ),
)


# ---------------------------------------------------------------------------
#  SECTION 3  -  DEFENSIVE KEY RESOLUTION AND DESCRIPTOR CONSTRUCTION
#
#  Two local helpers, both deliberately local to this file rather than shared: the
#  tier contract forbids a helper module, and neither helper carries behaviour that
#  another file could reuse without also inheriting this file's citations.
# ---------------------------------------------------------------------------


def _resolve_dictionary_key(*candidates: str) -> str:
    """Return the first candidate key the generated dictionary actually carries.

    Keys are resolved DEFENSIVELY because the artifact keys a field by the view that
    declares it, and the two views do not always spell a name alike. `Scycle` is the
    live example: it REDEFINES `Cyclea` [copybooks/wssystem.cob:L62-L63], so the
    schema - and therefore the table view - knows only `SYSTEM-REC.CYCLEA`, while the
    copybook view is keyed `System-Record.Scycle`. Trying candidates in order and
    naming the near misses on failure turns a spelling drift into a legible message
    instead of a bare `KeyError` from three frames down.

    Args:
        *candidates: Entry keys to try, most-preferred first. Exact and
            case-sensitive, as `loader.find_entry` requires.

    Returns:
        The first candidate that names an entry.

    Raises:
        loader.DictionaryKeyError: None of the candidates names an entry. The message
            lists what was tried and every key whose final segment matches one of
            them, so the correct spelling is visible without opening the artifact.
    """
    for candidate in candidates:
        if loader.find_entry(candidate) is not None:
            return candidate

    wanted = {candidate.rsplit(".", 1)[-1].upper() for candidate in candidates}
    near = tuple(
        key
        for key in loader.entry_keys()
        if key.rsplit(".", 1)[-1].upper() in wanted
    )
    raise loader.DictionaryKeyError(
        "none of the candidate dictionary keys "
        f"{candidates!r} names an entry in "
        "data_dictionary/acas_posting_dictionary.json. Keys whose final "
        f"segment matches: {near or '(none)'}. Rule R-5 requires every "
        "descriptor to cite its entry, so a field is never described by hand "
        "when the artifact catalogues it."
    )


def _catalogued(*candidates: str) -> cobol_field.FieldDescriptor:
    """Build the descriptor for a catalogued field, resolving its key defensively.

    Args:
        *candidates: Entry keys to try, most-preferred first.

    Returns:
        The descriptor the generated dictionary holds for the first key that resolves.
    """
    return cobol_field.FieldDescriptor.from_dictionary_key(
        _resolve_dictionary_key(*candidates)
    )


def _working_storage(
    *,
    name: str,
    source_locator: str,
    usage: model.Usage,
    picture: str,
    digits: int,
    scale: int,
    signed: bool = False,
    unsigned: bool = False,
    sign_position: model.SignPosition = model.SignPosition.NONE,
    is_edited: bool = False,
) -> cobol_field.FieldDescriptor:
    """Describe a PROGRAM-LOCAL item the generated dictionary does not catalogue.

    The dictionary catalogues the copybook record layouts, the bridge-derived columns
    and the work-file records the General Ledger programs declare in their own FILE
    SECTIONs. It does NOT catalogue a program's WORKING-STORAGE, so the four
    `77`-level and print-line items this file needs - `a` and `y`
    [general/gl080.cbl:L182-L183], `acc-ok` [general/gl051.cbl:L233], `l6-account`
    [general/gl072.cbl:L233] - arrive here instead, each carrying the locator of its
    own declaration so rule R-5 still holds.

    `FieldDescriptor.for_working_storage` was REMOVED from
    `acas_posting/cobol/field.py`, which now publishes `from_dictionary_key` as its
    only factory, so the descriptor is constructed directly. `__post_init__` admits a
    key-less descriptor on exactly two conditions, both met here: it carries a
    `<path>:L<n>` locator, and its `python_storage` is the carrier its own usage and
    scale imply - which is why the carrier is DERIVED from
    `usage.python_storage_for` rather than passed in.

    Args:
        name: The COBOL item name, verbatim from the frozen declaration.
        source_locator: `<path>:L<n>` pointing at that declaration.
        usage: The storage class in force.
        picture: The PICTURE clause exactly as written.
        digits: Total digit count, integer digits plus scale.
        scale: Digit count after the implied decimal point.
        signed: Whether the declaration carries a sign.
        unsigned: Whether it carries the explicit UNSIGNED keyword.
        sign_position: Where the sign lives, when there is one.
        is_edited: Whether the picture is numeric-edited, as `pic 9999.99` is.

    Returns:
        The descriptor for that declaration.
    """
    return cobol_field.FieldDescriptor(
        name=name,
        usage=usage,
        usage_declared_at=model.UsageDeclaredAt.FIELD
        if usage is not model.Usage.DISPLAY
        else model.UsageDeclaredAt.DEFAULT,
        picture=picture,
        signed=signed,
        sign_position=sign_position,
        digits=digits,
        integer_digits=digits - scale,
        scale=scale,
        unsigned=unsigned,
        is_edited=is_edited,
        python_storage=cobol_usage.python_storage_for(usage, scale),
        source_locator=source_locator,
    )


# ---------------------------------------------------------------------------
#  SECTION 4  -  THE RECEIVING AND OPERAND FIELDS OF THE FIVE SITES
#
#  Built once at import, which is where the arithmetic tier's ONLY file-system
#  prerequisite - data_dictionary/acas_posting_dictionary.json - is read. Nothing
#  below opens a socket, spawns a process or reads a `.cbl`.
# ---------------------------------------------------------------------------

#: Sites 1 and 2 receive here. `pic s9(8)v99`, zoned DISPLAY, signed with the sign
#: overpunched on the trailing digit [copybooks/wspost.cob:L28].
GL_VAT_AMOUNT: cobol_field.FieldDescriptor = _catalogued(
    "GLPOSTING-REC.VAT-AMOUNT", "WS-Posting-Record.Vat-Amount"
)

#: Pair A's successor [general/gl051.cbl:L797] receives here, and site 2's expression
#: reads it. `pic s9(8)v99` [copybooks/wspost.cob:L23].
GL_POST_AMOUNT: cobol_field.FieldDescriptor = _catalogued(
    "GLPOSTING-REC.POST-AMOUNT", "WS-Posting-Record.Post-Amount"
)

#: Sites 4 and 5 receive here. `pic s9(7)v99 sign is leading` - two digits narrower
#: than the GL field and with the sign on the LEADING digit
#: [copybooks/irswspost.cob:L18].
IRS_VAT_AMOUNT: cobol_field.FieldDescriptor = _catalogued(
    "IRSPOSTING-REC.VAT-AMOUNT4", "Posting-Record.Vat-Amount"
)

#: Pair C's successor [irs/irs030.cbl:L1564] receives here
#: [copybooks/irswspost.cob:L14].
IRS_POST_AMOUNT: cobol_field.FieldDescriptor = _catalogued(
    "IRSPOSTING-REC.POST4-AMOUNT", "Posting-Record.Post-Amount"
)

#: The rate sites 1 and 2 read. `pic 99v99` with COMP inherited from the group header
#: `05 Vat-Rates comp.` [copybooks/wssystem.cob:L55-L60]; `gl051` moves it into its
#: own local copy at [general/gl051.cbl:L522].
SYSTEM_VAT_RATE: cobol_field.FieldDescriptor = _catalogued(
    "SYSTEM-REC.VAT-RATE-1", "System-Record.Vat-Rate-1"
)

#: Site 3's dividend. SIGNED `binary-char` [copybooks/wssystem.cob:L63], which
#: REDEFINES `Cyclea` [copybooks/wssystem.cob:L62] - hence the two candidate keys.
SCYCLE: cobol_field.FieldDescriptor = _catalogued(
    "System-Record.Scycle", "SYSTEM-REC.SCYCLE", "SYSTEM-REC.CYCLEA"
)

#: Site 3's divisor, and pair B's successor's multiplicand. SIGNED `binary-char`
#: [copybooks/wssystem.cob:L64].
PERIOD: cobol_field.FieldDescriptor = _catalogued(
    "SYSTEM-REC.PERIOD", "System-Record.Period"
)

#: Site 3's receiver: `77  a  pic 99  value zero.` [general/gl080.cbl:L183]. TWO
#: digits, UNSIGNED, zoned DISPLAY - a different storage class from either operand.
WS_A: cobol_field.FieldDescriptor = _working_storage(
    name="a",
    source_locator="general/gl080.cbl:L183",
    usage=model.Usage.DISPLAY,
    picture="99",
    digits=2,
    scale=0,
)

#: Pair B's successor's receiver: `77  y  pic 99  value zero.`
#: [general/gl080.cbl:L182].
WS_Y: cobol_field.FieldDescriptor = _working_storage(
    name="y",
    source_locator="general/gl080.cbl:L182",
    usage=model.Usage.DISPLAY,
    picture="99",
    digits=2,
    scale=0,
)

#: `gl051`'s own copy of the rate: `03  ws-vat-rate  pic 99v99  comp  value zero.`
#: [general/gl051.cbl:L183]. Same picture and same usage as the system field it is
#: loaded from, which is why sites 1 and 2 can read either without a conversion.
WS_VAT_RATE_GL051: cobol_field.FieldDescriptor = _working_storage(
    name="ws-vat-rate",
    source_locator="general/gl051.cbl:L183",
    usage=model.Usage.COMP,
    picture="99v99",
    digits=4,
    scale=2,
)

#: The rate sites 4 and 5 read: `03  WS-Vat-Current  pic 99v99  value zero.`
#: [irs/irs030.cbl:L277]. NO usage clause, so zoned DISPLAY by language default -
#: unlike `gl051`'s COMP copy of the same picture.
WS_VAT_CURRENT_IRS030: cobol_field.FieldDescriptor = _working_storage(
    name="WS-Vat-Current",
    source_locator="irs/irs030.cbl:L277",
    usage=model.Usage.DISPLAY,
    picture="99v99",
    digits=4,
    scale=2,
)


# ---------------------------------------------------------------------------
#  SECTION 5  -  THE RECEIVING FIELDS OF THE REPRESENTATIVE UN-`ROUNDED` SITES
#
#  The negative form of the census. These five statements carry NO `ROUNDED`, so
#  every one of them truncates - which is `store`'s default and therefore needs no
#  keyword at the call site at all.
# ---------------------------------------------------------------------------

#: `add post-amount to actual-gross.` [general/gl051.cbl:L1063] receives here.
#: `pic 9(9)v99` with COMP-3 inherited from `03 Amounts comp-3.`
#: [copybooks/wsbatch.cob:L40-L43] - and UNSIGNED, so a negative posting loses its
#: sign on the way in.
BATCH_ACTUAL_GROSS: cobol_field.FieldDescriptor = _catalogued(
    "GLBATCH-REC.ACTUAL-GROSS", "WS-Batch-Record.Actual-Gross"
)

#: `add vat-amount to actual-vat.` [general/gl051.cbl:L1064] receives here
#: [copybooks/wsbatch.cob:L44].
BATCH_ACTUAL_VAT: cobol_field.FieldDescriptor = _catalogued(
    "GLBATCH-REC.ACTUAL-VAT", "WS-Batch-Record.Actual-Vat"
)

#: The minuend of `subtract input-vat from input-gross giving l9-amount.`
#: [general/gl051.cbl:L1105] [copybooks/wsbatch.cob:L41].
BATCH_INPUT_GROSS: cobol_field.FieldDescriptor = _catalogued(
    "GLBATCH-REC.INPUT-GROSS", "WS-Batch-Record.Input-Gross"
)

#: The subtrahend of that same statement [copybooks/wsbatch.cob:L42].
BATCH_INPUT_VAT: cobol_field.FieldDescriptor = _catalogued(
    "GLBATCH-REC.INPUT-VAT", "WS-Batch-Record.Input-Vat"
)

#: `divide post-dr by 100 giving acc-ok` [general/gl051.cbl:L604] receives here:
#: `03  acc-ok  pic 9(4)v99.` [general/gl051.cbl:L233], a REDEFINES of the
#: four-digit-plus-two-digit account work area at [general/gl051.cbl:L229-L231].
WS_ACC_OK: cobol_field.FieldDescriptor = _working_storage(
    name="acc-ok",
    source_locator="general/gl051.cbl:L233",
    usage=model.Usage.DISPLAY,
    picture="9(4)v99",
    digits=6,
    scale=2,
)

#: `divide WS-Ledger-Nos by 100 giving l6-account.` [general/gl072.cbl:L413] receives
#: here: `03  l6-account  pic 9999.99  blank when zero.` [general/gl072.cbl:L233] - a
#: numeric-EDITED print item, whose underlying numeric shape is six digits at scale
#: two.
WS_L6_ACCOUNT: cobol_field.FieldDescriptor = _working_storage(
    name="l6-account",
    source_locator="general/gl072.cbl:L233",
    usage=model.Usage.DISPLAY,
    picture="9999.99",
    digits=6,
    scale=2,
    is_edited=True,
)

#: `subtract input-vat from input-gross giving l9-amount.`
#: [general/gl051.cbl:L1105] receives here: `03  l9-amount  pic z(9)9.99bb.`
#: [general/gl051.cbl:L331] - ten integer digits, two decimals, edited.
WS_L9_AMOUNT: cobol_field.FieldDescriptor = _working_storage(
    name="l9-amount",
    source_locator="general/gl051.cbl:L331",
    usage=model.Usage.DISPLAY,
    picture="z(9)9.99bb",
    digits=12,
    scale=2,
    is_edited=True,
)


# ---------------------------------------------------------------------------
#  SECTION 6  -  MEASURED OPERANDS
#
#  One named constant per probe, so that a failing assertion names the scenario and
#  so that the SAME operands are reused by the census, the adjacency and the
#  quantize-once tests instead of being retyped.
# ---------------------------------------------------------------------------

#: Sites 1 and 4 - VAT FROM NET. 12.34 at 17.50% gives 2.1595 exactly, whose third
#: decimal is 9: the ROUNDED store keeps 2.16 where an un-ROUNDED one would keep
#: 2.15, so the two directions are VISIBLY different on this pair.
NET_POST_AMOUNT: Decimal = Decimal("12.34")
NET_VAT_RATE: Decimal = Decimal("17.50")

#: Sites 2 and 5 - VAT FROM GROSS. 117.55 is a VAT-inclusive gross at the same
#: 17.50% rate; the exact VAT is 17.5074468085106382978723404255319148936170212766
#: recurring, so ROUNDED keeps 17.51 and un-ROUNDED keeps 17.50.
GROSS_POST_AMOUNT: Decimal = Decimal("117.55")
GROSS_VAT_RATE: Decimal = Decimal("17.50")

#: Site 3 - the cycle divide. 5 over 3 is 1.666 recurring: ROUNDED gives 2 and
#: un-ROUNDED gives 1, and the successor multiply then gives 6 or 3 respectively, so
#: BOTH members of pair B are visibly mode-sensitive on this pair.
CYCLE_SCYCLE: int = 5
CYCLE_PERIOD: int = 3

#: THE NET-SIDE PROBE, and the arithmetic reason it is needed.
#:
#: At pairs A and C the successor subtracts the VAT from the gross, so its result is
#: the NET. The exact VAT and the exact net sum to the gross, which is a scale-two
#: quantity, so their third-and-later decimals are COMPLEMENTS: if the VAT's tail
#: exceeds a half penny then the net's tail cannot, and vice versa. It is therefore
#: ARITHMETICALLY IMPOSSIBLE for one `(post, rate)` pair to make the ROUNDED store at
#: the site AND the un-ROUNDED store at its successor visibly mode-sensitive at the
#: same time - not a matter of choosing better numbers.
#:
#: 10.01 at 25.00% is the complement of the pair above: the exact VAT is 2.002, whose
#: tail is below a half penny, and the exact net is 8.008, whose tail is above it. The
#: successor's store direction is therefore visible here - truncating keeps 8.00 where
#: rounding would keep 8.01 - which is what the adjacency tests use it for.
NET_SIDE_PROBE_POST_AMOUNT: Decimal = Decimal("10.01")
NET_SIDE_PROBE_VAT_RATE: Decimal = Decimal("25.00")


def _vat_from_gross(post_amount: Decimal, vat_rate: Decimal):
    """Return the site 2 / site 5 expression as a callable, unevaluated.

    A callable rather than a value, because that is how `arithmetic.compute` and
    `arithmetic.intermediate` guarantee the operators run inside
    `INTERMEDIATE_CONTEXT` and are quantized exactly ONCE, at the store.

    This is NOT a VAT helper. It builds the expression `post-amount - (post-amount /
    ((rate + 100) / 100))` exactly as [general/gl051.cbl:L796] and
    [irs/irs030.cbl:L1562-L1563] write it, and it is used here only to exercise the
    store DIRECTION. The formula's own semantics, and the destructive post-condition
    its successor imposes on `post-amount`, belong to
    `test_irs_vat_from_gross.py`.

    Args:
        post_amount: The VAT-inclusive gross.
        vat_rate: The rate, as a percentage.

    Returns:
        A zero-argument callable holding the expression.
    """
    return lambda: post_amount - (post_amount / ((vat_rate + 100) / 100))


def _vat_from_net(post_amount: Decimal, vat_rate: Decimal):
    """Return the site 1 / site 4 expression as a callable, unevaluated.

    As above: the expression `post-amount * rate / 100` exactly as
    [general/gl051.cbl:L791] and [irs/irs030.cbl:L1551] write it, used only to
    exercise the store direction. `test_irs_vat_from_net.py` owns the formula.

    Args:
        post_amount: The VAT-exclusive net.
        vat_rate: The rate, as a percentage.

    Returns:
        A zero-argument callable holding the expression.
    """
    return lambda: post_amount * vat_rate / 100


# ---------------------------------------------------------------------------
#  SECTION 7  -  THE CENSUS
#
#  Five live sites, no more and no fewer. If a sixth `ROUNDED` is ever introduced -
#  or one of these five is quietly turned into an un-ROUNDED store - the census
#  assertions here are what notices.
# ---------------------------------------------------------------------------


def test_exactly_five_live_rounded_sites_exist() -> None:
    """The whole in-scope cycle carries FIVE `ROUNDED` stores and no more.

    Census method, recorded because R-5 asks for traceability of a claim as much as of
    a field: a case-insensitive search for `rounded` across all twelve in-scope
    programs - `gl051`, `gl070`, `gl071`, `gl072`, `gl080`, `sl055`, `sl060`, `sl100`,
    `pl055`, `pl060`, `pl100` and `irs030` - returns SEVEN lines. Two of them,
    [irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561], are commented out with `*>`
    and are anomaly A-19. Five remain, and they are the five below.
    """
    assert len(ROUNDED_SITES) == 5

    # Each locator is a real `<path>:L<n>` into the frozen tree. The pattern is the
    # dictionary's own, imported rather than retyped so the two cannot drift.
    for locator, _verb, _receiver, _statement in ROUNDED_SITES:
        assert loader.SOURCE_LOCATOR_PATTERN.match(locator), locator

    # No site is cited twice, which is how a copy-paste in the table would show up.
    assert len({locator for locator, _v, _r, _s in ROUNDED_SITES}) == 5

    # Every statement in the census actually writes ROUNDED. The commented-out A-19
    # variants write it too, which is exactly why they are held in a separate tuple.
    for locator, _verb, _receiver, statement in ROUNDED_SITES:
        assert "rounded" in statement, locator
        assert not statement.lstrip().startswith("*>"), locator


def test_only_one_rounded_site_is_a_divide() -> None:
    """[general/gl080.cbl:L328] is the sole `ROUNDED` DIVIDE; the other four COMPUTE.

    The distinction is load-bearing rather than trivia. A `DIVIDE ... GIVING` reaches
    the store through `arithmetic.divide_by_giving`, which has an exact-integer path
    for an un-ROUNDED divide into an integer receiver; the four COMPUTEs reach it
    through `arithmetic.compute`, which evaluates a caller-supplied expression. The
    two paths must agree on what `rounded=True` means, and they do because both funnel
    into the single `arithmetic.store`.
    """
    divides = tuple(
        locator for locator, verb, _r, _s in ROUNDED_SITES if verb == "DIVIDE"
    )
    computes = tuple(
        locator for locator, verb, _r, _s in ROUNDED_SITES if verb == "COMPUTE"
    )

    assert divides == ("general/gl080.cbl:L328",)
    assert computes == (
        "general/gl051.cbl:L791",
        "general/gl051.cbl:L796",
        "irs/irs030.cbl:L1551",
        "irs/irs030.cbl:L1562-L1563",
    )
    assert len(divides) + len(computes) == len(ROUNDED_SITES)


def test_the_gl_and_irs_vat_computes_mirror_one_another() -> None:
    """Four of the five sites are TWO VAT pairs, one per ledger, and they mirror.

    [general/gl051.cbl:L791] and [general/gl051.cbl:L796] sit in the paragraphs `net.`
    [general/gl051.cbl:L788] and `gross.` [general/gl051.cbl:L793];
    [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562-L1563] sit in `Net section.`
    [irs/irs030.cbl:L1544] and `Gross section.` [irs/irs030.cbl:L1556]. Same two
    formulae, same order, different receivers and different rate fields - which is why
    this file describes all four receivers separately instead of assuming one shape.
    """
    gl_vat_sites = tuple(
        locator
        for locator, _v, receiver, _s in ROUNDED_SITES
        if receiver == "vat-amount" and locator.startswith("general/gl051.cbl")
    )
    irs_vat_sites = tuple(
        locator
        for locator, _v, receiver, _s in ROUNDED_SITES
        if receiver == "vat-amount" and locator.startswith("irs/irs030.cbl")
    )

    assert gl_vat_sites == ("general/gl051.cbl:L791", "general/gl051.cbl:L796")
    assert irs_vat_sites == ("irs/irs030.cbl:L1551", "irs/irs030.cbl:L1562-L1563")

    # The receivers are NOT interchangeable: ten digits against nine, and a trailing
    # overpunched sign against a leading one [copybooks/wspost.cob:L28] versus
    # [copybooks/irswspost.cob:L18].
    assert GL_VAT_AMOUNT.digits == 10
    assert IRS_VAT_AMOUNT.digits == 9
    assert GL_VAT_AMOUNT.sign_position is model.SignPosition.TRAILING_INCLUDED
    assert IRS_VAT_AMOUNT.sign_position is model.SignPosition.LEADING_INCLUDED

    # Nor are the rate fields: `gl051` holds its copy as COMP
    # [general/gl051.cbl:L183], `irs030` holds its as zoned DISPLAY by language
    # default [irs/irs030.cbl:L277], from the same `pic 99v99`.
    assert WS_VAT_RATE_GL051.picture == WS_VAT_CURRENT_IRS030.picture
    assert WS_VAT_RATE_GL051.usage is model.Usage.COMP
    assert WS_VAT_CURRENT_IRS030.usage is model.Usage.DISPLAY


def test_a19_commented_out_variants_are_recorded_and_not_implemented() -> None:
    """Anomaly A-19: two superseded `ROUNDED` computes are DEAD and stay dead.

    [irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561] each sit one line above a live
    site and each spells the rate `vat` rather than `WS-Vat-Current`. They are
    commented out in the frozen source, so they have NO behaviour to reproduce: R-4
    requires reproducing what the compiled program DOES, and a comment does nothing.
    They are recorded here so that a reader comparing the COBOL against the Python
    does not conclude a variant was lost, and they appear in no other assertion.
    """
    assert len(A19_COMMENTED_OUT_VARIANTS) == 2

    for locator, statement in A19_COMMENTED_OUT_VARIANTS:
        assert loader.SOURCE_LOCATOR_PATTERN.match(locator), locator
        # Commented out with `*>`, hence dead.
        assert statement.lstrip().startswith("*>"), locator
        # The superseded rate spelling, which is what identifies them.
        assert " vat " in statement or "(vat " in statement, locator
        # And they are NOT part of the live census.
        assert locator not in {loc for loc, _v, _r, _s in ROUNDED_SITES}

    # They sit immediately above sites 4 and 5 respectively - the adjacency that makes
    # them easy to mistake for the live statements when skim-reading the file.
    assert A19_COMMENTED_OUT_VARIANTS[0][0] == "irs/irs030.cbl:L1550"
    assert A19_COMMENTED_OUT_VARIANTS[1][0] == "irs/irs030.cbl:L1561"


def test_three_of_the_five_sites_have_an_unrounded_successor() -> None:
    """THREE of five `ROUNDED` stores are immediately followed by a truncating store.

    This is the census fact that decides the API shape. Sites 1 and 4 stand alone;
    sites 2, 3 and 5 are each followed on the very next statement by a store with no
    `ROUNDED` on it. A rounding mode held anywhere other than the individual call -
    a module constant, a `decimal` context, a "money rounding" helper - would round
    those three successors too, and would be wrong three times over.
    """
    assert len(ADJACENT_UNROUNDED_SUCCESSORS) == 3

    rounded_locators = {locator for locator, _v, _r, _s in ROUNDED_SITES}
    for pair, rounded_locator, successor, statement in ADJACENT_UNROUNDED_SUCCESSORS:
        assert rounded_locator in rounded_locators, pair
        assert loader.SOURCE_LOCATOR_PATTERN.match(successor), pair
        # The successor statement carries NO `ROUNDED`. That is the entire point.
        assert "rounded" not in statement.lower(), pair

    paired = {locator for _p, locator, _s, _st in ADJACENT_UNROUNDED_SUCCESSORS}
    # Sites 1 and 4 - the two "VAT from net" computes - have no successor store.
    assert rounded_locators - paired == {
        "general/gl051.cbl:L791",
        "irs/irs030.cbl:L1551",
    }


# ---------------------------------------------------------------------------
#  SECTION 8  -  THE THREE ADJACENCY PAIRS
#
#  One test per pair, BOTH members asserted in the same function, because the point
#  is the TRANSITION from a rounded store to a truncating one across two consecutive
#  statements. Splitting a pair across two tests would lose exactly the property
#  being proved.
# ---------------------------------------------------------------------------


def test_pair_a_gl051_rounded_gross_then_unrounded_subtract() -> None:
    """PAIR A: [general/gl051.cbl:L796] rounds, [general/gl051.cbl:L797] truncates.

    The two statements, verbatim and consecutive:

        compute  vat-amount rounded = post-amount - (post-amount /
                                       ((ws-vat-rate + 100) / 100)).
        subtract vat-amount  from  post-amount.

    MEMBER 1, the ROUNDED store. 117.55 at 17.50% is a VAT-inclusive gross; the exact
    VAT is 17.50744680851063829787234042553... so ROUNDED keeps 17.51. Truncating
    instead would keep 17.50 - a penny out, on every gross-entered posting.

    MEMBER 2, the un-ROUNDED store. The subtraction reads what member 1 STORED, not
    what it computed, so its operands are both at scale two and the difference is
    exact: 117.55 - 17.51 = 100.04. The wrong direction at member 1 is nonetheless
    visible right here, because it changes member 2's stored value to 100.05.

    MEMBER 2's OWN DIRECTION is then probed on the complementary pair, for the
    arithmetic reason recorded on `NET_SIDE_PROBE_POST_AMOUNT`: the VAT's tail and the
    net's tail are complements, so only one of the two members can be tail-sensitive
    at any one `(post, rate)`.
    """
    post_amount = GROSS_POST_AMOUNT
    vat_rate = GROSS_VAT_RATE

    # --- member 1: [general/gl051.cbl:L796], ROUNDED -----------------------
    vat_rounded = arithmetic.compute(
        _vat_from_gross(post_amount, vat_rate), GL_VAT_AMOUNT, rounded=True
    )
    # Measured: exact 17.5074468085106382978723404255319148936170212766...,
    # ROUND_HALF_UP into `pic s9(8)v99` [copybooks/wspost.cob:L28].
    assert vat_rounded == Decimal("17.51")

    # The counterfactual, asserted rather than described: dropping the ROUNDED keyword
    # here costs a penny. R-4 - this is the correction that must fail the suite.
    vat_if_truncated = arithmetic.compute(
        _vat_from_gross(post_amount, vat_rate), GL_VAT_AMOUNT
    )
    assert vat_if_truncated == Decimal("17.50")
    assert vat_rounded != vat_if_truncated

    # --- member 2: [general/gl051.cbl:L797], NO `ROUNDED` -----------------
    # `subtract a from b` is b = b - a, so the receiver is an operand: `post-amount`
    # is both `receiver_value` and the destination.
    net_amount = arithmetic.subtract_from(
        vat_rounded, receiver_value=post_amount, receiving=GL_POST_AMOUNT
    )
    # Measured: 117.55 - 17.51 = 100.04 exactly.
    assert net_amount == Decimal("100.04")

    # And with member 1 wrongly truncated the successor lands a penny away, which is
    # how a single missing ROUNDED propagates into the posted figure.
    net_if_member_1_truncated = arithmetic.subtract_from(
        vat_if_truncated, receiver_value=post_amount, receiving=GL_POST_AMOUNT
    )
    assert net_if_member_1_truncated == Decimal("100.05")
    assert net_amount != net_if_member_1_truncated

    # --- member 2's own store direction, on the complementary pair --------
    # 10.01 at 25.00%: the exact VAT is 2.002 (tail below a half penny) and the exact
    # net is 8.008 (tail above it). Handing the successor the UNQUANTIZED VAT - which
    # is what an implementation that skipped member 1's store would do - makes the
    # successor's own direction visible.
    probe_post = NET_SIDE_PROBE_POST_AMOUNT
    probe_rate = NET_SIDE_PROBE_VAT_RATE
    unquantized_vat = arithmetic.intermediate(
        _vat_from_gross(probe_post, probe_rate)
    )
    assert unquantized_vat == Decimal("2.002")

    truncated_net = arithmetic.subtract_from(
        unquantized_vat, receiver_value=probe_post, receiving=GL_POST_AMOUNT
    )
    rounded_net = arithmetic.subtract_from(
        unquantized_vat,
        receiver_value=probe_post,
        receiving=GL_POST_AMOUNT,
        rounded=True,
    )
    # Measured: 10.01 - 2.002 = 8.008; truncating keeps 8.00, rounding would keep
    # 8.01. [general/gl051.cbl:L797] writes no ROUNDED, so 8.00 is the reproduction.
    assert truncated_net == Decimal("8.00")
    assert rounded_net == Decimal("8.01")
    assert truncated_net != rounded_net


def test_pair_b_gl080_rounded_cycle_divide_then_unrounded_multiply() -> None:
    """PAIR B: [general/gl080.cbl:L328] rounds, [general/gl080.cbl:L329] truncates.

    The two statements, verbatim and consecutive:

        divide   scycle by period giving a rounded.
        multiply a  by  period  giving  y.

    This is the pair where BOTH members are visibly mode-sensitive, because both
    receivers are two-digit integers and the quotient recurs. With `scycle` 5 over
    `period` 3:

        member 1 ROUNDED   -> a = 2      (truncating would give a = 1)
        member 2 truncated -> y = 2 * 3 = 6   (from a = 1 it would be y = 3)

    And if an implementation skipped member 1's store altogether and carried the
    unquantized 1.666... forward, member 2 would receive 4.99999...98 and store 4
    truncating, or 5 rounding - three different answers from one pair of statements,
    which is the whole case for quantizing at the store and only there.

    NOT DUPLICATED HERE: the `if scycle not = y` round-trip gate at
    [general/gl080.cbl:L331] and everything it controls - the read-before-write of `a`
    at [general/gl080.cbl:L324], the `add 1 to scycle` at [general/gl080.cbl:L334] and
    the unbounded quarter subscript at [general/gl080.cbl:L345] - are locked by
    `test_gl080_cycle_divide_rounded.py`. This test asserts only the rounding at L328
    and the truncation at L329.
    """
    # --- member 1: [general/gl080.cbl:L328], ROUNDED ----------------------
    # `divide scycle by period giving a` is a = scycle / period, so the operands are
    # written in the same order the statement writes them.
    a_rounded = arithmetic.divide_by_giving(
        CYCLE_SCYCLE, CYCLE_PERIOD, WS_A, rounded=True
    )
    # Measured: 5 / 3 = 1.666..., ROUND_HALF_UP into `77 a pic 99`
    # [general/gl080.cbl:L183] gives 2.
    assert a_rounded == 2
    # An integer receiver hands back an `int`, never a Decimal at scale zero - the
    # carrier `pic 99` implies.
    assert isinstance(a_rounded, int)

    a_if_truncated = arithmetic.divide_by_giving(CYCLE_SCYCLE, CYCLE_PERIOD, WS_A)
    # Measured: truncation toward zero gives 1. R-4 - dropping ROUNDED here changes
    # which quarter column the end-of-period processing writes.
    assert a_if_truncated == 1
    assert a_rounded != a_if_truncated

    # --- member 2: [general/gl080.cbl:L329], NO `ROUNDED` ----------------
    y_value = arithmetic.multiply_by_giving(a_rounded, CYCLE_PERIOD, WS_Y)
    # Measured: 2 * 3 = 6 exactly, into `77 y pic 99` [general/gl080.cbl:L182].
    assert y_value == 6
    assert isinstance(y_value, int)

    y_if_member_1_truncated = arithmetic.multiply_by_giving(
        a_if_truncated, CYCLE_PERIOD, WS_Y
    )
    # Measured: 1 * 3 = 3. The wrong direction at member 1 halves member 2.
    assert y_if_member_1_truncated == 3
    assert y_value != y_if_member_1_truncated

    # --- member 2's own store direction ----------------------------------
    # The "skipped the store" wiring: 5/3 evaluated at INTERMEDIATE_CONTEXT precision
    # and carried forward unquantized.
    unquantized_quotient = arithmetic.intermediate(
        lambda: Decimal(CYCLE_SCYCLE) / Decimal(CYCLE_PERIOD)
    )
    # Sixty significant digits of 6, TRUNCATED - never 1.666...7, because
    # INTERMEDIATE_CONTEXT rounds DOWN. Written out rather than approximated, since
    # R-2 leaves no room for "close enough".
    assert unquantized_quotient == Decimal(
        "1." + "6" * (arithmetic.INTERMEDIATE_PRECISION - 1)
    )

    y_from_unquantized_truncated = arithmetic.multiply_by_giving(
        unquantized_quotient, CYCLE_PERIOD, WS_Y
    )
    y_from_unquantized_rounded = arithmetic.multiply_by_giving(
        unquantized_quotient, CYCLE_PERIOD, WS_Y, rounded=True
    )
    # Measured: 1.666...6 * 3 = 4.999...98, so truncating keeps 4 and rounding keeps
    # 5. [general/gl080.cbl:L329] writes no ROUNDED, so the truncating answer is the
    # one this layer must produce for that operand.
    assert y_from_unquantized_truncated == 4
    assert y_from_unquantized_rounded == 5
    assert y_from_unquantized_truncated != y_from_unquantized_rounded

    # Neither wrong wiring reaches the right answer, and one of them would flip the
    # gate at [general/gl080.cbl:L331] from "not equal" to "equal" - which is why that
    # gate has a test of its own rather than being asserted here.
    assert y_from_unquantized_rounded == CYCLE_SCYCLE
    assert y_value != CYCLE_SCYCLE


def test_pair_c_irs030_rounded_gross_then_unrounded_subtract() -> None:
    """PAIR C: [irs/irs030.cbl:L1562-L1563] rounds, [irs/irs030.cbl:L1564] truncates.

    The three physical lines, verbatim and consecutive:

        compute  vat-amount rounded =
                 post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
        subtract vat-amount from post-amount.

    Note the shape: ONE statement spanning TWO physical lines, then the successor.
    Nothing about the line break changes the arithmetic, and this test asserts the
    statement, not the lines.

    CITATION: the successor is at L1564. The Agent Action Plan body cites L1565; that
    line is a `*>` comment. Verified verbatim against the frozen file.

    The receivers are the IRS internal posting record's, NOT the GL posting record's:
    `pic s9(7)v99 sign is leading` [copybooks/irswspost.cob:L14] and
    [copybooks/irswspost.cob:L18] - nine digits with a LEADING sign, against the GL's
    ten with a trailing one. The rounding direction is the same; the field is not.
    """
    post_amount = GROSS_POST_AMOUNT
    vat_rate = GROSS_VAT_RATE

    # --- member 1: [irs/irs030.cbl:L1562-L1563], ROUNDED ------------------
    vat_rounded = arithmetic.compute(
        _vat_from_gross(post_amount, vat_rate), IRS_VAT_AMOUNT, rounded=True
    )
    # Measured: the same exact 17.50744680851..., ROUND_HALF_UP into
    # `pic s9(7)v99 sign is leading` [copybooks/irswspost.cob:L18].
    assert vat_rounded == Decimal("17.51")

    vat_if_truncated = arithmetic.compute(
        _vat_from_gross(post_amount, vat_rate), IRS_VAT_AMOUNT
    )
    assert vat_if_truncated == Decimal("17.50")
    assert vat_rounded != vat_if_truncated

    # --- member 2: [irs/irs030.cbl:L1564], NO `ROUNDED` ------------------
    net_amount = arithmetic.subtract_from(
        vat_rounded, receiver_value=post_amount, receiving=IRS_POST_AMOUNT
    )
    # Measured: 117.55 - 17.51 = 100.04 exactly.
    assert net_amount == Decimal("100.04")

    net_if_member_1_truncated = arithmetic.subtract_from(
        vat_if_truncated, receiver_value=post_amount, receiving=IRS_POST_AMOUNT
    )
    assert net_if_member_1_truncated == Decimal("100.05")
    assert net_amount != net_if_member_1_truncated

    # --- member 2's own store direction, on the complementary pair --------
    unquantized_vat = arithmetic.intermediate(
        _vat_from_gross(NET_SIDE_PROBE_POST_AMOUNT, NET_SIDE_PROBE_VAT_RATE)
    )
    truncated_net = arithmetic.subtract_from(
        unquantized_vat,
        receiver_value=NET_SIDE_PROBE_POST_AMOUNT,
        receiving=IRS_POST_AMOUNT,
    )
    rounded_net = arithmetic.subtract_from(
        unquantized_vat,
        receiver_value=NET_SIDE_PROBE_POST_AMOUNT,
        receiving=IRS_POST_AMOUNT,
        rounded=True,
    )
    # Measured: 10.01 - 2.002 = 8.008 -> 8.00 truncating, 8.01 rounding.
    assert truncated_net == Decimal("8.00")
    assert rounded_net == Decimal("8.01")
    assert truncated_net != rounded_net

    # The successor is DESTRUCTIVE - it overwrites `post-amount` with the net, so the
    # gross is gone by the time the posting record is written. That consequence, and
    # what it does to the row, belong to `test_irs_vat_from_gross.py`; here it is
    # enough that the value stored is the truncating one.
    assert net_amount != post_amount


# ---------------------------------------------------------------------------
#  SECTION 9  -  ROUNDING IS PER-CALL, NEVER A MODE
#
#  The three tests above prove that three of five sites need the two directions on
#  consecutive statements. These prove that the implementation can actually deliver
#  that: a rounded call leaves nothing behind.
# ---------------------------------------------------------------------------


def test_a_rounded_store_leaves_no_residual_state() -> None:
    """Pair A's two stores, in sequence: the second truncates after the first rounded.

    The scenario is [general/gl051.cbl:L796] followed by [general/gl051.cbl:L797],
    executed in that order in one process, and then the SAME pair of calls repeated -
    because a mode held in module or context state would show up either as the second
    call inheriting the first's direction, or as the third call behaving unlike the
    first.

    The probe value is the one place both directions are visible on ONE field, so the
    same `store` call can be made twice with opposite keywords and compared: the
    unquantized VAT 17.50744680851..., which truncates to 17.50 and rounds to 17.51.
    """
    unquantized_vat = arithmetic.intermediate(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE)
    )

    # Statement 1, ROUNDED. Statement 2, un-ROUNDED, on the same field, immediately
    # after. Statement 3, ROUNDED again.
    first_rounded = arithmetic.store(unquantized_vat, GL_VAT_AMOUNT, rounded=True)
    then_truncated = arithmetic.store(unquantized_vat, GL_VAT_AMOUNT)
    rounded_again = arithmetic.store(unquantized_vat, GL_VAT_AMOUNT, rounded=True)

    # Measured: 17.51, 17.50, 17.51. The middle call is NOT dragged up by the one
    # before it, and the third is NOT dragged down by the one before it.
    assert first_rounded == Decimal("17.51")
    assert then_truncated == Decimal("17.50")
    assert rounded_again == Decimal("17.51")
    assert first_rounded == rounded_again
    assert then_truncated != first_rounded

    # The same sequence again, to rule out a first-call-only initialisation.
    assert arithmetic.store(unquantized_vat, GL_VAT_AMOUNT) == Decimal("17.50")
    assert arithmetic.store(
        unquantized_vat, GL_VAT_AMOUNT, rounded=True
    ) == Decimal("17.51")


def test_a_rounded_call_does_not_mutate_the_intermediate_context() -> None:
    """`INTERMEDIATE_CONTEXT` is unchanged by a rounded call - it is not the mode.

    `arithmetic.INTERMEDIATE_CONTEXT` carries `rounding=ROUND_DOWN`, because it
    governs the EVALUATION of an expression and COBOL's evaluation does not round -
    the direction is applied once, at the store, from the call's own keyword. If a
    rounded call reached in and set the context's rounding instead, every later
    evaluation in the process would inherit it.

    R-2 also forbids touching the ambient `decimal` context, so nothing here reads or
    writes `decimal.getcontext()`; the module's own named context is inspected
    directly.

    All three entry points into the rounding path are exercised, one per verb form the
    census uses: a bare store, a COMPUTE as at [general/gl051.cbl:L796], and a DIVIDE
    as at [general/gl080.cbl:L328]. The context is declared at
    [acas_posting/cobol/arithmetic.py:L102].
    """
    rounding_before = arithmetic.INTERMEDIATE_CONTEXT.rounding
    precision_before = arithmetic.INTERMEDIATE_CONTEXT.prec
    flags_before = dict(arithmetic.INTERMEDIATE_CONTEXT.flags)

    # A rounded store, then a rounded COMPUTE - both directions of entry into the
    # rounding path.
    arithmetic.store(Decimal("1.995"), GL_VAT_AMOUNT, rounded=True)
    arithmetic.compute(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE),
        GL_VAT_AMOUNT,
        rounded=True,
    )
    arithmetic.divide_by_giving(CYCLE_SCYCLE, CYCLE_PERIOD, WS_A, rounded=True)

    assert arithmetic.INTERMEDIATE_CONTEXT.rounding == rounding_before
    assert arithmetic.INTERMEDIATE_CONTEXT.prec == precision_before
    assert dict(arithmetic.INTERMEDIATE_CONTEXT.flags) == flags_before

    # And the context's own rounding is the TRUNCATING one, not the rounded one: the
    # evaluation context must never round, whatever the store does.
    assert arithmetic.INTERMEDIATE_CONTEXT.rounding == decimal.ROUND_DOWN
    assert arithmetic.INTERMEDIATE_CONTEXT.rounding != decimal.ROUND_HALF_UP


def test_the_rounding_vocabulary_has_exactly_two_members() -> None:
    """Two store directions, no third, and the mapping is stated in one place.

    COBOL has exactly two: with `ROUNDED` and without. `ROUNDING_DIRECTIONS`
    [acas_posting/cobol/arithmetic.py:L78] is that vocabulary as immutable data rather
    than as a branch, which is what lets this test assert the correspondence between
    the COBOL keyword and the `decimal` mode directly instead of inferring it from
    behaviour.

    Five statements in the cycle select the second member - [general/gl051.cbl:L791],
    [general/gl051.cbl:L796], [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and
    [irs/irs030.cbl:L1562-L1563] - and every other store in the cycle selects the
    first, so a THIRD member would have no statement to serve.
    """
    assert len(arithmetic.ROUNDING_DIRECTIONS) == 2
    assert set(arithmetic.ROUNDING_DIRECTIONS) == {False, True}

    # Without `ROUNDED`: truncate toward zero. With it: round half away from zero.
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP

    # The two named constants agree with the mapping, so neither can drift.
    assert cobol_field.TRUNCATING_STORE == arithmetic.ROUNDING_DIRECTIONS[False]
    assert arithmetic.ROUNDED_STORE == arithmetic.ROUNDING_DIRECTIONS[True]

    # NOT banker's rounding. `ROUND_HALF_EVEN` is `decimal`'s own default and is what
    # a reader might assume; it is not what COBOL `ROUNDED` means.
    assert arithmetic.ROUNDED_STORE != decimal.ROUND_HALF_EVEN

    # The vocabulary is immutable, so a caller cannot redefine what `rounded=True`
    # means process-wide - which is the same property, expressed as a type.
    with pytest.raises(TypeError):
        # type: ignore[index] - assigning into the proxy is the point of the test.
        arithmetic.ROUNDING_DIRECTIONS[True] = decimal.ROUND_HALF_EVEN  # type: ignore


def test_truncation_is_the_default_of_the_rounded_parameter() -> None:
    """Omitting `rounded=` truncates, at every verb this file's sites use.

    The default is what makes the census safe. Five statements in twelve programs
    write `ROUNDED`; every other store in the cycle is written WITHOUT the keyword and
    is therefore transcribed without it, so the default has to be the truncating
    direction or the migration is wrong nearly everywhere.

    One verb per site shape: `compute` for [general/gl051.cbl:L796],
    `divide_by_giving` for [general/gl080.cbl:L328], `subtract_from` for the successor
    at [general/gl051.cbl:L797] and `multiply_by_giving` for the successor at
    [general/gl080.cbl:L329] - so every call form the census needs is covered.
    """
    probe = arithmetic.intermediate(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE)
    )

    # `store`, the single funnel every verb ends in.
    assert arithmetic.store(probe, GL_VAT_AMOUNT) == arithmetic.store(
        probe, GL_VAT_AMOUNT, rounded=False
    )
    assert arithmetic.store(probe, GL_VAT_AMOUNT) != arithmetic.store(
        probe, GL_VAT_AMOUNT, rounded=True
    )

    # `compute`, which sites 1, 2, 4 and 5 reach.
    expression = _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE)
    assert arithmetic.compute(expression, GL_VAT_AMOUNT) == Decimal("17.50")

    # `divide_by_giving`, which site 3 reaches.
    assert arithmetic.divide_by_giving(CYCLE_SCYCLE, CYCLE_PERIOD, WS_A) == 1

    # `subtract_from` and `multiply_by_giving`, the two successors.
    assert arithmetic.subtract_from(
        probe, receiver_value=GROSS_POST_AMOUNT, receiving=GL_POST_AMOUNT
    ) == Decimal("100.04")
    assert arithmetic.multiply_by_giving(2, CYCLE_PERIOD, WS_Y) == 6


# ---------------------------------------------------------------------------
#  SECTION 10  -  THE ROUNDING-MODE TRUTH TABLE
#
#  Both directions, both signs, and the three interesting neighbourhoods of a half
#  penny: just below, exactly at, just above. Every expected value was measured.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "truncated", "rounded"),
    (
        # Exactly at the half penny: truncation drops it, ROUNDED carries it AWAY FROM
        # ZERO. Receiver `pic s9(8)v99` [copybooks/wspost.cob:L28].
        (Decimal("1.995"), Decimal("1.99"), Decimal("2.00")),
        # The same magnitude, negative: the carry goes further from zero, to -2.00,
        # NOT toward it. This row is why `ROUND_DOWN` and not `ROUND_FLOOR` is the
        # truncating mode, and why `ROUND_HALF_UP` and not `ROUND_HALF_EVEN` or
        # `ROUND_CEILING` is the rounded one.
        (Decimal("-1.995"), Decimal("-1.99"), Decimal("-2.00")),
        # Just below the half penny: BOTH directions agree. A test that used only
        # values like this one would pass with the modes swapped.
        (Decimal("1.994"), Decimal("1.99"), Decimal("1.99")),
        # Just above: both carry, but only one of them was going to anyway.
        (Decimal("1.996"), Decimal("1.99"), Decimal("2.00")),
        (Decimal("-1.996"), Decimal("-1.99"), Decimal("-2.00")),
        # Zero is fixed under both directions, and keeps the receiver's scale.
        (Decimal("0.005"), Decimal("0.00"), Decimal("0.01")),
        (Decimal("0.004"), Decimal("0.00"), Decimal("0.00")),
    ),
)
def test_truth_table_on_a_scaled_money_receiver(
    value: Decimal, truncated: Decimal, rounded: Decimal
) -> None:
    """The two directions on `Vat-Amount pic s9(8)v99`, at and around a half penny.

    The receiver is the one sites 1 and 2 write [copybooks/wspost.cob:L28], reached
    through its dictionary key so that its digits, scale, signedness and sign position
    are the artifact's and not this file's opinion (R-5).
    """
    assert arithmetic.store(value, GL_VAT_AMOUNT) == truncated
    assert arithmetic.store(value, GL_VAT_AMOUNT, rounded=True) == rounded

    # The stored value carries the receiver's own scale, so `Decimal("2.00")` and not
    # `Decimal("2")`: a table dump renders the scale, and a scale difference is a diff.
    assert arithmetic.store(value, GL_VAT_AMOUNT).as_tuple().exponent == -2
    assert (
        arithmetic.store(value, GL_VAT_AMOUNT, rounded=True).as_tuple().exponent == -2
    )


@pytest.mark.parametrize(
    ("value", "truncated", "rounded"),
    (
        # Site 3's receiver, `77 a pic 99` [general/gl080.cbl:L183]: an INTEGER, so
        # the half falls at .5 rather than at .005.
        (Decimal("2.50"), 2, 3),
        (Decimal("2.49"), 2, 2),
        (Decimal("2.51"), 2, 3),
        (Decimal("0.50"), 0, 1),
        # An exact integer is fixed under both.
        (Decimal("4"), 4, 4),
    ),
)
def test_truth_table_on_the_two_digit_integer_receiver(
    value: Decimal, truncated: int, rounded: int
) -> None:
    """The two directions on `a pic 99`, the receiver of the only `ROUNDED` DIVIDE.

    `2.50 -> 3` is [general/gl080.cbl:L328] itself: the quotient of two `binary-char`
    items landing in a two-digit unsigned display field, where a half period rounds up
    into the next quarter column.
    """
    assert arithmetic.store(value, WS_A) == truncated
    assert arithmetic.store(value, WS_A, rounded=True) == rounded

    # An integer receiver hands back `int`, not a zero-scale Decimal.
    assert isinstance(arithmetic.store(value, WS_A), int)
    assert isinstance(arithmetic.store(value, WS_A, rounded=True), int)


def test_rounded_is_ties_away_from_zero_not_bankers_rounding() -> None:
    """`ROUNDED` breaks a tie AWAY FROM ZERO. Banker's rounding would break it to even.

    The distinguishing pair is 2.5 and 3.5 into an integer receiver:

        COBOL ROUNDED / ROUND_HALF_UP   ->  3  and  4
        banker's      / ROUND_HALF_EVEN ->  2  and  4
        Python's built-in `round`       ->  2  and  4

    They agree on 3.5, so a test that probed only 3.5 would pass under either rule.
    2.5 is the row that decides it, and it is asserted first for that reason.

    The integer receiver is site 3's own, `77 a pic 99` [general/gl080.cbl:L183], and
    the scaled receiver is sites 1 and 2's, `pic s9(8)v99`
    [copybooks/wspost.cob:L28] - so the rule is asserted on the real fields the
    `ROUNDED` sites write and not on a contrivance.
    """
    # 2.5 - the deciding row. Banker's rounding would give 2.
    assert arithmetic.store(Decimal("2.5"), WS_A, rounded=True) == 3
    # 3.5 - where the two rules agree, asserted so the pair is complete.
    assert arithmetic.store(Decimal("3.5"), WS_A, rounded=True) == 4

    # Stated against the two `decimal` modes directly, so the claim does not rest on
    # the two examples alone.
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDED_STORE != decimal.ROUND_HALF_EVEN

    # And on a scaled money field, at the half penny: 0.125 -> 0.13, where banker's
    # rounding would give 0.12 because 2 is even.
    assert arithmetic.store(Decimal("0.125"), GL_VAT_AMOUNT, rounded=True) == Decimal(
        "0.13"
    )
    assert arithmetic.store(Decimal("0.135"), GL_VAT_AMOUNT, rounded=True) == Decimal(
        "0.14"
    )


def test_truth_table_on_a_signed_integer_receiver() -> None:
    """A negative tie rounds AWAY from zero: -2.50 stores as -3, never -2.

    SUBSTITUTION, recorded rather than made silently. The Agent Action Plan's truth
    table names `pic s9(4)` for this row. NO SIGNED ZERO-SCALE NUMERIC FIELD EXISTS
    ANYWHERE IN THE IN-SCOPE SOURCES - verified against the generated dictionary,
    whose 1000-plus entries contain not one signed item with scale zero and a digit
    count. Rather than invent a `pic s9(4)` declaration that no frozen file carries,
    which R-5 would have nothing to trace and section 0.7.1 forbids, this row is
    asserted on the real signed integer that site 3 itself reads: `Scycle`, declared
    `binary-char` and therefore SIGNED at [copybooks/wssystem.cob:L63].

    The store shape is the same one the substituted picture would have had - a signed
    receiver at scale zero - so the property under test is unchanged.
    """
    assert SCYCLE.signed is True
    assert SCYCLE.scale in (0, None)

    # Measured on the signed `binary-char` receiver.
    assert arithmetic.store(Decimal("-2.50"), SCYCLE) == -2
    assert arithmetic.store(Decimal("-2.50"), SCYCLE, rounded=True) == -3
    assert arithmetic.store(Decimal("-3.50"), SCYCLE) == -3
    assert arithmetic.store(Decimal("-3.50"), SCYCLE, rounded=True) == -4

    # Symmetric on the positive side, which is what "away from zero" means.
    assert arithmetic.store(Decimal("2.50"), SCYCLE) == 2
    assert arithmetic.store(Decimal("2.50"), SCYCLE, rounded=True) == 3

    # Truncation is toward ZERO on both signs, so -2.9 truncates to -2 and not to the
    # floor -3. Python's `//` would give -3, which is why the truncating mode is
    # `ROUND_DOWN` and not a floor division.
    assert arithmetic.store(Decimal("-2.9"), SCYCLE) == -2
    assert arithmetic.store(Decimal("2.9"), SCYCLE) == 2


# ---------------------------------------------------------------------------
#  SECTION 11  -  THE RECEIVING FIELDS OF THE FIVE SITES
#
#  The direction is only half of a store; the receiving field's digits, scale, sign
#  and storage class are the other half. Five sites, four distinct receivers, and at
#  site 3 a statement whose operands and receiver are declared in different storage
#  classes altogether.
# ---------------------------------------------------------------------------


def test_sites_1_and_2_receive_into_the_gl_posting_vat_field() -> None:
    """Sites 1 and 2 store into `Vat-Amount pic s9(8)v99` [copybooks/wspost.cob:L28].

    Ten digits, two of them after the point, signed with the sign OVERPUNCHED on the
    trailing digit because the declaration carries no SIGN clause - the COBOL default.
    Zoned DISPLAY, ten bytes on the wire, carried in Python by `Decimal`.
    """
    assert GL_VAT_AMOUNT.dictionary_key == "GLPOSTING-REC.VAT-AMOUNT"
    assert GL_VAT_AMOUNT.source_locator == "copybooks/wspost.cob:L28"
    assert GL_VAT_AMOUNT.picture == "s9(8)v99"
    assert GL_VAT_AMOUNT.usage is model.Usage.DISPLAY
    assert GL_VAT_AMOUNT.digits == 10
    assert GL_VAT_AMOUNT.integer_digits == 8
    assert GL_VAT_AMOUNT.scale == 2
    assert GL_VAT_AMOUNT.signed is True
    assert GL_VAT_AMOUNT.sign_position is model.SignPosition.TRAILING_INCLUDED
    assert GL_VAT_AMOUNT.sign_clause_text is None
    assert GL_VAT_AMOUNT.byte_length == 10
    assert GL_VAT_AMOUNT.is_zoned_display is True
    assert GL_VAT_AMOUNT.is_decimal is True
    assert GL_VAT_AMOUNT.quantum == Decimal("0.01")

    # The provenance R-5 asks for, as one line naming all three views.
    assert GL_VAT_AMOUNT.cite().startswith("GLPOSTING-REC.VAT-AMOUNT")
    assert "copybooks/wspost.cob:L28" in GL_VAT_AMOUNT.cite()


def test_pair_a_successor_receives_into_the_gl_posting_amount_field() -> None:
    """[general/gl051.cbl:L797] stores into `Post-Amount` [copybooks/wspost.cob:L23].

    Site 2 READS this field and its successor OVERWRITES it, which is why the two must
    be described separately even though the shapes match: the value that leaves the
    pair is a net where the value that entered it was a gross.
    """
    assert GL_POST_AMOUNT.dictionary_key == "GLPOSTING-REC.POST-AMOUNT"
    assert GL_POST_AMOUNT.source_locator == "copybooks/wspost.cob:L23"
    assert GL_POST_AMOUNT.picture == "s9(8)v99"
    assert GL_POST_AMOUNT.digits == 10
    assert GL_POST_AMOUNT.scale == 2
    assert GL_POST_AMOUNT.signed is True
    assert GL_POST_AMOUNT.sign_position is model.SignPosition.TRAILING_INCLUDED

    # Same shape as the VAT field it is paired with, which is what makes the
    # subtraction at L797 exact rather than truncating - see the adjacency test.
    assert GL_POST_AMOUNT.digits == GL_VAT_AMOUNT.digits
    assert GL_POST_AMOUNT.scale == GL_VAT_AMOUNT.scale
    assert GL_POST_AMOUNT.usage is GL_VAT_AMOUNT.usage


def test_sites_4_and_5_receive_into_the_irs_posting_vat_field() -> None:
    """Sites 4 and 5 store into `Vat-Amount pic s9(7)v99 sign is leading`.

    [copybooks/irswspost.cob:L18]. NINE digits where the GL field has ten, and the
    sign on the LEADING digit because the declaration says `sign is leading` - the
    spelling itself is preserved rather than normalised, because
    [copybooks/wspost-irs.cob:L21] writes the same clause as `sign leading` and the two
    stay distinguishable.
    """
    assert IRS_VAT_AMOUNT.dictionary_key == "IRSPOSTING-REC.VAT-AMOUNT4"
    assert IRS_VAT_AMOUNT.source_locator == "copybooks/irswspost.cob:L18"
    assert IRS_VAT_AMOUNT.picture == "s9(7)v99"
    assert IRS_VAT_AMOUNT.usage is model.Usage.DISPLAY
    assert IRS_VAT_AMOUNT.digits == 9
    assert IRS_VAT_AMOUNT.integer_digits == 7
    assert IRS_VAT_AMOUNT.scale == 2
    assert IRS_VAT_AMOUNT.signed is True
    assert IRS_VAT_AMOUNT.sign_position is model.SignPosition.LEADING_INCLUDED
    assert IRS_VAT_AMOUNT.is_decimal is True

    # The SIGN clause is carried verbatim, and it is one of the two live spellings.
    assert IRS_VAT_AMOUNT.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS

    # One digit narrower than the GL receiver at the integer end, which is a real
    # capacity difference and not a formatting one.
    assert IRS_VAT_AMOUNT.max_value < GL_VAT_AMOUNT.max_value


def test_pair_c_successor_receives_into_the_irs_posting_amount_field() -> None:
    """[irs/irs030.cbl:L1564] stores into `Post-Amount` [copybooks/irswspost.cob:L14].

    Also `sign is leading`, and also overwritten by its own successor - the destructive
    subtract. Cited at L1564; L1565 is a comment.
    """
    assert IRS_POST_AMOUNT.dictionary_key == "IRSPOSTING-REC.POST4-AMOUNT"
    assert IRS_POST_AMOUNT.source_locator == "copybooks/irswspost.cob:L14"
    assert IRS_POST_AMOUNT.picture == "s9(7)v99"
    assert IRS_POST_AMOUNT.digits == 9
    assert IRS_POST_AMOUNT.scale == 2
    assert IRS_POST_AMOUNT.signed is True
    assert IRS_POST_AMOUNT.sign_position is model.SignPosition.LEADING_INCLUDED
    assert IRS_POST_AMOUNT.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS

    # The IRS pair and the GL pair are NOT the same fields, which is the reason pairs
    # A and C are separate tests rather than one parametrised one.
    assert IRS_POST_AMOUNT.digits != GL_POST_AMOUNT.digits
    assert IRS_POST_AMOUNT.sign_position is not GL_POST_AMOUNT.sign_position


def test_the_vat_rate_operands_of_the_four_vat_sites() -> None:
    """The rate the four VAT computes read is `pic 99v99`, and its USAGE is INHERITED.

    `05 Vat-Rates comp.` [copybooks/wssystem.cob:L55] declares COMP on the GROUP, and
    the five `07 Vat-Rate-n pic 99v99` items beneath it
    [copybooks/wssystem.cob:L56-L60] inherit it - they carry no usage clause of their
    own. That inheritance is the highest-risk fact a data dictionary records, because
    reading only the field's own line would say DISPLAY and change both the stored
    bytes and the arithmetic; asserting `usage_declared_at` here is what keeps the
    reading honest.

    Two decimals on the rate matter to the census directly: 17.50 is not 17.5 and not
    18, so both VAT formulae carry a hundredth of a percent into the product before the
    ROUNDED store ever sees it.
    """
    assert SYSTEM_VAT_RATE.picture == "99v99"
    assert SYSTEM_VAT_RATE.usage is model.Usage.COMP
    assert SYSTEM_VAT_RATE.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert SYSTEM_VAT_RATE.usage_inherited_from == "Vat-Rates"
    assert SYSTEM_VAT_RATE.digits == 4
    assert SYSTEM_VAT_RATE.scale == 2
    assert SYSTEM_VAT_RATE.signed is False
    assert SYSTEM_VAT_RATE.value_domain == (0, 9999)
    assert SYSTEM_VAT_RATE.quantum == Decimal("0.01")
    assert SYSTEM_VAT_RATE.source_locator == "copybooks/wssystem.cob:L56"

    # `gl051` holds the value it reads in a local COMP copy of the same picture
    # [general/gl051.cbl:L183], loaded at [general/gl051.cbl:L522]; `irs030` holds its
    # own in a zoned DISPLAY item of the same picture [irs/irs030.cbl:L277], loaded at
    # [irs/irs030.cbl:L721]. Same digits, same scale, DIFFERENT storage - so the two
    # rate fields are described separately rather than shared.
    assert WS_VAT_RATE_GL051.digits == SYSTEM_VAT_RATE.digits
    assert WS_VAT_RATE_GL051.scale == SYSTEM_VAT_RATE.scale
    assert WS_VAT_RATE_GL051.usage is SYSTEM_VAT_RATE.usage
    assert WS_VAT_CURRENT_IRS030.digits == SYSTEM_VAT_RATE.digits
    assert WS_VAT_CURRENT_IRS030.usage is not SYSTEM_VAT_RATE.usage
    assert WS_VAT_CURRENT_IRS030.byte_length != WS_VAT_RATE_GL051.byte_length

    # The rate reaches the same stored penny through either field, which is why the
    # site 1 and site 4 tests can share one expected value.
    assert arithmetic.store(GROSS_VAT_RATE, WS_VAT_RATE_GL051) == arithmetic.store(
        GROSS_VAT_RATE, WS_VAT_CURRENT_IRS030
    )
    assert arithmetic.store(GROSS_VAT_RATE, SYSTEM_VAT_RATE) == Decimal("17.50")


def test_site_3_mixes_storage_classes_in_one_statement() -> None:
    """[general/gl080.cbl:L328] divides SIGNED BINARY items into an UNSIGNED ZONED one.

    All four items of the pair, described:

        scycle  binary-char, SIGNED, domain -128..127, 1 byte, carried as `int`
                [copybooks/wssystem.cob:L63]
        period  binary-char, SIGNED, domain -128..127, 1 byte, carried as `int`
                [copybooks/wssystem.cob:L64]
        a       pic 99, UNSIGNED zoned DISPLAY, domain 0..99, 2 bytes, `int`
                [general/gl080.cbl:L183]
        y       pic 99, UNSIGNED zoned DISPLAY, domain 0..99, 2 bytes, `int`
                [general/gl080.cbl:L182]

    Two declared storage classes and two distinct value domains across four items, and
    a third distinction on top of them - signedness - which is the one that bites: a
    negative quotient CANNOT be represented in the receiver at all, so the sign is
    dropped rather than stored. The Agent Action Plan counts that signed/unsigned
    split as a class of its own, which is where its "three storage classes" comes
    from; this test asserts the concrete differences rather than the count.

    `Scycle` REDEFINES `Cyclea` [copybooks/wssystem.cob:L62], so the schema knows the
    column only as `CYCLEA` and the copybook view is what carries the name the
    statement writes - which is why its key is resolved defensively.
    """
    # The two operands: one byte each, signed, sign implicit in the representation.
    for operand in (SCYCLE, PERIOD):
        assert operand.usage is model.Usage.BINARY_CHAR
        assert operand.signed is True
        assert operand.unsigned is False
        assert operand.sign_position is model.SignPosition.IMPLICIT_BINARY
        assert operand.value_domain == (-128, 127)
        assert operand.byte_length == 1
        assert operand.is_binary_family is True
        assert operand.is_int is True
        # A binary-family item has NO picture: its range comes from its width.
        assert operand.picture is None
        assert operand.digits is None

    # The two receivers: two digits each, unsigned, zoned.
    for receiver in (WS_A, WS_Y):
        assert receiver.usage is model.Usage.DISPLAY
        assert receiver.picture == "99"
        assert receiver.signed is False
        assert receiver.sign_position is model.SignPosition.NONE
        assert receiver.digits == 2
        assert receiver.scale == 0
        assert receiver.value_domain == (0, 99)
        assert receiver.byte_length == 2
        assert receiver.is_zoned_display is True
        assert receiver.is_binary_family is False
        assert receiver.is_int is True
        # Program-local, so a locator rather than a dictionary key.
        assert receiver.dictionary_key is None
        assert receiver.source_locator is not None

    # The differences, stated as differences.
    assert SCYCLE.usage is not WS_A.usage
    assert SCYCLE.signed != WS_A.signed
    assert SCYCLE.value_domain != WS_A.value_domain
    assert SCYCLE.byte_length != WS_A.byte_length

    # ALL FOUR are carried by `int`, never by `Decimal` and never by a float: that is
    # what makes the quotient's truncation an INTEGER truncation.
    for item in (SCYCLE, PERIOD, WS_A, WS_Y):
        assert item.python_storage is model.CobolPythonStorage.INT

    # The unsigned receiver cannot hold a negative quotient, so a negative `scycle`
    # loses its sign on store. Reproduced, not guarded (R-3, R-4) - the frozen
    # statement has no ON SIZE ERROR and no sign test.
    assert arithmetic.store(Decimal("-2"), WS_A) == 2


# ---------------------------------------------------------------------------
#  SECTION 12  -  QUANTIZE ONCE, AT THE STORE
#
#  Sites 2 and 5 are the probes, because they are the only THREE-LEVEL NESTED
#  expressions in the census: `post - (post / ((rate + 100) / 100))`. Agent Action
#  Plan section 0.6.8 records why they matter - with no dialect flag and no arithmetic
#  directive anywhere in the frozen source, the compiler's default intermediate
#  precision governs every multi-term expression, and the compound VAT expression is
#  "the one place a precision difference could change a stored penny".
# ---------------------------------------------------------------------------


def test_the_intermediate_context_carries_extended_precision() -> None:
    """An expression is evaluated at 60 or more significant digits, not at the scale.

    Asserted OBSERVABLY as well as by inspection: one third, evaluated through
    `arithmetic.intermediate`, comes back with exactly as many significant digits as
    the context declares. R-2 forbids reading the ambient `decimal` context, so the
    precision is proved by what the arithmetic produces rather than by inspecting
    whatever context happens to be installed.

    Extended precision is what sites 2 and 5 need - [general/gl051.cbl:L796] and
    [irs/irs030.cbl:L1562-L1563] are three-level nested expressions whose inner
    quotient recurs - and the context that supplies it is declared at
    [acas_posting/cobol/arithmetic.py:L102] with its digit count at
    [acas_posting/cobol/arithmetic.py:L97].
    """
    assert arithmetic.INTERMEDIATE_PRECISION >= 60
    assert arithmetic.INTERMEDIATE_CONTEXT.prec == arithmetic.INTERMEDIATE_PRECISION

    one_third = arithmetic.intermediate(lambda: Decimal(1) / Decimal(3))
    assert len(one_third.as_tuple().digits) == arithmetic.INTERMEDIATE_PRECISION
    # Written out in full rather than compared against another quotient, because any
    # quotient computed HERE would be computed in whatever context happens to be
    # installed - and R-2 forbids this file from reading the ambient one.
    assert one_third == Decimal("0." + "3" * arithmetic.INTERMEDIATE_PRECISION)

    # Truncated rather than rounded at the last digit, because the EVALUATION context
    # rounds DOWN: the direction is applied once, at the store, from the call keyword.
    # Two thirds is the case that shows it - rounding half up would end ...667.
    two_thirds = arithmetic.intermediate(lambda: Decimal(2) / Decimal(3))
    assert two_thirds == Decimal("0." + "6" * arithmetic.INTERMEDIATE_PRECISION)
    assert str(two_thirds).endswith("6")

    # Site 2's own expression keeps far more digits than the receiver's two, which is
    # the property "quantize once" depends on.
    unquantized = arithmetic.intermediate(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE)
    )
    assert len(unquantized.as_tuple().digits) > 2
    assert unquantized != Decimal("17.51")
    assert unquantized != Decimal("17.50")


def test_site_2_quantizes_exactly_once_at_the_store() -> None:
    """[general/gl051.cbl:L796] is quantized ONCE, and the difference is observable.

    Two computations of the SAME inputs - 117.55 at 17.50% - differing only in where
    the quantize happens:

        quantize once, at the store        ->  17.51
        quantize each sub-expression       ->  17.08

    The second is what a reduced default intermediate precision amounts to in
    practice, and it is out by FORTY-THREE PENCE on a single posting, because
    `(rate + 100) / 100` quantized to the receiver's two decimals is 1.17 rather than
    1.175. That is the whole reason `arithmetic.compute` takes a CALLABLE: the
    caller's operators then run inside `INTERMEDIATE_CONTEXT`, and the only quantize
    in the statement is the store at the end.

    THIS TEST DOES NOT OWN THE FORMULA. It exercises the quantize discipline using
    the site's expression; `test_irs_vat_from_gross.py` owns what the formula means
    and what its successor at [irs/irs030.cbl:L1564] does to `post-amount`. Site 5,
    [irs/irs030.cbl:L1562-L1563], is checked at the end to show the discipline belongs
    to the arithmetic layer rather than to one receiver.
    """
    once = arithmetic.compute(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE),
        GL_VAT_AMOUNT,
        rounded=True,
    )
    assert once == Decimal("17.51")

    # The deliberately wrong wiring, built one sub-expression at a time so that each
    # intermediate is forced through the receiving field's scale.
    step_1 = arithmetic.store(
        arithmetic.intermediate(lambda: GROSS_VAT_RATE + 100), GL_VAT_AMOUNT
    )
    step_2 = arithmetic.store(
        arithmetic.intermediate(lambda: step_1 / 100), GL_VAT_AMOUNT
    )
    step_3 = arithmetic.store(
        arithmetic.intermediate(lambda: GROSS_POST_AMOUNT / step_2), GL_VAT_AMOUNT
    )
    per_sub_expression = arithmetic.store(
        arithmetic.intermediate(lambda: GROSS_POST_AMOUNT - step_3),
        GL_VAT_AMOUNT,
        rounded=True,
    )

    # Measured at each step: 117.50, then 1.17 - the divisor loses its half hundredth
    # here - then 100.47, then 17.08.
    assert step_1 == Decimal("117.50")
    assert step_2 == Decimal("1.17")
    assert step_3 == Decimal("100.47")
    assert per_sub_expression == Decimal("17.08")

    # The observable difference, which is the point of the test. Subtracted through
    # `arithmetic.intermediate` rather than with a bare `-`: `Decimal.__sub__` is a
    # CONTEXT operation and would round this difference to whatever precision the
    # ambient context happens to carry, so a bare `-` here would assert a property of
    # the caller's context rather than of the two measured figures. `intermediate` is
    # the layer's own escape hatch for an expression with no receiving field
    # (acas_posting/cobol/arithmetic.py:L359) and evaluates it exactly (R-2).
    assert once != per_sub_expression
    assert arithmetic.intermediate(lambda: once - per_sub_expression) == Decimal("0.43")

    # Site 5 is the same expression on the IRS receiver, and it behaves the same way,
    # so the discipline is a property of the arithmetic layer and not of one field.
    assert (
        arithmetic.compute(
            _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE),
            IRS_VAT_AMOUNT,
            rounded=True,
        )
        == Decimal("17.51")
    )


def test_sites_1_and_4_quantize_once_across_a_multiply_then_divide() -> None:
    """`post * rate / 100` rounds from ONE intermediate, not from a rounded product.

    12.34 at 17.50% is 215.950 before the divide and 2.1595 after it. Quantizing the
    product first would make no difference at this rate - 215.95 is already exact - but
    quantizing the QUOTIENT first would lose the tail that the ROUNDED store is there
    to catch, turning 2.16 into 2.15. Both steps are therefore asserted.
    """
    product = arithmetic.intermediate(lambda: NET_POST_AMOUNT * NET_VAT_RATE)
    assert product == Decimal("215.9500")

    quotient = arithmetic.intermediate(_vat_from_net(NET_POST_AMOUNT, NET_VAT_RATE))
    assert quotient == Decimal("2.159500")

    # Site 1, on the GL receiver [general/gl051.cbl:L791].
    assert (
        arithmetic.compute(
            _vat_from_net(NET_POST_AMOUNT, NET_VAT_RATE),
            GL_VAT_AMOUNT,
            rounded=True,
        )
        == Decimal("2.16")
    )
    # Site 4, the same formula on the IRS receiver [irs/irs030.cbl:L1551].
    assert (
        arithmetic.compute(
            _vat_from_net(NET_POST_AMOUNT, NET_VAT_RATE),
            IRS_VAT_AMOUNT,
            rounded=True,
        )
        == Decimal("2.16")
    )

    # And without the keyword both would store 2.15 - the penny the ROUNDED exists for.
    assert (
        arithmetic.compute(
            _vat_from_net(NET_POST_AMOUNT, NET_VAT_RATE), GL_VAT_AMOUNT
        )
        == Decimal("2.15")
    )
    assert (
        arithmetic.compute(
            _vat_from_net(NET_POST_AMOUNT, NET_VAT_RATE), IRS_VAT_AMOUNT
        )
        == Decimal("2.15")
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{Q_INTERMEDIATE_PRECISION}: the intermediate-precision question. The "
        "cobol layer records it as MEASURED against GnuCOBOL 3.2.0 "
        "(acas_posting/cobol/arithmetic.py:L96) - evaluate at extended precision, "
        "quantize ONCE at the store - so site 2 stores 17.51 for these inputs. "
        "This test asserts the REJECTED alternative, the reduced-precision "
        "per-sub-expression penny of 17.08, and must therefore FAIL. It is a "
        "tripwire, not a wish: if the arithmetic layer is ever changed to quantize "
        "sub-expressions, this xfail turns into an XPASS and strict=True fails the "
        "suite instead of letting the change pass unnoticed (R-4). The compiled "
        "oracle cannot be rebuilt in this checkout to re-measure the answer - "
        "copybooks/ACAS-SQLstate-error-list.cob is absent from the frozen archive - "
        "so the alternative is recorded here rather than asserted as fact (R-6)."
    ),
)
def test_site_2_does_not_store_the_reduced_precision_penny() -> None:
    """The reduced-precision alternative for site 2, recorded as a strict xfail.

    [general/gl051.cbl:L796] with 117.55 at 17.50%. See the xfail reason for why this
    expectation is recorded rather than asserted.
    """
    assert arithmetic.compute(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE),
        GL_VAT_AMOUNT,
        rounded=True,
    ) == Decimal("17.08")


# ---------------------------------------------------------------------------
#  SECTION 13  -  TRUNCATION REMAINS THE DEFAULT EVERYWHERE ELSE
#
#  The negative form of the census, on five representative statements drawn from
#  across the cycle. NONE of them writes `ROUNDED`, so none of them is transcribed
#  with `rounded=True`, and each assertion below states the value the truncating
#  direction produces together with the value the rounded one WOULD have produced.
# ---------------------------------------------------------------------------

#: Five representative un-`ROUNDED` statements: (locator, the statement verbatim).
#: Every one of these truncates. They are a sample, not a census - the un-ROUNDED
#: stores in the cycle number in the hundreds, which is precisely why truncation has
#: to be the DEFAULT and `ROUNDED` the annotation.
UNROUNDED_SITES: tuple[tuple[str, str], ...] = (
    ("general/gl051.cbl:L1063", "add      post-amount  to  actual-gross."),
    ("general/gl051.cbl:L1064", "add      vat-amount   to  actual-vat."),
    ("general/gl051.cbl:L604", "divide post-dr by 100 giving acc-ok"),
    (
        "general/gl072.cbl:L413",
        "divide   WS-Ledger-Nos  by  100  giving  l6-account.",
    ),
    (
        "general/gl051.cbl:L1105",
        "subtract input-vat  from  input-gross  giving  l9-amount.",
    ),
)


def test_no_representative_site_writes_rounded() -> None:
    """None of the five sampled statements carries the keyword, so none rounds.

    Asserted as data for the same reason the `ROUNDED` census is: R-1 keeps this tier
    away from the COBOL, so the transcription is checked against itself rather than
    against a file it must not read.
    """
    assert len(UNROUNDED_SITES) == 5

    rounded_locators = {locator for locator, _v, _r, _s in ROUNDED_SITES}
    for locator, statement in UNROUNDED_SITES:
        assert loader.SOURCE_LOCATOR_PATTERN.match(locator), locator
        assert "rounded" not in statement.lower(), locator
        assert locator not in rounded_locators, locator

    # The two sampled `gl051` adds sit INSIDE the in-scope control-total block, one
    # line apart [general/gl051.cbl:L1063-L1064], and the sampled subtract sits in
    # `end-batch` [general/gl051.cbl:L1096] - so all three are statements this
    # migration actually reproduces, not decoration.
    assert UNROUNDED_SITES[0][0] == "general/gl051.cbl:L1063"
    assert UNROUNDED_SITES[1][0] == "general/gl051.cbl:L1064"


def test_gl051_l1063_and_l1064_accumulate_by_truncating() -> None:
    """`add ... to actual-gross` / `actual-vat` truncate into unsigned COMP-3 fields.

    Both receivers are `pic 9(9)v99` with COMP-3 inherited from the group header
    `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40-L44], and both are UNSIGNED.

    In the frozen data path the operand is the value a previous statement STORED at
    scale two, so the sum is exact and the direction cannot show. The direction is
    nonetheless the receiver's, not the data's, so it is probed here with an
    unquantized operand: passing `rounded=True` at either site would store a penny
    more.
    """
    # The real path: a scale-two posting into a scale-two accumulator.
    assert arithmetic.add_to(
        Decimal("117.55"),
        receiver_value=Decimal("1000.00"),
        receiving=BATCH_ACTUAL_GROSS,
    ) == Decimal("1117.55")
    assert arithmetic.add_to(
        Decimal("17.51"),
        receiver_value=Decimal("0.00"),
        receiving=BATCH_ACTUAL_VAT,
    ) == Decimal("17.51")

    # The direction probe, on an operand that carries a tail.
    tail_bearing = arithmetic.intermediate(
        _vat_from_gross(GROSS_POST_AMOUNT, GROSS_VAT_RATE)
    )
    assert arithmetic.add_to(
        tail_bearing, receiver_value=Decimal("0.00"), receiving=BATCH_ACTUAL_VAT
    ) == Decimal("17.50")
    # Measured: `rounded=True` here would store 17.51 instead. [general/gl051.cbl:L1064]
    # writes no ROUNDED, so 17.50 is the reproduction and 17.51 is the defect.
    assert arithmetic.add_to(
        tail_bearing,
        receiver_value=Decimal("0.00"),
        receiving=BATCH_ACTUAL_VAT,
        rounded=True,
    ) == Decimal("17.51")

    # The same receiver ALSO drops the sign, because `pic 9(9)v99` carries none
    # [copybooks/wsbatch.cob:L43]: a credit posting accumulates as a debit. Reproduced,
    # never guarded (R-3, R-4); what it does to the control-total gate at
    # [general/gl051.cbl:L1117] belongs to `test_control_total_comparison.py`.
    assert BATCH_ACTUAL_GROSS.signed is False
    assert BATCH_ACTUAL_GROSS.usage is model.Usage.COMP_3
    assert arithmetic.add_to(
        Decimal("-117.55"),
        receiver_value=Decimal("0.00"),
        receiving=BATCH_ACTUAL_GROSS,
    ) == Decimal("117.55")


def test_gl051_l604_account_scaling_divide_truncates() -> None:
    """`divide post-dr by 100 giving acc-ok` truncates into `pic 9(4)v99`.

    [general/gl051.cbl:L604], receiving [general/gl051.cbl:L233]. `post-dr` is a
    six-digit integer [copybooks/wspost.cob:L19], so the quotient lands on exactly two
    decimals and the direction cannot show on the real operand - the scaling is exact
    by construction. The probe below carries a third decimal so the receiver's own
    direction is visible.
    """
    # The real path: 123456 becomes account 1234 point-code 56.
    assert arithmetic.divide_by_giving(123456, 100, WS_ACC_OK) == Decimal("1234.56")
    assert WS_ACC_OK.digits == 6
    assert WS_ACC_OK.scale == 2
    assert WS_ACC_OK.signed is False

    # The direction probe. Measured: `rounded=True` would store 1234.57.
    assert arithmetic.divide_by_giving(
        Decimal("123456.5"), 100, WS_ACC_OK
    ) == Decimal("1234.56")
    assert arithmetic.divide_by_giving(
        Decimal("123456.5"), 100, WS_ACC_OK, rounded=True
    ) == Decimal("1234.57")

    # `DIVIDE a BY b GIVING c` is c = a / b. The operands are written in the order the
    # statement writes them, so 100 is the DIVISOR and not the dividend - the other
    # spelling, `DIVIDE ... INTO ... GIVING`, would mean the reverse.
    assert arithmetic.divide_by_giving(123456, 100, WS_ACC_OK) != Decimal("0.00")
    assert arithmetic.divide_into_giving(100, 123456, WS_ACC_OK) == Decimal("1234.56")


def test_gl072_l413_account_scaling_divide_truncates_into_an_edited_field() -> None:
    """`divide WS-Ledger-Nos by 100 giving l6-account` truncates into `pic 9999.99`.

    [general/gl072.cbl:L413], receiving the numeric-EDITED print item at
    [general/gl072.cbl:L233]. Edited or not, the store obeys the item's underlying
    numeric shape - six digits at scale two - and the direction is still the truncating
    default. The same statement appears at [general/gl072.cbl:L386]; both are
    transcribed the same way.
    """
    assert WS_L6_ACCOUNT.is_edited is True
    assert WS_L6_ACCOUNT.picture == "9999.99"
    assert WS_L6_ACCOUNT.digits == 6
    assert WS_L6_ACCOUNT.scale == 2

    # The real path: a nominal key of 401000 prints as account 4010.00.
    assert arithmetic.divide_by_giving(401000, 100, WS_L6_ACCOUNT) == Decimal(
        "4010.00"
    )
    assert arithmetic.divide_by_giving(123456, 100, WS_L6_ACCOUNT) == Decimal(
        "1234.56"
    )

    # The direction probe. Measured: `rounded=True` would store 1234.57.
    assert arithmetic.divide_by_giving(
        Decimal("123456.5"), 100, WS_L6_ACCOUNT
    ) == Decimal("1234.56")
    assert arithmetic.divide_by_giving(
        Decimal("123456.5"), 100, WS_L6_ACCOUNT, rounded=True
    ) == Decimal("1234.57")


def test_gl051_l1105_subtract_giving_truncates_and_takes_b_minus_a() -> None:
    """`subtract input-vat from input-gross giving l9-amount` is c = b - a.

    [general/gl051.cbl:L1105], receiving [general/gl051.cbl:L331]. The operand ORDER is
    the thing to get right: the item written FIRST is the subtrahend and the item
    written after FROM is the minuend, so the answer is `input-gross - input-vat` and
    not the other way about. `arithmetic.subtract_giving` takes the minuend as a
    keyword for exactly that reason - a positional pair would invite the swap.
    """
    # The real path, with both operands at the batch record's scale two
    # [copybooks/wsbatch.cob:L41-L42].
    assert arithmetic.subtract_giving(
        Decimal("17.51"), minuend=Decimal("117.55"), receiving=WS_L9_AMOUNT
    ) == Decimal("100.04")

    # Swapping the two operands computes -100.04 instead, and at THIS receiver the
    # swap is INVISIBLE: `pic z(9)9.99bb` [general/gl051.cbl:L331] is unsigned, so the
    # sign is dropped and the same magnitude is stored. That is the strongest argument
    # for the keyword-only `minuend`: a swap here would not announce itself.
    assert arithmetic.subtract_giving(
        Decimal("117.55"), minuend=Decimal("17.51"), receiving=WS_L9_AMOUNT
    ) == Decimal("100.04")

    # On a SIGNED receiver the same swap is plainly visible, which is how the order was
    # confirmed rather than assumed [copybooks/wspost.cob:L23].
    assert arithmetic.subtract_giving(
        Decimal("17.51"), minuend=Decimal("117.55"), receiving=GL_POST_AMOUNT
    ) == Decimal("100.04")
    assert arithmetic.subtract_giving(
        Decimal("117.55"), minuend=Decimal("17.51"), receiving=GL_POST_AMOUNT
    ) == Decimal("-100.04")

    # The direction probe, on the complementary pair whose tail falls on the net side:
    # 10.01 - 2.002 = 8.008 truncates to 8.00. Measured: `rounded=True` would store
    # 8.01, and [general/gl051.cbl:L1105] writes no ROUNDED.
    assert arithmetic.subtract_giving(
        Decimal("2.002"), minuend=Decimal("10.01"), receiving=WS_L9_AMOUNT
    ) == Decimal("8.00")
    assert arithmetic.subtract_giving(
        Decimal("2.002"),
        minuend=Decimal("10.01"),
        receiving=WS_L9_AMOUNT,
        rounded=True,
    ) == Decimal("8.01")

    # The two batch fields the statement reads are the unsigned COMP-3 pair, which is
    # why neither operand can arrive negative in the first place.
    assert BATCH_INPUT_GROSS.signed is False
    assert BATCH_INPUT_VAT.signed is False
    assert BATCH_INPUT_GROSS.usage is model.Usage.COMP_3
    assert BATCH_INPUT_VAT.usage is model.Usage.COMP_3


# ---------------------------------------------------------------------------
#  SECTION 14  -  OVERFLOW IS SILENT, AND `REMAINDER` IS NEVER ASKED FOR
#
#  `ON SIZE ERROR` occurs ZERO times across all twelve in-scope programs, and so does
#  `REMAINDER`. A rounded store whose carry takes the result past the receiver's
#  capacity therefore raises NOTHING, clamps nothing, and logs nothing - it keeps the
#  low-order digits and carries on. R-3 forbids adding the guard the COBOL does not
#  have, so this section asserts the silence.
# ---------------------------------------------------------------------------

#: Census, as declared data: neither construct appears anywhere in the twelve in-scope
#: programs. Verified by a case-insensitive search over `gl051`, `gl070`, `gl071`,
#: `gl072`, `gl080`, `sl055`, `sl060`, `sl100`, `pl055`, `pl060`, `pl100` and
#: `irs030`, each of which returned no match.
ZERO_OCCURRENCE_CONSTRUCTS: tuple[str, ...] = ("ON SIZE ERROR", "REMAINDER")


def test_no_in_scope_statement_has_a_size_error_or_remainder_phrase() -> None:
    """Both constructs are absent from the cycle, which is why overflow is silent.

    The consequence for this file: there is no phrase to reproduce on the overflow
    path, so there must be no exception on it either. And no divide in the cycle asks
    for a remainder, so no verb here returns one - not even the only `ROUNDED` DIVIDE,
    [general/gl080.cbl:L328], whose quotient of 5 over 3 leaves a remainder the
    statement simply never names.
    """
    assert ZERO_OCCURRENCE_CONSTRUCTS == ("ON SIZE ERROR", "REMAINDER")

    # No `ROUNDED` site's statement carries either phrase, so the census and this one
    # agree with each other.
    for locator, _verb, _receiver, statement in ROUNDED_SITES:
        upper = statement.upper()
        for construct in ZERO_OCCURRENCE_CONSTRUCTS:
            assert construct not in upper, f"{locator}: {construct}"

    # Nor does any of the sampled un-ROUNDED statements.
    for locator, statement in UNROUNDED_SITES:
        upper = statement.upper()
        for construct in ZERO_OCCURRENCE_CONSTRUCTS:
            assert construct not in upper, f"{locator}: {construct}"

    # And every verb this file uses returns ONE value, not a value and a remainder.
    assert isinstance(
        arithmetic.divide_by_giving(CYCLE_SCYCLE, CYCLE_PERIOD, WS_A), int
    )


def test_a_rounded_store_that_overflows_is_silent_and_keeps_low_order_digits() -> None:
    """A carry past the receiver's capacity is discarded WITHOUT a word.

    `99.5` into `77 a pic 99` [general/gl080.cbl:L183] rounds to 100, which needs three
    digits where the field has two, so the high-order digit is discarded and the field
    holds 0. Truncating the same value instead keeps 99 - so at this boundary the two
    directions differ by ninety-nine rather than by one, and neither of them raises.

    Nothing here is a wish about what SHOULD happen. It is what the store does, and
    R-3 forbids adding the size-error guard the frozen statement does not carry.
    """
    # No exception, on either direction. A raised exception fails the test outright.
    truncated = arithmetic.store(Decimal("99.5"), WS_A)
    rounded = arithmetic.store(Decimal("99.5"), WS_A, rounded=True)

    assert truncated == 99
    # Measured: 99.5 rounds to 100, and 100 modulo 100 is 0.
    assert rounded == 0
    assert rounded != truncated

    # High-order digits are discarded rather than clamped, on both directions: a clamp
    # would have given 99.
    assert arithmetic.store(Decimal("123.45"), WS_A) == 23
    assert arithmetic.store(Decimal("123.45"), WS_A, rounded=True) == 23

    # The same on a scaled money receiver: 9999999.995 into `pic s9(7)v99`
    # [copybooks/irswspost.cob:L18] truncates to 9999999.99, but the rounded carry
    # takes it to 10000000.00, whose leading digit does not fit - so the field holds
    # zero, silently.
    assert arithmetic.store(Decimal("9999999.995"), IRS_VAT_AMOUNT) == Decimal(
        "9999999.99"
    )
    assert arithmetic.store(
        Decimal("9999999.995"), IRS_VAT_AMOUNT, rounded=True
    ) == Decimal("0.00")

    # And on a binary-family receiver the reduction is by BITS rather than by digits,
    # so a rounded carry past 127 wraps to the negative end of the one-byte domain
    # [copybooks/wssystem.cob:L63] instead of losing a decimal digit.
    assert SCYCLE.value_domain == (-128, 127)
    assert arithmetic.store(Decimal("127.5"), SCYCLE) == 127
    assert arithmetic.store(Decimal("127.5"), SCYCLE, rounded=True) == -128


@pytest.mark.xfail(
    strict=True,
    reason=(
        f"{Q_ROUNDED_OVERFLOW_ORDER}: whether an overflowing ROUNDED store discards "
        "the high-order carry AFTER rounding or BEFORE it. This layer rounds first "
        "and then discards, so 99.5 into `pic 99` holds 0 - which the sibling test "
        "asserts as the reproduction. The alternative order would hold 99, and this "
        "test asserts THAT, so it must FAIL. It is recorded rather than asserted "
        "because ISO leaves the receiver's content undefined when a size error "
        "occurs with no ON SIZE ERROR phrase, and there is no such phrase anywhere "
        "in the twelve in-scope programs, so only the compiled oracle can settle the "
        "order - and the oracle cannot be rebuilt in this checkout, since "
        "copybooks/ACAS-SQLstate-error-list.cob is absent from the frozen archive "
        "(R-6). If the layer is ever changed to the other order this xfail becomes "
        "an XPASS and strict=True fails the suite (R-4)."
    ),
)
def test_overflowing_rounded_store_does_not_discard_the_carry_before_rounding() -> None:
    """The alternative overflow order, recorded as a strict xfail.

    `99.5` into `77 a pic 99` [general/gl080.cbl:L183]. See the xfail reason.
    """
    assert arithmetic.store(Decimal("99.5"), WS_A, rounded=True) == 99
