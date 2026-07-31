"""COBOL-language semantics for the ACAS Python 3.12 posting-cycle migration.

`acas_posting.cobol` supplies, as ordinary Python, the language-level services
the COBOL compiler used to provide for free: picture clauses, the numeric
storage classes, the arithmetic verbs and their store semantics, `MOVE` between
unlike pictures, 88-level condition names, and the `SORT` verb's key ordering.
It exists so that those semantics live in exactly one place, where they can be
proved against values captured from the compiled programs.

WHY THIS PACKAGE EXISTS
=======================
Agent Action Plan section 0.3.1, verbatim:

    "`cobol/` contains no business logic and `programs/` contains no numeric
    primitives. This split is what makes the arithmetic parity suite possible.
    Every picture-clause, packed-decimal, truncation and `MOVE` rule lives in
    `cobol/`, where it can be tested in isolation against values captured from
    the compiled programs, with no database and no scenario setup. The program
    modules then read as accounting logic, and any parity failure localises
    immediately to one layer or the other."

ZERO BUSINESS LOGIC
===================
This package "contains no business logic whatsoever" (Agent Action Plan
section 0.1.2), and the boundary is drawn in the folder's own words: if you
find yourself writing an account number, a VAT rate, a ledger balance or a
batch status in this folder, you are in the wrong folder. Accounting decisions
belong to `acas_posting.programs`; table access belongs to `acas_posting.dal`.
`condition_names` is not an exception to that - it publishes the 88-level
predicate mechanism named after the frozen declarations, never the decision
about which status permits which posting.

THIS FILE IMPORTS NOTHING, DELIBERATELY
=======================================
This module is a package marker and this folder's index. It is emphatically not
a convenience-import hub: no eager submodule imports, no import-time file
access, no logging configuration, no lazy `__getattr__` shim, and no path or
version constants - `acas_posting/__init__.py` owns those, and one source of
truth is enough. Not one import statement appears below, and that is the point.
Agent Action Plan section 0.4.3 makes a promise this file must not break,
verbatim:

    "the arithmetic test suite imports only `cobol` and `records` and touches
    no database, so it runs anywhere."

`field` reaches the generated data dictionary through
`acas_posting.dictionary.loader`, whose lookup is lazily cached and does no
work at import time. Eagerly importing `field` here would add an import edge
running from the bare package name to the dictionary layer, and a later change
on either side of that edge could turn `import acas_posting.cobol` into a file
read. `__all__` at the foot of this module therefore records the inventory as
data instead, so that `import acas_posting.cobol` stays free of I/O and cannot
fail for an environmental reason.

MODULE INVENTORY  (Agent Action Plan sections 0.3.1 and 0.4.1.4; rule R-5)
=========================================================================
The folder is closed at eight files and has no subfolder. Each entry gives the
module, its role, and the frozen source it is derived from; the frozen COBOL is
read as specification only, never modified (see THE FREEZE below).

    __init__.py         This file: package marker and folder index. Derived
                        directly from Agent Action Plan sections 0.3.1 and
                        0.4.1.4; it has no COBOL source of its own.

    picture.py          PIC clause parser, producing field descriptors. From
                        the in-scope picture clauses of `copybooks/*.cob`.

    field.py            The FieldDescriptor value object - digits, scale,
                        signedness, usage and sign position. From
                        `data_dictionary/acas_posting_dictionary.json`, itself
                        generated from the copybook picture clause, the bridge
                        host-variable declaration and the CREATE TABLE column.

    usage.py            The six numeric storage classes: DISPLAY, COMP, COMP-3,
                        DISPLAY with SIGN LEADING, and the BINARY-CHAR /
                        BINARY-SHORT / BINARY-LONG family. From
                        `copybooks/wssl.cob` (signed `binary-long` statistics
                        at L46-L52 sitting beside `comp-3` money at L54-L55),
                        `copybooks/wspost-irs.cob` (`sign leading`, L21 and
                        L25), `copybooks/irswspost.cob` (`sign is leading`, L14
                        and L19), `copybooks/wspost.cob`,
                        `copybooks/wsbatch.cob` and `copybooks/wssystem.cob`.

    arithmetic.py       ADD, SUBTRACT, MULTIPLY, DIVIDE and COMPUTE with COBOL
                        store semantics. From the arithmetic census in Agent
                        Action Plan section 0.6.1: `general/gl051.cbl`,
                        `general/gl072.cbl`, `general/gl080.cbl`,
                        `irs/irs030.cbl`, `sales/sl060.cbl`,
                        `sales/sl100.cbl`, `purchase/pl060.cbl` and
                        `purchase/pl100.cbl`.

    move.py             MOVE between unlike pictures: receiving-field
                        truncation, space padding and justification. From the
                        in-scope MOVE statements of `general/gl070.cbl`,
                        `general/gl072.cbl`, `sales/sl060.cbl` and
                        `irs/irs030.cbl`.

    condition_names.py  88-level condition-name predicates - Status-Open,
                        Waiting, GL-Batch, IRS-Used and their siblings. From
                        `copybooks/wsfnctn.cob` (the function-code and
                        access-type vocabulary at L88-L118),
                        `copybooks/wsbatch.cob` (the batch and cleared status
                        names) and `copybooks/wssystem.cob` (the IRS fan-out
                        switch at L179-L181).

    sortverb.py         SORT with COBOL key semantics and guaranteed
                        stability. From `general/gl071.cbl`, whose single SORT
                        orders the work file on four ascending keys - batch,
                        account, profit centre, posting - and which contains no
                        arithmetic at all. Stability is a correctness
                        requirement, not a nicety: `general/gl072.cbl` locates
                        the nominal-ledger row for a posting with a sequential
                        read-next - `GL-Nominal-Read-Next` at L408, inside the
                        block the Agent Action Plan cites as L410-L412 - rather
                        than an indexed read, so it finds the right account
                        only because that ordering held.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
A module in this package MAY import `acas_posting.dictionary.loader` and the
`acas_posting.dictionary` package's public enums and dataclasses, plus the
standard library - and nothing else. It MUST NOT import `acas_posting.records`,
`acas_posting.dal`, `acas_posting.programs`, `acas_posting.cli`,
`acas_posting.clock`, `acas_posting.dates`, `acas_posting.workfiles`, or the
sibling compiled-oracle tree. No third-party import is permitted anywhere in
this folder.

Consumers, listed for orientation only - never import back toward them:

    acas_posting.records.*   imports `acas_posting.cobol.field`
    acas_posting.programs.*  imports `acas_posting.cobol.arithmetic`,
                             `acas_posting.cobol.move` and
                             `acas_posting.cobol.condition_names`
    acas_posting.workfiles   imports `acas_posting.cobol.sortverb`
    tests/arithmetic/*       imports `acas_posting.cobol` and
                             `acas_posting.records`

NUMERIC POLICY  (rule R-2: zero binary floating point)
======================================================
No accounting value may pass through a binary floating-point type at any
point: not in computation, not in storage, not in transport. Throughout this
package and everything it serves, DISPLAY, COMP and COMP-3 money and quantity
values are `decimal.Decimal` carrying the digits and scale of the field that
receives them; BINARY-CHAR, BINARY-SHORT and BINARY-LONG values are native
Python `int`, so their truncation on divide is integer truncation exactly as
the compiled program's is; `float` and `complex` never appear; and `pandas`
and `numpy` are prohibited outright, an exclusion the Agent Action Plan calls
absolute and which extends even to comparing table dumps.

TRUNCATION IS THE DEFAULT; ROUNDING IS THE ANNOTATED EXCEPTION
==============================================================
COBOL truncates toward zero when it stores an arithmetic result unless the
statement is written with `ROUNDED`. So `arithmetic` truncates by default
(`decimal.ROUND_DOWN`) and rounds half-away-from-zero
(`decimal.ROUND_HALF_UP`) only where a `ROUNDED` site is being reproduced.
There are exactly five such sites in the entire in-scope cycle:

    general/gl051.cbl:L791   VAT computed from the net amount
    general/gl051.cbl:L796   VAT computed back out of a VAT-inclusive gross
    general/gl080.cbl:L328   the cycle-to-period divide
    irs/irs030.cbl:L1551     VAT computed from the net amount
    irs/irs030.cbl:L1562     VAT computed back out of a VAT-inclusive gross

Every other store truncates. Agent Action Plan section 0.1.1, verbatim:
"Getting this backwards would corrupt essentially every posted figure, so
truncation is the default and rounding is the annotated exception."

THIS PACKAGE MUST NOT NORMALISE ANYTHING  (rule R-4)
====================================================
Defects in the compiled behaviour are part of the specification. Agent Action
Plan section 0.8.2, preserved verbatim from the user's own requirements: "There
is no test suite: compiled COBOL execution is the behavioral specification,
defects included. A defect reproduced is correct; a defect fixed is a failure."

The primitives published here must therefore be general enough for a caller to
express divergent legacy idioms exactly as they stand, and must never smooth
them into one shape. The standing example is the moving average, which three
in-scope programs implement three mutually incompatible ways:

    sales/sl060.cbl:L819  ba000-Sales-Comp: a two-part guard on the activity
                          counter and the average, an ELSE that zeroes the
                          accumulator, the counter incremented BEFORE the
                          divide, and `DIVIDE ... INTO ... GIVING`.
    sales/sl060.cbl:L835  ba000-Credit-Comp: the same two-part guard, but NO
                          counter increment at all, plus an extra
                          `work-2 not = zero` guard wrapping both the add and
                          the divide - which silently drops a customer's first
                          credit note.
    sales/sl100.cbl:L506  compute-sales-pay: a SINGLE-condition guard with no
                          ELSE, the counter incremented AFTER the add, and
                          `DIVIDE ... BY ... GIVING` - the reversed operand
                          order.

Do not publish a `moving_average()` helper, here or anywhere else. Agent Action
Plan section 0.6.1, verbatim: "Normalising them into one helper would be the
single easiest way to fail this migration." The same discipline governs the
double truncation those idioms depend on: `sales/sl060.cbl:L206` declares the
accumulator with zero decimal places while the value added into it at
`sales/sl060.cbl:L826` carries two, and the average it divides into at
`sales/sl060.cbl:L827` is a `binary-long` (`copybooks/wssl.cob:L49`), so pence
are discarded once on accumulation and the remainder is discarded again on the
divide. Both losses are reproduced by modelling both field widths exactly.

NO COBOL AT RUNTIME  (rule R-1)
===============================
COBOL is the specification for this migration, not a runtime dependency of the
result: the shipped package must run on a host with no COBOL compiler and no
COBOL runtime present. Every construct in the inventory above is reimplemented
natively here rather than delegated, so this package never launches a process,
never loads a foreign library, and never reaches the sibling compiled-oracle
tree - which only the scenario and determinism suites drive, out of process, as
a comparison oracle.

SEQUENTIAL AND SIDE-EFFECT FREE  (rule R-3)
===========================================
The migration adds no validation, no fields and no schema change, and
introduces no concurrency. Nothing here starts a thread, an event loop or a
process pool; execution is strictly sequential, matching the single-threaded
COBOL. Importing this package has no observable effect beyond binding the name
below.

DETERMINISM  (rule R-6)
=======================
Compiled behaviour is the tie-breaker for every semantic question, and two runs
of one scenario under the same pinned clock must produce byte-identical output;
so no module here reads a clock, draws on an entropy source, consults the
process environment, or iterates a `set` or `dict` in a way a caller can
observe, and every `decimal` context is constructed explicitly rather than
inherited from - or written back into - the interpreter's ambient global
context.

THE FREEZE
==========
Nothing in this package may cause a diff to `common/`, `copybooks/`,
`general/`, `sales/`, `purchase/`, `irs/`, `stock/` or `mysql/ACASDB.sql`.
Those trees are read as specification and are never modified, reformatted,
commented, moved or built from here.

FURTHER READING
===============
    docs/migration/traceability.md           program-to-module,
                                             paragraph-to-function and
                                             field-to-dictionary-entry mappings
    docs/migration/anomaly-log.md            the register of legacy defects
                                             this migration reproduces
    docs/migration/ambiguity-resolutions.md  each semantic question and the
                                             compiled-behaviour arbitration
                                             that settled it
"""

# The submodule inventory, in the order Agent Action Plan section 0.3.1 lists
# them. Declaring the names as data hands a reader - and any tooling - the
# inventory without this module importing a thing: a plain
# `import acas_posting.cobol` binds none of these submodules, which is what
# keeps the package cheap and I/O-free to import. A tuple, not a list and not a
# set, so the inventory cannot be reordered, extended or mutated in place.
#
# THE ORDER IS DELIBERATE AND MUST NOT BE ALPHABETISED. It is the layer order
# of the semantics runtime - a picture clause yields a field descriptor, which
# carries a usage, which the arithmetic and MOVE rules store through, after
# which come the condition-name predicates and the SORT ordering - and it is
# the order the Agent Action Plan tree, its transformation table in section
# 0.4.1.4, the MODULE INVENTORY above and docs/migration/traceability.md all
# use. Sorting these seven names would break that one-to-one correspondence
# for no behavioural gain, so a linter suggesting it is to be declined.
__all__: tuple[str, ...] = (
    "picture",
    "field",
    "usage",
    "arithmetic",
    "move",
    "condition_names",
    "sortverb",
)
