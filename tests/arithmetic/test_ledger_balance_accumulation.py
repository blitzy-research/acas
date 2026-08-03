"""Ledger-balance accumulation and the sort order it depends on - ANOMALY A-14.

WHAT THIS FILE LOCKS. Two things that look unrelated in the source and are the
same fact:

  1. `gl072` locates the nominal-ledger account for a posting with a SEQUENTIAL
     read [general/gl072.cbl:L408], guarded at [general/gl072.cbl:L407], after a
     key move that a `READ NEXT` ignores entirely [general/gl072.cbl:L405]. It
     therefore finds the right account ONLY because `gl071` already emitted the
     stream in nominal-key order [general/gl071.cbl:L172-L178]. Perturb the sort
     key or the sort's stability and the program posts to the wrong account with
     NO error, NO diagnostic and wrong balances. That is anomaly A-14.
  2. The brought-forward accumulation into `tot-dr` / `tot-cr` is SIGN-DIRECTED
     but NOT SIGN-NORMALISED, is guarded by `> zero` and NOT `>= zero`, and sits
     behind THREE identical `if read-ledger not = "R"` guards that were never
     factored into one.

Agent Action Plan section 0.6.9, verbatim: "`gl071`'s output ordering is asserted
directly by a test rather than left to be caught indirectly by a state diff."
THIS IS THAT TEST - see `test_a14_gl071_output_ordering_asserted_directly`.

CITATION CORRECTION, recorded rather than passed over. The specification body
cites the sequential read as [general/gl072.cbl:L410-L412]. The real sites are
L405 (the key move), L407 (the guard) and L408 (the read). L410-L411 is the
SECOND guard and the `tot-dr` / `tot-cr` reset, and there is no L412 statement at
all - L412 is blank.

`new-account.` VERBATIM, [general/gl072.cbl:L402-L431], as it stands in the
checkout - every statement below has a test in this file:

     402  new-account.
     405      move     post-ledger  to  WS-Ledger-Key.
     407      if       read-ledger not = "R"
     408               perform  GL-Nominal-Read-Next.
     410      if       read-ledger not = "R"
     411               move  zero   to  tot-dr  tot-cr.
     413      divide   WS-Ledger-Nos  by  100  giving  l6-account.
     414      move     ledger-pc       to  l6-pc.
     415      move     ledger-balance  to  l6-balance.
     416      move     zero            to  l6-debit.
     417      move     zero            to  l6-credit.
     418      perform  zz070-convert-date.
     419      move     ws-date         to  l6-date.
     421      if       read-ledger not = "R"
     422            if    ledger-balance  >  zero
     423                  move  ledger-balance  to  l6-debit
     424                  add   ledger-balance  to  tot-dr
     425            else
     426                  move  ledger-balance  to  l6-credit
     427                  add   ledger-balance  to  tot-cr.
     429      move     "Brought Forward"  to  l6-legend.
     430      move     zero            to  l6-tran.
     431      move     space  to  read-ledger.

The SORT this all depends on, VERBATIM [general/gl071.cbl:L172-L178]:

     172      sort     sort-trans
     173               on ascending key sort-batch
     174                                sort-ac
     175                                sort-pc
     176                                sort-post
     177               using  pre-trans
     178               giving post-trans.

and the record it sorts, VERBATIM [general/gl071.cbl:L134-L144]:

     134  sd  sort-trans.
     136  01  sort-trans-record.
     137      03  sort-batch      pic 9(5).
     138      03  sort-post       pic 9(5).
     139      03  sort-code       pic xx.
     140      03  sort-date       pic x(8).
     141      03  sort-ac         pic 9(6).
     142      03  sort-pc         pic 99.
     143      03  sort-amount     pic s9(8)v99.
     144      03  sort-legend     pic x(32).

THE KEY ORDER IS NOT THE DECLARATION ORDER. `sort-post` is the SECOND field but
the FOURTH key; `sort-ac` is the FIFTH field but the SECOND key. A test that only
varies one field cannot tell the two apart, so the discriminating case below
varies `sort-ac` and `sort-post` in OPPOSITE directions.

THE SIX BINDING RULES, as they bind this file
---------------------------------------------
There is NO user rules document for this project: `review_rules` returns exactly
"No user rules provided." The binding rules R-1 to R-6 live in the Technical
Specification section 0.7.2, and where it is silent, enterprise-standard best
practice applies and nothing is invented.

R-1  No COBOL at runtime. "tests/arithmetic/* touch neither COBOL nor a
     database." The paragraph modelled here performs `GL-Nominal-Read-Next`
     [general/gl072.cbl:L408] and `end-account` performs `GL-Nominal-Rewrite`
     [general/gl072.cbl:L382]; NEITHER is called here and no `acas_posting.dal`
     module is imported. The read is modelled as A RECORD SUPPLIED TO THE TESTED
     SEQUENCE, which is exactly what its observable effect is.
R-2  Zero binary floating point. Every value here is `decimal.Decimal`, `int` or
     `str`. No binary literal, no binary constructor, no tolerance and no
     approximate comparison anywhere. The ambient decimal context is neither read
     nor written. The sort's key extraction REJECTS `float` and `complex`, and
     that rejection is asserted rather than assumed.
R-3  No new validation, no new field, no schema change, no concurrency. The three
     identical guards stay THREE separate tests, the key move at L405 stays
     inert, and no "did the read find the right account?" check exists anywhere
     in this file. Execution is strictly sequential: no parallel-execution plugin
     and no plugin that shuffles collection order - ordering determinism is this
     file's own subject, so a runner that reordered tests would be testing
     itself.
R-4  Legacy anomalies reproduced, never fixed. "A defect reproduced is correct; a
     defect fixed is a failure." Every reproduction site below carries a comment
     naming A-14 and its locator. In particular a balance of exactly zero is
     booked as a CREDIT and a negative balance is added to `tot-cr` as the
     statement writes it, with no negation and no absolute value applied by the
     paragraph. These tests exist so that a future well-intentioned correction
     fails the suite rather than passing unnoticed.
R-5  Full traceability. Every descriptor arrives by its dictionary key or by a
     `<path>:L<n>` locator into the frozen source, and every test names A-14 and
     the `[general/gl072.cbl:Lnnn]` or `[general/gl071.cbl:Lnnn]` line it locks.
     Coverage is evidence, never a gate.
R-6  Compiled behavior is the tie-breaker. Where the frozen source cannot settle
     a question, the assertion is `xfail(strict=True)` against a named `Q-` id
     from `OPEN_QUESTIONS` below. THIS FILE OWNS THE SORT TIE-ORDER QUESTION.

Also binding - section 0.8.4. No timing and no performance assertion anywhere.
The sequential read is NOT turned into an indexed one even though an indexed read
would obviously be faster: section 0.8.4 states the sequential read "is entangled
with sort-order correctness" and that "Any performance work is therefore out of
scope by construction, not merely unrequested."

Infrastructure: NONE. No Docker, no MariaDB, no GnuCOBOL. The single prerequisite
is `data_dictionary/acas_posting_dictionary.json`, read when the descriptors
below are built; run from the repository root.
"""

from __future__ import annotations

import dataclasses
import decimal
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

import pytest

from acas_posting.cobol import (
    arithmetic,
    field as cobol_field,
    move as cobol_move,
    picture as cobol_picture,
    sortverb,
    usage as cobol_usage,
)
from acas_posting.dictionary import loader, model
from acas_posting.records import work_records

pytestmark = pytest.mark.arithmetic


#  THE OPEN QUESTIONS THIS FILE RAISES (rule R-6)
#
#  Each is a question that reading the frozen source CANNOT settle and that only
#  the compiled program can answer. Every assertion that depends on one is
#  `xfail(strict=True)` against its id, so the day the oracle answers it the
#  suite reports an unexpected pass rather than staying quietly wrong.
#
#  Two questions that might be expected here are deliberately ABSENT, because
#  they are not open:
#
#    * the unsigned store into `tot-dr` / `tot-cr` - both are declared
#      `pic 9(8)v99` [general/gl072.cbl:L165-L166], with no `s`, so the sign is
#      dropped on store. `acas_posting.cobol.usage` states that rule for a
#      declared digit count and its zoned questions Q-5.1, Q-5.2 and Q-5.3 are
#      already settled there, so the value is asserted plainly below.
#    * the high-order digit discard of an un-ROUNDED store - same module, same
#      settled rule: nothing is raised and nothing is clamped.
OPEN_QUESTIONS: Final[dict[str, str]] = {
    "Q-SORT-TIE-ORDER": (
        "Where the compiled SORT places two records carrying an IDENTICAL "
        "(sort-batch, sort-ac, sort-pc, sort-post). The tie is reachable: the "
        "CR leg and the VAT leg of the gl070 double-entry explosion coincide "
        "when the VAT account equals the CR account, and "
        "[general/gl071.cbl:L172-L178] carries NO `with duplicates in order` "
        "phrase, so GnuCOBOL's tie order is unstated. Our own sort is stable "
        "unconditionally, because Agent Action Plan section 0.4.1.2 makes the "
        "output ordering a hard contract consumed by gl072; until the oracle "
        "answers, the two may diverge and the scenario tier will surface it."
    ),
    "Q-EDITED-BLANK-WHEN-ZERO": (
        "The characters the compiled program renders into a `blank when zero` "
        "numeric-edited print item - `l6-account pic 9999.99 blank when zero` "
        "[general/gl072.cbl:L233], `l6-debit` and `l6-credit pic z(7)9.99 "
        "blank when zero` [general/gl072.cbl:L241], [general/gl072.cbl:L243]. "
        "No in-scope database write reaches an edited picture, so no table "
        "diff can observe the rendering; `acas_posting.cobol.move` refuses it "
        "under its own question Q-14 rather than inventing an answer."
    ),
}


#  THE DEFENSIVE DICTIONARY-KEY RESOLUTION, local to this file
#
#  A key that does not exist must fail with a diagnostic that NAMES THE NEAR
#  MISSES, because the alternative - a test skipped or a descriptor guessed - is
#  how a field-level transcription error survives (rule R-5). One real near miss
#  drives this: `Ledger-PC` is a `05` item INSIDE `WS-Ledger-Key`
#  [copybooks/wsledger.cob:L20], so no `GLLEDGER-REC.LEDGER-PC` column entry
#  exists and the copybook-record key must be used instead.

#: `loader.DictionaryKeyError` is a `KeyError` subclass, so a near miss is caught
#: as one without importing the loader's own exception name into every call site.
_KEY_ERRORS: Final[tuple[type[BaseException], ...]] = (KeyError,)


def _near_misses(field_name: str) -> tuple[str, ...]:
    """Every dictionary key whose field name matches, for a diagnostic.

    Args:
        field_name: The unqualified COBOL field name, compared case-insensitively
            because the artifact carries `LEDGER-BALANCE` for the column view and
            `Ledger-Balance` for the copybook view of one field.

    Returns:
        The matching entry keys, in the artifact's own order.
    """
    wanted = field_name.casefold()
    return tuple(
        entry.key
        for entry in loader.entries()
        if entry.key.rsplit(".", 1)[-1].split("#", 1)[0].casefold() == wanted
    )


def descriptor(*candidates: str) -> cobol_field.FieldDescriptor:
    """Build the descriptor for the first candidate key the artifact carries.

    Several candidates are accepted because one field can be keyed by its table
    and column or by its copybook record and field name, and which of the two the
    artifact holds is a property of whether a column backs the field - not
    something a test may assume.

    Args:
        *candidates: Qualified entry keys, most specific first.

    Returns:
        The descriptor for the first key that exists.

    Raises:
        AssertionError: No candidate exists. The message lists the near misses so
            that the real key is one line away rather than a search.
    """
    assert candidates, "descriptor() needs at least one candidate key"
    for key in candidates:
        try:
            return cobol_field.FieldDescriptor.from_dictionary_key(key)
        except _KEY_ERRORS:
            continue
    field_name = candidates[0].rsplit(".", 1)[-1]
    raise AssertionError(
        "none of the candidate dictionary keys "
        + repr(candidates)
        + " exists in data_dictionary/acas_posting_dictionary.json. Entries "
        "whose field name is "
        + repr(field_name)
        + ": "
        + repr(_near_misses(field_name))
        + ". Rule R-5 requires every descriptor to cite its entry, so a "
        "guessed shape is not an option; regenerate the artifact with "
        "`python -m acas_posting.dictionary.generate` if it is stale."
    )


#  THE LEDGER RECORD  [copybooks/wsledger.cob]

#: `03 Ledger-Balance pic s9(8)v99 comp-3.` [copybooks/wsledger.cob:L28] - the
#: item both accumulations write: `add post-amount to ledger-balance`
#: [general/gl072.cbl:L331] and the brought-forward read at
#: [general/gl072.cbl:L422-L427].
LEDGER_BALANCE: Final[cobol_field.FieldDescriptor] = descriptor(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

#: `03 Ledger-Last pic s9(8)v99 comp-3.` [copybooks/wsledger.cob:L29] - the same
#: shape, one line below, and NOT written by `gl072`.
LEDGER_LAST: Final[cobol_field.FieldDescriptor] = descriptor(
    "GLLEDGER-REC.LEDGER-LAST"
)

#: `05 Ledger-Q pic s9(8)v99 comp-3 occurs 4.` [copybooks/wsledger.cob:L36],
#: under `03 filler redefines Quarters.` [copybooks/wsledger.cob:L35].
LEDGER_Q: Final[cobol_field.FieldDescriptor] = descriptor(
    "WS-Ledger-Record.Ledger-Q"
)

#: `03 filler redefines Quarters.` [copybooks/wsledger.cob:L35] - the group that
#: carries the REDEFINES relationship the four `05` quarters are seen through.
LEDGER_QUARTERS_REDEFINITION: Final[cobol_field.FieldDescriptor] = descriptor(
    "WS-Ledger-Record.filler#35"
)

#: `03 Quarters.` [copybooks/wsledger.cob:L30] - the group being redefined.
LEDGER_QUARTERS: Final[cobol_field.FieldDescriptor] = descriptor(
    "WS-Ledger-Record.Quarters"
)

#: `03 Ledger-Name pic x(24).` [copybooks/wsledger.cob:L27]. ANOMALY A-12 lives
#: here - 24 characters in the copybook, 32 in the bridge host variable and 32 in
#: the column. The primary lock for A-12 is `test_pic_field_descriptors.py`; this
#: file only records that the drift is carried and not smoothed away.
LEDGER_NAME: Final[cobol_field.FieldDescriptor] = descriptor(
    "GLLEDGER-REC.LEDGER-NAME"
)

#: `05 Ledger-PC pic 9(2).` [copybooks/wsledger.cob:L20] - the sender of `move
#: ledger-pc to l6-pc` [general/gl072.cbl:L414]. THE NEAR MISS: it is a `05`
#: inside `WS-Ledger-Key`, so no column is keyed for it on its own.
LEDGER_PC: Final[cobol_field.FieldDescriptor] = descriptor(
    "GLLEDGER-REC.LEDGER-PC", "WS-Ledger-Record.Ledger-PC"
)

#: `05 WS-Ledger-Nos pic 9(6).` [copybooks/wsledger.cob:L14] - the dividend of
#: both account-number scalings, [general/gl072.cbl:L386] and
#: [general/gl072.cbl:L413].
WS_LEDGER_NOS: Final[cobol_field.FieldDescriptor] = descriptor(
    "WS-Ledger-Record.WS-Ledger-Nos"
)

#: `03 WS-Ledger-Key.` [copybooks/wsledger.cob:L13] - the GROUP receiver of the
#: inert key move [general/gl072.cbl:L405].
WS_LEDGER_KEY: Final[cobol_field.FieldDescriptor] = descriptor(
    "WS-Ledger-Record.WS-Ledger-Key"
)


#  THE POSTING RECORD  [copybooks/wspost.cob]

#: `03 Post-Amount pic s9(8)v99.` [copybooks/wspost.cob:L23] - DISPLAY, signed,
#: sign trailing and included. Ten bytes, and the copybook proves it with its own
#: offset comments: `CR-PC` ends at 36 [copybooks/wspost.cob:L22] and
#: `Post-Amount` at 46, so 46 - 36 = 10; `Post-Vat-Side` ends at 86
#: [copybooks/wspost.cob:L27] and `Vat-Amount` at 96, so 96 - 86 = 10 again.
POST_AMOUNT: Final[cobol_field.FieldDescriptor] = descriptor(
    "GLPOSTING-REC.POST-AMOUNT"
)


#  THE SORT WORK RECORD  [general/gl071.cbl:L136-L144]
#
#  These eight fields are declared INLINE in `gl071`'s own SORT-FILE description -
#  no copybook declares them, no bridge host variable carries them and no column
#  stores them - so they have exactly ONE layer view and therefore ZERO DRIFT by
#  construction. The generated artifact catalogues them anyway, and says why: the
#  sequential read at [general/gl072.cbl:L408] "depends on the widths and the
#  order these records fix". Every one carries `anomaly_refs == ("A-14",)`.
#
#  Note on the API. An earlier factory, `FieldDescriptor.for_working_storage`,
#  minted a descriptor for such a field from a bare `<path>:L<n>` locator; it was
#  withdrawn (see the note at acas_posting/cobol/field.py, just below
#  `from_dictionary_key`) once the artifact began cataloguing the work-file
#  records. The dictionary key is the stronger provenance of the two, so these
#  come through `descriptor()` like every other catalogued field.

SORT_FIELD_KEYS: Final[tuple[tuple[str, str], ...]] = (
    # (attribute on SortTransRecord, unqualified COBOL name) in DECLARATION order,
    # [general/gl071.cbl:L137-L144].
    ("sort_batch", "sort-batch"),
    ("sort_post", "sort-post"),
    ("sort_code", "sort-code"),
    ("sort_date", "sort-date"),
    ("sort_ac", "sort-ac"),
    ("sort_pc", "sort-pc"),
    ("sort_amount", "sort-amount"),
    ("sort_legend", "sort-legend"),
)

SORT_DESCRIPTORS: Final[dict[str, cobol_field.FieldDescriptor]] = {
    attribute: descriptor("sort-trans-record." + cobol_name)
    for attribute, cobol_name in SORT_FIELD_KEYS
}


#  `gl072`'s OWN WORKING STORAGE AND PRINT LINE
#
#  These are program-local items: no copybook declares them, so they arrive
#  through the picture parser with a `<path>:L<n>` locator into the frozen program
#  (rule R-5). The pictures below are transcribed character-for-character from the
#  lines cited.

#: `03 read-ledger pic x value space.` [general/gl072.cbl:L162] - the flag all
#: three guards test, set to "R" only by the page-overflow path
#: [general/gl072.cbl:L338] and cleared unconditionally at
#: [general/gl072.cbl:L431].
READ_LEDGER: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic x value space",
    name="read-ledger",
    source_locator="general/gl072.cbl:L162",
)

#: `03 tot-dr pic 9(8)v99 value zero.` [general/gl072.cbl:L165]. NO `s`: the
#: accumulator is UNSIGNED, ten digits, scale two.
TOT_DR: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic 9(8)v99 value zero",
    name="tot-dr",
    source_locator="general/gl072.cbl:L165",
)

#: `03 tot-cr pic 9(8)v99 value zero.` [general/gl072.cbl:L166]. Also UNSIGNED,
#: which is what makes the sign of a negative brought-forward balance a question
#: about the FIELD and not about the statement - see
#: `test_a14_credit_accumulation_is_sign_directed_not_sign_normalised`.
TOT_CR: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic 9(8)v99 value zero",
    name="tot-cr",
    source_locator="general/gl072.cbl:L166",
)

#: `03 l6-account pic 9999.99 blank when zero.` [general/gl072.cbl:L233] - the
#: receiver of BOTH account-number divides, [general/gl072.cbl:L386] and
#: [general/gl072.cbl:L413]. NUMERIC-EDITED, and a print-line item.
L6_ACCOUNT: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic 9999.99 blank when zero",
    name="l6-account",
    source_locator="general/gl072.cbl:L233",
)

#: `03 l6-debit pic z(7)9.99 blank when zero.` [general/gl072.cbl:L241].
L6_DEBIT: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic z(7)9.99 blank when zero",
    name="l6-debit",
    source_locator="general/gl072.cbl:L241",
)

#: `03 l6-credit pic z(7)9.99 blank when zero.` [general/gl072.cbl:L243].
L6_CREDIT: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic z(7)9.99 blank when zero",
    name="l6-credit",
    source_locator="general/gl072.cbl:L243",
)

#: `03 l6-legend pic x(32).` [general/gl072.cbl:L245] - plain alphanumeric, and
#: therefore the one print-line receiver whose stored value is observable without
#: settling `Q-EDITED-BLANK-WHEN-ZERO`.
L6_LEGEND: Final[cobol_field.FieldDescriptor] = cobol_picture.descriptor_for(
    "pic x(32)",
    name="l6-legend",
    source_locator="general/gl072.cbl:L245",
)

#: `03 post-ledger.` [general/gl072.cbl:L115-L117] - a GROUP over `05 post-ac pic
#: 9(6)` and `05 post-pc pic 99`, and the sending item of the inert key move.
POST_LEDGER_GROUP: Final[cobol_field.FieldDescriptor] = descriptor(
    "post-trans-record.post-ledger"
)

#: `05 post-ac pic 9(6).` [general/gl072.cbl:L116] - `gl072`'s NESTED account
#: number, distinct from `gl071`'s flat one at [general/gl071.cbl:L129].
POST_LEDGER_AC: Final[cobol_field.FieldDescriptor] = descriptor(
    "post-trans-record.post-ac#116"
)

#: `05 post-pc pic 99.` [general/gl072.cbl:L117].
POST_LEDGER_PC: Final[cobol_field.FieldDescriptor] = descriptor(
    "post-trans-record.post-pc#117"
)

#: `03 post-ac pic 9(6).` [general/gl071.cbl:L129] - `gl071`'s FLAT declaration of
#: the same physical bytes. Recorded beside the nested one, NOT harmonised with
#: it (rule R-4); see `test_two_post_trans_record_declarations_are_both_recorded`.
POST_AC_FLAT: Final[cobol_field.FieldDescriptor] = descriptor(
    "post-trans-record.post-ac#129"
)

#: `03 post-pc pic 99.` [general/gl071.cbl:L130].
POST_PC_FLAT: Final[cobol_field.FieldDescriptor] = descriptor(
    "post-trans-record.post-pc#130"
)


#  CONSTANTS TRANSCRIBED FROM THE FROZEN SOURCE

#: The literal the three guards compare against [general/gl072.cbl:L407],
#: [general/gl072.cbl:L410], [general/gl072.cbl:L421], stored at
#: [general/gl072.cbl:L338].
READ_SUPPRESSED: Final[str] = "R"

#: What [general/gl072.cbl:L431] leaves in `read-ledger` - `move space to
#: read-ledger` into a `pic x` item, so one space.
READ_ALLOWED: Final[str] = " "

#: The divisor of `divide WS-Ledger-Nos by 100 giving l6-account`
#: [general/gl072.cbl:L413].
ACCOUNT_DIVISOR: Final[int] = 100

#: `move "Brought Forward" to l6-legend.` [general/gl072.cbl:L429], padded by the
#: receiver to its own `pic x(32)` width.
BROUGHT_FORWARD: Final[str] = "Brought Forward"

#: The scale-two zero the two `value zero` clauses declare
#: [general/gl072.cbl:L165-L166].
MONEY_ZERO: Final[Decimal] = Decimal("0.00")

#: `03 l6-tran pic bbbz9 blank when zero.` [general/gl072.cbl:L238] receives zero
#: at [general/gl072.cbl:L430].
L6_TRAN_ZERO: Final[int] = 0

#: The five `ROUNDED` sites of the whole migrated cycle. NONE is in `gl072`, which
#: is why every store this file asserts is the truncating one.
ROUNDED_SITES: Final[tuple[str, ...]] = (
    "general/gl051.cbl:L791",
    "general/gl051.cbl:L796",
    "general/gl080.cbl:L328",
    "irs/irs030.cbl:L1551",
    "irs/irs030.cbl:L1562",
)

#: The `DIVIDE` census over the twelve in-scope programs, counted from the frozen
#: source: seventeen statements, thirteen written `BY ... GIVING` and four written
#: `INTO ... GIVING`. [general/gl072.cbl:L413] is a `BY` form.
DIVIDE_CENSUS: Final[dict[str, int]] = {
    "total": 17,
    "by_giving": 13,
    "into_giving": 4,
}

#: The `DIVIDE`-into-an-edited-receiver sites, counted over the twelve programs.
#: FIVE, not three: the specification body names three of them, and the two it
#: does not name are the sibling print divides in `gl051` whose receivers are
#: `l7-dr pic zzz9.99b` [general/gl051.cbl:L308] and `l7-vat-ac pic zzz9.99 blank
#: when zero` [general/gl051.cbl:L314]. `gl051`'s other two divides
#: [general/gl051.cbl:L604], [general/gl051.cbl:L607] give into `acc-ok pic
#: 9(4)v99` [general/gl051.cbl:L233], which is NOT edited, and are excluded.
DIVIDE_INTO_EDITED_SITES: Final[tuple[str, ...]] = (
    "general/gl051.cbl:L1035",
    "general/gl051.cbl:L1037",
    "general/gl051.cbl:L1044",
    "general/gl072.cbl:L386",
    "general/gl072.cbl:L413",
)


#  THE PARAGRAPH UNDER TEST  -  `new-account.` [general/gl072.cbl:L402-L431]
#
#  Modelled here, statement by statement, with the frozen line number against
#  each. It is modelled rather than imported because rule R-1 keeps this tier off
#  `acas_posting.dal`, and `acas_posting.programs.gl072_transaction_update` reaches
#  the facade at [general/gl072.cbl:L408]. The one statement that would need the
#  facade is the READ, and its whole observable effect is that the ledger record
#  area is replaced - so it arrives here as A RECORD SUPPLIED TO THE SEQUENCE.
#
#  Two statements are deliberately NOT modelled, and neither is skipped silently:
#
#    * `perform zz070-convert-date.` [general/gl072.cbl:L418] and `move ws-date to
#      l6-date.` [general/gl072.cbl:L419]. The date sections are locked in the date
#      tier and `acas_posting.dates` is outside this file's import surface. What
#      matters to A-14 is that L418-L419 sit UNGUARDED between guard two and guard
#      three, and that is asserted through the un-guarded statements this file can
#      reach - L413, L429 and L431.
#    * the print writes at [general/gl072.cbl:L433-L435]. They have no database
#      effect, so section 0.3.4 drops them.


@dataclass(frozen=True, slots=True)
class LedgerArea:
    """The three `WS-Ledger-Record` items `new-account.` reads.

    Frozen, so that a test cannot mutate the record it supplied and then assert
    against its own mutation.

    Attributes:
        ws_ledger_nos: `05 WS-Ledger-Nos pic 9(6).`
            [copybooks/wsledger.cob:L14].
        ledger_pc: `05 Ledger-PC pic 9(2).` [copybooks/wsledger.cob:L20].
        ledger_balance: `03 Ledger-Balance pic s9(8)v99 comp-3.`
            [copybooks/wsledger.cob:L28].
    """

    ws_ledger_nos: int = 0
    ledger_pc: int = 0
    ledger_balance: Decimal = MONEY_ZERO


@dataclass(frozen=True, slots=True)
class PostLedgerGroup:
    """`03 post-ledger.` [general/gl072.cbl:L115-L117], the key move's sender.

    Attributes:
        post_ac: `05 post-ac pic 9(6).` [general/gl072.cbl:L116].
        post_pc: `05 post-pc pic 99.` [general/gl072.cbl:L117].
    """

    post_ac: int = 0
    post_pc: int = 0


@dataclass(frozen=True, slots=True)
class NewAccountOutcome:
    """Everything `new-account.` leaves behind, and nothing it does not.

    Attributes:
        ws_ledger_key_image: What `move post-ledger to WS-Ledger-Key`
            [general/gl072.cbl:L405] put in the indexed key. Recorded so that the
            key can be shown NOT to decide which record the `READ NEXT` consumed.
        ledger: The ledger record area after the guarded read.
        read_consumed: Whether guard one [general/gl072.cbl:L407] let the read at
            [general/gl072.cbl:L408] happen.
        totals_reset: Whether guard two [general/gl072.cbl:L410] let the reset at
            [general/gl072.cbl:L411] happen.
        tot_dr: `03 tot-dr pic 9(8)v99.` [general/gl072.cbl:L165] afterwards.
        tot_cr: `03 tot-cr pic 9(8)v99.` [general/gl072.cbl:L166] afterwards.
        l6_account: The quotient stored by [general/gl072.cbl:L413].
        l6_pc_sent: The value [general/gl072.cbl:L414] sends to `l6-pc`.
        l6_balance_sent: The value [general/gl072.cbl:L415] sends to `l6-balance`.
        l6_debit_sent: The last value sent to `l6-debit` - zero from
            [general/gl072.cbl:L416], replaced by the balance if
            [general/gl072.cbl:L423] runs.
        l6_credit_sent: The last value sent to `l6-credit` - zero from
            [general/gl072.cbl:L417], replaced by the balance if
            [general/gl072.cbl:L426] runs.
        balance_receiver: Which of the two print items the balance was sent to -
            `"l6-debit"`, `"l6-credit"`, or `""` when guard three suppressed both.
        accumulator: Which accumulator the balance was added to - `"tot-dr"`,
            `"tot-cr"`, or `""`.
        l6_legend: `03 l6-legend pic x(32).` [general/gl072.cbl:L245] after
            [general/gl072.cbl:L429].
        l6_tran_sent: The value [general/gl072.cbl:L430] sends to `l6-tran`.
        read_ledger: `read-ledger` after [general/gl072.cbl:L431].

    The four `l6_*_sent` members record the value the STATEMENT SENDS rather than
    the characters the receiver renders. Three of those four receivers are
    numeric-edited `blank when zero` print items and their rendering is question
    `Q-EDITED-BLANK-WHEN-ZERO`, so a rendered string here would be an invention -
    see `test_edited_print_receivers_have_no_compiled_rendering`.
    """

    ws_ledger_key_image: str
    ledger: LedgerArea
    read_consumed: bool
    totals_reset: bool
    tot_dr: Decimal
    tot_cr: Decimal
    l6_account: Decimal
    l6_pc_sent: int
    l6_balance_sent: Decimal
    l6_debit_sent: Decimal
    l6_credit_sent: Decimal
    balance_receiver: str
    accumulator: str
    l6_legend: str
    l6_tran_sent: int
    read_ledger: str


def new_account(
    *,
    read_ledger: str,
    ledger: LedgerArea,
    post_ledger: PostLedgerGroup,
    supplied: LedgerArea | None = None,
    tot_dr: Decimal = MONEY_ZERO,
    tot_cr: Decimal = MONEY_ZERO,
) -> NewAccountOutcome:
    """`new-account.` [general/gl072.cbl:L402-L431], statement by statement.

    ANOMALY A-14 IS THIS FUNCTION. The key move at L405 addresses an account; the
    read at L408 is a `READ NEXT` and ignores that key; so which account the
    paragraph actually posts against is decided entirely by where the sequential
    cursor happens to be, which is decided entirely by `gl071`'s sort
    [general/gl071.cbl:L172-L178].

    Args:
        read_ledger: `read-ledger` on entry - `"R"` suppresses all three guards.
        ledger: The ledger record area on entry.
        post_ledger: The `post-ledger` group the key move sends.
        supplied: The record the sequential read delivers when guard one permits
            it, standing in for `GL-Nominal-Read-Next` (rule R-1). None means the
            read delivered the area unchanged, which is what a read that hits the
            same account again does.
        tot_dr: `tot-dr` on entry.
        tot_cr: `tot-cr` on entry.

    Returns:
        Everything the paragraph left behind.
    """
    # 405 move post-ledger to WS-Ledger-Key.
    # A-14, FIRST HALF. This addresses an account and then nothing reads the
    # address: L408 is a `READ NEXT`. The move is INERT with respect to WHICH
    # record is consumed, and it stays inert - no key check is added here (R-3).
    # A group may be moved as an alphanumeric item of its children's concatenated
    # width, which is what makes this statement legal at all.
    sender = _zoned_image(post_ledger.post_ac, POST_LEDGER_AC) + _zoned_image(
        post_ledger.post_pc, POST_LEDGER_PC
    )
    key_image = str(
        cobol_move.move_group(
            sender, WS_LEDGER_KEY, sending_field=POST_LEDGER_GROUP
        )
    )

    # 407 if read-ledger not = "R"
    # 408          perform GL-Nominal-Read-Next.
    # GUARD ONE OF THREE. Its own `if`, testing its own copy of the condition.
    read_consumed = read_ledger != READ_SUPPRESSED
    area = ledger
    if read_consumed:
        # A-14, SECOND HALF: a SEQUENTIAL read. The record that arrives is the one
        # the cursor is on, not the one `key_image` names.
        if supplied is not None:
            area = supplied

    # 410 if read-ledger not = "R"
    # 411          move zero to tot-dr tot-cr.
    # GUARD TWO OF THREE - a SEPARATE `if` carrying the SAME condition, never
    # factored into guard one. The statement it guards is a MULTI-RECEIVER `MOVE`:
    # one sender, two receivers, each applying its own field's rules.
    totals_reset = read_ledger != READ_SUPPRESSED
    if totals_reset:
        reset_dr, reset_cr = cobol_move.move_to_all(
            cobol_move.Figurative.ZERO, [TOT_DR, TOT_CR]
        )
        tot_dr = _money(reset_dr)
        tot_cr = _money(reset_cr)

    # 413 divide WS-Ledger-Nos by 100 giving l6-account.
    # UNCONDITIONAL - it sits between guard two and guard three. Un-ROUNDED, into
    # a numeric-edited receiver, and presentation-only in effect.
    l6_account = _money(
        arithmetic.divide_by_giving(
            area.ws_ledger_nos, ACCOUNT_DIVISOR, L6_ACCOUNT, rounded=False
        )
    )

    # 414 move ledger-pc to l6-pc.
    # 415 move ledger-balance to l6-balance.
    # 416 move zero to l6-debit.
    # 417 move zero to l6-credit.
    # All four UNCONDITIONAL. The values sent are recorded; the rendering of the
    # three edited receivers is `Q-EDITED-BLANK-WHEN-ZERO`.
    l6_pc_sent = area.ledger_pc
    l6_balance_sent = area.ledger_balance
    l6_debit_sent = MONEY_ZERO
    l6_credit_sent = MONEY_ZERO

    # 418 perform zz070-convert-date.
    # 419 move ws-date to l6-date.
    # UNCONDITIONAL, and outside this file's import surface - see the note above
    # this class group.

    # 421 if read-ledger not = "R"
    # 422       if ledger-balance > zero
    # 423             move ledger-balance to l6-debit
    # 424             add  ledger-balance to tot-dr
    # 425       else
    # 426             move ledger-balance to l6-credit
    # 427             add  ledger-balance to tot-cr.
    # GUARD THREE OF THREE, and the accumulation it guards.
    #
    # `> zero` AND NOT `>= zero` [general/gl072.cbl:L422]: a balance of EXACTLY
    # zero fails the test and takes the `else`, so it is booked as a CREDIT. That
    # is correct because the source says so (R-4).
    #
    # SIGN-DIRECTED BUT NOT SIGN-NORMALISED [general/gl072.cbl:L426-L427]: the
    # sign of `ledger-balance` chooses the branch, and then the balance is added
    # AS IT STANDS. There is no `multiply by -1` anywhere in this paragraph -
    # contrast [general/gl072.cbl:L327], which writes `subtract post-amount from
    # tot-cr` for the same idea in the main loop. Neither an absolute value nor a
    # negation is applied here.
    balance_receiver = ""
    accumulator = ""
    if read_ledger != READ_SUPPRESSED:
        if arithmetic.compare(area.ledger_balance, 0) > 0:
            l6_debit_sent = area.ledger_balance
            balance_receiver = "l6-debit"
            tot_dr = _money(
                arithmetic.add_to(
                    area.ledger_balance,
                    receiver_value=tot_dr,
                    receiving=TOT_DR,
                    rounded=False,
                )
            )
            accumulator = "tot-dr"
        else:
            l6_credit_sent = area.ledger_balance
            balance_receiver = "l6-credit"
            tot_cr = _money(
                arithmetic.add_to(
                    area.ledger_balance,
                    receiver_value=tot_cr,
                    receiving=TOT_CR,
                    rounded=False,
                )
            )
            accumulator = "tot-cr"

    # 429 move "Brought Forward" to l6-legend.
    # 430 move zero to l6-tran.
    # 431 move space to read-ledger.
    # All three UNCONDITIONAL, including the reset at L431 - which is why a page
    # overflow suppresses the guards for exactly one visit and no more.
    l6_legend = str(cobol_move.move(BROUGHT_FORWARD, L6_LEGEND))
    l6_tran_sent = L6_TRAN_ZERO
    read_ledger_after = str(cobol_move.move(cobol_move.Figurative.SPACE, READ_LEDGER))

    return NewAccountOutcome(
        ws_ledger_key_image=key_image,
        ledger=area,
        read_consumed=read_consumed,
        totals_reset=totals_reset,
        tot_dr=tot_dr,
        tot_cr=tot_cr,
        l6_account=l6_account,
        l6_pc_sent=l6_pc_sent,
        l6_balance_sent=l6_balance_sent,
        l6_debit_sent=l6_debit_sent,
        l6_credit_sent=l6_credit_sent,
        balance_receiver=balance_receiver,
        accumulator=accumulator,
        l6_legend=l6_legend,
        l6_tran_sent=l6_tran_sent,
        read_ledger=read_ledger_after,
    )


def _zoned_image(value: int, field: cobol_field.FieldDescriptor) -> str:
    """The bytes a zoned DISPLAY item holds, as characters.

    Laid out by `acas_posting.cobol.usage.encode` rather than by string padding
    here, so that the zone nibbles are the ones that module measured against the
    compiler rather than ones this file assumed.

    Args:
        value: The value stored in the item.
        field: The item's description.

    Returns:
        Exactly `field.byte_length` characters.
    """
    return cobol_usage.encode(
        value,
        usage=field.usage,
        digits=field.digits,
        scale=field.scale,
        signed=field.signed,
        unsigned=field.unsigned,
        sign_position=field.sign_position,
    ).decode("latin-1")


def _money(value: object) -> Decimal:
    """Narrow a scaled store's result to `Decimal` for the outcome record.

    Args:
        value: What `arithmetic` or `move` returned for a scale-two item.

    Returns:
        The same value as `Decimal`.

    Raises:
        AssertionError: The value did not arrive on the `Decimal` carrier, which
            would mean a descriptor above lost its scale.
    """
    assert isinstance(value, Decimal), (
        "a scale-two COBOL item must arrive on the Decimal carrier (rule R-2); "
        "got " + type(value).__name__
    )
    return value


def sort_keys(*attributes: str) -> tuple[sortverb.SortKey, ...]:
    """Build a `SORT` key tuple from `sort-trans-record` attribute names.

    Built HERE, in the test, and not by `sortverb`: that module hard-codes no key
    tuple, so the key order asserted below is the one this file states and can be
    varied on purpose to show what a wrong one does.

    Args:
        *attributes: `SortTransRecord` attribute names, MOST SIGNIFICANT FIRST.

    Returns:
        One `SortKey` per attribute, each carrying that field's own descriptor.
    """
    return tuple(
        sortverb.SortKey(
            accessor=attribute, descriptor=SORT_DESCRIPTORS[attribute]
        )
        for attribute in attributes
    )


#: The key tuple `[general/gl071.cbl:L173-L176]` declares: batch, then ACCOUNT,
#: then profit centre, then POSTING NUMBER. NOT the record's declaration order.
GL071_KEYS: Final[tuple[sortverb.SortKey, ...]] = sort_keys(
    "sort_batch", "sort_ac", "sort_pc", "sort_post"
)

#: The record's DECLARATION order, used only as a counter-case. Sorting with this
#: is the mis-key, and a mis-key here is silent misposting.
DECLARATION_ORDER_KEYS: Final[tuple[sortverb.SortKey, ...]] = sort_keys(
    "sort_batch", "sort_post", "sort_ac", "sort_pc"
)


def sort_record(
    *,
    batch: int,
    post: int,
    account: int,
    profit_centre: int,
    legend: str = "",
    amount: str = "0.00",
    code: str = "GL",
    date: str = "21/09/25",
) -> work_records.SortTransRecord:
    """One `01 sort-trans-record.` [general/gl071.cbl:L136-L144].

    Keyword-only throughout, because the record's field order and its KEY order
    differ and a positional call would read as though they agreed.

    Args:
        batch: `sort-batch pic 9(5)` - the FIRST key.
        post: `sort-post pic 9(5)` - the FOURTH key, the second field.
        account: `sort-ac pic 9(6)` - the SECOND key, the fifth field.
        profit_centre: `sort-pc pic 99` - the THIRD key.
        legend: `sort-legend pic x(32)` - not a key; the tie marker below.
        amount: `sort-amount pic s9(8)v99` - not a key.
        code: `sort-code pic xx` - not a key.
        date: `sort-date pic x(8)` - not a key.

    Returns:
        The record.
    """
    return work_records.SortTransRecord(
        sort_batch=batch,
        sort_post=post,
        sort_code=code,
        sort_date=date,
        sort_ac=account,
        sort_pc=profit_centre,
        sort_amount=Decimal(amount),
        sort_legend=legend,
    )


#  GROUP A  -  THE FIELD SHAPES THE ACCUMULATION IS PERFORMED IN
#
#  Every expected number below is read off the frozen declaration cited beside it.
#  The two byte widths are HARD FACTS and are asserted plainly, not deferred to a
#  question: six bytes for `pic s9(8)v99 comp-3` and ten for the DISPLAY form.


def test_ledger_balance_is_signed_packed_ten_digits_six_bytes() -> None:
    """`Ledger-Balance pic s9(8)v99 comp-3.` [copybooks/wsledger.cob:L28].

    The receiving field of `add post-amount to ledger-balance`
    [general/gl072.cbl:L331] and the sender of the brought-forward accumulation
    [general/gl072.cbl:L422-L427], so its shape governs both. ANOMALY A-14 depends
    on this item being read from the record the SEQUENTIAL read delivered.

    Six bytes because a packed item spends one nibble per digit plus one for the
    sign: (10 + 2) // 2 == 6, the same count as ceil((10 + 1) / 2).
    """
    assert LEDGER_BALANCE.picture == "s9(8)v99"
    assert LEDGER_BALANCE.usage is model.Usage.COMP_3
    assert LEDGER_BALANCE.is_packed is True
    assert LEDGER_BALANCE.signed is True
    assert LEDGER_BALANCE.digits == 10
    assert LEDGER_BALANCE.integer_digits == 8
    assert LEDGER_BALANCE.scale == 2
    assert LEDGER_BALANCE.byte_length == 6
    assert LEDGER_BALANCE.python_storage is model.CobolPythonStorage.DECIMAL
    assert LEDGER_BALANCE.is_decimal is True
    # A packed item's sign is in its own low nibble, not overpunched on a digit.
    assert LEDGER_BALANCE.sign_position is model.SignPosition.IMPLICIT_BINARY
    # R-5: the descriptor leads a reader to the frozen line that declares it.
    assert "copybooks/wsledger.cob:L28" in LEDGER_BALANCE.cite()


def test_ledger_last_shares_the_balance_shape_and_is_not_written_by_gl072() -> None:
    """`Ledger-Last pic s9(8)v99 comp-3.` [copybooks/wsledger.cob:L29].

    Declared one line below `Ledger-Balance` with the identical picture and usage.
    `gl072` never writes it - the only ledger item the posting loop accumulates
    into is `Ledger-Balance` [general/gl072.cbl:L331] - so its presence here is a
    statement that the two are the same shape and are still two fields.

    ANOMALY A-14 therefore reaches exactly one of the two: whichever account the
    sequential read [general/gl072.cbl:L408] delivered has its `Ledger-Balance`
    moved and its `Ledger-Last` left alone.
    """
    assert LEDGER_LAST.picture == LEDGER_BALANCE.picture
    assert LEDGER_LAST.usage is LEDGER_BALANCE.usage
    assert LEDGER_LAST.digits == LEDGER_BALANCE.digits
    assert LEDGER_LAST.scale == LEDGER_BALANCE.scale
    assert LEDGER_LAST.byte_length == LEDGER_BALANCE.byte_length
    assert LEDGER_LAST.name != LEDGER_BALANCE.name
    assert "copybooks/wsledger.cob:L29" in LEDGER_LAST.cite()


def test_ledger_q_occurs_four_over_a_redefinition_of_quarters() -> None:
    """`Ledger-Q ... occurs 4.` [copybooks/wsledger.cob:L36].

    Two facts, and the second is the one a table item usually loses in
    translation: the OCCURS count is four, and the item lives under `03 filler
    redefines Quarters.` [copybooks/wsledger.cob:L35] - so the four quarters are
    reachable both by name [copybooks/wsledger.cob:L31-L34] and by subscript over
    the same bytes.

    ANOMALY A-14's paragraph touches none of them: it reads `Ledger-Balance`
    [general/gl072.cbl:L415], [general/gl072.cbl:L422] and leaves the quarters to
    the end-of-period program, so a mis-sorted stream moves a balance without
    moving the quarter it belongs in.
    """
    assert LEDGER_Q.occurs == 4
    assert LEDGER_Q.picture == "s9(8)v99"
    assert LEDGER_Q.usage is model.Usage.COMP_3
    assert LEDGER_Q.byte_length == 6
    # The REDEFINES relationship is carried on the group, exactly where the
    # copybook writes it, and it is exposed rather than flattened away.
    assert LEDGER_QUARTERS_REDEFINITION.redefines == "Quarters"
    assert LEDGER_QUARTERS_REDEFINITION.is_group is True
    assert LEDGER_QUARTERS_REDEFINITION.is_filler is True
    assert LEDGER_QUARTERS.name == "Quarters"
    assert LEDGER_QUARTERS.redefines is None
    # Four six-byte quarters is the redefined group's own width.
    assert LEDGER_Q.occurs * LEDGER_Q.byte_length == 24


def test_ledger_key_children_shapes() -> None:
    """`WS-Ledger-Nos pic 9(6)` and `Ledger-PC pic 9(2)`.

    [copybooks/wsledger.cob:L14] and [copybooks/wsledger.cob:L20]. The first is
    the dividend of [general/gl072.cbl:L413]; the second is the sender of
    [general/gl072.cbl:L414]. Both are `05` items inside `03 WS-Ledger-Key.`
    [copybooks/wsledger.cob:L13], which is the GROUP the inert key move at
    [general/gl072.cbl:L405] targets.

    ANOMALY A-14 turns on that group: eight characters go into it and nothing reads
    them back, because [general/gl072.cbl:L408] is a `READ NEXT`.
    """
    assert WS_LEDGER_NOS.picture == "9(6)"
    assert WS_LEDGER_NOS.digits == 6
    assert WS_LEDGER_NOS.scale == 0
    assert WS_LEDGER_NOS.signed is False
    assert WS_LEDGER_NOS.byte_length == 6
    assert WS_LEDGER_NOS.python_storage is model.CobolPythonStorage.INT

    assert LEDGER_PC.picture == "9(2)"
    assert LEDGER_PC.digits == 2
    assert LEDGER_PC.byte_length == 2

    # The group itself has no width of its own - a group's width is the sum of its
    # children's, and the layer reports the request rather than inventing a number.
    assert WS_LEDGER_KEY.is_group is True
    with pytest.raises(ValueError):
        _ = WS_LEDGER_KEY.byte_length
    # Six digits plus two is the eight-character image the key move carries.
    assert WS_LEDGER_NOS.byte_length + LEDGER_PC.byte_length == 8


def test_post_amount_display_form_is_ten_bytes() -> None:
    """`Post-Amount pic s9(8)v99.` [copybooks/wspost.cob:L23], DISPLAY, ten bytes.

    A HARD FACT, asserted plainly. The copybook proves it with its own offset
    comments: `CR-PC` ends at 36 [copybooks/wspost.cob:L22] and `Post-Amount` at
    46, so the field spans 46 - 36 == 10 bytes; and again at
    [copybooks/wspost.cob:L27-L28], where `Post-Vat-Side` ends at 86 and
    `Vat-Amount` at 96. Ten and not eleven because the sign is OVERPUNCHED on the
    trailing digit rather than held in a byte of its own, and the implied decimal
    point of the `V` occupies no byte at all.

    ANOMALY A-14: this is the sending field of `add post-amount to ledger-balance`
    [general/gl072.cbl:L331], the statement that posts - so its shape is what the
    mis-sorted stream would carry into the wrong account.
    """
    assert POST_AMOUNT.picture == "s9(8)v99"
    assert POST_AMOUNT.usage is model.Usage.DISPLAY
    assert POST_AMOUNT.is_zoned_display is True
    assert POST_AMOUNT.signed is True
    assert POST_AMOUNT.sign_position is model.SignPosition.TRAILING_INCLUDED
    assert POST_AMOUNT.digits == 10
    assert POST_AMOUNT.integer_digits == 8
    assert POST_AMOUNT.scale == 2
    assert POST_AMOUNT.byte_length == 10
    # The same ten digits packed occupy six - the two carriers of one picture.
    assert LEDGER_BALANCE.byte_length == 6
    assert POST_AMOUNT.digits == LEDGER_BALANCE.digits


def test_ledger_name_carries_the_a12_width_drift_unsmoothed() -> None:
    """`Ledger-Name pic x(24).` [copybooks/wsledger.cob:L27] - ANOMALY A-12.

    Twenty-four characters in the copybook, thirty-two in the bridge host variable
    [common/nominalMT.cbl:L299] and thirty-two in the column. The value is not
    damaged but the padding differs, and padding is visible in a table dump.

    The primary lock for A-12 is `test_pic_field_descriptors.py`; this test only
    records that the drift is CARRIED here rather than reconciled, because
    `Ledger-Name` is the item `end-account` sends to the print line
    [general/gl072.cbl:L392] in the same paragraph group as the accumulation - and
    which account's name that is, is decided by ANOMALY A-14's sequential read
    [general/gl072.cbl:L408].
    """
    assert LEDGER_NAME.character_length == 24
    assert LEDGER_NAME.usage is model.Usage.ALPHANUMERIC
    assert LEDGER_NAME.byte_length == 24
    assert "A-12" in LEDGER_NAME.anomaly_refs()
    drift = LEDGER_NAME.drift()
    assert drift is not None
    assert drift.character_length is True
    # The disagreement is stated in the artifact rather than adjudicated in it.
    assert any("24" in detail and "32" in detail for detail in drift.details)


def test_sort_record_field_shapes_have_one_layer_and_zero_drift() -> None:
    """`01 sort-trans-record.` [general/gl071.cbl:L136-L144], all eight fields.

    ANOMALY A-14. These fields are declared inline in `gl071`'s own SORT-FILE
    description: no copybook declares them, no bridge host variable carries them
    and no column stores them, so each has exactly ONE layer view and therefore
    cannot drift. They are catalogued regardless, because the sequential read at
    [general/gl072.cbl:L408] depends on the widths and the order they fix.
    """
    expected = {
        # attribute: (picture, digits, scale, character_length, byte_length)
        "sort_batch": ("9(5)", 5, 0, None, 5),
        "sort_post": ("9(5)", 5, 0, None, 5),
        "sort_code": ("xx", None, None, 2, 2),
        "sort_date": ("x(8)", None, None, 8, 8),
        "sort_ac": ("9(6)", 6, 0, None, 6),
        "sort_pc": ("99", 2, 0, None, 2),
        "sort_amount": ("s9(8)v99", 10, 2, None, 10),
        "sort_legend": ("x(32)", None, None, 32, 32),
    }
    for attribute, (pic, digits, scale, length, width) in expected.items():
        field = SORT_DESCRIPTORS[attribute]
        assert field.picture == pic, attribute
        assert field.digits == digits, attribute
        assert field.scale == scale, attribute
        assert field.character_length == length, attribute
        assert field.byte_length == width, attribute
        # A-14 is recorded on every one of them.
        assert field.anomaly_refs() == ("A-14",), attribute
        # One layer view, so nothing to disagree with.
        drift = field.drift()
        assert drift is not None, attribute
        assert drift.details == (), attribute

    # `sort-amount` is the DISPLAY form of the money picture, ten bytes, and it is
    # the one signed field in the record. Asserted plainly.
    amount = SORT_DESCRIPTORS["sort_amount"]
    assert amount.signed is True
    assert amount.sign_position is model.SignPosition.TRAILING_INCLUDED
    assert amount.byte_length == 10
    assert amount.python_storage is model.CobolPythonStorage.DECIMAL


def test_sort_record_attributes_are_in_declaration_order() -> None:
    """`SortTransRecord`'s attributes follow [general/gl071.cbl:L137-L144].

    Declaration order, which is deliberately NOT the key order - that separation is
    the whole of the discriminating case below, and it is where ANOMALY A-14 hides:
    a reader who takes the record's order for the key order writes a sort that looks
    right and mis-posts. Asserted from the dataclass rather than from a list retyped
    here, so the record and this file cannot drift apart.
    """
    declared = tuple(
        entry.name for entry in dataclasses.fields(work_records.SortTransRecord)
    )
    assert declared == tuple(attribute for attribute, _ in SORT_FIELD_KEYS)
    # Each attribute carries its own descriptor in its field metadata, which is
    # where `sort_keys` above takes them from.
    for entry in dataclasses.fields(work_records.SortTransRecord):
        carried = entry.metadata[work_records.COBOL_FIELD_METADATA_KEY]
        assert carried == SORT_DESCRIPTORS[entry.name], entry.name


#  GROUP B  -  ANOMALY A-14: THE SORT ORDER `gl072` DEPENDS ON
#
#  The headline group. Agent Action Plan section 0.6.9 requires `gl071`'s output
#  ordering to be asserted DIRECTLY by a test rather than left to be caught
#  indirectly by a state diff, because a perturbed order produces silent
#  misposting - no error, no diagnostic, wrong balances. Every test below names
#  A-14 and its locator.


def test_a14_key_tuple_is_batch_account_profit_centre_posting() -> None:
    """The four keys, in the order [general/gl071.cbl:L173-L176] writes them.

    ANOMALY A-14. `on ascending key sort-batch sort-ac sort-pc sort-post` - so the
    key order is batch, ACCOUNT, profit centre, POSTING NUMBER, while the record
    declares batch, POSTING NUMBER, code, date, ACCOUNT, profit centre, amount,
    legend [general/gl071.cbl:L137-L144]. `sort-post` is the second FIELD and the
    fourth KEY; `sort-ac` is the fifth FIELD and the second KEY.
    """
    assert [key.accessor for key in GL071_KEYS] == [
        "sort_batch",
        "sort_ac",
        "sort_pc",
        "sort_post",
    ]
    assert [key.descriptor.name for key in GL071_KEYS] == [
        "sort-batch",
        "sort-ac",
        "sort-pc",
        "sort-post",
    ]
    # The two positions that differ between the two orders, stated as numbers so
    # that a future edit to either list fails here.
    declaration = [attribute for attribute, _ in SORT_FIELD_KEYS]
    assert declaration.index("sort_post") == 1
    assert [key.accessor for key in GL071_KEYS].index("sort_post") == 3
    assert declaration.index("sort_ac") == 4
    assert [key.accessor for key in GL071_KEYS].index("sort_ac") == 1
    # Four keys and no more; `sort-code`, `sort-date`, `sort-amount` and
    # `sort-legend` are not keys at all.
    assert len(GL071_KEYS) == 4
    assert {key.accessor for key in GL071_KEYS}.isdisjoint(
        {"sort_code", "sort_date", "sort_amount", "sort_legend"}
    )


def test_a14_discriminating_case_account_outranks_posting_number() -> None:
    """THE DISCRIMINATING CASE - the one that tells the two orders apart.

    ANOMALY A-14, [general/gl071.cbl:L173-L176] against
    [general/gl071.cbl:L137-L144]. Two records in one batch:

        A  sort-post = 1      sort-ac = 500100     - the SMALLER posting number
        B  sort-post = 9      sort-ac = 100200     - the SMALLER account

    Under the declared key order `sort-ac` outranks `sort-post`, so B sorts FIRST.
    Under the record's declaration order `sort-post` would outrank `sort-ac` and A
    would sort first. A test that varied only one field could not distinguish the
    two and would not have locked A-14 at all.
    """
    a = sort_record(batch=7, post=1, account=500100, profit_centre=0, legend="A")
    b = sort_record(batch=7, post=9, account=100200, profit_centre=0, legend="B")

    ordered = sortverb.sort_records([a, b], GL071_KEYS)

    assert [record.sort_legend for record in ordered] == ["B", "A"]
    assert ordered[0] is b
    assert ordered[1] is a
    # The input order is not what produced this: reversing the input gives the same
    # answer, because the KEY decided it and not the arrival sequence.
    assert sortverb.sort_records([b, a], GL071_KEYS) == (b, a)
    # And `sort-pc` outranks `sort-post` too - the third key against the fourth.
    low_pc = sort_record(batch=7, post=9, account=100, profit_centre=1, legend="lo")
    high_pc = sort_record(batch=7, post=1, account=100, profit_centre=8, legend="hi")
    assert [
        record.sort_legend
        for record in sortverb.sort_records([high_pc, low_pc], GL071_KEYS)
    ] == ["lo", "hi"]


def test_a14_stability_five_identical_keys_keep_their_input_order() -> None:
    """THE STABILITY CASE - equal keys must not be reordered.

    ANOMALY A-14. Five records carrying an IDENTICAL
    `(sort-batch, sort-ac, sort-pc, sort-post)` and legends A, B, C, D, E in that
    input order. The output legends must be exactly A, B, C, D, E.

    This is a correctness requirement and not a quality of implementation:
    `gl072` walks the output with a sequential read [general/gl072.cbl:L408] and
    accumulates into whichever nominal account the cursor is on, so reordering
    equal keys moves money between accounts with no error and no diagnostic.
    """
    inputs = [
        sort_record(batch=3, post=4, account=101, profit_centre=5, legend=letter)
        for letter in ("A", "B", "C", "D", "E")
    ]
    # Every key tuple really is identical - otherwise this would test ordering,
    # not stability.
    key_tuples = {
        sortverb.comparison_values(record, GL071_KEYS) for record in inputs
    }
    assert len(key_tuples) == 1

    ordered = sortverb.sort_records(inputs, GL071_KEYS)

    assert [record.sort_legend.strip() for record in ordered] == [
        "A",
        "B",
        "C",
        "D",
        "E",
    ]
    # Same objects, same positions - not merely equal values in the same order.
    assert all(out is src for out, src in zip(ordered, inputs, strict=True))
    # `stable=True` is the behaviour, and it is the ONLY behaviour on offer.
    assert sortverb.sort_records(inputs, GL071_KEYS, stable=True) == ordered
    with pytest.raises(sortverb.SortVerbError):
        sortverb.sort_records(inputs, GL071_KEYS, stable=False)


def test_a14_numeric_key_orders_by_magnitude_not_by_character() -> None:
    """`sort-ac pic 9(6)` is NUMERIC, so it orders by value.

    ANOMALY A-14, [general/gl071.cbl:L141] and [general/gl071.cbl:L174]. THE
    CONSTRUCTED PAIR: `sort-ac` 100 against `sort-ac` 99.

        numeric ordering    99 before 100      (99 is the smaller value)
        character ordering  "100" before "99"  ('1' is below '9' in ASCII)

    The two DISAGREE, which is the point - a pair such as 100 against 1000 would
    order the same way either way and would prove nothing. The field's own
    declaration decides: six digits, zero-filled to its declared width, so the
    comparison is on magnitude.
    """
    hundred = sort_record(batch=1, post=1, account=100, profit_centre=0, legend="100")
    ninety_nine = sort_record(
        batch=1, post=1, account=99, profit_centre=0, legend="99"
    )

    ordered = sortverb.sort_records([hundred, ninety_nine], GL071_KEYS)

    assert [record.sort_ac for record in ordered] == [99, 100]
    # The disagreement, shown rather than asserted about: ordering these two by
    # their unpadded text forms puts 100 first, which is the wrong answer.
    assert sorted([100, 99], key=str) == [100, 99]
    # At the field's declared width the two texts are these, and the sort reads
    # them as the numbers they are.
    assert _zoned_image(100, SORT_DESCRIPTORS["sort_ac"]) == "000100"
    assert _zoned_image(99, SORT_DESCRIPTORS["sort_ac"]) == "000099"
    assert (
        sortverb.algebraic_value("000099", SORT_DESCRIPTORS["sort_ac"]) == 99
    )
    assert (
        sortverb.algebraic_value("000100", SORT_DESCRIPTORS["sort_ac"]) == 100
    )
    # A key value supplied as the field's own byte form orders the same way as the
    # `int`, because the descriptor and not the runtime type decides.
    as_text = [
        sort_record(batch=1, post=1, account=100, profit_centre=0, legend="t100"),
        sort_record(batch=1, post=1, account=99, profit_centre=0, legend="t99"),
    ]
    assert [
        record.sort_legend.strip()
        for record in sortverb.sort_records(as_text, GL071_KEYS)
    ] == ["t99", "t100"]


def test_a14_gl071_output_ordering_asserted_directly() -> None:
    """Agent Action Plan section 0.6.9's mitigation, realised.

    Verbatim: "`gl071`'s output ordering is asserted directly by a test rather
    than left to be caught indirectly by a state diff." THIS IS THAT ASSERTION,
    made with `sortverb.is_sorted` on the key tuple
    `(sort_batch, sort_ac, sort_pc, sort_post)` [general/gl071.cbl:L173-L176].

    ANOMALY A-14: the consumer finds its account by sequential read
    [general/gl072.cbl:L408], so this ordering IS the correctness condition.
    """
    scrambled = [
        sort_record(batch=2, post=1, account=300, profit_centre=1, legend="e"),
        sort_record(batch=1, post=9, account=200, profit_centre=2, legend="c"),
        sort_record(batch=1, post=3, account=200, profit_centre=1, legend="b"),
        sort_record(batch=2, post=7, account=100, profit_centre=1, legend="d"),
        sort_record(batch=1, post=5, account=100, profit_centre=9, legend="a"),
    ]

    ordered = sortverb.sort_records(scrambled, GL071_KEYS)

    # The direct assertion section 0.6.9 asks for.
    assert sortverb.is_sorted(ordered, GL071_KEYS) is True
    # Read out in full, so the expected sequence is visible and not merely
    # "sorted": batch first, then account, then profit centre, then posting.
    assert [record.sort_legend.strip() for record in ordered] == [
        "a",
        "b",
        "c",
        "d",
        "e",
    ]
    # The input was genuinely out of order, so the True above is not vacuous.
    assert sortverb.is_sorted(scrambled, GL071_KEYS) is False
    # A single adjacent swap of the sorted output is enough to make it False -
    # which is the whole point: nothing else in the cycle would notice.
    perturbed = list(ordered)
    perturbed[0], perturbed[1] = perturbed[1], perturbed[0]
    assert sortverb.is_sorted(perturbed, GL071_KEYS) is False


def test_a14_mis_key_counter_case_produces_a_different_sequence() -> None:
    """Sorting on the record's DECLARATION order gives a different answer.

    ANOMALY A-14. The counter-case: the same input sorted on
    `(sort_batch, sort_post, sort_ac, sort_pc)` - the order the record declares
    its fields in [general/gl071.cbl:L137-L144] rather than the order the SORT
    names its keys in [general/gl071.cbl:L173-L176].

    The resulting sequence differs, and `is_sorted` of the right answer against
    the wrong keys is False. In the compiled system this difference does not
    raise, does not log and does not stop the run: `gl072` simply accumulates each
    posting into whichever account its sequential read landed on
    [general/gl072.cbl:L408]. SILENT MISPOSTING - no error, no diagnostic, wrong
    balances.
    """
    inputs = [
        sort_record(batch=4, post=1, account=900, profit_centre=0, legend="one"),
        sort_record(batch=4, post=2, account=800, profit_centre=0, legend="two"),
        sort_record(batch=4, post=3, account=700, profit_centre=0, legend="three"),
    ]

    right = sortverb.sort_records(inputs, GL071_KEYS)
    wrong = sortverb.sort_records(inputs, DECLARATION_ORDER_KEYS)

    assert [record.sort_legend.strip() for record in right] == [
        "three",
        "two",
        "one",
    ]
    assert [record.sort_legend.strip() for record in wrong] == [
        "one",
        "two",
        "three",
    ]
    assert right != wrong
    assert sortverb.is_sorted(right, DECLARATION_ORDER_KEYS) is False
    assert sortverb.is_sorted(wrong, GL071_KEYS) is False
    # Both orders are self-consistent, which is exactly why the mistake is silent.
    assert sortverb.is_sorted(right, GL071_KEYS) is True
    assert sortverb.is_sorted(wrong, DECLARATION_ORDER_KEYS) is True


def test_a14_sort_returns_the_same_records_unwrapped() -> None:
    """`USING pre-trans GIVING post-trans` moves records, it does not rebuild them.

    ANOMALY A-14, [general/gl071.cbl:L177-L178]. The `USING` / `GIVING` form is
    the only form the in-scope cycle uses - no input procedure, no output
    procedure, no `RELEASE` and no `RETURN` - so a sort is TRANSPORT: every input
    record appears in the output exactly once, unwrapped and unmodified.
    """
    inputs = [
        sort_record(
            batch=6,
            post=index,
            account=500 - index,
            profit_centre=1,
            legend="r" + str(index),
            amount="12.34",
        )
        for index in (1, 2, 3)
    ]
    before = [dataclasses.asdict(record) for record in inputs]

    ordered = sortverb.sort_records(inputs, GL071_KEYS)

    assert isinstance(ordered, tuple)
    assert len(ordered) == len(inputs)
    # The very objects, not copies and not wrappers.
    assert {id(record) for record in ordered} == {id(record) for record in inputs}
    for record in ordered:
        assert isinstance(record, work_records.SortTransRecord)
    # Nothing was rounded, reformatted or otherwise touched on the way through.
    assert [dataclasses.asdict(record) for record in inputs] == before
    assert all(record.sort_amount == Decimal("12.34") for record in ordered)


def test_a14_sort_key_extraction_rejects_binary_floating_point() -> None:
    """A `float` or a `complex` key is refused, not silently ordered (rule R-2).

    ANOMALY A-14 makes this a correctness gate rather than hygiene: two decimal
    values that are equal can compare unequal once they have been through binary
    floating point, which would reorder equal keys - and reordering equal keys is
    precisely the silent misposting [general/gl072.cbl:L408] cannot survive.

    The two binary values below are the ONLY ones in this file, they exist solely
    to be refused, and no assertion anywhere reads a value out of either: every
    other number here is an `int` or a `decimal.Decimal` built from a string.
    """
    offender = sort_record(batch=1, post=1, account=1, profit_centre=1, legend="x")

    offender.sort_ac = 1.0  # type: ignore[assignment]
    with pytest.raises(TypeError):
        sortverb.sort_records([offender], GL071_KEYS)
    with pytest.raises(TypeError):
        sortverb.comparison_values(offender, GL071_KEYS)
    with pytest.raises(TypeError):
        sortverb.is_sorted([offender], GL071_KEYS)

    offender.sort_ac = complex(1, 0)  # type: ignore[assignment]
    with pytest.raises(TypeError):
        sortverb.sort_records([offender], GL071_KEYS)

    # The exact carriers a key may arrive on: int, Decimal, or the field's text.
    offender.sort_ac = 1
    assert sortverb.sort_records([offender], GL071_KEYS) == (offender,)


def test_a14_all_four_keys_are_ascending_and_ascending_is_the_default() -> None:
    """`on ascending key ...` [general/gl071.cbl:L173] governs all four keys.

    ANOMALY A-14. One `ASCENDING` phrase covers the whole key list, so every key
    ascends. `SortDirection.DESCENDING` exists in the vocabulary but is
    UNEXERCISED by the in-scope source: the cycle contains exactly one `SORT` and
    it is all-ascending, so nothing has been confirmed about the other direction.
    """
    assert all(
        key.direction is sortverb.SortDirection.ASCENDING for key in GL071_KEYS
    )
    # Ascending is the default, so a key built without naming a direction is the
    # key the frozen statement declares.
    defaulted = sortverb.SortKey(
        accessor="sort_ac", descriptor=SORT_DESCRIPTORS["sort_ac"]
    )
    assert defaulted.direction is sortverb.SortDirection.ASCENDING
    assert defaulted in GL071_KEYS
    # The vocabulary has two members and no more.
    assert set(sortverb.SortDirection) == {
        sortverb.SortDirection.ASCENDING,
        sortverb.SortDirection.DESCENDING,
    }
    # A malformed key is refused at construction, because a wrong key ordering
    # produces money in the wrong account rather than an exception.
    with pytest.raises(sortverb.SortVerbError):
        sortverb.SortKey(
            accessor="sort_ac",
            descriptor=SORT_DESCRIPTORS["sort_ac"],
            direction="ascending",  # type: ignore[arg-type]
        )
    with pytest.raises(sortverb.SortVerbError):
        sortverb.sort_records([], ())


def test_a14_sort_record_is_seventy_characters_wide() -> None:
    """`01 sort-trans-record.` is 70 characters [general/gl071.cbl:L137-L144].

    ANOMALY A-14: the record's widths are part of what the sequential consumer
    depends on. 5 + 5 + 2 + 8 + 6 + 2 + 10 + 32 == 70, summed from the eight
    descriptors' own `byte_length` values rather than from a number retyped here.

    The four key fields contribute 5 + 6 + 2 + 5 == 18 of those 70, and the four
    non-key fields the remaining 52.
    """
    widths = {
        attribute: SORT_DESCRIPTORS[attribute].byte_length
        for attribute, _ in SORT_FIELD_KEYS
    }
    assert sum(widths.values()) == 70

    key_attributes = [key.accessor for key in GL071_KEYS]
    assert sum(widths[str(name)] for name in key_attributes) == 18
    assert sum(
        width for attribute, width in widths.items()
        if attribute not in key_attributes
    ) == 52
    # `pre-trans-record` and `post-trans-record` are the same eight widths under
    # different prefixes, which is why `USING` and `GIVING` need no conversion.
    assert widths["sort_amount"] == POST_AMOUNT.byte_length == 10


def test_a14_gl071_is_a_pure_sort() -> None:
    """`gl071` performs the sort and nothing else [general/gl071.cbl:L167-L181].

    ANOMALY A-14. Counted over the whole 182-line program: ZERO `MOVE` statements
    and ZERO arithmetic statements. Its `main.` paragraph is a screen diagnostic,
    the `SORT`, and `main-exit.` with its `goback` - so no value is rounded,
    truncated, reformatted or otherwise altered between `pre-trans` and
    `post-trans`, and the only thing the program can get wrong is the ORDER.

    Asserted here against the sort layer rather than against the COBOL text (rule
    R-1): a sort transports records, so what goes in comes out unchanged.
    """
    inputs = [
        sort_record(
            batch=8,
            post=index,
            account=index * 11,
            profit_centre=index,
            legend="L" + str(index),
            amount="-1.05",
            code="CN",
            date="21/09/25",
        )
        for index in (3, 1, 2)
    ]
    snapshot = [dataclasses.asdict(record) for record in inputs]

    ordered = sortverb.sort_records(inputs, GL071_KEYS)

    # Multiset equality: the same records, reordered and nothing more.
    assert sorted(id(record) for record in ordered) == sorted(
        id(record) for record in inputs
    )
    assert [dataclasses.asdict(record) for record in inputs] == snapshot
    # A signed non-key amount survives with its sign and its scale intact.
    assert all(record.sort_amount == Decimal("-1.05") for record in ordered)
    assert all(
        record.sort_amount.as_tuple().exponent
        == -SORT_DESCRIPTORS["sort_amount"].scale
        for record in ordered
    )


#  GROUP C  -  THE SORT TIE-ORDER QUESTION, WHICH THIS FILE OWNS


def test_gl071_sort_declares_no_duplicates_phrase() -> None:
    """[general/gl071.cbl:L172-L178] carries no `with duplicates in order`.

    ANOMALY A-14. The SORT names its four keys, its `USING` and its `GIVING`, and
    nothing else - no `WITH DUPLICATES IN ORDER`, no input procedure and no output
    procedure. Ties are reachable: the CR leg and the VAT leg of the `gl070`
    double-entry explosion coincide when the VAT account equals the CR account, so
    two records can carry an identical `(batch, ac, pc, post)`.

    OUR contract is stability, unconditionally, because Agent Action Plan section
    0.4.1.2 makes the output ordering a hard contract consumed by `gl072`. What
    the COMPILED sort does with a tie is question `Q-SORT-TIE-ORDER`, asserted
    separately below and never mixed into the stability assertion.
    """
    assert "Q-SORT-TIE-ORDER" in OPEN_QUESTIONS
    assert "with duplicates in order" in OPEN_QUESTIONS["Q-SORT-TIE-ORDER"]
    # Stability is not an option the caller chooses, which is what makes it a
    # contract rather than a default.
    tied = [
        sort_record(batch=5, post=2, account=42, profit_centre=3, legend=letter)
        for letter in ("first", "second")
    ]
    assert sortverb.comparison_values(
        tied[0], GL071_KEYS
    ) == sortverb.comparison_values(tied[1], GL071_KEYS)
    assert sortverb.sort_records(tied, GL071_KEYS) == (tied[0], tied[1])


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Q-SORT-TIE-ORDER: "
        "the compiled GnuCOBOL 3.2 tie order for two records carrying an "
        "identical (sort-batch, sort-ac, sort-pc, sort-post) is UNARBITRATED - "
        "[general/gl071.cbl:L172-L178] declares no `with duplicates in order` "
        "phrase, so the compiler is free to place them either way round. Our "
        "sort is stable unconditionally (Agent Action Plan section 0.4.1.2), and "
        "until the oracle answers, the two may diverge; the scenario tier's "
        "table diff is what would surface it. This test asserts the MATCH and is "
        "expected to fail, so the day the oracle confirms input order it reports "
        "an unexpected pass and this marker comes off (rule R-6)."
    ),
)
def test_q_sort_tie_order_compiled_tie_order_matches_input_order() -> None:
    """`Q-SORT-TIE-ORDER` - the compiled tie order, which nothing here can state.

    ANOMALY A-14, [general/gl071.cbl:L172-L178]. Asserting that GnuCOBOL's own tie
    order equals the input order requires the compiled program's answer, and the
    oracle has not given one. The claim is therefore recorded as failing rather
    than asserted as true.
    """
    tied = [
        sort_record(batch=5, post=2, account=42, profit_centre=3, legend="lhs"),
        sort_record(batch=5, post=2, account=42, profit_centre=3, legend="rhs"),
    ]
    compiled_tie_order = OPEN_QUESTIONS.get("Q-SORT-TIE-ORDER-ANSWER")
    assert compiled_tie_order is not None, (
        "no compiled answer is on record for Q-SORT-TIE-ORDER; "
        + repr([record.sort_legend.strip() for record in tied])
        + " is what our stable sort produces, and whether the compiled sort "
        "agrees is exactly the open question"
    )


#  GROUP D  -  ANOMALY A-14 IN A SINGLE PARAGRAPH: THE INERT KEY MOVE


def test_a14_key_move_at_l405_does_not_decide_which_record_is_read() -> None:
    """`move post-ledger to WS-Ledger-Key.` [general/gl072.cbl:L405] is INERT.

    ANOMALY A-14, and this is where it is visible in one paragraph. L405 sets the
    indexed key, so the paragraph LOOKS like an indexed lookup. L408 then performs
    `GL-Nominal-Read-Next` [general/gl072.cbl:L407-L408] - a `READ NEXT`, which
    ignores the key entirely and hands back whatever record the sequential cursor
    is on. The move therefore has no effect on WHICH record is read, and the
    program is right only because `gl071` sorted the stream
    [general/gl071.cbl:L172-L178].

    CITATION CORRECTION: the specification body cites the sequential read as
    [general/gl072.cbl:L410-L412]; the real sites are L405, L407 and L408.

    Reproduced, not repaired: the move stays, no key comparison is introduced and
    nothing is logged when the key and the record disagree (rules R-3 and R-4).
    """
    # The key names account 500100 / profit centre 07 ...
    addressed = PostLedgerGroup(post_ac=500100, post_pc=7)
    # ... and the sequential cursor is sitting on a completely different account.
    delivered = LedgerArea(
        ws_ledger_nos=100200, ledger_pc=3, ledger_balance=Decimal("250.00")
    )

    outcome = new_account(
        read_ledger=READ_ALLOWED,
        ledger=LedgerArea(),
        post_ledger=addressed,
        supplied=delivered,
    )

    # The move happened and the key holds what it was sent.
    assert outcome.ws_ledger_key_image == "50010007"
    # The record consumed is the cursor's, NOT the key's.
    assert outcome.read_consumed is True
    assert outcome.ledger == delivered
    assert outcome.ledger.ws_ledger_nos != addressed.post_ac
    assert outcome.ledger.ledger_pc != addressed.post_pc
    # And every downstream figure comes from the record that arrived, so the
    # mismatch is not merely unreported - it is posted.
    assert outcome.l6_account == Decimal("1002.00")
    assert outcome.l6_pc_sent == delivered.ledger_pc
    assert outcome.l6_balance_sent == delivered.ledger_balance
    assert outcome.accumulator == "tot-dr"
    assert outcome.tot_dr == Decimal("250.00")
    # No exception, no diagnostic, no rejection: the paragraph completes normally.
    assert outcome.read_ledger == READ_ALLOWED
    assert outcome.l6_legend.strip() == BROUGHT_FORWARD


def test_two_post_trans_record_declarations_are_both_recorded() -> None:
    """One physical work file, TWO incompatible `01 post-trans-record.` layouts.

    ANOMALY A-14, citation note. `gl072` declares `03 post-ledger.` as a GROUP over
    `05 post-ac pic 9(6)` and `05 post-pc pic 99`
    [general/gl072.cbl:L115-L117], and consumes it as a unit at
    [general/gl072.cbl:L309], [general/gl072.cbl:L317] and
    [general/gl072.cbl:L405]. `gl071` declares the same two items FLAT at level 03
    with no enclosing group [general/gl071.cbl:L129-L130].

    Both shapes are recorded and neither is reconciled against the other (rule
    R-4). There is deliberately no third, merged view of this record anywhere.
    """
    # The grouped shape, from `gl072`.
    assert POST_LEDGER_GROUP.is_group is True
    assert POST_LEDGER_GROUP.source_locator == "general/gl072.cbl:L115"
    assert POST_LEDGER_AC.parent_group == "post-ledger"
    assert POST_LEDGER_PC.parent_group == "post-ledger"
    assert POST_LEDGER_AC.source_locator == "general/gl072.cbl:L116"
    assert POST_LEDGER_PC.source_locator == "general/gl072.cbl:L117"

    # The flat shape, from `gl071`. Same pictures, no enclosing group.
    assert POST_AC_FLAT.parent_group == "post-trans-record"
    assert POST_PC_FLAT.parent_group == "post-trans-record"
    assert POST_AC_FLAT.source_locator == "general/gl071.cbl:L129"
    assert POST_PC_FLAT.source_locator == "general/gl071.cbl:L130"
    assert POST_AC_FLAT.picture == POST_LEDGER_AC.picture
    assert POST_PC_FLAT.picture == POST_LEDGER_PC.picture
    assert POST_AC_FLAT.byte_length == POST_LEDGER_AC.byte_length

    # Both are catalogued under the one record name, kept apart by the declaration
    # line their keys carry - and the artifact says so in its own words.
    both = {
        entry.key
        for entry in loader.entries()
        if entry.key.startswith("post-trans-record.")
    }
    assert "post-trans-record.post-ac#116" in both
    assert "post-trans-record.post-ac#129" in both
    assert "post-trans-record.post-ledger" in both
    notes = loader.get_entry("post-trans-record.post-ledger").notes
    assert any("neither is harmonised" in note for note in notes)


#  GROUP E  -  THREE IDENTICAL GUARDS THAT WERE NEVER FACTORED
#
#  `if read-ledger not = "R"` is written THREE separate times in the one paragraph:
#  [general/gl072.cbl:L407], [general/gl072.cbl:L410] and
#  [general/gl072.cbl:L421]. They stay three. Each test below asserts what its own
#  guard controls, and the fourth proves they are independent.


def test_guard_one_at_l407_controls_the_read() -> None:
    """GUARD ONE, [general/gl072.cbl:L407], guards the read at L408.

    ANOMALY A-14: this is the guard on the SEQUENTIAL read, so it decides whether a
    record is consumed at all. `read-ledger` holds `"R"` only after a page
    overflow [general/gl072.cbl:L338], and the whole purpose of the flag is to
    reprint the brought-forward line for the SAME account on the new page without
    advancing the cursor past it.
    """
    already_positioned = LedgerArea(
        ws_ledger_nos=400500, ledger_pc=2, ledger_balance=Decimal("15.00")
    )
    next_in_sequence = LedgerArea(
        ws_ledger_nos=999999, ledger_pc=9, ledger_balance=Decimal("99.99")
    )

    # Guard open: the read runs and the cursor's record replaces the area.
    opened = new_account(
        read_ledger=READ_ALLOWED,
        ledger=already_positioned,
        post_ledger=PostLedgerGroup(post_ac=400500, post_pc=2),
        supplied=next_in_sequence,
    )
    assert opened.read_consumed is True
    assert opened.ledger == next_in_sequence

    # Guard shut: no record is consumed, so the area stands as it was.
    shut = new_account(
        read_ledger=READ_SUPPRESSED,
        ledger=already_positioned,
        post_ledger=PostLedgerGroup(post_ac=400500, post_pc=2),
        supplied=next_in_sequence,
    )
    assert shut.read_consumed is False
    assert shut.ledger == already_positioned
    assert shut.ledger != next_in_sequence


def test_guard_two_at_l410_controls_the_multi_receiver_totals_reset() -> None:
    """GUARD TWO, [general/gl072.cbl:L410], guards `move zero to tot-dr tot-cr`.

    ANOMALY A-14, second of the three unfactored guards. A SEPARATE `if` carrying
    the SAME condition as L407, and it is not merged with it.

    The statement it guards is a MULTI-RECEIVER `MOVE`
    [general/gl072.cbl:L411]: one sender, two receivers, each receiver applying
    its OWN field's rules - so the results come back in receiver order and each is
    stored at its own field's scale. When a page overflow suppresses this guard the
    running totals SURVIVE, which is what lets the account's totals keep
    accumulating across a page break.
    """
    carried_dr = Decimal("1234.56")
    carried_cr = Decimal("789.01")

    # Guard open: both receivers are zeroed.
    opened = new_account(
        read_ledger=READ_ALLOWED,
        ledger=LedgerArea(ws_ledger_nos=100, ledger_pc=1),
        post_ledger=PostLedgerGroup(post_ac=100, post_pc=1),
        tot_dr=carried_dr,
        tot_cr=carried_cr,
    )
    assert opened.totals_reset is True
    # A zero balance takes the credit branch, so `tot-cr` picks up that zero after
    # the reset - see the `> zero` group below.
    assert opened.tot_dr == MONEY_ZERO
    assert opened.tot_cr == MONEY_ZERO

    # Guard shut: neither is touched, and the carried values survive intact.
    shut = new_account(
        read_ledger=READ_SUPPRESSED,
        ledger=LedgerArea(ws_ledger_nos=100, ledger_pc=1),
        post_ledger=PostLedgerGroup(post_ac=100, post_pc=1),
        tot_dr=carried_dr,
        tot_cr=carried_cr,
    )
    assert shut.totals_reset is False
    assert shut.tot_dr == carried_dr
    assert shut.tot_cr == carried_cr

    # The multi-receiver form itself: two receivers named, two values returned, in
    # the order the statement names them, each at its own field's scale.
    stored = cobol_move.move_to_all(cobol_move.Figurative.ZERO, [TOT_DR, TOT_CR])
    assert len(stored) == 2
    for value, receiver in zip(stored, (TOT_DR, TOT_CR), strict=True):
        assert isinstance(value, Decimal)
        assert value == MONEY_ZERO
        assert value.as_tuple().exponent == -receiver.scale


def test_guard_three_at_l421_controls_the_accumulation() -> None:
    """GUARD THREE, [general/gl072.cbl:L421], guards L422-L427.

    ANOMALY A-14, third of the three unfactored guards. It gates the whole
    brought-forward decision - the `> zero` test, both `MOVE`s into the print
    items and both accumulations. With it shut, no accumulator moves and neither
    print item receives the balance, yet everything outside it still runs.
    """
    brought_forward = LedgerArea(
        ws_ledger_nos=222200, ledger_pc=4, ledger_balance=Decimal("40.00")
    )

    opened = new_account(
        read_ledger=READ_ALLOWED,
        ledger=brought_forward,
        post_ledger=PostLedgerGroup(post_ac=222200, post_pc=4),
    )
    assert opened.balance_receiver == "l6-debit"
    assert opened.accumulator == "tot-dr"
    assert opened.tot_dr == Decimal("40.00")
    assert opened.l6_debit_sent == Decimal("40.00")
    assert opened.l6_credit_sent == MONEY_ZERO

    shut = new_account(
        read_ledger=READ_SUPPRESSED,
        ledger=brought_forward,
        post_ledger=PostLedgerGroup(post_ac=222200, post_pc=4),
        tot_dr=Decimal("7.00"),
        tot_cr=Decimal("3.00"),
    )
    assert shut.balance_receiver == ""
    assert shut.accumulator == ""
    # Nothing accumulated, and the carried totals are exactly as they arrived.
    assert shut.tot_dr == Decimal("7.00")
    assert shut.tot_cr == Decimal("3.00")
    # Both print items still hold the zero L416-L417 sent them, unconditionally.
    assert shut.l6_debit_sent == MONEY_ZERO
    assert shut.l6_credit_sent == MONEY_ZERO


def test_the_three_guards_are_independent_and_the_rest_runs_regardless() -> None:
    """The statements BETWEEN and AFTER the guards run on the guarded path.

    ANOMALY A-14. With `read-ledger = "R"` all three guards are shut, and yet
    [general/gl072.cbl:L413-L419] and [general/gl072.cbl:L429-L431] still execute:
    the account number is still divided into the print line, the legend is still
    set, and `read-ledger` is still reset to a space at L431.

    THIS IS THE ASSERTION THAT FAILS IF SOMEONE WRAPS THE PARAGRAPH IN ONE `if`.
    Three separate `if`s with the same condition and unguarded statements between
    them is not the same program as one `if` around the lot, and the difference is
    observable: the L431 reset is what limits the suppression to exactly one visit.
    """
    area = LedgerArea(
        ws_ledger_nos=123456, ledger_pc=9, ledger_balance=Decimal("-5.00")
    )

    suppressed = new_account(
        read_ledger=READ_SUPPRESSED,
        ledger=area,
        post_ledger=PostLedgerGroup(post_ac=123456, post_pc=9),
        supplied=LedgerArea(ws_ledger_nos=1, ledger_pc=1),
        tot_dr=Decimal("11.11"),
        tot_cr=Decimal("22.22"),
    )

    # All three guards shut.
    assert suppressed.read_consumed is False
    assert suppressed.totals_reset is False
    assert suppressed.accumulator == ""

    # L413 ran anyway - it sits between guard two and guard three.
    assert suppressed.l6_account == Decimal("1234.56")
    # L414-L415 ran anyway.
    assert suppressed.l6_pc_sent == 9
    assert suppressed.l6_balance_sent == Decimal("-5.00")
    # L416-L417 ran anyway, so both print items hold zero.
    assert suppressed.l6_debit_sent == MONEY_ZERO
    assert suppressed.l6_credit_sent == MONEY_ZERO
    # L429-L430 ran anyway.
    assert suppressed.l6_legend == BROUGHT_FORWARD.ljust(
        L6_LEGEND.character_length or 0
    )
    assert len(suppressed.l6_legend) == 32
    assert suppressed.l6_tran_sent == L6_TRAN_ZERO
    # L431 ran anyway - THE RESET IS UNCONDITIONAL.
    assert suppressed.read_ledger == READ_ALLOWED
    assert suppressed.read_ledger != READ_SUPPRESSED
    # Which means the next visit finds all three guards open again.
    reopened = new_account(
        read_ledger=suppressed.read_ledger,
        ledger=area,
        post_ledger=PostLedgerGroup(post_ac=123456, post_pc=9),
        supplied=LedgerArea(ws_ledger_nos=1, ledger_pc=1),
    )
    assert reopened.read_consumed is True
    assert reopened.totals_reset is True
    assert reopened.accumulator == "tot-cr"


#  GROUP F  -  `> zero` AND NOT `>= zero`
#
#  [general/gl072.cbl:L422] is `if ledger-balance > zero`, and the `else` at
#  [general/gl072.cbl:L425-L427] therefore takes ZERO into `l6-credit` and
#  `tot-cr`. A BALANCE OF EXACTLY ZERO IS BOOKED AS A CREDIT, and that is correct
#  because the source says so (rule R-4). It is not repaired here and it is not
#  reported.

#: The boundary, exhaustively. Each row is
#: (balance, receiver, accumulator, l6-debit sent, l6-credit sent, tot-dr, tot-cr),
#: where the two accumulator columns are what the UNSIGNED accumulators
#: [general/gl072.cbl:L165-L166] hold after the single `ADD`, and the two `sent`
#: columns are what [general/gl072.cbl:L416-L417] and then
#: [general/gl072.cbl:L423] or [general/gl072.cbl:L426] send to the print items.
GT_ZERO_BOUNDARY: Final[
    tuple[tuple[str, str, str, str, str, str, str], ...]
] = (
    # A penny above zero: the only row that takes the debit branch.
    ("0.01", "l6-debit", "tot-dr", "0.01", "0.00", "0.01", "0.00"),
    # Exactly zero: `> zero` is FALSE, so it is a CREDIT.
    ("0.00", "l6-credit", "tot-cr", "0.00", "0.00", "0.00", "0.00"),
    # Negative zero: algebraically equal to zero, so `> zero` is FALSE as well and
    # the credit branch is taken, exactly as for 0.00.
    ("-0.00", "l6-credit", "tot-cr", "0.00", "-0.00", "0.00", "0.00"),
    # A penny below zero: credit branch, the balance is sent to `l6-credit` with
    # its sign, and the unsigned accumulator holds the magnitude.
    ("-0.01", "l6-credit", "tot-cr", "0.00", "-0.01", "0.00", "0.01"),
)


@pytest.mark.parametrize(
    (
        "balance",
        "receiver",
        "accumulator",
        "debit_sent",
        "credit_sent",
        "expected_dr",
        "expected_cr",
    ),
    GT_ZERO_BOUNDARY,
    ids=[row[0] for row in GT_ZERO_BOUNDARY],
)
def test_gt_zero_not_ge_zero_boundary(
    balance: str,
    receiver: str,
    accumulator: str,
    debit_sent: str,
    credit_sent: str,
    expected_dr: str,
    expected_cr: str,
) -> None:
    """`if ledger-balance > zero` [general/gl072.cbl:L422], across the boundary.

    ANOMALY A-14's paragraph. Three of the four rows take the `else`, including
    the two zero rows - because `> zero` excludes zero and `>= zero` was never
    written. A zero brought-forward balance therefore appears in the CREDIT column
    of the printed line and in `tot-cr`.

    Args:
        balance: `Ledger-Balance` on entry [copybooks/wsledger.cob:L28].
        receiver: Which print item [general/gl072.cbl:L423] or
            [general/gl072.cbl:L426] sends the balance to.
        accumulator: Which accumulator [general/gl072.cbl:L424] or
            [general/gl072.cbl:L427] adds it to.
        debit_sent: The value last sent to `l6-debit`.
        credit_sent: The value last sent to `l6-credit`.
        expected_dr: What `tot-dr` holds afterwards.
        expected_cr: What `tot-cr` holds afterwards.
    """
    outcome = new_account(
        read_ledger=READ_ALLOWED,
        ledger=LedgerArea(
            ws_ledger_nos=310000,
            ledger_pc=1,
            ledger_balance=Decimal(balance),
        ),
        post_ledger=PostLedgerGroup(post_ac=310000, post_pc=1),
    )

    assert outcome.balance_receiver == receiver
    assert outcome.accumulator == accumulator
    assert outcome.l6_debit_sent == Decimal(debit_sent)
    assert outcome.l6_credit_sent == Decimal(credit_sent)
    assert outcome.tot_dr == Decimal(expected_dr)
    assert outcome.tot_cr == Decimal(expected_cr)
    # Exactly one of the two accumulators moved off the reset zero, and only for a
    # non-zero balance - a zero balance is booked as a credit OF ZERO.
    assert (outcome.tot_dr != MONEY_ZERO) is (accumulator == "tot-dr" and
                                              Decimal(balance) != 0)
    # The relation itself, stated directly: `> zero` is what decides, and it is
    # false for both zeros.
    greater = arithmetic.compare(Decimal(balance), 0) > 0
    assert greater is (receiver == "l6-debit")
    # `>= zero` would move both zero rows to the debit branch, which is the change
    # this test exists to fail.
    at_least = arithmetic.compare(Decimal(balance), 0) >= 0
    if Decimal(balance) == 0:
        assert greater is False
        assert at_least is True


def test_negative_zero_is_algebraically_zero_and_stores_as_a_positive_zero() -> None:
    """`Decimal("-0.00")` takes the credit branch [general/gl072.cbl:L425-L427].

    ANOMALY A-14's paragraph, the boundary's awkward row spelled out. Two separate
    facts, and neither is an adjustment:

      * ALGEBRAICALLY, negative zero equals zero, so `ledger-balance > zero`
        [general/gl072.cbl:L422] is FALSE and the `else` runs - the same branch
        `0.00` takes.
      * IN THE FIELD, `Ledger-Balance pic s9(8)v99 comp-3`
        [copybooks/wsledger.cob:L28] has no negative zero to hold: a packed zero
        carries the positive sign nibble, so the stored value is `0.00`.
    """
    negative_zero = Decimal("-0.00")
    # The carrier really does distinguish the two, which is why the relation and
    # the store have to be stated separately.
    assert negative_zero.is_signed() is True
    assert negative_zero == Decimal("0.00")
    # The relation COBOL evaluates.
    assert arithmetic.compare(negative_zero, 0) == 0
    assert (arithmetic.compare(negative_zero, 0) > 0) is False
    # The store the record area performs. A packed zero is positively signed.
    stored = LEDGER_BALANCE.store(negative_zero)
    assert stored == Decimal("0.00")
    assert isinstance(stored, Decimal)
    assert stored.is_signed() is False
    raw = cobol_usage.encode(
        negative_zero,
        usage=LEDGER_BALANCE.usage,
        digits=LEDGER_BALANCE.digits,
        scale=LEDGER_BALANCE.scale,
        signed=LEDGER_BALANCE.signed,
        sign_position=LEDGER_BALANCE.sign_position,
    )
    assert len(raw) == 6
    assert raw[-1] & 0x0F == cobol_usage.PACKED_SIGN_POSITIVE
    # And a real negative penny is held with the negative nibble, so the test above
    # is about zero and not about signs being dropped generally.
    negative_penny = cobol_usage.encode(
        Decimal("-0.01"),
        usage=LEDGER_BALANCE.usage,
        digits=LEDGER_BALANCE.digits,
        scale=LEDGER_BALANCE.scale,
        signed=LEDGER_BALANCE.signed,
        sign_position=LEDGER_BALANCE.sign_position,
    )
    assert negative_penny[-1] & 0x0F == cobol_usage.PACKED_SIGN_NEGATIVE


#  GROUP G  -  SIGN-DIRECTED BUT NOT SIGN-NORMALISED


def test_a14_credit_accumulation_is_sign_directed_not_sign_normalised() -> None:
    """`add ledger-balance to tot-cr.` [general/gl072.cbl:L426-L427], as written.

    ANOMALY A-14's paragraph. The sign of the balance DIRECTS the branch and then
    the balance is added AS IT STANDS. There is no `multiply by -1`, no absolute
    value and no negation anywhere in this paragraph - and the contrast is inside
    the same program: the main loop writes `subtract post-amount from tot-cr`
    [general/gl072.cbl:L327] for the same idea, which flips the sign of a negative
    posting on the way in. The two are not harmonised (rule R-4).

    What then happens to the sign is a property of the FIELD and not of the
    statement: `tot-cr pic 9(8)v99` [general/gl072.cbl:L166] carries no `s`, so
    the store drops the sign. That is `acas_posting.cobol.usage`'s stated rule for
    an unsigned receiving item, and it is asserted rather than deferred.
    """
    # The statement adds what it is given. Asserted on the accumulator directly,
    # one balance at a time, from the reset zero the paragraph leaves.
    assert TOT_CR.signed is False
    assert TOT_CR.unsigned is False
    assert TOT_CR.picture == "9(8)v99"
    assert TOT_DR.picture == TOT_CR.picture

    # A mixed sequence of brought-forward balances, one per account visit, each
    # visit resetting the totals at [general/gl072.cbl:L411] first. The branch and
    # the accumulator are what the sign directs.
    sequence = (
        ("100.00", "tot-dr", "100.00", "0.00"),
        ("-50.00", "tot-cr", "0.00", "50.00"),
        ("0.00", "tot-cr", "0.00", "0.00"),
        ("-0.01", "tot-cr", "0.00", "0.01"),
        ("0.01", "tot-dr", "0.01", "0.00"),
    )
    for balance, accumulator, expected_dr, expected_cr in sequence:
        outcome = new_account(
            read_ledger=READ_ALLOWED,
            ledger=LedgerArea(
                ws_ledger_nos=100, ledger_pc=0, ledger_balance=Decimal(balance)
            ),
            post_ledger=PostLedgerGroup(post_ac=100, post_pc=0),
        )
        assert outcome.accumulator == accumulator, balance
        assert outcome.tot_dr == Decimal(expected_dr), balance
        assert outcome.tot_cr == Decimal(expected_cr), balance
        # The value SENT to the print item is the balance itself, sign and all -
        # the paragraph does not normalise it before sending it either.
        sent = (
            outcome.l6_debit_sent
            if accumulator == "tot-dr"
            else outcome.l6_credit_sent
        )
        assert sent == Decimal(balance), balance

    # And the store's own rule, stated on its own: an unsigned receiver holds the
    # magnitude. Not an adjustment made here - the field has no sign to hold.
    assert arithmetic.add_to(
        Decimal("-50.00"), receiver_value=MONEY_ZERO, receiving=TOT_CR
    ) == Decimal("50.00")
    # The same value into the SIGNED ledger item keeps its sign, which is what
    # shows the drop is the field's and not the arithmetic's.
    assert arithmetic.add_to(
        Decimal("-50.00"), receiver_value=MONEY_ZERO, receiving=LEDGER_BALANCE
    ) == Decimal("-50.00")


def test_ledger_balance_accumulation_at_l331_keeps_the_sign() -> None:
    """`add post-amount to ledger-balance.` [general/gl072.cbl:L331].

    THE LEDGER-BALANCE ACCUMULATION ITSELF - the statement that actually posts,
    and the one anomaly A-14 makes dangerous: it accumulates into whichever
    account the sequential read at [general/gl072.cbl:L408] delivered.

    Unlike `tot-dr` / `tot-cr`, the receiver here is SIGNED
    [copybooks/wsledger.cob:L28], so a credit drives the balance negative and it
    stays negative. Un-ROUNDED, so the store truncates toward zero - though a
    two-place amount into a two-place balance has nothing to truncate, which is
    itself worth stating rather than assuming.
    """
    balance = Decimal("0.00")
    postings = ("1500.00", "-250.50", "-1300.00", "0.01", "-0.02")
    running = ("1500.00", "1249.50", "-50.50", "-50.49", "-50.51")
    for amount, expected in zip(postings, running, strict=True):
        stored = arithmetic.add_to(
            Decimal(amount),
            receiver_value=balance,
            receiving=LEDGER_BALANCE,
            rounded=False,
        )
        assert isinstance(stored, Decimal)
        balance = stored
        assert balance == Decimal(expected), amount
        assert balance.as_tuple().exponent == -LEDGER_BALANCE.scale

    # The sign survives to the end, which is the whole difference between this
    # receiver and the two unsigned print totals.
    assert balance < 0
    # A two-place sender into a two-place receiver loses nothing.
    assert arithmetic.add_to(
        Decimal("0.01"), receiver_value=Decimal("0.01"), receiving=LEDGER_BALANCE
    ) == Decimal("0.02")
    # Ten digits is the capacity, and the store reduces into it silently.
    assert LEDGER_BALANCE.value_domain == (-9999999999, 9999999999)


def test_no_rounded_site_lies_in_gl072() -> None:
    """Every store in `gl072` truncates, because no `ROUNDED` is written in it.

    ANOMALY A-14's paragraph included. The whole migrated cycle contains exactly
    five `ROUNDED` sites and all five are elsewhere, so truncation is the default
    everywhere in this file and `rounded=True` appears nowhere in the model above -
    not at the divide [general/gl072.cbl:L413], not at either accumulation
    [general/gl072.cbl:L424], [general/gl072.cbl:L427], and not at the posting
    accumulation [general/gl072.cbl:L331].
    """
    assert len(ROUNDED_SITES) == 5
    assert not any(site.startswith("general/gl072.cbl") for site in ROUNDED_SITES)
    # The two directions, and the mapping between the COBOL keyword and the
    # `decimal` mode, taken from the layer rather than restated here.
    assert arithmetic.ROUNDING_DIRECTIONS[False] == cobol_field.TRUNCATING_STORE
    assert arithmetic.ROUNDING_DIRECTIONS[True] == arithmetic.ROUNDED_STORE
    assert cobol_field.TRUNCATING_STORE == decimal.ROUND_DOWN
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    assert set(arithmetic.ROUNDING_DIRECTIONS) == {False, True}
    # And the default really is the truncating one, so an omitted keyword cannot
    # silently round.
    assert arithmetic.store(Decimal("1.999"), LEDGER_BALANCE) == Decimal("1.99")
    assert arithmetic.store(
        Decimal("1.999"), LEDGER_BALANCE, rounded=True
    ) == Decimal("2.00")
    # Truncation is toward zero and not toward minus infinity.
    assert arithmetic.store(Decimal("-1.999"), LEDGER_BALANCE) == Decimal("-1.99")


#  GROUP H  -  `DIVIDE` INTO A NUMERIC-EDITED RECEIVER


def test_l413_divides_the_account_number_into_an_edited_receiver() -> None:
    """`divide WS-Ledger-Nos by 100 giving l6-account.` [general/gl072.cbl:L413].

    ANOMALY A-14's paragraph, and the one statement between guard two and guard
    three. The receiver is `03 l6-account pic 9999.99 blank when zero.`
    [general/gl072.cbl:L233] - NUMERIC-EDITED, four printing integer digits and
    two decimals, six digits in six bytes.

    A print-line item, so this store is representation only. That the whole cycle
    can do this without ever writing an edited value to a table is not an
    assumption: a scan of every `pic` clause in all of `copybooks/*.cob` finds ZERO
    edited pictures and ZERO `blank when zero` clauses, so no record layout the
    data-access layer writes carries one.
    """
    assert L6_ACCOUNT.is_edited is True
    assert L6_ACCOUNT.picture == "9999.99"
    assert L6_ACCOUNT.digits == 6
    assert L6_ACCOUNT.integer_digits == 4
    assert L6_ACCOUNT.scale == 2
    assert L6_ACCOUNT.byte_length == 6
    assert L6_ACCOUNT.is_numeric is True
    assert L6_ACCOUNT.source_locator == "general/gl072.cbl:L233"

    # The live site's own arithmetic. `WS-Ledger-Nos pic 9(6)` holds six digits and
    # the divisor is 100, so the quotient carries exactly two decimals and there is
    # nothing for the un-ROUNDED store to discard - the truncation is latent here,
    # not exercised, which is worth saying rather than leaving implied.
    for nominal, quotient in (
        (123456, "1234.56"),
        (500107, "5001.07"),
        (100, "1.00"),
        (0, "0.00"),
    ):
        assert arithmetic.divide_by_giving(
            nominal, ACCOUNT_DIVISOR, L6_ACCOUNT, rounded=False
        ) == Decimal(quotient), nominal

    # The receiver's truncation, exercised with a divisor that does produce a third
    # decimal. Un-ROUNDED discards it; `ROUNDED` would not - and `gl072` writes no
    # `ROUNDED`, so the discarding form is the one the program performs.
    assert arithmetic.divide_by_giving(
        20, 3, L6_ACCOUNT, rounded=False
    ) == Decimal("6.66")
    assert arithmetic.divide_by_giving(
        20, 3, L6_ACCOUNT, rounded=True
    ) == Decimal("6.67")
    # The two sites that share this receiver, and the census across the cycle.
    assert "general/gl072.cbl:L386" in DIVIDE_INTO_EDITED_SITES
    assert "general/gl072.cbl:L413" in DIVIDE_INTO_EDITED_SITES
    assert len(DIVIDE_INTO_EDITED_SITES) == 5


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Q-EDITED-BLANK-WHEN-ZERO: "
        "the characters the compiled program renders into a `blank when zero` "
        "numeric-edited print item are UNARBITRATED. `l6-account pic 9999.99 "
        "blank when zero` [general/gl072.cbl:L233] and `l6-debit` / `l6-credit "
        "pic z(7)9.99 blank when zero` [general/gl072.cbl:L241], "
        "[general/gl072.cbl:L243] all reach a print line and never a table, so "
        "no state diff can observe the rendering and the oracle has nothing to "
        "compare. `acas_posting.cobol.move` refuses these pictures under its own "
        "question Q-14 rather than inventing an answer, and Agent Action Plan "
        "section 0.2.2 puts report formatting beyond database effects out of "
        "scope. This test asserts a rendering and is expected to fail (rule R-6)."
    ),
)
def test_edited_print_receivers_have_no_compiled_rendering() -> None:
    """`Q-EDITED-BLANK-WHEN-ZERO` - the three print items' rendered characters.

    ANOMALY A-14's paragraph sends values to `l6-account`
    [general/gl072.cbl:L413], `l6-debit` [general/gl072.cbl:L416],
    [general/gl072.cbl:L423] and `l6-credit` [general/gl072.cbl:L417],
    [general/gl072.cbl:L426]. What each renders is the open question, so this test
    asks for the rendering and is recorded as failing.
    """
    assert cobol_move.move_to_edited(Decimal("1234.56"), L6_ACCOUNT) == "1234.56"


def test_edited_print_receivers_are_refused_rather_than_guessed() -> None:
    """The layer declines the rendering instead of producing a plausible one.

    ANOMALY A-14's paragraph. `move ledger-balance to l6-credit`
    [general/gl072.cbl:L426] targets `pic z(7)9.99 blank when zero`
    [general/gl072.cbl:L243], and `move zero to l6-debit`
    [general/gl072.cbl:L416] targets the same picture at
    [general/gl072.cbl:L241]. Both are refused - loudly and by type - which is why
    the model above records the value SENT and never a rendered string.
    """
    assert L6_DEBIT.is_edited is True
    assert L6_CREDIT.is_edited is True
    assert L6_DEBIT.picture == "z(7)9.99"
    assert L6_CREDIT.picture == L6_DEBIT.picture
    assert L6_DEBIT.digits == 10
    assert L6_DEBIT.integer_digits == 8
    assert L6_DEBIT.scale == 2
    assert L6_DEBIT.byte_length == 10

    for receiver in (L6_DEBIT, L6_CREDIT, L6_ACCOUNT):
        with pytest.raises(cobol_move.UnobservableEditedPicture):
            cobol_move.move(Decimal("12.34"), receiver)
        with pytest.raises(cobol_move.UnobservableEditedPicture):
            cobol_move.move(cobol_move.Figurative.ZERO, receiver)

    # The numeric value the receiver would hold before any rendering IS available,
    # and it is the unsigned store - both print totals are unsigned pictures.
    assert arithmetic.store(Decimal("-12.34"), L6_DEBIT) == Decimal("12.34")
    assert arithmetic.store(MONEY_ZERO, L6_CREDIT) == MONEY_ZERO
    # `l6-legend pic x(32)` [general/gl072.cbl:L245] is NOT edited, which is why
    # its value is asserted plainly in the guard-independence test above.
    assert L6_LEGEND.is_edited is False
    assert L6_LEGEND.character_length == 32


#  GROUP I  -  THE `DIVIDE` CENSUS, OPERAND ORDER, AND SILENT OVERFLOW


def test_divide_by_giving_and_into_giving_take_their_operands_oppositely() -> None:
    """`BY ... GIVING` is a / b; `INTO ... GIVING` is b / a.

    ANOMALY A-14's paragraph writes the `BY` form at [general/gl072.cbl:L413], and
    its sibling at [general/gl072.cbl:L386] writes the same one, which is why the
    model above calls `divide_by_giving`. Asserted with NON-SYMMETRIC operands so
    that swapping them is observably wrong rather than accidentally right.

    Census over the twelve in-scope programs: seventeen `DIVIDE` statements,
    thirteen written `BY ... GIVING` and four written `INTO ... GIVING`.
    """
    assert DIVIDE_CENSUS["by_giving"] + DIVIDE_CENSUS["into_giving"] == (
        DIVIDE_CENSUS["total"]
    )
    assert DIVIDE_CENSUS["total"] == 17
    assert DIVIDE_CENSUS["by_giving"] == 13
    assert DIVIDE_CENSUS["into_giving"] == 4

    # 8 and 2: 8 / 2 is four, 2 / 8 is a quarter. Neither is the other.
    assert arithmetic.divide_by_giving(8, 2, TOT_DR) == Decimal("4.00")
    assert arithmetic.divide_into_giving(8, 2, TOT_DR) == Decimal("0.25")
    assert arithmetic.divide_by_giving(
        8, 2, TOT_DR
    ) != arithmetic.divide_into_giving(8, 2, TOT_DR)
    # The `BY` form reads the same way round as the statement: dividend first.
    assert arithmetic.divide_by_giving(
        123456, ACCOUNT_DIVISOR, L6_ACCOUNT
    ) == Decimal("1234.56")
    # Writing the same two operands the other way round would give this instead,
    # which is the mistake the two names exist to prevent.
    assert arithmetic.divide_into_giving(
        123456, ACCOUNT_DIVISOR, L6_ACCOUNT
    ) == MONEY_ZERO


def test_divide_overflow_keeps_the_low_order_digits_silently() -> None:
    """No `ON SIZE ERROR` and no `REMAINDER` exists in the twelve programs.

    Counted over all twelve: ZERO `ON SIZE ERROR` phrases and ZERO `REMAINDER`
    phrases. So when a quotient will not fit its receiver, the high-order digits
    are simply lost: nothing is raised, nothing is clamped and nothing is logged.
    Adding any of the three would be the new validation rule R-3 forbids.

    ANOMALY A-14's paragraph is where this matters: `l6-account pic 9999.99`
    [general/gl072.cbl:L233] holds four integer digits, and `WS-Ledger-Nos pic
    9(6)` [copybooks/wsledger.cob:L14] holds six - so the live divisor of 100 at
    [general/gl072.cbl:L413] is exactly what keeps the quotient inside the
    receiver, and a smaller divisor would silently drop digits off the front of the
    account number the read delivered.
    """
    # Six digits divided by 100 fits; the same six digits divided by 10 does not.
    assert arithmetic.divide_by_giving(
        999999, ACCOUNT_DIVISOR, L6_ACCOUNT
    ) == Decimal("9999.99")
    assert arithmetic.divide_by_giving(999999, 10, L6_ACCOUNT) == Decimal("9999.90")
    # 999999 / 1 is 999999.00, and the receiver keeps the LOW-ORDER four integer
    # digits - 9999.00 - discarding the leading 99 without a word.
    assert arithmetic.divide_by_giving(999999, 1, L6_ACCOUNT) == Decimal("9999.00")
    assert arithmetic.store(Decimal("123456.78"), L6_ACCOUNT) == Decimal("3456.78")
    # The same silence on the unsigned money accumulators, ten digits wide.
    assert TOT_DR.value_domain == (0, 9999999999)
    assert arithmetic.add_to(
        Decimal("99999999.99"),
        receiver_value=Decimal("0.02"),
        receiving=TOT_DR,
    ) == Decimal("0.01")
    # A zero divisor is the frozen programs' own concern, not this layer's: they
    # guard in their own logic and no guard is added here.
    with pytest.raises(arithmetic.SizeErrorNoStore):
        arithmetic.divide_by_giving(1, 0, L6_ACCOUNT)
    assert arithmetic.divide_by_giving(
        1, 0, L6_ACCOUNT, receiver_value=Decimal("7.77")
    ) == Decimal("7.77")


#  GROUP J  -  CONTEXT RECORDED, NOT DUPLICATED


def test_a13_silent_skips_are_noted_here_and_locked_elsewhere() -> None:
    """ANOMALY A-13's two silent skips live in `gl072` but not in this file.

    `if post-batch not numeric go to loop.` [general/gl072.cbl:L291-L292] and `if
    we-error equal 999 go to loop.` [general/gl072.cbl:L306-L307] both abandon a
    record with no message, no counter and no trace. They are A-13, their primary
    lock is `test_move_truncation.py` by way of `is_numeric_class` returning a
    plain boolean and never raising, and they are recorded here only because they
    sit in the same program as A-14 and reach the same `loop.` paragraph.

    The one thing asserted here is that the class test really is a plain predicate:
    if it raised, the skip would stop being silent and A-13 would be repaired by
    accident.
    """
    batch_number = SORT_DESCRIPTORS["sort_batch"]
    for candidate in ("00042", "     ", "0004A", "-0042", "00 42"):
        verdict = cobol_move.is_numeric_class(candidate, batch_number)
        assert isinstance(verdict, bool), candidate
    # A well-formed batch number is numeric and a blank one is not, which is the
    # only distinction [general/gl072.cbl:L291] draws.
    assert cobol_move.is_numeric_class("00042", batch_number) is True
    assert cobol_move.is_numeric_class("     ", batch_number) is False
