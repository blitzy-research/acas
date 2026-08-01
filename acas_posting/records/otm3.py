"""The Sales Open-Item record - OTM3 - as the frozen COBOL copybooks declare it.

The open-item record is the sales ledger's unpaid-item register. `sl060` writes
it and applies credit against it; `sl100` clears it and reads `OI-Date` against
`OI-Date-Cleared` to drive the payment-days average. Both dates are
`binary-long`, so that arithmetic is INTEGER arithmetic; the `oi_date` field
comment carries the locators and the reason (rule R-4).

Entity facade OTM3, handler `acas019`, bridge `otm3MT`, table `SAITM3-REC`.

THE THREE FROZEN SOURCES, AND WHY THERE ARE THREE
-------------------------------------------------
The transformation plan's entity-to-table spine names one record copybook for
OTM3, `copybooks/slwsoi3.cob`. That file declares only a raw buffer plus a
four-item view naming its first nineteen bytes; the twenty-eight field body
lives in a second copybook, `copybooks/slwsoi.cob`, reached by a two-line COPY
at [copybooks/slwsoi3.cob:L18-L19].

The bridge does not read `slwsoi3.cob` at all - the string occurs zero times in
it. It copies the body copybook directly [common/otm3MT.cbl:L345], one of seven
COPY statements written in TWO DIFFERENT CASES: five lower-case `copy` at
[:L169], [:L211], [:L336], [:L340] and [:L345], and two upper-case `COPY` at
[:L296] and [:L1306] - `mysql-variables.cpy` and `mysql-procedures.cpy`, the two
the preSQL translator inserts. A lower-case-only search finds five of the seven,
so the case split must be allowed for, not assumed away.

Both copybooks are sources of this module and both are cited field by field
below; the divergence between the plan's naming and the bridge's own COPY is
recorded rather than settled - question 7 below.

    copybooks/slwsoi3.cob   20 lines   the buffer and the short view
    copybooks/slwsoi.cob    57 lines   the twenty-eight field body
    common/otm3MT.cbl     2192 lines   the bridge: record <-> table mapping
    mysql/ACASDB.sql                   the frozen schema, table at L896

All four are specification only: never modified, reformatted, relocated,
commented or executed. This module reads no file, spawns no process and loads no
shared library (rule R-1). `WsOtm3Record` records the one identifier that names
two incompatible things across those sources.

THE LAYOUT
----------
Set this module beside `cat -n` on either copybook and the two diff line for
line. Field order within every class is copybook DECLARATION order, never
column-ordinal order and never alphabetical (rule R-6).

`copybooks/slwsoi3.cob`::

    L9   WsOtm3Record        01  WS-OTM3-Record   pic x(118)   elementary
    L11  OpenItemRecord3     01  Open-Item-Record-3  redefines WS-OTM3-Record
    L12    Oi3Key            03  OI3-Key                       group
    L13      oi3_customer    05  OI3-Customer     pic x(7)     str
    L14      oi3_invoice     05  OI3-Invoice      PIC 9(8)     int
    L15    oi3_date          03  OI3-Date         binary-long  int
    L16    filler_1          03  filler           pic x(99)    str  FILLER

`copybooks/slwsoi.cob`::

    L8   OiHeader            01  OI-Header
    L9     OiKey             02  OI-key                        group
    L10      OiCustomer      03  OI-Customer                   group
    L11        oi_nos        05  OI-Nos           pic x(6)     str
    L12        oi_check      05  OI-Check         pic 9        int
    L13      oi_invoice      03  OI-Invoice       pic 9(8)     int
    L14    Filler1           02  filler                 group  FILLER
    L15      oi_date         03  OI-Date          binary-long  int
    L16      OiBatch         03  OI-Batch          comp  group
    L17        oi_b_nos      05  OI-B-Nos         pic 9(5)     int
    L18        oi_b_item     05  OI-B-Item        pic 999      int
    L19      oi_type         03  OI-Type          pic 9        int
    L32      oi_description  03  OI-Description   pic x(25)    str
    L33      oi_hold_flag    03  OI-Hold-flag     pic x        str
    L34      oi_unapl        03  OI-Unapl         pic x        str
    L35      Filler2         03  filler       comp-3   group  FILLER
    L36        oi_p_c        05  OI-P-C           pic s9(7)v99 Decimal
    L37        oi_net        05  OI-Net           pic s9(7)v99 Decimal
    L38        oi_approp     05  OI-Approp  redefines OI-Net   Decimal
    L40        oi_extra      05  OI-Extra         pic s9(7)v99 Decimal
    L41        oi_carriage   05  OI-Carriage      pic s9(7)v99 Decimal
    L42        oi_vat        05  OI-Vat           pic s9(7)v99 Decimal
    L43        oi_discount   05  OI-Discount      pic s9(7)v99 Decimal
    L44        oi_e_vat      05  OI-E-Vat         pic s9(7)v99 Decimal
    L45        oi_c_vat      05  OI-C-Vat         pic s9(7)v99 Decimal
    L46        oi_paid       05  OI-Paid          pic s9(7)v99 Decimal
    L47      oi_status       03  OI-Status        pic 9        int
    L50      oi_deduct_days  03  OI-Deduct-Days   binary-Char  int
    L51      oi_deduct_amt   03  OI-Deduct-Amt    pic s999v99 comp  Decimal
    L52      oi_deduct_vat   03  OI-Deduct-Vat    pic s999v99 comp  Decimal
    L53      oi_days         03  OI-Days          binary-Char  int
    L54      oi_cr           03  OI-Cr            binary-long  int
    L55      oi_applied      03  OI-Applied       pic x        str
    L56      oi_date_cleared 03  OI-Date-Cleared  binary-long  int

TYPE DISCIPLINE (rule R-2)
--------------------------
No accounting value passes through a binary floating-point type at any point,
in computation, in storage or in transport. There is no such type anywhere in
this module.

    pic x(n), pic x                          -> str
    pic 9(n) / pic 999 / pic 9   scale 0     -> int
    pic 9(5) / pic 999 under an inherited
        comp group                  scale 0  -> int
    binary-Char / binary-long       scale 0  -> int, SIGNED
    pic s9(7)v99 under an inherited
        comp-3 group                scale 2  -> Decimal
    pic s999v99 comp                scale 2  -> Decimal
    group items                              -> nested dataclass
    01 WS-OTM3-Record pic x(118)             -> str, elementary

THE TWO-DIRECTION RULE. Scale zero gives `int`, scale above zero gives
`Decimal`, whatever the usage - so the binary family gives `int` while
`pic s999v99 comp` and the packed money block give `Decimal`. "COMP means int"
is false in both directions, and getting it wrong corrupts every stored value.
Twelve of the thirty-nine declared fields carry `Decimal`, each at scale two.

GROUP-USAGE INHERITANCE - TWELVE FIELDS, TWO GROUP HEADERS
----------------------------------------------------------
Two group headers carry a usage clause that their children inherit. One is
named and one is an unnamed FILLER, and both sit inside the unnamed level-02
filler at [copybooks/slwsoi.cob:L14]::

    [copybooks/slwsoi.cob:L16]  03  OI-Batch     comp.     2 children
    [copybooks/slwsoi.cob:L35]  03  filler       comp-3.  10 children

Twelve items therefore carry NO usage clause of their own, and reading usage
from the picture line alone would class all twelve as zoned display. Eleven
reach a column; `OI-Approp` does not. `OiBatch` and `Filler2` record the
provenance for their own children, and the `oi_deduct_amt` comment records the
opposite case - a field that writes `comp` on its own picture line.

THIS TABLE IS THE PROOF THAT SIGNEDNESS DRIFT IS PER-BRIDGE, NOT PER-TYPE
-------------------------------------------------------------------------
The migration plan states, of drift at the bridge boundary, that "the drift is
specific rather than systemic and must be handled field by field from the
dictionary". `SAITM3-REC` is the sharpest available evidence, because the same
COBOL declaration goes both ways WITHIN THIS ONE TABLE.

Signed at all three layers - copybook, bridge host variable and column::

    OI-Cr          binary-long    S9(10) COMP        int(8)
    OI-Deduct-Amt  s999v99 comp   S9(03)V9(02) COMP  decimal(5,2)
    OI-Deduct-Vat  s999v99 comp   S9(03)V9(02) COMP  decimal(5,2)

Sign lost AT THE BRIDGE, before any SQL runs::

    OI-Date          binary-long   9(10) COMP   int(8) unsigned
    OI-Deduct-Days   binary-Char   9(03) COMP   tinyint(3) unsigned
    OI-Days          binary-Char   9(03) COMP   tinyint(3) unsigned
    OI-Date-Cleared  binary-long   9(10) COMP   int(8) unsigned

`OI-Cr` keeps its sign while `OI-Date` and `OI-Date-Cleared`, declared
identically as `binary-long`, lose theirs - same record, same bridge program,
same table. Both invoice bridges then go the other way again for that same type:
`sih-cr binary-long` [copybooks/slwsinv.cob:L66] becomes unsigned `9(10) COMP`
[common/slinvoiceMT.cbl:L418] and an unsigned column. No rule of the form
"binary-long always loses its sign" exists, and none may be written: the drift
is PER FIELD, NEVER PER TYPE, and every field's treatment is read from its own
dictionary entry. The four narrowed fields are the ones the dictionary tags
`A-11` and `Q-3`; all seven above report `signed` true, every descriptor
reporting the COPYBOOK view.

THE OTHER SEVEN DRIFTS AT THIS BRIDGE
-------------------------------------
Seven further kinds, each field's own comment carrying its locators. Only the
first and the sixth are not documented in full at their point of reproduction.

1. SYSTEMATIC PREFIX RENAME. Every column is prefixed `OI3-` while the copybook
   names its fields `OI-`, so twenty-seven of the twenty-eight entries carry a
   name disagreement for that alone - all but `OI3-Key`, the one entry with no
   drift of any kind. Hence the key convention below: upper casing `OI-Net`
   yields `OI-NET`, which does not exist.

2. NAME TRUNCATION, once only - `OI-Date` to `OI3-DAT`, the trailing E dropped,
   while `OI-Date-Cleared` keeps its full name. A fact, not a rule.

3. TRIPLE MATERIALISATION of `OI-Batch` [common/otm3MT.cbl:L306-L308]: the group
   AND both children each get a host variable and a column, all three CHARACTER.

4. NUMERIC TO CHARACTER, four sites - `OI-Type` and `OI-Status`, both `pic 9`,
   into `char(1)`; `OI-B-Nos` and `OI-B-Item` into `char(5)` and `char(3)`.

5. WIDTH DRIFT, once only - `OI-Description pic x(25)` into `char(32)`. The value
   is not corrupted but the PADDING differs, which is why the oracle harness
   reduces fixed-character trailing spaces to a single agreed form.

6. STORAGE CLASS AND DIGIT WIDENING. `OI-Invoice pic 9(8)`, zoned display
   [copybooks/slwsoi.cob:L13], becomes binary ten-digit `9(10) COMP`
   [common/otm3MT.cbl:L304] then `int(8) unsigned`; the descriptor reports
   DISPLAY and eight. Storage class drifts for nineteen of the twenty-eight
   columns, digit width for this one alone.

7. GROUP CONCATENATION WITH THE CHILDREN ALSO MATERIALISED, twice - `OI3-Key`
   into the primary key `OI3-KEY char(15)` [mysql/ACASDB.sql:L925] and
   `OI-Customer` into `OI3-CUSTOMER char(7)`, their constituents drawing columns
   from the body copybook or none at all.

A COMMENT IN THE BRIDGE DESCRIBING A SITUATION THAT DOES NOT EXIST
------------------------------------------------------------------
Immediately above the COPY, the bridge says [common/otm3MT.cbl:L342-L343]::

    *>  Using the first record but not the 2nd as it uses occurs 40 but
    *>   to reduce Ram usage get rid of the occurs, hopefully.

`occurs` occurs zero times in `copybooks/slwsoi.cob`, the bridge's replacing
clause strips no occurs, and there is no second record. The identical two
lines, down to the trailing ", hopefully.", also stand in
[common/plinvoiceMT.cbl:L452-L453] and [common/otm5MT.cbl:L345-L346], so the
text is shared residue across three bridges and which one it started in is not
determinable from the frozen source. Quoted, recorded, changed nowhere.

There is consequently no OCCURS anywhere in this module, and none is added.

THE `OI-Type` DOMAIN, AS THE COPYBOOK DOCUMENTS IT
--------------------------------------------------
Reproduced verbatim from [copybooks/slwsoi.cob:L21-L30]::

    *>                              ***********************************
    *>                              *  1  =  Receipt                  *
    *>                              *  2  =  Account                  *
    *>                              *  3  =  Cr. Note                 *
    *>                              *  4  =  Proforma (Not used)      *
    *>                              *  5  =  Payment                  *
    *>                              *  6  =  Journal-Unapplied Cash   *
    *>                              *  7  =  Journal Type B (Not Used)*
    *>                              *  9  =  Old Payments             *
    *>                              ***********************************

The `oi_type` field comment records what follows from it: 8 is absent, the two
"Not used" entries differ in capitalisation, the block is DOCUMENTATION, and no
enumeration, lookup, predicate or check is built from it here (rule R-3).

CONDITION NAMES ARE DATA, NOT BEHAVIOUR
---------------------------------------
Exactly two 88-level names exist in this record, both on `OI-Status`
[copybooks/slwsoi.cob:L48-L49]::

    88  S-Open                         value zero.
    88  S-Closed                       value 1.      *> Paid

`condition_names_for` returns them as declared - the figurative constant
`zero` stays `"zero"` - and records the two fields that declare none.

BYTE ARITHMETIC - REPORTED, NOT SETTLED
---------------------------------------
Three size annotations exist: `*> Rec Size 118 Bytes`
[copybooks/slwsoi3.cob:L4], its change note "changed size to 118 (from 114)
after changing Inv from Bin to 9(8)" [:L6-L7], and `*> record size 118 bytes
08/02/17 inv bin -> 9(8)` [copybooks/slwsoi.cob:L6]. Summing the body
copybook's fields from the dictionary's own byte widths, in declaration order,
`OI-Approp` contributing nothing as a redefine, packed and binary usages at
their storage widths::

    OI-Nos 6, OI-Check 1, OI-Invoice 8, OI-Date 4                 -> 19
    OI-B-Nos 4, OI-B-Item 2, OI-Type 1                            -> 26
    OI-Description 25, OI-Hold-flag 1, OI-Unapl 1                 -> 53
    nine money fields at 5 each, [OI-Approp +0]                   -> 98
    OI-Status 1, OI-Deduct-Days 1                                 -> 100
    OI-Deduct-Amt 4, OI-Deduct-Vat 4, OI-Days 1                   -> 109
    OI-Cr 4, OI-Applied 1, OI-Date-Cleared 4                      -> 118

    field sum 118   declared 118   difference 0

`OpenItemRecord3` reports the short view's independent agreement from the inline
offset markers the copybook itself carries.

Closing cleanly is not universal in this folder, and the contrasts are what make
the disagreements specific rather than a systemic habit: the purchase open-item
record closes at 113 and the analysis record at 36, while the batch record
contradicts itself at 96 against 98 and the IRS system record at 256 against
257. No record-length constant is declared here even so, and the figures above
do not close question 5 of the oracle list: the compiled program is the
tie-breaker for byte layout (rule R-6).

NEARLY EVERY FIELD NAME IN THIS RECORD COLLIDES WITH THE PURCHASE COPYBOOK
--------------------------------------------------------------------------
The general ledger posting path is already forced to write qualified references
because three posting copybooks declare colliding names
[general/gl070.cbl:L497], [:L521], [:L525]. This record's collision is at the
RECORD level, not merely the field level: `copybooks/plwsoi.cob` also declares
`01 OI-Header`, so asking the dictionary for that record name returns 69
entries - 34 from `copybooks/slwsoi.cob` and 35 from `copybooks/plwsoi.cob`.

Every declared name in the sales copybook appears in the purchase one EXCEPT
`OI-Description`, which is sales-only. Four of the shared names match only
case-insensitively and are therefore distinct identifiers::

    sales  OI-key        purchase  OI-Key
    sales  OI-Unapl      purchase  OI-unapl
    sales  OI-Cr         purchase  OI-CR
    sales  OI-Hold-flag  purchase  OI-hold-flag

Going the other way, `OI-ref`, `OI-order`, `OI-Supplier` and the condition name
`payment-held` are purchase-only. Any COBOL program copying both copybooks would
collide on everything else. The Python module namespace makes that harmless for
free, and the dictionary disambiguates its copybook-only keys with a line-number
suffix - the sales `OI-Nos` is keyed `OI-Header.OI-Nos#11`. Recorded here so the
migration's traceability document can explain it rather than have a reader
discover it.

WHY THIS MODULE SHARES NOTHING WITH `otm5.py`
---------------------------------------------
`records/otm5.py` is the purchase open-item module and its body copybook
`copybooks/plwsoi.cob` is near-identical to this one's: the same `OI-` names, the
same money block under the same unnamed packed FILLER group, the same two
condition names on the status field, the same two-physical-line `OI-Approp
redefines OI-Net`. There is no import in either direction, no subclass, no shared
base or mixin factored into a third place, and no copy-and-rename. Nine
divergences were counted in the frozen source and every one has to survive
independently:

    sales `OI-Description pic x(25)`     purchase has no such field
    purchase `OI-ref x(10)`, `OI-order x(10)`   sales has neither
    purchase nests its key FOUR deep with an extra `OI-Supplier` level
        [copybooks/plwsoi.cob:L13-L15]; sales nests THREE
    purchase declares a condition name on its hold flag
        [copybooks/plwsoi.cob:L39]; sales declares none
    purchase spells it `OI-CR` [copybooks/plwsoi.cob:L60];
        sales spells it `OI-Cr` [copybooks/slwsoi.cob:L54]
    purchase writes `binary-char`; sales writes `binary-Char`
    purchase has ONE unnamed FILLER group; sales has TWO
    purchase capitalises `Pic`, `Comp`, `Binary-long`; sales does not
    118 bytes against 113 [copybooks/plwsoi.cob:L8-L9]

Divergence preservation is the point of the exercise. If the two modules end up
textually similar that is a RESULT, never a MECHANISM.

LAYERING - THIS IS A LEAF MODULE
--------------------------------
The per-directory import contract grants `records/*.py` exactly two imports and
forbids everything else, "this keeps the record layer a leaf". Permitted:
`acas_posting.cobol.field` for the descriptor type and
`acas_posting.dictionary.loader` for the lookup, plus the standard library.
There is no exception to that, and none is needed: the two object-model types
this module names in return annotations, `ConditionName` and `Drift`, come
through `dictionary.loader`, which re-exports them as bindings to the single
definition rather than copies.

Forbidden, and absent: `acas_posting.dictionary.model` reached directly rather
than through the loader, every `dal` module, `programs`, `cli`, `clock`, `dates`,
`workfiles`, `cobol.arithmetic`, `cobol.move`, `cobol.picture`, `cobol.usage`,
`cobol.condition_names`, `cobol.sortverb`, `dictionary.generate`, the compiled
comparison oracle in its sibling tree, and ANY other module of this package -
`otm5` and `sales_invoice` included. The reason is concrete: the arithmetic
test tier "imports only `cobol` and `records` and touches no database, so it
runs anywhere", and one import reaching into `dal` would drag a database driver
into that tier.

DESCRIPTOR LOOKUP (rule R-5)
----------------------------
No picture clause, digit count, scale, sign position or storage class is written
by hand here. Every attribute declares three strings as field metadata - the
verbatim COBOL name, its dictionary key and its copybook locator - and the
storage metadata comes from the generated dictionary on demand: derived, not
transcribed. All forty-one fields and groups in the two copybooks have an entry,
so `FieldDescriptor.from_dictionary_key` covers every one and no field's
metadata is stated here by hand.

Keys take one of two forms and never a bare field name::

    <TABLE-NAME>.<COLUMN-NAME>       for the twenty-eight column-mapped fields
    <COPYBOOK-RECORD>.<FIELD-NAME>   for the thirteen copybook-only ones

The left side of a column-mapped key is the MySQL table name, `SAITM3-REC`, not
the copybook 01-name; the right side is the COLUMN name, which drift 1 shows is
prefixed `OI3-` and drift 2 shows is sometimes truncated. Every key was obtained
by asking the loader for the table's and the copybooks' entries and matching
each entry's copybook name to its attribute - never by upper casing a field
name. `cite` returns the three-locator provenance string::

    SAITM3-REC.OI3-CR  copybook=copybooks/slwsoi.cob:L54
                       bridge=common/otm3MT.cbl:L327
                       column=mysql/ACASDB.sql:L922

DETERMINISM (rule R-6)
----------------------
Field order is copybook declaration order. Fixed collections are tuples, never
lists. There is no import-time input or output: the dictionary is read on the
first descriptor request and not before. Nothing here consults a clock, draws
an unpredictable value, inspects the process environment or walks a directory,
and execution is strictly sequential with no concurrency introduced. Two
imports in two processes produce identical state. `OiHeader` records why no
field carries a default value.

QUESTIONS ONLY THE COMPILED PROGRAM CAN SETTLE
----------------------------------------------
Each is recorded in the migration's ambiguity-resolutions document, not decided
here.

1. What is actually stored in `OI3-BATCH`, `OI3-BATCH-NOS` and `OI3-BATCH-ITEM`?
   Two numeric children under an inherited `comp` become three character
   columns, the group materialised as well as its children.
2. What is stored in `OI3-STATUS` and `OI3-TYPE`? Both are `pic 9` in the
   copybook and `char(1)` in the schema, and `OI-Status` carries a condition name
   whose value is the figurative constant `zero`. Does a zero arrive as the
   character "0" or as a space?
3. When `OI-Approp` has been written, as a redefine of `OI-Net`, what appears in
   `OI3-NET`? The two share storage, so the last write wins - but which programs
   write which name, and in what order, has to be measured.
4. What value is stored when a NEGATIVE `binary-Char` or `binary-long` passes
   through an unsigned host variable into an unsigned column? Four sites, each
   already tagged with an anomaly and an open-question reference.
5. Does the field sum govern the record actually read, or the declared length?
   Both are 118 here, but the byte layout is the compiled program's to decide.
6. `OI-Description` is 25 characters in the copybook and 32 in the column. What
   occupies bytes 26 to 32 on a read-back?
7. The plan's spine names `copybooks/slwsoi3.cob` as this record's copybook while
   the bridge copies `copybooks/slwsoi.cob`. Which layout governs the bytes on
   disk?

ANOMALIES THIS MODULE REPRODUCES AND MUST NEVER FIX (rule R-4)
--------------------------------------------------------------
A defect present in the compiled behaviour is part of the specification: a
defect reproduced is correct, a defect fixed is a failure. Each site below
carries a comment citing its COBOL locator at the point of reproduction, and
the register of every such site is the migration's anomaly log.

     1  `WS-OTM3-Record` names two incompatible things
     2  a bridge comment about an `occurs 40` that does not exist
     3  `OI-Approp` present in the copybook, absent from the bridge
     4  triple materialisation of `OI-Batch`, character on all three
     5  signedness drift per bridge, not per type
     6  four signedness narrowings, surfaced unsettled
     7  four numeric-to-character drifts
     8  `OI-Date` truncated to `OI3-DAT`, `OI-Date-Cleared` not truncated
     9  the systematic `OI-` to `OI3-` prefix rename across all 28 columns
    10  `OI-Description` widened from 25 to 32
    11  two group headers, one of them an unnamed FILLER, carrying the usage
        clause that twelve fields depend on
    12  `binary-Char` with a capital C beside all-lower-case `binary-long`
    13  upper-case `PIC` amid lower-case `pic`
    14  declaration beats comment, twice, the comments differing in case
    15  the `OI-Type` domain block with 8 absent and capitalisation adrift
    16  `OI-Hold-flag` declaring no condition name where purchase declares one
    17  the figurative constant `zero` beside the literal `1`
    18  dual materialisation of `OI3-Key` - the group and both children
    19  two different `replacing` forms for the same COPY, and two different
        cases of the COPY verb itself

There is deliberately no settled, single-answer or one-winner type, view, value
or picture anywhere in this module, and none may be introduced. Where the
copybook, the bridge host variable and the column disagree, all three views are
carried and all three are cited.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Final, Mapping

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# `ConditionName` and `Drift` are imported for the two return annotations below
# and for nothing else. The per-directory import contract grants this package
# `cobol.field` and `dictionary.loader`, and both types arrive through the
# loader, which re-exports them for exactly this purpose - see its
# `RE_EXPORTED_MODEL_NAMES`. Each re-export is a BINDING to the one definition in
# `acas_posting.dictionary.model`, not a copy of it, so this annotation names the
# same class the loader's own accessors return while the record layer stays the
# leaf the contract requires. No enum or record type is ever redefined here to
# avoid the import - a competing copy of a dictionary type would be a second
# source of truth for field metadata, which is exactly what rule R-5 exists to
# prevent.
from acas_posting.dictionary.loader import ConditionName, Drift

__all__: Final[tuple[str, ...]] = (
    # The record layouts, in code-point order. Two groups of them: the buffer
    # and its short view from copybooks/slwsoi3.cob, and the body from
    # copybooks/slwsoi.cob.
    "Filler1",
    "Filler2",
    "Oi3Key",
    "OiBatch",
    "OiCustomer",
    "OiHeader",
    "OiKey",
    "OpenItemRecord3",
    "WsOtm3Record",
    # The traceability accessors, likewise in code-point order.
    "cite",
    "cobol_name_for",
    "condition_names_for",
    "copybook_source_for",
    "descriptor_for",
    "dictionary_key_for",
    "drift_for",
)


#  FIELD METADATA - THREE STRINGS PER ATTRIBUTE, NOTHING MORE
# Each attribute below declares the verbatim COBOL name, the dictionary key and
# the copybook locator. All three are plain string literals, so building a class
# performs no input or output of any kind and the dictionary stays unread until
# a caller asks for a descriptor (rule R-6).
# Nothing about STORAGE is written here - no picture, no digit count, no scale,
# no sign position, no usage. Those come from the generated dictionary, which is
# built from the maintainer's one-way COBOL-to-MySQL bridge, because field
# metadata has to be derived rather than transcribed (rule R-5).

_COBOL_NAME: Final[str] = "cobol_name"
_DICTIONARY_KEY: Final[str] = "dictionary_key"
_COPYBOOK_SOURCE: Final[str] = "copybook_source"


def _cobol(name: str, key: str, source: str) -> Mapping[str, str]:
    """Bind one attribute to its COBOL declaration and its dictionary entry.

    Args:
        name: The COBOL data-name VERBATIM, case and hyphens intact -
            `"OI-Hold-flag"`, `"OI-B-Nos"`, `"OI3-Invoice"`, `"filler"`. Never
            rewritten and never snake-cased; the snake-cased form is the Python
            attribute name, which is a separate thing.
        key: The dictionary entry key - `<TABLE-NAME>.<COLUMN-NAME>` for a
            column-mapped field, `<COPYBOOK-RECORD>.<FIELD-NAME>` for a
            copybook-only one. Obtained from the loader, never assembled by
            upper casing `name`: the bridge re-prefixes this whole record from
            `OI-` to `OI3-`, so upper casing `OI-Net` yields `OI-NET`, which no
            entry is keyed by.
        source: The `<path>:L<n>` locator of the declaration, so a reader has
            the citation at the declaration site without a dictionary read.

    Returns:
        The metadata mapping for `dataclasses.field`.
    """
    return {_COBOL_NAME: name, _DICTIONARY_KEY: key, _COPYBOOK_SOURCE: source}


def _metadata_for(record: Any, attribute: str) -> Mapping[str, Any]:
    """Return one attribute's metadata mapping from a record class or instance.

    Args:
        record: Any dataclass this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        That attribute's metadata mapping.

    Raises:
        AttributeError: The record declares no such attribute. This fires on a
            PROGRAMMER error - a mistyped attribute name - and cannot fire on a
            data value, so it adds no validation to the migrated behaviour
            (rule R-3).
    """
    for member in dataclasses.fields(record):
        if member.name == attribute:
            return member.metadata
    declared = ", ".join(member.name for member in dataclasses.fields(record))
    raise AttributeError(
        "%s declares no attribute %r. Its attributes, in copybook declaration "
        "order, are: %s" % (_record_name(record), attribute, declared)
    )


def _record_name(record: Any) -> str:
    """Return a record class's or instance's class name, for a message."""
    return record.__name__ if isinstance(record, type) else type(record).__name__


#  THE TRACEABILITY ACCESSORS  (rule R-5)
# Module-level FUNCTIONS taking a record and an attribute name - deliberately
# not properties or attributes on the records themselves, so that none of them
# can be mistaken for a stored field of the COBOL layout (rule R-3). Every one
# reads the metadata declared above and, where it needs storage facts, delegates
# to the dictionary loader. None reimplements a loader primitive.


def descriptor_for(record: Any, attribute: str) -> FieldDescriptor:
    """Return the storage description the dictionary holds for one attribute.

    The descriptor reports the COPYBOOK view of the field - its own digits,
    scale, signedness and usage - and never a blend of the copybook, bridge and
    column views. It does not widen a field to its column width, does not
    retype a numeric field as character to match a character column, and does
    not apply the sign loss the bridge performs. Reproducing the bridge's
    conversions belongs to the `acas019` handler module; ask `drift_for`
    for the disagreement itself, unsettled.

    Lazy and memoised: the dictionary is read on the first call in a process and
    the descriptor cache is keyed on the entry key, so a repeated call returns
    the same frozen object (rule R-6).

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name, for example `"oi_net"`.

    Returns:
        The field's descriptor.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so. Allowed to propagate
            untouched because its own message lists near misses and restates the
            key convention.
    """
    return FieldDescriptor.from_dictionary_key(dictionary_key_for(record, attribute))


def dictionary_key_for(record: Any, attribute: str) -> str:
    """Return one attribute's dictionary entry key.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The entry key - `"SAITM3-REC.OI3-NET"` for a column-mapped field,
        `"OI-Header.OI-Approp#38"` for a copybook-only one.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    return str(_metadata_for(record, attribute)[_DICTIONARY_KEY])


def cobol_name_for(record: Any, attribute: str) -> str:
    """Return one attribute's COBOL data-name, verbatim.

    Case and hyphens are exactly as the frozen copybook writes them, which is
    why `"OI-Hold-flag"` keeps its lower-case f, `"OI-key"` its lower-case k and
    `"OI-Cr"` its lower-case r - the purchase copybook spells that last one
    `OI-CR`, and the two are different records (rule R-4).

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The COBOL data-name.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    return str(_metadata_for(record, attribute)[_COBOL_NAME])


def copybook_source_for(record: Any, attribute: str) -> str:
    """Return the `<path>:L<n>` locator of one attribute's COBOL declaration.

    Answered from the metadata declared at the attribute, so this needs no
    dictionary read at all. It agrees with the `source_locator` the dictionary
    records for the same field.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The locator, for example `"copybooks/slwsoi.cob:L37"`.

    Raises:
        AttributeError: The record declares no such attribute.
    """
    return str(_metadata_for(record, attribute)[_COPYBOOK_SOURCE])


def cite(record: Any, attribute: str) -> str:
    """Return the three-locator provenance string for one attribute.

    Delegates to the loader's own primitive, which is the traceability
    mechanism for this migration; nothing about it is reimplemented here. The
    string names the copybook field, the bridge host variable and the MySQL
    column, and reads `absent` for a view a field does not have - as
    `OI-Approp` does not have a bridge or a column.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The provenance string.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so.
    """
    return loader.cite(dictionary_key_for(record, attribute))


def drift_for(record: Any, attribute: str) -> Drift:
    """Return the UNSETTLED disagreement between one field's three views.

    The copybook, the bridge host variable and the MySQL column disagree for
    most fields of this record - on name for twenty-seven of the twenty-eight
    columns, on storage class for nineteen, on signedness for four, on digit
    width for one and on character length for one. The loader records every such
    disagreement side by side and picks no winner, which is the requirement:
    reproducing a discrepancy is the job and choosing an answer is the failure
    (rule R-4).

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The drift object, with its per-aspect flags and its detail sentences.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so.
    """
    return loader.drift_for(dictionary_key_for(record, attribute))


def condition_names_for(record: Any, attribute: str) -> tuple[ConditionName, ...]:
    """Return the 88-level condition names declared on one attribute, as DATA.

    A tuple, never a list, and empty for every attribute of this record except
    `OiHeader`'s `oi_status`, which carries the two the copybook declares at
    [copybooks/slwsoi.cob:L48-L49]. Each carries its name, its value-clause text
    and its locator. The value is always TEXT in the declared spelling, so
    `S-Open` reports `"zero"` - the figurative constant, not `"0"` - beside
    `S-Closed`'s literal `"1"`.

    These are the DECLARED names and values. Turning one into a predicate over
    a record is `acas_posting/cobol/condition_names.py`'s work, and importing
    that module from this leaf layer is forbidden.

    Args:
        record: Any record class this module declares, or an instance of one.
        attribute: The Python attribute name.

    Returns:
        The condition names in declaration order, empty if the field declares
        none. `oi_type` and `oi_hold_flag` both return an empty tuple, and both
        emptinesses are facts about the frozen source rather than omissions
        here.

    Raises:
        AttributeError: The record declares no such attribute.
        loader.DictionaryKeyError: No entry is keyed so.
    """
    copybook_field = loader.copybook_field_for(dictionary_key_for(record, attribute))
    if copybook_field is None:
        return ()
    return tuple(copybook_field.condition_names)


#  SECTION A - copybooks/slwsoi3.cob, THE BUFFER AND ITS SHORT VIEW
# Twenty lines. Its header reads, verbatim:
#     *>      Rec Size 118 Bytes
#     *> 08/02/17 VBC changed size to 118 (from 114) after
#     *>          changing Inv from Bin to 9(8)
# `VBC` is the maintainer's own initials, quoted as written.


@dataclass
class WsOtm3Record:
    """The raw 118-byte buffer `WS-OTM3-Record`, declared elementary.

    `01  WS-OTM3-Record         pic x(118).` [copybooks/slwsoi3.cob:L9]

    AN ELEMENTARY ALPHANUMERIC ITEM, NOT A GROUP - a raw 118-byte buffer that
    the two views below redefine. Its descriptor reports `is_group` false,
    `character_length` 118 and a string carrier, which is what the copybook
    declares.

    R-4: THE SAME IDENTIFIER NAMES SOMETHING ELSE ENTIRELY IN THE BRIDGE.
    [copybooks/slwsoi3.cob:L18-L19] copies the body copybook while KEEPING the
    copied name and ADDING a redefines clause, so `WS-OTM3-Record` there is this
    buffer. [common/otm3MT.cbl:L345-L346] copies the same body copybook while
    RENAMING outright with no redefines, so `WS-OTM3-Record` there is the whole
    twenty-eight field group. One identifier, two incompatible meanings, in two
    files that both feed this module. This class is the copybook's meaning. The
    bridge's meaning is documented and nowhere implemented, and the two are not
    unified.
    """

    ws_otm3_record: str = field(
        metadata=_cobol(
            "WS-OTM3-Record",
            "WS-OTM3-Record.WS-OTM3-Record",
            "copybooks/slwsoi3.cob:L9",
        )
    )


@dataclass
class Oi3Key:
    """The fifteen-byte key group `OI3-Key`, customer plus invoice number.

    `03  OI3-Key.` [copybooks/slwsoi3.cob:L12]

    The primary key of `SAITM3-REC`, and the one group in either copybook that
    the bridge stores as a column in its own right: an alphanumeric
    concatenation of its two children, seven plus eight giving `char(15)`,
    filled by a group move the bridge performs at [common/otm3MT.cbl:L1351]'s
    neighbour, [common/otm3MT.cbl:L1345].

    R-4: DUAL MATERIALISATION. Both children are ALSO stored, as `OI3-CUSTOMER`
    and `OI3-INVOICE` - but from the BODY copybook's `OI-Customer` and
    `OI-Invoice`, not from these two. So `OI3-Customer` and `OI3-Invoice` here
    have no column of their own and are copybook-only entries, while the group
    above them is column-mapped. The dictionary also notes of `HV-OI3-KEY` that
    it "is never moved back into the record after a read", so a value read from
    the database does not reach a caller through that host variable.
    """

    # R-4: `PIC` in UPPER CASE at L14 where every other picture in this file is
    # lower-case `pic`, and `*> Was binary-long.` with a capital W where the
    # body copybook writes `*> was binary-long.` with a lower-case w
    # [copybooks/slwsoi.cob:L13]. DECLARATION BEATS COMMENT: the field is
    # `PIC 9(8)`, zoned display at scale zero, so its carrier is `int`. The
    # comment records history and does not change the type.
    oi3_customer: str = field(
        metadata=_cobol(
            "OI3-Customer",
            "Open-Item-Record-3.OI3-Customer",
            "copybooks/slwsoi3.cob:L13",
        )
    )
    oi3_invoice: int = field(
        metadata=_cobol(
            "OI3-Invoice",
            "Open-Item-Record-3.OI3-Invoice",
            "copybooks/slwsoi3.cob:L14",
        )
    )


@dataclass
class OpenItemRecord3:
    """The `Open-Item-Record-3` view redefining the 118-byte buffer.

    `01  Open-Item-Record-3  redefines WS-OTM3-Record.` [copybooks/slwsoi3.cob:L11]

    A SHORT VIEW over the 118-byte buffer: the key, the date and a 99-byte
    filler, which is all this copybook declares for itself. Its descriptor
    carries `redefines` `"WS-OTM3-Record"`.

    The full field set arrives at [copybooks/slwsoi3.cob:L18-L19] through a COPY
    of `copybooks/slwsoi.cob`, producing a THIRD view over the same 118 bytes -
    `OiHeader` in section B below. Base and views are not kept in step with one
    another: the COBOL does not do so, and rule R-3 forbids adding logic that
    would.

    Byte arithmetic, and the inline offset markers the copybook itself carries:
    7 plus 8 is 15 (`*> 15` at L14), plus 4 is 19 (`*> 19` at L15), plus 99 is
    118 (`*> 118` at L16) - agreeing with the buffer's declared width and with
    the body copybook's own field sum.
    """

    oi3_key: Oi3Key = field(
        metadata=_cobol("OI3-Key", "SAITM3-REC.OI3-KEY", "copybooks/slwsoi3.cob:L12")
    )
    # R-4: `binary-long` in ALL LOWER CASE here and at [copybooks/slwsoi.cob:L15]
    # and [:L54] and [:L56], while the same storage class is written
    # `binary-Char` with a CAPITAL C at [copybooks/slwsoi.cob:L50] and [:L53].
    # Same usage, differently written; both spellings preserved.
    oi3_date: int = field(
        metadata=_cobol(
            "OI3-Date", "Open-Item-Record-3.OI3-Date", "copybooks/slwsoi3.cob:L15"
        )
    )
    # The one ELEMENTARY filler in this module - 99 characters, not a group. It
    # is declared rather than dropped: rule R-3 removes nothing. `name` carries
    # the verbatim COBOL text `filler`; the attribute is numbered positionally
    # within its own class, and this class holds exactly one.
    filler_1: str = field(
        metadata=_cobol(
            "filler", "Open-Item-Record-3.filler", "copybooks/slwsoi3.cob:L16"
        )
    )


#  SECTION B - copybooks/slwsoi.cob, THE TWENTY-EIGHT FIELD BODY
# Fifty-seven lines. Its header reads, verbatim:
#     *>            Sales   in sales                *
#     *>  Working Storage For The Open Item Header  *
#     *> record size 118 bytes 08/02/17 inv bin -> 9(8)
# This is the copybook the BRIDGE reads [common/otm3MT.cbl:L345], and the one
# every column but the primary key is derived from. It is also the copybook whose
# every field name collides with `copybooks/plwsoi.cob` - see the module
# docstring; asking the dictionary for record `OI-Header` returns 69 entries
# spanning both files.


@dataclass
class OiCustomer:
    """The seven-byte group `OI-Customer`, number plus check digit.

    `03  OI-Customer.` [copybooks/slwsoi.cob:L10]

    An alphanumeric concatenation, six plus one giving `char(7)`. Stored as the
    column `OI3-CUSTOMER`; NEITHER of its two children gets a column, so both are
    copybook-only entries. The purchase copybook nests one level deeper here,
    interposing an `OI-Supplier` group [copybooks/plwsoi.cob:L15] that this one
    does not have - a divergence that must survive, so nothing is shared between
    the two modules.
    """

    oi_nos: str = field(
        metadata=_cobol("OI-Nos", "OI-Header.OI-Nos#11", "copybooks/slwsoi.cob:L11")
    )
    oi_check: int = field(
        metadata=_cobol("OI-Check", "OI-Header.OI-Check#12", "copybooks/slwsoi.cob:L12")
    )


@dataclass
class OiKey:
    """The fifteen-byte key group `OI-key`, spelled with a lower-case key.

    `02  OI-key.` [copybooks/slwsoi.cob:L9]

    R-4: the copybook writes `OI-key` with a LOWER-CASE k, while the purchase
    copybook writes `OI-Key` with a capital one [copybooks/plwsoi.cob:L13]. The
    casing is preserved exactly, and it is load-bearing rather than cosmetic:
    it is the reason the dictionary can key this group `OI-Header.OI-key` with no
    line-number suffix, where every other colliding name in the pair needs one.

    This group has no column of its own. The primary key is built from the SHORT
    VIEW's `OI3-Key` [copybooks/slwsoi3.cob:L12] instead, which is the only
    table-mapped field in this record that comes from the other copybook.
    """

    oi_customer: OiCustomer = field(
        metadata=_cobol(
            "OI-Customer", "SAITM3-REC.OI3-CUSTOMER", "copybooks/slwsoi.cob:L10"
        )
    )
    # R-4: DECLARATION BEATS COMMENT. `pic 9(8).   *> was binary-long.` - zoned
    # display, eight digits, scale zero, so the carrier is `int`. The comment
    # records that the field used to be binary and changes nothing about the
    # type. The bridge then widens it to `9(10) COMP` [common/otm3MT.cbl:L304]
    # and the column is `int(8) unsigned`; the descriptor reports DISPLAY and
    # eight digits, never the bridge's.
    oi_invoice: int = field(
        metadata=_cobol(
            "OI-Invoice", "SAITM3-REC.OI3-INVOICE", "copybooks/slwsoi.cob:L13"
        )
    )


@dataclass
class OiBatch:
    """The batch group `OI-Batch`, carrying `comp` for both children.

    `03  OI-Batch                        comp.` [copybooks/slwsoi.cob:L16]

    A GROUP CARRYING A USAGE CLAUSE. Neither child below writes a usage of its
    own, so both inherit `comp` from this header - and both descriptors record
    that provenance, reporting `usage_declared_at` GROUP with
    `usage_inherited_from` `"OI-Batch"`. Reading usage from the picture lines
    alone would class both as zoned display and every stored value would be
    wrong.

    R-4: TRIPLE MATERIALISATION, THE WIDEST IN THIS PACKAGE, WITH A STORAGE-CLASS
    CHANGE ON TOP. The bridge gives this group AND both its children a host
    variable and a column [common/otm3MT.cbl:L306-L308], and all three columns
    are CHARACTER although the two children are numeric::

        OI-Batch   group comp  HV-OI3-BATCH      X(8)  OI3-BATCH      char(8)
        OI-B-Nos   pic 9(5)    HV-OI3-BATCH-NOS  X(5)  OI3-BATCH-NOS  char(5)
        OI-B-Item  pic 999     HV-OI3-BATCH-ITEM X(3)  OI3-BATCH-ITEM char(3)

    Both child columns carry the schema comment `Batch content`, and the group's
    column is filled by a concatenation move at [common/otm3MT.cbl:L1351]. The
    `comp` usage is lost entirely on the way out. The children are carried here
    as `int`, the copybook's own view, and are NOT retyped as text to match the
    column. What the compiled program actually stores in the three of them is
    question 1 of the oracle list.
    """

    oi_b_nos: int = field(
        metadata=_cobol(
            "OI-B-Nos", "SAITM3-REC.OI3-BATCH-NOS", "copybooks/slwsoi.cob:L17"
        )
    )
    oi_b_item: int = field(
        metadata=_cobol(
            "OI-B-Item", "SAITM3-REC.OI3-BATCH-ITEM", "copybooks/slwsoi.cob:L18"
        )
    )


@dataclass
class Filler2:
    """The unnamed `filler` group carrying `comp-3` for ten children.

    `03  filler                          comp-3.` [copybooks/slwsoi.cob:L35]

    AN UNNAMED FILLER GROUP CARRYING THE PACKED-DECIMAL USAGE FOR TEN FIELDS.
    None of the ten below writes a usage of its own, so all ten inherit `comp-3`
    from this header, and every one of their descriptors reports
    `usage_declared_at` GROUP with `usage_inherited_from` `"filler"` - the name
    of a FILLER, carried as declared, with no invented name substituted for it.

    The group is declared rather than dropped even though it has no column and no
    host variable, for two reasons: rule R-3 removes nothing, and this header is
    the sole carrier of the storage class that ten money fields depend on. Its
    descriptor reports `is_filler` and `is_group` both true. The class name is the
    PascalCase of the verbatim COBOL text `filler` plus its position within
    `OiHeader`, matching the `filler_2` attribute that holds it.

    All nine of the fields that reach the schema pass through cleanly - signed
    `pic s9(7)v99` in the copybook, signed `S9(07)V9(02) COMP` in the bridge
    [common/otm3MT.cbl:L313-L321] and signed `decimal(9,2)` in the schema. In
    `VALUEANAL-REC` the money fields lose their sign instead, which is the same
    lesson the module docstring draws from `OI-Cr`: the drift is per field, never
    per type.
    """

    oi_p_c: Decimal = field(
        metadata=_cobol("OI-P-C", "SAITM3-REC.OI3-P-C", "copybooks/slwsoi.cob:L36")
    )
    oi_net: Decimal = field(
        metadata=_cobol("OI-Net", "SAITM3-REC.OI3-NET", "copybooks/slwsoi.cob:L37")
    )
    # R-4: `OI-Approp` HAS NO HOST VARIABLE - `grep -inc "approp"
    # common/otm3MT.cbl` returns 0. It is declared across TWO PHYSICAL LINES,
    # `05  OI-Approp redefines OI-Net` at L38 and `pic s9(7)v99.` at L39, and its
    # existence survives at the far end only as a schema comment on the column
    # its base field owns: `OI3-NET decimal(9,2) NOT NULL COMMENT 'Also called
    # Approp'`. Declared here regardless, as a redefine view over `oi_net`
    # carrying `redefines` `"OI-Net"` - rule R-3 cuts both ways, nothing added
    # AND nothing removed. It contributes no bytes of its own, and what appears
    # in `OI3-NET` once it has been written is question 3 of the oracle list.
    oi_approp: Decimal = field(
        metadata=_cobol(
            "OI-Approp", "OI-Header.OI-Approp#38", "copybooks/slwsoi.cob:L38"
        )
    )
    oi_extra: Decimal = field(
        metadata=_cobol("OI-Extra", "SAITM3-REC.OI3-EXTRA", "copybooks/slwsoi.cob:L40")
    )
    oi_carriage: Decimal = field(
        metadata=_cobol(
            "OI-Carriage", "SAITM3-REC.OI3-CARRIAGE", "copybooks/slwsoi.cob:L41"
        )
    )
    oi_vat: Decimal = field(
        metadata=_cobol("OI-Vat", "SAITM3-REC.OI3-VAT", "copybooks/slwsoi.cob:L42")
    )
    oi_discount: Decimal = field(
        metadata=_cobol(
            "OI-Discount", "SAITM3-REC.OI3-DISCOUNT", "copybooks/slwsoi.cob:L43"
        )
    )
    oi_e_vat: Decimal = field(
        metadata=_cobol("OI-E-Vat", "SAITM3-REC.OI3-E-VAT", "copybooks/slwsoi.cob:L44")
    )
    oi_c_vat: Decimal = field(
        metadata=_cobol("OI-C-Vat", "SAITM3-REC.OI3-C-VAT", "copybooks/slwsoi.cob:L45")
    )
    oi_paid: Decimal = field(
        metadata=_cobol("OI-Paid", "SAITM3-REC.OI3-PAID", "copybooks/slwsoi.cob:L46")
    )


@dataclass
class Filler1:
    """The unnamed `filler` group at `02` level, holding fifteen children.

    `02  filler.` [copybooks/slwsoi.cob:L14]

    AN UNNAMED FILLER GROUP AT LEVEL 02 WRAPPING ALL BUT THE KEY. Everything the
    copybook declares from L15 to L56 nests inside it, which makes `OI-Header`'s
    direct children exactly two - the key group and this one. The dictionary
    confirms the nesting independently: `OI-Batch` records its parent group as
    `filler`.

    Unlike `Filler2` this header carries NO usage clause of its own, so its
    descriptor reports `usage_declared_at` DEFAULT. It has no column and no host
    variable; it is declared because rule R-3 removes nothing and because
    dropping it would flatten the record's real shape. The class name is the
    PascalCase of the verbatim COBOL text `filler` plus its position within
    `OiHeader`, matching the `filler_1` attribute that holds it.

    The purchase copybook has no counterpart to this group at all - its fields
    sit at level 03 directly under `01 OI-Header` [copybooks/plwsoi.cob:L19] - so
    the two records have genuinely different shapes and neither module may be
    derived from the other.
    """

    # R-4: SIGN LOST AT THE BRIDGE, NOT AT THE DATABASE. `binary-long` is signed; the host
    # variable is `9(10) COMP`, unsigned [common/otm3MT.cbl:L305]; the column is `int(8)
    # unsigned`. The `acas019` handler module reproduces that conversion; the descriptor here
    # reports the copybook view - signed - and `drift_for` offers the disagreement unsettled.
    # R-4: NAME TRUNCATED. `OI-Date` becomes `HV-OI3-DAT` and column `OI3-DAT`, the trailing E
    # dropped, while `OI-Date-Cleared` keeps its full name [common/otm3MT.cbl:L329].
    # R-2: this field and `oi_date_cleared` ARE the payment-days arithmetic.
    # [sales/sl100.cbl:L500-L503] guards on zero then subtracts one from the other, feeding the
    # moving average and the worst-days watermark. Both are `binary-long`, so that is INTEGER
    # arithmetic and the carrier is `int`; carrying either as exact-decimal would keep a
    # remainder the compiled program discards (R-4).
    oi_date: int = field(
        metadata=_cobol("OI-Date", "SAITM3-REC.OI3-DAT", "copybooks/slwsoi.cob:L15")
    )
    oi_batch: OiBatch = field(
        metadata=_cobol("OI-Batch", "SAITM3-REC.OI3-BATCH", "copybooks/slwsoi.cob:L16")
    )
    # R-4: NUMERIC TO CHARACTER. `pic 9` in the copybook, `X(1)` in the host
    # variable [common/otm3MT.cbl:L309], `char(1)` in the schema. The descriptor
    # reports the numeric copybook view and the carrier is `int`, never text.
    # R-4: the copybook documents this field's domain in a comment block at
    # [copybooks/slwsoi.cob:L21-L30] - eight codes, with 8 ABSENT and two of them
    # marked "Not used" and "Not Used" with inconsistent capitalisation. It is
    # reproduced verbatim in the module docstring and is DOCUMENTATION ONLY: the
    # COBOL declares no 88-level condition name for this field, the dictionary
    # confirms an empty condition-name tuple for it, and rule R-3 forbids adding
    # the enumeration, lookup or check that block might otherwise invite.
    oi_type: int = field(
        metadata=_cobol("OI-Type", "SAITM3-REC.OI3-TYPE", "copybooks/slwsoi.cob:L19")
    )
    # R-4: WIDTH DRIFT, 25 TO 32. `pic x(25)` here, `X(32)` in the host variable
    # [common/otm3MT.cbl:L310], `char(32)` in the schema - the same shape as the
    # ledger-name widening in `gl_ledger.py`. The value is not corrupted but the
    # PADDING differs, which shows up in a table dump. The descriptor reports 25,
    # and what occupies bytes 26 to 32 on a read-back is question 6 of the oracle
    # list.
    # SALES ONLY: the purchase copybook declares no description field at all,
    # carrying `OI-ref` and `OI-order` in its place [copybooks/plwsoi.cob:L36-L37].
    oi_description: str = field(
        metadata=_cobol(
            "OI-Description", "SAITM3-REC.OI3-DESCRIPTION", "copybooks/slwsoi.cob:L32"
        )
    )
    # `03  OI-Hold-flag     pic x.                 *> Q(uery)`
    # R-4: THE SALES COPYBOOK DECLARES NO CONDITION NAME ON THIS FIELD, where its
    # purchase counterpart declares `88  payment-held                      value
    # "H".` [copybooks/plwsoi.cob:L39]. The absence is preserved and the purchase
    # name is NOT borrowed - no condition name by that name is declared in this
    # module, and `condition_names_for` returns an empty tuple for this attribute
    # because the frozen source declares none. Note too that this record spells it
    # `OI-Hold-flag` with a capital H where purchase spells it `OI-hold-flag` with
    # a lower-case one [copybooks/plwsoi.cob:L38]; both casings are carried
    # verbatim.
    oi_hold_flag: str = field(
        metadata=_cobol(
            "OI-Hold-flag", "SAITM3-REC.OI3-HOLD-FLAG", "copybooks/slwsoi.cob:L33"
        )
    )
    oi_unapl: str = field(
        metadata=_cobol("OI-Unapl", "SAITM3-REC.OI3-UNAPL", "copybooks/slwsoi.cob:L34")
    )
    filler_2: Filler2 = field(
        metadata=_cobol("filler", "OI-Header.filler#35", "copybooks/slwsoi.cob:L35")
    )
    # R-4: NUMERIC TO CHARACTER, and the pointed instance of it. `pic 9` in the
    # copybook, `X(1)` in the host variable [common/otm3MT.cbl:L322], `char(1)` in
    # the schema - yet this is the one field in the record that carries condition
    # names, and their values are NUMERIC:
    #     88  S-Open                         value zero.
    #     88  S-Closed                       value 1.      *> Paid
    # R-4: one uses the figurative constant `zero` and the other the literal `1`.
    # `condition_names_for` returns both as TEXT in the declared spelling, so
    # `"zero"` is never rewritten as `"0"`. Whether a zero arrives in the column as
    # the character "0" or as a space is question 2 of the oracle list.
    oi_status: int = field(
        metadata=_cobol(
            "OI-Status", "SAITM3-REC.OI3-STATUS", "copybooks/slwsoi.cob:L47"
        )
    )
    # R-4: `binary-Char` with a CAPITAL C here and at L53, where the same storage
    # class is written all lower case as `binary-long` at L15, L54 and L56. Same
    # usage, differently written; both spellings preserved.
    # R-4: SIGN LOST AT THE BRIDGE - signed `binary-Char`, unsigned `9(03) COMP`
    # [common/otm3MT.cbl:L323], `tinyint(3) unsigned`. Surfaced unsettled.
    oi_deduct_days: int = field(
        metadata=_cobol(
            "OI-Deduct-Days", "SAITM3-REC.OI3-DEDUCT-DAYS", "copybooks/slwsoi.cob:L50"
        )
    )
    # THE OPPOSITE CASE TO GROUP-USAGE INHERITANCE, and the contrast that makes the
    # rule readable: these two write `comp` ON THEIR OWN PICTURE LINES, so their
    # descriptors report `usage_declared_at` FIELD and `usage_inherited_from`
    # None - unlike the twelve fields under `OI-Batch` and `Filler2`. Getting the
    # direction wrong either way changes every stored value.
    # R-2: `pic s999v99 comp` is a DECIMAL, at scale two, even though its usage is
    # COMP. "COMP means int" is false; scale decides the carrier.
    # These two also keep their sign at all three layers - `S9(03)V9(02) COMP`
    # [common/otm3MT.cbl:L324-L325] and `decimal(5,2)` - while the invoice bridges
    # narrow the identically-purposed fields to unsigned. Per bridge, not per type.
    oi_deduct_amt: Decimal = field(
        metadata=_cobol(
            "OI-Deduct-Amt", "SAITM3-REC.OI3-DEDUCT-AMT", "copybooks/slwsoi.cob:L51"
        )
    )
    oi_deduct_vat: Decimal = field(
        metadata=_cobol(
            "OI-Deduct-Vat", "SAITM3-REC.OI3-DEDUCT-VAT", "copybooks/slwsoi.cob:L52"
        )
    )
    # R-4: SIGN LOST AT THE BRIDGE - signed `binary-Char`, unsigned `9(03) COMP`
    # [common/otm3MT.cbl:L326], `tinyint(3) unsigned`. Surfaced unsettled.
    oi_days: int = field(
        metadata=_cobol("OI-Days", "SAITM3-REC.OI3-DAYS", "copybooks/slwsoi.cob:L53")
    )
    # R-4: THE PROOF THAT SIGNEDNESS DRIFT IS PER BRIDGE AND NOT PER TYPE. This
    # field is `binary-long`, exactly as `OI-Date` at L15 and `OI-Date-Cleared` at
    # L56 are - and it KEEPS its sign the whole way, `S9(10) COMP`
    # [common/otm3MT.cbl:L327] into a signed `int(8)`, while those two lose theirs
    # through the same bridge program into the same table. The invoice bridges then
    # narrow their own `binary-long` field to unsigned again. No rule of the form
    # "binary-long always loses its sign" exists, and none may be written: every
    # field's treatment is read from its own dictionary entry.
    # Note also that the purchase copybook spells this field `OI-CR`
    # [copybooks/plwsoi.cob:L60] where this one spells it `OI-Cr`. Both verbatim.
    oi_cr: int = field(
        metadata=_cobol("OI-Cr", "SAITM3-REC.OI3-CR", "copybooks/slwsoi.cob:L54")
    )
    oi_applied: str = field(
        metadata=_cobol(
            "OI-Applied", "SAITM3-REC.OI3-APPLIED", "copybooks/slwsoi.cob:L55"
        )
    )
    # R-4: SIGN LOST AT THE BRIDGE - signed `binary-long`, unsigned `9(10) COMP`
    # [common/otm3MT.cbl:L329], `int(8) unsigned`. Its name, unlike `OI-Date`'s, is
    # NOT truncated. R-2: integer carrier, for the payment-days reason given at
    # `oi_date` above.
    oi_date_cleared: int = field(
        metadata=_cobol(
            "OI-Date-Cleared", "SAITM3-REC.OI3-DATE-CLEARED", "copybooks/slwsoi.cob:L56"
        )
    )


@dataclass
class OiHeader:
    """The sales open-item record `OI-Header`, two groups over 29 leaves.

    `01  OI-Header.` [copybooks/slwsoi.cob:L8]

    The twenty-eight field body of the sales open-item record, and the layout the
    bridge actually reads [common/otm3MT.cbl:L345]. Twenty-seven of its fields
    reach `SAITM3-REC` as columns, `OI-Approp` reaches it only as a comment on
    another field's column, and the primary key comes from the short view in the
    other copybook.

    Exactly TWO direct children, because everything from L15 to L56 nests inside
    the unnamed level-02 filler: the key group, then that filler.

    THIS IS ALSO A REDEFINE. [copybooks/slwsoi3.cob:L18-L19] copies this record
    while keeping its name and adding `redefines WS-OTM3-Record`, so in that file
    this layout is a third view over the same 118 bytes that `WsOtm3Record` holds
    and `OpenItemRecord3` also redefines. Base and views are not kept in step
    with one another; the COBOL does not do so, and rule R-3 forbids adding logic
    that would.

    MUTABLE BY DESIGN. `sl060` writes this record and applies credit against it,
    and `sl100` clears it, so it is read, mutated and rewritten in the ordinary
    course. It is deliberately not frozen.

    NO FIELD CARRIES A DEFAULT. Neither copybook states an initial value for any
    field - the only `value` clauses in either file are the two 88-level ones at
    [copybooks/slwsoi.cob:L48-L49] - so inventing one would add a value the frozen
    source never states (rule R-3).
    """

    oi_key: OiKey = field(
        metadata=_cobol("OI-key", "OI-Header.OI-key", "copybooks/slwsoi.cob:L9")
    )
    filler_1: Filler1 = field(
        metadata=_cobol("filler", "OI-Header.filler#14", "copybooks/slwsoi.cob:L14")
    )
