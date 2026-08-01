"""`WS-Sales-Record` - the Sales Ledger customer account, field for field.

A CREATE from `copybooks/wssl.cob`, the 68-line copybook that lays out the
Sales Ledger. Four plain dataclasses mirror the copybook's declarations in its
own order, each attribute obtaining its storage metadata from the generated
data dictionary rather than from a picture clause typed by eye. Nothing is
added, nothing is renamed and nothing is put right.

    entity facade   Sales
    handler         acas012          [common/acas012.cbl]
    bridge          salesMT          [common/salesMT.cbl]
    MySQL table     SALEDGER-REC     37 columns, every one NOT NULL
    copybook        copybooks/wssl.cob
    record          01  WS-Sales-Record.            [copybooks/wssl.cob:L12]

This module holds no accounting logic. It declares no arithmetic, no
predicate, no accessor and no check. It supplies field TYPES - and for this
one record the field types are load-bearing to a degree no other record in
the folder matches, which the next two sections explain before anything else.

THE TWO-DIRECTION TYPING RULE (RULE R-2)
========================================
Rule R-2, verbatim: "No accounting value may pass through a binary
floating-point type at any point - not in computation, not in storage, not in
transport."

This record contains BOTH directions of the rule that follows from it, which
is why the rule has to be stated as two clauses rather than one:

    a binary-family item carries NO `V`, so its scale is zero
                                    -> `int`      nine fields, L43-L53
    a `comp` or `comp-3` item WITH a `V` has a fractional part
                                    -> `Decimal`  eight fields, L42 and
                                                  L54-L63

"binary -> `int`" therefore holds ONLY at scale zero. Getting either clause
backwards changes every stored value in the direction it is wrong:

    typing any of the nine `binary-short`/`binary-long` items as `Decimal`
    carries a remainder the compiled program discards, silently repairing
    anomalies A-8, A-9 and A-10 - see the next section;

    typing `Sales-Discount pic 99v99 comp` [copybooks/wssl.cob:L42] as `int`
    discards its pence, corrupting every discount. It is `comp`, but it has
    a `V`, so it is `Decimal` at scale 2.

The nine `int` items are `Sales-Late-Min` and `Sales-Late-Max`
(`binary-short`, L43-L44) and `Sales-Limit`, `Sales-Activety`,
`Sales-Last-Inv`, `Sales-Last-Pay`, `Sales-Average`, `Sales-Pay-Activety`,
`Sales-Pay-Average`, `Sales-Pay-Worst`, `Sales-Create-Date` (`binary-long`,
L45-L53). That is eleven items in two `binary` families; nine of them are the
`binary-long` group the Agent Action Plan names. No binary floating-point
value appears anywhere below.

WHY THESE TYPES MAKE THREE DEFECTS REPRODUCIBLE (RULE R-4)
==========================================================
Agent Action Plan section 0.6.1 calls the averaging defect "The highest-value
finding" of the whole analysis, and states the consequence for this file
directly: because the statistics fields "are declared `binary-long`
[copybooks/wssl.cob:L46-L52]", the truncation they take when a quotient is
stored back into one of them is integer truncation - and that, in the plan's
own words, "is exactly what makes the moving-average defect reproducible."

Three registered anomalies depend on the types declared here. This module
does not reproduce them - it makes them reproducible, and the program modules
named beside each one do the reproducing:

    A-8   Double truncation of the running average. The accumulator
          `03 work-2 pic s9(14) comp-3.` [sales/sl060.cbl:L206] has
          FOURTEEN digits and scale ZERO, while the value added into it,
          `03 work-goods pic s9(7)v99 comp-3.` [sales/sl060.cbl:L218],
          carries two. Pence are therefore discarded on every accumulation
          [sales/sl060.cbl:L826], and the quotient that follows
          [sales/sl060.cbl:L827] discards its remainder as well, because the
          receiving field `Sales-Average` is an integer
          [copybooks/wssl.cob:L49].
          Reproduced by `programs/sl060_invoice_posting.py`.
    A-9   The credit-note path never steps its `Sales-Activety` counter, so
          the first credit note for a customer is dropped in silence
          [sales/sl060.cbl:L832-L843].
          Reproduced by `programs/sl060_invoice_posting.py`.
    A-10  Three mutually inconsistent guards on one averaging idiom
          [sales/sl060.cbl:L819], [sales/sl060.cbl:L835],
          [sales/sl100.cbl:L506].
          Reproduced by `programs/sl060_invoice_posting.py` and
          `programs/sl100_cash_posting.py`.

Agent Action Plan section 0.6.1 closes the point: "Normalising them into one
helper would be the single easiest way to fail this migration." Nothing below
merges the three idioms, and nothing below computes an average at all. The
truncation itself belongs to `acas_posting.cobol.arithmetic`, invoked from the
program layer; this module never imports it (see LAYERING).

THE THREE AVERAGING SITES - LOCATORS ONLY, ALL RE-READ FROM SOURCE
=================================================================
Recorded here so that `docs/migration/anomaly-log.md` and
`docs/migration/traceability.md` can lift verified locators rather than
approximate ones. Every line number below was read from the frozen source
during this module's construction; where it disagreed with a secondary
account, the source won (rule R-6).

    ba000-Sales-Comp, a SECTION       [sales/sl060.cbl:L816]
        guard on TWO conditions           L819-L820
        product into work-2               L821
        `else move zero to work-2`        L823, closed by `end-if` L824
        `add 1 to sales-activety.`        L825  <- counter stepped FIRST
        `add work-goods to work-2.`       L826
        quotient into Sales-Average       L827
    ba000-Credit-Comp, a SECTION      [sales/sl060.cbl:L832]
        guard on TWO conditions           L835-L836
        product into work-2               L837
        `else move zero to work-2`        L839, closed by `end-if` L840
        extra guard `if work-2 not = zero`  L841
        `add work-goods to work-2`        L842
        quotient into Sales-Average       L843
        and NO counter step anywhere in the section - this is A-9
    compute-sales-pay, a PARAGRAPH    [sales/sl100.cbl:L497]
        early exit `if oi-date-cleared = zero / go to csp-exit.` L500-L501
        day count into work-a             L503
        `move zero to work-b.`           L504
        guard on ONE condition            L506
        product into work-b               L507, period-terminated, no end-if
        `add work-a to work-b.`          L509
        `add 1 to sales-pay-activety.`   L510
        quotient into Sales-Pay-Average   L511
        worst-days watermark              L513-L514
        `csp-exit.` L516, `exit.` L517

CITATIONS CHECKED AND LEFT AS THE PLAN HAS THEM. A secondary account of this
work proposed moving three `sl100` citations - the guard to L508, the product
to L509 and the quotient to L513. Read directly, `sales/sl100.cbl` puts the
guard at L506, the product at L507 and the quotient at L511, so the Agent
Action Plan's own L506, L507 and L511 are exact and the proposed replacements
are each two lines late. The plan's numbers stand; the proposal does not.

FOUR FURTHER DIVERGENCES BETWEEN THE "SAME" IDIOM
=================================================
Beyond the guard count, the missing counter step and the operand order, four
more differences were measured. They are recorded because a migrator who
smoothed any of them away would change a stored figure:

    1. STORAGE CLASS AND CAPACITY, not scale. `sl060`'s accumulator is
       packed decimal, `03 work-2 pic s9(14) comp-3.`
       [sales/sl060.cbl:L206]. `sl100`'s accumulators are BINARY,
       `03 work-a binary-long value zero.` and
       `03 work-b binary-long value zero.` [sales/sl100.cbl:L182-L183].
       BOTH are scale ZERO, so the guess that the cash path truncates once
       where the invoice path truncates twice does not survive contact with
       the source. What actually differs is the representation and the range
       it can hold - fourteen decimal digits against a 32-bit signed integer.
       Note that `sl060` ALSO declares `work-a` and `work-b`, and there they
       are `pic s9(7)v99 comp-3` at scale 2 [sales/sl060.cbl:L207-L208]: the
       same two names mean different storage in the two programs.
    2. WHAT ENTERS THE ACCUMULATOR. In `sl060` a scale-2 money value enters
       a scale-0 accumulator, which is where the pence go (A-8). In `sl100`
       what enters is a day count [sales/sl100.cbl:L503], already integral,
       so there are no pence to lose at that step - yet the quotient at
       [sales/sl100.cbl:L511] still truncates.
    3. CONTROL-FLOW SHAPE. The two `sl060` sites are SECTIONS using `end-if`
       [sales/sl060.cbl:L824], [sales/sl060.cbl:L840]; the `sl100` site is a
       PARAGRAPH using period termination and a `go to csp-exit` early exit
       [sales/sl100.cbl:L500-L501].
    4. THE OPERAND ORDER DIVERGES IN SPELLING ONLY - do not over-read it.
       `sl060` writes the `INTO` form and `sl100` the `BY` form, so the two
       statements are written in opposite orders. The quotient is
       nevertheless the same in both: `INTO` names the divisor first and
       `BY` names it second, and each site ends up taking accumulator over
       counter. A migrator who reproduced "the opposite order" as an
       inverted quotient would INTRODUCE a defect rather than preserve one.
       Preserve the spelling at each site; do not invert the result.

DRIFT AT THE BRIDGE BOUNDARY - FIVE KINDS, ALL LEFT UNSETTLED
=============================================================
The bridge is not a transparent pipe. For several fields the copybook, the
bridge host variable and the MySQL column disagree, and the disagreement
changes values BEFORE any SQL executes. The host-variable group is
`01 TD-SALEDGER-REC.` [common/salesMT.cbl:L284] with thirty-seven host
variables at [common/salesMT.cbl:L285-L321], loaded by
`bb000-HV-Load Section.` [common/salesMT.cbl:L1196].

Every descriptor below reports the COPYBOOK view and only the copybook view.
The disagreement is offered exactly as the dictionary records it, through
`loader.drift_for(key)` and `FieldDescriptor.drift()`, and it is settled
nowhere in this file. Applying a bridge conversion belongs to
`dal/acas012_sales.py`, at the boundary that performs it.

KIND 1 - SIGNEDNESS LOSS. Registered as anomaly A-11, whose textbook case
is this record's `Sales-Average`:

    layer            declaration                              range
    ---------------  ---------------------------------------  --------
    copybook         `Sales-Average binary-long`              SIGNED
                     [copybooks/wssl.cob:L49]
    host variable    `HV-SALES-AVERAGE PIC  9(10) COMP`       unsigned
                     [common/salesMT.cbl:L308]
    MySQL column     `SALES-AVERAGE int(8) unsigned NOT NULL` unsigned
                     [mysql/ACASDB.sql:L969]

Agent Action Plan section 0.6.2 states the consequence, verbatim: "a negative
value computed in COBOL loses its sign at the bridge, not at the database - so
the Python data-access layer must reproduce the bridge's conversion, not
merely write the computed value and let MySQL complain."

THE NARROWING BLOCK IS ELEVEN HOST VARIABLES WIDE, NOT EIGHT. The Agent
Action Plan cites [common/salesMT.cbl:L305-L312]. Read directly, the block of
signed-source items narrowed to unsigned host variables runs
[common/salesMT.cbl:L302-L312], because `Sales-Late-Min` and `Sales-Late-Max`
are `binary-short` and therefore signed too, and both narrow to
`PIC  9(05) COMP`. The generated dictionary agrees independently: all ELEVEN
carry anomaly reference A-11 and ambiguity reference Q-3, while every money
field carries neither. The full map, copybook line to host-variable line:

    Sales-Late-Min      L43 -> L302        Sales-Pay-Activety  L50 -> L309
    Sales-Late-Max      L44 -> L303        Sales-Pay-Average   L51 -> L310
    Sales-Limit         L45 -> L304        Sales-Pay-Worst     L52 -> L311
    Sales-Activety      L46 -> L305        Sales-Create-Date   L53 -> L312
    Sales-Last-Inv      L47 -> L306
    Sales-Last-Pay      L48 -> L307        Sales-Average       L49 -> L308

KIND 2 - GROUP CONCATENATION, alphanumeric. `03 Sales-Address.`
[copybooks/wssl.cob:L18] is a GROUP of two 48-character children
[copybooks/wssl.cob:L19-L20]. The bridge declares ONE
`HV-SALES-ADDRESS PIC X(96)` [common/salesMT.cbl:L287] and moves the group
whole - `move Sales-ADDRESS to HV-SALES-ADDRESS` [common/salesMT.cbl:L1207],
the bridge's own upper-case spelling of the name - and the column is a single
`SALES-ADDRESS char(96)` [mysql/ACASDB.sql:L948]. So `Sales-Addr1` and
`Sales-Addr2` have NO columns of their own. Both are declared here regardless,
because rule R-3 forbids removing what the copybook declares.

    A NOTE ON HOW THIS KIND SHOWS UP, since it is easy to look for it in the
    wrong place: `loader.drift_for("SALEDGER-REC.SALES-ADDRESS")` reports NO
    flags and no details. That is correct rather than a gap - a GROUP has no
    width of its own to compare against a column, so there is nothing for a
    field-by-field comparison to disagree about. The concatenation is visible
    instead in the KEY LAYOUT: the parent group owns the column-backed key
    `SALEDGER-REC.SALES-ADDRESS`, while both children are copybook-only keys
    under `WS-Sales-Record.`. See DICTIONARY_KEYS below.

KIND 3 - NAME TRUNCATION. `Sales-Create-Date` [copybooks/wssl.cob:L53]
becomes `HV-SALES-CREATE-DAT` [common/salesMT.cbl:L312] and column
`SALES-CREATE-DAT` [mysql/ACASDB.sql:L973] - the trailing `E` is dropped. The
bridge's own move says so: `move Sales-CREATE-DATE to HV-SALES-CREATE-DAT`
[common/salesMT.cbl:L1232]. This is precisely why keys are obtained from the
dictionary and never assembled from an attribute name.

KIND 4 - TYPE-CLASS DRIFT, NUMERIC TO CHARACTER. `Sales-Stats-Date` is
declared `pic 9(4)` [copybooks/wssl.cob:L64] - NUMERIC, zoned DISPLAY, four
digits, scale 0 - yet the bridge declares `HV-SALES-STATS-DATE PIC X(4)`
[common/salesMT.cbl:L320] and the column is `SALES-STATS-DATE char(4)`
[mysql/ACASDB.sql:L981]. A numeric copybook field becomes an alphanumeric
host variable and an alphanumeric column. No other record in this folder
carries this kind. Its descriptor reports the COPYBOOK view and its attribute
is therefore `int`, NOT `str`; the column's character view is reached through
`loader.column_for` by the handler that writes it.

KIND 5 - DIGIT WIDENING. The `binary-short` pair widens to `9(05)`, the
`binary-long` group to `9(10)`, and each single-digit zoned flag widens to
`9(03) COMP` - `Sales-Status pic 9.` [copybooks/wssl.cob:L25] becomes
`HV-SALES-STATUS PIC  9(03) COMP` [common/salesMT.cbl:L292] and column
`SALES-STATUS tinyint(1) unsigned` [mysql/ACASDB.sql:L953]. The value is
unharmed; only the declared room for it changes.

A CLEAN PASS-THROUGH, WHICH IS THE POINT OF A-11. Agent Action Plan section
0.6.2 records that the drift is "specific rather than systemic", and the money
fields prove it: `Sales-Current` and `Sales-Last pic s9(8)v99 comp-3`
[copybooks/wssl.cob:L54-L55] become `PIC S9(08)V9(02) COMP`
[common/salesMT.cbl:L313-L314] and `decimal(10,2)`
[mysql/ACASDB.sql:L974-L975] - SIGNED at all three layers. The same holds for
`Turnover-Q1` through `Turnover-Q4` [common/salesMT.cbl:L315-L318] and
`Sales-Unapplied` [common/salesMT.cbl:L319]. Money keeps its sign; statistics
lose theirs. That contrast is the whole of A-11.

TRAILING SPACES ARE NOT THIS FILE'S BUSINESS. The bridge trims on the way out
- `STRING FUNCTION TRIM (HV-SALES-ADDRESS,TRAILING)`
[common/salesMT.cbl:L1332] - and the harness's dump-comparison step owns
padding differences. Nothing here trims anything.

WHY EVERY COLUMN IS NOT NULL, AND WHY NO DEFAULT IS `None`
==========================================================
The load paragraph opens with `initialize TD-SALEDGER-REC.`
[common/salesMT.cbl:L1204], so a field the caller never set reaches SQL as
zero or space and never as NULL. Agent Action Plan section 0.6.2, verbatim:
"This is why every column in the schema can be declared NOT NULL and why the
Python layer must default rather than omit." All 37 columns are `NOT NULL` and
none carries a column default. Accordingly no attribute below defaults to
`None`: numeric items default to `0` or `Decimal("0.00")`, and alphanumeric
items default to SPACES at the declared width, which is what COBOL's own
`INITIALIZE` stores.

THE 37 COLUMNS, AND THE ARITHMETIC THAT REACHES 37
==================================================
The copybook declares 40 elementary items once the `STurnover-Q` redefines
view is set aside. From there:

    40  elementary items in declaration order
   - 2  FILLER items, L40 and L68, which no column carries
   - 1  because `Sales-Addr1` and `Sales-Addr2` share ONE column (KIND 2)
   ----
    37  columns, matching the count in Agent Action Plan section 0.6.6

Two further facts were measured rather than assumed. Those 40 items' byte
lengths sum to exactly 300, matching the copybook header's own
"rec size 300 bytes" [copybooks/wssl.cob:L7] - so unlike the batch record,
whose declared length contradicts its field sum (A-15), THIS record's header
and layout agree, and no such contradiction should be looked for here. And
the redefines area balances exactly: `STurnover-Q` is 6 bytes occurring 4
times, against `Turnover-Q1` through `Turnover-Q4` at 6 bytes each.

THE DEAD DECLARATION AT L14-L16 IS NOT MODELLED
===============================================
`copybooks/wssl.cob` carries a commented-out redefinition of the key, three
lines each prefixed `*>` [copybooks/wssl.cob:L14-L16]: a `filler redefines
WS-Sales-Key` group with a six-occurrence `Array-K` character item and a
`Check-Digit` numeric item. It is COMMENTED OUT, so GnuCOBOL never sees it and
neither does this module. No attribute, no view and no key decomposition is
declared for it, and no check digit is verified anywhere - rule R-3 permits
nothing that the live copybook does not declare. Its presence is recorded
here and nowhere else. `records/purchase_ledger.py` carries the identical dead
block at [copybooks/wspl.cob:L15-L17]; neither is modelled, and the two
modules share no code (see LAYERING).

DECLARATION BEATS COMMENT, ELEVEN TIMES
=======================================
Eleven items carry an inline comment that contradicts the declaration beside
it. `Sales-Late-Min` and `Sales-Late-Max` are declared `binary-short` while
their comments read `*> 9999 comp` [copybooks/wssl.cob:L43-L44]. The nine
`binary-long` items read `*> 9(8) comp` [copybooks/wssl.cob:L45-L53].

THE DECLARATION GOVERNS. `binary-short` is a signed 16-bit integer at scale
zero; `binary-long` is a signed 32-bit integer at scale zero. Neither digits
nor scale nor signedness is taken from a comment, and `9999` and `9(8)` are
not digit counts for any descriptor here - the dictionary supplies those from
the declaration. Each stale comment is reproduced verbatim beside its
attribute, with the locator, and labelled stale. It is not put right, because
rule R-4 makes the source's oddities part of the specification.

THE MISSPELLINGS TRAVEL ALL THE WAY TO THE COLUMN NAME
======================================================
`Sales-Activety` [copybooks/wssl.cob:L46] and `Sales-Pay-Activety`
[copybooks/wssl.cob:L50] are misspelled in the copybook, and the misspelling
is carried through by the bridge - `HV-SALES-ACTIVETY`
[common/salesMT.cbl:L305], `HV-SALES-PAY-ACTIVETY` [common/salesMT.cbl:L309] -
and by the schema - `SALES-ACTIVETY` [mysql/ACASDB.sql:L966],
`SALES-PAY-ACTIVETY` [mysql/ACASDB.sql:L970]. The spelling is therefore part
of the dictionary key and of the SQL, not a typographical slip to be tidied:
respelling it would break the lookup and the statement together. It is
preserved exactly, everywhere, in every spelling this module writes.

OTHER ODDITIES PRESERVED, WITH LOCATORS
=======================================
    * `03 filler pic xxx.` [copybooks/wssl.cob:L40] spells its width as
      three `x` characters rather than `x(3)`. Recorded as written.
    * `03 Sales-Partial-Ship-Flag` [copybooks/wssl.cob:L65] and its
      `pic x.` [copybooks/wssl.cob:L66] occupy TWO physical lines. A
      line-oriented reader takes L65 for a group and loses the picture.
    * Three separate dated stamps mark the record's growth:
      `*> added 15/01/18.` [copybooks/wssl.cob:L64],
      `*> added 06/02/24` [copybooks/wssl.cob:L66] and
      `*> added 17/03/24` [copybooks/wssl.cob:L67]. All three verbatim.
    * The header explains why the trailing FILLER shrank instead of the
      record growing: "06/02/24 Added Partial ship flag into the filler no
      rec size / change. This to support Back Ordering etc, may be."
      [copybooks/wssl.cob:L9-L10]. The maintainer's own "may be" is his, and
      is kept.
    * The record header also records its origin: "Record Definition For The
      Sales Ledger" / "Taken from fdsel" [copybooks/wssl.cob:L3-L4], and
      "rec size 300 bytes ** 02/11/10 plus cleanup"
      [copybooks/wssl.cob:L7].
    * `03 filler redefines Quarters.` [copybooks/wssl.cob:L61] is an
      UNNAMED group. `QuartersView` below is a Python name for something
      the copybook does not name at all.

CONDITION NAMES ARE CARRIED AS DATA HERE, EVALUATED ELSEWHERE
=============================================================
Eight `88`-level condition names are declared on seven fields:
`Customer-Live` and `Customer-Dead` [copybooks/wssl.cob:L26-L27],
`Late-Charges` [copybooks/wssl.cob:L29], `Dunning-Letters`
[copybooks/wssl.cob:L31], `Email-Invoicing` [copybooks/wssl.cob:L33],
`Email-Statementing` [copybooks/wssl.cob:L35], `Email-Dunning`
[copybooks/wssl.cob:L37] and `Sales-BO-Set` [copybooks/wssl.cob:L67].

Agent Action Plan section 0.4.1.4 assigns the PREDICATE to
`acas_posting/cobol/condition_names.py`: "88-level condition name ->
Predicate function over the record." This module therefore publishes the
names and their value-clause text as data, through `CONDITION_NAMES`, and
declares no predicate, no accessor and no enumeration of its own. The type is
the dictionary's own `ConditionName`; a second definition of it here would be
exactly the divergence rule R-4 exists to prevent.

Each value is TEXT, never a number, and each is the value clause as written -
so `Customer-Live` reads `1` while `Customer-Dead` reads `zero`
[copybooks/wssl.cob:L26-L27], two spellings of one idea, both kept; and
`Sales-BO-Set` keeps its quote characters, `"Y"`, so a one-character switch
cannot be mistaken for a bare name.

THE OPEN ORACLE QUESTION - Q-3, SETTLED NOWHERE (RULE R-6)
==========================================================
Rule R-6, verbatim: "Where a semantic question is ambiguous, the compiled
program's observed behavior decides it, and each such resolution must be
documented rather than settled silently."

One such question is about this record, and the generated dictionary tags all
eleven narrowed fields with it as ambiguity reference Q-3. Agent Action Plan
section 0.6.8, verbatim: "A negative binary value through an unsigned host
variable into an unsigned column. Section 0.6.2 establishes that the sign is
lost; what the resulting stored value IS depends on the conversion the
bridge's C interface performs, which must be measured rather than assumed."

Nothing below answers it. No two's-complement reinterpretation, no absolute
value, no bit mask and no saturation is stored, implied or hinted at here.
The descriptors report the signed copybook view; the measurement and its
outcome belong to `docs/migration/ambiguity-resolutions.md`, and the
conversion that follows from it belongs to `dal/acas012_sales.py`.

TRACEABILITY (RULE R-5)
=======================
Agent Action Plan section 0.8.1, verbatim: "Data dictionary first. The
dictionary is generated from the bridge before record definitions are
written, and every Python field definition cites its entry. This ordering is a
directive, not a preference - it is what prevents fields being transcribed by
eye." And section 0.3.3: "Field metadata is therefore derived, not
transcribed, which eliminates an entire class of transcription error across
several hundred fields."

No picture clause, digit count, scale, sign position or storage class is typed
by hand below. `DICTIONARY_KEYS` holds every key once, in copybook
declaration order, and `FIELD_DESCRIPTORS` is built from it by lookup. A key
is never assembled from an attribute name - two of them could not be, since
`Sales-Create-Date` keys on `SALES-CREATE-DAT` and the two address children
key on the copybook record rather than on any column. A mistyped key raises at
import, because `FieldDescriptor.from_dictionary_key` refuses an unknown one.

All 45 items of this record have dictionary entries - the 37 column-mapped
ones plus eight copybook-only ones - so every descriptor here is built by
`from_dictionary_key` and NONE needs `for_working_storage`. That factory is
reserved for `work_records.py`, whose layouts belong to no copybook.

`loader.cite(key)` returns the three-locator provenance string and is
surfaced, never reimplemented. For this record it yields the worked example
rule R-5 itself uses:

    SALEDGER-REC.SALES-AVERAGE  copybook=copybooks/wssl.cob:L49
    bridge=common/salesMT.cbl:L308  column=mysql/ACASDB.sql:L969

LAYERING - THIS IS A LEAF MODULE (AGENT ACTION PLAN SECTION 0.4.3)
==================================================================
    MAY import       `acas_posting.cobol.field`,
                     `acas_posting.dictionary.loader`, the standard library
    MUST NOT import  anything else - "this keeps the record layer a leaf"

Forbidden, and each for a reason worth naming because each is a live
temptation in exactly this file:

    `acas_posting.cobol.arithmetic`   the strongest one. The truncation that
        makes A-8 visible lives there and is invoked from the program layer.
        Importing it here would put accounting behaviour in a record layout.
    `acas_posting.dal.acas012_sales`  owns the bridge's signedness loss. The
        drift above is described here and applied there.
    `acas_posting.programs.*`         `sl055`, `sl060` and `sl100` own the
        averages and mutate instances of this record.
    `records/purchase_ledger.py`      a near-mirror layout, and the sharpest
        invitation to share code. Record modules never import one another.
    also `cli`, `clock`, `dates`, `workfiles`, `cobol.move`,
        `cobol.picture`, `cobol.usage`, `cobol.condition_names`,
        `cobol.sortverb`, `dictionary.generate`, and the comparison oracle in
        its sibling tree.

Agent Action Plan section 0.4.3 gives the reason this matters rather than
being bookkeeping: "the arithmetic suite imports only `cobol` and `records`
and touches no database, so it runs anywhere." One import reaching into `dal`
would drag a database driver into that tier.

`ConditionName` is imported from `acas_posting.dictionary.model`, the
dictionary package's own object model, on the precedent
`acas_posting/cobol/field.py` sets and documents for the same edge: the
loader's whole return surface is built from those dataclasses, so importing
one is the SAME architectural edge as importing the loader, whereas
re-declaring it would create two competing definitions of one vocabulary.
Nothing from `acas_posting.cobol.condition_names` is imported.

DETERMINISM (RULE R-6)
======================
Dataclass field order follows copybook declaration order, so a reader can set
this module beside `copybooks/wssl.cob` and compare the two by eye. Every
published collection is a tuple or a read-only mapping, never a list. There is
no clock, no entropy source, no environment read and no process inspection
anywhere below - note that `Sales-Last-Inv`, `Sales-Last-Pay`,
`Sales-Create-Date` and `Sales-Stats-Date` are all date-bearing fields and not
one of them consults one. The only import-time work is the dictionary
loader's own lazy cached read, which every record module performs while its
classes are being defined.

NOT FROZEN, AND THAT IS DELIBERATE
==================================
`WS-Sales-Record` is read, changed and rewritten in place by the posting
steps, so these dataclasses are mutable. Not one of them is a frozen
dataclass, and freezing them would do more than inconvenience a caller: a
record that had to be copied to be changed invites a snapshot-and-rewrite
shape, and that shape is what makes a lost-update defect AVOIDABLE, which is
precisely the defect the IRS path already commits. Rule R-4 requires such
defects stay reproducible. `slots=True` is used instead - it closes each class
at its declared fields, so an attribute the copybook does not declare cannot
be attached by accident, which is rule R-3 enforced by the language.

RULE PROVENANCE
===============
This project carries NO separate user rules document - `review_rules` reports
that none was provided. The identifiers R-1 through R-6 cited above are the
Agent Action Plan's own (section 0.7.2), and the plan is where their full text
lives. Anomaly references A-n and ambiguity references Q-n are the generated
dictionary's own, and are reachable from any descriptor through
`anomaly_refs()` and `ambiguity_refs()`. The registers are
`docs/migration/anomaly-log.md` and
`docs/migration/ambiguity-resolutions.md`; the mapping this module feeds is
`docs/migration/traceability.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

# The dictionary package's own object model. Imported for `ConditionName`
# alone, on the precedent `acas_posting/cobol/field.py` sets and documents for
# this edge (Agent Action Plan section 0.4.3): the loader's entire return
# surface is built from these dataclasses, so importing one of them is the
# same architectural edge as importing the loader itself. Re-declaring it here
# would create a second, competing definition of one vocabulary, which is the
# divergence rule R-4 exists to prevent.
from acas_posting.dictionary.model import ConditionName

# Ordered by plain string comparison, so `tuple(__all__) == tuple(sorted(...))`
# holds and a test can assert it in one line. That is a deliberate choice, not
# an oversight: an import-sorter's grouping convention would place the two
# `RECORD_KEY`-style constants after the class names instead, and this project
# ships no linter configuration to make either convention binding. One
# already-committed module in this package orders its own list the same way.
__all__: Final[tuple[str, ...]] = (
    "BRIDGE_PROGRAM",
    "CONDITION_NAMES",
    "COPYBOOK_FILE",
    "COPYBOOK_RECORD",
    "DICTIONARY_KEYS",
    "ENTITY_FACADE",
    "FIELD_DESCRIPTORS",
    "FILE_HANDLER",
    "MYSQL_TABLE",
    "Quarters",
    "QuartersView",
    "RECORD_KEY",
    "SalesAddress",
    "WsSalesRecord",
)


# =============================================================================
#  PROVENANCE - THE ENTITY SPINE, AS AGENT ACTION PLAN SECTION 0.2.1.1 GIVES IT
# =============================================================================

ENTITY_FACADE: Final[str] = "Sales"
"""The entity facade name in `copybooks/Proc-ACAS-FH-Calls.cob`.

The facade publishes the twelve-verb vocabulary for this entity - Open,
Open-Input, Open-Output, Open-Extend, Close, Start, Read-Next, Read-Indexed,
Write, Rewrite, Delete, Delete-All. Recorded for traceability only; this
module calls none of them and never reaches the data-access layer.
"""

FILE_HANDLER: Final[str] = "acas012"
"""The numbered handler program the posting steps CALL for this entity.

Reproduced by `dal/acas012_sales.py` [common/acas012.cbl].
"""

BRIDGE_PROGRAM: Final[str] = "salesMT"
"""The generated bridge program that owns this table's SQL.

Read as `common/salesMT.scb` for its embedded table and host-variable
directive and its key metadata, and as `common/salesMT.cbl` for the
host-variable record and the load and unload paragraphs. Together with the
schema this pair is what the data dictionary for this migration is generated
from.
"""

MYSQL_TABLE: Final[str] = "SALEDGER-REC"
"""The frozen table name, spelt as `mysql/ACASDB.sql` spells it.

37 columns [mysql/ACASDB.sql:L945-L984], primary key `SALES-KEY`, every
column NOT NULL, no column default, no secondary index. The left half of
every column-mapped dictionary key below.
"""

COPYBOOK_FILE: Final[str] = "copybooks/wssl.cob"
"""The frozen copybook this module is a CREATE from - 68 lines, read-only."""

COPYBOOK_RECORD: Final[str] = "WS-Sales-Record"
"""The `01`-level record name, spelt as the copybook spells it.

`01  WS-Sales-Record.` [copybooks/wssl.cob:L12]. The left half of every
copybook-only dictionary key below - the two address children, the three
FILLER items, the two quarter groups and the `STurnover-Q` view.
"""

RECORD_KEY: Final[str] = "WS-Sales-Record.WS-Sales-Record"
"""The dictionary key of the `01`-level group itself.

A group has no storage of its own, so this entry's Python carrier is NONE and
its descriptor answers `is_group`. Held here rather than in `DICTIONARY_KEYS`
because the `01` level is the class, not one of its attributes.
"""


# =============================================================================
#  THE KEY TABLE - EVERY DICTIONARY KEY, ONCE, IN DECLARATION ORDER
# =============================================================================
#
# This tuple is the traceability table `docs/migration/traceability.md` lifts,
# and it is the ONLY place in this module where a key appears. Left half: the
# dotted attribute path, rooted at `WsSalesRecord`. Right half: the key,
# obtained by looking the record up through
# `loader.entries_for_copybook_record` and reading each entry's own
# `copybook.name` - never by transforming an attribute name. Two of these keys
# could not be derived from an attribute name at any rate:
#
#   * `Sales-Create-Date` keys on `SALEDGER-REC.SALES-CREATE-DAT`, the bridge
#     having dropped the trailing `E` [common/salesMT.cbl:L312].
#   * `Sales-Addr1` and `Sales-Addr2` key on the COPYBOOK RECORD, not on any
#     column, because their parent group owns the only column between them
#     [common/salesMT.cbl:L287].
#
# Order is the copybook's own, L13 through L68. It is NOT the loader's order:
# `entries_for_copybook_record` returns the 37 column-mapped entries in column
# ordinal order and appends the eight copybook-only ones, so declaration order
# has to be stated here. Rule R-6 makes an observable order part of behaviour,
# and for this record the order is also the byte layout - the 40 elementary
# items sum to the 300 bytes the header declares [copybooks/wssl.cob:L7].
#
# A key that does not exist raises `loader.DictionaryKeyError` at import, from
# inside `FieldDescriptor.from_dictionary_key`, so a typo cannot survive to
# run time.

_FIELD_KEYS: Final[tuple[tuple[str, str], ...]] = (
    # -- L13 .. L17 ------------------------------------------------------
    ("ws_sales_key", "SALEDGER-REC.SALES-KEY"),
    ("sales_name", "SALEDGER-REC.SALES-NAME"),
    # -- L18 .. L20  the group with one column and two column-less children
    ("sales_address", "SALEDGER-REC.SALES-ADDRESS"),
    ("sales_address.sales_addr1", "WS-Sales-Record.Sales-Addr1"),
    ("sales_address.sales_addr2", "WS-Sales-Record.Sales-Addr2"),
    # -- L21 .. L24 ------------------------------------------------------
    ("sales_phone", "SALEDGER-REC.SALES-PHONE"),
    ("sales_ext", "SALEDGER-REC.SALES-EXT"),
    ("sales_email", "SALEDGER-REC.SALES-EMAIL"),
    ("sales_fax", "SALEDGER-REC.SALES-FAX"),
    # -- L25 .. L39  the zoned single-digit switches -----------------------
    ("sales_status", "SALEDGER-REC.SALES-STATUS"),
    ("sales_late", "SALEDGER-REC.SALES-LATE"),
    ("sales_dunning", "SALEDGER-REC.SALES-DUNNING"),
    ("email_invoice", "SALEDGER-REC.EMAIL-INVOICE"),
    ("email_statement", "SALEDGER-REC.EMAIL-STATEMENT"),
    ("email_letters", "SALEDGER-REC.EMAIL-LETTERS"),
    ("delivery_tag", "SALEDGER-REC.DELIVERY-TAG"),
    ("notes_tag", "SALEDGER-REC.NOTES-TAG"),
    # -- L40  FILLER, `pic xxx`, no column --------------------------------
    ("filler_l40", "WS-Sales-Record.filler#40"),
    # -- L41 .. L42 ------------------------------------------------------
    ("sales_credit", "SALEDGER-REC.SALES-CREDIT"),
    ("sales_discount", "SALEDGER-REC.SALES-DISCOUNT"),
    # -- L43 .. L53  the eleven signed binary items narrowed at the bridge
    ("sales_late_min", "SALEDGER-REC.SALES-LATE-MIN"),
    ("sales_late_max", "SALEDGER-REC.SALES-LATE-MAX"),
    ("sales_limit", "SALEDGER-REC.SALES-LIMIT"),
    ("sales_activety", "SALEDGER-REC.SALES-ACTIVETY"),
    ("sales_last_inv", "SALEDGER-REC.SALES-LAST-INV"),
    ("sales_last_pay", "SALEDGER-REC.SALES-LAST-PAY"),
    ("sales_average", "SALEDGER-REC.SALES-AVERAGE"),
    ("sales_pay_activety", "SALEDGER-REC.SALES-PAY-ACTIVETY"),
    ("sales_pay_average", "SALEDGER-REC.SALES-PAY-AVERAGE"),
    ("sales_pay_worst", "SALEDGER-REC.SALES-PAY-WORST"),
    ("sales_create_date", "SALEDGER-REC.SALES-CREATE-DAT"),
    # -- L54 .. L55  money, signed at all three layers --------------------
    ("sales_current", "SALEDGER-REC.SALES-CURRENT"),
    ("sales_last", "SALEDGER-REC.SALES-LAST"),
    # -- L56 .. L60  the named quarters -----------------------------------
    ("quarters", "WS-Sales-Record.Quarters"),
    ("quarters.turnover_q1", "SALEDGER-REC.TURNOVER-Q1"),
    ("quarters.turnover_q2", "SALEDGER-REC.TURNOVER-Q2"),
    ("quarters.turnover_q3", "SALEDGER-REC.TURNOVER-Q3"),
    ("quarters.turnover_q4", "SALEDGER-REC.TURNOVER-Q4"),
    # -- L61 .. L62  the unnamed FILLER group redefining them, and its view
    ("quarters_view", "WS-Sales-Record.filler#61"),
    ("quarters_view.sturnover_q", "WS-Sales-Record.STurnover-Q"),
    # -- L63 .. L66 ------------------------------------------------------
    ("sales_unapplied", "SALEDGER-REC.SALES-UNAPPLIED"),
    ("sales_stats_date", "SALEDGER-REC.SALES-STATS-DATE"),
    ("sales_partial_ship_flag", "SALEDGER-REC.SALES-PARTIAL-SHIP-FLAG"),
    # -- L68  FILLER, `pic x(5)`, no column -------------------------------
    ("filler_l68", "WS-Sales-Record.filler#68"),
)

DICTIONARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    dict(_FIELD_KEYS)
)
"""Dotted attribute path to dictionary key, in copybook declaration order.

44 entries: the 37 column-mapped fields, the two column-less address
children, the two quarter group headers, the `STurnover-Q` view and the two
FILLER items. The `01`-level group's own key is `RECORD_KEY`, since the `01`
level is the class rather than one of its attributes.

Read-only. A caller that needs the entry itself passes a value from here to
`loader.get_entry`; for the three-locator provenance string, to
`loader.cite`; for the disagreement between the three layers, to
`loader.drift_for`.
"""

FIELD_DESCRIPTORS: Final[Mapping[str, FieldDescriptor]] = MappingProxyType(
    {
        path: FieldDescriptor.from_dictionary_key(key)
        for path, key in _FIELD_KEYS
    }
)
"""Dotted attribute path to `FieldDescriptor`, in declaration order.

Every descriptor reports the COPYBOOK view of its field - usage, digits,
scale, signedness, sign position and Python carrier - and none is blended
with the bridge or column view. Built entirely by
`FieldDescriptor.from_dictionary_key`: all 45 items of this record have
dictionary entries, so `for_working_storage` is needed for none of them and
appears nowhere in this module.

The disagreement between the three layers is reached from a descriptor by
`drift()`, and its registered references by `anomaly_refs()` and
`ambiguity_refs()`. For the eleven narrowed binary fields those answer
`('A-11',)` and `('Q-3',)`; for the money fields they answer `()`.
"""


def _condition_names(
    field_keys: tuple[tuple[str, str], ...] = _FIELD_KEYS,
) -> Mapping[str, tuple[ConditionName, ...]]:
    """Collect the `88`-level condition names the copybook declares.

    Each item's copybook view is asked for the condition names it already
    carries, so every name, its value-clause text and its locator are DERIVED
    from the dictionary rather than retyped here (rule R-5). An item that
    declares none is absent from the result rather than mapped to an empty
    tuple, so membership is a meaningful test.

    Written as a function rather than a comprehension on purpose: the
    assignment-expression form binds its temporaries in the ENCLOSING scope,
    which at module level is the module's own namespace, and this module
    publishes only the names in `__all__`.

    Args:
        field_keys: Attribute-path and dictionary-key pairs to read, in
            declaration order. Defaults to this record's own 44 pairs; it is
            a parameter so that the bridge-only arm below is reachable, since
            all 44 of this record's items do have a copybook view.

    Returns:
        A read-only mapping of dotted attribute path to the tuple of
        `ConditionName` triples declared on that item.

    A key whose field is declared only by the bridge and by no copybook at all
    contributes nothing: `loader.copybook_field_for` answers None for it, and
    fourteen such keys exist in this dictionary - the internal IRS posting
    table's three derived date components among them. None belongs to this
    record, but the arm is correct against the contract that function
    publishes rather than against this one caller's key set.
    """
    collected: dict[str, tuple[ConditionName, ...]] = {}
    for path, key in field_keys:
        copybook_field = loader.copybook_field_for(key)
        if copybook_field is None:
            continue
        declared = tuple(copybook_field.condition_names)
        if declared:
            collected[path] = declared
    return MappingProxyType(collected)


CONDITION_NAMES: Final[Mapping[str, tuple[ConditionName, ...]]] = (
    _condition_names()
)
"""Dotted attribute path to the `88`-level condition names declared on it.

Seven entries carrying eight condition names between them, in declaration
order, taken from the dictionary rather than restated. `Sales-Status` carries
two [copybooks/wssl.cob:L26-L27]; the other six carry one each.

Each `ConditionName` holds the name with its case preserved, the value clause
as TEXT exactly as written - `1`, `zero`, `"Y"` with its quote characters -
and the copybook line that declares it. Rule R-2 keeps a number out of a
member where precision could be lost, and rule R-4 forbids respelling a
source, so `value 1` and `value zero` stay two spellings of one idea.

Data only. Turning a condition name into a predicate over a record belongs to
`acas_posting/cobol/condition_names.py` (Agent Action Plan section 0.4.1.4),
which is why this module declares no predicate, no accessor and no
enumeration for these eight names.
"""


# =============================================================================
#  DEFAULTS - WHAT `INITIALIZE` WOULD STORE, AND NOTHING CLEVERER
# =============================================================================
#
# The bridge's load paragraph opens with `initialize TD-SALEDGER-REC.`
# [common/salesMT.cbl:L1204], so an unset field reaches SQL as zero or space
# and never as NULL, and every one of the 37 columns is NOT NULL with no
# column default [mysql/ACASDB.sql:L945-L984]. Defaults below follow that:
# never `None`, and never a sentinel of any kind.
#
# Alphanumeric items default to SPACES at the width the copybook declares,
# taken from the field's own descriptor so that no width is retyped here. The
# alternative, an empty string, was rejected for a stated reason: the record's
# 40 elementary items sum to exactly the 300 bytes its header declares
# [copybooks/wssl.cob:L7], and a space-filled default is the only one that
# holds that true for a freshly built instance. Nothing pads, trims or
# validates afterwards - this module declares no post-initialisation hook of
# any kind, and storing a value at its declared width belongs instead to
# `acas_posting.cobol.move`.

_ZERO_MONEY: Final[Decimal] = Decimal("0.00")
"""Zero at scale 2, the scale every `comp-3` money field here declares.

Written as a string literal so the value is exact and its scale explicit;
`Decimal` never sees a binary floating-point value anywhere in this package
(rule R-2).
"""

_QUARTER_ZEROS: Final[tuple[Decimal, Decimal, Decimal, Decimal]] = (
    _ZERO_MONEY,
    _ZERO_MONEY,
    _ZERO_MONEY,
    _ZERO_MONEY,
)
"""The four-element default for `STurnover-Q`, whose OCCURS is 4.

A tuple, so it is immutable and safe as a dataclass default, and so that two
runs cannot differ through a shared mutable default (rule R-6).
"""


def _spaces(path: str) -> str:
    """SPACES at the width the copybook declares for one field.

    The width is read from the field's own `FieldDescriptor`, so it is never
    retyped in this module and cannot drift from the copybook. Called only
    while the classes below are being defined, to build a default.

    Args:
        path: A dotted attribute path, as `DICTIONARY_KEYS` keys them.

    Returns:
        A string of that many spaces. Empty for an item with no declared
        character width, which no alphanumeric field of this record is - every
        one of the eleven declares a width, so that branch is unreachable
        here and exists only so this helper cannot answer with `None`.
    """
    width = FIELD_DESCRIPTORS[path].character_length
    return " " * width if width is not None else ""


# =============================================================================
#  THE SUBORDINATE GROUPS
# =============================================================================


@dataclass(slots=True)
class SalesAddress:
    """`03  Sales-Address.` [copybooks/wssl.cob:L18] - two lines of address.

    A COBOL group of two 48-character children [copybooks/wssl.cob:L19-L20].
    The group is what the bridge and the schema see: ONE
    `HV-SALES-ADDRESS PIC X(96)` [common/salesMT.cbl:L287], moved whole by
    `move Sales-ADDRESS to HV-SALES-ADDRESS` [common/salesMT.cbl:L1207], into
    ONE `SALES-ADDRESS char(96)` column [mysql/ACASDB.sql:L948]. So neither
    child has a column of its own, and both are declared here anyway, because
    rule R-3 forbids removing what the copybook declares. Their dictionary
    entries are copybook-only, keyed on `WS-Sales-Record.` rather than on the
    table - see `DICTIONARY_KEYS`.

    Mutable, never a frozen dataclass, for the reason given in this module's
    docstring. `slots=True` closes the class at these two fields.

    Attributes:
        sales_addr1: First address line, 48 characters.
        sales_addr2: Second address line, 48 characters.
    """

    # `05  Sales-Addr1    pic x(48).`                                     L19
    # No column of its own; covered by SALES-ADDRESS char(96) with L20.
    sales_addr1: str = _spaces("sales_address.sales_addr1")

    # `05  Sales-Addr2    pic x(48).`                                     L20
    # No column of its own; covered by SALES-ADDRESS char(96) with L19.
    sales_addr2: str = _spaces("sales_address.sales_addr2")


@dataclass(slots=True)
class Quarters:
    """`03  Quarters.` [copybooks/wssl.cob:L56] - four quarterly turnovers.

    Each child is `pic s9(8)v99 comp-3` [copybooks/wssl.cob:L57-L60]: packed
    decimal, ten digits, scale 2, SIGNED - and signed at all three layers,
    `PIC S9(08)V9(02) COMP` in the bridge [common/salesMT.cbl:L315-L318] and
    `decimal(10,2)` in the schema [mysql/ACASDB.sql:L976-L979]. They are part
    of the clean pass-through that makes anomaly A-11 specific rather than
    systemic: money keeps its sign where the statistics fields lose theirs.

    The group is redefined immediately afterwards by `QuartersView`, which
    presents the same 24 bytes as a four-element table. Both are declared,
    in the copybook's order, and neither is designated the real one.

    Attributes:
        turnover_q1: First quarter's turnover.
        turnover_q2: Second quarter's turnover.
        turnover_q3: Third quarter's turnover.
        turnover_q4: Fourth quarter's turnover.
    """

    # `05  Turnover-Q1    pic s9(8)v99   comp-3.`                        L57
    turnover_q1: Decimal = _ZERO_MONEY

    # `05  Turnover-Q2    pic s9(8)v99   comp-3.`                        L58
    turnover_q2: Decimal = _ZERO_MONEY

    # `05  Turnover-Q3    pic s9(8)v99   comp-3.`                        L59
    turnover_q3: Decimal = _ZERO_MONEY

    # `05  Turnover-Q4    pic s9(8)v99   comp-3.`                        L60
    turnover_q4: Decimal = _ZERO_MONEY


@dataclass(slots=True)
class QuartersView:
    """`03  filler redefines Quarters.` [copybooks/wssl.cob:L61] as a table.

    THE COBOL GROUP HAS NO NAME. It is declared as an unnamed `filler` that
    redefines `Quarters`, so `QuartersView` is a Python name for something the
    copybook does not name at all. `records/gl_ledger.py` meets the identical
    shape at [copybooks/wsledger.cob:L35-L36] and names it the same way -
    group name plus `View` - so that a reader moving between the two record
    modules meets one convention. The two modules share no code; record
    modules never import one another.

    Its single child is
    `05  STurnover-Q    pic s9(8)v99   comp-3 occurs  4.`
    [copybooks/wssl.cob:L62] - the same ten-digit, scale-2, signed packed
    decimal as the four named fields, presented as a four-element table. The
    areas balance exactly: 6 bytes times 4 occurrences against four 6-byte
    fields.

    A REDEFINES IS NOT A CHOICE. `Quarters` and this view describe the SAME
    24 bytes through two declarations. Neither is the real one, neither is
    derived from the other, and nothing here designates one of them or keeps
    the two in step: no property switches between them, no value is copied
    across, and no arithmetic reads one and writes the other. Rule R-4 makes
    the source's shape the specification, and its shape is two declarations
    over one area.

    COBOL SUBSCRIPTS ARE 1-BASED. `STurnover-Q (1)` is the first quarter, so
    it is `sturnover_q[0]` here. That offset is left in the open on purpose -
    no accessor hides it, because a hidden offset is how an off-by-one enters
    a posting.

    Attributes:
        sturnover_q: The four turnovers as a fixed four-element tuple. A
            tuple rather than a list, so a shared default cannot be mutated
            and two runs cannot diverge through it (rule R-6).
    """

    # `05  STurnover-Q    pic s9(8)v99   comp-3 occurs  4.`              L62
    # Redefines the four named fields of `Quarters` [L57-L60]; same 24 bytes.
    sturnover_q: tuple[Decimal, Decimal, Decimal, Decimal] = _QUARTER_ZEROS


# =============================================================================
#  THE RECORD
# =============================================================================


@dataclass(slots=True)
class WsSalesRecord:
    """`01  WS-Sales-Record.` [copybooks/wssl.cob:L12] - a customer account.

    The Sales Ledger account record: 37 attributes in copybook declaration
    order, L13 through L68, backed by the 37 columns of `SALEDGER-REC`
    [mysql/ACASDB.sql:L945-L984] through handler `acas012` and bridge
    `salesMT`. Read, changed and rewritten in place by `sl055`, `sl060` and
    `sl100`.

    Set this class beside `copybooks/wssl.cob` and the two compare line for
    line. Each attribute carries a comment holding its COBOL name verbatim,
    its PICTURE or USAGE as written, any inline comment the maintainer left,
    and its locator. Where a comment is marked STALE it contradicts the
    declaration beside it and the DECLARATION governs - see this module's
    docstring, which names all eleven such items.

    THE TYPES ARE THE POINT. Nine of these attributes are `int` because their
    items are `binary-short` or `binary-long` and therefore carry no
    fractional part, and that integer truncation is what makes anomalies A-8,
    A-9 and A-10 reproducible in the program modules. `sales_discount` is
    `Decimal` because its item is `comp` WITH a `V`. Both directions of that
    one rule live in this record; this module's docstring states them.

    Mutable by design, and never a frozen dataclass: the posting steps change
    an account in place, and a shape that forced a copy would make a
    lost-update defect avoidable where rule R-4 requires it stay reproducible.
    `slots=True` closes the class at these 37 fields, so an attribute the
    copybook does not declare cannot be attached by accident (rule R-3).

    No attribute defaults to `None`, because the bridge initialises its
    host-variable group before loading [common/salesMT.cbl:L1204] and every
    column is NOT NULL. There is no validation, no padding and no rounding on
    construction.

    Attributes:
        ws_sales_key: `pic x(7)` - the account key and the table's primary
            key. The copybook's commented-out redefinition of it
            [copybooks/wssl.cob:L14-L16] is NOT modelled and no check digit
            is verified here.
        sales_name: `pic x(30)` - the customer name.
        sales_address: The two-line address group, whose two children share
            ONE 96-character column.
        sales_phone: `pic x(13)`.
        sales_ext: `pic x(4)` - telephone extension.
        sales_email: `pic x(30)`.
        sales_fax: `pic x(13)`.
        sales_status: `pic 9` - live or dead. Carries two condition names.
        sales_late: `pic 9` - late-charge switch.
        sales_dunning: `pic 9` - reminder-letter switch.
        email_invoice: `pic 9` - e-mail the invoice.
        email_statement: `pic 9` - e-mail the statement.
        email_letters: `pic 9` - e-mail the reminder letters.
        delivery_tag: `pic 9`. Column `DELIVERY-TAG`
            [mysql/ACASDB.sql:L959] - a field of THIS table, not to be
            confused with the out-of-scope delivery table.
        notes_tag: `pic 9`.
        filler_l40: FILLER, three characters, no column.
        sales_credit: `pic 99` - credit period in days.
        sales_discount: `pic 99v99 comp` - `Decimal` at scale 2, unsigned.
        sales_late_min: `binary-short` - `int`, signed 16-bit.
        sales_late_max: `binary-short` - `int`, signed 16-bit.
        sales_limit: `binary-long` - `int`, signed 32-bit.
        sales_activety: `binary-long` - `int`. Misspelt in the copybook, the
            bridge and the column alike; the spelling is part of the key.
        sales_last_inv: `binary-long` - `int`, a day number.
        sales_last_pay: `binary-long` - `int`, a day number.
        sales_average: `binary-long` - `int`. The textbook case of anomaly
            A-11 and the field whose integer truncation makes A-8 visible.
        sales_pay_activety: `binary-long` - `int`. Misspelt as above.
        sales_pay_average: `binary-long` - `int`.
        sales_pay_worst: `binary-long` - `int`, a watermark.
        sales_create_date: `binary-long` - `int`. Its column drops the
            trailing `E`: `SALES-CREATE-DAT`.
        sales_current: `pic s9(8)v99 comp-3` - `Decimal`, signed, scale 2.
        sales_last: `pic s9(8)v99 comp-3` - `Decimal`, signed, scale 2.
        quarters: The four named quarterly turnovers.
        quarters_view: The same 24 bytes as a four-element table.
        sales_unapplied: `pic s9(8)v99 comp-3` - `Decimal`, signed, scale 2.
        sales_stats_date: `pic 9(4)` - NUMERIC in the copybook, `int` here,
            though its column is `char(4)`.
        sales_partial_ship_flag: `pic x` - back-order switch, declared across
            two physical lines.
        filler_l68: FILLER, five characters, no column.
    """

    # -- L13 ---------------------------------------------------------------
    # `03  WS-Sales-Key       pic x(7).`                                  L13
    # Primary key `SALES-KEY char(7)` [mysql/ACASDB.sql:L946].
    # L14-L16 commented-out redefinition NOT modelled - see module docstring.
    ws_sales_key: str = _spaces("ws_sales_key")

    # -- L17 ---------------------------------------------------------------
    # `03  Sales-Name         pic x(30).`                                 L17
    sales_name: str = _spaces("sales_name")

    # -- L18 .. L20  GROUP; the bridge concatenates it into one X(96) ------
    # `03  Sales-Address.`                                                L18
    sales_address: SalesAddress = field(default_factory=SalesAddress)

    # -- L21 .. L24 --------------------------------------------------------
    # `03  Sales-Phone        pic x(13).`                                 L21
    sales_phone: str = _spaces("sales_phone")

    # `03  Sales-Ext          pic x(4).`                                  L22
    sales_ext: str = _spaces("sales_ext")

    # `03  Sales-Email        pic x(30).`                                 L23
    sales_email: str = _spaces("sales_email")

    # `03  Sales-Fax          pic x(13).`                                 L24
    sales_fax: str = _spaces("sales_fax")

    # -- L25 .. L39  zoned single-digit switches; each widens to 9(03) at --
    # -- the bridge and to tinyint(1) unsigned in the schema (drift KIND 5) -
    # `03  Sales-Status       pic 9.`                                     L25
    # 88 Customer-Live value 1.  L26   88 Customer-Dead value zero.  L27
    sales_status: int = 0

    # `03  Sales-Late         pic 9.`                                     L28
    # 88 Late-Charges value 1.                                            L29
    sales_late: int = 0

    # `03  Sales-Dunning      pic 9.       *> Reminder letters`            L30
    # 88 Dunning-Letters value 1.                                         L31
    sales_dunning: int = 0

    # `03  Email-Invoice      pic 9.`                                     L32
    # 88 Email-Invoicing value 1.                                         L33
    email_invoice: int = 0

    # `03  Email-Statement    pic 9.`                                     L34
    # 88 Email-Statementing value 1.                                      L35
    email_statement: int = 0

    # `03  Email-Letters      pic 9.`                                     L36
    # 88 Email-Dunning value 1.  - the name does not match the field's;    L37
    # both spellings are the maintainer's and both are kept as they stand.
    email_letters: int = 0

    # `03  Delivery-Tag       pic 9.`                                     L38
    delivery_tag: int = 0

    # `03  Notes-Tag          pic 9.`                                     L39
    notes_tag: int = 0

    # -- L40  FILLER --------------------------------------------------------
    # `03  filler             pic xxx.`                                   L40
    # COBOL name is `filler`; the width is spelt as three `x` characters
    # rather than `x(3)`, and is recorded that way. Named for its line number
    # here because the record declares three separate FILLER items and a
    # Python attribute name has to be unique. No column carries it.
    filler_l40: str = _spaces("filler_l40")

    # -- L41 .. L42 --------------------------------------------------------
    # `03  Sales-Credit       pic 99.                    *> In days`      L41
    sales_credit: int = 0

    # `03  Sales-Discount     pic 99v99          comp.`                   L42
    # `comp` WITH a `V`, so `Decimal` at scale 2 and NOT `int`. Four digits,
    # unsigned; column `SALES-DISCOUNT decimal(4,2) unsigned`
    # [mysql/ACASDB.sql:L962]. Typing this one `int` would drop every pence.
    sales_discount: Decimal = _ZERO_MONEY

    # -- L43 .. L53  THE ELEVEN SIGNED BINARY ITEMS ------------------------
    # Every one is signed at the copybook and unsigned from the bridge
    # onwards [common/salesMT.cbl:L302-L312] - anomaly A-11, open question
    # Q-3. Every one carries an inline comment that CONTRADICTS its
    # declaration; the comment is reproduced verbatim and marked STALE, and
    # the DECLARATION governs. No digits, scale or signedness is taken from
    # any of them. All are `int`: no `V`, so no fractional part.
    #
    # `03  Sales-Late-Min     binary-short. *> 9999 comp`                 L43
    # STALE comment: `binary-short` is a signed 16-bit integer, not `9999`.
    sales_late_min: int = 0

    # `03  Sales-Late-Max     binary-short. *> 9999 comp`                 L44
    # STALE comment, as L43.
    sales_late_max: int = 0

    # `03  Sales-Limit        binary-long. *> 9(8) comp`                  L45
    # STALE comment: `binary-long` is a signed 32-bit integer, not `9(8)`.
    sales_limit: int = 0

    # `03  Sales-Activety     binary-long. *> 9(8) comp`                  L46
    # STALE comment, as L45. The name is MISSPELT in the copybook and the
    # misspelling is carried by `HV-SALES-ACTIVETY`
    # [common/salesMT.cbl:L305] and by column `SALES-ACTIVETY`
    # [mysql/ACASDB.sql:L966], so it is part of the dictionary key and of the
    # SQL. Respelling it would break both. Stepped at [sales/sl060.cbl:L825]
    # and NOT stepped in the credit path [sales/sl060.cbl:L832-L843] - A-9.
    sales_activety: int = 0

    # `03  Sales-Last-Inv     binary-long. *> 9(8) comp`                  L47
    # STALE comment, as L45. A day number; it consults no clock here.
    sales_last_inv: int = 0

    # `03  Sales-Last-Pay     binary-long. *> 9(8) comp`                  L48
    # STALE comment, as L45. A day number; it consults no clock here.
    sales_last_pay: int = 0

    # `03  Sales-Average      binary-long. *> 9(8) comp`                  L49
    # STALE comment, as L45.
    # THE TEXTBOOK CASE OF A-11, and the single most consequential type in
    # this folder. SIGNED here [copybooks/wssl.cob:L49]; unsigned as
    # `HV-SALES-AVERAGE PIC  9(10) COMP` [common/salesMT.cbl:L308]; unsigned
    # as `SALES-AVERAGE int(8) unsigned` [mysql/ACASDB.sql:L969].
    # `int` because the item is binary: the quotient taken into it at
    # [sales/sl060.cbl:L827] therefore truncates as an integer quotient, and
    # that is what makes A-8 reproducible. Typing it `Decimal` would carry a
    # remainder the compiled program discards and would repair A-8, A-9 and
    # A-10 at once, which rule R-4 counts as a failure.
    sales_average: int = 0

    # `03  Sales-Pay-Activety binary-long. *> 9(8) comp`                  L50
    # STALE comment, as L45. MISSPELT as at L46, and likewise carried through
    # `HV-SALES-PAY-ACTIVETY` [common/salesMT.cbl:L309] to column
    # `SALES-PAY-ACTIVETY` [mysql/ACASDB.sql:L970].
    sales_pay_activety: int = 0

    # `03  Sales-Pay-Average  binary-long. *> 9(8) comp`                  L51
    # STALE comment, as L45. The cash path takes its quotient into this field
    # at [sales/sl100.cbl:L511], from a `binary-long` accumulator
    # [sales/sl100.cbl:L182-L183] - a third guard variant, part of A-10.
    sales_pay_average: int = 0

    # `03  Sales-Pay-Worst    binary-long. *> 9(8) comp`                  L52
    # STALE comment, as L45. A watermark, raised at [sales/sl100.cbl:L514].
    sales_pay_worst: int = 0

    # `03  Sales-Create-Date  binary-long. *> 9(8) comp`                  L53
    # STALE comment, as L45. NAME TRUNCATION at the bridge: the host variable
    # is `HV-SALES-CREATE-DAT` [common/salesMT.cbl:L312] and the column is
    # `SALES-CREATE-DAT` [mysql/ACASDB.sql:L973] - the trailing `E` is gone,
    # as the bridge's own move shows [common/salesMT.cbl:L1232]. Its key is
    # therefore `SALEDGER-REC.SALES-CREATE-DAT`, which no transformation of
    # this attribute name would produce.
    sales_create_date: int = 0

    # -- L54 .. L55  money; SIGNED at all three layers ---------------------
    # `03  Sales-Current      pic s9(8)v99       comp-3.`                 L54
    sales_current: Decimal = _ZERO_MONEY

    # `03  Sales-Last         pic s9(8)v99       comp-3.`                 L55
    sales_last: Decimal = _ZERO_MONEY

    # -- L56 .. L60  GROUP -------------------------------------------------
    # `03  Quarters.`                                                     L56
    quarters: Quarters = field(default_factory=Quarters)

    # -- L61 .. L62  GROUP, unnamed in COBOL, redefining L56 ---------------
    # `03  filler redefines Quarters.`                                    L61
    # Declared second because the copybook declares it second. It describes
    # the SAME 24 bytes as `quarters`; neither is designated the real one and
    # nothing here keeps the two in step.
    quarters_view: QuartersView = field(default_factory=QuartersView)

    # -- L63 ---------------------------------------------------------------
    # `03  Sales-Unapplied    pic s9(8)v99   comp-3.`                     L63
    sales_unapplied: Decimal = _ZERO_MONEY

    # -- L64 ---------------------------------------------------------------
    # `03  Sales-Stats-Date   pic 9(4).             *> added 15/01/18.`   L64
    # TYPE-CLASS DRIFT, numeric to character, and the only instance of it in
    # this folder. Declared NUMERIC - zoned DISPLAY, four digits, scale 0 -
    # yet the host variable is `HV-SALES-STATS-DATE PIC X(4)`
    # [common/salesMT.cbl:L320] and the column is
    # `SALES-STATS-DATE char(4)` [mysql/ACASDB.sql:L981].
    # `int` here because a descriptor reports the COPYBOOK view. It is NOT
    # retyped `str` to agree with the column, and the two views are not
    # reconciled: the conversion belongs to `dal/acas012_sales.py`, and the
    # column's own view is reached through `loader.column_for`.
    sales_stats_date: int = 0

    # -- L65 .. L66  ONE declaration across TWO physical lines -------------
    # `03  Sales-Partial-Ship-Flag`                                       L65
    # `                    pic x.                *> added 06/02/24`       L66
    # A line-oriented reader takes L65 for a group and loses the PICTURE
    # entirely; the two lines are one `pic x` item.
    # 88 Sales-BO-Set value "Y".  *> added 17/03/24                       L67
    # The condition-name value keeps its quote characters - see
    # `CONDITION_NAMES`. Three separate dated stamps mark this area's growth,
    # at L64, L66 and L67, and all three are reproduced verbatim above.
    sales_partial_ship_flag: str = _spaces("sales_partial_ship_flag")

    # -- L68  FILLER --------------------------------------------------------
    # `03  filler             pic x(5).`                                  L68
    # COBOL name is `filler`; named for its line number here, as at L40. Five
    # characters, no column. The header explains why this FILLER is five
    # rather than six characters wide: the partial-ship flag was taken out of
    # it in 2024 with "no rec size change"
    # [copybooks/wssl.cob:L9-L10]. The record still sums to the 300 bytes the
    # header declares [copybooks/wssl.cob:L7].
    filler_l68: str = _spaces("filler_l68")
