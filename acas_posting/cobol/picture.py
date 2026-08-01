"""The COBOL PICTURE and data-description-entry parser.

Agent Action Plan section 0.3.1 fixes this file in one line -
`picture.py (PIC clause parser -> FieldDescriptor)` - and section 0.4.1.4
states the transformation row in full, quoted verbatim:

    | `acas_posting/cobol/picture.py` | CREATE | `copybooks/*.cob` (all
    in-scope picture clauses) | Parses `PIC 9(n)`, `9(n)V9(m)`,
    `S9(n)V9(m)`, `X(n)`, `99` and their redefines into descriptors |

"AND THEIR REDEFINES" IS WHY THIS IS AN ENTRY PARSER, NOT A STRING PARSER
=========================================================================
A REDEFINES clause is not part of a picture: it is a sibling clause on the
same data-description entry. So this module reads a whole ENTRY - its level
number, its name, `REDEFINES`, `PIC`, the usage clause, the `SIGN` clause,
`UNSIGNED`, `OCCURS` with its optional key and index phrases, `VALUE` and
`BLANK WHEN ZERO` - and turns it into an
`acas_posting.cobol.field.FieldDescriptor`. Four real declarations show why
nothing less would do:

    03  WS-Batch-Key9 redefines WS-Batch-Key
                            pic 9(6).              [copybooks/wsbatch.cob:L20-L21]
    05  Ledger-Q      pic s9(8)v99   comp-3   occurs  4.
                                               [copybooks/wsledger.cob:L36]
    05  Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5.
                                               [copybooks/wssystem.cob:L61]
    03  CoA-Table   occurs 500
                     ascending key CoA-Desc
                     indexed       CoA-Index.    [irs/irs030.cbl:L379-L381]

The last one is the only in-scope site to write the OCCURS key and index
phrases, and it omits the optional `BY`. Neither phrase changes storage - a key
is a sort order, an index a subscript name - so both are RECORDED on
`ParsedEntry` and acted on nowhere; this module implements no SEARCH.

WHAT THIS MODULE IS FOR
=======================
Every RECORD field already has its storage components pre-parsed in the
generated dictionary, and `field.py` reads them from there through
`FieldDescriptor.from_dictionary_key`. This module exists for the fields the
dictionary does NOT cover: PROGRAM-LOCAL WORKING STORAGE, which the in-scope
cycle turns on.

    03  work-2          pic s9(14)    comp-3.     [sales/sl060.cbl:L206]
    03  work-goods      pic s9(7)v99  comp-3.     [sales/sl060.cbl:L218]
    03  work-a          binary-long   value zero. [sales/sl100.cbl:L182]
    03  l6-account      pic 9999.99 blank when zero.
                                                  [general/gl072.cbl:L233]

`work-2` has ZERO scale while the value added into it carries two, so pence
are discarded on every accumulation; `work-a` is a 32-bit integer in the cash
posting step while the same name is packed decimal in the invoice posting step
[sales/sl060.cbl:L207]; and `l6-account` receives a live `divide`
[general/gl072.cbl:L386], [general/gl072.cbl:L413]. Describe any of them
wrongly and a posted figure moves.

THE IMPORT EDGE IS ONE-DIRECTIONAL, AND DELIBERATELY SO
=======================================================
`picture.py` imports `field.py`. `field.py` MUST NEVER import `picture.py`.
That is sound rather than merely conventional: the dictionary's
`CopybookField` already carries `digits`, `integer_digits`, `scale`, `signed`,
`sign_position`, `usage` and `character_length` pre-parsed, so `field.py` has
no parsing to do and no reason to reach back here.

Agent Action Plan section 0.4.3 gives the layer its whole permission set:

    | Module group | MAY import                              | MUST NOT import |
    |--------------|-----------------------------------------|-----------------|
    | `cobol/*.py` | `dictionary.loader`, `dictionary.model` | `records`, `dal`|
    |              | enums and dataclasses, plus the         | `programs`,     |
    |              | standard library                        | `cli`, `harness`|

For this file that resolves to the standard library, `dictionary.model`'s
vocabularies, `cobol.field` and `cobol.usage`. Nothing else, and no
third-party package at all: the pinned dependency set holds nothing this
folder could use.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  PARSE EVERYTHING. RENDER NOTHING.                                       !!
!!                                                                          !!
!!  This module recognises numeric-EDITED pictures and reports their digit  !!
!!  count and scale, because a live `divide` stores into one                !!
!!  [general/gl072.cbl:L386]. It does NOT produce the edited string, and    !!
!!  there is deliberately no `format`, `edit`, `de_edit`, `render`,         !!
!!  `display` or `to_str` anywhere below. Agent Action Plan section 0.2.2   !!
!!  puts "Report formatting beyond database effects" out of scope and       !!
!!  section 0.3.4 removes the presentation layer rather than reimplementing !!
!!  it, so producing an edited string here would be work this migration is  !!
!!  explicitly not doing.                                                   !!
!!                                                                          !!
!!  No edited value reaches the database in any case: a search for edit     !!
!!  characters inside a `pic` clause across all 29 in-scope copybooks       !!
!!  returns ZERO matches, so an edited picture occurs only in program-local !!
!!  working storage and print lines.                                        !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

THE GRAMMAR IS CLOSED, SMALL AND MEASURED
=========================================
Every form below was counted across the 29 in-scope copybooks and the twelve
in-scope programs rather than assumed.

PLAIN PICTURES.  `x(n)` and repeated `x` runs [copybooks/wspost.cob:L24],
[copybooks/wspost.cob:L17], [copybooks/wsfnctn.cob:L26],
[copybooks/wsfnctn.cob:L38]; repeated `9` runs `9`, `99`, `999`, `9999`
[copybooks/wsfnctn.cob:L23], [copybooks/wsbatch.cob:L23]; `9(n)`
[copybooks/wspost.cob:L13], [copybooks/wsledger.cob:L14]; `9(n)v9(m)` and the
mixed repeat forms [copybooks/wsbatch.cob:L41], [copybooks/wssl.cob:L42],
[general/gl051.cbl:L178]; `s9(n)` [sales/sl060.cbl:L206]; `s9(n)v9(m)`
[copybooks/wspost.cob:L23], [copybooks/wspost-irs.cob:L21]. Case is
irrelevant - the copybooks write `pic s9(8)v99` in lower case while the
generated bridges write `PIC S9(08)V9(02) COMP` in upper case with zero-padded
repeat counts - so both are accepted.

`v99` - A LEADING `V` WITH NO INTEGER DIGITS - IS REAL AND IS IMPLEMENTED.
Twelve occurrences: [general/gl051.cbl:L189], [general/gl051.cbl:L193] and
[general/gl051.cbl:L261]. It yields `digits=2, integer_digits=0, scale=2`.

USAGE CLAUSES.  `comp-3` [copybooks/wsledger.cob:L28], bare `comp`
[copybooks/wsfnctn.cob:L24], `binary-char` [copybooks/wssystem.cob:L62],
`binary-short` [copybooks/wssl.cob:L43], `binary-long`
[copybooks/wsbatch.cob:L36], and the optional `unsigned` modifier
[copybooks/wssystem.cob:L65]. `COMPUTATIONAL`, `COMPUTATIONAL-3` and `COMP-5`
are recognised for completeness of the vocabulary; `COMP-5` is declared in
bridge working storage [common/glpostingMT.scb:L256] and by no in-scope
copybook field.

TWO USAGE FACTS THAT A NAIVE PARSER GETS WRONG:
  * `COMP` MAY CARRY A SCALE. `pic 99v99          comp`
    [copybooks/wssl.cob:L42] and `pic 99v99 comp occurs 5`
    [copybooks/wssystem.cob:L61] are two-place binary items. `COMP` does not
    imply integer.
  * A BINARY-FAMILY ITEM MAY HAVE NO PICTURE AT ALL. Four in one group at
    [copybooks/wsbatch.cob:L36-L39], eleven at [copybooks/wssl.cob:L43-L53],
    the run-date group at [copybooks/wssystem.cob:L62-L69], one at
    [copybooks/wssystem.cob:L127], and two program-local ones at
    [sales/sl100.cbl:L182-L183]. Such an item parses with `picture=None` and
    `digits=None`, and its domain comes from `usage.value_domain`, which reads
    the declared WIDTH.

SIGN CLAUSES.  Exactly two spellings occur and they are NOT unified:
`sign leading` [copybooks/wspost-irs.cob:L21], [copybooks/wspost-irs.cob:L25]
and `sign is leading` [copybooks/irswspost.cob:L14],
[copybooks/irswspost.cob:L18]. Both map to `SignPosition.LEADING_INCLUDED`
and both survive verbatim in `sign_clause_text` (rule R-4). The recognised set
is imported from `usage.SIGN_LEADING_SPELLINGS` rather than retyped, so the
two files cannot drift apart.

EDIT SYMBOLS.  Exactly `Z`, `9`, an ACTUAL `.`, `B`, `CR`, `-`, plus `(n)`
repetition and the `BLANK WHEN ZERO` clause. Thirty distinct edited pictures
occur across the twelve programs; the load-bearing one is
`pic 9999.99 blank when zero` [general/gl072.cbl:L233], and the widest is
`z(9)9.99bb` [general/gl051.cbl:L331]. `BLANK WHEN ZERO` occurs 21 times in
the programs and ZERO times in the copybooks.

CLAUSES AND FORMS MEASURED AT ZERO OCCURRENCES - NOT IMPLEMENTED, AND NOT
SILENTLY ACCEPTED EITHER.  `P` scaling, `*` cheque protection, `$` and any
currency sign, `,` as a thousands separator, `DB`, `+`, `/`, `0` insertion,
`binary-double`, `sign trailing`, `SEPARATE`, `JUSTIFIED`, `SYNCHRONIZED`,
`RENAMES`, `EXTERNAL`, `GLOBAL`, `INDEXED BY`, `DEPENDING ON`, and level
numbers `66` and `78`. A picture carrying one of them comes back as a
`PictureSpec` whose `is_recognised` is false and whose `unrecognised_reason`
names the input verbatim, so the omission is visible in a result rather than
buried in a guess.

`pic a` - THE ONE DEPARTURE FROM THAT LIST, STATED OPENLY
========================================================
ALPHABETIC `A` occurs ZERO times in `copybooks/*.cob`, and the brief for this
file therefore lists it among the forms to surface as unrecognised. It does
occur, twice, in the IRS posting program: `03  nl31-type         pic a.`
[irs/irs030.cbl:L352] and `05  nl31-ac       pic a.`
[irs/irs030.cbl:L359]. Those two fields sit inside `nl31-record`, which the
IN-SCOPE section reads and writes back - `move WS-IRSNL-Record to nl31-record`
[irs/irs030.cbl:L1602] and `move nl31-record to WS-IRSNL-Record`
[irs/irs030.cbl:L1704], the pre-loop snapshot whose end-of-job rewrite is the
lost update of anomaly A-5.

So `A` IS recognised here, because a parser that refused it could not describe
the very record the migrated section reads. What is NOT done is invent a
vocabulary member for it: `dictionary.model.Usage` has no ALPHABETIC member
and rule R-3 forbids adding one, so such an item records the vocabulary's text
class, `Usage.ALPHANUMERIC`, while `PictureSpec.is_alphabetic` and the
verbatim `FieldDescriptor.picture` keep the distinction intact. Nothing about
the frozen source is smoothed away and nothing is settled silently (rule R-6).

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  GROUP-LEVEL USAGE INHERITANCE - THE HIGHEST-RISK DETAIL IN THE GRAMMAR  !!
!!                                                                          !!
!!  A USAGE clause may sit on a GROUP and be inherited by every             !!
!!  subordinate item that declares none of its own. The four in-scope       !!
!!  cases, with the group that carries the class and one of the fields      !!
!!  that takes it:                                                          !!
!!                                                                          !!
!!  03  Amounts                comp-3.  [copybooks/wsbatch.cob:L40]         !!
!!      05  Input-Gross  pic 9(9)v99.   [copybooks/wsbatch.cob:L41]         !!
!!  03  Sales-Ledger-Data      comp-3.  [copybooks/wssys4.cob:L9]           !!
!!      05  sl-payments  pic s9(8)v99.  [copybooks/wssys4.cob:L17]          !!
!!  03  Purchase-Ledger-Data   comp-3.  [copybooks/wssys4.cob:L20]          !!
!!      05  pl-payments  pic s9(8)v99.  [copybooks/wssys4.cob:L28]          !!
!!  05  Vat-Rates              comp.    [copybooks/wssystem.cob:L55]        !!
!!      07  Vat-Rate-1   pic 99v99.     [copybooks/wssystem.cob:L56]        !!
!!  03  total-group  occurs 3  comp-3.  [sales/sl060.cbl:L219]              !!
!!      05  total-net    pic s9(7)v99.  [sales/sl060.cbl:L220]              !!
!!                                                                          !!
!!  NOT ONE of those picture lines carries a usage clause. A parser         !!
!!  that read usage from the picture line alone would class all four        !!
!!  batch amounts and all twenty period totals as zoned DISPLAY, and        !!
!!  EVERY STORED VALUE WOULD BE WRONG. Eighty-five fields of the            !!
!!  generated dictionary inherit their storage this way, every one of       !!
!!  them marked `UsageDeclaredAt.GROUP`; the last of the four cases         !!
!!  carries an OCCURS as well, so the two clauses must not be confused      !!
!!  for one another.                                                        !!
!!                                                                          !!
!!  `parse_entries` therefore maintains a LEVEL STACK and propagates        !!
!!  group usage downward. `parse_entry`, which sees one entry in            !!
!!  isolation, takes `inherited_usage` explicitly and NEVER defaults an     !!
!!  unstated usage to DISPLAY when the caller has said a group usage        !!
!!  applies.                                                                !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

A DECLARATION IS NOT A LINE, AND A PERIOD IS NOT ALWAYS A TERMINATOR
====================================================================
Four in-scope entries put their picture on a continuation line, one of them
splitting merely the name from the picture:

    03  WS-Batch-Key9 redefines WS-Batch-Key
                            pic 9(6).       [copybooks/wsbatch.cob:L20-L21]
    03  WS-Ledger-Key9 redefines WS-Ledger-Key
                          pic 9(8).        [copybooks/wsledger.cob:L21-L22]
    03  Sales-Partial-Ship-Flag
                           pic x.          [copybooks/wssl.cob:L65-L66]
    05  sil-Back-Ordered
                           pic x.          [copybooks/slwsinv.cob:L97-L98]

and a `VALUE` literal may continue across lines with `&`, as the 120-character
heading at [general/gl072.cbl:L224-L226] does. So `join_continuations`
accumulates physical lines until the entry's terminating period.

FINDING THAT PERIOD IS THE SUBTLE PART, and getting it wrong is catastrophic
rather than merely wrong. COBOL's own rule is used: A PERIOD ENDS AN ENTRY
ONLY WHEN IT IS OUTSIDE A LITERAL AND IS FOLLOWED BY WHITESPACE OR THE END OF
THE TEXT. Four declarations prove each half of it:

    03  l6-account      pic 9999.99 blank when zero.
                                          [general/gl072.cbl:L233]
    03  display-vat     pic z9.99.        [general/gl051.cbl:L165]
    03  ws-period1      pic x     value ".".
                                          [general/gl051.cbl:L188]
    77  prog-name       pic x(15)       value "gl071 (3.3.00)".
                                          [general/gl071.cbl:L149]

Split on the first period and the first two lose their pictures to `9999.` and
`z9.`, and the last two lose their entries entirely.

A LITERAL NEED NOT BE PRECEDED BY A SPACE, either. One in-scope declaration
writes its opening quote hard against the keyword:

    03  filler   pic x(65)   value" Old Balance    New Balance    Payment
                             Deduction   Apportioned".
                                          [purchase/pl100.cbl:L234]

The compiler reads it, so this grammar reads it (rule R-6): a literal always
begins and ends a token of its own, whatever abuts it.

A `>>` COMPILER DIRECTIVE CARRIES NO PERIOD AT ALL - `>>source free` is line 1
of [copybooks/wsmaps03.cob:L1] and of every one of the twelve in-scope
programs - so a directive line is emitted as a unit of its own. Without that,
the joiner swallows the rest of the file.

COMMENTS ARE STRIPPED BEFORE PARSING, AND NEVER LEARNED FROM
============================================================
Rule R-4 in one sentence: the maintainer's comments state digit counts that
contradict his own declarations, and the declaration wins.

    03  Sales-Late-Min     binary-short. *> 9999 comp  [copybooks/wssl.cob:L43]
    03  Sales-Limit        binary-long. *> 9(8) comp  [copybooks/wssl.cob:L45]
    05  Page-Lines      binary-char  unsigned. *> 999.  [copybooks/wssystem.cob:L65]

Sixteen bits are not four digits, thirty-two are not eight, and an unsigned
byte spans 0 to 255 rather than 0 to 999. The ruling is to trust the
declaration and resolve nothing, so this module never sees those comments:
`strip_comments` removes them first, and no digit count is ever derived from
one. Stripping is QUOTE-AWARE, because `*>` also follows a literal on the
same line - `copy "file00.cob".    *> "system"`
[copybooks/wsnames.cob:L17].

`88`-LEVEL CONDITION NAMES ARE NOT FIELDS
=========================================
They are part of the data description and they get no descriptor. All six
in-scope shapes are recognised and handed on for
`acas_posting/cobol/condition_names.py` to turn into predicates:

    88  fn-open            value 1.            [copybooks/wsfnctn.cob:L89]
    88  Customer-Dead      value zero.         [copybooks/wssl.cob:L27]
    88  valid-os-type      values 1 2 3 4 5 6. [copybooks/wssystem.cob:L101]
    88  OS-Single          values 1 2 4.       [copybooks/wssystem.cob:L109]
    88  FS-Valid-Options   values 0 thru 1.    [copybooks/wssystem.cob:L122]
    88  IRS-Used           value "Y".          [copybooks/wssystem.cob:L180]
    88  Owner              value is "O".       [copybooks/irswsnl.cob:L13]

Every value is carried as `str`, matching `model.ConditionName.value`, and a
QUOTED LITERAL KEEPS ITS QUOTES, so `'"Y"'` is unambiguous next to `"zero"`.

PROVENANCE IS MANDATORY  (rule R-5)
===================================
`FieldDescriptor` enforces an invariant: an instance must carry either a
`dictionary_key` or a `source_locator` matching
`model.SOURCE_LOCATOR_PATTERN`. Every descriptor this module builds is for a
field the dictionary does NOT cover, so it can only ever have the second.
`source_locator` is therefore a REQUIRED keyword argument on every public
entry point that produces one, and `parse_entries` derives each entry's
locator from the source path and the line the entry begins on. A parse
function able to produce a provenance-less descriptor would be a bug.

Beyond that, every grammar rule, every compiled pattern and every branch below
cites at least one exemplar `[path:Lnnn]` locator from the census, so that a
reader can check the rule against the frozen source that motivated it.

DETERMINISM  (rule R-6)
=======================
Parsing is a pure function of its argument. No clock, no environment, no
randomness, no process identity, and no file is read - a `COPY` statement is
RECORDED rather than expanded, which is what keeps `parse_entries` pure. Every
pattern is compiled once at module level as a `Final` constant. Every table a
caller can iterate is a `tuple` or a `MappingProxyType` over a fixed-order
mapping, never a `set`, so iteration order cannot vary between runs.

EXACTNESS  (rule R-2)
=====================
Every quantity this module produces is an `int` count of digits, characters or
table entries, and `level` is carried as `str` to match
`model.CopybookField.level`, because a level number is a two-character COBOL
token and not an arithmetic quantity. A numeric `VALUE` literal is parsed to
`decimal.Decimal`, never through `float`. The words `float` and `complex` occur
in this module ONLY inside prohibitions such as this one - there is no call to
either, no `math`, no `round`, and no third-party numeric library.

NO ADDED VALIDATION  (rule R-3)
===============================
Nothing here rejects an unusual but legal declaration, and nothing repairs a
contradictory one. Out-of-grammar input comes back as a structured result -
`EntryKind.UNRECOGNISED` for an entry, `is_recognised is False` for a picture -
carrying the offending text verbatim so it can be added to the grammar
deliberately. The two exceptions raise `PictureError`, and both are programmer
errors about the SHAPE OF A CALL rather than about a declaration: a missing
`source_locator`, and a locator that does not match the dictionary's pattern.
No branch below can fire on an accounting value, because no value ever reaches
this module.
"""

from __future__ import annotations

import decimal
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from types import MappingProxyType
from typing import Final

from acas_posting.cobol import usage as cobol_usage
from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary.model import (
    SOURCE_LOCATOR_PATTERN,
    SignPosition,
    Usage,
    UsageDeclaredAt,
)

__all__: Final[tuple[str, ...]] = (
    # The failure first, then the three vocabularies and result objects in the
    # order a reader meets them, then the five functions - the same shape the
    # sibling modules publish.
    "PictureError",
    "EntryKind",
    "JoinedEntry",
    "ParsedEntry",
    "PictureSpec",
    "descriptor_for",
    "join_continuations",
    "parse_entries",
    "parse_entry",
    "parse_picture",
    "strip_comments",
)


# =============================================================================
#  THE ONE FAILURE  (rule R-3)
# =============================================================================


class PictureError(ValueError):
    """A call into this module was shaped wrongly.

    ALWAYS a programmer error about the CALL, never a judgement on a
    declaration and never reachable from an accounting value - no value reaches
    this module at all. It fires in exactly two situations, both of which mean
    the caller cannot satisfy the provenance invariant rule R-5 puts on
    `FieldDescriptor`: a `source_locator` that is empty, and one that does not
    match `model.SOURCE_LOCATOR_PATTERN`.

    An out-of-grammar DECLARATION does not raise. It comes back as
    `EntryKind.UNRECOGNISED` with its text carried verbatim, or as a
    `PictureSpec` whose `is_recognised` is false, so that a caller walking a
    whole copybook can keep going and a reviewer can see precisely which form
    the grammar has not been taught. Rule R-3 forbids adding a validation the
    compiler does not perform, and refusing to continue would be exactly that.

    It derives from `ValueError` so a caller who does not care which of the two
    situations fired can still catch it with the builtin.
    """


# =============================================================================
#  WHAT ONE PARSED UNIT IS
# =============================================================================


class EntryKind(StrEnum):
    """What a line of a COBOL data description turned out to be.

    A data description is not made of field declarations alone, and the four
    non-field kinds below are not hypothetical - they are measured. Naming each
    one is what lets a caller walk a whole copybook and get ZERO unrecognised
    units, without the alternative of quietly dropping whatever did not look
    like a field.

    `StrEnum`, so a member IS its own text and a caller may compare against the
    string directly.
    """

    FIELD = "FIELD"
    """A data-description entry that describes storage, and the only kind that
    carries a `FieldDescriptor`. Every level except `88` produces one -
    including a group [copybooks/wsbatch.cob:L35] and a `filler`
    [copybooks/wsledger.cob:L26], both of which consume record positions."""

    CONDITION_NAME = "CONDITION_NAME"
    """An `88`-level condition name. Part of the data description and NOT a
    field, so it carries no descriptor: 154 of them occur across the 29
    in-scope copybooks, from `88 GL-Batch value 1.`
    [copybooks/wsbatch.cob:L16] to `88 IRS-Both-Used value "B".`
    [copybooks/wssystem.cob:L181]."""

    COPY = "COPY"
    """A `COPY` statement. RECORDED AND NOT EXPANDED - no file is read, which
    is what keeps parsing a pure function of its argument (rule R-6). Thirty-
    four occur in one copybook alone [copybooks/wsnames.cob:L17], and one
    spans two physical lines with pseudo-text delimiters
    [copybooks/slwsoi3.cob:L18-L19]."""

    DIRECTIVE = "DIRECTIVE"
    """A `>>` compiler directive. `>>source free` is line 1 of
    [copybooks/wsmaps03.cob:L1] and of every one of the twelve in-scope
    programs. It carries NO terminating period, which is why it is a unit of
    its own rather than something the joiner accumulates."""

    UNRECOGNISED = "UNRECOGNISED"
    """Text the closed grammar does not cover, carried verbatim with a reason.
    Deliberately a RESULT rather than an exception (rule R-3), and deliberately
    NOT a place to put anything the grammar could have handled: every one of
    the 29 in-scope copybooks parses with zero units of this kind."""


# =============================================================================
#  COMMENT STRIPPING - AND WHY IT MUST HAPPEN FIRST  (rule R-4)
# =============================================================================

# The free-form inline comment marker. Everything from it to the end of the
# physical line is commentary, and every comment in all 29 in-scope copybooks
# is written this way - the legacy fixed-form indicator-column form does not
# occur, and a scan of column 7 across those files finds only `*>` comments
# that happen to start in column 1.
INLINE_COMMENT_MARKER: Final[str] = "*>"

# The compiler-directive prefix. `>>source free` [copybooks/wsmaps03.cob:L1].
DIRECTIVE_PREFIX: Final[str] = ">>"

# The two characters COBOL may delimit an alphanumeric literal with. Only the
# double quote occurs in the frozen sources; the apostrophe is recognised
# because ignoring it would be a silent assumption, and because a scanner that
# tracks the OPENING delimiter handles the real case correctly - an apostrophe
# INSIDE a double-quoted literal, as in the spool command at
# [copybooks/print-spool-command-p.cob:L6], must not open anything.
LITERAL_DELIMITERS: Final[tuple[str, ...]] = ('"', "'")


def strip_comments(text: str) -> str:
    """Remove `*>` commentary from one or more physical lines, quote-aware.

    THIS MUST HAPPEN BEFORE ANY PARSING, and rule R-4 is the reason. The
    maintainer annotated three of his own declarations with digit counts that
    contradict them:

        03  Sales-Late-Min     binary-short. *> 9999 comp
                                             [copybooks/wssl.cob:L43]
        03  Sales-Limit        binary-long. *> 9(8) comp
                                             [copybooks/wssl.cob:L45]
        05  Page-Lines      binary-char  unsigned. *> 999.
                                             [copybooks/wssystem.cob:L65]

    Sixteen bits are not four digits, thirty-two are not eight, and an unsigned
    byte spans 0 to 255. The ruling is to trust the declaration and resolve
    nothing - so the parser is never shown the comment at all, and no digit
    count below can be derived from one.

    QUOTE-AWARENESS IS NOT DECORATION. `*>` follows a literal on the same line
    at [copybooks/wsnames.cob:L17] - `copy "file00.cob".    *> "system"` - and
    a marker that sat INSIDE a literal would have to be kept. The scan tracks
    the delimiter that OPENED the current literal, so an apostrophe inside a
    double-quoted literal is inert, as it must be for the spool command at
    [copybooks/print-spool-command-p.cob:L6].

    Doubled delimiters, COBOL's way of embedding one in a literal, are handled
    for completeness; they occur zero times in the 29 in-scope copybooks.

    Args:
        text: One physical line, or several separated by newlines. Line
            structure is preserved exactly, so a caller can strip a whole file
            in one call and still count lines afterwards.

    Returns:
        The same text with every comment removed. Trailing whitespace left by a
        removal is stripped from the end of that line, so an otherwise blank
        line comes back empty rather than as a run of spaces. No other
        whitespace is touched - a tab stays a tab, and
        [copybooks/wssystem.cob] contains several.
    """
    kept_lines: list[str] = []
    for line in text.split("\n"):
        kept_lines.append(_strip_one_line(line))
    return "\n".join(kept_lines)


def _strip_one_line(line: str) -> str:
    """Remove commentary from a single physical line.

    Split out from `strip_comments` so the literal-tracking scan is stated once
    and reads as the small state machine it is.
    """
    delimiter: str | None = None
    index = 0
    limit = len(line)
    while index < limit:
        character = line[index]
        if delimiter is None:
            if character in LITERAL_DELIMITERS:
                delimiter = character
                index += 1
                continue
            if line.startswith(INLINE_COMMENT_MARKER, index):
                # Outside a literal, so this really is commentary
                # [copybooks/wssl.cob:L43].
                return line[:index].rstrip()
            index += 1
            continue
        if character == delimiter:
            # A doubled delimiter is an embedded one, not the end of the
            # literal. Unexercised by the frozen sources and cheap to keep
            # right.
            if line.startswith(delimiter * 2, index):
                index += 2
                continue
            delimiter = None
        index += 1
    return line.rstrip()


# =============================================================================
#  JOINING PHYSICAL LINES INTO ENTRIES
#
#  A DECLARATION IS NOT A LINE. Four in-scope entries put their picture on a
#  continuation line - [copybooks/wsbatch.cob:L20-L21],
#  [copybooks/wsledger.cob:L21-L22], [copybooks/wssl.cob:L65-L66] and
#  [copybooks/slwsinv.cob:L97-L98] - and a VALUE literal continues across lines
#  with `&` [general/gl072.cbl:L224-L226]. So the unit of parsing is the ENTRY,
#  which ends at its terminating period, and physical lines are accumulated
#  until one is found.
# =============================================================================


@dataclass(frozen=True, slots=True)
class JoinedEntry:
    """One data-description entry, with the physical lines it came from.

    Frozen and slotted so a caller cannot mutate it behind the joiner's back
    and two runs behave identically (rule R-6).

    Attributes:
        text: The entry with comments already removed and its physical lines
            joined by single spaces, INCLUDING its terminating period when it
            had one. Runs of whitespace inside the entry are left alone, so
            `pic s9(8)v99   comp-3` [copybooks/wsledger.cob:L28] keeps its
            spacing and a reader can compare the text against the source by
            eye.
        first_line: The physical line the entry begins on, one-based. This is
            the line every `source_locator` is built from.
        last_line: The physical line its terminating period sits on. Equal to
            `first_line` for the great majority; 21 for the entry that begins
            at 20 in [copybooks/wsbatch.cob:L20-L21].
    """

    text: str
    first_line: int
    last_line: int


def join_continuations(
    lines: Iterable[str], *, first_line: int = 1
) -> tuple[JoinedEntry, ...]:
    """Accumulate physical lines into whole entries, in source order.

    THE PERIOD RULE, which is COBOL's own and is the load-bearing part of this
    function: A PERIOD ENDS AN ENTRY ONLY WHEN IT IS OUTSIDE A LITERAL AND IS
    FOLLOWED BY WHITESPACE OR BY THE END OF THE TEXT. Four declarations prove
    each half, and each would be destroyed by a naive split on the first
    period:

        03  l6-account      pic 9999.99 blank when zero.
                                            [general/gl072.cbl:L233]
        03  display-vat     pic z9.99.      [general/gl051.cbl:L165]
        03  ws-period1      pic x     value ".".
                                            [general/gl051.cbl:L188]
        77  prog-name       pic x(15)       value "gl071 (3.3.00)".
                                            [general/gl071.cbl:L149]

    The first two would lose their pictures to `9999.` and `z9.` - and
    `l6-account` is the receiver of a live `divide` [general/gl072.cbl:L386],
    so the loss would move a printed account number. The last two would lose
    their entries to a period inside a literal.

    A `>>` DIRECTIVE IS A UNIT OF ITS OWN, because it carries no terminating
    period: `>>source free` is line 1 of [copybooks/wsmaps03.cob:L1] and of all
    twelve in-scope programs. Treating it as ordinary text would make the
    joiner accumulate the entire rest of the file into one unit.

    Several entries on one physical line are handled, because free-form COBOL
    permits it: the scan continues after a terminating period rather than
    discarding the remainder of the line. No in-scope source does this, and
    silently dropping the remainder would be worse than supporting it.

    Args:
        lines: The physical lines, WITHOUT their line terminators. Comments may
            still be present - they are removed here - so a caller may pass
            `path.read_text().splitlines()` straight in.
        first_line: The one-based number of the first line given, so that a
            caller parsing an extract of a file still gets true locators. The
            group at [copybooks/wsbatch.cob:L35-L44] is parsed as an extract
            with `first_line=35`.

    Returns:
        The entries in source order, as a `tuple` because order is observable
        (rule R-6). Blank lines and lines that were entirely commentary
        contribute nothing and produce no entry.
    """
    entries: list[JoinedEntry] = []
    # Parts of the entry currently being accumulated, and the line it began on.
    pending: list[str] = []
    pending_first: int = first_line

    for offset, raw_line in enumerate(lines):
        line_number = first_line + offset
        stripped = _strip_one_line(raw_line)
        if not stripped.strip():
            continue

        if not pending and stripped.lstrip().startswith(DIRECTIVE_PREFIX):
            # Period-less by definition, so it is complete as it stands
            # [copybooks/wsmaps03.cob:L1].
            entries.append(
                JoinedEntry(
                    text=stripped.strip(),
                    first_line=line_number,
                    last_line=line_number,
                )
            )
            continue

        if not pending:
            pending_first = line_number

        remainder = stripped.strip()
        while remainder:
            head, tail = _split_at_terminator(remainder)
            pending.append(head)
            if tail is None:
                # No terminator on this line: keep accumulating
                # [copybooks/wsbatch.cob:L20-L21].
                break
            entries.append(
                JoinedEntry(
                    text=" ".join(part for part in pending if part),
                    first_line=pending_first,
                    last_line=line_number,
                )
            )
            pending = []
            pending_first = line_number
            remainder = tail.strip()

    if pending:
        # A trailing entry with no terminating period. It occurs nowhere in the
        # frozen sources, and emitting what was read beats discarding it
        # silently (rule R-3).
        entries.append(
            JoinedEntry(
                text=" ".join(part for part in pending if part),
                first_line=pending_first,
                last_line=pending_first + max(len(pending) - 1, 0),
            )
        )
    return tuple(entries)


def _split_at_terminator(text: str) -> tuple[str, str | None]:
    """Split one line's worth of text at its first entry terminator.

    Returns the text up to and INCLUDING the terminating period, and whatever
    followed it, or `(text, None)` when the line holds no terminator. The
    period is kept so that a reader comparing `JoinedEntry.text` against the
    source sees the same characters.
    """
    delimiter: str | None = None
    index = 0
    limit = len(text)
    while index < limit:
        character = text[index]
        if delimiter is None:
            if character in LITERAL_DELIMITERS:
                delimiter = character
                index += 1
                continue
            if character == "." and _period_terminates(text, index):
                return text[: index + 1], text[index + 1:]
            index += 1
            continue
        if character == delimiter:
            if text.startswith(delimiter * 2, index):
                index += 2
                continue
            delimiter = None
        index += 1
    return text, None


def _period_terminates(text: str, index: int) -> bool:
    """Whether the period at `index` separates an entry rather than decorating.

    True only at the end of the text or when whitespace follows. That single
    test is what keeps the actual decimal point of an edited picture intact -
    `pic 9999.99 blank when zero.` [general/gl072.cbl:L233] has a `9` after its
    first period and whitespace after its second, and `pic z9.99.`
    [general/gl051.cbl:L165] has the terminator hard against the picture.
    """
    following = index + 1
    if following >= len(text):
        return True
    return text[following].isspace()


# =============================================================================
#  THE PICTURE CHARACTER SET - CLOSED, AND MEASURED
# =============================================================================

# Every symbol below was found in a real declaration; nothing is here on
# suspicion. The value is the number of CHARACTER POSITIONS one occurrence
# occupies in the item, which is what the rendered width is built from and is
# ZERO for the two symbols that describe the value rather than occupy a
# position.
#
#   S   the sign, overpunched or implicit, occupying no position of its own
#         `pic s9(8)v99`            [copybooks/wspost.cob:L23]
#   V   the IMPLIED decimal point, likewise occupying nothing
#         `pic 9(9)v99`             [copybooks/wsbatch.cob:L41]
#   9   a digit position
#         `pic 9(5)`                [copybooks/wspost.cob:L13]
#   X   an alphanumeric position
#         `pic x(32)`               [copybooks/wspost.cob:L24]
#   A   an alphabetic position - see the module docstring for the two sites
#         `pic a`                   [irs/irs030.cbl:L352]
#   Z   a zero-suppressed digit position, and an EDIT symbol
#         `pic z(7)9.99cr`          [general/gl072.cbl:L237]
#   B   a space insertion, an edit symbol, and NOT a digit position
#         `pic bbbz9`               [general/gl072.cbl:L238]
#   .   the ACTUAL decimal point, an edit symbol occupying a position
#         `pic 9999.99`             [general/gl072.cbl:L233]
#   -   a sign insertion, an edit symbol occupying a position
#         `pic 9(8).99-`            [general/gl051.cbl:L182]
#   CR  the credit symbol, an edit symbol occupying TWO positions
#         `pic z(6)9.99cr`          [sales/sl060.cbl:L354]
PICTURE_SYMBOL_WIDTHS: Final[Mapping[str, int]] = MappingProxyType(
    {
        "S": 0,
        "V": 0,
        "9": 1,
        "X": 1,
        "A": 1,
        "Z": 1,
        "B": 1,
        ".": 1,
        "-": 1,
        "CR": 2,
    }
)

# The symbols that count as DIGIT positions, in the sense `digits` and `scale`
# use. `Z` counts because a zero-suppressed position still holds a digit - which
# is why `pic z(7)9.99cr` is ten digits and not two [general/gl072.cbl:L237] -
# and `B`, `.`, `-` and `CR` do not, which is why `pic bbbz9` is two
# [general/gl072.cbl:L238] and `pic z(4)9b(4)` is five
# [general/gl051.cbl:L305].
DIGIT_POSITION_SYMBOLS: Final[tuple[str, ...]] = ("9", "Z")

# The two symbols that mark the decimal point: `V` implies it and occupies
# nothing, `.` is an actual character in a numeric-edited picture. No in-scope
# picture carries both, and none carries two of either.
DECIMAL_POINT_SYMBOLS: Final[tuple[str, ...]] = ("V", ".")

# The symbols whose presence makes a picture numeric-EDITED. `Z`, `B`, `CR`,
# `-` and an actual `.`, exactly as the thirty distinct edited pictures across
# the twelve in-scope programs use them - and no others: `*`, `$`, `,`, `DB`,
# `+`, `/` and `0` insertion were measured at ZERO occurrences and are not
# implemented.
EDIT_SYMBOLS: Final[tuple[str, ...]] = ("Z", "B", ".", "-", "CR")

# The edit symbols that let an item render a negative value. `-`
# [general/gl051.cbl:L182] and `CR` [general/gl072.cbl:L237]. `DB` and `+` do
# not occur.
SIGN_EDIT_SYMBOLS: Final[tuple[str, ...]] = ("-", "CR")

# `PIC` or `PICTURE`, with the optional `IS`. Only the short form occurs - 667
# times across the 29 in-scope copybooks, and not once as `PICTURE` or
# `PIC IS` - but the two long forms cost one alternation each and refusing them
# would be a validation the compiler does not perform (rule R-3).
# Exemplar: `pic 9(5)` [copybooks/wspost.cob:L13].
PICTURE_KEYWORD_RE: Final[re.Pattern[str]] = re.compile(
    r"^pic(?:ture)?\s+(?:is\s+)?", re.IGNORECASE
)

# One picture symbol with its optional repeat count. `CR` leads the alternation
# because it is two characters and must win against a single-symbol match at
# the same position; neither `C` nor `R` is a symbol on its own, so a stray one
# is reported rather than absorbed. The count accepts a leading zero, because
# the generated bridges write `PIC S9(08)V9(02) COMP` while the copybooks write
# `pic s9(8)v99` [copybooks/wspost.cob:L23].
PICTURE_SYMBOL_RE: Final[re.Pattern[str]] = re.compile(
    r"(CR|[9XASVZB.\-])(?:\((\d+)\))?"
)


# =============================================================================
#  WHAT A PICTURE SAYS
# =============================================================================


@dataclass(frozen=True, slots=True)
class PictureSpec:
    """Everything one PICTURE clause states about its item's storage.

    Frozen, slotted and built from tuples rather than lists, so that it cannot
    be mutated behind a holder's back and two runs behave identically
    (rule R-6). It holds counts and flags only - no accounting value ever
    reaches it, and every quantity on it is an `int` (rule R-2).

    An out-of-grammar picture is representable: `is_recognised` comes back false
    with `unrecognised_reason` naming the input, and the numeric members are
    None. That is a result rather than an exception because a caller walking a
    whole copybook must be able to keep going, and because refusing to continue
    would be a validation the compiler does not perform (rule R-3).

    Attributes:
        text: The picture exactly as the caller wrote it, case preserved and
            with any `PIC` keyword and terminating period removed. Verbatim for
            the same reason `sign_clause_text` is verbatim: it is the only place
            the source's own spelling survives, and rule R-4 requires it to.
        digits: Total digit positions, integer plus fractional, excluding the
            sign and the decimal point. None for a picture that holds text
            rather than a number. `pic s9(8)v99` is 10
            [copybooks/wspost.cob:L23]; `pic z(7)9.99cr` is also 10, because a
            zero-suppressed position still holds a digit
            [general/gl072.cbl:L237].
        integer_digits: Digit positions left of the decimal point, so that
            `integer_digits + scale == digits` always holds when all three are
            present - the invariant `FieldDescriptor` checks. `pic v99` is 0
            [general/gl051.cbl:L189].
        scale: Digit positions right of it. ZERO IS A REAL AND IMPORTANT
            ANSWER, not a missing one: `pic s9(14)   comp-3`
            [sales/sl060.cbl:L206] has zero scale while the amounts added into
            it carry two, and that is what makes the legacy double truncation
            reproducible.
        character_length: Character positions for a picture that holds text -
            32 for `pic x(32)` [copybooks/wspost.cob:L24], 1 for `pic a`
            [irs/irs030.cbl:L352]. None for a numeric picture, matching the
            dictionary's own convention.
        signed: Whether the picture carries a sign: a leading `S`, or one of the
            sign edit symbols. `pic 9(8).99-` [general/gl051.cbl:L182] is
            signed by its trailing `-`.
        is_numeric: Whether the picture describes a number.
        is_alphanumeric: Whether it describes `X` positions.
        is_alphabetic: Whether it describes `A` positions and no `X`. True at
            exactly two in-scope sites, [irs/irs030.cbl:L352] and
            [irs/irs030.cbl:L359]; see the module docstring for why `A` is
            recognised even though it occurs in no copybook, and why no
            vocabulary member is invented for it.
        is_edited: Whether the picture is numeric-EDITED - any of `Z`, `B`,
            `CR`, `-`, or an ACTUAL `.`. True for `pic 9999.99`
            [general/gl072.cbl:L233] and false for every field of every
            in-scope copybook, since a search for edit characters inside a
            `pic` clause across all 29 returns zero matches.
        edited_character_length: The RENDERED width in characters of an edited
            picture, counting every inserted symbol - 7 for `pic 9999.99`, 13
            for `pic z(7)9.99cr`, 9 for `pic z(4)9b(4)`
            [general/gl051.cbl:L305]. Recorded so a reader can SEE the width;
            NOTHING here produces the rendered string, because report
            formatting is out of scope (Agent Action Plan section 0.2.2). None
            for a picture that is not edited.
        digit_positions: The digit-position symbols in source order, upper
            case - `("9", "9", "9", "9", "9", "9")` for `pic 9999.99` and
            `("Z", "Z", "Z", "Z", "Z", "Z", "Z", "9", "9", "9")` for
            `pic z(7)9.99`. It shows WHICH positions are zero-suppressed, which
            no single count can, and it is a `tuple` because its order is
            observable (rule R-6). Empty for a picture that holds text.
        unrecognised_reason: Why the closed grammar could not read the picture,
            or None when it could. Names the input verbatim so the form can be
            added deliberately rather than guessed at.
    """

    text: str
    digits: int | None
    integer_digits: int | None
    scale: int | None
    character_length: int | None
    signed: bool
    is_numeric: bool
    is_alphanumeric: bool
    is_alphabetic: bool
    is_edited: bool
    edited_character_length: int | None
    digit_positions: tuple[str, ...]
    unrecognised_reason: str | None = None

    @property
    def is_recognised(self) -> bool:
        """Whether the closed grammar read this picture.

        The one flag a caller has to test before trusting the counts. False
        means the picture used a form measured at zero occurrences across the
        frozen sources, and `unrecognised_reason` says which.
        """
        return self.unrecognised_reason is None

    @property
    def holds_text(self) -> bool:
        """Whether the item this picture describes holds characters, not a number.

        True for `pic x(32)` [copybooks/wspost.cob:L24] and for `pic a`
        [irs/irs030.cbl:L352]. The two are kept distinct by `is_alphanumeric`
        and `is_alphabetic`; this asks the question they have in common, which
        is which storage class the item takes.
        """
        return self.is_alphanumeric or self.is_alphabetic


def parse_picture(text: str) -> PictureSpec:
    """Read one PICTURE character-string into its storage components.

    The picture ALONE - not a whole entry. An optional leading `PIC`,
    `PICTURE`, `PIC IS` or `PICTURE IS` and an optional single terminating
    period are accepted and removed, so both `parse_picture("s9(8)v99")` and
    `parse_picture("pic s9(8)v99.")` work; anything else beside the picture is
    out of grammar here, because a COBOL picture contains no space and clauses
    are `parse_entry`'s business.

    The forms it reads, each with the declaration that put it in the grammar:

        9, 99, 999, 9999      [copybooks/wsfnctn.cob:L23]
        9(n), 9(0n)           [copybooks/wspost.cob:L13]
        s9(n)                 [sales/sl060.cbl:L206]
        9(n)v9(m), 99v99      [copybooks/wsbatch.cob:L41]
        s9(n)v9(m)            [copybooks/wspost.cob:L23]
        v99                   [general/gl051.cbl:L189]
        x, xx, xxx, x(n)      [copybooks/wsfnctn.cob:L26]
        a                     [irs/irs030.cbl:L352]
        edited: z, b, cr, -, and an actual .
                              [general/gl072.cbl:L233]

    Case is irrelevant: the copybooks are lower case and the generated bridges
    upper case with zero-padded counts.

    Args:
        text: The picture character-string.

    Returns:
        Its `PictureSpec`. Out-of-grammar input comes back with
        `is_recognised` false and the reason naming the input, NEVER as an
        exception (rule R-3): `P` scaling, `*`, `$`, `,`, `DB`, `+`, `/` and
        `0` insertion were all measured at zero occurrences, so meeting one
        means the grammar needs extending deliberately.
    """
    stated = text.strip()
    body = PICTURE_KEYWORD_RE.sub("", stated).strip()
    if body.endswith("."):
        # A terminating period, not a decimal point: `pic z9.99.`
        # [general/gl051.cbl:L165] ends in both, and only the last is dropped.
        # The scan below still sees `z9.99`, whose `.` is a genuine edit symbol.
        body = body[:-1].strip()

    if not body:
        return _unrecognised_picture(body, f"no picture characters in {text!r}")
    if any(character.isspace() for character in body):
        return _unrecognised_picture(
            body,
            f"{text!r} is not a picture on its own: a COBOL picture contains no "
            "whitespace, so the surplus text is a separate clause - pass the "
            "whole entry to parse_entry instead",
        )

    symbols = _scan_picture_symbols(body)
    if isinstance(symbols, str):
        return _unrecognised_picture(body, symbols)
    return _classify_picture(body, symbols)


def _unrecognised_picture(body: str, reason: str) -> PictureSpec:
    """Build the result for a picture the closed grammar does not cover."""
    return PictureSpec(
        text=body,
        digits=None,
        integer_digits=None,
        scale=None,
        character_length=None,
        signed=False,
        is_numeric=False,
        is_alphanumeric=False,
        is_alphabetic=False,
        is_edited=False,
        edited_character_length=None,
        digit_positions=(),
        unrecognised_reason=reason,
    )


def _scan_picture_symbols(body: str) -> tuple[tuple[str, int], ...] | str:
    """Expand a picture into `(symbol, count)` pairs, or say why it cannot be.

    Repeat counts are expanded into the count rather than into repeated pairs,
    so `z(7)9` becomes `(("Z", 7), ("9", 1))` and a 525-character picture
    [copybooks/wsfnctn.cob:L38] costs two pairs rather than 525.

    Returns:
        The pairs in source order, or a reason string when a character outside
        the closed set was met.
    """
    upper = body.upper()
    pairs: list[tuple[str, int]] = []
    index = 0
    limit = len(upper)
    while index < limit:
        match = PICTURE_SYMBOL_RE.match(upper, index)
        if match is None:
            return (
                f"{body!r} uses the picture character {upper[index]!r} at "
                f"position {index + 1}, which this grammar does not cover. The "
                "recognised set is 9 S V X A Z B CR - . with optional (n) "
                "repetition; P scaling, * cheque protection, a currency sign, "
                "a thousands comma, DB, + , / and 0 insertion were all measured "
                "at zero occurrences across the frozen sources and are not "
                "implemented"
            )
        symbol = match.group(1)
        repeat = match.group(2)
        count = int(repeat) if repeat is not None else 1
        pairs.append((symbol, count))
        index = match.end()
    return tuple(pairs)


def _classify_picture(
    body: str, symbols: tuple[tuple[str, int], ...]
) -> PictureSpec:
    """Turn expanded picture symbols into the storage components they state.

    The counting rules, each with the declaration that fixes it:

      * A digit position is `9` or `Z`, so `pic z(7)9.99cr` is ten digits
        [general/gl072.cbl:L237] while `pic bbbz9` is two
        [general/gl072.cbl:L238].
      * The FIRST `V` or `.` is the decimal point; digits after it are the
        scale. `pic v99` therefore has zero integer digits
        [general/gl051.cbl:L189]. No in-scope picture carries two point
        symbols, and a second one is counted as an ordinary position rather
        than rejected (rule R-3).
      * `X` wins over `A` if a picture somehow carried both, and a text picture
        reports `character_length` while a numeric one reports None - the
        dictionary's own convention.
      * An item is signed by a leading `S` or by a sign edit symbol.
    """
    digit_positions: list[str] = []
    character_positions = 0
    has_x = False
    has_a = False
    has_sign_symbol = False
    edited = False
    point_seen = False
    scale_positions = 0

    for symbol, count in symbols:
        character_positions += PICTURE_SYMBOL_WIDTHS[symbol] * count
        if symbol in EDIT_SYMBOLS:
            edited = True
        if symbol in SIGN_EDIT_SYMBOLS:
            has_sign_symbol = True
        if symbol == "S":
            has_sign_symbol = True
        if symbol == "X":
            has_x = True
        elif symbol == "A":
            has_a = True
        if symbol in DECIMAL_POINT_SYMBOLS and not point_seen:
            point_seen = True
            continue
        if symbol in DIGIT_POSITION_SYMBOLS:
            digit_positions.extend([symbol] * count)
            if point_seen:
                scale_positions += count

    if has_x or has_a:
        # A text item. `pic x(32)` [copybooks/wspost.cob:L24], `pic a`
        # [irs/irs030.cbl:L352]. Its length is its character positions, and it
        # reports no digit count, exactly as the dictionary records for one.
        return PictureSpec(
            text=body,
            digits=None,
            integer_digits=None,
            scale=None,
            character_length=character_positions,
            signed=False,
            is_numeric=False,
            is_alphanumeric=has_x,
            is_alphabetic=has_a and not has_x,
            is_edited=False,
            edited_character_length=None,
            digit_positions=(),
            unrecognised_reason=None,
        )

    if not digit_positions:
        return _unrecognised_picture(
            body,
            f"{body!r} states neither a digit position (9 or Z) nor a character "
            "position (X or A), so there is nothing for it to describe",
        )

    total_digits = len(digit_positions)
    return PictureSpec(
        text=body,
        digits=total_digits,
        integer_digits=total_digits - scale_positions,
        scale=scale_positions,
        character_length=None,
        signed=has_sign_symbol,
        is_numeric=True,
        is_alphanumeric=False,
        is_alphabetic=False,
        is_edited=edited,
        edited_character_length=character_positions if edited else None,
        digit_positions=tuple(digit_positions),
        unrecognised_reason=None,
    )


# =============================================================================
#  THE CLAUSE VOCABULARY - ALSO CLOSED, ALSO MEASURED
# =============================================================================

# Every usage spelling this grammar reads, mapped to the dictionary's own
# vocabulary so that nothing downstream has to know COBOL spelling. The counts
# beside each are occurrences across the 29 in-scope copybooks.
#
# The long `COMPUTATIONAL` spellings occur ZERO times and cost one entry each;
# admitting them is cheaper than a validation the compiler does not perform
# (rule R-3). `BINARY-DOUBLE`, `COMP-1`, `COMP-2`, `COMP-4` and `COMP-6` were
# each measured at zero occurrences and are deliberately absent, so meeting one
# is reported rather than guessed at.
USAGE_TOKENS: Final[Mapping[str, Usage]] = MappingProxyType(
    {
        # 36 occurrences. `pic 9(5) comp` [copybooks/wsfnctn.cob:L24], and note
        # `pic 99v99 comp` [copybooks/wssl.cob:L42] - COMP CARRIES A SCALE.
        "COMP": Usage.COMP,
        "COMPUTATIONAL": Usage.COMP,
        # 45 occurrences. `pic s9(8)v99  comp-3` [copybooks/wsledger.cob:L28].
        "COMP-3": Usage.COMP_3,
        "COMPUTATIONAL-3": Usage.COMP_3,
        # Zero occurrences in the copybooks; in the vocabulary because
        # `model.Usage` publishes it.
        "COMP-5": Usage.COMP_5,
        "COMPUTATIONAL-5": Usage.COMP_5,
        # 26 occurrences, usually with no picture at all.
        # `05  Cyclea          binary-char.` [copybooks/wssystem.cob:L62]
        "BINARY-CHAR": Usage.BINARY_CHAR,
        # 20 occurrences. `05  Maps-Ser-nn   binary-short.`
        # [copybooks/wssystem.cob:L127]
        "BINARY-SHORT": Usage.BINARY_SHORT,
        # 64 occurrences. `05  Entered       binary-long.`
        # [copybooks/wsbatch.cob:L36]
        "BINARY-LONG": Usage.BINARY_LONG,
    }
)

# The clause keywords this grammar reads, published so a caller can see the
# closed set without reading the scanner. Order is the scanner's own dispatch
# order and is observable, so it is a tuple (rule R-6).
CLAUSE_KEYWORDS: Final[tuple[str, ...]] = (
    "PIC",
    "PICTURE",
    "REDEFINES",
    "USAGE",
    "SIGN",
    "SIGNED",
    "UNSIGNED",
    "OCCURS",
    "VALUE",
    "VALUES",
    "BLANK",
)

# The phrases an OCCURS clause may carry after its count. Six data descriptions
# across the repository write one, and the only in-scope site writes BOTH at once
# and omits the optional `BY`:
#     03  CoA-Table   occurs 500
#                      ascending key CoA-Desc
#                      indexed       CoA-Index.
#                                       [irs/irs030.cbl:L379-L381]
# The simpler form is `pic x occurs 26 indexed by q` [copybooks/glwspc.cob:L11].
# Neither phrase changes the item's storage - a key is a sort order and an index
# is a subscript name - so they are RECORDED rather than acted on, which keeps
# them out of the unrecognised bucket without pretending to implement SEARCH.
OCCURS_PHRASE_KEYWORDS: Final[tuple[str, ...]] = (
    "ASCENDING",
    "DESCENDING",
    "INDEXED",
)

# The noise words a clause may carry between its keyword and its operand.
# `value is 0` [copybooks/irswsnl.cob:L13] writes one; `value 1`
# [copybooks/wsfnctn.cob:L89] does not.
CLAUSE_NOISE_WORDS: Final[tuple[str, ...]] = ("IS", "ARE", "TIMES", "CHARACTER")

# The figurative constants that occur, and the only ones. Measured across the
# twelve in-scope programs and the 29 in-scope copybooks: `HIGH-VALUES`,
# `LOW-VALUES`, `QUOTES` and `NULL` occur ZERO times.
#   `value zero`   [copybooks/wsfnctn.cob:L74], [sales/sl060.cbl:L214]
#   `value spaces` [copybooks/wsfnctn.cob:L36]
FIGURATIVE_CONSTANTS: Final[tuple[str, ...]] = (
    "ZERO",
    "ZEROS",
    "ZEROES",
    "SPACE",
    "SPACES",
)

# The range words in an 88-level value list.
# `values 0 thru 1` [copybooks/wssystem.cob:L122]
RANGE_WORDS: Final[tuple[str, ...]] = ("THRU", "THROUGH")

# The level number that introduces a condition name rather than a field.
# `88  IRS-Used   value "Y".` [copybooks/wssystem.cob:L180]
CONDITION_NAME_LEVEL: Final[str] = "88"

# The name that means "no name" - an unnamed area, which still occupies its
# bytes and so still needs a descriptor. 54 occurrences in the copybooks,
# including `03  filler redefines Quarters.` [copybooks/wsledger.cob:L35] and
# the upper-case `03  FILLER  pic x(20).` [copybooks/wssystem.cob:L81].
FILLER_NAME: Final[str] = "FILLER"

# A leading level number. Levels measured across the frozen sources: 01, 02
# [copybooks/wsnames.cob:L14], 03, 05, 07, 77 [general/gl071.cbl:L149] and 88.
# One or two digits, so `1` is read as readily as `01`; 66 and 78 occur zero
# times but a two-digit match admits them without a special case.
LEVEL_RE: Final[re.Pattern[str]] = re.compile(r"^(\d{1,2})(?=\s|$)")

# `COPY "wsnames.cob".` and its friends - 34 occurrences across the copybooks,
# e.g. [copybooks/wsnames.cob:L17]. RECORDED, NEVER EXPANDED: expanding one
# would mean reading a file, and this module is a pure function of its argument
# (rule R-6).
COPY_RE: Final[re.Pattern[str]] = re.compile(r"^copy(?=\s|$)", re.IGNORECASE)

# `BLANK WHEN ZERO`, and the legal short form `BLANK ZERO`. 21 occurrences
# across the twelve in-scope programs, ZERO across the copybooks - which is one
# more piece of evidence that no edited item reaches the database.
# `pic 9999.99 blank when zero` [general/gl072.cbl:L233]
BLANK_WHEN_ZERO_RE: Final[re.Pattern[str]] = re.compile(
    r"^blank(?:\s+when)?\s+zero(?=\s|$)", re.IGNORECASE
)


def _tokenise_clauses(text: str) -> tuple[str, ...]:
    """Split an entry into whitespace-separated tokens, keeping literals whole.

    A quoted literal is ONE token, quotes included, because a VALUE literal may
    contain spaces and a naive split would shred it:
    `value "gl071 (3.3.00)"` [general/gl071.cbl:L149] and
    `value "GL054 No check on items."` [general/gl051.cbl:L226] are each a
    single operand, and the second also contains the period that would
    otherwise look like a terminator.

    Case is preserved, because `sign_clause_text` and the VALUE literal must
    come back exactly as the source wrote them (rule R-4).
    """
    tokens: list[str] = []
    current: list[str] = []
    delimiter: str | None = None
    index = 0
    limit = len(text)
    while index < limit:
        character = text[index]
        if delimiter is not None:
            current.append(character)
            if character == delimiter:
                if index + 1 < limit and text[index + 1] == delimiter:
                    # A doubled delimiter is one embedded quote, not a close.
                    current.append(delimiter)
                    index += 2
                    continue
                # The literal closes here and is complete, so it is emitted at
                # once - anything hard against its closing quote then starts a
                # token of its own rather than being glued to the literal.
                delimiter = None
                tokens.append("".join(current))
                current = []
            index += 1
            continue
        if character in LITERAL_DELIMITERS:
            # ⭐ A LITERAL ALWAYS BEGINS A TOKEN OF ITS OWN, even with no
            # separator before it. `pic x(65) value" Old Balance    New Balance
            # Payment   Deduction   Apportioned".`
            # [purchase/pl100.cbl:L234] writes the opening quote hard against
            # the keyword; the compiler reads it, so this must too (rule R-6 -
            # compiled behaviour decides). Without this, `value"` becomes one
            # token and the whole clause goes unread.
            if current:
                tokens.append("".join(current))
                current = []
            delimiter = character
            current.append(character)
            index += 1
            continue
        if character.isspace():
            if current:
                tokens.append("".join(current))
                current = []
            index += 1
            continue
        current.append(character)
        index += 1
    if current:
        tokens.append("".join(current))
    return tuple(tokens)


@dataclass(slots=True)
class _ClauseScan:
    """A scratch record of the clauses one entry writes, filled left to right.

    Private and mutable on purpose: it is an accumulator that never leaves this
    module. Everything the module RETURNS is frozen (rule R-6).
    """

    picture_text: str | None = None
    redefines: str | None = None
    usage: Usage | None = None
    usage_text: str | None = None
    unsigned: bool = False
    signed_written: bool = False
    sign_clause_text: str | None = None
    sign_word: str | None = None
    sign_separate: bool = False
    occurs: int | None = None
    occurs_key_order: str | None = None
    occurs_keys: tuple[str, ...] = ()
    occurs_indexed_by: tuple[str, ...] = ()
    value_keyword: str | None = None
    value_tokens: tuple[str, ...] = ()
    blank_when_zero: bool = False
    unknown_tokens: tuple[str, ...] = ()


def _scan_clauses(tokens: tuple[str, ...]) -> _ClauseScan:
    """Read the clauses that follow an entry's level and name.

    Clause order is free in COBOL and the frozen sources exercise several, so
    this is a left-to-right dispatch rather than a fixed sequence:
    `pic s9(8)v99   comp-3   occurs  4` [copybooks/wsledger.cob:L36] writes
    three, `Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5` writes four on
    one line [copybooks/wssystem.cob:L61], and `pic 99 comp value zero`
    [sales/sl060.cbl:L223] writes three in a different order again.

    A token outside the vocabulary is COLLECTED, not raised on, so that a
    caller walking a whole copybook keeps going and the omission is visible
    (rule R-3). `JUSTIFIED`, `SYNCHRONIZED`, `EXTERNAL`, `GLOBAL` and `RENAMES`
    were each measured at zero occurrences and are deliberately not in the
    vocabulary, so meeting one lands here and says so.
    """
    scan = _ClauseScan()
    unknown: list[str] = []
    index = 0
    limit = len(tokens)
    while index < limit:
        token = tokens[index]
        upper = token.upper()

        if upper in ("PIC", "PICTURE"):
            index = _skip_noise(tokens, index + 1)
            if index < limit:
                scan.picture_text = tokens[index]
                index += 1
            continue

        if upper == "REDEFINES":
            # Mixed case is live: `redefines` [copybooks/wsbatch.cob:L20] and
            # `Redefines` [copybooks/wssystem.cob:L63] both occur, which is why
            # the comparison is on the upper-cased token.
            index += 1
            if index < limit:
                scan.redefines = tokens[index]
                index += 1
            continue

        if upper == "USAGE":
            # No in-scope source writes the keyword - all 191 usage clauses are
            # bare, as at `pic 9(5) comp` [copybooks/wsfnctn.cob:L24] - but
            # skipping it costs one branch and refusing it would be a
            # validation the compiler does not perform (rule R-3).
            index = _skip_noise(tokens, index + 1)
            continue

        if upper in USAGE_TOKENS:
            scan.usage = USAGE_TOKENS[upper]
            scan.usage_text = token
            index += 1
            continue

        if upper == "UNSIGNED":
            # `05  Page-Lines   binary-char  unsigned.`
            # [copybooks/wssystem.cob:L65]
            scan.unsigned = True
            index += 1
            continue

        if upper == "SIGNED":
            scan.signed_written = True
            index += 1
            continue

        if upper == "SIGN":
            index = _scan_sign_clause(tokens, index, scan)
            continue

        if upper == "OCCURS":
            # Irregular spacing is live - `occurs  4`
            # [copybooks/wsledger.cob:L36] - and tokenising has already
            # absorbed it. A group may carry OCCURS as well as a usage:
            # `03  total-group    occurs 3       comp-3` [sales/sl060.cbl:L219].
            index += 1
            if index < limit and tokens[index].isdigit():
                scan.occurs = int(tokens[index])
                index += 1
            index = _skip_noise(tokens, index)
            continue

        if upper in OCCURS_PHRASE_KEYWORDS:
            index = _scan_occurs_phrase(tokens, index, scan)
            continue

        if upper in ("VALUE", "VALUES"):
            scan.value_keyword = token
            index = _skip_noise(tokens, index + 1)
            index, scan.value_tokens = _scan_value_operand(tokens, index)
            continue

        if upper == "BLANK":
            consumed = _match_blank_when_zero(tokens, index)
            if consumed > 0:
                scan.blank_when_zero = True
                index += consumed
                continue

        unknown.append(token)
        index += 1

    scan.unknown_tokens = tuple(unknown)
    return scan


def _skip_noise(tokens: tuple[str, ...], index: int) -> int:
    """Step past the optional noise words a clause may carry.

    `value is 0` [copybooks/irswsnl.cob:L13] writes one where `value 1`
    [copybooks/wsfnctn.cob:L89] writes none.
    """
    while index < len(tokens) and tokens[index].upper() in CLAUSE_NOISE_WORDS:
        index += 1
    return index


def _scan_sign_clause(
    tokens: tuple[str, ...], index: int, scan: _ClauseScan
) -> int:
    """Read a SIGN clause, keeping the source's own spelling.

    ⛔ THE TWO LIVE SPELLINGS ARE NOT UNIFIED. `sign leading`
    [copybooks/wspost-irs.cob:L21] and `sign is leading`
    [copybooks/irswspost.cob:L14] both describe the same storage, and both
    resolve to the same `SignPosition`, but `sign_clause_text` comes back as
    whichever the source wrote. Rule R-4: the divergence is evidence, and
    smoothing it away would destroy it.

    `SEPARATE` and `TRAILING` are read for completeness - `SignPosition`
    publishes all four placements - and were each measured at ZERO occurrences
    across the frozen sources.
    """
    consumed = [tokens[index]]
    index += 1
    if index < len(tokens) and tokens[index].upper() == "IS":
        consumed.append(tokens[index])
        index += 1
    if index < len(tokens) and tokens[index].upper() in ("LEADING", "TRAILING"):
        scan.sign_word = tokens[index].upper()
        consumed.append(tokens[index])
        index += 1
    if index < len(tokens) and tokens[index].upper() == "SEPARATE":
        scan.sign_separate = True
        consumed.append(tokens[index])
        index += 1
        if index < len(tokens) and tokens[index].upper() == "CHARACTER":
            consumed.append(tokens[index])
            index += 1
    # Joined on a single space, which is what the two live spellings already
    # use, so the text matches `usage.SIGN_LEADING_SPELLINGS` exactly.
    scan.sign_clause_text = " ".join(consumed)
    return index


def _scan_occurs_phrase(
    tokens: tuple[str, ...], index: int, scan: _ClauseScan
) -> int:
    """Read an OCCURS key or index phrase, recording its names.

    `ascending key CoA-Desc` and `indexed CoA-Index`
    [irs/irs030.cbl:L379-L381] - note the second omits the optional `BY`, which
    is why `BY` is accepted rather than required. `indexed by q`
    [copybooks/glwspc.cob:L11] writes it.

    A name list runs until the next clause keyword, usage word or sibling
    phrase, which is how two phrases on one OCCURS are separated without a
    lookahead table.
    """
    word = tokens[index].upper()
    index += 1
    if index < len(tokens) and tokens[index].upper() in ("KEY", "BY"):
        index += 1
    index = _skip_noise(tokens, index)
    names: list[str] = []
    while index < len(tokens):
        candidate = tokens[index].upper()
        if (
            candidate in CLAUSE_KEYWORDS
            or candidate in USAGE_TOKENS
            or candidate in OCCURS_PHRASE_KEYWORDS
        ):
            break
        names.append(tokens[index])
        index += 1
    if word == "INDEXED":
        scan.occurs_indexed_by = scan.occurs_indexed_by + tuple(names)
    else:
        scan.occurs_key_order = word
        scan.occurs_keys = scan.occurs_keys + tuple(names)
    return index


def _scan_value_operand(
    tokens: tuple[str, ...], index: int
) -> tuple[int, tuple[str, ...]]:
    """Collect a VALUE operand, stopping at the next clause keyword.

    A value operand is a literal, a figurative constant, an `ALL` literal
    [general/gl051.cbl:L265], or - on an 88 level - a list of them
    [copybooks/wssystem.cob:L101] possibly with a THRU range
    [copybooks/wssystem.cob:L122]. None of those is a clause keyword, so
    stopping at one lets VALUE appear before another clause without swallowing
    it: `pic 99  comp  value zero` [sales/sl060.cbl:L223] and a hypothetical
    reversal both read correctly.

    A quoted literal is already one token and keeps its quotes, so a literal
    that happens to spell a keyword cannot be mistaken for one.
    """
    collected: list[str] = []
    limit = len(tokens)
    while index < limit:
        upper = tokens[index].upper()
        if (
            upper in CLAUSE_KEYWORDS
            or upper in USAGE_TOKENS
            or upper in OCCURS_PHRASE_KEYWORDS
        ):
            break
        collected.append(tokens[index])
        index += 1
    return index, tuple(collected)


def _match_blank_when_zero(tokens: tuple[str, ...], index: int) -> int:
    """Count the tokens a BLANK WHEN ZERO clause occupies, or return zero.

    `pic 9999.99 blank when zero` [general/gl072.cbl:L233] writes the long
    form; the short `BLANK ZERO` is legal and costs nothing to admit.
    """
    remainder = " ".join(tokens[index:index + 3])
    match = BLANK_WHEN_ZERO_RE.match(remainder)
    if match is None:
        return 0
    return len(match.group(0).split())


# =============================================================================
#  WHAT A WHOLE DATA-DESCRIPTION ENTRY SAYS
# =============================================================================


@dataclass(frozen=True, slots=True)
class ParsedEntry:
    """One data-description entry, read into its clauses and its descriptor.

    Frozen and slotted, holding tuples rather than lists, so a holder cannot
    mutate it and two runs behave identically (rule R-6).

    `kind` says what was read, and it must be tested before the field members
    are trusted: a `COPY` statement, a `>>` directive and an `88` condition name
    are all legitimate members of a data description, and none of them is a
    field. `descriptor` is populated for `EntryKind.FIELD` alone.

    Attributes:
        kind: What this entry is.
        level: The level number exactly as written, so `05` stays `05` and `5`
            stays `5`. A `str` because `model.CopybookField.level` is a `str`
            and the two must not drift.
        name: The item's name as written, case preserved, or `FILLER` for an
            unnamed area. None for a `COPY` or a directive.
        source_locator: `<path>:L<n>` for this entry, always present, because
            the descriptor it builds cannot exist without one (rule R-5).
        text: The entry verbatim after comment stripping and continuation
            joining, whitespace collapsed to single spaces.
        first_line: The physical line the entry starts on.
        last_line: The physical line its terminating period is on. Different
            from `first_line` for the four verified multi-line entries, e.g.
            [copybooks/wsbatch.cob:L20-L21].
        picture: The `PictureSpec`, or None for an item with no PICTURE - which
            is normal, not exceptional: `05  Entered  binary-long.`
            [copybooks/wsbatch.cob:L36] and every group item have none.
        usage: The storage class in the dictionary's own vocabulary.
        usage_declared_at: Whether that usage was written on this entry, was
            INHERITED FROM A GROUP, or fell to the default.
        usage_inherited_from: The group item it was inherited from - `Amounts`
            for the four batch amounts [copybooks/wsbatch.cob:L40], `Vat-Rates`
            for the five VAT rates [copybooks/wssystem.cob:L55].
        usage_group_source: That group's own `<path>:L<n>`, so a reader can go
            straight to the declaration that decided this item's storage. It
            lives here rather than on `FieldDescriptor` because the descriptor
            publishes no such member and rule R-3 forbids adding one.
        signed: Whether the item holds a sign.
        unsigned: Whether the entry wrote `UNSIGNED`
            [copybooks/wssystem.cob:L65].
        sign_position: Where that sign lives.
        sign_clause_text: The SIGN clause verbatim, or None. NOT unified across
            the two live spellings - see `_scan_sign_clause`.
        occurs: The OCCURS count, or None. May sit on a group
            [sales/sl060.cbl:L219].
        occurs_key_order: `ASCENDING` or `DESCENDING` when the OCCURS names a
            sort key, else None [irs/irs030.cbl:L380].
        occurs_keys: The key names that phrase gave, in source order.
        occurs_indexed_by: The index names an `INDEXED` phrase gave, in source
            order [irs/irs030.cbl:L381], [copybooks/glwspc.cob:L11]. Recorded
            only: an index is a subscript name, not storage, so nothing here
            acts on it.
        redefines: The item this one redefines, or None.
        is_filler: Whether the item is an unnamed area.
        is_group: Whether it has subordinate items. Exact when the entry came
            from `parse_entries`, which can see the next entry's level;
            inferred when it was parsed alone, because groupness is NOT
            decidable from one entry - `03  Amounts  comp-3.`
            [copybooks/wsbatch.cob:L40] and `05  Entered  binary-long.`
            [copybooks/wsbatch.cob:L36] are written identically and only one is
            a group.
        parent_group: The group immediately above it, or None at the top.
        value_keyword: `VALUE` or `VALUES` as written, or None.
        value_text: The VALUE operand verbatim, quotes and case intact -
            `"gl071 (3.3.00)"` [general/gl071.cbl:L149]. Text rather than a
            converted value, because converting one here would be a store, and
            stores belong to `move.py`.
        value_number: The VALUE operand as a number, when it is a single numeric
            literal, and None otherwise. An integer literal comes back an `int`
            and one with a decimal point a `decimal.Decimal` - NEVER a `float`,
            because rule R-2 forbids binary floating point from touching an
            accounting value at any point, and a VALUE clause initialises a
            field an accounting value will later occupy. A figurative constant
            (`value zero` [sales/sl060.cbl:L214]), a quoted literal
            (`value "gl071 (3.3.00)"` [general/gl071.cbl:L149]) and an `ALL`
            literal (`value all "+"` [general/gl051.cbl:L265]) stay in
            `value_text` alone: turning one into a value means knowing the
            receiving field, and that is a store, which belongs to `move.py`.
        blank_when_zero: Whether BLANK WHEN ZERO was written
            [general/gl072.cbl:L233]. Recorded only; nothing here renders.
        condition_values: For an `88` entry, its values as written, each a
            `str` and a quoted literal keeping its quotes - matching
            `model.ConditionName.value`, which is a `str` even for `0` and `1`.
            Empty for every other kind.
        condition_is_range: Whether those two values are a THRU range
            [copybooks/wssystem.cob:L122] rather than a list.
        descriptor: The `FieldDescriptor` for a field entry, None otherwise.
        unrecognised_reason: Why the entry could not be read, or None. Names
            the input verbatim so the grammar can be extended deliberately.
        carried_usage: ⭐ THE HIGHEST-RISK MEMBER OF THE WHOLE GRAMMAR. The
            storage class this entry hands DOWN to its subordinate items, which
            is not the same thing as its own `usage`: a group item's own usage
            is always `Usage.GROUP`, because that is what the dictionary records
            for an item with subordinates, so the class it carries for its
            children has to be kept separately. `03  Amounts   comp-3.`
            [copybooks/wsbatch.cob:L40] carries `COMP-3` down to four amount
            fields whose own picture lines say nothing about storage
            [copybooks/wsbatch.cob:L41-L44]; `03  Sales-Ledger-Data  comp-3.`
            [copybooks/wssys4.cob:L9] carries it down to ten;
            `05  Vat-Rates   comp.` [copybooks/wssystem.cob:L55] carries `COMP`
            down to five [copybooks/wssystem.cob:L56-L60]; and
            `03  total-group    occurs 3       comp-3.`
            [sales/sl060.cbl:L219] carries it down to two while also carrying
            an OCCURS [sales/sl060.cbl:L220-L221]. A parser that read usage
            only from the picture line would type all of those DISPLAY, and
            every value it stored would be wrong. A nested group passes down
            whatever it was handed, so the chain does not break at one level.
            None for an elementary item, which has nothing below it, and None
            for a group that neither wrote nor inherited a usage.
    """

    kind: EntryKind
    level: str | None
    name: str | None
    source_locator: str
    text: str
    first_line: int
    last_line: int
    picture: PictureSpec | None = None
    usage: Usage = Usage.GROUP
    usage_declared_at: UsageDeclaredAt = UsageDeclaredAt.DEFAULT
    usage_inherited_from: str | None = None
    usage_group_source: str | None = None
    signed: bool = False
    unsigned: bool = False
    sign_position: SignPosition = SignPosition.NONE
    sign_clause_text: str | None = None
    occurs: int | None = None
    occurs_key_order: str | None = None
    occurs_keys: tuple[str, ...] = ()
    occurs_indexed_by: tuple[str, ...] = ()
    redefines: str | None = None
    is_filler: bool = False
    is_group: bool = False
    parent_group: str | None = None
    value_keyword: str | None = None
    value_text: str | None = None
    value_number: decimal.Decimal | int | None = None
    blank_when_zero: bool = False
    condition_values: tuple[str, ...] = ()
    condition_is_range: bool = False
    descriptor: FieldDescriptor | None = None
    unrecognised_reason: str | None = None

    carried_usage: Usage | None = None

    @property
    def is_recognised(self) -> bool:
        """Whether the closed grammar read this entry."""
        return self.unrecognised_reason is None


def _require_locator(source_locator: str) -> str:
    """Insist on the provenance every descriptor is required to carry.

    Rule R-5 makes a locator mandatory, and `FieldDescriptor` enforces it. This
    module builds descriptors for the program-local working storage the
    generated dictionary does not cover - `work-2` [sales/sl060.cbl:L206],
    `work-a` [sales/sl100.cbl:L182], `l6-account` [general/gl072.cbl:L233] -
    so the locator is the ONLY traceability those fields will ever have and a
    parse that could omit it would be a defect.

    Raises:
        PictureError: The locator is empty or malformed. This is the module's
            one exception, and it is a programmer error rather than a business
            validation: it fires on a caller mistake, never on COBOL input.
    """
    stated = source_locator.strip()
    if not stated:
        raise PictureError(
            "every parsed entry needs a source_locator of the form "
            "<path>:L<n> - 'sales/sl060.cbl:L206' for a single line, "
            "'copybooks/wsbatch.cob:L36-L39' for a span - because rule R-5 "
            "requires every descriptor to be traceable to its frozen "
            "declaration and this module's fields have no dictionary key"
        )
    if not SOURCE_LOCATOR_PATTERN.match(stated):
        raise PictureError(
            f"the source_locator {source_locator!r} is malformed: it must be a "
            "repository-relative path, a colon, then L and the line number, as "
            "in 'copybooks/wsbatch.cob:L41'"
        )
    return stated


# The line numbers inside a locator, so that a single-entry parse can report
# them without the caller repeating itself. `copybooks/wsbatch.cob:L36` gives
# (36, 36) and `copybooks/wsbatch.cob:L36-L39` gives (36, 39).
LOCATOR_LINES_RE: Final[re.Pattern[str]] = re.compile(
    r":L(?P<first>[0-9]+)(?:-L(?P<last>[0-9]+))?$"
)


def _lines_from_locator(locator: str) -> tuple[int, int]:
    """Read the first and last line a locator names.

    The locator has already been matched against the dictionary's own pattern,
    so the numbers are present; the fallback exists only so the function is
    total.
    """
    match = LOCATOR_LINES_RE.search(locator)
    if match is None:
        return (0, 0)
    first = int(match.group("first"))
    last_text = match.group("last")
    return (first, int(last_text) if last_text is not None else first)


def parse_entry(
    text: str,
    *,
    source_locator: str,
    inherited_usage: Usage | None = None,
    inherited_usage_from: str | None = None,
    inherited_usage_source: str | None = None,
    parent_group: str | None = None,
    is_group: bool | None = None,
    first_line: int | None = None,
    last_line: int | None = None,
) -> ParsedEntry:
    """Read one complete data-description entry.

    The entry may span physical lines - four verified declarations do, and the
    parser must not care - so newlines are collapsed before the clause scan.
    Comments are stripped here as well as by `join_continuations`, because
    stripping is idempotent and a caller parsing a single declaration by hand
    should not have to remember (rule R-4 makes the maintainer's comments
    inadmissible, so they must never survive to the clause scan).

    Args:
        text: The entry, with or without its terminating period. Exactly one
            trailing period is removed, so an edited picture keeps its actual
            decimal point: `pic z9.99.` [general/gl051.cbl:L165] parses as
            `z9.99`.
        source_locator: `<path>:L<n>` for the declaration. REQUIRED - see
            `_require_locator` for why rule R-5 admits no default.
        inherited_usage: The storage class a group above this item carries, when
            one does. Passing it is what makes `Input-Gross pic 9(9)v99`
            [copybooks/wsbatch.cob:L41] come back COMP-3 rather than DISPLAY.
            When it is given and the entry writes no usage of its own,
            `usage_declared_at` comes back `GROUP` - NEVER `DEFAULT`, and never
            silently DISPLAY.
        inherited_usage_from: The name of that group, for `usage_inherited_from`.
        inherited_usage_source: That group's own locator, for
            `usage_group_source`.
        parent_group: The group immediately above this item, when known.
        is_group: Whether this item has subordinates. Groupness is NOT
            decidable from one entry - `03  Amounts  comp-3.`
            [copybooks/wsbatch.cob:L40] is a group and
            `05  Entered  binary-long.` [copybooks/wsbatch.cob:L36] is not, and
            the two are written identically - so pass it when it is known and
            leave it None to accept the isolated-entry inference described on
            `ParsedEntry.is_group`. `parse_entries` always passes it, because
            it can see the next entry's level.
        first_line: The physical line the entry starts on. Defaults to the line
            the locator names.
        last_line: The line its terminator is on. Defaults likewise.

    Returns:
        The `ParsedEntry`. A field entry carries a `FieldDescriptor` with the
        given locator; a `COPY`, a `>>` directive and an `88` condition name
        carry none, because none of them is a field.

    Raises:
        PictureError: `source_locator` is empty or malformed. Nothing about the
            COBOL input can raise: an entry the grammar cannot read comes back
            with `is_recognised` false (rule R-3).
    """
    locator = _require_locator(source_locator)
    located_first, located_last = _lines_from_locator(locator)
    begins = first_line if first_line is not None else located_first
    ends = last_line if last_line is not None else located_last

    collapsed = " ".join(strip_comments(text).split())
    if not collapsed:
        return _unrecognised_entry(
            collapsed,
            locator,
            begins,
            ends,
            f"there is no data-description entry in {text!r} - it is blank or "
            "entirely commentary",
        )

    body = collapsed[:-1].rstrip() if collapsed.endswith(".") else collapsed

    if body.startswith(DIRECTIVE_PREFIX):
        # `>>source free` [copybooks/wsmaps03.cob:L1]. A compiler directive,
        # recorded so a caller can see it was there and skipped.
        return _plain_entry(
            EntryKind.DIRECTIVE, collapsed, locator, begins, ends
        )

    if COPY_RE.match(body):
        # `copy "wsnames.cob".` [copybooks/wsnames.cob:L17], including the
        # REPLACING form that spans two lines [copybooks/slwsoi3.cob:L19-L20].
        # RECORDED, NEVER EXPANDED: expanding it would mean reading a file, and
        # this module is a pure function of its argument (rule R-6).
        return _plain_entry(EntryKind.COPY, collapsed, locator, begins, ends)

    level_match = LEVEL_RE.match(body)
    if level_match is None:
        return _unrecognised_entry(
            collapsed,
            locator,
            begins,
            ends,
            f"{collapsed!r} does not begin with a level number, a COPY "
            "statement or a >> directive, so it is not a data-description "
            "entry this grammar reads",
        )

    level = level_match.group(1)
    tokens = _tokenise_clauses(body[level_match.end():])
    name, is_filler, remainder = _split_name(tokens)
    scan = _scan_clauses(remainder)

    if level == CONDITION_NAME_LEVEL:
        return _condition_name_entry(
            name, level, scan, collapsed, locator, begins, ends
        )

    picture = (
        parse_picture(scan.picture_text)
        if scan.picture_text is not None
        else None
    )
    grouped = (
        is_group
        if is_group is not None
        else (picture is None and scan.usage is None)
    )
    # An item that states a picture describes storage itself and so cannot be a
    # group, whatever level follows it. `01  WS-OTM3-Record  pic x(118).`
    # [copybooks/slwsoi3.cob:L9] is the whole record as one alphanumeric item,
    # redefined by the structured view on the next entry.
    if picture is not None:
        grouped = False

    usage, declared_at, inherited_from, group_source, carried = _decide_usage(
        picture=picture,
        written=scan.usage,
        grouped=grouped,
        inherited_usage=inherited_usage,
        inherited_usage_from=inherited_usage_from,
        inherited_usage_source=inherited_usage_source,
    )
    signed = _decide_signed(
        picture=picture, usage=usage, unsigned=scan.unsigned, grouped=grouped
    )
    sign_position = _decide_sign_position(
        picture=picture,
        usage=usage,
        signed=signed,
        sign_word=scan.sign_word,
        sign_separate=scan.sign_separate,
    )
    digits, integer_digits, scale, character_length = _storage_counts(
        picture, grouped
    )
    value_text = " ".join(scan.value_tokens) if scan.value_tokens else None
    value_number = _value_number(scan.value_tokens)

    descriptor = FieldDescriptor(
        name=name,
        usage=usage,
        usage_declared_at=declared_at,
        usage_inherited_from=inherited_from,
        picture=picture.text if picture is not None else None,
        signed=signed,
        sign_position=sign_position,
        sign_clause_text=scan.sign_clause_text,
        digits=digits,
        integer_digits=integer_digits,
        scale=scale,
        character_length=character_length,
        unsigned=scan.unsigned,
        is_edited=picture.is_edited if picture is not None else False,
        occurs=scan.occurs,
        redefines=scan.redefines,
        is_filler=is_filler,
        is_group=grouped,
        parent_group=parent_group,
        # Always derived, never asserted, so `FieldDescriptor.__post_init__`
        # cross-checks it against the same rule the generated dictionary states.
        python_storage=cobol_usage.python_storage_for(usage, scale),
        dictionary_key=None,
        source_locator=locator,
    )

    return ParsedEntry(
        kind=EntryKind.FIELD,
        level=level,
        name=name,
        source_locator=locator,
        text=collapsed,
        first_line=begins,
        last_line=ends,
        picture=picture,
        usage=usage,
        usage_declared_at=declared_at,
        usage_inherited_from=inherited_from,
        usage_group_source=group_source,
        signed=signed,
        unsigned=scan.unsigned,
        sign_position=sign_position,
        sign_clause_text=scan.sign_clause_text,
        occurs=scan.occurs,
        occurs_key_order=scan.occurs_key_order,
        occurs_keys=scan.occurs_keys,
        occurs_indexed_by=scan.occurs_indexed_by,
        redefines=scan.redefines,
        is_filler=is_filler,
        is_group=grouped,
        parent_group=parent_group,
        value_keyword=scan.value_keyword,
        value_text=value_text,
        value_number=value_number,
        blank_when_zero=scan.blank_when_zero,
        descriptor=descriptor,
        unrecognised_reason=_entry_reason(picture, scan),
        carried_usage=carried,
    )


def _split_name(
    tokens: tuple[str, ...],
) -> tuple[str, bool, tuple[str, ...]]:
    """Take the item's name off the front of its clauses.

    Three cases occur. A named item spends one token on its name. `FILLER` -
    lower case at [copybooks/wsledger.cob:L35], upper at
    [copybooks/wssystem.cob:L81] - is recognised as the unnamed area it is, and
    its written spelling is kept as the name because `FieldDescriptor` requires
    a non-empty one and rule R-4 wants the source's own text. An item whose
    level is followed straight by a clause keyword has an OMITTED name, which
    COBOL reads as an implicit FILLER; no in-scope declaration does this, and
    inventing a name for it would be worse than naming it what the compiler
    calls it.
    """
    if not tokens:
        return (FILLER_NAME, True, ())
    head = tokens[0]
    upper = head.upper()
    if upper in CLAUSE_KEYWORDS or upper in USAGE_TOKENS:
        return (FILLER_NAME, True, tokens)
    return (head, upper == FILLER_NAME, tokens[1:])


def _plain_entry(
    kind: EntryKind, text: str, locator: str, first_line: int, last_line: int
) -> ParsedEntry:
    """Record a COPY statement or a compiler directive as itself.

    Neither is a field, so neither carries a descriptor; both are returned
    rather than dropped, so that a caller counting a copybook's entries sees
    everything the file contains.
    """
    return ParsedEntry(
        kind=kind,
        level=None,
        name=None,
        source_locator=locator,
        text=text,
        first_line=first_line,
        last_line=last_line,
    )


def _unrecognised_entry(
    text: str, locator: str, first_line: int, last_line: int, reason: str
) -> ParsedEntry:
    """Record an entry the closed grammar could not read, and say why.

    A result rather than an exception, so a caller walking a whole copybook
    keeps going and the omission is visible instead of fatal (rule R-3).
    """
    return ParsedEntry(
        kind=EntryKind.UNRECOGNISED,
        level=None,
        name=None,
        source_locator=locator,
        text=text,
        first_line=first_line,
        last_line=last_line,
        unrecognised_reason=reason,
    )


def _condition_name_entry(
    name: str,
    level: str,
    scan: _ClauseScan,
    text: str,
    locator: str,
    first_line: int,
    last_line: int,
) -> ParsedEntry:
    """Record an `88` condition name, which is a TEST rather than a field.

    An `88` entry occupies no storage and so gets no descriptor: evaluating one
    is `condition_names.py`'s work, and this module's job is to hand it the
    values the source wrote. All seven live shapes are read:

        88  fn-open                 value 1.
                                        [copybooks/wsfnctn.cob:L89]
        88  FA-FS-Cobol-Files-Used  value zero.
                                        [copybooks/wsfnctn.cob:L74]
        88  valid-os-type           values 1 2 3 4 5 6.
                                        [copybooks/wssystem.cob:L101]
        88  OS-Single               values 1 2 4.
                                        [copybooks/wssystem.cob:L109]
        88  FS-Valid-Options        values 0 thru 1.
                                        [copybooks/wssystem.cob:L122]
        88  IRS-Used                value "Y".
                                        [copybooks/wssystem.cob:L180]
        88  Sales-BO-Set            value "Y".
                                        [copybooks/wssl.cob:L67]

    QUOTING CONVENTION, stated once and held to: a value comes back as a `str`
    exactly as written, and A QUOTED LITERAL KEEPS ITS QUOTES - `'"Y"'`, not
    `'Y'`. That is `model.ConditionName.value`'s own convention, and matching it
    means a condition name read from a copybook and one read from the generated
    dictionary compare equal. A figurative constant keeps its word, `"zero"`,
    for the same reason: converting it here would be a store, and stores belong
    to `move.py`.
    """
    values, is_range = _condition_values(scan.value_tokens)
    return ParsedEntry(
        kind=EntryKind.CONDITION_NAME,
        level=level,
        name=name,
        source_locator=locator,
        text=text,
        first_line=first_line,
        last_line=last_line,
        value_keyword=scan.value_keyword,
        value_text=" ".join(scan.value_tokens) if scan.value_tokens else None,
        condition_values=values,
        condition_is_range=is_range,
        unrecognised_reason=(
            None
            if values
            else f"the 88 entry {text!r} states no value, so there is nothing "
            "for the condition to test against"
        ),
    )


def _condition_values(tokens: tuple[str, ...]) -> tuple[tuple[str, ...], bool]:
    """Split an `88` value operand into its values, and say whether it is a range.

    A trailing comma is dropped, because a list may legally be written with
    separators; none of the 154 condition names across the in-scope copybooks
    uses one, so this costs nothing and guesses nothing.
    """
    values: list[str] = []
    is_range = False
    for token in tokens:
        if token.upper() in RANGE_WORDS:
            # `values 0 thru 1` [copybooks/wssystem.cob:L122]: the word joins
            # two values into bounds rather than being a value itself.
            is_range = True
            continue
        cleaned = token[:-1] if token.endswith(",") else token
        if cleaned:
            values.append(cleaned)
    return (tuple(values), is_range)


def _decide_usage(
    *,
    picture: PictureSpec | None,
    written: Usage | None,
    grouped: bool,
    inherited_usage: Usage | None,
    inherited_usage_from: str | None,
    inherited_usage_source: str | None,
) -> tuple[Usage, UsageDeclaredAt, str | None, str | None, Usage | None]:
    """Decide an item's storage class, and what it hands down.

    ⭐ THE DECISION ORDER, WHICH IS THE WHOLE POINT OF THIS FUNCTION. Stated
    once, held to everywhere, and the reason a group's usage reaches its
    children:

    1. A GROUP is `Usage.GROUP`, because that is what the dictionary records for
       an item with subordinates - but it CARRIES whatever class it was given,
       written on itself (`03  Amounts  comp-3.`
       [copybooks/wsbatch.cob:L40]) or handed to it by a group above, and hands
       that on. `usage_declared_at` says which: FIELD when it wrote one, GROUP
       when it inherited one, DEFAULT when neither.
    2. AN ELEMENTARY ITEM THAT WRITES A USAGE takes it, at FIELD. Note that
       `COMP` may carry a scale - `pic 99v99 comp` [copybooks/wssl.cob:L42] -
       so nothing may assume COMP means integer.
    3. AN ELEMENTARY ITEM THAT WRITES NONE BUT INHERITS ONE takes the inherited
       class, at GROUP, recording the group's name and locator. This is the
       branch that gets 85 fields of the generated dictionary right, among them
       all four batch amounts [copybooks/wsbatch.cob:L41-L44] and all twenty
       period totals [copybooks/wssys4.cob:L9], [copybooks/wssys4.cob:L20].
       ⛔ IT MUST NEVER FALL THROUGH TO DISPLAY.
    4. A NUMERIC PICTURE WITH NOTHING ELSE is `DISPLAY`, at DEFAULT - zoned
       decimal, one byte per digit. `pic 9(5)` [copybooks/wspost.cob:L13].
    5. A TEXT PICTURE WITH NOTHING ELSE is `ALPHANUMERIC`, at DEFAULT.
       `pic x(32)` [copybooks/wspost.cob:L24], and also `pic a`
       [irs/irs030.cbl:L352] - see the module docstring for why the alphabetic
       distinction is carried on `PictureSpec.is_alphabetic` rather than as an
       invented vocabulary member (rule R-3).
    6. NEITHER A PICTURE NOR A USAGE NOR SUBORDINATES is `Usage.GROUP` at
       DEFAULT: it is a group whose children the caller did not supply, which is
       exactly what `parse_entry` sees when handed one line of a record in
       isolation.

    Returns:
        The usage, where it was declared, the group it came from, that group's
        locator, and the class this item carries down to its own children.
    """
    if grouped:
        if written is not None:
            return (Usage.GROUP, UsageDeclaredAt.FIELD, None, None, written)
        if inherited_usage is not None:
            return (
                Usage.GROUP,
                UsageDeclaredAt.GROUP,
                inherited_usage_from,
                inherited_usage_source,
                inherited_usage,
            )
        return (Usage.GROUP, UsageDeclaredAt.DEFAULT, None, None, None)

    if written is not None:
        return (written, UsageDeclaredAt.FIELD, None, None, None)

    if inherited_usage is not None:
        return (
            inherited_usage,
            UsageDeclaredAt.GROUP,
            inherited_usage_from,
            inherited_usage_source,
            None,
        )

    if picture is None:
        return (Usage.GROUP, UsageDeclaredAt.DEFAULT, None, None, None)
    if picture.holds_text:
        return (Usage.ALPHANUMERIC, UsageDeclaredAt.DEFAULT, None, None, None)
    return (Usage.DISPLAY, UsageDeclaredAt.DEFAULT, None, None, None)


def _decide_signed(
    *,
    picture: PictureSpec | None,
    usage: Usage,
    unsigned: bool,
    grouped: bool,
) -> bool:
    """Decide whether an item holds a sign.

    `UNSIGNED` settles it outright - `05  Page-Lines  binary-char  unsigned.`
    [copybooks/wssystem.cob:L65]. A group holds no value and so no sign. A
    picture answers for itself: a leading `S` [copybooks/wspost.cob:L23] or a
    sign edit symbol [general/gl051.cbl:L182]. AN ITEM OF THE BINARY FAMILY WITH
    NO PICTURE AT ALL IS SIGNED, which is the COBOL default and is why
    `05  Entered  binary-long.` [copybooks/wsbatch.cob:L36] spans the full
    32-bit signed range - a distinction that matters, because the sign of one
    such field is lost at the bridge boundary, and that loss is a reproduced
    anomaly rather than a defect to repair [copybooks/wssl.cob:L49].
    """
    if unsigned or grouped:
        return False
    if picture is not None:
        return picture.signed
    return cobol_usage.is_binary_family(usage)


def _decide_sign_position(
    *,
    picture: PictureSpec | None,
    usage: Usage,
    signed: bool,
    sign_word: str | None,
    sign_separate: bool,
) -> SignPosition:
    """Decide where an item's sign lives.

    In order:

      * An unsigned item, and a group, have NO sign position.
      * A COMP, COMP-3, COMP-5 or BINARY-* item's sign is part of its binary or
        packed representation, so it is `IMPLICIT_BINARY` -
        `pic s9(8)v99  comp-3` [copybooks/wsledger.cob:L28].
      * A written SIGN clause decides a DISPLAY item's placement, and BOTH LIVE
        SPELLINGS reach `LEADING_INCLUDED`: `sign leading`
        [copybooks/wspost-irs.cob:L21] and `sign is leading`
        [copybooks/irswspost.cob:L14]. The spellings themselves stay distinct in
        `sign_clause_text` (rule R-4). `SEPARATE` is admitted for completeness
        and occurs at zero sites.
      * ⭐ A NUMERIC-EDITED ITEM HAS NO SIGN POSITION, and this is a deliberate
        decision rather than an oversight. All five placements the vocabulary
        publishes describe where a STORED sign sits; an edit sign is an inserted
        character in a RENDERED form, and this module renders nothing (Agent
        Action Plan section 0.2.2). Nothing downstream is weakened by the
        choice: `usage.coerce` never consults the sign position, and the item is
        still `signed`, so its domain still spans negatives - which is what a
        store into `pic 9(8).99-` [general/gl051.cbl:L182] needs.
      * A signed DISPLAY item with no clause carries its sign in the last digit
        position, which is COBOL's default: `TRAILING_INCLUDED`.
    """
    if not signed:
        return SignPosition.NONE
    if cobol_usage.is_binary_family(usage) or cobol_usage.is_packed(usage):
        return SignPosition.IMPLICIT_BINARY
    if usage in (Usage.COMP, Usage.COMP_5):
        return SignPosition.IMPLICIT_BINARY
    if sign_word == "LEADING":
        return (
            SignPosition.LEADING_SEPARATE
            if sign_separate
            else SignPosition.LEADING_INCLUDED
        )
    if sign_word == "TRAILING":
        return (
            SignPosition.TRAILING_SEPARATE
            if sign_separate
            else SignPosition.TRAILING_INCLUDED
        )
    if picture is not None and picture.is_edited:
        return SignPosition.NONE
    return SignPosition.TRAILING_INCLUDED


def _storage_counts(
    picture: PictureSpec | None, grouped: bool
) -> tuple[int | None, int | None, int | None, int | None]:
    """Report the digit and character counts a descriptor should carry.

    A group reports none, because its size is the sum of its children and
    nothing here walks them. An item with no picture reports none either, which
    is not a gap: `05  Entered  binary-long.` [copybooks/wsbatch.cob:L36] takes
    its domain and its width from its usage, and `usage.py` owns that. A numeric
    picture reports digits and scale and no character length; a text picture the
    reverse. That split is the generated dictionary's own convention, so a
    program-local descriptor and a dictionary-backed one read alike.
    """
    if grouped or picture is None or not picture.is_recognised:
        return (None, None, None, None)
    return (
        picture.digits,
        picture.integer_digits,
        picture.scale,
        picture.character_length,
    )


# A whole-number VALUE literal. `value 1` [copybooks/wsfnctn.cob:L89],
# `value 31` [irs/irs030.cbl:L1602].
VALUE_INTEGER_RE: Final[re.Pattern[str]] = re.compile(r"^[+-]?[0-9]+$")

# A VALUE literal with a decimal point. None of the in-scope declarations writes
# one - every numeric VALUE is a whole number or the figurative `zero` - and
# reading it as `Decimal` rather than refusing it costs one branch.
VALUE_DECIMAL_RE: Final[re.Pattern[str]] = re.compile(
    r"^[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)$"
)


def _value_number(tokens: tuple[str, ...]) -> decimal.Decimal | int | None:
    """Read a single numeric VALUE literal, exactly.

    ⛔ NEVER `float`. Rule R-2 forbids binary floating point from touching an
    accounting value at any point, and a VALUE clause initialises a field that an
    accounting value will later occupy - `77  y   pic 99  value zero.`
    [general/gl080.cbl:L182] is the receiver of the one `ROUNDED` divide in the
    General Ledger cycle. An integer literal becomes an `int` and one with a
    decimal point a `decimal.Decimal`, which is the same split
    `usage.python_storage_for` applies to a field's own scale.

    Anything that is not a single numeric literal comes back None and stays in
    `value_text`: a figurative constant, a quoted literal, and an `ALL` literal
    all need the receiving field before they mean anything, and supplying a
    receiving field is a store, which belongs to `move.py`.
    """
    if len(tokens) != 1:
        return None
    literal = tokens[0]
    if VALUE_INTEGER_RE.match(literal):
        return int(literal)
    if VALUE_DECIMAL_RE.match(literal):
        # An exact decimal built from the literal's own text, so the value is
        # the digits the source wrote and nothing else.
        return decimal.Decimal(literal)
    return None


def _entry_reason(picture: PictureSpec | None, scan: _ClauseScan) -> str | None:
    """Say why an entry was only partly read, or None when it was read whole.

    An entry that carries an out-of-grammar picture or an out-of-vocabulary
    clause still comes back with everything that WAS read, and with this reason
    naming what was not, so the omission is visible and the grammar can be
    extended deliberately (rule R-3).
    """
    problems: list[str] = []
    if picture is not None and not picture.is_recognised:
        problems.append(str(picture.unrecognised_reason))
    if scan.unknown_tokens:
        listed = ", ".join(repr(token) for token in scan.unknown_tokens)
        problems.append(
            f"the clause word or words {listed} are outside this grammar's "
            "vocabulary; JUSTIFIED, SYNCHRONIZED, EXTERNAL, GLOBAL and RENAMES "
            "were each measured at zero occurrences across the frozen sources "
            "and are deliberately not implemented"
        )
    return "; ".join(problems) if problems else None


# =============================================================================
#  A WHOLE RECORD, WITH THE LEVEL STACK THAT MAKES GROUP USAGE REACH ITS FIELDS
# =============================================================================

# The levels that never nest: an independent working-storage item, a RENAMES and
# a constant. `77  prog-name  pic x(15)  value "gl071 (3.3.00)".`
# [general/gl071.cbl:L149] and `77  fs-reply  pic xx.`
# [general/gl071.cbl:L150] are both elementary by definition, so a 77 can
# neither be a group nor be subordinate to one - which matters, because a naive
# "is the next level higher?" test would make an 01 above a 77 look like a group.
# 66 and 78 were each measured at zero occurrences and cost nothing to admit.
SPECIAL_LEVELS: Final[tuple[str, ...]] = ("66", "77", "78")

# The record level. An 01 always restarts the hierarchy, so it clears the stack.
TOP_LEVEL: Final[int] = 1


@dataclass(slots=True)
class _StackFrame:
    """One open group while a record is being walked.

    Private and mutable, like `_ClauseScan`: an accumulator that never leaves
    this module.

    `carried` is the storage class this group hands to its children, and
    `origin_name` / `origin_locator` name the group that actually WROTE that
    class - which is the declaration a reader has to visit, and is why they are
    propagated unchanged through a nested group rather than being overwritten at
    each level.
    """

    level: int
    name: str
    carried: Usage | None
    origin_name: str | None
    origin_locator: str | None


def parse_entries(
    text: str, *, source_path: str, first_line: int = 1
) -> tuple[ParsedEntry, ...]:
    """Read a whole record, or a whole working-storage group, in source order.

    ⭐ THIS IS THE FUNCTION THAT GETS GROUP-LEVEL USAGE RIGHT, and it is the one
    a caller should reach for by default. `parse_entry` cannot: a usage clause
    may sit on a GROUP and be inherited by every subordinate item that writes
    none of its own, and 85 record fields of the generated dictionary take their
    storage that way - among them all four batch amounts
    [copybooks/wsbatch.cob:L40-L44], all twenty period totals
    [copybooks/wssys4.cob:L9], [copybooks/wssys4.cob:L20], and all five VAT
    rates [copybooks/wssystem.cob:L55-L60]. A parser that read usage from the
    picture line alone would type every one of them DISPLAY, and every value it
    stored would be wrong.

    It works in TWO PASSES, which is what lets it be exact rather than
    heuristic:

    1. Every entry is read once with no context, to learn its level and whether
       it states a picture of its own. GROUPNESS IS NOT DECIDABLE FROM ONE
       ENTRY - `03  Amounts  comp-3.` [copybooks/wsbatch.cob:L40] and
       `05  Entered  binary-long.` [copybooks/wsbatch.cob:L36] are written
       identically, and only the level of what FOLLOWS separates them - so this
       pass exists purely to make the next entry's level available.
    2. Every entry is read again, this time with its parent group, the storage
       class that group carries, and its exact `is_group`. Reading twice rather
       than patching the first result keeps ONE grammar path, so a fix can never
       land in one pass and miss the other.

    An item that states a picture is never a group, whatever level follows:
    `01  WS-OTM3-Record  pic x(118).` [copybooks/slwsoi3.cob:L9] is the whole
    record as one alphanumeric item, redefined by the structured view that
    follows it.

    A `COPY` statement is RECORDED, NEVER EXPANDED, and does not break the
    hierarchy either side of it - 34 of them occur, e.g.
    [copybooks/wsnames.cob:L17] and the REPLACING form at
    [copybooks/slwsoi3.cob:L19-L20]. Expanding one would mean reading a file,
    and this function is a pure function of its argument (rule R-6).

    Args:
        text: The source of the record or group, comments and all.
        source_path: The repository-relative path the text came from, used to
            build each entry's locator. Every descriptor needs one (rule R-5).
        first_line: The one-based number of the first line of `text`, so an
            extract still yields true locators - pass 35 when handing it
            [copybooks/wsbatch.cob:L35-L44].

    Returns:
        The entries in SOURCE ORDER, as a `tuple` because that order is
        observable and must not vary between runs (rule R-6). Every field entry
        carries a `FieldDescriptor`; condition names, COPY statements and
        directives carry none.
    """
    joined = join_continuations(text.splitlines(), first_line=first_line)
    context_free = tuple(
        parse_entry(
            entry.text,
            source_locator=f"{source_path}:L{entry.first_line}",
            first_line=entry.first_line,
            last_line=entry.last_line,
        )
        for entry in joined
    )
    groupness = _groupness(context_free)

    stack: list[_StackFrame] = []
    walked: list[ParsedEntry] = []
    # The elementary or group item most recently seen, so that an 88 condition
    # name can name the item it qualifies - which is how the generated
    # dictionary attaches one, as `copybook.condition_names`.
    qualified: str | None = None

    for index, entry in enumerate(joined):
        parsed = context_free[index]

        if parsed.kind is EntryKind.CONDITION_NAME:
            walked.append(replace(parsed, parent_group=qualified))
            continue

        if parsed.kind is not EntryKind.FIELD:
            walked.append(parsed)
            continue

        level = parsed.level or ""
        if level in SPECIAL_LEVELS or _level_value(level) <= TOP_LEVEL:
            # An 01 restarts the hierarchy; a 77 stands outside it entirely.
            stack.clear()
        else:
            value = _level_value(level)
            while stack and stack[-1].level >= value:
                stack.pop()

        frame = stack[-1] if stack else None
        rebuilt = parse_entry(
            entry.text,
            source_locator=f"{source_path}:L{entry.first_line}",
            inherited_usage=frame.carried if frame is not None else None,
            inherited_usage_from=frame.origin_name if frame is not None else None,
            inherited_usage_source=(
                frame.origin_locator if frame is not None else None
            ),
            parent_group=frame.name if frame is not None else None,
            is_group=groupness[index],
            first_line=entry.first_line,
            last_line=entry.last_line,
        )
        walked.append(rebuilt)
        qualified = rebuilt.name

        if rebuilt.is_group and rebuilt.level not in SPECIAL_LEVELS:
            wrote_it = rebuilt.usage_declared_at is UsageDeclaredAt.FIELD
            stack.append(
                _StackFrame(
                    level=_level_value(rebuilt.level or ""),
                    name=rebuilt.name or FILLER_NAME,
                    carried=rebuilt.carried_usage,
                    # The group that WROTE the class keeps the credit, so a
                    # nested group passes its ancestor's name and locator
                    # through rather than substituting its own.
                    origin_name=(
                        rebuilt.name
                        if wrote_it
                        else (frame.origin_name if frame is not None else None)
                    ),
                    origin_locator=(
                        rebuilt.source_locator
                        if wrote_it
                        else (
                            frame.origin_locator if frame is not None else None
                        )
                    ),
                )
            )

    return tuple(walked)


def _level_value(level: str) -> int:
    """Read a level number, treating an unreadable one as the record level.

    `LEVEL_RE` has already matched digits by the time this is reached, so the
    fallback exists only so the function is total.
    """
    return int(level) if level.isdigit() else TOP_LEVEL


def _groupness(entries: tuple[ParsedEntry, ...]) -> tuple[bool, ...]:
    """Decide, for each entry, whether it has subordinate items.

    An entry is a group when it states NO picture of its own and the next field
    entry sits at a HIGHER level number. Three refinements, each from a measured
    declaration:

      * An entry that states a picture is never a group
        [copybooks/slwsoi3.cob:L9].
      * A 66, 77 or 78 is never a group and can never be subordinate to one, so
        it neither becomes one nor makes its predecessor one
        [general/gl071.cbl:L149].
      * A condition name, a COPY and a directive are skipped when looking for
        the next field, because none of them is a subordinate item. An 88 sits at
        a numerically higher level than everything, and treating it as a
        subordinate would make every item that carries a condition name look
        like a group [copybooks/wssystem.cob:L180].

    Returns a `tuple` so the order matches the entries it was built from
    (rule R-6).
    """
    flags: list[bool] = []
    total = len(entries)
    for index, entry in enumerate(entries):
        if (
            entry.kind is not EntryKind.FIELD
            or entry.picture is not None
            or (entry.level or "") in SPECIAL_LEVELS
        ):
            flags.append(False)
            continue
        own = _level_value(entry.level or "")
        grouped = False
        for follower in range(index + 1, total):
            candidate = entries[follower]
            if candidate.kind is not EntryKind.FIELD:
                continue
            if (candidate.level or "") in SPECIAL_LEVELS:
                break
            grouped = _level_value(candidate.level or "") > own
            break
        flags.append(grouped)
    return tuple(flags)


# =============================================================================
#  ONE DECLARATION, ONE DESCRIPTOR
# =============================================================================


def descriptor_for(
    clauses: str,
    *,
    name: str,
    source_locator: str,
    level: str = "03",
    inherited_usage: Usage | None = None,
    inherited_usage_from: str | None = None,
    inherited_usage_source: str | None = None,
    parent_group: str | None = None,
    is_group: bool | None = None,
) -> FieldDescriptor:
    """Build the descriptor for one field from its clauses and its name.

    The convenience entry point for the program-local working storage this
    module exists to describe - the fields the generated dictionary does not
    cover, because they never reach a table:

        work-2      s9(14)   comp-3          [sales/sl060.cbl:L206]
        work-goods  s9(7)v99 comp-3          [sales/sl060.cbl:L218]
        work-a      binary-long value zero   [sales/sl100.cbl:L182]
        l6-account  9999.99 blank when zero  [general/gl072.cbl:L233]

    It composes the declaration and hands it to `parse_entry`, so there is
    exactly ONE grammar in this module and a caller cannot reach a second,
    divergent reading of the same text.

    Args:
        clauses: The picture and clauses as the source writes them, with or
            without the `PIC` keyword and with or without a terminating period.
            A leading bare picture is given the keyword automatically, so
            `"99v99 comp"` [copybooks/wssl.cob:L42] and
            `"pic 99v99 comp"` both work.
        name: The field's name, verbatim from its declaration.
        source_locator: `<path>:L<n>`. REQUIRED, and the whole point: these
            fields have no dictionary key, so the locator is the only
            traceability they will ever have (rule R-5).
        level: The level number, defaulting to the commonest. Pass `"77"` for an
            independent item [general/gl071.cbl:L149].
        inherited_usage: The class a group above the field carries, when one
            does - `Usage.COMP_3` for a field under `03  Amounts  comp-3.`
            [copybooks/wsbatch.cob:L40].
        inherited_usage_from: That group's name.
        inherited_usage_source: That group's locator.
        parent_group: The group immediately above the field.
        is_group: Whether the field has subordinates. Leave None for an
            ordinary elementary item.

    Returns:
        The `FieldDescriptor`, carrying the locator.

    Raises:
        PictureError: The locator is missing or malformed, or the composed text
            did not read as a field entry - which can only happen if `clauses`
            or `name` was not what it claimed, and the message names both so the
            mistake is obvious.
    """
    stated = clauses.strip()
    if stated.endswith("."):
        stated = stated[:-1].rstrip()
    entry = parse_entry(
        f"{level}  {name}  {_with_picture_keyword(stated)}.",
        source_locator=source_locator,
        inherited_usage=inherited_usage,
        inherited_usage_from=inherited_usage_from,
        inherited_usage_source=inherited_usage_source,
        parent_group=parent_group,
        is_group=is_group,
    )
    if entry.descriptor is None:
        raise PictureError(
            f"the declaration {level} {name} {stated!r} did not read as a field "
            f"entry: it came back as {entry.kind.value}"
            + (
                f" because {entry.unrecognised_reason}"
                if entry.unrecognised_reason
                else ""
            )
        )
    return entry.descriptor


def _with_picture_keyword(clauses: str) -> str:
    """Give a bare leading picture its `PIC` keyword, and leave anything else be.

    `"s9(7)v99 sign leading"` [copybooks/wspost-irs.cob:L21] becomes
    `"pic s9(7)v99 sign leading"`; `"binary-long value zero"`
    [sales/sl100.cbl:L182] and `"pic 99 comp value zero"`
    [sales/sl060.cbl:L223] are already well formed and are returned untouched.
    """
    if not clauses:
        return clauses
    head = clauses.split(maxsplit=1)[0].upper()
    if head in CLAUSE_KEYWORDS or head in USAGE_TOKENS:
        return clauses
    return f"pic {clauses}"
