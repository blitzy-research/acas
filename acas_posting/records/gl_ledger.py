"""The General/Nominal Ledger account record: `WS-Ledger-Record`.

A CREATE from `copybooks/wsledger.cob`, which the copybook's own header calls
the "WS definition for the General/Nominal Ledger file"
[copybooks/wsledger.cob:L3-L4]. This module declares the layout and nothing
else. It stores; it does not post, read, sort, scale, concatenate or validate.

This is the account the whole General Ledger posting cycle writes into.
Agent Action Plan section 0.4.1.2 assigns the writing elsewhere, verbatim:
`gl072` "Posts to the nominal ledger by accumulating into the ledger balance."
That accumulation lives in `acas_posting/programs/gl072_transaction_update.py`,
so `Ledger-Balance` and the four quarters below are plain mutable attributes
with no accumulator method attached (R-3).

THE ENTITY-TO-TABLE SPINE  (Agent Action Plan section 0.2.1.1)
==============================================================
    entity facade   GL-Nominal
    handler         acas005
    bridge          nominalMT
    MySQL table     GLLEDGER-REC, 11 columns, PRIMARY KEY (LEDGER-KEY)
                    [mysql/ACASDB.sql:L122-L134]
    copybook        copybooks/wsledger.cob

Section 0.6.6 records what makes the state diff cheap for this table: a
single-column primary key, no secondary index, no TIMESTAMP column, no
AUTO_INCREMENT and no column-level DEFAULT. The dump is therefore a plain
SELECT of every column ordered by LEDGER-KEY, with no tie-breaking logic -
which is the comparison harness's business, not this module's.

WHY THIS RECORD IS REACHED SEQUENTIALLY  -  READ THIS BEFORE TOUCHING ORDER
==========================================================================
Section 0.6.4's strongest finding concerns this very record, verbatim:

    "The sort feeds a sequential read. `gl072` locates the nominal-ledger
    account for each posting with a sequential read-next rather than an
    indexed read. It finds the right account only because `gl071` has already
    emitted the stream in nominal-key order. Any change in sort stability or
    key composition produces silent misposting - no error, no diagnostic,
    wrong balances."

The plan cites that read at [general/gl072.cbl:L410-L412]. The actual sites
are [general/gl072.cbl:L405] and [general/gl072.cbl:L407-L408]; the verified
locators are recorded here and were confirmed independently by the author of
`acas_posting/cobol/sortverb.py`. L405 is `move post-ledger to WS-Ledger-Key`,
where `post-ledger` is a GROUP in `gl072`'s own work record
[general/gl072.cbl:L115] combining `post-ac pic 9(6)` and `post-pc pic 99`.
A whole eight-digit group moves into `WS-Ledger-Key` in one statement, which
is why the group's shape below is load-bearing rather than cosmetic.

None of that is implemented here. The ordering guarantee belongs to
`gl071_batch_sort.py` and `cobol/sortverb.py`; the read belongs to
`dal/acas005_gl_nominal.py`.

ANOMALY A-12 IS REPRODUCED HERE  -  THIS MODULE IS ITS SITE  (R-4)
==================================================================
Anomaly register entry 12 (section 0.6.7) reads "Ledger-name width drift from
24 to 32 characters across copybook, host variable and column". All three
layers were read directly and disagree:

    copybook    `03  Ledger-Name       pic x(24).`
                                        [copybooks/wsledger.cob:L27]
    host var    `05  HV-LEDGER-NAME    PIC X(32).`
                                        [common/nominalMT.cbl:L299]
    column      LEDGER-NAME char(32) NOT NULL
                                        [mysql/ACASDB.sql:L127]

`ledger_name` below is 24 characters, the copybook's own width, and it is
never widened to 32. Section 0.6.2 states why the widening is harmless to the
value and yet must not be applied here: "The value is not corrupted, but the
padding differs, and padding is visible in a table dump". The dictionary holds
all three views plus an unadjudicated `drift` object, surfaced through
`WsLedgerRecord.LEDGER_NAME.drift()` and tagged `A-12` by that same
descriptor's `anomaly_refs()`, and this module settles none of it. The
widening on write belongs to
`dal/acas005_gl_nominal.py`, which reproduces the bridge boundary; the padding
difference is absorbed by the harness dump comparison step. Both are named at
the attribute itself so the register can cite this file.

The bridge moves the value at [common/nominalMT.cbl:L965] and [:L993] and
trims it with `FUNCTION TRIM (HV-LEDGER-NAME,TRAILING)` at [:L1067] and
[:L1246]. No trimming or padding of a supplied value happens below.

A SECOND, LESS ADVERTISED DRIFT ON THE SAME RECORD
==================================================
`LEDGER-KEY` drifts too, in three aspects at once, and the dictionary reports
all three: the storage class changes DISPLAY -> COMP -> INT, the digit count
changes 8 -> 10 -> 8, and even the name changes, the copybook calling it
`WS-Ledger-Key9` while both the host variable and the column call it
`LEDGER-KEY`. The host variable is `PIC 9(10) COMP`
[common/nominalMT.cbl:L295] against a copybook field of eight digits and a
column of `int(8) unsigned` [mysql/ACASDB.sql:L123]. It carries no anomaly
reference of its own, so it is recorded here rather than left for a reader to
rediscover. It is not adjudicated either.

By contrast the six money fields are a CLEAN PASS-THROUGH in every aspect
that could move a figure: signedness, digits and scale agree across all three
layers. Only the storage class changes at the bridge, COMP-3 -> COMP ->
DECIMAL, as it does for every numeric field the bridge carries. Section 0.6.2
makes the general point that the drift in this system "is specific rather than
systemic and must be handled field by field from the dictionary". This record
is a compact demonstration: its character field drifts, its key drifts, and
its money does not.

HOW THE EIGHT-DIGIT KEY REACHES ONE COLUMN  -  NO CONCATENATION EXISTS
======================================================================
`WS-Ledger-Key` [:L13] holds `WS-Ledger-Nos pic 9(6)` [:L14] - itself
redefined into `Ledger-n pic 9(4)` plus `Ledger-s pic 9(2)` [:L16-L18] - and
`Ledger-PC pic 9(2)` [:L20]. Eight DISPLAY digits in eight bytes, flattened
into the single column `LEDGER-KEY int(8) unsigned`.

Nothing flattens them. The plan describes this as a "group-concatenation
drift" and directs that the concatenation not be built here; the frozen bridge
shows there is no concatenation to build anywhere. COBOL `REDEFINES` supplies
a ready-made eight-digit numeric view over the same eight bytes, and the
bridge simply moves that view:

    load    `move     WS-Ledger-Key9  to HV-LEDGER-KEY.`
                                        [common/nominalMT.cbl:L962]
    unload  `move     HV-LEDGER-KEY         to WS-Ledger-Key9`
                                        [common/nominalMT.cbl:L990]

So `WS-Ledger-Key9` is the field backing `LEDGER-KEY`, confirmed by the
generated dictionary independently: `loader.entries_for_table("GLLEDGER-REC")`
returns `GLLEDGER-REC.LEDGER-KEY` with `copybook.name == "WS-Ledger-Key9"`.
The copybook's own changelog says why the field was added at all - "07/01/17
vbc - Added new field ledger-key9." [copybooks/wsledger.cob:L9] - one release
after the layout was taken from `fdledger` [:L8].

The GROUP view stays live alongside it: the bridge builds its ISAM key from
the group, not the redefine, at [common/nominalMT.cbl:L743] and [:L795],
`move WS-Ledger-Key to WS-File-Key.` Both views are therefore declared below,
because both are used. Neither view is picked over the other and no key is
assembled here; `dal/acas005_gl_nominal.py` owns the bridge boundary.

REDEFINES DOES NOT ALIAS IN PYTHON  -  A GAP STATED RATHER THAN PAPERED OVER
============================================================================
In COBOL a REDEFINES item occupies the SAME BYTES as the item it redefines, so
storing through one view is immediately visible through the other. Separate
Python attributes are separate storage and do NOT alias: assigning
`ws_ledger_key9.ws_ledger_key9` leaves `ws_ledger_key.ws_ledger_nos`
untouched, and the reverse.

That difference is recorded and not repaired. Reproducing byte aliasing would
mean adding synchronising logic to this layer, which R-3 forbids outright and
which would put a behavioural decision in a record layout. The three redefine
views below are declared for traceability and for use by the layers that own
the corresponding COBOL statements - whichever view a program names is that
program's business, and the handler module reads `WS-Ledger-Key9` because the
bridge does.

SIZE  -  THE HEADER NOTE AND THE FIELD SUM AGREE
================================================
The copybook's last header note is `*> 31/01/18 vbc - Resized to 126 bytes.`
[copybooks/wsledger.cob:L10]. Summing the storage-bearing items in
declaration order, with REDEFINES contributing no new bytes because it shares
the storage it redefines, and packed decimal occupying `ceil((digits + 1) / 2)`
bytes:

    WS-Ledger-Nos    pic 9(6)              DISPLAY    6      [:L14]
    Ledger-PC        pic 9(2)              DISPLAY    2      [:L20]
    Ledger-Type      pic 9                 DISPLAY    1      [:L23]
    Ledger-Place     pic x                 DISPLAY    1      [:L24]
    Ledger-Level     pic 9                 DISPLAY    1      [:L25]
    filler           pic x(5)              DISPLAY    5      [:L26]
    Ledger-Name      pic x(24)             DISPLAY   24      [:L27]
    Ledger-Balance   pic s9(8)v99 comp-3   PACKED     6      [:L28]
    Ledger-Last      pic s9(8)v99 comp-3   PACKED     6      [:L29]
    Ledger-Q1..Q4    pic s9(8)v99 comp-3   PACKED    24      [:L31-L34]
    filler           pic x(50)             DISPLAY   50      [:L37]
                                                     ---
                                                     126

126 bytes, matching the note exactly. Stated because the sibling batch record
does NOT agree with its own declared length - anomaly 15, "The batch record's
declared length contradicts the sum of its fields" - and section 0.6.8 lists
that contradiction among the questions only the compiled program can settle.
This record raises no such question, so there is nothing here to leave open.
The arithmetic is reproduced above so the claim is checkable rather than
asserted; the widths themselves are read from the dictionary, never typed in.

TWO FURTHER PROPERTIES OF THIS COPYBOOK, BOTH UNUSUAL IN THIS FOLDER
====================================================================
USAGE IS DECLARED ON THE FIELD, NOT ON A GROUP. Every one of the seven
`comp-3` items carries its usage on its own line - [:L28], [:L29], [:L31],
[:L32], [:L33], [:L34], [:L36] - and no group header in this copybook carries
a usage clause at all. Their descriptors therefore report
`usage_declared_at == FIELD` and `usage_inherited_from is None`. This is worth
stating because most sibling record modules are the other way round: across
the generated artifact 85 fields inherit usage from 12 group headers, among
them `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40], which silently makes
`05 Input-Gross pic 9(9)v99.` packed decimal with nothing on its own line
saying so. Nothing is inherited here, and a reader should not assume it is.

NO CONDITION NAMES. This copybook declares no `88` level: `grep -c ' 88 '`
over it returns 0. Unusual for this codebase - the batch and system records
this cycle tests are full of them, `Status-Open` and `Waiting` among them -
and stated so that nobody looks for a predicate that the frozen source never
declared. No predicate, property or enumeration is defined below, and
`cobol.condition_names` is deliberately not imported.

FILLER IS MODELLED AS NAMED ATTRIBUTES  -  THE CHOICE AND THE REASON
====================================================================
The two storage-bearing FILLER items, `pic x(5)` [:L26] and `pic x(50)`
[:L37], are declared as the attributes `filler_l26` and `filler_l37`, each
carrying a descriptor whose `is_filler` is True. They could have been left as
descriptors with no attribute. They are not, for one measured reason: at 5 and
50 bytes they are 55 of the record's 126 bytes, 43.7% of it, and R-3 requires
these modules "mirror their copybooks field for field with nothing added" -
which cuts both ways, since a mirror that drops 43.7% of the bytes is not a
mirror. The suffixes are the declaration lines, mirroring the dictionary's own
key convention for repeated names, `WS-Ledger-Record.filler#26` and
`WS-Ledger-Record.filler#37`, so the correspondence needs no lookup table.

The two anonymous FILLER items at [:L16] and [:L35] are different: both are
group headers introducing a REDEFINES view and neither has storage of its own,
so each becomes a view class rather than an attribute, and the descriptor that
carries its REDEFINES clause is surfaced on that class.

DESCRIPTORS ARE LOOKED UP, NEVER TRANSCRIBED  (R-5)
===================================================
No picture clause, digit count, scale, sign, storage class, character width or
OCCURS count is typed in below. Every one is read from the generated data
dictionary through `FieldDescriptor.from_dictionary_key`, whose keys were
obtained by calling `loader.entries_for_table("GLLEDGER-REC")` and
`loader.entries_for_copybook_record("WS-Ledger-Record")` and reading each
entry's own `copybook.name` - never guessed from a field name. Section 0.8.1
makes that ordering binding rather than tidy:

    "Data dictionary first. The dictionary is generated from the bridge before
    record definitions are written, and every Python field definition cites
    its entry. This ordering is a directive, not a preference - it is what
    prevents fields being transcribed by eye."

Defaults follow from the descriptors too: string widths come from
`character_length` and the quarter table's length from `occurs`, so no width
literal appears in this file and none can drift from the frozen source.

Every class exposes `FIELDS`, its descriptors in copybook declaration order,
and the group and redefine descriptors are exposed alongside them. All are
`ClassVar` tuples, so they are not dataclass fields and add no attribute to
any instance.

THE LOADER IS REACHED THROUGH THE DESCRIPTOR, NOT IMPORTED DIRECTLY. The two
provenance primitives this module owes its readers are both already published
on `FieldDescriptor` as documented pass-throughs: `descriptor.cite()` returns
`loader.cite(key)` verbatim and `descriptor.drift()` returns
`loader.drift_for(key)` verbatim, neither reduced to a boolean nor summarised.
Surfacing them through the descriptor is the sanctioned route rather than a
reimplementation, and it keeps this module's import edges at one. A second,
direct edge to the loader would be redundant - and an unused import, which is
a defect in its own right.

So the whole provenance surface is available from any descriptor here:

    WsLedgerRecord.LEDGER_NAME.cite()          the three locators
    WsLedgerRecord.LEDGER_NAME.drift()         the disagreement, unadjudicated
    WsLedgerRecord.LEDGER_NAME.anomaly_refs()  ('A-12',)
    WsLedgerRecord.LEDGER_NAME.dictionary_key  'GLLEDGER-REC.LEDGER-NAME'

and the table-level and record-level listings, for a reader who wants to check
this module against the artifact, come straight from the loader itself:
`loader.entries_for_table("GLLEDGER-REC")` for the eleven column-mapped
entries in column ordinal order, and
`loader.entries_for_copybook_record("WS-Ledger-Record")` for all twenty-three.

TYPES  (R-2)
============
    pic 9(n)                        -> int,     default 0
    pic x(n)                        -> str,     default n spaces
    pic s9(8)v99 comp-3             -> Decimal, default Decimal("0.00")

Signed, ten digits, scale two for all six money fields, and `Ledger-Balance`
is the figure the entire General Ledger cycle accumulates into. A binary
floating-point value here would corrupt every posted balance, so no such value
appears in this file and none may be introduced. Spaces rather than the empty
string are the string
default because section 0.6.2 records that each bridge load paragraph "begins
by initialising the host-variable group, so unset fields become zero or space
rather than SQL NULL. This is why every column in the schema can be declared
NOT NULL and why the Python layer must default rather than omit."

WHAT THIS MODULE DOES NOT DO
============================
No accumulation, no posting, no key assembly, no account-number scaling - the
divides and multiplies by 100 at [general/gl072.cbl:L386] and [:L413] belong
to `gl072_transaction_update.py`. No bounds check on the quarter table, for
the reason given at `LedgerQuartersTable`. No widening or trimming of
`ledger_name`. No post-initialisation hook, no value checking, no property, no
ORM base class or declarative metadata, no SQL and no DDL. No clock, no
entropy, no environment read and no concurrency.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
    MAY import       `acas_posting.cobol.field`,
                     `acas_posting.dictionary.loader`, and the standard library
    MUST NOT import  anything else - "this keeps the record layer a leaf",
                     including every other module of this package

Section 0.4.3's promise is what the restriction protects: the arithmetic test
tier "imports only `cobol` and `records` and touches no database, so it runs
anywhere". One import reaching into `dal` would drag a database driver into
that tier. `cobol.arithmetic` is the live temptation in a record full of
accumulators and is not imported either: the programs accumulate, this record
only stores.

The rule identifiers R-1 through R-6 are the Agent Action Plan's own
(section 0.7.2). This project carries no separate rules document - a
`review_rules` lookup returns "No user rules provided." - so the plan is where
their full text lives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[tuple[str, ...]] = (
    "LedgerQuarters",
    "LedgerQuartersTable",
    "WsLedgerKey",
    "WsLedgerKey9",
    "WsLedgerNosParts",
    "WsLedgerRecord",
)


# =============================================================================
#  THE DICTIONARY ENTRIES THIS RECORD IS BUILT FROM  (R-5)
# =============================================================================
#
# One descriptor per copybook item, in declaration order, each naming its own
# dictionary key. The key strings below were not invented: they were read back
# from the generated artifact by calling
#
#     loader.entries_for_table("GLLEDGER-REC")            -> 11 column-mapped
#     loader.entries_for_copybook_record("WS-Ledger-Record") -> 23 in total
#
# and taking each entry's own `key`. Both halves of a key are the names the
# frozen sources use themselves - hyphens intact, case unfolded - so lookup is
# exact. Where one name repeats inside one record the artifact appends `#` and
# the declaration line, which is why the two FILLER data items and the two
# anonymous FILLER groups are keyed `filler#16`, `filler#26`, `filler#35` and
# `filler#37`.
#
# `from_dictionary_key` is memoised on the key, and the loader reads the
# artifact lazily and caches it, so importing this module parses the dictionary
# once and repeated lookups return the same frozen object.
#
# Nothing about a field is written out below - no picture, no digit count, no
# scale, no sign, no storage class, no width, no OCCURS count. Every one of
# those comes from the entry, which is what section 0.3.3 means by "derived,
# not transcribed".

# -- the 01 record itself -------------------------------------------------
# 01  WS-Ledger-Record.                      [copybooks/wsledger.cob:L12]
# A group: no storage of its own, so no attribute corresponds to it.
_WS_LEDGER_RECORD: Final[FieldDescriptor] = (
    FieldDescriptor.from_dictionary_key("WS-Ledger-Record.WS-Ledger-Record")
)

# -- the key group and the two views over it -----------------------------
# 03  WS-Ledger-Key.                                                   [:L13]
# The eight bytes the bridge builds its ISAM key from, whole
# [common/nominalMT.cbl:L743], [common/nominalMT.cbl:L795]. No column of its
# own; the column is fed from the WS-Ledger-Key9 view instead [:L962].
_WS_LEDGER_KEY: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Key"
)

# 05      WS-Ledger-Nos    pic 9(6).                                   [:L14]
# Six DISPLAY digits. No column: LEDGER-KEY is fed from the redefine.
_WS_LEDGER_NOS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.WS-Ledger-Nos"
)

# 05      filler  redefines  WS-Ledger-Nos.                            [:L16]
# The anonymous group that carries the REDEFINES clause for the two-part view
# of WS-Ledger-Nos. `redefines` sits HERE, on the 05 group - not on the 07
# items beneath it. No storage and no column of its own.
_WS_LEDGER_NOS_REDEFINES: Final[FieldDescriptor] = (
    FieldDescriptor.from_dictionary_key("WS-Ledger-Record.filler#16")
)

# 07          Ledger-n  pic 9(4).                                      [:L17]
_LEDGER_N: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-n"
)

# 07          Ledger-s  pic 9(2).                                      [:L18]
_LEDGER_S: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-s"
)

# 05      Ledger-PC     pic 9(2).                                      [:L20]
# The profit-centre pair completing the eight digits. No column of its own.
_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-PC"
)

# 03  WS-Ledger-Key9 redefines WS-Ledger-Key                       [:L21-L22]
#                       pic 9(8).
# TWO PHYSICAL LINES, ONE DECLARATION. L21 carries the name and the REDEFINES
# clause; the `pic 9(8).` that types the field is alone on L22. A line-by-line
# read of the copybook misses the picture and mis-types the field, so the span
# is cited as L21-L22 throughout.
#
# THIS IS THE FIELD BEHIND THE LEDGER-KEY COLUMN, which is why its key is
# table-qualified while its three siblings above are record-qualified. The
# bridge moves this redefine, not the group: `move WS-Ledger-Key9 to
# HV-LEDGER-KEY.` [common/nominalMT.cbl:L962], and back at [:L990]. It drifts
# in three aspects at once - DISPLAY -> COMP -> INT, 8 digits -> 10 -> 8, and
# the name itself, WS-Ledger-Key9 -> LEDGER-KEY - all of it readable through
# `WsLedgerKey9.WS_LEDGER_KEY9.drift()` and none of it settled here.
_WS_LEDGER_KEY9: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-KEY"
)

# -- the scalar body -----------------------------------------------------
# 03  Ledger-Type       pic 9.                                         [:L23]
_LEDGER_TYPE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-TYPE"
)

# 03  Ledger-Place      pic x.                                         [:L24]
_LEDGER_PLACE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-PLACE"
)

# 03  Ledger-Level      pic 9.                                         [:L25]
_LEDGER_LEVEL: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LEVEL"
)

# 03  filler            pic x(5).                                      [:L26]
# Five bytes of real storage with NO MySQL column. Declared because R-3 has
# these modules mirror the copybook field for field; see the module docstring
# for why both FILLERs became attributes rather than descriptors alone.
_FILLER_L26: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.filler#26"
)

# 03  Ledger-Name       pic x(24).                                     [:L27]
# ANOMALY A-12. Twenty-four characters here, thirty-two at the bridge host
# variable [common/nominalMT.cbl:L299] and thirty-two at the column
# [mysql/ACASDB.sql:L127]. This descriptor reports the COPYBOOK view, so its
# `character_length` is 24 and never the column's width; `drift()` hands back
# the disagreement untouched and `anomaly_refs()` returns ('A-12',).
_LEDGER_NAME: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-NAME"
)

# -- the money ------------------------------------------------------------
# Six fields, every one `pic s9(8)v99   comp-3` with the usage on its OWN
# line: signed, ten digits, scale two, packed into six bytes each. Nothing is
# inherited from a group header, because no group header in this copybook
# declares a usage at all - so all six report `usage_declared_at == FIELD`.
#
# Signedness, digits and scale agree across copybook, host variable and
# column; only the storage class changes at the bridge, as it does for every
# numeric field it carries. The drift in this record is the character field
# and the key, not the money - section 0.6.2's point that the drift here "is
# specific rather than systemic" made concrete in one record.

# 03  Ledger-Balance    pic s9(8)v99   comp-3.                         [:L28]
# THE ACCUMULATOR THE WHOLE GENERAL LEDGER CYCLE WRITES INTO. gl072 adds each
# posting into it; `tests/arithmetic/test_ledger_balance_accumulation.py`
# locks that behaviour. Decimal only - a binary floating-point value here would
# corrupt every posted balance (R-2).
_LEDGER_BALANCE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-BALANCE"
)

# 03  Ledger-Last       pic s9(8)v99   comp-3.                         [:L29]
_LEDGER_LAST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-LAST"
)

# 03  Quarters.                                                        [:L30]
# A group: no storage of its own, no column of its own. Its four subordinates
# are the columns.
_QUARTERS: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Quarters"
)

# 05      Ledger-Q1 .. Ledger-Q4   pic s9(8)v99   comp-3.         [:L31-L34]
_LEDGER_Q1: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q1"
)
_LEDGER_Q2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q2"
)
_LEDGER_Q3: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q3"
)
_LEDGER_Q4: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "GLLEDGER-REC.LEDGER-Q4"
)

# 03  filler redefines Quarters.                                       [:L35]
# The anonymous group carrying the REDEFINES clause for the table view of the
# four quarters. As with L16, `redefines` sits on THIS group and the OCCURS
# sits on the 05 item beneath it. No storage and no column of its own.
_QUARTERS_REDEFINES: Final[FieldDescriptor] = (
    FieldDescriptor.from_dictionary_key("WS-Ledger-Record.filler#35")
)

# 05      Ledger-Q      pic s9(8)v99   comp-3   occurs  4.             [:L36]
# The same twenty-four bytes as Ledger-Q1..Q4, addressed as a table. Carries
# `occurs == 4`; carries no column, because LEDGER-Q1..LEDGER-Q4 are the
# named columns.
_LEDGER_Q: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.Ledger-Q"
)

# 03  filler            pic x(50).                                     [:L37]
# Fifty bytes of real storage with no MySQL column - the largest single item
# in the record, and the one that brings the field sum to the 126 bytes the
# copybook header claims at [copybooks/wsledger.cob:L10].
_FILLER_L37: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "WS-Ledger-Record.filler#37"
)


# =============================================================================
#  THE KEY GROUP AND ITS TWO ALTERNATE VIEWS
# =============================================================================


@dataclass(slots=True)
class WsLedgerNosParts:
    """The two-part view of `WS-Ledger-Nos`: a nominal number and a sub-code.

    NAMING. The COBOL original is ANONYMOUS - `05  filler  redefines
    WS-Ledger-Nos.` [copybooks/wsledger.cob:L16] - so this class needed a name
    that the copybook does not supply. `WsLedgerNosParts` was chosen because
    the group's whole purpose is to address `WS-Ledger-Nos` as its two
    constituent parts. The descriptor of the anonymous group itself is kept on
    `REDEFINES` below, keyed `WS-Ledger-Record.filler#16`, so the nameless
    original remains findable from here.

    WHERE THE CLAUSE SITS. `redefines` is carried by the 05 group at L16, not
    by the 07 items at L17 and L18 beneath it. `REDEFINES.redefines` is
    therefore `"WS-Ledger-Nos"` while `LEDGER_N.redefines` and
    `LEDGER_S.redefines` are both None. That is the copybook's own shape and
    not an omission.

    Neither part has a MySQL column: `LEDGER-KEY` is fed from the
    `WS-Ledger-Key9` view instead [common/nominalMT.cbl:L962]. Both are
    declared because R-3 has these modules mirror the copybook field for field.

    This view does NOT alias `WsLedgerKey.ws_ledger_nos`; see the module
    docstring under "REDEFINES DOES NOT ALIAS IN PYTHON".
    """

    # The anonymous group that carries the REDEFINES clause, kept so the
    # redefinition is readable from the class that represents it.
    REDEFINES: ClassVar[FieldDescriptor] = _WS_LEDGER_NOS_REDEFINES
    LEDGER_N: ClassVar[FieldDescriptor] = _LEDGER_N
    LEDGER_S: ClassVar[FieldDescriptor] = _LEDGER_S
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_LEDGER_N, _LEDGER_S)

    # 07  Ledger-n  pic 9(4).   DISPLAY, unsigned, 4 digits, scale 0   [:L17]
    ledger_n: int = 0

    # 07  Ledger-s  pic 9(2).   DISPLAY, unsigned, 2 digits, scale 0   [:L18]
    ledger_s: int = 0


@dataclass(slots=True)
class WsLedgerKey:
    """`WS-Ledger-Key` - the eight bytes that identify a nominal account.

    From `03  WS-Ledger-Key.` [copybooks/wsledger.cob:L13]. Eight DISPLAY
    digits in eight bytes: `WS-Ledger-Nos pic 9(6)` [:L14] followed by
    `Ledger-PC pic 9(2)` [:L20], with `WS-Ledger-Nos` itself redefined into
    two parts at [:L16-L18].

    The group has no column of its own, and no concatenation of its members is
    performed here or anywhere - `WsLedgerKey9` is an eight-digit view over
    these same eight bytes and the bridge moves that view straight into the
    host variable [common/nominalMT.cbl:L962]. The group form is nonetheless
    live: the bridge builds its ISAM key from it, `move WS-Ledger-Key to
    WS-File-Key.` at [common/nominalMT.cbl:L743] and [:L795].

    WHY THE GROUP SHAPE MATTERS BEHAVIOURALLY. `gl072` moves a whole
    eight-digit group into this one in a single statement - `move post-ledger
    to WS-Ledger-Key` [general/gl072.cbl:L405] - where `post-ledger` combines
    `post-ac pic 9(6)` with `post-pc pic 99` [general/gl072.cbl:L115]. The
    account it then finds comes from a SEQUENTIAL read
    [general/gl072.cbl:L407-L408], so the group's composition is what makes
    that read land on the right account. Nothing about the move, the read or
    the ordering is implemented here.
    """

    GROUP: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY
    WS_LEDGER_NOS: ClassVar[FieldDescriptor] = _WS_LEDGER_NOS
    LEDGER_PC: ClassVar[FieldDescriptor] = _LEDGER_PC
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_LEDGER_NOS,
        _WS_LEDGER_NOS_REDEFINES,
        _LEDGER_N,
        _LEDGER_S,
        _LEDGER_PC,
    )

    # 05  WS-Ledger-Nos    pic 9(6).  DISPLAY, unsigned, 6 digits      [:L14]
    ws_ledger_nos: int = 0

    # 05  filler  redefines  WS-Ledger-Nos.                       [:L16-L18]
    # The alternate two-part view of the six digits above. Separate storage in
    # Python; the COBOL byte aliasing is not reproduced (see module docstring).
    ws_ledger_nos_parts: WsLedgerNosParts = field(
        default_factory=WsLedgerNosParts
    )

    # 05  Ledger-PC     pic 9(2).  DISPLAY, unsigned, 2 digits, scale 0 [:L20]
    ledger_pc: int = 0


@dataclass(slots=True)
class WsLedgerKey9:
    """`WS-Ledger-Key9` - the same eight bytes read as one eight-digit number.

    From `03  WS-Ledger-Key9 redefines WS-Ledger-Key` [:L21] continued by
    `pic 9(8).` [:L22]. TWO PHYSICAL LINES, ONE DECLARATION: a line-by-line
    read of the copybook sees the REDEFINES on L21, misses the picture on L22
    and mis-types the field, so the span is always cited as L21-L22.

    The copybook's changelog records why it exists at all - "07/01/17 vbc -
    Added new field ledger-key9." [copybooks/wsledger.cob:L9] - one release
    after the layout was taken from `fdledger` [:L8]. It gives the bridge a
    single numeric item to move where the group would otherwise have to be
    assembled, and the bridge uses exactly that: `move WS-Ledger-Key9 to
    HV-LEDGER-KEY.` [common/nominalMT.cbl:L962], reversed at [:L990].

    So THIS is the field behind the `LEDGER-KEY` column, and its descriptor is
    the only one on this record whose key is table-qualified while its
    siblings inside the key group are record-qualified.

    A class wraps a single elementary item here rather than the item being
    declared directly on `WsLedgerRecord`. That keeps all three redefine views
    on this record symmetrical and gives the two-line declaration somewhere to
    be documented; the item is elementary, not a group, so `WS_LEDGER_KEY9`
    below is its own descriptor and there is no separate group descriptor.

    Separate storage in Python: assigning `ws_ledger_key9` does not change
    `WsLedgerKey.ws_ledger_nos`. See the module docstring.
    """

    WS_LEDGER_KEY9: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY9
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_WS_LEDGER_KEY9,)

    # 03  WS-Ledger-Key9 redefines WS-Ledger-Key pic 9(8).        [:L21-L22]
    # DISPLAY, unsigned, 8 digits, scale 0, redefines WS-Ledger-Key.
    # Drifts in three aspects at the bridge - storage class, digit count and
    # even the name - all readable through `WS_LEDGER_KEY9.drift()` and none
    # of it settled here (R-4).
    ws_ledger_key9: int = 0


# =============================================================================
#  THE FOUR QUARTERS, NAMED AND AS A TABLE
# =============================================================================

# The zero every money field starts at: signed, scale two, exact. Written once
# so that all six carry the identical value, and written from a STRING literal
# because constructing a Decimal from a binary floating-point literal instead
# would route an accounting default through binary floating point, which R-2
# forbids outright.
_MONEY_ZERO: Final[Decimal] = Decimal("0.00")

# The quarter table's default, built deterministically in index order and as a
# TUPLE because R-6 makes a fixed collection immutable. Its length is read from
# the descriptor's own OCCURS count, so it can never drift from the copybook.
_QUARTER_TABLE_ZERO: Final[tuple[Decimal, ...]] = tuple(
    _MONEY_ZERO for _ in range(_LEDGER_Q.occurs or 0)
)


@dataclass(slots=True)
class LedgerQuarters:
    """The four quarterly balances, addressed by name.

    NAMING. The COBOL original is `03  Quarters.`
    [copybooks/wsledger.cob:L30]. This class is `LedgerQuarters` rather than a
    bare `Quarters` because the bare name is too generic to survive an import
    into a program module - two sibling copybooks in this migration declare a
    group called `Quarters` of their own, and a reader seeing `Quarters` in
    `gl080_end_of_cycle.py` would have no way to tell which record it came
    from. The `Ledger` prefix names the record; the COBOL original is stated
    here so the correspondence is not lost.

    All four are `pic s9(8)v99   comp-3` with the usage on their own lines
    [:L31-L34]: signed, ten digits, scale two, packed into six bytes each.
    Each has its own MySQL column, `LEDGER-Q1` through `LEDGER-Q4`.

    `gl080` writes these during end-of-period processing, and it selects which
    one by a subscript it does not bounds-check - see `LedgerQuartersTable`,
    which is the view that subscript addresses.
    """

    GROUP: ClassVar[FieldDescriptor] = _QUARTERS
    LEDGER_Q1: ClassVar[FieldDescriptor] = _LEDGER_Q1
    LEDGER_Q2: ClassVar[FieldDescriptor] = _LEDGER_Q2
    LEDGER_Q3: ClassVar[FieldDescriptor] = _LEDGER_Q3
    LEDGER_Q4: ClassVar[FieldDescriptor] = _LEDGER_Q4
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _LEDGER_Q1,
        _LEDGER_Q2,
        _LEDGER_Q3,
        _LEDGER_Q4,
    )

    # 05  Ledger-Q1     pic s9(8)v99   comp-3.   COMP-3, signed, 10, 2 [:L31]
    ledger_q1: Decimal = _MONEY_ZERO

    # 05  Ledger-Q2     pic s9(8)v99   comp-3.   COMP-3, signed, 10, 2 [:L32]
    ledger_q2: Decimal = _MONEY_ZERO

    # 05  Ledger-Q3     pic s9(8)v99   comp-3.   COMP-3, signed, 10, 2 [:L33]
    ledger_q3: Decimal = _MONEY_ZERO

    # 05  Ledger-Q4     pic s9(8)v99   comp-3.   COMP-3, signed, 10, 2 [:L34]
    ledger_q4: Decimal = _MONEY_ZERO


@dataclass(slots=True)
class LedgerQuartersTable:
    """The same four quarterly balances, addressed as an OCCURS 4 table.

    NAMING. The COBOL original is ANONYMOUS - `03  filler redefines Quarters.`
    [copybooks/wsledger.cob:L35] - holding one subordinate,
    `05  Ledger-Q      pic s9(8)v99   comp-3   occurs  4.` [:L36]. The name
    `LedgerQuartersTable` was chosen to pair with `LedgerQuarters`, and the
    anonymous group's own descriptor is kept on `REDEFINES` below, keyed
    `WS-Ledger-Record.filler#35`, so the nameless original stays findable.

    WHERE THE CLAUSES SIT. `redefines` is on the 03 group at L35;
    `occurs` is on the 05 item at L36. So `REDEFINES.redefines` is
    `"Quarters"` while `LEDGER_Q.occurs` is `4` and `LEDGER_Q.redefines` is
    None. Both halves of the redefinition are therefore readable from this
    class, each from the level that actually declares it.

    `Ledger-Q` has no MySQL column: `LEDGER-Q1` through `LEDGER-Q4` are the
    named columns for these same twenty-four bytes.

    SUBSCRIPT BASE. COBOL `OCCURS` is ONE-based, so COBOL's `Ledger-Q (1)` is
    `ledger_q[0]` here and `Ledger-Q (4)` is `ledger_q[3]`; the offset is one.
    No one-based wrapper, accessor or index-translating helper is provided -
    the callers own that conversion, and adding it here would be logic this
    layer must not hold (R-3).

    THERE IS DELIBERATELY NO BOUNDS CHECK ON THIS TABLE, AND NONE MAY BE
    ADDED. Anomaly register entry 2 is "A quarter-array subscript is computed
    by a `ROUNDED` divide and used without bounds checking, so an out-of-range
    period silently indexes past the array" - the divide at
    [general/gl080.cbl:L328] and the unchecked use at [general/gl080.cbl:L345].
    That unbounded subscript is reproduced in
    `acas_posting/programs/gl080_end_of_cycle.py`, which is where it belongs.
    A length or range check here would silently repair it, and R-4 is explicit
    that a defect fixed is a failure, not a success.

    Separate storage in Python: this tuple does not alias `LedgerQuarters`.
    See the module docstring.
    """

    REDEFINES: ClassVar[FieldDescriptor] = _QUARTERS_REDEFINES
    LEDGER_Q: ClassVar[FieldDescriptor] = _LEDGER_Q
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (_LEDGER_Q,)

    # 05  Ledger-Q      pic s9(8)v99   comp-3   occurs  4.             [:L36]
    # COMP-3, signed, 10 digits, scale 2, four occurrences. A tuple, not a
    # list, because the OCCURS count is fixed by the copybook and R-6 makes a
    # fixed collection immutable; its length comes from the descriptor's own
    # `occurs`, so no literal 4 is typed anywhere in this file.
    ledger_q: tuple[Decimal, ...] = _QUARTER_TABLE_ZERO


# =============================================================================
#  THE RECORD
# =============================================================================


@dataclass(slots=True)
class WsLedgerRecord:
    """`WS-Ledger-Record` - one General/Nominal Ledger account, 126 bytes.

    A field-for-field mirror of `01  WS-Ledger-Record.`
    [copybooks/wsledger.cob:L12], declared in copybook order from L13 through
    L37 so that this class can be set beside the copybook and diffed by eye.
    Reached through the GL-Nominal facade and handler `acas005`, carried by the
    `nominalMT` bridge, stored in `GLLEDGER-REC`.

    MUTABLE ON PURPOSE, and never `frozen=True`: `gl072` "Posts to the nominal
    ledger by accumulating into the ledger balance" (Agent Action Plan section
    0.4.1.2), so `ledger_balance` and the four quarters are rewritten on every
    posting. The accumulation itself is `gl072_transaction_update.py`'s work -
    this class holds no accumulator, no key builder, no scaler and no
    value checking of any kind (R-3).

    ELEVEN of its items have a MySQL column. TWELVE do not, and all twelve are
    declared anyway because R-3 requires the mirror be complete: the two
    storage-bearing FILLERs at L26 and L37, the key group and its three
    members, the two anonymous REDEFINES groups, the `Quarters` group, the
    `Ledger-Q` table view, and the `01` record item itself. Their
    column-lessness is recorded at each declaration rather than inferred.

    `FIELDS` below is the flattened descriptor list in copybook declaration
    order - all 22 items beneath the `01` level, groups and redefine views
    included. `RECORD` is the `01` item's own descriptor.
    `COLUMN_MAPPED_FIELDS` is the eleven that carry a column, in the same
    declaration order; the table's own column ordinal order is available from
    `loader.entries_for_table("GLLEDGER-REC")` and is not restated here.
    """

    # -- descriptors, one per declaration (R-5) ---------------------------
    RECORD: ClassVar[FieldDescriptor] = _WS_LEDGER_RECORD
    WS_LEDGER_KEY: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY
    WS_LEDGER_KEY9: ClassVar[FieldDescriptor] = _WS_LEDGER_KEY9
    LEDGER_TYPE: ClassVar[FieldDescriptor] = _LEDGER_TYPE
    LEDGER_PLACE: ClassVar[FieldDescriptor] = _LEDGER_PLACE
    LEDGER_LEVEL: ClassVar[FieldDescriptor] = _LEDGER_LEVEL
    FILLER_L26: ClassVar[FieldDescriptor] = _FILLER_L26
    LEDGER_NAME: ClassVar[FieldDescriptor] = _LEDGER_NAME
    LEDGER_BALANCE: ClassVar[FieldDescriptor] = _LEDGER_BALANCE
    LEDGER_LAST: ClassVar[FieldDescriptor] = _LEDGER_LAST
    QUARTERS: ClassVar[FieldDescriptor] = _QUARTERS
    FILLER_L37: ClassVar[FieldDescriptor] = _FILLER_L37

    # Every item beneath the 01 level, in copybook declaration order.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _WS_LEDGER_KEY,             # L13  group
        _WS_LEDGER_NOS,             # L14
        _WS_LEDGER_NOS_REDEFINES,   # L16  group, redefines WS-Ledger-Nos
        _LEDGER_N,                  # L17
        _LEDGER_S,                  # L18
        _LEDGER_PC,                 # L20
        _WS_LEDGER_KEY9,            # L21-L22  redefines WS-Ledger-Key
        _LEDGER_TYPE,               # L23
        _LEDGER_PLACE,              # L24
        _LEDGER_LEVEL,              # L25
        _FILLER_L26,                # L26  no column
        _LEDGER_NAME,               # L27  ANOMALY A-12
        _LEDGER_BALANCE,            # L28
        _LEDGER_LAST,               # L29
        _QUARTERS,                  # L30  group
        _LEDGER_Q1,                 # L31
        _LEDGER_Q2,                 # L32
        _LEDGER_Q3,                 # L33
        _LEDGER_Q4,                 # L34
        _QUARTERS_REDEFINES,        # L35  group, redefines Quarters
        _LEDGER_Q,                  # L36  occurs 4, no column
        _FILLER_L37,                # L37  no column
    )

    # The eleven that reach GLLEDGER-REC, in declaration order. Derived by
    # asking each descriptor whether it carries a table-qualified dictionary
    # key, so the count follows the artifact rather than a hand-kept list.
    COLUMN_MAPPED_FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = tuple(
        descriptor
        for descriptor in FIELDS
        if descriptor.dictionary_key is not None
        and descriptor.dictionary_key.startswith("GLLEDGER-REC.")
    )

    # -- the layout, in copybook declaration order L13 -> L37 -------------

    # 03  WS-Ledger-Key.                                              [:L13]
    # The eight-byte account key as a group. No column of its own; the column
    # is fed from the ws_ledger_key9 view below.
    ws_ledger_key: WsLedgerKey = field(default_factory=WsLedgerKey)

    # 03  WS-Ledger-Key9 redefines WS-Ledger-Key pic 9(8).       [:L21-L22]
    # THE FIELD BEHIND THE LEDGER-KEY COLUMN. Two physical lines, one
    # declaration; the bridge moves this view, not the group
    # [common/nominalMT.cbl:L962]. Separate storage from ws_ledger_key here -
    # the COBOL byte aliasing is not reproduced (see module docstring).
    ws_ledger_key9: WsLedgerKey9 = field(default_factory=WsLedgerKey9)

    # 03  Ledger-Type       pic 9.                                    [:L23]
    # DISPLAY, unsigned, 1 digit, scale 0.  ->  LEDGER-TYPE tinyint(1) unsigned
    ledger_type: int = 0

    # 03  Ledger-Place      pic x.                                    [:L24]
    # One character.  ->  LEDGER-PLACE char(1). Defaults to a single space, for
    # the reason given at ledger_name.
    ledger_place: str = " " * (_LEDGER_PLACE.character_length or 0)

    # 03  Ledger-Level      pic 9.                                    [:L25]
    # DISPLAY, unsigned, 1 digit, scale 0. -> LEDGER-LEVEL tinyint(1) unsigned
    ledger_level: int = 0

    # 03  filler            pic x(5).                                 [:L26]
    # FIVE BYTES WITH NO MYSQL COLUMN, declared because R-3 requires a
    # complete mirror. Keyed `WS-Ledger-Record.filler#26`; its descriptor
    # reports `is_filler` True. Named for its declaration line so the two
    # FILLERs can never be confused with one another.
    filler_l26: str = " " * (_FILLER_L26.character_length or 0)

    # 03  Ledger-Name       pic x(24).                                [:L27]
    #
    # ANOMALY A-12 - REPRODUCED HERE, NOT FIXED (R-4). The width disagrees
    # across all three layers, and this attribute holds the COPYBOOK width:
    #
    #     copybook  pic x(24)                  [copybooks/wsledger.cob:L27]
    #     host var  PIC X(32)                  [common/nominalMT.cbl:L299]
    #     column    char(32) NOT NULL          [mysql/ACASDB.sql:L127]
    #     moves/trims               [common/nominalMT.cbl:L965], [:L993],
    #                               [:L1067], [:L1246]
    #
    # TWENTY-FOUR CHARACTERS, NEVER THIRTY-TWO. `LEDGER_NAME.character_length`
    # is 24 and `LEDGER_NAME.anomaly_refs()` returns ('A-12',);
    # `LEDGER_NAME.drift()` hands back the three-layer disagreement
    # unadjudicated and this module settles none of it. The widening on write
    # is reproduced by `acas_posting/dal/acas005_gl_nominal.py`, which owns the
    # bridge boundary; the trailing-space difference the widening leaves in a
    # table dump is absorbed by the harness dump comparison step. Neither is
    # done here, and the width below is read from the descriptor so it cannot
    # be widened by an edit.
    ledger_name: str = " " * (_LEDGER_NAME.character_length or 0)

    # 03  Ledger-Balance    pic s9(8)v99   comp-3.                    [:L28]
    # COMP-3, SIGNED, 10 digits, scale 2.  ->  LEDGER-BALANCE decimal(10,2).
    # THE ACCUMULATOR THE WHOLE GENERAL LEDGER CYCLE POSTS INTO. gl072 adds
    # each posting into it. Decimal, exact, never binary floating point (R-2).
    ledger_balance: Decimal = _MONEY_ZERO

    # 03  Ledger-Last       pic s9(8)v99   comp-3.                    [:L29]
    # COMP-3, SIGNED, 10 digits, scale 2.  ->  LEDGER-LAST decimal(10,2)
    ledger_last: Decimal = _MONEY_ZERO

    # 03  Quarters.                                              [:L30-L34]
    # The four quarterly balances by name. The group itself has no column; its
    # four members are LEDGER-Q1 .. LEDGER-Q4.
    quarters: LedgerQuarters = field(default_factory=LedgerQuarters)

    # 03  filler redefines Quarters.                             [:L35-L36]
    # The same twenty-four bytes as an OCCURS 4 table. No column. Separate
    # storage from `quarters` here; no bounds check, by design - see
    # `LedgerQuartersTable` and anomaly register entry 2.
    quarters_table: LedgerQuartersTable = field(
        default_factory=LedgerQuartersTable
    )

    # 03  filler            pic x(50).                                [:L37]
    # FIFTY BYTES WITH NO MYSQL COLUMN - the largest single item in the record
    # and the one that brings the field sum to the 126 bytes the copybook
    # header claims at [copybooks/wsledger.cob:L10]. Keyed
    # `WS-Ledger-Record.filler#37`; its descriptor reports `is_filler` True.
    filler_l37: str = " " * (_FILLER_L37.character_length or 0)
