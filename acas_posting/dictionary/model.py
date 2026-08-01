"""The data-dictionary object model: the copybook / bridge / column triple.

This module is the Python mirror of
data_dictionary/acas_posting_dictionary.schema.json. That schema is the
NORMATIVE CONTRACT and this file is its shape in code, not an independent
design: every record below declares exactly the members the schema declares,
under the same names, in the same order, with the same nullability, and every
enumeration carries exactly the schema's member set. A record that added a
member would produce documents the schema rejects, because every object in it
is closed.

Agent Action Plan section 0.4.1.6 gives this module its whole mandate,
verbatim:

    "The dictionary schema: copybook field (name, picture, usage, sign,
    scale), bridge host variable, MySQL column (name, type) - plus derivation
    notes for bridge-only columns"

The module DESCRIBES fields. It parses nothing - `generate.py` parses and
writes the artifact, `loader.py` reads it back at run time - and it holds no
accounting value of any kind. What travels through these records is picture
text, place counts, scales, SQL type names, source citations and prose.

WHAT AN ENTRY IS
================
One entry is one field seen from all three layers at once:

    copybook               what the frozen COBOL record layout declares
    bridge_host_variable   what the generated bridge program declares, and
                           the AUTHORITATIVE view
    column                 what the frozen schema dump declares

plus `drift`, which states where those views disagree, `presence` and
`one_sided`, which state which of them the field was found in at all, and
`derivation`, which states how a value comes to exist when the mapping is not
a plain field-for-field move.

THE BRIDGE IS AUTHORITATIVE, AND THE CODEBASE PROVES IT
=======================================================
The user requirement this whole package rests on, preserved verbatim in Agent
Action Plan section 0.8.2 and byte-identical to `DICTIONARY_AUTHORITY` below:

    "The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative
    record-layout ↔ table mapping - it is the data dictionary for this
    migration."

The obvious place to look for field metadata is the copybooks, and they are
not sufficient. IRSPOSTING-REC carries three columns - POST4-DAY, POST4-MONTH
and POST4-YEAR - that appear in NO copybook whatsoever. They are declared only
in the bridge, each `PIC 9(03) COMP`, at [common/irspostingMT.cbl:L177-L179],
because the bridge derives them from two-character slices of a date string
under a guard [common/irspostingMT.cbl:L982-L987]. In the frozen schema they
are `tinyint(2) unsigned NOT NULL` at ordinals 4, 5 and 6
[mysql/ACASDB.sql:L278-L280] - INTERLEAVED before POST4-DR, not appended after
the copybook's own columns. Section 0.1.1 draws the conclusion: "A migration
driven from the copybooks alone would silently omit three columns of a posting
table." Two consequences are structural, not advisory:
`DictionaryEntry.copybook` is nullable, so a bridge-derived column is
representable at all; and no view is required, so nothing here can force a
correct dictionary to be unwritable.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  THE THREE VIEWS ARE SIBLINGS. THEY ARE NEVER RECONCILED.  (rule R-4)   !!
!!                                                                         !!
!!  There is deliberately NO member anywhere in this module that names a    !!
!!  single winning type, picture, width or signedness across the views, and !!
!!  none may be added. Where the sources disagree, an entry records ALL     !!
!!  THREE views, sets the matching flags in `Drift`, and explains the       !!
!!  disagreement in `Drift.details` and `DictionaryEntry.notes`.            !!
!!                                                                         !!
!!  A DEFECT REPRODUCED IS CORRECT; A DEFECT FIXED IS A FAILURE.            !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

That last line is the user's own requirement, which section 0.8.2 preserves
verbatim - reproduced in full so it can be cited exactly rather than read
through a gutter:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a defect
    fixed is a failure."

The prohibition is not a matter of taste. The disagreements between the views
are LOAD-BEARING BEHAVIOUR:

  * `Sales-Average binary-long` is signed [copybooks/wssl.cob:L49]; the host
    variable receiving it is `PIC 9(10) COMP`, unsigned
    [common/salesMT.cbl:L308]; the column is `int(8) unsigned`. The sign is
    lost AT THE BRIDGE, before any SQL runs, and the data-access layer has to
    reproduce that conversion rather than write the computed value and let the
    database object.
  * `Ledger-Name pic x(24)` [copybooks/wsledger.cob:L27] becomes
    `HV-LEDGER-NAME PIC X(32)` [common/nominalMT.cbl:L299] and
    `LEDGER-NAME char(32)` [mysql/ACASDB.sql:L127]. The value survives; the
    padding does not, and padding is visible in a table dump.
  * The three IRS date components above have no copybook view at all.

Give an implementer one "winning type" member and it will be filled in, and
every one of those facts leaves the record. The one derived scalar this module
does carry, `DictionaryEntry.cobol_python_storage`, is documented at its
definition site as describing the COBOL side ALONE and settling nothing.

`DictionaryEntry.anomaly_refs` points into the register of the twenty-two
legacy defects this migration reproduces, and `ambiguity_refs` into the
register of questions only the compiled program can settle. Both registers -
docs/migration/anomaly-log.md and docs/migration/ambiguity-resolutions.md -
are to be written at a later boundary; the identifiers are recorded here now
so that no entry has to be revisited when they are.

WHAT THIS MODULE DOES NOT DO  (rule R-3)
========================================
It adds no check of any kind. No record here runs code of its own after being
constructed, none rejects a member, none supplies a default for a missing one,
and the compiled patterns published below are exported FOR `generate.py` AND
THE TEST SUITE TO USE - this module never applies them. Section 0.7.4 settles
the apparent tension for the whole package, verbatim: "R-3 constrains the
database, not the repository. Describing a schema in a committed artifact is
orthogonal to altering it." So the column view describes the frozen schema
exhaustively and offers no way to express a data definition statement, a
suggested width or a corrected type.

Five agreements the schema's conservative keyword subset cannot express belong
to `generate.py` and are checked by the dictionary test, NOT here: that `key`
is unique across entries; that each `Presence` flag equals whether its view is
non-null; that at least one view is non-null; that `one_sided` is the negation
of the conjunction of the three flags; and that a `derivation` is present
whenever a column exists with no copybook view.

DETERMINISM  (rule R-6)
=======================
The dictionary is committed, so regenerating it must reproduce it byte for
byte. Two properties deliver that, both argued at `_JsonRecord.to_json_obj`:
field declaration order IS the serialisation order, and every collection
member is a tuple in a frozen record.

Nothing here consults a clock, an entropy source, the process environment, the
host it runs on or installed distribution metadata, so two imports in two
processes produce identical state. `Meta` is closed against a generation date,
a host name, a user name, an absolute path and a revision identifier by the
simple fact that it declares no such member.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point. This module states that structurally rather than promising it:

  * The token naming Python's binary approximation of a real number appears
    nowhere in this file - not as an annotation, not as a cast, not as a
    default - and `JsonValue` has no member for it either, in or out.
  * Every count is `int` and every declaration is `str`, each argued at its
    own member: a count because it is dimensionless, a declaration so it
    cannot lose precision in transport.
  * `SqlBaseType` omits the three binary floating-point SQL types outright.
    The frozen dump declares none of them across all 720 of its columns, so
    they are made unrepresentable rather than merely discouraged.

The point of recording `usage` and `scale` faithfully is that
`acas_posting/cobol/field.py` selects the exact-decimal type or `int` FROM THE
DICTIONARY rather than from hand-written per-field code. It matters
concretely: the sales statistics fields are `binary-long`
[copybooks/wssl.cob:L45-L53], so their truncation on divide is integer
truncation, which is exactly what makes the legacy moving-average defect
reproducible.

NO COBOL AT RUNTIME  (rule R-1)
===============================
This module is pure declarative Python on the standard library alone -
`dataclasses`, `enum`, `re` and `typing`. It starts no child process, loads no
foreign library, names no compiler and reaches nothing outside itself. It also
imports NO sibling: `acas_posting.dictionary` is the first layer of the
migration, so this file is a leaf and does not even import its own package
marker. A JSON Schema checker is deliberately not in the pinned dependency
set, which is the second reason the schema check lives in a test.

TRACEABILITY  (rule R-5)
========================
Every view carries a REQUIRED `source` locator, whose form `SourceLocator`
defines, so a reader can jump from any member of the artifact straight to the
COBOL or SQL line that establishes it. Every entry carries a stable `key`,
cited verbatim by `acas_posting/cobol/field.py` and by all twenty-seven
modules under `acas_posting/records/`. `Presence` plus `one_sided` make
"declared in one source, absent from another" a recorded fact, so nothing
discovered in any source is ever dropped. The wider mapping - program to
module, paragraph to function, field to dictionary entry - belongs to the
traceability document a later boundary writes.

THE FREEZE
==========
The COBOL under common/ and copybooks/ and the schema dump under mysql/ are
read here only as citations in prose. Section 0.8.1, verbatim: "Any diff
touching `common/*.cbl`, `common/*.scb`, `copybooks/*.cob`, `general/*.cbl`,
`sales/*.cbl`, `purchase/*.cbl`, `irs/*.cbl` or `mysql/ACASDB.sql` is a defect
in the migration, regardless of how harmless it appears."
"""

# PROVENANCE
# Every member below is derived from one of four frozen inputs: the
# maintainer's one-way COBOL-to-MySQL bridge pairs (common/*MT.scb and
# common/*MT.cbl), the record copybooks under copybooks/, the schema dump
# mysql/ACASDB.sql, and the inline FILE SECTION record declarations of
# the General Ledger posting programs (general/gl070.cbl, general/gl071.cbl and
# general/gl072.cbl), which are the only declaration of the work files those
# phases pass data through. Those files are this module's specification and are
# never modified by it. No licence grant is stated here: the COBOL carries the
# maintainer's own notice, which is his to make and not this migration's to
# copy or replace.

import hashlib
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from enum import Enum, StrEnum
from functools import cache
from types import UnionType
from typing import (
    Any,
    Final,
    Self,
    TypeAliasType,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

#  THE JSON VALUE DOMAIN
#  The plain-tree form of the artifact, written out as a type so that the
#  numeric policy of rule R-2 is visible in the type system rather than only
#  in prose: the union below admits strings, dimensionless integers, booleans,
#  absence, arrays and objects, and it admits NOTHING ELSE. There is no member
#  for a binary approximation of a real number, in either direction of the
#  conversion, so a value that could lose precision cannot be carried by a
#  document this module builds or reads.
#  Written with the PEP 695 `type` statement because the alias is recursive
#  and lazy evaluation is what lets it refer to itself.

type JsonValue = str | int | bool | None | list[JsonValue] | dict[str, JsonValue]
"""One value of the artifact in plain-tree form. No binary-approximation member."""

type JsonObject = Mapping[str, Any]
"""One object of the artifact as decoded from JSON, before it is mapped to a record.

`Any` marks the boundary where the document is still untyped. Nothing past
that boundary coerces: a member is read and placed in its record exactly as it
was recorded, and a member that is absent raises rather than acquiring a
default (rule R-3).
"""


#  STRING DOMAINS AND THEIR PATTERNS
#  The schema constrains several string members by pattern. Each pattern is
#  published here as a compiled constant so that `generate.py` and the
#  dictionary test can hold themselves to the schema without re-reading it,
#  and so that a reader of a record can see what shape a member takes.
#
#  WHERE THESE PATTERNS ARE APPLIED, AND WHY THAT IS NOT A NEW VALIDATION.
#  `from_json_obj` on the root record - and only there - walks the decoded
#  document once and holds every member to the pattern, member set and value
#  domain recorded here, raising `DictionaryIntegrityError` on the first
#  departure. See THE INTEGRITY PASS below for the full argument; in short,
#  rule R-3 forbids new validation of the *accounting data* the migrated cycle
#  posts, while rule R-5 requires that every Python field cite a dictionary
#  entry. A citation is worth nothing if the cited document is not the document
#  the generator produced from the frozen sources, so checking the artifact's
#  own integrity is what makes R-5 mean something rather than a new rule
#  imposed on the ledger. No accounting value is examined, no posting decision
#  consults it, and a repository whose artifact is intact sees identical
#  behaviour with the pass present and absent.
#
#  Individual records still never check their own members: construction stays a
#  plain field-by-field mapping so that `generate.py` can build a record from
#  values it has just derived without paying for a check it does not need.
# =============================================================================

type RepoPath = str
"""A path relative to the repository root, forward slashes, never absolute."""

type SourceLocator = str
"""A citation into a frozen source: `<path>:L<n>` or `<path>:L<n>-L<m>` (rule R-5)."""

type EntryKey = str
"""The stable identifier of an entry. See `DictionaryEntry.key` for both forms."""

type TableName = str
"""A table name as `mysql/ACASDB.sql` declares it, upper case with hyphens."""

type BridgeName = str
"""A bridge pair's stem, lower case, ending in `MT` - for example `glpostingMT`."""

type HandlerName = str
"""A file-handler program name - `acas000` through `acas029`, or `acasirsubN`."""

_PATH_SEGMENT: Final[str] = r"[A-Za-z0-9_][A-Za-z0-9_.-]*"
"""One segment of a repository-relative path, used to build the two path
patterns below. Written as a segment rather than as a flat character class for
one reason: a segment must BEGIN with a letter, a digit or an underscore, so
`..` and `.` are not segments at all. That single restriction is what makes a
path member containable.

The consequences are worth spelling out, because each of them is a way a path
member could otherwise name a file outside the repository or name the same file
two different ways:

* `copybooks/../../etc/passwd` is rejected - a dot-dot segment cannot be built;
* `common/./salesMT.cbl` is rejected - nor can a bare-dot segment;
* `/etc/passwd` is rejected - the first character may not be a separator;
* `copybooks//wssl.cob` is rejected - an empty segment cannot be built;
* `copybooks/` is rejected - a trailing separator would leave a final segment
  empty.

Every path in the frozen sources is an ordinary relative path, so nothing the
generator legitimately records is affected: all 106 distinct path members and
all 3290 distinct citations in the artifact satisfy this shape."""

REPO_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^%s(/%s)*$" % (_PATH_SEGMENT, _PATH_SEGMENT)
)
"""Shape of every path member: one or more segments joined by single forward
slashes, relative to the repository root and CONTAINED WITHIN IT.

An absolute path would encode the machine that wrote the artifact and is
forbidden content (rule R-6), so the leading character may not be a separator.
A path that climbs out of the repository would let a member of this document
cite a file the frozen sources do not contain - and a consumer that resolved
such a citation against the repository root would read outside it - so no
segment may be `..` or `.`. See `_PATH_SEGMENT` for the full list of forms this
excludes."""

SOURCE_LOCATOR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^%s(/%s)*:L[0-9]+(-L[0-9]+)?$" % (_PATH_SEGMENT, _PATH_SEGMENT)
)
"""Shape of every `source` member: a repository-relative path, a colon, then a
single line as `L<n>` or an inclusive span as `L<n>-L<m>`.

The path half is exactly `REPO_PATH_PATTERN`, and is contained for the same
reason: a citation is the mechanism rule R-5 rests on, and a citation that can
point outside the repository is one a reader cannot check."""

ENTRY_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9-]*\.[A-Za-z0-9][A-Za-z0-9-]*(#[0-9]+)?$"
)
"""Shape of `DictionaryEntry.key`. The optional `#<n>` tail disambiguates a
field name that repeats inside one record - `filler` occurs four times in
copybooks/wsledger.cob - by appending its declaration line."""

TABLE_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9-]*$")
"""Shape of a table name."""

BRIDGE_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*MT$")
"""Shape of a bridge name."""

HANDLER_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(acas[0-9]{3}|acasirsub[0-9])$"
)
"""Shape of a handler name. Both conventions occur: the numbered handlers the
General, Sales and Purchase programs call, and the IRS subroutine handlers."""

COPYBOOK_LEVEL_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(0[1-9]|[1-4][0-9])$")
"""Shape of `CopybookField.level`: a two-character token, leading zero kept.
An 88-level condition name is NOT a level here - it is carried by
`CopybookField.condition_names` on the field it qualifies."""

HV_GROUP_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^TD-[A-Z][A-Z0-9-]*$")
"""Shape of a host-variable group name: `TD-` followed by the table name."""

HV_GROUP_SUFFIX_PATTERN: Final[re.Pattern[str]] = re.compile(r"^HV[0-9]?$")
"""Shape of a host-variable group suffix. Only two values occur across the
twenty in-scope bridges: `HV`, and `HV1` for the lines table of a two-table
bridge [common/slinvoiceMT.scb:L381-L385]."""

HV_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^HV[0-9]?-[A-Z0-9][A-Z0-9-]*$")
"""Shape of a host-variable name, prefix included and never rewritten."""

COLUMN_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")
"""Shape of a column name as it appears between backticks in the frozen dump."""

BRIDGE_KEY_TYPE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z]{3}$")
"""Shape of a bridge key-type literal. Two occur in scope: `STR`, annotated in
the source as key is string [common/glpostingMT.scb:L234], and `BNT`."""

ANOMALY_REF_PATTERN: Final[re.Pattern[str]] = re.compile(r"^A-([1-9]|1[0-9]|2[0-2])$")
"""Shape of an anomaly reference - `A-` and the register number, 1 to 22."""

AMBIGUITY_REF_PATTERN: Final[re.Pattern[str]] = re.compile(r"^Q-[0-9]+$")
"""Shape of an ambiguity reference - `Q-` and the register number."""

DECLARED_LENGTH_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9]+$")
"""Shape of one element of `CopybookSource.declared_lengths`: a digit string."""

DICTIONARY_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
"""Shape of `Meta.dictionary_version`. It advances with the dictionary's
CONTENT and carries no relation to elapsed time."""

BINDING_RULE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^R-[1-6]$")
"""Shape of `BindingRule.id` - the six rules that govern this migration."""

SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
"""Shape of a SHA-256 digest as this document records it: sixty-four lower-case
hexadecimal characters, no prefix and no separator.

Used by `SourceDigest.sha256` and by `Meta.source_inputs_sha256`, the two
members that bind this artifact to the exact bytes of the frozen inputs it was
derived from. The lower-case restriction is not cosmetic: it makes the recorded
digest comparable to a recomputed one by simple equality, with no case folding
step that could be forgotten at one of the two comparison sites.
"""


#  THE FIXED VALUES THE SCHEMA PINS WITH `const`
#  Each of these is a value the schema allows to be one thing only. They are
#  published so that `generate.py` writes them from one place and the test
#  compares against one place, which is the whole reason a `const` is worth
#  mirroring in code at all.

DICTIONARY_NAME: Final[str] = "acas_posting_dictionary"
"""`Meta.dictionary_name` - the stem shared by the artifact and its schema."""

DICTIONARY_SCHEMA_REF: Final[str] = "acas_posting_dictionary.schema.json"
"""`Meta.schema_ref` - a bare relative name, deliberately not a URL, so that
nothing ever attempts to fetch a schema over a network (rule R-1)."""

DICTIONARY_GENERATED_BY: Final[str] = "acas_posting/dictionary/generate.py"
"""`Meta.generated_by` - the only module that may produce the artifact. A
dictionary produced by anything else could not be reproduced from the frozen
sources, and reproducibility is the property being protected (rule R-6)."""

DICTIONARY_AUTHORITY: Final[str] = (
    "The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative "
    "record-layout \u2194 table mapping - it is the data dictionary for this "
    "migration."
)
"""`Meta.authority` - the user requirement the dictionary rests on, carried
verbatim and pinned so it cannot be paraphrased into something weaker. The
arrow is U+2194 LEFT RIGHT ARROW, exactly as the requirement writes it."""

DETERMINISM_ENCODING: Final[str] = "utf-8"
"""`Determinism.encoding` - how the artifact is written."""

DETERMINISM_NEWLINE: Final[str] = "LF"
"""`Determinism.newline`. A carriage-return pair would change the bytes of the
artifact while parsing identically, which is the class of difference the
determinism contract exists to eliminate."""

DETERMINISM_INDENT: Final[int] = 2
"""`Determinism.indent` - spaces per level, spaces and never tabs."""

DETERMINISM_TRAILING_NEWLINE: Final[bool] = True
"""`Determinism.trailing_newline` - exactly one, at the end of the artifact."""

DETERMINISM_BYTE_ORDER_MARK: Final[bool] = False
"""`Determinism.byte_order_mark` - a mark would change the bytes without
changing the content."""


#  ENUMERATED VOCABULARIES
#  Each one mirrors an `enum` in the schema, member for member and value for
#  value. They are `StrEnum`, so a member IS its recorded string: a consumer
#  may compare a member against the text in the artifact directly, and
#  `Usage("COMP-3")` maps the recorded text back to its member. Nothing here
#  admits a value the frozen sources do not use, which is how a vocabulary
#  becomes a structural guarantee rather than a comment.


class Usage(StrEnum):
    """The COBOL storage class in force for an item - `cobolUsage` in the schema.

    All six storage classes the in-scope record layouts actually use are kept
    distinct, because collapsing any of them changes the value that reaches the
    database. Signedness is NOT carried here: it lives in the separate `signed`
    member of each view, so `BINARY-LONG` and `BINARY-LONG UNSIGNED` share one
    usage value and differ in `signed`.

    The leading-sign display form is deliberately not a usage either. It is
    `DISPLAY` plus `SignPosition.LEADING_INCLUDED`, which is what lets the two
    spellings the copybooks use survive verbatim in `sign_clause_text`.
    """

    DISPLAY = "DISPLAY"
    """Zoned decimal - declared by the ABSENCE of any usage clause, as every
    numeric field of copybooks/wspost.cob:L13-L28 is."""

    COMP = "COMP"
    """Binary within the range the picture declares - `pic 99v99 comp`
    [copybooks/wssl.cob:L42], `pic 9(5) comp` [copybooks/wsfnctn.cob:L24], and
    at group level `05 Vat-Rates comp.` [copybooks/wssystem.cob:L55], whose
    five subordinate `pic 99v99` items inherit it."""

    COMP_3 = "COMP-3"
    """Packed decimal, declared both on the field
    [copybooks/wsledger.cob:L28] and on the group - `03 Amounts comp-3.`
    [copybooks/wsbatch.cob:L40], `03 Sales-Ledger-Data comp-3.`
    [copybooks/wssys4.cob:L9], `03 Purchase-Ledger-Data comp-3.`
    [copybooks/wssys4.cob:L20]."""

    COMP_5 = "COMP-5"
    """Native binary. It appears in bridge working storage -
    `01 subscripts usage comp-5.` [common/glpostingMT.scb:L256] - and is
    listed so that the vocabulary covers the frozen sources completely."""

    BINARY_CHAR = "BINARY-CHAR"
    """The one-byte member of the native binary family
    [copybooks/wssystem.cob:L53-L54], including the `unsigned` form at
    [copybooks/wssystem.cob:L65]."""

    BINARY_SHORT = "BINARY-SHORT"
    """The two-byte member [copybooks/wssl.cob:L43-L44]. Note that the
    maintainer's trailing comment there says `9999 comp`, which describes four
    digits while the declaration is a 16-bit integer; the declaration is
    recorded in `usage` and the comment in `notes`, and neither is corrected
    (rule R-4)."""

    BINARY_LONG = "BINARY-LONG"
    """The four-byte member [copybooks/wssl.cob:L45-L53],
    [copybooks/wsbatch.cob:L36-L39], and `Run-Date binary-long`
    [copybooks/wssystem.cob:L67]. Signed unless `unsigned` is written, which is
    why the sales statistics fields are signed and their host variables are
    not."""

    POINTER = "POINTER"
    """The `TP-` item each bridge declares beside its host-variable group -
    `01 TP-GLPOSTING-REC USAGE POINTER.` [common/glpostingMT.cbl:L280]."""

    ALPHANUMERIC = "ALPHANUMERIC"
    """`PIC X(n)`. COBOL itself classes this as usage display; the dictionary
    separates it so that `cobol_python_storage` can select text without
    re-parsing the picture."""

    GROUP = "GROUP"
    """An item with subordinate items and no picture of its own - including a
    group that carries the usage its children inherit."""


class SignPosition(StrEnum):
    """Where the sign of a signed item lives - `signPosition` in the schema.

    Kept separate from `Usage` because one usage carries different sign
    placements, and because the placement is what a consumer needs in order to
    read or write the field's bytes.
    """

    NONE = "NONE"
    """The item is unsigned."""

    TRAILING_INCLUDED = "TRAILING_INCLUDED"
    """The COBOL default for a signed display item written `S9(n)V9(m)` with no
    sign clause: the sign overpunches the last digit
    [copybooks/wspost.cob:L23]."""

    LEADING_INCLUDED = "LEADING_INCLUDED"
    """The `SIGN LEADING` form. Two in-scope copybooks use it and they spell it
    differently - `sign leading` [copybooks/wspost-irs.cob:L21] and
    [copybooks/wspost-irs.cob:L25], against `sign is leading`
    [copybooks/irswspost.cob:L14] and [copybooks/irswspost.cob:L18]. Both
    spellings are preserved verbatim in `sign_clause_text` (rule R-4)."""

    LEADING_SEPARATE = "LEADING_SEPARATE"
    """The `SIGN LEADING SEPARATE CHARACTER` form, listed for completeness of
    the vocabulary."""

    TRAILING_SEPARATE = "TRAILING_SEPARATE"
    """The `SIGN TRAILING SEPARATE CHARACTER` form, likewise."""

    IMPLICIT_BINARY = "IMPLICIT_BINARY"
    """The sign of a signed `COMP`, `COMP-3`, `COMP-5` or binary-family item,
    where it is part of the packed or binary representation rather than a
    character position."""


class UsageDeclaredAt(StrEnum):
    """Where the generator found the usage it recorded - `usageDeclaredAt`.

    This is the highest-risk fact in the whole dictionary, and it is not
    decoration. COBOL lets a group declare usage and every subordinate item
    inherit it: `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40] governs the
    four amount fields at [copybooks/wsbatch.cob:L41-L44], which carry no usage
    on their own picture lines, and the two period-total groups
    [copybooks/wssys4.cob:L9] and [copybooks/wssys4.cob:L20] govern twenty
    more at [copybooks/wssys4.cob:L10-L19] and
    [copybooks/wssys4.cob:L21-L30]. Twenty-four money fields inherit their
    storage class, and a generator that read usage only from the picture line
    would class every batch amount and every period total as zoned decimal -
    so every stored value would be wrong.

    Recording the provenance forces the generator to prove that it looked.
    """

    FIELD = "FIELD"
    """The usage clause is on the item's own declaration."""

    GROUP = "GROUP"
    """The usage was inherited from an ancestor group, which
    `usage_inherited_from` names and `usage_group_source` cites."""

    DEFAULT = "DEFAULT"
    """No usage clause governs the item anywhere, so COBOL's own default of
    zoned display applies."""


class CobolPythonStorage(StrEnum):
    """The Python type for the COBOL-side value - `cobolPythonStorage`.

    READ ALL OF THIS BEFORE USING IT. The value is derived SOLELY from the
    copybook view's `usage` and `scale`, by the rule recorded in
    `DerivationRules.cobol_python_storage`. It describes THE COBOL SIDE ALONE.

    It is NOT a settlement of any disagreement between the three views, and it
    must never be read in place of them: the bridge view and the column view
    keep their own independent `usage`, `digits`, `scale` and signedness, and
    anything that needs to know what the bridge or the database does has to
    read those views (rule R-4).

    It exists for one reason only - rule R-2 requires that the choice between
    the exact-decimal type and `int` be data-driven rather than hand-coded per
    field, so that `acas_posting/cobol/field.py` can select the type from the
    dictionary.
    """

    DECIMAL = "DECIMAL"
    """Any numeric item with a non-zero scale, and packed or zoned money.
    Carried in Python by the exact type of the `decimal` module, never by a
    binary approximation (rule R-2)."""

    INT = "INT"
    """The binary integer family and zero-scale integers. This is the value
    that makes the legacy moving-average defect reproducible: the sales
    statistics fields are `binary-long` [copybooks/wssl.cob:L45-L53], so their
    truncation on divide is integer truncation."""

    STR = "STR"
    """An alphanumeric item."""

    NONE = "NONE"
    """A group item, or an entry that has no copybook view at all - as the three
    bridge-derived IRS date components do not."""


class SqlBaseType(StrEnum):
    """A column's SQL base type, width and unsigned suffix removed.

    The vocabulary is exactly the seven base types the frozen dump uses and no
    others. The three binary floating-point SQL types are OMITTED, which makes
    a binary floating-point column unrepresentable rather than merely
    discouraged: the dump declares none of them across all 720 of its columns,
    and rule R-2 forbids one outright.
    """

    DECIMAL = "DECIMAL"
    """Exact-decimal storage. Every monetary column in the posting cycle is one
    of these - `POST-AMOUNT decimal(10,2)` [mysql/ACASDB.sql:L163] - which is
    why the driver must materialise them as exact values."""

    INT = "INT"
    """A four-byte integer column - `int(8) unsigned` [mysql/ACASDB.sql:L123]."""

    TINYINT = "TINYINT"
    """A one-byte integer column - `tinyint(2) unsigned`
    [mysql/ACASDB.sql:L278]."""

    SMALLINT = "SMALLINT"
    """A two-byte integer column."""

    MEDIUMINT = "MEDIUMINT"
    """A three-byte integer column - `mediumint(5) unsigned`
    [mysql/ACASDB.sql:L155]."""

    BIGINT = "BIGINT"
    """An eight-byte integer column - `bigint(10) unsigned`
    [mysql/ACASDB.sql:L156]. A SIGNED one occurs too, `bigint(11)` with no
    unsigned suffix [mysql/ACASDB.sql:L367], so `unsigned` is genuinely per
    column and not a property of the base type."""

    CHAR = "CHAR"
    """A fixed-width character column - `char(32)` [mysql/ACASDB.sql:L127].
    Trailing padding is significant when two table states are compared, which
    is why the state normaliser evens it out."""


class DerivationKind(StrEnum):
    """How a column's value comes to exist - `derivation.kind` in the schema."""

    BRIDGE_DERIVED = "BRIDGE_DERIVED"
    """The bridge computes the value from other record data. This is how
    IRSPOSTING-REC acquires POST4-DAY, POST4-MONTH and POST4-YEAR - three
    columns with no counterpart in any copybook, derived under a guard at
    [common/irspostingMT.cbl:L982-L987]."""

    GROUP_CONCATENATION = "GROUP_CONCATENATION"
    """A copybook group is moved whole into one host variable and hence one
    column, as the two five-digit children of `WS-Post-Key`
    [copybooks/wspost.cob:L14-L16] are moved into `HV-POST-KEY PIC 9(18) COMP`
    [common/glpostingMT.cbl:L283] at [common/glpostingMT.cbl:L1054]."""

    REDEFINES_ALTERNATIVE = "REDEFINES_ALTERNATIVE"
    """The column corresponds to a redefines view of the storage rather than to
    the original declaration, as with the eight-digit redefinition of the
    ledger key group [copybooks/wsledger.cob:L21-L22]."""


class EntityFacade(StrEnum):
    """The entity facade the posting programs address a table through.

    The names are the maintainer's own, taken from the twenty-one-entity facade
    blueprint copybooks/Proc-ACAS-FH-Calls.cob, and they are recorded exactly
    as he writes them - spaces, hyphens and abbreviations included. Twenty of
    the twenty-one reach an in-scope table.
    """

    SYSTEM = "System"
    """System record, reached through `acas000` with file-key number 1."""

    SYSTEM_DEFAULTS = "System defaults"
    """System defaults record, `acas000` with file-key number 2."""

    SYSTEM_FINAL = "System final"
    """System final-accounts record, `acas000` with file-key number 3."""

    SYSTEM_TOTALS = "System totals"
    """System period-totals record, `acas000` with file-key number 4."""

    GL_NOMINAL = "GL-Nominal"
    """The nominal ledger."""

    GL_POSTING = "GL-Posting"
    """The General Ledger posting file."""

    GL_BATCH = "GL-Batch"
    """The batch header file."""

    SPL_POSTING = "SPL-Posting"
    """The Sales and Purchase transfer file that feeds IRS. Its record layout
    copybooks/wspost-irs.cob:L6-L7 says in as many words that it "is NOT the
    same as the internal IRS posting file"."""

    SALES = "Sales"
    """The sales ledger."""

    VALUE = "Value"
    """The value-analysis file."""

    ANALYSIS = "Analysis"
    """The analysis-code file."""

    INVOICE = "Invoice"
    """The sales invoice header and lines pair."""

    OTM3 = "OTM3"
    """The sales open-item file."""

    PURCH = "Purch"
    """The purchase ledger."""

    PINVOICE = "PInvoice"
    """The purchase invoice header and lines pair."""

    OTM5 = "OTM5"
    """The purchase open-item file."""

    IRS_NOMINAL = "IRS nominal"
    """The IRS nominal ledger."""

    IRS_DEFAULTS = "IRS defaults"
    """The IRS defaults record."""

    IRS_POSTING = "IRS posting"
    """The internal IRS posting file."""

    IRS_FINAL = "IRS final"
    """The IRS final-accounts record."""


#  SERIALISATION - THE DETERMINISM CONTRACT IN CODE  (rule R-6)
#  `_JsonRecord` gives every record below one shared way out to the plain-tree
#  form, and that one way is driven by `dataclasses.fields()`, which yields
#  members in DECLARATION ORDER. Because every record declares its members in
#  the order the JSON Schema declares them, the emitted object order is the
#  schema's order by construction. Nothing sorts, and `sort_keys=True` is
#  never needed - passing it would produce a valid but byte-different file and
#  break the reproducibility the committed artifact depends on.
#  The base carries no members of its own and an empty `__slots__`, so a
#  subclass declared with `slots=True` gains no instance dictionary from it.
#  It is behaviour, not data: it cannot appear in the artifact.


class _JsonRecord:
    """Shared plain-tree conversion for every record in this module.

    Not part of the artifact and not a member of anything: it exists so that
    the declaration-order rule is written once rather than reimplemented on
    twenty-two records, each of which could then drift from the schema
    independently.
    """

    __slots__ = ()

    def to_json_obj(self) -> dict[str, JsonValue]:
        """Return this record as a plain object, members in declaration order.

        Enumeration members become their recorded string, nested records become
        nested objects, tuples become arrays, and `None` becomes JSON null. The
        result contains only the members the schema declares for this record,
        because a frozen record has no room for anything else.
        """
        return _record_to_json_obj(self)


def _record_to_json_obj(record: _JsonRecord) -> dict[str, JsonValue]:
    """Convert one record to a plain object, walking its declared members in order.

    `dataclasses.fields()` is the whole determinism mechanism here: it yields
    the members in the order they were declared, which is the order the JSON
    Schema declares them in its own `properties` block.
    """
    # Every concrete subclass of `_JsonRecord` in this module is a frozen
    # dataclass, so `fields()` always has a dataclass to walk.
    return {
        member.name: _json_value(getattr(record, member.name))
        for member in fields(record)
    }


def _json_value(value: object) -> JsonValue:
    """Convert one member value to its plain-tree form.

    The enumeration test comes FIRST and deliberately so: every enumeration
    here is a `StrEnum`, so its members are also strings, and testing for a
    string first would emit the member object rather than its value.
    """
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, _JsonRecord):
        return _record_to_json_obj(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    # What remains is already one of the JSON scalars this module admits - text,
    # a dimensionless count, a flag or absence. The cast states that in the type
    # system and does nothing at run time; no value is converted, widened or
    # rounded on the way out (rules R-2 and R-3).
    return cast(JsonValue, value)


#  THE COPYBOOK VIEW - the first of the three siblings


@dataclass(frozen=True, slots=True)
class ConditionName(_JsonRecord):
    """One 88-level condition name declared on a copybook field.

    `acas_posting/cobol/condition_names.py` turns each of these into a
    predicate over its record, because the posting cycle tests the NAMES rather
    than raw values: the batch statuses at [copybooks/wsbatch.cob:L26-L32] gate
    the whole posting flow, and the three-state IRS fan-out switch at
    [copybooks/wssystem.cob:L179-L181] decides which tables a run touches at
    all.

    Attributes:
        name: The condition name exactly as declared, its case preserved -
            `Status-Open`, `Waiting`, `GL-Batch`, `IRS-Used`, `IRS-Both-Used`.
        value: The value-clause text exactly as written, INCLUDING the
            figurative-constant spelling where one is used, and always text
            rather than a number. Two reasons: rule R-2 keeps a number out of
            any member where precision could be lost, and rule R-4 forbids
            normalising a source. [copybooks/wssl.cob:L27] writes `value zero`
            where [copybooks/wsbatch.cob:L26] writes `value 0` for the same
            idea, and both are recorded as they stand. A quoted literal keeps
            its quotes, so a one-character switch such as `"Y"` or `"B"` is
            unambiguous.
        source: The copybook line that declares the condition name.
    """

    name: str
    value: str
    source: SourceLocator

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one condition name from its recorded object.

        Reads exactly the members the schema declares. A member that is absent
        raises rather than acquiring a default, because a silently defaulted
        member would be an assertion about a frozen source that the source
        never made (rule R-3).
        """
        return cls(
            name=obj["name"],
            value=obj["value"],
            source=obj["source"],
        )


@dataclass(frozen=True, slots=True)
class CopybookField(_JsonRecord):
    """THE COPYBOOK VIEW: the field as the frozen COBOL record layout declares it.

    Every member records what the copybook SAYS, never what it ought to say. A
    picture that disagrees with the host variable or the column stays exactly as
    declared, and the disagreement is flagged in `DictionaryEntry.drift`
    instead (rule R-4).

    `DictionaryEntry.copybook` is nullable, and null is the correct value for a
    column the bridge derives with no copybook counterpart - which is why this
    view is a separate record rather than a set of members on the entry.

    THIS RECORD SERVES A SECOND MEMBER TOO. `DictionaryEntry.program_source`
    carries the same type, because a COBOL data declaration has one shape
    wherever it is written and a work-file record declared inline in a program's
    FILE SECTION has exactly the members below. The type is REUSED
    rather than cloned so the two cannot drift apart in either direction; which
    member a given record is reached through is told by `presence`, and the
    record itself says so as well, since `file` names the declaring source and a
    program is not a copybook. Nothing here treats the two differently.

    Attributes:
        file: The source that declares the field. A copybook for the copybook
            view, for example `copybooks/wsledger.cob`; a program for the
            program-source view, for example `general/gl071.cbl`.
        source: The line or span in that file where it is declared.
        name: The data-name exactly as declared, mixed case preserved.
            `filler` is recorded under its own name with `is_filler` true
            rather than dropped, because it consumes record positions.
        level: The level number as written, leading zero kept, because a level
            is a two-character COBOL token and not an arithmetic quantity. All
            four levels the in-scope layouts use occur: `01` on a record, `03`
            and `05` on subordinate items, and `07` inside a nested redefines
            such as [copybooks/wsledger.cob:L17-L18].
        picture: The picture clause exactly as written, lower case preserved,
            or null when the item has none. Null is not an omission: a group
            item has no picture, and
            `05 Scycle Redefines cyclea binary-char`
            [copybooks/wssystem.cob:L63] declares a usage with no picture at
            all, so `picture` has to be nullable independently of `usage`.
        usage: The storage class in force, whether declared on the item or
            inherited from a group. Never null, so that
            `acas_posting/cobol/field.py` can choose its Python type from data
            alone (rule R-2).
        usage_declared_at: Whether that usage was on the item, inherited from
            an ancestor group, or left to COBOL's own default.
        usage_inherited_from: The ancestor group whose usage clause the item
            inherits, or null when nothing is inherited. `Amounts` for the four
            batch amount fields [copybooks/wsbatch.cob:L40];
            `Sales-Ledger-Data` or `Purchase-Ledger-Data` for the twenty
            period-total fields [copybooks/wssys4.cob:L9],
            [copybooks/wssys4.cob:L20].
        usage_group_source: The line that declares the inherited usage clause,
            or null. Citing the group line separately from the field line is
            what lets a reviewer confirm the inheritance instead of taking it
            on trust.
        signed: Whether the copybook declares the item signed - an `S` in the
            picture, or a binary-family item without `unsigned`. Load-bearing:
            `Sales-Average binary-long` [copybooks/wssl.cob:L49] is signed and
            the host variable that receives it is not, so the sign is lost
            before any SQL runs.
        sign_position: Where the sign sits for a signed item, or `NONE`.
            Recorded for every field so that no consumer has to infer it.
        sign_clause_text: The sign clause exactly as spelled, or null when the
            item declares none. Kept verbatim because the two in-scope
            copybooks that use the leading form spell it differently -
            `sign leading` [copybooks/wspost-irs.cob:L21] against
            `sign is leading` [copybooks/irswspost.cob:L14] - and rule R-4
            requires the difference be preserved rather than smoothed away.
        digits: Total decimal digit positions the picture declares, integer plus
            fractional, excluding any sign and the implied decimal point. Null
            only where there is no numeric picture. A dimensionless count
            (rule R-2).
        integer_digits: Digit positions left of the implied decimal point, so
            that `digits` minus `integer_digits` is `scale`. Recorded rather
            than computed, so a widening such as the copybook's nine integer
            digits [copybooks/wsbatch.cob:L41] against the host variable's
            twelve [common/glbatchMT.cbl:L291] is directly comparable.
        scale: Digit positions right of the implied decimal point - the `V` in
            the picture. Zero is a real and important value and not a missing
            one: the moving-average accumulators the Sales and Purchase
            programs maintain are declared with no decimal places while the
            amounts added into them carry two, which is what makes the legacy
            double truncation reproducible.
        character_length: Declared length in characters for an alphanumeric
            item, or the stated byte length of a group; null for a numeric
            item. Compared across views to expose padding drift, as with the
            twenty-four characters of [copybooks/wsledger.cob:L27] against the
            thirty-two of [common/nominalMT.cbl:L299].
        redefines: The data-name this item redefines, or null. Never dropped:
            the redefinition is frequently how a record is actually addressed,
            as with `WS-Ledger-Key9` over the ledger key group
            [copybooks/wsledger.cob:L21-L22], which is the form the bridge and
            the column correspond to.
        occurs: The occurs count for a table item, or null. Recorded because
            the quarter arrays are addressed both by name and by subscript -
            [copybooks/wsledger.cob:L36] and [copybooks/wssl.cob:L62] both
            redefine four named quarters as a four-element table - and because
            one program indexes such an array with an unbounded subscript, a
            defect to be reproduced rather than guarded.
        is_filler: True when the item is declared as `filler`. Filler entries
            are kept: they explain the gaps between a copybook layout and a
            column list, and dropping them would break the byte accounting that
            the declared record lengths are read against.
        is_group: True when the item has subordinate items and therefore no
            picture of its own. A group can still map to a single column - the
            two five-digit children of `WS-Post-Key`
            [copybooks/wspost.cob:L14-L16] are moved as one group into one host
            variable - in which case the entry carries a `Derivation` of kind
            `GROUP_CONCATENATION`.
        parent_group: The immediately containing group item, or null for the
            01-level record itself. This is what makes an inherited usage
            checkable against the group that declared it, and it is what
            records anomaly A-20 without renaming anything: `sl4-spare3` and
            `sl4-spare4` [copybooks/wssys4.cob:L29-L30] carry the Sales prefix
            inside `Purchase-Ledger-Data`, and both names are preserved exactly
            as the maintainer wrote them.
        condition_names: Every 88-level condition name declared on the field, in
            declaration order; empty for the great majority. Never summarised
            into a single flag: the IRS fan-out switch carries two condition
            names over a three-state field
            [copybooks/wssystem.cob:L179-L181], and both, plus the unnamed
            space state, change which tables a run writes to.
    """

    file: RepoPath
    source: SourceLocator
    name: str
    level: str
    picture: str | None
    usage: Usage
    usage_declared_at: UsageDeclaredAt
    usage_inherited_from: str | None
    usage_group_source: SourceLocator | None
    signed: bool
    sign_position: SignPosition
    sign_clause_text: str | None
    digits: int | None
    integer_digits: int | None
    scale: int | None
    character_length: int | None
    redefines: str | None
    occurs: int | None
    is_filler: bool
    is_group: bool
    parent_group: str | None
    condition_names: tuple[ConditionName, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the copybook view from its recorded object.

        The three enumerated members - `usage`, `usage_declared_at` and
        `sign_position` - are mapped back through their own vocabularies, so a
        value the frozen sources never use cannot enter a record here.
        Everything else is placed exactly as recorded.
        """
        return cls(
            file=obj["file"],
            source=obj["source"],
            name=obj["name"],
            level=obj["level"],
            picture=obj["picture"],
            usage=Usage(obj["usage"]),
            usage_declared_at=UsageDeclaredAt(obj["usage_declared_at"]),
            usage_inherited_from=obj["usage_inherited_from"],
            usage_group_source=obj["usage_group_source"],
            signed=obj["signed"],
            sign_position=SignPosition(obj["sign_position"]),
            sign_clause_text=obj["sign_clause_text"],
            digits=obj["digits"],
            integer_digits=obj["integer_digits"],
            scale=obj["scale"],
            character_length=obj["character_length"],
            redefines=obj["redefines"],
            occurs=obj["occurs"],
            is_filler=obj["is_filler"],
            is_group=obj["is_group"],
            parent_group=obj["parent_group"],
            condition_names=tuple(
                ConditionName.from_json_obj(item) for item in obj["condition_names"]
            ),
        )


#  THE BRIDGE VIEW - the second sibling, and the authoritative one


@dataclass(frozen=True, slots=True)
class BridgeHostVariable(_JsonRecord):
    """THE BRIDGE VIEW: the host variable the generated bridge program declares.

    This is the layer at which the record layout is actually mapped onto the
    table, and the user requirement quoted in `DICTIONARY_AUTHORITY` makes it
    the authoritative one.

    The conversion this layer performs is NOT transparent and has to be
    reproduced by the data-access layer rather than left to the database: a
    value declared signed in the copybook can arrive at an unsigned host
    variable and lose its sign before any SQL executes
    [copybooks/wssl.cob:L49] against [common/salesMT.cbl:L308].

    Attributes:
        file: The generated bridge program that declares the host variable, for
            example `common/glpostingMT.cbl`. The generated program is cited
            rather than the bridge source because the host-variable group is
            materialised there; the bridge source is cited separately in
            `BridgeSource` for the table directive and the key metadata.
        source: The line in that program where the host variable is declared.
        hv_group_name: The 01-level group containing it - `TD-` followed by the
            table name. Each bridge declares a matching `TP-` pointer item
            beside it [common/glpostingMT.cbl:L280-L281].
        hv_group_suffix: The suffix the bridge's own table directive assigns
            that group, which is what tells the groups apart when one bridge
            serves two tables. Only `HV` and `HV1` occur across the twenty
            in-scope bridges [common/slinvoiceMT.scb:L381-L385].
        name: The host-variable name exactly as declared, upper case, prefix
            included and never rewritten.
        picture: The host variable's picture and usage text as the bridge
            declares it. Text, never a number (rule R-2).
        usage: Its storage class. In practice the bridges declare numeric host
            variables as binary and character ones as `PIC X(n)`, so a copybook
            item stored as packed decimal or as a leading-sign zoned field
            changes representation at this boundary - which
            `DictionaryEntry.drift.usage` records.
        signed: Whether the host-variable picture carries an `S`. This is the
            member that exposes the narrowing: nine signed binary-long
            statistics fields [copybooks/wssl.cob:L45-L53] arrive at unsigned
            host variables [common/salesMT.cbl:L304-L312], and four signed
            batch date fields [copybooks/wsbatch.cob:L36-L39] arrive at
            unsigned host variables [common/glbatchMT.cbl:L287-L290]. The
            dictionary states both facts and settles neither (rule R-4).
        digits: Total declared digit positions, or null for a character host
            variable.
        integer_digits: Digit positions left of the implied decimal point, or
            null. Comparing this against the copybook view is how digit
            widening is detected.
        scale: Digit positions right of the implied decimal point, or null.
        character_length: Declared length for a `PIC X(n)` host variable, or
            null for a numeric one.
        loaded_from_record: Whether the load section actually moves the record
            field into this host variable before a write. FALSE IS A REAL AND
            DELIBERATE VALUE: [common/glpostingMT.cbl:L281-L295] declares
            fourteen host variables while the load section moves only thirteen
            [common/glpostingMT.cbl:L1054-L1066] - `HV-POST-RRN`
            [common/glpostingMT.cbl:L282] is never loaded, yet it is read in
            the fetch list [common/glpostingMT.cbl:L538], it is written into
            the insert [common/glpostingMT.cbl:L1120-L1126], and `POST-RRN` is
            the table's primary key [mysql/ACASDB.sql:L169]. The bridge source
            records the maintainer's own uncertainty about it verbatim at
            [common/glpostingMT.scb:L229]. Both facts are recorded and flagged;
            neither is settled here (rules R-4 and R-6).
        load_source: The line of the load section that performs that move, or
            null when there is none.
        unloaded_to_record: Whether the unload section moves the host variable
            back into the record after a read. False for a bridge-derived
            column: the three IRS date components are loaded on write and never
            unloaded, because the record has nowhere to put them, and the
            bridge says so at [common/irspostingMT.cbl:L1017-L1018].
        unload_source: The line of the unload section that performs that move,
            or null when there is none.
        group_initialised_before_load: Whether the bridge issues an initialise
            over the whole host-variable group before its first move, as every
            in-scope bridge does [common/glpostingMT.cbl:L1053],
            [common/irspostingMT.cbl:L966]. This is why an unset field reaches
            the database as zero or space rather than as SQL null, and
            therefore why every column in the frozen schema can be declared not
            null and why the data-access layer must default a value rather than
            omit the column.
    """

    file: RepoPath
    source: SourceLocator
    hv_group_name: str
    hv_group_suffix: str
    name: str
    picture: str
    usage: Usage
    signed: bool
    digits: int | None
    integer_digits: int | None
    scale: int | None
    character_length: int | None
    loaded_from_record: bool
    load_source: SourceLocator | None
    unloaded_to_record: bool
    unload_source: SourceLocator | None
    group_initialised_before_load: bool

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the bridge view from its recorded object."""
        return cls(
            file=obj["file"],
            source=obj["source"],
            hv_group_name=obj["hv_group_name"],
            hv_group_suffix=obj["hv_group_suffix"],
            name=obj["name"],
            picture=obj["picture"],
            usage=Usage(obj["usage"]),
            signed=obj["signed"],
            digits=obj["digits"],
            integer_digits=obj["integer_digits"],
            scale=obj["scale"],
            character_length=obj["character_length"],
            loaded_from_record=obj["loaded_from_record"],
            load_source=obj["load_source"],
            unloaded_to_record=obj["unloaded_to_record"],
            unload_source=obj["unload_source"],
            group_initialised_before_load=obj["group_initialised_before_load"],
        )


#  THE COLUMN VIEW - the third sibling


@dataclass(frozen=True, slots=True)
class MysqlColumn(_JsonRecord):
    """THE COLUMN VIEW: the column as the frozen schema dump declares it.

    The schema is frozen, so this view DESCRIBES it and never proposes a change
    to it. That is why there is no member here for a suggested type, a widened
    field or a data definition statement of any kind: there is nowhere in a
    conforming document to write one down (rule R-3).

    Attributes:
        file: The frozen schema file that declares the column - in practice
            always `mysql/ACASDB.sql`, the only schema file the posting cycle
            touches.
        source: The line of the table declaration where the column appears.
        name: The column name exactly as it stands between backticks in the
            dump, upper case with hyphens. Because a hyphen is not a bare
            identifier character in SQL, every reference to it has to be
            quoted; the dictionary stores the bare name and leaves quoting to
            the data-access layer.
        sql_type: The column's type text copied verbatim, display width and
            unsigned suffix included, nullability and comment excluded because
            those have their own members. Verbatim so that no re-rendering can
            silently change a width or a scale, and text rather than a
            structured number because rule R-2 keeps a number out of any
            member where precision could be lost.
        base_type: The base type with the width and the unsigned suffix
            removed. The vocabulary omits the three binary floating-point
            types, which makes such a column unrepresentable (rule R-2).
        display_width: The parenthesised width of an integer type, the
            precision of an exact-decimal type, or the character count of a
            fixed-width text type; null only where the dump declares no width.
            On the integer types this is a rendering hint and not a range
            constraint, which is precisely why the dictionary records it as
            declared and derives nothing from it.
        scale: The second parenthesised argument of an exact-decimal type - the
            digits kept to the right of the point - or null for any other type.
            Zero occurs and is meaningful, so a null scale and a zero scale are
            different facts.
        unsigned: Whether the declaration carries the unsigned suffix. Compared
            against the copybook and bridge views to expose the signedness
            drift that costs a negative value its sign. Genuinely per column: a
            signed eight-byte primary key occurs at
            [mysql/ACASDB.sql:L367].
        nullable: Whether the column permits SQL null. All 720 columns of the
            frozen dump are declared not null, so this normally carries false
            throughout; the member exists because that is an observation about
            the schema and not an assumption the dictionary is entitled to bake
            in.
        column_default: The text of the column's default clause exactly as
            written, or null when it declares none. Recording it changes
            nothing and proposes nothing (rule R-3): it is the only way a
            conforming document can preserve the one default the frozen dump
            declares, at [mysql/ACASDB.sql:L1219], since `sql_type` carries the
            type alone and `nullable` the nullability alone.
        is_primary_key: Whether the column is the table's primary key. Each of
            the 22 in-scope tables has a single-column primary key and no
            secondary index at all, which is what makes an ordering-normalised
            table dump deterministic with a plain ordering on this column and
            no tie-breaking.
        ordinal: The column's one-based position within its table declaration.
            This is the sort key that fixes entry order inside a table, so it is
            what makes the committed artifact reproducible; see
            `Determinism.array_order`. It also carries a fact a positional
            reading would otherwise miss: the three bridge-derived IRS date
            components sit at ordinals 4, 5 and 6
            [mysql/ACASDB.sql:L278-L280], interleaved rather than appended.
        comment: The text of the column's comment clause without its quotes, or
            null. Fifteen columns in the frozen dump carry one and they are
            load-bearing rather than decorative: `POST-RRN` is annotated
            `Rel. replacement` at [mysql/ACASDB.sql:L155], which records that
            the column replaced relative-file processing and explains why the
            bridge treats it differently from every other host variable.
    """

    file: RepoPath
    source: SourceLocator
    name: str
    sql_type: str
    base_type: SqlBaseType
    display_width: int | None
    scale: int | None
    unsigned: bool
    nullable: bool
    column_default: str | None
    is_primary_key: bool
    ordinal: int
    comment: str | None

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the column view from its recorded object."""
        return cls(
            file=obj["file"],
            source=obj["source"],
            name=obj["name"],
            sql_type=obj["sql_type"],
            base_type=SqlBaseType(obj["base_type"]),
            display_width=obj["display_width"],
            scale=obj["scale"],
            unsigned=obj["unsigned"],
            nullable=obj["nullable"],
            column_default=obj["column_default"],
            is_primary_key=obj["is_primary_key"],
            ordinal=obj["ordinal"],
            comment=obj["comment"],
        )


#  WHAT THE THREE VIEWS SAY TOGETHER - presence, drift and derivation


@dataclass(frozen=True, slots=True)
class Presence(_JsonRecord):
    """Which of the four sources a field was found in.

    This is where the one-sided rule lives: a field discovered in any source is
    never dropped from the dictionary, so a field that exists in only one place
    is recorded with the other views null and its ABSENCE STATED rather
    than implied (rule R-5).

    Two agreements bind these flags and are the generator's to keep - each flag
    equals whether its view is non-null, and at least one view is non-null,
    since an entry with all four null would describe no field in any layer.
    Neither is enforced here (rule R-3).

    THREE OF THE FOUR ARE THE AUTHORITATIVE TRIPLE; the fourth is a declaration
    site the triple cannot reach. `in_copybook`, `in_bridge` and `in_column` are
    the copybook / bridge / column views, and `one_sided` is computed from those
    three alone, because they are the three layers a stored value passes
    through. `in_program_source` marks a field COBOL declares inline in a
    program's FILE SECTION instead of in a copybook - a work-file record
    that never reaches a table, and therefore never reaches a bridge or a
    column either. Such a field is one-sided by construction.

    Attributes:
        in_copybook: True when a copybook declares the field. False for a
            column the bridge derives with no copybook counterpart, of which
            IRSPOSTING-REC has three [common/irspostingMT.cbl:L177-L179], and
            false for a program-source field, which no copybook declares.
        in_bridge: True when a bridge declares a host variable for it. False for
            a copybook-only field such as a filler, a redefines alternative, or
            a subordinate item the bridge carries only as part of its parent
            group.
        in_column: True when the frozen schema declares a column for it.
        in_program_source: True when a program's own FILE SECTION
            declares the field - the General Ledger work files `pretrans.tmp`
            and `postrans.tmp` and the sort file that carries them between
            phases, declared inline in [general/gl070.cbl], [general/gl071.cbl]
            and [general/gl072.cbl] and named as work files at
            [copybooks/wsnames.cob:L14-L17]. These records are transient
            scratch storage, so nothing about them is in the schema and nothing
            about them appears in a table dump - but every one of their fields
            still has a picture clause, a usage and a width that the migrated
            code must reproduce exactly, which is why they are catalogued here
            rather than typed by hand at the point of use (rule R-5).
    """

    in_copybook: bool
    in_bridge: bool
    in_column: bool
    in_program_source: bool

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the presence flags from their recorded object."""
        return cls(
            in_copybook=obj["in_copybook"],
            in_bridge=obj["in_bridge"],
            in_column=obj["in_column"],
            in_program_source=obj["in_program_source"],
        )


@dataclass(frozen=True, slots=True)
class Drift(_JsonRecord):
    """Where the views disagree: one flag per kind of disagreement, plus the specifics.

    THIS RECORD IS HOW RULE R-4 IS HONOURED STRUCTURALLY. Because no member
    anywhere in an entry names a single winning type, a generator cannot quietly
    reconcile the views; the only thing it can do with a disagreement is state
    it here.

    Every entry carries a `Drift` even when every flag is false, because the
    absence of drift is a recorded fact and not a missing one - a false is an
    assertion that the views were compared and found to agree, not that nobody
    looked.

    A flag is set by COMPARING the views actually present, never by matching a
    field name against a list of known cases: the signedness narrowing occurs in
    at least two different bridges - [common/salesMT.cbl:L304-L312] and
    [common/glbatchMT.cbl:L287-L290] - so a hard-coded list would have found one
    and missed the other.

    Attributes:
        signedness: True when the views disagree about whether the value is
            signed. The consequence is real: a signed binary-long copybook field
            feeding an unsigned host variable and an unsigned column loses its
            sign AT THE BRIDGE, so the data-access layer has to reproduce that
            conversion rather than write the computed value and let the database
            object.
        usage: True when the storage class changes between views - a
            leading-sign zoned field in the copybook
            [copybooks/irswspost.cob:L14], a binary host variable in the bridge
            and an exact-decimal column in the database are three
            representations of one value.
        digits: True when the total or integer digit count differs, as with the
            batch amount fields declared with nine integer digits in the
            copybook [copybooks/wsbatch.cob:L41] and twelve in both the host
            variable [common/glbatchMT.cbl:L291] and the column.
        scale: True when the number of fractional digits differs. Kept apart
            from `digits` because a scale difference changes rounding and
            truncation behaviour rather than range.
        character_length: True when the declared character length differs, as
            with the ledger name at twenty-four characters in the copybook
            [copybooks/wsledger.cob:L27] and thirty-two in both the host
            variable [common/nominalMT.cbl:L299] and the column
            [mysql/ACASDB.sql:L127]. The value is not corrupted but the padding
            is, and padding is visible in a table dump.
        name: True when the copybook data-name, the host-variable name with its
            prefix removed, and the column name are not all one identifier. All
            three names are always recorded independently in their own views, so
            this flag is a convenience for readers and reports and never a
            substitute for them.
        details: One short sentence per disagreement, naming the views involved
            and what each of them says, so the record reads without
            cross-referencing three files. Empty when no flag is set. This is
            the place to state a divergence plainly; it is not a place to argue
            for a correction.
    """

    signedness: bool
    usage: bool
    digits: bool
    scale: bool
    character_length: bool
    name: bool
    details: tuple[str, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the drift record from its recorded object."""
        return cls(
            signedness=obj["signedness"],
            usage=obj["usage"],
            digits=obj["digits"],
            scale=obj["scale"],
            character_length=obj["character_length"],
            name=obj["name"],
            details=tuple(obj["details"]),
        )


@dataclass(frozen=True, slots=True)
class Derivation(_JsonRecord):
    """How a column's value comes to exist when the mapping is not a plain move.

    `DictionaryEntry.derivation` is null when the mapping IS a plain move. It
    must be present whenever a column exists with no copybook view, because the
    bridge is authoritative and a column with no copybook counterpart has to say
    where its value comes from or the dictionary would be asserting a column out
    of nowhere. That obligation belongs to the generator and its test, not here
    (rule R-3).

    The clearest case is the three IRS date components, verbatim at
    [common/irspostingMT.cbl:L982-L987]:

        if       Post-Date (1:2) numeric
                 move     Post-Date (1:2) to HV-POST4-DAY.
        if       Post-Date (4:2) numeric
                 move     Post-Date (4:2) to HV-POST4-MONTH.
        if       Post-Date (7:2) numeric
                 move     Post-Date (7:2) to HV-POST4-YEAR.

    There is no `else` and no `end-if`. Because the load section opened with an
    initialise over the whole host-variable group
    [common/irspostingMT.cbl:L966], A FAILING GUARD LEAVES THE COMPONENT AT ZERO
    WHILE THE RAW DATE TEXT IS STILL STORED in POST4-DAT - a row that reaches
    the database internally inconsistent. The maintainer's own comment sits
    immediately above it, verbatim: "These added after new columns created
    31/12/16 - inhouse mysql & mariadb / and yes they all should be numeric as a
    date is present / but JIC (just in case)."

    Attributes:
        kind: Which kind of derivation this is.
        expression: The COBOL text that performs it, quoted closely enough that
            a reader can match it in the frozen source. Text, always: there is
            no executable content here and nothing in this migration interprets
            it as code (rule R-1).
        guard: The condition the derivation is performed under, verbatim, or
            null when it is unconditional.
        guard_failure_behaviour: What is stored when the guard fails, or null
            when there is no guard. Stated explicitly because the failure mode
            is itself part of the specification and must be reproduced rather
            than repaired (rule R-4); the module that reproduces it is named in
            the anomaly log, which `DictionaryEntry.anomaly_refs` points into.
        source: The line or span in the bridge program that performs it.
    """

    kind: DerivationKind
    expression: str
    guard: str | None
    guard_failure_behaviour: str | None
    source: SourceLocator

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the derivation record from its recorded object."""
        return cls(
            kind=DerivationKind(obj["kind"]),
            expression=obj["expression"],
            guard=obj["guard"],
            guard_failure_behaviour=obj["guard_failure_behaviour"],
            source=obj["source"],
        )


#  THE ENTRY - one authoritative triple


@dataclass(frozen=True, slots=True)
class DictionaryEntry(_JsonRecord):
    """ONE AUTHORITATIVE TRIPLE: one field seen from all three layers at once.

    The entry is the dictionary's unit of traceability. Its three views -
    `copybook`, `bridge_host_variable` and `column` - are SEPARATE SIBLING
    MEMBERS and any of them may be null, because the bridge is authoritative and
    neither of the other two is guaranteed to exist.

    There is deliberately no member that names one winning type across the
    views, and none may be added. A generator handed such a member would fill it
    in, and the disagreement would leave the record - which is exactly the
    failure rule R-4 exists to prevent. Where the views disagree the entry
    records all three, sets the matching flags in `drift`, and explains the
    disagreement in `drift.details` and in `notes`.

    A FOURTH VIEW EXISTS FOR ONE POPULATION AND ONLY THAT POPULATION.
    `program_source` carries a field COBOL declares inline in a program's FILE
    SECTION rather than in a copybook. It is not a fourth member of the
    triple and it never coexists with any of the three: an entry either has
    the triple's views, or it has this one. The population is the General
    Ledger work files - `pretrans.tmp`, `postrans.tmp` and the sort file that
    carries their records between phases - which are transient scratch storage
    that reaches no table, so no bridge maps them and no column stores them.
    They are catalogued because their pictures, usages and widths are
    load-bearing anyway: [general/gl072.cbl:L410-L412] locates a nominal-ledger
    account by SEQUENTIAL read and therefore depends on the sort order
    [general/gl071.cbl] emits, so a work-record field whose width or storage
    class was mistyped would misposts silently (anomaly A-14). Rule R-5 admits
    no field bound by eye, and these are fields.

    Attributes:
        key: The stable identifier this entry is cited by from
            `acas_posting/cobol/field.py` and from every module under
            `acas_posting/records/`. Two forms, both fully qualified by the
            record or table they belong to:

                <TABLE-NAME>.<COLUMN-NAME>      for a column-mapped field,
                                                such as
                                                IRSPOSTING-REC.POST4-DAY
                <COPYBOOK-RECORD>.<FIELD-NAME>  for a copybook-only field

            The qualification is what keeps PSIRSPOST-REC and IRSPOSTING-REC
            apart. They are DIFFERENT TABLES with near-identical field names -
            the transfer file the Sales and Purchase programs write, reached
            through `acas008` and the `slpostingMT` bridge with ten columns
            [mysql/ACASDB.sql:L366-L378], against the internal IRS posting file,
            reached through `acasirsub4` and the `irspostingMT` bridge with
            thirteen [mysql/ACASDB.sql:L274-L289] - and
            [copybooks/wspost-irs.cob:L6-L7] says so in as many words: "This is
            NOT the same as the internal IRS posting file". Because the key
            embeds the table or record name, two entries can never be merged by
            field name alone.

            Both halves are the names the frozen sources use themselves,
            unaltered: hyphens are not turned into underscores and case is not
            folded, so a key can be searched for in the COBOL and in the schema
            exactly as it stands. Where one field name repeats inside one record
            - `filler` occurs four times in copybooks/wsledger.cob - the key is
            disambiguated by appending `#` and the declaration line, which is
            unique and stays traceable.
        table: The in-scope table this entry belongs to, or null for a
            copybook-only field that maps to no table.
        bridge: The in-scope bridge pair that maps the field, or null when no
            bridge carries it.
        handler: The file handler the posting programs call to reach the table,
            or null. Recorded per entry as well as per table so that a
            field-level report is self-contained.
        entity_facade: The facade the posting programs address the table
            through, or null when the entry belongs to none.
        presence: Which of the four sources declare the field. A false here is
            what makes a one-sided field visible instead of absent.
        one_sided: True when the field is not present in all three layers of the
            authoritative triple - the negation of `in_copybook` and
            `in_bridge` and `in_column`. Redundant with `presence` by design, so
            that a report can select the interesting entries without recomputing
            the conjunction. `in_program_source` is not a term of it: a
            program-source field has all three of those false, so it is
            one-sided by construction rather than by comparison.
        copybook: THE COPYBOOK VIEW, or null when no copybook declares the
            field. Null is expected, not exceptional: the three IRS posting date
            components have no copybook counterpart anywhere, and requiring this
            view would make the correct dictionary unwritable.
        program_source: THE PROGRAM-SOURCE VIEW, or null - which it is for every
            entry except the work-file fields described above. It carries the
            SAME record type as `copybook`, `CopybookField`, because a COBOL
            data declaration has the same shape wherever it is written: one
            level, one name, one picture, one usage, one sign, one parent group.
            Reusing the type rather than cloning its twenty-two members keeps
            the two from drifting apart, and the two are told apart without
            ambiguity by `presence.in_program_source` and by this view's own
            `file` member, which names a program rather than a copybook -
            `general/gl070.cbl` rather than `copybooks/wspost.cob`. The
            declaring section, FD or SD, is recorded once per record in
            `Sources.program_sources` rather than repeated on every field.
        bridge_host_variable: THE BRIDGE VIEW - the authoritative one - or null
            when no bridge carries the field. This is where a signedness or
            width conversion actually happens, so it has to be read rather than
            inferred from either of the other two.
        column: THE COLUMN VIEW, or null when the field reaches no column. Null
            for every copybook-only field: a filler, a redefines alternative, or
            a subordinate item folded into its parent group.
        drift: The disagreements between whichever views are present. Always
            present, even when every flag is false, so that agreement is
            asserted rather than assumed.
        derivation: How the value comes to exist when the mapping is not a plain
            field-for-field move, or null when it is.
        cobol_python_storage: The Python type for the COBOL-side value, derived
            only from the declaring view's `usage` and `scale` - the copybook
            view where there is one, the program-source view otherwise - so that
            the choice between the exact-decimal type and `int` is data-driven
            (rule R-2). `NONE` when the entry has neither declaring view, which
            is the bridge-derived case. NOT a settlement of any drift - see
            `CobolPythonStorage`.
        notes: Observations about this field, one per element, may be empty.
            This is where a fact with no dedicated member is recorded rather
            than lost: a host variable declared but never loaded, a maintainer's
            comment that disagrees with the declaration it sits beside, a spare
            field carrying the wrong ledger's prefix. A note may state that a
            value is inconsistent; it never proposes correcting it (rule R-4).
        anomaly_refs: Identifiers of the entries this field participates in
            within the migration's anomaly log, may be empty. That log - a
            later boundary writes it - is the register of legacy defects this
            migration REPRODUCES rather than fixes, each entry naming the
            module that reproduces it.
        ambiguity_refs: Identifiers of the entries in the migration's
            ambiguity-resolutions log that bear on this field, may
            be empty. An ambiguity is a question reading the source cannot
            settle and only running the compiled program can, which is what
            rule R-6 is about. Two of the five land here: what value a negative
            binary actually stores after passing through an unsigned host
            variable into an unsigned column, and the record-length
            contradiction a copybook states about itself.
    """

    key: EntryKey
    table: TableName | None
    bridge: BridgeName | None
    handler: HandlerName | None
    entity_facade: EntityFacade | None
    presence: Presence
    one_sided: bool
    copybook: CopybookField | None
    program_source: CopybookField | None
    bridge_host_variable: BridgeHostVariable | None
    column: MysqlColumn | None
    drift: Drift
    derivation: Derivation | None
    cobol_python_storage: CobolPythonStorage
    notes: tuple[str, ...]
    anomaly_refs: tuple[str, ...]
    ambiguity_refs: tuple[str, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one entry from its recorded object.

        Each of the five nullable object members is read once and mapped only
        when it is present, so a null view stays a null view: nothing here
        substitutes an empty record for an absent one, which would turn "no
        copybook declares this field" into "a copybook declares nothing about
        it" (rules R-3 and R-4).
        """
        entity_facade = obj["entity_facade"]
        copybook = obj["copybook"]
        program_source = obj["program_source"]
        bridge_host_variable = obj["bridge_host_variable"]
        column = obj["column"]
        derivation = obj["derivation"]
        return cls(
            key=obj["key"],
            table=obj["table"],
            bridge=obj["bridge"],
            handler=obj["handler"],
            entity_facade=(
                None if entity_facade is None else EntityFacade(entity_facade)
            ),
            presence=Presence.from_json_obj(obj["presence"]),
            one_sided=obj["one_sided"],
            copybook=(
                None if copybook is None else CopybookField.from_json_obj(copybook)
            ),
            program_source=(
                None
                if program_source is None
                else CopybookField.from_json_obj(program_source)
            ),
            bridge_host_variable=(
                None
                if bridge_host_variable is None
                else BridgeHostVariable.from_json_obj(bridge_host_variable)
            ),
            column=(None if column is None else MysqlColumn.from_json_obj(column)),
            drift=Drift.from_json_obj(obj["drift"]),
            derivation=(
                None if derivation is None else Derivation.from_json_obj(derivation)
            ),
            cobol_python_storage=CobolPythonStorage(obj["cobol_python_storage"]),
            notes=tuple(obj["notes"]),
            anomaly_refs=tuple(obj["anomaly_refs"]),
            ambiguity_refs=tuple(obj["ambiguity_refs"]),
        )


#  THE FROZEN INPUTS - recorded so every entry can be re-derived, not trusted


@dataclass(frozen=True, slots=True)
class BridgeTableRef(_JsonRecord):
    """One table named by a bridge's own table directive, with its host-variable group.

    A bridge may name more than one table, which is why `BridgeSource.tables` is
    an array rather than a single value: the sales and purchase invoice bridges
    each map a header table and a lines table
    [common/slinvoiceMT.scb:L381-L385].

    Attributes:
        name: The table named in the directive.
        hv_group_suffix: The suffix the directive assigns that table's
            host-variable group - `HV` for a single-table bridge or the header
            table of a two-table bridge, `HV1` for the lines table.
        hv_group_name: The 01-level group the generated program emits for it,
            `TD-` followed by the table name.
    """

    name: TableName
    hv_group_suffix: str
    hv_group_name: str

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one bridge table reference from its recorded object."""
        return cls(
            name=obj["name"],
            hv_group_suffix=obj["hv_group_suffix"],
            hv_group_name=obj["hv_group_name"],
        )


@dataclass(frozen=True, slots=True)
class BridgeKey(_JsonRecord):
    """One key of reference declared in a bridge's key-name table.

    This is the metadata the data-access layer needs in order to EMULATE the
    indexed-file start and read-next verbs rather than merely issue equivalent
    SQL. The COBOL comment beside the table states the constraint that makes it
    necessary [common/glpostingMT.scb:L243-L245]: a start condition cannot be
    compounded and must use a key of reference within the record.

    The declaration is three filler items with literal values
    [common/glpostingMT.scb:L232-L234] - the key name padded to thirty
    characters, then a single eight-character literal that is the offset and the
    length concatenated four digits each, then the three-character type. The
    bridges declare one or two keys, and a two-key bridge is indexed by a
    subscript the calling program sets [common/slinvoiceMT.scb:L305].

    Attributes:
        name_in_rdb: The key's column name in the database as the key-name table
            spells it, with the declaration's trailing padding removed.
        offset: The key's one-based starting position within the working-storage
            record, taken from the FIRST FOUR digits of that literal. A
            position, not a magnitude (rule R-2).
        length: The key's length in record positions, taken from the LAST FOUR
            digits of the same literal.
        type: The three-character key-type literal. Two occur across the
            in-scope bridges: `STR`, annotated in the source as key is string,
            and `BNT`, annotated as key is bigint. Carried as text and matched
            by pattern rather than by a closed vocabulary, so that a bridge
            declaring a third one would be recorded rather than rejected.
        source: The span of the key-name table that declares this key.
    """

    name_in_rdb: str
    offset: int
    length: int
    type: str
    source: SourceLocator

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one bridge key from its recorded object."""
        return cls(
            name_in_rdb=obj["name_in_rdb"],
            offset=obj["offset"],
            length=obj["length"],
            type=obj["type"],
            source=obj["source"],
        )


@dataclass(frozen=True, slots=True)
class BridgeSource(_JsonRecord):
    """One of the twenty in-scope bridge pairs - `bridgeRecord` in the schema.

    Recorded because the bridge is the authoritative mapping layer, and BOTH
    members of the pair are cited: the `.scb` source carries the live table
    directive and the key metadata, and the generated `.cbl` carries the
    host-variable group and the load and unload sections. The distinction
    matters - in the generated program the directive block is commented out and
    replaced by an included variables copybook
    [common/glpostingMT.cbl:L276-L296], so the directive has to be cited from
    the `.scb`.

    The eight bridge pairs the posting cycle never reaches are out of scope and
    are NOT representable here; only their count is recorded, in
    `Coverage.out_of_scope_bridges`, so that the arithmetic stays auditable
    without naming one.

    Attributes:
        scb_path: The bridge source the vendored translator consumes, for
            example `common/glpostingMT.scb`.
        cbl_path: The generated bridge program that is actually compiled, for
            example `common/glpostingMT.cbl`.
        base: The database named in the bridge's own base directive. Fixed to
            one value because it is identical in all twenty in-scope bridge
            sources [common/glpostingMT.scb:L274] - one schema, named the same
            way everywhere.
        directive_source: The span of the live table-directive block in the
            `.scb`, which is the authority for the table-to-host-variable-group
            mapping [common/glpostingMT.scb:L273-L276].
        tables: The tables this bridge maps, in directive order. One for
            eighteen of the twenty in-scope bridges; two for the sales and
            purchase invoice bridges.
        keys: The keys of reference the bridge declares, in subscript order, for
            indexed-read emulation. Never given a floor: the array records what
            the bridge declares, and requiring a minimum would be adding a check
            the source does not perform (rule R-3).
        load_paragraph: The name of the section that loads the host variables
            from the passed record before a write. Recorded per bridge rather
            than assumed, and that is not a formality: sixteen of the twenty
            in-scope bridges name it `bb000-HV-Load`
            [common/glpostingMT.cbl:L1045], while four have no such section at
            all and perform their moves inline in a process section, whose name
            is what is recorded for them.
        load_paragraph_source: The span of that section in the generated
            program. Comparing the moves it contains against the declared
            host-variable group is how a host variable that is declared but
            never loaded is discovered
            [common/glpostingMT.cbl:L1054-L1066].
        unload_paragraph: The name of the section that unloads the host
            variables back into the record after a read, `bb100-UnloadHVs`
            where one exists [common/glpostingMT.cbl:L1074].
        unload_paragraph_source: The span of that section.
        group_initialised_before_load: Whether the load section issues an
            initialise over the whole host-variable group before its first move,
            as every in-scope bridge does [common/glpostingMT.cbl:L1053]. This
            is the reason unset fields reach the database as zero or space
            rather than as SQL null, and therefore the reason every column in
            the frozen schema can be declared not null.
    """

    scb_path: RepoPath
    cbl_path: RepoPath
    base: str
    directive_source: SourceLocator
    tables: tuple[BridgeTableRef, ...]
    keys: tuple[BridgeKey, ...]
    load_paragraph: str
    load_paragraph_source: SourceLocator
    unload_paragraph: str
    unload_paragraph_source: SourceLocator
    group_initialised_before_load: bool

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one bridge record from its recorded object."""
        return cls(
            scb_path=obj["scb_path"],
            cbl_path=obj["cbl_path"],
            base=obj["base"],
            directive_source=obj["directive_source"],
            tables=tuple(
                BridgeTableRef.from_json_obj(item) for item in obj["tables"]
            ),
            keys=tuple(BridgeKey.from_json_obj(item) for item in obj["keys"]),
            load_paragraph=obj["load_paragraph"],
            load_paragraph_source=obj["load_paragraph_source"],
            unload_paragraph=obj["unload_paragraph"],
            unload_paragraph_source=obj["unload_paragraph_source"],
            group_initialised_before_load=obj["group_initialised_before_load"],
        )


@dataclass(frozen=True, slots=True)
class CopybookSource(_JsonRecord):
    """One COBOL copybook and the record it declares - `copybookRecord`.

    Recorded so that the copybook side of every entry traces back to a file, and
    so that a copybook's own statements about its record length are preserved
    EVEN WHEN THEY CONTRADICT EACH OTHER.

    Attributes:
        path: The copybook path, for example `copybooks/wsbatch.cob`.
        record_name: The 01-level record it declares, case preserved.
        declared_lengths: Every record length the copybook states about itself,
            as digit strings, in the order it states them. AN ARRAY PRECISELY SO
            THAT A CONTRADICTION CAN BE RECORDED RATHER THAN RESOLVED (rule
            R-4). The batch copybook gives two different lengths and disputes
            its own second one, verbatim at [copybooks/wsbatch.cob:L7-L9]:
            "96 bytes 26/03/09" / "98 bytes 20/12/11 (no, dont understand as I
            count 96)" / "but function length (Batch-record) says 98?" - which
            is anomaly A-15, and which only running the compiled program can
            settle. The General Ledger posting copybook likewise records both
            98 and 96 bytes at [copybooks/wspost.cob:L6-L7], the second
            annotated "(leading sign removed)", which is why that record has no
            leading-sign field while [copybooks/wspost-irs.cob:L21] does.
        notes: Observations about the copybook or its record as a whole rather
            than about any single field, may be empty: a declared length its own
            author disputes, a field carrying the wrong ledger's prefix inside a
            group, a comment that disagrees with the declaration beside it.
    """

    path: RepoPath
    record_name: str
    declared_lengths: tuple[str, ...]
    notes: tuple[str, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one copybook record from its recorded object."""
        return cls(
            path=obj["path"],
            record_name=obj["record_name"],
            declared_lengths=tuple(obj["declared_lengths"]),
            notes=tuple(obj["notes"]),
        )


@dataclass(frozen=True, slots=True)
class ProgramSourceRecord(_JsonRecord):
    """One record a PROGRAM declares inline, in its own FILE SECTION.

    The fourth frozen input family, and the smallest: the General Ledger work
    files. `copybooks/wsnames.cob:L14-L17` names `pretrans.tmp` and
    `postrans.tmp` and annotates both as belonging to `gl071`, but no copybook
    declares their LAYOUT - each program that touches them writes the `01`
    record out inline instead, which is why these records need a source family
    of their own rather than a row among the copybooks.

    WHY THEY ARE CATALOGUED AT ALL, given that they reach no table. Because
    their field widths and storage classes are load-bearing:
    [general/gl072.cbl:L410-L412] finds the nominal-ledger account for a posting
    by SEQUENTIAL read rather than by key, so it lands on the right account only
    because [general/gl071.cbl] has already sorted the stream into nominal
    order. Perturb a key field's width or its usage and the program posts to the
    wrong account with no error and no diagnostic - anomaly A-14. Rule R-5
    admits no field bound by eye, so these are derived from the frozen programs
    like every other field in this document.

    THE SAME LOGICAL RECORD IS DECLARED MORE THAN ONCE, AND THE DECLARATIONS DO
    NOT ALL AGREE. `pre-trans-record` is declared in both `gl070` and `gl071`,
    identically. `post-trans-record` is declared in both `gl071` and `gl072` and
    the two differ: `gl071` declares the account and profit-centre fields FLAT
    at level 03, while `gl072` wraps the same eight bytes in a `03 post-ledger.`
    group with the two fields at 05 beneath it, because it needs the composite.
    Both declarations are recorded, neither is harmonised, and the divergence is
    left visible (rule R-4). It is also why an entry key for one of the repeated
    field names carries its declaration line.

    Attributes:
        path: The program that declares the record, for example
            `general/gl071.cbl`.
        record_name: The 01-level record it declares, case preserved as the
            program writes it - which for these records is lower case
            throughout, unlike most copybook records.
        section: `FD` for a file description or `SD` for a sort description.
            Recorded because the distinction is real: `sd sort-trans`
            [general/gl071.cbl:L134] is the sort work file the SORT verb owns,
            and the two `fd` records are the sequential work files it reads and
            writes.
        declared_lengths: Every record length the program states about the
            record, as digit strings, in the order it states them - EMPTY for
            all of these records, because the programs state none. Kept as an
            array for the same reason `CopybookSource.declared_lengths` is one:
            so that a contradiction could be recorded rather than resolved
            (rule R-4).
        notes: Observations about the record as a whole rather than about any
            single field, may be empty: that a second program declares the same
            record differently, that the record is transient scratch storage
            reaching no table, or that a downstream sequential read depends on
            the order its fields are sorted in.
    """

    path: RepoPath
    record_name: str
    section: str
    declared_lengths: tuple[str, ...]
    notes: tuple[str, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one program-source record from its recorded object."""
        return cls(
            path=obj["path"],
            record_name=obj["record_name"],
            section=obj["section"],
            declared_lengths=tuple(obj["declared_lengths"]),
            notes=tuple(obj["notes"]),
        )


@dataclass(frozen=True, slots=True)
class NumericTypeCensus(_JsonRecord):
    """How many columns of each base type the frozen schema declares.

    The member set is CLOSED to exactly the seven base types that occur, which
    has a deliberate second effect: there is no member here for a binary
    floating-point type, so a conforming document cannot even claim such a
    column exists (rule R-2).

    Attributes:
        DECIMAL: Columns declared as an exact-decimal type. Every monetary
            column in the posting cycle is one of these, which is why the driver
            must materialise them as exact values.
        INT: Columns declared as a four-byte integer.
        TINYINT: Columns declared as a one-byte integer.
        SMALLINT: Columns declared as a two-byte integer.
        MEDIUMINT: Columns declared as a three-byte integer.
        BIGINT: Columns declared as an eight-byte integer.
        CHAR: Columns declared as fixed-width text. Fixed width, so trailing
            padding is significant when two table states are compared and has to
            be evened out by the state normaliser.
    """

    DECIMAL: int
    INT: int
    TINYINT: int
    SMALLINT: int
    MEDIUMINT: int
    BIGINT: int
    CHAR: int

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the census from its recorded object."""
        return cls(
            DECIMAL=obj["DECIMAL"],
            INT=obj["INT"],
            TINYINT=obj["TINYINT"],
            SMALLINT=obj["SMALLINT"],
            MEDIUMINT=obj["MEDIUMINT"],
            BIGINT=obj["BIGINT"],
            CHAR=obj["CHAR"],
        )


@dataclass(frozen=True, slots=True)
class SchemaSource(_JsonRecord):
    """The frozen schema dump as an input - `sourcesSchema` in the schema.

    The audit figures below establish that it really is frozen, and one
    distinction among them is easy to get wrong. A plain text search of the dump
    for a table-alteration statement returns sixty-six hits, and EVERY ONE OF
    THEM is a version-guarded key-management comment that the dump utility emits
    twice per table around each data section. Not one of them changes a table's
    structure. Both figures are therefore recorded separately, so a reader can
    see sixty-six and nought side by side instead of having to reconcile them.

    Attributes:
        path: The frozen schema file. Read only: this migration adds no table,
            column, index, constraint, view or trigger of any kind (rule R-3).
        server_version: The database server that produced the dump, verbatim
            from its header. The comparison oracle stands up the same version,
            so that a behavioural difference can never be attributed to the
            server.
        server_version_source: The header line that records it
            [mysql/ACASDB.sql:L5].
        create_table_count: How many table declarations the dump contains.
            Thirty-three, of which 22 are in scope for the posting cycle and 11
            are not.
        create_index_count: How many standalone index declarations it contains.
            Nought. Recorded because it is what makes an ordering-normalised
            state dump deterministic: with no secondary index there is no
            alternative row order for a query to return.
        schema_evolution_alter_table_count: How many statements actually change
            a table's structure. Nought. This is the figure that matters for the
            freeze, and it is reported apart from the raw text count for the
            reason given above.
        dump_key_management_comment_count: How many version-guarded
            key-management comments the dump contains - the disable-keys and
            enable-keys pair the dump utility wraps each data section in.
            Sixty-six: two per table across thirty-three tables.
        float_double_real_column_count: How many columns are declared with one
            of the three binary floating-point SQL types. Nought, across all 720
            columns. Recorded because it is the schema-side half of rule R-2:
            the database cannot hand a binary approximation to the Python layer.
        numeric_type_census: Per-base-type column counts across the dump.
        notes: Observations about the frozen schema, one per element, may be
            empty. The place for a precise fact no counter above captures - for
            instance that exactly one in-scope column declares a default clause,
            at [mysql/ACASDB.sql:L1219]. A table outside the posting cycle may
            be referred to by count but never by name.
    """

    path: RepoPath
    server_version: str
    server_version_source: SourceLocator
    create_table_count: int
    create_index_count: int
    schema_evolution_alter_table_count: int
    dump_key_management_comment_count: int
    float_double_real_column_count: int
    numeric_type_census: NumericTypeCensus
    notes: tuple[str, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the schema-source record from its recorded object."""
        return cls(
            path=obj["path"],
            server_version=obj["server_version"],
            server_version_source=obj["server_version_source"],
            create_table_count=obj["create_table_count"],
            create_index_count=obj["create_index_count"],
            schema_evolution_alter_table_count=obj[
                "schema_evolution_alter_table_count"
            ],
            dump_key_management_comment_count=obj[
                "dump_key_management_comment_count"
            ],
            float_double_real_column_count=obj["float_double_real_column_count"],
            numeric_type_census=NumericTypeCensus.from_json_obj(
                obj["numeric_type_census"]
            ),
            notes=tuple(obj["notes"]),
        )


@dataclass(frozen=True, slots=True)
class SourceDigest(_JsonRecord):
    """One frozen input file, bound to the exact bytes the generator read.

    The three source sets above name WHICH files every entry was derived from.
    They do not, by themselves, say anything about the CONTENT of those files,
    so a document could claim a derivation from `common/salesMT.cbl` that the
    file on disk does not support - whether because the file legitimately
    changed, or because the document was edited by hand, or because it was
    substituted wholesale. This record closes that gap: it pins the digest and
    the byte length of every file the generator actually opened, so the claim
    "this dictionary was derived from these inputs" becomes checkable rather
    than asserted.

    Checking is what `--check` does. It re-derives the whole document from the
    working tree, which recomputes every digest here from the files as they
    stand; a mismatch therefore surfaces as a difference in the regenerated
    document rather than needing a separate comparison step. The manifest is
    also bound as a whole by `Meta.source_inputs_sha256`, so editing one digest
    is not enough to make a forged document self-consistent.

    A digest is not a signature and this manifest does not claim to be one: it
    binds the artifact to the repository it was generated from, which is exactly
    the property the frozen-source rule needs, since the repository itself is
    the authority.

    Attributes:
        path: The input's path relative to the repository root, forward slashes,
            never absolute - so the manifest is identical whichever checkout it
            was produced in (rule R-6 forbids an absolute path in this
            document).
        sha256: Lower-case hexadecimal SHA-256 of the file's bytes, exactly as
            they sit on disk. Computed over the raw bytes, not over the decoded
            or line-normalised text, so a line-ending change is a change.
        byte_length: The file's size in bytes. Redundant against the digest and
            deliberately so: it makes an accidental truncation legible at a
            glance rather than only detectable by recomputation.
    """

    path: RepoPath
    sha256: str
    byte_length: int

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one input digest from its recorded object."""
        return cls(
            path=obj["path"],
            sha256=obj["sha256"],
            byte_length=obj["byte_length"],
        )


@dataclass(frozen=True, slots=True)
class Sources(_JsonRecord):
    """The four frozen input sets the dictionary is derived from, and their digests.

    Recorded so that every entry can be RE-DERIVED from the repository rather
    than trusted. Field metadata in this dictionary is derived and not
    transcribed, which is what removes an entire class of transcription error
    across several hundred fields - and what makes recording the inputs a
    requirement rather than a courtesy.

    Attributes:
        schema: The frozen schema dump and its audit figures.
        bridges: The twenty in-scope bridge pairs - the authoritative mapping
            layer - sorted by bridge-source filename per
            `Determinism.array_order`.
        copybooks: The copybooks whose record layouts the dictionary reads,
            sorted by path.
        input_digests: Every file the generator opened, with its digest and byte
            length, sorted by path. This is the authenticated binding between
            the artifact and the exact frozen bytes behind it; see
            `SourceDigest`.
        program_sources: The records the posting programs declare inline in
            their own FILE SECTIONs - the General Ledger work files -
            sorted by path and then by the record's declaration line, since one
            program declares three of them. The smallest of the four families
            and the only one whose fields reach no table; see
            `ProgramSourceRecord` for why they are catalogued regardless.
    """

    schema: SchemaSource
    bridges: tuple[BridgeSource, ...]
    copybooks: tuple[CopybookSource, ...]
    input_digests: tuple[SourceDigest, ...]
    program_sources: tuple[ProgramSourceRecord, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the sources record from its recorded object."""
        return cls(
            schema=SchemaSource.from_json_obj(obj["schema"]),
            bridges=tuple(
                BridgeSource.from_json_obj(item) for item in obj["bridges"]
            ),
            copybooks=tuple(
                CopybookSource.from_json_obj(item) for item in obj["copybooks"]
            ),
            input_digests=tuple(
                SourceDigest.from_json_obj(item) for item in obj["input_digests"]
            ),
            program_sources=tuple(
                ProgramSourceRecord.from_json_obj(item)
                for item in obj["program_sources"]
            ),
        )


#  THE TABLE SPINE - which COBOL machinery reaches which table


@dataclass(frozen=True, slots=True)
class TableRecord(_JsonRecord):
    """One in-scope table and the COBOL machinery that reaches it.

    This is the entity-to-table spine: the four-hop call chain the posting cycle
    uses to touch a table, recorded once per table so that an entry key's table
    component always resolves to a named bridge, handler and entity facade.

    The eleven tables the posting cycle never reaches are out of scope and are
    NOT representable here - not by name, not by reference. Only their count is
    recorded, in `Coverage.out_of_scope_tables`, so that twenty-two plus eleven
    still visibly accounts for all thirty-three tables in the frozen dump
    without naming one that the cycle never touches.

    Attributes:
        name: The table name as the frozen dump spells it between backticks.
        bridge: The bridge pair that owns this table's SQL.
        handler: The numbered handler program the posting programs call. Not
            always one per table: one handler dispatches to four different
            bridges by key number, and two handlers each own a header table and
            a lines table, which is why the data-access layer mirrors the
            handler boundary rather than the table boundary.
        entity_facade: The facade name the shared call copybook publishes for
            this table's twelve verbs.
        copybooks: The copybooks whose record layouts map onto this table, in
            path order. More than one where a table is declared across a header
            copybook and a lines copybook.
        primary_key: The single column named in the table's primary-key clause.
            Single-column for every in-scope table, which together with the
            complete absence of secondary indexes is what makes an
            ordering-normalised state dump deterministic: ordering by this one
            column has no ties to break.
        column_count: How many columns the table declares.
        ordinal_source: The line that opens this table's declaration in the
            frozen dump. Column ordinals are counted from there, so a reader can
            confirm any ordinal by counting from the cited line - which is how
            the three bridge-derived date components are shown to sit at
            ordinals four, five and six rather than at the end of the record.
    """

    name: TableName
    bridge: BridgeName
    handler: HandlerName
    entity_facade: str
    copybooks: tuple[RepoPath, ...]
    primary_key: str
    column_count: int
    ordinal_source: SourceLocator

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one table record from its recorded object."""
        return cls(
            name=obj["name"],
            bridge=obj["bridge"],
            handler=obj["handler"],
            entity_facade=obj["entity_facade"],
            copybooks=tuple(obj["copybooks"]),
            primary_key=obj["primary_key"],
            column_count=obj["column_count"],
            ordinal_source=obj["ordinal_source"],
        )


#  THE DETERMINISM CONTRACT - two regenerations must not differ by one byte


@dataclass(frozen=True, slots=True)
class ArrayOrder(_JsonRecord):
    """How each top-level array of the dictionary is ordered.

    Recorded rather than left implicit because an array's order is part of the
    document's bytes: two regenerations that ordered an array differently would
    both satisfy the schema and yet differ, which rule R-6 forbids. Every
    ordering below is a total order over values the frozen sources themselves
    supply, so none of them can depend on the order a directory happened to be
    listed in.

    Attributes:
        tables: How the tables array is ordered.
        entries: How the entries array is ordered - the one that carries real
            information, because it is deliberately NOT by key. Entries are
            grouped by table and then follow the column's ordinal within the
            table's declaration, so that the dictionary reads down a table in
            exactly the order the frozen dump declares it, with copybook-only
            fields following their record's column-mapped fields in declaration
            order.
        bridges: How the bridges array under sources is ordered.
        copybooks: How the copybooks array under sources is ordered.
        program_sources: How the program_sources array under sources is ordered.
            Two keys are needed rather than one, because a single program
            declares three of these records.
    """

    tables: str
    entries: str
    bridges: str
    copybooks: str
    program_sources: str

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the array-order record from its recorded object."""
        return cls(
            tables=obj["tables"],
            entries=obj["entries"],
            bridges=obj["bridges"],
            copybooks=obj["copybooks"],
            program_sources=obj["program_sources"],
        )


@dataclass(frozen=True, slots=True)
class Determinism(_JsonRecord):
    """The byte-for-byte serialisation contract - `determinism` in the schema.

    Two regenerations of the dictionary from an unchanged repository must
    produce IDENTICAL BYTES (rule R-6). That property is not decoration: the
    whole verification design rests on being able to compare two states and
    treat any difference as real, and a dictionary that shifted under its own
    regeneration would put that in doubt. The five fixed members below are
    published as module constants as well, so a writer sets them from one place.

    The single most consequential clause is the member order: object members are
    emitted in the order the JSON Schema declares them, never sorted. This
    module is what makes that mechanical - the declaration order of every record
    here IS the schema's declaration order, and the writer walks the declared
    fields in order rather than sorting keys.

    Attributes:
        encoding: The character encoding of the written document.
        newline: The line ending, named rather than written so the value itself
            cannot be mangled by an editor.
        indent: How many spaces each nesting level is indented by.
        trailing_newline: Whether the document ends with a single line ending.
        byte_order_mark: Whether a byte-order mark is written. False: it would
            be invisible in a text diff and would change the bytes.
        member_order: How object members are ordered, stated in full - see
            above.
        array_order: How each top-level array is ordered.
        forbidden_content: The kinds of content that may never appear anywhere
            in the dictionary because they would differ between two otherwise
            identical regenerations, one element per kind: a date or time of
            generation, a machine or account name, an absolute path, a revision
            or branch identifier, a tool version read from the environment, an
            identifier drawn by chance or by hashing, any ordering that depends
            on how a directory was traversed, and any credential value. A date
            QUOTED
            FROM A COMMENT in a frozen source is a different thing entirely -
            that is evidence about the source and is kept verbatim.
    """

    encoding: str
    newline: str
    indent: int
    trailing_newline: bool
    byte_order_mark: bool
    member_order: str
    array_order: ArrayOrder
    forbidden_content: tuple[str, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the determinism record from its recorded object."""
        return cls(
            encoding=obj["encoding"],
            newline=obj["newline"],
            indent=obj["indent"],
            trailing_newline=obj["trailing_newline"],
            byte_order_mark=obj["byte_order_mark"],
            member_order=obj["member_order"],
            array_order=ArrayOrder.from_json_obj(obj["array_order"]),
            forbidden_content=tuple(obj["forbidden_content"]),
        )


@dataclass(frozen=True, slots=True)
class DerivationRules(_JsonRecord):
    """The rules the generator applied, stated so a reader can check its work.

    Every member is prose describing HOW a derived member of an entry was
    arrived at. Recorded because field metadata in this dictionary is derived
    rather than transcribed, and a derivation nobody can audit is no better than
    a transcription: with the rule written down, a reader can take any entry,
    apply the rule to the cited frozen source and confirm the recorded value.

    None of these rules resolves a disagreement between the three views. They
    describe how each view was READ, and how the drift flags were computed by
    comparing the views that are present (rule R-4).

    Attributes:
        entry_key: How an entry's key is formed, for a column-mapped entry and
            for a copybook-only one, including how a repeated name within one
            record is disambiguated.
        presence_and_one_sided: How the three presence booleans and the
            one-sided flag are set from what was actually found.
        drift_detection: How each drift flag is computed - by comparing the
            views that are present, never by consulting a list of known cases,
            which is what lets the dictionary find a narrowing nobody had
            catalogued in advance.
        digits_and_scale_from_picture: How a picture clause is expanded and
            counted into integer digits, scale, total digits and character
            length.
        sign_position_from_clause: How the sign position is read from the sign
            clause, the picture and the usage together.
        usage_inheritance: How a storage class declared on a group reaches the
            subordinate items that declare none, and how that inheritance is
            recorded rather than silently applied. THE HIGHEST-RISK DERIVATION
            IN THE DICTIONARY - see `UsageDeclaredAt`.
        bridge_derived_columns: How a host variable is bound to the copybook
            field it carries, and what happens when no copybook field can be
            found for it - which is the case that discovers a column existing in
            the bridge and the database but in no copybook.
        cobol_python_storage: How the exact-decimal-versus-integer-versus-text
            choice is made FROM THE DECLARING VIEW ALONE. Restating what
            `CobolPythonStorage` says, because it is the one derived scalar in
            the whole document and must not be mistaken for a settlement of
            drift.
        program_source_entries: How a record declared inline in a program's FILE
            SECTION is found, which line span is read for it, and why
            its bridge and column views are recorded as absent rather than
            searched for.
    """

    entry_key: str
    presence_and_one_sided: str
    drift_detection: str
    digits_and_scale_from_picture: str
    sign_position_from_clause: str
    usage_inheritance: str
    bridge_derived_columns: str
    cobol_python_storage: str
    program_source_entries: str

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the derivation-rules record from its recorded object."""
        return cls(
            entry_key=obj["entry_key"],
            presence_and_one_sided=obj["presence_and_one_sided"],
            drift_detection=obj["drift_detection"],
            digits_and_scale_from_picture=obj["digits_and_scale_from_picture"],
            sign_position_from_clause=obj["sign_position_from_clause"],
            usage_inheritance=obj["usage_inheritance"],
            bridge_derived_columns=obj["bridge_derived_columns"],
            cobol_python_storage=obj["cobol_python_storage"],
            program_source_entries=obj["program_source_entries"],
        )


@dataclass(frozen=True, slots=True)
class BindingRule(_JsonRecord):
    """One of the six binding rules, recorded inside the artefact it governs.

    Carried in the document itself so that a reader who has only the dictionary
    still knows what it was held to - in particular that a defect found in the
    frozen sources is recorded and reproduced rather than corrected.

    Attributes:
        id: The rule identifier, `R-1` through `R-6`.
        summary: What the rule requires OF THIS DICTIONARY specifically, in the
            dictionary's own terms rather than as a general statement.
    """

    id: str
    summary: str

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one binding rule from its recorded object."""
        return cls(id=obj["id"], summary=obj["summary"])


@dataclass(frozen=True, slots=True)
class Meta(_JsonRecord):
    """The dictionary's identity, authority and contracts - `meta`.

    !! THIS RECORD DECLARES NO MEMBER FOR WHEN, WHERE, BY WHOM OR FROM WHICH
    !! REVISION THE DICTIONARY WAS PRODUCED, and none may be added. No date or
    !! time of generation, no machine or account name, no revision identifier,
    !! no absolute path, no tool version read from the environment. Because this
    !! record is frozen and declares fixed slots, such a member is not merely
    !! discouraged - it is UNREPRESENTABLE, which is exactly the point (rule
    !! R-6). Any one of them would differ between two regenerations from an
    !! unchanged repository and destroy the byte-for-byte guarantee.
    !!
    !! The one version this document does record is the database server version,
    !! and it is recorded because THE FROZEN DUMP STATES IT IN ITS OWN HEADER -
    !! it is a fact about a frozen source, not a reading of the machine that
    !! happened to run the generator.

    Attributes:
        dictionary_name: The dictionary's stable name, fixed to one value.
        dictionary_version: The dictionary format's own version, three
            dot-separated numbers. Advanced deliberately when the shape of the
            document changes; it is not derived from anything in the
            environment.
        schema_ref: The JSON Schema this document conforms to, named as a
            filename beside it so the reference cannot depend on where the
            repository is checked out.
        generated_by: The generator module, fixed to one value, so a reader
            knows which file to read to audit any derivation.
        authority: The authority statement this whole dictionary rests on,
            preserved verbatim: the maintainer's one-way bridge defines the
            authoritative record-layout-to-table mapping, and it IS the data
            dictionary for this migration. Every design decision in this module
            follows from that sentence - above all the decision that a copybook
            view may be absent, because three columns of one posting table exist
            in the bridge and the database and in no copybook at all.
        determinism: The byte-for-byte serialisation contract.
        derivation_rules: How every derived member was arrived at.
        binding_rules: The six rules that govern this migration and therefore
            this dictionary, in identifier order.
        source_inputs_sha256: The digest of `sources.input_digests` taken as a
            whole - one lower-case hexadecimal SHA-256 over the canonical
            rendering `"<path>:<sha256>:<byte_length>\\n"` of every manifest
            entry, joined in the manifest's own order. It binds the manifest
            itself, so a document whose per-file digests have been edited to
            match a substituted input is still detectably inconsistent here.
            This member records a property of frozen inputs, not of the machine
            that ran the generator, so it does not weaken the prohibition above:
            two regenerations from an unchanged repository produce the same
            value.
    """

    dictionary_name: str
    dictionary_version: str
    schema_ref: str
    generated_by: str
    authority: str
    determinism: Determinism
    derivation_rules: DerivationRules
    binding_rules: tuple[BindingRule, ...]
    source_inputs_sha256: str

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the meta record from its recorded object."""
        return cls(
            dictionary_name=obj["dictionary_name"],
            dictionary_version=obj["dictionary_version"],
            schema_ref=obj["schema_ref"],
            generated_by=obj["generated_by"],
            authority=obj["authority"],
            determinism=Determinism.from_json_obj(obj["determinism"]),
            derivation_rules=DerivationRules.from_json_obj(
                obj["derivation_rules"]
            ),
            binding_rules=tuple(
                BindingRule.from_json_obj(item) for item in obj["binding_rules"]
            ),
            source_inputs_sha256=obj["source_inputs_sha256"],
        )


#  COVERAGE - the completeness claim, made auditable by counting


@dataclass(frozen=True, slots=True)
class Coverage(_JsonRecord):
    """Tallies that make the dictionary's completeness claim checkable.

    Every count exists so a reader can verify a claim by arithmetic instead of
    taking it on trust: that the in-scope and out-of-scope tables together
    account for every table in the frozen dump, that the in-scope and
    out-of-scope bridges together account for every bridge pair, and that every
    in-scope column has an entry.

    !! THE OUT-OF-SCOPE TALLIES ARE COUNTS AND NOTHING ELSE. There is
    !! deliberately no member here, or anywhere in this module, that could NAME
    !! a table or a bridge the posting cycle does not reach. The arithmetic
    !! stays auditable; the names of things outside the migrated boundary stay
    !! out of the document.

    Attributes:
        schema_tables_total: How many tables the frozen dump declares in total.
        in_scope_tables: How many of them the posting cycle reaches.
        out_of_scope_tables: How many it does not. A count only.
        in_scope_bridges: How many bridge pairs the cycle reaches.
        out_of_scope_bridges: How many it does not. A count only.
        in_scope_columns: How many columns the in-scope tables declare between
            them.
        entry_count: How many entries the document carries. Larger than the
            column count, and necessarily so: a copybook field that reaches no
            column still gets an entry, because nothing found in any source is
            ever dropped (rule R-5).
        columns_covered: How many columns have an entry. Equal to
            `in_scope_columns` when coverage is complete, and stated separately
            so the claim is a comparison rather than an assertion.
        host_variables_covered: How many bridge host variables have an entry.
        copybook_fields_covered: How many copybook fields have an entry.
        program_source_fields_covered: How many fields declared inline in a
            program's FILE SECTION have an entry - the General Ledger
            work-file records. Counted separately from the copybook fields
            rather than folded into them, because they come from a different
            source family and no copybook declares them; adding the two
            together would misreport both.
        one_sided_entry_keys: The key of every entry whose one-sided flag is
            true, gathered in one place. This is the review list for
            cross-source disagreement: a field present in one source and absent
            from another is FLAGGED HERE AND NEVER DROPPED, so the reader who
            wants to see every such case reads this array rather than filtering
            a thousand entries by hand.
    """

    schema_tables_total: int
    in_scope_tables: int
    out_of_scope_tables: int
    in_scope_bridges: int
    out_of_scope_bridges: int
    in_scope_columns: int
    entry_count: int
    columns_covered: int
    host_variables_covered: int
    copybook_fields_covered: int
    program_source_fields_covered: int
    one_sided_entry_keys: tuple[EntryKey, ...]

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the coverage record from its recorded object."""
        return cls(
            schema_tables_total=obj["schema_tables_total"],
            in_scope_tables=obj["in_scope_tables"],
            out_of_scope_tables=obj["out_of_scope_tables"],
            in_scope_bridges=obj["in_scope_bridges"],
            out_of_scope_bridges=obj["out_of_scope_bridges"],
            in_scope_columns=obj["in_scope_columns"],
            entry_count=obj["entry_count"],
            columns_covered=obj["columns_covered"],
            host_variables_covered=obj["host_variables_covered"],
            copybook_fields_covered=obj["copybook_fields_covered"],
            program_source_fields_covered=obj["program_source_fields_covered"],
            one_sided_entry_keys=tuple(obj["one_sided_entry_keys"]),
        )


#  THE DOCUMENT ROOT


@dataclass(frozen=True, slots=True)
class DataDictionary(_JsonRecord):
    """The whole machine-readable data dictionary, in memory.

    The root object of `data_dictionary/acas_posting_dictionary.json`, and the
    in-memory form the generator builds and the loader reads back. Its five
    members are declared in the order the JSON Schema declares them, which is
    also the order they are written: identity, then the frozen inputs, then the
    table spine, then the field-level entries, then the coverage tallies.

    That ordering is not arbitrary. A reader meets the authority statement and
    the determinism contract before any data; then the sources, so every later
    claim can be checked against the repository; then the tables, so an entry
    key's table component already means something; then the entries; and finally
    the tallies that make the whole thing auditable.

    Round-tripping is exact by construction. `to_json_obj` walks the declared
    fields of each record in declaration order and converts enumerations to
    their string values and sequences to arrays; `from_json_obj` reads the
    members back by name and supplies NOTHING for a member that is absent. A
    document written from this model, read back, and written again is identical
    to the byte.

    Attributes:
        meta: Identity, authority, the determinism contract, the derivation
            rules and the binding rules.
        sources: The frozen inputs every entry was derived from.
        tables: The in-scope tables and the COBOL machinery that reaches each,
            in table-name order.
        entries: The field-level triples, grouped by table and then by column
            ordinal, with copybook-only fields following their record's
            column-mapped fields and the program-source work-file fields last of
            all. One entry per column, per host variable, per copybook field and
            per program-source field, including every field that exists in only
            one source.
        coverage: The tallies that make the completeness claim checkable.
    """

    meta: Meta
    sources: Sources
    tables: tuple[TableRecord, ...]
    entries: tuple[DictionaryEntry, ...]
    coverage: Coverage

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build the whole dictionary from a parsed JSON document.

        Args:
            obj: The parsed document, exactly as the standard-library JSON
                module produced it from the written file.

        Returns:
            The document as an immutable tree of records.

        The read is strict on purpose: every member is fetched by name, no
        member has a fallback, and no value is coerced. A document missing a
        member the schema requires fails here rather than being quietly
        completed with a default that no frozen source supports (rule R-3).
        """
        return cls(
            meta=Meta.from_json_obj(obj["meta"]),
            sources=Sources.from_json_obj(obj["sources"]),
            tables=tuple(
                TableRecord.from_json_obj(item) for item in obj["tables"]
            ),
            entries=tuple(
                DictionaryEntry.from_json_obj(item) for item in obj["entries"]
            ),
            coverage=Coverage.from_json_obj(obj["coverage"]),
        )


# =============================================================================
#  THE INTEGRITY PASS - the artifact's own trust boundary
#
#  Rule R-5 requires that every Python field cite a dictionary entry, and every
#  record module does. A citation is only worth what the cited document is
#  worth, so the document itself is where the whole traceability claim can be
#  attacked: substitute the artifact, or edit one member of it by hand, and
#  several hundred fields silently acquire a picture, a scale, a signedness or a
#  storage class that no frozen source supports. Nothing downstream would
#  notice, because everything downstream trusts the dictionary by design.
#
#  This pass closes that. It runs once, on the way IN, in the door below, and
#  holds the decoded document to everything this module already states about it:
#  the exact member set of every record, the exact value domain of every member,
#  the patterns declared above, the values the schema pins to one literal each,
#  the uniqueness of every identifier, the agreement between the presence flags
#  and the views they describe, the coverage tallies against the entries
#  actually present, and the digest that binds the source manifest to itself.
#  The first document that departs from any of it raises
#  `DictionaryIntegrityError` and no record is built from it.
#
#  WHY THIS IS NOT A NEW VALIDATION (rule R-3). R-3 forbids adding validation
#  to the migrated accounting cycle: no new check on a posting, an amount, an
#  account code or a batch, because the compiled program is the specification
#  and a check it does not perform is a behaviour change. Nothing here examines
#  an accounting value. This pass examines the migration's own metadata artifact
#  - the document that says what shape a field has - and it examines it for
#  self-consistency against facts stated in this module, not against any
#  judgement about what the frozen sources ought to contain. A repository whose
#  artifact is the one its generator produced sees byte-identical behaviour with
#  this pass present and absent; the pass changes what happens only when the
#  document is already not the document it claims to be. That is provenance
#  control, which R-5 requires, not ledger validation, which R-3 forbids.
#
#  WHAT IT DELIBERATELY DOES NOT DO. It does not read a frozen COBOL or SQL
#  source, so it cannot and does not confirm that a recorded digest matches the
#  bytes on disk - `generate.py --check` is what does that, by re-deriving the
#  whole document. It does not repair, default, coerce or warn: there is one
#  outcome for a document that does not hold up, and it is a raise. And it does
#  not consult the clock, the environment, the filesystem or the network, so it
#  cannot make two runs differ (rule R-6).
# =============================================================================


class DictionaryIntegrityError(ValueError):
    """A dictionary document does not hold up as the document it claims to be.

    Raised by the `from_json_obj` door, before any record is built, when the
    decoded document departs from the structure, domains, patterns, pinned
    values, identifier uniqueness, internal agreement or manifest binding this
    module declares. The message names every departure found, one per line, in
    the order the walk found them, so a single raise diagnoses the whole
    document rather than only its first fault.

    A `ValueError` subclass because that is what a caller who does not care
    about the distinction already catches, and because the fault is always in
    the value handed in - never in the caller's use of the interface.
    """


#: Every string member the schema constrains by pattern, keyed
#: `"<record class>.<member>"`. A member absent from this map is checked for
#: being text and nothing more; a member present is additionally held to its
#: pattern, and so is every element when the member is an array of text. The map
#: is the single place the pattern-to-member correspondence is written down,
#: which is what keeps it from drifting away from the schema it mirrors.
_PATTERN_BY_MEMBER: Final[Mapping[str, re.Pattern[str]]] = {
    "BindingRule.id": BINDING_RULE_ID_PATTERN,
    "BridgeHostVariable.file": REPO_PATH_PATTERN,
    "BridgeHostVariable.hv_group_name": HV_GROUP_NAME_PATTERN,
    "BridgeHostVariable.hv_group_suffix": HV_GROUP_SUFFIX_PATTERN,
    "BridgeHostVariable.load_source": SOURCE_LOCATOR_PATTERN,
    "BridgeHostVariable.name": HV_NAME_PATTERN,
    "BridgeHostVariable.source": SOURCE_LOCATOR_PATTERN,
    "BridgeHostVariable.unload_source": SOURCE_LOCATOR_PATTERN,
    "BridgeKey.source": SOURCE_LOCATOR_PATTERN,
    "BridgeKey.type": BRIDGE_KEY_TYPE_PATTERN,
    "BridgeSource.cbl_path": REPO_PATH_PATTERN,
    "BridgeSource.directive_source": SOURCE_LOCATOR_PATTERN,
    "BridgeSource.load_paragraph_source": SOURCE_LOCATOR_PATTERN,
    "BridgeSource.scb_path": REPO_PATH_PATTERN,
    "BridgeSource.unload_paragraph_source": SOURCE_LOCATOR_PATTERN,
    "BridgeTableRef.hv_group_name": HV_GROUP_NAME_PATTERN,
    "BridgeTableRef.hv_group_suffix": HV_GROUP_SUFFIX_PATTERN,
    "BridgeTableRef.name": TABLE_NAME_PATTERN,
    "ConditionName.source": SOURCE_LOCATOR_PATTERN,
    "CopybookField.file": REPO_PATH_PATTERN,
    "CopybookField.level": COPYBOOK_LEVEL_PATTERN,
    "CopybookField.source": SOURCE_LOCATOR_PATTERN,
    "CopybookField.usage_group_source": SOURCE_LOCATOR_PATTERN,
    "CopybookSource.declared_lengths": DECLARED_LENGTH_PATTERN,
    "CopybookSource.path": REPO_PATH_PATTERN,
    "Coverage.one_sided_entry_keys": ENTRY_KEY_PATTERN,
    "Derivation.source": SOURCE_LOCATOR_PATTERN,
    "DictionaryEntry.ambiguity_refs": AMBIGUITY_REF_PATTERN,
    "DictionaryEntry.anomaly_refs": ANOMALY_REF_PATTERN,
    "DictionaryEntry.bridge": BRIDGE_NAME_PATTERN,
    "DictionaryEntry.handler": HANDLER_NAME_PATTERN,
    "DictionaryEntry.key": ENTRY_KEY_PATTERN,
    "DictionaryEntry.table": TABLE_NAME_PATTERN,
    "Meta.dictionary_version": DICTIONARY_VERSION_PATTERN,
    "Meta.source_inputs_sha256": SHA256_PATTERN,
    "MysqlColumn.file": REPO_PATH_PATTERN,
    "MysqlColumn.name": COLUMN_NAME_PATTERN,
    "MysqlColumn.source": SOURCE_LOCATOR_PATTERN,
    "SchemaSource.path": REPO_PATH_PATTERN,
    "SchemaSource.server_version_source": SOURCE_LOCATOR_PATTERN,
    "SourceDigest.path": REPO_PATH_PATTERN,
    "SourceDigest.sha256": SHA256_PATTERN,
    "TableRecord.bridge": BRIDGE_NAME_PATTERN,
    "TableRecord.copybooks": REPO_PATH_PATTERN,
    "TableRecord.handler": HANDLER_NAME_PATTERN,
    "TableRecord.name": TABLE_NAME_PATTERN,
    "TableRecord.ordinal_source": SOURCE_LOCATOR_PATTERN,
}

#: The members the schema pins to exactly one literal, keyed the same way. A
#: document that names a different generator, a different schema, a different
#: authority statement or a different serialisation contract is not this
#: dictionary, whatever else it may be, and saying so here is cheaper and more
#: exact than any amount of downstream suspicion.
_PINNED_BY_MEMBER: Final[Mapping[str, str | int | bool]] = {
    "Determinism.byte_order_mark": DETERMINISM_BYTE_ORDER_MARK,
    "Determinism.encoding": DETERMINISM_ENCODING,
    "Determinism.indent": DETERMINISM_INDENT,
    "Determinism.newline": DETERMINISM_NEWLINE,
    "Determinism.trailing_newline": DETERMINISM_TRAILING_NEWLINE,
    "Meta.authority": DICTIONARY_AUTHORITY,
    "Meta.dictionary_name": DICTIONARY_NAME,
    "Meta.generated_by": DICTIONARY_GENERATED_BY,
    "Meta.schema_ref": DICTIONARY_SCHEMA_REF,
}

#: How many departures one raise reports in full. A document that has gone
#: badly wrong can fail in thousands of places at once and an unbounded message
#: would bury the useful part; the count is always reported in full, so nothing
#: is hidden, only elided.
_MAX_REPORTED_PROBLEMS: Final[int] = 25


def source_inputs_digest_material(digests: Sequence[SourceDigest]) -> str:
    """Render a source manifest to the exact text its roll-up digest is taken over.

    Args:
        digests: The manifest, in the order it appears in the document. Order is
            part of the material, so a reordered manifest is a different
            manifest - which is what stops two documents with the same set of
            inputs but different array order from sharing a digest.

    Returns:
        One line per entry, `"<path>:<sha256>:<byte_length>"`, each terminated
        by a single line feed. Deliberately plain: it can be reproduced by hand
        from the artifact with a text editor and a shell, so the binding is
        auditable without running this module.

    Written once here and used by both ends - `generate.py` to compute
    `Meta.source_inputs_sha256` and this module's integrity pass to recompute
    it - because two implementations of a digest input are two chances to
    disagree, and a disagreement would make every artifact look forged.
    """
    return "".join(
        "%s:%s:%d\n" % (digest.path, digest.sha256, digest.byte_length)
        for digest in digests
    )


def source_inputs_digest(digests: Sequence[SourceDigest]) -> str:
    """Compute the roll-up digest that binds a source manifest as a whole.

    Args:
        digests: The manifest, in document order.

    Returns:
        Lower-case hexadecimal SHA-256 of `source_inputs_digest_material`,
        which is the value `Meta.source_inputs_sha256` carries.

    The per-file digests bind each input to its bytes; this binds the list of
    them to itself. Without it, a forged document could swap one input's digest
    for the digest of a file it substituted and remain internally consistent.
    With it, that edit has to be made in two places that are computed from each
    other, and the second one is over the whole manifest.
    """
    return hashlib.sha256(
        source_inputs_digest_material(digests).encode(DETERMINISM_ENCODING)
    ).hexdigest()


@cache
def _resolved_hints(record: type) -> Mapping[str, Any]:
    """Resolve one record class's annotations to real objects, once per class.

    `from __future__ import annotations` is not in force here, but the string
    domains are PEP 695 aliases and the records refer to one another, so
    resolution still has to go through `get_type_hints` rather than reading
    `__annotations__` directly. Cached because the walk asks the same twenty-odd
    classes the same question several thousand times for a document of this
    size, and resolution is the expensive half.
    """
    return get_type_hints(record)


def _unwrap_alias(hint: Any) -> Any:
    """Reduce a PEP 695 alias to the type it stands for.

    Every string domain above - `RepoPath`, `EntryKey`, `TableName` and the
    rest - is an alias for `str`, declared separately so that a reader of a
    record sees which domain a member belongs to. The walk cares only about the
    underlying shape, so the alias is unwrapped here; the domain it named is
    still enforced, through `_PATTERN_BY_MEMBER`.
    """
    while isinstance(hint, TypeAliasType):
        hint = hint.__value__
    return hint


def _check_member(
    hint: Any,
    value: object,
    where: str,
    pattern: re.Pattern[str] | None,
    pinned: str | int | bool | None,
    problems: list[str],
) -> None:
    """Hold one decoded member to the type its record declares for it.

    Args:
        hint: The resolved annotation, possibly an alias, an optional or an
            array of one of those.
        value: The decoded member.
        where: Its path in the document, for the message.
        pattern: The pattern its record declares for it, if any. An array
            member's pattern applies to every element.
        pinned: The single literal the schema pins it to, if any.
        problems: Where a departure is appended. Nothing raises here, so one
            walk reports the whole document.
    """
    hint = _unwrap_alias(hint)

    # `X | None` - absence is admitted, and the arm is checked when present.
    # Every union in this module is exactly one type or nothing; anything else
    # would be a shape the schema cannot express, so it is reported rather than
    # guessed at.
    if isinstance(hint, UnionType):
        arms = [arm for arm in get_args(hint) if arm is not type(None)]
        if value is None:
            return
        if len(arms) != 1:
            problems.append("%s: cannot check a %d-arm union" % (where, len(arms)))
            return
        _check_member(arms[0], value, where, pattern, pinned, problems)
        return

    # `tuple[X, ...]` - JSON carries it as an array; every element is checked
    # against the same element type and the same pattern.
    if get_origin(hint) is tuple:
        if not isinstance(value, list):
            problems.append(
                "%s: expected an array, found %s" % (where, type(value).__name__)
            )
            return
        element = get_args(hint)[0]
        for index, item in enumerate(value):
            _check_member(
                element, item, "%s[%d]" % (where, index), pattern, None, problems
            )
        return

    if isinstance(hint, type) and issubclass(hint, Enum):
        admitted = {member.value for member in hint}
        if not isinstance(value, str) or value not in admitted:
            problems.append(
                "%s: %r is not one of the %d values %s admits"
                % (where, value, len(admitted), hint.__name__)
            )
        return

    if isinstance(hint, type) and issubclass(hint, _JsonRecord):
        _check_record(hint, value, where, problems)
        return

    # A flag before a whole number, because `bool` is a subclass of `int` and
    # the two are not interchangeable in this document: a member declared as a
    # flag that arrives as 0 or 1 is a document written by something other than
    # this module's writer.
    if hint is bool:
        if not isinstance(value, bool):
            problems.append("%s: expected a flag, found %r" % (where, value))
        elif pinned is not None and value != pinned:
            problems.append("%s: expected the pinned %r, found %r"
                            % (where, pinned, value))
        return

    if hint is int:
        if isinstance(value, bool) or not isinstance(value, int):
            problems.append(
                "%s: expected a whole number, found %r" % (where, value)
            )
        elif pinned is not None and value != pinned:
            problems.append("%s: expected the pinned %r, found %r"
                            % (where, pinned, value))
        return

    if hint is str:
        if not isinstance(value, str):
            problems.append("%s: expected text, found %r" % (where, value))
            return
        if pinned is not None and value != pinned:
            problems.append("%s: does not carry the pinned value" % where)
            return
        if pattern is not None and pattern.match(value) is None:
            problems.append(
                "%s: %r does not match %s" % (where, value, pattern.pattern)
            )
        return

    problems.append("%s: no rule for declared type %r" % (where, hint))


def _check_record(
    record: type, obj: object, where: str, problems: list[str]
) -> None:
    """Hold one decoded object to the record class that will be built from it.

    The member set is checked in both directions: a member the record declares
    and the document omits is a document that cannot be read without inventing
    a default, which rule R-3 forbids; a member the document carries and the
    record does not declare is content this module cannot account for, and
    accepting it silently is how a forged addition would survive a round trip.
    """
    if not isinstance(obj, Mapping):
        problems.append(
            "%s: expected an object, found %s" % (where, type(obj).__name__)
        )
        return

    hints = _resolved_hints(record)
    declared = [member.name for member in fields(record)]

    for unknown in sorted(set(obj) - set(declared)):
        problems.append("%s: %s declares no member %r"
                        % (where, record.__name__, unknown))

    for name in declared:
        if name not in obj:
            problems.append("%s: missing member %r" % (where, name))
            continue
        qualified = "%s.%s" % (record.__name__, name)
        _check_member(
            hints[name],
            obj[name],
            "%s.%s" % (where, name),
            _PATTERN_BY_MEMBER.get(qualified),
            _PINNED_BY_MEMBER.get(qualified),
            problems,
        )


def _check_identifiers(obj: JsonObject, problems: list[str]) -> None:
    """Refuse a document that names any one thing twice.

    Every identifier in this document is meant to be unique, and every consumer
    relies on that: `loader.py` indexes entries by key so a repeated key would
    silently shadow a field's real metadata with another field's, and the same
    argument holds for a table named twice, an input digested twice or a binding
    rule stated twice. Uniqueness is not checkable after the fact, because a
    mapping keeps only the last of a repeated identity - so it is checked here,
    while the arrays are still arrays.
    """
    def report_repeats(where: str, label: str, identities: Sequence[str]) -> None:
        """Append one departure per identity that appears more than once."""
        counts: dict[str, int] = {}
        for identity in identities:
            counts[identity] = counts.get(identity, 0) + 1
        for identity in sorted(
            name for name, count in counts.items() if count > 1
        ):
            problems.append(
                "%s: %s %r appears %d times"
                % (where, label, identity, counts[identity])
            )

    def member_of_each(items: object, member: str) -> tuple[str, ...]:
        """Collect one text member from every object of an array."""
        return tuple(
            cast(str, item[member])
            for item in cast(Sequence[JsonObject], items)
        )

    sources = cast(JsonObject, obj["sources"])
    meta = cast(JsonObject, obj["meta"])
    coverage = cast(JsonObject, obj["coverage"])

    report_repeats(
        "$.entries", "entry key", member_of_each(obj["entries"], "key")
    )
    report_repeats(
        "$.tables", "table name", member_of_each(obj["tables"], "name")
    )
    report_repeats(
        "$.sources.input_digests",
        "source-manifest path",
        member_of_each(sources["input_digests"], "path"),
    )
    report_repeats(
        "$.meta.binding_rules",
        "binding rule",
        member_of_each(meta["binding_rules"], "id"),
    )
    report_repeats(
        "$.coverage.one_sided_entry_keys",
        "entry key",
        tuple(cast(Sequence[str], coverage["one_sided_entry_keys"])),
    )


def _check_internal_agreement(obj: JsonObject, problems: list[str]) -> None:
    """Refuse a document whose own parts disagree with each other.

    Three kinds of agreement are checked, all of them arithmetic or set
    comparison over the document itself and none of them a judgement about what
    the frozen sources ought to say:

    * a presence flag against the view it describes, and `one_sided` against all
      three flags together - the flags are what a consumer tests before reading
      a view, so a flag that disagrees with its view is the one inconsistency
      that reliably produces a wrong answer downstream rather than an error;
    * the coverage tallies against the entries actually present - these are the
      mechanical proof of the completeness claim rule R-5 rests on, and a tally
      that is merely asserted proves nothing;
    * each table's declared column count against the column entries recorded
      for it.
    """
    entries = cast(Sequence[JsonObject], obj["entries"])
    coverage = cast(JsonObject, obj["coverage"])
    sources = cast(JsonObject, obj["sources"])
    tables = cast(Sequence[JsonObject], obj["tables"])

    with_column = 0
    with_host_variable = 0
    with_copybook = 0
    flagged_one_sided: set[str] = set()
    columns_per_table: dict[str, int] = {}

    for entry in entries:
        key = cast(str, entry["key"])
        presence = cast(JsonObject, entry["presence"])
        views = (
            ("in_copybook", "copybook"),
            ("in_bridge", "bridge_host_variable"),
            ("in_column", "column"),
        )
        for flag, view in views:
            if bool(presence[flag]) != (entry[view] is not None):
                problems.append(
                    "$.entries[%r]: presence.%s says %r but %s is %s"
                    % (key, flag, presence[flag], view,
                       "absent" if entry[view] is None else "present")
                )
        if bool(entry["one_sided"]) != (
            not all(bool(presence[flag]) for flag, _ in views)
        ):
            problems.append(
                "$.entries[%r]: one_sided disagrees with its presence flags" % key
            )

        if entry["column"] is not None:
            with_column += 1
            table = cast(str, entry["table"])
            columns_per_table[table] = columns_per_table.get(table, 0) + 1
        if entry["bridge_host_variable"] is not None:
            with_host_variable += 1
        if entry["copybook"] is not None:
            with_copybook += 1
        if bool(entry["one_sided"]):
            flagged_one_sided.add(key)

    for member, actual, described in (
        ("entry_count", len(entries), "entries recorded"),
        ("columns_covered", with_column, "entries carrying a column view"),
        ("host_variables_covered", with_host_variable,
         "entries carrying a host-variable view"),
        ("copybook_fields_covered", with_copybook,
         "entries carrying a copybook view"),
        ("in_scope_tables", len(tables), "table records"),
        ("in_scope_bridges", len(cast(Sequence[object], sources["bridges"])),
         "bridge records"),
    ):
        if coverage[member] != actual:
            problems.append(
                "$.coverage.%s claims %r against %d %s"
                % (member, coverage[member], actual, described)
            )

    if coverage["columns_covered"] != coverage["in_scope_columns"]:
        problems.append(
            "$.coverage: %r columns covered of %r in scope - rule R-5 requires "
            "every in-scope column to have an entry"
            % (coverage["columns_covered"], coverage["in_scope_columns"])
        )

    if cast(int, coverage["in_scope_tables"]) + cast(
        int, coverage["out_of_scope_tables"]
    ) != coverage["schema_tables_total"]:
        problems.append(
            "$.coverage: in-scope and out-of-scope tables do not sum to the total"
        )

    schema_tables = cast(JsonObject, sources["schema"])["create_table_count"]
    if coverage["schema_tables_total"] != schema_tables:
        problems.append(
            "$.coverage.schema_tables_total claims %r against the %r tables the "
            "frozen dump declares"
            % (coverage["schema_tables_total"], schema_tables)
        )

    recorded_one_sided = set(
        cast(Sequence[str], coverage["one_sided_entry_keys"])
    )
    for key in sorted(recorded_one_sided - flagged_one_sided):
        problems.append(
            "$.coverage.one_sided_entry_keys: %r is listed but no entry is "
            "flagged one-sided" % key
        )
    for key in sorted(flagged_one_sided - recorded_one_sided):
        problems.append(
            "$.entries[%r]: flagged one-sided but absent from "
            "coverage.one_sided_entry_keys" % key
        )

    for table in tables:
        name = cast(str, table["name"])
        if columns_per_table.get(name, 0) != table["column_count"]:
            problems.append(
                "$.tables[%r]: column_count %r against %d column entries"
                % (name, table["column_count"], columns_per_table.get(name, 0))
            )


def _check_manifest_binding(obj: JsonObject, problems: list[str]) -> None:
    """Refuse a document whose source manifest does not bind to itself.

    `Meta.source_inputs_sha256` is computed over the whole manifest, so editing
    one recorded digest - to make a substituted input look accounted for -
    leaves this value disagreeing with the list it summarises. Recomputing it
    here costs one pass over a few dozen short strings and is the only part of
    the manifest that can be checked without reading the frozen sources
    themselves; confirming the digests against the bytes on disk is
    `generate.py --check`, which re-derives the entire document.
    """
    sources = cast(JsonObject, obj["sources"])
    meta = cast(JsonObject, obj["meta"])
    manifest = tuple(
        SourceDigest.from_json_obj(item)
        for item in cast(Sequence[JsonObject], sources["input_digests"])
    )
    recomputed = source_inputs_digest(manifest)
    if meta["source_inputs_sha256"] != recomputed:
        problems.append(
            "$.meta.source_inputs_sha256 does not bind the %d-entry source "
            "manifest it summarises" % len(manifest)
        )


def check_integrity(obj: JsonObject) -> None:
    """Hold a decoded dictionary document to everything this module declares, or raise.

    Args:
        obj: The parsed document, exactly as the standard-library JSON module
            produced it with `parse_float=str`.

    Raises:
        DictionaryIntegrityError: The document departs from the structure, value
            domains, patterns, pinned values, identifier uniqueness, internal
            agreement or manifest binding declared above. The message names
            every departure found, up to a bound, and always states the total.

    The structural walk runs first and alone: when a document's shape is wrong,
    the checks that read members by name and compare them arithmetically would
    report a second, larger and entirely derivative set of failures, which
    obscures the one fault that matters. Only a document that is structurally
    sound is asked whether it agrees with itself.
    """
    problems: list[str] = []
    _check_record(DataDictionary, obj, "$", problems)

    if not problems:
        _check_identifiers(obj, problems)
        _check_internal_agreement(obj, problems)
        _check_manifest_binding(obj, problems)

    if not problems:
        return

    shown = problems[:_MAX_REPORTED_PROBLEMS]
    elided = len(problems) - len(shown)
    report = "\n".join("  - %s" % problem for problem in shown)
    if elided:
        report += "\n  - ... and %d further departures" % elided
    raise DictionaryIntegrityError(
        "the data dictionary document does not hold up (%d departures):\n%s"
        % (len(problems), report)
    )



# =============================================================================
#  THE TWO DOORS - the whole document in, the whole document out
#  `generate.py` builds a `DataDictionary` and hands it to `to_json_obj`; the
#  standard-library JSON module writes the result under the settings named in
#  `Determinism`. `loader.py` parses the written file and hands the plain tree
#  to `from_json_obj`. Nothing else is needed in either direction, and nothing
#  else is offered: no partial read, no merge, no upgrade path, no repair.


def to_json_obj(dictionary: DataDictionary) -> dict[str, JsonValue]:
    """Convert the whole dictionary to a plain tree ready to be written.

    Args:
        dictionary: The dictionary to convert.

    Returns:
        A plain tree of objects, arrays, text, whole numbers, flags and nulls -
        nothing else. Object members appear in the order the JSON Schema
        declares them, because that is the order this module declares them in
        and the conversion walks declared members rather than sorting names.

    The written file's determinism follows from two things together: this
    function for the member order, and the writer's settings for the bytes. A
    writer must therefore emit with a two-space indent, a single trailing line
    ending, no byte-order mark, and WITHOUT asking the JSON module to sort keys
    - sorting would produce a valid but byte-different file and break the
    guarantee that two regenerations from an unchanged repository are identical
    (rule R-6).
    """
    return dictionary.to_json_obj()


def from_json_obj(obj: JsonObject) -> DataDictionary:
    """Build the whole dictionary from a parsed JSON document.

    Args:
        obj: The parsed document, exactly as the standard-library JSON module
            produced it.

    Returns:
        The document as an immutable tree of records.

    Raises:
        DictionaryIntegrityError: The document does not hold up as the document
            it claims to be. `check_integrity` runs FIRST, before a single
            record is built, so a document that has been substituted or edited
            never becomes an object any consumer could mistake for the real
            dictionary. See THE INTEGRITY PASS above for why holding the
            migration's own metadata artifact to its declared shape is required
            by rule R-5 rather than forbidden by rule R-3.

    The read adds nothing and forgives nothing: every member is fetched by
    name, no member has a fallback, and no value is coerced or widened. A
    document missing a member the schema requires fails here, loudly, rather
    than being quietly completed with a default that no frozen source supports
    (rule R-3). Reading back what this module wrote and writing it again
    reproduces the same bytes.
    """
    check_integrity(obj)
    return DataDictionary.from_json_obj(obj)


#  PUBLIC SURFACE
#  Constants first, then the string domains, then the records, then the two
#  doors - each group in alphabetical order. Everything else in this module is
#  private conversion machinery and is deliberately absent: `_JsonRecord`,
#  `_record_to_json_obj` and `_json_value` are how the determinism rule is
#  written once, not part of what this module offers.

__all__: Final[tuple[str, ...]] = (
    # Patterns published for the generator and the test suites to check with,
    # and applied by this module's own integrity pass on the way in - see THE
    # INTEGRITY PASS for why that is provenance control under rule R-5 and not
    # new validation under rule R-3.
    "AMBIGUITY_REF_PATTERN",
    "ANOMALY_REF_PATTERN",
    "BINDING_RULE_ID_PATTERN",
    "BRIDGE_KEY_TYPE_PATTERN",
    "BRIDGE_NAME_PATTERN",
    "COLUMN_NAME_PATTERN",
    "COPYBOOK_LEVEL_PATTERN",
    "DECLARED_LENGTH_PATTERN",
    "DICTIONARY_VERSION_PATTERN",
    "ENTRY_KEY_PATTERN",
    "HANDLER_NAME_PATTERN",
    "HV_GROUP_NAME_PATTERN",
    "HV_GROUP_SUFFIX_PATTERN",
    "HV_NAME_PATTERN",
    "REPO_PATH_PATTERN",
    "SHA256_PATTERN",
    "SOURCE_LOCATOR_PATTERN",
    "TABLE_NAME_PATTERN",
    # The fixed values the schema pins to one literal each.
    "DETERMINISM_BYTE_ORDER_MARK",
    "DETERMINISM_ENCODING",
    "DETERMINISM_INDENT",
    "DETERMINISM_NEWLINE",
    "DETERMINISM_TRAILING_NEWLINE",
    "DICTIONARY_AUTHORITY",
    "DICTIONARY_GENERATED_BY",
    "DICTIONARY_NAME",
    "DICTIONARY_SCHEMA_REF",
    # The string domains, each carrying the shape its pattern above describes.
    "BridgeName",
    "EntryKey",
    "HandlerName",
    "JsonObject",
    "JsonValue",
    "RepoPath",
    "SourceLocator",
    "TableName",
    # The enumerations.
    "CobolPythonStorage",
    "DerivationKind",
    "EntityFacade",
    "SignPosition",
    "SqlBaseType",
    "Usage",
    "UsageDeclaredAt",
    # The records: the three views of the authoritative triple plus the
    # program-source view, the cross-view facts, the entry, the frozen inputs,
    # the contracts, the tallies and the root.
    "ArrayOrder",
    "BindingRule",
    "BridgeHostVariable",
    "BridgeKey",
    "BridgeSource",
    "BridgeTableRef",
    "ConditionName",
    "CopybookField",
    "CopybookSource",
    "Coverage",
    "DataDictionary",
    "Derivation",
    "DerivationRules",
    "Determinism",
    "DictionaryEntry",
    "Drift",
    "Meta",
    "MysqlColumn",
    "NumericTypeCensus",
    "Presence",
    "ProgramSourceRecord",
    "SchemaSource",
    "SourceDigest",
    "Sources",
    "TableRecord",
    # The integrity pass: the failure it raises, the check the door performs,
    # and the two functions that define what the source-manifest digest is
    # taken over - published so `generate.py` computes the value the reader
    # recomputes, from one implementation rather than two.
    "DictionaryIntegrityError",
    "check_integrity",
    "source_inputs_digest",
    "source_inputs_digest_material",
    # The two doors.
    "from_json_obj",
    "to_json_obj",
)
