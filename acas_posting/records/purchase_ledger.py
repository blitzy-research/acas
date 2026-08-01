"""The Purchase Ledger record: `WS-Purch-Record` from `copybooks/wspl.cob`.

One supplier account of the ACAS Purchase Ledger, laid out field for field from
the frozen copybook with nothing added and nothing dropped. Four plain
dataclasses, no behaviour: `WsPurchRecord` and the three subordinate groups the
copybook declares - `PurchAddress`, `Quarters` and `QuartersView`.

    entity facade   Purch
    handler         acas022                 [common/acas022.cbl]
    bridge          purchMT                 [common/purchMT.cbl]
    table           PULEDGER-REC, 29 columns
                                            [mysql/ACASDB.sql:L646-L677]
    primary key     PURCH-KEY               [mysql/ACASDB.sql:L676]
    copybook        copybooks/wspl.cob, 55 lines, 01 level at L13

Agent Action Plan section 0.4.1.3 sets this folder's mandate, verbatim: "Every
module is a CREATE from its copybook, translating each 05/03 field to a
dataclass attribute whose descriptor is looked up in the generated dictionary."
Its second sentence, restated rather than quoted because the plan's wording uses
a word this module must keep out of its text, requires that oddities in the
source be preserved and never amended. Section 0.8.1 fixes the shape - "Plain
modules and dataclasses; no ORM entity layer" - and R-3 the content: "The 27
record modules mirror their copybooks field for field with nothing added."
R-1 through R-6 are the plan's own identifiers (section 0.7.2); this project
carries no separate rules document, so the plan is where their full text lives.

THIS MODULE COMPUTES NOTHING
============================
It declares storage and provenance: no arithmetic, no padding, no truncation,
no store, and no condition-name test. Those belong to `cobol/arithmetic.py`,
`cobol/move.py` and `cobol/condition_names.py`, to the `acas022` handler module
at the bridge boundary, and to the `pl055`, `pl060` and `pl100` program modules.

WHY THE TYPES HERE DECIDE WHETHER THREE LEGACY DEFECTS SURVIVE
==============================================================
Three anomaly-register entries - A-8 double truncation, A-9 the skipped counter
increment, A-10 three disagreeing guards - have a Purchase instance, and every
one turns on the storage class of the five statistics fields at
[copybooks/wspl.cob:L35-L42]: `binary-long`, signed 32-bit integers with no
PICTURE clause and so no fractional positions, making the running figures the
posting programs keep in them integer quotients that discard their remainder.
Agent Action Plan section 0.6.1 states the consequence - that truncation "is
integer truncation, which is exactly what makes the moving-average defect
reproducible." Carry any one as a `Decimal` and the remainder survives, the
defect disappears, and under R-4 that is a failure: "A defect reproduced is
correct; a defect fixed is a failure." They are `int`; the dependent sites are:

    purchase/pl060.cbl  purch-comp section L740
        L743-L744 two-condition guard; L745 product; L746-L747 else zero;
        L749 "add 1 to purch-activety." BEFORE the quotient; L750 accumulate;
        L751 "divide purch-activety into work-2 giving purch-average."

    purchase/pl060.cbl  credit-comp section L755
        L758-L759 the SAME two-condition guard; L760 product; the counter is
        NEVER incremented here (A-9); L764 an extra "if work-2 not = zero";
        L765 accumulate; L766 the quotient, into the SAME two fields.

    purchase/pl100.cbl  compute-purch-pay region
        L494 "subtract oi-date from oi-date-cleared giving work-a."; L495 zero
        into the accumulator; L497 a ONE-condition guard - a third variant
        (A-10); L498 product; L500 accumulate; L501 "add 1 to
        purch-pay-activety."; L502 "divide work-b by purch-pay-activety giving
        purch-pay-average." - the REVERSED operand order, `by` where pl060
        writes `into`; L504-L505 the worst-payment-days watermark.

Two nuances are recorded rather than smoothed over. `credit-comp` reuses
`purch-activety` and `purch-average` - the very fields `purch-comp` maintains -
rather than a separate credit pair. And the reversal at pl100:L502 is TEXTUAL:
`into` and `by` exchange the roles of their operands, so both sites happen to
form accumulator over counter. It is preserved as written, the program modules
own it, and nothing here folds the three variants together. Agent Action Plan
section 0.6.1 gives the reason: "Normalising them into one helper would be the
single easiest way to fail this migration."

THE TWO-DIRECTION TYPE RULE - AND THIS RECORD CONTAINS BOTH DIRECTIONS
======================================================================
"Binary means integer" holds only at scale zero, and this one record carries an
example of each direction:

    DIRECTION 1  binary usage, NO picture, no fractional positions -> int.
                 `Purch-Credit binary-char` [copybooks/wspl.cob:L31] plus the
                 eleven `binary-long` items at L32-L42: twelve fields.
    DIRECTION 2  COMP WITH a V, two fractional positions -> Decimal.
                 `Purch-Discount pic 99v99 comp` [copybooks/wspl.cob:L30], four
                 digits, scale 2, UNSIGNED - Decimal despite its own comment.

Get either direction wrong and every stored value changes; `records/
irs_nominal.py` carries the same warning for `pic 9(8)v99 comp`.

DECLARATION BEATS COMMENT - THREE TIMES IN THIS COPYBOOK
========================================================
Three inline comments describe something other than what their own line declares
- L30 `*> RDB comp-3` on a COMP item, L31 `*> were pic 99` on a `binary-char`,
and L32 `*> all these were pic 9(8) comp` covering the whole L32-L42 run. In each
case the DECLARATION governs and the comment is history; each field's own
attribute comment below carries the detail, including the bridge's dated
explanation "11/07/23 was comp-3 now matches wspl.cob"
[common/purchMT.cbl:L343], which settles the L30 question rather than leaving it
open, and the fact that its Sales counterpart [copybooks/wssl.cob:L42] carries no
such comment. No digit count, scale or sign below is taken from a comment: the
`99` and `9(8)` inside them are historical text, not declarations.

NAMES ARE CARRIED VERBATIM, MISSPELLINGS AND CASING INCLUDED
============================================================
Every COBOL name below is quoted exactly as `copybooks/wspl.cob` spells it, with
its locator on the attribute's own comment.

    Purch-Activety [L35] and Purch-Pay-Activety [L40] misspell the word, and the
    misspelling travels the whole way through - HV-PURCH-ACTIVETY
    [common/purchMT.cbl:L299] and column PURCH-ACTIVETY - so the correctly
    spelled form appears nowhere here. Purch-Last-inv [L36] and Purch-Last-pay
    [L37] carry lower-case tail segments where every neighbour is capitalised,
    yet their columns are PURCH-LAST-INV and PURCH-LAST-PAY. Turnover-q1..q4
    [L46-L49] and PTurnover-q [L51] use lower-case q where the Sales twin writes
    upper-case Q, yet the columns are TURNOVER-Q1 through TURNOVER-Q4. And
    Supplier-live [L19] / Supplier-dead [L20] are lower-case condition names
    carrying `value 0` where the Sales twin writes `value zero`
    [copybooks/wssl.cob:L27] for the same idea.

Because the COBOL name, the host-variable name and the column name drift apart,
no key below is built by mechanical transformation of an attribute name; each is
looked up by copybook name and declaration line - see `_index_copybook` and
`_descriptor`.

THE HEADER'S OWN HISTORY, VERBATIM
==================================
    L3-L4  "WS Definition For The Purchase Ledger" / "Record."
    L6     "rec size 299 bytes  26/03/09"
    L7     "rec size 300 bytes  22/12/11"
    L8     "rec size 302 bytes  4/03/2012 checked by COBSTRUCT (PRIMA tool)"
    L9     "13/09/15 changed 4 SQL Mig."
    L10    "taken from fdpl.cob 23/07/16"
    L11    "15/01/18 Added Purch-Stats-Date with filler space."

Three successive declared sizes, 299 then 300 then 302, the last carrying an
external verification note - COBSTRUCT, the PRIMA tool - with no counterpart in
`copybooks/wssl.cob`, whose header records a single size of 300 [:L7]. The 302
includes `Purch-Stats-Date`, which is why that field stays declared below.

A NEW ANOMALY RAISED BY THIS MODULE
===================================
`Purch-Stats-Date pic 9(4).  *> added 15/01/18.` [copybooks/wspl.cob:L53]
reaches NO host variable and NO column. It is not among the Agent Action Plan's
twenty-two section 0.6.7 entries, so it is raised here as a new entry for the
migration's anomaly log. The field's own attribute comment below carries the
four-part evidence - declared, no host variable, skipped by `bb000-HV-Load`
[common/purchMT.cbl:L1203], no column - and the generated entry is one-sided,
`loader.cite` reporting "bridge=absent column=absent". One nuance, because a
coarser check would mislead: the STRING "stats" DOES occur in
`common/purchMT.cbl`, at L364, but as part of the bridge's own inline buffer `01
Purch-Rec.` (see THE FOURTH LAYER below), never as a host variable. So the field
is declared TWICE on the COBOL side and mapped ZERO times.

AND THE ASYMMETRY IS THE EVIDENCE OF ACCIDENT
    The Sales copybook added the identical field on the identical date with the
    identical comment - `Sales-Stats-Date pic 9(4). *> added 15/01/18.`
    [copybooks/wssl.cob:L64] - and there the bridge DID gain
    `HV-SALES-STATS-DATE PIC X(4).` [common/salesMT.cbl:L320] and the schema DID
    gain `SALES-STATS-DATE char(4) NOT NULL` [mysql/ACASDB.sql:L981]. Neither of
    the latter two exists here: the Purchase side of that change was never carried
    through. R-3 forbids removal as firmly as addition, so the field is declared
    regardless at its copybook view - DISPLAY, 4 digits, scale 0, unsigned, int -
    with no stub column, no stub host variable and no reconciliation with Sales.

THE SHAPE IS NOT UNIQUE; THE ASYMMETRY IS
    A sweep of all 1015 generated entries shows the SHAPE recurs: `IRSFINAL-REC`
    drops `ar3 pic x(5)` [copybooks/irswsfinal.cob:L68] and the `ar1-1..ar1-26`
    and `ar2-1..ar2-26` runs, and `SYSTEM-REC` drops `Phone-No`
    [copybooks/wssystem.cob:L80], `SL-BO-Default` [:L277] and `FILLER-Dummy4`
    [:L329]. `records/irs_posting.py` carries the exact MIRROR: three COLUMNS with
    no copybook field at all, derived by the bridge under a guard
    [common/irspostingMT.cbl:L982-L987]. What IS particular here is narrower -
    this is the only dropped standalone field in `copybooks/wspl.cob`, its parent
    is the 01 record directly rather than an array or nested group, and its Sales
    twin was carried through in full.

AN OPEN QUESTION FOR THE COMPILED ORACLE (R-6, question 2 of 2)
    Because the field reaches no column, any value written to it is invisible in
    every table dump, so the state-diff protocol cannot observe it at all. Whether
    anything in the posting cycle ever reads it back is undecidable from the
    source and must be measured against the compiled program. Recorded for the
    migration's ambiguity-resolutions document; nothing here presumes an answer.

DRIFT AT THE BRIDGE BOUNDARY - FIVE KINDS, ALL LEFT UNSETTLED HERE
==================================================================
The bridge is not a transparent pipe. For several fields the copybook
declaration, the bridge host variable and the MySQL column disagree, and some
disagreements change a value BEFORE any SQL executes. The descriptors below
report the COPYBOOK view and nothing else; the `acas022` handler module owns the
conversions, and `loader.drift_for` shows the disagreement. The host-variable
group is `01 TD-PULEDGER-REC.` [common/purchMT.cbl:L284], twenty-nine variables
at L285-L313, loaded by `bb000-HV-Load Section.` [:L1203] from
`ba070-Process-Write` [:L884] and `ba090-Process-Rewrite` [:L967].

KIND 1 - SIGNEDNESS LOSS. Anomaly A-11's Purchase instance, twelve fields wide.
    The twelve signed copybook items at L31-L42 - `Purch-Credit` and the eleven
    `binary-long` - narrow to twelve unsigned host variables at
    [common/purchMT.cbl:L295-L306], in declaration order, and to twelve unsigned
    columns at [mysql/ACASDB.sql:L657-L668]. Agent Action Plan section 0.6.2
    states the consequence, verbatim: "a negative value computed in COBOL loses
    its sign at the bridge, not at the database - so the Python data-access layer
    must reproduce the bridge's conversion, not merely write the computed value
    and let MySQL complain." Section 0.6.7 entry 11 names only the Sales case;
    this instance is wider and adds a `binary-char`, which Sales never declares.

KIND 2 - A THREE-WAY WIDTH DISAGREEMENT, in two different directions.
    `Purch-Credit`  binary-char 8-bit signed -> `PIC  9(08) COMP`, a WIDENING
                    [common/purchMT.cbl:L295] -> `mediumint(2)`, a NARROWING.
    `Purch-SortCode` binary-long 32-bit signed -> `PIC  9(08) COMP` [:L296] ->
                    `mediumint(6)`, NARROWER THAN BOTH. A UK sort code is six
                    digits, so that column is semantically apt and structurally
                    the tightest of its three layers.
    Neither chain is widened or narrowed here.

KIND 3 - GROUP CONCATENATION, alphanumeric. `PurchAddress`'s own docstring carries
    this in full: the L23 group's two x(48) children reach one `HV-PURCH-ADDRESS
    PIC X(96)` [common/purchMT.cbl:L289] and one `PURCH-ADDRESS char(96)`, derived
    as GROUP_CONCATENATION at [:L1216]. Both children are declared below
    regardless. SALES-ADDRESS is the same shape, as is `WS-Post-Key` numerically.

KIND 4 - NAME TRUNCATION. `Purch-Create-Date` [copybooks/wspl.cob:L39] becomes
    `HV-PURCH-CREATE-DAT` [common/purchMT.cbl:L303] and column
    `PURCH-CREATE-DAT`, the trailing E dropped, and the bridge records why at
    [:L352] - "chg name 4 SQL Mig." `Post-Date` -> `POST4-DAT` in
    `records/irs_posting.py` is the same shape, as is SALES-CREATE-DAT.

KIND 5 - COPYBOOK ONLY: no host variable, no column. `Purch-Stats-Date`
    [copybooks/wspl.cob:L53]; see the new-anomaly section above. This is the one
    field for which the bridge is NOT the record-layout source, because it never
    maps it - so here, and only here, the copybook is the only source there is.
    Saying so explicitly matters: left implicit it would misrepresent the
    preserved user requirement that the bridge "defines the ... record-layout <->
    table mapping - it is the data dictionary for this migration."

TWO FURTHER KINDS, COUNTED FROM THE DICTIONARY RATHER THAN THE BRIEFING
    KIND 2b - DIGIT WIDENING ON THE TWO ZONED FLAGS. `Purch-Status` [L18] and
    `Purch-Notes-Tag` [L21] are `pic 9` - ONE digit - yet their host variables are
    `PIC  9(03) COMP` [common/purchMT.cbl:L286-L287] and their columns
    `tinyint(1) unsigned`: DISPLAY -> COMP -> TINYINT. KIND 2c - STORAGE CLASS
    ONLY, on every money field: the seven `comp-3` fields are COMP-3, then COMP,
    then DECIMAL, with sign, digits and scale agreeing throughout.

    THE FULL CENSUS: 22 of the 29 table-backed entries carry at least one drift
    flag - `PURCH-KEY` carries `name`, the two zoned flags `usage` and `digits`,
    the twelve binary fields `signedness` and `usage` (with `PURCH-CREATE-DAT`
    additionally `name`), and the seven money fields `usage`. The seven UNFLAGGED
    entries are the five alphanumerics, the `PURCH-ADDRESS` group and
    `PURCH-DISCOUNT` - making PURCH-DISCOUNT the only NUMERIC field here that
    agrees perfectly across all three layers, a pointed contrast with the stale
    comment on its own declaration line.

THE CLEAN PASS-THROUGH, stated because the drift is specific rather than
    systemic: `Purch-Current` and `Purch-Last` `pic s9(8)v99 comp-3` [L43-L44]
    become `PIC S9(08)V9(02) COMP` [common/purchMT.cbl:L307-L308] and
    `decimal(10,2)`, as do `Turnover-q1..q4` [:L309-L312] and `Purch-Unapplied`
    [:L313]. Money keeps its sign; statistics do not.

TRAILING SPACES AND SUBSTRING TRIMS BELONG TO THE HARNESS, NOT HERE. The bridge
    trims on the way out - `STRING FUNCTION TRIM (HV-PURCH-ADDRESS, TRAILING)`
    [common/purchMT.cbl:L1351], likewise HV-PURCH-KEY, -NAME, -PHONE, -EXT, -FAX
    and -EMAIL at [:L1309], [:L1342], [:L1360], [:L1369], [:L1378], [:L1387] - and
    takes numeric substrings of an edit field at [:L1320], [:L1332], [:L1398],
    [:L1415], [:L1427], [:L1439] onward. The harness owns stored-value padding.

THE FOURTH LAYER - A STALE INLINE RECORD INSIDE THE BRIDGE ITSELF
=================================================================
The drift is four-layered, not three. `common/purchMT.cbl` has no `copy
"wspl.cob"` statement - its only four copies are mysql-variables.cpy [:L279],
wsfnctn.cob [:L320], Test-Data-Flags.cob [:L324] and mysql-procedures.cpy
[:L1178], and the string `wspl.cob` appears only inside two comments, at [:L110]
and [:L343]. Instead the bridge declares its own record inline in the LINKAGE
SECTION [:L316], as `01 Purch-Rec.` at [:L331], under this header:

    [:L326]  "Generated by MOSTGEN from the COPY Book... The record buffer"
    [:L327]  "This data buffer was derived from the ...PULEDGER.CBF" - the
             original quotes a DOS-style path, separator included
    [:L328]  "COPY book by MOSTGEN. It is hard coded here so you"
    [:L329]  "can see which version of the Source Set was used."

That buffer is operative, not decorative: it is the third parameter of the
bridge's own entry point, `PROCEDURE DIVISION using File-Access /
ACAS-DAL-Common-data / Purch-Rec.  *> Ws record` at [:L385-L387], is indexed as
`Purch-Rec (K:L)` at [:L872] and is cleared by `initialize Purch-Rec with
filler` at [:L1149]. AND IT HAS DRIFTED FROM THE FROZEN COPYBOOK IN TWELVE WAYS:

Each row reads "inline buffer vs frozen copybook".

    record name       Purch-Rec [:L331] vs WS-Purch-Record [L13]
    key name          Purch-Key [:L332] vs WS-Purch-Key [L14]
    condition names   Supplier-Live/-Dead, mixed case [:L334-L335] vs
                      Supplier-live/-dead, lower case [L19-L20]
    address           FLAT `pic x(96)` [:L338] vs a GROUP of two x(48) [L23-L25]
    credit            `pic 99 comp` [:L344] vs `binary-char` [L31]
    sortcode spelling Purch-Sortcode [:L345] vs Purch-SortCode [L32]
    last-inv / -pay   Purch-Last-Inv / -Pay, mixed [:L349-L350] vs
                      Purch-Last-inv / -pay, lower [L36-L37]
    create-date       Purch-Create-Dat [:L352] vs Purch-Create-Date [L39]
    MONEY WIDTH       `pic s9(9)v99`, ELEVEN digits [:L356-L363] vs
                      `pic s9(8)v99`, TEN digits [L43-L52]
    quarter casing    Turnover-Q1..Q4, upper [:L359-L362] vs Turnover-q1..q4,
                      lower [L46-L49]
    the redefines view  ABSENT ENTIRELY vs `filler redefines Quarters` plus
                      `PTurnover-q ... occurs 4` [L50-L51]
    stats-date        present [:L364] but never mapped vs present [L53]

The decisive point: the HOST VARIABLES agree with the frozen COPYBOOK - ten
digits, `PIC S9(08)V9(02) COMP` at [:L307-L313] - and NOT with the inline
buffer's eleven. So this module is built from `copybooks/wspl.cob`, and the
buffer is recorded as a fourth, divergent layer rather than treated as a source,
and offered as a further entry for the migration's anomaly log. Two of its
comments earn their keep by explaining copybook oddities - [:L343] the stale
`*> RDB comp-3` at [copybooks/wspl.cob:L30], and [:L352] the dropped trailing E
on PURCH-CREATE-DAT - both confirming that the declaration governs. One briefing
claim is corrected rather than repeated: the comment at [:L884] does NOT name a
record appearing nowhere, since `01 Purch-Rec.` IS declared at [:L331] and IS a
PROCEDURE DIVISION parameter. The only genuine oddity is casing, the comment
writing `Purch-REC` against the declaration's `Purch-Rec`.

"THE PURCHASE MIRROR" IS THE MOST DANGEROUS PHRASE IN THIS BRIEF
================================================================
`records/sales_ledger.py` models a genuinely similar record, and that similarity
is a trap. This module IMPORTS NOTHING FROM IT, shares no base class, mixin,
helper, descriptor table or naming shortcut with it, and is not a copy of it with
the prefixes exchanged; it was built from `copybooks/wspl.cob` alone. The two
copybooks differ structurally in fourteen counted ways - nine named in the
briefing, five more found by comparing them - and every one survives here
unharmonised. The register, for the migration's traceability document:

Each row reads "Purchase (wspl.cob) / Sales (wssl.cob)".

     1  stats-date column  absent, no host var, no column [L53] /
        SALES-STATS-DATE char(4) present [L64]
     2  field order  Purch-Status [L18] and Purch-Notes-Tag [L21] BEFORE
        Purch-Name [L22] / Sales-Name first [L17], Sales-Status later [L25]
     3  fax / e-mail order  Purch-Fax [L28] before Purch-Email [L29] /
        Sales-Email [L23] before Sales-Fax [L24]
     4  the flag block  ABSENT ENTIRELY, no late-charge, reminder or e-mail
        switches / six flags, FIVE of them with 88s - Sales-Late [L28-29],
        Sales-Dunning [L30-31], Email-Invoice [L32-33], Email-Statement
        [L34-35], Email-Letters [L36-37], and Delivery-Tag [L38] with no 88
     5  bank details  Purch-SortCode [L32] + Purch-Accountno [L33] / ABSENT
     6  binary run ORDER  Purch-Create-Date at position 8 [L39], BEFORE the
        Pay-* trio / Sales-Create-Date LAST [L53], AFTER that trio
     7  credit field type  binary-char [L31] / pic 99 [L41], zoned DISPLAY,
        "*> In days"
     8  partial-ship flag  ABSENT / Sales-Partial-Ship-Flag [L65-66] plus
        88 Sales-BO-Set value "Y" [L67]
     9  FILLER shape  one, pic x(12) [L54] / two, pic xxx [L40] and x(5) [L68]
    10  binary-short  NONE declared at all / Sales-Late-Min and Sales-Late-Max
        [L43-44]
    11  redefines view name  PTurnover-q, P prefix, lower q [L51] /
        STurnover-Q, S prefix, upper Q [L62]
    12  header end date  last entry 15/01/18 [L11] / last entry 06/02/24, the
        back-order flag [L9-10]
    13  header wording  "WS Definition For The Purchase Ledger Record." /
        "Record Definition For The Sales Ledger / Taken from fdsel"
    14  declared size  302 bytes, three revisions, plus the COBSTRUCT note
        [L6-L8] / 300 bytes, one revision, no external note [L7]

And the casing and spelling divergences on top of those fourteen:
Supplier-live / Supplier-dead with `value 0` here against Customer-Live /
Customer-Dead with
`value zero` there [copybooks/wssl.cob:L26-L27]; the prefixed `Purch-Notes-Tag`
[L21] against the bare `Notes-Tag` [copybooks/wssl.cob:L39]; `Turnover-q1`
against `Turnover-Q1`; `Purch-Last-inv` / `-pay` against `Sales-Last-Inv` /
`-Pay`; and `Array-k` against `Array-K` - even the dead declarations diverge.

THE DEAD DECLARATION AT L15-L17 IS RECORDED AND NOT MODELLED
============================================================
    *>     03  filler   redefines WS-Purch-Key.      [copybooks/wspl.cob:L15]
    *>         05  Array-k         pic x  occurs 6.  [copybooks/wspl.cob:L16]
    *>         05  Check-Digit     pic 9.            [copybooks/wspl.cob:L17]

All three lines are COMMENTED OUT in the frozen copybook, so the key-character
array and the check digit are not part of the record: no attribute, nested class
or key-decomposition view for them appears below, and the dictionary carries no
entry for either name. Their presence is recorded because the casing diverges
from the Sales twin's `Array-K` [copybooks/wssl.cob:L15], and because a reader
diffing the two files should know the omission is deliberate.

WHY THE TABLE HAS TWENTY-NINE COLUMNS - THE ARITHMETIC, SHOWN
=============================================================
`copybooks/wspl.cob` declares 33 leaf (non-group) data items: L14, L18, L21,
L22, L24, L25, L26, L27, L28, L29, L30, L31, the eleven at L32-L42, L43, L44,
the four at L46-L49, L51, L52, L53 and L54. Its groups are L23 Purch-Address,
L45 Quarters and L50 the unnamed `filler redefines`, under the L13 01 record.

    33  leaf data items
    -1  the trailing FILLER at L54            - fillers reach no column
    -1  the PTurnover-q redefines view at L51 - a second view of L46-L49,
                                                not additional storage
    -1  Purch-Stats-Date at L53               - no column at all (KIND 5)
    ---
    30
    -2  the two address children L24, L25     - concatenated by the bridge
    +1  the Purch-Address group L23           - into one column (KIND 3)
    ---
    29  columns

Twenty-nine, matching the frozen DDL at [mysql/ACASDB.sql:L646-L677] and Agent
Action Plan section 0.6.6 exactly. Every one of the 29 columns is NOT NULL,
there are no column-level defaults, no TIMESTAMP, no AUTO_INCREMENT and - as R-2
requires across the whole schema - no FLOAT, DOUBLE or REAL anywhere.

That NOT NULL property is why NO attribute below is ever None. Agent Action Plan
section 0.6.2 gives the mechanism: the bridge `initialize`s its host-variable
group before loading, "so unset fields become zero or space rather than SQL NULL.
This is why every column in the schema can be declared NOT NULL and why the
Python layer must default rather than omit." Defaults follow exactly - zero for a
numeric field, SPACES AT THE DECLARED WIDTH for an alphanumeric one rather than an
empty string, because a `char(n)` column holding an initialised COBOL field holds
n spaces - with the widths read from each descriptor, never typed in.

PROVENANCE: EVERY DESCRIPTOR IS LOOKED UP, NONE IS TRANSCRIBED
==============================================================
Agent Action Plan section 0.8.1 makes the ordering a directive: "Data dictionary
first. The dictionary is generated from the bridge before record definitions are
written, and every Python field definition cites its entry ... it is what
prevents fields being transcribed by eye." So every attribute below carries a
`FieldDescriptor` in its `dataclasses.field` metadata via
`FieldDescriptor.from_dictionary_key`, every key found by asking the dictionary
which entry sits at a given copybook field name and declaration line - see
`_index_copybook` and `_descriptor`. No key is assembled by upper-casing or
hyphenating an attribute name, which would be wrong for five fields here alone:

    Purch-Create-Date -> PULEDGER-REC.PURCH-CREATE-DAT   trailing E dropped
    Purch-Address     -> PULEDGER-REC.PURCH-ADDRESS      one column, two children
    Purch-Last-inv    -> PULEDGER-REC.PURCH-LAST-INV     casing changes
    Turnover-q1       -> PULEDGER-REC.TURNOVER-Q1        casing changes
    Purch-Stats-Date  -> WS-Purch-Record.Purch-Stats-Date   a different namespace
                                                         entirely, no column to
                                                         key on

THE DESCRIPTOR SPLIT, COUNTED: 37 LOOKED UP, 0 HAND-BUILT.
    Metadata typed in by hand is not needed for the FILLERs, the
    PTurnover-q view, the address children or Purch-Stats-Date, none of which has
    a column: `loader.entries_for_copybook_file("copybooks/wspl.cob")` returns 37
    entries - the 29 table-backed plus 8 one-sided (the 01 record, Purch-Addr1,
    Purch-Addr2, Quarters, filler#50, PTurnover-q, Purch-Stats-Date, filler#54).
    EVERY field here has a generated entry, so the four dataclasses between them
    carry 37 DISTINCT dictionary keys - 36 on fields plus four class-level, three
    of which repeat a field key - and state NO metadata by hand at all, so
    R-5's "derived, not transcribed" holds without exception. One-sided keys use
    the `<COPYBOOK-RECORD>.<FIELD-NAME>` form, the fillers disambiguated by line.

ONE DISCREPANCY AGAINST THE BRIEFING, REPORTED NOT PATCHED. The briefing expects
    `scale == 0` for the twelve binary fields; the dictionary records `scale is
    None` and `digits is None` too, because `binary-char` and `binary-long` carry
    no PICTURE clause at all - None here means ABSENT, not zero. That is the
    dictionary's representation of a picture-less binary item and is left alone.
    The load-bearing fact is untouched: `python_storage` is INT, `is_int` is true,
    and the integer truncation A-8, A-9 and A-10 depend on is reproducible.

AN OPEN QUESTION FOR THE COMPILED ORACLE (R-6, question 1 of 2)
    Agent Action Plan section 0.6.8, verbatim: "A negative binary value through
    an unsigned host variable into an unsigned column. Section 0.6.2 establishes
    that the sign is lost; what the resulting stored value IS depends on the
    conversion the bridge's C interface performs, which must be measured rather
    than assumed."

    That question is about the twelve fields in KIND 1, and it is SHARPER here
    than on the Sales side because of KIND 2: `Purch-SortCode`'s column is
    narrower than both its field and its host variable, so overflow behaviour
    must be measured as well as sign behaviour. This module therefore stores no
    assumed bit pattern, no magnitude and no modulus - it reports the signed
    copybook view, and the `acas022` handler module will carry whatever the
    oracle shows. Recorded for the migration's ambiguity-resolutions document.

DETERMINISM (R-6)
=================
Attribute order is the copybook's declaration order, L14 through L54, which is
NOT the Sales order - see register rows 2, 3 and 6. `PTurnover-q ... occurs 4` is
a fixed four-element tuple, never a list. Four attributes are date-like -
Purch-Last-inv, Purch-Last-pay, Purch-Create-Date and Purch-Stats-Date - and
none touches a clock: no wall-clock reads, no environment reads, no identity
reads and no directory scans anywhere in this module. The only I/O is the
dictionary loader's own lazily cached read of the committed JSON artifact.

R-1 holds trivially - standard library plus two first-party modules, no process
spawning, no foreign-function interface, no driver, no translator invocation -
and R-3 by construction: exactly the fields the copybook declares, in its order,
with no checks, no coercion, no post-construction hook and no schema-owning
metadata; no threads and no event loop.

THE LEAF RULE (Agent Action Plan section 0.4.3)
==============================================
`records/*.py` may import `cobol.field` and `dictionary.loader` and nothing
else, "which keeps the record layer a leaf". That is taken literally:
`ConditionName` and `DictionaryEntry` come through `dictionary.loader`, which
re-exports the object model's records as bindings to the single definition
rather than copies - the same door `cobol/field.py` uses for its own
enumerations. Not imported, deliberately: `dictionary.model` reached directly
rather than through the loader, any `dal` module, any `programs`
module, `cli`, `clock`, `dates`, `workfiles`, `cobol.arithmetic`, `cobol.move`,
`cobol.picture`, `cobol.usage`, `cobol.condition_names`, `cobol.sortverb`,
`dictionary.generate`, `harness`, and any other `records` module - above all
`records/sales_ledger.py`. Section 0.4.3 gives the payoff: "the arithmetic suite
imports only cobol and records and touches no database, so it runs anywhere."
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# Two dictionary types, reached through the loader - the one door Agent Action
# Plan section 0.4.3 opens from this layer onto the dictionary package. The
# loader re-exports the object model's records for exactly this purpose (see its
# `RE_EXPORTED_MODEL_NAMES`), each re-export being a BINDING to the single
# definition rather than a copy, so no competing copy is declared here (rule
# R-5). `DictionaryEntry` is an annotation only; `ConditionName` additionally
# carries real data here - see PURCH_STATUS_CONDITION_NAMES.
from acas_posting.dictionary.loader import ConditionName, DictionaryEntry

__all__ = (
    # Sorted the way the sibling modules sort theirs - the spine constants and the
    # condition-name data first, each group alphabetical, then the record and its
    # three subordinate groups.
    "BRIDGE",
    "COPYBOOK",
    "HANDLER",
    "PURCH_STATUS_CONDITION_NAMES",
    "TABLE",
    "PurchAddress",
    "Quarters",
    "QuartersView",
    "WsPurchRecord",
)

# The entity spine, from Agent Action Plan section 0.2.1.1

COPYBOOK: Final[str] = "copybooks/wspl.cob"
"""The frozen record layout this module mirrors. Read-only, never modified."""

TABLE: Final[str] = "PULEDGER-REC"
"""The MySQL table, 29 columns [mysql/ACASDB.sql:L646-L677]; its
`PRIMARY KEY (PURCH-KEY)` clause is at [mysql/ACASDB.sql:L676]."""

HANDLER: Final[str] = "acas022"
"""The COBOL file handler the posting programs CALL [common/acas022.cbl]."""

BRIDGE: Final[str] = "purchMT"
"""The generated bridge program [common/purchMT.cbl]."""

# Provenance: descriptors are looked up, never transcribed (R-5)


def _locator(line: int) -> str:
    """Build the source locator for a declaration line of the frozen copybook.

    Produces exactly the `<file>:L<line>` form the generated dictionary and
    `FieldDescriptor.source_locator` both use, so a locator written here is
    matched against the artifact rather than merely resembling it.
    """
    return f"{COPYBOOK}:L{line}"


def _index_copybook() -> dict[tuple[str, str], DictionaryEntry]:
    """Index this copybook's generated entries by COBOL name and locator.

    Keying on the pair rather than the name alone matters: `copybooks/wspl.cob`
    declares `filler` twice, at L50 and L54, and the dictionary disambiguates
    them as `filler#50` and `filler#54`. The pair is unique across all 37
    entries, so the locator both selects the right one and checks that the line
    number quoted at each attribute below is the line the artifact records.
    """
    return {
        (entry.copybook.name, entry.copybook.source): entry
        for entry in loader.entries_for_copybook_file(COPYBOOK)
    }


_ENTRIES: Final[dict[tuple[str, str], DictionaryEntry]] = _index_copybook()
"""All 37 generated entries for this copybook - 29 table-backed, 8 one-sided."""


def _descriptor(cobol_name: str, locator: str) -> FieldDescriptor:
    """Look up one field's descriptor by its COBOL name and declaration line.

    The dictionary key is READ from the matching entry, never assembled from
    the Python attribute name. That distinction is load-bearing for this
    record: `Purch-Create-Date` is keyed on the column `PURCH-CREATE-DAT` with
    its trailing E dropped, `Purch-Last-inv` on `PURCH-LAST-INV` with different
    casing, `Turnover-q1` on `TURNOVER-Q1`, both address children on no column
    at all, and `Purch-Stats-Date` on the copybook-record namespace because it
    has no column to key on. Any mechanical transformation of an attribute name
    would get five fields in this one record wrong.

    A field absent from the index raises `KeyError` on the spot, naming the
    pair, rather than silently yielding a descriptor for the wrong field.
    """
    return FieldDescriptor.from_dictionary_key(_ENTRIES[(cobol_name, locator)].key)


def _metadata(descriptor: FieldDescriptor) -> dict[str, FieldDescriptor]:
    """Attach a descriptor to an attribute so the field literally cites its entry.

    `dataclasses` exposes this through `fields(cls)[i].metadata["descriptor"]`
    and wraps it immutably, which is how the arithmetic parity suite reaches the
    storage metadata without this module publishing an accessor of its own.
    """
    return {"descriptor": descriptor}


# Defaults: derived from each descriptor, and never None
# Every one of the 29 columns is NOT NULL because the bridge `initialize`s its
# host-variable group before loading, so an unset COBOL field arrives as zero or
# as spaces (Agent Action Plan section 0.6.2). Both zeroes below are therefore
# derived from the descriptor rather than typed in.

def _zero(descriptor: FieldDescriptor) -> Decimal:
    """Build the zero of a numeric field, at the scale its descriptor reports.

    Built from the Decimal tuple form so the scale comes from the dictionary:
    a scale of 2 yields Decimal('0.00'), which is the value a NOT NULL
    decimal(10,2) column holds for an initialised COBOL field. No arithmetic and
    no re-scaling happens here; `cobol/arithmetic.py` owns storing values.
    """
    return Decimal((0, (0,), -(descriptor.scale or 0)))


def _spaces(descriptor: FieldDescriptor) -> str:
    """Build an alphanumeric field's initialised value: spaces at the declared width.

    Spaces rather than an empty string, because that is what a `char(n)` column
    holds for an initialised COBOL field, and the width is read from the
    descriptor's `character_length` rather than counted by eye. The bridge trims
    trailing spaces on the way out, and the harness step that makes two table
    dumps comparable owns padding for the state diff; nothing is trimmed or
    padded in this module.
    """
    return " " * (descriptor.character_length or 0)


# Each builder below returns the keyword arguments for `dataclasses.field`, and every
# attribute then spells `field(**...)` itself. Calling `field` directly at the
# attribute is the sanctioned form: it keeps the default expression a `dataclasses`
# construct rather than an opaque helper call, which is both what a reader of a
# dataclass expects and what static analysis can verify.


def _text_spec(cobol_name: str, locator: str) -> dict[str, object]:
    """Build the field arguments for an alphanumeric attribute, spaces-defaulted."""
    descriptor = _descriptor(cobol_name, locator)
    return {"default": _spaces(descriptor), "metadata": _metadata(descriptor)}


def _int_spec(cobol_name: str, locator: str) -> dict[str, object]:
    """Build the field arguments for an integer attribute - zoned DISPLAY or binary."""
    descriptor = _descriptor(cobol_name, locator)
    return {"default": 0, "metadata": _metadata(descriptor)}


def _dec_spec(cobol_name: str, locator: str) -> dict[str, object]:
    """Build the field arguments for an exact-decimal attribute, zero at its scale."""
    descriptor = _descriptor(cobol_name, locator)
    return {"default": _zero(descriptor), "metadata": _metadata(descriptor)}


def _group_spec(
    cobol_name: str, locator: str, factory: Callable[[], object]
) -> dict[str, object]:
    """Build the field arguments for a group attribute, built fresh per record.

    `default_factory` rather than `default`, so every record owns its own
    subordinate group and two records can never share one.
    """
    descriptor = _descriptor(cobol_name, locator)
    return {"default_factory": factory, "metadata": _metadata(descriptor)}


def _pturnover_zeroes() -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """Build the initialised `PTurnover-q ... occurs 4` view: four zeroes at scale 2.

    A fixed four-element tuple, matching the OCCURS count the dictionary records
    for [copybooks/wspl.cob:L51]. `Decimal` is immutable, so one zero object
    serves all four positions.
    """
    zero = _zero(_descriptor("PTurnover-q", _locator(51)))
    return (zero, zero, zero, zero)


# Condition names: carried as data, evaluated elsewhere
# Agent Action Plan section 0.4.1.4 assigns 88-level evaluation to
# `cobol/condition_names.py` - "88-level condition name -> Predicate function
# over the record". So the two names this record declares are surfaced here as
# metadata and nothing more: no predicate, no property, no enumeration. Their
# literal values stay strings exactly as written, "1" and "0" - NOT rewritten as
# the word `zero` that the Sales twin happens to use at
# [copybooks/wssl.cob:L27] for the same idea.

PURCH_STATUS_CONDITION_NAMES: Final[tuple[ConditionName, ...]] = (
    _ENTRIES[("Purch-Status", _locator(18))].copybook.condition_names
)
"""The two 88-levels on `Purch-Status` [copybooks/wspl.cob:L19-L20].

    Supplier-live  value 1   [copybooks/wspl.cob:L19]
    Supplier-dead  value 0   [copybooks/wspl.cob:L20]

Exactly two, where the Sales record declares eight condition names across six
flag fields - divergence register rows 4 and 8. Lower-case names here against
that record's mixed-case `Customer-Live` / `Customer-Dead`, and `value 0` here
against its `value zero`; both spellings stand as their copybooks write them.
"""


# The subordinate groups

@dataclass(slots=True)
class PurchAddress:
    """`03 Purch-Address.` [copybooks/wspl.cob:L23] - two lines, one column.

    The bridge concatenates this group into a single `HV-PURCH-ADDRESS PIC
    X(96)` [common/purchMT.cbl:L289] and the schema stores one `PURCH-ADDRESS
    char(96)`, so NEITHER child has a column of its own - drift KIND 3. Both are
    declared anyway: the copybook declares them, and R-3 forbids dropping a
    field as firmly as adding one. The generated dictionary records the parent's
    derivation as a group concatenation at [common/purchMT.cbl:L1216] and both
    children as one-sided copybook entries.
    """

    GROUP_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor(
        "Purch-Address", _locator(23)
    )
    """The group's own descriptor - usage GROUP, keyed on PULEDGER-REC.PURCH-ADDRESS."""

    # 05  Purch-Addr1     pic x(48).                      [copybooks/wspl.cob:L24]
    purch_addr1: str = field(**_text_spec("Purch-Addr1", _locator(24)))

    # 05  Purch-Addr2     pic x(48).                      [copybooks/wspl.cob:L25]
    purch_addr2: str = field(**_text_spec("Purch-Addr2", _locator(25)))


@dataclass(slots=True)
class Quarters:
    """`03 Quarters.` [copybooks/wspl.cob:L45] - the four quarterly turnover figures.

    Each child is `pic s9(8)v99 comp-3`: signed packed decimal, ten digits,
    scale 2, and each reaches its own signed `decimal(10,2)` column. Money keeps
    its sign at all three layers here, unlike the statistics fields.

    Two naming points are preserved rather than tidied. The children spell their
    quarter suffix with a LOWER-CASE q - `Turnover-q1` through `Turnover-q4` -
    where the columns are TURNOVER-Q1 through TURNOVER-Q4 and where the Sales
    copybook writes an upper-case Q [copybooks/wssl.cob:L57-L60]. And
    `copybooks/wssl.cob:L56` declares a group of this same COBOL name,
    `Quarters`, for the Sales record: the two are distinct records that happen
    to share a group name, kept apart by Python's module namespaces. THIS one is
    the Purchase group, from `copybooks/wspl.cob`.
    """

    GROUP_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor("Quarters", _locator(45))
    """The group's own descriptor - a one-sided copybook entry, usage GROUP."""

    # 05  Turnover-q1     pic s9(8)v99   comp-3.          [copybooks/wspl.cob:L46]
    turnover_q1: Decimal = field(**_dec_spec("Turnover-q1", _locator(46)))

    # 05  Turnover-q2     pic s9(8)v99   comp-3.          [copybooks/wspl.cob:L47]
    turnover_q2: Decimal = field(**_dec_spec("Turnover-q2", _locator(47)))

    # 05  Turnover-q3     pic s9(8)v99   comp-3.          [copybooks/wspl.cob:L48]
    turnover_q3: Decimal = field(**_dec_spec("Turnover-q3", _locator(48)))

    # 05  Turnover-q4     pic s9(8)v99   comp-3.          [copybooks/wspl.cob:L49]
    turnover_q4: Decimal = field(**_dec_spec("Turnover-q4", _locator(49)))


@dataclass(slots=True)
class QuartersView:
    """`03 filler redefines Quarters.` [copybooks/wspl.cob:L50] - the array view.

    A second view of the same four bytes-worth of storage that `Quarters`
    names individually, reached as a subscripted array instead:
    `05 PTurnover-q pic s9(8)v99 comp-3 occurs 4.` [copybooks/wspl.cob:L51].

    NAMING SCHEME, applied consistently for every unnamed `filler redefines
    <Group>` in this package: the class is `<Group>View`. The COBOL group itself
    has NO name - it is a `filler` - so there is nothing to transliterate, and
    the dictionary keys it as `WS-Purch-Record.filler#50`, disambiguated by
    declaration line. `records/gl_ledger.py` and `records/sales_ledger.py` face
    the identical shape and use the same rule; the rule is shared, no code is.

    Both views are present, in declaration order, and neither is designated the
    primary one. There is no accessor that switches between them and no property
    that hides the subscript: COBOL OCCURS subscripts are 1-BASED, so
    `PTurnover-q (1)` is `pturnover_q[0]` here, and that offset is stated rather
    than papered over. The Sales twin names its view `STurnover-Q` with an S
    prefix and an upper-case Q [copybooks/wssl.cob:L62] - divergence register
    row 11.

    Note that the bridge's own stale inline record buffer omits this redefines
    view entirely [common/purchMT.cbl:L358-L362]; the frozen copybook is what
    this module follows.
    """

    GROUP_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor("filler", _locator(50))
    """The unnamed redefining group's descriptor - is_filler and is_group both true."""

    # 05  PTurnover-q     pic s9(8)v99   comp-3 occurs  4. [copybooks/wspl.cob:L51]
    # A fixed four-element tuple, never a list: the OCCURS count is 4 and the
    # shape must not vary between runs (R-6).
    pturnover_q: tuple[Decimal, Decimal, Decimal, Decimal] = field(
        **_group_spec("PTurnover-q", _locator(51), _pturnover_zeroes)
    )


# The record

@dataclass(slots=True)
class WsPurchRecord:
    """`01 WS-Purch-Record.` [copybooks/wspl.cob:L13] - one supplier account.

    Twenty-nine attributes in the copybook's own declaration order, L14 through
    L54, which is NOT the Sales record's order: `Purch-Status` and
    `Purch-Notes-Tag` come BEFORE the name, `Purch-Fax` before `Purch-Email`,
    and `Purch-Create-Date` before the `Pay-*` trio rather than after it -
    divergence register rows 2, 3 and 6.

    Twenty-nine attributes, twenty-nine columns, but not the same twenty-nine:
    `Purch-Address` is one attribute and one column but two copybook children;
    `Purch-Stats-Date` and the trailing FILLER are attributes with no column;
    and `QuartersView` is a second view of `Quarters`, not extra storage. The
    arithmetic is shown in the module docstring.

    DELIBERATELY MUTABLE. Never frozen, and never snapshot-copied on assignment.
    `pl055`, `pl060` and `pl100` all update a supplier account in place, and the
    reasoning `records/irs_nominal.py` records applies here too: a frozen or
    copy-on-write record could make a lost-update defect impossible to express,
    and R-4 requires such defects stay reproducible rather than becoming
    unreachable.

    Nothing is checked, coerced, padded or scaled on construction. There is no
    hook after `__init__`, no bounds test on the credit limit, no shape test on
    the sort code, the account number or the e-mail address, and no test of
    either condition name - R-3 forbids adding validation that the COBOL does
    not perform, and the COBOL performs none here.
    """

    RECORD_DESCRIPTOR: ClassVar[FieldDescriptor] = _descriptor(
        "WS-Purch-Record", _locator(13)
    )
    """The 01 level's own descriptor, keyed `WS-Purch-Record.WS-Purch-Record`.

    A one-sided entry whose note records that it is "a group item whose
    subordinate items carry the values".
    """

    # 03  WS-Purch-Key        pic x(7).                   [copybooks/wspl.cob:L14]
    # The primary key. Its only drift is `name`: the column is PURCH-KEY, so the
    # WS- prefix is dropped at the bridge.
    # L15-L17 declare `filler redefines WS-Purch-Key` with `Array-k pic x
    # occurs 6` and `Check-Digit pic 9` - ALL THREE LINES COMMENTED OUT in the
    # frozen copybook. Neither name is modelled here and neither has a
    # dictionary entry. See the module docstring; the Sales twin's dead copy
    # spells it `Array-K`, with an upper-case K.
    ws_purch_key: str = field(**_text_spec("WS-Purch-Key", _locator(14)))

    # 03  Purch-Status        pic 9.                      [copybooks/wspl.cob:L18]
    #         88  Supplier-live               value 1.    [copybooks/wspl.cob:L19]
    #         88  Supplier-dead               value 0.    [copybooks/wspl.cob:L20]
    # Zoned DISPLAY, one digit, unsigned. The two condition names are surfaced as
    # data in PURCH_STATUS_CONDITION_NAMES; evaluating them belongs to
    # `cobol/condition_names.py`. Drift KIND 2b: one digit here, three at the
    # host variable [common/purchMT.cbl:L286], a `tinyint(1) unsigned` column.
    purch_status: int = field(**_int_spec("Purch-Status", _locator(18)))

    # 03  Purch-Notes-Tag     pic 9.                      [copybooks/wspl.cob:L21]
    # PREFIXED, where the Sales copybook declares a bare `Notes-Tag`
    # [copybooks/wssl.cob:L39]. Same KIND 2b digit widening as Purch-Status.
    purch_notes_tag: int = field(**_int_spec("Purch-Notes-Tag", _locator(21)))

    # 03  Purch-Name          pic x(30).                  [copybooks/wspl.cob:L22]
    # Declared AFTER the two flags, where the Sales record declares its name
    # first - divergence register row 2.
    purch_name: str = field(**_text_spec("Purch-Name", _locator(22)))

    # 03  Purch-Address.                                  [copybooks/wspl.cob:L23]
    # A GROUP of two 48-character children that the bridge concatenates into one
    # 96-character column - drift KIND 3. See PurchAddress.
    purch_address: PurchAddress = field(
        **_group_spec("Purch-Address", _locator(23), PurchAddress)
    )

    # 03  Purch-Phone         pic x(13).                  [copybooks/wspl.cob:L26]
    purch_phone: str = field(**_text_spec("Purch-Phone", _locator(26)))

    # 03  Purch-Ext           pic x(4).                   [copybooks/wspl.cob:L27]
    purch_ext: str = field(**_text_spec("Purch-Ext", _locator(27)))

    # 03  Purch-Fax           pic x(13).                  [copybooks/wspl.cob:L28]
    # FAX BEFORE E-MAIL here; the Sales record declares e-mail first
    # [copybooks/wssl.cob:L23-L24] - divergence register row 3.
    purch_fax: str = field(**_text_spec("Purch-Fax", _locator(28)))

    # 03  Purch-Email         pic x(30).                  [copybooks/wspl.cob:L29]
    purch_email: str = field(**_text_spec("Purch-Email", _locator(29)))

    # 03  Purch-Discount      pic 99v99      comp.    *> RDB comp-3
    #                                                     [copybooks/wspl.cob:L30]
    # DECIMAL, not int: this is the second direction of the two-direction rule -
    # a COMP usage WITH a V in its picture, so four digits at scale 2, unsigned.
    # THE DECLARATION GOVERNS AND THE COMMENT IS STALE. The inline `*> RDB
    # comp-3` claims packed decimal; the line declares COMP. The bridge records
    # why, at [common/purchMT.cbl:L343]: "11/07/23 was comp-3 now matches
    # wspl.cob". Fittingly, this is the ONE field in the whole record that
    # carries no drift flag at all - it agrees across copybook, host variable
    # [common/purchMT.cbl:L294] and column. Its Sales counterpart
    # [copybooks/wssl.cob:L42] declares the same picture with no such comment.
    purch_discount: Decimal = field(**_dec_spec("Purch-Discount", _locator(30)))

    # 03  Purch-Credit        binary-char.  *> were pic 99
    #                                                     [copybooks/wspl.cob:L31]
    # int: a SIGNED 8-BIT integer with no picture, so no fractional positions.
    # The `*> were pic 99` is history, not a type - the `99` in it is not a digit
    # count. The Sales twin really is `pic 99` [copybooks/wssl.cob:L41], a zoned
    # DISPLAY field - divergence register row 7.
    # DRIFT KIND 2, a three-way width disagreement in two directions: 8-bit
    # signed here, 8 digits unsigned at [common/purchMT.cbl:L295] - a widening -
    # and a `mediumint(2) unsigned` column - a narrowing. Reported unsettled;
    # the `acas022` handler module owns the conversion.
    purch_credit: int = field(**_int_spec("Purch-Credit", _locator(31)))

    # 03  Purch-SortCode      binary-long. *> all these were pic 9(8) comp
    #                                                     [copybooks/wspl.cob:L32]
    # int: SIGNED 32-BIT, no picture, scale 0. The inline comment covers the
    # whole L32-L42 run and is history; the `9(8)` in it is not a digit count.
    # DRIFT KIND 2 again, and the sharper case: 32-bit signed here, 8 digits at
    # [common/purchMT.cbl:L296], and a `mediumint(6) unsigned` column that is
    # NARROWER THAN BOTH. A UK sort code is six digits, so the column is apt and
    # is the tightest of the three layers - which is why the oracle question in
    # the module docstring has to measure overflow as well as sign.
    # Absent from the Sales record entirely - divergence register row 5.
    purch_sortcode: int = field(**_int_spec("Purch-SortCode", _locator(32)))

    # 03  Purch-Accountno     binary-long.                [copybooks/wspl.cob:L33]
    # Signed 32-bit -> unsigned `PIC 9(10) COMP` [common/purchMT.cbl:L297] ->
    # unsigned column. Drift KIND 1. Absent from the Sales record - row 5.
    purch_accountno: int = field(**_int_spec("Purch-Accountno", _locator(33)))

    # 03  Purch-Limit         binary-long.                [copybooks/wspl.cob:L34]
    # The credit limit. Signed here, unsigned at [common/purchMT.cbl:L298] and at
    # the column - drift KIND 1. No limit test is performed anywhere in this
    # module; the COBOL performs none on the record.
    purch_limit: int = field(**_int_spec("Purch-Limit", _locator(34)))

    # 03  Purch-Activety      binary-long.                [copybooks/wspl.cob:L35]
    # MISSPELLED IN THE SOURCE and carried verbatim - the host variable is
    # HV-PURCH-ACTIVETY [common/purchMT.cbl:L299] and the column is
    # PURCH-ACTIVETY, so amending the spelling would break the dictionary key.
    # int, NOT Decimal. This is the counter that `purch-comp` steps at
    # [purchase/pl060.cbl:L749] before forming the running figure, and that
    # `credit-comp` NEVER steps [purchase/pl060.cbl:L755-L766] - anomalies A-8
    # and A-9. Both sections write this same field rather than a separate credit
    # counter. Typing it Decimal would let the remainder survive and quietly
    # repair both defects.
    purch_activety: int = field(**_int_spec("Purch-Activety", _locator(35)))

    # 03  Purch-Last-inv      binary-long.                [copybooks/wspl.cob:L36]
    # LOWER-CASE tail segment where every neighbour is capitalised; the column is
    # PURCH-LAST-INV. Date-like, and it touches no clock. Drift KIND 1.
    purch_last_inv: int = field(**_int_spec("Purch-Last-inv", _locator(36)))

    # 03  Purch-Last-pay      binary-long.                [copybooks/wspl.cob:L37]
    # Same lower-case tail; the column is PURCH-LAST-PAY. Drift KIND 1.
    purch_last_pay: int = field(**_int_spec("Purch-Last-pay", _locator(37)))

    # 03  Purch-Average       binary-long.                [copybooks/wspl.cob:L38]
    # int, NOT Decimal - the single most consequential type in this module.
    # The quotient statements at [purchase/pl060.cbl:L751] and [:L766] write this
    # field, and because it is a scale-0 binary integer both are INTEGER
    # division that discards the remainder. That truncation, together with the
    # accumulator it is formed from, is anomaly A-8's double truncation.
    # Drift KIND 1: signed here, unsigned at [common/purchMT.cbl:L302].
    purch_average: int = field(**_int_spec("Purch-Average", _locator(38)))

    # 03  Purch-Create-Date   binary-long.                [copybooks/wspl.cob:L39]
    # POSITION 8 of the eleven `binary-long` items - BEFORE the Pay-* trio -
    # where the Sales record declares its create date LAST, after them
    # [copybooks/wssl.cob:L53]. Divergence register row 6.
    # DRIFT KIND 4, name truncation: HV-PURCH-CREATE-DAT
    # [common/purchMT.cbl:L303] and the column PURCH-CREATE-DAT both drop the
    # trailing E. The bridge's inline buffer records the reason at
    # [common/purchMT.cbl:L352]: "chg name 4 SQL Mig." This field carries three
    # drift flags - signedness, usage and name - more than any other here.
    # Date-like, and it touches no clock.
    purch_create_date: int = field(**_int_spec("Purch-Create-Date", _locator(39)))

    # 03  Purch-Pay-Activety  binary-long.                [copybooks/wspl.cob:L40]
    # MISSPELLED IN THE SOURCE and carried verbatim, like L35. int, NOT Decimal:
    # this is the counter stepped at [purchase/pl100.cbl:L501], guarded by the
    # ONE-condition test at [:L497] that is the third of the three disagreeing
    # guard variants - anomaly A-10.
    purch_pay_activety: int = field(**_int_spec("Purch-Pay-Activety", _locator(40)))

    # 03  Purch-Pay-Average   binary-long.                [copybooks/wspl.cob:L41]
    # int, NOT Decimal. Written by the quotient statement at
    # [purchase/pl100.cbl:L502], which spells its operands in the REVERSED order
    # - `by` where [purchase/pl060.cbl:L751] writes `into`. The reversal is
    # textual, and it is preserved exactly rather than harmonised; the program
    # module owns it.
    purch_pay_average: int = field(**_int_spec("Purch-Pay-Average", _locator(41)))

    # 03  Purch-Pay-Worst     binary-long.                [copybooks/wspl.cob:L42]
    # int. The worst-payment-days watermark, stepped only upward at
    # [purchase/pl100.cbl:L504-L505]. Last of the eleven `binary-long` items.
    purch_pay_worst: int = field(**_int_spec("Purch-Pay-Worst", _locator(42)))

    # 03  Purch-Current       pic s9(8)v99   comp-3.      [copybooks/wspl.cob:L43]
    # Signed packed decimal, ten digits, scale 2 -> `PIC S9(08)V9(02) COMP`
    # [common/purchMT.cbl:L307] -> a signed `decimal(10,2)` column. A CLEAN
    # PASS-THROUGH: only the storage class changes (KIND 2c); sign, digits and
    # scale agree at all three layers. Money keeps its sign.
    purch_current: Decimal = field(**_dec_spec("Purch-Current", _locator(43)))

    # 03  Purch-Last          pic s9(8)v99   comp-3.      [copybooks/wspl.cob:L44]
    # Clean pass-through, as L43. Host variable at [common/purchMT.cbl:L308].
    purch_last: Decimal = field(**_dec_spec("Purch-Last", _locator(44)))

    # 03  Quarters.                                       [copybooks/wspl.cob:L45]
    # The four named quarterly figures. See Quarters.
    quarters: Quarters = field(
        **_group_spec("Quarters", _locator(45), Quarters)
    )

    # 03  filler redefines Quarters.                      [copybooks/wspl.cob:L50]
    # The array view of the same four figures. Present in declaration order,
    # immediately after the group it redefines; neither view is designated the
    # primary one. See QuartersView.
    quarters_view: QuartersView = field(
        **_group_spec("filler", _locator(50), QuartersView)
    )

    # 03  Purch-Unapplied     pic s9(8)v99   comp-3.      [copybooks/wspl.cob:L52]
    # Clean pass-through, as L43-L44. Host variable at [common/purchMT.cbl:L313],
    # the last of the twenty-nine.
    purch_unapplied: Decimal = field(**_dec_spec("Purch-Unapplied", _locator(52)))

    # 03  Purch-Stats-Date  pic 9(4).  *> added 15/01/18.  [copybooks/wspl.cob:L53]
    # A NEW ANOMALY: this field reaches NO host variable and NO column. Neither HV-PURCH-STATS
    # nor PURCH-STATS occurs in common/purchMT.cbl or mysql/ACASDB.sql, bb000-HV-Load
    # [common/purchMT.cbl:L1203] loads twenty-nine fields and not this one, and the dictionary
    # entry is one-sided. It IS declared again in the bridge's stale inline buffer
    # [common/purchMT.cbl:L364], and mapped from neither.
    # THE ASYMMETRY IS THE EVIDENCE OF ACCIDENT: the Sales copybook added the identical field on
    # the identical date with the identical comment [copybooks/wssl.cob:L64], and there it DID
    # gain a host variable [common/salesMT.cbl:L320] and a column [mysql/ACASDB.sql:L981].
    # Declared here regardless (R-3), keyed on `WS-Purch-Record.Purch-Stats-Date`. Raised as a
    # new anomaly-log entry, and as an open question because a value written here is invisible
    # in every table dump. Zoned DISPLAY, four digits, scale 0, unsigned.
    purch_stats_date: int = field(**_int_spec("Purch-Stats-Date", _locator(53)))

    # 03  filler              pic x(12).                  [copybooks/wspl.cob:L54]
    # The trailing FILLER, declared rather than skipped: it is part of the 302
    # declared bytes and R-3 forbids dropping it. It reaches no column, which is
    # one of the three subtractions in the 29-column arithmetic.
    # NAMING SCHEME: `filler_l<line>`. The COBOL name is simply `filler`, which
    # `copybooks/wspl.cob` uses twice - at L50 for the redefining group, modelled
    # as QuartersView, and here at L54 - so the declaration line is what
    # separates them. The dictionary does exactly the same thing, keying them
    # `filler#50` and `filler#54`, so this scheme mirrors the artifact rather
    # than inventing a convention. The Sales record has TWO alphanumeric fillers,
    # `pic xxx` and `pic x(5)` [copybooks/wssl.cob:L40, L68], against this one -
    # divergence register row 9.
    filler_l54: str = field(**_text_spec("filler", _locator(54)))
