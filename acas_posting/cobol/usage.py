r"""The six COBOL numeric storage classes, modelled as storage behaviour.

This module answers three questions about a COBOL data item and nothing else:
how many bytes it occupies, what values it can hold, and what happens to a
value on the way into it. It is the storage layer of the semantics runtime -
`picture.py` reads a PICTURE clause into components, `field.py` composes those
components into a descriptor, and this module says what the components MEAN in
storage terms. Accounting behaviour lives in `acas_posting.programs`; there is
none here, and there must never be: no account number, no VAT rate, no ledger
balance and no batch status appears below.

It is deliberately NOT a name vocabulary. The vocabulary already exists in
`acas_posting.dictionary.model`, whose `Usage` and `SignPosition` enumerations
mirror the generated artifact member for member, so every public entry point
below is keyed by those members instead of re-declaring them. Two competing
definitions of one vocabulary is precisely the divergence rule R-4 exists to
stop. A caller holding raw text out of the dictionary rather than an imported
member is not forced to import the enumeration either: every entry point takes
the member OR its recorded string.

SIX CLASSES, NEVER COLLAPSED
============================
Agent Action Plan section 0.6.1, verbatim:

    "Six numeric storage classes must be modelled, because collapsing any of
    them changes stored values."

The six, with an exemplar apiece:

    1. DISPLAY, zoned decimal, sign overpunched on the LAST digit when the
       picture is signed and no SIGN clause is written - `pic s9(8)v99`
       [copybooks/wspost.cob:L23], and unsigned as `pic 9(5)`
       [copybooks/wspost.cob:L13].

    2. DISPLAY with a LEADING sign, the easily-missed form: the same zoned
       decimal with the sign overpunched on the FIRST digit -
       `pic s9(7)v99   sign leading` [copybooks/wspost-irs.cob:L21] and
       `pic s9(7)v99  sign is leading` [copybooks/irswspost.cob:L14].

    3. COMP, binary bounded by the digit count the picture declares, and it
       MAY carry a scale - `pic 99v99          comp` [copybooks/wssl.cob:L42],
       `pic 9(5)   comp` [copybooks/wsfnctn.cob:L24].

    4. COMP-3, packed decimal, two digits to the byte plus a low-order sign
       nibble - `pic s9(8)v99   comp-3` [copybooks/wsledger.cob:L28].

    5. The BINARY-CHAR / BINARY-SHORT / BINARY-LONG family: true 8-, 16- and
       32-bit integers, signed unless UNSIGNED is written, and frequently
       carrying NO PICTURE AT ALL - [copybooks/wssl.cob:L43],
       [copybooks/wssl.cob:L45] and the four picture-less batch date stamps at
       [copybooks/wsbatch.cob:L36-L39].

    6. COMP-5, native binary, carried for completeness of the vocabulary
       because the generated bridges declare it - `01 subscripts usage comp-5`
       [common/glpostingMT.scb:L256] - while no in-scope copybook field uses
       it.

Two non-numeric cases ride along because a caller walking a record meets them:
ALPHANUMERIC, `pic x(32)` [copybooks/wspost.cob:L24], and GROUP, an item with
subordinates and no picture of its own, whose byte length is the sum of its
children's and therefore not this module's to state.

THE CLOSED SET, AND THE METHOD THAT MEASURED IT
===============================================
The point of a census is that the set is CLOSED: anything outside it is
speculative surface area, and speculative surface area is where behaviour
drift hides. Counted over the 187 files matching `copybooks/*.cob`, as raw
token occurrences and again with every `*>` comment stripped, so that a reader
can tell a declaration from a remark about one:

    token              raw   code-only
    comp-3             182     177
    bare comp          214     144      (`comp` not followed by `-`)
    binary-long        166     128
    binary-short        31      30
    binary-char         84      59
    sign leading         4       4
    sign is leading      2       2
    occurs             107      99
    redefines           60      53
    unsigned            31      20

Two notes on that table, because a figure without its method invites a later
disagreement. First, the "bare comp" line counts only the standalone usage
token: all `\\bcomp\\b` matches number 413, but 182 of those are the `comp` of
`comp-3` and 17 more belong to identifiers such as `comp-head` and
`comp-time`, which are names rather than usage clauses. Second, the raw and
code-only columns differ because the maintainer annotates declarations with
the storage he might have used instead - see THE DECLARATION WINS below - and
those annotations are evidence, not declarations.

ZERO occurrences in `copybooks/*.cob`, therefore NOT implemented here:
`binary-double`, `comp-5` as a copybook field, `sign trailing`, `separate`,
`justified`, `blank when zero`, `PIC A`, a trailing `V` with no following `9`,
and `P` scaling. `binary-double` does occur eight times in the tree, all of
them in bridge working storage that no in-scope record layout includes -
`binary-double unsigned` [copybooks/mysql-variables.cpy:L73] - and the `Usage`
vocabulary has no member for it, so an attempt to use one is reported as the
programmer error it is rather than guessed at.

The generated dictionary corroborates the closed set from the other end.
Across its 1001 copybook views the usage counts are ALPHANUMERIC 386, DISPLAY
202, GROUP 134, COMP-3 114, BINARY-LONG 69, BINARY-CHAR 30, BINARY-SHORT 20
and COMP 46 - no COMP-5 and no POINTER among them - and the sign positions
are NONE 767, IMPLICIT_BINARY 228, LEADING_INCLUDED 4 and TRAILING_INCLUDED
2, with ZERO of either SEPARATE form. The SEPARATE branches below are
therefore written for completeness and are unexercised by this migration, and
they are commented as such where they appear.

WHERE THE BYTE WIDTHS COME FROM
===============================
The width rules are not taken on trust from a manual. Each one is confirmed by
reconstructing a whole record from its fields and comparing the total against
the record length the maintainer himself declares, which is the one number in
the frozen source that can falsify all of the rules at once. With DISPLAY at
one byte per digit, COMP at the size policy below, BINARY-SHORT at two bytes,
BINARY-LONG at four and COMP-3 at `ceil((digits + 1) / 2)`:

    copybooks/wssl.cob      300 bytes, matching "rec size 300 bytes"
                            [copybooks/wssl.cob:L7]. This is the decisive one:
                            the record mixes DISPLAY, a scaled COMP
                            [copybooks/wssl.cob:L42], BINARY-SHORT
                            [copybooks/wssl.cob:L43-L44], nine BINARY-LONG
                            [copybooks/wssl.cob:L45-L53] and eight COMP-3
                            [copybooks/wssl.cob:L54-L63], so every rule is
                            exercised at once and any one of them being wrong
                            moves the total.

    copybooks/wsledger.cob  126 bytes, matching "Resized to 126 bytes"
                            [copybooks/wsledger.cob:L10].

    copybooks/wssys4.cob    1024 bytes - twenty COMP-3 items at six bytes plus
                            a 904-byte filler - matching "Record size 1024
                            bytes" [copybooks/wssys4.cob:L6].

    copybooks/wsbatch.cob   96 bytes, matching the maintainer's own count at
                            [copybooks/wsbatch.cob:L8], where the header
                            records the contradiction rather than settling it:
                            "98 bytes 20/12/11 (no, dont understand as I count
                            96) but function length (Batch-record) says 98?".

GROUP-LEVEL USAGE IS INHERITED - THE HIGHEST-RISK DETAIL IN THE MODEL
=====================================================================
This module is handed the usage of an item as the dictionary records it, and
does not re-derive it; deriving usage is the generator's job. The warning
belongs here anyway, because a reader who assumes a storage class can be read
off a PICTURE line will mis-type whole records.

COBOL lets a GROUP declare usage that every subordinate item without one
inherits. `03  Amounts                         comp-3.`
[copybooks/wsbatch.cob:L40] governs the four batch amount fields at
[copybooks/wsbatch.cob:L41-L44], whose own lines read only
`pic 9(9)v99` - eleven digits, UNSIGNED, six packed bytes each. The two
period-total groups [copybooks/wssys4.cob:L9] and
[copybooks/wssys4.cob:L20] do the same for twenty more at
[copybooks/wssys4.cob:L10-L19] and [copybooks/wssys4.cob:L21-L30]. That is 24
fields in the three groups this module's own sources declare, and 85 distinct
copybook fields once the whole generated dictionary is counted. COMP inherits
the same way: `05  Vat-Rates                    comp.`
[copybooks/wssystem.cob:L55] governs five `pic 99v99` items at
[copybooks/wssystem.cob:L56-L60], and the item that redefines the group
restates the usage on its own line [copybooks/wssystem.cob:L61].

Read usage from the picture line alone and every batch total and every period
total becomes zoned decimal - so every stored value would be wrong.

One consequence deserves stating because it constrains callers rather than
this module: the four batch amounts are UNSIGNED packed decimal, and
`add      actual-vat   to  actual-gross.` [general/gl051.cbl:L1109] adds into
one of them, so a negative intermediate has no representation at that field at
all.

THE DECLARATION WINS OVER THE MAINTAINER'S COMMENT  (rule R-4)
==============================================================
Three declarations in the sources sit beside a comment that describes
something else:

    03  Sales-Late-Min     binary-short. *> 9999 comp
                                        [copybooks/wssl.cob:L43]
    03  Sales-Limit        binary-long. *> 9(8) comp
                                        [copybooks/wssl.cob:L45]
    05  Page-Lines      binary-char  unsigned. *> 999. Portrait / default
                                        [copybooks/wssystem.cob:L65]

BINARY-SHORT is a 16-bit signed integer, not a four-digit one. BINARY-LONG is
a 32-bit signed integer, not an eight-digit one. BINARY-CHAR UNSIGNED is an
8-bit unsigned integer whose maximum is 255, not 999. This module models the
declarations - 16-bit, 32-bit and 8-bit-unsigned - records the comments here,
and changes nothing about either. A defect reproduced is correct; a defect
fixed is a failure.

The same maintainer writes the width correctly elsewhere, which is what makes
these three comments evidence of a slip rather than of a different intent:
`05  PL-Next-Rec     binary-short unsigned.            *> 2 bytes 0 - 65k`
[copybooks/wssystem.cob:L210] states the hardware width outright. Others
repeat the slip - `*> 9(4) comp` beside a BINARY-CHAR
[copybooks/wssystem.cob:L199], `*> 9999 comp.` beside two more
[copybooks/wssystem.cob:L306-L307] - and are equally left alone.

The two spellings of the leading-sign clause are treated the same way. The
copybooks write `sign leading` [copybooks/wspost-irs.cob:L21],
[copybooks/wspost-irs.cob:L25] and `sign is leading`
[copybooks/irswspost.cob:L14], [copybooks/irswspost.cob:L18]; both are
recognised verbatim and neither is rewritten into the other. `SIGN_LEADING_
SPELLINGS` publishes exactly those two texts, in that order, and matching is
case-insensitive with runs of whitespace collapsed because the source writes
the clause after a run of spaces. Nothing in this module alters the text a
caller passes: the dictionary keeps it verbatim in `sign_clause_text`, and
that record is the point.

Note on one locator: Agent Action Plan section 0.4.1.3 cites
`[copybooks/irswspost.cob:L19]` for the second leading-sign field. L19 is the
closing `*>` of that copybook; the field is at L18, and L18 is what this
module cites.

NUMERIC POLICY  (rule R-2: zero binary floating point)
======================================================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. In this module
that resolves to four concrete commitments:

    * Scaled and packed and zoned values are `decimal.Decimal`, carrying the
      scale of the field that receives them.
    * The binary integer family is native Python `int`. This is load-bearing
      rather than tidy: Agent Action Plan section 0.6.1, verbatim - "their
      truncation on divide is integer truncation, which is exactly what makes
      the moving-average defect reproducible" - and the field it is talking
      about is `Sales-Average      binary-long` [copybooks/wssl.cob:L49].
    * Text is `str` and raw storage is `bytes`. Nothing else is returned.
    * Every `decimal` operation runs inside `decimal.localcontext()` with a
      context this module constructs, never the ambient global one, so a
      result cannot depend on what a caller did earlier. No binary
      floating-point type, and no library that computes in one, appears
      anywhere below.

`truncate_toward_zero` exists for the same reason. COBOL integer division
truncates toward zero, while Python's `//` floors toward negative infinity;
they disagree on every negative dividend, and a caller reaching for `//` would
silently move posted figures.

NO ADDED VALIDATION, AND SILENCE IS A FEATURE  (rule R-3)
=========================================================
A COBOL store that overflows its receiving field discards high-order digits
and carries on. There is no error path to reproduce: `ON SIZE ERROR` occurs
zero times across the twelve in-scope programs, and so does `REMAINDER`. So
`coerce` discards high-order digits silently. It does not raise, does not
clamp to the maximum, does not widen the field and does not warn.

Every `raise` below reports a PROGRAMMER error - an unknown usage token, a
negative digit count, a component the class requires and the caller omitted, a
non-elementary item asked for an elementary answer, or a buffer whose length
is not the field's. None reports a DATA condition. Decoding is tolerant for
the same reason: a zoned field is read a nibble at a time, so a space-filled
field - the state COBOL leaves an uninitialised display item in - reads as
zero instead of failing.

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
This module may import the standard library and the `acas_posting.dictionary`
public surface, and nothing else. It must not import `records`, `dal`,
`programs`, `cli`, `clock`, `dates`, `workfiles` or the compiled-oracle tree,
and no third-party package belongs here.

It must not import the sibling field-descriptor module either. That module
imports THIS one, and the edge runs one way only. Which is why every signature
below takes primitive components - digits, scale, character length, signedness
and sign position - and never a descriptor object.

OPEN QUESTIONS, RECORDED RATHER THAN SETTLED  (rule R-6)
========================================================
Where compiled behaviour is the tie-breaker and it has not yet been measured,
the question is marked, the provisional behaviour is implemented behind a
named constant so one edit re-targets it, and the marker says so at the site.
Three land in this module:

    Q-5.1  The GnuCOBOL default `binary-size` and `binary-truncate` policy
           that governs COMP storage width and store truncation. See
           `DEFAULT_BINARY_SIZE_THRESHOLDS` and `BINARY_TRUNCATE`.
    Q-5.2  The byte length of a leading-sign display field, where the frozen
           evidence does not reconcile. See `byte_length`.
    Q-5.3  The exact zoned overpunch byte values. See `ZONED_POSITIVE_ZONE`
           and `ZONED_NEGATIVE_ZONE`.

A fourth question already carries a number in the register, `Q-3`, and is
cross-referenced rather than renumbered: a signed copybook value narrowed into
an unsigned bridge host variable loses its sign before any SQL runs
[copybooks/wssl.cob:L46-L52], and what is stored in that case can only be
measured. `coerce` implements the COBOL-level unsigned store; the bridge
conversion belongs to the data-access layer, not here.

The three labels Q-5.1, Q-5.2 and Q-5.3 are this module's own, taken from the
brief that specified it, and sit deliberately outside the integer sequence -
`Q-3`, `Q-4` and `Q-6` are already in use in
data_dictionary/acas_posting_dictionary.json - so that neither numbering
disturbs the other. docs/migration/ambiguity-resolutions.md carries the
register entry, the experiment and its outcome.

THE FREEZE
==========
The COBOL, the generated bridges and the schema are read as specification and
are never modified, reformatted, commented, moved or built from here. Nothing
in this module causes a diff to `common/`, `copybooks/`, `general/`, `sales/`,
`purchase/`, `irs/`, `stock/` or `mysql/ACASDB.sql`.

FURTHER READING
===============
    acas_posting/dictionary/model.py         the `Usage` and `SignPosition`
                                             vocabularies this module is keyed
                                             by
    data_dictionary/acas_posting_dictionary.json
                                             the recorded metadata of every
                                             in-scope field
    docs/migration/traceability.md           program-to-module,
                                             paragraph-to-function and
                                             field-to-dictionary-entry maps
    docs/migration/anomaly-log.md            the legacy defects reproduced
    docs/migration/ambiguity-resolutions.md  each open question and its
                                             compiled-behaviour arbitration
"""

from __future__ import annotations

import decimal
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from acas_posting.dictionary.model import CobolPythonStorage, SignPosition, Usage

# The export surface, sorted so that it is stable and reviewable. Sorting the
# EXPORT LIST is not the same thing as sorting the DECLARATIONS: the
# declarations below run in layering order - byte constants, then the usage
# families, then the predicates, then the storage answers, then the store step,
# then the byte-level codec - because that is the order in which one builds on
# the last. Rule R-6 asks only that the order be fixed, and both of these are.
__all__: Final[tuple[str, ...]] = (
    "ALPHANUMERIC_USAGES",
    "BINARY_FAMILY_USAGES",
    "BINARY_TRUNCATE",
    "BINARY_WIDTH_BYTES",
    "COMPUTATIONAL_BINARY_USAGES",
    "DEFAULT_BINARY_SIZE_THRESHOLDS",
    "GROUP_USAGES",
    "NUMERIC_USAGES",
    "PACKED_DECIMAL_USAGES",
    "PACKED_SIGN_NEGATIVE",
    "PACKED_SIGN_POSITIVE",
    "PACKED_SIGN_UNSIGNED",
    "SEPARATE_SIGN_BYTE_NEGATIVE",
    "SEPARATE_SIGN_BYTE_POSITIVE",
    "SIGN_LEADING_SPELLINGS",
    "ZONED_DECIMAL_USAGES",
    "ZONED_NEGATIVE_BASE",
    "ZONED_NEGATIVE_ZONE",
    "ZONED_POSITIVE_BASE",
    "ZONED_POSITIVE_ZONE",
    "byte_length",
    "coerce",
    "decode",
    "encode",
    "is_alphanumeric",
    "is_binary_family",
    "is_group",
    "is_numeric",
    "is_packed",
    "is_zoned_display",
    "python_storage_for",
    "truncate_toward_zero",
    "value_domain",
)


# =============================================================================
#  THE BINARY FAMILY'S TRUE HARDWARE WIDTHS  (rule R-4: the declaration wins)
# =============================================================================

# 8, 16 and 32 bits. NOT four digits, NOT eight digits, and NOT three digits,
# whatever the comment beside the declaration says:
#
#     03  Sales-Late-Min     binary-short. *> 9999 comp
#                                         [copybooks/wssl.cob:L43]
#     03  Sales-Limit        binary-long. *> 9(8) comp
#                                         [copybooks/wssl.cob:L45]
#     05  Page-Lines      binary-char  unsigned. *> 999. ...
#                                         [copybooks/wssystem.cob:L65]
#
# The comments are recorded, in the module docstring and here, and left alone.
# The widths below are the declarations, and they are what the four record
# reconciliations in the docstring confirm - two bytes per BINARY-SHORT and
# four per BINARY-LONG is what makes [copybooks/wssl.cob] total the 300 bytes
# its own header declares at [copybooks/wssl.cob:L7], and four bytes per
# BINARY-LONG is what makes [copybooks/wsbatch.cob] total the 96 the
# maintainer counts at [copybooks/wsbatch.cob:L8].
#
# A read-only proxy over a dict built in width order, so that a caller can
# neither mutate the table nor observe an order this module did not choose
# (rule R-6). BINARY-DOUBLE is absent because the vocabulary has no member for
# it and no in-scope copybook field declares one.
BINARY_WIDTH_BYTES: Final[Mapping[Usage, int]] = MappingProxyType(
    {
        Usage.BINARY_CHAR: 1,
        Usage.BINARY_SHORT: 2,
        Usage.BINARY_LONG: 4,
    }
)


# =============================================================================
#  THE TWO LEADING-SIGN SPELLINGS, PRESERVED AS WRITTEN  (rule R-4)
# =============================================================================

# Both spellings are live in the frozen sources and neither is rewritten into
# the other:
#
#     pic s9(7)v99   sign leading      [copybooks/wspost-irs.cob:L21]
#                                      [copybooks/wspost-irs.cob:L25]
#     pic s9(7)v99  sign is leading    [copybooks/irswspost.cob:L14]
#                                      [copybooks/irswspost.cob:L18]
#
# The tuple order is source order: the two-word spelling first, because
# `wspost-irs.cob` is the copybook the Sales and Purchase posting programs
# write through, then the three-word spelling of the internal IRS record.
#
# NEITHER carries SEPARATE. The token `separate` occurs zero times in the whole
# of `copybooks/*.cob`, and so does `sign trailing`, so `SIGN LEADING` here
# always means the ISO default: overpunched on the first digit, costing no
# extra byte. See `byte_length` for the Q-5.2 marker on that width.
#
# Matching is case-insensitive with runs of whitespace collapsed, because the
# source writes the clause after a run of spaces, so the recognised set is
# exactly 'sign leading' and 'sign is leading' and nothing besides. Nothing
# here alters the text a caller passes in - the dictionary keeps it verbatim in
# `sign_clause_text` and that record is the whole point.
SIGN_LEADING_SPELLINGS: Final[tuple[str, ...]] = ("sign leading", "sign is leading")


# =============================================================================
#  PACKED-DECIMAL SIGN NIBBLES  (COMP-3)
# =============================================================================

# A COMP-3 item stores one digit per nibble and spends its LAST nibble on the
# sign - which an unsigned item spends too, so `pic 9(9)v99` inherited from
# `03  Amounts                         comp-3.` [copybooks/wsbatch.cob:L40] is
# eleven digits in six bytes, sign nibble included and unsigned.
PACKED_SIGN_POSITIVE: Final[int] = 0xC
PACKED_SIGN_NEGATIVE: Final[int] = 0xD
PACKED_SIGN_UNSIGNED: Final[int] = 0xF


# =============================================================================
#  ZONED-DECIMAL BYTE VALUES  (Q-5.3: to be measured against the oracle)
# =============================================================================

# ---------------------------------------------------------------------------
# Q-5.3  OPEN QUESTION - the zoned overpunch byte values.
#
# A zoned DISPLAY digit is one byte whose low nibble is the digit. The ZONE -
# the high nibble - is where the sign of a signed item lives, overpunched onto
# the sign-carrying digit. Which zone value marks a negative is a property of
# the compiler and the platform, not of the source: GnuCOBOL 3.2 is the target
# [common/comp-common.sh:L9], the compile scripts select no dialect and set no
# arithmetic directive, and the negative zone therefore has to be MEASURED
# against the compiled program rather than assumed.
#
# PROVISIONAL, implemented below: the ASCII high-nibble convention - 0x30 for a
# positive digit, so '0' through '9', and 0x70 for a negative one, so 'p'
# through 'y'. The two zone nibbles are the only edit needed to re-target
# every table and every branch that depends on them, and `decode(encode(v))`
# returns `v` whichever convention the oracle confirms, because decoding reads
# the digit from the low nibble and tests the zone against these same
# constants.
#
# docs/migration/ambiguity-resolutions.md carries the register entry.
# ---------------------------------------------------------------------------
ZONED_POSITIVE_ZONE: Final[int] = 0x30
ZONED_NEGATIVE_ZONE: Final[int] = 0x70

# Digit-indexed byte tables, built from the two zone nibbles in one fixed pass
# so that they cannot drift apart from them.
ZONED_POSITIVE_BASE: Final[tuple[int, ...]] = tuple(
    ZONED_POSITIVE_ZONE | digit for digit in range(10)
)
ZONED_NEGATIVE_BASE: Final[tuple[int, ...]] = tuple(
    ZONED_NEGATIVE_ZONE | digit for digit in range(10)
)

# The sign character of a SEPARATE sign, which is a byte of its own rather than
# an overpunch. Written for completeness of the vocabulary: no in-scope
# copybook field uses either SEPARATE form - the generated dictionary records
# LEADING_SEPARATE and TRAILING_SEPARATE zero times across its 1001 copybook
# views - so every branch keyed by them is unexercised by this migration.
SEPARATE_SIGN_BYTE_POSITIVE: Final[int] = 0x2B
SEPARATE_SIGN_BYTE_NEGATIVE: Final[int] = 0x2D


# =============================================================================
#  COMP STORAGE POLICY  (Q-5.1: to be measured against the oracle)
# =============================================================================

# ---------------------------------------------------------------------------
# Q-5.1  OPEN QUESTION - the compiler's default `binary-size` and
#        `binary-truncate` policy.
#
# A COMP item's width and its behaviour on store are set by compiler
# configuration, not by the source. Agent Action Plan section 0.5.2, verbatim:
# "A census of every compile invocation in the repository finds no `-std=`
# dialect selection, no `>>SET ARITHMETIC` directive in any source, and no
# `binary-truncate` flag anywhere." So the compiler's own defaults govern, the
# compiler is GnuCOBOL 3.2 [common/comp-common.sh:L9], and its defaults are
# what has to be measured.
#
# PROVISIONAL, implemented below:
#   * `binary-size` allocates the smallest whole number of bytes that holds the
#     declared digit count - 1, 2, 4 or 8 bytes for up to 2, 4, 9 or 18
#     digits. Corroborated by the record reconciliations: `pic 99v99  comp`
#     [copybooks/wssl.cob:L42] at two bytes is what makes
#     [copybooks/wssl.cob] total its declared 300.
#   * `binary-truncate` is on, so a store truncates to the DECLARED DIGIT
#     COUNT rather than to the byte capacity. The widest COMP item in scope
#     declares 10 digits, so it occupies 8 bytes and truncates at 10 digits,
#     and the two differ.
#   * Where no digit count exists to truncate to - the BINARY-CHAR /
#     BINARY-SHORT / BINARY-LONG family, whose items carry no picture at all
#     [copybooks/wsbatch.cob:L36-L39] - a store reduces into the hardware
#     domain instead, the way the C type it compiles to does.
#
# Both constants are named so that one edit re-targets every branch that
# consults them. docs/migration/ambiguity-resolutions.md carries the register
# entry.
# ---------------------------------------------------------------------------

# (maximum declared digits, bytes allocated), ascending. A tuple of tuples, so
# the policy is ordered, immutable and iterable without a caller observing an
# order this module did not choose (rule R-6).
DEFAULT_BINARY_SIZE_THRESHOLDS: Final[tuple[tuple[int, int], ...]] = (
    (2, 1),
    (4, 2),
    (9, 4),
    (18, 8),
)

# True reproduces GnuCOBOL's default `binary-truncate: yes`. Set it False and
# a COMP store reduces into its byte capacity instead of its digit count.
BINARY_TRUNCATE: Final[bool] = True


# =============================================================================
#  THE USAGE FAMILIES
#
#  Membership sets, and membership is ALL they are used for. Never iterate one
#  where a caller can observe the order: a frozenset has no order to observe
#  (rule R-6). Anything that must be ordered - the width table, the size
#  policy, the sign spellings - is a tuple or a proxied dict above.
# =============================================================================

# Zoned decimal: declared by the ABSENCE of a usage clause, as every numeric
# field of [copybooks/wspost.cob:L13-L28] is.
ZONED_DECIMAL_USAGES: Final[frozenset[Usage]] = frozenset({Usage.DISPLAY})

# Packed decimal [copybooks/wsledger.cob:L28], [copybooks/wssl.cob:L54-L55].
PACKED_DECIMAL_USAGES: Final[frozenset[Usage]] = frozenset({Usage.COMP_3})

# Binary bounded by a declared digit count [copybooks/wssl.cob:L42],
# [copybooks/wsfnctn.cob:L24]. COMP-5 joins COMP here because it is binary in
# the same sense; it differs in that it is not bounded by the picture, and no
# in-scope copybook field declares one.
COMPUTATIONAL_BINARY_USAGES: Final[frozenset[Usage]] = frozenset(
    {Usage.COMP, Usage.COMP_5}
)

# The native binary family, whose range comes from its width rather than from
# a picture [copybooks/wssl.cob:L43-L53], [copybooks/wsbatch.cob:L36-L39],
# [copybooks/wssystem.cob:L62-L69].
BINARY_FAMILY_USAGES: Final[frozenset[Usage]] = frozenset(
    {Usage.BINARY_CHAR, Usage.BINARY_SHORT, Usage.BINARY_LONG}
)

# `PIC X(n)` [copybooks/wspost.cob:L24], [copybooks/wsledger.cob:L27],
# [copybooks/wsfnctn.cob:L38-L39].
ALPHANUMERIC_USAGES: Final[frozenset[Usage]] = frozenset({Usage.ALPHANUMERIC})

# An item with subordinates and no picture of its own - including one that
# carries the usage its children inherit [copybooks/wsbatch.cob:L40],
# [copybooks/wssys4.cob:L9], [copybooks/wssys4.cob:L20].
GROUP_USAGES: Final[frozenset[Usage]] = frozenset({Usage.GROUP})

# Every usage that holds a number, and therefore has a value domain and a
# store rule. POINTER is not numeric and not elementary storage in any sense
# this migration needs: it appears only as the `TP-` item each generated bridge
# declares beside its host-variable group, which no record layout includes.
NUMERIC_USAGES: Final[frozenset[Usage]] = (
    ZONED_DECIMAL_USAGES
    | PACKED_DECIMAL_USAGES
    | COMPUTATIONAL_BINARY_USAGES
    | BINARY_FAMILY_USAGES
)


# The widest digit count the size policy above covers. Nothing in scope comes
# near it: the widest declared item in the generated dictionary is the eleven
# digits of `pic 9(9)v99` [copybooks/wsbatch.cob:L41-L44].
_MAX_POLICY_DIGITS: Final[int] = DEFAULT_BINARY_SIZE_THRESHOLDS[-1][0]

# The floor on the working precision of the `decimal` contexts constructed
# below. Every context is built here and entered with `decimal.localcontext`,
# never inherited from the interpreter's ambient global context and never
# written back into it, so a stored value cannot depend on what a caller did
# earlier (rule R-6). The working precision is sized from the operand as well,
# so no store can exceed it; this floor only keeps small operands from being
# handled in an absurdly narrow context.
_MINIMUM_WORKING_PRECISION: Final[int] = 40

# COBOL truncates toward zero on store unless the statement says ROUNDED, so
# truncation is the default here and rounding is what a caller asks for. There
# are exactly five ROUNDED sites in the whole in-scope cycle -
# [general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
# [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - and at those the caller
# passes `decimal.ROUND_HALF_UP` instead.
_DEFAULT_STORE_ROUNDING: Final[str] = decimal.ROUND_DOWN


# =============================================================================
#  EITHER A MEMBER OR ITS RECORDED TEXT
#
#  Every public entry point is keyed by the `acas_posting.dictionary.model`
#  vocabularies, and takes either the member or the string the artifact records
#  for it, so that a caller reading raw dictionary JSON is not forced to import
#  the enumeration. Matching is case-insensitive with runs of whitespace
#  collapsed and `_` accepted for `-`, because the artifact spells a usage
#  `COMP-3` while the Python member is `COMP_3` and the copybooks write
#  `comp-3` in lower case.
# =============================================================================


def _normalise_token(text: str) -> str:
    """Fold one vocabulary token to the form the lookup tables are keyed by."""
    return "-".join(text.strip().upper().replace("_", "-").split())


_USAGE_BY_TEXT: Final[Mapping[str, Usage]] = MappingProxyType(
    {_normalise_token(member.value): member for member in Usage}
)

_SIGN_POSITION_BY_TEXT: Final[Mapping[str, SignPosition]] = MappingProxyType(
    {_normalise_token(member.value): member for member in SignPosition}
)


def _usage_of(usage: Usage | str) -> Usage:
    """Return the `Usage` member for a member or its recorded text.

    Raises:
        TypeError: if `usage` is neither a `Usage` member nor a string. A
            PROGRAMMER error: the caller has passed something that is not a
            storage class at all.
        ValueError: if the text names no member of the vocabulary. Also a
            PROGRAMMER error, and the reason `BINARY-DOUBLE` needs no branch of
            its own: the vocabulary has no member for it, so asking is reported
            rather than guessed at. Never a data condition - no value reaches
            this function.

    """
    if isinstance(usage, Usage):
        return usage
    if not isinstance(usage, str):
        raise TypeError(
            "usage must be a Usage member or its recorded text, "
            f"not {type(usage).__name__}"
        )
    member = _USAGE_BY_TEXT.get(_normalise_token(usage))
    if member is None:
        raise ValueError(f"unknown COBOL usage: {usage!r}")
    return member


def _sign_position_of(sign_position: SignPosition | str) -> SignPosition:
    """Return the `SignPosition` member for a member or its recorded text.

    Raises:
        TypeError: if the argument is neither a member nor a string - a
            PROGRAMMER error, as above.
        ValueError: if the text names no member - likewise a PROGRAMMER error.

    """
    if isinstance(sign_position, SignPosition):
        return sign_position
    if not isinstance(sign_position, str):
        raise TypeError(
            "sign_position must be a SignPosition member or its recorded "
            f"text, not {type(sign_position).__name__}"
        )
    member = _SIGN_POSITION_BY_TEXT.get(_normalise_token(sign_position))
    if member is None:
        raise ValueError(f"unknown COBOL sign position: {sign_position!r}")
    return member


def _checked_count(name: str, value: int | None) -> int | None:
    """Pass a digit, scale or character count through, or report a bad one.

    Raises:
        TypeError: if the count is not an integer. A PROGRAMMER error.
        ValueError: if it is negative. Also a PROGRAMMER error - a picture
            clause cannot declare a negative number of digits, so a negative
            count means the caller computed it wrongly, and silently repairing
            it would hide the mistake. This tests the FIELD DESCRIPTION, never
            a value being stored.

    """
    if value is None:
        return None
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int or None, not {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} cannot be negative: {value}")
    return value


def _is_unsigned(*, signed: bool, unsigned: bool) -> bool:
    """Decide signedness from the two flags every entry point accepts.

    Two flags rather than one, because the two callers of this module hold the
    fact in the two different forms the frozen sources present it in. The
    generated dictionary records a `signed` boolean for each view; the copybook
    writes the keyword `UNSIGNED` when it means it, as
    `binary-char  unsigned` does at [copybooks/wssystem.cob:L65] - the one
    unsigned binary item the in-scope posting cycle reads. The four others in
    that copybook, [copybooks/wssystem.cob:L210],
    [copybooks/wssystem.cob:L275], [copybooks/wssystem.cob:L306] and
    [copybooks/wssystem.cob:L307], belong to the Autogen and Stock blocks,
    which the cycle does not reach.

    The rule is stated once here so no branch can read it differently: the item
    is unsigned if `unsigned` is asserted OR `signed` is denied. Passing
    `signed=True, unsigned=True` therefore yields unsigned, the keyword
    winning, and no combination is rejected.
    """
    return unsigned or not signed


# =============================================================================
#  CLASSIFICATION
#
#  Six predicates over the vocabulary, so that a caller can branch on the
#  family without importing the family sets or knowing which member sits in
#  which. They answer questions about a STORAGE CLASS; none of them looks at a
#  value.
# =============================================================================


def is_zoned_display(usage: Usage | str) -> bool:
    """Report whether this is the zoned-decimal class.

    True for `DISPLAY`, which is declared by the ABSENCE of a usage clause:
    every numeric field of [copybooks/wspost.cob:L13-L28] is one, signed at
    [copybooks/wspost.cob:L23] and unsigned at [copybooks/wspost.cob:L13].

    False for `ALPHANUMERIC`, even though COBOL itself classes `PIC X(n)` as
    usage display, because the two behave differently on store: a number is
    truncated at its high-order end and text at its right-hand end.
    """
    return _usage_of(usage) in ZONED_DECIMAL_USAGES


def is_packed(usage: Usage | str) -> bool:
    """Report whether this is the packed-decimal class.

    True for `COMP-3`, whether it was declared on the item
    [copybooks/wsledger.cob:L28] or inherited from a group
    [copybooks/wsbatch.cob:L40], which this module cannot and need not tell
    apart: the dictionary records which at `usage_declared_at`.
    """
    return _usage_of(usage) in PACKED_DECIMAL_USAGES


def is_binary_family(usage: Usage | str) -> bool:
    """Report whether this is the native binary family.

    These are true 8-, 16- and 32-bit integers whose range comes from their
    width rather than from a picture, and which frequently carry no picture at
    all [copybooks/wsbatch.cob:L36-L39]. Their Python carrier is native `int`,
    which is load-bearing: integer truncation on divide is what makes the
    legacy average defect reproducible, and the field at the centre of it is
    `Sales-Average      binary-long` [copybooks/wssl.cob:L49].

    False for `COMP` and `COMP-5`, which are binary too but bounded by a
    declared digit count instead of by their width; `is_numeric` covers both
    families at once.
    """
    return _usage_of(usage) in BINARY_FAMILY_USAGES


def is_alphanumeric(usage: Usage | str) -> bool:
    """Report whether this is text rather than a number.

    Exemplars: `Post-Legend     pic x(32)` [copybooks/wspost.cob:L24],
    `Ledger-Name       pic x(24)` [copybooks/wsledger.cob:L27], and the two
    525-byte path items at [copybooks/wsfnctn.cob:L38-L39].
    """
    return _usage_of(usage) in ALPHANUMERIC_USAGES


def is_group(usage: Usage | str) -> bool:
    """Report whether this is a group item.

    A group's byte length is the sum of its children's, so it is not a fact
    this module can state - `byte_length` reports the request as a programmer
    error rather than inventing an answer. A group may still carry the usage
    its children inherit, which is the highest-risk detail in the storage model
    and is set out in the module docstring: [copybooks/wsbatch.cob:L40],
    [copybooks/wssys4.cob:L9], [copybooks/wssys4.cob:L20],
    [copybooks/wssystem.cob:L55].
    """
    return _usage_of(usage) in GROUP_USAGES


def is_numeric(usage: Usage | str) -> bool:
    """Report whether this class holds a number.

    True for all six numeric classes - zoned `pic s9(8)v99`
    [copybooks/wspost.cob:L23], packed `pic s9(8)v99 comp-3`
    [copybooks/wsledger.cob:L28], `pic 99v99 comp` [copybooks/wssl.cob:L42],
    `COMP-5` [common/glpostingMT.scb:L256], and the three-member binary family
    [copybooks/wssl.cob:L43-L53]. False for `ALPHANUMERIC`
    [copybooks/wspost.cob:L24], for `GROUP` [copybooks/wsbatch.cob:L40], and
    for `POINTER`, which no record layout declares at all.
    """
    return _usage_of(usage) in NUMERIC_USAGES


# =============================================================================
#  THE PYTHON CARRIER  (rule R-2)
# =============================================================================


def python_storage_for(
    usage: Usage | str, scale: int | None = None
) -> CobolPythonStorage:
    """Which Python type carries a value of this class and scale.

    READ THIS BEFORE USING IT. For a RECORD FIELD, the value to use is the one
    the dictionary entry already records at `cobol_python_storage`, generated
    from the frozen sources. This function derives the same answer from the two
    components it depends on, for convenience where no entry is at hand and as
    a cross-check that an entry and the rule agree. It settles nothing, it
    adjudicates nothing between the copybook, the bridge and the column views,
    and it must never be read in place of a recorded value (rule R-4).

    The rule is the one the artifact states at `meta.derivation_rules.
    cobol_python_storage`, applied in the order it is written there: NONE for a
    group item; STR for an alphanumeric item; DECIMAL for a numeric item with a
    non-zero scale; INT for the BINARY-CHAR, BINARY-SHORT, BINARY-LONG and
    COMP-5 family and for any zero-scale integer.

    Scale decides BEFORE family, and the artifact settles that ordering
    empirically rather than by argument: it records INT for all 188 of its
    zero-scale zoned fields and for its 8 zero-scale COMP fields, so a looser
    reading under which a zoned or packed item were exact-decimal whatever its
    scale would contradict the generated artifact on nearly two hundred real
    fields. Where a paraphrase of the rule and the artifact disagree, the
    artifact governs, because it is what the record layer actually carries.

    That last clause is the load-bearing one, and it is why the order matters.
    The sales statistics fields are `binary-long`
    [copybooks/wssl.cob:L46-L52], so they are carried by `int` and their
    truncation on divide is integer truncation - which is exactly what makes
    the legacy average defect reproducible. Money is `decimal.Decimal`
    [copybooks/wsledger.cob:L28], and a zero-scale zoned item such as
    `pic 9(5)` [copybooks/wspost.cob:L13] is an integer, so it is `int` too.

    Args:
        usage: A `Usage` member or its recorded text.
        scale: The number of digits after the implied decimal point, or None
            for an item that has no picture - a group, or a binary-family item
            whose range comes from its width [copybooks/wsbatch.cob:L36-L39].
            None is treated as zero scale, which is what having no fractional
            digits means; it is NOT treated as unknown, because the artifact
            records None for exactly the items that have no fractional part.

    Returns:
        The `CobolPythonStorage` member naming the carrier.

    Raises:
        ValueError: for `POINTER`, which is not record storage in this
            migration - it appears only as the `TP-` item each generated bridge
            declares beside its host-variable group, and no record layout
            includes one. A PROGRAMMER error: no value is involved.

    """
    member = _usage_of(usage)
    scale_count = _checked_count("scale", scale) or 0

    if member in GROUP_USAGES:
        return CobolPythonStorage.NONE
    if member in ALPHANUMERIC_USAGES:
        return CobolPythonStorage.STR
    if member in NUMERIC_USAGES:
        # The order below is the artifact's: scale decides first, so a scaled
        # COMP such as `pic 99v99          comp` [copybooks/wssl.cob:L42] is
        # exact-decimal rather than integer, and only then does the family
        # decide.
        if scale_count > 0:
            return CobolPythonStorage.DECIMAL
        return CobolPythonStorage.INT
    raise ValueError(f"{member.value} is not record storage: no Python carrier")


# =============================================================================
#  BYTE WIDTH
# =============================================================================


def byte_length(
    usage: Usage | str,
    *,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    sign_position: SignPosition | str = SignPosition.NONE,
    unsigned: bool = False,
) -> int:
    """How many bytes an elementary item of this description occupies.

    The width rules, each with the evidence that confirms it:

    ZONED DISPLAY - one byte per digit CHARACTER. The implied decimal point of
    a `V` occupies no byte, which is why `scale` does not enter the arithmetic
    at all: `pic s9(8)v99` [copybooks/wspost.cob:L23] is ten digits and ten
    bytes, and the maintainer's own cumulative offsets agree, reaching 86
    before the second such field [copybooks/wspost.cob:L27] and 96 after it
    [copybooks/wspost.cob:L28]. A signed item with no SIGN clause overpunches
    its LAST digit, so signedness costs nothing either.

    ZONED DISPLAY WITH A LEADING SIGN - the same width, the sign overpunched on
    the FIRST digit instead. See the Q-5.2 marker below.

    THE SEPARATE SIGN FORMS - one byte more, for a sign character of its own.
    Written for completeness and unexercised by this migration: no in-scope
    copybook field declares either, and the token `separate` occurs zero times
    in the whole of `copybooks/*.cob`.

    PACKED DECIMAL - `ceil((digits + 1) / 2)`: one nibble per digit plus a
    low-order sign nibble, which an unsigned item spends too. So
    `pic s9(8)v99   comp-3` [copybooks/wsledger.cob:L28] is ten digits in six
    bytes, and the unsigned eleven-digit `pic 9(9)v99` inherited from
    `03  Amounts                         comp-3.`
    [copybooks/wsbatch.cob:L40-L44] is six bytes as well.

    COMP AND COMP-5 - the smallest whole number of bytes that holds the
    declared digit count, by `DEFAULT_BINARY_SIZE_THRESHOLDS`. So
    `pic 99v99          comp` [copybooks/wssl.cob:L42] is two bytes and
    `pic 9(5)   comp` [copybooks/wsfnctn.cob:L24] is four. Marked Q-5.1 at the
    constant.

    THE BINARY FAMILY - its width, from `BINARY_WIDTH_BYTES`, and NOT from a
    picture: these items commonly have none [copybooks/wsbatch.cob:L36-L39],
    and the generated dictionary records `digits` as null for every one of
    them, on the ground that inventing a digit count would add a fact the
    source does not state. `digits` is accepted and ignored here for that
    reason rather than rejected, so a caller passing a whole descriptor
    through does not have to strip it.

    ALPHANUMERIC - `character_length` bytes [copybooks/wspost.cob:L24].

    Args:
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits, integer plus fractional. Required for a
            zoned, packed, COMP or COMP-5 item; ignored for the binary family.
        scale: Accepted for a uniform signature and deliberately not consulted:
            an implied decimal point occupies no byte.
        character_length: Required for an alphanumeric item.
        sign_position: Where the sign sits. Only the two SEPARATE forms change
            the width.
        unsigned: Accepted for a uniform signature. Signedness never changes a
            width in COBOL: a zoned sign is overpunched, and a packed sign
            nibble is present whether or not the item is signed.

    Returns:
        The byte width.

    Raises:
        ValueError: for a group or a pointer, which have no elementary width of
            their own; for a required component the caller omitted; or for a
            digit count wider than the size policy covers. All PROGRAMMER
            errors - the function is given a field description, never a value.

    """
    member = _usage_of(usage)
    position = _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    _checked_count("scale", scale)
    text_length = _checked_count("character_length", character_length)
    del unsigned  # width never depends on signedness; see the docstring

    if member in GROUP_USAGES:
        # A group's width is the sum of its children's, which this module
        # cannot see. Reporting the request beats inventing an answer.
        raise ValueError(
            "a group item has no width of its own: sum its children's widths"
        )
    if member in ALPHANUMERIC_USAGES:
        if text_length is None:
            raise ValueError("character_length is required for an alphanumeric item")
        return text_length
    if member in BINARY_FAMILY_USAGES:
        return BINARY_WIDTH_BYTES[member]
    if member not in NUMERIC_USAGES:
        raise ValueError(f"{member.value} has no byte width in a record layout")
    if digit_count is None:
        raise ValueError(f"digits is required for a {member.value} item")

    if member in ZONED_DECIMAL_USAGES:
        # -----------------------------------------------------------------
        # Q-5.2  OPEN QUESTION - the width of a leading-sign display item.
        #
        # PROVISIONAL, implemented here: the ISO and GnuCOBOL default. SIGN
        # LEADING without SEPARATE CHARACTER overpunches the first digit, so
        # the item is `digits` bytes and `pic s9(7)v99   sign leading`
        # [copybooks/wspost-irs.cob:L21] is NINE bytes, not ten. The
        # alternative is `digits + 1`, the width a separate sign character
        # would need.
        #
        # THE FROZEN EVIDENCE DOES NOT RECONCILE, which is why this is
        # marked rather than settled. [copybooks/wspost.cob:L6-L7] reads
        # "98 bytes 26/03/09" then "96 bytes 20/12/11 (leading sign
        # removed)", and that record's two signed items were exactly the
        # ones the clause was removed from - a two-byte reduction across two
        # fields, which is what a SEPARATE sign would cost and an overpunch
        # would not. Against that: summing every field below WS-Post-rrn at
        # `digits` bytes for each signed item gives 98 TODAY, with the
        # clause already gone, so the later figure of 96 matches nothing.
        # The maintainer's inline offsets show why - they are self-consistent
        # from [copybooks/wspost.cob:L24] onward but two low, 46 + 32 being
        # written as 76 - so the 96 in the header carries the same slip, and
        # correcting it gives 98, the same as both the earlier note and
        # today's overpunched sum. On that reading removing the clause
        # changed nothing, which is the overpunch behaviour.
        #
        # Neither reading is adopted as fact. The width matters for
        # record-length reconciliation and for the fixed-character padding of
        # the state-dump normaliser in the compiled-oracle tree, not for the
        # arithmetic, so nothing downstream of the arithmetic is at risk
        # while it stands open. Only compiled behaviour settles it;
        # docs/migration/ambiguity-resolutions.md carries the register entry.
        # -----------------------------------------------------------------
        if position in (
            SignPosition.LEADING_SEPARATE,
            SignPosition.TRAILING_SEPARATE,
        ):
            return digit_count + 1
        return digit_count

    if member in PACKED_DECIMAL_USAGES:
        return (digit_count + 2) // 2

    # COMP and COMP-5, by the Q-5.1 size policy.
    if digit_count > _MAX_POLICY_DIGITS:
        raise ValueError(
            f"digits={digit_count} exceeds the {_MAX_POLICY_DIGITS}-digit "
            "binary size policy; the widest in-scope item declares 11"
        )
    for policy_digits, policy_bytes in DEFAULT_BINARY_SIZE_THRESHOLDS:
        if digit_count <= policy_digits:
            return policy_bytes
    # Unreachable while the size policy above covers every digit count up to
    # `_MAX_POLICY_DIGITS`. It is kept because that policy is a Q-5.1 knob meant
    # to be re-targeted once compiled behaviour settles the question, and an
    # edit that leaves a gap should say so rather than return nothing at all.
    raise ValueError(  # pragma: no cover - a policy-edit guard, not a data path
        f"no binary size covers digits={digit_count}"
    )


# =============================================================================
#  VALUE DOMAIN
# =============================================================================


def value_domain(
    usage: Usage | str,
    *,
    digits: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
) -> tuple[int, int]:
    """Return the inclusive bounds an item of this description can hold.

    The bounds are on the item's DIGITS, not on its value: they count scaled
    units, so `pic s9(8)v99` returns (-9999999999, 9999999999) and a caller
    that wants the value bounds divides by ten to the power of the scale
    itself. Integers throughout, so every bound is exact and no binary
    floating-point type is anywhere near them (rule R-2).

    Two different rules, because two different things bound an item:

    A DECLARED DIGIT COUNT bounds a zoned, packed, COMP or COMP-5 item at ten
    to the power of `digits`, less one - signed either way about zero, unsigned
    from zero up.

    A WIDTH bounds the binary family, which has no digit count to be bounded
    by. Signed spans the two's-complement range of its bytes and unsigned spans
    the whole of it, so `binary-char  unsigned`
    [copybooks/wssystem.cob:L65] is (0, 255) - NOT the (0, 999) its neighbouring
    comment describes - and `Sales-Average      binary-long`
    [copybooks/wssl.cob:L49] is (-2147483648, 2147483647), NOT the eight digits
    its own comment describes. The declaration wins; the comments are recorded
    in the module docstring and left alone (rule R-4).

    Args:
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required for a zoned, packed, COMP or
            COMP-5 item; ignored for the binary family, which has none.
        signed: The dictionary's `signed` boolean for the item.
        unsigned: The copybook's `UNSIGNED` keyword. See `_is_unsigned` for how
            the two combine.

    Returns:
        `(minimum, maximum)`, inclusive, in scaled units.

    Raises:
        ValueError: for a class that holds no number, or for a missing digit
            count. PROGRAMMER errors both - no value is passed to this
            function, so no data condition can reach it.

    """
    member = _usage_of(usage)
    digit_count = _checked_count("digits", digits)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    if member not in NUMERIC_USAGES:
        raise ValueError(f"{member.value} holds no number: it has no value domain")

    if member in BINARY_FAMILY_USAGES:
        bits = 8 * BINARY_WIDTH_BYTES[member]
        if without_sign:
            return (0, (1 << bits) - 1)
        return (-(1 << (bits - 1)), (1 << (bits - 1)) - 1)

    if digit_count is None:
        raise ValueError(f"digits is required for a {member.value} item")
    magnitude = 10**digit_count - 1
    if without_sign:
        return (0, magnitude)
    return (-magnitude, magnitude)


# =============================================================================
#  INTEGER DIVISION, COBOL STYLE
# =============================================================================


def truncate_toward_zero(numerator: int, denominator: int) -> int:
    """Divide two integers the way COBOL does: truncating TOWARD ZERO.

    THIS IS NOT PYTHON'S `//`. The two operators agree on every positive
    dividend and disagree on every negative one, because `//` floors toward
    negative infinity while COBOL discards the remainder and keeps the sign:

        truncate_toward_zero(-7, 2) == -3     while  -7 // 2 == -4
        truncate_toward_zero(7, -2) == -3     while  7 // -2 == -4
        truncate_toward_zero(-7, -2) == 3     while  -7 // -2 == 3
        truncate_toward_zero(7, 2) == 3       while  7 // 2 == 3

    Reaching for `//` instead would move a posted figure by one penny, in one
    direction, on negative amounts only - which is the hardest kind of
    divergence to notice and the easiest to introduce. It matters because whole
    paths of the migrated cycle are integer arithmetic end to end: the sales
    statistics are `binary-long` [copybooks/wssl.cob:L45-L53], the payment-days
    average divides one of them by another [sales/sl100.cbl:L511], and the
    program's own working items are `binary-long` too
    [sales/sl100.cbl:L182-L183].

    Args:
        numerator: The dividend, in whatever units the caller is working in.
        denominator: The divisor.

    Returns:
        The quotient, remainder discarded, sign preserved.

    A zero divisor raises Python's own `ZeroDivisionError` from the division
    below. Nothing is invented for that case and no guard is added: the
    in-scope programs test the divisor themselves before dividing, as
    [sales/sl060.cbl:L819] and [sales/sl100.cbl:L506] do, and COBOL's own
    behaviour for an unguarded divide by zero with no ON SIZE ERROR clause -
    and there is no ON SIZE ERROR anywhere in the twelve in-scope programs - is
    not something the frozen source states.

    """
    quotient = abs(numerator) // abs(denominator)
    if (numerator < 0) != (denominator < 0):
        return -quotient
    return quotient


# =============================================================================
#  THE STORE STEP
#
#  Everything below reproduces what happens to a value on its way INTO a field.
#  Three commitments hold throughout, and each is a rule rather than a
#  preference:
#
#  R-2  Exactness. Values are `decimal.Decimal`, `int`, `str` and `bytes`, and
#       every `decimal` operation runs in a context constructed here, entered
#       with `decimal.localcontext`, sized from the operand so that it cannot
#       fail, and discarded on the way out. The interpreter's ambient global
#       context is neither read nor written, so a store cannot depend on what a
#       caller did earlier.
#
#  R-3  Silence. A store that overflows discards high-order digits and carries
#       on. `ON SIZE ERROR` occurs zero times across the twelve in-scope
#       programs, so there is no error path to reproduce - no exception, no
#       clamp to the maximum, no widening of the field and no warning.
#
#  R-4  No repair. Where the frozen behaviour is odd it is kept odd, and the
#       oddity is cited rather than smoothed.
# =============================================================================


def _exact_decimal(value: decimal.Decimal | int | str) -> decimal.Decimal:
    """Bring an incoming value into exact decimal form without any loss.

    Accepts what an exact computation produces and nothing else: a `Decimal`, a
    Python `int`, or a string holding a numeric literal. A binary
    floating-point argument is refused by omission rather than by name - it
    simply is not one of the accepted types - which is how rule R-2 is enforced
    at the boundary instead of merely documented.

    Raises:
        TypeError: for any other type. A PROGRAMMER error: an accounting value
            that arrives in an inexact carrier has already lost precision
            before this module sees it, and accepting it would launder the
            loss.
        ValueError: for a non-finite decimal. Also a PROGRAMMER error - COBOL
            has no representation for one, so its appearance means the caller
            computed outside the exact-decimal discipline.

    """
    if isinstance(value, decimal.Decimal):
        candidate = value
    elif isinstance(value, int):
        candidate = decimal.Decimal(value)
    elif isinstance(value, str):
        # An unparseable literal raises decimal.InvalidOperation from the
        # constructor. That is the constructor's contract, not a check added
        # here, and it is likewise a programmer error rather than a data
        # condition: no COBOL field delivers free text to a numeric store.
        candidate = decimal.Decimal(value)
    else:
        raise TypeError(
            "an exact numeric value is required - Decimal, int or a numeric "
            f"string - not {type(value).__name__}"
        )
    if not candidate.is_finite():
        raise ValueError(f"COBOL has no representation for {candidate}")
    return candidate


def _quantum(scale: int) -> decimal.Decimal:
    """Return the unit of the last place at this scale, without a context."""
    return decimal.Decimal((0, (1,), -scale))


def _rebuild_decimal(units: int, scale: int) -> decimal.Decimal:
    """Rebuild an exact `Decimal` at `scale` from its scaled integer units.

    Constructed from the digit tuple rather than by scaling, so the result is
    exact, carries exactly `scale` decimal places, and depends on no context.
    """
    magnitude = abs(units)
    return decimal.Decimal(
        (1 if units < 0 else 0, tuple(int(digit) for digit in str(magnitude)), -scale)
    )


def _scaled_units(value: decimal.Decimal, scale: int, rounding: str) -> int:
    """Align a value to `scale` and return it as an exact integer of units.

    This is the half of a COBOL store that acts on the LOW-ORDER end: the
    fractional excess is discarded, or rounded if the statement said ROUNDED.
    Truncation is the default because COBOL truncates unless told otherwise,
    and there are exactly five ROUNDED sites in the whole in-scope cycle.

    The working context is sized from the operand itself - digits, exponent and
    target scale, with slack - so the alignment cannot exceed its precision or
    its exponent range, and so the result depends on nothing but the arguments.
    """
    _, incoming_digits, exponent = value.as_tuple()
    # A finite decimal always carries an integer exponent; `_exact_decimal` has
    # already refused the non-finite forms, whose exponent is a string.
    span = len(incoming_digits) + abs(int(exponent)) + scale + 2
    precision = max(_MINIMUM_WORKING_PRECISION, span)
    exponent_limit = max(999_999, span)
    with decimal.localcontext(
        decimal.Context(
            prec=precision,
            rounding=rounding,
            Emax=exponent_limit,
            Emin=-exponent_limit,
        )
    ):
        aligned = value.quantize(_quantum(scale))
    sign, aligned_digits, _ = aligned.as_tuple()
    magnitude = 0
    for digit in aligned_digits:
        magnitude = magnitude * 10 + digit
    return -magnitude if sign else magnitude


def _wrap_into_bits(units: int, *, bits: int, without_sign: bool) -> int:
    """Reduce an integer into a binary field's own capacity.

    The half of a store that acts on the HIGH-ORDER end, for a field whose
    capacity is a number of bits rather than a number of digits. Signed fields
    wrap two's-complement, exactly as the C type the item compiles to does, so
    40000 stored into a BINARY-SHORT [copybooks/wssl.cob:L43] becomes -25536.
    Unsigned fields take the magnitude first - see `_reduce_units` for why - and
    then wrap.

    Silent by construction: no branch here reports an out-of-range value,
    because a COBOL store does not (rule R-3).
    """
    span = 1 << bits
    if without_sign:
        return abs(units) % span
    half = span >> 1
    return ((units + half) % span) - half


def _reduce_units(
    units: int,
    member: Usage,
    digit_count: int | None,
    without_sign: bool,
) -> int:
    """Reduce aligned units into the receiving field's capacity, silently.

    The high-order half of a COBOL store. Three rules, one per capacity kind:

    A DECLARED DIGIT COUNT - zoned, packed, and COMP under
    `BINARY_TRUNCATE` - discards high-order DIGITS, so 12345.67 stored into a
    `pic 9(3)v99` item is 345.67. Nothing is raised, nothing is clamped: there
    is no ON SIZE ERROR anywhere in the twelve in-scope programs to reproduce.

    A WIDTH - the binary family, and COMP-5, and COMP if `BINARY_TRUNCATE` is
    turned off - wraps into its bits instead. The binary family has no digit
    count to discard by [copybooks/wsbatch.cob:L36-L39], and COMP-5 is native
    binary that the picture does not bound.

    AN UNSIGNED RECEIVING FIELD takes the ABSOLUTE VALUE of a negative sending
    value. That is the ISO COBOL rule for storing into an unsigned item, and it
    is applied uniformly here rather than being invented per class - it is why
    `abs` appears before every reduction below.

    That last rule is worth separating from a question it is often confused
    with. This is the COBOL-level store, and it is settled. What is NOT settled
    is what the GENERATED BRIDGE does when it carries a signed copybook value
    into an unsigned host variable - the sales statistics are signed
    [copybooks/wssl.cob:L46-L52] and their host variables are not, so the sign
    is lost before any SQL runs. That conversion is performed by the bridge's C
    interface, belongs to the data-access layer rather than to this module, and
    is open question Q-3 in the register: the generated dictionary records it
    against every affected field, and only compiled behaviour can measure it.
    """
    if member in BINARY_FAMILY_USAGES:
        bits = 8 * BINARY_WIDTH_BYTES[member]
        return _wrap_into_bits(units, bits=bits, without_sign=without_sign)

    if digit_count is None:
        raise ValueError(f"digits is required to store into a {member.value} item")

    if member is Usage.COMP_5 or (member is Usage.COMP and not BINARY_TRUNCATE):
        bits = 8 * byte_length(member, digits=digit_count)
        return _wrap_into_bits(units, bits=bits, without_sign=without_sign)

    magnitude = abs(units) % 10**digit_count
    if without_sign or units >= 0:
        return magnitude
    return -magnitude


def _stored_units(
    value: decimal.Decimal | int | str,
    *,
    member: Usage,
    digit_count: int | None,
    scale_count: int,
    without_sign: bool,
    rounding: str,
) -> int:
    """Perform a whole numeric store and return the result as scaled units.

    Low-order alignment first, then high-order reduction. The order matters and
    is not interchangeable: rounding can carry into a new integer digit -
    999.996 aligned to two places is 1000.00 - and that carry must then be
    subject to the field's capacity, which it is only if alignment runs first.

    Units rather than a carrier type, because both public callers need the
    integer: `coerce` wraps it into `Decimal` or `int`, and `encode` lays it out
    as bytes. A COMP item with a scale stores its scaled integer -
    `pic 99v99          comp` [copybooks/wssl.cob:L42] holds 12.34 as 1234 in
    two bytes - so the units ARE the stored representation there.
    """
    aligned = _scaled_units(_exact_decimal(value), scale_count, rounding)
    return _reduce_units(aligned, member, digit_count, without_sign)


def _require_text(value: decimal.Decimal | int | str) -> str:
    """Accept a string for an alphanumeric item, or report a category error.

    Raises:
        TypeError: for anything else. A PROGRAMMER error, and a deliberate
            boundary: storing a number into a `PIC X(n)` item is a MOVE between
            unlike CATEGORIES, whose unpacking rules belong to `move.py`.
            Storage answers what a field holds, not how a value crosses
            categories.

    """
    if not isinstance(value, str):
        raise TypeError(
            "an alphanumeric item stores str; a numeric-to-alphanumeric MOVE "
            f"belongs to move.py, not here (got {type(value).__name__})"
        )
    return value


def _stored_text(value: str, character_length: int) -> str:
    """Store text into a `PIC X(n)` item: right-truncated, right-padded.

    COBOL's default alphanumeric MOVE is left-justified with space fill, so a
    value shorter than the item is padded on the right and a longer one loses
    its right-hand end. Neither is an error and neither is reported: the item is
    a fixed run of bytes and always holds exactly `character_length` of them.
    `JUSTIFIED RIGHT` would reverse both, and is not implemented, because the
    token `justified` occurs zero times in `copybooks/*.cob`.

    Padding is preserved on the way out rather than trimmed. Normalising the
    trailing spaces of a fixed-character column belongs to the state-dump
    normaliser of the comparison oracle, which has to do it because a name
    declared 24 characters wide in the copybook becomes a 32-character column
    [copybooks/wsledger.cob:L27]. Doing it here would hide the padding from the
    layer whose job is to compare it.
    """
    return value[:character_length].ljust(character_length)


def coerce(
    value: decimal.Decimal | int | str,
    *,
    usage: Usage | str,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
    rounding: str = _DEFAULT_STORE_ROUNDING,
) -> decimal.Decimal | int | str:
    """Store a value into a field of this description and return what it holds.

    This is the COBOL store, and it is where most of the migration's exactness
    lives. A value is aligned to the receiving field's scale, then reduced into
    its capacity, then handed back in the carrier the field's storage class
    calls for - `decimal.Decimal` for anything scaled, `int` for the binary
    family and for a zero-scale integer, `str` for text.

    TRUNCATION IS THE DEFAULT AND ROUNDING IS THE EXCEPTION. `rounding`
    defaults to `decimal.ROUND_DOWN` because COBOL truncates toward zero on
    store unless the statement is written with ROUNDED. There are exactly five
    ROUNDED sites in the entire in-scope cycle - [general/gl051.cbl:L791],
    [general/gl051.cbl:L796], [general/gl080.cbl:L328], [irs/irs030.cbl:L1551]
    and [irs/irs030.cbl:L1562] - and at those the caller passes
    `decimal.ROUND_HALF_UP`. Getting this the wrong way round would corrupt
    essentially every posted figure, which is why the truncating behaviour is
    the one you get by saying nothing.

    OVERFLOW IS SILENT. High-order digits are discarded and the store carries
    on. Nothing is raised, nothing is clamped, the field is not widened and no
    warning is emitted: `ON SIZE ERROR` occurs zero times across the twelve
    in-scope programs, so there is no error behaviour to reproduce - only
    truncation (rule R-3).

    Args:
        value: An exact value - `Decimal`, `int`, or a numeric string. No
            binary floating-point carrier is accepted (rule R-2).
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required except for the binary family.
        scale: Digits after the implied decimal point; None means none.
        character_length: Required for an alphanumeric item.
        signed: The dictionary's `signed` boolean for the receiving field.
        unsigned: The copybook's `UNSIGNED` keyword.
        sign_position: Where the sign sits. It does not affect the stored
            VALUE - only its byte layout, which `encode` handles - and is
            accepted here so that one description serves both.
        rounding: A `decimal` rounding mode. Truncating by default.

    Returns:
        The value the field now holds, in the carrier `python_storage_for`
        names for it.

    Raises:
        TypeError: for a value in a carrier this module will not accept, or for
            text stored into an alphanumeric item as a non-string. PROGRAMMER
            errors.
        ValueError: for a group or pointer, a non-finite decimal, or a missing
            component. PROGRAMMER errors. NOTHING here raises because of the
            MAGNITUDE or the SIGN of a value: those are data conditions and
            COBOL accepts them silently.

    """
    member = _usage_of(usage)
    _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    scale_count = _checked_count("scale", scale) or 0
    text_length = _checked_count("character_length", character_length)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    if member in ALPHANUMERIC_USAGES:
        if text_length is None:
            raise ValueError("character_length is required for an alphanumeric item")
        return _stored_text(_require_text(value), text_length)

    if member not in NUMERIC_USAGES:
        raise ValueError(f"{member.value} has no elementary store")

    units = _stored_units(
        value,
        member=member,
        digit_count=digit_count,
        scale_count=scale_count,
        without_sign=without_sign,
        rounding=rounding,
    )
    if python_storage_for(member, scale_count) is CobolPythonStorage.INT:
        return units
    return _rebuild_decimal(units, scale_count)


# =============================================================================
#  THE BYTE-LEVEL CODEC
#
#  `encode` and `decode` exist so that the storage rules can be asserted
#  against values captured from the compiled programs BYTE FOR BYTE, which is
#  the only comparison that can prove a packed sign nibble, a zoned overpunch
#  or a binary byte order right. tests/arithmetic/test_comp3_packed_decimal.py,
#  test_comp_binary.py and test_sign_leading_display.py are their consumers.
#
#  `decode(encode(v), ...) == v` holds for every value in a field's domain,
#  whatever the Q-5.3 zone constants turn out to be, because both directions
#  read those same constants.
#
#  Byte order for every binary class is BIG-ENDIAN, reproducing GnuCOBOL's
#  default `binary-byteorder`, and it is covered by the Q-5.1 marker along with
#  the size and truncation policy: the compile scripts select no dialect, so the
#  compiler's defaults govern and are what must be measured. COMP-5 is native
#  byte order by definition, which is NOT modelled here - it is laid out
#  big-endian like the rest, and that branch is unexercised, no in-scope
#  copybook field declaring one.
# =============================================================================

# Byte-transparent for the single-byte character set the frozen sources use, so
# that a record's bytes survive a round trip through `str` unchanged. Chosen
# over an ASCII codec because a COBOL alphanumeric item may hold any byte, and
# a codec that refuses one would be validation this module has no business
# adding (rule R-3).
_TEXT_ENCODING: Final[str] = "latin-1"

# The zoned sign placements that spend a byte of their own, rather than
# overpunching a digit. Unexercised: no in-scope copybook field declares
# either, and `separate` occurs zero times in `copybooks/*.cob`.
_SEPARATE_SIGN_POSITIONS: Final[frozenset[SignPosition]] = frozenset(
    {SignPosition.LEADING_SEPARATE, SignPosition.TRAILING_SEPARATE}
)


def _sign_carrying_index(digit_count: int, position: SignPosition) -> int:
    """Which digit of a zoned item carries the overpunched sign.

    The first for a LEADING sign - `pic s9(7)v99   sign leading`
    [copybooks/wspost-irs.cob:L21] - and the last otherwise. `SignPosition.NONE`
    on a signed item lands here as the last digit deliberately: the ABSENCE of a
    SIGN clause is what declares COBOL's default, a sign overpunched on the
    trailing digit, which is how `pic s9(8)v99` [copybooks/wspost.cob:L23] is
    stored.
    """
    if position is SignPosition.LEADING_INCLUDED:
        return 0
    return digit_count - 1


def _encode_zoned(
    units: int, digit_count: int, position: SignPosition, without_sign: bool
) -> bytes:
    """Lay out zoned decimal: one byte per digit, sign overpunched or separate."""
    digits_text = format(abs(units), f"0{digit_count}d")
    body = bytearray(ZONED_POSITIVE_BASE[int(character)] for character in digits_text)
    negative = units < 0 and not without_sign

    if position in _SEPARATE_SIGN_POSITIONS:
        sign_byte = (
            SEPARATE_SIGN_BYTE_NEGATIVE if negative else SEPARATE_SIGN_BYTE_POSITIVE
        )
        if position is SignPosition.LEADING_SEPARATE:
            return bytes(bytearray([sign_byte]) + body)
        return bytes(body + bytearray([sign_byte]))

    if negative:
        index = _sign_carrying_index(digit_count, position)
        body[index] = ZONED_NEGATIVE_BASE[int(digits_text[index])]
    return bytes(body)


def _decode_zoned(
    raw: bytes, digit_count: int, position: SignPosition, without_sign: bool
) -> int:
    """Read zoned decimal back, tolerantly, and return its scaled units.

    The digit of each byte is its LOW NIBBLE, which is what makes this tolerant
    without any check being added: a space is 0x20, so a space-filled item - the
    state COBOL leaves an uninitialised display field in - reads as zero rather
    than failing. A zone this module does not recognise reads as positive. Both
    are deliberate: reporting them would be validation the COBOL does not
    perform (rule R-3).
    """
    body = raw
    negative = False

    if position in _SEPARATE_SIGN_POSITIONS:
        if position is SignPosition.LEADING_SEPARATE:
            negative = body[0] == SEPARATE_SIGN_BYTE_NEGATIVE
            body = body[1:]
        else:
            negative = body[-1] == SEPARATE_SIGN_BYTE_NEGATIVE
            body = body[:-1]
    elif not without_sign:
        index = _sign_carrying_index(digit_count, position)
        negative = (body[index] & 0xF0) == ZONED_NEGATIVE_ZONE

    magnitude = 0
    for byte in body:
        magnitude = magnitude * 10 + (byte & 0x0F)
    return -magnitude if negative else magnitude


def _encode_packed(units: int, digit_count: int, without_sign: bool) -> bytes:
    """Lay out packed decimal: two digits per byte, sign in the last nibble."""
    width = byte_length(Usage.COMP_3, digits=digit_count)
    digit_positions = 2 * width - 1
    digits_text = format(abs(units), f"0{digit_positions}d")

    if without_sign:
        sign_nibble = PACKED_SIGN_UNSIGNED
    elif units < 0:
        sign_nibble = PACKED_SIGN_NEGATIVE
    else:
        sign_nibble = PACKED_SIGN_POSITIVE

    nibbles = [int(character) for character in digits_text]
    nibbles.append(sign_nibble)
    return bytes(
        (nibbles[index] << 4) | nibbles[index + 1]
        for index in range(0, len(nibbles), 2)
    )


def _decode_packed(raw: bytes, without_sign: bool) -> int:
    """Read packed decimal back and return its scaled units.

    A digit nibble is accumulated arithmetically, so a nibble above nine yields
    a deterministic value instead of an exception. Nothing in the frozen sources
    produces one - every packed field is written by the encoder above or by the
    compiled program - and GnuCOBOL's behaviour for an invalid digit nibble is
    not something the specification states, so no error is invented for it
    (rule R-3). A sign nibble that is not the negative one reads as positive,
    which is what makes the unsigned nibble 0xF and the positive nibble 0xC
    behave alike.
    """
    magnitude = 0
    nibbles: list[int] = []
    for byte in raw:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)
    for nibble in nibbles[:-1]:
        magnitude = magnitude * 10 + nibble
    negative = not without_sign and nibbles[-1] == PACKED_SIGN_NEGATIVE
    return -magnitude if negative else magnitude


def encode(
    value: decimal.Decimal | int | str,
    *,
    usage: Usage | str,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
    rounding: str = _DEFAULT_STORE_ROUNDING,
) -> bytes:
    """Store a value into a field of this description and lay out its bytes.

    The store runs first, exactly as `coerce` performs it - alignment to the
    receiving scale with the caller's rounding, then silent reduction into the
    field's capacity - because a field cannot hold bytes it has no room for.
    The layout then follows the storage class:

    ZONED - one byte per digit, sign overpunched on the trailing digit by
    default [copybooks/wspost.cob:L23] or on the leading digit for the
    SIGN LEADING form [copybooks/wspost-irs.cob:L21],
    [copybooks/irswspost.cob:L14].

    PACKED - two digits per byte with the sign in the last nibble, so
    `pic s9(8)v99   comp-3` [copybooks/wsledger.cob:L28] is six bytes and
    unsigned `pic 9(9)v99` [copybooks/wsbatch.cob:L41-L44] is six bytes with
    an unsigned sign nibble.

    BINARY - the scaled integer, big-endian, in the field's own width. A COMP
    item with a scale holds its scaled integer, so `pic 99v99          comp`
    [copybooks/wssl.cob:L42] holds 12.34 as 1234 in two bytes.

    ALPHANUMERIC - the stored text, right-padded, byte for byte.

    Args:
        value: An exact value, as `coerce` accepts.
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required except for the binary family.
        scale: Digits after the implied decimal point; None means none.
        character_length: Required for an alphanumeric item.
        signed: The dictionary's `signed` boolean for the receiving field.
        unsigned: The copybook's `UNSIGNED` keyword.
        sign_position: Where the sign sits, which here decides the layout.
        rounding: A `decimal` rounding mode. Truncating by default.

    Returns:
        Exactly `byte_length(...)` bytes.

    Raises:
        TypeError, ValueError: as `coerce` and `byte_length` raise them, and for
            the same reason - a PROGRAMMER error in the description or the
            carrier, never a data condition.

    """
    member = _usage_of(usage)
    position = _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    scale_count = _checked_count("scale", scale) or 0
    text_length = _checked_count("character_length", character_length)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    width = byte_length(
        member,
        digits=digit_count,
        scale=scale_count,
        character_length=text_length,
        sign_position=position,
        unsigned=unsigned,
    )

    if member in ALPHANUMERIC_USAGES:
        # `width` is `text_length` here, and `byte_length` has already refused a
        # missing one, so the store below cannot be handed None.
        return _stored_text(_require_text(value), width).encode(_TEXT_ENCODING)

    units = _stored_units(
        value,
        member=member,
        digit_count=digit_count,
        scale_count=scale_count,
        without_sign=without_sign,
        rounding=rounding,
    )

    # A zoned or packed item always declares its digits, and `byte_length` has
    # already refused the call if the caller omitted them, so the fallbacks
    # below are unreachable and exist only to keep the types honest.
    if member in ZONED_DECIMAL_USAGES:
        return _encode_zoned(units, digit_count or 0, position, without_sign)
    if member in PACKED_DECIMAL_USAGES:
        return _encode_packed(units, digit_count or 0, without_sign)
    return units.to_bytes(width, "big", signed=not without_sign)


def decode(
    raw: bytes,
    *,
    usage: Usage | str,
    digits: int | None = None,
    scale: int | None = None,
    character_length: int | None = None,
    signed: bool = True,
    unsigned: bool = False,
    sign_position: SignPosition | str = SignPosition.NONE,
) -> decimal.Decimal | int | str:
    """Read a field's bytes back into the carrier its storage class calls for.

    The inverse of `encode`, and deliberately tolerant of bytes `encode` would
    not have produced: a zoned digit is read from its low nibble so a
    space-filled item reads as zero, an unrecognised zone reads as positive, and
    a packed digit nibble above nine accumulates rather than failing. A COBOL
    read performs no validation, so neither does this (rule R-3).

    The three byte layouts it reads back are the three the sources declare: one
    byte per digit with the sign overpunched on the trailing digit
    [copybooks/wspost.cob:L23] or on the leading one
    [copybooks/wspost-irs.cob:L21], [copybooks/irswspost.cob:L14]; two digits
    per byte with a trailing sign nibble [copybooks/wsledger.cob:L28],
    [copybooks/wsbatch.cob:L41-L44]; and a two's-complement integer of the
    field's own width [copybooks/wssl.cob:L43-L53],
    [copybooks/wsbatch.cob:L36-L39]. Text is returned with its padding intact
    [copybooks/wspost.cob:L24].

    Args:
        raw: Exactly `byte_length(...)` bytes.
        usage: A `Usage` member or its recorded text.
        digits: Total declared digits. Required except for the binary family.
        scale: Digits after the implied decimal point; None means none.
        character_length: Required for an alphanumeric item.
        signed: The dictionary's `signed` boolean for the field.
        unsigned: The copybook's `UNSIGNED` keyword.
        sign_position: Where the sign sits.

    Returns:
        The field's value in the carrier `python_storage_for` names for it -
        `decimal.Decimal` for anything scaled, `int` for the binary family and
        for a zero-scale integer, `str` for text, padding included.

    Raises:
        TypeError: if `raw` is not a bytes-like object. A PROGRAMMER error.
        ValueError: if the buffer is not the field's width, or as `byte_length`
            raises it. A PROGRAMMER error too: the width of a field is part of
            its description, so a buffer of another length means the caller read
            the wrong slice of the record, not that the data is bad.

    """
    member = _usage_of(usage)
    position = _sign_position_of(sign_position)
    digit_count = _checked_count("digits", digits)
    scale_count = _checked_count("scale", scale) or 0
    text_length = _checked_count("character_length", character_length)
    without_sign = _is_unsigned(signed=signed, unsigned=unsigned)

    if not isinstance(raw, bytes | bytearray | memoryview):
        raise TypeError(f"raw must be bytes-like, not {type(raw).__name__}")
    buffer = bytes(raw)

    width = byte_length(
        member,
        digits=digit_count,
        scale=scale_count,
        character_length=text_length,
        sign_position=position,
        unsigned=unsigned,
    )
    if len(buffer) != width:
        raise ValueError(
            f"a {member.value} field of this description is {width} bytes, "
            f"not {len(buffer)}"
        )

    if member in ALPHANUMERIC_USAGES:
        return buffer.decode(_TEXT_ENCODING)

    if member in ZONED_DECIMAL_USAGES:
        units = _decode_zoned(buffer, digit_count or 0, position, without_sign)
    elif member in PACKED_DECIMAL_USAGES:
        units = _decode_packed(buffer, without_sign)
    else:
        units = int.from_bytes(buffer, "big", signed=not without_sign)

    if python_storage_for(member, scale_count) is CobolPythonStorage.INT:
        return units
    return _rebuild_decimal(units, scale_count)
