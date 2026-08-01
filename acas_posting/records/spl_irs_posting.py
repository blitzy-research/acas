"""Record layout of the Sales/Purchase-to-IRS posting transfer file.

    "This is NOT the same as the internal IRS
       posting file"
                              -- [copybooks/wspost-irs.cob:L6-L7], verbatim

The maintainer's own warning is the first thing this module says, because it
is the fact most easily lost. THREE posting records exist in this migration,
their field names are near-identical, and two of them sit side by side in one
program's data division - `irs030` reads this record and moves it field for
field into the internal one [irs/irs030.cbl:L1661-L1669]. Merging any two of
them would be silent and catastrophic:

    records/gl_posting.py       copybooks/wspost.cob       WS-Posting-Record
        table GLPOSTING-REC   14 cols   handler acas006     bridge glpostingMT
    records/spl_irs_posting.py  copybooks/wspost-irs.cob   WS-IRS-Posting-Record
        table PSIRSPOST-REC   10 cols   handler acas008     bridge slpostingMT
        ^^ THIS FILE
    records/irs_posting.py      copybooks/irswspost.cob    Posting-Record
        table IRSPOSTING-REC  13 cols   handler acasirsub4  bridge irspostingMT

This file imports neither sibling and aliases nothing across them. Every
dictionary key it uses is qualified by the MySQL table name precisely so the
three can never collapse into one another.

WHAT THIS FILE IS
=================
A CREATE from `copybooks/wspost-irs.cob`, a 26-line copybook, under the
mandate section 0.4.1.3 gives this folder - "translating each 05/03 field to
a dataclass attribute whose descriptor is looked up in the generated
dictionary", with oddities in the source preserved rather than repaired - and
in the shape section 0.8.1 requires, "plain modules and dataclasses; no ORM
entity layer". So: two plain dataclasses, ten attributes and two attributes,
nothing added.

THE COPYBOOK, ITEM BY ITEM
==========================
Read line by line against the frozen source; the locators below are counted
from it rather than transcribed from the plan:

    01  WS-IRS-Posting-Record.                                     L13
        03  WS-IRS-Post-Key.                                       L14
            05  WS-IRS-Batch       pic 9(5).                       L15
            05  WS-IRS-Post-Number pic 9(5).                       L16
        03  WS-IRS-Post-Code       pic xx.                         L17
        03  WS-IRS-Post-Date       pic x(8).                       L18
        03  WS-IRS-Post-DR         pic 9(5).                       L19
        03  WS-IRS-Post-CR         pic 9(5).                       L20
        03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.    L21
        03  WS-IRS-Post-Legend     pic x(32).                      L22
        03  WS-IRS-Vat-AC-Def      pic 99.                         L23
        03  WS-IRS-Post-Vat-Side   pic xx.                         L24
        03  WS-IRS-Vat-Amount      pic s9(7)v99   sign leading.    L25

Ten items at the `03` level - one group and nine elementary - which is why
`PSIRSPOST-REC` has ten columns: the bridge flattens the two-part key group
into a single host variable. `WsIrsPostingRecord` therefore carries TEN
attributes, one per `03` item and one per column, and the two children of the
key group live on `WsIrsPostKey`, which carries TWO. Eleven elementary items
in total, ten columns, twelve descriptors.

There is no FILLER in this copybook and no `88`-level condition name -
counted, zero of each - and none is invented here. The programs compare the
VAT side and the VAT selector against bare literals instead, at the locators
recorded on those two attributes below; predicates for literals belong to
`acas_posting/cobol/condition_names.py`, which is where the `88`-levels that
DO exist are modelled.

THE MAINTAINER'S HEADER, VERBATIM
=================================
    "File Definition for irs Postings File
       within IRS FROM SL (SL100) & PL100
                SL060, PL060 & irs030"     [copybooks/wspost-irs.cob:L3-L5]
    "This is NOT the same as the internal IRS
       posting file"                       [copybooks/wspost-irs.cob:L6-L7]
    "Chg 16/01/09 money to 9M"             [copybooks/wspost-irs.cob:L9]
    "  again 28/03/09 for IRS-batch-item"  [copybooks/wspost-irs.cob:L10]
    "  Taken from the fd copybook 24/11/16" [copybooks/wspost-irs.cob:L11]

The five programs he names are exactly the writers and the reader. Four Sales
and Purchase posting steps write this record when the IRS fan-out switch is
set - `move Batch to WS-IRS-Batch` and the ten moves after it
[sales/sl060.cbl:L1126-L1142], and the same block in
[sales/sl100.cbl:L659-L661], [purchase/pl060.cbl:L993-L995] and
[purchase/pl100.cbl:L640-L642] - and `irs030` walks the file, posts from it
and clears it at end of job [irs/irs030.cbl:L1715-L1724].

NONE of that behaviour is implemented here. The fan-out test, the walk and the
clear belong to the `sl060`, `sl100`, `pl060`, `pl100` and `irs030` program
modules and to the `acas008` handler module. This file is a layout and
nothing else.

THE ENTITY SPINE
================
    entity facade   SPL-Posting
    handler         acas008          [common/acas008.cbl]
    bridge          slpostingMT      [common/slpostingMT.scb], [common/slpostingMT.cbl]
    MySQL table     PSIRSPOST-REC    10 columns [mysql/ACASDB.sql:L366-L378],
                                     primary key IRS-POST-KEY - the column at
                                     [:L367], the clause at [:L377]
    copybook        copybooks/wspost-irs.cob

The bridge declares that pairing itself: `BASE=ACASDB` and
`TABLE=PSIRSPOST-REC,HV` [common/slpostingMT.scb:L257-L260].

The FILE is named `spl_irs_posting.py` after the entity facade and section
0.3.1's own file plan; the CLASS is `WsIrsPostingRecord` after the COBOL
`01`-name [copybooks/wspost-irs.cob:L13]. Neither name is bent towards the
other: tracing by table leads to the file, tracing by record to the class.

SIGN LEADING - THE REASON THIS MODULE EXISTS
============================================
Section 0.1.1 calls it "the easily-missed `DISPLAY` with `SIGN LEADING`
form", and section 0.6.1 lists it among the six numeric storage classes that
"must be modelled, because collapsing any of them changes stored values".
Both money items here carry it [copybooks/wspost-irs.cob:L21], [:L25]. No
`SEPARATE` keyword is written, so the sign is leading and INCLUDED -
overpunched on the high-order digit rather than occupying a byte of its own,
nine digits in nine bytes on the wire, not ten. The dictionary's descriptor
says exactly that, and this module asserts nothing of its own about it:

    usage DISPLAY - sign_position LEADING_INCLUDED - signed
    sign_clause_text "sign leading" - digits 9, integer_digits 7, scale 2
    python_storage DECIMAL - quantum 0.01 - byte_length 9

TWO SPELLINGS, AND THEY STAY TWO
--------------------------------
    "sign leading"      [copybooks/wspost-irs.cob:L21] and [:L25]  <- here
    "sign is leading"   [copybooks/irswspost.cob:L14]  and [:L18]

Both mean the same to the compiler; the TEXT differs, `sign_clause_text`
records the text, and so the two stay distinguishable here. Neither is
rewritten to match the other. The plan's own citation of the sibling's second
clause is one line late, and the correction is recorded on the attribute it
belongs to below.

A census across every copybook puts this vocabulary at six clauses in total:
`sign leading` four times - twice here, twice in the matching file definition
`copybooks/fdpost-irs.cob` - and `sign is leading` twice, both in
`copybooks/irswspost.cob`. `sign trailing`, `separate`, `justified` and
`blank when zero` occur ZERO times anywhere. So these two spellings are the
whole of it.

THE THIRD TREATMENT, FOR CONTRAST
---------------------------------
The General Ledger posting record carries NO sign clause at all - its amounts
are `pic s9(8)v99` [copybooks/wspost.cob:L23], [copybooks/wspost.cob:L28],
COBOL's default trailing overpunch - and its header records why: "98 bytes
26/03/09" then "96 bytes 20/12/11 (leading sign removed)"
[copybooks/wspost.cob:L6-L7]. Its debit and credit accounts are `9(6)` where
this record's are `9(5)`. Three posting records, three sign treatments, three
widths. All three are reproduced as found; none is brought into line with the
others.

Nothing in this copybook is `COMP`, `COMP-3` or `binary-*`: the record is
zoned decimal and alphanumeric throughout, and it becomes binary ONLY at the
bridge [common/slpostingMT.cbl:L266-L275]. That is a fact about where the
conversion happens, and the reason it is not performed in this file.

TYPE DISCIPLINE (RULE R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport.

    WS-IRS-Post-Amount, WS-IRS-Vat-Amount   -> Decimal, scale 2, signed
    WS-IRS-Batch, WS-IRS-Post-Number,
    WS-IRS-Post-DR, WS-IRS-Post-CR,
    WS-IRS-Vat-AC-Def                       -> int
    WS-IRS-Post-Code, WS-IRS-Post-Date,
    WS-IRS-Post-Legend,
    WS-IRS-Post-Vat-Side                    -> str, at the declared width
    WS-IRS-Post-Key                         -> group; holds no value itself

Money defaults are `Decimal("0.00")` at the declared scale, integers `0`, and
characters spaces at the declared width - each taken from the dictionary
rather than typed here, for the reason set out at `_spaces` below. The carrier
for each attribute is the one the dictionary names, never a reading of what
the field "means".

DESCRIPTORS ARE LOOKED UP, NEVER TYPED IN (RULE R-5)
====================================================
Section 0.8.1 of the plan, verbatim:

    "Data dictionary first. The dictionary is generated from the bridge
    before record definitions are written, and every Python field definition
    cites its entry. This ordering is a directive, not a preference - it is
    what prevents fields being transcribed by eye."

The user's own requirement behind it says of the maintainer's one-way
COBOL-to-MySQL bridge that "it is the data dictionary for this migration",
and section 0.3.3 states the consequence: "Field metadata is therefore
derived, not transcribed, which eliminates an entire class of transcription
error across several hundred fields."

Accordingly not one picture, digit count, scale, sign position or storage
class is written by hand below. Each attribute's `FieldDescriptor` comes from
`FieldDescriptor.from_dictionary_key`, and every key is read out of the
generated artifact by `_entry_keys_by_cobol_name`, whose docstring sets out
which accessor supplies which entry and why a key assembled from a field name
would miss. Provenance travels with each descriptor: `FIELDS[n].cite()`
returns the loader's compact three-locator citation and `FIELDS[n].drift()`
the unsettled cross-view record, both surfaced rather than reimplemented. The
wider mapping is the migration's traceability document.

THE BRIDGE DISAGREES WITH THE COPYBOOK IN FOUR WAYS
===================================================
The host-variable group is ten items [common/slpostingMT.cbl:L266-L275],
loaded from this record field by field in `bb000-HV-Load`
[common/slpostingMT.cbl:L992], [common/slpostingMT.cbl:L1001-L1010]. It is
not a transparent pipe, and each disagreement is documented on the attribute
it acts on:

    1  the key is FLATTENED, widened ten digits to eighteen, and gains a
       SIGN - see `WsIrsPostKey`
    2  both money items change STORAGE CLASS, zoned with a leading sign
       becoming binary - see the two amount attributes
    3  three items are WIDENED at the host variable and come back to the
       copybook's own width at the column - see the DR, CR and VAT-selector
       attributes
    4  one NAME is truncated, `WS-IRS-Post-Date` to `HV-IRS-POST-DAT`, and
       the column follows the host variable - see that attribute

Kind 1 is worth one comparison the attributes cannot make. Its direction is
the OPPOSITE of anomaly A-11, where `Sales-Average` is signed in the copybook
[copybooks/wssl.cob:L49] and LOSES its sign to an unsigned host variable
[common/salesMT.cbl:L308]. One gains a sign, the other loses one, which is
section 0.6.2's point exactly - the drift "is specific rather than systemic
and must be handled field by field from the dictionary".

THIS MODULE APPLIES NONE OF IT. A descriptor reports the COPYBOOK view as its
own digits, scale, sign and usage, and offers the disagreement unsettled
through `drift()`. Nothing here blends layers, widens an item to a column
width, flattens the key, or performs the bridge's conversions.
The `acas008` handler module owns the bridge boundary; the register of these
sites is the migration's anomaly log.

AN OPEN QUESTION, LEFT OPEN (RULE R-6)
======================================
Where a semantic question cannot be settled by reading the source, the
compiled program's behaviour settles it, and the arbitration is written down
in the migration's ambiguity-resolutions document. Drift kind 2 is such a
question. Section 0.6.8 poses the mirror-image case - "A negative binary
value through an unsigned host variable into an unsigned column ... what the
resulting stored value *is* depends on the conversion the bridge's C
interface performs, which must be measured rather than assumed" - and the
same reasoning applies to a leading-sign zoned value entering a signed binary
host variable. What the compiled bridge stores for a negative
`WS-IRS-Post-Amount` is to be measured against the oracle. It is recorded
here and settled nowhere.

WHAT THE HANDLER DOES - RECORDED HERE, IMPLEMENTED IN THE HANDLER MODULE
========================================================================
`acas008` is this record's handler, and it has three behaviours worth naming
so the anomaly log can cite this module beside the handler module. None is
implemented here; this file defines no status value, no verb and no method.

 * A PUBLISHED VERB THAT CAN NEVER SUCCEED - anomaly A-6. The handler tests
   `File-Function` at entry and rejects four of the verbs the facade
   publishes: `when 4` read-indexed, `when 7` re-write, `when 9` start and
   `when 8` delete [common/acas008.cbl:L299-L307]. It moves its
   "Action type wrong for file type (seq)" code to `WE-Error`
   [common/acas008.cbl:L304] and `99` to `fs-reply`
   [common/acas008.cbl:L305], then leaves. The transfer file is sequential,
   so a caller invoking the published Rewrite verb always fails. The status
   vocabulary lives in `dal/status.py`; the numeric code lives at the locator
   above and deliberately not in this file.
 * OPENING FOR OUTPUT DELETES EVERY ROW. `if fn-Open and fn-output and not
   FS-Cobol-Files-Used` sets `fn-delete-all` and processes it
   [common/acas008.cbl:L313-L319], repeated at
   [common/acas008.cbl:L571-L574]. That is how `irs030`'s end-of-job clear of
   the transfer file is implemented [irs/irs030.cbl:L1720-L1724].
 * THE HANDLER LOGS ITSELF AS THE IRS SUBSYSTEM. `move 1 to WS-Log-System`
   with the inline legend "1 = IRS, 2=GL, 3=SL, 4=PL, 5=Stock", and
   `move 15 to WS-Log-File-No` [common/acas008.cbl:L293-L294] - even though
   the bridge is named `slpostingMT` and all four writers are Sales and
   Purchase programs. A naming inconsistency, recorded rather than tidied.

ANOMALIES ARE REPRODUCED, NEVER REPAIRED (RULE R-4)
===================================================
From the preserved user requirement in section 0.8.2, verbatim:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included.
    A defect reproduced is correct; a defect fixed is a failure."

For a layout module that means every oddity above is carried with its locator
and none is smoothed: the two sign-clause spellings stay two, the four kinds
of drift stay unsettled, the truncated column name stays truncated, the
eight-character date stays eight characters and stays text, the two-digit VAT
selector stays two digits, and no condition name is invented for the bare
literals the programs compare against. There is no "winner" view of any field
in this system and none is introduced here.

WHAT THIS MODULE DOES NOT DO
============================
No date is parsed, converted or widened - `acas_posting/dates.py` owns date
conversion. No defaults table is consulted for `WS-IRS-Vat-AC-Def`. No value
is validated, padded, quantized or truncated on assignment: there is no
post-initialisation hook, `acas_posting/cobol/move.py` performs a MOVE and
`acas_posting/cobol/arithmetic.py` the arithmetic. No SQL, no DDL, no schema
metadata, no ORM base class. No COBOL is executed, embedded or shelled out to
(rule R-1); nothing here needs a COBOL compiler or runtime present.

LAYERING (SECTION 0.4.3)
========================
    MAY import       the standard library, `acas_posting.cobol.field` and
                     `acas_posting.dictionary.loader`
    MUST NOT import  dal, programs, cli, clock, dates, workfiles,
                     cobol.arithmetic, cobol.move, cobol.picture,
                     cobol.usage, cobol.condition_names, cobol.sortverb,
                     dictionary.generate, the comparison oracle in its
                     sibling tree, and ANY other records module - the two IRS
                     and GL posting siblings above included

The record layer is a leaf, and section 0.4.3 gives the reason: the
arithmetic test tier "imports only `cobol` and `records` and touches no
database, so it runs anywhere". A single reach into `dal` would drag a
database driver into that tier. Attribute order is copybook declaration
order, fixed collections are tuples, and the only I/O at import is the
loader's own lazy cached read, so two imports in two processes produce
identical state (rule R-6).
"""

# PROVENANCE
# The COBOL system, its generated MySQL bridge and its schema are the
# maintainer's work: they are the specification for this migration and are
# read only - never modified, reformatted, commented, relocated or built from
# here. The rule identifiers R-1 through R-6 cited above are the Agent Action
# Plan's own (section 0.7.2); this project carries no separate rules document,
# so the plan is where their full text lives.

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = ["WsIrsPostKey", "WsIrsPostingRecord"]


#  THE TWO NAMES THIS RECORD IS KEYED BY
#  Both are the frozen sources' own spellings, case and hyphens intact,
#  because dictionary lookup is exact and case-sensitive.

# The MySQL table the bridge declares for this record:
# `TABLE=PSIRSPOST-REC,HV` [common/slpostingMT.scb:L257-L260]. Ten columns,
# primary key IRS-POST-KEY. The left half of every column-mapped key below.
_TABLE: Final[str] = "PSIRSPOST-REC"

# The COBOL 01-name [copybooks/wspost-irs.cob:L13]. The left half of the keys
# of the items that reach no column at all.
_COPYBOOK_RECORD: Final[str] = "WS-IRS-Posting-Record"


#  KEYS AND DESCRIPTORS, TAKEN FROM THE GENERATED DICTIONARY


def _entry_keys_by_cobol_name() -> dict[str, str]:
    """Return this record's dictionary key for each COBOL field name.

    Both loader accessors are asked, because between them they cover the
    record and neither covers it alone:

      * `entries_for_table` yields the TEN column-mapped entries, in the
        column ordinal order of the frozen schema. Each keys as
        `PSIRSPOST-REC.<COLUMN-NAME>`, and the column name is not always the
        copybook's field name - `WS-IRS-Post-Date` is stored in
        `IRS-POST-DAT` [common/slpostingMT.cbl:L268] - which is why the key
        is read from the artifact and never assembled from a field name.
      * `entries_for_copybook_record` additionally yields the items that
        reach no column. The two children of the key group are such items,
        because the bridge flattens the group into one host variable
        [common/slpostingMT.cbl:L266]: `WS-IRS-Batch` and
        `WS-IRS-Post-Number` are declared by the copybook alone and key as
        `WS-IRS-Posting-Record.<FIELD-NAME>`. Thirteen entries come back for
        this copybook in all - the ten above, these two, and the `01` group
        itself.

    Where a name appears in both, the column-mapped key is kept, since the
    table view is the mapping this migration is keyed on.

    Returns:
        Every COBOL field name this copybook declares, against its key.
    """
    keys = {
        entry.copybook.name: str(entry.key)
        for entry in loader.entries_for_table(_TABLE)
        if entry.copybook is not None
    }
    for entry in loader.entries_for_copybook_record(_COPYBOOK_RECORD):
        if entry.copybook is not None:
            keys.setdefault(entry.copybook.name, str(entry.key))
    return keys


_ENTRY_KEYS: Final[dict[str, str]] = _entry_keys_by_cobol_name()


def _describe(cobol_name: str) -> FieldDescriptor:
    """Return the dictionary's description of one item of this record.

    Args:
        cobol_name: The item's COBOL name, exactly as
            `copybooks/wspost-irs.cob` spells it.

    Returns:
        The `FieldDescriptor` built from that item's dictionary entry,
        carrying its key and its copybook locator as provenance.
    """
    return FieldDescriptor.from_dictionary_key(_ENTRY_KEYS[cobol_name])


def _spaces(descriptor: FieldDescriptor) -> str:
    """Return one space for each character the copybook declares.

    The width comes from the dictionary, not from this file, so a default can
    never drift from the declaration it stands for. Spaces rather than an
    empty string, because that is what the record holds before anything is
    moved into it and what the bridge writes for an item left unset: its load
    paragraph opens with `initialize TD-PSIRSPOST-REC`
    [common/slpostingMT.cbl:L1000], and every column of `PSIRSPOST-REC` is
    declared NOT NULL.

    Every alphanumeric item of this record declares a character count, so the
    empty fallback is an accommodation for the optional member's type and not
    a decision about data; no attribute defined below can reach it.

    Args:
        descriptor: The item's description.

    Returns:
        The item's character default.
    """
    width = descriptor.character_length
    return " " * width if width is not None else ""


# The twelve items, each looked up once. Nine of the ten `03`-level items are
# elementary and one is the key group; the two `05`-level children of that
# group are declared by the copybook alone. Ordered as the copybook declares
# them, L14 through L25.
_POST_KEY: Final[FieldDescriptor] = _describe("WS-IRS-Post-Key")
_BATCH: Final[FieldDescriptor] = _describe("WS-IRS-Batch")
_POST_NUMBER: Final[FieldDescriptor] = _describe("WS-IRS-Post-Number")
_POST_CODE: Final[FieldDescriptor] = _describe("WS-IRS-Post-Code")
_POST_DATE: Final[FieldDescriptor] = _describe("WS-IRS-Post-Date")
_POST_DR: Final[FieldDescriptor] = _describe("WS-IRS-Post-DR")
_POST_CR: Final[FieldDescriptor] = _describe("WS-IRS-Post-CR")
_POST_AMOUNT: Final[FieldDescriptor] = _describe("WS-IRS-Post-Amount")
_POST_LEGEND: Final[FieldDescriptor] = _describe("WS-IRS-Post-Legend")
_VAT_AC_DEF: Final[FieldDescriptor] = _describe("WS-IRS-Vat-AC-Def")
_POST_VAT_SIDE: Final[FieldDescriptor] = _describe("WS-IRS-Post-Vat-Side")
_VAT_AMOUNT: Final[FieldDescriptor] = _describe("WS-IRS-Vat-Amount")


#  THE KEY GROUP


@dataclass(slots=True)
class WsIrsPostKey:
    """`03  WS-IRS-Post-Key.` [copybooks/wspost-irs.cob:L14].

    The two-part key of the Sales/Purchase-to-IRS posting transfer file: a
    batch number and a posting number within that batch, each five unsigned
    zoned digits. The Sales and Purchase posting steps set both from the
    General Ledger posting they are fanning out - `move Batch to
    WS-IRS-Batch` and `move Post-Number to WS-IRS-Post-Number`
    [sales/sl060.cbl:L1127-L1128].

    Not frozen, because those steps populate a record item by item before
    writing it.

    A group in COBOL holds no storage of its own; its children do. Reading
    `byte_length` on the group's own descriptor fails for that reason - sum
    the two children instead, as the copybook's own byte layout does.

    THE BRIDGE FLATTENS THIS GROUP, AND ADDS A SIGN
    -----------------------------------------------
    Ten unsigned digits across two items become one signed eighteen-digit
    binary host variable, `HV-IRS-POST-KEY PIC S9(18) COMP`
    [common/slpostingMT.cbl:L266], loaded from the GROUP in a single move -
    `move WS-IRS-Post-Key to HV-IRS-POST-KEY`
    [common/slpostingMT.cbl:L1001] - and stored in a `bigint(11)` column. The
    handler then reads that host variable back into its own key field
    [common/slpostingMT.cbl:L548], [common/slpostingMT.cbl:L642],
    [common/slpostingMT.cbl:L749].

    Neither the flattening nor the widening nor the added sign happens here.
    The two children keep the five digits each that the copybook gives them,
    and the disagreement is offered unsettled by `FIELDS[n].drift()` and by
    the loader's bridge view. The `acas008` handler module reproduces the
    conversion at the boundary where the COBOL performs it.

    Attributes:
        ws_irs_batch: `WS-IRS-Batch`, the batch this posting belongs to.
        ws_irs_post_number: `WS-IRS-Post-Number`, the posting's number
            within that batch.
        FIELDS: The two descriptors, in copybook declaration order. Each
            carries its own dictionary key, its copybook locator, `cite()`
            for the full three-locator citation and `drift()` for the
            unsettled cross-view record.
    """

    # 05  WS-IRS-Batch       pic 9(5).   unsigned zoned DISPLAY, scale 0
    #   [copybooks/wspost-irs.cob:L15]
    # Declared by the copybook alone: it reaches no column, because the
    # bridge carries the whole group in one host variable. Its dictionary
    # key is therefore record-qualified, not table-qualified.
    ws_irs_batch: int = 0

    # 05  WS-IRS-Post-Number pic 9(5).   unsigned zoned DISPLAY, scale 0
    #   [copybooks/wspost-irs.cob:L16]
    # Copybook-only for the same reason. `irs030` does not read it: it
    # assigns its own key from a running counter instead
    # [irs/irs030.cbl:L1670-L1671], which is a fact about that program and
    # not about this layout.
    ws_irs_post_number: int = 0

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_BATCH, _POST_NUMBER)


#  THE RECORD


@dataclass(slots=True)
class WsIrsPostingRecord:
    """`01  WS-IRS-Posting-Record.` [copybooks/wspost-irs.cob:L13].

    The Sales/Purchase-to-IRS posting transfer file's record, entity facade
    SPL-Posting, handler `acas008`, bridge `slpostingMT`, MySQL table
    `PSIRSPOST-REC`. And, in the maintainer's own words at
    [copybooks/wspost-irs.cob:L6-L7], "This is NOT the same as the internal
    IRS posting file" - see this module's docstring for the three-record
    table that keeps the distinction.

    TEN attributes, one per `03`-level item and one per column of the table.
    The first is the two-part key group; the other nine are elementary. Every
    one is zoned DISPLAY or alphanumeric: this copybook declares no `COMP`,
    no `COMP-3` and no `binary-*` item anywhere.

    Not frozen, because the four Sales and Purchase posting steps populate a
    record item by item before writing it
    [sales/sl060.cbl:L1126-L1142]. Members are in copybook declaration
    order, L14 through L25.

    Attributes:
        ws_irs_post_key: `WS-IRS-Post-Key`, the batch and posting number.
        ws_irs_post_code: `WS-IRS-Post-Code`, the posting's type code.
        ws_irs_post_date: `WS-IRS-Post-Date`, eight characters of date TEXT.
        ws_irs_post_dr: `WS-IRS-Post-DR`, the debit account.
        ws_irs_post_cr: `WS-IRS-Post-CR`, the credit account.
        ws_irs_post_amount: `WS-IRS-Post-Amount`, SIGN LEADING.
        ws_irs_post_legend: `WS-IRS-Post-Legend`, the posting narrative.
        ws_irs_vat_ac_def: `WS-IRS-Vat-AC-Def`, a defaults-table selector.
        ws_irs_post_vat_side: `WS-IRS-Post-Vat-Side`, which side the VAT
            falls on.
        ws_irs_vat_amount: `WS-IRS-Vat-Amount`, SIGN LEADING.
        FIELDS: The ten descriptors, in copybook declaration order, each
            with its dictionary key, its copybook locator, `cite()` and the
            unsettled `drift()`.
    """

    # 03  WS-IRS-Post-Key.   group; no storage of its own
    #   [copybooks/wspost-irs.cob:L14]
    # Flattened, widened 10 digits to 18 and given a sign at the bridge
    # [common/slpostingMT.cbl:L266]; none of that is done here. Stored in
    # `IRS-POST-KEY`, the table's primary key.
    ws_irs_post_key: WsIrsPostKey = field(default_factory=WsIrsPostKey)

    # 03  WS-IRS-Post-Code       pic xx.      alphanumeric, 2 characters
    #   [copybooks/wspost-irs.cob:L17]
    ws_irs_post_code: str = _spaces(_POST_CODE)

    # 03  WS-IRS-Post-Date       pic x(8).    alphanumeric, 8 characters
    #   [copybooks/wspost-irs.cob:L18]
    # EIGHT characters of TEXT, a two-digit-year form - not a date object and
    # not a binary day number. Neither parsed nor widened to ten here;
    # `acas_posting/dates.py` owns date conversion. Two drifts meet on this
    # one item: the host variable's name is TRUNCATED to `HV-IRS-POST-DAT`
    # [common/slpostingMT.cbl:L268] and the column follows the host variable,
    # so the item is stored in `IRS-POST-DAT`.
    ws_irs_post_date: str = _spaces(_POST_DATE)

    # 03  WS-IRS-Post-DR         pic 9(5).    unsigned zoned DISPLAY, scale 0
    #   [copybooks/wspost-irs.cob:L19]
    # FIVE digits. The General Ledger posting record's equivalent is `9(6)`
    # [copybooks/wspost.cob:L19]; the difference is preserved, not reconciled.
    # Widened to `9(10) COMP` at the bridge [common/slpostingMT.cbl:L269] and
    # then stored in an `int(5) unsigned` column - three views, three widths.
    ws_irs_post_dr: int = 0

    # 03  WS-IRS-Post-CR         pic 9(5).    unsigned zoned DISPLAY, scale 0
    #   [copybooks/wspost-irs.cob:L20]
    # Five digits likewise, and widened likewise
    # [common/slpostingMT.cbl:L270].
    ws_irs_post_cr: int = 0

    # 03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.
    #   [copybooks/wspost-irs.cob:L21]
    # The sign clause is written exactly so - "sign leading", lower case, without `is`. The
    # sibling internal posting record spells the same meaning "sign is leading"
    # [copybooks/irswspost.cob:L14]; both spellings are carried as written and neither is
    # rewritten to match the other. No SEPARATE keyword, so the sign is leading and INCLUDED:
    # overpunched on the high-order digit, nine bytes on the wire. Signed, nine digits, scale 2,
    # zoned DISPLAY -> Decimal. It becomes `PIC S9(07)V9(02) COMP` only at the bridge
    # [common/slpostingMT.cbl:L271], where the leading sign disappears into a binary item; what
    # that conversion stores for a negative amount is an R-6 question for the compiled oracle,
    # settled nowhere here.
    ws_irs_post_amount: Decimal = Decimal("0.00")

    # 03  WS-IRS-Post-Legend     pic x(32).   alphanumeric, 32 characters
    #   [copybooks/wspost-irs.cob:L22]
    ws_irs_post_legend: str = _spaces(_POST_LEGEND)

    # 03  WS-IRS-Vat-AC-Def      pic 99.      unsigned zoned DISPLAY, scale 0
    #   [copybooks/wspost-irs.cob:L23]
    # TWO digits, and a SELECTOR INTO THE IRS DEFAULTS TABLE - not an account number. The Sales
    # steps set it to 32 [sales/sl060.cbl:L1138], [sales/sl100.cbl:L659] and the Purchase steps
    # to 31 [purchase/pl060.cbl:L993], [purchase/pl100.cbl:L640]; `irs030` tests it against
    # zero, 31 and 32 to choose which VAT control account the amount accumulates into
    # [irs/irs030.cbl:L1682-L1699]. No lookup happens here and `records/irs_dflt.py`, which
    # carries that table, is not imported. The move that sets it has a second receiver carrying
    # the maintainer's own inline question mark - `move 32 to WS-IRS-vat-ac-def / Vat-PC  *> IS
    # IT ???` [sales/sl060.cbl:L1138-L1139] - and `DR-PC` and `CR-PC` are not carried into this
    # record at all, which he also flags at [:L1133] and [:L1135]. Widened to `9(03) COMP` at
    # the bridge [common/slpostingMT.cbl:L273], stored in `tinyint(2) unsigned`.
    ws_irs_vat_ac_def: int = 0

    # 03  WS-IRS-Post-Vat-Side   pic xx.      alphanumeric, 2 characters
    #   [copybooks/wspost-irs.cob:L24]
    # Compared against the bare literals "CR" and "DR"
    # [irs/irs030.cbl:L1686], [irs/irs030.cbl:L1690],
    # [irs/irs030.cbl:L1694], [irs/irs030.cbl:L1698]. The copybook declares
    # no `88`-level for either literal, so none is created here.
    ws_irs_post_vat_side: str = _spaces(_POST_VAT_SIDE)

    # 03  WS-IRS-Vat-Amount      pic s9(7)v99   sign leading.
    #   [copybooks/wspost-irs.cob:L25]
    # The second SIGN LEADING item, spelt identically to the first and with
    # the same nine-digit, scale-2, nine-byte zoned shape. Its counterpart in
    # the internal posting record again reads "sign is leading"
    # [copybooks/irswspost.cob:L18] - and note that the plan cites that
    # clause at L19, which is one line late. Turned into
    # `PIC S9(07)V9(02) COMP` at the bridge [common/slpostingMT.cbl:L275].
    ws_irs_vat_amount: Decimal = Decimal("0.00")

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _POST_KEY,
        _POST_CODE,
        _POST_DATE,
        _POST_DR,
        _POST_CR,
        _POST_AMOUNT,
        _POST_LEGEND,
        _VAT_AC_DEF,
        _POST_VAT_SIDE,
        _VAT_AMOUNT,
    )
