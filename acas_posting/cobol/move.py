"""The COBOL `MOVE` verb: receiving-field data-movement semantics.

A `MOVE` IS NOT AN ASSIGNMENT. Agent Action Plan section 0.1.2, transformation
rule 11, makes a `MOVE` between unlike pictures an explicit truncate/pad helper
governed by "sending-field-to-receiving-field rules, not assignment", and
sections 0.3.1 and 0.4.1.4 assign this file `MOVE` truncation, space padding and
justification.

Every `MOVE` is governed by the RECEIVING field. An alphanumeric item is filled
from the left, padded with spaces on the right and truncated on the RIGHT. A
numeric item is aligned on its implied decimal point and truncated or zero-padded
on BOTH ends independently. Getting the direction of truncation backwards
corrupts data silently, with no error either way, and nothing will report it
except a non-empty state diff.

ZERO BUSINESS LOGIC
Section 0.3.1 keeps business logic out of `cobol/`, so no posting rule, no
calendar decision, no print-line layout and no account number appears below. This
module supplies the movement mechanics; the program layer decides what is moved
where. Every business noun in this file appears inside a docstring or a
locator-citing comment, never as an identifier and never as a literal.

THE `MOVE` CENSUS
`MOVE` is the most-executed primitive in the migration. `MOVE_CENSUS` publishes
the plan's own measure - lines containing the word, comments included - counted
against the frozen checkout:

    general/gl051.cbl  157     sales/sl055.cbl     92  (the plan records 91)
    general/gl070.cbl   66     sales/sl060.cbl    177
    general/gl071.cbl    0     sales/sl100.cbl    124
    general/gl072.cbl   59     purchase/pl055.cbl  91
    general/gl080.cbl   48     purchase/pl060.cbl 165
                               purchase/pl100.cbl 122
                               irs/irs030.cbl     190

`MOVE_STATEMENT_CENSUS` publishes a second count, of lines that BEGIN a live
`MOVE` statement, totalling 1,250 against the first table's 1,291. Both carry the
counting method that produced them, because a single number whose method is
unstated cannot be checked. `general/gl071.cbl` counts ZERO either way: it is a
pure sort and contains no `MOVE` at all.

THE FIVE MOVE CATEGORIES, AND THE DIRECTION EACH TRUNCATES
Each category is stated in full - with its receivers, its locators and the open
question it raises - at the function that implements it. The index:

    (a) alphanumeric from alphanumeric   `move_alphanumeric`   right-truncates
    (b) numeric from numeric             `move_numeric`        both ends
    (c) alphanumeric from numeric        `move_alphanumeric`   right-truncates
    (d) numeric from alphanumeric        `move_numeric`        both ends, Q-13
    (e) a figurative constant            `move_figurative`     fill character

Category (b) and (d) DELEGATE the store to `acas_posting.cobol.arithmetic.store`,
which already owns scale alignment, the unsigned sign drop and silent high-order
truncation; two truncation code paths would mean one of them was eventually wrong.
Category (a) and (c) delegate truncate-and-pad to `acas_posting.cobol.usage.coerce`
for the same reason. Categories (c) and (d) exist at all because a `pic 9(n)`
DISPLAY item IS a character field in COBOL: `move WS-Batch-nos to Batch.`
[sales/sl060.cbl:L1073] moves into `Batch pic 9(5)` [copybooks/wspost.cob:L15], and
the digit-string image of a numeric sending item is its declared width, zero-filled
- `pic 9(5)` holding 42 has the image `00042`, not `42`.

Two facts from those functions must not be lost by a reader who stops here. An
UNSIGNED numeric receiver drops the sign, and the unsigned receivers are real -
`Input-Gross` through `Actual-Vat` are `pic 9(9)v99` with no sign under
`03 Amounts comp-3.` [copybooks/wsbatch.cob:L40-L44], which is question Q-3. A
`SIGN LEADING` receiver keeps the sign in the leading position, and the frozen
sources spell the clause two ways - `sign leading`
[copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25] and `sign is
leading` [copybooks/irswspost.cob:L14], [copybooks/irswspost.cob:L18] - which stay
exactly as written and are never reconciled into one.

Category (e) has no sending field at all: moving `ZERO` into an alphanumeric item
fills it with the character `0` - `move zero to tot-dr tot-cr.`
[general/gl072.cbl:L411] - while moving `SPACE` into a NUMERIC item DOES NOT
COMPILE, so it is refused rather than answered, which is question Q-9. The live
form is `move space to oi-applied oi-unapl oi-hold-flag.`
[sales/sl055.cbl:L655], whose three receivers are alphanumeric flags.

MULTIPLE RECEIVERS, AND GROUP MOVES
One `MOVE` may name several receivers, and each applies its own truncation
independently. The decisive exemplar is [general/gl051.cbl:L1017], `move batch to
l4-batch save-batch WS-Batch-Nos`: three receivers of three DIFFERENT descriptions
- `l4-batch pic z(4)9`, numeric-edited [general/gl051.cbl:L289]; `save-batch pic
9(5) comp`, binary [general/gl051.cbl:L174]; and `WS-Batch-Nos pic 9(5)`, zoned
DISPLAY [copybooks/wsbatch.cob:L19] - so one sending value gives three different
stored results. `move_to_all` therefore takes a SEQUENCE of receiving descriptors
and returns one value PER RECEIVER, in receiver order, as a tuple, never one value
reused; it cites ten further multi-receiver sites.

A `MOVE` whose receiver is a GROUP item is an alphanumeric move of the group's
whole byte image, with NO per-field conversion of any kind. A live one: `move
WS-Analysis-Record to WS-Value-Record` [sales/sl055.cbl:L538], whose two records
do NOT have the same width, so the move truncates. A group has no width of its own
- `FieldDescriptor.byte_length` says so and tells a caller to sum its children -
so `move_group` takes the width from `length` if given, else from the descriptor's
`character_length`, else from the sending image's own length. Summing a group's
children is the record layer's knowledge, not this module's.

REFERENCE MODIFICATION IS 1-BASED
The `(offset:length)` form occurs 83 times across the twelve program files, on
BOTH the sending and the receiving side. `REFERENCE_MODIFICATION_CENSUS`
publishes the frequencies: `(7:4)` x16, `(4:2)` x16, `(1:2)` x16, `(9:2)` x9,
`(1:6)` x8, `(6:2)` x5, `(1:4)` x5, `(7:2)` x4, `(1:1)` x3 and `(1:22)` x1.
Three further sites use variable operands, all of them `m (b:c)`:
[sales/sl060.cbl:L1091], [purchase/pl060.cbl:L954] and [purchase/pl100.cbl:L608].

`ref_mod` and `ref_mod_into` take a 1-BASED offset and an explicit length, so
that a program module transcribes `(9:2)` as `offset=9, length=2` and a reviewer
can diff it against the frozen source character for character. Translating to a
0-based slice at the call site is exactly the mistake this signature prevents.

THE SITE THAT MAKES THIS LOAD-BEARING  [sales/sl060.cbl:L1071-L1072]
    move  u-date (1:6) to post-date (1:6).
    move  u-date (9:2) to post-date (7:2).

The sending item is ten characters in `DD/MM/CCYY` form; the receiver is
`Post-Date pic x(8)` [copybooks/wspost.cob:L18], in `DD/MM/YY` form. Those two
statements are the ENTIRE four-digit-to-two-digit year conversion, done by
character surgery with no calendar logic whatsoever, and the receiver is a
database column; [sales/sl100.cbl:L612-L613] repeats the pair verbatim. This
module must not notice what those characters mean - section 0.6.6 makes the two
coexisting text forms a job for the harness normaliser. An off-by-one here would
corrupt every posted row of that column, which is why `ref_mod` publishes 1-based
offsets and why its self-test asserts the exact result of those two statements.

NUMERIC-EDITED RECEIVERS - ONE SHAPE, AND ONLY ONE, IS CLAIMED
Section 0.2.2 excludes report formatting BEYOND DATABASE EFFECTS. The emphasis
decides this file's scope: exactly one edited move does have a database effect, and
editing is a property of the `MOVE` verb, so that one is implemented here. At
[sales/sl060.cbl:L1085-L1094] a `pic z(7)9` item [sales/sl060.cbl:L213] is tallied
for leading spaces and then `STRING`ed into `Post-Legend pic x(32)`
[copybooks/wspost.cob:L24], a database column; the maintainer states the intent
just above, at [sales/sl060.cbl:L1082-L1083]. Mirrored at
[purchase/pl060.cbl:L207] with [purchase/pl060.cbl:L947-L956], and at
[purchase/pl100.cbl:L600-L610]. Note that `subtract b from 8 giving c` HARD-CODES
8, the field's own length; a program module transcribes that literally rather than
deriving it.

`move_to_edited` implements the Z-suppression-then-9 shape and nothing else - a run
of `Z` positions followed by a run of `9` positions, one character position per
digit position, no insertion character anywhere - and `EDIT_SYMBOLS_IMPLEMENTED`
names the two symbols. `z(7)9` and `z(4)9` are the two live instances, and ONLY
`z(7)9` is reachable from a database write - `z(4)9` at [general/gl051.cbl:L289] is
a print line, while `z(7)9` [sales/sl060.cbl:L213] reaches `Post-Legend pic x(32)`
[copybooks/wspost.cob:L24] through the `STRING` build at
[sales/sl060.cbl:L1082-L1091], mirrored at [purchase/pl060.cbl:L947-L956] and
[purchase/pl100.cbl:L600-L610]. That build's `subtract b from 8 giving c`
HARD-CODES 8, the field's own length, and a program module transcribes it literally
rather than deriving it. Every other edited picture in the frozen sources -
`z(6)9.99cr`, `z(8)9.99b`, `bbbz9`, `9(8).99-`, `z(4)9b(4)`, `bz9bbbbbb` and their
siblings - receives into a print line with no database effect and is OUT OF SCOPE:
such a picture is REFUSED rather than rendered, because no in-scope database write
reaches one, so no experiment against the compiled cycle can observe its rendering
and a rendering produced here would be this module's invention. That is question
Q-14, and `UnobservableEditedPicture` carries the reasoning at the point of
refusal. The insertion symbols `*`, `$`, `,`, `DB`, `+`, `/` and `0` are not
implemented at all: each occurs zero times.

WHY `INSPECT` AND `STRING` LIVE HERE
The folder requirement closes this folder at exactly eight files: "Nothing else.
No `strings.py`, no `numeric.py`, no `helpers.py`." Three in-scope programs
nevertheless build a DATABASE field with `INSPECT ... TALLYING ... FOR LEADING`
and `STRING ... DELIMITED BY ... INTO ... POINTER`. Those verbs are
receiving-field character movement, they have a database effect, and the permitted
file set offers nowhere else for them, so they live here and are named here rather
than smuggled in - `inspect_tallying_leading` and `string_into`, each citing its
own sites. The tally variable ACCUMULATES into whatever it already holds, which is
precisely why [sales/sl060.cbl:L1086] writes `move zero to b.` first;
`inspect_tallying_leading` reproduces the accumulate and never resets implicitly.

A DIVERGENCE THAT MUST NOT BE UNIFIED
[sales/sl100.cbl:L620-L628] builds the SAME 32-character database column with FIVE
separate `STRING` statements sharing ONE pointer, using neither the edited-move nor
the `INSPECT` idiom. The maintainer flagged it himself at [sales/sl100.cbl:L618]:
"THIS DOES NOT APPEAR THE SAME as SL060 and PL060/PL100". It is a preserved
divergence in the same spirit as the three disagreeing moving-average guards, and
rule R-4 forbids unifying it. `string_into` therefore returns the updated receiver
AND the updated 1-based pointer, so five successive calls chain through one pointer
exactly as the five statements do. Note also that the separator there is FIVE
characters, `"  :  "`, not the three-character `" : "` of the `sl060` shape.

Both `DELIMITED BY SIZE` and `DELIMITED BY SPACE` are needed: across the twelve
program files `SIZE` occurs 22 times, `SPACE` 3 times, and a literal delimiter not
at all. [general/gl080.cbl:L530-L536] mixes the two in one statement and carries NO
`POINTER` phrase, so its pointer starts at 1; [irs/irs030.cbl:L1424-L1426] is the
same shape. Overflow is silent - the receiver is 32 characters and the sources can
exceed it (Q-11).

WHAT THIS FILE DELIBERATELY DOES NOT OWN
`INSPECT ... REPLACING ALL "." BY "/"` is not this module's. It appears at
[general/gl051.cbl:L1178-L1180] and [irs/irs030.cbl:L1312-L1314], and section
0.4.1.6 assigns the `.`, `,` and `-` separators to `acas_posting/dates.py`, a
standard-library-only module that does not import this package. The boundary is
recorded here so the omission reads as deliberate.
[irs/irs030.cbl:L1315], `inspect u-date tallying q for all "/"`, is the `FOR ALL`
form rather than `FOR LEADING` and sits inside that program's out-of-scope
validation section; only `Ledger-Postings-Add` [irs/irs030.cbl:L1569-L1733] is
migrated from `irs030`. It is found, named and not implemented.

ZERO-OCCURRENCE FORMS, RECORDED SO THE OMISSIONS READ AS DELIBERATE
`ZERO_OCCURRENCE_FORMS` publishes this list as data. Each was counted across the
twelve in-scope program files, and the first two across `copybooks/*.cob` too:
`MOVE CORRESPONDING`, `JUSTIFIED`, `UNSTRING`, `HIGH-VALUES`, `LOW-VALUES`,
`QUOTES` and a literal `DELIMITED BY` operand all count zero, so none is
implemented and only DEFAULT justification exists - from the left for an
alphanumeric item, on the implied decimal point for a numeric one.

`ALL "x"` needs a precise statement rather than a bare zero: it occurs FOUR
times, at [general/gl051.cbl:L265], [general/gl051.cbl:L269],
[general/gl072.cbl:L249] and [general/gl072.cbl:L251], and every one is a VALUE
clause declaring an initial value. As a `MOVE` sending operand - the only form
this module would implement - it occurs zero times, so it is absent.

The figurative constants that DO occur are `ZERO` (532 lines), `SPACES` (138),
`SPACE` (64) and `ZEROS` (12). `ZEROES` counts zero and is accepted anyway,
because it is the same word and refusing one spelling would be a validation this
module has no business adding.

A `MOVE` DOES NOT VALIDATE, AND NEITHER MAY THIS FILE  (rule R-3)
Rule R-3 forbids added validation, added fields, schema change and concurrency,
and the folder requirement states the consequence: "A COBOL `MOVE` does not
validate; neither may `move.py`. A `COMPUTE` that overflows its receiving field
silently truncates high-order digits; reproduce that rather than raising." So,
below:

no length check that raises, so a forty-character sending item moved into
`Post-Legend pic x(32)` [copybooks/wspost.cob:L24] loses its last eight
characters silently into a database column; no range check, so `123456.78` into
`pic 999v99` stores `456.78`; no "is this really a number?" check, per the A-13
note below; no truncation courtesy of any kind - no ellipsis, no marker
character, no warning suffix, no log record that alters control flow; no bounds
check on a reference-modified range or a subscript, because anomaly A-2 is
precisely an unbounded index, a quarter subscript computed by a ROUNDED divide
[general/gl080.cbl:L328] and used without a bound [general/gl080.cbl:L345]
against `Ledger-Q ... occurs 4` [copybooks/wsledger.cob:L36], and Python's own
slicing does not raise on an over-long slice (Q-10); and no concurrency - no
threading, no asyncio, no multiprocessing, no coroutine.

SIX `raise` STATEMENTS APPEAR IN THIS FILE, in two families, and neither family
fires on a value's magnitude, sign, length or numeric content - the things a COBOL
program would simply have accepted. The first is the rule R-2 carrier gate in
`_exact_carrier`, which fires on a value's Python TYPE, a binary float, that
cannot appear anywhere in this migration. The second is the three-member
`MovementWithNoCompiledAnswer` family, which fires on an ARGUMENT COMBINATION THE
COMPILED SYSTEM CANNOT PRODUCE AT ALL: `MOVE SPACE` into a numeric receiver does
not compile (Q-9); a reference-modification range past its item either does not
compile or reads adjacent storage a Python `str` does not have (Q-10); an edited
picture outside the Z-then-9 shape is reached by no in-scope database write and is
unobservable through the only contract this migration is verified against (Q-14).
Each was MEASURED, each carries its experiment at its own definition, and each
raises precisely so that no value this module invented can be written where the
oracle supplies none. Refusing to invent is not validating: an R-3 validation would
reject something the COBOL accepted, while these reject something the COBOL cannot
express. Where an ordinary programmer error must still be reported - an
unrecognised figurative spelling, an unrecognised delimiter - the enum constructor
reports it, so the mechanism is the standard library's and not a validation branch
added here. Nothing here checks a length, a range or a numeric class: a
forty-character sender into `Post-Legend pic x(32)` [copybooks/wspost.cob:L24]
loses its last eight characters silently, `123456.78` into `pic 999v99` stores
`456.78` silently, no subscript is bounded - anomaly A-2's unbounded quarter
subscript [general/gl080.cbl:L328], [general/gl080.cbl:L345] against
`Ledger-Q ... occurs 4` [copybooks/wsledger.cob:L36] is left to stand - and no
truncation courtesy of any kind is added.

ANOMALY A-13 DEPENDS ON THIS MODULE NOT VALIDATING
`general/gl072.cbl` skips a posting whose batch number is NOT NUMERIC, and the
anomaly register records the skip as entirely silent - "no message, counter or
trace" - at `if post-batch not numeric / go to loop.`
[general/gl072.cbl:L291-L292]. The register cites that construct as
[general/gl072.cbl:L289-L290] and its sibling skip on a specific handler error as
[general/gl072.cbl:L303-L304]; in the frozen checkout the two statements read at
L291-L292 and L306-L307. The offset is recorded rather than reconciled silently,
because the frozen file is the authority and a reader following either citation
should find both accounted for. If this module raised on non-numeric text that
silent skip could never be reproduced, so `is_numeric_class` is a PLAIN BOOLEAN
PREDICATE that never raises on content, and the skip itself is business logic
belonging to the program layer.

LAYERING  (Agent Action Plan section 0.4.3)
May import the standard library, the `acas_posting.dictionary` public enums, and
`acas_posting.cobol.field`, `.usage` and `.arithmetic`. Must not import
`acas_posting.records`, `.dal`, `.programs`, `.cli`, `.clock`, `.dates`,
`.workfiles`, the sibling compiled-oracle tree, or the sibling semantics modules
`picture`, `condition_names` and `sortverb`. No third-party import is permitted;
the interpreter is pinned to `requires-python = "==3.12.*"`.

`arithmetic` is imported deliberately: a numeric `MOVE` performs the same scale
alignment, unsigned sign drop and silent high-order truncation as an arithmetic
store, so it delegates rather than reimplementing. Because `picture` may not be
imported, the two-symbol reading of an edited receiver's picture below is local,
deliberately minimal, and recognises `Z` and `9` and nothing else. The program
layer imports THIS module; nothing here imports back toward it.

EXACT ARITHMETIC ONLY  (rule R-2)
A `MOVE` is transport, and transport is the quietest place in a system for a lost
penny. A numeric value moved here is a `decimal.Decimal` or an `int` and never
anything else, and a positions-and-lengths value - a reference-modification
offset or length, a `STRING` pointer, an `INSPECT` tally - is an `int` count. A
binary floating-point carrier is refused by `_exact_carrier` with a `TypeError`.
No `math`, no rounding built-in, no `pandas` and no `numpy` appear below; section
0.5.1 calls the last two exclusions absolute.

DETERMINISM  (rule R-6)
No clock, no environment, no randomness, and no `set` or `dict` iteration whose
order a caller can observe. `decimal` contexts are never touched here: every
decimal computation goes through `acas_posting.cobol.arithmetic`, which enters its
own explicit context, so a result cannot vary with what a caller did earlier.
Every published table is a `tuple` or a `MappingProxyType`, and the two membership
sets are `frozenset`s consulted only for membership.

ARBITRATED AGAINST COMPILED BEHAVIOUR  (rule R-6)
Rule R-6 makes the compiled program the arbiter of an ambiguous semantic question
and requires each resolution to be documented rather than settled silently. Six
questions are this module's own, in the `^Q-[0-9]+$` numbering space shared with
`data_dictionary/`; Q-2, Q-3, Q-4, Q-6, Q-7 and Q-8 are already in use and the
sibling `usage` claimed Q-5.1 to Q-5.3, so Q-9 through Q-14 are the next free
integers. Each is stated in full at the function that implements it:

    Q-3   a MOVE into an unsigned numeric receiver      `move_numeric`
    Q-9   `MOVE SPACE` into a numeric DISPLAY field     `move_figurative`
    Q-10  a reference-modified range past the field      `ref_mod`
    Q-11  a `STRING` pointer beyond the receiver         `string_into`
    Q-12  the exact `z(7)9` rendering of zero            `move_to_edited`
    Q-13  a non-numeric byte image into a numeric field  `_string_source`
    Q-14  an edited picture outside the Z-then-9 shape    `move_to_edited`

ALL SIX ARE NOW MEASURED against GnuCOBOL 3.2.0, invoked as the compile scripts
invoke it, with the experiment and its output recorded at the site that uses the
answer. The outcome is mixed, and the mix is the point: TWO questions turned out
NOT TO BE EXPRESSIBLE IN COBOL AT ALL, one was OVERTURNED, one splits into two
unlike cases, and two were confirmed.

Q-3 is not a new question: `arithmetic` already numbers it, has measured it, and
this module inherits both the number and the answer - the ABSOLUTE VALUE is stored
and the sign is dropped silently. The unsigned receivers are real - `pic 9(9)v99`
under `03 Amounts comp-3.` [copybooks/wsbatch.cob:L41-L44].

    Q-9   `MOVE SPACE` INTO A NUMERIC FIELD. RESOLVED, AND THE STATEMENT CANNOT
          EXIST. GnuCOBOL 3.2 rejects it at compile time - "error: MOVE of
          figurative constant SPACE to numeric item used", no object produced -
          for a numeric receiver and for a numeric-EDITED receiver alike.
          Neither cited authority contains it either: [sales/sl055.cbl:L655]
          moves space to three ALPHANUMERIC flags, and the class test at
          [general/gl072.cbl:L291-L292] reads bytes that arrived from a READ. So
          there is no compiled behaviour to reproduce, and `move_figurative`
          REFUSES the combination rather than answering it. See that function
          and `move_to_edited`.

    Q-10  A REFERENCE-MODIFICATION RANGE THAT RUNS PAST THE FIELD. RESOLVED,
          AND IT IS TWO UNLIKE CASES. A LITERAL out-of-range pair is a COMPILE
          ERROR - "error: length of 'leg' out of bounds: 4" - so it cannot exist
          in the compiled system either. A COMPUTED offset is NOT range-checked
          at run time and READS ADJACENT STORAGE: with `leg pic x(10)` followed
          by `guard pic x(10) value all "#"`, `leg(9:4)` was measured as `IJ##`
          and `leg(12:2)` as `##`. A Python `str` has no adjacent storage, so
          that outcome is NOT REPRODUCIBLE HERE and returning a short slice
          would be an invented answer rather than the measured one; `ref_mod`
          and `ref_mod_into` therefore refuse an out-of-range range explicitly.
          They can never do so for a faithful transcription - see the
          reachability proof at `ref_mod`, which shows all three
          computed-offset sites in the cycle are in bounds BY CONSTRUCTION.
    Q-11  A `STRING` POINTER BEYOND THE RECEIVER'S LENGTH. RESOLVED,
          CONFIRMED, with one refinement: a pointer already past the receiver
          writes NOTHING and THE POINTER IS LEFT UNCHANGED, while a source that
          fits partly contributes exactly the characters that fit and the
          pointer advances to one past the end. `Post-Legend pic x(32)`
          [copybooks/wspost.cob:L24] is the receiver and the five-statement
          build at [sales/sl100.cbl:L620-L628] can exceed it. `ON OVERFLOW`
          occurs zero times across the twelve program files, so the overflow is
          silent at every in-scope site.
    Q-12  THE EXACT `z(7)9` RENDERING OF ZERO. RESOLVED, CONFIRMED. Measured:
          zero renders as SEVEN SPACES THEN `0`, `1234` as four spaces then
          `1234`, and `pic z(4)9` renders zero as four spaces then `0`. It
          changes a database column when the sending value is zero
          [sales/sl060.cbl:L1085], and it also settles Q-10's reachability
          proof, because a picture that always prints its final digit bounds
          the tally that computes the one live reference-modification offset.
    Q-13  A NON-NUMERIC BYTE IMAGE MOVED INTO A NUMERIC RECEIVER. RESOLVED,
          AND THE PROVISIONAL ANSWER WAS WRONG. It is THREE different paths and
          they do not agree. (1) Through a group MOVE, a REDEFINES or a file
          READ - which is how the frozen system actually reaches it - the RAW
          BYTES SURVIVE VERBATIM and a class test then reports them
          non-numeric; this is anomaly A-13's path and it belongs to
          `move_group` and the record layer, not to a conversion. (2) Through
          an ELEMENTARY alphanumeric-to-numeric MOVE, GnuCOBOL CONVERTS rather
          than preserving: spaces and commas are ignored, a leading sign is
          honoured, a period is the decimal point, and ANY other character
          makes the WHOLE result ZERO. Thirty measurements pin this down and
          are recorded at `_alphanumeric_to_numeric`, which implements them;
          the provisional answer - text kept, right-aligned, losing from the
          LEFT - is wrong for this path. (3) Through a numeric COMPARISON or a
          SORT key the bytes are decoded as zoned decimal, which belongs to
          `acas_posting.cobol.sortverb` and to `is_numeric_class` here, and
          neither rewrites the bytes.
    Q-14  AN EDITED RECEIVING PICTURE OUTSIDE THE Z-THEN-9 SHAPE. RESOLVED AS
          UNOBSERVABLE, so it is REFUSED rather than rendered. No in-scope
          database write reaches it - every other edited picture in the frozen
          sources receives into a print line - which means no experiment
          against the compiled cycle can observe it and no fixture could be
          captured for it. The provisional fall-through rendered the digit
          positions with no suppression and no insertion character; that was an
          invented answer with nothing behind it, and it now raises instead.
          See `move_to_edited`.

FURTHER READING
    docs/migration/traceability.md           program-to-module,
                                             paragraph-to-function and
                                             field-to-dictionary-entry mappings
    docs/migration/anomaly-log.md            the register of legacy defects this
                                             migration reproduces, including
                                             A-2 and A-13 above
    docs/migration/ambiguity-resolutions.md  each semantic question and the
                                             compiled-behaviour arbitration that
                                             settled it, including Q-9 through
                                             Q-14 above

PROVENANCE AND THE FREEZE
There is no user rules document for this project: `review_rules` reports that none
was provided. The six binding rules R-1 through R-6 are the Agent Action Plan's
own, from its section 0.7.2, and are cited where they bear on this file. Nothing
has been invented to fill the gap, and everything the plan is silent on is held to
enterprise-standard best practice. Rule R-4 additionally forbids a vocabulary of
outcome words - canonical, effective, authoritative, corrected, recommended,
preferred, normalise, normalize, sanitize - because each would imply that a legacy
behaviour had been improved rather than reproduced; this paragraph is the only
place any of them is used as a word here. The word `resolved` above is not one of
them and carries only its literal rule R-6 sense, an ambiguous semantic question
ARBITRATED AGAINST COMPILED BEHAVIOUR, which R-6 requires each such answer to
record; it never says a legacy behaviour was improved. One prohibited word does
occur twice as part of a FILE NAME, `harness/normalize.py`, the sibling comparison
tool Agent Action Plan section 0.6.6 charges with reconciling the two coexisting
text forms of a run date; naming a file is not describing an outcome, and that
file is deliberately unreachable from this package. Under the section 0.8.1 freeze
- verbatim, "Any diff touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`,
`general/*.cbl`, `sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or
`mysql/ACASDB.sql` is a defect in the migration, regardless of how harmless it
appears" - every frozen file cited above is read as specification and is never
modified, reformatted, commented, relocated or built from here.
"""

from __future__ import annotations

import dataclasses
import decimal
import enum
import logging
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

from acas_posting.cobol import arithmetic as cobol_arithmetic
from acas_posting.cobol import usage as cobol_usage
from acas_posting.cobol.field import FieldDescriptor
# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader`
# and nothing else from the dictionary package. The loader re-exports these two
# vocabulary members (`loader.RE_EXPORTED_MODEL_NAMES`) as bindings to the ONE
# definition in `acas_posting.dictionary.model`, so the sending and receiving
# rules below are keyed on the same objects the dictionary artifact records
# (rule R-5) while this layer stays inside its one permitted door.
from acas_posting.dictionary.loader import SignPosition, Usage

#: Diagnostics only. The one thing this module logs is the reading or writing of
#: bytes OUTSIDE an enclosing group by an unchecked subscript - a condition whose
#: outcome is a property of the compiled binary rather than of the frozen source,
#: and therefore the one thing a maintainer must be able to see happening. No
#: control flow depends on a log record and none appears in a table dump.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

# The export surface, sorted so that it is stable and reviewable. It is the whole
# contract the record layer, the program layer and the arithmetic parity suite are
# written against, so it is stated exhaustively rather than left to be discovered:
# twelve verbs, two vocabularies, seven sentinels and seven published tables.
# There is deliberately NO calendar helper, NO print-line builder, NO
# `MOVE CORRESPONDING`, NO `JUSTIFIED` support, NO `UNSTRING`, and no business
# constant of any kind - the module docstring gives the frozen-source count behind
# each of those absences.
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
    "PACKED_RECEIVER_READ_ORACLE_EVIDENCE",
    "UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE",
    "ZERO",
    "ZEROES",
    "ZEROS",
    "ZERO_OCCURRENCE_FORMS",
    "Delimiter",
    "Figurative",
    "FigurativeSpaceIntoNumeric",
    "GroupItem",
    "MovementWithNoCompiledAnswer",
    "ReferenceModificationOutOfRange",
    "StorageGroup",
    "UnobservableEditedPicture",
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
    "subscripted_store",
    "subscripted_value",
)

# THE TWO VOCABULARIES
# A figurative constant and a `DELIMITED BY` phrase are both closed sets in
# the frozen sources, and both are published as enums so that a program
# module transcribes the COBOL word rather than a bare Python literal, and so
# that an unrecognised word is reported by the enum constructor rather than
# by a validation branch added here (rule R-3).
# Both are plain `enum.Enum` rather than `enum.StrEnum`, deliberately. A
# `StrEnum` member IS a `str`, which would make `isinstance(value, str)` true
# for `ZERO` and `SPACE`; the dispatch below distinguishes a figurative
# constant from sending text on exactly that test, and a member that answered
# to both would route a figurative constant down the text path.


class Figurative(enum.Enum):
    """The figurative constants the frozen sources actually move.

    Two members, because a census of the twelve in-scope program files finds
    exactly two figurative constants used as a `MOVE` sending operand:

        zero    532 occurrences   [general/gl072.cbl:L411]
        zeros    12 occurrences   [sales/sl060.cbl:L477]
        space    64 occurrences   [sales/sl055.cbl:L655]
        spaces  138 occurrences   [general/gl051.cbl:L1042]

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

    Across the twelve in-scope program files `DELIMITED BY SIZE` appears 22
    times, `DELIMITED BY SPACE` 3 times, and a literal delimiter not at all.
    The `SPACE` form's live sites both build a name for the
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


# =====================================================================
# THE THREE MOVEMENTS THE COMPILED SYSTEM CANNOT PERFORM
#
# Rule R-6 makes compiled behaviour the arbiter. Three of this module's six
# questions were measured to have NO compiled answer to reproduce, each for
# its own reason, and each therefore raises rather than returning a value
# this module made up:
#
#   Q-9   the statement DOES NOT COMPILE, so no program can contain it
#   Q-10  the statement does not compile with a literal range, and with a
#         computed one its measured behaviour - reading adjacent storage -
#         has no Python counterpart
#   Q-14  no in-scope database write reaches the shape, so no experiment
#         against the compiled cycle can observe it and no fixture exists
#
# Each exception's docstring carries the experiment and its output. None of
# the three can fire on a faithful transcription of a frozen statement, and
# each says why at its own definition, so a raise here means a
# transcription slip rather than a data condition (rule R-3).
# =====================================================================


class MovementWithNoCompiledAnswer(ValueError):
    """Base for a movement whose outcome the compiled system cannot supply.

    A `ValueError` because it reports an argument combination that cannot
    occur, not a numeric condition. One base so a program module can catch
    the whole family, and three subclasses so a traceback names which
    question it met.
    """


class FigurativeSpaceIntoNumeric(MovementWithNoCompiledAnswer):
    """`MOVE SPACE` into a numeric receiver - question Q-9, INEXPRESSIBLE.

    THE QUESTION.  What COBOL leaves in a numeric `DISPLAY` item after
    `MOVE SPACE`, since spaces in a numeric item then fail a class test and
    anomaly A-13's silent skip [general/gl072.cbl:L291-L292] turns on exactly
    that.

    THE EXPERIMENT.  The statement itself, compiled with GnuCOBOL 3.2.0 and
    no dialect flag, against a numeric receiver and then a numeric-edited one:

        01  n5  pic 9(5)  value 12345.
        01  m   pic z(7)9.
        move space to n5
        move space to m

    THE MEASURED RESULT.  BOTH ARE REJECTED AT COMPILE TIME:

        error: MOVE of figurative constant SPACE to numeric item used

    with `cobc` exiting 1 and producing no object file at all.

    THE RESOLUTION.  The statement cannot exist in the compiled system, so
    there is no behaviour to reproduce and any value returned here would be
    invented. Neither cited authority contains it either:
    [sales/sl055.cbl:L655] moves space to three ALPHANUMERIC flags -
    `oi-applied`, `oi-unapl` and `oi-hold-flag` - and the non-numeric bytes
    the class test at [general/gl072.cbl:L291-L292] reads arrived from a READ.

    ANOMALY A-13 IS UNAFFECTED, which is worth stating plainly: it never
    depended on this statement. Non-numeric bytes reach a numeric item through
    a group MOVE, a REDEFINES or a file READ, all of which carry bytes
    verbatim, and `is_numeric_class` reports False for them.

    `MOVE SPACE` into an ALPHANUMERIC or a GROUP receiver is ordinary and
    entirely supported; only the numeric and numeric-edited receivers raise.
    """


class ReferenceModificationOutOfRange(MovementWithNoCompiledAnswer):
    """A reference-modification range past the item - Q-10, UNREPRODUCIBLE.

    THE QUESTION.  What `item (offset:length)` yields when the range runs past
    the end of the item.

    THE EXPERIMENT, AND IT SPLIT IN TWO.  A LITERAL out-of-range pair was
    compiled first:

        01  leg    pic x(10)  value "ABCDEFGHIJ".
        move leg (9:4) to ...

    and GnuCOBOL 3.2.0 REJECTED IT AT COMPILE TIME -
    "error: length of 'leg' out of bounds: 4" - so a literal range that runs
    past its item cannot exist in the compiled system. A COMPUTED offset was
    then compiled, with a recognisable guard item declared immediately after
    the sender so that whatever lay beyond it could be identified:

        01  leg    pic x(10)  value "ABCDEFGHIJ".
        01  guard  pic x(10)  value all "#".
        move 9 to off  move 4 to len  move leg (off:len) to ...

    THE MEASURED RESULT.  A computed range is NOT range-checked at run time
    and READS ADJACENT STORAGE: `leg(9:4)` yielded `IJ##` and `leg(12:2)`
    yielded `##`. The run continued and exited zero.

    THE RESOLUTION.  Reading adjacent storage has no counterpart in Python,
    where a `str` has no neighbour and no fixed address. Returning a SHORT
    slice - which is what Python's own slicing gives, and what this module
    provisionally did - is a DIFFERENT answer from the measured one, not a
    weaker form of it: the measurement returned four characters where a slice
    returns two. So the range is refused, and the refusal names the
    measurement rather than pretending to satisfy it.

    IT CANNOT FIRE ON A FAITHFUL TRANSCRIPTION.  `ref_mod` carries the
    reachability proof: every literal offset in the cycle is in bounds because
    the compiler enforced it, and all three computed-offset sites are in
    bounds by construction.
    """


class UnobservableEditedPicture(MovementWithNoCompiledAnswer):
    """An edited picture outside Z-then-9 - question Q-14, UNOBSERVABLE.

    THE QUESTION.  How a numeric-edited receiver renders when its picture uses
    a symbol outside the `Z`-suppression-then-`9` shape - a floating sign, a
    comma, a currency symbol, `CR`, `DB`, `BLANK WHEN ZERO`.

    WHY NO EXPERIMENT CAN ANSWER IT.  Rule R-6 makes compiled behaviour the
    arbiter, and arbitration needs an OBSERVABLE. The only observable this
    migration has is table state: Agent Action Plan section 0.8.5 defines the
    pass condition as an empty ordering-normalised diff of the affected
    tables. Every edited picture in the frozen sources except the Z-then-9
    shape receives into a PRINT LINE, and report formatting beyond database
    effects is excluded by section 0.2.2 - so no scenario can make one of
    these pictures change a column, and no fixture can be captured for one.
    The question is not merely unmeasured; it is unobservable through the
    contract this migration is verified against.

    THE RESOLUTION.  Refuse it. The provisional fall-through rendered the
    digit positions with no suppression and no insertion character, which was
    an invented answer with nothing behind it and which would have written
    that invention into a column had a picture ever reached it.

    THE SHAPE THAT IS IMPLEMENTED is the one that does write:
    `pic z(7)9` [sales/sl060.cbl:L213] and `pic z(4)9`
    [general/gl051.cbl:L289], both measured. Only the first of the two is
    reachable from a database write; the second receives into a print line
    and is implemented because it is the SAME shape, not because it posts.
    See `move_to_edited`.
    """


#: `MOVE ZERO ...` - the singular spelling. [general/gl072.cbl:L411].
ZERO: Final[Figurative] = Figurative.ZERO

#: `MOVE ZEROS ...` - the plural spelling. [sales/sl060.cbl:L477].
ZEROS: Final[Figurative] = Figurative.ZERO

#: `MOVE ZEROES ...` - the variant spelling, zero occurrences, accepted
#: anyway because refusing it would be a validation (rule R-3).
ZEROES: Final[Figurative] = Figurative.ZERO

#: `MOVE SPACE ...` - the singular spelling. [sales/sl055.cbl:L655].
SPACE: Final[Figurative] = Figurative.SPACE

#: `MOVE SPACES ...` - the plural spelling. [general/gl051.cbl:L1042].
SPACES: Final[Figurative] = Figurative.SPACE

#: `... DELIMITED BY SIZE`. [sales/sl060.cbl:L1091-L1093].
DELIMITED_BY_SIZE: Final[Delimiter] = Delimiter.SIZE

#: `... DELIMITED BY SPACE`. [general/gl080.cbl:L531].
DELIMITED_BY_SPACE: Final[Delimiter] = Delimiter.SPACE


# THE PUBLISHED CENSUS TABLES
# Every table is a `tuple` or a `MappingProxyType`, so nothing published here can
# be mutated by a caller and no iteration order is a caller's to observe
# (rule R-6). They exist so that the traceability document the plan mandates can
# cite a count over the frozen source rather than an impression, and so that a
# future reader deciding whether some COBOL form is "missing" from this file finds
# the count that settled it (rule R-5).

#: `MOVE` LINE counts per in-scope program - the Agent Action Plan's own
#: metric, section 0.4.1, counting every LINE mentioning the verb, comments and
#: continuations included. Reproduced so that a reader comparing this file
#: against the plan finds the plan's own figures. Total 1,291 against the plan's
#: stated 1,290; the single-line difference is in `sales/sl055.cbl`, which the
#: plan records as 91 and the frozen file contains 92.
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
#: Every offset is 1 through 9, and every range is inside its item - which is
#: not a coincidence but a compiler guarantee, since GnuCOBOL rejects a literal
#: range that overruns (question Q-10, measured). Three further sites use a
#: computed pair rather than a literal one - `m (b:c)` at
#: [sales/sl060.cbl:L1091], [purchase/pl060.cbl:L954] and
#: [purchase/pl100.cbl:L608] - and are not counted here because their operands
#: are variables; `ref_mod` proves all three in bounds by construction.
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
#: with the space character. This table is consulted for TEXT receivers only -
#: `MOVE SPACE` into a numeric receiver does not compile and never reaches it,
#: which is question Q-9, measured.
#: [sales/sl055.cbl:L655] and [general/gl072.cbl:L411].
FIGURATIVE_FILL_CHARACTER: Final[Mapping[Figurative, str]] = MappingProxyType(
    {
        Figurative.ZERO: "0",
        Figurative.SPACE: " ",
    }
)

#: COBOL data-movement forms that occur ZERO times across the twelve in-scope
#: program files and every in-scope copybook, mapped to that count. Each is
#: therefore NOT implemented below, and this table makes the omission checkable
#: against the frozen source rather than leaving it to look overlooked (rule R-5).
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


# THE RULE R-2 CARRIER GATE
# THE ONLY `raise` STATEMENT IN THIS FILE. It fires on a value's Python TYPE,
# never on its content, which is the whole difference between an R-2 type gate
# and an R-3 validation. See the module docstring.


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


# PRIVATE HELPERS
# None of these is published. Each exists so that exactly one place in this
# file decides one question, and so that the twelve verbs read as the COBOL
# forms they implement rather than as string arithmetic.


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
       [copybooks/wspost.cob:L23] gives 10. It is the width a text movement
       fills when the receiver happens to be a numeric item, which a group
       MOVE reaches - Q-13's byte-preserving path 1.
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


def _alphanumeric_to_numeric(text: str) -> decimal.Decimal:
    """Read sending characters as a value the way an elementary MOVE does.

    Q-13, PATH 2  RESOLVED against the compiled oracle.

    THE QUESTION.  What an ELEMENTARY `MOVE` of an alphanumeric item into a
    numeric receiver does when the sending bytes are not a clean digit string.
    The provisional answer kept the characters, right-aligned in the receiver's
    byte width and losing from the left. That is what a byte-preserving path
    does, and an elementary MOVE is not one.

    THE EXPERIMENT.  A standalone GnuCOBOL 3.2.0 program declaring the sending
    and receiving shapes the cycle uses, moving a literal into the sender and
    the sender into the receiver, and displaying the receiver - FORTY-TWO
    cases, covering every character class a byte image can carry:

        01  s5    pic x(5).
        01  n5    pic 9(5).       01  n3    pic 9(3).
        01  sn5   pic s9(5).      01  n3v2  pic 9(3)v99.
        move "AB123" to s5   move s5 to n3   display n3

    THE MEASURED RESULT, all forty-two, grouped by what each one settles:

        SPACES ARE IGNORED, wherever they fall
            '1 3 5' -> 9(3)   = 135        '  123' -> 9(5) = 00123
            '123  ' -> 9(5)   = 00123      '     ' -> 9(5) = 00000
            '  1 2' -> 9(3)v99= 012.00     '12      '->9(5) = 00012
            '1 3 5' -> 9(3)v99= 135.00     '1 3 5' -> 9(5) = 00135
        A COMMA IS IGNORED TOO, AND SO IS A SECOND ONE
            '1,234' -> 9(5)   = 01234      '1,2,3' -> 9(5) = 00123
        A PERIOD IS THE DECIMAL POINT
            '12.45' -> 9(3)v99= 012.45     '1.5  '-> 9(3)v99 = 001.50
            '.1234' -> 9(3)v99= 000.12     '12.45'-> 9(5)    = 00012
        A LEADING SIGN IS HONOURED; INTO AN UNSIGNED RECEIVER IT IS DROPPED
            '-0123' -> s9(3)  = -123       '-0123'-> 9(5)    = 00123
            '+0123' -> s9(3)v99 = +123.00  '  -12'-> s9(5)   = -00012
            '-  12' -> s9(5)  = -00012     '+0123'-> 9(5)    = 00123
            '-0123' -> s9(3)v99 = -123.00
        A TRAILING SIGN IS IGNORED - NOT APPLIED, AND NOT FATAL EITHER
            '0123-' -> s9(5)  = +00123     '0123+'-> s9(5)   = +00123
            '+123-' -> s9(5)  = +00123   (the LEADING sign of the pair is
                                          the one that counts, and here it
                                          is `+`, so the result is positive)
        TWO SIGNS ON THE SAME SIDE ARE JUST AN INVALID CHARACTER
            '--123' -> s9(5)  = +00000
        ANY OTHER CHARACTER MAKES THE WHOLE RESULT ZERO - not just its own
        position, and not the valid digits beside it
            'AB123' -> 9(3)   = 000        'AB123'-> 9(5)    = 00000
            '0000A' -> 9(5)   = 00000      'A0000'-> 9(5)    = 00000
            'ab123' -> 9(5)   = 00000      'AB12C'-> 9(3)    = 000
            '12-45' -> 9(5)   = 00000      '12$45'-> 9(5)    = 00000
            '1e2  ' -> 9(5)   = 00000      '1.2.3'-> 9(3)v99 = 000.00
            'AB12C' -> 9(5)   = 00000      'AB123'-> 9(3)v99 = 000.00
            '0000q' -> s9(5)  = +00000   (an overpunch byte is NOT decoded
                                          on this path, though a class test
                                          and a SORT key do decode it)
        THE VALUE IS THEN STORED BY THE ORDINARY NUMERIC RULES - the sending
        characters carry an INTEGER unless a period says otherwise, so the
        implied decimal point is at the RIGHT END and not the receiver's
            '12345' -> 9(3)     = 345      '12345'-> 9(3)v99 = 345.00
            '12345' -> s9(3)v99 = +345.00  '12345'-> s9(5)   = +12345

    THE RESOLUTION, implemented below.  Remove every space and comma; drop a
    single trailing sign, which the compiler ignores; require what remains to
    be an optional leading sign, then digits with at most one period among
    them, and at least one digit. Anything else is ZERO. All forty-two
    measurements above follow from those four steps, and the store that
    receives the result applies scale truncation, silent high-order loss and
    the unsigned sign drop as it does for any other value.

    The four steps were deliberately probed at their edges rather than only in
    the middle: `'1,2,3'` proves the comma rule is every comma and not the
    first, `'--123'` proves a doubled sign falls to the invalid-character
    ZERO rather than to a double negation, and `'+123-'` proves the leading
    sign of a leading-and-trailing pair is the one that survives. Those three
    are the cases a reading built from the other thirty-nine would most
    plausibly have got wrong, so each is measured rather than reasoned about.

    WHAT THIS FUNCTION IS NOT.  It is not the byte-preserving path. When the
    frozen system holds non-numeric bytes in a numeric item they arrived
    through a group MOVE, a REDEFINES or a file READ - `post-batch pic 9(5)`
    [general/gl072.cbl:L291-L292] arrived from a READ - and on THAT path the
    bytes survive verbatim, which is what makes anomaly A-13's silent skip
    fire. `move_group` carries bytes and `is_numeric_class` reads them,
    overpunch included; neither routes through here.

    docs/migration/ambiguity-resolutions.md carries the register entry; this
    docstring is the resolution itself, recorded where the reading is done.

    Args:
        text: The sending characters.

    Returns:
        The value the compiled program reads from them - zero for any image
        the measurement showed converting to zero.
    """
    body = text.replace(" ", "").replace(",", "")
    if body[-1:] in ("+", "-"):
        # Measured: a trailing sign is discarded and does not set the sign.
        body = body[:-1]
    negative = body[:1] == "-"
    if body[:1] in ("+", "-"):
        body = body[1:]
    digits = body.replace(".", "", 1)
    if (
        not body
        or body.count(".") > 1
        or not digits
        or not digits.isascii()
        or not digits.isdigit()
    ):
        return decimal.Decimal(0)
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
    a sign symbol, a `9` before a `Z` - reports None, and `move_to_edited`
    then refuses it under question Q-14.

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


# THE FIVE MOVE CATEGORIES
# One primitive per category, because the truncation direction differs by
# category and both directions are silent. Every one of them cites the frozen
# site it implements (rule R-5), and not one of them inspects a value's
# content to decide whether it will fit (rule R-3).


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

    `JUSTIFIED` is not supported, and that is a decision rather than an
    oversight: the keyword occurs zero times in every in-scope copybook and every
    in-scope program, so the default placement from the left is the only one the
    frozen sources ever ask for.

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
    entry, measured there, and this one inherits the answer: the ABSOLUTE
    VALUE is stored and the sign is dropped silently.

    A `SIGN LEADING` receiver keeps its sign in its leading digit position,
    and the two spellings the frozen sources use are both honoured without
    being collapsed into one: `sign leading`
    [copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25] and
    `sign is leading` [copybooks/irswspost.cob:L14],
    [copybooks/irswspost.cob:L18]. The byte form is
    `acas_posting.cobol.usage`'s work; each descriptor keeps its own recorded
    wording.

    Category (d), numeric from alphanumeric, CONVERTS the sending characters to
    a value - it does not carry their bytes across. The conversion is the one
    measured at `_alphanumeric_to_numeric`: spaces and commas ignored, a
    leading sign honoured, a period read as the decimal point, and ANY other
    character making the whole result ZERO. `'AB123'` therefore stores 0 and
    not `AB123`, which is question Q-13, path 2, and which OVERTURNED this
    module's provisional answer.

    THE BYTE-PRESERVING PATH IS A DIFFERENT ONE, and anomaly A-13 depends on
    it rather than on this. `post-batch pic 9(5)`
    [general/gl072.cbl:L291-L292] holds non-numeric bytes because they arrived
    from a READ, not from a MOVE; a group MOVE or a REDEFINES reaches the same
    state. Those carry bytes verbatim - see `move_group` - and
    `is_numeric_class` then reports False for them, which is what makes the
    silent skip fire. Nothing here rewrites those bytes and nothing here
    fabricates digits.

    Args:
        value: The sending value - an exact numeric carrier, text, or a
            figurative constant.
        receiving_field: The receiving field.
        sending_field: Accepted for symmetry with the other categories and
            unused: a numeric receiver reads the sending VALUE, and a sending
            item's own picture cannot change it.

    Returns:
        What the receiver now holds - `decimal.Decimal` for a scaled field,
        `int` for the binary family and a zero-scale integer.

    Raises:
        TypeError: If `value` is a binary floating-point carrier (rule R-2).
        FigurativeSpaceIntoNumeric: If `value` is the figurative constant
            SPACE, which GnuCOBOL 3.2 rejects at compile time for a numeric
            receiver (question Q-9).
    """
    _exact_carrier(value, role="sending value")
    del sending_field
    if isinstance(value, Figurative):
        return move_figurative(value, receiving_field)
    if isinstance(value, str):
        # Q-13, path 2: the characters are CONVERTED, measured value for
        # measured value, and an unreadable image converts to zero.
        return cobol_arithmetic.store(
            _alphanumeric_to_numeric(value), receiving_field
        )
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
    four spaces.

    `MOVE SPACE` INTO A NUMERIC OR NUMERIC-EDITED RECEIVER RAISES, because the
    statement DOES NOT COMPILE - question Q-9, measured, and
    `FigurativeSpaceIntoNumeric` carries the compiler's own message. The
    frozen statement often cited for it, `move space to oi-applied oi-unapl
    oi-hold-flag.` [sales/sl055.cbl:L655], moves space into three
    ALPHANUMERIC flags, which is ordinary and supported here. Anomaly A-13's
    silent skip at [general/gl072.cbl:L291-L292] never depended on this
    statement: the non-numeric bytes it tests arrived from a READ.

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

    Raises:
        FigurativeSpaceIntoNumeric: `MOVE SPACE` into a numeric or
            numeric-edited receiver, which GnuCOBOL 3.2 rejects at compile
            time (question Q-9).
    """
    member = (
        figurative if isinstance(figurative, Figurative)
        else Figurative(figurative)
    )
    if member is Figurative.SPACE:
        if receiving_field.is_numeric or receiving_field.is_edited:
            # Q-9: measured as a COMPILE ERROR, so there is no behaviour to
            # reproduce. See FigurativeSpaceIntoNumeric.
            kind = (
                "numeric-edited" if receiving_field.is_edited else "numeric"
            )
            raise FigurativeSpaceIntoNumeric(
                f"MOVE SPACE into {receiving_field.name!r}, a {kind}"
                " item, does not compile under GnuCOBOL 3.2: 'error: MOVE of "
                "figurative constant SPACE to numeric item used'. The "
                "statement cannot exist in the compiled system, so no value "
                "is reproducible (question Q-9, measured). MOVE SPACE into an "
                "alphanumeric or group receiver is supported."
            )
        width = _receiver_width(receiving_field, length)
        fill = FIGURATIVE_FILL_CHARACTER[member]
        return fill if width is None else fill * width
    if receiving_field.is_edited:
        # Q-12, measured: the trailing `9` of `z(7)9` prints, so zero renders
        # as seven spaces then a single `0` [sales/sl060.cbl:L1085].
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
    RAISES `UnobservableEditedPicture` - question Q-14, resolved as
    unobservable rather than merely unmeasured, because the only observable
    this migration is verified against is table state and no scenario can make
    such a picture change a column. The provisional fall-through rendered its
    digit positions with no suppression and no insertion character, and that
    invention is now refused rather than written.

    THE SUPPRESSION RULE, MEASURED. Scanning from the left, a `Z` position
    holding a zero with no significant digit yet to its left is replaced by a
    space; a `Z` position at or after the first significant digit prints its
    digit; a `9` position always prints. With no `BLANK WHEN ZERO` - the clause
    occurs zero times in every in-scope copybook - the trailing `9` prints even
    for zero. Question Q-12, measured under GnuCOBOL 3.2.0 by moving each value
    into each declaration and displaying the receiver:

        zero  into pic z(7)9  ->  [       0]      seven spaces then 0
        1234  into pic z(7)9  ->  [    1234]
        zero  into pic z(4)9  ->  [    0]         four spaces then 0

    so the provisional answer was CONFIRMED. It changes a database column
    whenever the sending value is zero, which is why it was a question at all.

    AN ALPHANUMERIC SENDER IS CONVERTED FIRST, then edited, and that too was
    measured rather than assumed:

        '  123' into pic z(7)9  ->  [     123]
        'AB123' into pic z(7)9  ->  [       0]

    which is `_alphanumeric_to_numeric`'s measured rule - any invalid
    character makes the value zero - followed by this function's suppression.

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
        FigurativeSpaceIntoNumeric: If `value` is the figurative constant
            SPACE, which does not compile against an edited receiver either
            (question Q-9).
        UnobservableEditedPicture: If the receiving picture is outside the
            `Z`-then-`9` shape (question Q-14).
    """
    _exact_carrier(value, role="sending value")
    shape = _edited_shape_of(receiving_field.picture)
    if isinstance(value, Figurative):
        if value is Figurative.SPACE:
            # Q-9: measured as a COMPILE ERROR for a numeric-edited receiver
            # exactly as for a plain numeric one.
            raise FigurativeSpaceIntoNumeric(
                f"MOVE SPACE into {receiving_field.name!r}, a numeric-edited "
                "item, does not compile under GnuCOBOL 3.2: 'error: MOVE of "
                "figurative constant SPACE to numeric item used'. The "
                "statement cannot exist in the compiled system, so no value "
                "is reproducible (question Q-9, measured)."
            )
        exact: decimal.Decimal | int = 0
    elif isinstance(value, str):
        # Q-13, path 2, then the editing: measured as conversion followed by
        # suppression, with an unreadable image converting to zero.
        exact = _alphanumeric_to_numeric(value)
    else:
        exact = value
    if shape is None:
        # Q-14: refused, not rendered. See UnobservableEditedPicture.
        raise UnobservableEditedPicture(
            f"{receiving_field.name!r} declares the edited picture "
            f"{receiving_field.picture!r}, which is outside the Z-then-9 "
            f"shape {EDIT_SYMBOLS_IMPLEMENTED} implements. No in-scope "
            "database "
            "write reaches such a picture - every other edited picture in the "
            "frozen sources receives into a print line - so no experiment "
            "against the compiled cycle can observe its rendering and none is "
            "reproduced here (question Q-14). Report formatting beyond "
            "database effects is out of scope by Agent Action Plan section "
            "0.2.2."
        )
    stored = cobol_arithmetic.store(exact, receiving_field)
    plain = str(stored) if isinstance(stored, int) else format(stored, "f")
    digits = plain.lstrip("+-").replace(".", "")
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


# THE AUDITED DISPATCH
# One entry point a program module normally calls, and one for the
# multiple-receiver form. Both choose a category from the RECEIVING field and
# never from the sending value's convenience.


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
    and the `Usage` vocabulary imported above admits nothing else.

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


# REFERENCE MODIFICATION - 1-BASED, AND NEVER BOUNDS-CHECKED
# Eighty-three literal uses across the twelve in-scope program files, on both
# the sending and the receiving side, and one pair of them writes a database
# column. See `REFERENCE_MODIFICATION_CENSUS` for the per-pair counts.


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

    A RANGE THAT RUNS PAST THE ITEM IS REFUSED - question Q-10, measured, and
    `ReferenceModificationOutOfRange` carries the two experiments: a LITERAL
    out-of-range pair does not compile, and a COMPUTED one is not range-checked
    at run time and READS ADJACENT STORAGE, which a Python `str` has none of.
    Returning the short slice Python's own slicing gives would be a DIFFERENT
    answer from the measured one - two characters where the compiled program
    produced four - so it is refused instead of guessed.

    THE REACHABILITY PROOF, which is why that refusal can never fire on a
    faithful transcription. Every LITERAL offset in
    `REFERENCE_MODIFICATION_CENSUS` is 1 through 9 against items at least ten
    characters wide, and it could not be otherwise: the compiler rejects a
    literal range that overruns, so a literal range present in a frozen source
    is in bounds by the fact of having compiled. Exactly THREE in-scope sites
    compute their offset, and all three are the same statement shape -
    [sales/sl060.cbl:L1091], [purchase/pl060.cbl:L954] and
    [purchase/pl100.cbl:L608] - each writing `string m (b:c) ...` after
    `inspect m tallying b for leading space`, `subtract b from 8 giving c` and
    `add 1 to b`, with `m pic z(7)9` and `b`, `c` both `binary-char`
    [sales/sl060.cbl:L213-L215]. `m` is EIGHT characters, so `b` after the
    increment is the first non-space position and `c` is the count from it to
    the end: `b + c - 1 = 8` exactly, always, whatever the value. The range is
    in bounds BY CONSTRUCTION rather than by luck.

    That proof RESTS ON QUESTION Q-12's measurement, which is the interlock.
    `z(7)9` always prints its final digit - zero renders as seven spaces then
    `0`, measured - so the leading-space tally is at most 7 and `b` at most 8.
    Had that picture blanked entirely for zero, the tally would have been 8,
    `b` would have been 9, and the reference modification WOULD have run past
    the field. Two measurements, and only together do they establish that this
    module's refusal is unreachable.

    An offset below 1 is refused for the same reason: it would index from the
    end the way a negative Python index does, which is not a COBOL behaviour at
    all, and no in-scope site produces one.

    Args:
        text: The sending item's characters.
        offset: The 1-based first character position.
        length: The number of characters.

    Returns:
        The character range.

    Raises:
        TypeError: If `offset` or `length` is a binary floating-point carrier
            (rule R-2).
        ReferenceModificationOutOfRange: The range is not wholly inside `text`
            (question Q-10).
    """
    _exact_carrier(offset, role="reference-modification offset")
    _exact_carrier(length, role="reference-modification length")
    start = int(offset) - 1
    span = int(length)
    if start < 0 or span < 1 or start + span > len(text):
        raise ReferenceModificationOutOfRange(
            f"({offset}:{length}) is not wholly inside an item of "
            f"{len(text)} characters. A literal range like this does not "
            "compile under GnuCOBOL 3.2, and a computed one reads ADJACENT "
            "STORAGE, which a Python str does not have - so no value here is "
            "reproducible (question Q-10, measured). Every in-scope range is "
            "in bounds; see this function's reachability proof."
        )
    return text[start:start + span]


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

    A RANGE THAT RUNS PAST THE RECEIVER IS REFUSED, for the reason `ref_mod`
    sets out under question Q-10: on the receiving side the compiled program
    would write over ADJACENT STORAGE, and silently extending a Python string
    instead - which is what this primitive provisionally did - is a different
    outcome, not a weaker form of the same one. Callers hold a receiver at its
    full declared width, which every record layout initialises it to, so the
    two live sites are in bounds: `(1:6)` and `(7:2)` into
    `Post-Date pic x(8)` [copybooks/wspost.cob:L18].

    Args:
        receiver_text: The receiver's current characters, at its declared
            width.
        offset: The 1-based first character position of the range.
        length: The number of characters in the range.
        value: The characters to place in the range.

    Returns:
        The receiver's characters after the overwrite.

    Raises:
        TypeError: If `offset` or `length` is a binary floating-point carrier
            (rule R-2).
        ReferenceModificationOutOfRange: The range is not wholly inside
            `receiver_text` (question Q-10).
    """
    _exact_carrier(offset, role="reference-modification offset")
    _exact_carrier(length, role="reference-modification length")
    start = int(offset) - 1
    span = int(length)
    stop = start + span
    if start < 0 or span < 1 or stop > len(receiver_text):
        raise ReferenceModificationOutOfRange(
            f"({offset}:{length}) is not wholly inside a receiver of "
            f"{len(receiver_text)} characters. The compiled program would "
            "write over ADJACENT STORAGE, which a Python str does not have, "
            "so no result here is reproducible (question Q-10, measured). "
            "Hold the receiver at its declared width - every record layout "
            "initialises it to that - and every in-scope range fits."
        )
    placed = value[:span].ljust(span)
    return receiver_text[:start] + placed + receiver_text[stop:]


# THE TWO CHARACTER VERBS THAT LIVE HERE
# `INSPECT ... TALLYING ... FOR LEADING` and
# `STRING ... DELIMITED BY ... INTO ... POINTER` are receiving-field character
# movement, they have a database effect, and the folder they would otherwise
# belong to does not exist: the folder requirement closes this package at eight
# files and says, verbatim, "Nothing else. No `strings.py`, no `numeric.py`, no
# `helpers.py`." NOT here: `INSPECT ... REPLACING ALL "." BY "/"`, at
# [general/gl051.cbl:L1178-L1180] and [irs/irs030.cbl:L1312-L1314] - Agent Action
# Plan section 0.4.1.6 assigns separator handling for `.`, `,` and `-` to
# `acas_posting/dates.py`, a standard-library-only module that does not import
# this package, and the boundary is recorded so the omission is visible.


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

    Writes each source's contributed characters into the receiver starting at the
    1-based pointer, advancing the pointer by what was written, and OVERWRITING
    rather than clearing: COBOL's `STRING` leaves every position it does not reach
    exactly as it found it, which is why the frozen source clears the receiver itself
    first when it wants it clear - `move space to Arg-Test.`
    [general/gl080.cbl:L530].

    THE POINTER IS READ AND RETURNED, SO SUCCESSIVE STATEMENTS CHAIN. This is not a
    convenience; it is a divergence in the frozen sources that must not be unified.
    One program builds its 32-character receiver with a SINGLE statement carrying
    three sources, at [sales/sl060.cbl:L1091-L1094], while another builds the SAME
    column with FIVE successive statements sharing ONE pointer and does not use the
    edited-move idiom at all, at [sales/sl100.cbl:L620-L628], where the pointer is
    initialised by an ordinary `MOVE` and three further moves load the sources
    between the statements. The pointer is plainly the caller's variable, which is
    why it is passed in and handed back rather than being state this module keeps.
    The maintainer flagged the difference himself immediately above it
    [sales/sl100.cbl:L618]. Both shapes are supported, neither is rewritten into the
    other, and the fourth source in the five-statement build is FIVE characters where
    the single-statement build uses three - another difference left exactly as it is.

    A DELIMITER PER SOURCE, because the frozen sources mix them within one statement:
    [general/gl080.cbl:L530-L536] uses `SPACE`, `SIZE`, `SIZE`, `SPACE` in order.
    `DELIMITED BY SIZE` contributes the whole item including its trailing spaces;
    `DELIMITED BY SPACE` stops at the first space, which is how a space-padded item
    contributes only its significant characters [irs/irs030.cbl:L1424]. See
    `_string_source` for how a source names its own delimiter, and
    `ZERO_OCCURRENCE_FORMS` for the literal-delimiter form, which occurs zero times.

    OVERFLOW IS SILENT - question Q-11, RESOLVED and CONFIRMED against the
    compiled oracle, with one refinement the provisional answer had not
    stated. Measured under GnuCOBOL 3.2.0 against a `pic x(4)` receiver:

        pointer 6, source "AB"      ->  receiver UNCHANGED, POINTER STILL 6
                                        (with ON OVERFLOW present it FIRED,
                                         which is what proves the condition)
        pointer 3, source "ABCD"    ->  receiver "  AB", POINTER 5

    so a pointer already past the receiver writes nothing AND DOES NOT ADVANCE,
    while a source that fits partly contributes exactly the characters that fit
    and leaves the pointer one past the end. `Post-Legend pic x(32)`
    [copybooks/wspost.cob:L24] is 32 characters and the five-statement build at
    [sales/sl100.cbl:L620-L628] can exceed it. `ON OVERFLOW` occurs zero times
    across the twelve in-scope program files, so every in-scope overflow is the
    silent form.

    Args:
        receiver_text: The receiver's current characters, at its own width.
        sources: The sending operands, in statement order. Each is bare text, a bare
            exact numeric carrier, or a tuple naming its own delimiter and, when it
            is numeric, its own descriptor.
        pointer: The 1-based position to write from. Two frozen sites name no
            `POINTER` phrase at all - [general/gl080.cbl:L531] and
            [irs/irs030.cbl:L1424] - and for them the default 1 is the COBOL
            behaviour.
        delimited_by: The delimiter for any source that names none.

    Returns:
        The receiver's characters after the write, and the pointer's new 1-based
        value, so that the next statement can be handed both.

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
            # Q-11, measured: nothing is written AND the pointer does not
            # advance, silently.
            continue
        start = position - 1
        written = piece[:width - start]
        text = text[:start] + written + text[start + len(written):]
        position += len(written)
    return text, position


# THE NUMERIC CLASS CONDITION
# A predicate, never an exception, because anomaly A-13 depends on it.


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

    THE SKIP ITSELF IS NOT THIS MODULE'S. It is business logic and it belongs to
    the program layer's `gl072` module. This function only
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

    An item holding SPACES is not numeric, and that answer is still needed even
    though `MOVE SPACE` into a numeric item turned out not to compile
    (question Q-9): spaces reach a numeric item through a group MOVE, a
    REDEFINES or a file READ, all of which carry bytes verbatim, and it is
    THIS predicate that anomaly A-13's silent skip
    [general/gl072.cbl:L291-L292] consults. An empty item is not numeric
    either: there is no digit in it.

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


# ---------------------------------------------------------------------------
#  UNCHECKED SUBSCRIPTED STORAGE - `table (n)` where `n` is outside `OCCURS`
# ---------------------------------------------------------------------------
#
# ⭐ WHY THIS EXISTS. Four of the in-scope programs index an `OCCURS` table with
# a variable that nothing constrains to the declared range:
#
#     move     ledger-balance  to  ledger-q (a).          [general/gl080.cbl:L345]
#     add      work-vat  to  total-vat (a).               [sales/sl060.cbl:L526]
#     add      work-net  to  total-net (a).              [sales/sl060.cbl:L527]
#     add      work-goods to STurnover-Q (current-quarter)
#                                    [sales/sl060.cbl:L545, :L551, :L558]
#     add      work-vat  to  total-vat (a).            [purchase/pl060.cbl:L467]
#     add      work-net  to  total-net (a).            [purchase/pl060.cbl:L468]
#     add      work-goods to pturnover-q (current-quarter)
#                              [purchase/pl060.cbl:L484, :L490, :L497]
#
# `a` is loaded straight from `oi-type` [sales/sl060.cbl:L509],
# [purchase/pl060.cbl:L450], whose own copybook documents type codes running to
# 9 [copybooks/plwsoi.cob:L25-L34] against a table of `occurs 3`; and
# `05 Current-Quarter pic 9` [copybooks/wssystem.cob:L110] is a single digit
# indexing a table of `occurs 4`. Nothing tests either before it is used, and the
# compile scripts pass no subscript-checking flag, so the generated code addresses
# whatever byte the arithmetic lands on. That is anomaly A-2 in the register and
# it is reproduced, never fixed (rule R-4).
#
# ⭐ WHAT THE COMPILED PROGRAM ACTUALLY DOES - MEASURED, NOT INFERRED (rule R-6).
# GnuCOBOL 3.2.0 - the version the maintainer's own compile script targets
# [common/comp-common.sh:L9] - was driven with each of the four real layouts
# transcribed verbatim and a VARIABLE subscript, a literal one being refused at
# compile time (which is itself why the frozen `move oi-type to a` form is what
# makes any of this reachable). In every case the store is PLAIN LINEAR BYTE
# ADDRESSING with no bounds test, no diagnostic, no status and no abort:
# `element (n)` is written at `offset(element 1) + (n - 1) * bytes-per-occurrence`
# and whichever elementary items share those bytes are what change.
# :data:`UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE` records every reading.
#
# ⛔ WHAT MUST NOT BE DONE HERE, and each of these was measured to be wrong:
#   * NO clamp, NO modulo, NO default occurrence, NO skip. The compiled program
#     does none of them.
#   * NO Python `[n - 1]`. Subscript 0 becomes index -1 and silently accumulates
#     into the LAST occurrence, which corresponds to nothing: the measured
#     answer is the field IMMEDIATELY BEFORE the table.
#   * NO exception for an in-group window. The compiled program has a definite,
#     measured answer there, so raising would replace a reproduced anomaly with
#     an invented one (rules R-3, R-4).
#
# HOW IT IS MODELLED. A :class:`StorageGroup` is the enclosing COBOL group
# expressed as what the compiled program addresses: an ordered list of elementary
# items and their pictures, hence a byte image. A store encodes the value into the
# member's own picture and pokes those bytes at the computed offset; every
# elementary item overlapping the window is then decoded back out of the image, so
# an invalid packed nibble reads exactly as the compiled program reads it -
# tolerantly, which the measurement also confirmed.
#
# THE ONE THING THAT IS NOT REPRODUCIBLE, stated rather than guessed: a window
# that extends PAST the end of the enclosing group lands on a different `01` item,
# and which item that is - and whether the generated code padded between them - is
# a property of the compiled binary and not of the frozen source. The measurement
# showed the compiled program CONTINUES in that case (it ran to completion and
# returned normally, having also changed the process's own exit status), so control
# flow is preserved: the in-group bytes are written exactly, and the overflow is
# reported as a log record with no effect on control flow. Section 0.3.4's rule
# for a diagnostic that has no database effect is what licenses the log record.


#: Every reading taken from the compiled oracle, kept beside the code that
#: reproduces it so that a maintainer can re-run the experiment rather than
#: trust a comment. Each entry is
#: `(statement locator, subscript, what received the value)`.
#:
#: The probes transcribed `copybooks/wsledger.cob`, the tail of
#: `sales/sl060.cbl`'s `01 ws-data` [sales/sl060.cbl:L216-L233], the tail of
#: `purchase/pl060.cbl`'s `01 ws-data` [purchase/pl060.cbl:L208-L220] and the
#: `Quarters` window of `copybooks/wssl.cob` [copybooks/wssl.cob:L54-L66], and
#: `function length` of each group was read back to pin the widths GnuCOBOL
#: chose: `pic 99 comp` is ONE byte, `pic s9(5) comp` is FOUR, and
#: `pic s9(7)v99 comp-3` is FIVE.
UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE: Final[tuple[tuple[str, int, str], ...]] = (
    # `move ledger-balance to ledger-q (a)`; WS-Ledger-Record is 126 bytes.
    ("general/gl080.cbl:L345", 0, "Ledger-Last [copybooks/wsledger.cob:L29] - A COLUMN"),
    ("general/gl080.cbl:L345", 5, "bytes 1-6 of the trailing filler x(50) - no column"),
    ("general/gl080.cbl:L345", 6, "bytes 7-12 of the trailing filler x(50) - no column"),
    # `add work-vat to total-vat (a)` then `add work-net to total-net (a)`;
    # sl060's `01 ws-data` measures 62 bytes.
    ("sales/sl060.cbl:L526", 0, "work-goods [sales/sl060.cbl:L218]"),
    ("sales/sl060.cbl:L527", 0, "work-vat [sales/sl060.cbl:L217]"),
    ("sales/sl060.cbl:L526", 4, "ws-deduction and total-deduct, partially"),
    ("sales/sl060.cbl:L527", 4, "a, line-cnt and ws-deduction, partially"),
    # pl060's `01 ws-data` measures 50 bytes and the table is near its END.
    ("purchase/pl060.cbl:L467", 0, "work-goods [purchase/pl060.cbl:L213]"),
    ("purchase/pl060.cbl:L468", 0, "work-vat [purchase/pl060.cbl:L212]"),
    (
        "purchase/pl060.cbl:L467",
        4,
        "line-cnt and File-28-status, then 8 bytes PAST the 01 group",
    ),
    # `add work-goods to STurnover-Q (current-quarter)`; the sales-ledger window
    # measures 52 bytes. BOTH out-of-range neighbours are COLUMNS.
    ("sales/sl060.cbl:L545", 0, "Sales-Last [copybooks/wssl.cob:L55] - A COLUMN"),
    (
        "sales/sl060.cbl:L545",
        5,
        "Sales-Unapplied [copybooks/wssl.cob:L63] - A COLUMN",
    ),
    (
        "sales/sl060.cbl:L545",
        6,
        "Sales-Stats-Date and Sales-Partial-Ship-Flag - BOTH COLUMNS",
    ),
    # `add work-goods to PTurnover-q (current-quarter)`; the purchase-ledger
    # window [copybooks/wspl.cob:L43-L54] measures 58 bytes, SIX more than the
    # sales one, because the purchase record carries no partial-ship flag and its
    # trailing filler is x(12) rather than x(5). Seeded Purch-Last 200.02,
    # quarters 1.01/2.02/3.03/4.04, Purch-Unapplied 500.05, addend 77.77:
    # q=1 left Q1 78.78 and q=4 left Q4 81.81.
    ("purchase/pl060.cbl:L484", 0, "Purch-Last [copybooks/wspl.cob:L44] - A COLUMN"),
    (
        "purchase/pl060.cbl:L484",
        5,
        "Purch-Unapplied [copybooks/wspl.cob:L52] - A COLUMN",
    ),
    (
        "purchase/pl060.cbl:L484",
        6,
        "Purch-Stats-Date [copybooks/wspl.cob:L53] - A COLUMN - and the first "
        "two bytes of the trailing filler x(12)",
    ),
)


#: ⭐⭐ HOW THE COMPILED PROGRAM READS THE RECEIVER OF A SUBSCRIPTED `ADD` -
#: MEASURED, NOT INFERRED (rule R-6).
#:
#: An unchecked subscript makes the receiver's bytes an arbitrary slice of the
#: enclosing group rather than a field that was ever stored, so the receiver can
#: carry a nibble no `MOVE` would ever put there - typically the sign nibble of the
#: neighbouring packed field, landing in a DIGIT position. What the compiled
#: program then reads is NOT the digit-by-digit reading that
#: :func:`acas_posting.cobol.usage.decode` performs.
#:
#: `cobc -C` was used to confirm the code path first: `add <field> to <comp-3>`
#: compiles to `cob_add (&receiver, &addend, 0)`, the runtime's generic add. That
#: routine reads a COMP-3 receiver BYTE BY BYTE in base 100 rather than nibble by
#: nibble in base 10, and the two agree for every byte pattern a `MOVE` can
#: produce but diverge for the rest. The per-byte contribution was measured
#: directly, 26 byte values in each of three positions of a
#: `pic s9(7)v99 comp-3` field:
#:
#:     high nibble <= 9 and low nibble <= 9  ->  high * 10 + low   (ordinary BCD)
#:     high nibble <= 9 and low nibble >= 10 ->  255
#:     high nibble >= 10                     ->  0
#:
#: and the LAST byte of the field, whose low nibble is the sign, contributes its
#: high nibble as a single digit - EXCEPT when that low nibble is zero, which is
#: not a sign nibble at all, in which case the last byte contributes two digits
#: like any other. Readings that pin this: `0x4C` -> 4, `0x5C` -> 5, `0x99` -> 9,
#: `0x9A` -> 9, `0x9F` -> 9, against `0x10` -> 10, `0x20` -> 20, `0x30` -> 30.
#:
#: The reading is then truncated to the field's digit count with no diagnostic,
#: which is how a window whose bytes decode to more digits than the field holds
#: still yields a definite answer.
#:
#: ⛔ SIX READINGS ARE DELIBERATELY NOT REPRODUCED, and they are named rather than
#: quietly absorbed. When the receiver's LAST byte has an invalid HIGH nibble and a
#: zero low nibble - `0xA0`, `0xC0`, `0xD0`, `0xE0`, `0xF0` - the runtime yielded
#: 2550 where every other rule it obeys predicts 0, and no consistent digit rule
#: reproduces that column alongside the `0x20` -> 20 readings. The value is a
#: sentinel from the runtime's own lookup, so encoding it would assert a property
#: of one libcob build as if it were the accounting specification. The sixth is a
#: probe artefact rather than a program state: a trailing filler seeded with `"Z"`
#: (`0x5A`) instead of the SPACES the frozen programs hold.
#:
#: NEITHER EXCLUSION IS REACHABLE AT ANY MIGRATED SITE. A receiver window's last
#: byte is always one of three things, and none can carry a high nibble above 9: a
#: byte of a stored packed value (whose high nibble is a decimal digit), a
#: character byte of a DISPLAY field or filler (`0x20`-`0x3F`), or a small binary
#: counter. Every other reading - 89 of the 95 taken - is reproduced exactly,
#: including `0x32 0x30 0x32 0x34 0x20 0x20`, the real six-byte window that
#: `PTurnover-q (6)` addresses over `Purch-Stats-Date`.
PACKED_RECEIVER_READ_ORACLE_EVIDENCE: Final[tuple[tuple[str, str], ...]] = (
    ("444C000005 + 22.22", "465502222C"),
    ("444C00000C + 22.22", "465502222C"),
    ("000000000C + 22.22", "000002222C"),
    ("0A0000000C + 22.22", "550002222C"),
    ("00000000AC + 22.22", "000002222C"),
    ("0000000C0C + 22.22", "000004772C"),
    ("0000044655 + 22.22", "000006687C"),
    ("2020202020 + 22.22", "020204242C"),
    ("FFFFFFFFFC + 22.22", "000002222C"),
    ("123456789C + 22.22", "123459011C"),
    ("323032342020 + 77.77", "030323497 97C"),
)


def _packed_byte_contribution(byte_value: int) -> int:
    """One byte's contribution to a COMP-3 receiver read, as measured.

    See :data:`PACKED_RECEIVER_READ_ORACLE_EVIDENCE` for the readings. The two
    non-BCD branches return the runtime's own sentinels rather than raising,
    because the compiled program does not raise (rules R-3, R-4).
    """
    high, low = byte_value >> 4, byte_value & 0x0F
    if high > 9:
        return 0
    if low > 9:
        return 255
    return high * 10 + low


def _packed_receiver_value(
    raw: bytes, *, digits: int, scale: int
) -> decimal.Decimal:
    """Read a signed COMP-3 receiver the way `cob_add` reads it.

    Identical to :func:`acas_posting.cobol.usage.decode` for every byte pattern a
    `MOVE` can produce, and different only where an unchecked subscript has
    aliased bytes that were never a field. That equivalence is not asserted: it
    was measured on ordinary values of both widths the cycle uses,
    `pic s9(7)v99 comp-3` and `pic s9(8)v99 comp-3`, positive and negative.
    """
    accumulator = 0
    for byte_value in raw[:-1]:
        accumulator = accumulator * 100 + _packed_byte_contribution(byte_value)

    last = raw[-1]
    high, low = last >> 4, last & 0x0F
    if low == 0:
        #  A zero low nibble is not a sign nibble, so the byte carries two
        #  digits like any other. Measured: 0x10 -> 10, 0x20 -> 20, 0x30 -> 30.
        accumulator = accumulator * 100 + _packed_byte_contribution(last)
    else:
        accumulator = accumulator * 10 + (high if high <= 9 else 0)

    #  Silent high-order truncation to the field's digit count; `cob_add` was
    #  called with opt = 0, so there is no size-error path to take.
    accumulator %= 10**digits
    if low == 0x0D:
        accumulator = -accumulator
    return decimal.Decimal(accumulator).scaleb(-scale)


@dataclasses.dataclass(frozen=True)
class GroupItem:
    """One elementary item of a COBOL group, in declaration order.

    Attributes:
        name: The item's own name, exactly as the frozen source spells it. An
            occurrence of a table is named `item (n)` so that the layout reads
            like the storage the compiled program addresses.
        descriptor: Its picture, from `acas_posting.cobol.picture` or from the
            generated dictionary. `descriptor.byte_length` is the item's width,
            so no width is written here.
    """

    name: str
    descriptor: FieldDescriptor


class StorageGroup:
    """A COBOL group as the byte image the compiled program addresses.

    A group item in COBOL is not a container of independent fields; it is a run
    of bytes that its elementary items divide up, and two declarations can name
    the same bytes. That is the only reason this class exists: an unchecked
    subscript lands on bytes, so a byte model is the only thing that can say
    what it hits.

    ⛔ NOT A RECORD LAYER, and not a substitute for one. It holds no values, no
    identity and no defaults; the record dataclasses in
    `acas_posting.records` remain the layouts. This is a projection of ONE group
    for ONE statement, built at module scope beside the statement that needs it.

    Args:
        items: The group's elementary items, in DECLARATION ORDER, which in
            COBOL is byte order.
        source_locator: Where the group is declared, for the message a failure
            carries (rule R-5).

    Raises:
        ValueError: Two items share a name, which would make an offset
            ambiguous. A programmer error in the layout, never a data
            condition.
    """

    __slots__ = ("_items", "_offsets", "_size", "_source_locator")

    def __init__(self, items: Sequence[GroupItem], *, source_locator: str) -> None:
        offsets: dict[str, int] = {}
        cursor = 0
        for item in items:
            if item.name in offsets:
                raise ValueError(
                    f"StorageGroup {source_locator}: two items named "
                    f"{item.name!r}; an offset would be ambiguous"
                )
            offsets[item.name] = cursor
            cursor += item.descriptor.byte_length
        self._items: Final[tuple[GroupItem, ...]] = tuple(items)
        self._offsets: Final[Mapping[str, int]] = MappingProxyType(offsets)
        self._size: Final[int] = cursor
        self._source_locator: Final[str] = source_locator

    @property
    def items(self) -> tuple[GroupItem, ...]:
        """The elementary items, in declaration order."""
        return self._items

    @property
    def size(self) -> int:
        """The group's length in bytes - what `function length` reports."""
        return self._size

    @property
    def source_locator(self) -> str:
        """Where the group is declared in the frozen source."""
        return self._source_locator

    def __repr__(self) -> str:
        return (
            f"StorageGroup({self._source_locator}, "
            f"{len(self._items)} items, {self._size} bytes)"
        )

    def offset_of(self, name: str) -> int:
        """The item's byte offset from the start of the group, zero-based.

        Raises:
            KeyError: No item of that name. A programmer error in the layout.
        """
        try:
            return self._offsets[name]
        except KeyError:
            raise KeyError(
                f"StorageGroup {self._source_locator} has no item {name!r}"
            ) from None

    def descriptor_of(self, name: str) -> FieldDescriptor:
        """The item's descriptor.

        Raises:
            KeyError: No item of that name.
        """
        for item in self._items:
            if item.name == name:
                return item.descriptor
        raise KeyError(f"StorageGroup {self._source_locator} has no item {name!r}")

    def image(self, values: Mapping[str, object]) -> bytes:
        """Lay the group out as bytes, exactly as the compiled program holds it.

        Args:
            values: The current contents, keyed by item name. An item the
                mapping omits is laid out at its category's figurative value -
                zero for a numeric item, spaces for an alphanumeric one - which
                is how COBOL `INITIALIZE` leaves it and how every bridge's own
                load paragraph leaves an unset host variable.

        Returns:
            Exactly `size` bytes.
        """
        out = bytearray()
        for item in self._items:
            descriptor = item.descriptor
            if item.name in values:
                value = values[item.name]
            elif descriptor.is_str:
                value = ""
            else:
                value = 0
            out += cobol_usage.encode(
                _exact_or_text(value),
                usage=descriptor.usage,
                digits=descriptor.digits,
                scale=descriptor.scale,
                character_length=descriptor.character_length,
                signed=descriptor.signed,
                unsigned=descriptor.unsigned,
                sign_position=descriptor.sign_position,
            )
        return bytes(out)

    def read(self, image: bytes) -> dict[str, decimal.Decimal | int | str]:
        """Decode every elementary item out of a byte image.

        Tolerant in exactly the way the compiled program is tolerant: a byte
        pattern no `MOVE` would have produced is still decoded rather than
        rejected, which is what makes an out-of-range store's aftermath
        observable instead of fatal.
        """
        out: dict[str, decimal.Decimal | int | str] = {}
        for item in self._items:
            descriptor = item.descriptor
            start = self._offsets[item.name]
            raw = image[start : start + descriptor.byte_length]
            out[item.name] = cobol_usage.decode(
                raw,
                usage=descriptor.usage,
                digits=descriptor.digits,
                scale=descriptor.scale,
                character_length=descriptor.character_length,
                signed=descriptor.signed,
                unsigned=descriptor.unsigned,
                sign_position=descriptor.sign_position,
            )
        return out


def _exact_or_text(value: object) -> decimal.Decimal | int | str:
    """Narrow a group value to a carrier `usage.encode` accepts.

    Raises:
        TypeError: The value is a binary floating-point carrier (rule R-2) or a
            type no COBOL item can hold.
    """
    if isinstance(value, bool):
        # `bool` is an `int` subclass, and a COBOL item never holds one.
        raise TypeError(f"a COBOL item cannot hold a bool: {value!r}")
    if isinstance(value, float):
        raise TypeError(
            "binary floating point cannot reach COBOL storage (rule R-2): "
            f"{value!r}"
        )
    if isinstance(value, (decimal.Decimal, int, str)):
        return value
    raise TypeError(f"unsupported carrier for COBOL storage: {value!r}")


def _subscript_window(
    group: StorageGroup,
    *,
    member: str,
    element_length: int,
    subscript: int,
) -> tuple[int, int]:
    """Where `member (subscript)` lands, as `(offset, length)`.

    The whole of the unchecked-subscript reproduction is this one expression -
    `offset(member of occurrence 1) + (subscript - 1) * element_length` - which
    is the address the generated code computes and the reason a subscript of
    zero reaches the field BEFORE the table rather than its last occurrence.

    Args:
        group: The enclosing group.
        member: The name the layout gives this member of occurrence ONE, e.g.
            `"total-vat (1)"`.
        element_length: Bytes per occurrence, i.e. the sum of one occurrence's
            members. Stated by the caller from the frozen declaration rather
            than derived, because a table's occurrence may carry members the
            statement does not name.
        subscript: The subscript as the program computed it. NOT validated.

    Returns:
        The zero-based byte offset and the member's own width. The offset may be
        negative and the window may run past the end of the group; both are
        conditions the compiled program has, so neither is refused here.
    """
    base = group.offset_of(member)
    width = group.descriptor_of(member).byte_length
    return base + (subscript - 1) * element_length, width


def _window_bytes(
    group: StorageGroup, image: bytes, offset: int, width: int, *, statement: str
) -> bytes:
    """The window's current bytes, padded where it leaves the group.

    A window that starts before the group or ends after it reaches a different
    `01` item, whose identity is a property of the compiled binary rather than
    of the frozen source. Those bytes are read as NUL, which is what an
    `INITIALIZE`d group holds, and the substitution is logged so it is never
    silent.
    """
    if offset >= 0 and offset + width <= len(image):
        return image[offset : offset + width]
    raw = bytearray(width)
    for index in range(width):
        position = offset + index
        if 0 <= position < len(image):
            raw[index] = image[position]
    _LOG.error(
        "%s: unchecked subscript reads %d byte(s) outside %s (offset %d, width "
        "%d, group %d bytes); those bytes belong to an adjacent 01 item whose "
        "identity is a property of the compiled binary and are read as zero. "
        "Anomaly A-2 reproduced; see UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE.",
        statement,
        sum(
            1
            for index in range(width)
            if not 0 <= offset + index < len(image)
        ),
        group.source_locator,
        offset,
        width,
        len(image),
    )
    return bytes(raw)


def subscripted_value(
    group: StorageGroup,
    values: Mapping[str, object],
    *,
    member: str,
    element_length: int,
    subscript: int,
    statement: str,
) -> decimal.Decimal | int | str:
    """Read `member (subscript)` through the group's storage, unchecked.

    The read half of an `ADD ... TO table (n)`: the receiver is read from
    whichever bytes the subscript addresses, exactly as the generated code reads
    them, so an out-of-range receiver contributes its ALIASED value to the sum.

    Args:
        group: The enclosing group.
        values: Its current contents, keyed by item name.
        member: The member of occurrence ONE, as the layout names it.
        element_length: Bytes per occurrence.
        subscript: As the program computed it. NOT validated (rule R-3).
        statement: The frozen statement's locator, for the log record.

    Returns:
        The value those bytes decode to under the member's own picture.
    """
    image = group.image(values)
    offset, width = _subscript_window(
        group, member=member, element_length=element_length, subscript=subscript
    )
    raw = _window_bytes(group, image, offset, width, statement=statement)
    descriptor = group.descriptor_of(member)
    if (
        descriptor.usage is cobol_usage.Usage.COMP_3
        and descriptor.signed
        and descriptor.digits is not None
    ):
        #  A signed COMP-3 receiver is read by `cob_add`, whose base-100 per-byte
        #  reading differs from a nibble-by-nibble one exactly where an unchecked
        #  subscript has aliased bytes that were never a field. Measured; see
        #  :data:`PACKED_RECEIVER_READ_ORACLE_EVIDENCE`.
        return _packed_receiver_value(
            raw, digits=descriptor.digits, scale=descriptor.scale or 0
        )
    return cobol_usage.decode(
        raw,
        usage=descriptor.usage,
        digits=descriptor.digits,
        scale=descriptor.scale,
        character_length=descriptor.character_length,
        signed=descriptor.signed,
        unsigned=descriptor.unsigned,
        sign_position=descriptor.sign_position,
    )


def subscripted_store(
    group: StorageGroup,
    values: Mapping[str, object],
    *,
    member: str,
    element_length: int,
    subscript: int,
    value: decimal.Decimal | int | str,
    statement: str,
    rounding: str | None = None,
) -> dict[str, decimal.Decimal | int | str]:
    """Store into `member (subscript)` through the group's storage, unchecked.

    The write half. The value is stored into the member's own picture first -
    truncating toward zero unless the caller names a rounding mode, which is the
    COBOL default for a store without `ROUNDED` - and the resulting bytes are
    poked at the address the subscript computes. Every elementary item of the
    group is then decoded back out, so a caller sees exactly what the compiled
    program would leave behind, including in the fields that share the window.

    ⛔ NOTHING IS VALIDATED, CLAMPED OR REFUSED for an in-group window. That is
    the whole point: see this section's header for the measurements.

    Args:
        group: The enclosing group.
        values: Its current contents, keyed by item name.
        member: The member of occurrence ONE, as the layout names it.
        element_length: Bytes per occurrence.
        subscript: As the program computed it. NOT validated (rule R-3).
        value: What the statement stores.
        statement: The frozen statement's locator, for the log record.
        rounding: A `decimal` rounding mode for the store into the member's
            picture. None means the COBOL default, truncation toward zero.

    Returns:
        Every elementary item of the group, decoded after the store.

    ⛔ THE ONE LIMIT OF A VALUE-CARRYING MODEL, stated rather than left to be
    discovered. The window's own bytes are reproduced exactly, and so is the
    VALUE of every neighbour the window clips - which is what reaches the
    database, because the bridge's host variables carry values and never raw
    bytes. What is NOT carried forward is a clipped neighbour's non-canonical BYTE
    IMAGE. Two measured examples of the same thing:

      * a clipped PACKED neighbour can be left holding a `0x5` where its sign
        nibble was `0xC`; decoding then re-encoding normalises the nibble and
        preserves the value;
      * a clipped DISPLAY neighbour can be left holding `03 03 23 49`, which
        `Purch-Stats-Date` reads as 3339 by the zoned low-nibble rule - the value
        the oracle's own bytes yield, verified against them - and which
        re-encodes to `33 33 33 39`.

    The consequence to be aware of is narrow: a LATER `cob_add` whose RECEIVER is
    that same clipped neighbour reads raw bytes, so it could diverge. Exactly one
    migrated site could reach that - `sl060`'s `a = 4` clips `total-deduct`, which
    [sales/sl060.cbl:L565] then accumulates into - and it needs `oi-type = 4`,
    which [copybooks/slwsoi.cob:L24] documents as `Proforma (Not used)` on the
    sales side. The purchase side DOES use type 4 [copybooks/plwsoi.cob:L28] -
    that is finding F7 - but there the clipped neighbours are `line-cnt`
    (`binary-char`) and `File-28-status` (`pic 9` DISPLAY), neither of which any
    later statement accumulates into as a packed receiver, and the whole site was
    checked against the oracle: `line-cnt` came out at 115 in both.
    """
    descriptor = group.descriptor_of(member)
    encode_kwargs: dict[str, object] = {
        "usage": descriptor.usage,
        "digits": descriptor.digits,
        "scale": descriptor.scale,
        "character_length": descriptor.character_length,
        "signed": descriptor.signed,
        "unsigned": descriptor.unsigned,
        "sign_position": descriptor.sign_position,
    }
    if rounding is not None:
        encode_kwargs["rounding"] = rounding
    raw = cobol_usage.encode(_exact_or_text(value), **encode_kwargs)  # type: ignore[arg-type]

    image = bytearray(group.image(values))
    offset, width = _subscript_window(
        group, member=member, element_length=element_length, subscript=subscript
    )

    outside = 0
    for index in range(width):
        position = offset + index
        if 0 <= position < len(image):
            image[position] = raw[index]
        else:
            outside += 1
    if outside:
        _LOG.error(
            "%s: unchecked subscript %d writes %d byte(s) outside %s (offset "
            "%d, width %d, group %d bytes). The compiled program writes them "
            "into an adjacent 01 item and CONTINUES, so control flow is "
            "preserved and only the in-group bytes are reproduced here. "
            "Anomaly A-2; see UNCHECKED_SUBSCRIPT_ORACLE_EVIDENCE.",
            statement,
            subscript,
            outside,
            group.source_locator,
            offset,
            width,
            len(image),
        )
    return group.read(bytes(image))
