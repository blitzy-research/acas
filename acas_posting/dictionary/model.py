"""The data-dictionary object model: the copybook / bridge / column triple.

One `DictionaryEntry` per field, carrying up to three views of it - the copybook
field as declared, the bridge host variable it is loaded into, and the MySQL
column it reaches - plus the facts that hold BETWEEN them.

A view may legitimately be absent, and absence is a recorded fact rather than an
error: a copybook field the bridge never carries has no host variable and no
column, and a column the bridge derives has no copybook field. `Presence` says
which views exist, `Drift` says where they disagree in name, width, digits, sign
or storage class, and `Derivation` says how a bridge-only column is computed.

Nothing here adjudicates a disagreement. The three views stand side by side
because the migration needs each of them for a different purpose: the copybook
governs what a field IS, the bridge governs which column it reaches, and the
column governs what a state comparison sees.
"""

# Every member below is derived from one of four frozen inputs.

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

# The plain-tree form of the artifact, written out as a type so that the numeric policy
# of rule R-2 is visible in the type system rather than only in prose.

type JsonValue = str | int | bool | None | list[JsonValue] | dict[str, JsonValue]
"""One value of the artifact in plain-tree form. No binary-approximation member."""

type JsonObject = Mapping[str, Any]
"""One object of the artifact as decoded from JSON, before it is mapped to a record.

`Any` marks the boundary where the document is still untyped. Nothing past
that boundary coerces: a member is read and placed in its record exactly as it
was recorded, and a member that is absent raises rather than acquiring a
default (rule R-3).
"""


# The schema constrains several string members by pattern.

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
"""One segment of a repository-relative path, used to build the two path patterns below.

The consequences are worth spelling out, because each of them is a way a path member
could otherwise name a file outside the repository or name the same file two different
ways.
"""

REPO_PATH_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^%s(/%s)*$" % (_PATH_SEGMENT, _PATH_SEGMENT)
)
"""Shape of every path member: one or more segments joined by single forward slashes,
relative to the repository root and CONTAINED WITHIN IT.

An absolute path would encode the machine that wrote the artifact and is forbidden
content (rule R-6), so the leading character may not be a separator.
"""

SOURCE_LOCATOR_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^%s(/%s)*:L[0-9]+(-L[0-9]+)?$" % (_PATH_SEGMENT, _PATH_SEGMENT)
)
"""Shape of every `source` member: a repository-relative path, a colon, then a single line
as `L<n>` or an inclusive span as `L<n>-L<m>`.

The path half is exactly `REPO_PATH_PATTERN`, and is contained for the same reason: a
citation is the mechanism rule R-5 rests on, and a citation that can point outside the
repository is one a reader cannot check.
"""

ENTRY_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9-]*\.[A-Za-z0-9][A-Za-z0-9-]*"
    r"(@[A-Za-z0-9][A-Za-z0-9-]*)?(#[0-9]+)?$"
)
"""Shape of `DictionaryEntry.key`: `<record>.<field>`, with two optional tails that
disambiguate rather than describe.

`@<file stem>` names the DECLARING FILE, and appears only on the second and later
physical declarations of one signature. Two copybooks in the closure are variants of one
layout - copybooks/plwsoi5B.cob and copybooks/plwsoi5C.cob differ only in whether a single
COPY is commented out - so they declare the same items at the same lines. Rule R-5 binds
every field to an entry, and each of those declarations is a field a reader can point at,
so each gets its own entry; the first in closure order keeps the unqualified key and the
rest carry this tail.

`#<n>` disambiguates a field name that repeats inside one record - `filler` occurs four
times in copybooks/wsledger.cob - by appending its declaration line. Both tails may occur
together, file stem first, in the order the generator appends them.
"""

TABLE_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z][A-Z0-9-]*$")
"""Shape of a table name."""

BRIDGE_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9]*MT$")
"""Shape of a bridge name."""

HANDLER_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(acas[0-9]{3}|acasirsub[0-9])$"
)
"""Shape of a handler name. Both conventions occur: the numbered handlers the General,
Sales and Purchase programs call, and the IRS subroutine handlers.
"""

COPYBOOK_LEVEL_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(0[1-9]|[1-4][0-9])$")
"""Shape of `CopybookField.level`: a two-character token, leading zero kept. An 88-level
condition name is NOT a level here - it is carried by `CopybookField.condition_names` on
the field it qualifies.
"""

HV_GROUP_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^TD-[A-Z][A-Z0-9-]*$")
"""Shape of a host-variable group name: `TD-` followed by the table name."""

HV_GROUP_SUFFIX_PATTERN: Final[re.Pattern[str]] = re.compile(r"^HV[0-9]?$")
"""Shape of a host-variable group suffix. Only two values occur across the twenty in-scope
bridges: `HV`, and `HV1` for the lines table of a two-table bridge
[common/slinvoiceMT.scb:L381-L385].
"""

HV_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^HV[0-9]?-[A-Z0-9][A-Z0-9-]*$")
"""Shape of a host-variable name, prefix included and never rewritten."""

COLUMN_NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9][A-Z0-9-]*$")
"""Shape of a column name as it appears between backticks in the frozen dump."""

BRIDGE_KEY_TYPE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Z]{3}$")
"""Shape of a bridge key-type literal. Two occur in scope: `STR`, annotated in the source
as key is string [common/glpostingMT.scb:L234], and `BNT`.
"""

ANOMALY_REF_PATTERN: Final[re.Pattern[str]] = re.compile(r"^A-([1-9]|1[0-9]|2[0-2])$")
"""Shape of an anomaly reference - `A-` and the register number, 1 to 22."""

AMBIGUITY_REF_PATTERN: Final[re.Pattern[str]] = re.compile(r"^Q-[0-9]+$")
"""Shape of an ambiguity reference - `Q-` and the register number."""

DECLARED_LENGTH_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9]+$")
"""Shape of one element of `CopybookSource.declared_lengths`: a digit string."""

DICTIONARY_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+$"
)
"""Shape of `Meta.dictionary_version`. It advances with the dictionary's CONTENT and
carries no relation to elapsed time.
"""

BINDING_RULE_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^R-[1-6]$")
"""Shape of `BindingRule.id` - the six rules that govern this migration."""

SHA256_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[0-9a-f]{64}$")
"""Shape of a SHA-256 digest as this document records it: sixty-four lower-case hexadecimal
characters, no prefix and no separator.
"""


# Each of these is a value the schema allows to be one thing only.

DICTIONARY_NAME: Final[str] = "acas_posting_dictionary"
"""`Meta.dictionary_name` - the stem shared by the artifact and its schema."""

DICTIONARY_SCHEMA_REF: Final[str] = "acas_posting_dictionary.schema.json"
"""`Meta.schema_ref` - a bare relative name, deliberately not a URL, so that nothing ever
attempts to fetch a schema over a network (rule R-1).
"""

DICTIONARY_GENERATED_BY: Final[str] = "acas_posting/dictionary/generate.py"
"""`Meta.generated_by` - the only module that may produce the artifact. A dictionary
produced by anything else could not be reproduced from the frozen sources, and
reproducibility is the property being protected (rule R-6).
"""

DICTIONARY_AUTHORITY: Final[str] = (
    "The maintainer's one-way COBOL-to-MySQL bridge defines the authoritative "
    "record-layout \u2194 table mapping - it is the data dictionary for this "
    "migration."
)
"""`Meta.authority` - the user requirement the dictionary rests on, carried verbatim and
pinned so it cannot be paraphrased into something weaker. The arrow is U+2194 LEFT RIGHT
ARROW, exactly as the requirement writes it.
"""

DETERMINISM_ENCODING: Final[str] = "utf-8"
"""`Determinism.encoding` - how the artifact is written."""

DETERMINISM_NEWLINE: Final[str] = "LF"
"""`Determinism.newline`. A carriage-return pair would change the bytes of the artifact
while parsing identically, which is the class of difference the determinism contract
exists to eliminate.
"""

DETERMINISM_INDENT: Final[int] = 2
"""`Determinism.indent` - spaces per level, spaces and never tabs."""

DETERMINISM_TRAILING_NEWLINE: Final[bool] = True
"""`Determinism.trailing_newline` - exactly one, at the end of the artifact."""

DETERMINISM_BYTE_ORDER_MARK: Final[bool] = False
"""`Determinism.byte_order_mark` - a mark would change the bytes without changing the
content.
"""


# Each one mirrors an `enum` in the schema, member for member and value for value. They
# are `StrEnum`, so a member IS its recorded string.


class Usage(StrEnum):
    """The COBOL storage class in force for an item - `cobolUsage` in the schema.

    All six storage classes the in-scope record layouts actually use are kept distinct,
    because collapsing any of them changes the value that reaches the database.
    Signedness is NOT carried here.
    """

    DISPLAY = "DISPLAY"
    """Zoned decimal - declared by the ABSENCE of any usage clause, as every numeric field
    of copybooks/wspost.cob:L13-L28 is.
    """

    COMP = "COMP"
    """Binary within the range the picture declares - `pic 99v99 comp`
    [copybooks/wssl.cob:L42], `pic 9(5) comp` [copybooks/wsfnctn.cob:L24], and at group
    level `05 Vat-Rates comp.` [copybooks/wssystem.cob:L55], whose five subordinate `pic
    99v99` items inherit it.
    """

    COMP_3 = "COMP-3"
    """Packed decimal, declared both on the field [copybooks/wsledger.cob:L28] and on the
    group - `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40], `03 Sales-Ledger-Data
    comp-3.` [copybooks/wssys4.cob:L9], `03 Purchase-Ledger-Data comp-3.`
    [copybooks/wssys4.cob:L20].
    """

    COMP_5 = "COMP-5"
    """Native binary. It appears in bridge working storage - `01 subscripts usage comp-5.`
    [common/glpostingMT.scb:L256] - and is listed so that the vocabulary covers the
    frozen sources completely.
    """

    BINARY_CHAR = "BINARY-CHAR"
    """The one-byte member of the native binary family [copybooks/wssystem.cob:L53-L54],
    including the `unsigned` form at [copybooks/wssystem.cob:L65].
    """

    BINARY_SHORT = "BINARY-SHORT"
    """The two-byte member [copybooks/wssl.cob:L43-L44]. Note that the maintainer's
    trailing comment there says `9999 comp`, which describes four digits while the
    declaration is a 16-bit integer.
    """

    BINARY_LONG = "BINARY-LONG"
    """The four-byte member [copybooks/wssl.cob:L45-L53], [copybooks/wsbatch.cob:L36-L39],
    and `Run-Date binary-long` [copybooks/wssystem.cob:L67]. Signed unless `unsigned` is
    written, which is why the sales statistics fields are signed and their host
    variables are not.
    """

    POINTER = "POINTER"
    """The `TP-` item each bridge declares beside its host-variable group - `01 TP-
    GLPOSTING-REC USAGE POINTER.` [common/glpostingMT.cbl:L280].
    """

    ALPHANUMERIC = "ALPHANUMERIC"
    """`PIC X(n)`. COBOL itself classes this as usage display; the dictionary separates it
    so that `cobol_python_storage` can select text without re-parsing the picture.
    """

    GROUP = "GROUP"
    """An item with subordinate items and no picture of its own - including a group that
    carries the usage its children inherit.
    """


class SignPosition(StrEnum):
    """Where the sign of a signed item lives - `signPosition` in the schema.

    Kept separate from `Usage` because one usage carries different sign placements, and
    because the placement is what a consumer needs in order to read or write the field's
    bytes.
    """

    NONE = "NONE"
    """The item is unsigned."""

    TRAILING_INCLUDED = "TRAILING_INCLUDED"
    """The COBOL default for a signed display item written `S9(n)V9(m)` with no sign
    clause: the sign overpunches the last digit [copybooks/wspost.cob:L23].
    """

    LEADING_INCLUDED = "LEADING_INCLUDED"
    """The `SIGN LEADING` form."""

    LEADING_SEPARATE = "LEADING_SEPARATE"
    """The `SIGN LEADING SEPARATE CHARACTER` form, listed for completeness of the
    vocabulary.
    """

    TRAILING_SEPARATE = "TRAILING_SEPARATE"
    """The `SIGN TRAILING SEPARATE CHARACTER` form, likewise."""

    IMPLICIT_BINARY = "IMPLICIT_BINARY"
    """The sign of a signed `COMP`, `COMP-3`, `COMP-5` or binary-family item, where it is
    part of the packed or binary representation rather than a character position.
    """


class UsageDeclaredAt(StrEnum):
    """Where the generator found the usage it recorded - `usageDeclaredAt`.

    This is the highest-risk fact in the whole dictionary, and it is not decoration.
    COBOL lets a group declare usage and every subordinate item inherit it.
    """

    FIELD = "FIELD"
    """The usage clause is on the item's own declaration."""

    GROUP = "GROUP"
    """The usage was inherited from an ancestor group, which `usage_inherited_from` names
    and `usage_group_source` cites.
    """

    DEFAULT = "DEFAULT"
    """No usage clause governs the item anywhere, so COBOL's own default of zoned display
    applies.
    """


class CobolPythonStorage(StrEnum):
    """The Python type for the COBOL-side value - `cobolPythonStorage`.

    It is NOT a settlement of any disagreement between the three views, and it must
    never be read in place of them.
    """

    DECIMAL = "DECIMAL"
    """Any numeric item with a non-zero scale, and packed or zoned money. Carried in Python
    by the exact type of the `decimal` module, never by a binary approximation (rule
    R-2).
    """

    INT = "INT"
    """The binary integer family and zero-scale integers. This is the value that makes the
    legacy moving-average defect reproducible: the sales statistics fields are `binary-
    long` [copybooks/wssl.cob:L45-L53], so their truncation on divide is integer
    truncation.
    """

    STR = "STR"
    """An alphanumeric item."""

    NONE = "NONE"
    """A group item, or an entry that has no copybook view at all - as the three bridge-
    derived IRS date components do not.
    """


class SqlBaseType(StrEnum):
    """A column's SQL base type, width and unsigned suffix removed.

    The vocabulary is exactly the seven base types the frozen dump uses and no others.
    The three binary floating-point SQL types are OMITTED, which makes a binary
    floating-point column unrepresentable rather than merely discouraged.
    """

    DECIMAL = "DECIMAL"
    """Exact-decimal storage. Every monetary column in the posting cycle is one of these -
    `POST-AMOUNT decimal(10,2)` [mysql/ACASDB.sql:L163] - which is why the driver must
    materialise them as exact values.
    """

    INT = "INT"
    """A four-byte integer column - `int(8) unsigned` [mysql/ACASDB.sql:L123]."""

    TINYINT = "TINYINT"
    """A one-byte integer column - `tinyint(2) unsigned` [mysql/ACASDB.sql:L278]."""

    SMALLINT = "SMALLINT"
    """A two-byte integer column."""

    MEDIUMINT = "MEDIUMINT"
    """A three-byte integer column - `mediumint(5) unsigned` [mysql/ACASDB.sql:L155]."""

    BIGINT = "BIGINT"
    """An eight-byte integer column - `bigint(10) unsigned` [mysql/ACASDB.sql:L156]. A
    SIGNED one occurs too, `bigint(11)` with no unsigned suffix [mysql/ACASDB.sql:L367],
    so `unsigned` is genuinely per column and not a property of the base type.
    """

    CHAR = "CHAR"
    """A fixed-width character column - `char(32)` [mysql/ACASDB.sql:L127]. Trailing
    padding is significant when two table states are compared, which is why the state
    normaliser evens it out.
    """


class DerivationKind(StrEnum):
    """How a column's value comes to exist - `derivation.kind` in the schema."""

    BRIDGE_DERIVED = "BRIDGE_DERIVED"
    """The bridge computes the value from other record data. This is how IRSPOSTING-REC
    acquires POST4-DAY, POST4-MONTH and POST4-YEAR - three columns with no counterpart
    in any copybook, derived under a guard at [common/irspostingMT.cbl:L982-L987].
    """

    GROUP_CONCATENATION = "GROUP_CONCATENATION"
    """A copybook group is moved whole into one host variable and hence one column, as the
    two five-digit children of `WS-Post-Key` [copybooks/wspost.cob:L14-L16] are moved
    into `HV-POST-KEY PIC 9(18) COMP` [common/glpostingMT.cbl:L283] at
    [common/glpostingMT.cbl:L1054].
    """

    REDEFINES_ALTERNATIVE = "REDEFINES_ALTERNATIVE"
    """The column corresponds to a redefines view of the storage rather than to the
    original declaration, as with the eight-digit redefinition of the ledger key group
    [copybooks/wsledger.cob:L21-L22].
    """


class EntityFacade(StrEnum):
    """The entity facade the posting programs address a table through."""

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
    copybooks/wspost-irs.cob:L6-L7 says in as many words that it "is NOT the same as the
    internal IRS posting file".
    """

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


# `_JsonRecord` gives every record below one shared way out to the plain-tree form, and
# that one way is driven by `dataclasses.fields()`, which yields members in DECLARATION
# ORDER.


class _JsonRecord:
    """Shared plain-tree conversion for every record in this module.

    Not part of the artifact and not a member of anything: it exists so that the
    declaration-order rule is written once rather than reimplemented on twenty-two
    records, each of which could then drift from the schema independently.
    """

    __slots__ = ()

    def to_json_obj(self) -> dict[str, JsonValue]:
        """Return this record as a plain object, members in declaration order.

        Enumeration members become their recorded string, nested records become nested
        objects, tuples become arrays, and `None` becomes JSON null.
        """
        return _record_to_json_obj(self)


def _record_to_json_obj(record: _JsonRecord) -> dict[str, JsonValue]:
    """Convert one record to a plain object, walking its declared members in order."""
    return {
        member.name: _json_value(getattr(record, member.name))
        for member in fields(record)
    }


def _json_value(value: object) -> JsonValue:
    """Convert one member value to its plain-tree form.

    The enumeration test comes FIRST and deliberately so: every enumeration here is a
    `StrEnum`, so its members are also strings, and testing for a string first would
    emit the member object rather than its value.
    """
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, _JsonRecord):
        return _record_to_json_obj(value)
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    # What remains is already one of the JSON scalars this module admits - text, a
    # dimensionless count, a flag or absence.
    return cast(JsonValue, value)


@dataclass(frozen=True, slots=True)
class ConditionName(_JsonRecord):
    """One 88-level condition name declared on a copybook field.

    `acas_posting/cobol/condition_names.py` turns each of these into a predicate over
    its record, because the posting cycle tests the NAMES rather than raw values.

    Attributes:
        name: The condition name exactly as declared, its case preserved - `Status-
            Open`, `Waiting`, `GL-Batch`, `IRS-Used`, `IRS-Both-Used`.
        value: The value-clause text exactly as written, INCLUDING the figurative-
            constant spelling where one is used, and always text rather than a number.
            Two reasons.
        source: The copybook line that declares the condition name.
    """

    name: str
    value: str
    source: SourceLocator

    @classmethod
    def from_json_obj(cls, obj: JsonObject) -> Self:
        """Build one condition name from its recorded object.

        Reads exactly the members the schema declares. A member that is absent raises
        rather than acquiring a default, because a silently defaulted member would be an
        assertion about a frozen source that the source never made (rule R-3).
        """
        return cls(
            name=obj["name"],
            value=obj["value"],
            source=obj["source"],
        )


@dataclass(frozen=True, slots=True)
class CopybookField(_JsonRecord):
    """THE COPYBOOK VIEW: the field as the frozen COBOL record layout declares it.

    Every member records what the copybook SAYS, never what it ought to say. A picture
    that disagrees with the host variable or the column stays exactly as declared, and
    the disagreement is flagged in `DictionaryEntry.drift` instead (rule R-4).

    Attributes:
        file: The source that declares the field. A copybook for the copybook view, for
            example `copybooks/wsledger.cob`; a program for the program-source view, for
            example `general/gl071.cbl`.
        source: The line or span in that file where it is declared.
        name: The data-name exactly as declared, mixed case preserved. `filler` is
            recorded rather than dropped, because it consumes record positions.
        level: The level number as written, leading zero kept - a level is a
            two-character COBOL token, not an arithmetic quantity.
        picture: The picture clause exactly as written, or null when the item has
            none; null is not an omission.
        usage: The storage class in force, declared or inherited.
        usage_declared_at: Whether it was on the item, inherited, or left to default.
        usage_inherited_from: The ancestor group whose usage clause the item inherits,
            or null when nothing is inherited. `Amounts` for the four batch amount
            fields [copybooks/wsbatch.cob:L40].
        usage_group_source: The line that declares the inherited usage clause, or null.
        signed: Whether the copybook declares the item signed - an `S` in the picture,
            or a binary-family item without `unsigned`. Load-bearing.
        sign_position: Where the sign sits, or `NONE`. Recorded for every field.
        sign_clause_text: The sign clause exactly as spelled, or null when the item
            declares none.
        digits: Total decimal digit positions declared, excluding sign and implied
            point. Null only where there is no numeric picture.
        integer_digits: Digit positions left of the implied decimal point, so that
            `digits` minus `integer_digits` is `scale`.
        scale: Digit positions right of the implied decimal point - the `V` in the
            picture. A zero here is a real value, never a missing one: the
            moving-average accumulators the Sales and Purchase programs maintain are
            declared with no decimal places while the amounts added into them carry two,
            which is what makes the legacy double truncation reproducible.
        character_length: Declared characters for an alphanumeric item or stated bytes
            for a group; null for a numeric item.
        redefines: The data-name this item redefines, or null. Never dropped.
        occurs: The occurs count for a table item, or null.
        is_filler: True when the item is declared as `filler`. Filler entries are kept.
        is_group: True when the item has subordinate items and therefore no picture of
            its own.
        parent_group: The immediately containing group item, or null for the 01-level
            record itself.
        condition_names: Every 88-level condition name declared on the field, in
            declaration order, never summarised into a single flag.
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

        The three enumerated members - `usage`, `usage_declared_at` and `sign_position`
        - are mapped back through their own vocabularies, so a value the frozen sources
        never use cannot enter a record here. Everything else is placed exactly as
        recorded.
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


@dataclass(frozen=True, slots=True)
class BridgeHostVariable(_JsonRecord):
    """THE BRIDGE VIEW: the host variable the generated bridge program declares.

    The conversion this layer performs is NOT transparent and has to be reproduced by
    the data-access layer rather than left to the database.

    Attributes:
        file: The generated bridge program that declares the host variable, for example
            `common/glpostingMT.cbl`.
        source: The line in that program where the host variable is declared.
        hv_group_name: The 01-level group containing it - `TD-` followed by the table
            name. Each bridge declares a matching `TP-` pointer item beside it
            [common/glpostingMT.cbl:L280-L281].
        hv_group_suffix: The suffix the bridge's own table directive assigns that group,
            which is what tells the groups apart when one bridge serves two tables.
        name: The host-variable name exactly as declared, upper case, prefix included
            and never rewritten.
        picture: The host variable's picture and usage text as the bridge declares it.
            Text, never a number (rule R-2).
        usage: Its storage class.
        signed: Whether the host-variable picture carries an `S`. This is the member
            that exposes the narrowing.
        digits: Total declared digit positions, or null for a character host variable.
        integer_digits: Digit positions left of the implied decimal point, or null.
            Comparing this against the copybook view is how digit widening is detected.
        scale: Digit positions right of the implied decimal point, or null.
        character_length: Declared length for a `PIC X(n)` host variable, or null for a
            numeric one.
        loaded_from_record: Whether the load section actually moves the record field
            into this host variable before a write. FALSE IS A REAL AND DELIBERATE
            VALUE.
        load_source: The line of the load section that performs that move, or null when
            there is none.
        unloaded_to_record: Whether the unload section moves the host variable back into
            the record after a read. False for a bridge-derived column: the three IRS
            date components are loaded on write and never unloaded, because the record
            has nowhere to put them [common/irspostingMT.cbl:L1017-L1018].
        unload_source: The line of the unload section that performs that move, or null
            when there is none.
        group_initialised_before_load: Whether the bridge issues an initialise over the
            whole host-variable group before its first move, as every in-scope bridge
            does [common/glpostingMT.cbl:L1053], [common/irspostingMT.cbl:L966].
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


@dataclass(frozen=True, slots=True)
class MysqlColumn(_JsonRecord):
    """THE COLUMN VIEW: the column as the frozen schema dump declares it.

    The schema is frozen, so this view DESCRIBES it and never proposes a change to it.
    That is why there is no member here for a suggested type, a widened field or a data
    definition statement of any kind.

    Attributes:
        file: The frozen schema file that declares the column - in practice always
            `mysql/ACASDB.sql`, the only schema file the posting cycle touches.
        source: The line of the table declaration where the column appears.
        name: The column name exactly as it stands between backticks in the dump, upper
            case with hyphens.
        sql_type: The column's type text copied verbatim, display width and unsigned
            suffix included, nullability and comment excluded because those have their
            own members.
        base_type: The base type with the width and the unsigned suffix removed.
        display_width: The parenthesised width of an integer type, the precision of an
            exact-decimal type, or the character count of a fixed-width text type.
        scale: The second parenthesised argument of an exact-decimal type - the digits
            kept to the right of the point - or null for any other type.
        unsigned: Whether the declaration carries the unsigned suffix. Compared against
            the copybook and bridge views to expose the signedness drift that costs a
            negative value its sign.
        nullable: Whether the column permits SQL null. All 720 columns of the frozen
            dump are declared not null, so this normally carries false throughout.
        column_default: The text of the column's default clause exactly as written, or
            null when it declares none. Recording it changes nothing and proposes
            nothing (rule R-3).
        is_primary_key: Whether the column is the table's primary key.
        ordinal: The column's one-based position within its table declaration.
        comment: The text of the column's comment clause without its quotes, or null.
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


@dataclass(frozen=True, slots=True)
class Presence(_JsonRecord):
    """Which of the four sources a field was found in.

    This is where the one-sided rule lives.

    Attributes:
        in_copybook: True when a copybook declares the field.
        in_bridge: True when a bridge declares a host variable for it.
        in_column: True when the frozen schema declares a column for it.
        in_program_source: True when a program's own FILE SECTION declares the field -
            the General Ledger work files `pretrans.tmp` and `postrans.tmp` and the sort
            file that carries them between phases, declared inline in
            [general/gl070.cbl], [general/gl071.cbl] and [general/gl072.cbl] and named
            as work files at [copybooks/wsnames.cob:L15-L16].
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

    THIS RECORD IS HOW RULE R-4 IS HONOURED STRUCTURALLY. Because no member anywhere in
    an entry names a single winning type, a generator cannot quietly reconcile the
    views.

    Attributes:
        signedness: True when the views disagree about whether the value is signed. The
            consequence is real.
        usage: True when the storage class changes between views - a leading-sign zoned
            field in the copybook [copybooks/irswspost.cob:L14], a binary host variable
            in the bridge and an exact-decimal column in the database are three
            representations of one value.
        digits: True when the total or integer digit count differs, as with the batch
            amount fields declared with nine integer digits in the copybook
            [copybooks/wsbatch.cob:L41] and twelve in both the host variable
            [common/glbatchMT.cbl:L291] and the column.
        scale: True when the number of fractional digits differs. Kept apart from
            `digits` because a scale difference changes rounding and truncation
            behaviour rather than range.
        character_length: True when the declared character length differs, as with the
            ledger name at twenty-four characters in the copybook
            [copybooks/wsledger.cob:L27] and thirty-two in both the host variable
            [common/nominalMT.cbl:L299] and the column [mysql/ACASDB.sql:L127].
        name: True when the copybook data-name, the host-variable name with its prefix
            removed, and the column name are not all one identifier.
        details: One short sentence per disagreement, naming the views involved and what
            each of them says, so the record reads without cross-referencing three
            files.
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

    `DictionaryEntry.derivation` is null when the mapping IS a plain move.

    Attributes:
        kind: Which kind of derivation this is.
        expression: The COBOL text that performs it, quoted closely enough that a reader
            can match it in the frozen source. Text, always.
        guard: The condition the derivation is performed under, verbatim, or null when
            it is unconditional.
        guard_failure_behaviour: What is stored when the guard fails, or null when there
            is no guard.
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


@dataclass(frozen=True, slots=True)
class DictionaryEntry(_JsonRecord):
    """ONE AUTHORITATIVE TRIPLE: one field seen from all three layers at once.

    The entry is the dictionary's unit of traceability.

    Attributes:
        key: The stable identifier this entry is cited by from
            `acas_posting/cobol/field.py` and from every module under
            `acas_posting/records/`.
            The name is left unaltered - hyphens are not turned into underscores and
            case is not folded - so a key can be searched for in the COBOL and in the
            schema exactly as it stands.
        table: The in-scope table this entry belongs to, or null for a copybook-only
            field that maps to no table.
        bridge: The in-scope bridge pair that maps the field, or null when no bridge
            carries it.
        handler: The file handler the posting programs call to reach the table, or null.
        entity_facade: The facade the posting programs address the table through, or
            null when the entry belongs to none.
        presence: Which of the four sources declare the field. A false here is what
            makes a one-sided field visible instead of absent.
        one_sided: True when the field is not present in all three layers of the
            authoritative triple - the negation of `in_copybook` and `in_bridge` and
            `in_column`.
        copybook: THE COPYBOOK VIEW, or null when no copybook declares the field. Null
            is expected, not exceptional.
        program_source: THE PROGRAM-SOURCE VIEW, or null - which it is for every entry
            except the work-file fields described above.
        bridge_host_variable: THE BRIDGE VIEW - the authoritative one - or null when no
            bridge carries the field.
        column: THE COLUMN VIEW, or null when the field reaches no column. Null for
            every copybook-only field.
        drift: The disagreements between whichever views are present. Always present,
            even when every flag is false, so that agreement is asserted rather than
            assumed.
        derivation: How the value comes to exist when the mapping is not a plain field-
            for-field move, or null when it is.
        cobol_python_storage: The Python type for the COBOL-side value, derived only
            from the declaring view's `usage` and `scale` - the copybook view where
            there is one, the program-source view otherwise - so that the choice between
            the exact-decimal type and `int` is data-driven (rule R-2).
        notes: Observations about this field, one per element, may be empty. This is
            where a fact with no dedicated member is recorded rather than lost.
        anomaly_refs: Identifiers of the entries this field participates in within the
            migration's anomaly log, may be empty.
        ambiguity_refs: Identifiers of the entries in the migration's ambiguity-
            resolutions log that bear on this field, may be empty.
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

        Each of the five nullable object members is read once and mapped only when it is
        present, so a null view stays a null view.
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


@dataclass(frozen=True, slots=True)
class BridgeTableRef(_JsonRecord):
    """One table named by a bridge's own table directive, with its host-variable group.

    A bridge may name more than one table, which is why `BridgeSource.tables` is an
    array rather than a single value: the sales and purchase invoice bridges each map a
    header table and a lines table [common/slinvoiceMT.scb:L381-L385].

    Attributes:
        name: The table named in the directive.
        hv_group_suffix: The suffix the directive assigns that table's host-variable
            group - `HV` for a single-table bridge or the header table of a two-table
            bridge, `HV1` for the lines table.
        hv_group_name: The 01-level group the generated program emits for it, `TD-`
            followed by the table name.
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

    This is the metadata the data-access layer needs in order to EMULATE the indexed-
    file start and read-next verbs rather than merely issue equivalent SQL. The COBOL
    comment beside the table states the constraint that makes it necessary
    [common/glpostingMT.scb:L243-L245].

    Attributes:
        name_in_rdb: The key's column name in the database as the key-name table spells
            it, with the declaration's trailing padding removed.
        offset: The key's one-based starting position within the working-storage record,
            taken from the FIRST FOUR digits of that literal. A position, not a
            magnitude (rule R-2).
        length: The key's length in record positions, taken from the LAST FOUR digits of
            the same literal.
        type: The three-character key-type literal. Two occur across the in-scope
            bridges - `STR`, annotated in the source as key is string, and `BNT`,
            annotated as key is bigint.
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

    Recorded because the bridge is the authoritative mapping layer, and BOTH members of
    the pair are cited.

    Attributes:
        scb_path: The bridge source the vendored translator consumes, for example
            `common/glpostingMT.scb`.
        cbl_path: The generated bridge program that is actually compiled, for example
            `common/glpostingMT.cbl`.
        base: The database named in the bridge's own base directive.
        directive_source: The span of the live table-directive block in the `.scb`,
            which is the authority for the table-to-host-variable-group mapping
            [common/glpostingMT.scb:L273-L276].
        tables: The tables this bridge maps, in directive order. One for eighteen of the
            twenty in-scope bridges; two for the sales and purchase invoice bridges.
        keys: The keys of reference the bridge declares, in subscript order, for
            indexed-read emulation. Never given a floor.
        load_paragraph: The name of the section that loads the host variables from the
            passed record before a write.
        load_paragraph_source: The span of that section in the generated program.
        unload_paragraph: The name of the section that unloads the host variables back
            into the record after a read, `bb100-UnloadHVs` where one exists
            [common/glpostingMT.cbl:L1074].
        unload_paragraph_source: The span of that section.
        group_initialised_before_load: Whether the load section issues an initialise
            over the whole host-variable group before its first move, as every in-scope
            bridge does [common/glpostingMT.cbl:L1053].
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

    Recorded so that the copybook side of every entry traces back to a file, and so that
    a copybook's own statements about its record length are preserved.

    Attributes:
        path: The copybook path, for example `copybooks/wsbatch.cob`.
        record_name: The 01-level record it declares, case preserved.
        declared_lengths: Every record length the copybook states about itself, as digit
            strings, in the order it states them.
        notes: Observations about the copybook or its record as a whole rather than
            about any single field, may be empty.
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

    The fourth frozen input family, and the smallest: the General Ledger work files.

    Attributes:
        path: The program that declares the record, for example `general/gl071.cbl`.
        record_name: The 01-level record it declares, case preserved as the program
            writes it - which for these records is lower case throughout, unlike most
            copybook records.
        section: `FD` for a file description or `SD` for a sort description. Recorded
            because the distinction is real.
        declared_lengths: Every record length the program states about the record, as
            digit strings, in the order it states them - EMPTY for all of these records,
            because the programs state none.
        notes: Observations about the record as a whole rather than about any single
            field, may be empty.
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

    The member set is CLOSED to exactly the seven base types that occur, which has a
    deliberate second effect.

    Attributes:
        DECIMAL: Columns declared as an exact-decimal type.
        INT: Columns declared as a four-byte integer.
        TINYINT: Columns declared as a one-byte integer.
        SMALLINT: Columns declared as a two-byte integer.
        MEDIUMINT: Columns declared as a three-byte integer.
        BIGINT: Columns declared as an eight-byte integer.
        CHAR: Columns declared as fixed-width text.
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

    The audit figures below establish that it really is frozen, and one distinction
    among them is easy to get wrong.

    Attributes:
        path: The frozen schema file. Read only: this migration adds no table, column,
            index, constraint, view or trigger of any kind (rule R-3).
        server_version: The database server that produced the dump, verbatim from its
            header.
        server_version_source: The header line that records it [mysql/ACASDB.sql:L5].
        create_table_count: How many table declarations the dump contains. Thirty-three,
            of which 22 are in scope for the posting cycle and 11 are not.
        create_index_count: How many standalone index declarations it contains. Nought.
            Recorded because it is what makes an ordering-normalised state dump
            deterministic.
        schema_evolution_alter_table_count: How many statements actually change a
            table's structure. Nought.
        dump_key_management_comment_count: How many version-guarded key-management
            comments the dump contains - the disable-keys and enable-keys pair the dump
            utility wraps each data section in. Sixty-six.
        float_double_real_column_count: How many columns are declared with one of the
            three binary floating-point SQL types. Nought, across all 720 columns.
        numeric_type_census: Per-base-type column counts across the dump.
        notes: Observations about the frozen schema, one per element, may be empty.
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

    Attributes:
        path: The input's path relative to the repository root, forward slashes, never
            absolute - so the manifest is identical whichever checkout it was produced
            in (rule R-6 forbids an absolute path in this document).
        sha256: Lower-case hexadecimal SHA-256 of the file's bytes, exactly as they sit
            on disk.
        byte_length: The file's size in bytes. Redundant against the digest and
            deliberately so.
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

    Recorded so that every entry can be RE-DERIVED from the repository rather than
    trusted.

    Attributes:
        schema: The frozen schema dump and its audit figures.
        bridges: The twenty in-scope bridge pairs - the authoritative mapping layer -
            sorted by bridge-source filename per `Determinism.array_order`.
        copybooks: The copybooks whose record layouts the dictionary reads, sorted by
            path.
        input_digests: Every file the generator opened, with its digest and byte length,
            sorted by path.
        program_sources: The records the posting programs declare inline in their own
            FILE SECTIONs - the General Ledger work files - sorted by path and then by
            the record's declaration line, since one program declares three of them.
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


@dataclass(frozen=True, slots=True)
class TableRecord(_JsonRecord):
    """One in-scope table and the COBOL machinery that reaches it.

    This is the entity-to-table spine: the four-hop call chain the posting cycle uses to
    touch a table, recorded once per table so that an entry key's table component always
    resolves to a named bridge, handler and entity facade.

    Attributes:
        name: The table name as the frozen dump spells it between backticks.
        bridge: The bridge pair that owns this table's SQL.
        handler: The numbered handler program the posting programs call. Not always one
            per table.
        entity_facade: The facade name the shared call copybook publishes for this
            table's twelve verbs.
        copybooks: The copybooks whose record layouts map onto this table, in path
            order.
        primary_key: The single column named in the table's primary-key clause.
        column_count: How many columns the table declares.
        ordinal_source: The line that opens this table's declaration in the frozen dump.
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
    document's bytes: two regenerations that ordered an array differently would both
    satisfy the schema and yet differ, which rule R-6 forbids.

    Attributes:
        tables: How the tables array is ordered.
        entries: How the entries array is ordered - the one that carries real
            information, because it is deliberately NOT by key.
        bridges: How the bridges array under sources is ordered.
        copybooks: How the copybooks array under sources is ordered.
        program_sources: How the program_sources array under sources is ordered. Two
            keys are needed rather than one, because a single program declares three of
            these records.
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

    Two regenerations of the dictionary from an unchanged repository must produce
    IDENTICAL BYTES (rule R-6). That property is not decoration.

    Attributes:
        encoding: The character encoding of the written document.
        newline: The line ending, named rather than written so the value itself cannot
            be mangled by an editor.
        indent: How many spaces each nesting level is indented by.
        trailing_newline: Whether the document ends with a single line ending.
        byte_order_mark: Whether a byte-order mark is written. False: it would be
            invisible in a text diff and would change the bytes.
        member_order: How object members are ordered, stated in full - see above.
        array_order: How each top-level array is ordered.
        forbidden_content: The kinds of content that may never appear anywhere in the
            dictionary because they would differ between two otherwise identical
            regenerations, one element per kind.
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

    Every member is prose describing HOW a derived member of an entry was arrived at.
    Recorded because field metadata in this dictionary is derived rather than
    transcribed, and a derivation nobody can audit is no better than a transcription.

    Attributes:
        entry_key: How an entry's key is formed, for a column-mapped entry and for a
            copybook-only one, including how a repeated name within one record is
            disambiguated.
        presence_and_one_sided: How the three presence booleans and the one-sided flag
            are set from what was actually found.
        drift_detection: How each drift flag is computed - by comparing the views that
            are present, never by consulting a list of known cases, which is what lets
            the dictionary find a narrowing nobody had catalogued in advance.
        digits_and_scale_from_picture: How a picture clause is expanded and counted into
            integer digits, scale, total digits and character length.
        sign_position_from_clause: How the sign position is read from the sign clause,
            the picture and the usage together.
        usage_inheritance: How a storage class declared on a group reaches the
            subordinate items that declare none, and how that inheritance is recorded
            rather than silently applied.
        bridge_derived_columns: How a host variable is bound to the copybook field it
            carries, and what happens when no copybook field can be found for it - which
            is the case that discovers a column existing in the bridge and the database
            but in no copybook.
        cobol_python_storage: How the exact-decimal-versus-integer-versus-text choice is
            made FROM THE DECLARING VIEW ALONE.
        program_source_entries: How a record declared inline in a program's FILE SECTION
            is found, which line span is read for it, and why its bridge and column
            views are recorded as absent rather than searched for.
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

    Carried in the document itself so that a reader who has only the dictionary still
    knows what it was held to - in particular that a defect found in the frozen sources
    is recorded and reproduced rather than corrected.

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
    r"""The dictionary's identity, authority and contracts - `meta`.

    !! REVISION THE DICTIONARY WAS PRODUCED, and none may be added. No date or !! time
    of generation, no machine or account name, no revision identifier, !! no absolute
    path, no tool version read from the environment.

    Attributes:
        dictionary_name: The dictionary's stable name, fixed to one value.
        dictionary_version: The dictionary format's own version, three dot-separated
            numbers. Advanced deliberately when the shape of the document changes; it is
            not derived from anything in the environment.
        schema_ref: The JSON Schema this document conforms to, named as a filename
            beside it so the reference cannot depend on where the repository is checked
            out.
        generated_by: The generator module, fixed to one value, so a reader knows which
            file to read to audit any derivation.
        authority: The authority statement this whole dictionary rests on, preserved
            verbatim.
        determinism: The byte-for-byte serialisation contract.
        derivation_rules: How every derived member was arrived at.
        binding_rules: The six rules that govern this migration and therefore this
            dictionary, in identifier order.
        source_inputs_sha256: The digest of `sources.input_digests` taken as a whole -
            one lower-case hexadecimal SHA-256 over the canonical rendering
            `"<path>:<sha256>:<byte_length>\n"` of every manifest entry, joined in the
            manifest's own order.
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


@dataclass(frozen=True, slots=True)
class Coverage(_JsonRecord):
    """Tallies that make the dictionary's completeness claim checkable.

    Every count exists so a reader can verify a claim by arithmetic instead of taking it
    on trust.

    Attributes:
        schema_tables_total: How many tables the frozen dump declares in total.
        in_scope_tables: How many of them the posting cycle reaches.
        out_of_scope_tables: How many it does not. A count only.
        in_scope_bridges: How many bridge pairs the cycle reaches.
        out_of_scope_bridges: How many it does not. A count only.
        in_scope_columns: How many columns the in-scope tables declare between them.
        entry_count: How many entries the document carries. Larger than the column
            count, and necessarily so.
        columns_covered: How many columns have an entry. Equal to `in_scope_columns`
            when coverage is complete, and stated separately so the claim is a
            comparison rather than an assertion.
        host_variables_covered: How many bridge host variables have an entry.
        copybook_fields_covered: How many ENTRIES carry a copybook view. Larger than
            `copybook_declarations_covered` whenever a column binds one OCCURS
            declaration several times over, because each occurrence is its own entry and
            each entry cites the one declaration behind it.
        copybook_declarations_covered: How many DISTINCT PHYSICAL DECLARATIONS in the
            frozen copybooks have at least one entry citing them - counted by
            `(source locator, name)` pair, so an OCCURS declaration bound by six columns
            counts once. This is the number rule R-5's field-level closure is about: the
            entry tally above can be made to look complete by two entries citing one
            declaration while another declaration has none, which is exactly the defect
            this member exists to expose.
        program_source_fields_covered: How many fields declared inline in a program's
            FILE SECTION have an entry - the General Ledger work-file records.
        one_sided_entry_keys: The key of every entry whose one-sided flag is true,
            gathered in one place. This is the review list for cross-source
            disagreement.
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
    copybook_declarations_covered: int
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
            copybook_declarations_covered=obj["copybook_declarations_covered"],
            program_source_fields_covered=obj["program_source_fields_covered"],
            one_sided_entry_keys=tuple(obj["one_sided_entry_keys"]),
        )


@dataclass(frozen=True, slots=True)
class DataDictionary(_JsonRecord):
    """The whole machine-readable data dictionary, in memory.

    Attributes:
        meta: Identity, authority, the determinism contract, the derivation rules and
            the binding rules.
        sources: The frozen inputs every entry was derived from.
        tables: The in-scope tables and the COBOL machinery that reaches each, in table-
            name order.
        entries: The field-level triples, grouped by table and then by column ordinal,
            with copybook-only fields following their record's column-mapped fields and
            the program-source work-file fields last of all.
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

        The read is strict on purpose: every member is fetched by name, no member has a
        fallback, and no value is coerced.

        Args:
            obj: The parsed document, exactly as the standard-library JSON module
                produced it from the written file.

        Returns:
            The document as an immutable tree of records.
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


# THE INTEGRITY PASS - the artifact's own trust boundary Rule R-5 requires that every
# Python field cite a dictionary entry, and every record module does.


class DictionaryIntegrityError(ValueError):
    """A dictionary document does not hold up as the document it claims to be.

    Raised by the `from_json_obj` door, before any record is built, when the decoded
    document departs from the structure, domains, patterns, pinned values, identifier
    uniqueness, internal agreement or manifest binding this module declares.
    """


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

#: How many departures one raise reports in full.
_MAX_REPORTED_PROBLEMS: Final[int] = 25


def source_inputs_digest_material(digests: Sequence[SourceDigest]) -> str:
    """Render a source manifest to the exact text its roll-up digest is taken over.

    Written once here and used by both ends - `generate.py` to compute
    `Meta.source_inputs_sha256` and this module's integrity pass to recompute it -
    because two implementations of a digest input are two chances to disagree, and a
    disagreement would make every artifact look forged.

    Args:
        digests: The manifest, in the order it appears in the document.

    Returns:
        One line per entry, `"<path>:<sha256>:<byte_length>"`, each terminated by a
            single line feed. Deliberately plain.
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
        Lower-case hexadecimal SHA-256 of `source_inputs_digest_material`, which is the
            value `Meta.source_inputs_sha256` carries.
    """
    return hashlib.sha256(
        source_inputs_digest_material(digests).encode(DETERMINISM_ENCODING)
    ).hexdigest()


@cache
def _resolved_hints(record: type) -> Mapping[str, Any]:
    """Resolve one record class's annotations to real objects, once per class.

    `from __future__ import annotations` is not in force here, but the string domains
    are PEP 695 aliases and the records refer to one another, so resolution still has to
    go through `get_type_hints` rather than reading `__annotations__` directly.
    """
    return get_type_hints(record)


def _unwrap_alias(hint: Any) -> Any:
    """Reduce a PEP 695 alias to the type it stands for.

    Every string domain above - `RepoPath`, `EntryKey`, `TableName` and the rest - is an
    alias for `str`, declared separately so that a reader of a record sees which domain
    a member belongs to.
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
        hint: The resolved annotation, possibly an alias, an optional or an array of one
            of those.
        value: The decoded member.
        where: Its path in the document, for the message.
        pattern: The pattern its record declares for it, if any. An array member's
            pattern applies to every element.
        pinned: The single literal the schema pins it to, if any.
        problems: Where a departure is appended. Nothing raises here, so one walk
            reports the whole document.
    """
    hint = _unwrap_alias(hint)

    # `X | None` - absence is admitted, and the arm is checked when present. Every union
    # in this module is exactly one type or nothing.
    if isinstance(hint, UnionType):
        arms = [arm for arm in get_args(hint) if arm is not type(None)]
        if value is None:
            return
        if len(arms) != 1:
            problems.append("%s: cannot check a %d-arm union" % (where, len(arms)))
            return
        _check_member(arms[0], value, where, pattern, pinned, problems)
        return

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

    # A flag before a whole number, because `bool` is a subclass of `int` and the two
    # are not interchangeable in this document.
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

    The member set is checked in both directions: a member the record declares and the
    document omits is a document that cannot be read without inventing a default, which
    rule R-3 forbids.
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

    Every identifier in this document is meant to be unique, and every consumer relies
    on that.
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

    * a presence flag against the view it describes, and `one_sided` against all three
    flags together - the flags are what a consumer tests before reading a view, so a
    flag that disagrees with its view is the one inconsistency that reliably produces a
    wrong answer downstream rather than an error.
    """
    entries = cast(Sequence[JsonObject], obj["entries"])
    coverage = cast(JsonObject, obj["coverage"])
    sources = cast(JsonObject, obj["sources"])
    tables = cast(Sequence[JsonObject], obj["tables"])

    with_column = 0
    with_host_variable = 0
    with_copybook = 0
    #: One member per DISTINCT physical copybook declaration cited by some entry,
    #: identified by `(source locator, name)`.
    cited_declarations: set[tuple[str, str]] = set()
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
            #  THE DECLARATION MULTISET, not the entry tally. A
            #  physical declaration is identified by its source locator and its name, so
            #  an OCCURS item bound by six columns contributes SIX entries and ONE
            #  declaration. Counting both is what makes the two figures able to disagree,
            #  and their disagreement is the only thing that can reveal one declaration
            #  cited twice while another is cited not at all.
            copybook_view = cast(JsonObject, entry["copybook"])
            cited_declarations.add(
                (cast(str, copybook_view["source"]), cast(str, copybook_view["name"]))
            )
        if bool(entry["one_sided"]):
            flagged_one_sided.add(key)

    for member, actual, described in (
        ("entry_count", len(entries), "entries recorded"),
        ("columns_covered", with_column, "entries carrying a column view"),
        ("host_variables_covered", with_host_variable,
         "entries carrying a host-variable view"),
        ("copybook_fields_covered", with_copybook,
         "entries carrying a copybook view"),
        ("copybook_declarations_covered", len(cited_declarations),
         "distinct physical copybook declarations cited"),
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
    """Refuse a document whose source manifest does not bind to itself."""
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

    The structural walk runs first and alone.

    Args:
        obj: The parsed document, exactly as the standard-library JSON module produced
            it with `parse_float=str`.

    Raises:
        DictionaryIntegrityError: The document departs from the structure, value
            domains, patterns, pinned values, identifier uniqueness, internal agreement
            or manifest binding declared above.
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


def to_json_obj(dictionary: DataDictionary) -> dict[str, JsonValue]:
    """Convert the whole dictionary to a plain tree ready to be written.

    The written file's determinism follows from two things together: this function for
    the member order, and the writer's settings for the bytes.

    Args:
        dictionary: The dictionary to convert.

    Returns:
        A plain tree of objects, arrays, text, whole numbers, flags and nulls - nothing
            else.
    """
    return dictionary.to_json_obj()


def from_json_obj(obj: JsonObject) -> DataDictionary:
    """Build the whole dictionary from a parsed JSON document.

    The read adds nothing and forgives nothing: every member is fetched by name, no
    member has a fallback, and no value is coerced or widened.

    Args:
        obj: The parsed document, exactly as the standard-library JSON module produced
            it.

    Returns:
        The document as an immutable tree of records.

    Raises:
        DictionaryIntegrityError: The document does not hold up as the document it
            claims to be.
    """
    check_integrity(obj)
    return DataDictionary.from_json_obj(obj)


# Constants first, then the string domains, then the records, then the two doors - each
# group in alphabetical order.

__all__: Final[tuple[str, ...]] = (
    # Patterns published for the generator and the test suites to check with, and
    # applied by this module's own integrity pass on the way in - see THE INTEGRITY PASS
    # for why that is provenance control under rule R-5 and not new validation under
    # rule R-3.
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
    "DETERMINISM_BYTE_ORDER_MARK",
    "DETERMINISM_ENCODING",
    "DETERMINISM_INDENT",
    "DETERMINISM_NEWLINE",
    "DETERMINISM_TRAILING_NEWLINE",
    "DICTIONARY_AUTHORITY",
    "DICTIONARY_GENERATED_BY",
    "DICTIONARY_NAME",
    "DICTIONARY_SCHEMA_REF",
    "BridgeName",
    "EntryKey",
    "HandlerName",
    "JsonObject",
    "JsonValue",
    "RepoPath",
    "SourceLocator",
    "TableName",
    "CobolPythonStorage",
    "DerivationKind",
    "EntityFacade",
    "SignPosition",
    "SqlBaseType",
    "Usage",
    "UsageDeclaredAt",
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
    # The integrity pass.
    "DictionaryIntegrityError",
    "check_integrity",
    "source_inputs_digest",
    "source_inputs_digest_material",
    "from_json_obj",
    "to_json_obj",
)
