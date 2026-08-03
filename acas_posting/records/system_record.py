"""The `01 System-Record.` layout: the widest record in the migration.

`SYSTEM-REC` is the ACAS system record - 1024 bytes in six blocks, 169
MySQL columns, declared across 330 lines of `copybooks/wssystem.cob`. This
module mirrors it field for field as plain dataclasses and does nothing
else. It holds no accounting logic, no predicate over a condition name, no
date conversion, no database access and no clock read. It says what the
record IS, not what any value in it MEANS.

Entity-to-table spine, from Agent Action Plan section 0.2.1.1:

    entity facade  System
    handler        acas000, file-key number 1
    bridge         systemMT
    MySQL table    SYSTEM-REC   (169 columns, primary key SYSTEM-REC-KEY,
                                 no secondary index, no TIMESTAMP and no
                                 AUTO_INCREMENT)
    copybook       copybooks/wssystem.cob

One correction to plan section 0.6.6, which describes the in-scope tables
as having no column-level DEFAULT: `PASS-WORD char(4) NOT NULL DEFAULT ''`
[mysql/ACASDB.sql:L1219], from `Pass-Word pic x(4)`
[copybooks/wssystem.cob:L97], carries the only one in the whole 33-table
frozen schema. It changes nothing here, since the default is reachable
only by a writer that omits the column and every bridge load paragraph
initialises its host-variable group first.

`acas_posting/records/__init__.py` sets out the conventions every record
module follows: descriptors looked up rather than typed by hand (rule
R-5), the six numeric storage classes, exact decimals (R-2), the two
permitted imports, and condition names living in
`acas_posting.cobol.condition_names`.

WHY THIS RECORD MATTERS MORE THAN ITS SIZE SUGGESTS
===================================================
Three reasons, each load-bearing.

1.  It is the SECOND parameter of every in-scope linkage shape, and the
    FIRST argument of every file-handler call. The General Ledger family
    takes `using ws-calling-data, system-record, to-day, file-defs`
    [general/gl071.cbl:L161-L164]; the Sales and Purchase families add a
    fourth system record; and irs030 takes a third, materially different
    shape with neither the calling-data block nor the run date -
    `using IRS-System-Params, WS-System-Record, File-Defs`
    [irs/irs030.cbl:L552-L554]. Handler calls then pass it first, as in
    `call "acas007" using System-Record WS-Batch-Record File-Access
    File-Defs ACAS-DAL-Common-Data` (plan section 0.4.3).

2.  It carries `Run-Date` [copybooks/wssystem.cob:L67], one of the two
    observables the controlled clock pins. Plan section 0.1.1, verbatim:
    "the controlled clock needs to pin exactly two observables - the text
    date `to-day pic x(10)` in DD/MM/CCYY form, and the binary `Run-Date`
    [copybooks/wssystem.cob:L67] - and inject them at the CLI boundary."

3.  It carries the IRS fan-out switch `IRS-Instead`
    [copybooks/wssystem.cob:L179], which decides WHICH TABLES A RUN
    TOUCHES. Plan section 0.6.4 records that it is tested at three sites
    in each of the four Sales and Purchase posting programs - for this
    record's own source references, [sales/sl060.cbl:L1039],
    [sales/sl060.cbl:L1126] and [sales/sl060.cbl:L1175].

THE LEAF CONTRACT, AND THE ONE IMPORT MOST TEMPTING HERE
========================================================
Plan section 0.4.3 grants `records/*.py` only `cobol.field`,
`dictionary.loader` and the standard library, forbidding "anything else -
this keeps the record layer a leaf". So `dal`, `programs`, `cli`, `dates`,
`workfiles`, the rest of `cobol`, `dictionary.generate`, the oracle tree
and every other module of this package are absent - `irs_system.py`
included, despite the rename note below.

`acas_posting.clock` above all, a live temptation precisely because this
record carries `Run-Date`: the clock pins the value and the CLI injects
it, so the dependency runs clock and cli INTO records and never the other
way. A cycle there would break the arithmetic suite, which section 0.4.3
requires to import "only `cobol` and `records`" and touch no database.

WHERE THE FIELD METADATA COMES FROM - NOT FROM THIS FILE
========================================================
Plan section 0.8.1 makes the dictionary-first ordering a directive rather
than a preference, precisely to stop fields being transcribed by eye.
With 169 columns this is where transcription by eye would be both most
likely and most damaging, so no digit count, scale, sign, usage or column
name is written here. `_descriptor` looks every item up through
`acas_posting.dictionary.loader`, keyed by the item's verbatim COBOL name
and declaration line, and hands the key to
`FieldDescriptor.from_dictionary_key`. All 199 items have an entry, so no
item's metadata is stated by hand here - and there is no way to state it,
`from_dictionary_key` being the one factory `FieldDescriptor` offers. The
per-attribute comments quote the copybook declaration and the column, but
they are COMMENTS: the descriptors are what a consumer reads. Each
descriptor's `cite()` delegates to `loader.cite()` for the compact
copybook/bridge/column provenance string; nothing here reimplements it.

HOW THE COBOL DECLARATIONS BECOME PYTHON
========================================
Six conventions, each applied without exception across all 198 attributes.

FILLER items are real named attributes, `filler_<declaration line>`.
    Nine are declared - L81, L211, L252, L278, L299, L308, L323, L324 and
    L327 - and the suffix mirrors how the generated dictionary itself
    disambiguates repeated names, as `FILLER#81`. They are attributes
    rather than metadata-only descriptors because the record's byte layout
    INCLUDES their bytes: summing a block's elementary items reproduces
    the declared block size only when the FILLER bytes are counted, and
    the record's own header reads `*> File size 1024 with fillers`
    [copybooks/wssystem.cob:L7]. Their descriptors carry `is_filler=True`
    from the dictionary rather than asserted here. `FILLER-Dummy4`
    [copybooks/wssystem.cob:L329] is deliberately NOT among the nine: its
    COBOL name is a name, not the FILLER keyword.

Text items default to spaces of the declared width.
    `str` items default to `" " * n` for a `pic x(n)`; a `pic x` defaults
    to a single space. The reason is the bridge's own behaviour, recorded
    in plan section 0.6.2: every load paragraph initialises its
    host-variable group before a write, so an unset text item reaches
    MySQL as spaces and never as SQL NULL - which is why every column in
    the frozen schema can be NOT NULL. Spaces are the value the frozen
    system stores, not a convenience, and the copybook's three `value
    spaces` clauses (L140, L143, L144) and three `value space` clauses
    (L209, L274, L276) already agree with it.

Numeric items default to zero at their declared scale.
    `int` items default to `0`; `Decimal` items to `decimal.Decimal("0.00")`
    - all thirteen scaled items in this record are scale 2, so one quantum
    covers every one. No binary approximation appears anywhere in this file.

Group items become nested dataclasses, built with `default_factory`.
    Fifteen subordinate groups are declared, each becoming its own class
    named as the PascalCase of its COBOL group name with the hyphens
    dropped: `Vat-Rates` -> `VatRates`, `RDBMS-Flat-Statuses` ->
    `RdbmsFlatStatuses`. One group has no name to carry over - see next.

The one ANONYMOUS group is named for what it redefines.
    `05 FILLER redefines PL-Approp-AC6.` [copybooks/wssystem.cob:L323] is a
    FILLER group, so it has no COBOL name. This module calls it
    `PlAppropAc6Parts`, and its class docstring states both the chosen name
    and the anonymous original with its locator, so the mapping is recorded
    rather than silent. Its attribute on the containing block keeps the
    FILLER convention and is therefore `filler_323`.

REDEFINES views are declared, never applied.
    Five appear: `Vat-Rate` over `Vat-Rates` [L61], `Scycle` over
    `cyclea` [L63], `Vat-Group` over `Vat-Rates2` [L316], the anonymous
    group over `PL-Approp-AC6` [L323], and `IRS-Data-Block` over
    `IRS-Entry-Block` [L328]. A REDEFINES is an alternate view of bytes
    already declared, not additional storage. Group redefines become
    classes; elementary redefines stay attributes, with an `OCCURS`
    becoming a `list` because `move x to Vat-Rate(2)` is legal COBOL and
    the element must be assignable. Making the two views share storage
    belongs to the data-access and MOVE layers, not to a layout module,
    and each redefining attribute's comment says so.

Fixed metadata collections are tuples; data collections are lists.
    Every class publishes `FIELDS`, a `ClassVar` tuple of `FieldDescriptor`
    in copybook declaration order - a tuple because R-6 wants fixed
    collections immutable and ordering stable, a `ClassVar` so it is class
    metadata rather than one more dataclass field.

ITEM CENSUS
    199 items are declared, sixteen of them group headers - one being the
    `01` record itself, an attribute of nothing. That leaves 198
    attributes across the sixteen classes below: 95 `int`, 75 `str`, 13
    `decimal.Decimal` and 15 a nested block. 168 of the 199 reach a MySQL
    column; the other 31 are the group headers, the REDEFINES views, the
    FILLER runs and seven elementary items the bridge does not map -
    `Usera` [L71], `Phone-No` [L80], `Maps-Ser-xx` [L126], `Maps-Ser-nn`
    [L127], `SL-BO-Default` [L277], `Vat-Psent` [L317] and `FILLER-Dummy4`
    [L329]. The table has 169 columns because its primary key
    `SYSTEM-REC-KEY` is declared in no copybook at all.

THE RECORD IS MUTABLE WORKING STORAGE - NEVER FROZEN
====================================================
Every class is `@dataclass(slots=True)` and none is frozen, because the
posting cycle writes into this record while it runs: the CLI injects
`Run-Date` [L67] at the boundary; `Next-Invoice` [L66], `Next-Batch`
[L185], `Next-Folio` [L193] and `Next-Post` [L311] are incremented as
documents are posted; and `Current-Quarter` [L110] is rewritten by the
end-of-cycle step. `slots=True` keeps instances compact and stops a typo
silently creating a 170th attribute.

THE ATTRIBUTE THAT COULD NOT KEEP ITS COBOL NAME
================================================
One rename was unavoidable, recorded here so that
`docs/migration/traceability.md` can pick it up (R-5):

    COBOL item      1st-Time-Flag        [copybooks/wssystem.cob:L326]
    dictionary key  SYSTEM-REC.1ST-TIME-FLAG
    column          1ST-TIME-FLAG
    attribute       IrsEntryBlock.first_time_flag

The COBOL name begins with a DIGIT, which no Python identifier may do. The
spelling is not this module's invention: the maintainer's own comment on
that line reads "(was First-Time-Flag in IRS system file)", and irs030
renames the same item `IRS-First-Time-Flag` [irs/irs030.cbl:L448]. The
descriptor keeps the verbatim COBOL name `1st-Time-Flag`, so nothing
downstream has to know about the rename.

WHAT irs030 DOES TO THIS COPYBOOK, AND WHY IT CHANGES NOTHING HERE
==================================================================
`irs030` copies this record and renames 28 of its items in a single
`replacing` clause [irs/irs030.cbl:L419-L448], among them::

    System-Record  by WS-System-Record
    Run-Date       by ACAS-Run-Date      *> these 3 are in binary
    Start-Date     by ACAS-Start-Date    *> IRS expects as x(8)
    End-Date       by ACAS-End-Date      *>  dd/mm/yy
    1st-Time-Flag  by IRS-First-Time-Flag

It has to. The program also copies `copybooks/irswssystem.cob`, itself
renamed `system-record by IRS-System-Params` [irs/irs030.cbl:L416-L417],
and that record declares its own `run-date pic x(8)`
[copybooks/irswssystem.cob:L14] and `start-date pic x(8)`
[copybooks/irswssystem.cob:L21] - TEXT where this record declares BINARY.
Two records with colliding item names in one program is direct evidence
for anomaly A-21, field-name collisions forcing qualified references.

This module records the renames and acts on none. There is no
`acas_run_date` alias, no `x(8)` view of a binary item, and nothing merged
in from `irs_system.py`, which models `irswssystem.cob` separately.

CONDITION NAMES ARE STORAGE HERE, PREDICATES ELSEWHERE
======================================================
This record declares exactly sixty `88` condition names over thirty-seven
items - the largest concentration in the migration. Plan section 0.4.1.4
assigns the predicates over them to
`acas_posting/cobol/condition_names.py`, naming the IRS fan-out names at
[copybooks/wssystem.cob:L179-L181] explicitly. So every `88` name below
appears verbatim in a comment with its value and locator, and not one
predicate, property or constant set is defined for any (R-3). That module
is not imported here either.

THE ANOMALIES THIS MODULE REPRODUCES
====================================
Rule R-4 is unambiguous: "A defect reproduced is a success; a defect fixed
is a failure." Plan section 0.7.4 C-4 asks for a comment at each
reproduction site citing the COBOL locator, and every site below carries
one.

    Group usage on `Vat-Rates comp.` [L55] makes its five children BINARY
    although their own PICTURE lines carry no usage clause, while
    `Vat-Rates2` [L312] leaves its three children ZONED - two
    near-identical VAT-rate groups in one record, one COMP and one
    DISPLAY, never harmonised. Deriving usage from a PICTURE line alone
    would type the five at L56-L60 DISPLAY and corrupt every stored rate.

    The declaration beats the comment. `Page-Lines binary-char unsigned`
    [L65] is annotated `*> 999.` but holds 0..255. Sibling copybooks share
    the habit - `binary-short. *> 9999 comp` [copybooks/wssl.cob:L43],
    `binary-long. *> 9(8) comp` [copybooks/wssl.cob:L45] - so it is a
    house habit, not a slip, and `Stk-Page-Lines` [L306] and
    `Stk-Audit-No` [L307] are annotated `*> 9999 comp.` while likewise
    binary-char unsigned. The comments are recorded; declarations govern.

    `88 Date-Valid-Formats values 1 2 3` [L132] is declared and never
    tested anywhere in the in-scope cycle. Kept, and not newly tested.

    `88 FS-MySql-Used` [L114] and `88 FS-RDBMS-Used` [L116] carry the same
    value 1 - two names for one state.

    `88 OS-Single values 1 2 4` [L109] is a non-contiguous value list, and
    `88 FS-Valid-Options values 0 thru 1` [L122] is the only THRU range in
    this copybook.

    Literal database credentials at L137-L139 with the port at L142, each
    annotated `*> change in setup` - see the dedicated note below.

    Six `GL-*` control accounts [L280-L285] name General-Ledger and
    Purchase-Ledger accounts yet are declared inside the Sales Ledger
    block, under the maintainer's own `*> GL overflow` heading [L279]. They
    stay where the copybook puts them.

    `IRS-Instead` [L179] is a THREE-state switch with only TWO condition
    names; the third state is a space and is unnamed. No name is invented.

    Column-name and signedness drift at the bridge, recorded per attribute
    and reconciled nowhere. Six items are renamed: `Run-Date` ->
    `RUN-DAT`, `Start-Date` -> `START-DAT`, `End-Date` -> `END-DAT`,
    `BL-End-Cycle-Date` -> `BL-END-CYCLE-DAT`, `S-End-Cycle-Date` ->
    `S-END-CYCLE-DAT`, and `System-Record-Version-Secondary` truncated to
    30 characters as `SYSTEM-RECORD-VERSION-SECONDAR`. Forty-one items are
    signed in the copybook and unsigned at both the bridge and the column,
    which is anomaly A-11 and open question Q-3 - a negative value loses
    its sign BEFORE any SQL runs. `SL-Next-Rec` [L275] is the forty-second
    signedness drift and runs the other way, unsigned in the copybook and
    signed at the bridge. The dictionary carries the drift for every item;
    this module carries none of the adjudication, which belongs to the
    data-access layer and has to be measured against the compiled program.

    Bridge-only and group-level columns. `SYSTEM-REC-KEY` is the table's
    primary key and NO copybook declares it, which is exactly why the
    bridge rather than the copybook is the mapping of record to table.
    `Suser` [L70] and `Maps-Ser` [L125] are mapped as GROUP columns while
    their children are not mapped at all - and `Maps-Ser` is a `char(6)`
    column over two children, `pic xx` [L126] and `binary-short` [L127],
    totalling four bytes. Recorded, reconciled nowhere.

ON THE CREDENTIALS IN THE FROZEN SOURCE
=======================================
`RDBMS-DB-Name`, `RDBMS-User`, `RDBMS-Passwd` and `RDBMS-Port` are
declared with literal VALUE clauses in the frozen copybook, each carrying
the maintainer's own `*> change in setup` annotation. They are
placeholders, not live secrets: they already sit in this repository at
`copybooks/wssystem.cob:L137-L142`, they match no credential format any
scanner recognises, and the running system's actual parameters live
outside the checkout. Carrying them verbatim is what R-3 and R-4 require -
they are the copybook's declared defaults, and inventing different ones
would be adding behaviour. This module only DECLARES them; reaching a
database is `acas_posting/dal/connection.py`'s business (plan section
0.4.1.5), and no MySQL driver is imported here.

BYTE LAYOUT
===========
    System-Data-Block     [L52]    512
    General-Ledger-Block  [L150]    80
    Purchase-Ledger-Block [L192]    88
    Sales-Ledger-Block    [L215]   128
    Stock-Control-Block   [L290]    88
    IRS-Entry-Block       [L309]   128
                                 -----
                                  1024

512 + 80 + 88 + 128 + 88 + 128 = 1024, matching `*> File size 1024 with
fillers` [copybooks/wssystem.cob:L7]. `IRS-Data-Block` [L328] adds nothing
- it redefines the 128 bytes of `IRS-Entry-Block`. Each block's own
docstring repeats its size against its declaring line.

THE STOCK BLOCK IS IN SCOPE
===========================
Plan section 0.2.2 puts the `stock/` SUBSYSTEM and the stock tables out of
scope. It does not remove `Stock-Control-Block` [L290] from `SYSTEM-REC`,
whose 169 columns include that block's. Every item there is declared, and
the `88` names `Stock` [L91], `Stock-Audit-On` [L244],
`Stock-Control-Exists` [L301] and `Stock-Averaging` [L303] are legitimate
in-scope `SYSTEM-REC` condition names. No out-of-scope table or bridge is
named in this file.

THE TWO RULES THAT NEED SAYING AGAIN HERE
=========================================
R-1 is covered by the leaf contract above, R-3 by the item census, R-4 by
the anomaly list and R-5 by the per-attribute comments and `FIELDS`. Two
rules bear directly on how the 198 attributes are typed and ordered.

R-2, zero binary approximation. All thirteen scaled items are
`decimal.Decimal` at scale 2 - the five inherited-COMP rates [L56-L60] and
the five-element view over them [L61], the three declared-COMP rates
[L245-L247], the three zoned IRS rates [L313-L315] and the three-element
view over them [L317]. Every `binary-char`, `binary-short` and
`binary-long` item and every scale-0 zoned item is `int`. `Run-Date` [L67]
is an `int` because it is a binary day number; typing it otherwise would
misrepresent its storage and could mask integer truncation elsewhere in
the cycle. The token for the inexact numeric type appears nowhere here.

R-6, compiled behaviour decides, and runs are byte-identical. No clock is
read here, the single most damaging determinism failure this module could
contain: plan section 0.1.1 records that every in-scope posting program
performs ZERO clock reads and takes the date purely through linkage, so
`Run-Date` defaults to 0 and `acas_posting/cli/args.py` injects it from
`acas_posting/clock.py`. Nothing below reads the process environment, a
host name, a user name, an installed-version table or a directory listing,
and no pseudo-arbitrary number source is used. Attribute order is copybook
declaration order throughout; fixed collections are tuples; and the only
import-time input is the loader's own cached dictionary read.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    "FROZEN_PLACEHOLDER_RDBMS_DB_NAME",
    "FROZEN_PLACEHOLDER_RDBMS_PASSWD",
    "FROZEN_PLACEHOLDER_RDBMS_PORT",
    "FROZEN_PLACEHOLDER_RDBMS_USER",
    "GeneralLedgerBlock",
    "IrsDataBlock",
    "IrsEntryBlock",
    "Level",
    "MapsSer",
    "PlAppropAc6Parts",
    "PurchaseLedgerBlock",
    "RdbmsFlatStatuses",
    "SalesLedgerBlock",
    "StockControlBlock",
    "Suser",
    "SystemDataBlock",
    "SystemRecord",
    "VatGroup",
    "VatRates",
    "VatRates2",
    "carries_frozen_placeholder_rdbms_credentials",
)


#  DICTIONARY LOOKUP  (rule R-5, and plan section 0.8.1 "data dictionary
#  first")

# The `01` record name the copybook declares, and the MySQL table the bridge
# maps it to. Both are needed because the dictionary is indexed by whichever
# of the two views an item actually has.
_RECORD: Final[str] = "System-Record"
_MYSQL_TABLE: Final[str] = "SYSTEM-REC"


def _line_of(source_locator: str) -> int:
    """Return the first line number of a `<path>:L<n>` source locator."""
    return int(source_locator.rsplit(":L", 1)[1].split("-")[0])


def _entry_key_index() -> dict[tuple[str, int], str]:
    """Index every dictionary entry key by COBOL name and declaration line.

    A dictionary entry key is `<TABLE>.<COLUMN>` when the item reaches a
    MySQL column and `<COPYBOOK-RECORD>.<FIELD>` when it does not, with a
    `#<line>` suffix disambiguating a repeated name. Neither form can be
    derived from the copybook name by rule: the column name DRIFTS from it -
    `Run-Date` becomes `RUN-DAT`, `System-Record-Version-Secondary` is
    truncated to thirty characters - so guessing a key would silently
    mis-describe dozens of items. Every key is therefore taken from the
    generated artifact.

    Both whole-record accessors are used, in this order and for different
    reasons:

    `loader.entries_for_table(_MYSQL_TABLE)` is the mapping of record to
    table that plan section 0.8.2 designates, and it returns all 169 columns
    in column ordinal order. One of them, the primary key `SYSTEM-REC-KEY`,
    has no copybook view at all - it exists in the bridge host-variable group
    and in the frozen schema only - so it contributes no COBOL item to index
    and is skipped here rather than guessed at.

    `loader.entries_for_copybook_record(_RECORD)` then adds the items that
    reach no column: the group headers, the REDEFINES views and the FILLER
    runs. Its ordering is the artifact's own - column ordinal order first,
    then copybook-only items - so the classes below take their order from
    each item's own declaration line instead, which is what the copybook
    states.

    The index is keyed by `(verbatim COBOL name, declaration line)` because
    the name alone is not unique: nine items are called FILLER. The pair is
    unique across all 199 items of this record.
    """
    index: dict[tuple[str, int], str] = {}
    for entry in loader.entries_for_table(_MYSQL_TABLE):
        item = entry.copybook
        if item is None:
            continue
        index[(item.name, _line_of(item.source))] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD):
        item = entry.copybook
        index[(item.name, _line_of(item.source))] = entry.key
    return index


_KEY_INDEX: Final[dict[tuple[str, int], str]] = _entry_key_index()


def _descriptor(cobol_name: str, line: int) -> FieldDescriptor:
    """Describe one item of this record, by verbatim COBOL name and line.

    The lookup is deliberately total: an item named or numbered wrongly
    fails the index lookup at import time with a `KeyError` naming the pair,
    rather than producing a descriptor that quietly describes the wrong
    storage. Every item of this record has a dictionary entry, so no
    descriptor here is assembled by hand.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_INDEX[(cobol_name, line)])


# The 169 dictionary keys of the columns of SYSTEM-REC, in column ordinal
# order, kept so that a consumer counting the table's width reads the
# artifact rather than this file. 168 of them describe a copybook item; the
# 169th is the bridge-only primary key.
_COLUMN_KEYS: Final[tuple[str, ...]] = tuple(
    entry.key for entry in loader.entries_for_table(_MYSQL_TABLE)
)


#  SUBORDINATE GROUPS OF System-Data-Block


@dataclass(slots=True)
class VatRates:
    """The `05 Vat-Rates comp.` group [copybooks/wssystem.cob:L55].

    Five VAT rates. The group header carries the USAGE and every
    subordinate item inherits it - see the note on the first
    attribute below, which is the highest-risk semantic in this
    record.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Vat-Rate-1", 56),
        _descriptor("Vat-Rate-2", 57),
        _descriptor("Vat-Rate-3", 58),
        _descriptor("Vat-Rate-4", 59),
        _descriptor("Vat-Rate-5", 60),
    )

    # 07 Vat-Rate-1 pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L56]
    # column SYSTEM-REC.VAT-RATE-1 decimal(4,2) unsigned
    # Usage COMP inherited from the group header at L55, not from this line.
    vat_rate_1: decimal.Decimal = decimal.Decimal("0.00")

    # 07 Vat-Rate-2 pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L57]
    # column SYSTEM-REC.VAT-RATE-2 decimal(4,2) unsigned
    # Usage COMP inherited from the group header at L55, not from this line.
    vat_rate_2: decimal.Decimal = decimal.Decimal("0.00")

    # 07 Vat-Rate-3 pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L58]
    # column SYSTEM-REC.VAT-RATE-3 decimal(4,2) unsigned
    # Usage COMP inherited from the group header at L55, not from this line.
    vat_rate_3: decimal.Decimal = decimal.Decimal("0.00")

    # 07 Vat-Rate-4 pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L59]
    # column SYSTEM-REC.VAT-RATE-4 decimal(4,2) unsigned
    # Usage COMP inherited from the group header at L55, not from this line.
    vat_rate_4: decimal.Decimal = decimal.Decimal("0.00")

    # 07 Vat-Rate-5 pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L60]
    # column SYSTEM-REC.VAT-RATE-5 decimal(4,2) unsigned
    # Usage COMP inherited from the group header at L55, not from this line.
    vat_rate_5: decimal.Decimal = decimal.Decimal("0.00")


@dataclass(slots=True)
class Suser:
    """The `05 Suser.` group [copybooks/wssystem.cob:L70].

    One child, and the group rather than the child is what the
    bridge maps to a column.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Usera", 71),
    )

    # 07 Usera pic x(32)
    # str, 32 chars   [copybooks/wssystem.cob:L71]
    # No column of its own - the bridge maps the parent group at L70.
    usera: str = " " * 32


@dataclass(slots=True)
class Level:
    """The `05 Level.` group [copybooks/wssystem.cob:L83].

    Six one-digit sub-system-in-use switches, each with its own 88
    condition name. Level-5 carries two - one for IRS in use and one
    for IRS not in use.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Level-1", 84),
        _descriptor("Level-2", 86),
        _descriptor("Level-3", 88),
        _descriptor("Level-4", 90),
        _descriptor("Level-5", 92),
        _descriptor("Level-6", 95),
    )

    # 07 Level-1 pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L84]
    # column SYSTEM-REC.LEVEL-1 tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 G-L value 1  [copybooks/wssystem.cob:L85]
    level_1: int = 0

    # 07 Level-2 pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L86]
    # column SYSTEM-REC.LEVEL-2 tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 B-L value 1  [copybooks/wssystem.cob:L87]
    level_2: int = 0

    # 07 Level-3 pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L88]
    # column SYSTEM-REC.LEVEL-3 tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 S-L value 1  [copybooks/wssystem.cob:L89]
    level_3: int = 0

    # 07 Level-4 pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L90]
    # column SYSTEM-REC.LEVEL-4 tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Stock value 1  [copybooks/wssystem.cob:L91]
    level_4: int = 0

    # 07 Level-5 pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L92]
    # column SYSTEM-REC.LEVEL-5 tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 IRS value 1  [copybooks/wssystem.cob:L93]
    #   88 IRS-No value zero  [copybooks/wssystem.cob:L94]
    level_5: int = 0

    # 07 Level-6 pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L95]
    # column SYSTEM-REC.LEVEL-6 tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Payroll value 1  [copybooks/wssystem.cob:L96]
    level_6: int = 0


@dataclass(slots=True)
class RdbmsFlatStatuses:
    """The `05 RDBMS-Flat-Statuses.` group [copybooks/wssystem.cob:L111].

    Two one-digit switches choosing the file system in use. Between
    them they carry this copybook's two 88 oddities: two names on
    one value, and its only THRU range.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("File-System-Used", 112),
        _descriptor("File-Duplicates-In-Use", 123),
    )

    # 07 File-System-Used pic 9  ->  int, digits 1, scale 0
    # [copybooks/wssystem.cob:L112]; column FILE-SYSTEM-USED tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to acas_posting/cobol/condition_names.py
    # (plan section 0.4.1.4): `FS-Cobol-Files-Used value zero` [:L113], `FS-MySql-Used value 1`
    # [:L114], `FS-RDBMS-Used value 1` [:L116], `FS-Valid-Options values 0 thru 1` [:L122].
    # Two oddities, both left as they are. FS-MySql-Used (L114) and FS-RDBMS-Used (L116) BOTH
    # carry value 1 - two names for one state. And FS-Valid-Options (L122) is the only THRU
    # range in this copybook.
    file_system_used: int = 0

    # 07 File-Duplicates-In-Use pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L123]
    # column SYSTEM-REC.FILE-DUPLICATES-IN-USE tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 FS-Duplicate-Processing value 1  [copybooks/wssystem.cob:L124]
    file_duplicates_in_use: int = 0


@dataclass(slots=True)
class MapsSer:
    """The `05 Maps-Ser.` group [copybooks/wssystem.cob:L125].

    A serial number in two parts, two characters and a binary
    short. The maintainer notes it is not needed in the open-source
    version.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Maps-Ser-xx", 126),
        _descriptor("Maps-Ser-nn", 127),
    )

    # 07 Maps-Ser-xx pic xx
    # str, 2 chars   [copybooks/wssystem.cob:L126]
    # No column of its own - the bridge maps the parent group at L125.
    maps_ser_xx: str = " " * 2

    # 07 Maps-Ser-nn binary-short
    # int, signed   [copybooks/wssystem.cob:L127]
    # No column of its own - the bridge maps the parent group at L125.
    maps_ser_nn: int = 0


# BLOCK 1 OF 6 - System-Data-Block, 512 bytes [copybooks/wssystem.cob:L52]


@dataclass(slots=True)
class SystemDataBlock:
    """The `03 System-Data-Block.` [copybooks/wssystem.cob:L52].

    512 bytes, the largest of the six blocks, raised from 384 on
    25/06/16. Company identity, the run and cycle dates, the
    sub-system-in-use switches, the date form and the database
    connection parameters.

    Byte layout, summing the elementary items the block declares
    and skipping the two REDEFINES views, which overlay bytes
    already counted: 512, matching the size the copybook states on
    L52.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("System-Record-Version-Prime", 53),
        _descriptor("System-Record-Version-Secondary", 54),
        _descriptor("Vat-Rates", 55),
        _descriptor("Vat-Rate", 61),
        _descriptor("Cyclea", 62),
        _descriptor("Scycle", 63),
        _descriptor("Period", 64),
        _descriptor("Page-Lines", 65),
        _descriptor("Next-Invoice", 66),
        _descriptor("Run-Date", 67),
        _descriptor("Start-Date", 68),
        _descriptor("End-Date", 69),
        _descriptor("Suser", 70),
        _descriptor("User-Code", 72),
        _descriptor("Address-1", 73),
        _descriptor("Address-2", 74),
        _descriptor("Address-3", 75),
        _descriptor("Address-4", 76),
        _descriptor("Post-Code", 77),
        _descriptor("Country", 78),
        _descriptor("Print-Spool-Name", 79),
        _descriptor("Phone-No", 80),
        _descriptor("FILLER", 81),
        _descriptor("Pass-Value", 82),
        _descriptor("Level", 83),
        _descriptor("Pass-Word", 97),
        _descriptor("Host", 98),
        _descriptor("Op-System", 100),
        _descriptor("Current-Quarter", 110),
        _descriptor("RDBMS-Flat-Statuses", 111),
        _descriptor("Maps-Ser", 125),
        _descriptor("Date-Form", 128),
        _descriptor("Data-Capture-Used", 133),
        _descriptor("RDBMS-DB-Name", 137),
        _descriptor("RDBMS-User", 138),
        _descriptor("RDBMS-Passwd", 139),
        _descriptor("VAT-Reg-Number", 140),
        _descriptor("Param-Restrict", 141),
        _descriptor("RDBMS-Port", 142),
        _descriptor("RDBMS-Host", 143),
        _descriptor("RDBMS-Socket", 144),
        _descriptor("Stats-Date-Period", 145),
        _descriptor("Company-Email", 146),
    )

    # 05 System-Record-Version-Prime binary-char
    # int, signed   [copybooks/wssystem.cob:L53]
    # column SYSTEM-REC.SYSTEM-RECORD-VERSION-PRIME tinyint(2) unsigned
    system_record_version_prime: int = 0

    # 05 System-Record-Version-Secondary binary-char
    # int, signed   [copybooks/wssystem.cob:L54]
    # column SYSTEM-REC.SYSTEM-RECORD-VERSION-SECONDAR tinyint(2) unsigned
    # The column name is TRUNCATED to 30 characters at the bridge: the
    # copybook says System-Record-Version-Secondary, the column says
    # SYSTEM-RECORD-VERSION-SECONDAR. Recorded, not reconciled.
    system_record_version_secondary: int = 0

    # 05 Vat-Rates comp
    # group item - no storage of its own   [copybooks/wssystem.cob:L55]
    # GROUP USAGE. The `comp` on THIS line governs the five subordinate
    # items at L56-L60, whose own PICTURE lines carry no usage clause at
    # all. They are therefore BINARY, not zoned display, and their
    # descriptors report usage COMP with usage_declared_at GROUP and
    # usage_inherited_from 'Vat-Rates'. Reading usage from a PICTURE line
    # alone would type all five DISPLAY and every stored VAT rate would be
    # wrong, invisibly. Contrast Vat-Rates2 at L312, whose three children
    # carry no group usage and are genuinely DISPLAY: two near-identical
    # VAT-rate groups in one record, one binary and one zoned. Both stand
    # exactly as declared.
    vat_rates: VatRates = field(default_factory=VatRates)

    # 05 Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L61]
    # REDEFINES the five items above as a 5-element table over the SAME
    # bytes. A REDEFINES is an alternate view, not extra storage; the
    # overlay is applied at the storage boundary by the data-access and MOVE
    # layers, never here. Declared because R-3 requires the record mirror
    # the copybook field for field. No column: the bridge maps the five
    # named items instead.
    vat_rate: list[decimal.Decimal] = field(
        default_factory=lambda: [decimal.Decimal("0.00")] * 5
    )

    # 05 Cyclea binary-char
    # int, signed   [copybooks/wssystem.cob:L62]
    # column SYSTEM-REC.CYCLEA tinyint(2) unsigned
    cyclea: int = 0

    # 05 Scycle redefines cyclea binary-char
    # int, signed   [copybooks/wssystem.cob:L63]
    # REDEFINES `cyclea` - lower case in the frozen source, carried
    # verbatim. No column of its own.
    scycle: int = 0

    # 05 Period binary-char
    # int, signed   [copybooks/wssystem.cob:L64]
    # column SYSTEM-REC.PERIOD tinyint(2) unsigned
    period: int = 0

    # 05 Page-Lines binary-char unsigned
    # int, unsigned   [copybooks/wssystem.cob:L65]
    # column SYSTEM-REC.PAGE-LINES tinyint(3) unsigned
    # DECLARATION BEATS COMMENT (R-4). The inline comment on this line reads
    # `*> 999.` but a binary-char unsigned item holds 0..255, and the
    # descriptor reports that domain. The same habit appears in sibling
    # copybooks - `binary-short. *> 9999 comp` [copybooks/wssl.cob:L43] and
    # `binary-long. *> 9(8) comp` [copybooks/wssl.cob:L45] - so it is a
    # house habit rather than an isolated slip. The comment is recorded; the
    # declaration governs; nothing is reconciled. One of exactly five items
    # in this record carrying the explicit UNSIGNED keyword.
    page_lines: int = 0

    # 05 Next-Invoice binary-long
    # int, signed   [copybooks/wssystem.cob:L66]
    # column SYSTEM-REC.NEXT-INVOICE int(8) unsigned
    # Incremented by the invoice posting path, so this record is mutable
    # working storage and is never frozen.
    next_invoice: int = 0

    # 05 Run-Date binary-long  ->  int, signed  [copybooks/wssystem.cob:L67]
    # column SYSTEM-REC.RUN-DAT int(8) unsigned
    # THE CONTROLLED-CLOCK OBSERVABLE. Plan section 0.1.1: the clock pins exactly two
    # observables - the text date `to-day pic x(10)` and this binary run date - and injects them
    # at the CLI boundary. It defaults to 0 here and is set by acas_posting/cli/args.py from
    # acas_posting/clock.py. This module reads NO clock: the dependency runs clock and cli into
    # records, never the reverse. It is an `int` - a binary day number - never a scaled or
    # binary floating-point value.
    # Column name drift: RUN-DAT, not RUN-DATE. Anomaly A-11 and open question Q-3 apply: signed
    # here, unsigned in both host variable and column, so a negative value loses its sign AT THE
    # BRIDGE, before any SQL runs; what is stored then has to be measured against the compiled
    # program. Renamed ACAS-Run-Date where irs030 copies this record [irs/irs030.cbl:L421].
    run_date: int = 0

    # 05 Start-Date binary-long
    # int, signed   [copybooks/wssystem.cob:L68]
    # column SYSTEM-REC.START-DAT int(8) unsigned
    # Renamed ACAS-Start-Date where irs030 copies this record
    # [irs/irs030.cbl:L422], because copybooks/irswssystem.cob declares its
    # own `start-date pic x(8)` - text where this one is binary. Column name
    # drift: START-DAT. Anomaly A-11 applies.
    start_date: int = 0

    # 05 End-Date binary-long
    # int, signed   [copybooks/wssystem.cob:L69]
    # column SYSTEM-REC.END-DAT int(8) unsigned
    # Renamed ACAS-End-Date where irs030 copies this record
    # [irs/irs030.cbl:L423]. Column name drift: END-DAT. Anomaly A-11
    # applies.
    end_date: int = 0

    # 05 Suser
    # group item - no storage of its own   [copybooks/wssystem.cob:L70]
    # column SYSTEM-REC.SUSER char(32)
    # The BRIDGE MAPS THIS GROUP, not its child: SUSER is a char(32) column
    # and `Usera` at L71 has no column at all. Renamed ACAS-suser where
    # irs030 copies this record [irs/irs030.cbl:L424].
    suser: Suser = field(default_factory=Suser)

    # 05 User-Code pic x(32)
    # str, 32 chars   [copybooks/wssystem.cob:L72]
    # column SYSTEM-REC.USER-CODE char(32)
    user_code: str = " " * 32

    # 05 Address-1 pic x(24)
    # str, 24 chars   [copybooks/wssystem.cob:L73]
    # column SYSTEM-REC.ADDRESS-1 char(24)
    address_1: str = " " * 24

    # 05 Address-2 pic x(24)
    # str, 24 chars   [copybooks/wssystem.cob:L74]
    # column SYSTEM-REC.ADDRESS-2 char(24)
    address_2: str = " " * 24

    # 05 Address-3 pic x(24)
    # str, 24 chars   [copybooks/wssystem.cob:L75]
    # column SYSTEM-REC.ADDRESS-3 char(24)
    address_3: str = " " * 24

    # 05 Address-4 pic x(24)
    # str, 24 chars   [copybooks/wssystem.cob:L76]
    # column SYSTEM-REC.ADDRESS-4 char(24)
    address_4: str = " " * 24

    # 05 Post-Code pic x(12)
    # str, 12 chars   [copybooks/wssystem.cob:L77]
    # column SYSTEM-REC.POST-CODE char(12)
    post_code: str = " " * 12

    # 05 Country pic x(24)
    # str, 24 chars   [copybooks/wssystem.cob:L78]
    # column SYSTEM-REC.COUNTRY char(24)
    country: str = " " * 24

    # 05 Print-Spool-Name pic x(48)
    # str, 48 chars   [copybooks/wssystem.cob:L79]
    # column SYSTEM-REC.PRINT-SPOOL-NAME char(48)
    print_spool_name: str = " " * 48

    # 05 Phone-No pic x(12)
    # str, 12 chars   [copybooks/wssystem.cob:L80]
    # No column: added by the maintainer out of a filler, and the bridge
    # does not map it.
    phone_no: str = " " * 12

    # 05 FILLER pic x(20)
    # str, 20 chars   [copybooks/wssystem.cob:L81]
    filler_81: str = " " * 20

    # 05 Pass-Value pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L82]
    # column SYSTEM-REC.PASS-VALUE tinyint(1) unsigned
    pass_value: int = 0

    # 05 Level
    # group item - no storage of its own   [copybooks/wssystem.cob:L83]
    level: Level = field(default_factory=Level)

    # 05 Pass-Word pic x(4)
    # str, 4 chars   [copybooks/wssystem.cob:L97]
    # column SYSTEM-REC.PASS-WORD char(4)
    pass_word: str = " " * 4

    # 05 Host pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L98]
    # column SYSTEM-REC.HOST tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Multi-User value 1  [copybooks/wssystem.cob:L99]
    host: int = 0

    # 05 Op-System pic 9  ->  int, digits 1, scale 0  [copybooks/wssystem.cob:L100]
    # column SYSTEM-REC.OP-SYSTEM tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to acas_posting/cobol/condition_names.py
    # (plan section 0.4.1.4), declared in this order at [copybooks/wssystem.cob:L101-L109]:
    # `valid-os-type values 1 2 3 4 5 6` (L101), `No-OS value zero` (L102), `Dos value 1`
    # (L103), `Windows value 2` (L104), `Mac value 3` (L105), `Os2 value 4` (L106), `Unix value
    # 5` (L107), `Linux value 6` (L108), `OS-Single values 1 2 4` (L109).
    # Note OS-Single at L109 - a NON-CONTIGUOUS value list, left exactly as declared.
    op_system: int = 0

    # 05 Current-Quarter pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L110]
    # column SYSTEM-REC.CURRENT-QUARTER tinyint(1) unsigned
    current_quarter: int = 0

    # 05 RDBMS-Flat-Statuses
    # group item - no storage of its own   [copybooks/wssystem.cob:L111]
    rdbms_flat_statuses: RdbmsFlatStatuses = field(
        default_factory=RdbmsFlatStatuses
    )

    # 05 Maps-Ser
    # group item - no storage of its own   [copybooks/wssystem.cob:L125]
    # column SYSTEM-REC.MAPS-SER char(6)
    # The BRIDGE MAPS THIS GROUP as a char(6) column while its two children
    # at L126-L127 total four bytes, and neither child has a column.
    # Recorded, not reconciled.
    maps_ser: MapsSer = field(default_factory=MapsSer)

    # 05 Date-Form pic 9  ->  int, digits 1, scale 0  [copybooks/wssystem.cob:L128]
    # column SYSTEM-REC.DATE-FORM tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to acas_posting/cobol/condition_names.py
    # (plan section 0.4.1.4): `Date-UK value 1` [:L129], `Date-USA value 2` [:L130], `Date-Intl
    # value 3` [:L131], `Date-Valid-Formats values 1 2 3` [:L132].
    # Date-Valid-Formats (L132) is DECLARED BUT NEVER TESTED anywhere in the in-scope cycle.
    # Recorded as found; not deleted, and not newly tested either - R-3 forbids adding a
    # validation the frozen source does not perform.
    date_form: int = 0

    # 05 Data-Capture-Used pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L133]
    # column SYSTEM-REC.DATA-CAPTURE-USED tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 DC-Cobol-Standard value zero  [copybooks/wssystem.cob:L134]
    #   88 DC-GUI value 1  [copybooks/wssystem.cob:L135]
    #   88 DC-Widget value 2  [copybooks/wssystem.cob:L136]
    data_capture_used: int = 0

    # 05 RDBMS-DB-Name pic x(12) value "ACASDB"
    # str, 12 chars   [copybooks/wssystem.cob:L137]
    # column SYSTEM-REC.RDBMS-DB-NAME char(12)
    # LITERAL DATABASE CREDENTIALS IN THE FROZEN SOURCE (L137-L139, and the
    # port at L142). They are the copybook's own VALUE clauses, so they are
    # carried as the declared defaults and are neither read from the
    # environment nor from a configuration file (R-6 determinism, R-3
    # nothing added). This record only DECLARES them;
    # acas_posting/dal/connection.py owns actually reaching the database,
    # per plan section 0.4.1.5, and this module imports no database driver
    # at all (R-1). The values below are the maintainer's placeholders,
    # annotated `*> change in setup` on every one of the four lines.
    rdbms_db_name: str = "ACASDB".ljust(12)

    # 05 RDBMS-User pic x(12) value "ACAS-User"
    # str, 12 chars   [copybooks/wssystem.cob:L138]
    # column SYSTEM-REC.RDBMS-USER char(12)
    rdbms_user: str = "ACAS-User".ljust(12)

    # 05 RDBMS-Passwd pic x(12) value "PaSsWoRd"
    # str, 12 chars   [copybooks/wssystem.cob:L139]
    # column SYSTEM-REC.RDBMS-PASSWD char(12)
    #
    # ⭐ `repr=False`, AND NOTHING ELSE ABOUT THIS FIELD CHANGES. It is still
    # declared here, in this position, as `x(12)`, with the copybook's own
    # placeholder `VALUE` padded to twelve characters exactly as before - so the
    # layout, the declaration order, the default, the `FIELDS` tuple above and
    # every dictionary and descriptor lookup are byte-for-byte what they were
    # (rules R-3 and R-5). The column it maps to is untouched, and the value still
    # reaches `RDB-Data.DB-UPass` through the six frozen moves
    # [common/acas008.cbl:L558-L563].
    #
    # What changes is the DEFAULT `__repr__` this dataclass generates. SYSTEM-REC
    # is the largest record in the migration - 169 columns of company identity,
    # addresses and operator names - and rendering it whole put a password in the
    # middle of that. Nothing in the cycle renders the block today, which is why
    # this is INFO rather than a live leak; but the hazard is one
    # `_LOG.debug("%s", system_record)` or one failing assertion away, and a
    # password written to a log cannot be taken back (CWE-532).
    #
    # THE VALUE IS NOT MASKED, only its rendering omitted, and the credential
    # question itself is settled elsewhere and is not reopened here:
    # `carries_frozen_placeholder_rdbms_credentials` still reads this field, and
    # `dal/connection.py` still refuses to authenticate with the shipped
    # placeholder unless the caller declares the server disposable.
    rdbms_passwd: str = field(default="PaSsWoRd".ljust(12), repr=False)

    # 05 VAT-Reg-Number pic x(11) value spaces
    # str, 11 chars   [copybooks/wssystem.cob:L140]
    # column SYSTEM-REC.VAT-REG-NUMBER char(11)
    # Declared `value spaces` in the frozen source.
    vat_reg_number: str = " " * 11

    # 05 Param-Restrict pic x
    # str, 1 chars   [copybooks/wssystem.cob:L141]
    # column SYSTEM-REC.PARAM-RESTRICT char(1)
    param_restrict: str = " "

    # 05 RDBMS-Port pic x(5) value "3306"
    # str, 5 chars   [copybooks/wssystem.cob:L142]
    # column SYSTEM-REC.RDBMS-PORT char(5)
    rdbms_port: str = "3306".ljust(5)

    # 05 RDBMS-Host pic x(32) value spaces
    # str, 32 chars   [copybooks/wssystem.cob:L143]
    # column SYSTEM-REC.RDBMS-HOST char(32)
    # Declared `value spaces` in the frozen source.
    rdbms_host: str = " " * 32

    # 05 RDBMS-Socket pic x(64) value spaces
    # str, 64 chars   [copybooks/wssystem.cob:L144]
    # column SYSTEM-REC.RDBMS-SOCKET char(64)
    # Declared `value spaces` in the frozen source.
    rdbms_socket: str = " " * 64

    # 05 Stats-Date-Period pic 9(4)
    # int, digits 4, scale 0   [copybooks/wssystem.cob:L145]
    # column SYSTEM-REC.STATS-DATE-PERIOD char(4)
    stats_date_period: int = 0

    # 05 Company-Email pic x(30)
    # str, 30 chars   [copybooks/wssystem.cob:L146]
    # column SYSTEM-REC.COMPANY-EMAIL char(30)
    company_email: str = " " * 30


# =============================================================================
#  THE FROZEN PLACEHOLDER RDBMS CREDENTIALS  (declared above, published here)
# =============================================================================
#  The four items at [copybooks/wssystem.cob:L137-L139] and L142 are the only
#  place in the whole migrated cycle where a user name, a password, a schema
#  name and a port arrive from a SOURCE LITERAL rather than from a stored row,
#  and the maintainer annotated every one of the four lines `*> change in
#  setup`. They are shipped placeholders: an installer is expected to replace
#  them before the system ever reaches a real server.
#
#  This module DECLARES them and must keep declaring them byte-for-byte, for
#  two reasons that are both hard constraints. `SYSTEM-REC` is one of the 22
#  tables the scenario comparison dumps, so its 169 declared defaults are
#  diff-visible and changing one would move a compared value (rule R-4). And
#  reading a credential from the process environment, a dotenv file or a
#  parameter file would introduce an ambient input the frozen source does not
#  have, which rule R-6 (determinism) and rule R-3 (nothing added) both forbid.
#
#  What this section adds is therefore NOT a change of behaviour but a way to
#  ASK a question: "is this record still carrying the shipped placeholders?"
#  `acas_posting/dal/connection.py` is the one module that reaches a real
#  server, and on a yes it reports the exposure - and refuses only when the
#  deployment's installed policy asked it to, since the compiled program applies
#  no such check (rule R-3). Publishing the four values here - read out of
#  this module's own declared defaults, never transcribed a second time - is
#  what lets that module do so without owning a copy of the literals.
#
#  Nothing below is applied by this module: constructing a `SystemDataBlock` or
#  a `SystemRecord` behaves exactly as it did before, and the predicate is a
#  pure query over a record the caller already holds.


def _declared_system_data_block() -> SystemDataBlock:
    """Return a fresh `System-Data-Block` holding only its declared defaults.

    A brand-new instance per call, so this module holds no shared mutable state
    at module scope and no later mutation of a real record can reach the
    constants derived below. Pure in-memory work - no file, no connection and
    nothing read from the surroundings - so it is safe at import time.

    Returns:
        A `SystemDataBlock` whose items carry exactly what the frozen copybook
        declares.
    """
    return SystemDataBlock()


#  `05 RDBMS-DB-Name pic x(12) value "ACASDB"` [copybooks/wssystem.cob:L137],
#  space-filled to its declared width, as a `MOVE` of the literal into the item
#  leaves it.
FROZEN_PLACEHOLDER_RDBMS_DB_NAME: Final[str] = (
    _declared_system_data_block().rdbms_db_name
)

#  `05 RDBMS-User pic x(12) value "ACAS-User"` [copybooks/wssystem.cob:L138].
FROZEN_PLACEHOLDER_RDBMS_USER: Final[str] = (
    _declared_system_data_block().rdbms_user
)

#  `05 RDBMS-Passwd pic x(12) value "PaSsWoRd"` [copybooks/wssystem.cob:L139] -
#  a password in plain source text. Reproduced exactly as declared, and never
#  used to reach a real server without an explicit opt-in; see the module named
#  above.
FROZEN_PLACEHOLDER_RDBMS_PASSWD: Final[str] = (
    _declared_system_data_block().rdbms_passwd
)

#  `05 RDBMS-Port pic x(5) value "3306"` [copybooks/wssystem.cob:L142]. Not a
#  credential; published for completeness because it is the fourth of the four
#  `*> change in setup` items and a caller reporting on the set wants all four.
FROZEN_PLACEHOLDER_RDBMS_PORT: Final[str] = (
    _declared_system_data_block().rdbms_port
)


def carries_frozen_placeholder_rdbms_credentials(
    system_record: SystemRecord,
) -> bool:
    """Report whether `SYSTEM-REC` still carries the shipped credentials.

    A pure query. Nothing is validated, nothing is rejected and nothing is
    mutated: the caller decides what a `True` means, and only
    `acas_posting/dal/connection.py` acts on it.

    The test is an OR rather than an AND, and that is deliberately the weaker
    condition to satisfy: a deployment that replaced the user but left the
    maintainer's password - or the reverse - is still reaching a server with a
    value published in the frozen source and in this file, which is exactly the
    exposure being guarded. The schema name and the port take no part; neither
    is a credential.

    Trailing spaces are ignored on both sides, which is COBOL's own comparison
    semantics rather than a convenience: `if RDBMS-User = "ACAS-User"` pads the
    literal to the item's `PIC X(12)` width before comparing, so a caller who
    assigned an unpadded `"ACAS-User"` is carrying the placeholder just as
    surely as one who padded it. Case is significant, again as COBOL compares.

    Args:
        system_record: the record a caller is about to open a connection from.
            Read only; never mutated.

    Returns:
        `True` when the user name or the password still equals its declared
        placeholder, `False` when both have been replaced.
    """
    block = system_record.system_data_block
    user_is_placeholder = (
        block.rdbms_user.rstrip() == FROZEN_PLACEHOLDER_RDBMS_USER.rstrip()
    )
    passwd_is_placeholder = (
        block.rdbms_passwd.rstrip() == FROZEN_PLACEHOLDER_RDBMS_PASSWD.rstrip()
    )
    return user_is_placeholder or passwd_is_placeholder



# =============================================================================
# BLOCK 2 OF 6 - General-Ledger-Block, 80 bytes [copybooks/wssystem.cob:L150]


@dataclass(slots=True)
class GeneralLedgerBlock:
    """The `03 General-Ledger-Block.` [copybooks/wssystem.cob:L150].

    80 bytes. Profit-centre and comparative settings, the automatic
    VAT switch, the batch and posting counters, the two control
    accounts, and the IRS fan-out switch that decides which tables a
    posting run touches.

    Byte layout: 80, matching the size the copybook states on L150.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("P-C", 151),
        _descriptor("P-C-Grouped", 154),
        _descriptor("P-C-Level", 156),
        _descriptor("Comps", 158),
        _descriptor("Comps-Active", 160),
        _descriptor("M-V", 162),
        _descriptor("Arch", 164),
        _descriptor("Trans-Print", 166),
        _descriptor("Trans-Printed", 168),
        _descriptor("Header-Level", 170),
        _descriptor("Sales-Range", 171),
        _descriptor("Purchase-Range", 172),
        _descriptor("Vat", 173),
        _descriptor("Batch-Id", 175),
        _descriptor("Ledger-2nd-Index", 177),
        _descriptor("IRS-Instead", 179),
        _descriptor("Ledger-Sec", 182),
        _descriptor("Updates", 183),
        _descriptor("Postings", 184),
        _descriptor("Next-Batch", 185),
        _descriptor("Extra-Charge-Ac", 186),
        _descriptor("Vat-Ac", 187),
        _descriptor("Print-Spool-Name2", 188),
    )

    # 05 P-C pic x
    # str, 1 chars   [copybooks/wssystem.cob:L151]
    # column SYSTEM-REC.P-C char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Profit-Centres value "P"  [copybooks/wssystem.cob:L152]
    #   88 Branches value "B"  [copybooks/wssystem.cob:L153]
    p_c: str = " "

    # 05 P-C-Grouped pic x
    # str, 1 chars   [copybooks/wssystem.cob:L154]
    # column SYSTEM-REC.P-C-GROUPED char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Grouped value "Y"  [copybooks/wssystem.cob:L155]
    p_c_grouped: str = " "

    # 05 P-C-Level pic x
    # str, 1 chars   [copybooks/wssystem.cob:L156]
    # column SYSTEM-REC.P-C-LEVEL char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Revenue-Only value "R"  [copybooks/wssystem.cob:L157]
    p_c_level: str = " "

    # 05 Comps pic x
    # str, 1 chars   [copybooks/wssystem.cob:L158]
    # column SYSTEM-REC.COMPS char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Comparatives value "Y"  [copybooks/wssystem.cob:L159]
    comps: str = " "

    # 05 Comps-Active pic x
    # str, 1 chars   [copybooks/wssystem.cob:L160]
    # column SYSTEM-REC.COMPS-ACTIVE char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Comparatives-Active value "Y"  [copybooks/wssystem.cob:L161]
    comps_active: str = " "

    # 05 M-V pic x
    # str, 1 chars   [copybooks/wssystem.cob:L162]
    # column SYSTEM-REC.M-V char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Minimum-Validation value "Y"  [copybooks/wssystem.cob:L163]
    m_v: str = " "

    # 05 Arch pic x
    # str, 1 chars   [copybooks/wssystem.cob:L164]
    # column SYSTEM-REC.ARCH char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Archiving value "Y"  [copybooks/wssystem.cob:L165]
    arch: str = " "

    # 05 Trans-Print pic x
    # str, 1 chars   [copybooks/wssystem.cob:L166]
    # column SYSTEM-REC.TRANS-PRINT char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Mandatory value "Y"  [copybooks/wssystem.cob:L167]
    trans_print: str = " "

    # 05 Trans-Printed pic x
    # str, 1 chars   [copybooks/wssystem.cob:L168]
    # column SYSTEM-REC.TRANS-PRINTED char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Trans-Done value "Y"  [copybooks/wssystem.cob:L169]
    trans_printed: str = " "

    # 05 Header-Level pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L170]
    # column SYSTEM-REC.HEADER-LEVEL tinyint(1) unsigned
    header_level: int = 0

    # 05 Sales-Range pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L171]
    # column SYSTEM-REC.SALES-RANGE tinyint(1) unsigned
    sales_range: int = 0

    # 05 Purchase-Range pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L172]
    # column SYSTEM-REC.PURCHASE-RANGE tinyint(1) unsigned
    purchase_range: int = 0

    # 05 Vat pic x
    # str, 1 chars   [copybooks/wssystem.cob:L173]
    # column SYSTEM-REC.VAT char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Auto-Vat value "Y"  [copybooks/wssystem.cob:L174]
    vat: str = " "

    # 05 Batch-Id pic x
    # str, 1 chars   [copybooks/wssystem.cob:L175]
    # column SYSTEM-REC.BATCH-ID char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Preserve-Batch value "Y"  [copybooks/wssystem.cob:L176]
    batch_id: str = " "

    # 05 Ledger-2nd-Index pic x
    # str, 1 chars   [copybooks/wssystem.cob:L177]
    # column SYSTEM-REC.LEDGER-2ND-INDEX char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Index-2 value "Y"  [copybooks/wssystem.cob:L178]
    ledger_2nd_index: str = " "

    # 05 IRS-Instead pic x  ->  str, 1 chars  [copybooks/wssystem.cob:L179]
    # column SYSTEM-REC.IRS-INSTEAD char(1)
    # 88 condition names, verbatim - predicates belong to acas_posting/cobol/condition_names.py
    # (plan section 0.4.1.4): `IRS-Used value "Y"` [:L180], `IRS-Both-Used value "B"` [:L181].
    # THE IRS FAN-OUT SWITCH - a THREE-state field with only TWO condition names. 'Y' (L180) and
    # 'B' (L181) are named; the third state is a SPACE and is UNNAMED in the frozen source, so
    # no name is invented for it here. Which tables a run touches depends on it, and it is
    # tested at three sites in each of the four Sales and Purchase posting programs -
    # [sales/sl060.cbl:L1039], [:L1126] and [:L1175]. Plan section 0.6.4 therefore requires
    # every scenario definition to pin it explicitly rather than leave it at a default.
    irs_instead: str = " "

    # 05 Ledger-Sec binary-short
    # int, signed   [copybooks/wssystem.cob:L182]
    # column SYSTEM-REC.LEDGER-SEC smallint(4) unsigned
    ledger_sec: int = 0

    # 05 Updates binary-short
    # int, signed   [copybooks/wssystem.cob:L183]
    # column SYSTEM-REC.UPDATES smallint(4) unsigned
    updates: int = 0

    # 05 Postings binary-short
    # int, signed   [copybooks/wssystem.cob:L184]
    # column SYSTEM-REC.POSTINGS smallint(4) unsigned
    postings: int = 0

    # 05 Next-Batch binary-short
    # int, signed   [copybooks/wssystem.cob:L185]
    # column SYSTEM-REC.NEXT-BATCH smallint(4) unsigned
    # Incremented by the posting programs; see the mutability note at L66.
    next_batch: int = 0

    # 05 Extra-Charge-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L186]
    # column SYSTEM-REC.EXTRA-CHARGE-AC int(8) unsigned
    extra_charge_ac: int = 0

    # 05 Vat-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L187]
    # column SYSTEM-REC.VAT-AC int(8) unsigned
    vat_ac: int = 0

    # 05 Print-Spool-Name2 pic x(48)
    # str, 48 chars   [copybooks/wssystem.cob:L188]
    # column SYSTEM-REC.PRINT-SPOOL-NAME2 char(48)
    print_spool_name2: str = " " * 48


# BLOCK 3 OF 6 - Purchase-Ledger-Block, 88 bytes [copybooks/wssystem.cob:L192]


@dataclass(slots=True)
class PurchaseLedgerBlock:
    """The `03 Purchase-Ledger-Block.` [copybooks/wssystem.cob:L192].

    88 bytes. The purchase folio and batch counters, four control
    accounts, the cycle-end date and the entry-level switches.

    Byte layout: 88, matching the size the copybook states on L192.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Next-Folio", 193),
        _descriptor("BL-Pay-Ac", 194),
        _descriptor("P-Creditors", 195),
        _descriptor("BL-Purch-Ac", 196),
        _descriptor("BL-End-Cycle-Date", 197),
        _descriptor("BL-Next-Batch", 198),
        _descriptor("Age-To-Pay", 199),
        _descriptor("Purchase-Ledger", 200),
        _descriptor("PL-Delim", 202),
        _descriptor("Entry-Level", 203),
        _descriptor("P-Flag-A", 204),
        _descriptor("P-Flag-I", 205),
        _descriptor("P-Flag-P", 206),
        _descriptor("PL-Stock-Link", 207),
        _descriptor("Print-Spool-Name3", 208),
        _descriptor("PL-Autogen", 209),
        _descriptor("PL-Next-Rec", 210),
        _descriptor("FILLER", 211),
    )

    # 05 Next-Folio binary-long
    # int, signed   [copybooks/wssystem.cob:L193]
    # column SYSTEM-REC.NEXT-FOLIO int(8) unsigned
    # Incremented by the purchase posting path; see the note at L66.
    next_folio: int = 0

    # 05 BL-Pay-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L194]
    # column SYSTEM-REC.BL-PAY-AC int(8) unsigned
    bl_pay_ac: int = 0

    # 05 P-Creditors binary-long
    # int, signed   [copybooks/wssystem.cob:L195]
    # column SYSTEM-REC.P-CREDITORS int(8) unsigned
    p_creditors: int = 0

    # 05 BL-Purch-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L196]
    # column SYSTEM-REC.BL-PURCH-AC int(8) unsigned
    bl_purch_ac: int = 0

    # 05 BL-End-Cycle-Date binary-long
    # int, signed   [copybooks/wssystem.cob:L197]
    # column SYSTEM-REC.BL-END-CYCLE-DAT int(1) unsigned
    # Column name drift: BL-END-CYCLE-DAT. Anomaly A-11 applies.
    bl_end_cycle_date: int = 0

    # 05 BL-Next-Batch binary-short
    # int, signed   [copybooks/wssystem.cob:L198]
    # column SYSTEM-REC.BL-NEXT-BATCH smallint(4) unsigned
    bl_next_batch: int = 0

    # 05 Age-To-Pay binary-char
    # int, signed   [copybooks/wssystem.cob:L199]
    # column SYSTEM-REC.AGE-TO-PAY smallint(4) unsigned
    age_to_pay: int = 0

    # 05 Purchase-Ledger pic x
    # str, 1 chars   [copybooks/wssystem.cob:L200]
    # column SYSTEM-REC.PURCHASE-LEDGER char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 P-L-Exists value "Y"  [copybooks/wssystem.cob:L201]
    purchase_ledger: str = " "

    # 05 PL-Delim pic x
    # str, 1 chars   [copybooks/wssystem.cob:L202]
    # column SYSTEM-REC.PL-DELIM char(1)
    pl_delim: str = " "

    # 05 Entry-Level pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L203]
    # column SYSTEM-REC.ENTRY-LEVEL tinyint(1) unsigned
    entry_level: int = 0

    # 05 P-Flag-A pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L204]
    # column SYSTEM-REC.P-FLAG-A tinyint(1) unsigned
    p_flag_a: int = 0

    # 05 P-Flag-I pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L205]
    # column SYSTEM-REC.P-FLAG-I tinyint(1) unsigned
    p_flag_i: int = 0

    # 05 P-Flag-P pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L206]
    # column SYSTEM-REC.P-FLAG-P tinyint(1) unsigned
    p_flag_p: int = 0

    # 05 PL-Stock-Link pic x
    # str, 1 chars   [copybooks/wssystem.cob:L207]
    # column SYSTEM-REC.PL-STOCK-LINK char(1)
    pl_stock_link: str = " "

    # 05 Print-Spool-Name3 pic x(48)
    # str, 48 chars   [copybooks/wssystem.cob:L208]
    # column SYSTEM-REC.PRINT-SPOOL-NAME3 char(48)
    print_spool_name3: str = " " * 48

    # 05 PL-Autogen pic x value space
    # str, 1 chars   [copybooks/wssystem.cob:L209]
    # column SYSTEM-REC.PL-AUTOGEN char(1)
    # Declared `value space` in the frozen source.
    pl_autogen: str = " "

    # 05 PL-Next-Rec binary-short unsigned
    # int, unsigned   [copybooks/wssystem.cob:L210]
    # column SYSTEM-REC.PL-NEXT-REC smallint(4) unsigned
    pl_next_rec: int = 0

    # 05 FILLER pic x(7)
    # str, 7 chars   [copybooks/wssystem.cob:L211]
    filler_211: str = " " * 7


# BLOCK 4 OF 6 - Sales-Ledger-Block, 128 bytes [copybooks/wssystem.cob:L215]


@dataclass(slots=True)
class SalesLedgerBlock:
    """The `03 Sales-Ledger-Block.` [copybooks/wssystem.cob:L215].

    128 bytes, and the widest of the five subordinate blocks. The
    invoicing level, the discount and late-payment rates, the ageing
    day bands, five control accounts - and, at L280-L285, six
    General-Ledger and Purchase-Ledger accounts that the maintainer
    put here rather than in the blocks their names match. See the
    note on the first of those six.

    Byte layout: 128, matching the size the copybook states on L215.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Sales-Ledger", 216),
        _descriptor("SL-Delim", 218),
        _descriptor("Oi-3-Flag", 219),
        _descriptor("Cust-Flag", 220),
        _descriptor("Oi-5-Flag", 221),
        _descriptor("S-Flag-Oi-3", 222),
        _descriptor("Full-Invoicing", 223),
        _descriptor("S-Flag-A", 224),
        _descriptor("S-Flag-I", 225),
        _descriptor("S-Flag-P", 226),
        _descriptor("SL-Dunning", 227),
        _descriptor("SL-Charges", 228),
        _descriptor("Sl-Own-Nos", 229),
        _descriptor("SL-Stats-Run", 230),
        _descriptor("Sl-Day-Book", 231),
        _descriptor("invoicer", 232),
        _descriptor("Extra-Desc", 237),
        _descriptor("Extra-Type", 238),
        _descriptor("Extra-Print", 241),
        _descriptor("SL-Stock-Link", 242),
        _descriptor("SL-Stock-Audit", 243),
        _descriptor("SL-Late-Per", 245),
        _descriptor("SL-Disc", 246),
        _descriptor("Extra-Rate", 247),
        _descriptor("SL-Days-1", 248),
        _descriptor("SL-Days-2", 249),
        _descriptor("SL-Days-3", 250),
        _descriptor("SL-Credit", 251),
        _descriptor("FILLER", 252),
        _descriptor("SL-Min", 253),
        _descriptor("SL-Max", 254),
        _descriptor("PF-Retention", 255),
        _descriptor("First-Sl-Batch", 256),
        _descriptor("First-Sl-Inv", 257),
        _descriptor("SL-Limit", 258),
        _descriptor("SL-Pay-Ac", 259),
        _descriptor("S-Debtors", 260),
        _descriptor("SL-Sales-Ac", 261),
        _descriptor("S-End-Cycle-Date", 262),
        _descriptor("SL-Comp-Head-Pick", 263),
        _descriptor("SL-Comp-Head-Inv", 265),
        _descriptor("SL-Comp-Head-Stat", 267),
        _descriptor("SL-Comp-Head-Lets", 269),
        _descriptor("SL-VAT-Printed", 271),
        _descriptor("SL-Invoice-Lines", 273),
        _descriptor("SL-Autogen", 274),
        _descriptor("SL-Next-Rec", 275),
        _descriptor("SL-BO-Flag", 276),
        _descriptor("SL-BO-Default", 277),
        _descriptor("FILLER", 278),
        _descriptor("GL-BL-Pay-Ac", 280),
        _descriptor("GL-P-Creditors", 281),
        _descriptor("GL-BL-Purch-Ac", 282),
        _descriptor("GL-SL-Pay-Ac", 283),
        _descriptor("GL-S-Debtors", 284),
        _descriptor("GL-SL-Sales-Ac", 285),
    )

    # 05 Sales-Ledger pic x
    # str, 1 chars   [copybooks/wssystem.cob:L216]
    # column SYSTEM-REC.SALES-LEDGER char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 S-L-Exists value "Y"  [copybooks/wssystem.cob:L217]
    sales_ledger: str = " "

    # 05 SL-Delim pic x
    # str, 1 chars   [copybooks/wssystem.cob:L218]
    # column SYSTEM-REC.SL-DELIM char(1)
    sl_delim: str = " "

    # 05 Oi-3-Flag pic x
    # str, 1 chars   [copybooks/wssystem.cob:L219]
    # column SYSTEM-REC.OI-3-FLAG char(1)
    oi_3_flag: str = " "

    # 05 Cust-Flag pic x
    # str, 1 chars   [copybooks/wssystem.cob:L220]
    # column SYSTEM-REC.CUST-FLAG char(1)
    cust_flag: str = " "

    # 05 Oi-5-Flag pic x
    # str, 1 chars   [copybooks/wssystem.cob:L221]
    # column SYSTEM-REC.OI-5-FLAG char(1)
    oi_5_flag: str = " "

    # 05 S-Flag-Oi-3 pic x
    # str, 1 chars   [copybooks/wssystem.cob:L222]
    # column SYSTEM-REC.S-FLAG-OI-3 char(1)
    s_flag_oi_3: str = " "

    # 05 Full-Invoicing pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L223]
    # column SYSTEM-REC.FULL-INVOICING tinyint(1) unsigned
    full_invoicing: int = 0

    # 05 S-Flag-A pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L224]
    # column SYSTEM-REC.S-FLAG-A tinyint(1) unsigned
    s_flag_a: int = 0

    # 05 S-Flag-I pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L225]
    # column SYSTEM-REC.S-FLAG-I tinyint(1) unsigned
    s_flag_i: int = 0

    # 05 S-Flag-P pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L226]
    # column SYSTEM-REC.S-FLAG-P tinyint(1) unsigned
    s_flag_p: int = 0

    # 05 SL-Dunning pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L227]
    # column SYSTEM-REC.SL-DUNNING tinyint(1) unsigned
    sl_dunning: int = 0

    # 05 SL-Charges pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L228]
    # column SYSTEM-REC.SL-CHARGES tinyint(1) unsigned
    sl_charges: int = 0

    # 05 Sl-Own-Nos pic x
    # str, 1 chars   [copybooks/wssystem.cob:L229]
    # column SYSTEM-REC.SL-OWN-NOS char(1)
    sl_own_nos: str = " "

    # 05 SL-Stats-Run pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L230]
    # column SYSTEM-REC.SL-STATS-RUN tinyint(1) unsigned
    sl_stats_run: int = 0

    # 05 Sl-Day-Book pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L231]
    # column SYSTEM-REC.SL-DAY-BOOK tinyint(1) unsigned
    sl_day_book: int = 0

    # 05 invoicer pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L232]
    # column SYSTEM-REC.INVOICER tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 I-Level-0 value 0  [copybooks/wssystem.cob:L233]
    #   88 I-Level-1 value 1  [copybooks/wssystem.cob:L234]
    #   88 I-Level-2 value 2  [copybooks/wssystem.cob:L235]
    #   88 Not-Invoicing value 9  [copybooks/wssystem.cob:L236]
    invoicer: int = 0

    # 05 Extra-Desc pic x(14)
    # str, 14 chars   [copybooks/wssystem.cob:L237]
    # column SYSTEM-REC.EXTRA-DESC char(14)
    extra_desc: str = " " * 14

    # 05 Extra-Type pic x
    # str, 1 chars   [copybooks/wssystem.cob:L238]
    # column SYSTEM-REC.EXTRA-TYPE char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Discount value "D"  [copybooks/wssystem.cob:L239]
    #   88 Charge value "C"  [copybooks/wssystem.cob:L240]
    extra_type: str = " "

    # 05 Extra-Print pic x
    # str, 1 chars   [copybooks/wssystem.cob:L241]
    # column SYSTEM-REC.EXTRA-PRINT char(1)
    extra_print: str = " "

    # 05 SL-Stock-Link pic x
    # str, 1 chars   [copybooks/wssystem.cob:L242]
    # column SYSTEM-REC.SL-STOCK-LINK char(1)
    sl_stock_link: str = " "

    # 05 SL-Stock-Audit pic x
    # str, 1 chars   [copybooks/wssystem.cob:L243]
    # column SYSTEM-REC.SL-STOCK-AUDIT char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Stock-Audit-On value "Y"  [copybooks/wssystem.cob:L244]
    sl_stock_audit: str = " "

    # 05 SL-Late-Per pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L245]
    # column SYSTEM-REC.SL-LATE-PER decimal(4,2) unsigned
    # Usage COMP is declared ON THIS LINE, so usage_declared_at is FIELD -
    # not GROUP. Do not confuse these three items (L245-L247) with the five
    # at L56-L60, which inherit their usage from the group header at L55.
    sl_late_per: decimal.Decimal = decimal.Decimal("0.00")

    # 05 SL-Disc pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L246]
    # column SYSTEM-REC.SL-DISC decimal(4,2) unsigned
    sl_disc: decimal.Decimal = decimal.Decimal("0.00")

    # 05 Extra-Rate pic 99v99 comp
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L247]
    # column SYSTEM-REC.EXTRA-RATE decimal(4,2) unsigned
    extra_rate: decimal.Decimal = decimal.Decimal("0.00")

    # 05 SL-Days-1 binary-char
    # int, signed   [copybooks/wssystem.cob:L248]
    # column SYSTEM-REC.SL-DAYS-1 smallint(3) unsigned
    sl_days_1: int = 0

    # 05 SL-Days-2 binary-char
    # int, signed   [copybooks/wssystem.cob:L249]
    # column SYSTEM-REC.SL-DAYS-2 smallint(3) unsigned
    sl_days_2: int = 0

    # 05 SL-Days-3 binary-char
    # int, signed   [copybooks/wssystem.cob:L250]
    # column SYSTEM-REC.SL-DAYS-3 smallint(3) unsigned
    sl_days_3: int = 0

    # 05 SL-Credit binary-char
    # int, signed   [copybooks/wssystem.cob:L251]
    # column SYSTEM-REC.SL-CREDIT smallint(3) unsigned
    sl_credit: int = 0

    # 05 FILLER binary-short
    # int, signed   [copybooks/wssystem.cob:L252]
    filler_252: int = 0

    # 05 SL-Min binary-short
    # int, signed   [copybooks/wssystem.cob:L253]
    # column SYSTEM-REC.SL-MIN smallint(4) unsigned
    sl_min: int = 0

    # 05 SL-Max binary-short
    # int, signed   [copybooks/wssystem.cob:L254]
    # column SYSTEM-REC.SL-MAX smallint(4) unsigned
    sl_max: int = 0

    # 05 PF-Retention binary-short
    # int, signed   [copybooks/wssystem.cob:L255]
    # column SYSTEM-REC.PF-RETENTION smallint(4) unsigned
    pf_retention: int = 0

    # 05 First-Sl-Batch binary-short
    # int, signed   [copybooks/wssystem.cob:L256]
    # column SYSTEM-REC.FIRST-SL-BATCH smallint(4) unsigned
    first_sl_batch: int = 0

    # 05 First-Sl-Inv binary-long
    # int, signed   [copybooks/wssystem.cob:L257]
    # column SYSTEM-REC.FIRST-SL-INV int(8) unsigned
    first_sl_inv: int = 0

    # 05 SL-Limit binary-long
    # int, signed   [copybooks/wssystem.cob:L258]
    # column SYSTEM-REC.SL-LIMIT int(8) unsigned
    sl_limit: int = 0

    # 05 SL-Pay-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L259]
    # column SYSTEM-REC.SL-PAY-AC int(8) unsigned
    sl_pay_ac: int = 0

    # 05 S-Debtors binary-long
    # int, signed   [copybooks/wssystem.cob:L260]
    # column SYSTEM-REC.S-DEBTORS int(8) unsigned
    s_debtors: int = 0

    # 05 SL-Sales-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L261]
    # column SYSTEM-REC.SL-SALES-AC int(8) unsigned
    sl_sales_ac: int = 0

    # 05 S-End-Cycle-Date binary-long
    # int, signed   [copybooks/wssystem.cob:L262]
    # column SYSTEM-REC.S-END-CYCLE-DAT int(8) unsigned
    # Column name drift: S-END-CYCLE-DAT. Anomaly A-11 applies.
    s_end_cycle_date: int = 0

    # 05 SL-Comp-Head-Pick pic x
    # str, 1 chars   [copybooks/wssystem.cob:L263]
    # column SYSTEM-REC.SL-COMP-HEAD-PICK char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 SL-Comp-Pick value "Y"  [copybooks/wssystem.cob:L264]
    sl_comp_head_pick: str = " "

    # 05 SL-Comp-Head-Inv pic x
    # str, 1 chars   [copybooks/wssystem.cob:L265]
    # column SYSTEM-REC.SL-COMP-HEAD-INV char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 SL-Comp-Inv value "Y"  [copybooks/wssystem.cob:L266]
    sl_comp_head_inv: str = " "

    # 05 SL-Comp-Head-Stat pic x
    # str, 1 chars   [copybooks/wssystem.cob:L267]
    # column SYSTEM-REC.SL-COMP-HEAD-STAT char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 SL-Comp-Stat value "Y"  [copybooks/wssystem.cob:L268]
    sl_comp_head_stat: str = " "

    # 05 SL-Comp-Head-Lets pic x
    # str, 1 chars   [copybooks/wssystem.cob:L269]
    # column SYSTEM-REC.SL-COMP-HEAD-LETS char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 SL-Comp-Lets value "Y"  [copybooks/wssystem.cob:L270]
    sl_comp_head_lets: str = " "

    # 05 SL-VAT-Printed pic x
    # str, 1 chars   [copybooks/wssystem.cob:L271]
    # column SYSTEM-REC.SL-VAT-PRINTED char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 SL-VAT-Prints value "Y"  [copybooks/wssystem.cob:L272]
    sl_vat_printed: str = " "

    # 05 SL-Invoice-Lines pic 99
    # int, digits 2, scale 0   [copybooks/wssystem.cob:L273]
    # column SYSTEM-REC.SL-INVOICE-LINES tinyint(2) unsigned
    sl_invoice_lines: int = 0

    # 05 SL-Autogen pic x value space
    # str, 1 chars   [copybooks/wssystem.cob:L274]
    # column SYSTEM-REC.SL-AUTOGEN char(1)
    # Declared `value space` in the frozen source.
    sl_autogen: str = " "

    # 05 SL-Next-Rec binary-short unsigned
    # int, unsigned   [copybooks/wssystem.cob:L275]
    # column SYSTEM-REC.SL-NEXT-REC smallint(4)
    # One of exactly five items in this record carrying the explicit
    # UNSIGNED keyword - and its drift runs the OPPOSITE way to the other
    # 41: unsigned here, SIGNED in the bridge host variable and signed in
    # the column. Neither direction wins over the other here; both views are
    # recorded exactly as each one declares itself.
    sl_next_rec: int = 0

    # 05 SL-BO-Flag pic x value space
    # str, 1 chars   [copybooks/wssystem.cob:L276]
    # column SYSTEM-REC.SL-BO-FLAG char(1)
    # Declared `value space` in the frozen source.
    sl_bo_flag: str = " "

    # 05 SL-BO-Default pic x
    # str, 1 chars   [copybooks/wssystem.cob:L277]
    # No column: the bridge does not map this item.
    sl_bo_default: str = " "

    # 05 FILLER pic X(14)
    # str, 14 chars   [copybooks/wssystem.cob:L278]
    filler_278: str = " " * 14

    # 05 GL-BL-Pay-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L280]
    # column SYSTEM-REC.GL-BL-PAY-AC int(8) unsigned
    # MISPLACED BLOCK (R-4). These six items (L280-L285) name General-Ledger
    # and Purchase-Ledger control accounts yet are declared inside the SALES
    # Ledger block, under the maintainer's own `*> GL overflow` heading at
    # L279. They were added on 06/06/18 to let the General Ledger and IRS
    # run at the same time. They stay exactly where the copybook puts them;
    # moving them to a block whose name matches would change the byte layout
    # and is precisely the tidying R-4 forbids.
    gl_bl_pay_ac: int = 0

    # 05 GL-P-Creditors binary-long
    # int, signed   [copybooks/wssystem.cob:L281]
    # column SYSTEM-REC.GL-P-CREDITORS int(8) unsigned
    gl_p_creditors: int = 0

    # 05 GL-BL-Purch-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L282]
    # column SYSTEM-REC.GL-BL-PURCH-AC int(8) unsigned
    gl_bl_purch_ac: int = 0

    # 05 GL-SL-Pay-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L283]
    # column SYSTEM-REC.GL-SL-PAY-AC int(8) unsigned
    gl_sl_pay_ac: int = 0

    # 05 GL-S-Debtors binary-long
    # int, signed   [copybooks/wssystem.cob:L284]
    # column SYSTEM-REC.GL-S-DEBTORS int(8) unsigned
    gl_s_debtors: int = 0

    # 05 GL-SL-Sales-Ac binary-long
    # int, signed   [copybooks/wssystem.cob:L285]
    # column SYSTEM-REC.GL-SL-SALES-AC int(8) unsigned
    gl_sl_sales_ac: int = 0


# BLOCK 5 OF 6 - Stock-Control-Block, 88 bytes [copybooks/wssystem.cob:L290]


@dataclass(slots=True)
class StockControlBlock:
    """The `03 Stock-Control-Block.` [copybooks/wssystem.cob:L290].

    88 bytes. Stock-control settings held in the system record. In
    scope: see the note on the first attribute.

    Byte layout: 88, matching the size the copybook states on L290.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Stk-Abrev-Ref", 291),
        _descriptor("Stk-Debug", 292),
        _descriptor("Stk-Manu-Used", 293),
        _descriptor("Stk-OE-Used", 294),
        _descriptor("Stk-Audit-Used", 295),
        _descriptor("Stk-Mov-Audit", 296),
        _descriptor("Stk-Period-Cur", 297),
        _descriptor("Stk-Period-dat", 298),
        _descriptor("FILLER", 299),
        _descriptor("Stock-Control", 300),
        _descriptor("Stk-Averaging", 302),
        _descriptor("Stk-Activity-Rep-Run", 304),
        _descriptor("Stk-BO-Active", 305),
        _descriptor("Stk-Page-Lines", 306),
        _descriptor("Stk-Audit-No", 307),
        _descriptor("FILLER", 308),
    )

    # 05 Stk-Abrev-Ref pic x(6)
    # str, 6 chars   [copybooks/wssystem.cob:L291]
    # column SYSTEM-REC.STK-ABREV-REF char(6)
    stk_abrev_ref: str = " " * 6

    # 05 Stk-Debug pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L292]
    # column SYSTEM-REC.STK-DEBUG tinyint(1) unsigned
    stk_debug: int = 0

    # 05 Stk-Manu-Used pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L293]
    # column SYSTEM-REC.STK-MANU-USED tinyint(1) unsigned
    stk_manu_used: int = 0

    # 05 Stk-OE-Used pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L294]
    # column SYSTEM-REC.STK-OE-USED tinyint(1) unsigned
    stk_oe_used: int = 0

    # 05 Stk-Audit-Used pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L295]
    # column SYSTEM-REC.STK-AUDIT-USED tinyint(1) unsigned
    stk_audit_used: int = 0

    # 05 Stk-Mov-Audit pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L296]
    # column SYSTEM-REC.STK-MOV-AUDIT tinyint(1) unsigned
    stk_mov_audit: int = 0

    # 05 Stk-Period-Cur pic x
    # str, 1 chars   [copybooks/wssystem.cob:L297]
    # column SYSTEM-REC.STK-PERIOD-CUR char(1)
    stk_period_cur: str = " "

    # 05 Stk-Period-dat pic x
    # str, 1 chars   [copybooks/wssystem.cob:L298]
    # column SYSTEM-REC.STK-PERIOD-DAT char(1)
    stk_period_dat: str = " "

    # 05 FILLER pic x
    # str, 1 chars   [copybooks/wssystem.cob:L299]
    # Annotated `*> was stk-date-form` in the frozen source.
    filler_299: str = " "

    # 05 Stock-Control pic x
    # str, 1 chars   [copybooks/wssystem.cob:L300]
    # column SYSTEM-REC.STOCK-CONTROL char(1)
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Stock-Control-Exists value "Y"  [copybooks/wssystem.cob:L301]
    stock_control: str = " "

    # 05 Stk-Averaging pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L302]
    # column SYSTEM-REC.STK-AVERAGING tinyint(1) unsigned
    # 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4):
    #   88 Stock-Averaging value 1  [copybooks/wssystem.cob:L303]
    stk_averaging: int = 0

    # 05 Stk-Activity-Rep-Run pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L304]
    # column SYSTEM-REC.STK-ACTIVITY-REP-RUN tinyint(1) unsigned
    stk_activity_rep_run: int = 0

    # 05 Stk-BO-Active pic x
    # str, 1 chars   [copybooks/wssystem.cob:L305]
    # column SYSTEM-REC.STK-BO-ACTIVE char(1)
    stk_bo_active: str = " "

    # 05 Stk-Page-Lines binary-char unsigned
    # int, unsigned   [copybooks/wssystem.cob:L306]
    # column SYSTEM-REC.STK-PAGE-LINES tinyint(4) unsigned
    # One of exactly five items in this record carrying the explicit
    # UNSIGNED keyword, so its domain is 0..255. Its inline comment says `*>
    # 9999 comp.`; the declaration governs. See the note at L65.
    stk_page_lines: int = 0

    # 05 Stk-Audit-No binary-char unsigned
    # int, unsigned   [copybooks/wssystem.cob:L307]
    # column SYSTEM-REC.STK-AUDIT-NO tinyint(4) unsigned
    # One of exactly five items in this record carrying the explicit
    # UNSIGNED keyword. Its inline comment says `*> 9999 comp.`; the
    # declaration governs. See the note at L65.
    stk_audit_no: int = 0

    # 05 FILLER pic x(68)
    # str, 68 chars   [copybooks/wssystem.cob:L308]
    filler_308: str = " " * 68


# SUBORDINATE GROUPS AND VIEWS OF IRS-Entry-Block


@dataclass(slots=True)
class VatRates2:
    """The `05 Vat-Rates2.` group [copybooks/wssystem.cob:L312].

    Three IRS VAT rates. Deliberately NOT the same storage class as
    the five-rate group at L55: no usage clause appears on this
    group header, so these three are zoned display. See the note on
    the attributes below.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("vat1", 313),
        _descriptor("vat2", 314),
        _descriptor("vat3", 315),
    )

    # 07 vat1 pic 99v99
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L313]
    # column SYSTEM-REC.VAT1 decimal(4,2) unsigned
    vat1: decimal.Decimal = decimal.Decimal("0.00")

    # 07 vat2 pic 99v99
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L314]
    # column SYSTEM-REC.VAT2 decimal(4,2) unsigned
    vat2: decimal.Decimal = decimal.Decimal("0.00")

    # 07 vat3 pic 99v99
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L315]
    # column SYSTEM-REC.VAT3 decimal(4,2) unsigned
    vat3: decimal.Decimal = decimal.Decimal("0.00")


@dataclass(slots=True)
class VatGroup:
    """The `Vat-Group` view over `Vat-Rates2` [copybooks/wssystem.cob:L316].

    Declared `05 Vat-Group redefines Vat-Rates2.`: the three rates
    above seen as a 3-element table over the same bytes.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Vat-Psent", 317),
    )

    # 07 Vat-Psent pic 99v99 occurs 3
    # decimal, digits 4, scale 2   [copybooks/wssystem.cob:L317]
    # No column: the bridge maps vat1, vat2 and vat3 instead.
    vat_psent: list[decimal.Decimal] = field(
        default_factory=lambda: [decimal.Decimal("0.00")] * 3
    )


@dataclass(slots=True)
class PlAppropAc6Parts:
    """The anonymous view over `PL-Approp-AC6` [copybooks/wssystem.cob:L323].

    Declared `05 FILLER redefines PL-Approp-AC6.`

    The COBOL group is FILLER and therefore has no name to carry
    over. `PlAppropAc6Parts` is this module's name for it, chosen
    for what it redefines; the original declaration is the line
    quoted above. It splits the six-digit appropriation account
    into a discarded leading digit and the five digits IRS uses -
    "loose leading char for IRS" in the maintainer's own words at
    L324. Moved to the front of the field on 10/02/18.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("FILLER", 324),
        _descriptor("PL-Approp-AC", 325),
    )

    # 07 FILLER pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L324]
    filler_324: int = 0

    # 07 PL-Approp-AC pic 9(5)
    # int, digits 5, scale 0   [copybooks/wssystem.cob:L325]
    # column SYSTEM-REC.PL-APPROP-AC mediumint(5) unsigned
    pl_approp_ac: int = 0


# BLOCK 6 OF 6 - IRS-Entry-Block, 128 bytes, AND THE VIEW OVER IT
#  [copybooks/wssystem.cob:L309]


@dataclass(slots=True)
class IrsEntryBlock:
    """The `03 IRS-Entry-Block.` [copybooks/wssystem.cob:L309].

    128 bytes. The IRS client name, its posting sequence number, its
    own three VAT rates and the appropriation account. The
    maintainer notes that once IRS data is mapped into ACAS this
    block could shrink to 32 bytes; it has not, so it stands at 128.

    Byte layout: 128, matching the size the copybook states on L309.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Client", 310),
        _descriptor("Next-Post", 311),
        _descriptor("Vat-Rates2", 312),
        _descriptor("Vat-Group", 316),
        _descriptor("IRS-Pass-Value", 318),
        _descriptor("Save-Sequ", 319),
        _descriptor("System-Work-Group", 320),
        _descriptor("PL-App-Created", 321),
        _descriptor("PL-Approp-AC6", 322),
        _descriptor("FILLER", 323),
        _descriptor("1st-Time-Flag", 326),
        _descriptor("FILLER", 327),
    )

    # 05 Client pic x(24)
    # str, 24 chars   [copybooks/wssystem.cob:L310]
    # column SYSTEM-REC.CLIENT char(24)
    # Renamed IRS-Client where irs030 copies this record
    # [irs/irs030.cbl:L435].
    client: str = " " * 24

    # 05 Next-Post pic 9(5)
    # int, digits 5, scale 0   [copybooks/wssystem.cob:L311]
    # column SYSTEM-REC.NEXT-POST mediumint(5) unsigned
    # Incremented by the IRS posting path; see the note at L66.
    next_post: int = 0

    # 05 Vat-Rates2
    # group item - no storage of its own   [copybooks/wssystem.cob:L312]
    # NO GROUP USAGE on this line, so the three items at L313-L315 are
    # genuinely DISPLAY - zoned decimal. This is the deliberate contrast
    # with `Vat-Rates comp.` at L55, whose five children inherit COMP. The
    # maintainer's own comment here reads `*> these can be replaced by the
    # other VAT blk`; they are not, and the divergence is preserved (R-4).
    vat_rates2: VatRates2 = field(default_factory=VatRates2)

    # 05 Vat-Group redefines Vat-Rates2
    # group item - no storage of its own   [copybooks/wssystem.cob:L316]
    # REDEFINES Vat-Rates2 as a 3-element table over the same bytes. An
    # alternate view, not extra storage; see the note at L61.
    vat_group: VatGroup = field(default_factory=VatGroup)

    # 05 IRS-Pass-Value pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L318]
    # column SYSTEM-REC.IRS-PASS-VALUE tinyint(1) unsigned
    irs_pass_value: int = 0

    # 05 Save-Sequ pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L319]
    # column SYSTEM-REC.SAVE-SEQU tinyint(1) unsigned
    save_sequ: int = 0

    # 05 System-Work-Group pic x(18)
    # str, 18 chars   [copybooks/wssystem.cob:L320]
    # column SYSTEM-REC.SYSTEM-WORK-GROUP char(18)
    system_work_group: str = " " * 18

    # 05 PL-App-Created pic x
    # str, 1 chars   [copybooks/wssystem.cob:L321]
    # column SYSTEM-REC.PL-APP-CREATED char(1)
    pl_app_created: str = " "

    # 05 PL-Approp-AC6 pic 9(6)
    # int, digits 6, scale 0   [copybooks/wssystem.cob:L322]
    # column SYSTEM-REC.PL-APPROP-AC6 mediumint(6) unsigned
    # Widened from 9(5) to 9(6) on 19/10/16 for General Ledger support, with
    # the filler reduced by one. Both this item and the 9(5) view over it at
    # L323-L325 reach the database, on their own columns.
    pl_approp_ac6: int = 0

    # 05 FILLER redefines PL-Approp-AC6
    # group item - no storage of its own   [copybooks/wssystem.cob:L323]
    filler_323: PlAppropAc6Parts = field(default_factory=PlAppropAc6Parts)

    # 05 1st-Time-Flag pic 9
    # int, digits 1, scale 0   [copybooks/wssystem.cob:L326]
    # column SYSTEM-REC.1ST-TIME-FLAG tinyint(1) unsigned
    # RENAMED ATTRIBUTE (R-4). The COBOL name is `1st-Time-Flag` and it
    # BEGINS WITH A DIGIT, which no Python identifier may do. The attribute
    # is therefore `first_time_flag` while the descriptor keeps the verbatim
    # COBOL name `1st-Time-Flag` and the dictionary key keeps the column
    # spelling `1ST-TIME-FLAG`. The spelling is not invented: the
    # maintainer's own comment on this line reads `(was First-Time-Flag in
    # IRS system file)`, and [irs/irs030.cbl:L448] renames the item
    # `IRS-First-Time-Flag`. The rename is also listed in this module's
    # docstring so that the traceability document picks it up.
    first_time_flag: int = 0

    # 05 FILLER pic x(59)
    # str, 59 chars   [copybooks/wssystem.cob:L327]
    filler_327: str = " " * 59


@dataclass(slots=True)
class IrsDataBlock:
    """The `IRS-Data-Block` view [copybooks/wssystem.cob:L328].

    Declared `03 IRS-Data-Block redefines IRS-Entry-Block.`: the
    whole IRS entry block seen as one opaque 128-character run.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("FILLER-Dummy4", 329),
    )

    # 05 FILLER-Dummy4 pic x(128)
    # str, 128 chars   [copybooks/wssystem.cob:L329]
    # Note that this item is NOT flagged as FILLER by the dictionary: its
    # COBOL name is `FILLER-Dummy4`, which is a name, not the FILLER
    # keyword. It has no column.
    filler_dummy4: str = " " * 128


# THE RECORD - 512 + 80 + 88 + 128 + 88 + 128 = 1024 bytes
#  [copybooks/wssystem.cob:L48]


@dataclass(slots=True)
class SystemRecord:
    """The `01 System-Record.` [copybooks/wssystem.cob:L48].

    1024 bytes in six blocks plus one redefining view, and the
    widest record in the migration: 169 columns in SYSTEM-REC.

    This is the SECOND parameter of every in-scope linkage shape -
    `using ws-calling-data, system-record, to-day, file-defs` in the
    General Ledger family, the same plus a fourth system record in
    the Sales and Purchase families, and `using IRS-System-Params,
    WS-System-Record, File-Defs` in irs030 [irs/irs030.cbl:L552-L554]
    - and the FIRST argument of every file-handler call.

    Byte layout: 512 + 80 + 88 + 128 + 88 + 128 = 1024, matching
    `*> File size 1024 with fillers` [copybooks/wssystem.cob:L7].
    IRS-Data-Block adds nothing: it redefines the 128 bytes of
    IRS-Entry-Block.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("System-Data-Block", 52),
        _descriptor("General-Ledger-Block", 150),
        _descriptor("Purchase-Ledger-Block", 192),
        _descriptor("Sales-Ledger-Block", 215),
        _descriptor("Stock-Control-Block", 290),
        _descriptor("IRS-Entry-Block", 309),
        _descriptor("IRS-Data-Block", 328),
    )

    # 03 System-Data-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L52]
    system_data_block: SystemDataBlock = field(default_factory=SystemDataBlock)

    # 03 General-Ledger-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L150]
    general_ledger_block: GeneralLedgerBlock = field(
        default_factory=GeneralLedgerBlock
    )

    # 03 Purchase-Ledger-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L192]
    purchase_ledger_block: PurchaseLedgerBlock = field(
        default_factory=PurchaseLedgerBlock
    )

    # 03 Sales-Ledger-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L215]
    sales_ledger_block: SalesLedgerBlock = field(
        default_factory=SalesLedgerBlock
    )

    # 03 Stock-Control-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L290]
    # IN SCOPE. Plan section 0.2.2 puts the stock/ SUBSYSTEM and its own
    # tables out of scope; it does not remove this block's columns from
    # SYSTEM-REC, which has 169 of them. Every item here is declared, and
    # the 88 names `Stock-Control-Exists` (L301) and `Stock-Averaging`
    # (L303) - like `Stock` (L91) and `Stock-Audit-On` (L244) elsewhere in
    # this record - are legitimate in-scope SYSTEM-REC condition names.
    stock_control_block: StockControlBlock = field(
        default_factory=StockControlBlock
    )

    # 03 IRS-Entry-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L309]
    irs_entry_block: IrsEntryBlock = field(default_factory=IrsEntryBlock)

    # 03 IRS-Data-Block redefines IRS-Entry-Block
    # group item - no storage of its own   [copybooks/wssystem.cob:L328]
    # REDEFINES the whole IRS-Entry-Block above as one opaque 128-character
    # run. An alternate view over the same 128 bytes, not extra storage; see
    # the note at L61.
    irs_data_block: IrsDataBlock = field(default_factory=IrsDataBlock)
