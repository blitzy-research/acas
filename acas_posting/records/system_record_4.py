"""The period-totals record: `System-Record-4`, from `copybooks/wssys4.cob`.

One module, one copybook, field for field. `SystemRecord4` and its two
subordinate groups mirror the 32 lines of `copybooks/wssys4.cob` exactly:
twenty scaled money items in two ledger blocks, then a 904-character
FILLER that pads the layout to the 1024 bytes the copybook's own header
states. Nothing is added, nothing is dropped, nothing is renamed, and no
storage metadata is typed by hand - every field's description is looked
up in the generated data dictionary (rule R-5).

Agent Action Plan section 0.4.1.3 sets the mandate for this folder: every
module is a CREATE from its copybook; each 03 and 05 item becomes a
dataclass attribute whose descriptor is looked up in the generated
dictionary; and an oddity in the frozen source is preserved rather than
put right. Section 0.8.1 fixes the shape - "Plain modules and
dataclasses; no ORM entity layer." Rule R-3 names this very copybook when
it states the folder rule: "The 27 record modules mirror their copybooks
field for field with nothing added, preserving even the misnamings - the
two spare fields keep their Sales prefix inside the Purchase group
[copybooks/wssys4.cob]."

The frozen COBOL is read as the specification and never modified. This
module executes, embeds and shells out to nothing: it runs on a host with
no COBOL compiler and no COBOL runtime present (rule R-1).

WHERE THIS RECORD SITS
----------------------
The entity-to-table spine of Agent Action Plan section 0.2.1.1::

    entity facade   System totals
    handler         acas000, dispatching on file-key number 4
    bridge          sys4MT   [common/sys4MT.scb, common/sys4MT.cbl]
    MySQL table     SYSTOT-REC, 21 columns
                    [mysql/ACASDB.sql:L1376-L1398]
    primary key     LEDGER-TOTALS-REC-KEY, and see below - no copybook
                    declares it
    copybook        copybooks/wssys4.cob, one 01 record, 32 lines

The bridge declares its table and host-variable group in an embedded
directive, `BASE=ACASDB` with `TABLE=SYSTOT-REC,HV`
[common/sys4MT.scb:L306-L309], materialises the group as `TD-SYSTOT-REC`,
COPYs this copybook at [common/sys4MT.cbl:L346], loads the host variables
from the record in `bb000-HV-Load` [common/sys4MT.cbl:L760-L790] and
unloads them back in `bb100-UnloadHVs` [common/sys4MT.cbl:L794-L823].
That bridge, not the copybook, defines the record-layout to table mapping
for this migration - it is the data dictionary for this migration, as the
generated artifact's own `meta().authority` line states.

THE COPYBOOK, IN FULL
---------------------
Every item, with its locator, in declaration order. The two `03` group
headers each carry `comp-3`; not one of the twenty `05` children carries
a USAGE clause of its own::

    L8   01  System-Record-4.
    L9       03  Sales-Ledger-Data                       comp-3.
    L10          05  sl-os-bal-last-month        pic s9(8)v99.
    L11          05  sl-os-bal-this-month        pic s9(8)v99.
    L12          05  sl-invoices-this-month      pic s9(8)v99.
    L13          05  sl-credit-notes-this-month  pic s9(8)v99.
    L14          05  sl-variance                 pic s9(8)v99.
    L15          05  sl-credit-deductions        pic s9(8)v99.
    L16          05  sl-cn-unappl-this-month     pic s9(8)v99.
    L17          05  sl-payments                 pic s9(8)v99.
    L18          05  sl4-spare1                  pic s9(8)v99.
    L19          05  sl4-spare2                  pic s9(8)v99.
    L20      03  Purchase-Ledger-Data                    comp-3.
    L21          05  pl-os-bal-last-month        pic s9(8)v99.
    L22          05  pl-os-bal-this-month        pic s9(8)v99.
    L23          05  pl-invoices-this-month      pic s9(8)v99.
    L24          05  pl-credit-notes-this-month  pic s9(8)v99.
    L25          05  pl-variance                 pic s9(8)v99.
    L26          05  pl-credit-deductions        pic s9(8)v99.
    L27          05  pl-cn-unappl-this-month     pic s9(8)v99.
    L28          05  pl-payments                 pic s9(8)v99.
    L29          05  sl4-spare3                  pic s9(8)v99.  <- A-20
    L30          05  sl4-spare4                  pic s9(8)v99.  <- A-20
    L31      03  filler                          pic x(904).

WHO WRITES THIS RECORD - THE NINE PERIOD-TOTAL SITES
----------------------------------------------------
Agent Action Plan section 0.6.4: "Period totals are written at exactly
nine sites, all inside the Sales and Purchase programs, and all in scope.
They are the sole writers of the totals record, which makes the
period-end-totals scenario verifiable by inspecting one table." A reader
of this record needs to know exactly who moves its figures, so all nine
are named here, each with the field it reaches::

    sl-invoices-this-month      add ws-inv-amt   [sales/sl055.cbl:L675]
    sl-credit-notes-this-month  add ws-inv-amt   [sales/sl055.cbl:L677]
    sl-credit-deductions        add total-deduct [sales/sl060.cbl:L641]
    sl-cn-unappl-this-month     add work-b       [sales/sl060.cbl:L700]
    sl-payments                 add oi-paid      [sales/sl100.cbl:L404]
    pl-invoices-this-month      add ws-inv-amt   [purchase/pl055.cbl:L582]
    pl-credit-notes-this-month  add ws-inv-amt   [purchase/pl055.cbl:L584]
    pl-cn-unappl-this-month     add work-b       [purchase/pl060.cbl:L628]
    pl-payments                 add oi-paid      [purchase/pl100.cbl:L396]

Two of the nine are MULTI-TARGET adds - `add oi-paid to t-paid
sl-payments` [sales/sl100.cbl:L404] and its purchase counterpart
[purchase/pl100.cbl:L396] feed a program-local total and the period total
from one statement, so a migration that split them into two adds would
still have to keep both receiving fields.

Nine sites reach nine distinct fields, which leaves ELEVEN of the twenty
untouched by the migrated cycle: both sales and both purchase
outstanding-balance figures, both variances, `pl-credit-deductions`, and
all four spares. Two consequences worth carrying:

    * The period ROLL-OVER that carries `SL-os-bal-This-month` into
      `SL-os-bal-Last-month` and zeroes the accumulators lives in the
      end-of-cycle driver [common/xl150.cbl:L1726-L1730] and its purchase
      mirror [common/xl150.cbl:L1997-L2001]. Agent Action Plan section
      0.2.2 places that driver out of scope, so within the migrated cycle
      these fields are accumulated and never cleared.
    * `sl-credit-deductions` is accumulated [sales/sl060.cbl:L641] while
      `pl-credit-deductions` never is - the purchase posting program has
      no counterpart statement, and the only other mention of the field
      in the purchase tree is commented out [purchase/pl120.cbl:L900].
      The asymmetry is the specification; it is not evened up here.

The period-end-totals scenario turns on this one table, so
`tests/scenarios/test_period_end_totals_update.py` and its scenario
definition under `harness/scenarios/` are what prove these nine sites
land the same figures as the compiled programs.

HOW IT REACHES A PROGRAM
------------------------
By LINKAGE, never by a file read of its own. The record is the third
parameter of the Sales and Purchase posting shape - `procedure division
using ws-calling-data system-record system-record-4 to-day file-defs`
[sales/sl055.cbl:L269-L275] - which is the "fourth system record" that
Agent Action Plan section 0.1.1 notes the Sales and Purchase families add
to the General Ledger shape. Exactly six in-scope programs COPY the
copybook and take that parameter: [sales/sl055.cbl:L269],
[sales/sl060.cbl:L393], [sales/sl100.cbl:L267],
[purchase/pl055.cbl:L234], [purchase/pl060.cbl:L335] and
[purchase/pl100.cbl:L260].

A grep for `System-Record-4` also finds a one-character item of the same
name in the four General Ledger programs, for instance
[general/gl070.cbl:L135]. That is NOT this record: it is a `pic x` stub
inside `01 Dummies-4-Unused-ACAS-FH-Calls.`, the block declared purely so
the linker resolves the facade copybook's full verb set, which Agent
Action Plan section 0.4.3 maps to nothing. The six Sales and Purchase
programs comment that same stub out precisely because they take the real
record by linkage. The General Ledger cycle never touches this record.

GROUP-USAGE INHERITANCE - THE CORRECTNESS HINGE OF THIS LAYOUT
--------------------------------------------------------------
`03 Sales-Ledger-Data` [copybooks/wssys4.cob:L9] and
`03 Purchase-Ledger-Data` [copybooks/wssys4.cob:L20] each carry `comp-3`
ON THE GROUP HEADER. All twenty `05` children are written as
`pic s9(8)v99` with no USAGE clause of their own, so all twenty INHERIT
COMP-3 and are PACKED DECIMAL - six bytes each, sign in the low nibble.

Reading a usage off the PICTURE line alone would class every one of them
as zoned DISPLAY and every stored value would be wrong. The generated
dictionary says so in each of the twenty entries' notes: "The item
carries no USAGE clause of its own; it inherits COMP-3 from the group
Sales-Ledger-Data declared at copybooks/wssys4.cob:L9. Reading usage from
the picture line alone would class it as DISPLAY."

Because the descriptors are looked up rather than transcribed, that fact
arrives as data: every one of the twenty reports `usage` COMP-3,
`usage_declared_at` GROUP and `usage_inherited_from` naming its group
header. Nothing in this module re-derives it.

All twenty are signed with two decimal places and ten digits, which the
schema mirrors as `decimal(10,2) NOT NULL` [mysql/ACASDB.sql:L1378-L1397].
Signedness is a clean pass-through here - the copybook signs them, the
bridge host variable signs them and the column is not unsigned - unlike
the narrowing the sales ledger record suffers at the bridge. Drift in
this system is specific, not systemic, which is why it is read per field
from the dictionary and never assumed either way.

TWENTY MONEY FIELDS, ALL EXACT DECIMALS (RULE R-2)
--------------------------------------------------
Rule R-2: "No accounting value may pass through a binary floating-point
type at any point - not in computation, not in storage, not in
transport." Every attribute of the two ledger groups is money, so every
one is a `decimal.Decimal` carried at the scale its copybook declares,
defaulting to `Decimal("0.00")` - never a binary approximation, never an
integer zero that would drop the scale. The carrier is not chosen by
reading what a field "means": it is the `python_storage` the dictionary
holds, so this module and the arithmetic layer cannot disagree about what
holds a value.

This is a period-totals record whose one table is the entire verification
surface of a mandated scenario. A single inexact carrier here would
corrupt exactly the figures that scenario compares.

ANOMALY A-20, REPRODUCED HERE AND NOT PUT RIGHT (RULE R-4)
----------------------------------------------------------
THIS MODULE IS THE REPRODUCING SITE FOR ANOMALY A-20, entry 20 of the
register in Agent Action Plan section 0.6.7: "Two spare fields carry the
Sales prefix inside the Purchase group" [copybooks/wssys4.cob].

Concretely: `sl4-spare3` [copybooks/wssys4.cob:L29] and `sl4-spare4`
[copybooks/wssys4.cob:L30] are declared INSIDE `03 Purchase-Ledger-Data`
[copybooks/wssys4.cob:L20], among eight `pl-` siblings, while the Sales
group's own spares are `sl4-spare1` [copybooks/wssys4.cob:L18] and
`sl4-spare2` [copybooks/wssys4.cob:L19]. The maintainer's misnaming
carries all the way through: the bridge host variable is `HV-SL4-SPARE3`
[common/sys4MT.cbl:L334] and the column is `SL4-SPARE3`
[mysql/ACASDB.sql:L1396].

So `PurchaseLedgerData` ends with `sl4_spare3` and `sl4_spare4`, keeping
the Sales prefix, and their descriptors carry the verbatim COBOL names
`sl4-spare3` and `sl4-spare4` with `parent_group` `Purchase-Ledger-Data`.
Renaming them to a purchase prefix, or moving them into
`SalesLedgerData` to make the names agree, would repair a defect that
rule R-4 makes part of the specification: "A defect reproduced is
correct; a defect fixed is a failure." The generated dictionary tags both
entries `A-20` and tags no other entry of this table, so the artifact
corroborates the ownership; `docs/migration/anomaly-log.md` cites this
module.

Recorded alongside it, from the copybook header: "Record size 1024 bytes
to match system-record 07/11/10" [copybooks/wssys4.cob:L6]. The layout is
padded to match a different record's size, and the 904-byte FILLER at
[copybooks/wssys4.cob:L31] exists for no other reason.

THE FILLER, AND THE 1024 BYTES IT EXISTS TO REACH
-------------------------------------------------
The FILLER is modelled as a NAMED attribute, `SystemRecord4.filler`,
defaulting to spaces at a width taken from its own descriptor. Two
reasons for naming it rather than leaving it implicit: the copybook
declares it as a real `03` data item, so a layout that dropped it would
no longer be the record; and the byte arithmetic only closes with it
present. Spaces rather than an empty string because spaces are what those
904 bytes hold in the record, and because the width is then visible in
the value as well as in the descriptor.

It reaches no database column. The dictionary holds it as a copybook-only
entry whose bridge and column views are both absent, and its descriptor
reports `is_filler` true, so nothing about it appears in a table dump.

THE COLUMN THE COPYBOOK DOES NOT DECLARE
----------------------------------------
`SYSTOT-REC` has 21 columns and this record has 20 money fields. The
difference is the primary key `LEDGER-TOTALS-REC-KEY`, and it is NOT a
field of this record: the dictionary records it present in the bridge and
in the schema and ABSENT FROM EVERY COPYBOOK, with its value produced at
the bridge by `move 1 to HV-LEDGER-TOTALS-REC-KEY`
[common/sys4MT.cbl:L769] - a hard-coded singleton key on a
`tinyint(1) unsigned NOT NULL PRIMARY KEY` column
[mysql/ACASDB.sql:L1377]. Its entry adds that the host variable is never
moved back into the record after a read, so no value reaches a caller
through it.

No attribute is created for it. Reproducing a bridge-derived column
belongs at the bridge boundary, in `acas_posting/dal/acas000_system.py`,
exactly as the three date components of the internal IRS posting table
belong to `acas_posting/dal/acasirsub4_irs_posting.py`. Asking
`FieldDescriptor.from_dictionary_key` for it raises
`BridgeOnlyFieldError`, by design, because a bridge-only column has no
COBOL-side storage for a descriptor to describe.

    20 copybook fields  +  1 bridge-only key  =  the table's 21 columns

THE ONE DISAGREEMENT BETWEEN THE THREE LAYERS, REGISTERED NOT SETTLED
---------------------------------------------------------------------
Every one of the twenty carries a usage drift, which the dictionary
states as: "Storage class changes at the bridge: copybook declares
COMP-3, host variable declares COMP, column is DECIMAL." The copybook
item is packed decimal, the host variable it loads into is declared
`S9(08)V9(02) COMP` [common/sys4MT.cbl:L316-L335], and the column is
`decimal(10,2)`.

That disagreement is REGISTERED AND LEFT OPEN. This module holds the
COPYBOOK view, because a record layout is what a COBOL program
manipulates; the conversion the bridge performs on its way to SQL is
reproduced at the bridge boundary by the handler module. Each
descriptor's `drift()` offers all three views untouched, and rule R-4
forbids picking a winner between them. There is deliberately no second,
tidier view of any field in this module.

DESCRIPTOR LOOKUP AND ORDERING (RULES R-5 AND R-6)
--------------------------------------------------
Agent Action Plan section 0.8.1 is a directive rather than a preference:
the dictionary is generated from the bridge BEFORE record definitions are
written, and every Python field definition cites its entry. Section 0.3.3
gives the reason - "Field metadata is therefore derived, not transcribed,
which eliminates an entire class of transcription error across several
hundred fields."

So no key is guessed here. `_dictionary_keys` asks
`loader.entries_for_table("SYSTOT-REC")` and
`loader.entries_for_copybook_record("System-Record-4")` for this record's
entries and reads each entry's own `copybook.name`, which is what makes
the module immune to the name drift that appears elsewhere in this system
- a key's left side is the TABLE name and its right side is the COLUMN
name, and the two differ from the copybook field name often enough that
composing a key by rule would be a trap. On this table the twenty column
names happen to be the upper-case copybook names, and that is an
observation from the artifact, not an assumption built into the code.

Each class publishes two class-level views, both tuples or single values
fixed at import so two runs agree (rule R-6):

    FIELDS      the descriptors of the items THIS class declares, in
                copybook declaration order
    DESCRIPTOR  the descriptor of the group or record item itself, so the
                two `comp-3` group headers at L9 and L20 cite their own
                entries too

`FIELDS` order is DERIVED, not transcribed: the children of a group are
ordered by the declaration line in each descriptor's `source_locator`.
That is what `loader.entries_for_copybook_record` itself directs a caller
to do - for a table-backed record it returns document order, which is
column-ordinal order first and copybook-only fields after, and its
docstring notes that "A caller that needs strict copybook declaration
order has each entry's own `copybook.source` line to order by". Ordering
that way reproduces the copybook line for line, L8 through L31, and it
means `FIELDS` is an independent witness to the hand-written attribute
order rather than a restatement of it.

For a field's provenance, `descriptor.cite()` surfaces the loader's
compact three-locator string - copybook field, bridge host variable,
MySQL column - and is never reimplemented here. The full mapping is
recorded in `docs/migration/traceability.md`.

LAYERING - THIS IS A LEAF MODULE
--------------------------------
The per-directory import contract of Agent Action Plan section 0.4.3
grants `records/*.py` two internal imports and forbids the rest, "this
keeps the record layer a leaf":

    permitted   acas_posting.cobol.field, acas_posting.dictionary.loader,
                plus the standard library
    forbidden   dal, programs, cli, clock, dates, workfiles,
                cobol.arithmetic, cobol.move, cobol.picture, cobol.usage,
                cobol.condition_names, cobol.sortverb,
                dictionary.generate, the comparison oracle in its sibling
                tree, and any other module of this package - including
                `records/system_record.py`, despite the copybook header's
                mention of `system-record`

`cobol.arithmetic` is the live temptation in a module full of
accumulators, and it is not imported: the nine posting sites accumulate,
this record only stores. The arithmetic test tier "imports only `cobol`
and `records` and touches no database, so it runs anywhere", and a single
reach into `dal` would drag a database driver into that tier.

DETERMINISM (RULE R-6)
----------------------
Field order is the copybook's declaration order, so this module can be
set beside `copybooks/wssys4.cob` and diffed by eye. Fixed collections
are tuples. Nothing here consults a clock, draws an unpredictable value
or inspects the process environment, and the only import-time work is the
data dictionary's own lazy cached read.

Note in particular that although eight field names say "this month" or
"last month", NO field derives a month from anything: the figures are
accumulated by the posting programs and the period boundary comes from
`SYSTEM-REC`. The roll-over that gives "last month" its meaning is the
out-of-scope driver's move at [common/xl150.cbl:L1726].

WHAT THIS MODULE DELIBERATELY DOES NOT DO (RULE R-3)
----------------------------------------------------
Rule R-3: "The migration may not add validation logic, add fields, or
alter the database schema, and must not introduce concurrent execution."
Here that means exactly twenty money attributes plus the FILLER - no
more, no fewer - and:

    * no derived figure of any kind. `sl-variance` and `pl-variance` are
      STORED fields, written by nothing in the migrated cycle and rolled
      by the out-of-scope driver; computing either one would invent
      behaviour the compiled programs do not have.
    * no accumulate, add-invoice or roll-up helper. That logic belongs to
      the nine sites in `acas_posting/programs/sl055_*`, `sl060_*`,
      `sl100_*`, `pl055_*`, `pl060_*` and `pl100_*`.
    * no post-initialisation hook, no padding, no quantising and no
      checks on assignment. `acas_posting/cobol/move.py` and
      `acas_posting/cobol/arithmetic.py` own those semantics; a store
      here would apply them twice.
    * no ORM base, no declarative metadata, no schema emission, and no
      concurrency. Execution is strictly sequential, as the
      single-threaded COBOL is.

The classes are MUTABLE on purpose - not frozen - because the nine
posting sites accumulate into these fields and rewrite the record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    # Sorted, the way the sibling modules sort theirs. The two group classes
    # are part of the surface because `SystemRecord4` holds them by value, so
    # a caller reaching a single figure names one of them on the way in.
    "PurchaseLedgerData",
    "SalesLedgerData",
    "SystemRecord4",
)


# =============================================================================
#  THE NAMES THE FROZEN SOURCES GIVE THIS LAYOUT
# =============================================================================

# The copybook path, the 01-level record name, the table name and the two
# group headers, each spelled the way its own source spells it. These are the
# only literals the module needs in order to ask the dictionary for everything
# else: the table name keys the twenty column-mapped entries, and the record
# name keys the copybook-only ones - the two group headers and the FILLER.
_COPYBOOK: Final[str] = "copybooks/wssys4.cob"
_RECORD: Final[str] = "System-Record-4"
_TABLE: Final[str] = "SYSTOT-REC"

# The two `03` headers that carry `comp-3` on behalf of all twenty children,
# at [copybooks/wssys4.cob:L9] and [copybooks/wssys4.cob:L20]. Named because
# the group is what `usage_inherited_from` reports and what decides which of
# the two classes below a field belongs to.
_SALES_GROUP: Final[str] = "Sales-Ledger-Data"
_PURCHASE_GROUP: Final[str] = "Purchase-Ledger-Data"


# =============================================================================
#  KEYS LOOKED UP, NEVER GUESSED  (rule R-5)
# =============================================================================


def _dictionary_keys() -> dict[str, str]:
    """Map each COBOL field name of this record to its dictionary key.

    Built by ASKING the loader and reading each entry's own
    `copybook.name`, never by composing a key from a rule. A key's left
    side is the TABLE name and its right side is the COLUMN name, and the
    column name drifts from the copybook field name often enough
    elsewhere in this system that a composed key would be a trap. Here
    the twenty column names turn out to be the upper-case copybook
    names - an observation read off the artifact rather than an
    assumption built into this module.

    Two accessors are needed because the record spans two key spaces.
    `entries_for_table` yields the twenty column-mapped entries keyed
    `SYSTOT-REC.<COLUMN>` in the schema's own column ordinal order, and
    the one entry it yields with no copybook view is the bridge-only
    primary key, which this record does not declare and this module does
    not model. It cannot yield the rest, and says so - "The copybook-only
    fields of the records behind a table are NOT part of this result" -
    so `entries_for_copybook_record` adds those, keyed
    `System-Record-4.<FIELD>`: the 01 record, the two group headers and
    the FILLER, none of which reaches a column.

    The second pass is filtered on the copybook file because a record
    name can be declared by more than one copybook, which the loader
    documents and which is true of `Default-Record` and `Final-Record`
    among others. `System-Record-4` is declared by one copybook only, and
    filtering says so rather than relying on it.

    Returns:
        The COBOL field name of every item of this record, in either key
        space, mapped to the entry key that describes it.
    """
    keys: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE):
        copybook = entry.copybook
        if copybook is None:
            # LEDGER-TOTALS-REC-KEY: present in the bridge and in the
            # schema, absent from every copybook, and produced at the
            # bridge by `move 1 to HV-LEDGER-TOTALS-REC-KEY`
            # [common/sys4MT.cbl:L769]. Reproducing it is the handler
            # module's job, not this one's, so it gets no name here.
            continue
        keys[copybook.name] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD):
        copybook = entry.copybook
        if copybook is None or copybook.file != _COPYBOOK:
            continue
        # setdefault, so the column-mapped key already found for a field
        # wins over anything the copybook-only pass could offer for the
        # same name. The two agree for all twenty; this makes the
        # precedence explicit rather than incidental.
        keys.setdefault(copybook.name, entry.key)
    return keys


# Looked up once, at import, which is the only import-time work in this module
# beyond the dictionary's own lazy cached read (rule R-6).
_KEYS: Final[dict[str, str]] = _dictionary_keys()


def _describe(cobol_name: str) -> FieldDescriptor:
    """Return the storage description the dictionary holds for one field.

    Args:
        cobol_name: A COBOL field name of this record, verbatim from
            `copybooks/wssys4.cob` - `"sl4-spare3"`, `"filler"`,
            `"Sales-Ledger-Data"`. Case-sensitive, as every name in the
            dictionary is.

    Returns:
        Its descriptor, carrying the COPYBOOK view of digits, scale,
        sign, usage and Python carrier, plus the dictionary key and the
        copybook locator that make it traceable.

    Raises:
        KeyError: No item of this record is named so, which can only be
            a mis-typed name in this module or an artifact that no longer
            covers this copybook. The key names the field.
    """
    return FieldDescriptor.from_dictionary_key(_KEYS[cobol_name])


def _declaration_line(descriptor: FieldDescriptor) -> int:
    """Return the copybook line a field is declared on.

    Read out of the descriptor's own `<path>:L<n>` locator, which a
    dictionary-backed descriptor always carries - for a record field it
    points at the copybook declaration. A locator naming a span keeps its
    first line, which is the declaration's own.

    This exists so that declaration order is DERIVED rather than
    restated. `loader.entries_for_copybook_record` returns document
    order, and for a table-backed record that is column ordinal order
    first with the copybook-only fields after it; its docstring directs a
    caller who needs strict declaration order to "each entry's own
    `copybook.source` line to order by". This is that ordering key.

    Args:
        descriptor: A descriptor built from a dictionary entry.

    Returns:
        The line number its declaration begins on.
    """
    _, _, tail = str(descriptor.source_locator).rpartition(":L")
    return int(tail.partition("-")[0])


def _children_of(group: str) -> tuple[FieldDescriptor, ...]:
    """Describe the items one group of this record declares, in order.

    Order comes from the copybook, through `_declaration_line`, so the
    result is an independent witness to the hand-written attribute order
    of the class it belongs to rather than a restatement of it. Sorting
    is stable and the line numbers are distinct, so two runs agree
    (rule R-6).

    Args:
        group: A group name verbatim from the copybook -
            `"Sales-Ledger-Data"`, `"Purchase-Ledger-Data"` or
            `"System-Record-4"` for the record's own three children.

    Returns:
        The descriptors of the items immediately subordinate to it, in
        copybook declaration order. Group items are included where the
        copybook declares them, which is how the record's two `03`
        headers reach `SystemRecord4.FIELDS`.
    """
    return tuple(
        sorted(
            (
                descriptor
                for descriptor in (_describe(name) for name in _KEYS)
                if descriptor.parent_group == group
            ),
            key=_declaration_line,
        )
    )


# The FILLER at [copybooks/wssys4.cob:L31] and the width it pads the record
# to. The width is DERIVED from the descriptor rather than written here, so
# the value and the description cannot drift apart. The arithmetic it closes:
#
#     20 money items x 6 bytes each   = 120   (s9(8)v99 comp-3: ten digits
#                                              pack into six bytes)
#      1 FILLER      x 904 bytes      = 904
#                                      -----
#                                       1024   "Record size 1024 bytes to
#                                               match system-record"
#                                              [copybooks/wssys4.cob:L6]
_FILLER: Final[FieldDescriptor] = _describe("filler")
_FILLER_SPACES: Final[str] = " " * _FILLER.byte_length


# =============================================================================
#  THE SALES HALF  [copybooks/wssys4.cob:L9-L19]
# =============================================================================


@dataclass(slots=True)
class SalesLedgerData:
    """`03  Sales-Ledger-Data  comp-3.` [copybooks/wssys4.cob:L9].

    The level number, the identifier, the group's USAGE clause and its
    terminating period are the copybook's own; only the column padding
    that aligns `comp-3.` in the source is compressed to fit here. The
    full-width declaration is in this module's docstring inventory.

    The Sales half of the period totals: ten money items at
    [copybooks/wssys4.cob:L10-L19], every one of them PACKED DECIMAL by
    inheritance from the `comp-3` on this group's own header, and every
    one signed with two decimal places over ten digits.

    Five of the ten are accumulated by the migrated cycle, and each
    attribute below names the statement that reaches it. The other five -
    both outstanding-balance figures, the variance and the two spares -
    are carried but written by nothing in scope; the roll-over that
    carries this month into last month and clears the accumulators is the
    out-of-scope end-of-cycle driver's [common/xl150.cbl:L1726-L1730].

    Mutable on purpose, never frozen: the posting sites add into these
    fields and the record is then rewritten through handler `acas000`.
    """

    # Class-level traceability, not record fields: `FIELDS` is the ten
    # descriptors in copybook declaration order and `DESCRIPTOR` is this
    # group item's own, so the `comp-3` header at L9 cites its entry too.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _children_of(_SALES_GROUP)
    DESCRIPTOR: ClassVar[FieldDescriptor] = _describe(_SALES_GROUP)

    # sl-os-bal-last-month  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L10]
    #   set only by the out-of-scope roll-over's `move
    #   SL-os-bal-This-month to SL-os-bal-Last-month`
    #   [common/xl150.cbl:L1726]
    sl_os_bal_last_month: Decimal = Decimal("0.00")

    # sl-os-bal-this-month  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L11]
    sl_os_bal_this_month: Decimal = Decimal("0.00")

    # sl-invoices-this-month  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L12]
    #   accumulated by `add ws-inv-amt to sl-invoices-this-month`
    #   [sales/sl055.cbl:L675]
    sl_invoices_this_month: Decimal = Decimal("0.00")

    # sl-credit-notes-this-month  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L13]
    #   accumulated by `add ws-inv-amt to sl-credit-notes-this-month`
    #   [sales/sl055.cbl:L677]
    sl_credit_notes_this_month: Decimal = Decimal("0.00")

    # sl-variance  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L14]
    #   STORED, never computed. Nothing in the migrated cycle writes it
    #   and nothing here derives it; the out-of-scope roll-over zeroes it
    #   [common/xl150.cbl:L1727].
    sl_variance: Decimal = Decimal("0.00")

    # sl-credit-deductions  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L15]
    #   accumulated by `add total-deduct to sl-credit-deductions`
    #   [sales/sl060.cbl:L641]. Its purchase counterpart has no such
    #   statement - see `PurchaseLedgerData.pl_credit_deductions`.
    sl_credit_deductions: Decimal = Decimal("0.00")

    # sl-cn-unappl-this-month  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L16]
    #   accumulated by `add work-b to sl-cn-unappl-this-month`
    #   [sales/sl060.cbl:L700]
    sl_cn_unappl_this_month: Decimal = Decimal("0.00")

    # sl-payments  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L17]
    #   accumulated by the MULTI-TARGET `add oi-paid to t-paid
    #   sl-payments` [sales/sl100.cbl:L404], which feeds a program-local
    #   total and this period total from one statement
    sl_payments: Decimal = Decimal("0.00")

    # sl4-spare1  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L18]
    #   a spare the maintainer left in the Sales group, where its `sl4-`
    #   prefix belongs. Kept because it is a real column, `SL4-SPARE1`
    #   [mysql/ACASDB.sql:L1386].
    sl4_spare1: Decimal = Decimal("0.00")

    # sl4-spare2  pic s9(8)v99  comp-3 inherited from
    # Sales-Ledger-Data  [copybooks/wssys4.cob:L19]
    #   the second Sales spare, column `SL4-SPARE2`
    #   [mysql/ACASDB.sql:L1387]. Its numbering runs on into the Purchase
    #   group, which is how anomaly A-20 arises there.
    sl4_spare2: Decimal = Decimal("0.00")


# =============================================================================
#  THE PURCHASE HALF  [copybooks/wssys4.cob:L20-L30]  -  HOLDS ANOMALY A-20
# =============================================================================


@dataclass(slots=True)
class PurchaseLedgerData:
    """`03  Purchase-Ledger-Data  comp-3.` [copybooks/wssys4.cob:L20].

    Quoted on the same terms as `SalesLedgerData`: everything but the
    source's column padding is the copybook's own.

    The Purchase half of the period totals: ten money items at
    [copybooks/wssys4.cob:L21-L30], packed decimal by inheritance from
    the `comp-3` on this group's own header, signed, two decimal places.

    Four of the ten are accumulated by the migrated cycle. The layout is
    the Sales half's mirror in eight of its ten positions and diverges in
    two places, both preserved:

        * `pl-credit-deductions` is never accumulated, while its Sales
          counterpart is [sales/sl060.cbl:L641].
        * THE LAST TWO ITEMS CARRY THE SALES PREFIX. `sl4-spare3` and
          `sl4-spare4` are declared here, in the Purchase group, and not
          in the Sales group where their `sl4-` names would fit. That is
          ANOMALY A-20 and this class is its reproducing site; see the
          comment on each attribute and this module's docstring.

    Mutable on purpose, never frozen.
    """

    # Class-level traceability, not record fields. `FIELDS` ends with the
    # two A-20 descriptors, whose `name` values are the verbatim COBOL
    # `sl4-spare3` and `sl4-spare4` and whose `parent_group` is this group.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _children_of(
        _PURCHASE_GROUP
    )
    DESCRIPTOR: ClassVar[FieldDescriptor] = _describe(_PURCHASE_GROUP)

    # pl-os-bal-last-month  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L21]
    #   set only by the out-of-scope roll-over's `move
    #   PL-os-bal-This-month to PL-os-bal-Last-month`
    #   [common/xl150.cbl:L1997]
    pl_os_bal_last_month: Decimal = Decimal("0.00")

    # pl-os-bal-this-month  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L22]
    pl_os_bal_this_month: Decimal = Decimal("0.00")

    # pl-invoices-this-month  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L23]
    #   accumulated by `add ws-inv-amt to pl-invoices-this-month`
    #   [purchase/pl055.cbl:L582]
    pl_invoices_this_month: Decimal = Decimal("0.00")

    # pl-credit-notes-this-month  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L24]
    #   accumulated by `add ws-inv-amt to pl-credit-notes-this-month`
    #   [purchase/pl055.cbl:L584]
    pl_credit_notes_this_month: Decimal = Decimal("0.00")

    # pl-variance  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L25]
    #   STORED, never computed, exactly like its Sales counterpart. The
    #   out-of-scope roll-over zeroes it [common/xl150.cbl:L1998].
    pl_variance: Decimal = Decimal("0.00")

    # pl-credit-deductions  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L26]
    #   NEVER ACCUMULATED BY THE MIGRATED CYCLE, unlike the Sales
    #   counterpart at [sales/sl060.cbl:L641]. No in-scope purchase
    #   program names it, and the only other mention of it in the
    #   purchase tree is commented out [purchase/pl120.cbl:L900]. The
    #   out-of-scope roll-over still zeroes it
    #   [common/xl150.cbl:L2000]. The asymmetry is the specification;
    #   nothing here evens it up.
    pl_credit_deductions: Decimal = Decimal("0.00")

    # pl-cn-unappl-this-month  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L27]
    #   accumulated by `add work-b to pl-cn-unappl-this-month`
    #   [purchase/pl060.cbl:L628]
    pl_cn_unappl_this_month: Decimal = Decimal("0.00")

    # pl-payments  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L28]
    #   accumulated by the MULTI-TARGET `add oi-paid to t-paid
    #   pl-payments` [purchase/pl100.cbl:L396]
    pl_payments: Decimal = Decimal("0.00")

    # sl4-spare3  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L29]
    #
    #   ANOMALY A-20, REPRODUCED AND NOT PUT RIGHT. The maintainer
    #   declared this spare with the SALES prefix `sl4-` inside the
    #   PURCHASE group [copybooks/wssys4.cob:L20], among eight `pl-`
    #   siblings, while the Sales group's own spares are `sl4-spare1`
    #   [copybooks/wssys4.cob:L18] and `sl4-spare2`
    #   [copybooks/wssys4.cob:L19]. The misnaming carries through the
    #   whole chain: host variable `HV-SL4-SPARE3`
    #   [common/sys4MT.cbl:L334] and column `SL4-SPARE3`
    #   [mysql/ACASDB.sql:L1396]. Rule R-4 makes it part of the
    #   specification - a defect reproduced is correct, a defect fixed is
    #   a failure - so the name stays exactly as he wrote it, in this
    #   group, and is never given a purchase prefix nor moved into
    #   `SalesLedgerData` to make the names agree. The dictionary tags
    #   this field `A-20` too; `docs/migration/anomaly-log.md` registers
    #   it against this module.
    sl4_spare3: Decimal = Decimal("0.00")

    # sl4-spare4  pic s9(8)v99  comp-3 inherited from
    # Purchase-Ledger-Data  [copybooks/wssys4.cob:L30]
    #
    #   ANOMALY A-20, REPRODUCED AND NOT PUT RIGHT - the second of the
    #   pair, on the same terms as `sl4_spare3` above. Sales prefix,
    #   Purchase group, kept: host variable `HV-SL4-SPARE4`
    #   [common/sys4MT.cbl:L335], column `SL4-SPARE4`
    #   [mysql/ACASDB.sql:L1397], dictionary anomaly reference `A-20`.
    sl4_spare4: Decimal = Decimal("0.00")


# =============================================================================
#  THE RECORD  [copybooks/wssys4.cob:L8-L31]
# =============================================================================


@dataclass(slots=True)
class SystemRecord4:
    """`01  System-Record-4.` [copybooks/wssys4.cob:L8].

    The whole period-totals record, in the copybook's own order: the
    Sales group [copybooks/wssys4.cob:L9], then the Purchase group
    [copybooks/wssys4.cob:L20], then the FILLER
    [copybooks/wssys4.cob:L31]. Three `03` items, twenty money figures
    between the two groups, 1024 bytes.

    It reaches the twenty-one column table `SYSTOT-REC` through the
    `sys4MT` bridge and handler `acas000` on file-key number 4, and it
    reaches a program through LINKAGE as the third parameter of the Sales
    and Purchase posting shape [sales/sl055.cbl:L269-L275] - never by a
    file read of its own.

    A default instance is the record with every figure at zero and the
    FILLER at spaces, which is what an `INITIALIZE` of the group leaves
    behind. Building one field by field means building its two groups::

        totals = SystemRecord4(
            sales_ledger_data=SalesLedgerData(
                sl_invoices_this_month=Decimal("1234.56"),
            ),
        )

    Mutable on purpose, never frozen: the nine period-total sites listed
    in this module's docstring add into these figures and the record is
    rewritten. It carries no rolled-up figure and no accumulate helper -
    that logic belongs to the program modules (rule R-3).
    """

    # Class-level traceability, not record fields: the three items this
    # record declares, in declaration order, and the record item itself.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = _children_of(_RECORD)
    DESCRIPTOR: ClassVar[FieldDescriptor] = _describe(_RECORD)

    # Sales-Ledger-Data  group, comp-3 declared here for its ten children
    # [copybooks/wssys4.cob:L9]
    sales_ledger_data: SalesLedgerData = field(
        default_factory=SalesLedgerData
    )

    # Purchase-Ledger-Data  group, comp-3 declared here for its ten
    # children, two of which keep the Sales prefix - anomaly A-20
    # [copybooks/wssys4.cob:L20]
    purchase_ledger_data: PurchaseLedgerData = field(
        default_factory=PurchaseLedgerData
    )

    # filler  pic x(904)  alphanumeric, no usage clause
    # [copybooks/wssys4.cob:L31]
    #   904 bytes of padding, and nothing else: 20 packed items of six
    #   bytes reach 120, and this FILLER takes the record to the 1024 the
    #   header asks for to "match system-record"
    #   [copybooks/wssys4.cob:L6]. Named rather than left implicit
    #   because the copybook declares it as a real `03` item, and
    #   defaulted to spaces at a width read off its own descriptor so the
    #   value and the description cannot drift apart. It maps to no
    #   column - the dictionary holds it as a copybook-only entry with
    #   both its bridge and column views absent - so it never appears in
    #   a table dump.
    filler: str = _FILLER_SPACES
