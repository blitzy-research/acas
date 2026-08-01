"""Purchase invoice header and lines record layouts.

A CREATE from two frozen copybooks, read as specification and never modified:

    copybooks/plwspinv.cob    86 lines - the primary layout
    copybooks/plwspinv2.cob   73 lines - three views over one buffer

with the record-to-table mapping taken from the maintainer's one-way
COBOL-to-MySQL bridge and the frozen schema:

    common/plinvoiceMT.cbl  3226 lines - handler acas026, entity facade
                                         PInvoice, host-variable prefixes
                                         HV- (header) and HV1- (lines)
    mysql/ACASDB.sql                   - PUINVOICE-REC, 30 columns
                                       - PUINV-LINES-REC, 14 columns

`pl055` extracts purchase orders for proof and `pl060` posts them, including
the IRS fan-out. Both walk the invoice header and its lines, so the sign
flips [purchase/pl055.cbl:L376], [purchase/pl055.cbl:L387],
[purchase/pl055.cbl:L572-L575], [purchase/pl060.cbl:L507],
[purchase/pl060.cbl:L683], [purchase/pl060.cbl:L783], the two moving-average
blocks [purchase/pl060.cbl:L745], [purchase/pl060.cbl:L751],
[purchase/pl060.cbl:L760], [purchase/pl060.cbl:L766] and the period-total
writes [purchase/pl055.cbl:L582], [purchase/pl055.cbl:L584],
[purchase/pl060.cbl:L628] all read and write fields declared here. A wrong
scale, sign or storage class in this file moves every posted purchase figure.

THE COBOL RECORDS, AND THE SIXTEEN CLASSES THAT CARRY THEM
----------------------------------------------------------
Class names are fixed by the migration plan. Where the plan's name does not
mechanically follow the COBOL spelling, the COBOL spelling is what the
descriptor's `name` carries - see PInvoiceBodies below::

    copybooks/plwspinv.cob
      01  PInvoice-Header                  L8    PInvoiceHeader
        03  ih-prime                       L9    IhPrime
          05  WS-Invoice-Key               L10   WsInvoiceKey
          05  ih-Supplier                  L13   IhSupplier
          05  ih-order                     L17   IhOrder
        03  ih-sub-prime                   L30   IhSubPrime
          05  ih-Fig                       L31   IhFig
      01  Pinvoice-Bodies                  L65   PInvoiceBodies
        03  invoice-line   occurs 40       L66   IlInvoiceLineBody
          05  il-Key                       L67   IlKey

    copybooks/plwspinv2.cob
      01  WS-PInvoice-Record               L10   WsPInvoiceRecord
        03  Invoice-Key                    L11   InvoiceKey
      01  Invoice-Header redefines ...     L21   IhInvoiceHeader
        03  ih-supplier                    L24   IhSupplier2
        03  ih-fig                         L31   IhFig2
      01  Invoice-Line   redefines ...     L56   IlInvoiceLine

Two group names collide inside this module because the two copybooks declare
the same idea twice with different casing. `IhSupplier` and `IhFig` are
`copybooks/plwspinv.cob`'s; `IhSupplier2` and `IhFig2` are
`copybooks/plwspinv2.cob`'s. The digit is a Python disambiguator; neither COBOL
name carries one.

FIELD ORDER FOLLOWS THE COPYBOOK, NOT THE COLUMN ORDINAL
--------------------------------------------------------
Every dataclass below declares its attributes in copybook declaration order,
so this file can be set beside `cat -n copybooks/plwspinv.cob` and diffed by
eye. For this table the two orders genuinely differ, in two ways:

  * `ih-lines` is declared at [copybooks/plwspinv.cob:L44], immediately
    before `ih-deduct-days` at L45. The bridge declares `HV-IH-LINES` at
    [common/plinvoiceMT.cbl:L418], after `HV-IH-CR` at L417 and before
    `HV-IH-DAY-BOOK-FLAG` at L419, and the schema puts `IH-LINES` at column
    ordinal 28, after `IH-CR` at 27.
  * five columns have no copybook position at all - see below.

So `loader.entries_for_table("PUINVOICE-REC")` and the copybook disagree about
this record's field sequence. The copybook wins here, because a copybook's
field order IS its byte layout.

WHAT THE THREE LAYERS AGREE AND DISAGREE ABOUT
----------------------------------------------
Money passes through cleanly. All eight `ih-Fig` children and all eight
`ih-fig` children are `pic s9(7)v99`, become `PIC S9(07)V9(02) COMP` at
[common/plinvoiceMT.cbl:L399-L406], and land in `decimal(9,2)` - signed at
all three layers. `il-net`, `il-unit` and `il-vat` do the same through
[common/plinvoiceMT.cbl:L434], [common/plinvoiceMT.cbl:L435] and
[common/plinvoiceMT.cbl:L437]. The unsigned money fields `ih-deduct-amt`,
`ih-deduct-vat` and `il-discount` are unsigned at all three layers too.

Six INTEGER fields do not pass through cleanly: they are signed in the copybook
and unsigned in both the host variable and the column, so a negative value
loses its sign at the bridge, before any SQL runs. Set against `VALUEANAL-REC`,
where it is the money that loses its sign, that shows the drift to be specific
rather than systemic - which is why every descriptor in this file is fetched
field by field from the dictionary rather than inferred from a field's kind.

Five more columns - `IH-STATUS-A`, `-C`, `-I`, `-L` and `-P` - have no copybook
position at all: neither Purchase copybook declares them, and the dictionary
reports no copybook side for any of the five. Sales carries the same five
columns, but there they ARE declared, as `sih-status-P` through `sih-status-I`
[copybooks/slwsinv.cob:L56-L60] - same columns, opposite provenance.

A descriptor here reports the COPYBOOK view of its own field. It never blends
one layer into another and never applies the bridge's conversion; all three
views are offered untouched through `descriptor_for(...).drift()`. Reproducing
that conversion belongs to the `acas026` handler module, at the bridge
boundary.

THE BRIDGE COPIES ONE COPYBOOK, NOT TWO
---------------------------------------
[common/plinvoiceMT.cbl:L455-L458] verbatim::

     copy "plwspinv.cob"   replacing PInvoice-Header        by WS-Invoice-Record
                                     leading ==ih-==      by ==WS-ih-==
                                      ==occurs 40.== by ==.==
                                      ==il-==      by ==Un-Used-il-==.

preceded at [common/plinvoiceMT.cbl:L452-L453] by "Using the first record but
not the 2nd as it uses occurs 40 but to reduce Ram usage get rid of the occurs,
hopefully." - the trailing ", hopefully." is the Purchase bridge's own; the
Sales bridge's otherwise-identical comment does not carry it. The four-part
clause textually DELETES `occurs 40.` and renames the copied bodies record's
every member to `Un-Used-il-`, neutralising a record it does not want. Note the
lower-case renames, where the Sales bridge uses `WS-Sih-` and `Un-Used-Sil-`.

There is no `copy "plwspinv2.cob"` anywhere in the bridge - the string does not
occur in it at all. Matching `copy "` case-insensitively returns six
statements: `envdiv.cob` L256, `wsfnctn.cob` L446, `Test-Data-Flags.cob` L450
and `plwspinv.cob` L455, plus the two the preSQL translator emits in upper
case, `mysql-variables.cpy` L385 and `mysql-procedures.cpy` L1417. The
migration plan names both copybooks as this module's sources while the bridge
copies one; both are carried here in full, and which layout governs the bytes
on disk is left to the compiled program.

The bridge also declares its OWN line record inline at
[common/plinvoiceMT.cbl:L362-L379], its members at `03` level with one
`03 WS-il-Key` group among them and no `occurs`, ending
`88 WS-il-Analyised value "Z".` at L379 - a SINGLE case where
[copybooks/plwspinv.cob:L83] declares two. The classes below come from the
copybooks, not from that inline block.

THE MAINTAINER'S OWN SIZE ANNOTATIONS, VERBATIM
-----------------------------------------------
    *> record size 100 bytes  06/05/17   26/03/09      [copybooks/plwspinv.cob:L6]
    *> 42 bytes  +1 06/05/17                           [copybooks/plwspinv.cob:L9]
    *> 58 bytes 06/05/17                               [copybooks/plwspinv.cob:L30]
    *> 40 bytes                                        [copybooks/plwspinv.cob:L31]
    *> 75 bytes each - 3000 bytes 02/11/10- line +1 & filler remd so same
       size.                                          [copybooks/plwspinv.cob:L63]
    *> record size 129 bytes 22/12/11                  [copybooks/plwspinv2.cob:L7]
    *>           = 100 less filler err. 06/05/17 item-nos > 99 from
       bin-char                                       [copybooks/plwspinv2.cob:L8]
    *> was x(88).  now rec  100                        [copybooks/plwspinv2.cob:L19]
    *> 100 bytes                                       [copybooks/plwspinv2.cob:L21]
    *> 75 bytes 06/05/17, 74 bytes 22/12/11            [copybooks/plwspinv2.cob:L56]

Summing the declared elementary items gives: PInvoice-Header 100, of which
ih-prime 42 and ih-sub-prime 58 and ih-Fig 40; invoice-line 75 each and so 3000
for the table of 40; WS-PInvoice-Record 100; the Invoice-Header redefine 100;
the Invoice-Line redefine 75. Every annotation in `copybooks/plwspinv.cob`
therefore agrees with its own fields, down to the running subtotals at L29,
L39, L45 and L76.

Two disagreements survive that summing, both of them in the SECOND copybook,
and this file settles NEITHER. `copybooks/plwspinv2.cob:L7` records 129 bytes
while L8 qualifies it as "= 100 less filler err." and L19 records
"now rec  100" - the copybook admits an error in its own recorded length. And
the Invoice-Line redefine is annotated 75 bytes (74 in an earlier revision)
while redefining a 100-byte base, leaving 25 bytes of that base outside the
view. No length constant is declared anywhere in this module, by design:
whether a declared length or a field sum governs the record actually read
affects trailing-field alignment, and only the compiled program shows which.

COBOL NAME COLLISIONS, RECORDED
-------------------------------
`pending`, `invoiced`, `applied`, `day-booked`, `ih-analyised`, `il-analyised`
and every `ih-*` and `il-*` field name are declared in BOTH Purchase
copybooks, and the `ih-*` and `il-*` names collide with
`copybooks/slwsinv2.cob` as well. That is why `plinvoiceMT` has to rename them
on copy, and it is the same pressure that forces qualified references in the
General Ledger posting path [general/gl070.cbl:L497], [general/gl070.cbl:L521],
[general/gl070.cbl:L525]. The Python namespace removes the ambiguity for free,
so the collision is written down here instead of showing up in the code.

TYPE DISCIPLINE
---------------
The rule is about SCALE, not about storage class::

    pic x(n) / pic xx / pic xxx / pic x            -> str
    pic 9(n) / pic 99 / pic 9   (DISPLAY, scale 0) -> int
    binary-char / binary-short / binary-long       -> int   (signed)
    pic s9(7)v99 under an inherited comp-3 group   -> Decimal
    pic 999v99 comp / pic 99v99 comp               -> Decimal
    group items                                    -> nested dataclass

"COMP means integer" is false: `ih-deduct-amt`, `ih-deduct-vat` and
`il-discount` are COMP with scale 2 and are therefore Decimal. Bare
`binary-char`, `binary-short` and `binary-long` are SIGNED - GnuCOBOL wants an
explicit `unsigned` keyword otherwise, and this bridge writes that keyword five
times when it means it - so their descriptors report `signed` true and their
truncation on divide is integer truncation, which is what the posting programs
depend on. There is no binary floating point in this module, in any form.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
-----------------------------------------
It declares no field the copybooks do not declare and drops none that they do
- the autogen members and every live FILLER stay. It implements no
condition-name predicate: the 88-levels are published here as data and
`acas_posting/cobol/condition_names.py` turns them into predicates. It adds no
post-initialisation hook, no check, no derived attribute a caller could
mistake for a stored field, no length constant and no entity-mapping layer. It
performs no I/O at import, reads no file, starts no process and loads no
shared library, so it runs where no COBOL compiler or runtime is present.

Nothing here is imported from any other `records` module, from `dal`, from
`programs`, from `cli` or from the comparison oracle. Section 0.4.3 of the
migration plan grants this layer `acas_posting.cobol.field` and
`acas_posting.dictionary.loader` and nothing else, because the arithmetic test
tier imports `cobol` and `records` only and must run with no infrastructure.

The sales invoice module is close enough in shape to look shareable and is
not. Fourteen structural divergences separate the two: header length (137
versus 100); sub-group sizes (42+95 versus 42+58); line length (80 and 3200
versus 75 and 3000); customer versus supplier group; how the 10-byte order
field is declared, three ways for one idea (a picture plus a redefining
filler, a plain group here, a plain elementary item in the second copybook);
where the five status flags are declared; the `applied` condition name,
`sapplied` [copybooks/slwsinv.cob:L55] against `applied`
[copybooks/plwspinv.cob:L43]; 88 value case ordering; line description width
(32 versus 24); the two line fillers Purchase has and Sales does not; the
back-order flag Sales has and Purchase has not; header key nesting depth
(03/05 versus 05/07); whether the second copybook keeps its intermediate
groups; and the bodies record's own casing. Beyond those fourteen,
`copybooks/plwspinv.cob` carries no REDEFINES where `copybooks/slwsinv.cob`
carries one. Divergence-preservation is the point of the exercise, so this
module shares no base class, mixin, helper, constant or type alias with any
sibling.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from decimal import Decimal
from types import MappingProxyType
from typing import Any, ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `ConditionName` is the generated dictionary's own carrier for an 88-level,
# with exactly the three members this module needs - name, value and source.
# The migration plan's section 0.4.3 grants this layer `cobol.field` and
# `dictionary.loader`, and the loader is where this type comes from: it
# re-exports the object model's records for exactly this purpose (see its
# `RE_EXPORTED_MODEL_NAMES`), as a BINDING to the one definition rather than a
# copy. So the type the dictionary already publishes is named here directly,
# through the one permitted door, and no competing copy is declared (rule R-5).
from acas_posting.dictionary.loader import ConditionName

__all__: Final[tuple[str, ...]] = (
    # The 88-level inventory and the four lookups, then the sixteen record
    # types in one alphabetical run, so the surface is stable between runs.
    "CONDITION_NAMES",
    "IhFig",
    "IhFig2",
    "IhInvoiceHeader",
    "IhOrder",
    "IhPrime",
    "IhSubPrime",
    "IhSupplier",
    "IhSupplier2",
    "IlInvoiceLine",
    "IlInvoiceLineBody",
    "IlKey",
    "InvoiceKey",
    "PInvoiceBodies",
    "PInvoiceHeader",
    "WsInvoiceKey",
    "WsPInvoiceRecord",
    "cite_for",
    "condition_names_for",
    "descriptor_for",
    "dictionary_key_for",
)


# FIVE COLUMNS THAT NO COPYBOOK DECLARES. mysql/ACASDB.sql:L562-L567 declares six `IH-STATUS*`
# columns - the bare `IH-STATUS` plus `-A`, `-C`, `-I`, `-L` and `-P`, each carrying its own
# COMMENT - and common/plinvoiceMT.cbl:L408-L412 supplies a host variable for the five suffixed
# ones. Only the bare `IH-STATUS` has a copybook field, at [copybooks/plwspinv.cob:L40] and
# [copybooks/plwspinv2.cob:L40]; grepping either copybook for the five suffixed names returns 0
# against the schema's 5.
# Their ALPHABETICAL suffix order, against declaration order everywhere else, marks them as
# generated at the schema rather than derived from a layout - and `PUINVOICE-REC` is the only
# in-scope table whose columns carry comments at all, including `IH-UPDATE`'s 'jic, Invoice rec
# merged with OTM rec' [mysql/ACASDB.sql:L575]. They are therefore NOT dataclass fields here:
# this module publishes the copybook layout, and asking for one raises `BridgeOnlyFieldError`,
# which names the bridge as the only place they exist.


# The private metadata slot each attribute's dictionary key travels in. A key
# is a plain string, so building one costs nothing at import; the descriptor
# behind it is fetched only when `descriptor_for` is called.
_DICTIONARY_KEY: Final[str] = "dictionary_key"


def _cited(key: str) -> Mapping[str, str]:
    """Return the field metadata that cites one generated-dictionary entry.

    A formatting device and nothing else, so that the 102 cited attribute
    declarations below read as one line each. The string it is handed is the entry key the
    loader itself reports for that field - never a key built by upper-casing
    an attribute name, which would be wrong for `ih-Date` (column `IH-DAT`),
    for `ih-Supplier` (one `char(7)` column) and for `ih-Invoice` (widened
    from 8 digits to 10 at the bridge).

    Args:
        key: A qualified entry key, `<TABLE-NAME>.<COLUMN-NAME>` for a
            column-mapped field or `<COPYBOOK-RECORD>.<FIELD-NAME>` with the
            loader's own line disambiguator for a copybook-only field.

    Returns:
        The metadata mapping for `dataclasses.field`.
    """
    return {_DICTIONARY_KEY: key}


# THE 88-LEVELS, AS DATA. Eighteen condition names are carried - twelve over the header views
# and six over the line view - and five oddities in them are reproduced rather than repaired
# (R-4). `ih-Daily` and `ih-Testing` are given the SAME value "D"
# [copybooks/plwspinv.cob:L22-L23], so the second can never be distinguished from the first; L24
# mis-capitalises "LAst"; L51 puts a space before its terminating period; and the value-case
# ORDERING inverts between the header names at L41, L42, L43, L51 and L53, which list upper case
# first, and the line name at L83, which lists lower case first.
# `ih-analyised` and `il-analyised` carry the frozen misspelling of "analysed", and it is kept
# exactly as written so a reader grepping the COBOL finds the Python. Predicates are evaluated
# by `cobol.condition_names`, never re-declared here.
CONDITION_NAMES: Final[Mapping[str, tuple[ConditionName, ...]]] = MappingProxyType(
    {
        # -- copybooks/plwspinv.cob ---------------------------------------
        # On `07  ih-Freq  pic x.` [copybooks/plwspinv.cob:L18], inside the
        # `ih-order` group. Six names over one byte, two of them sharing "D".
        "PInvoice-Header.ih-Freq": (
            ConditionName(
                name="ih-Yearly",
                value='"Y"',
                source="copybooks/plwspinv.cob:L19",
            ),
            ConditionName(
                name="ih-Monthly",
                value='"M"',
                source="copybooks/plwspinv.cob:L20",
            ),
            ConditionName(
                name="ih-Quarterly",
                value='"Q"',
                source="copybooks/plwspinv.cob:L21",
            ),
            # "These two are only for testing." - shares "D" with ih-Testing.
            ConditionName(
                name="ih-Daily",
                value='"D"',
                source="copybooks/plwspinv.cob:L22",
            ),
            # "So NOT documented and removed after tests." Still declared.
            ConditionName(
                name="ih-Testing",
                value='"D"',
                source="copybooks/plwspinv.cob:L23",
            ),
            # One condition name, four values. "LAst one for TESTING ONLY so
            # remove after" - the typo is the maintainer's.
            ConditionName(
                name="ih-Valid-Freqs",
                value='"Y" "M" "Q" "D"',
                source="copybooks/plwspinv.cob:L24",
            ),
        ),
        # On `05  ih-status  pic x.` [copybooks/plwspinv.cob:L40].
        # Upper-case first in this copybook; lower-case first in the other.
        "PUINVOICE-REC.IH-STATUS": (
            ConditionName(
                name="pending",
                value='"P" "p"',
                source="copybooks/plwspinv.cob:L41",
            ),
            ConditionName(
                name="invoiced",
                value='"I" "i"',
                source="copybooks/plwspinv.cob:L42",
            ),
            ConditionName(
                name="applied",
                value='"Z" "z"',
                source="copybooks/plwspinv.cob:L43",
            ),
        ),
        # On `05  ih-day-book-flag  pic x  value space.`
        # [copybooks/plwspinv.cob:L50]. The declaration at L51 carries a space
        # before its terminating period.
        "PUINVOICE-REC.IH-DAY-BOOK-FLAG": (
            ConditionName(
                name="day-booked",
                value='"B" "b"',
                source="copybooks/plwspinv.cob:L51",
            ),
        ),
        # On `05  ih-update  pic x.` [copybooks/plwspinv.cob:L52].
        "PUINVOICE-REC.IH-UPDATE": (
            ConditionName(
                name="ih-analyised",
                value='"Z" "z"',
                source="copybooks/plwspinv.cob:L53",
            ),
        ),
        # On `05  il-update  pic x.` [copybooks/plwspinv.cob:L82]. LOWER-case
        # first, alone among this copybook's five lists, and annotated "using
        # Z hopefully." The bridge's inline record declares the same name with
        # a SINGLE value, "Z" [common/plinvoiceMT.cbl:L379].
        "PUINV-LINES-REC.IL-UPDATE": (
            ConditionName(
                name="il-analyised",
                value='"z" "Z"',
                source="copybooks/plwspinv.cob:L83",
            ),
        ),
        # -- copybooks/plwspinv2.cob --------------------------------------
        # On `03  ih-status  pic x.` [copybooks/plwspinv2.cob:L40]. The same
        # three names as above with the two cases the other way round.
        "Invoice-Header.ih-status#40": (
            ConditionName(
                name="pending",
                value='"p" "P"',
                source="copybooks/plwspinv2.cob:L41",
            ),
            ConditionName(
                name="invoiced",
                value='"i" "I"',
                source="copybooks/plwspinv2.cob:L42",
            ),
            ConditionName(
                name="applied",
                value='"z" "Z"',
                source="copybooks/plwspinv2.cob:L43",
            ),
        ),
        # On `03  ih-day-book-flag  pic x.` [copybooks/plwspinv2.cob:L50] -
        # which, unlike its counterpart, declares no VALUE clause.
        "Invoice-Header.ih-day-book-flag#50": (
            ConditionName(
                name="day-booked",
                value='"b" "B"',
                source="copybooks/plwspinv2.cob:L51",
            ),
        ),
        # On `03  ih-update  pic x.` [copybooks/plwspinv2.cob:L52].
        "Invoice-Header.ih-update#52": (
            ConditionName(
                name="ih-analyised",
                value='"z" "Z"',
                source="copybooks/plwspinv2.cob:L53",
            ),
        ),
        # On `03  il-update  pic x.` [copybooks/plwspinv2.cob:L71].
        "Invoice-Line.il-update#71": (
            ConditionName(
                name="il-analyised",
                value='"z" "Z"',
                source="copybooks/plwspinv2.cob:L72",
            ),
        ),
    }
)


#  THE FOUR LOOKUPS


def dictionary_key_for(record: Any, attribute: str) -> str:
    """Return the generated-dictionary key one attribute is cited to.

    Args:
        record: Any dataclass in this module, or an instance of one.
        attribute: The Python attribute name, as `"ih_net"`.

    Returns:
        The qualified entry key, as `"PUINVOICE-REC.IH-NET"`.

    Raises:
        TypeError: `record` is not a dataclass type or instance.
        KeyError: No such attribute on that record, or - which cannot happen
            for a record declared in this module - an attribute carrying no
            citation. Every one of this module's 102 attributes carries one;
            the guard exists for a dataclass passed in from elsewhere.
    """
    for declared in fields(record):
        if declared.name == attribute:
            key = declared.metadata.get(_DICTIONARY_KEY)
            if key is None:
                raise KeyError(
                    f"{attribute!r} on "
                    f"{getattr(record, '__name__', type(record).__name__)!r} "
                    f"carries no data dictionary citation."
                )
            return str(key)
    raise KeyError(
        f"{getattr(record, '__name__', type(record).__name__)!r} declares no "
        f"attribute {attribute!r}. Its attributes, in copybook declaration "
        f"order, are: {', '.join(f.name for f in fields(record))}."
    )


def descriptor_for(record: Any, attribute: str) -> FieldDescriptor:
    """Describe one attribute's COBOL storage, from the generated dictionary.

    The storage metadata of every field in this module is fetched here rather
    than written down beside the attribute, which is what keeps a picture
    clause, a digit count, a scale, a sign position or a storage class from
    being transcribed by eye across 102 cited fields.

    The descriptor reports the COPYBOOK view. It is not blended with the
    bridge or the column view, and it does not apply the narrowing that six of
    this record's integer fields undergo at the bridge; call `.drift()` on the
    result to see all three views and their disagreement untouched.

    Lazy, and memoised inside `FieldDescriptor` itself, so importing this
    module reads nothing and the first ask pays for the artifact once.

    Args:
        record: Any dataclass in this module, or an instance of one.
        attribute: The Python attribute name, as `"il_qty"`.

    Returns:
        The descriptor for that field, carrying its dictionary key and the
        `<path>:L<n>` locator of its copybook declaration.

    Raises:
        KeyError: No such attribute on that record.
        loader.DictionaryKeyError: The dictionary carries no such entry, which
            would mean this module and the generated artifact had drifted
            apart.
    """
    return FieldDescriptor.from_dictionary_key(dictionary_key_for(record, attribute))


def cite_for(record: Any, attribute: str) -> str:
    """Return one attribute's three-locator provenance line.

    A pass-through to `loader.cite`, which is the traceability primitive this
    migration keeps in one place; it is surfaced here and never reimplemented.
    For a field that reaches a table it names all three views::

        PUINVOICE-REC.IH-NET  copybook=copybooks/plwspinv.cob:L33
        bridge=common/plinvoiceMT.cbl:L400  column=mysql/ACASDB.sql:L555

    and for a copybook-only field it says so, which is how the autogen members
    of the `ih-order` group declare themselves::

        PInvoice-Header.ih-Freq  copybook=copybooks/plwspinv.cob:L18
        bridge=absent  column=absent

    Args:
        record: Any dataclass in this module, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The provenance line for that field.

    Raises:
        KeyError: No such attribute on that record.
    """
    return loader.cite(dictionary_key_for(record, attribute))


def condition_names_for(key: str) -> tuple[ConditionName, ...]:
    """Return the 88-levels declared on the item one dictionary key names.

    Args:
        key: A qualified entry key, as returned by `dictionary_key_for`.

    Returns:
        The condition names in copybook declaration order, each with its
        literal list verbatim and its own locator. An empty tuple for an item
        that declares none, which is 93 of this module's 102 cited
        attributes; the other nine carry one or more.
    """
    return CONDITION_NAMES.get(key, ())


#  copybooks/plwspinv.cob - THE WORKING-STORAGE INVOICE HEADER AND BODIES
# Field order below follows the copybook line for line, so that a reader can
# set `cat -n copybooks/plwspinv.cob` beside this section and walk both
# together. It is deliberately NOT column-ordinal order; see the module
# docstring for where the two part company.
# Every class carries `COBOL_DICTIONARY_KEY`, the generated-dictionary entry
# for the group item itself. It is a `ClassVar`, so it is not a dataclass
# field and holds no record data - it is how a `01`-level record cites its own
# declaration, since a nested group is already cited by the attribute that
# holds it on its parent.


@dataclass(slots=True, kw_only=True)
class WsInvoiceKey:
    """`05  WS-Invoice-Key.` [copybooks/plwspinv.cob:L10].

    The copybook comment reads `*> added 08/01/18.`

    Two children at level 07, which is one level deeper than the sales
    copybook nests the same idea. Together they occupy ten characters, and the
    bridge promotes that run to an alphanumeric primary key of its own,
    `HV-PINVOICE-KEY PIC X(10)` [common/plinvoiceMT.cbl:L391] ->
    `PINVOICE-KEY char(10)`, while ALSO materialising both members separately
    as `IH-INVOICE` and `IH-TEST`. Neither copybook declares a field named
    `PINVOICE-KEY`; the group is what the column is built from. This dual
    materialisation is exactly what the sales invoice record does, promoting
    `WS-Invoice-Key` [copybooks/slwsinv.cob:L20] to `SINVOICE-KEY char(10)`
    while also materialising both of its members. The IRS nominal and general
    ledger posting records promote a group too - `NL-Key`
    [copybooks/irswsnl.cob:L9] to `KEY-1`, `WS-Post-Key`
    [copybooks/wspost.cob:L14] to `POST-KEY` - but both of those land numeric
    rather than alphanumeric, and neither materialises the group's members as
    separate columns.

    No `pinvoice_key` attribute is declared here. That name belongs to the
    column side, and building its value is the `acas026` handler module's
    work.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINVOICE-REC.PINVOICE-KEY"

    # `07  ih-Invoice   pic 9(8).` [copybooks/plwspinv.cob:L11]
    # Zoned display, eight digits, scale 0. The bridge widens it to
    # `PIC 9(10) COMP` [common/plinvoiceMT.cbl:L392] and the column is
    # `int(8) unsigned`; the descriptor reports the copybook's eight digits
    # and its display storage, not the bridge's ten and binary.
    ih_invoice: int = field(metadata=_cited("PUINVOICE-REC.IH-INVOICE"))

    # `07  ih-Test      pic 99     value zero.    *> was binary-char   value
    # zero.` [copybooks/plwspinv.cob:L12]
    # The comment records what this field used to be; the declaration is what
    # it is - `pic 99`, zoned display, scale 0. The VALUE clause is declared,
    # so the default below reproduces it.
    ih_test: int = field(default=0, metadata=_cited("PUINVOICE-REC.IH-TEST"))


@dataclass(slots=True, kw_only=True)
class IhSupplier:
    """`05  ih-Supplier.` [copybooks/plwspinv.cob:L13].

    Where the sales copybook names its counterpart for the customer, this
    names the supplier - the pair are not the same record with different
    labels.

    Six characters and a check digit, which the bridge folds into a single
    `HV-IH-SUPPLIER X(7)` [common/plinvoiceMT.cbl:L394] -> `IH-SUPPLIER
    char(7)`. Both children are declared here, as the copybook declares them;
    the second copybook's base view instead writes the same seven characters
    flat, as `Invoice-Supplier pic x(7)` [copybooks/plwspinv2.cob:L14], and
    that form is carried too, on `WsPInvoiceRecord`.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINVOICE-REC.IH-SUPPLIER"

    # `07  ih-Nos       pic x(6).` [copybooks/plwspinv.cob:L14]
    ih_nos: str = field(metadata=_cited("PInvoice-Header.ih-Nos"))

    # `07  ih-Check     pic 9.` [copybooks/plwspinv.cob:L15]
    ih_check: int = field(metadata=_cited("PInvoice-Header.ih-Check"))


@dataclass(slots=True, kw_only=True)
class IhOrder:
    """`05  ih-order.` [copybooks/plwspinv.cob:L17].

    The declaration line carries `*>    pic x(10).    *> New changes 18/5/23
    for Autogen` - a commented-out picture clause on the very line that turned
    an elementary ten-character item into a group. The sales copybook took a
    different route for the same ten bytes, a picture plus a redefining
    filler, and the second purchase copybook a third, a plain elementary item
    with no group and no redefinition [copybooks/plwspinv2.cob:L28]. Three
    treatments of one concept, each kept in its own source's terms.

    None of the four members below reaches the bridge or a table. Only the ten
    bytes as a whole do, as `HV-IH-ORDER X(10)` [common/plinvoiceMT.cbl:L396]
    -> `IH-ORDER char(10)`. That is consistent with the autogen tables being
    out of the migration's scope - `PUAUTOGEN-REC` is named there as excluded -
    and the members are declared anyway, because the record layer removes
    nothing the copybook declares any more than it adds anything the copybook
    does not. Their citations say so directly: `bridge=absent column=absent`.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINVOICE-REC.IH-ORDER"

    # `07  ih-Freq      pic x.` [copybooks/plwspinv.cob:L18]
    # Carries six 88-levels, L19 to L24, two of which share the value "D".
    # See CONDITION_NAMES, keyed "PInvoice-Header.ih-Freq".
    ih_freq: str = field(metadata=_cited("PInvoice-Header.ih-Freq"))

    # `07  ih-Repeat    pic 99.` [copybooks/plwspinv.cob:L25]
    ih_repeat: int = field(metadata=_cited("PInvoice-Header.ih-Repeat"))

    # `07  filler       pic xxx.` [copybooks/plwspinv.cob:L26]
    # Written `xxx`, which is three characters. It occupies bytes and is
    # declared; a filler is never dropped from this layer.
    filler_1: str = field(metadata=_cited("PInvoice-Header.filler"))

    # `07  ih-Last-Date binary-long.   *> 4 bytes date an invoice was
    # generated/posted` [copybooks/plwspinv.cob:L27]
    # Bare `binary-long`, so signed - the compiler wants the `unsigned`
    # keyword written when unsigned is meant, and these sources do write it
    # where they mean it.
    ih_last_date: int = field(metadata=_cited("PInvoice-Header.ih-Last-Date"))


@dataclass(slots=True, kw_only=True)
class IhPrime:
    """The first of the header's two halves, 42 bytes.

    `03  ih-prime.` [copybooks/plwspinv.cob:L9], annotated
    `*> 42 bytes  +1 06/05/17`. The sales copybook's equivalent pair splits 42
    and 95; this one splits 42 and 58.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.ih-prime"

    # `05  WS-Invoice-Key.` [copybooks/plwspinv.cob:L10]
    ws_invoice_key: WsInvoiceKey = field(metadata=_cited("PUINVOICE-REC.PINVOICE-KEY"))

    # `05  ih-Supplier.` [copybooks/plwspinv.cob:L13]
    ih_supplier: IhSupplier = field(metadata=_cited("PUINVOICE-REC.IH-SUPPLIER"))

    # `05  ih-Date          binary-long.` [copybooks/plwspinv.cob:L16]
    # Signed in the copybook; the bridge declares `HV-IH-DAT PIC 9(10) COMP`
    # [common/plinvoiceMT.cbl:L395] and the column is `int(8) unsigned`, so the
    # sign is lost before any statement runs. The host variable's name also
    # drops the trailing E of `ih-Date`, which is why this attribute keeps the
    # copybook spelling and the dictionary entry carries the column spelling.
    # Both facts are reported by `descriptor_for(...).drift()`, unblended.
    ih_date: int = field(metadata=_cited("PUINVOICE-REC.IH-DAT"))

    # `05  ih-order.` [copybooks/plwspinv.cob:L17]
    ih_order: IhOrder = field(metadata=_cited("PUINVOICE-REC.IH-ORDER"))

    # `05  ih-Type          pic 9.` [copybooks/plwspinv.cob:L28]
    ih_type: int = field(metadata=_cited("PUINVOICE-REC.IH-TYPE"))

    # `05  ih-Ref           pic x(10).  *> 42` [copybooks/plwspinv.cob:L29]
    ih_ref: str = field(metadata=_cited("PUINVOICE-REC.IH-REF"))


@dataclass(slots=True, kw_only=True)
class IhFig:
    """The header's eight packed money fields.

    `05  ih-Fig                          comp-3.   *> 40 bytes`
    [copybooks/plwspinv.cob:L31].

    GROUP-USAGE INHERITANCE. The usage clause is written once, on the group, and
    each of the eight children below carries only `pic s9(7)v99` with no usage of
    its own [copybooks/plwspinv.cob:L32-L39]. All eight are therefore packed
    decimal, and every descriptor reports `usage` COMP-3, `usage_declared_at` GROUP
    and `usage_inherited_from` "ih-Fig". Reading usage off the picture line alone
    would type all eight as zoned display and put a different byte pattern in every
    money column of the table.

    The second copybook declares the same group as `ih-fig`, lower case
    [copybooks/plwspinv2.cob:L31]; `IhFig2` carries that spelling, verbatim.

    Contrast with `IhSubPrime`, where `ih-deduct-amt` and `ih-deduct-vat` write
    their usage on their own picture lines and so report `usage_declared_at` FIELD
    with no inheritance.

    Money passes through all three layers unchanged here: signed in the copybook,
    `PIC S9(07)V9(02) COMP` in the bridge [common/plinvoiceMT.cbl:L399-L406],
    `decimal(9,2)` in the column. Worth stating because the value analysis record
    loses the sign on its money while this record loses it only on six integers -
    which is why field metadata is asked for one field at a time rather than
    assumed from a field's kind.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.ih-Fig"

    # `07  ih-p-c       pic s9(7)v99.` [copybooks/plwspinv.cob:L32]
    ih_p_c: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-P-C"))

    # `07  ih-net       pic s9(7)v99.` [copybooks/plwspinv.cob:L33]
    ih_net: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-NET"))

    # `07  ih-extra     pic s9(7)v99.` [copybooks/plwspinv.cob:L34]
    ih_extra: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-EXTRA"))

    # `07  ih-carriage  pic s9(7)v99.` [copybooks/plwspinv.cob:L35]
    ih_carriage: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-CARRIAGE"))

    # `07  ih-vat       pic s9(7)v99.` [copybooks/plwspinv.cob:L36]
    ih_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-VAT"))

    # `07  ih-discount  pic s9(7)v99.` [copybooks/plwspinv.cob:L37]
    ih_discount: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-DISCOUNT"))

    # `07  ih-e-vat     pic s9(7)v99.` [copybooks/plwspinv.cob:L38]
    ih_e_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-E-VAT"))

    # `07  ih-c-vat     pic s9(7)v99.   *> 40` [copybooks/plwspinv.cob:L39]
    ih_c_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-C-VAT"))


@dataclass(slots=True, kw_only=True)
class IhSubPrime:
    """The header's second half - money, status and the deduction terms.

    `03  ih-sub-prime.` [copybooks/plwspinv.cob:L30], annotated
    `*> 58 bytes 06/05/17`.

    ORDER NOTE. `ih-lines` is declared here at [copybooks/plwspinv.cob:L44],
    immediately before `ih-deduct-days`. The bridge declares `HV-IH-LINES PIC
    9(03) COMP` at [common/plinvoiceMT.cbl:L418], third from last of its thirty
    header host variables - after `HV-IH-CR` at L417 and before
    `HV-IH-DAY-BOOK-FLAG` at L419 - and the table puts `IH-LINES` at column
    ordinal 28, after `IH-CR` at 27. The attribute below sits where the copybook
    puts it. Asking the dictionary for this table by column and by copybook record
    therefore returns two different orders, and this field is one of the two
    reasons why; the other is the five columns with no copybook position at all.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.ih-sub-prime"

    # `05  ih-Fig                          comp-3.   *> 40 bytes`
    # [copybooks/plwspinv.cob:L31]
    ih_fig: IhFig = field(metadata=_cited("PInvoice-Header.ih-Fig"))

    # `05  ih-status        pic x.` [copybooks/plwspinv.cob:L40]
    # Three 88-levels, L41 to L43, upper-case first. The table comments the
    # matching column `'STATUS-X not yet used'`, and follows it with five more
    # status columns that no copybook declares - see the block above.
    ih_status: str = field(metadata=_cited("PUINVOICE-REC.IH-STATUS"))

    # `05  ih-lines         binary-char.` [copybooks/plwspinv.cob:L44]
    # Signed `binary-char` here; `PIC 9(03) COMP` at
    # [common/plinvoiceMT.cbl:L418] and `tinyint(2) unsigned` in the table, so
    # this is one of the six integers that lose their sign at the bridge.
    ih_lines: int = field(metadata=_cited("PUINVOICE-REC.IH-LINES"))

    # `05  ih-deduct-days   binary-char.  *> 43`
    # [copybooks/plwspinv.cob:L45]
    # Signed here, `tinyint(3) unsigned` in the table.
    ih_deduct_days: int = field(metadata=_cited("PUINVOICE-REC.IH-DEDUCT-DAYS"))

    # `05  ih-deduct-amt    pic 999v99    comp.  *> 4`
    # [copybooks/plwspinv.cob:L46]
    # Usage written on its own picture line, so no group inheritance applies.
    # Scale is 2, so this is exact decimal even though the usage is COMP; the
    # rule is scale, not usage. Unsigned at all three layers - `PIC
    # 9(03)V9(02) COMP` [common/plinvoiceMT.cbl:L414], `decimal(5,2) unsigned`.
    ih_deduct_amt: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-DEDUCT-AMT"))

    # `05  ih-deduct-vat    pic 999v99    comp.` [copybooks/plwspinv.cob:L47]
    ih_deduct_vat: Decimal = field(metadata=_cited("PUINVOICE-REC.IH-DEDUCT-VAT"))

    # `05  ih-days          binary-char.` [copybooks/plwspinv.cob:L48]
    # Signed here, `tinyint(3) unsigned` in the table.
    ih_days: int = field(metadata=_cited("PUINVOICE-REC.IH-DAYS"))

    # `05  ih-cr            binary-long.  *> 4` [copybooks/plwspinv.cob:L49]
    # Signed here, `int(8) unsigned` in the table.
    ih_cr: int = field(metadata=_cited("PUINVOICE-REC.IH-CR"))

    # `05  ih-day-book-flag pic x   value space.`
    # [copybooks/plwspinv.cob:L50]
    # The VALUE clause is declared, so the default below reproduces it. The
    # second copybook declares the same field with NO value clause
    # [copybooks/plwspinv2.cob:L50], and `IhInvoiceHeader` accordingly gives it
    # no default. One 88-level, L51, whose declaration carries a space before
    # its terminating period.
    ih_day_book_flag: str = field(
        default=" ", metadata=_cited("PUINVOICE-REC.IH-DAY-BOOK-FLAG")
    )

    # `05  ih-update        pic x.` [copybooks/plwspinv.cob:L52]
    # One 88-level, `ih-analyised`, L53 - misspelled in the source and kept
    # that way. The table comments the column `'jic, Invoice rec merged with
    # OTM rec'`.
    ih_update: str = field(metadata=_cited("PUINVOICE-REC.IH-UPDATE"))

    # Two filler declarations sit next in the source and are COMMENTED OUT, so
    # nothing is declared for them: `*>         05  filler           pic x.`
    # [copybooks/plwspinv.cob:L55] and `*>         05 filler pic x(29).  *> not
    # used for WS as its a filler 2 match header`
    # [copybooks/plwspinv.cob:L56]. They are dead source, not fillers.


@dataclass(slots=True, kw_only=True)
class PInvoiceHeader:
    """`01  PInvoice-Header.` [copybooks/plwspinv.cob:L8].

    The header the purchase posting programs read, mutate and write back. The
    copybook's own notes above it read `In Purchase`, `Working Storage For The
    Invoice Header`, `Temporary processing.` and `*> record size 100 bytes
    06/05/17   26/03/09`.

    Note the casing the source uses for its two `01`-levels: `PInvoice-Header`
    with a capital I here, `Pinvoice-Bodies` with a lower-case i at
    [copybooks/plwspinv.cob:L65]. The inconsistency is inside one file and is
    kept, in this module's class docstrings and in every descriptor's own
    `name`.

    Two halves only, so this class has two attributes; the twenty-eight leaf
    fields, one of them a live FILLER, live inside them. Summing the declared fields gives 100
    bytes, with `ih-prime` at 42 and `ih-sub-prime` at 58, which matches every
    annotation the copybook makes about itself. The second copybook's account
    of the same 100 bytes does not agree with its own opening line, and that
    disagreement is left standing; see the module docstring.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PInvoice-Header.PInvoice-Header"

    # `03  ih-prime.   *> 42 bytes  +1 06/05/17` [copybooks/plwspinv.cob:L9]
    ih_prime: IhPrime = field(metadata=_cited("PInvoice-Header.ih-prime"))

    # `03  ih-sub-prime.                  *> 58 bytes 06/05/17`
    # [copybooks/plwspinv.cob:L30]
    ih_sub_prime: IhSubPrime = field(metadata=_cited("PInvoice-Header.ih-sub-prime"))


@dataclass(slots=True, kw_only=True)
class IlKey:
    """`05  il-Key.` [copybooks/plwspinv.cob:L67], commented `*> New 08/10/18`.

    Ten characters, promoted by the bridge to an alphanumeric primary key of
    its own, `HV1-IL-LINE-KEY X(10)` [common/plinvoiceMT.cbl:L426] ->
    `IL-LINE-KEY char(10)`, while both members are ALSO materialised
    separately as `IL-INVOICE` and `IL-LINE`. As with the header key, no
    copybook declares a field of that name, so none is declared here; building
    its value belongs to the `acas026` handler module.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "PUINV-LINES-REC.IL-LINE-KEY"

    # `07  il-invoice   pic 9(8).` [copybooks/plwspinv.cob:L68]
    il_invoice: int = field(metadata=_cited("PUINV-LINES-REC.IL-INVOICE"))

    # `07  il-line      pic 99.     *> was binary-char.`
    # [copybooks/plwspinv.cob:L69]
    # Declaration over comment again: `pic 99`, zoned display, scale 0.
    il_line: int = field(metadata=_cited("PUINV-LINES-REC.IL-LINE"))


@dataclass(slots=True, kw_only=True)
class IlInvoiceLineBody:
    """One of the forty invoice lines the bodies record holds.

    `03  invoice-line                   occurs 40.`
    [copybooks/plwspinv.cob:L66].

    The group's descriptor reports `occurs` 40; the copybook heading above it reads
    `*> 75 bytes each - 3000 bytes 02/11/10- line +1 & filler remd so same size.`,
    and summing the declared fields gives exactly 75, and so 3000 for forty.

    The same line record appears three ways across the sources: with `occurs 40`
    here; without it in [copybooks/plwspinv2.cob:L56], where it redefines a single
    buffer; and in the bridge, which copies this copybook and then textually deletes
    the `occurs 40.` and renames every `il-` field to `Un-Used-il-`
    [common/plinvoiceMT.cbl:L455-L458], declaring its own line record inline instead
    [common/plinvoiceMT.cbl:L362-L379]. Each form is carried in its own source's
    terms.

    Its description is 24 characters wide. The sales copybook's is 32; that is one
    of the fourteen divergences, not a transcription slip. Purchase also carries two
    `filler pic xx` runs Sales has none of, and Sales carries a back-order flag
    Purchase has none of - a grep for `back-ordered` across both purchase copybooks
    and the purchase bridge returns nothing, so the absence is recorded here rather
    than filled in.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Pinvoice-Bodies.invoice-line"

    # `05  il-Key.        *> New 08/10/18` [copybooks/plwspinv.cob:L67]
    il_key: IlKey = field(metadata=_cited("PUINV-LINES-REC.IL-LINE-KEY"))

    # `05  il-product       pic x(13).   *> +1 to match wspinv2`
    # [copybooks/plwspinv.cob:L70]
    il_product: str = field(metadata=_cited("PUINV-LINES-REC.IL-PRODUCT"))

    # `05  il-pa            pic xx.` [copybooks/plwspinv.cob:L71]
    # `xx` is two characters.
    il_pa: str = field(metadata=_cited("PUINV-LINES-REC.IL-PA"))

    # `05  filler           pic xx.      *> -1 to match wspinv2`
    # [copybooks/plwspinv.cob:L72]
    filler_1: str = field(metadata=_cited("Pinvoice-Bodies.filler#72"))

    # `05  il-qty           binary-short.` [copybooks/plwspinv.cob:L73]
    # Signed here; `HV1-IL-QTY PIC 9(05) COMP` [common/plinvoiceMT.cbl:L431]
    # and `smallint(6) unsigned` in the table. The sixth and last of the
    # signedness narrowings. Integer storage, so a division truncates as an
    # integer division - which is the behaviour the arithmetic layer has to
    # reproduce, not improve.
    il_qty: int = field(metadata=_cited("PUINV-LINES-REC.IL-QTY"))

    # `05  il-type          pic x.` [copybooks/plwspinv.cob:L74]
    il_type: str = field(metadata=_cited("PUINV-LINES-REC.IL-TYPE"))

    # `05  il-description   pic x(24).` [copybooks/plwspinv.cob:L75]
    il_description: str = field(metadata=_cited("PUINV-LINES-REC.IL-DESCRIPTION"))

    # `05  filler           pic xx.  *> 56` [copybooks/plwspinv.cob:L76]
    filler_2: str = field(metadata=_cited("Pinvoice-Bodies.filler#76"))

    # `05  il-net           pic s9(7)v99   comp-3.`
    # [copybooks/plwspinv.cob:L77]
    # Usage on its own picture line - `usage_declared_at` FIELD, no
    # inheritance. Signed at all three layers, `decimal(9,2)` in the table.
    il_net: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-NET"))

    # `05  il-unit          pic s9(7)v99   comp-3.`
    # [copybooks/plwspinv.cob:L78]
    il_unit: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-UNIT"))

    # `05  il-discount      pic 99v99      comp.`
    # [copybooks/plwspinv.cob:L79]
    # Scale 2, so exact decimal, even though the usage is COMP.
    il_discount: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-DISCOUNT"))

    # `05  il-vat           pic s9(7)v99   comp-3.`
    # [copybooks/plwspinv.cob:L80]
    il_vat: Decimal = field(metadata=_cited("PUINV-LINES-REC.IL-VAT"))

    # `05  il-vat-code      pic 9.` [copybooks/plwspinv.cob:L81]
    il_vat_code: int = field(metadata=_cited("PUINV-LINES-REC.IL-VAT-CODE"))

    # `05  il-update        pic x.` [copybooks/plwspinv.cob:L82]
    # One 88-level, `il-analyised`, L83 - the only lower-case-first list in
    # this copybook, and annotated `*> using Z hopefully.` The bridge's inline
    # record declares the same name with a single value
    # [common/plinvoiceMT.cbl:L379]. Which case actually reaches the column is
    # a question for the compiled program, not for this module.
    il_update: str = field(metadata=_cited("PUINV-LINES-REC.IL-UPDATE"))

    # A third filler follows in the source and is COMMENTED OUT, so nothing is
    # declared for it: `*>       05  filler         pic x.   *> rounding filler
    # for WS only` [copybooks/plwspinv.cob:L85].


@dataclass(slots=True, kw_only=True)
class PInvoiceBodies:
    """`01  Pinvoice-Bodies.  *> was lines.` [copybooks/plwspinv.cob:L65].

    Forty invoice lines. The trailing comment records that the record used to
    be called `lines`, and the `01`-name is spelled with a lower-case i where
    the header at [copybooks/plwspinv.cob:L8] uses a capital I - an
    inconsistency inside one file, kept.

    The table is a `tuple`, fixed at forty elements, because the `OCCURS 40`
    is fixed at forty and because a run of this cycle has to come out the same
    way twice.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Pinvoice-Bodies.Pinvoice-Bodies"

    # `03  invoice-line                   occurs 40.`
    # [copybooks/plwspinv.cob:L66]
    invoice_line: tuple[IlInvoiceLineBody, ...] = field(
        metadata=_cited("Pinvoice-Bodies.invoice-line")
    )


# plwspinv2.cob: THREE VIEWS OVER ONE BUFFER. The copybook declares three 01-levels over the
# same storage, the second and third as REDEFINES of the first, and its own length notes
# contradict each other - L19 reads `*> was x(88).  now rec  100`, and the field bytes sum to
# 100, so the 100 is the one to trust.
# Unlike the header copybook, this one interposes NO intermediate group items between the 01 and
# its elementary fields [copybooks/plwspinv2.cob:L21-L53], so every field sits at 03 level
# directly under the record. The three views are published as three dataclasses over one
# dictionary namespace; which one a given program writes is a question for the compiled program,
# not a choice made here.


@dataclass(slots=True, kw_only=True)
class InvoiceKey:
    """`03  Invoice-Key.` [copybooks/plwspinv2.cob:L11].

    The base view's ten-character key run, spelled out where the first
    copybook writes `WS-Invoice-Key` and nests one level deeper.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "WS-PInvoice-Record.Invoice-Key"

    # `05  Invoice-Nos  pic 9(8).` [copybooks/plwspinv2.cob:L12]
    invoice_nos: int = field(metadata=_cited("WS-PInvoice-Record.Invoice-Nos"))

    # `05  Item-Nos     pic 99.   *> was  binary-char.`
    # [copybooks/plwspinv2.cob:L13]
    # Note the double space after the comment marker, which is the source's.
    # Declaration over comment: `pic 99`, zoned display, scale 0. No VALUE
    # clause is declared on this one, unlike its counterpart `ih-Test`
    # [copybooks/plwspinv.cob:L12], so no default is given.
    item_nos: int = field(metadata=_cited("WS-PInvoice-Record.Item-Nos"))


@dataclass(slots=True, kw_only=True)
class WsPInvoiceRecord:
    """`01  WS-PInvoice-Record.` [copybooks/plwspinv2.cob:L10].

    The base view - the buffer the two redefinitions below sit over. It
    describes the first 32 bytes in its own terms and then covers the rest
    with two fillers.

    None of its fields reaches a table under these names; the bridge copies
    the other copybook, not this one, so every citation here reports
    `bridge=absent column=absent`.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "WS-PInvoice-Record.WS-PInvoice-Record"

    # `03  Invoice-Key.` [copybooks/plwspinv2.cob:L11]
    invoice_key: InvoiceKey = field(metadata=_cited("WS-PInvoice-Record.Invoice-Key"))

    # `03  Invoice-Supplier pic x(7).` [copybooks/plwspinv2.cob:L14]
    # FLAT, where the other copybook nests six characters and a check digit
    # [copybooks/plwspinv.cob:L13-L15]. Both forms are carried, each on its own
    # view.
    invoice_supplier: str = field(
        metadata=_cited("WS-PInvoice-Record.Invoice-Supplier")
    )

    # `03  Invoice-Date     binary-long.` [copybooks/plwspinv2.cob:L15]
    invoice_date: int = field(metadata=_cited("WS-PInvoice-Record.Invoice-Date"))

    # `03  Inv-Order        pic x(10).` [copybooks/plwspinv2.cob:L16]
    # Abbreviated where every sibling is spelled out - `Invoice-Nos`,
    # `Invoice-Supplier`, `Invoice-Date`, `Invoice-Type`. The abbreviation is
    # kept.
    inv_order: str = field(metadata=_cited("WS-PInvoice-Record.Inv-Order"))

    # `03  Invoice-Type     pic 9.` [copybooks/plwspinv2.cob:L17]
    invoice_type: int = field(metadata=_cited("WS-PInvoice-Record.Invoice-Type"))

    # `03  filler           pic x(10).` [copybooks/plwspinv2.cob:L18]
    filler_1: str = field(metadata=_cited("WS-PInvoice-Record.filler#18"))

    # `03  filler           pic x(58).     *> was x(88).  now rec  100`
    # [copybooks/plwspinv2.cob:L19]
    filler_2: str = field(metadata=_cited("WS-PInvoice-Record.filler#19"))


@dataclass(slots=True, kw_only=True)
class IhSupplier2:
    """`03  ih-supplier.` [copybooks/plwspinv2.cob:L24].

    The same supplier group as `IhSupplier`, declared lower case and one level
    shallower in the second copybook. The two classes are named apart only
    because Python cannot hold both spellings of one name in one module:
    `IhSupplier` is [copybooks/plwspinv.cob:L13]'s and this is
    [copybooks/plwspinv2.cob:L24]'s. Each descriptor's own `name` keeps the
    spelling its source uses.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-supplier"

    # `05  ih-nos       pic x(6).` [copybooks/plwspinv2.cob:L25]
    ih_nos: str = field(metadata=_cited("Invoice-Header.ih-nos#25"))

    # `05  ih-check     pic 9.` [copybooks/plwspinv2.cob:L26]
    ih_check: int = field(metadata=_cited("Invoice-Header.ih-check#26"))


@dataclass(slots=True, kw_only=True)
class IhFig2:
    """The second copybook's spelling of the same eight money fields.

    `03  ih-fig                          comp-3.`
    [copybooks/plwspinv2.cob:L31].

    GROUP-USAGE INHERITANCE again, and the same eight money fields, but the group
    is spelled `ih-fig` in lower case where the first copybook writes `ih-Fig`
    [copybooks/plwspinv.cob:L31]. Every descriptor below reports `usage` COMP-3,
    `usage_declared_at` GROUP and `usage_inherited_from` "ih-fig" - the casing its
    own source uses, not the other's.

    Named apart from `IhFig` only because one module cannot hold both spellings;
    this is the second copybook's group.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.ih-fig#31"

    # `05  ih-p-c       pic s9(7)v99.` [copybooks/plwspinv2.cob:L32]
    ih_p_c: Decimal = field(metadata=_cited("Invoice-Header.ih-p-c#32"))

    # `05  ih-net       pic s9(7)v99.` [copybooks/plwspinv2.cob:L33]
    ih_net: Decimal = field(metadata=_cited("Invoice-Header.ih-net#33"))

    # `05  ih-extra     pic s9(7)v99.` [copybooks/plwspinv2.cob:L34]
    ih_extra: Decimal = field(metadata=_cited("Invoice-Header.ih-extra#34"))

    # `05  ih-carriage  pic s9(7)v99.` [copybooks/plwspinv2.cob:L35]
    ih_carriage: Decimal = field(metadata=_cited("Invoice-Header.ih-carriage#35"))

    # `05  ih-vat       pic s9(7)v99.` [copybooks/plwspinv2.cob:L36]
    ih_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-vat#36"))

    # `05  ih-discount  pic s9(7)v99.` [copybooks/plwspinv2.cob:L37]
    ih_discount: Decimal = field(metadata=_cited("Invoice-Header.ih-discount#37"))

    # `05  ih-e-vat     pic s9(7)v99.` [copybooks/plwspinv2.cob:L38]
    ih_e_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-e-vat#38"))

    # `05  ih-c-vat     pic s9(7)v99.` [copybooks/plwspinv2.cob:L39]
    ih_c_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-c-vat#39"))


@dataclass(slots=True, kw_only=True)
class IhInvoiceHeader:
    """The header view over the shared buffer.

    `01  Invoice-Header redefines WS-PInvoice-Record.   *> 100 bytes`
    [copybooks/plwspinv2.cob:L21].

    The first of the two redefinitions. The record's own descriptor - the one
    behind `COBOL_DICTIONARY_KEY` - carries `redefines` "WS-PInvoice-Record", which
    is where the COBOL writes the clause; the members below carry none, because the
    COBOL gives them none.

    It has no `ih-prime`/`ih-sub-prime` halves, so where `PInvoiceHeader` reaches
    its twenty-eight leaf fields through those two groups, this class reaches its
    twenty-five directly. Two groups do survive at level 03, `ih-supplier`
    [copybooks/plwspinv2.cob:L24] and `ih-fig` [copybooks/plwspinv2.cob:L31]. The
    sales copybook's equivalent keeps its intermediate groups; that difference is
    one of the fourteen, and it is why the two classes have different shapes rather
    than different names for the same shape.

    Its 88-levels put the lower-case letter first throughout - L41, L42, L43, L51,
    L53 - where the first copybook puts the upper-case letter first. The lists are
    carried in the order declared.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Header.Invoice-Header#21"

    # `03  ih-invoice       pic 9(8).` [copybooks/plwspinv2.cob:L22]
    ih_invoice: int = field(metadata=_cited("Invoice-Header.ih-invoice#22"))

    # `03  ih-test          pic 99.    *> was binary-char.`
    # [copybooks/plwspinv2.cob:L23]
    # Declaration over comment; and no VALUE clause here, where
    # [copybooks/plwspinv.cob:L12] declares one, so no default.
    ih_test: int = field(metadata=_cited("Invoice-Header.ih-test#23"))

    # `03  ih-supplier.` [copybooks/plwspinv2.cob:L24]
    ih_supplier: IhSupplier2 = field(metadata=_cited("Invoice-Header.ih-supplier"))

    # `03  ih-date          binary-long.` [copybooks/plwspinv2.cob:L27]
    ih_date: int = field(metadata=_cited("Invoice-Header.ih-date#27"))

    # `03  ih-order         pic x(10).` [copybooks/plwspinv2.cob:L28]
    # A plain elementary item - no group, no redefinition. The first copybook
    # makes the same ten bytes a group [copybooks/plwspinv.cob:L17] and the
    # sales copybook a picture plus a redefining filler. The third of three
    # treatments, kept as declared.
    ih_order: str = field(metadata=_cited("Invoice-Header.ih-order#28"))

    # `03  ih-type          pic 9.` [copybooks/plwspinv2.cob:L29]
    ih_type: int = field(metadata=_cited("Invoice-Header.ih-type#29"))

    # `03  ih-ref           pic x(10).` [copybooks/plwspinv2.cob:L30]
    ih_ref: str = field(metadata=_cited("Invoice-Header.ih-ref#30"))

    # `03  ih-fig                          comp-3.`
    # [copybooks/plwspinv2.cob:L31]
    ih_fig: IhFig2 = field(metadata=_cited("Invoice-Header.ih-fig#31"))

    # `03  ih-status        pic x.` [copybooks/plwspinv2.cob:L40]
    # Three 88-levels, L41 to L43, LOWER-case first.
    ih_status: str = field(metadata=_cited("Invoice-Header.ih-status#40"))

    # `03  ih-lines         binary-char.` [copybooks/plwspinv2.cob:L44]
    # Declared here immediately before `ih-deduct-days`, as in the other
    # copybook, and moved to the end by the bridge
    # [common/plinvoiceMT.cbl:L418]. The attribute stays where the copybook
    # puts it.
    ih_lines: int = field(metadata=_cited("Invoice-Header.ih-lines#44"))

    # `03  ih-deduct-days   binary-char.` [copybooks/plwspinv2.cob:L45]
    ih_deduct_days: int = field(metadata=_cited("Invoice-Header.ih-deduct-days#45"))

    # `03  ih-deduct-amt    pic 999v99    comp.`
    # [copybooks/plwspinv2.cob:L46]
    # Usage on its own picture line; scale 2, so exact decimal.
    ih_deduct_amt: Decimal = field(metadata=_cited("Invoice-Header.ih-deduct-amt#46"))

    # `03  ih-deduct-vat    pic 999v99    comp.`
    # [copybooks/plwspinv2.cob:L47]
    ih_deduct_vat: Decimal = field(metadata=_cited("Invoice-Header.ih-deduct-vat#47"))

    # `03  ih-days          binary-char.` [copybooks/plwspinv2.cob:L48]
    ih_days: int = field(metadata=_cited("Invoice-Header.ih-days#48"))

    # `03  ih-cr            binary-long.` [copybooks/plwspinv2.cob:L49]
    ih_cr: int = field(metadata=_cited("Invoice-Header.ih-cr#49"))

    # `03  ih-day-book-flag pic x.` [copybooks/plwspinv2.cob:L50]
    # NO VALUE clause here, where [copybooks/plwspinv.cob:L50] declares `value
    # space`. No default is given, because the copybook declares none. One
    # 88-level, L51, lower-case first.
    ih_day_book_flag: str = field(metadata=_cited("Invoice-Header.ih-day-book-flag#50"))

    # `03  ih-update        pic x.` [copybooks/plwspinv2.cob:L52]
    # One 88-level, `ih-analyised`, L53 - the source's spelling, kept.
    ih_update: str = field(metadata=_cited("Invoice-Header.ih-update#52"))

    # A filler follows in the source and is COMMENTED OUT, so nothing is
    # declared for it: `*>     03  filler           pic x(30).   *> This
    # appears to be empty of data on all rec types. 06/05/17`
    # [copybooks/plwspinv2.cob:L54].


@dataclass(slots=True, kw_only=True)
class IlInvoiceLine:
    """The invoice-line view over the shared buffer.

    `01  Invoice-Line  redefines WS-PInvoice-Record.     *> 75 bytes 06/05/17,
    74 bytes 22/12/11` [copybooks/plwspinv2.cob:L56].

    The second redefinition. The record's own descriptor carries `redefines`
    "WS-PInvoice-Record", as the COBOL writes it on the `01`-level and nowhere
    else.

    Summing its declared fields gives 75, which matches the first figure in its own
    comment and not the second, and it redefines a buffer that sums to 100. What
    the compiled program finds past byte 75 of this view is not something this
    module decides.

    Unlike `IlInvoiceLineBody` there is no `OCCURS` and no `il-Key` group: the two
    key members sit flat at level 03. Both `filler pic xx` runs are here, and the
    description is 24 characters, as in the other copybook.
    """

    COBOL_DICTIONARY_KEY: ClassVar[str] = "Invoice-Line.Invoice-Line#56"

    # `03  il-invoice       pic 9(8).` [copybooks/plwspinv2.cob:L57]
    il_invoice: int = field(metadata=_cited("Invoice-Line.il-invoice#57"))

    # `03  il-line          pic 99.    *> was binary-char.`
    # [copybooks/plwspinv2.cob:L58]
    il_line: int = field(metadata=_cited("Invoice-Line.il-line#58"))

    # `03  il-product       pic x(13).    *> +1 18/05/13`
    # [copybooks/plwspinv2.cob:L59]
    il_product: str = field(metadata=_cited("Invoice-Line.il-product#59"))

    # `03  il-pa            pic xx.` [copybooks/plwspinv2.cob:L60]
    il_pa: str = field(metadata=_cited("Invoice-Line.il-pa#60"))

    # `03  filler           pic xx.       *> -1 18/05/13`
    # [copybooks/plwspinv2.cob:L61]
    filler_1: str = field(metadata=_cited("Invoice-Line.filler#61"))

    # `03  il-qty           binary-short.` [copybooks/plwspinv2.cob:L62]
    il_qty: int = field(metadata=_cited("Invoice-Line.il-qty#62"))

    # `03  il-type          pic x.` [copybooks/plwspinv2.cob:L63]
    il_type: str = field(metadata=_cited("Invoice-Line.il-type#63"))

    # `03  il-description   pic x(24).` [copybooks/plwspinv2.cob:L64]
    il_description: str = field(metadata=_cited("Invoice-Line.il-description#64"))

    # `03  filler           pic xx.` [copybooks/plwspinv2.cob:L65]
    filler_2: str = field(metadata=_cited("Invoice-Line.filler#65"))

    # `03  il-net           pic s9(7)v99   comp-3.`
    # [copybooks/plwspinv2.cob:L66]
    il_net: Decimal = field(metadata=_cited("Invoice-Line.il-net#66"))

    # `03  il-unit          pic s9(7)v99   comp-3.`
    # [copybooks/plwspinv2.cob:L67]
    il_unit: Decimal = field(metadata=_cited("Invoice-Line.il-unit#67"))

    # `03  il-discount      pic 99v99      comp.`
    # [copybooks/plwspinv2.cob:L68]
    il_discount: Decimal = field(metadata=_cited("Invoice-Line.il-discount#68"))

    # `03  il-vat           pic s9(7)v99   comp-3.`
    # [copybooks/plwspinv2.cob:L69]
    il_vat: Decimal = field(metadata=_cited("Invoice-Line.il-vat#69"))

    # `03  il-vat-code      pic 9.` [copybooks/plwspinv2.cob:L70]
    il_vat_code: int = field(metadata=_cited("Invoice-Line.il-vat-code#70"))

    # `03  il-update        pic x.` [copybooks/plwspinv2.cob:L71]
    # One 88-level, `il-analyised`, L72.
    il_update: str = field(metadata=_cited("Invoice-Line.il-update#71"))
