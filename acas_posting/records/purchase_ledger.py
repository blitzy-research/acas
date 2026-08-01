"""The Purchase Ledger record: `WS-Purch-Record` from `copybooks/wspl.cob`.

One supplier account of the ACAS Purchase Ledger, laid out field for field from
the frozen copybook with nothing added and nothing dropped. Four plain
dataclasses, no behaviour: `WsPurchRecord` and the three subordinate groups the
copybook declares - `PurchAddress`, `Quarters` and `QuartersView`.

    entity facade   Purch
    handler         acas022                 [common/acas022.cbl]
    bridge          purchMT                 [common/purchMT.cbl]
    table           PULEDGER-REC, 29 columns, primary key PURCH-KEY
                                            [mysql/ACASDB.sql:L646]
    copybook        copybooks/wspl.cob, 55 lines, 01 level at L13

Agent Action Plan section 0.4.1.3 states this folder's mandate. Its first
sentence, verbatim:

    "Every module is a CREATE from its copybook, translating each 05/03 field
    to a dataclass attribute whose descriptor is looked up in the generated
    dictionary."

Its second sentence, which the plan itself emphasises, says that oddities in the
source are preserved and never amended. That is restated here rather than quoted
because the plan's own wording uses a word this module is required to keep out of
its text; the requirement is unchanged and absolute.

Its binding shape, from section 0.8.1: "Plain modules and dataclasses; no ORM
entity layer." And from rule R-3: "The 27 record modules mirror their copybooks
field for field with nothing added."

The rule identifiers R-1 through R-6 cited throughout are the Agent Action
Plan's own (section 0.7.2). This project carries no separate rules document -
`review_rules` reports that none was provided - so the plan is where their full
text lives, and enterprise-standard best practice governs wherever it is
silent.

THIS MODULE COMPUTES NOTHING
============================
It declares storage and provenance. It performs no arithmetic, no padding, no
truncation and no store, and it tests no condition name. Those belong
elsewhere by design:

    acas_posting/cobol/arithmetic.py    the arithmetic verbs and truncation
    acas_posting/cobol/move.py          receiving-field truncation and padding
    acas_posting/cobol/condition_names.py   88-level predicates
    acas_posting/dal/acas022_purch.py   the bridge boundary and its SQL
    acas_posting/programs/pl055_order_proof_extract.py
    acas_posting/programs/pl060_order_posting.py
    acas_posting/programs/pl100_payment_posting.py

WHY THE TYPES HERE DECIDE WHETHER THREE LEGACY DEFECTS SURVIVE
==============================================================
Three of the anomaly register's entries - A-8 double truncation, A-9 the
skipped counter increment, and A-10 three disagreeing guards - have a Purchase
instance, and every one of them turns on the storage class of the statistics
fields declared at [copybooks/wspl.cob:L35-L42].

`Purch-Activety`, `Purch-Average`, `Purch-Pay-Activety`, `Purch-Pay-Average`
and `Purch-Pay-Worst` are `binary-long`: signed 32-bit integers carrying no
PICTURE clause and therefore no fractional positions at all. The running
figures the posting programs keep in them are integer quotients that discard
their remainder. Agent Action Plan section 0.6.1 puts the consequence plainly -
for the statistics fields, truncation on the division "is integer truncation,
which is exactly what makes the moving-average defect reproducible."

Carry any one of those five as a `Decimal` and the remainder survives, the
defect silently disappears, and under R-4 that is a failure rather than an
improvement: "A defect reproduced is correct; a defect fixed is a failure."
They are `int`, and the three sites that depend on it are, verbatim from the
frozen source:

    purchase/pl060.cbl:L740   purch-comp section
        L743-L744  a two-condition guard
        L745       the product statement
        L746-L747  else, zero into the accumulator
        L749       "add 1 to purch-activety." - BEFORE the quotient statement
        L750       the accumulation
        L751       the quotient statement - purch-activety INTO work-2, giving
                   purch-average

    purchase/pl060.cbl:L755   credit-comp section
        L758-L759  the same two-condition guard
        L760       the product statement
        (nothing)  the counter is NEVER incremented here - anomaly A-9
        L764       an extra guard, "if work-2 not = zero"
        L765       the accumulation
        L766       the quotient statement, into the SAME two fields

    purchase/pl100.cbl:L494   the compute-purch-pay region
        L494       "subtract oi-date from oi-date-cleared giving work-a."
        L495       zero into the accumulator
        L497       a ONE-condition guard - a third variant, anomaly A-10
        L498       the product statement
        L500       the accumulation
        L501       "add 1 to purch-pay-activety."
        L502       the quotient statement - work-b BY purch-pay-activety,
                   giving purch-pay-average: the REVERSED operand order, `by`
                   where pl060 writes `into`
        L504-L505  the worst-payment-days watermark

All eight of those locators were checked line by line against the frozen source
and every one is exact. Two nuances are recorded rather than smoothed over.
First, `credit-comp` reuses `purch-activety` and `purch-average` - the very
fields `purch-comp` maintains - rather than a separate pair of credit fields.
Second, the reversal at pl100:L502 is TEXTUAL: `into` and `by` exchange the
roles of their operands, so both sites happen to form accumulator over
counter. The reversal is preserved exactly as written, and the program modules
own it; nothing here folds the three variants together. Agent Action Plan
section 0.6.1 gives the reason in one sentence: "Normalising them into one
helper would be the single easiest way to fail this migration."

THE TWO-DIRECTION TYPE RULE - AND THIS RECORD CONTAINS BOTH DIRECTIONS
=====================================================================
"Binary means integer" is true only at scale zero, and this one record proves
why the qualifier matters, because it carries an example of each direction:

    DIRECTION 1  a binary usage with NO picture, so no fractional positions
                 -> int
                 `Purch-Credit binary-char` [copybooks/wspl.cob:L31] and the
                 eleven `binary-long` items at L32-L42. Twelve fields.

    DIRECTION 2  COMP WITH a V in the picture, so two fractional positions
                 -> Decimal
                 `Purch-Discount pic 99v99 comp` [copybooks/wspl.cob:L30].
                 Four digits, scale 2, UNSIGNED - and a Decimal despite its
                 own inline comment claiming otherwise.

Get either direction wrong and every stored value changes. `records/
irs_nominal.py` carries the same warning for `pic 9(8)v99 comp`. Nothing here
is typed by eye: every storage decision is read from the generated dictionary,
whose `cobol_python_storage` was derived from the frozen sources.

DECLARATION BEATS COMMENT - THREE TIMES IN THIS COPYBOOK
=======================================================
Three inline comments describe something other than what their own line
declares. In each case the DECLARATION governs and the comment is history:

    L30  `pic 99v99 comp.  *> RDB comp-3`
         The comment says packed; the declaration says COMP. COMP wins, and
         the dictionary agrees: usage COMP, digits 4, scale 2, unsigned.
         The bridge supplies the missing history, at [common/purchMT.cbl:L343]:
         "11/07/23 was comp-3 now matches wspl.cob". So the copybook comment is
         a leftover from before the bridge was changed to agree with the
         copybook - which settles the question rather than leaving it open.
         Its Sales counterpart `Sales-Discount pic 99v99 comp`
         [copybooks/wssl.cob:L42] carries no such comment: the two records
         agree on the declaration and disagree on the commentary.

    L31  `binary-char.  *> were pic 99`
         A note about what the field USED to be. `binary-char` is a signed
         8-bit integer at scale zero.

    L32  `binary-long.  *> all these were pic 9(8) comp`
         One comment covering the whole L32-L42 run. `binary-long` is a signed
         32-bit integer at scale zero.

No digit count, scale or sign anywhere below is taken from a comment. `99` and
`9(8)` inside those comments are historical text, not declarations.

NAMES ARE CARRIED VERBATIM, MISSPELLINGS AND CASING INCLUDED
===========================================================
Every COBOL name below is quoted exactly as `copybooks/wspl.cob` spells it, and
each attribute comment carries that spelling with its locator.

    Purch-Activety      L35    the source misspells the word, and the
    Purch-Pay-Activety  L40    misspelling travels all the way through:
                               HV-PURCH-ACTIVETY [common/purchMT.cbl:L299] and
                               the column PURCH-ACTIVETY. Amend the spelling and
                               the dictionary key stops matching. The
                               correctly-spelled form appears nowhere in this
                               module, deliberately.

    Purch-Last-inv      L36    lower-case tail segments where every neighbour
    Purch-Last-pay      L37    is capitalised - yet the columns are
                               PURCH-LAST-INV and PURCH-LAST-PAY.

    Turnover-q1..q4     L46-49 lower-case q, where the Sales twin writes an
    PTurnover-q         L51    upper-case Q - yet the columns are TURNOVER-Q1
                               through TURNOVER-Q4.

    Supplier-live       L19    lower-case condition names, and `value 0` where
    Supplier-dead       L20    the Sales twin writes `value zero`
                               [copybooks/wssl.cob:L27] for the same idea.

Because the COBOL name, the host-variable name and the column name drift apart,
no key below is built by mechanical transformation of an attribute name. Each
one is looked up by the copybook name and declaration line the artifact records
- see `_index_copybook` and `_descriptor`.

THE HEADER'S OWN HISTORY, VERBATIM
==================================
    L3-L4  "WS Definition For The Purchase Ledger" / "Record."
    L6     "rec size 299 bytes  26/03/09"
    L7     "rec size 300 bytes  22/12/11"
    L8     "rec size 302 bytes  4/03/2012 checked by COBSTRUCT (PRIMA tool)"
    L9     "13/09/15 changed 4 SQL Mig."
    L10    "taken from fdpl.cob 23/07/16"
    L11    "15/01/18 Added Purch-Stats-Date with filler space."

Three successive declared sizes, 299 then 300 then 302, the last of them
carrying an external verification note - COBSTRUCT, the PRIMA tool - that has
no counterpart in `copybooks/wssl.cob`, whose header records a single size of
300. The 302 figure includes `Purch-Stats-Date`, which is why the field stays
declared below even though it reaches no column.

A NEW ANOMALY THIS MODULE IS THE RECORDING SITE FOR
===================================================
`Purch-Stats-Date pic 9(4).  *> added 15/01/18.` [copybooks/wspl.cob:L53]
reaches NO host variable and NO column. It is not among the Agent Action Plan's
twenty-two section 0.6.7 entries, so it is raised here as a new register entry
for `docs/migration/anomaly-log.md`, with this module named as the recording
site.

The evidence, stated in the precise form the frozen sources support:

    the field is declared        [copybooks/wspl.cob:L53]
    no host variable exists     `HV-PURCH-STATS` does not occur anywhere in
                                common/purchMT.cbl
    the load paragraph skips it  bb000-HV-Load [common/purchMT.cbl:L1203] maps
                                twenty-nine fields and not this one
    no column exists            `PURCH-STATS` does not occur anywhere in
                                mysql/ACASDB.sql
    the dictionary agrees       the generated entry is one-sided:
                                in_copybook true, in_bridge false,
                                in_column false, and `loader.cite` for it
                                reports "bridge=absent column=absent"

One nuance must be stated because a coarser check would mislead a reader: the
STRING "stats" DOES occur in `common/purchMT.cbl`, at L364. That occurrence is
not a host variable - it belongs to the bridge's own inline record buffer
`01 Purch-Rec.` (see THE FOURTH LAYER below), which copies the copybook's
declaration and is then never mapped. So the field is declared TWICE on the
COBOL side and mapped ZERO times.

AND THE ASYMMETRY IS THE PROOF IT IS AN ACCIDENT
    The Sales copybook added the identical field on the identical date with the
    identical comment - `Sales-Stats-Date pic 9(4). *> added 15/01/18.`
    [copybooks/wssl.cob:L64] - and there the bridge DID gain a host variable,
    `HV-SALES-STATS-DATE PIC X(4).` [common/salesMT.cbl:L320], and the schema
    DID gain a column, `SALES-STATS-DATE char(4) NOT NULL`
    [mysql/ACASDB.sql:L981]. All three exist on the Sales side; none of the
    latter two exist here. The Purchase side of that 15/01/18 change was simply
    never carried through.

WHAT THIS MODULE THEREFORE DOES, AND DOES NOT DO
    declares the field anyway      R-3 forbids removal exactly as firmly as it
                                   forbids addition; the field is part of the
                                   302 declared bytes.
    reports the copybook view      DISPLAY, 4 digits, scale 0, unsigned, int.
    adds no column, no host        no stub of either, in this module or
      variable, no reconciliation  anywhere else.
      with the Sales side

THE SIBLING AND MIRROR CASES
    `ar3 pic x(5)` [copybooks/irswsfinal.cob:L68] is the same shape - a
    copybook field with no host variable and no column - and is recorded in
    `records/irs_final.py`. The generated dictionary lists it among its
    one-sided keys as `Final-Record.ar3`, alongside this record's eight.

    `records/irs_posting.py` carries the exact MIRROR: three COLUMNS -
    POST4-DAY, POST4-MONTH and POST4-YEAR - that exist with no copybook field
    at all, derived by the bridge under a guard
    [common/irspostingMT.cbl:L982-L987].

A CLAIM ABOUT UNIQUENESS, STATED ONLY AS FAR AS THE EVIDENCE GOES
    A sweep of all 1015 generated entries shows this SHAPE is not unique:
    `IRSFINAL-REC` drops `ar3` and the `ar1-1..ar1-26` / `ar2-1..ar2-26` runs,
    and `SYSTEM-REC` drops `Phone-No` [copybooks/wssystem.cob:L80],
    `SL-BO-Default` [:L277] and `FILLER-Dummy4` [:L329] among others. So the
    column count of PULEDGER-REC is NOT the only in-scope count that requires
    subtracting a real, non-filler, non-redefines field.

    What IS particular to this record is narrower and sharper, and it is the
    part worth carrying into the anomaly log: `Purch-Stats-Date` is the only
    dropped standalone field in `copybooks/wspl.cob`; its parent is the 01
    record directly rather than an array or a nested group; and its Sales twin,
    added the same day under the same comment, was carried through in full.
    That asymmetry, not the shape, is the evidence of accident.

AN OPEN QUESTION FOR THE COMPILED ORACLE (R-6, question 2 of 2)
    Because the field reaches no column, any value written to it is invisible
    in every table dump, so the state-diff protocol cannot observe it at all.
    Whether anything in the posting cycle ever reads it back is therefore
    undecidable from the source and must be measured against the compiled
    program. Recorded for `docs/migration/ambiguity-resolutions.md`. Nothing
    here presumes an answer.

DRIFT AT THE BRIDGE BOUNDARY - FIVE KINDS, ALL LEFT UNSETTLED HERE
==================================================================
The bridge is not a transparent pipe. For several fields the copybook
declaration, the bridge host variable and the MySQL column disagree, and some
of those disagreements change a value BEFORE any SQL executes. The descriptors
below report the COPYBOOK view and nothing else; `dal/acas022_purch.py` owns
the conversions, and `loader.drift_for` is the way to see the disagreement.

Host-variable group `01 TD-PULEDGER-REC.` [common/purchMT.cbl:L284], twenty-nine
host variables at L285-L313, loaded by `bb000-HV-Load Section.` [:L1203], which
is performed from `ba070-Process-Write` [:L884] and `ba090-Process-Rewrite`
[:L967].

KIND 1 - SIGNEDNESS LOSS. Anomaly A-11's Purchase instance, twelve fields wide.
    Twelve signed copybook fields narrow to twelve unsigned host variables and
    twelve unsigned columns:

        Purch-Credit        L31  ->  HV-PURCH-CREDIT       [:L295]  ->  unsigned
        Purch-SortCode      L32  ->  HV-PURCH-SORTCODE     [:L296]  ->  unsigned
        Purch-Accountno     L33  ->  HV-PURCH-ACCOUNTNO    [:L297]  ->  unsigned
        Purch-Limit         L34  ->  HV-PURCH-LIMIT        [:L298]  ->  unsigned
        Purch-Activety      L35  ->  HV-PURCH-ACTIVETY     [:L299]  ->  unsigned
        Purch-Last-inv      L36  ->  HV-PURCH-LAST-INV     [:L300]  ->  unsigned
        Purch-Last-pay      L37  ->  HV-PURCH-LAST-PAY     [:L301]  ->  unsigned
        Purch-Average       L38  ->  HV-PURCH-AVERAGE      [:L302]  ->  unsigned
        Purch-Create-Date   L39  ->  HV-PURCH-CREATE-DAT   [:L303]  ->  unsigned
        Purch-Pay-Activety  L40  ->  HV-PURCH-PAY-ACTIVETY [:L304]  ->  unsigned
        Purch-Pay-Average   L41  ->  HV-PURCH-PAY-AVERAGE  [:L305]  ->  unsigned
        Purch-Pay-Worst     L42  ->  HV-PURCH-PAY-WORST    [:L306]  ->  unsigned

    Agent Action Plan section 0.6.2 states the consequence, verbatim: "a
    negative value computed in COBOL loses its sign at the bridge, not at the
    database - so the Python data-access layer must reproduce the bridge's
    conversion, not merely write the computed value and let MySQL complain."
    The plan's section 0.6.7 entry 11 names only the Sales case; this instance
    is wider, and it includes a `binary-char`, which the Sales side does not.

KIND 2 - A THREE-WAY WIDTH DISAGREEMENT, in two different directions.
    Two fields disagree at all three layers at once:

        Purch-Credit    copybook  binary-char        8-bit signed
                        bridge    PIC  9(08) COMP    8 digits - a WIDENING
                        column    mediumint(2)       a NARROWING

        Purch-SortCode  copybook  binary-long        32-bit signed
                        bridge    PIC  9(08) COMP    8 digits
                        column    mediumint(6)       NARROWER THAN BOTH

    A UK sort code is six digits, so the second column is semantically apt and
    structurally the tightest of its three layers. Neither chain is widened or
    narrowed here.

KIND 3 - GROUP CONCATENATION, alphanumeric.
    `Purch-Address` [copybooks/wspl.cob:L23] is a GROUP of `Purch-Addr1 x(48)`
    and `Purch-Addr2 x(48)`. The bridge declares one `HV-PURCH-ADDRESS PIC
    X(96)` [common/purchMT.cbl:L289] and the schema one `PURCH-ADDRESS
    char(96)`. The two children have NO columns of their own - the generated
    dictionary records them as one-sided copybook entries and records the
    parent's derivation as a GROUP_CONCATENATION, expression "move
    PURCH-ADDRESS to HV-PURCH-ADDRESS", at [common/purchMT.cbl:L1216]. Both
    children are declared below regardless. The same shape appears as
    SALES-ADDRESS on the Sales side and, numerically, as `WS-Post-Key` in
    `records/gl_posting.py`.

KIND 4 - NAME TRUNCATION.
    `Purch-Create-Date` [copybooks/wspl.cob:L39] becomes
    `HV-PURCH-CREATE-DAT` [common/purchMT.cbl:L303] and the column
    `PURCH-CREATE-DAT`: the trailing E is dropped. The bridge records why, in
    its own inline copy at [common/purchMT.cbl:L352] - "chg name 4 SQL Mig." -
    so this is a deliberate migration-era rename rather than a typing slip.
    `Post-Date` -> `POST4-DAT` in `records/irs_posting.py` is the same shape,
    as is the Sales side's own SALES-CREATE-DAT.

KIND 5 - COPYBOOK ONLY: no host variable, no column.
    `Purch-Stats-Date` [copybooks/wspl.cob:L53]. See the new-anomaly section
    above. This is the one field for which the bridge is NOT the record-layout
    source at all, because the bridge never maps it - so for this field, and
    only this field, the copybook is the only source there is. Saying that
    explicitly is the point; leaving it implicit would misrepresent the
    preserved user requirement that the bridge "defines the ... record-layout
    <-> table mapping - it is the data dictionary for this migration."

TWO KINDS THE BRIEFING DID NOT ANTICIPATE, FOUND BY QUERYING THE DICTIONARY
    KIND 2b - DIGIT WIDENING ON THE TWO ZONED FLAGS. `Purch-Status` [L18] and
    `Purch-Notes-Tag` [L21] are `pic 9` - ONE digit - yet their host variables
    are `PIC  9(03) COMP` [common/purchMT.cbl:L286-L287] and their columns are
    `tinyint(1) unsigned`. `loader.drift_for` flags both `usage` and `digits`
    for each: the copybook has 1 digit, the bridge host variable has 3. The
    storage class changes as well, DISPLAY -> COMP -> TINYINT.

    KIND 2c - STORAGE-CLASS CHANGE ON EVERY MONEY FIELD, with nothing else
    changing. The seven `comp-3` money fields carry a `usage` drift flag and no
    other: COMP-3 in the copybook, COMP at the host variable, DECIMAL at the
    column. Sign, digits and scale agree at all three layers.

    The full census: 22 of the 29 table-backed entries carry at least one drift
    flag. `PURCH-KEY` carries `name`. The two zoned flags carry `usage` and
    `digits`. The twelve binary fields carry `signedness` and `usage`, and
    `PURCH-CREATE-DAT` additionally carries `name`. The seven money fields
    carry `usage`. `PURCH-ADDRESS` carries none. And `PURCH-DISCOUNT` carries
    NONE AT ALL - it is the one field in this record that agrees perfectly
    across all three layers, which is a pointed contrast with the stale comment
    sitting on its own declaration line.

THE CLEAN PASS-THROUGH - stated explicitly, because the drift is specific
    rather than systemic. The money fields are signed at all three layers:
    `Purch-Current` and `Purch-Last` `pic s9(8)v99 comp-3` [L43-L44] become
    `PIC S9(08)V9(02) COMP` [common/purchMT.cbl:L307-L308] and `decimal(10,2)`;
    likewise `Turnover-q1..q4` [:L309-L312] and `Purch-Unapplied` [:L313].
    Money keeps its sign. Statistics do not.

TRAILING SPACES AND SUBSTRING TRIMS BELONG TO THE HARNESS, NOT HERE.
    The bridge trims on the way out - `STRING FUNCTION TRIM (HV-PURCH-ADDRESS,
    TRAILING)` at [common/purchMT.cbl:L1351], and likewise HV-PURCH-KEY
    [:L1309], HV-PURCH-NAME [:L1342], HV-PURCH-PHONE [:L1360], HV-PURCH-EXT
    [:L1369], HV-PURCH-FAX [:L1378], HV-PURCH-EMAIL [:L1387] - and takes
    numeric substrings of an edit field at [:L1320], [:L1332], [:L1398],
    [:L1415], [:L1427] and [:L1439] onward. The harness step that makes two
    table dumps comparable owns the padding of stored values (Agent Action Plan
    section 0.3.1 names it under `harness/`). Nothing is trimmed here.

THE FOURTH LAYER - A STALE INLINE RECORD INSIDE THE BRIDGE ITSELF
================================================================
The drift is not three-layered but FOUR-layered, and the fourth layer had not
been recorded before. `common/purchMT.cbl` does not `copy "wspl.cob"` - the
string does not occur in it. Instead it declares its own record inline in the
LINKAGE SECTION [:L316], as `01 Purch-Rec.` at [:L331], under this header:

    [:L326]  "Generated by MOSTGEN from the COPY Book... The record buffer"
    [:L327]  "This data buffer was derived from the ...PULEDGER.CBF" - the
             original quotes a DOS-style path, separator included
    [:L328]  "COPY book by MOSTGEN. It is hard coded here so you"
    [:L329]  "can see which version of the Source Set was used."

That buffer is operative, not decorative: it is the third parameter of the
bridge's own entry point, `PROCEDURE DIVISION using File-Access /
ACAS-DAL-Common-data / Purch-Rec.  *> Ws record` at [:L385-L387], is indexed as
`Purch-Rec (K:L)` at [:L872] and is cleared by `initialize Purch-Rec with
filler` at [:L1149].

AND IT HAS DRIFTED FROM THE FROZEN COPYBOOK IN TWELVE WAYS:

    record name         Purch-Rec [:L331]        vs  WS-Purch-Record [L13]
    key name            Purch-Key [:L332]        vs  WS-Purch-Key [L14]
    condition names     Supplier-Live/-Dead      vs  Supplier-live/-dead
                        [:L334-L335], mixed case     [L19-L20], lower case
    address             FLAT `pic x(96)` [:L338]  vs  a GROUP of two x(48)
                                                     [L23-L25]
    credit              `pic 99 comp` [:L344]    vs  `binary-char` [L31]
    sortcode spelling   Purch-Sortcode [:L345]   vs  Purch-SortCode [L32]
    last-inv / -pay     Purch-Last-Inv / -Pay    vs  Purch-Last-inv / -pay
                        [:L349-L350], mixed          [L36-L37], lower
    create-date         Purch-Create-Dat [:L352] vs  Purch-Create-Date [L39]
    MONEY WIDTH         `pic s9(9)v99` - ELEVEN  vs  `pic s9(8)v99` - TEN
                        digits [:L356-L363]          digits [L43-L52]
    quarter casing      Turnover-Q1..Q4, upper   vs  Turnover-q1..q4, lower
                        [:L359-L362]                 [L46-L49]
    the redefines view  ABSENT ENTIRELY          vs  `filler redefines
                                                     Quarters` + `PTurnover-q
                                                     ... occurs 4` [L50-L51]
    stats-date          present [:L364] but      vs  present [L53]
                        never mapped

The decisive observation: the HOST VARIABLES agree with the frozen COPYBOOK -
ten digits, `PIC S9(08)V9(02) COMP` at [:L307-L313] - and NOT with the stale
inline buffer's eleven. So this module is built from `copybooks/wspl.cob`, and
the inline buffer is recorded as a fourth, divergent layer rather than treated
as a source. It is offered as a further register entry for
`docs/migration/anomaly-log.md`.

Two of its comments earn their keep by explaining copybook oddities:
[:L343] "11/07/23 was comp-3 now matches wspl.cob" explains the stale
`*> RDB comp-3` at [copybooks/wspl.cob:L30], and [:L352] "chg name 4 SQL Mig."
explains the dropped trailing E on PURCH-CREATE-DAT. Both confirm that the
declaration governs.

One briefing claim is restated here rather than repeated, because the frozen
source does not support it as given: the comment at [common/purchMT.cbl:L884]
does NOT name a record that appears nowhere. `01 Purch-Rec.` IS declared, at
[:L331], in the LINKAGE SECTION, and IS a PROCEDURE DIVISION parameter. The
only genuine oddity is casing - the comment writes `Purch-REC` where the
declaration writes `Purch-Rec`. Recorded as casing, not as a phantom.

"THE PURCHASE MIRROR" IS THE MOST DANGEROUS PHRASE IN THIS BRIEF
===============================================================
`records/sales_ledger.py` models a genuinely similar record, and that
similarity is a trap. This module IMPORTS NOTHING FROM IT, shares no base
class, no mixin, no helper, no descriptor table and no naming shortcut with it,
and is not a copy of it with the prefixes exchanged. It was built from
`copybooks/wspl.cob` alone. The two copybooks were compared line by line, and
they differ structurally in fourteen ways - nine of them named in the briefing
and five more found in the comparison. Every one survives here; none is
harmonised. The register, for `docs/migration/traceability.md`:

     #  divergence            Purchase (wspl.cob)      Sales (wssl.cob)
     1  stats-date column     ABSENT - no host var,    SALES-STATS-DATE
                              no column [L53]          char(4) present [L64]
     2  field order           Purch-Status [L18] and   Sales-Name first [L17];
                              Purch-Notes-Tag [L21]    Sales-Status later [L25]
                              BEFORE Purch-Name [L22]
     3  fax / e-mail order    Purch-Fax [L28] BEFORE   Sales-Email [L23]
                              Purch-Email [L29]        BEFORE Sales-Fax [L24]
     4  the flag block        ABSENT ENTIRELY - no     six flags with 88s:
                              late-charge, no          Sales-Late [L28-29],
                              reminder, no e-mail      Sales-Dunning [L30-31],
                              switches                 Email-Invoice [L32-33],
                                                       Email-Statement [L34-35],
                                                       Email-Letters [L36-37],
                                                       Delivery-Tag [L38]
     5  bank details          Purch-SortCode [L32] +   ABSENT
                              Purch-Accountno [L33]
     6  binary run ORDER      Purch-Create-Date at     Sales-Create-Date LAST
                              position 8 [L39],        [L53], AFTER the Pay-*
                              BEFORE the Pay-* trio    trio
     7  credit field type     binary-char [L31]        pic 99 [L41] - zoned
                                                       DISPLAY, "*> In days"
     8  partial-ship flag     ABSENT                   Sales-Partial-Ship-Flag
                                                       [L65-66] + 88
                                                       Sales-BO-Set value "Y"
                                                       [L67]
     9  FILLER shape          one, pic x(12) [L54]     two: pic xxx [L40] and
                                                       pic x(5) [L68]
    10  binary-short          NONE declared at all     Sales-Late-Min and
                                                       Sales-Late-Max
                                                       binary-short [L43-44]
    11  redefines view name   PTurnover-q, P prefix,   STurnover-Q, S prefix,
                              lower q [L51]            upper Q [L62]
    12  header end date       last entry 15/01/18      last entry 06/02/24, the
                              [L11]                    back-order flag [L9-10]
    13  header wording        "WS Definition For The   "Record Definition For
                              Purchase Ledger Record." The Sales Ledger /
                                                       Taken from fdsel"
    14  declared size         302 bytes, three         300 bytes, one revision,
                              revisions, plus the      no external note [L7]
                              COBSTRUCT note [L6-L8]

And the casing and spelling divergences, on top of those fourteen:
Supplier-live / Supplier-dead with `value 0` here, against Customer-Live /
Customer-Dead with `value zero` there [copybooks/wssl.cob:L26-L27]; the
prefixed `Purch-Notes-Tag` [L21] against the bare `Notes-Tag`
[copybooks/wssl.cob:L39]; `Turnover-q1` against `Turnover-Q1`;
`Purch-Last-inv` / `-pay` against `Sales-Last-Inv` / `-Pay`; and `Array-k`
against `Array-K` - even the dead, commented-out declarations diverge.

THE DEAD DECLARATION AT L15-L17 IS RECORDED AND NOT MODELLED
============================================================
    *>     03  filler   redefines WS-Purch-Key.      [copybooks/wspl.cob:L15]
    *>         05  Array-k         pic x  occurs 6.  [copybooks/wspl.cob:L16]
    *>         05  Check-Digit     pic 9.            [copybooks/wspl.cob:L17]

All three lines are COMMENTED OUT in the frozen copybook, so the key-character
array and the check digit are not part of the record. No attribute, no nested
class and no key-decomposition view for them appears below, and the generated
dictionary contains no entry for either name. Its presence is recorded because
its casing diverges from the Sales twin's `Array-K` [copybooks/wssl.cob:L15] -
noted at register row 11's neighbourhood above - and because a reader diffing
the two files should know the omission is deliberate.

WHY THE TABLE HAS TWENTY-NINE COLUMNS - THE ARITHMETIC, SHOWN
============================================================
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

Twenty-nine, matching the frozen DDL at [mysql/ACASDB.sql:L646] and Agent
Action Plan section 0.6.6 exactly. Every one of the 29 columns is NOT NULL,
there are no column-level defaults, no TIMESTAMP, no AUTO_INCREMENT and - as
R-2 requires across the whole schema - no FLOAT, DOUBLE or REAL anywhere.

That NOT NULL property is why NO attribute below is ever None. Agent Action Plan
section 0.6.2 gives the mechanism: the bridge `initialize`s its host-variable
group before loading, "so unset fields become zero or space rather than SQL
NULL. This is why every column in the schema can be declared NOT NULL and why
the Python layer must default rather than omit." Defaults follow that exactly -
zero for a numeric field, and SPACES AT THE DECLARED WIDTH for an alphanumeric
one rather than an empty string, because a `char(n)` column holding an
initialised COBOL field holds n spaces. The widths are read from each
descriptor's `character_length`, never typed in.

PROVENANCE: EVERY DESCRIPTOR IS LOOKED UP, NONE IS TRANSCRIBED
==============================================================
Agent Action Plan section 0.8.1 makes the ordering a directive rather than a
preference: "Data dictionary first. The dictionary is generated from the bridge
before record definitions are written, and every Python field definition cites
its entry ... it is what prevents fields being transcribed by eye." Section
0.3.3 states the consequence: "Field metadata is therefore derived, not
transcribed, which eliminates an entire class of transcription error across
several hundred fields."

So every attribute below carries a `FieldDescriptor` in its `dataclasses.field`
metadata, obtained through `FieldDescriptor.from_dictionary_key`, and every key
is found by asking the dictionary which entry sits at a given copybook field
name and declaration line - see `_index_copybook` and `_descriptor`. No key is
assembled by upper-casing or hyphenating an attribute name, which would be wrong
for at least five fields in this record alone:

    Purch-Create-Date  ->  PULEDGER-REC.PURCH-CREATE-DAT   the E is dropped
    Purch-Address      ->  PULEDGER-REC.PURCH-ADDRESS      one column, two
                                                           children
    Purch-Last-inv     ->  PULEDGER-REC.PURCH-LAST-INV     casing changes
    Turnover-q1        ->  PULEDGER-REC.TURNOVER-Q1        casing changes
    Purch-Stats-Date   ->  WS-Purch-Record.Purch-Stats-Date
                                                           a different table
                                                           namespace entirely,
                                                           because there is no
                                                           column to key on

THE DESCRIPTOR SPLIT IS BETTER THAN EXPECTED: 37 LOOKED UP, 0 HAND-BUILT.
    The briefing anticipated needing `FieldDescriptor.for_working_storage` for
    the FILLER, the PTurnover-q view, the two address children and
    Purch-Stats-Date, because none of them has a column to key on. Querying the
    generated dictionary shows that is unnecessary: `loader.
    entries_for_copybook_file("copybooks/wspl.cob")` returns 37 entries - the
    29 table-backed ones plus 8 marked one-sided, namely the 01 record itself,
    Purch-Addr1, Purch-Addr2, Quarters, filler#50, PTurnover-q,
    Purch-Stats-Date and filler#54. So EVERY field in this copybook, including
    all five the briefing expected to be hand-built, has a generated entry, and
    this module calls `from_dictionary_key` 37 times and `for_working_storage`
    ZERO times. That is the stronger outcome: not one descriptor in this record
    was assembled by hand, so R-5's "derived, not transcribed" holds without
    exception. The one-sided keys use the `<COPYBOOK-RECORD>.<FIELD-NAME>`
    form, and the two fillers are disambiguated by declaration line exactly as
    the artifact spells them - `filler#50` and `filler#54`.

ONE DISCREPANCY AGAINST THE BRIEFING'S EXPECTED VALUES, REPORTED NOT PATCHED.
    The briefing's checklist expects `scale == 0` for the twelve binary fields.
    The generated dictionary records `scale is None` for them, and `digits is
    None` too, because `binary-char` and `binary-long` carry no PICTURE clause
    at all - None here means ABSENT, not zero. That is the dictionary's
    considered representation of a picture-less binary item, and it is left
    alone. The load-bearing fact is untouched and is what the tests assert:
    `python_storage` is INT, `is_int` is true, `quantum` is None, and therefore
    the integer truncation that A-8, A-9 and A-10 depend on is reproducible.

AN OPEN QUESTION FOR THE COMPILED ORACLE (R-6, question 1 of 2)
    Agent Action Plan section 0.6.8, verbatim: "A negative binary value through
    an unsigned host variable into an unsigned column. Section 0.6.2
    establishes that the sign is lost; what the resulting stored value IS
    depends on the conversion the bridge's C interface performs, which must be
    measured rather than assumed."

    That question is about the twelve fields in KIND 1. It is SHARPER here than
    on the Sales side because of KIND 2: `Purch-SortCode`'s column is narrower
    than both its field and its host variable, so overflow behaviour must be
    measured as well as sign behaviour. This module therefore stores no assumed
    bit pattern, no magnitude and no modulus - it reports the signed copybook
    view, and `dal/acas022_purch.py` will carry whatever the oracle shows.
    Recorded for `docs/migration/ambiguity-resolutions.md`.

DETERMINISM (R-6)
=================
Attribute order is the copybook's declaration order, L14 through L54, which is
NOT the Sales order - see register rows 2, 3 and 6. `PTurnover-q ... occurs 4`
is a fixed four-element tuple, never a list. Four attributes are date-like -
Purch-Last-inv, Purch-Last-pay, Purch-Create-Date and Purch-Stats-Date - and
none of them touches a clock: no wall-clock reads, no environment reads, no
identity reads, no directory scans anywhere in this module. The only I/O is the
dictionary loader's own lazily cached read of the committed JSON artifact.

R-1 (no COBOL at runtime) holds trivially: standard library plus two
first-party modules, no process spawning, no foreign-function interface, no
database driver, no compiler or translator invocation. R-3 holds by
construction: exactly the fields the copybook declares, in its order, with no
checks, no coercion, no hook after construction and no schema-owning metadata;
no threads and no event loop.

THE LEAF RULE (Agent Action Plan section 0.4.3)
==============================================
`records/*.py` may import `cobol.field` and `dictionary.loader` and nothing
else, "which keeps the record layer a leaf". `ConditionName` is taken from
`dictionary.model` as a type only, following the precedent `cobol/field.py`
itself sets by importing its own enumerations from there rather than declaring
competing copies. Not imported, deliberately: any `dal` module, any `programs`
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

# Type-only imports. `cobol/field.py` sets this precedent by taking its own
# enumerations from `dictionary.model` rather than declaring competing copies;
# Agent Action Plan section 0.4.3 permits it for annotations. `ConditionName`
# additionally carries real data here - see PURCH_STATUS_CONDITION_NAMES.
from acas_posting.dictionary.model import ConditionName, DictionaryEntry

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

# ---------------------------------------------------------------------------
# The entity spine, from Agent Action Plan section 0.2.1.1
# ---------------------------------------------------------------------------

COPYBOOK: Final[str] = "copybooks/wspl.cob"
"""The frozen record layout this module mirrors. Read-only, never modified."""

TABLE: Final[str] = "PULEDGER-REC"
"""The MySQL table, 29 columns, primary key PURCH-KEY [mysql/ACASDB.sql:L646]."""

HANDLER: Final[str] = "acas022"
"""The COBOL file handler the posting programs CALL [common/acas022.cbl]."""

BRIDGE: Final[str] = "purchMT"
"""The generated bridge program [common/purchMT.cbl]."""

# ---------------------------------------------------------------------------
# Provenance: descriptors are looked up, never transcribed (R-5)
# ---------------------------------------------------------------------------


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
    and wraps it immutably, which is how `tests/arithmetic/*` reach the storage
    metadata without this module publishing an accessor of its own.
    """
    return {"descriptor": descriptor}


# ---------------------------------------------------------------------------
# Defaults: derived from each descriptor, and never None
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Condition names: carried as data, evaluated elsewhere
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# The subordinate groups
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------

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
    #
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
    #
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
    #
    # DRIFT KIND 2, a three-way width disagreement in two directions: 8-bit
    # signed here, 8 digits unsigned at [common/purchMT.cbl:L295] - a widening -
    # and a `mediumint(2) unsigned` column - a narrowing. Reported unsettled;
    # `dal/acas022_purch.py` owns the conversion.
    purch_credit: int = field(**_int_spec("Purch-Credit", _locator(31)))

    # 03  Purch-SortCode      binary-long. *> all these were pic 9(8) comp
    #                                                     [copybooks/wspl.cob:L32]
    # int: SIGNED 32-BIT, no picture, scale 0. The inline comment covers the
    # whole L32-L42 run and is history; the `9(8)` in it is not a digit count.
    #
    # DRIFT KIND 2 again, and the sharper case: 32-bit signed here, 8 digits at
    # [common/purchMT.cbl:L296], and a `mediumint(6) unsigned` column that is
    # NARROWER THAN BOTH. A UK sort code is six digits, so the column is apt and
    # is the tightest of the three layers - which is why the oracle question in
    # the module docstring has to measure overflow as well as sign.
    #
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
    #
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
    #
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

    # 03  Purch-Stats-Date    pic 9(4).             *> added 15/01/18.
    #                                                     [copybooks/wspl.cob:L53]
    # ===================================================================
    # THE NEW ANOMALY. This field reaches NO host variable and NO column.
    # ===================================================================
    #   declared            [copybooks/wspl.cob:L53], per header note L11
    #   no host variable    HV-PURCH-STATS does not occur in common/purchMT.cbl
    #   never mapped        bb000-HV-Load [common/purchMT.cbl:L1203] loads the
    #                       other twenty-nine fields and not this one
    #   no column           PURCH-STATS does not occur in mysql/ACASDB.sql
    #   dictionary agrees   the entry is one-sided; `loader.cite` for its key
    #                       reports "bridge=absent column=absent"
    #
    # It IS declared a second time on the COBOL side - in the bridge's own stale
    # inline buffer at [common/purchMT.cbl:L364] - and mapped from neither.
    #
    # THE ASYMMETRY IS THE EVIDENCE OF ACCIDENT: the Sales copybook added the
    # identical field on the identical date with the identical comment
    # [copybooks/wssl.cob:L64], and there it DID gain a host variable
    # [common/salesMT.cbl:L320] and a column [mysql/ACASDB.sql:L981].
    #
    # Declared here regardless, because R-3 forbids removing a field as firmly
    # as adding one, and because the header's 302-byte size counts it. Keyed on
    # the copybook-record namespace, `WS-Purch-Record.Purch-Stats-Date`, since
    # there is no column to key on. This is the one field for which the bridge
    # is not the layout source, because the bridge never maps it.
    #
    # Not among the Agent Action Plan's twenty-two section 0.6.7 entries: raised
    # as a new entry for `docs/migration/anomaly-log.md` with this module as the
    # recording site, cross-referenced to `ar3` in `records/irs_final.py`. And
    # raised for `docs/migration/ambiguity-resolutions.md`, because a value
    # written here is invisible in every table dump, so only the compiled program
    # can show whether anything reads it back.
    #
    # Zoned DISPLAY, four digits, scale 0, unsigned - the copybook view, which is
    # the only view there is. Date-like, and it touches no clock.
    purch_stats_date: int = field(**_int_spec("Purch-Stats-Date", _locator(53)))

    # 03  filler              pic x(12).                  [copybooks/wspl.cob:L54]
    # The trailing FILLER, declared rather than skipped: it is part of the 302
    # declared bytes and R-3 forbids dropping it. It reaches no column, which is
    # one of the three subtractions in the 29-column arithmetic.
    #
    # NAMING SCHEME: `filler_l<line>`. The COBOL name is simply `filler`, which
    # `copybooks/wspl.cob` uses twice - at L50 for the redefining group, modelled
    # as QuartersView, and here at L54 - so the declaration line is what
    # separates them. The dictionary does exactly the same thing, keying them
    # `filler#50` and `filler#54`, so this scheme mirrors the artifact rather
    # than inventing a convention. The Sales record has TWO alphanumeric fillers,
    # `pic xxx` and `pic x(5)` [copybooks/wssl.cob:L40, L68], against this one -
    # divergence register row 9.
    filler_l54: str = field(**_text_spec("filler", _locator(54)))
