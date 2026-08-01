"""The COBOL `SORT` verb: COBOL key semantics with guaranteed stability.

This module orders a sequence of records on an ordered list of keys, the way
the compiled `SORT` verb orders one, and it guarantees that records whose keys
all compare equal come out in the order they went in. That is the whole of its
job. It holds no key tuple, no record layout, no work-file identity and no
accounting decision: a caller names the keys, and this module supplies the
comparison and the stability.

WHY THIS FILE EXISTS - STABILITY IS CORRECTNESS, NOT TIDINESS
=============================================================
Agent Action Plan section 0.6.4 opens its ordering findings with this one, and
it is the strongest of them. Quoted in full:

    "`gl072` locates the nominal-ledger account for each posting with a
    sequential read-next rather than an indexed read
    [general/gl072.cbl:L410-L412]. It finds the right account only because
    `gl071` has already emitted the stream in nominal-key order. Any change in
    sort stability or key composition produces silent misposting - no error, no
    diagnostic, wrong balances. This single dependency is why `sortverb.py`
    guarantees stability and why a dedicated test asserts `gl071`'s output
    ordering."

Agent Action Plan section 0.1.1, Goal 2, states the same fact as a goal:

    "In this codebase the dependency is load-bearing rather than incidental:
    `gl072` locates the nominal-ledger row for a posting with a *sequential*
    read rather than an indexed one, so it finds the correct account only
    because `gl071` has already emitted the transaction stream in nominal-key
    order. Perturb the sort and the program silently posts to the wrong
    account."

There is no error path to reproduce when this goes wrong, because the compiled
program raises none. A perturbed ordering posts real money to the wrong
nominal account and reports success. That is why the ordering contract below
is spelled out rather than assumed, why stability cannot be switched off, and
why `is_sorted` exists so a test can assert the ordering directly.

THE AUTHORITY FOR THIS FILE
===========================
Agent Action Plan section 0.3.1 fixes it in one line:

    sortverb.py    (SORT with COBOL key semantics and guaranteed stability)

Agent Action Plan section 0.4.1.4, the transformation row, verbatim:

    Target File                        Transformation  Source File
    acas_posting/cobol/sortverb.py     CREATE          general/gl071.cbl
    Key Changes: "Stable sort with COBOL key semantics; stability is required
                  because a downstream program reads sequentially"

Agent Action Plan section 0.1.2, transformation rule 13, verbatim:

    COBOL construct     Python construct                Transformation rule
    `SORT` on work file  Stable sort on the identical    "Stability matters
                         key tuple                       because `gl072` reads
                                                         sequentially"

And section 0.4.1.2 on the program this file serves: "The `SORT` verbs become
stable sorts on the identical key tuples. Contains no arithmetic at all. The
output ordering is a hard contract consumed by `gl072`."

THE ONE IN-SCOPE `SORT`, VERBATIM  [general/gl071.cbl:L172-L178]
================================================================
     sort     sort-trans
              on ascending key sort-batch
                               sort-ac
                               sort-pc
                               sort-post
              using  pre-trans
              giving post-trans.

Four keys, ALL ASCENDING, in the order batch, account, profit centre, posting.
`USING` / `GIVING` form: no INPUT PROCEDURE and no OUTPUT PROCEDURE, so the
primitive below needs only the whole-sequence shape - an ordered sequence in,
an ordered sequence out. There is deliberately no `RELEASE` / `RETURN`
streaming API, because a census of the twelve in-scope program files finds
`RELEASE` and `RETURN` ZERO times.

`gl071` is astonishingly small, and that minimalism is itself specification.
Its whole procedure division is `main.` [general/gl071.cbl:L167], one screen
display [general/gl071.cbl:L170], the `SORT` above, then `main-exit.`
[general/gl071.cbl:L180] and `goback.` [general/gl071.cbl:L181]. The program
contains ZERO arithmetic statements and ZERO `MOVE` statements. Nothing else
may creep in on either side of this boundary: the display is a diagnostic with
no database effect, and turning it into a log record belongs to
`acas_posting.programs.gl071_batch_sort`, not here.

THE KEY ORDER IS NOT THE RECORD'S DECLARATION ORDER
===================================================
The sort description record, verbatim [general/gl071.cbl:L136-L144]:

    Locator                       Field        Picture      In record  In key
    [general/gl071.cbl:L137]      sort-batch   pic 9(5)         1st      1st
    [general/gl071.cbl:L138]      sort-post    pic 9(5)         2nd      4th
    [general/gl071.cbl:L139]      sort-code    pic xx           3rd        -
    [general/gl071.cbl:L140]      sort-date    pic x(8)         4th        -
    [general/gl071.cbl:L141]      sort-ac      pic 9(6)         5th      2nd
    [general/gl071.cbl:L142]      sort-pc      pic 99           6th      3rd
    [general/gl071.cbl:L143]      sort-amount  pic s9(8)v99     7th        -
    [general/gl071.cbl:L144]      sort-legend  pic x(32)        8th        -

`sort-post` sits SECOND in the record and FOURTH in the key list.
`sort-ac` sits FIFTH in the record and SECOND in the key list.

A primitive that derived the key order from the record layout - or a caller
that assumed it could - would produce a different ordering with no error at
all, and the downstream sequential read would then post to the wrong accounts.
So `sort_records` takes the key list as an EXPLICIT ORDERED PARAMETER and
never infers it, never reorders it, never extends it and never drops a key.

The record is 70 characters wide (5 + 5 + 2 + 8 + 6 + 2 + 10 + 32), and the
input and output layouts [general/gl071.cbl:L112-L120] and
[general/gl071.cbl:L124-L132] are field-identical to the sort description, so
nothing is converted across the sort. That layout belongs to
`acas_posting.workfiles`, and is recorded here only to show that this module
changes no value - it changes only the order of the records it is handed.

WHAT THE SECOND AND THIRD KEYS ACTUALLY ARE
===========================================
This is the mechanical reason key composition matters, and it is worth naming
precisely rather than leaving as "nominal-key order".

The consuming program declares its input record with the account and profit
centre grouped together [general/gl072.cbl:L115-L117]:

     03  post-ledger.
         05  post-ac     pic 9(6).
         05  post-pc     pic 99.

That eight-character group is byte-for-byte the nominal ledger's own key -
`WS-Ledger-Key` [copybooks/wsledger.cob:L13] over `WS-Ledger-Nos pic 9(6)`
[copybooks/wsledger.cob:L14] and `Ledger-PC pic 9(2)`
[copybooks/wsledger.cob:L20], redefined whole as `pic 9(8)`
[copybooks/wsledger.cob:L21-L22]. So the sort's second and third keys, taken
together, ARE the ledger key the consumer walks; the first key groups by batch
and the fourth orders postings within one account. Drop the third key, or swap
the second and third, and the stream is no longer in ledger-key order even
though every individual key is still ascending.

ANOMALY A-14, AND THE PARAGRAPH THAT PROVES IT
==============================================
The anomaly register entry this module reproduces, verbatim:

    A-14  "The nominal account is located by sequential read, so correctness
          depends entirely on upstream sort order - [general/gl072.cbl:L410-
          L412]."

The reproducing modules are `acas_posting.programs.gl071_batch_sort` (which
emits the ordering by calling `sort_records` below) and
`acas_posting.programs.gl072_transaction_update` (which consumes it with a
sequential read). A dedicated test asserts `gl071`'s output ordering directly
rather than waiting for a state diff to catch it - Agent Action Plan section
0.6.9, verbatim: "`gl071`'s output ordering is asserted directly by a test
rather than left to be caught indirectly by a state diff."

Here is the paragraph, verbatim [general/gl072.cbl:L402-L413]:

     new-account.
         move     post-ledger  to  WS-Ledger-Key.
         if       read-ledger not = "R"
                  perform  GL-Nominal-Read-Next.   *> read ledger-file record.
         if       read-ledger not = "R"
                  move  zero   to  tot-dr  tot-cr.
         divide   WS-Ledger-Nos  by  100  giving  l6-account.

Read it closely. The key is moved into `WS-Ledger-Key` and then a READ NEXT is
performed anyway. The key move is INERT for a sequential read: it positions
nothing and it selects nothing. The program relies entirely on the stream
already being in ledger-key order. That is anomaly A-14 in one paragraph, and
it is why this module's ordering contract is a correctness requirement rather
than a convenience.

CITATION CORRECTIONS - THE FROZEN FILES ARE THE AUTHORITY
=========================================================
Three citations in this area do not match the frozen sources. They are stated
here so the wrong spans are not propagated by anyone reading this module.

  * THE SEQUENTIAL READ. The Agent Action Plan cites it as
    [general/gl072.cbl:L410-L412]. The verified lines are the key move at
    [general/gl072.cbl:L405] and the read itself at
    [general/gl072.cbl:L407-L408]. L410 and L411 hold the second
    `if read-ledger not = "R"` and its `move zero to tot-dr tot-cr`, and L413
    holds the `divide` the plan cites correctly elsewhere. The sibling module
    `acas_posting.cobol` records the same correction in its inventory.
  * THE PARAGRAPH `main.` IN `gl071`. Both the Agent Action Plan and the brief
    for this file place it at L169. The frozen file puts it at
    [general/gl071.cbl:L167]; L168 and L169 are the paragraph's underline
    comment and a blank comment line.
  * THE WORK-FILE NAMES. The Agent Action Plan cites
    [copybooks/wsnames.cob:L14-L17]. The verified span is
    [copybooks/wsnames.cob:L13-L16] - `01 File-Defs.` at L13,
    `02 file-defs-a.` at L14, then the two names at L15 and L16.

Two further spans are quoted with their verified lines below rather than the
plan's: the two silent skips of anomaly A-13 are at
[general/gl072.cbl:L291-L292] and [general/gl072.cbl:L306-L307], where the
plan cites L289-L290 and L303-L304.

NO INDEX, NO LOOKUP MAP, NO CACHE, NO FAST PATH
===============================================
Agent Action Plan section 0.8.4, verbatim, is a prohibition and not a
preference:

    "the migration must not 'optimise' the sequential nominal read into an
    indexed one, even though that would obviously be faster, because section
    0.6.4's first finding shows the sequential read is entangled with
    sort-order correctness. Any performance work is therefore out of scope by
    construction, not merely unrequested."

Concretely, in this file: no index of any kind, no `bisect`, no
`sortedcontainers`, no key-to-record map, no memoised lookup and no fast path.
There is no `find` verb here and there never will be - the consumer's job is
to walk the sequence this module returns, in order, exactly as the compiled
program walks its work file. The obvious speed-up is precisely the forbidden
change. The sibling `acas_posting.workfiles` carries the identical
prohibition, and the two must stay consistent.

THIS MODULE HOLDS NO KEY TUPLE AND NO BUSINESS LOGIC
====================================================
Agent Action Plan section 0.3.1, verbatim: "`cobol/` contains no business
logic and `programs/` contains no numeric primitives." Section 0.1.2 says the
same of this package: it "contains no business logic whatsoever."

So the four key names of the one live sort appear in this module's
documentation and nowhere in its code. There is no default key list, no module
constant naming a key, and no parameter whose default supplies one.
`acas_posting.programs.gl071_batch_sort` names the four keys, in the order
[general/gl071.cbl:L173-L176] gives them; `acas_posting.workfiles` holds the
two record sequences; this module supplies the comparison and the stability.

NO COBOL AT RUNTIME, AND NO FILE OF ANY KIND  (rule R-1)
========================================================
Rule R-1, verbatim: "The Python implementation must not execute, embed, or
shell out to the COBOL programs. COBOL is the specification for the migration,
not a runtime dependency of the result. The shipped artifact must run on a host
with no COBOL compiler and no COBOL runtime present." Agent Action Plan section
0.7.2 names this file among those that "reimplement picture-clause parsing, the
six storage classes, the arithmetic verbs, `MOVE` truncation, condition-name
evaluation and `SORT` key semantics".

So the sort below is plain CPython. Nothing here starts a process, loads a
foreign library, or reaches the sibling compiled-oracle tree: no `subprocess`,
no `ctypes`, no `cffi`, no `os.system`, no `shutil.which`, no `cobc`, no
`cobcrun`, and no shelling out to the system sort utility.

The COBOL `SORT` does use a work file - `sort-trans assign file-21`
[general/gl071.cbl:L102], and both the input and the output are
`organization line sequential` [general/gl071.cbl:L95] and
[general/gl071.cbl:L100]. This module reproduces none of that, because Agent
Action Plan section 0.3.1 is explicit:

    "Work files are in-process sequences, not tables and not temporary files."

There is therefore NO filesystem access anywhere below: no `open`, no
`pathlib.Path`, no `tempfile`, no read or write of any kind. The two work files
named at [copybooks/wsnames.cob:L15] and [copybooks/wsnames.cob:L16] are
`acas_posting.workfiles`'s concern; nothing about them reaches a disk and
nothing about them reaches a table dump.

WHAT "COBOL KEY SEMANTICS" MEANS HERE
=====================================
A COBOL `SORT` key is compared according to the CLASS of the key item, not
according to the bytes that happen to be in it. Two rules follow, and both are
driven from the key's own `FieldDescriptor` rather than from the runtime type
of the value, so that the decision is a property of the frozen declaration and
cannot vary with how a caller happened to represent a value.

  * A NUMERIC key compares ALGEBRAICALLY. All four keys of the one live sort
    are unsigned DISPLAY numerics - `pic 9(5)`, `pic 9(6)`, `pic 99`. For a
    field zero-padded to its full width the algebraic and character orderings
    coincide, so it is tempting to compare the text. They DIVERGE the moment a
    field holds spaces or is short of its declared width: as characters,
    `"20"` sorts after `"000100"`, while algebraically 20 comes before 100. So
    a numeric key is compared as a number - `int` for a zero-scale or
    binary-family item, `decimal.Decimal` for a scaled one - and never as text.
    A scaled DISPLAY item stores its digits with an IMPLIED decimal point, so
    digit text carrying no point is scaled by the item's own scale before
    comparison, which is what makes the comparison value the item's algebraic
    value. Within one key that scaling is order-neutral, since dividing every
    value in a key by the same power of ten preserves their order; it is
    applied because it is the correct reading of the field, not to change any
    ordering.
  * AN ALPHANUMERIC key compares CHARACTER BY CHARACTER under the native
    collating sequence, which here is plain ASCII. Verified across the twelve
    in-scope program files: no `PROGRAM COLLATING SEQUENCE` clause and no
    `SPECIAL-NAMES` alphabet anywhere, and the shared configuration copybook
    the sorting program itself copies at [general/gl071.cbl:L85] has its
    `SPECIAL-NAMES` paragraph commented out at [copybooks/envdiv.cob:L4-L5].
    So the native sequence governs and Python's own `str` comparison is it.
  * A GROUP item is alphanumeric for comparison purposes in COBOL even when
    every subordinate item is numeric, and it falls out of the same rule: a
    group's descriptor reports itself as not numeric, so it takes the character
    path. `post-ledger` [general/gl072.cbl:L115] is exactly such a group.

OPEN QUESTIONS, RECORDED RATHER THAN SETTLED  (rule R-6)
========================================================
Rule R-6, verbatim: "Where a semantic question is ambiguous, the compiled
program's observed behavior decides it, and each such resolution must be
documented rather than settled silently." Two questions land in this module.
Each provisional behaviour sits behind a named constant so that one edit
re-targets it once the compiled oracle has measured the answer, and
docs/migration/ambiguity-resolutions.md carries the register entry, the
experiment and its outcome.

    Q-7  THE ORDER OF RECORDS WHOSE KEYS ALL COMPARE EQUAL.
         The `SORT` statement [general/gl071.cbl:L172-L178] carries no
         `WITH DUPLICATES IN ORDER` phrase - verified: the string `duplicates`
         occurs ZERO times across the twelve in-scope program files - so the
         COBOL standard leaves the relative order of equal-key records
         UNSPECIFIED, and GnuCOBOL's actual behaviour has NOT been measured.
         The Agent Action Plan nevertheless mandates stability outright
         (section 0.1.2 rule 13, and section 0.6.4's "any change in sort
         stability ... produces silent misposting"). Both are true, and the
         provisional behaviour implemented below is INPUT ORDER PRESERVED,
         which satisfies the mandate. The compiled oracle must confirm it.

         AND THE TIE IS GENUINELY REACHABLE, which is why this is a live
         question and not a theoretical one. The program that produces these
         records performs a three-leg double-entry explosion
         [general/gl070.cbl:L495-L533]: a debit leg written at
         [general/gl070.cbl:L508], a credit leg negated by
         `multiply pre-amount by -1` [general/gl070.cbl:L517] and written at
         [general/gl070.cbl:L519], and a VAT leg written at
         [general/gl070.cbl:L532] only when both the VAT account and the VAT
         amount are non-zero [general/gl070.cbl:L521-L523]. The batch and
         posting numbers are moved ONCE, before the legs
         [general/gl070.cbl:L495-L496]; only the account and profit centre
         change from leg to leg. So two legs of one posting that land on the
         same account and profit centre carry an IDENTICAL four-key tuple, and
         their relative order is decided entirely by the tie behaviour. The
         dedicated ordering test covers exactly that case.

    Q-8  THE POSITION OF A VALUE A NUMERIC KEY CANNOT HOLD.
         A DISPLAY field can contain characters that are not digits - the
         consuming program tests for precisely that and skips the record
         silently, `if post-batch not numeric / go to loop.`
         [general/gl072.cbl:L291-L292]. Rule R-3 forbids adding a validation,
         so such a value must SORT and must NOT raise; if this module raised,
         that silence could never be reproduced. The provisional ordering is
         stated by `RANK_NOT_NUMERIC` below: a value a numeric key cannot hold
         orders BEFORE every value it can, deterministically and stably, with
         ties among such values broken by their text. What the compiled sort
         does with such a record has NOT been measured.

Both labels are fresh in the `^Q-[0-9]+$` numbering space shared with
data_dictionary/. Q-3, Q-4 and Q-6 are already in use in
data_dictionary/acas_posting_dictionary.json, and the sibling
`acas_posting.cobol.usage` claimed Q-5.1, Q-5.2 and Q-5.3, so Q-7 and Q-8 are
the next free integers and neither numbering disturbs the other.

UNEXERCISED PATHS, DISCLOSED AS SUCH
====================================
Three capabilities below are implemented and are NOT exercised by the in-scope
cycle. They are named here so that nobody mistakes them for verified
behaviour, and so that a future reader knows which parts have oracle evidence
behind them and which do not.

  * DESCENDING keys. Verified ZERO occurrences of `descending` across the
    twelve in-scope program files; the one live sort is all-ascending
    [general/gl071.cbl:L173-L176] and so is the out-of-scope table sort at
    [irs/irs030.cbl:L1496]. `SortDirection.DESCENDING` exists because a
    general `SORT` primitive without it would be misleading, not because
    anything uses it.
  * ALPHANUMERIC keys. The sort description declares four of them -
    `sort-code` [general/gl071.cbl:L139], `sort-date`
    [general/gl071.cbl:L140] and `sort-legend` [general/gl071.cbl:L144] - and
    NONE is a key in the one live sort.
  * SIGNED numeric keys. `sort-amount pic s9(8)v99`
    [general/gl071.cbl:L143] is likewise not a key. A signed key compares by
    algebraic value, so minus one hundred sorts before zero which sorts before
    one hundred; that is implemented correctly and is untested against the
    compiled sort because the compiled sort never does it.

THE SECOND `SORT` IN THE CHECKOUT - FOUND, AND OUT OF SCOPE
===========================================================
A census of every `SORT` across the twelve in-scope program files finds exactly
TWO statements. The second is [irs/irs030.cbl:L1496]:

     sort     COA-Table ascending key CoA-Desc.

That is an in-memory sort of an `OCCURS` table on one ascending alphanumeric
key, and it sits inside `Initialise-Main` at [irs/irs030.cbl:L1402], which
Agent Action Plan section 0.4.2 places OUT OF SCOPE: only
`Ledger-Postings-Add` [irs/irs030.cbl:L1569-L1733] is migrated from that
program. No table-sort API is implemented for it. It is recorded here so that a
reader auditing the `SORT` census can see it was found and deliberately
excluded, rather than wondering whether it was missed.

The census also finds ZERO `MERGE`, ZERO `RELEASE` and ZERO `RETURN`
statements, which is why the whole-sequence form below is the only shape this
module publishes.

Note for the record: Agent Action Plan section 0.4.1.2 speaks of "the `SORT`
verbs" and "the identical key tuples", in the plural. The verified in-scope
count is ONE statement with ONE key list. The frozen files are the authority.

EXACT ARITHMETIC ONLY  (rule R-2)
=================================
Rule R-2, verbatim: "No accounting value may pass through a binary
floating-point type at any point - not in computation, not in storage, not in
transport." And, verbatim, on what it forces into scope: "Files this rule
forces into scope: the whole of `acas_posting/cobol/*.py`."

A sort is transport, and it is the quietest place in a system for a rounding
error to change an outcome: coerce two equal-looking money values to `float`
and they may compare unequal, or two unequal ones may compare equal, and the
records swap places with nothing to show for it. So a comparison value here is
an `int`, a `decimal.Decimal` or a `str`, and never anything else. A `float` or
a `complex` reaching a key is refused with a `TypeError`.

That refusal is an R-2 TYPE GATE and NOT an R-3 validation, and the distinction
matters: it fires on a value whose Python TYPE cannot appear anywhere in
this migration, not on a value whose CONTENT a COBOL program would have judged.
A non-numeric DISPLAY value is content, and it sorts (see Q-8). A `float` is a
prohibited carrier, and it is refused.

No `float`, no `complex`, no `math`, no `round`, no `pandas` and no `numpy`
appear below. Neither does any arithmetic: this module compares values, it does
not compute them, so `acas_posting.cobol.arithmetic` is not involved and is not
imported.

DETERMINISM  (rule R-6)
=======================
Two runs of one scenario must be byte-identical, and in a sort module the route
to breaking that is short. So:

  * NO `set` and NO `frozenset` appears anywhere below, and no set literal is
    written. Iterating a set is the most direct possible source of an
    order-dependent result. Every collection here is a `tuple` or an ordered
    sequence, the key specification is a `tuple`, and `sort_records` returns a
    `tuple`.
  * NO tie-break depends on `hash` or `id`, so nothing varies with
    `PYTHONHASHSEED` or with where an object happens to live. The only
    tie-break is input order, which is a property of the caller's sequence.
  * NO clock, NO entropy source and NO environment read: no `datetime.now`, no
    `time.time`, no `random`, no `uuid`, no `os.environ`.
  * NO AMBIENT DECIMAL CONTEXT IS CONSULTED, and this is stronger than pinning
    one. Every `decimal.Decimal` below is built either from a string or from
    the three-tuple `(sign, digits, exponent)` form, both of which are exact
    and context-free, and no arithmetic operation is performed on one at all.
    Measured on this interpreter with a deliberately hostile ambient context of
    precision 1 and a minimum exponent of -2: the three-tuple form yields
    `0.0001` for a four-place quantity and a digit string yields its exact
    value, whereas `Decimal(1).scaleb(-4)` - the obvious way to apply an
    implied decimal point - yields `0.00`, silently wrong. `scaleb` is
    therefore never used, `decimal.getcontext` and `decimal.setcontext` are
    never called, and there is no context object to be perturbed.
    Non-finite `Decimal` values are excluded from the numeric path rather than
    compared, because a comparison against a NaN signals rather than ordering,
    and a total order is what this module owes its caller.

SEQUENTIAL, AND ADDS NOTHING  (rule R-3)
========================================
Rule R-3, verbatim: "The migration may not add validation logic, add fields, or
alter the database schema, and must not introduce concurrent execution." Four
consequences, all of them visible in the code below.

  * NO VALIDATION OF THE RECORDS BEING SORTED. A malformed key is sorted, not
    rejected - see Q-8. The consuming program reproduces two entirely silent
    skips, a non-numeric batch number [general/gl072.cbl:L291-L292] and a
    specific handler error [general/gl072.cbl:L306-L307], both with no message,
    no counter and no trace at all (anomaly A-13). Every `raise` below reports
    a PROGRAMMER error - a prohibited carrier type, an empty key list, an
    attempt to switch stability off, or a malformed `SortKey` - and not one of
    them can fire on the content of a record.
  * NO DE-DUPLICATION. `SORT ... USING ... GIVING` emits every input record, so
    the output length always equals the input length. No `DUPLICATES` phrase is
    present to suppress anything, and none is invented.
  * NO NEW FIELD. The same record objects come back, unmodified and unwrapped,
    in a new order. Nothing is attached to them: no sequence number, no
    original-position member, no sort metadata, no wrapper object. The internal
    pairing used while sorting is discarded before the result is returned, and
    no record is mutated at any point.
  * NO CONCURRENCY. Agent Action Plan section 0.2.2, verbatim: "Concurrency. No
    threads, no `asyncio`, no `multiprocessing`, no connection pooling.
    Execution is strictly sequential, matching the single-threaded COBOL."
    Nothing here is parallel or chunked, and no `async def` or `await` appears.

NAMES THIS MODULE MUST NOT PUBLISH  (rule R-4)
==============================================
Rule R-4, verbatim: "Defects present in the compiled behavior are part of the
specification. A defect reproduced is a success; a defect fixed is a failure."
Agent Action Plan section 0.8.2 preserves the user's own words: "There is no
test suite: compiled COBOL execution is the behavioral specification, defects
included. A defect reproduced is correct; a defect fixed is a failure."

Two prohibitions follow for a module whose only job is ordering.

Nothing here is named - or means - resolved, canonical, effective,
authoritative, corrected, recommended, preferred, normalise, normalize,
optimise, optimize or fast_path. A sort primitive that offered a "canonical"
ordering, or a "preferred" tie-break, would be inviting exactly the smoothing
that fails this migration.

This module adds no stabilising key of its own. It is tempting to "complete"
the four-key list with `sort-code` [general/gl071.cbl:L139] or `sort-date`
[general/gl071.cbl:L140], or to reorder it to match the record layout. Either
would change which record the consumer reads next. `sort_records` orders on
EXACTLY the keys it is given, in EXACTLY the order it is given them, and breaks
a remaining tie on input order alone.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
    MAY import       the standard library, the `acas_posting.dictionary` public
                     surface, and `acas_posting.cobol.field` for the
                     `FieldDescriptor` whose metadata decides numeric versus
                     character comparison
    MUST NOT import  `acas_posting.records`, `acas_posting.dal`,
                     `acas_posting.programs`, `acas_posting.cli`,
                     `acas_posting.clock`, `acas_posting.dates`,
                     `acas_posting.workfiles`, the compiled-oracle tree,
                     and this folder's own `picture`, `usage`, `arithmetic`,
                     `move` and `condition_names`

`acas_posting.workfiles` imports THIS module - it "supplies the sequences and
the key tuple", while "`sortverb` supplies the comparison and the stability
guarantee" - so the edge runs one way only and importing it back would close a
cycle. No third-party package is imported at all; `sortedcontainers` in
particular is neither pinned in the dependency inventory nor needed, because
CPython's own sort is stable.

TRACEABILITY  (rule R-5)
========================
Rule R-5, verbatim: "Every program must map to a module, every paragraph to a
function, and every field to a data-dictionary entry, and the mapping must be
recorded as a document rather than left implicit in the code."

docs/migration/traceability.md maps `gl071`'s `main.` paragraph
[general/gl071.cbl:L167] to `acas_posting.programs.gl071_batch_sort`, and that
module calls `sort_records` below - so this module's name is part of the
traceability chain and is deliberately stable and obvious. Every public name
here cites at least one live locator into the frozen sources, and each key's
field metadata arrives on a `FieldDescriptor`, which carries either its
data-dictionary key or its own source locator as mandatory provenance.

THE FREEZE
==========
Agent Action Plan section 0.8.1, verbatim: "Any diff touching `common/*.cbl`,
`common/*.scb`, `copybooks/*.cob`, `general/*.cbl`, `sales/*.cbl`,
`purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect in the
migration, regardless of how harmless it appears." Every COBOL line quoted
above is quoted, never edited; nothing in this module reads, writes, formats or
builds any of those trees.

FURTHER READING
===============
    docs/migration/traceability.md           program-to-module,
                                             paragraph-to-function and
                                             field-to-dictionary-entry mappings
    docs/migration/anomaly-log.md            the register of legacy defects
                                             this migration reproduces,
                                             including A-13 and A-14
    docs/migration/ambiguity-resolutions.md  each semantic question and the
                                             compiled-behaviour arbitration
                                             that settled it, including Q-7 and
                                             Q-8 above
"""

from __future__ import annotations

import decimal
import enum
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final, TypeVar

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary.model import CobolPythonStorage

# The export surface, sorted so that it is stable and reviewable. It is
# short by design: a direction vocabulary, one value object, one failure, one
# comparison-value accessor, the sort itself and an ordering assertion. There
# is no `find` verb, no merge, no release/return streaming API, no table-sort
# API and no key list of any kind - see the module docstring on Agent Action
# Plan sections 0.8.4 and 0.3.1 for why each of those absences is a requirement
# rather than an omission.
__all__: Final[tuple[str, ...]] = (
    "RANK_ABSENT",
    "RANK_NOT_NUMERIC",
    "RANK_VALUE",
    "ComparisonValue",
    "SortDirection",
    "SortKey",
    "SortVerbError",
    "comparison_values",
    "is_sorted",
    "sort_records",
)

#: A record type, preserved across the sort so that a caller gets back a tuple
#: of what it passed in rather than a tuple of `object`. Nothing about the type
#: is required or inspected: a record may be a dataclass instance, a mapping or
#: anything a `SortKey` accessor can read a value out of.
RecordT = TypeVar("RecordT")

ComparisonValue = tuple[int, Any]
"""One key's value, reduced to something totally ordered.

A pair of a RANK and a PAYLOAD. The rank comes first so that two values with
different ranks are separated by the rank alone and their payloads are never
compared against one another - which is what lets a value a numeric key cannot
hold (payload: its text) sit in the same total order as one it can (payload: a
number) without any cross-type comparison ever being attempted.

Within one key every record yields the same rank-to-payload-type pairing,
because the payload type is decided by that key's `FieldDescriptor` and not by
the runtime type of any individual value. Values at different key positions are
never compared with each other.
"""


# =============================================================================
#  THE PROVISIONAL ORDERING, BEHIND NAMED CONSTANTS  (rule R-6, Q-8)
# =============================================================================
#
# These three are the ranks of `ComparisonValue`. They are named, exported
# constants rather than literals for the reason the sibling
# `acas_posting.cobol.usage` names its own open-question knobs: the ordering of
# a value a numeric key cannot hold has NOT been measured against the compiled
# sort (Q-8 in the module docstring), so the provisional answer must be
# re-targetable by one edit and must be assertable by a test.
#
# The order is: absent, then a value the key cannot hold, then a value it can.

RANK_ABSENT: Final[int] = 0
"""Rank of a key value that is `None`.

COBOL has no null: every field in the frozen record layouts holds something,
and the bridge's load paragraphs initialise their host-variable group so an
unset field becomes zero or space rather than SQL NULL. So this rank exists
purely to keep the ordering TOTAL rather than to model anything the compiled
program can produce. Ordering first, and stably among themselves, is a choice
made so that the result cannot vary; it is not a claim about COBOL.
"""

RANK_NOT_NUMERIC: Final[int] = 1
"""Rank of a value a NUMERIC key cannot hold - the Q-8 provisional ordering.

Reached by a DISPLAY field holding characters that are not digits, which the
consuming program tests for explicitly and skips in silence,
`if post-batch not numeric / go to loop.` [general/gl072.cbl:L291-L292]. Rule
R-3 forbids adding a validation, so such a value SORTS and never raises: it
orders before every value the key can hold, with ties among such values broken
by their text and then by input order. What the compiled sort does with such a
record has not been measured.
"""

RANK_VALUE: Final[int] = 2
"""Rank of a value the key can hold: a number, or text for a character key."""


# Recognised inside a numeric key's text form. COBOL's own numeric class test
# accepts digits with an optional operational sign, so these are what a digit
# string may carry beyond the digits themselves. ASCII only, and deliberately
# so: the native collating sequence governs here - no `PROGRAM COLLATING
# SEQUENCE` clause and no `SPECIAL-NAMES` alphabet exists in the twelve
# in-scope program files, and the configuration copybook the sorting program
# copies at [general/gl071.cbl:L85] has its `SPECIAL-NAMES` paragraph commented
# out at [copybooks/envdiv.cob:L4-L5].
_ASCII_DIGITS: Final[str] = "0123456789"
_SIGN_CHARACTERS: Final[str] = "+-"
_MINUS_SIGN: Final[str] = "-"
_DECIMAL_POINT: Final[str] = "."
_SPACE: Final[str] = " "

# `ord("0")`, so a digit character becomes its value without any lookup by
# character. Spelt this way rather than with a string search because the digit
# string above is a membership test only.
_ZERO_ORDINAL: Final[int] = ord(_ASCII_DIGITS[0])

# Payload carried by an absent value. A constant, so that two absent values
# compare equal and their relative order is then decided by input order alone.
_ABSENT_PAYLOAD: Final[str] = ""


# =============================================================================
#  DIRECTION
# =============================================================================


class SortDirection(enum.StrEnum):
    """Which way one key orders - the `ASCENDING` / `DESCENDING` phrase.

    The phrase this models is `on ascending key`
    [general/gl071.cbl:L173-L176], the only form the migrated cycle uses.

    A `StrEnum`, matching the enumerations `acas_posting.dictionary.model`
    publishes, so a direction renders as its own name in a log line or a test
    failure without a conversion step.
    """

    ASCENDING = "ASCENDING"
    """Ascending, as every key of the one in-scope `SORT` is declared.

    `on ascending key sort-batch sort-ac sort-pc sort-post`
    [general/gl071.cbl:L173-L176]. This is the default, because it is the only
    direction the migrated cycle uses.
    """

    DESCENDING = "DESCENDING"
    """Descending. UNEXERCISED by the in-scope cycle - not verified behaviour.

    A census of the twelve in-scope program files finds ZERO occurrences of
    `descending`: the one live sort is all-ascending
    [general/gl071.cbl:L173-L176], and so is the out-of-scope table sort at
    [irs/irs030.cbl:L1496]. This member exists because a general `SORT`
    primitive without it would be misleading, and stability holds for it just
    as it does for `ASCENDING` - CPython's sort keeps equal-key records in
    input order even when reversing. Nothing in the migration relies on that,
    and no oracle evidence stands behind it.
    """


# =============================================================================
#  FAILURE
# =============================================================================


class SortVerbError(ValueError):
    """A `SORT` was requested that could not order anything truthfully.

    Every use of this error reports a PROGRAMMER error: an empty key list, an
    attempt to switch stability off, or a malformed `SortKey`. None of them can
    fire on the CONTENT of a record, which rule R-3 forbids - a malformed key
    value is sorted, not rejected (see `RANK_NOT_NUMERIC`). Downstream,
    `gl072` skips a posting whose batch number is not numeric with no
    message, no counter and no trace [general/gl072.cbl:L291-L292]; a raise
    here would make that silence impossible to reproduce.

    A `ValueError` subclass, matching the failure `acas_posting.cobol.field`
    raises for the same class of mistake, so a caller can catch either the
    specific type or the built-in one.
    """


# =============================================================================
#  ONE KEY
# =============================================================================


@dataclass(frozen=True, slots=True, eq=True)
class SortKey:
    """One `ON ASCENDING KEY` / `ON DESCENDING KEY` item.

    Frozen, slotted and value-equal: a key specification cannot be mutated
    behind a holder's back, two keys built from the same parts compare equal,
    so a caller may build the list once and reuse it, and two runs behave
    identically (rule R-6).

    A key is DELIBERATELY three things and no more - where to read the value,
    what the field IS, and which way it orders. It carries no name of its own,
    no ordinal, and no relationship to any other key: the position of a key in
    the list passed to `sort_records` is its significance, most significant
    first, exactly as the `SORT` statement lists its keys
    [general/gl071.cbl:L173-L176].

    THE KEY LIST IS NOT THE RECORD LAYOUT. In the one in-scope sort,
    `sort-post` [general/gl071.cbl:L138] is the SECOND field of the record and
    the FOURTH key, while `sort-ac` [general/gl071.cbl:L141] is the FIFTH field
    and the SECOND key. Nothing here infers an order from a layout, and no
    caller may either - a key list in declaration order would order the
    stream differently with no error at all, and the consuming sequential read
    [general/gl072.cbl:L407-L408] would then post to the wrong accounts.

    Attributes:
        accessor: How to read this key's value out of a record. A CALLABLE is
            applied to the record. A `str` names an attribute, read with
            `getattr`, or a mapping key where the record is a `Mapping` - both
            are supported because the work-file sequences this serves may hold
            either shape. A missing attribute or mapping key is NOT caught and
            NOT converted here: the interpreter's own `AttributeError` or
            `KeyError` propagates, because silently ordering on a value that
            could not be read is precisely the silent misposting Agent Action
            Plan section 0.6.4 warns about.
        descriptor: The `FieldDescriptor` for the field this key reads. It is
            what decides numeric versus character comparison, and the implied
            decimal point of a scaled item - the decision is a property of the
            frozen declaration, never of the runtime type of a value. It also
            carries the field's provenance, so `key.descriptor.cite()` answers
            "where in the frozen sources does this key come from" (rule R-5).
        direction: Which way the key orders. Defaults to
            `SortDirection.ASCENDING`, the only direction the in-scope cycle
            uses.
    """

    accessor: str | Callable[[Any], Any]
    descriptor: FieldDescriptor
    direction: SortDirection = SortDirection.ASCENDING

    def __post_init__(self) -> None:
        """Reject a key specification that could not order anything.

        Each check fires on a PROGRAMMER error, at construction time and not
        part-way through a sort, because a malformed key produces a WRONG
        ORDERING rather than an exception - and a wrong ordering here is money
        posted to the wrong nominal account with no diagnostic at all
        [general/gl072.cbl:L405], [general/gl072.cbl:L407-L408]. None of them
        can fire on the content of a record.

        Raises:
            SortVerbError: The descriptor is not a `FieldDescriptor`, the
                accessor is neither a non-empty attribute or mapping name nor a
                callable, or the direction is not a `SortDirection` member.
        """
        if not isinstance(self.descriptor, FieldDescriptor):
            raise SortVerbError(
                "A sort key needs the FieldDescriptor of the field it reads,"
                " because that descriptor is what decides numeric versus"
                " character comparison; got "
                + type(self.descriptor).__name__
            )
        if not callable(self.accessor) and not (
            isinstance(self.accessor, str) and self.accessor
        ):
            raise SortVerbError(
                "A sort key accessor must be a callable applied to the record,"
                " or a non-empty attribute or mapping name; got "
                + repr(self.accessor)
                + " for field "
                + self.descriptor.name
            )
        if not isinstance(self.direction, SortDirection):
            raise SortVerbError(
                "A sort key direction must be a SortDirection member, not a"
                " bare string, so that an unrecognised direction cannot be"
                " read as ascending; got "
                + repr(self.direction)
                + " for field "
                + self.descriptor.name
            )


# =============================================================================
#  READING ONE KEY OUT OF ONE RECORD
# =============================================================================


def _raw_value(record: Any, key: SortKey) -> Any:
    """Read one key's value out of one record, exactly as the key says to.

    Three accessor shapes, and no guessing between them: a callable is
    applied; a name is a mapping key when the record is a `Mapping`, and an
    attribute otherwise.

    NOTHING IS CAUGHT HERE. A callable that raises, an attribute that is not
    there, a mapping key that is absent - each propagates untouched. That is
    deliberate: a typo in an accessor name would otherwise read as "no record
    has a value for this key", every record would then tie, and the stream
    handed to the consuming sequential read [general/gl072.cbl:L407-L408] would
    be in input order rather than key order, with no error raised anywhere. A
    loud `AttributeError` is the only safe answer, and costs no code to leave
    it alone (rule R-3: no validation is added here).

    Args:
        record: The record to read from.
        key: The key naming what to read.

    Returns:
        The raw value, in whatever Python type the record holds it.
    """
    accessor = key.accessor
    if callable(accessor):
        return accessor(record)
    if isinstance(record, Mapping):
        return record[accessor]
    return getattr(record, accessor)


def _text_value(text: str, descriptor: FieldDescriptor) -> ComparisonValue:
    """Reduce a NUMERIC key's text form to its algebraic value.

    This is where a zoned DISPLAY field becomes a number. COBOL compares a
    numeric key algebraically, and for a field short of its declared width - or
    holding spaces - the algebraic and character orderings DIVERGE: as
    characters `"20"` sorts after `"000100"`, while algebraically 20 precedes
    100. So the digits are read as a number and never as text.

    The implied decimal point is applied here, and only to text. A scaled
    DISPLAY item stores its digits with no point character in them, so digit
    text is scaled by the field's own scale to recover the value the field
    holds. Whether the field HAS a fractional part at all is taken from its
    Python carrier, which the generated data dictionary decides per field
    (`CobolPythonStorage.DECIMAL` against `INT`) - rule R-2's data-driven
    carrier rule, applied to comparison. Within one key the scaling is
    order-neutral, since dividing every value in a key by the same power of ten
    preserves their order; it is applied because it is the correct reading of
    the field. Text that carries its OWN decimal point states its own scale and
    is read at that scale instead.

    A value the field cannot hold - spaces, letters, two points, a sign at both
    ends, nothing at all - is NOT rejected. It comes back at
    `RANK_NOT_NUMERIC`, the Q-8 provisional ordering, because the consuming
    program's own reaction to such a value is an entirely silent skip
    [general/gl072.cbl:L291-L292] that could not be reproduced if this module
    raised.

    Args:
        text: The key's value as held.
        descriptor: The field's description, giving the scale and carrier.

    Returns:
        The comparison value: `RANK_VALUE` with an `int` or a
        `decimal.Decimal`, or `RANK_NOT_NUMERIC` with the text as given.
    """
    body = text
    negative = False
    # An operational sign may lead or trail; COBOL's own numeric class test
    # accepts either, and the frozen layouts declare both spellings: a trailing
    # overpunch by language default and `sign leading`
    # [copybooks/wspost-irs.cob:L21] where a SIGN clause says otherwise.
    if body and body[0] in _SIGN_CHARACTERS:
        negative = body[0] == _MINUS_SIGN
        body = body[1:]
    elif body and body[-1] in _SIGN_CHARACTERS:
        negative = body[-1] == _MINUS_SIGN
        body = body[:-1]

    point_count = body.count(_DECIMAL_POINT)
    if point_count > 1:
        return (RANK_NOT_NUMERIC, text)
    fraction_length = 0
    if point_count == 1:
        fraction_length = len(body) - body.find(_DECIMAL_POINT) - 1
        body = body.replace(_DECIMAL_POINT, "", 1)

    # Membership against an explicit ASCII digit string rather than
    # `str.isdigit`, which is true for characters such as a superscript two
    # that no COBOL field can hold and that `int` then refuses.
    if not body:
        return (RANK_NOT_NUMERIC, text)
    for character in body:
        if character not in _ASCII_DIGITS:
            return (RANK_NOT_NUMERIC, text)

    if point_count == 1:
        exponent = -fraction_length
    elif descriptor.python_storage is CobolPythonStorage.DECIMAL:
        exponent = -(descriptor.scale or 0)
    else:
        exponent = 0

    # Built from the three-tuple form, which consults NO decimal context and so
    # cannot be perturbed by what a caller did before. `Decimal(1).scaleb(-n)`,
    # the obvious alternative, IS context-sensitive and yields a silently wrong
    # value under a narrow ambient context - see DETERMINISM in the module
    # docstring, where the measurement is recorded.
    digits = tuple(ord(character) - _ZERO_ORDINAL for character in body)
    value = decimal.Decimal((1 if negative else 0, digits, exponent))
    if exponent == 0:
        # Exact at exponent zero, and it keeps an integral key's comparison
        # value an `int` - the carrier the field's own declaration names.
        return (RANK_VALUE, int(value))
    return (RANK_VALUE, value)


def _comparison_value(record: Any, key: SortKey) -> ComparisonValue:
    """Reduce one key of one record to something totally ordered.

    The single decision point for what "COBOL key semantics" means, and it is
    driven by the key's `FieldDescriptor` and not by the runtime type of the
    value, so that the answer is a property of the frozen declaration:

      * a NUMERIC field compares algebraically - see `_text_value`;
      * anything else compares as characters under the native collating
        sequence, which covers an alphanumeric item and a GROUP item too, as
        COBOL compares a group as alphanumeric even when every subordinate item
        is numeric. `post-ledger` [general/gl072.cbl:L115-L117] is exactly such
        a group.

    Trailing spaces are not significant on the character path. COBOL compares
    alphanumeric operands of unequal size as though the shorter were extended
    on the right with spaces, so a value shorter than its declared width is
    padded to that width here. A value with no declared width - a group, for
    instance - is compared as given.

    Args:
        record: The record to read from.
        key: The key naming what to read and how it is declared.

    Returns:
        The comparison value for that key of that record.

    Raises:
        TypeError: The value is a `float` or a `complex`. This is rule R-2's
            TYPE GATE, not a validation of content: a binary floating-point
            value may not pass through any part of this migration, in
            computation, in storage or in transport, and a sort is transport. A
            key coerced to `float` can make two equal money values compare
            unequal, or two unequal ones compare equal, and the records then
            swap places with nothing to show for it. A value whose CONTENT a
            COBOL program would have judged non-numeric is a different matter
            entirely and sorts - see `RANK_NOT_NUMERIC`.
    """
    raw = _raw_value(record, key)
    if isinstance(raw, (float, complex)):
        raise TypeError(
            "Rule R-2 forbids a binary floating-point value anywhere in this"
            " migration, including as a sort key, because a float comparison"
            " can reorder equal decimal values; field "
            + key.descriptor.name
            + " was handed a "
            + type(raw).__name__
            + ". Pass an int, a decimal.Decimal or the field's text form."
        )
    if raw is None:
        return (RANK_ABSENT, _ABSENT_PAYLOAD)
    if key.descriptor.is_numeric:
        if isinstance(raw, decimal.Decimal):
            # A non-finite Decimal is excluded from the numeric path rather
            # than compared: a comparison against a NaN signals instead of
            # ordering, and a total order is what this module owes its caller.
            # No COBOL field can hold one.
            if raw.is_finite():
                return (RANK_VALUE, raw)
            return (RANK_NOT_NUMERIC, str(raw))
        if isinstance(raw, int):
            # Already an algebraic value, so no implied decimal point applies.
            # `int` and `Decimal` compare exactly against one another, so which
            # of the two carries a given value never affects the ordering.
            return (RANK_VALUE, raw)
        if isinstance(raw, str):
            return _text_value(raw, key.descriptor)
        return (RANK_NOT_NUMERIC, str(raw))
    text = raw if isinstance(raw, str) else str(raw)
    width = key.descriptor.character_length
    if width is not None and len(text) < width:
        text = text.ljust(width, _SPACE)
    return (RANK_VALUE, text)


def _require_keys(keys: Sequence[SortKey]) -> None:
    """Refuse a `SORT` with no key at all.

    A `SORT` statement with no key does not exist in COBOL, and returning the
    input order unchanged would be INDISTINGUISHABLE from a correct sort at the
    call site: the consuming program would then walk an unordered stream with a
    sequential read [general/gl072.cbl:L407-L408] and post to whichever account
    happened to come next, silently. So an empty key list fails loudly. This is
    a PROGRAMMER error and cannot fire on the content of a record.

    Args:
        keys: The key list to check.

    Raises:
        SortVerbError: The key list is empty.
    """
    if not keys:
        raise SortVerbError(
            "A COBOL SORT names at least one key - the one in-scope statement"
            " names four, [general/gl071.cbl:L173-L176] - and a sort on no key"
            " would return the input order while looking like a sort, which is"
            " exactly the silent misposting this module exists to prevent"
        )


def comparison_values(
    record: Any, keys: Sequence[SortKey]
) -> tuple[ComparisonValue, ...]:
    """Reduce one record to the ordered tuple of its key values.

    Published so that a test - or `is_sorted` - can inspect precisely what the
    sort compares, rather than inferring it from an outcome. It is in KEY
    ORDER, most significant first, which for the one in-scope statement is
    batch, account, profit centre, posting [general/gl071.cbl:L173-L176] and is
    NOT the record's declaration order [general/gl071.cbl:L136-L144].

    The value at each position is a `ComparisonValue`, a rank-and-payload pair;
    see that alias and `RANK_NOT_NUMERIC` for what the ranks mean and for the
    Q-8 open question behind them.

    Args:
        record: The record to reduce.
        keys: The keys, most significant first.

    Returns:
        One comparison value per key, in the order the keys were given.

    Raises:
        SortVerbError: The key list is empty.
        TypeError: A key value is a `float` or a `complex` (rule R-2).
    """
    _require_keys(keys)
    return tuple(_comparison_value(record, key) for key in keys)


def _pass_selector(
    place: int,
) -> Callable[[tuple[tuple[ComparisonValue, ...], Any]], ComparisonValue]:
    """Build the key function for one pass of the sort.

    One pass per key, the four of [general/gl071.cbl:L173-L176] being the
    live case.

    Args:
        place: Which key's comparison value the pass orders on.

    Returns:
        A function selecting that comparison value from a paired record.
    """

    def selector(
        pair: tuple[tuple[ComparisonValue, ...], Any],
    ) -> ComparisonValue:
        return pair[0][place]

    return selector


def sort_records(
    records: Sequence[RecordT],
    keys: Sequence[SortKey],
    *,
    stable: bool = True,
) -> tuple[RecordT, ...]:
    """Order records on the given keys, stably - the `SORT` verb itself.

    Reproduces the `USING` / `GIVING` form, which is the only form the in-scope
    cycle uses [general/gl071.cbl:L172-L178]: an ordered sequence in, an
    ordered sequence out, and every input record present in the output
    exactly once.

    HOW THE ORDERING IS PRODUCED, and why this way. The keys are applied in
    successive stable passes, from the LEAST significant key to the MOST
    significant. Each pass preserves the relative order of records it finds
    equal, so after the last pass the sequence is in first-key order, ties
    broken by the second, and so on - and records equal on EVERY key are still
    in the order they arrived, because no pass ever moved them relative to one
    another. One code path serves both directions, so the exercised ascending
    case and the unexercised descending case cannot diverge; no comparison
    function is built, and no value is negated to fake a reversal, which would
    be impossible for a character key in any event.

    STABILITY IS NOT OPTIONAL. Agent Action Plan section 0.6.4: "Any change in
    sort stability or key composition produces silent misposting - no error, no
    diagnostic, wrong balances." There is no parameter, flag, environment
    variable or subclass hook by which a caller gets an unstable ordering:
    `stable` accepts only `True`, and `SortDirection.DESCENDING` reverses the
    comparison without disturbing the tie order.

    THE RECORDS COME BACK UNTOUCHED. The same objects are returned, in a new
    order, with nothing attached to them and nothing mutated: no sequence
    number, no original-place member, no sort metadata, no wrapper (rule R-3).
    The pairing used internally is discarded before the result is built. The
    output length always equals the input length, because `SORT ... USING ...
    GIVING` emits every record and no `DUPLICATES` phrase is there to suppress
    anything.

    Args:
        records: The records to order, in a sequence whose order is defined -
            that order is what breaks a tie on every key, so an unordered
            container would make the result vary between runs (rule R-6).
        keys: The keys, MOST SIGNIFICANT FIRST, in exactly the order the `SORT`
            statement names them. They are used exactly as given: none is
            reordered, none is dropped, and none is added - this module never
            appends a stabilising key of its own (rule R-4).
        stable: Accepted only as `True`. Present so that the guarantee is
            visible in the signature rather than merely documented.

    Returns:
        The same records, in key order, as a `tuple`. A `tuple` and not a list,
        so the ordering a caller was handed cannot be edited in place.

    Raises:
        SortVerbError: The key list is empty, or `stable` was not `True`.
        TypeError: A key value is a `float` or a `complex` (rule R-2).
    """
    _require_keys(keys)
    if stable is not True:
        raise SortVerbError(
            "Stability cannot be switched off. The consuming program locates a"
            " nominal-ledger account with a sequential read"
            " [general/gl072.cbl:L407-L408] and is correct only because this"
            " ordering held, so an unstable sort would post to the wrong"
            " account with no error and no diagnostic; got stable="
            + repr(stable)
        )
    paired: list[tuple[tuple[ComparisonValue, ...], RecordT]] = [
        (comparison_values(record, keys), record) for record in records
    ]
    place = len(keys) - 1
    while place >= 0:
        paired.sort(
            key=_pass_selector(place),
            reverse=keys[place].direction is SortDirection.DESCENDING,
        )
        place -= 1
    return tuple(record for _, record in paired)


def is_sorted(records: Sequence[Any], keys: Sequence[SortKey]) -> bool:
    """Whether the records are already in the order these keys describe.

    The mechanism by which Agent Action Plan section 0.6.9's mitigation is
    realised, verbatim: "`gl071`'s output ordering is asserted directly by a
    test rather than left to be caught indirectly by a state diff." The
    dedicated ordering test and the scenario suites call this so that a
    perturbed ordering fails as an ordering failure, at the point it happens,
    instead of surfacing later as an unexplained difference in posted
    balances. The ordering asserted is the one declared at
    [general/gl071.cbl:L173-L176] and relied on by the sequential read at
    [general/gl072.cbl:L407-L408].

    THE WHOLE KEY TUPLE IS CHECKED, not just the first key. For each adjacent
    pair the keys are walked in order and the FIRST key on which the two differ
    decides, honouring that key's own direction; a pair equal on every key is
    in order whichever way round it sits, which is what makes this consistent
    with the stability `sort_records` guarantees rather than stricter than it.

    An empty sequence and a single record are both in order.

    Args:
        records: The records to check, in the order they are held.
        keys: The keys, most significant first.

    Returns:
        True when no adjacent pair is out of order.

    Raises:
        SortVerbError: The key list is empty.
        TypeError: A key value is a `float` or a `complex` (rule R-2).
    """
    _require_keys(keys)
    previous: tuple[ComparisonValue, ...] | None = None
    for record in records:
        current = comparison_values(record, keys)
        if previous is not None:
            for place, key in enumerate(keys):
                if previous[place] == current[place]:
                    continue
                ascending = previous[place] < current[place]
                if ascending is not (
                    key.direction is SortDirection.ASCENDING
                ):
                    return False
                break
        previous = current
    return True
