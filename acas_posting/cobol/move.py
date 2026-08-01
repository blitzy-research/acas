"""The COBOL `MOVE` verb: receiving-field data-movement semantics.

A `MOVE` IS NOT AN ASSIGNMENT. Agent Action Plan section 0.1.2,
transformation rule 11, verbatim:

    #   COBOL construct              Python construct
    11  `MOVE` between unlike        Explicit truncate/pad helper
        pictures
    Transformation rule: "Sending-field-to-receiving-field rules, not
                          assignment"

Every `MOVE` is governed by the RECEIVING field. An alphanumeric item is
filled from the left, padded with spaces on the right and truncated on the
RIGHT. A numeric item is aligned on its implied decimal point and truncated
or zero-padded on BOTH ends independently. Getting the direction of
truncation backwards corrupts data silently, with no error either way, and
nothing will report it except a non-empty state diff.

THE AUTHORITY FOR THIS FILE
===========================
Agent Action Plan section 0.3.1 fixes it in one line:

    move.py    (MOVE truncation, space padding, justification)

Agent Action Plan section 0.4.1.4, the transformation row, verbatim:

    Target File                    Transformation  Source File
    acas_posting/cobol/move.py     CREATE          the in-scope `MOVE`
                                                   statements
    Key Changes: "Receiving-field truncation, space padding and
                  justification"

Rule R-1 names this file among those that "reimplement picture-clause
parsing, the six storage classes, the arithmetic verbs, `MOVE` truncation,
condition-name evaluation and `SORT` key semantics".

ZERO BUSINESS LOGIC
===================
Agent Action Plan section 0.3.1, verbatim: "`cobol/` contains no business
logic and `programs/` contains no numeric primitives." And section 0.1.2 on
this package: it "contains no business logic whatsoever."

So no posting rule, no calendar decision, no print-line layout and no
account number appears below. This module supplies the movement mechanics;
`acas_posting.programs.*` decides what is moved where. Every business noun
in this file appears inside a docstring or a locator-citing comment, never
as an identifier and never as a literal.

THE `MOVE` CENSUS
=================
`MOVE` is the most-executed primitive in the whole migration. Agent Action
Plan section 0.4.1 gives the census below, and `MOVE_CENSUS` publishes it as
data. Its figures count LINES CONTAINING THE WORD `move`, comment lines
included, and they reproduce exactly against the frozen checkout for eleven
of the twelve program files.

    general/gl051.cbl  157     sales/sl055.cbl   91
    general/gl070.cbl   66     sales/sl060.cbl  177
    general/gl071.cbl    0     sales/sl100.cbl  124
    general/gl072.cbl   59     purchase/pl055.cbl  91
    general/gl080.cbl   48     purchase/pl060.cbl 165
                               purchase/pl100.cbl 122
                               irs/irs030.cbl     190

A second census was taken here, counting only the lines that BEGIN a live
`MOVE` statement, and it totals 1,250 rather than 1,290. Both are published,
each with the measurement that produced it - `MOVE_CENSUS` and
`MOVE_STATEMENT_CENSUS` - because a single number whose method is unstated
is a number a later reader cannot check. `general/gl071.cbl` measures ZERO
either way: it is a pure sort and contains no `MOVE` at all.

THE FIVE MOVE CATEGORIES, AND THE DIRECTION EACH TRUNCATES
==========================================================
(a) ALPHANUMERIC from ALPHANUMERIC. Filled from the left, padded with
    spaces on the right, truncated on the RIGHT. `Post-Legend pic x(32)`
    [copybooks/wspost.cob:L24], `Post-Code pic xx`
    [copybooks/wspost.cob:L17] and `Ledger-Name pic x(24)`
    [copybooks/wsledger.cob:L27] are all such receivers, and all three are
    database columns. `move_alphanumeric` implements it, delegating the
    truncate-and-pad step to `acas_posting.cobol.usage.coerce` so that one
    implementation of the rule exists.

(b) NUMERIC from NUMERIC. Aligned on the implied decimal point, then
    truncated or zero-padded at BOTH ends independently. `move zero to
    tot-dr tot-cr.` [general/gl072.cbl:L411] and `move work-net to
    Post-Amount.` [sales/sl060.cbl:L1076], whose receiver is `Post-Amount
    pic s9(8)v99` [copybooks/wspost.cob:L23]. `move_numeric` implements it
    by DELEGATING to `acas_posting.cobol.arithmetic.store`, which already
    owns scale alignment, the unsigned sign drop and silent high-order
    truncation. Two truncation code paths would mean one of them was
    eventually wrong.

    Storing into an UNSIGNED receiver drops the sign: `Input-Gross` through
    `Actual-Vat` are `pic 9(9)v99` with no sign, under `03 Amounts comp-3.`
    [copybooks/wsbatch.cob:L40-L44]. That is already numbered open question
    Q-3 and is not renumbered here.

    Storing into a `SIGN LEADING` receiver keeps the sign in the leading
    position: `pic s9(7)v99   sign leading`
    [copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25], and
    `sign is leading` [copybooks/irswspost.cob:L14],
    [copybooks/irswspost.cob:L18]. The byte form belongs to
    `acas_posting.cobol.usage`, which this module delegates to; the two
    spellings are left exactly as the frozen copybooks write them and are
    never reconciled into one.

(c) ALPHANUMERIC from NUMERIC and (d) NUMERIC from ALPHANUMERIC. Both
    occur, because a `pic 9(n)` DISPLAY item IS a character field in COBOL:
    `move WS-Batch-nos to Batch.` [sales/sl060.cbl:L1073] moves into `Batch
    pic 9(5)` [copybooks/wspost.cob:L15]. The digit-string image of a
    numeric sending item is its declared width, zero-filled, with the sign
    where its SIGN clause puts it - so `pic 9(5)` holding 42 has the image
    `00042` and not `42`. Pass `sending_field` to get that image;
    `acas_posting.cobol.usage.encode` produces it. Both
    `acas_posting.cobol.usage._require_text` and `_stored_text` defer this
    category crossing here by name, and this is where it lives.

(e) A FIGURATIVE CONSTANT, which has no sending field at all. Moving `ZERO`
    into an alphanumeric item fills it with the character `0`; moving
    `SPACE` into a numeric item leaves spaces in its bytes, which then fail
    a numeric class test - see Q-9. `move zero to tot-dr tot-cr.`
    [general/gl072.cbl:L411] and `move space to oi-applied oi-unapl
    oi-hold-flag.` [sales/sl055.cbl:L655].

MULTIPLE RECEIVERS, EACH APPLYING ITS OWN RULES
===============================================
One `MOVE` may name several receivers, and each applies its own truncation
independently. The decisive exemplar is [general/gl051.cbl:L1017]:

    move   batch  to  l4-batch save-batch WS-Batch-Nos

Three receivers of three DIFFERENT descriptions - `l4-batch pic z(4)9`, a
numeric-edited item [general/gl051.cbl:L289]; `save-batch pic 9(5) comp`, a
binary item [general/gl051.cbl:L174]; and `WS-Batch-Nos pic 9(5)`, a zoned
DISPLAY item [copybooks/wsbatch.cob:L19]. One sending value, three
different stored results. `move_to_all` therefore takes a SEQUENCE of
receiving descriptors and returns one value PER RECEIVER, in receiver
order, as a tuple - never one value reused.

Ten further multi-receiver sites were verified: [general/gl051.cbl:L982],
[general/gl051.cbl:L1041], [general/gl070.cbl:L400],
[general/gl072.cbl:L281], [general/gl072.cbl:L411],
[general/gl072.cbl:L452], [sales/sl055.cbl:L539],
[sales/sl055.cbl:L653], [sales/sl060.cbl:L489] and
[sales/sl060.cbl:L546].

GROUP MOVES
===========
A `MOVE` whose receiver is a GROUP item is an alphanumeric move of the
group's whole byte image, with NO per-field conversion of any kind. Groups
are everywhere in the frozen layouts: `03 WS-Post-Key.`
[copybooks/wspost.cob:L14], `03 Dates.` [copybooks/wsbatch.cob:L35],
`03 Amounts comp-3.` [copybooks/wsbatch.cob:L40] and `03 Quarters.`
[copybooks/wsledger.cob:L30]. A live one: `move WS-Analysis-Record to
WS-Value-Record` [sales/sl055.cbl:L538], whose two records do NOT have the
same width, so the move truncates.

A group has no width of its own - `FieldDescriptor.byte_length` says so and
tells a caller to sum its children - so `move_group` takes the width from
`length` if given, else from the descriptor's `character_length`, else from
the sending image's own length, which is the equal-width degenerate case.
Summing a group's children is the record layer's knowledge, not this
module's.

REFERENCE MODIFICATION IS 1-BASED
=================================
83 uses of the `(offset:length)` form were verified across the twelve
program files, on BOTH the sending and the receiving side.
`REFERENCE_MODIFICATION_CENSUS` publishes the frequencies: `(7:4)` x16,
`(4:2)` x16, `(1:2)` x16, `(9:2)` x9, `(1:6)` x8, `(6:2)` x5, `(1:4)` x5,
`(7:2)` x4, `(1:1)` x3 and `(1:22)` x1. Three further sites use variable
operands, all of them `m (b:c)`: [sales/sl060.cbl:L1091],
[purchase/pl060.cbl:L954] and [purchase/pl100.cbl:L608].

`ref_mod` and `ref_mod_into` take a 1-BASED offset and an explicit length,
so that a program module transcribes `(9:2)` as `offset=9, length=2` and a
reviewer can diff it against the frozen source character for character.
Translating to a 0-based slice at the call site is exactly the mistake this
signature exists to prevent.

THE SITE THAT MAKES THIS LOAD-BEARING  [sales/sl060.cbl:L1071-L1072]
====================================================================
    move  u-date (1:6) to post-date (1:6).
    move  u-date (9:2) to post-date (7:2).

The sending item is ten characters in `DD/MM/CCYY` form; the receiver is
`Post-Date pic x(8)` [copybooks/wspost.cob:L18], in `DD/MM/YY` form. Those
two statements are the ENTIRE four-digit-to-two-digit year conversion, done
by character surgery with no calendar logic whatsoever, and the receiver is
a database column. `[sales/sl100.cbl:L612-L613]` repeats the pair verbatim.

This module must not notice what those characters mean. It supplies the
movement; it does not know that a calendar is involved and it does not
improve a two-digit year. Agent Action Plan section 0.6.6 makes the two
coexisting text forms one of `harness/normalize.py`'s three jobs, and that
is where the concern belongs. An off-by-one here would corrupt every
posted row of that column, which is why `ref_mod` publishes 1-based offsets
and why the self-test for those two statements asserts the exact result.

NUMERIC-EDITED RECEIVERS - ONE SHAPE, AND ONLY ONE, IS CLAIMED
==============================================================
Agent Action Plan section 0.2.2 excludes "Report formatting BEYOND DATABASE
EFFECTS". The emphasis decides this file's scope: exactly one edited move
does have a database effect, and editing is a property of the `MOVE` verb,
so that one is implemented here. [sales/sl060.cbl:L1085-L1094]:

    move     oi-invoice to m.
    move     zero to b.
    inspect  m tallying b for leading space.
    subtract b from 8 giving c.
    add      1 to b.

    string   m (b:c)     delimited by size
             " : "       delimited by size
             sales-name  delimited by size
                          into Post-Legend pointer  xx.

`m` is `pic z(7)9` [sales/sl060.cbl:L213] and the result lands in
`Post-Legend pic x(32)` [copybooks/wspost.cob:L24] - a database column. The
maintainer's own comment above it states the intent
[sales/sl060.cbl:L1082-L1083]. Mirrored at [purchase/pl060.cbl:L207] with
[purchase/pl060.cbl:L947-L956], and at [purchase/pl100.cbl:L600-L610].
Note that `subtract b from 8 giving c` HARD-CODES 8, the field's own
length; a program module transcribes that literally rather than deriving
it.

`move_to_edited` implements the Z-suppression-then-9 shape and nothing
else: a run of `Z` positions followed by a run of `9` positions, one
character position per digit position, no insertion character anywhere.
`EDIT_SYMBOLS_IMPLEMENTED` names the two symbols. `z(7)9` and `z(4)9` are
the two live instances of that shape, and ONLY `z(7)9` is reachable from a
database write - `z(4)9` at [general/gl051.cbl:L289] is a print line.

Every other edited picture in the frozen sources - `z(6)9.99cr`,
`z(8)9.99b`, `bbbz9`, `9(8).99-`, `z(4)9b(4)`, `bz9bbbbbb` and their
siblings - receives into a print line with no database effect and is OUT OF
SCOPE. Such a picture reaches an explicitly UNVERIFIED fall-through, which
renders the digit positions and NO insertion characters, and which is
labelled as unverified at its definition and in Q-14. It is stated rather
than hidden, because an unreachable path must never masquerade as verified
behaviour. The insertion symbols `*`, `$`, `,`, `DB`, `+`, `/` and `0` are
not implemented at all: each occurs zero times.

WHY `INSPECT` AND `STRING` LIVE HERE
====================================
The folder requirement closes this folder at exactly eight files, verbatim:
"Nothing else. No `strings.py`, no `numeric.py`, no `helpers.py`." Three
in-scope programs nevertheless build a DATABASE field with `INSPECT ...
TALLYING ... FOR LEADING` and `STRING ... DELIMITED BY ... INTO ...
POINTER`. Those verbs are receiving-field character movement, they have a
database effect, and the permitted file set offers nowhere else for them.
They belong here, and they are named here so that no reader thinks they
were smuggled in.

    inspect_tallying_leading   [sales/sl060.cbl:L1087],
                               [purchase/pl060.cbl:L949],
                               [purchase/pl100.cbl:L603]
    string_into                [sales/sl060.cbl:L1091],
                               [sales/sl100.cbl:L622-L628],
                               [purchase/pl060.cbl:L954],
                               [purchase/pl100.cbl:L608],
                               [general/gl080.cbl:L531],
                               [irs/irs030.cbl:L1424]

The tally variable ACCUMULATES into whatever it already holds, which is
precisely why [sales/sl060.cbl:L1086] writes `move zero to b.` first.
`inspect_tallying_leading` reproduces the accumulate and never resets
implicitly.

A DIVERGENCE THAT MUST NOT BE UNIFIED
=====================================
[sales/sl100.cbl:L620-L628] builds the SAME 32-character database column
with FIVE separate `STRING` statements sharing ONE pointer, and it does not
use the edited-move or `INSPECT` idiom at all:

    move     1  to  xx.
    move     oi-b-nos to batch.
    string   batch delimited by size into post-legend pointer xx.
    move     WS-Batch-Nos  to  batch.
    string   "/" delimited by size into post-legend pointer xx.
    move     oi-b-item to k.
    string   k delimited by size into post-legend pointer xx.
    string   "  :  "   delimited  by size into post-legend pointer xx.
    string   sales-name delimited by size into post-legend pointer xx.

The maintainer flagged it himself at [sales/sl100.cbl:L618]: "THIS DOES NOT
APPEAR THE SAME as SL060 and PL060/PL100". It is a preserved divergence in
the same spirit as the three disagreeing moving-average guards, and rule
R-4 forbids unifying it. `string_into` therefore returns the updated
receiver AND the updated 1-based pointer, so five successive calls chain
through one pointer exactly as the five statements do. Note also that the
separator there is FIVE characters, `"  :  "`, and not the three-character
`" : "` of the `sl060` shape.

Both `DELIMITED BY SIZE` and `DELIMITED BY SPACE` are needed. A census of
the twelve program files finds `SIZE` 22 times and `SPACE` 3 times, and no
literal delimiter at all. `[general/gl080.cbl:L530-L536]` mixes the two in
one statement and carries NO `POINTER` phrase, so its pointer starts at 1;
`[irs/irs030.cbl:L1424-L1426]` is the same shape. Overflow is silent: the
receiver is 32 characters and the sources can exceed it - see Q-11.

WHAT THIS FILE DELIBERATELY DOES NOT OWN
========================================
`INSPECT ... REPLACING ALL "." BY "/"` is NOT this module's. It appears at
[general/gl051.cbl:L1178-L1180] and [irs/irs030.cbl:L1312-L1314], and Agent
Action Plan section 0.4.1.6 assigns the handling of the `.`, `,` and `-`
separators to `acas_posting/dates.py`, which is a standard-library-only
module and does not import this package.
The boundary is recorded here so the omission reads as deliberate.
`[irs/irs030.cbl:L1315]`, `inspect u-date tallying q for all "/"`, is the
`FOR ALL` form rather than `FOR LEADING` and sits inside that program's
out-of-scope validation section; only `Ledger-Postings-Add`
[irs/irs030.cbl:L1569-L1733] is migrated from `irs030`. It is found, named
and not implemented.

VERIFIED ZERO-OCCURRENCE FORMS, RECORDED SO THE OMISSIONS ARE DELIBERATE
========================================================================
`ZERO_OCCURRENCE_FORMS` publishes this list as data. Each was counted
across the twelve in-scope program files, and the first two across
`copybooks/*.cob` as well.

    MOVE CORRESPONDING   0 - not implemented
    JUSTIFIED            0 - in every program AND every copybook, so only
                             DEFAULT justification is implemented: from the
                             left for an alphanumeric item, on the implied
                             decimal point for a numeric one
    UNSTRING             0 - not implemented
    HIGH-VALUES          0 - not implemented
    LOW-VALUES           0 - not implemented
    QUOTES               0 - not implemented
    literal delimiter    0 - `DELIMITED BY` names only SIZE and SPACE

`ALL "x"` is the one entry that needs a precise statement rather than a
bare zero: it occurs FOUR times, and all four are VALUE clauses declaring
an initial value - [general/gl051.cbl:L265], [general/gl051.cbl:L269],
[general/gl072.cbl:L249] and [general/gl072.cbl:L251]. It occurs ZERO
times as a `MOVE` sending operand, which is the count that matters here, so
it is not implemented. Recording the four keeps the claim checkable.

The figurative constants that DO occur are `ZERO` (532 lines), `SPACES`
(138), `SPACE` (64) and `ZEROS` (12). `ZEROES` measures zero and is
accepted anyway, because it is the same word and refusing one spelling of
it would be a validation this module has no business adding.

A `MOVE` DOES NOT VALIDATE, AND NEITHER MAY THIS FILE  (rule R-3)
================================================================
Rule R-3, verbatim: "The migration may not add validation logic, add
fields, or alter the database schema, and must not introduce concurrent
execution." The folder requirement states the consequence for this file,
verbatim: "A COBOL `MOVE` does not validate; neither may `move.py`. A
`COMPUTE` that overflows its receiving field silently truncates high-order
digits; reproduce that rather than raising."

So, below:

  * NO length check that raises. A forty-character sending item moved into
    `Post-Legend pic x(32)` [copybooks/wspost.cob:L24] loses its last eight
    characters, silently, and that receiver is a database column.
  * NO range check that raises. `123456.78` into `pic 999v99` stores
    `456.78`, silently.
  * NO "is this really a number?" check that raises. See the A-13 note
    below; the whole point is that this module must not pre-empt it.
  * NO truncation courtesy of any kind - no ellipsis, no marker character,
    no warning suffix, no log record that alters control flow.
  * NO bounds check on a reference-modified range or on a subscript.
    Anomaly A-2 is precisely an unbounded index: a quarter subscript
    computed by a ROUNDED divide [general/gl080.cbl:L328] and then used
    without a bound [general/gl080.cbl:L345] against `Ledger-Q ... occurs
    4` [copybooks/wsledger.cob:L36]. Python's own slicing does not raise on
    an over-long slice; that behaviour is left to stand and is documented
    (Q-10) rather than guarded.
  * NO concurrency: no threading, no asyncio, no multiprocessing, no
    `concurrent.futures`, no coroutine.

EXACTLY ONE `raise` STATEMENT APPEARS IN THIS FILE, and it is the rule R-2
carrier gate in `_exact_carrier`. It fires on a value's Python TYPE, which
cannot appear anywhere in this migration, and never on a value's CONTENT,
which a COBOL program would have accepted. That distinction is the whole
difference between an R-2 type gate and an R-3 validation. Where a
programmer error must still be reported - an unrecognised figurative
spelling, an unrecognised delimiter - the enum constructor reports it, so
the mechanism is the standard library's and not a validation branch added
here.

ANOMALY A-13 DEPENDS ON THIS MODULE NOT VALIDATING
==================================================
`general/gl072.cbl` skips a posting whose batch number is NOT NUMERIC, and
the anomaly register records the skip as entirely silent - "no message,
counter or trace":

    if       post-batch  not numeric
             go to  loop.
                                        [general/gl072.cbl:L291-L292]

The anomaly register cites that construct as
`[general/gl072.cbl:L289-L290]`, and its sibling skip on a specific handler
error as `[general/gl072.cbl:L303-L304]`; in the frozen checkout the two
statements read at L291-L292 and L306-L307. The offset is recorded here
rather than reconciled silently, because the frozen file is the authority
and a reader following either citation should find both accounted for.

If this module raised on non-numeric text, that silent skip could never be
reproduced. So `is_numeric_class` is a PLAIN BOOLEAN PREDICATE that never
raises on content, and the skip itself is business logic belonging to
`acas_posting.programs.gl072_transaction_update`, not to this file.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
    MAY import        the standard library, the `acas_posting.dictionary`
                      public enums, and `acas_posting.cobol.field`,
                      `acas_posting.cobol.usage` and
                      `acas_posting.cobol.arithmetic`
    MUST NOT import   `acas_posting.records`, `acas_posting.dal`,
                      `acas_posting.programs`, `acas_posting.cli`,
                      `acas_posting.clock`, `acas_posting.dates`,
                      `acas_posting.workfiles`, the sibling compiled-oracle
                      tree, and the sibling semantics modules
                      `acas_posting.cobol.picture`,
                      `acas_posting.cobol.condition_names` and
                      `acas_posting.cobol.sortverb`
    No third-party import is permitted. The interpreter is pinned to
    `requires-python = "==3.12.*"`.

`acas_posting.cobol.arithmetic` is imported deliberately and not
reluctantly: a numeric `MOVE` performs the same scale alignment, unsigned
sign drop and silent high-order truncation as an arithmetic store, so it
delegates to `arithmetic.store` rather than reimplementing it. Because
`picture` may not be imported, the two-symbol reading of an edited
receiver's own picture below is local, deliberately minimal, and recognises
`Z` and `9` and nothing else.

`acas_posting.programs.*` imports THIS module. Nothing here imports back
toward it.

EXACT ARITHMETIC ONLY  (rule R-2)
=================================
Rule R-2, verbatim: "No accounting value may pass through a binary
floating-point type at any point - not in computation, not in storage, not
in transport." And, verbatim, on what it forces into scope: "Files this
rule forces into scope: the whole of `acas_posting/cobol/*.py`, and the
whole of `tests/arithmetic/` - fourteen test files whose only purpose is to
prove per-field exactness." Agent Action Plan section 0.1.2, rule 8, says
it in three words: "never a float."

A `MOVE` is transport, and transport is the quietest place in a system for
a lost penny. So a numeric value moved here is a `decimal.Decimal` or an
`int` and never anything else, and a positions-and-lengths value - a
reference-modification offset or length, a `STRING` pointer, an `INSPECT`
tally - is an `int` count. A binary floating-point carrier is refused by
`_exact_carrier` with a `TypeError`. No `math`, no rounding built-in, no
`pandas` and no `numpy` appear below; Agent Action Plan section 0.5.1 calls
the last two exclusion "absolute".

DETERMINISM  (rule R-6)
=======================
No clock, no environment, no randomness, and no `set` or `dict` iteration
whose order a caller can observe. `decimal` contexts are never touched
here: every decimal computation goes through
`acas_posting.cobol.arithmetic`, which enters its own explicit context, so
a result cannot vary with what a caller did earlier. Every published table
is a `tuple` or a `MappingProxyType`, and the two membership sets are
`frozenset`s consulted only for membership.

OPEN QUESTIONS - PROVISIONAL BEHAVIOUR, MARKED AS SUCH  (rule R-6)
==================================================================
Rule R-6, verbatim: "Where a semantic question is ambiguous, the compiled
program's observed behavior decides it, and each such resolution must be
documented rather than settled silently." Six questions below are this
module's own, in the `^Q-[0-9]+$` numbering space shared with
`data_dictionary/`. Q-2, Q-3, Q-4, Q-6, Q-7 and Q-8 are already in use,
and the sibling `acas_posting.cobol.usage` claimed Q-5.1, Q-5.2 and Q-5.3,
so Q-9 through Q-14 are the next free integers.

    Q-3   A MOVE INTO AN UNSIGNED NUMERIC RECEIVER. Not a new question:
          `acas_posting.cobol.arithmetic` already numbers it Q-3 and this
          module inherits both the number and its provisional answer, the
          absolute value stored. The unsigned receivers are real - `pic
          9(9)v99` under `03 Amounts comp-3.`
          [copybooks/wsbatch.cob:L41-L44].

    Q-9   `MOVE SPACE` INTO A NUMERIC `DISPLAY` FIELD. COBOL leaves spaces
          in the item's bytes, which then fail a numeric class test.
          PROVISIONAL, implemented below: the field's byte width filled
          with spaces, returned as text, and `is_numeric_class` reports
          False for it. This interacts directly with anomaly A-13, so it
          matters rather than being a curiosity.
          [sales/sl055.cbl:L655] and [general/gl072.cbl:L291-L292].

    Q-10  A REFERENCE-MODIFICATION RANGE THAT RUNS PAST THE FIELD.
          PROVISIONAL, implemented below: Python slicing semantics, so a
          short result rather than an error, and no raise (rule R-4). What
          GnuCOBOL 3.2 does with and without bounds checking has NOT been
          measured; the compile scripts select no dialect. An offset below
          1 is a Python negative index and would wrap - no in-scope site
          produces one, every literal offset being 1 through 9 and the one
          computed offset being a tally plus one.

    Q-11  A `STRING` POINTER BEYOND THE RECEIVER'S LENGTH. PROVISIONAL,
          implemented below: nothing further is written, silently, and a
          partially fitting source contributes the characters that fit.
          `Post-Legend pic x(32)` [copybooks/wspost.cob:L24] is the
          receiver, and the five-statement build at
          [sales/sl100.cbl:L620-L628] can exceed it. `ON OVERFLOW` occurs
          zero times across the twelve program files, so there is no error
          path in the specification to reproduce.

    Q-12  THE EXACT `z(7)9` RENDERING OF ZERO. With no `BLANK WHEN ZERO`,
          that picture's final `9` prints, so zero renders as seven spaces
          then `0`. PROVISIONAL, implemented below: exactly that. It
          changes a database column when the sending value is zero
          [sales/sl060.cbl:L1085], so it is a genuine question for the
          oracle and not a formatting nicety.

    Q-13  A NON-NUMERIC BYTE IMAGE MOVED INTO A NUMERIC RECEIVER, the
          general case behind Q-9. PROVISIONAL, implemented below: the
          text is kept and aligned to the right of the receiver's byte
          width, losing characters from the LEFT and padded on the left
          with spaces - never with zeros, which would fabricate digits the
          sending bytes do not contain. No raise, so `is_numeric_class`
          can report False afterwards and A-13 stays reproducible.

    Q-14  AN EDITED RECEIVING PICTURE OUTSIDE THE Z-THEN-9 SHAPE.
          PROVISIONAL, implemented below and labelled UNVERIFIED at its
          definition: the digit positions are rendered with no suppression
          and no insertion character. NO in-scope database write reaches
          it - every other edited picture in the frozen sources receives
          into a print line - so it has no oracle evidence behind it and
          claims none.

FURTHER READING
===============
    docs/migration/traceability.md           program-to-module,
                                             paragraph-to-function and
                                             field-to-dictionary-entry
                                             mappings
    docs/migration/anomaly-log.md            the register of legacy defects
                                             this migration reproduces,
                                             including A-2 and A-13 above
    docs/migration/ambiguity-resolutions.md  each semantic question and the
                                             compiled-behaviour arbitration
                                             that settled it, including
                                             Q-9 through Q-14 above

THE FREEZE
==========
Agent Action Plan section 0.8.1, verbatim: "Any diff touching
`common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`,
`sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a
defect in the migration, regardless of how harmless it appears." Every
frozen file cited above is read as specification and is never modified,
reformatted, commented, relocated or built from here.

A NOTE ON PROVENANCE
====================
There is no user rules document for this project: `review_rules` reports
that none was provided. The six binding rules R-1 through R-6 are the Agent
Action Plan's own, from its section 0.7.2, and are quoted where they bear
on this file. Nothing has been invented to fill the gap, and everything the
plan is silent on is held to enterprise-standard best practice.

Rule R-4 additionally forbids a vocabulary of outcome words in this
migration's public surface, because each of them would imply that a legacy
behaviour had been improved rather than reproduced. The prohibited words
are: resolved, canonical, effective, authoritative, corrected, recommended,
preferred, normalise, normalize and sanitize. This paragraph is the only
place any of them is used as a word in this file, and it appears here to
record the prohibition. One of them also occurs twice as part of a FILE
NAME, `harness/normalize.py`, which is the sibling comparison tool that
Agent Action Plan section 0.6.6 charges with reconciling the two coexisting
text forms of a run date; naming a file is not describing an outcome, and
that file is deliberately unreachable from this package.
"""

from __future__ import annotations

import decimal
import enum
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

from acas_posting.cobol import arithmetic as cobol_arithmetic
from acas_posting.cobol import usage as cobol_usage
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary.model import SignPosition, Usage

# The export surface, sorted so that it is stable and reviewable. It is the
# whole contract that `acas_posting.records.*`, `acas_posting.programs.*` and
# tests/arithmetic/test_move_truncation.py will be written against, so it is
# stated exhaustively rather than left to be discovered.
#
# Twelve verbs, two vocabularies, seven sentinels and seven published tables.
# There is deliberately NO calendar helper, NO print-line builder, NO
# `MOVE CORRESPONDING`, NO `JUSTIFIED` support, NO `UNSTRING`, and no
# business constant of any kind - see the module docstring for the verified
# count behind each of those absences.
__all__: Final[tuple[str, ...]] = (
    "DELIMITED_BY_SIZE",
    "DELIMITED_BY_SPACE",
    "EDIT_SYMBOLS_IMPLEMENTED",
    "FIGURATIVE_FILL_CHARACTER",
    "FIGURATIVE_SPELLINGS",
    "MOVE_CENSUS",
    "MOVE_STATEMENT_CENSUS",
    "REFERENCE_MODIFICATION_CENSUS",
    "SPACE",
    "SPACES",
    "ZERO",
    "ZEROES",
    "ZEROS",
    "ZERO_OCCURRENCE_FORMS",
    "Delimiter",
    "Figurative",
    "inspect_tallying_leading",
    "is_numeric_class",
    "move",
    "move_alphanumeric",
    "move_figurative",
    "move_group",
    "move_numeric",
    "move_to_all",
    "move_to_edited",
    "ref_mod",
    "ref_mod_into",
    "string_into",
)

# =====================================================================
# THE TWO VOCABULARIES
#
# A figurative constant and a `DELIMITED BY` phrase are both closed sets in
# the frozen sources, and both are published as enums so that a program
# module transcribes the COBOL word rather than a bare Python literal, and so
# that an unrecognised word is reported by the enum constructor rather than
# by a validation branch added here (rule R-3).
#
# Both are plain `enum.Enum` rather than `enum.StrEnum`, deliberately. A
# `StrEnum` member IS a `str`, which would make `isinstance(value, str)` true
# for `ZERO` and `SPACE`; the dispatch below distinguishes a figurative
# constant from sending text on exactly that test, and a member that answered
# to both would route a figurative constant down the text path.
# =====================================================================


class Figurative(enum.Enum):
    """The figurative constants the frozen sources actually move.

    Two members, because a census of the twelve in-scope program files finds
    exactly two figurative constants used as a `MOVE` sending operand:

        zero    532 occurrences   [general/gl072.cbl:L411]
        zeros    12 occurrences   [sales/sl060.cbl:L477]
        space    64 occurrences   [sales/sl055.cbl:L655]
        spaces  138 occurrences   [sales/sl055.cbl:L539]

    `ZEROES` is accepted as a spelling although it occurs zero times, because
    it is the same word and refusing it would be a validation. `HIGH-VALUES`,
    `LOW-VALUES` and `QUOTES` are absent: each occurs zero times and none is
    implemented. `ALL "x"` occurs four times but only ever in a `VALUE`
    clause - [general/gl051.cbl:L265], [general/gl051.cbl:L269],
    [general/gl072.cbl:L249] and [general/gl072.cbl:L251] - and zero times as
    a sending operand, so it too is absent.

    A member is constructed from any of its accepted spellings, in any case,
    so a program module can transcribe the COBOL word it sees:

        >>> Figurative("spaces") is Figurative.SPACE
        True
        >>> Figurative("ZEROES") is Figurative.ZERO
        True
    """

    ZERO = "zero"
    SPACE = "space"

    @classmethod
    def _missing_(cls, value: object) -> Figurative | None:
        """Accept every spelling the frozen sources and COBOL admit.

        COBOL treats `ZERO`, `ZEROS` and `ZEROES` as one word, and `SPACE`
        and `SPACES` likewise. Mapping the plural and the variant spelling
        onto the same member keeps a program module's transcription literal
        while leaving exactly one member per constant to dispatch on.
        """
        if not isinstance(value, str):
            return None
        return _FIGURATIVE_BY_SPELLING.get(value.strip().casefold())


class Delimiter(enum.Enum):
    """The `DELIMITED BY` phrases the frozen sources actually use.

    `DELIMITED BY SIZE` takes the whole sending item including its trailing
    spaces; `DELIMITED BY SPACE` stops at the first space, which is how a
    space-padded item contributes only its significant characters.

    Verified across the twelve in-scope program files: `DELIMITED BY SIZE`
    appears 22 times, `DELIMITED BY SPACE` 3 times, and a literal delimiter
    zero times. The `SPACE` form's live sites both build a name for the
    operating system rather than a database column -
    [general/gl080.cbl:L531] and [irs/irs030.cbl:L1424] - and it is
    implemented because the verb admits it, not because a posted figure
    depends on it.
    """

    SIZE = "size"
    SPACE = "space"

    @classmethod
    def _missing_(cls, value: object) -> Delimiter | None:
        """Accept the COBOL word in any case, so transcription stays literal.

        `DELIMITED BY SIZE` and `delimited by size` are the same phrase; the
        frozen sources are written in lower case
        [sales/sl060.cbl:L1091-L1094] and a caller may reasonably use either.
        """
        if not isinstance(value, str):
            return None
        return _DELIMITER_BY_SPELLING.get(value.strip().casefold())


# Spelling to member, consulted by both `_missing_` hooks above. Declared
# after the enums because each value is a member, and kept private because
# `FIGURATIVE_SPELLINGS` below is the published, reviewable form.
_FIGURATIVE_BY_SPELLING: Final[Mapping[str, Figurative]] = MappingProxyType({
    "zero": Figurative.ZERO,
    "zeros": Figurative.ZERO,
    "zeroes": Figurative.ZERO,
    "space": Figurative.SPACE,
    "spaces": Figurative.SPACE,
})

_DELIMITER_BY_SPELLING: Final[Mapping[str, Delimiter]] = MappingProxyType({
    "size": Delimiter.SIZE,
    "space": Delimiter.SPACE,
})

#: `MOVE ZERO ...` - the singular spelling. [general/gl072.cbl:L411].
ZERO: Final[Figurative] = Figurative.ZERO

#: `MOVE ZEROS ...` - the plural spelling. [sales/sl060.cbl:L477].
ZEROS: Final[Figurative] = Figurative.ZERO

#: `MOVE ZEROES ...` - the variant spelling, zero occurrences, accepted
#: anyway because refusing it would be a validation (rule R-3).
ZEROES: Final[Figurative] = Figurative.ZERO

#: `MOVE SPACE ...` - the singular spelling. [sales/sl055.cbl:L655].
SPACE: Final[Figurative] = Figurative.SPACE

#: `MOVE SPACES ...` - the plural spelling. [sales/sl055.cbl:L539].
SPACES: Final[Figurative] = Figurative.SPACE

#: `... DELIMITED BY SIZE`. [sales/sl060.cbl:L1091-L1093].
DELIMITED_BY_SIZE: Final[Delimiter] = Delimiter.SIZE

#: `... DELIMITED BY SPACE`. [general/gl080.cbl:L531].
DELIMITED_BY_SPACE: Final[Delimiter] = Delimiter.SPACE


# =====================================================================
# THE PUBLISHED CENSUS TABLES
#
# Every table is a `tuple` or a `MappingProxyType`, so nothing published here
# can be mutated by a caller and no iteration order is a caller's to observe
# (rule R-6). They exist because `docs/migration/traceability.md` must be
# able to cite a measured count rather than an impression, and because a
# future reader deciding whether some COBOL form is "missing" from this file
# should find the count that settled it (rule R-5).
# =====================================================================

#: `MOVE` LINE counts per in-scope program - the Agent Action Plan's own
#: measure, section 0.4.1, which counts every LINE mentioning the verb,
#: comments and continuations included. Reproduced so that a reader comparing
#: this file against the plan finds the plan's own figures. Total 1,291
#: against the plan's stated 1,290; the single-line difference is in
#: `sales/sl055.cbl`, which the plan records as 91 and the frozen file
#: measures at 92.
MOVE_CENSUS: Final[tuple[tuple[str, int], ...]] = (
    ("general/gl051.cbl", 157),
    ("general/gl070.cbl", 66),
    ("general/gl071.cbl", 0),
    ("general/gl072.cbl", 59),
    ("general/gl080.cbl", 48),
    ("sales/sl055.cbl", 92),
    ("sales/sl060.cbl", 177),
    ("sales/sl100.cbl", 124),
    ("purchase/pl055.cbl", 91),
    ("purchase/pl060.cbl", 165),
    ("purchase/pl100.cbl", 122),
    ("irs/irs030.cbl", 190),
)

#: LIVE `MOVE` STATEMENT counts per in-scope program - statements that the
#: compiler executes, excluding commented-out lines and continuation lines.
#: This is the figure that matters to this module, because it is the number of
#: places a truncation direction can be got wrong. Total 1,250.
#:
#: `general/gl071.cbl` contributes zero because it is a pure sort: Agent
#: Action Plan section 0.6.1 records that it contains no arithmetic, and the
#: frozen file contains no `MOVE` either.
MOVE_STATEMENT_CENSUS: Final[tuple[tuple[str, int], ...]] = (
    ("general/gl051.cbl", 155),
    ("general/gl070.cbl", 66),
    ("general/gl071.cbl", 0),
    ("general/gl072.cbl", 59),
    ("general/gl080.cbl", 48),
    ("sales/sl055.cbl", 90),
    ("sales/sl060.cbl", 168),
    ("sales/sl100.cbl", 117),
    ("purchase/pl055.cbl", 91),
    ("purchase/pl060.cbl", 158),
    ("purchase/pl100.cbl", 116),
    ("irs/irs030.cbl", 182),
)

#: Every literal `(offset:length)` reference-modification pair in the twelve
#: in-scope program files, with its occurrence count, most frequent first.
#: Eighty-three occurrences in total, on both the sending and the receiving
#: side of a `MOVE`.
#:
#: Every offset is 1 through 9, so no in-scope site exercises the negative
#: offset noted under Q-10. Three further sites use a computed pair rather
#: than a literal one - `m (b:c)` at [sales/sl060.cbl:L1091],
#: [purchase/pl060.cbl:L954] and [purchase/pl100.cbl:L608] - and are not
#: counted here because their operands are variables.
REFERENCE_MODIFICATION_CENSUS: Final[
    tuple[tuple[int, int, int], ...]
] = (
    (7, 4, 16),
    (4, 2, 16),
    (1, 2, 16),
    (9, 2, 9),
    (1, 6, 8),
    (6, 2, 5),
    (1, 4, 5),
    (7, 2, 4),
    (1, 1, 3),
    (1, 22, 1),
)

#: Accepted spelling to figurative constant, with the count of that exact
#: spelling in the twelve in-scope program files. Published so that
#: `ZEROES`'s zero count is visible: it is accepted although it never occurs,
#: because refusing one spelling of a word COBOL treats as one word would be
#: a validation this module may not add (rule R-3).
FIGURATIVE_SPELLINGS: Final[Mapping[str, tuple[Figurative, int]]] = (
    MappingProxyType({
        "zero": (Figurative.ZERO, 532),
        "zeros": (Figurative.ZERO, 12),
        "zeroes": (Figurative.ZERO, 0),
        "space": (Figurative.SPACE, 64),
        "spaces": (Figurative.SPACE, 138),
    })
)

#: The single character each figurative constant fills a receiver with when
#: the receiver takes text. `ZERO` fills with the CHARACTER zero, so `MOVE
#: ZERO` into `pic x(4)` yields `"0000"` and not four spaces; `SPACE` fills
#: with the space character, so `MOVE SPACE` into a numeric `DISPLAY` item
#: leaves bytes that fail a numeric class test, which is question Q-9.
#: [sales/sl055.cbl:L655] and [general/gl072.cbl:L411].
FIGURATIVE_FILL_CHARACTER: Final[Mapping[Figurative, str]] = MappingProxyType(
    {
        Figurative.ZERO: "0",
        Figurative.SPACE: " ",
    }
)

#: COBOL data-movement forms that occur ZERO times across the twelve in-scope
#: program files and every in-scope copybook, mapped to the count that was
#: measured. Each is therefore NOT implemented below, and this table is the
#: evidence that the omission was verified rather than overlooked (rule R-5).
#:
#: `ALL "x"` needs its qualifier stated precisely rather than as a bare zero:
#: it occurs four times, at [general/gl051.cbl:L265],
#: [general/gl051.cbl:L269], [general/gl072.cbl:L249] and
#: [general/gl072.cbl:L251], but every one of those four is a `VALUE` clause
#: initialising working storage. As a `MOVE` sending operand - the only form
#: this module would have to implement - it occurs zero times.
ZERO_OCCURRENCE_FORMS: Final[Mapping[str, int]] = MappingProxyType({
    'ALL "x" as a MOVE sending operand': 0,
    "HIGH-VALUES": 0,
    "JUSTIFIED": 0,
    "LOW-VALUES": 0,
    "MOVE CORRESPONDING": 0,
    "ON OVERFLOW": 0,
    "QUOTES": 0,
    "UNSTRING": 0,
})

#: The picture edit symbols implemented by `move_to_edited`, and only those.
#: `Z` suppresses a leading zero with a space; `9` always prints its digit.
#:
#: Deliberately absent, each with zero occurrences in any in-scope receiving
#: picture that a database write reaches: the check-protect `*`, the currency
#: `$`, the thousands `,`, the credit and debit symbols `CR` and `DB`, the
#: fixed and floating sign `+` and `-`, the stroke `/`, the blank insertion
#: `B`, the decimal point `.` and the zero insertion `0`. Agent Action Plan
#: section 0.2.2 excludes "Report formatting beyond database effects", and
#: every picture using those symbols receives into a print line.
EDIT_SYMBOLS_IMPLEMENTED: Final[tuple[str, ...]] = ("Z", "9")

# The two edit symbols above, as a membership set for the picture reader. A
# `frozenset` consulted only for membership, so no iteration order is
# observable (rule R-6).
_EDIT_SYMBOLS: Final[frozenset[str]] = frozenset(EDIT_SYMBOLS_IMPLEMENTED)

# The sign positions that place a sign INSIDE the item's digit positions
# rather than in a byte of its own. Consulted only for membership.
_SIGN_INSIDE_DIGITS: Final[frozenset[SignPosition]] = frozenset({
    SignPosition.LEADING_INCLUDED,
    SignPosition.TRAILING_INCLUDED,
})

# The sign positions that spend a byte of their own. Unexercised by this
# migration: the generated dictionary records both zero times across its
# copybook views, and `separate` occurs zero times in `copybooks/*.cob`. The
# branch keyed by them exists so that the class condition below answers for
# the whole vocabulary rather than for the part that happens to occur.
_SIGN_IN_ITS_OWN_BYTE: Final[frozenset[SignPosition]] = frozenset({
    SignPosition.LEADING_SEPARATE,
    SignPosition.TRAILING_SEPARATE,
})

# Byte-transparent for the single-byte character set the frozen sources use:
# latin-1 maps the 256 byte values one to one onto the first 256 code points,
# so an item's byte image and its character image are the same sequence and a
# round trip loses nothing. The sibling `acas_posting.cobol.usage` chose the
# same codec for the same reason, and a codec that refused a byte would be a
# validation this module may not add (rule R-3).
_BYTE_IMAGE_ENCODING: Final[str] = "latin-1"


# =====================================================================
# THE RULE R-2 CARRIER GATE
#
# THE ONLY `raise` STATEMENT IN THIS FILE. It fires on a value's Python TYPE,
# never on its content, which is the whole difference between an R-2 type gate
# and an R-3 validation. See the module docstring.
# =====================================================================


def _exact_carrier(value: object, *, role: str) -> None:
    """Refuse a binary floating-point carrier - the rule R-2 type gate.

    Rule R-2 forbids an accounting value passing through a binary
    floating-point type "at any point - not in computation, not in storage,
    not in transport". A `MOVE` is transport, and transport is the quietest
    place in a system for a lost penny: `0.1 + 0.2` is not `0.3` in binary
    floating point, and a value that arrived here on a `float` has already
    lost exactness before this module could align it to a receiving field's
    scale.

    This gate is the reason the twelve verbs below can each state that they
    never inspect a value's content. A forty-character sending item that
    overflows `Post-Legend pic x(32)` [copybooks/wspost.cob:L24] is data, and
    data is silently truncated; a `float` is a programming error in a
    migration whose every numeric field is a picture clause, and no COBOL
    program could have produced one.

    Args:
        value: The carrier to check. Anything exact passes untouched.
        role: What the value is, for the message - "sending value", "tally",
            "pointer" and so on.

    Raises:
        TypeError: If `value` is a `float` or a `complex`.
    """
    if isinstance(value, (float, complex)):
        raise TypeError(
            f"rule R-2 forbids a binary floating-point {role} anywhere in "
            f"this migration, and {value!r} is a "
            f"{type(value).__name__}: carry an accounting value on "
            "decimal.Decimal, and a count, a position or a binary item "
            "on int"
        )


# =====================================================================
# PRIVATE HELPERS
#
# None of these is published. Each exists so that exactly one place in this
# file decides one question, and so that the twelve verbs read as the COBOL
# forms they implement rather than as string arithmetic.
# =====================================================================


def _receiver_width(
    receiving_field: FieldDescriptor,
    length: int | None,
) -> int | None:
    """Derive the character width a text movement fills, or None.

    The cascade, in order, and it is an ordering rather than a preference:

    1. An explicit `length` from the caller. A program module transcribing a
       group move supplies it, because a group descriptor carries no width of
       its own.
    2. The field's own `character_length`, which is how an alphanumeric item
       declares its width - `pic x(32)` [copybooks/wspost.cob:L24] gives 32.
    3. The field's `byte_length`, which is what a numeric item occupies when
       its bytes are treated as characters. `pic 9(5)`
       [copybooks/wspost.cob:L15] gives 5 and `pic s9(8)v99`
       [copybooks/wspost.cob:L23] gives 10. This is the width the Q-9 and
       Q-13 text paths fill.
    4. None, when the field is a group. `FieldDescriptor.byte_length` reports
       that a group has no width of its own and that its children's widths
       must be summed; every one of the 134 group views in the generated
       dictionary leaves `character_length` unset, so a group receiver needs
       its width from the caller. With no width there is nothing to fill, and
       the movement becomes a byte-image copy.

    Args:
        receiving_field: The receiving field.
        length: An explicit width, or None to derive one.

    Returns:
        The width in characters, or None when none can be derived.
    """
    if length is not None:
        return int(length)
    if receiving_field.character_length is not None:
        return int(receiving_field.character_length)
    try:
        return int(receiving_field.byte_length)
    except ValueError:
        # A group item. Step 4 above: no width of its own.
        return None


def _numeric_image_value(text: str) -> decimal.Decimal | None:
    """Read a byte image as an exact value, or report that it is not one.

    STRICT AND DELIBERATELY SO. Python's `decimal.Decimal` constructor accepts
    surrounding whitespace, an exponent and an underscore separator, so
    `Decimal("0012 ")` is 12 - which would silently turn the spaces left in a
    numeric item by `MOVE SPACE` [sales/sl055.cbl:L655] into a value, and
    would destroy the premise of anomaly A-13, whose skip at
    [general/gl072.cbl:L291-L292] fires precisely because an item's bytes are
    not digits. So the grammar here is spelled out rather than borrowed.

    Accepted, and nothing else: an optional single leading or trailing `+` or
    `-`, then one or more ASCII digits, with at most one `.` among them. No
    space anywhere, no exponent, no underscore, no other character, and at
    least one digit.

    A zoned overpunch image is deliberately NOT read here. `"000001234u"` is
    what `pic s9(8)v99` [copybooks/wspost.cob:L23] holds for -123.45, and its
    final byte carries both a digit and a sign; decoding that is
    `acas_posting.cobol.usage.decode`'s work, and a program module holding a
    raw byte image should go there rather than through a `MOVE`. The class
    condition below DOES read the overpunch, because a COBOL class test reads
    the item's bytes and must answer for them.

    Args:
        text: The byte image to read.

    Returns:
        The exact value, or None when the image is not a numeric one.
    """
    body = text
    negative = False
    if body[:1] in ("+", "-"):
        negative = body[0] == "-"
        body = body[1:]
    elif body[-1:] in ("+", "-"):
        negative = body[-1] == "-"
        body = body[:-1]
    if not body or body.count(".") > 1:
        return None
    digits = body.replace(".", "", 1)
    if not digits or not digits.isascii() or not digits.isdigit():
        return None
    return decimal.Decimal(("-" if negative else "") + body)


def _sender_text(
    value: decimal.Decimal | int | str,
    sending_field: FieldDescriptor | None,
) -> str:
    """Derive the byte image a sending item presents to a text receiver.

    In COBOL a numeric `DISPLAY` item IS a character item: `Batch pic 9(5)`
    [copybooks/wspost.cob:L15] holding 42 occupies the five bytes `00042`, and
    that is what a move or a `STRING` into an alphanumeric receiver moves.
    Deriving those bytes needs the sending item's picture, so a program module
    that crosses the numeric-to-text boundary passes its descriptor. The live
    site is the five-statement build at [sales/sl100.cbl:L620-L628], whose
    first source is exactly such an item.

    Three cases:

    * Text arrives as text and is returned untouched. Its own width is its
      own; the receiver applies its width, not this helper.
    * An exact numeric value with a numeric sending descriptor is laid out by
      `acas_posting.cobol.usage.encode`, so the zone, the overpunch position
      and the field's full width all come from the one audited layout. An
      edited sending item is rendered by `move_to_edited` instead, because an
      edited item's bytes ARE its edited characters - that is the whole point
      of `m pic z(7)9` [sales/sl060.cbl:L213] being read back at
      [sales/sl060.cbl:L1091].
    * An exact numeric value with NO sending descriptor has no picture, so it
      has no width, no zone and no sign position. The fallback is its digits
      alone, with the implied decimal point removed because COBOL never stores
      one and the sign dropped because there is no position to overpunch. No
      in-scope site takes this path: every crossing in the frozen sources has
      a declared sending item.

    Args:
        value: The sending value.
        sending_field: The sending item's descriptor, or None.

    Returns:
        The byte image, as characters.
    """
    if isinstance(value, str):
        return value
    if sending_field is not None and not sending_field.is_group:
        if sending_field.is_edited:
            return move_to_edited(value, sending_field)
        if sending_field.is_numeric:
            raw = cobol_usage.encode(
                value,
                usage=sending_field.usage,
                digits=sending_field.digits,
                scale=sending_field.scale,
                character_length=sending_field.character_length,
                signed=sending_field.signed,
                unsigned=sending_field.unsigned,
                sign_position=sending_field.sign_position,
            )
            return raw.decode(_BYTE_IMAGE_ENCODING)
    plain = str(value) if isinstance(value, int) else format(value, "f")
    return plain.lstrip("+-").replace(".", "")


def _edited_shape_of(clause: str | None) -> tuple[int, int] | None:
    """Read a `Z`-then-`9` edited picture, or report that it is not one.

    `acas_posting.cobol.picture` may not be imported from here - the layering
    table in the module docstring forbids it - so this is a local, deliberately
    minimal reader that recognises `Z` and `9` and nothing else. That is
    exactly enough for the one edited receiver a database write reaches,
    `m pic z(7)9` [sales/sl060.cbl:L213] and its two mirrors
    [purchase/pl060.cbl:L207] and the field behind
    [purchase/pl100.cbl:L603-L608], and enough for the three-receiver move at
    [general/gl051.cbl:L1017] whose first receiver is `pic z(4)9`.

    A repeat count in parentheses is expanded, so `z(7)9` reads as seven `Z`
    positions then one `9` position. The shape must be a run of `Z` followed
    by a run of `9`; anything else - an insertion character, a decimal point,
    a sign symbol, a `9` before a `Z` - reports None and takes the Q-14
    fall-through.

    Args:
        clause: The receiving field's recorded picture clause, or None.

    Returns:
        The count of suppressed positions and the count of always-printing
        positions, or None when the clause is not of this shape.
    """
    if not clause:
        return None
    text = clause.strip().upper()
    symbols: list[str] = []
    index = 0
    while index < len(text):
        symbol = text[index]
        if symbol not in _EDIT_SYMBOLS:
            return None
        index += 1
        repeat = 1
        if index < len(text) and text[index] == "(":
            close = text.find(")", index)
            if close < 0:
                return None
            inner = text[index + 1:close]
            if not inner or not inner.isascii() or not inner.isdigit():
                return None
            repeat = int(inner)
            index = close + 1
        symbols.append(symbol * repeat)
    expanded = "".join(symbols)
    if not expanded:
        return None
    suppressed = len(expanded) - len(expanded.lstrip("Z"))
    remainder = expanded[suppressed:]
    if remainder.count("9") != len(remainder):
        return None
    return suppressed, len(remainder)


def _string_source(
    source: object,
    default_delimiter: Delimiter,
) -> tuple[object, Delimiter, FieldDescriptor | None]:
    """Unpack one `STRING` sending operand into its three parts.

    A `STRING` statement carries a delimiter per operand rather than one for
    the statement, and the frozen sources use that: [general/gl080.cbl:L530]
    through [general/gl080.cbl:L536] mixes `DELIMITED BY SPACE`,
    `DELIMITED BY SIZE`, `DELIMITED BY SIZE` and `DELIMITED BY SPACE` in a
    single statement. So an operand may be given as bare text, which takes the
    call's default delimiter, or as a tuple of one to three elements:

        text                            the default delimiter
        (value,)                        the default delimiter
        (value, delimiter)              an explicit delimiter
        (value, delimiter, field)       and the sending item's descriptor,
                                        needed when `value` is numeric and its
                                        byte image must come from its picture

    A tuple rather than a published class, because the export surface is
    closed at the twelve verbs, two vocabularies, seven sentinels and seven
    tables listed in `__all__`.

    Args:
        source: The operand, as text or as a tuple.
        default_delimiter: The delimiter for an operand that names none.

    Returns:
        The value, its delimiter and its sending descriptor or None.
    """
    if not isinstance(source, tuple):
        # Bare text, or a bare exact numeric operand whose byte image comes
        # from the documented no-descriptor fallback in `_sender_text`.
        return source, default_delimiter, None
    padded = tuple(source) + (None, None, None)
    value, delimiter, field = padded[0], padded[1], padded[2]
    member = default_delimiter if delimiter is None else Delimiter(delimiter)
    descriptor = field if isinstance(field, FieldDescriptor) else None
    return value, member, descriptor


# =====================================================================
# THE FIVE MOVE CATEGORIES
#
# One primitive per category, because the truncation direction differs by
# category and both directions are silent. Every one of them cites the frozen
# site it implements (rule R-5), and not one of them inspects a value's
# content to decide whether it will fit (rule R-3).
# =====================================================================


def move_alphanumeric(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
    length: int | None = None,
) -> str:
    """`MOVE` into an alphanumeric receiver - category (a) and category (c).

    THE RECEIVER GOVERNS, AND IT TRUNCATES ON THE RIGHT. The sending
    characters are placed from the left of the receiver; a receiver wider than
    the sender is padded on the right with spaces, and a receiver narrower
    than the sender keeps its own width and the sender's trailing characters
    are DISCARDED. Nothing reports the loss - `MOVE` does not validate
    (rule R-3), and a forty-character name moved into
    `Post-Legend pic x(32)` [copybooks/wspost.cob:L24] simply loses its last
    eight characters into a database column.

    Category (a), alphanumeric from alphanumeric, is the common case:
    `Post-Code pic xx` [copybooks/wspost.cob:L17],
    `Post-Date pic x(8)` [copybooks/wspost.cob:L18] and
    `Ledger-Name pic x(24)` [copybooks/wsledger.cob:L27] are all such
    receivers, and the last of them is the field whose width drifts to 32 at
    the bridge and again in the column - anomaly A-12 - which is why the
    padding this function applies is visible in a table dump and has to be
    exact.

    Category (c), alphanumeric from numeric, reaches the same rules through
    `_sender_text`: a numeric `DISPLAY` item is a character item, so
    `batch pic 9(5)` contributes its five digit bytes at
    [sales/sl100.cbl:L622].

    `JUSTIFIED` is not supported, and that is a verified decision rather than
    an omission: the keyword occurs zero times in every in-scope copybook and
    every in-scope program, so the default placement from the left is the only
    one the frozen sources ever ask for.

    Args:
        value: The sending value - text, an exact numeric carrier, or a
            figurative constant.
        receiving_field: The receiving field.
        sending_field: The sending item's descriptor. Needed only when
            `value` is numeric and its byte image must come from its picture.
        length: An explicit receiver width, overriding the cascade in
            `_receiver_width`. A group receiver needs it.

    Returns:
        What the receiver now holds, as text of the receiver's own width.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    if isinstance(value, Figurative):
        return str(move_figurative(value, receiving_field, length=length))
    text = _sender_text(value, sending_field)
    width = _receiver_width(receiving_field, length)
    if width is None:
        # A group receiver with no width given: a byte-image copy, per
        # `_receiver_width` step 4 and the group-move rule below.
        return text
    return str(
        cobol_usage.coerce(
            text,
            usage=Usage.ALPHANUMERIC,
            character_length=width,
        )
    )


def move_numeric(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
) -> decimal.Decimal | int | str:
    """`MOVE` into a numeric receiver - category (b) and category (d).

    THE RECEIVER GOVERNS, AND IT TRUNCATES AT BOTH ENDS. Alignment is on the
    implied decimal point, and each end is then reduced or filled
    independently: digits beyond the receiver's scale are discarded toward
    zero, and digits beyond its integer capacity are discarded from the high
    order. Both losses are silent. `Decimal("123.456")` into
    `Post-Amount pic s9(8)v99` [copybooks/wspost.cob:L23] holds 123.45, and
    `Decimal("123456.78")` into a three-integer-digit receiver holds 456.78.

    THE STORE ITSELF IS DELEGATED to `acas_posting.cobol.arithmetic.store`,
    deliberately and not for brevity. Scale alignment, truncation toward zero,
    the sign drop into an unsigned receiver - `pic 9(9)v99` under
    `03 Amounts comp-3.` [copybooks/wsbatch.cob:L41-L44] - and the silent
    high-order reduction are all audited there, and two truncation code paths
    would mean one of them was eventually wrong. Question Q-3 - what an
    unsigned receiver does with a signed value - is that module's register
    entry and this one inherits its provisional answer, the absolute value
    stored.

    A `SIGN LEADING` receiver keeps its sign in its leading digit position,
    and the two spellings the frozen sources use are both honoured without
    being collapsed into one: `sign leading`
    [copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25] and
    `sign is leading` [copybooks/irswspost.cob:L14],
    [copybooks/irswspost.cob:L18]. The byte form is
    `acas_posting.cobol.usage`'s work; each descriptor keeps its own recorded
    wording.

    Category (d), numeric from alphanumeric, reads the sending characters as a
    value. The reading is strict - see `_numeric_image_value` - and when the
    characters are NOT a numeric image the movement takes the Q-13 path: they
    are kept as characters, aligned to the RIGHT of the receiver's byte width,
    losing characters from the LEFT and padded on the left with spaces, never
    with zeros, which would fabricate digits the sending bytes do not contain.
    No error is reported, so `is_numeric_class` can afterwards report False
    and the silent skip at [general/gl072.cbl:L291-L292] - anomaly A-13 -
    stays reproducible. Question Q-9 is the same path reached from
    `MOVE SPACE` [sales/sl055.cbl:L655].

    Args:
        value: The sending value - an exact numeric carrier, text, or a
            figurative constant.
        receiving_field: The receiving field.
        sending_field: Accepted for symmetry with the other categories and
            unused: a numeric receiver reads the sending VALUE, and a sending
            item's own picture cannot change it.

    Returns:
        What the receiver now holds - `decimal.Decimal` for a scaled field,
        `int` for the binary family and a zero-scale integer, or text on the
        Q-9 and Q-13 paths.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    del sending_field
    if isinstance(value, Figurative):
        return move_figurative(value, receiving_field)
    if isinstance(value, str):
        exact = _numeric_image_value(value)
        if exact is None:
            width = _receiver_width(receiving_field, None)
            if width is None:
                return value
            # Q-13: kept as characters, losing from the LEFT.
            return value[-width:].rjust(width)
        return cobol_arithmetic.store(exact, receiving_field)
    return cobol_arithmetic.store(value, receiving_field)


def move_group(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
    length: int | None = None,
) -> str:
    """`MOVE` into a group receiver - the whole byte image, unconverted.

    A `MOVE` whose receiver is a group item is an ALPHANUMERIC move of the
    group's entire byte image. No child field is examined, no picture clause
    is applied to any part of it, and no numeric conversion happens anywhere -
    the sending bytes are laid into the receiving bytes from the left, padded
    on the right with spaces or truncated on the right, exactly as category
    (a) does. That is why a group move can carry a value into a child field
    whose picture it does not match, and why it is worth having a named verb
    for it rather than letting it look like an ordinary text move.

    Group receivers are everywhere in the in-scope records:
    `03 WS-Post-Key.` [copybooks/wspost.cob:L14], `03 Dates.`
    [copybooks/wsbatch.cob:L35], `03 Amounts comp-3.`
    [copybooks/wsbatch.cob:L40] and `03 Quarters.`
    [copybooks/wsledger.cob:L30]. A live site is
    [sales/sl055.cbl:L538-L540], which moves a group and then clears six
    fields in one statement.

    A GROUP DESCRIPTOR CARRIES NO WIDTH OF ITS OWN.
    `FieldDescriptor.byte_length` says so, and every one of the 134 group
    views in the generated dictionary leaves `character_length` unset, so a
    program module transcribing a group move supplies `length` from the
    copybook. With no width the movement is a byte-image copy of whatever the
    sender presents: nothing is truncated because nothing is known to
    truncate against, and nothing is padded for the same reason.

    Args:
        value: The sending value.
        receiving_field: The receiving group.
        sending_field: The sending item's descriptor, when the sender is
            numeric.
        length: The group's width in characters, from the copybook.

    Returns:
        The receiving group's byte image, as characters.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    return move_alphanumeric(
        value,
        receiving_field,
        sending_field=sending_field,
        length=length,
    )


def move_figurative(
    figurative: Figurative | str,
    receiving_field: FieldDescriptor,
    *,
    length: int | None = None,
) -> decimal.Decimal | int | str:
    """`MOVE ZERO`/`MOVE SPACE` - category (e), a constant with no sender.

    A figurative constant has no sending field and no width: it fills the
    receiver, whatever the receiver's width is. Two constants, because a
    census of the twelve in-scope program files finds exactly two - see
    `FIGURATIVE_SPELLINGS` for the per-spelling counts.

    THE CONSTANT DOES NOT CHANGE THE RECEIVER'S CATEGORY, WHICH IS THE WHOLE
    SUBTLETY. `MOVE ZERO` into a numeric receiver stores the VALUE zero -
    `move zero to tot-dr tot-cr.` [general/gl072.cbl:L411] clears two
    accumulators to 0.00. `MOVE ZERO` into an alphanumeric receiver fills it
    with the CHARACTER zero, so a four-character receiver holds `0000` and not
    four spaces. And `MOVE SPACE` into a numeric `DISPLAY` receiver leaves
    SPACES in its bytes - `move space to oi-applied oi-unapl oi-hold-flag.`
    [sales/sl055.cbl:L655] - which is question Q-9, and which matters because
    those bytes then fail a numeric class test and feed anomaly A-13's silent
    skip at [general/gl072.cbl:L291-L292].

    `HIGH-VALUES`, `LOW-VALUES`, `QUOTES` and `ALL "x"` as a sending operand
    each occur zero times and are not implemented; `ZERO_OCCURRENCE_FORMS`
    carries the counts.

    Args:
        figurative: A `Figurative` member or any accepted spelling of one -
            `zero`, `zeros`, `zeroes`, `space` or `spaces`, in any case.
        receiving_field: The receiving field.
        length: An explicit receiver width, needed for a group receiver.

    Returns:
        What the receiver now holds: `decimal.Decimal` or `int` for a numeric
        receiver filled with `ZERO`, and text in every other case.
    """
    member = (
        figurative if isinstance(figurative, Figurative)
        else Figurative(figurative)
    )
    if member is Figurative.SPACE:
        # Q-9 when the receiver is numeric: the bytes hold spaces, and the
        # class condition below will report False for them.
        width = _receiver_width(receiving_field, length)
        fill = FIGURATIVE_FILL_CHARACTER[member]
        return fill if width is None else fill * width
    if receiving_field.is_edited:
        # Q-12: the trailing `9` of `z(7)9` prints, so zero renders as seven
        # spaces then a single `0` [sales/sl060.cbl:L1085].
        return move_to_edited(0, receiving_field)
    if receiving_field.is_numeric:
        return cobol_arithmetic.store(0, receiving_field)
    width = _receiver_width(receiving_field, length)
    fill = FIGURATIVE_FILL_CHARACTER[member]
    return fill if width is None else fill * width


def move_to_edited(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
) -> str:
    """`MOVE` into a numeric-edited receiver - the one form that writes.

    SCOPE, STATED PLAINLY. Agent Action Plan section 0.2.2 excludes "Report
    formatting beyond database effects", and the emphasis is load-bearing:
    ONE edited move in the frozen sources does have a database effect, so it
    is implemented here, editing being a property of the `MOVE` verb rather
    than of a picture parser. It is the `Z`-suppression-then-`9` form:

        03  m               pic z(7)9.       [sales/sl060.cbl:L213]
        move     oi-invoice to m.            [sales/sl060.cbl:L1085]

    whose result is then scanned by `INSPECT`, sliced by reference
    modification and concatenated by `STRING` into
    `Post-Legend pic x(32)` [copybooks/wspost.cob:L24] - a real column. The
    two mirrors are [purchase/pl060.cbl:L207] with
    [purchase/pl060.cbl:L947-L954] and [purchase/pl100.cbl:L600-L610]. The
    same shape appears as the first receiver of the three-receiver move at
    [general/gl051.cbl:L1017], `pic z(4)9`.

    EVERY OTHER EDITED PICTURE IN THE FROZEN SOURCES RECEIVES INTO A PRINT
    LINE and therefore has no database effect and no oracle evidence behind
    it. `EDIT_SYMBOLS_IMPLEMENTED` lists the two symbols implemented and names
    the ten deliberately absent. A picture outside the `Z`-then-`9` shape
    takes an explicitly UNVERIFIED fall-through, recorded as question Q-14:
    its digit positions are rendered with no suppression and no insertion
    character. That path is not a claim about compiled behaviour, and this
    docstring is the place that says so rather than letting it pass for
    verified.

    THE SUPPRESSION RULE. Scanning from the left, a `Z` position holding a
    zero with no significant digit yet to its left is replaced by a space; a
    `Z` position at or after the first significant digit prints its digit; a
    `9` position always prints. With no `BLANK WHEN ZERO` - the clause occurs
    zero times in every in-scope copybook - the trailing `9` of `z(7)9`
    prints even for zero, so zero renders as seven spaces then `0`. That is
    question Q-12, and it changes a database column whenever the sending value
    is zero.

    No sign is rendered. `+`, `-`, `CR` and `DB` each occur zero times in the
    in-scope edited pictures, so a sign has no position to occupy, and the
    digit image is taken from the stored value's magnitude.

    Args:
        value: The sending value - an exact numeric carrier, a numeric byte
            image as text, or a figurative constant.
        receiving_field: The edited receiving field.

    Returns:
        The edited characters, at the picture's own width.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    shape = _edited_shape_of(receiving_field.picture)
    if isinstance(value, Figurative):
        if value is Figurative.SPACE:
            width = _receiver_width(receiving_field, None)
            return " " if width is None else " " * width
        exact: decimal.Decimal | int = 0
    elif isinstance(value, str):
        read = _numeric_image_value(value)
        if read is None:
            # Q-13 reached through an edited receiver: characters kept,
            # losing from the LEFT, rather than an error.
            width = _receiver_width(receiving_field, None)
            return value if width is None else value[-width:].rjust(width)
        exact = read
    else:
        exact = value
    stored = cobol_arithmetic.store(exact, receiving_field)
    plain = str(stored) if isinstance(stored, int) else format(stored, "f")
    digits = plain.lstrip("+-").replace(".", "")
    if shape is None:
        # Q-14: UNVERIFIED. No suppression, no insertion character.
        fallback = _receiver_width(receiving_field, None)
        span = len(digits) if fallback is None else fallback
        return digits.zfill(span)[-span:]
    suppressed, printing = shape
    span = suppressed + printing
    digits = digits.zfill(span)[-span:]
    rendered: list[str] = []
    significant = False
    for position, digit in enumerate(digits):
        if position < suppressed and not significant and digit == "0":
            rendered.append(" ")
            continue
        significant = True
        rendered.append(digit)
    return "".join(rendered)


# =====================================================================
# THE AUDITED DISPATCH
#
# One entry point a program module normally calls, and one for the
# multiple-receiver form. Both choose a category from the RECEIVING field and
# never from the sending value's convenience.
# =====================================================================


def move(
    value: decimal.Decimal | int | str | Figurative,
    receiving_field: FieldDescriptor,
    *,
    sending_field: FieldDescriptor | None = None,
    length: int | None = None,
) -> decimal.Decimal | int | str:
    """`MOVE <sender> TO <one receiver>` - the single audited dispatch.

    THE RECEIVING FIELD DECIDES EVERYTHING. A `MOVE` is not an assignment:
    Agent Action Plan section 0.1.2, transformation rule 11, requires
    "Sending-field-to-receiving-field rules, not assignment", and the rules
    differ by the receiver's category, not by the sender's type. So the
    dispatch below tests the receiver in a fixed order, and the order is
    itself load-bearing:

    1. A FIGURATIVE CONSTANT first, because it has no sending field at all and
       because what it means depends on the receiver - the value zero into a
       numeric receiver, the character zero into a text one
       [general/gl072.cbl:L411], [sales/sl055.cbl:L655].
    2. A GROUP RECEIVER next, because a group move examines no child field and
       applies no picture [copybooks/wspost.cob:L14].
    3. AN EDITED RECEIVER next, and this ordering matters in practice: a
       descriptor for `m pic z(7)9` [sales/sl060.cbl:L213] reports itself as
       numeric as well as edited, so testing numeric first would store a value
       where the frozen source expects suppressed characters.
    4. A NUMERIC RECEIVER, aligned on the implied decimal point and truncated
       at both ends [copybooks/wspost.cob:L23].
    5. AN ALPHANUMERIC RECEIVER, filled from the left and truncated on the
       right [copybooks/wspost.cob:L24].

    There is no sixth case. A receiver is a group, edited, numeric or text,
    and the vocabulary `acas_posting.dictionary.model` publishes admits
    nothing else.

    Args:
        value: The sending value - text, an exact numeric carrier, or a
            figurative constant.
        receiving_field: The receiving field, which governs the movement.
        sending_field: The sending item's descriptor, needed only when a
            numeric value crosses into a text receiver and its byte image must
            come from its own picture [sales/sl100.cbl:L622].
        length: An explicit receiver width. A group receiver needs it, every
            group view in the generated dictionary leaving
            `character_length` unset.

    Returns:
        What the receiver now holds, in the carrier its storage class calls
        for.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    if isinstance(value, Figurative):
        return move_figurative(value, receiving_field, length=length)
    if receiving_field.is_group:
        return move_group(
            value,
            receiving_field,
            sending_field=sending_field,
            length=length,
        )
    if receiving_field.is_edited:
        return move_to_edited(value, receiving_field)
    if receiving_field.is_numeric:
        return move_numeric(
            value,
            receiving_field,
            sending_field=sending_field,
        )
    return move_alphanumeric(
        value,
        receiving_field,
        sending_field=sending_field,
        length=length,
    )


def move_to_all(
    value: decimal.Decimal | int | str | Figurative,
    receiving_fields: Sequence[FieldDescriptor],
    *,
    sending_field: FieldDescriptor | None = None,
) -> tuple[decimal.Decimal | int | str, ...]:
    """`MOVE <sender> TO <several receivers>` - each applying its own rules.

    ONE VALUE IS NOT REUSED; IT IS CONVERTED ONCE PER RECEIVER. A single COBOL
    `MOVE` may name several receivers, and each applies its own truncation,
    its own padding and its own storage class independently. The clearest
    proof in the frozen sources is a three-receiver statement whose three
    receivers have three different descriptions:

        move  batch  to  l4-batch  save-batch  WS-Batch-Nos
                                        [general/gl051.cbl:L1017]

    where `l4-batch pic z(4)9` [general/gl051.cbl:L289] is EDITED and yields
    suppressed characters, `save-batch pic 9(5) comp`
    [general/gl051.cbl:L174] is BINARY and yields an integer, and
    `WS-Batch-Nos pic 9(5)` [copybooks/wsbatch.cob:L19] is zoned DISPLAY. One
    statement, three carriers, three different results. A two-receiver
    statement is commoner still - `move oi-customer to WS-Sales-Key l5-cust.`
    [sales/sl060.cbl:L489] - and the form is used to clear several fields at
    once throughout: [general/gl051.cbl:L982], [general/gl051.cbl:L1041],
    [general/gl070.cbl:L400], [general/gl072.cbl:L281],
    [general/gl072.cbl:L411], [general/gl072.cbl:L452],
    [sales/sl055.cbl:L539], [sales/sl055.cbl:L653],
    [sales/sl055.cbl:L655], [sales/sl060.cbl:L477],
    [sales/sl060.cbl:L546] and [sales/sl060.cbl:L941].

    The results come back in RECEIVER ORDER, in a `tuple`, so a program module
    unpacks them in the order the COBOL statement names them and a reviewer
    can diff the two lists position by position.

    A receiver needing an explicit width - a group - is moved to with `move`
    directly rather than through this verb, so that its width travels with it.

    Args:
        value: The sending value, converted once per receiver.
        receiving_fields: The receivers, in the order the statement names
            them.
        sending_field: The sending item's descriptor, when a numeric value
            crosses into a text receiver.

    Returns:
        One stored value per receiver, in receiver order.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="sending value")
    return tuple(
        move(value, receiver, sending_field=sending_field)
        for receiver in receiving_fields
    )


# =====================================================================
# REFERENCE MODIFICATION - 1-BASED, AND NEVER BOUNDS-CHECKED
#
# Eighty-three literal uses across the twelve in-scope program files, on both
# the sending and the receiving side, and one pair of them writes a database
# column. See `REFERENCE_MODIFICATION_CENSUS` for the per-pair counts.
# =====================================================================


def ref_mod(text: str, offset: int, length: int) -> str:
    """`sending-item (offset:length)` - the sending-side character range.

    ONE-BASED, BECAUSE THE COBOL IS. `(1:2)` is the first two characters and
    `(7:4)` starts at the seventh. A program module transcribes the COBOL
    pair unchanged - `offset=7, length=4` for `(7:4)` - so a reviewer can diff
    the Python against the frozen source character for character. Translating
    to a zero-based slice at the call site is exactly the mistake this
    primitive exists to prevent, and an off-by-one here would corrupt every
    text field the cycle builds by surgery.

    The live sending-side sites, all four in one paragraph:

        move  u-date (1:2) to ws-Intl-Days.     [general/gl070.cbl:L568]
        move  to-day (7:4) to ws-Intl-Year.     [general/gl070.cbl:L596]
        move  to-day (4:2) to ws-Intl-Month.    [general/gl070.cbl:L597]
        move  to-day (1:2) to ws-Intl-Days.     [general/gl070.cbl:L598]

    NOT BOUNDS-CHECKED, deliberately (rule R-4). A range running past the end
    of the item yields the characters that are there and no error, which is
    Python's own slicing behaviour and is left to stand rather than guarded -
    question Q-10 records that GnuCOBOL's behaviour with and without bounds
    checking has not been measured. An offset below 1 would index from the end
    the way a negative Python index does; no in-scope site produces one, every
    literal offset in `REFERENCE_MODIFICATION_CENSUS` being 1 through 9 and
    the one computed offset being a tally plus one
    [sales/sl060.cbl:L1089-L1091].

    Args:
        text: The sending item's characters.
        offset: The 1-based first character position.
        length: The number of characters.

    Returns:
        The character range.

    Raises:
        TypeError: If `offset` or `length` is a binary floating-point carrier
            (rule R-2).
    """
    _exact_carrier(offset, role="reference-modification offset")
    _exact_carrier(length, role="reference-modification length")
    start = int(offset) - 1
    return text[start:start + int(length)]


def ref_mod_into(
    receiver_text: str,
    offset: int,
    length: int,
    value: str,
) -> str:
    """`receiving-item (offset:length)` - a partial overwrite in place.

    ONE-BASED, and the positions OUTSIDE the range are left exactly as they
    were. The range is itself an alphanumeric receiver, so the incoming
    characters are filled from the left within it, padded on the right with
    spaces or truncated on the right, precisely as `move_alphanumeric` does
    for a whole field.

    THE SITE THAT MAKES THIS PRIMITIVE MATTER writes a database column, and it
    is two statements long:

        move  u-date (1:6) to post-date (1:6).  [sales/sl060.cbl:L1071]
        move  u-date (9:2) to post-date (7:2).  [sales/sl060.cbl:L1072]

    A ten-character `DD/MM/CCYY` text item is carried into
    `Post-Date pic x(8)` [copybooks/wspost.cob:L18], which is `DD/MM/YY`. Those
    two statements are the ENTIRE conversion. There is no calendar logic
    anywhere in them, and there is none here either: this primitive moves
    characters and does not know what they mean. Agent Action Plan section
    0.6.6 makes the two coexisting text forms `harness/normalize.py`'s problem,
    not this module's. The same pair appears at
    [sales/sl100.cbl:L612-L613].

    NOT BOUNDS-CHECKED (rule R-4, question Q-10). A range starting beyond the
    end of the receiver extends it rather than reporting an error, because the
    receiver's own declared width is not a parameter of this primitive - the
    `move` that stores the result applies it. Callers hold a receiver at its
    full declared width, which every record layout initialises it to, and then
    this is exact.

    Args:
        receiver_text: The receiver's current characters.
        offset: The 1-based first character position of the range.
        length: The number of characters in the range.
        value: The characters to place in the range.

    Returns:
        The receiver's characters after the overwrite.

    Raises:
        TypeError: If `offset` or `length` is a binary floating-point carrier
            (rule R-2).
    """
    _exact_carrier(offset, role="reference-modification offset")
    _exact_carrier(length, role="reference-modification length")
    start = int(offset) - 1
    span = int(length)
    stop = start + span
    placed = value[:span].ljust(span)
    return receiver_text[:start] + placed + receiver_text[stop:]


# =====================================================================
# THE TWO CHARACTER VERBS THAT LIVE HERE
#
# `INSPECT ... TALLYING ... FOR LEADING` and
# `STRING ... DELIMITED BY ... INTO ... POINTER` are receiving-field character
# movement, they have a database effect, and the folder they would otherwise
# belong to does not exist: the folder requirement closes this package at
# eight files and says, verbatim, "Nothing else. No `strings.py`, no
# `numeric.py`, no `helpers.py`." So they are here by that rule, and this
# banner says so, rather than leaving a reader to think they were smuggled in.
#
# NOT here: `INSPECT ... REPLACING ALL "." BY "/"`, at
# [general/gl051.cbl:L1178-L1180] and [irs/irs030.cbl:L1312-L1314]. Agent
# Action Plan section 0.4.1.6 assigns separator handling for `.`, `,` and `-`
# to `acas_posting/dates.py`, a standard-library-only module that does not
# import this package. The boundary is recorded so the omission is visible
# rather than accidental.
# =====================================================================


def inspect_tallying_leading(
    text: str,
    figurative: Figurative | str,
    tally: int,
) -> int:
    """`INSPECT <item> TALLYING <n> FOR LEADING <figurative>`.

    Counts the run of the figurative's character at the START of the item and
    stops at the first character that is not it. The three live sites are all
    the same statement, and all three feed the one edited-move idiom that
    writes a database column:

        inspect  m tallying b for leading space. [sales/sl060.cbl:L1087]
                                                [purchase/pl060.cbl:L949]
                                                [purchase/pl100.cbl:L603]

    THE TALLY ACCUMULATES INTO WHAT IT ALREADY HOLDS. COBOL's `TALLYING` adds
    to the tally item rather than replacing it, which is exactly why the
    frozen source clears it first:

        move     zero to b.                     [sales/sl060.cbl:L1086]

    So the caller passes the tally's current value and receives its new one,
    and the reset stays where the COBOL put it. Resetting implicitly here
    would silently repair a program that forgot to, and rule R-4 forbids
    repairing anything.

    One further `INSPECT ... TALLYING` exists in the frozen sources,
    `inspect u-date tallying q for all "/"` [irs/irs030.cbl:L1315], but it
    sits in that program's validation section and only
    `Ledger-Postings-Add` [irs/irs030.cbl:L1569-L1733] is in scope. `FOR ALL`
    is therefore not implemented; only `FOR LEADING` is.

    Args:
        text: The item's characters.
        figurative: `SPACE` or `ZERO`, as a member or any accepted spelling.
        tally: The tally item's current value, added to.

    Returns:
        The tally item's new value.

    Raises:
        TypeError: If `tally` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(tally, role="tally")
    member = (
        figurative if isinstance(figurative, Figurative)
        else Figurative(figurative)
    )
    wanted = FIGURATIVE_FILL_CHARACTER[member]
    run = 0
    for character in text:
        if character != wanted:
            break
        run += 1
    return int(tally) + run


def string_into(
    receiver_text: str,
    sources: Sequence[object],
    *,
    pointer: int = 1,
    delimited_by: Delimiter | str = Delimiter.SIZE,
) -> tuple[str, int]:
    """Reproduce `STRING <sources> DELIMITED BY ... INTO ... POINTER <n>`.

    Writes each source's contributed characters into the receiver starting at
    the 1-based pointer, advancing the pointer by what was written, and
    OVERWRITING rather than clearing: COBOL's `STRING` leaves every position
    it does not reach exactly as it found it, which is why the frozen source
    clears the receiver itself first when it wants it clear -
    `move space to Arg-Test.` [general/gl080.cbl:L530].

    THE POINTER IS READ AND RETURNED, SO SUCCESSIVE STATEMENTS CHAIN. This is
    not a convenience; it is a divergence in the frozen sources that must not
    be unified. One program builds its 32-character receiver with a SINGLE
    statement carrying three sources:

        string   m (b:c)     delimited by size
                 " : "       delimited by size
                 sales-name  delimited by size
                              into Post-Legend pointer  xx.
                                        [sales/sl060.cbl:L1091-L1094]

    while another builds the SAME column with FIVE successive statements
    sharing ONE pointer, and does not use the edited-move idiom at all:

        move     1  to  xx.
        string batch       delimited by size into post-legend pointer xx.
        string "/"         delimited by size into post-legend pointer xx.
        string k           delimited by size into post-legend pointer xx.
        string "  :  "     delimited by size into post-legend pointer xx.
        string sales-name  delimited by size into post-legend pointer xx.
                                        [sales/sl100.cbl:L620-L628]

    That excerpt keeps the five statements and the pointer's own
    initialisation and drops three ordinary moves that sit between them,
    loading the sources; the frozen span is L620 to L628 and reads in that
    order. The pointer is plainly the caller's variable, initialised by a
    `MOVE` like any other item, which is why it is passed in and handed back
    rather than being state this module keeps.

    The maintainer flagged the difference himself in a comment immediately
    above it [sales/sl100.cbl:L618]. Both shapes are supported, neither is
    rewritten into the other, and the fourth source above is FIVE characters
    in the frozen file rather than the three of the other program - another
    difference left exactly as it is.

    A DELIMITER PER SOURCE, because the frozen sources mix them within one
    statement: [general/gl080.cbl:L530-L536] uses `SPACE`, `SIZE`, `SIZE`,
    `SPACE` in order. `DELIMITED BY SIZE` contributes the whole item including
    its trailing spaces; `DELIMITED BY SPACE` stops at the first space, which
    is how a space-padded item contributes only its significant characters
    [irs/irs030.cbl:L1424]. See `_string_source` for how a source names its
    own delimiter, and `ZERO_OCCURRENCE_FORMS` for the literal-delimiter form,
    which occurs zero times.

    OVERFLOW IS SILENT - question Q-11. `Post-Legend pic x(32)`
    [copybooks/wspost.cob:L24] is 32 characters and the sources can exceed it:
    a source that fits partly contributes the characters that fit, a pointer
    already past the end contributes nothing, and neither is reported.
    `ON OVERFLOW` occurs zero times across the twelve in-scope program files,
    so there is no error path in the specification to reproduce.

    Args:
        receiver_text: The receiver's current characters, at its own width.
        sources: The sending operands, in statement order. Each is bare text,
            a bare exact numeric carrier, or a tuple naming its own delimiter
            and, when it is numeric, its own descriptor.
        pointer: The 1-based position to write from. Two frozen sites name no
            `POINTER` phrase at all - [general/gl080.cbl:L531] and
            [irs/irs030.cbl:L1424] - and for them the default 1 is the COBOL
            behaviour.
        delimited_by: The delimiter for any source that names none.

    Returns:
        The receiver's characters after the write, and the pointer's new
        1-based value, so that the next statement can be handed both.

    Raises:
        TypeError: If `pointer` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(pointer, role="pointer")
    fallback = (
        delimited_by if isinstance(delimited_by, Delimiter)
        else Delimiter(delimited_by)
    )
    text = receiver_text
    width = len(text)
    position = int(pointer)
    for source in sources:
        value, delimiter, descriptor = _string_source(source, fallback)
        _exact_carrier(value, role="STRING sending value")
        piece = _sender_text(value, descriptor)
        if delimiter is Delimiter.SPACE:
            piece = piece.partition(" ")[0]
        if position < 1 or position > width:
            # Q-11: nothing further is written, silently.
            continue
        start = position - 1
        written = piece[:width - start]
        text = text[:start] + written + text[start + len(written):]
        position += len(written)
    return text, position


# =====================================================================
# THE NUMERIC CLASS CONDITION
#
# A predicate, never an exception, because anomaly A-13 depends on it.
# =====================================================================


def is_numeric_class(
    value: decimal.Decimal | int | str | Figurative,
    field: FieldDescriptor,
) -> bool:
    """`IF <item> IS NUMERIC` - the class condition, as a plain boolean.

    ANOMALY A-13 DEPENDS ON THIS BEING A PREDICATE AND NOT AN EXCEPTION. The
    frozen source tests an item for numeric class and, on failure, skips the
    record entirely - with, as the anomaly register puts it, "no message,
    counter or trace":

        if       post-batch  not numeric
                 go to  loop.             [general/gl072.cbl:L291-L292]

    The register cites that construct as `[general/gl072.cbl:L289-L290]` and
    its sibling skip on a specific handler error as
    `[general/gl072.cbl:L303-L304]`; in the frozen checkout the two read at
    L291-L292 and L306-L307. The offset is recorded rather than reconciled
    silently, the frozen file being the authority.

    THE SKIP ITSELF IS NOT THIS MODULE'S. It is business logic and it belongs
    to `acas_posting.programs.gl072_transaction_update`. This function only
    answers the question the COBOL asks, and it answers it for every input
    without ever reporting an error, so that a program module can express the
    test and the silence can be reproduced.

    WHAT IT ANSWERS. An item holding an exact numeric value is numeric. An
    item holding characters is numeric when every character is an ASCII digit,
    with one exception that has to be got right: a signed zoned item carries
    its sign OVERPUNCHED onto a digit rather than in a byte of its own, so the
    sign-carrying position may hold a byte from either zone table and is still
    a valid digit. The tables are
    `acas_posting.cobol.usage.ZONED_POSITIVE_BASE` and `ZONED_NEGATIVE_BASE`,
    and the position is the leading digit for the `SIGN LEADING` form
    [copybooks/wspost-irs.cob:L21], [copybooks/irswspost.cob:L14] and the
    trailing digit otherwise [copybooks/wspost.cob:L23]. A `SEPARATE` sign
    would occupy a byte of its own; the branch is written for completeness of
    the vocabulary and is unexercised, the generated dictionary recording
    neither separate position anywhere.

    An item holding SPACES is not numeric, which is the observable consequence
    of question Q-9 and the reason `MOVE SPACE` into a numeric `DISPLAY` item
    [sales/sl055.cbl:L655] is worth a register entry. An empty item is not
    numeric either: there is no digit in it.

    An alphanumeric item's class test considers no sign, so every one of its
    characters must be a digit.

    Args:
        value: What the item holds.
        field: The item's descriptor, which supplies the sign position.

    Returns:
        True when the item's contents satisfy COBOL's numeric class
        condition.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
    """
    _exact_carrier(value, role="tested value")
    if isinstance(value, Figurative):
        # `ZERO` leaves digits behind whatever the receiver's category;
        # `SPACE` leaves spaces, which no class test accepts.
        return value is Figurative.ZERO
    if not isinstance(value, str):
        return True
    if not value:
        return False
    signed_zoned = (
        field.is_numeric
        and field.signed
        and not field.is_binary_family
        and not field.is_packed
    )
    body = value
    if signed_zoned and field.sign_position in _SIGN_IN_ITS_OWN_BYTE:
        leading = field.sign_position is SignPosition.LEADING_SEPARATE
        sign_character = value[0] if leading else value[-1]
        accepted = (
            cobol_usage.SEPARATE_SIGN_BYTE_POSITIVE,
            cobol_usage.SEPARATE_SIGN_BYTE_NEGATIVE,
        )
        if ord(sign_character) not in accepted:
            return False
        body = value[1:] if leading else value[:-1]
    elif signed_zoned and field.sign_position in _SIGN_INSIDE_DIGITS:
        leading = field.sign_position is SignPosition.LEADING_INCLUDED
        overpunched = value[0] if leading else value[-1]
        code = ord(overpunched)
        if (
            code not in cobol_usage.ZONED_POSITIVE_BASE
            and code not in cobol_usage.ZONED_NEGATIVE_BASE
        ):
            return False
        body = value[1:] if leading else value[:-1]
    if not body:
        # A one-character signed item is all sign and no digit; the sign
        # itself was accepted above, so the item is numeric.
        return True
    return body.isascii() and body.isdigit()
