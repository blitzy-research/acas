"""The internal IRS posting record, from copybooks/irswspost.cob.

One dataclass, `PostingRecord`, mirroring the ten fields the COBOL record
`01  Posting-Record.` declares [copybooks/irswspost.cob:L8] field for
field, with nothing added and nothing repaired. It is the record the IRS
posting step fills and writes inside `Ledger-Postings-Add`
[irs/irs030.cbl:L1569-L1733]: that section walks the transfer file, posts
the debit, posts the credit, then writes one of these.

THE ENTITY SPINE
----------------
Obtained from the generated dictionary rather than restated by hand -
`loader.table_for("IRSPOSTING-REC")` returns all of it::

    entity facade   IRS posting
    handler         acasirsub4
    bridge          irspostingMT
    table           IRSPOSTING-REC, 13 columns, primary key KEY-4
    copybook        copybooks/irswspost.cob, 10 fields
    ordinal source  mysql/ACASDB.sql:L274

TEN FIELDS, THIRTEEN COLUMNS - AND THAT IS RIGHT
------------------------------------------------
The count a reader should be able to check for themselves::

     10   leaf fields declared at copybooks/irswspost.cob:L9-L18
    + 3   columns no copybook declares anywhere
    = 13  columns in IRSPOSTING-REC

`POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` have no counterpart in any
copybook. They exist because the bridge derives them from a date string
under a guard [common/irspostingMT.cbl:L982-L987], and they are declared
only in the bridge host-variable group
[common/irspostingMT.cbl:L177-L179] and in the frozen schema. This
module therefore declares TEN attributes and must never declare an
eleventh, twelfth or thirteenth; the block above the `post_date`
attribute records their absence in full so that the omission is visible
rather than accidental.

That gap is the reason this migration takes its field metadata from the
maintainer's one-way COBOL-to-MySQL bridge and not from the copybooks.
The preserved user requirement puts it directly - the bridge "defines the
... record-layout <-> table mapping - it is the data dictionary for this
migration" - and this table is the proof: a migration driven from the
copybooks alone would silently omit three columns of a posting table.

ANOMALY A-7 - THE GUARD IS THE ANOMALY
--------------------------------------
Recorded here, reproduced in `acas_posting/dal/acasirsub4_irs_posting.py`.

The bridge's load paragraph begins by zeroing its whole host-variable
group, `initialize TD-IRSPOSTING-REC.`
[common/irspostingMT.cbl:L966], then moves the ten record fields across
[common/irspostingMT.cbl:L967-L976]. Each date component is then moved
only if the two characters it comes from are numeric
[common/irspostingMT.cbl:L982-L987], taking positions 1-2, 4-5 and 7-8
of `Post-Date` by reference modification - so the year component reads
TWO digits, consistent with `Post-Date` being eight characters of
`DD/MM/YY` text and with the column being `POST4-YEAR tinyint(2)
unsigned`.

When a guard does not hold, the component keeps the zero the
`initialize` left while `POST4-DAT` still stores the raw eight
characters. The row is internally inconsistent, and it is reproduced that
way rather than repaired (R-4).

The maintainer's own note sits immediately above the guard and is the
evidence that it is deliberate and that the columns are an afterthought.
It is reproduced exactly as written, wide internal gap and all, which is
why the first of the three runs past this file's 79-column margin -
re-wrapping a quotation of frozen source would be the very tidying that
R-4 forbids [common/irspostingMT.cbl:L978-L980]::

    *> These added after new columns             created 31/12/16  - inhouse mysql & mariadb
    *>  and yes they all should be numeric as a date is present
    *>   but JIC (just in case).

THREE POSTING RECORDS, NEVER MERGED
-----------------------------------
`copybooks/wspost-irs.cob:L6-L7` warns about this in the maintainer's own
words - "This is NOT the same as the internal IRS posting file" - and
THIS module is the internal one it distinguishes itself from::

    records/gl_posting.py       WS-Posting-Record      GLPOSTING-REC  14
        copybooks/wspost.cob        acas006   glpostingMT
    records/spl_irs_posting.py  WS-IRS-Posting-Record  PSIRSPOST-REC  10
        copybooks/wspost-irs.cob    acas008   slpostingMT
    records/irs_posting.py      Posting-Record         IRSPOSTING-REC 13
        copybooks/irswspost.cob     acasirsub4 irspostingMT

Two structural differences from both siblings are preserved as declared:

* `Post-Key` is ONE flat `pic 9(5)` [copybooks/irswspost.cob:L9], where
  both siblings group two five-digit items - `WS-Post-Key` is `Batch` +
  `Post-Number` [copybooks/wspost.cob:L14-L16] and `WS-IRS-Post-Key` is
  `WS-IRS-Batch` + `WS-IRS-Post-Number`
  [copybooks/wspost-irs.cob:L14-L16]. No group is invented here and no
  batch component is added.
* This copybook's field names carry NO prefix at all, which is what
  forces qualified references once a program copies more than one
  posting layout - anomaly A-21, "field-name collisions across three
  posting copybooks force qualified references". `gl070` must write
  `move post-code in WS-Posting-Record to pre-code.`
  [general/gl070.cbl:L497] and `if vat-ac of WS-Posting-Record = zero`
  [general/gl070.cbl:L521], [general/gl070.cbl:L525]. Python's module
  namespace settles the collision for free, but the reason is recorded
  because the collision itself is not removed.

`irs030` copies this copybook with NO `replacing` clause
[irs/irs030.cbl:L288] while renaming both of its neighbours
[irs/irs030.cbl:L286], [irs/irs030.cbl:L287] - further evidence for
A-21, and the reason the class below keeps the copybook's own
undistinguished name.

THE SIGN CLAUSE - TWO SPELLINGS, HELD AS TWO
--------------------------------------------
Both money items are declared `pic s9(7)v99   sign is leading`
[copybooks/irswspost.cob:L14], [copybooks/irswspost.cob:L18]. There is no
`SEPARATE` keyword, so the sign is leading and INCLUDED in the high-order
digit byte: nine digits, two of them decimal, nine bytes.

The sibling `copybooks/wspost-irs.cob` writes the same idea WITHOUT the
word `is` - `sign leading` at L21 and L25 - and
`copybooks/wspost.cob` carries no sign clause on its amounts at all
(L23, L28), its header recording the record shrinking from 98 to 96
bytes "(leading sign removed)" [copybooks/wspost.cob:L6-L7]. Three
posting records, three sign treatments, kept as three.

`sign_clause_text` records the TEXT, so the descriptors of this module
report `"sign is leading"` and those of `spl_irs_posting` report
`"sign leading"`. The two spellings are never made to agree. A census
across `copybooks/` finds `sign leading` four times and `sign is
leading` twice, with no occurrence of `sign trailing`, `separate`,
`justified` or `blank when zero` anywhere - those two spellings are the
entire vocabulary in play.

BRIDGE DRIFT - RECORDED, NEVER APPLIED
--------------------------------------
This record is the folder's most heavily renamed. Every descriptor
below carries the COPYBOOK view of its field, and offers the
disagreement between the three layers unsettled through
`descriptor.drift()`; nothing here blends a layer, widens a field to a
host-variable or column width, or converts a storage class. That work
belongs to `acas_posting/dal/acasirsub4_irs_posting.py`, at the bridge
boundary where the COBOL does it.

Four kinds of drift are present, all left unsettled:

1. A systematic `4` infix at the bridge and the column -
   `POST4-CODE`, `POST4-DAT`, `POST4-DR`, `POST4-CR`, `POST4-AMOUNT`,
   `POST4-LEGEND`, `POST4-VAT-SIDE`, `VAT-AC-DEF4`, `VAT-AMOUNT4` - and
   one outright rename, `Post-Key` to `KEY-4`. The `4` is the handler
   number, `acasirsub4`. `Post-Date` to `POST4-DAT` also truncates the
   name.
2. Digit widening on five fields, and NOT in one direction: `Post-Key`,
   `Post-DR` and `Post-CR` go `9(5)` -> `9(08) COMP` ->
   `mediumint(5) unsigned`, and `Vat-AC-Def` goes `99` ->
   `9(03) COMP` -> `tinyint(2) unsigned`. In each case the host
   variable is wider than BOTH the copybook and the column - a
   three-layer drift that does not move monotonically.
3. Storage-class drift on both amounts: zoned `DISPLAY` with a leading
   sign, nine bytes, becomes `PIC S9(07)V9(02) COMP` at the bridge and
   `decimal(9,2)` in the column. Digits and scale survive; the leading
   sign disappears into a binary field.
4. The three bridge-only columns above.

WHY NO ATTRIBUTE IS EVER None
-----------------------------
Every one of the 13 columns is declared `NOT NULL`, and the reason is
the `initialize` at [common/irspostingMT.cbl:L966]: because each load
paragraph zeroes its host-variable group first, an unset field reaches
SQL as zero or space and never as NULL. So the defaults below are `0`,
`Decimal("0.00")` and spaces at the declared width - the Python layer
defaults rather than omits.

VERIFIED CITATION DISCREPANCIES
-------------------------------
Recorded for `docs/migration/traceability.md` to lift. Each was checked
against the frozen source rather than taken on trust:

* The second `sign is leading` field is at
  [copybooks/irswspost.cob:L18], not L19. L19 is the file's trailing
  `*>` comment and the file is 19 lines long. The Agent Action Plan
  cites L19 in both section 0.4.1.3 and section 0.6.1. The generated
  dictionary agrees with L18 independently: the `VAT-AMOUNT4` entry's
  copybook view carries `copybooks/irswspost.cob:L18`.
* Anomaly A-21's qualified references in `gl070` are at L497, L521 and
  L525. L510 - which the plan cites - reads `move post-cr to pre-ac.`
  and is NOT qualified. An exhaustive search of that program for a
  qualified reference to `WS-Posting-Record` returns exactly those
  three lines.
* `irs030`'s neighbouring renaming copies are at
  [irs/irs030.cbl:L416-L417] and [irs/irs030.cbl:L419-L423], one line
  later than the plan's L415-L416 and L418-L422. The fact they support
  - that L288 alone copies without `replacing` - is unaffected.
* The storage-class census below is NOT "all DISPLAY". Six numeric
  items report `Usage.DISPLAY` and the four `PIC X` items report
  `Usage.ALPHANUMERIC`, because the dictionary separates the two so
  that a carrier can be chosen without re-reading the picture. Both are
  display-class storage in COBOL's own terms. The substantive claim
  holds and is what matters: this copybook declares NO `COMP`, NO
  `COMP-3` and no binary usage anywhere - every `COMP` in the chain
  appears at the bridge.

OPEN QUESTIONS FOR THE COMPILED ORACLE (R-6)
--------------------------------------------
Neither is settled here. Both belong in
`docs/migration/ambiguity-resolutions.md`, decided by running the
compiled program:

(a) What a leading-sign zoned value becomes once it is moved into a
    signed binary host variable [common/irspostingMT.cbl:L182],
    [common/irspostingMT.cbl:L186] and then stored in a
    `decimal(9,2)` column. The conversion happens in the bridge's C
    interface and must be measured, not assumed.
(b) What a row looks like when a guard fails - `POST4-DAT` holding the
    raw eight characters beside three zero components.

WHAT THIS MODULE DOES NOT DO
----------------------------
It is a leaf. It imports `acas_posting.cobol.field` and
`acas_posting.dictionary.loader` and the standard library, and nothing
else - not the data-access layer, not `dates`, not `programs`, not a
sibling record module. Specifically:

* It does not declare, derive, expose or compute the three date
  components; `dal/acasirsub4_irs_posting.py` owns them.
* It does not read `Post-Date` apart. Those eight characters are text
  here; `acas_posting/dates.py` owns date conversion.
* It does not look `Vat-AC-Def` up. Those two digits index the IRS
  defaults table rather than naming an account - the posting step
  indexes entries 31 and 32 [irs/irs030.cbl:L1685-L1699] - and
  `records/irs_dflt.py` carries that table.
* It does not compute VAT. The two ROUNDED computes
  [irs/irs030.cbl:L1551], [irs/irs030.cbl:L1562] and the net-of-VAT
  subtraction [irs/irs030.cbl:L1565] belong to
  `programs/irs030_posting.py`.
* It does not store, pad, truncate or test a value.
  `acas_posting/cobol/move.py` and `acas_posting/cobol/arithmetic.py`
  own those, and each descriptor's own `store` method is the entry
  point they use.
* It declares no condition name. `Post-Vat-Side` is compared against a
  bare literal in the posting logic and this copybook gives it no
  `88`-level; none is invented, and predicates live in
  `acas_posting/cobol/condition_names.py`.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: list[str] = ["PostingRecord"]


# =============================================================================
#  THE DICTIONARY LOOKUP  (rule R-5 - derived, never transcribed)
# =============================================================================

# The table whose entries describe this record. The dictionary keys a
# column-mapped entry as `<TABLE-NAME>.<COLUMN-NAME>`, so the left side of
# every key below is this table name and NOT the copybook's own `01` name,
# `Posting-Record`. That distinction is what keeps this record and the
# similarly shaped PSIRSPOST-REC apart; keyed on the bare field name they
# would silently collapse into one [copybooks/wspost-irs.cob:L6-L7].
_TABLE: Final[str] = "IRSPOSTING-REC"


def _copybook_descriptors() -> tuple[FieldDescriptor, ...]:
    """Describe every field of this record that a copybook declares.

    Keys are read from the dictionary rather than written out here: the
    loader is asked for the table's entries and each entry supplies its
    own key. Nothing in this module guesses one, which matters because
    the bridge renames almost every column - `Post-Key` reaches the
    schema as `KEY-4`, `Post-Date` as `POST4-DAT`, `Vat-AC-Def` as
    `VAT-AC-DEF4`, `Vat-Amount` as `VAT-AMOUNT4`, and the rest gain a
    `4` infix - so a key typed from the copybook name would simply be
    wrong.

    `loader.entries_for_table` yields all 13 entries in the column
    ordinal order the frozen dump fixes, which puts `POST4-DAY`,
    `POST4-MONTH` and `POST4-YEAR` at positions four, five and six -
    interleaved into the middle of the list, not appended after it. The
    three are SKIPPED here, on the one test that identifies them without
    naming them: they have no copybook view. That is also the only
    honest test available, since a `FieldDescriptor` describes
    COBOL-side storage and those three have none - asking for one
    raises `BridgeOnlyFieldError`.

    Returns:
        The ten descriptors, in the order the dictionary yields them,
        which for this record is also copybook declaration order.
    """
    return tuple(
        FieldDescriptor.from_dictionary_key(entry.key)
        for entry in loader.entries_for_table(_TABLE)
        if entry.copybook is not None
    )


# The ten descriptors, in declaration order. A fixed tuple rather than a
# list, and built once at import from the loader's own lazily cached read,
# so two runs see identical state (R-6).
#
# Each member surfaces the dictionary's provenance primitives rather than
# reimplementing them:
#
#     descriptor.cite()          the compact three-locator string -
#                                copybook field, bridge host variable,
#                                MySQL column
#     descriptor.drift()         the disagreement between those three
#                                views, offered UNSETTLED
#     descriptor.anomaly_refs()  the anomaly register entries it belongs
#                                to
#     descriptor.store(value)    the store direction, owned by the
#                                arithmetic and move layers
FIELDS: Final[tuple[FieldDescriptor, ...]] = _copybook_descriptors()

_BY_COBOL_NAME: Final[dict[str, FieldDescriptor]] = {
    descriptor.name: descriptor for descriptor in FIELDS
}


def _blanks(cobol_name: str) -> str:
    """Return spaces at the declared width of one alphanumeric field.

    The width comes from the field's dictionary entry, so a change in the
    frozen copybook reaches this module through the regenerated artifact
    instead of through an edit here.

    Spaces rather than the empty string, and the choice is applied to all
    four alphanumeric attributes. The reason is the bridge: its load
    paragraph opens with `initialize TD-IRSPOSTING-REC.`
    [common/irspostingMT.cbl:L966], which leaves a character host
    variable holding spaces, so a `PostingRecord` that has been built but
    not filled carries what the COBOL record would carry at that point.
    Every column of this table is `NOT NULL`, and this is how the Python
    layer defaults instead of omitting.

    Args:
        cobol_name: The field name as the copybook spells it.

    Returns:
        A string of spaces at the field's declared character width.
    """
    width = _BY_COBOL_NAME[cobol_name].character_length
    # `character_length` is None for a numeric item; all four callers
    # below are alphanumeric, so the fallback is unreachable and exists
    # only to keep the expression total.
    return " " * (width or 0)


# =============================================================================
#  THE RECORD
# =============================================================================


@dataclass(slots=True)
class PostingRecord:
    """`01  Posting-Record.` [copybooks/irswspost.cob:L8].

    The internal IRS posting record: ten fields, one per `03`-level item
    the copybook declares, in its declaration order.

    The name is the copybook's own, undistinguished as the COBOL leaves
    it, even though it is the least telling of the three posting class
    names. The MODULE name carries the disambiguation instead, which is
    why the plan files this record under `irs_posting.py`. `irs030`
    copies the copybook with no `replacing` clause
    [irs/irs030.cbl:L288] while renaming both of its neighbours
    [irs/irs030.cbl:L286], [irs/irs030.cbl:L287], so an unprefixed name
    is exactly what the frozen program works with.

    Mutable, and deliberately not frozen: `Ledger-Postings-Add` fills
    one of these field by field before writing it
    [irs/irs030.cbl:L1569-L1733].

    This is the flattest record in the folder - ten `03`-level items
    under a single `01`, with no group item, no `FILLER`, no
    `REDEFINES`, no `OCCURS` and no `88`-level condition name anywhere,
    each confirmed absent in the frozen copybook. It is also entirely
    display-class storage: no `COMP`, no `COMP-3` and no binary usage is
    declared here, and every `COMP` in the chain appears at the bridge
    [common/irspostingMT.cbl:L173-L186].

    Attributes carry `int`, `str` and `decimal.Decimal` as the
    dictionary's own carrier selection dictates. No accounting value
    passes through a binary floating-point type at any point (R-2); the
    two money items are exact decimals at scale 2, which is what the two
    ROUNDED VAT computes [irs/irs030.cbl:L1551],
    [irs/irs030.cbl:L1562] produce and the net-of-VAT subtraction
    [irs/irs030.cbl:L1565] consumes.

    Storage metadata is not restated on the class. Read it from `FIELDS`,
    or reach one field's entry through its descriptor::

        FIELDS[5].sign_clause_text      'sign is leading'
        FIELDS[5].cite()                its three source locators
        FIELDS[5].drift()               the three views' disagreement,
                                        unsettled
    """

    # Post-Key       pic 9(5)                [copybooks/irswspost.cob:L9]
    # -> KEY-4 mediumint(5) unsigned, the primary key. One FLAT field:
    #    both sibling posting records group a batch and a number here,
    #    this one does not, and no group is added.
    post_key: int = 0

    # Post-Code      pic xx                 [copybooks/irswspost.cob:L10]
    # -> POST4-CODE char(2)
    post_code: str = _blanks("Post-Code")

    # Post-Date      pic x(8)               [copybooks/irswspost.cob:L11]
    # -> POST4-DAT char(8). EIGHT characters of text in DD/MM/YY form,
    #    one of the two date renderings the scenario dump comparison has
    #    to reconcile. Text here, and only text: nothing in this module
    #    reads it apart or converts it - `acas_posting/dates.py` owns
    #    date conversion.
    post_date: str = _blanks("Post-Date")

    # -------------------------------------------------------------------
    #  DELIBERATELY ABSENT HERE: POST4-DAY, POST4-MONTH, POST4-YEAR
    # -------------------------------------------------------------------
    #  The next three columns of IRSPOSTING-REC are ORDINALS 4, 5 AND 6 -
    #  they sit right here, interleaved into the middle of the table's
    #  column list between POST4-DAT and POST4-DR, and are not appended
    #  at the end:
    #
    #      4  POST4-DAY    tinyint(2) unsigned NOT NULL
    #      5  POST4-MONTH  tinyint(2) unsigned NOT NULL
    #      6  POST4-YEAR   tinyint(2) unsigned NOT NULL
    #
    #  NO COPYBOOK DECLARES ANY OF THEM. They exist only in the bridge
    #  host-variable group [common/irspostingMT.cbl:L177-L179] and in the
    #  frozen schema, and the bridge derives them from `Post-Date` under
    #  a guard [common/irspostingMT.cbl:L982-L987] - positions 1-2, 4-5
    #  and 7-8 by reference modification, each moved only if those two
    #  characters are numeric, after `initialize TD-IRSPOSTING-REC.`
    #  [common/irspostingMT.cbl:L966] has zeroed the group. A guard that
    #  does not hold leaves its component at zero while POST4-DAT still
    #  stores the raw eight characters: anomaly A-7, an internally
    #  inconsistent row, reproduced rather than repaired.
    #
    #  Their owner is `acas_posting/dal/acasirsub4_irs_posting.py`, which
    #  reproduces the derivation and its failure mode at the bridge
    #  boundary. This module RECORDS the absence and implements none of
    #  it: no attribute, no property, no method, no cached value, and no
    #  reading of `post_date` apart.
    #
    #  The maintainer's own note above the guard is the evidence that the
    #  guard is deliberate and the columns an afterthought
    #  [common/irspostingMT.cbl:L978-L980]: "These added after new
    #  columns created 31/12/16 - inhouse mysql & mariadb / and yes they
    #  all should be numeric as a date is present / but JIC (just in
    #  case)."
    #
    #  Ten fields here, thirteen columns there; 13 - 10 = these three.
    #  Recorded so the omission is visible rather than accidental - it is
    #  the case the plan uses to establish that the bridge, and not the
    #  copybook, is what this migration maps records to tables from.
    # -------------------------------------------------------------------

    # Post-DR        pic 9(5)               [copybooks/irswspost.cob:L12]
    # -> POST4-DR mediumint(5) unsigned
    post_dr: int = 0

    # Post-CR        pic 9(5)               [copybooks/irswspost.cob:L13]
    # -> POST4-CR mediumint(5) unsigned
    post_cr: int = 0

    # Post-Amount    pic s9(7)v99  sign is leading
    #                                       [copybooks/irswspost.cob:L14]
    # -> POST4-AMOUNT decimal(9,2). Zoned DISPLAY, sign LEADING and
    #    INCLUDED, 9 digits, 7 of them integral, scale 2, 9 bytes. The
    #    clause text is `sign is leading` WITH the word `is`; the sibling
    #    at [copybooks/wspost-irs.cob:L21] writes `sign leading` without
    #    it, and the two spellings stay two.
    post_amount: decimal.Decimal = decimal.Decimal("0.00")

    # Post-Legend    pic x(32)              [copybooks/irswspost.cob:L15]
    # -> POST4-LEGEND char(32)
    post_legend: str = _blanks("Post-Legend")

    # Vat-AC-Def     pic 99                 [copybooks/irswspost.cob:L16]
    # -> VAT-AC-DEF4 tinyint(2) unsigned. An INDEX into the IRS defaults
    #    table, not an account number: the posting step reads entries 31
    #    and 32 to pick which VAT control snapshot a figure accumulates
    #    into [irs/irs030.cbl:L1685-L1699]. No lookup is performed here.
    vat_ac_def: int = 0

    # Post-Vat-Side  pic xx                 [copybooks/irswspost.cob:L17]
    # -> POST4-VAT-SIDE char(2). Compared against a bare literal in the
    #    posting logic; the copybook gives it no `88`-level, and none is
    #    invented.
    post_vat_side: str = _blanks("Post-Vat-Side")

    # Vat-Amount     pic s9(7)v99   sign is leading
    #                                       [copybooks/irswspost.cob:L18]
    # -> VAT-AMOUNT4 decimal(9,2). The second `sign is leading` item, at
    #    L18 - the plan's L19 is the file's trailing `*>` comment.
    vat_amount: decimal.Decimal = decimal.Decimal("0.00")
