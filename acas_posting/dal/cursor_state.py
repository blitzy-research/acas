"""ISAM `START` / `READ NEXT` cursor emulation.

The posting programs navigate data with indexed-file verbs, so a handler module
must reproduce cursor POSITIONING and not merely issue equivalent SQL: a `START`
positions on a key by relation, and each `READ NEXT` returns the following row and
leaves the cursor where it stops.

The key metadata is taken from each bridge's own declarations - its key table and
its relation directive - rather than invented, so the ordering a `READ NEXT`
walks is the ordering the frozen program walked.

That ordering is load-bearing at least once: `gl072` locates the nominal-ledger
account with a SEQUENTIAL read [general/gl072.cbl:L408], guarded at L407, so a
cursor that returned rows in a different order would post to the wrong account
with no error and no diagnostic.

    *> The START condition cannot be compounded, and it must use a
    *> Key of Reference within the record. (These are COBOL rules...)
    *> The interface defines which key and the relation condition.

Everything here follows from those three sentences:

1. **Cannot be compounded** - the generated ``WHERE`` clause carries EXACTLY
   ONE predicate on EXACTLY ONE column. Never an ``AND``, never an ``OR``.
2. **Must use a Key of Reference within the record** - the column is always one
   of the table's declared ``Table-Of-Keynames`` entries, never an arbitrary
   column.
3. **The interface defines which key and the relation** - the caller supplies
   both, the key through the key-of-reference number and the relation through
   ``Access-Type``.
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar, Final, Protocol, runtime_checkable

from acas_posting.dal.connection import quote_identifier
from acas_posting.dal.status import (
    START_ACCESS_TYPE_RANGE,
    START_RELATION_BY_ACCESS_TYPE,
    START_RELATION_TOKEN_BY_ACCESS_TYPE,
    AccessType,
    FileFunction,
    FsReply,
    SqlState,
    WeError,
    end_of_file_status,
    log_handler_failure,
    start_access_type_is_valid,
    start_relation_for,
)
from acas_posting.records.file_access import FileAccess

__all__: Final[tuple[str, ...]] = (
    # Sorted as ruff's RUF022 orders a name list - SCREAMING_CASE constants, then the
    # types, then the callables - so the tuple is stable, reviewable, and identical in
    # every process (rule R-6).
    "ACCESS_TYPE_TO_RELATION",
    "ACCESS_TYPE_TO_RELATION_TOKEN",
    "EXTRA_READ_ORDERS",
    "HANDLER_REJECTED_FUNCTIONS",
    "LEGAL_RELATIONS",
    "LEGAL_RELATION_TOKENS",
    "POSITIONING_FUNCTIONS",
    "SEQUENTIAL_READ_START",
    "TABLE_OF_KEYNAMES",
    "TABLE_PRIMARY_KEYS",
    "AccessType",
    "CursorOutcome",
    "CursorSlot",
    "CursorState",
    "CursorStateTable",
    "DatabaseCursor",
    "ExtraReadOrder",
    "KeyOfReference",
    "MostRelation",
    "OrderQuoting",
    "OrderTerm",
    "SequentialReadStart",
    "key_of_reference",
    "keys_for",
    "quote_identifier",
    "read_indexed",
    "read_next",
    "reset",
    "start",
)

#: Module logger. A library module attaches no handler and configures no root logger;
#: the application decides where diagnostics go.
_LOG: Final[logging.Logger] = logging.getLogger(__name__)

#: The bridge whose positioning paragraphs this module reproduces, named in every
#: record it emits so that a reader can put the record back against the frozen
#: source (rule R-5).
#:
#: ONE NAME FOR ALL TWENTY BRIDGES, and that is a fact about the frozen source
#: rather than a simplification: `presql2` generates the same `ba050`, `ba060` and
#: `ba070` paragraphs into every `*MT.cbl`, so `common/glpostingMT.cbl` is the
#: representative every locator in this module already cites.
_BRIDGE_PROGRAM: Final[str] = "glpostingMT"


# `acas_posting/dal/connection.py` owns identifier quoting for the layer, and this
# module defers to it so there is ONE implementation.


@runtime_checkable
class DatabaseCursor(Protocol):
    """The narrow slice of a DB-API cursor this module needs.

    Declared as a protocol rather than imported from a driver for three reasons.
    Connection handling belongs to ``connection.py`` and importing a driver here would
    duplicate that ownership.
    """

    @property
    def description(self) -> Sequence[Sequence[object]] | None:
        """Column metadata for the last statement, or ``None``."""

    def execute(
        self,
        operation: str,
        parameters: Sequence[object] | None = None,
        /,
    ) -> object:
        """Issue one statement with its parameters bound by the driver."""

    def fetchone(self) -> Sequence[object] | Mapping[str, object] | None:
        """Return the next row, or ``None`` at end of result.

        Deliberately the ONLY fetch verb in this protocol, so that any driver
        ``connection.py`` chooses satisfies it. Where the bridge's
        ``mysql_store_result`` has to be reproduced, :func:`_store_result` drains this
        verb in a loop rather than widening the protocol with ``fetchall``.
        """


@dataclass(frozen=True, slots=True)
class MostRelation:
    """The ``MOST-Relation`` field, reproduced as a three-character value.

    Three characters holding a one- or two-character token, so ``>=`` and ``<=`` are
    SPACE-PADDED on the right and ``<``, ``>`` and ``=`` are padded by two.
    """

    #: The three-character stored form, e.g. ``">= "``. The ONLY field, so a relation is
    #: constructed from its stored value and nothing else.
    padded: str

    #: Width of the field, from ``pic xxx``. Named rather than inlined so the padding
    #: assertions in the tests cite the declaration and not a literal.
    WIDTH: ClassVar[int] = 3

    def __post_init__(self) -> None:
        """Enforce the ``pic xxx`` width and the five declared values."""
        if len(self.padded) != MostRelation.WIDTH:
            raise ValueError(
                f"MOST-Relation is pic xxx, so it holds exactly "
                f"{MostRelation.WIDTH} characters; got {self.padded!r}"
            )
        if self.padded.strip() not in LEGAL_RELATION_TOKENS:
            raise ValueError(
                f"{self.padded.strip()!r} is not one of the five relations "
                f"declared at [common/glpostingMT.scb:L248]: "
                f"{', '.join(LEGAL_RELATION_TOKENS)}"
            )

    @property
    def token(self) -> str:
        """The trimmed relation that reaches the SQL text.

        Reproduces ``MOST-relation delimited by space`` [common/glpostingMT.cbl:L732].
        """
        return self.padded.strip()

    @classmethod
    def of(cls, token: str) -> MostRelation:
        """Build from a trimmed token, padding to ``pic xxx`` as the bridge does.

        Args:
            token: One of ``>=``, ``<=``, ``<``, ``>``, ``=``.

        Returns:
            The relation in its stored, space-padded form.
        """
        return cls(token.ljust(cls.WIDTH))

    @classmethod
    def for_access_type(cls, access_type: AccessType | int) -> MostRelation:
        """Build from an ``Access-Type``, deferring to ``dal/status.py``.

        The relation table is consulted through
        :func:`acas_posting.dal.status.start_relation_for` rather than copied, so there
        is exactly one declaration of it in the package.

        Args:
            access_type: An ``Access-Type`` in the 5-9 relation band.

        Returns:
            The relation in its stored, space-padded form.
        """
        return cls(start_relation_for(access_type, padded=True))


#: The five relations declared at [common/glpostingMT.scb:L248], trimmed, in the order
#: the comment lists them - ``>=``, ``<=``, ``<``, ``>``, ``=``.
LEGAL_RELATION_TOKENS: Final[tuple[str, ...]] = (">=", "<=", "<", ">", "=")

#: Re-export of ``dal/status.py``'s ``Access-Type`` to relation mapping, under the name
#: the agent brief uses.
ACCESS_TYPE_TO_RELATION: Final[Mapping[int, str]] = START_RELATION_BY_ACCESS_TYPE

ACCESS_TYPE_TO_RELATION_TOKEN: Final[Mapping[int, str]] = (
    START_RELATION_TOKEN_BY_ACCESS_TYPE
)

LEGAL_RELATIONS: Final[tuple[MostRelation, ...]] = tuple(
    MostRelation.of(token) for token in LEGAL_RELATION_TOKENS
)


class CursorSlot(enum.IntEnum):
    """Which ``Most-Cursor-Set`` flag of ``01 DAL-Data`` a read order uses.

    Fourteen of the twenty in-scope bridges declare one flag; six declare two or three,
    one per read order, and the suffix in the COBOL name IS the slot number.
    """

    PRIMARY = 1

    SECONDARY = 2

    TERTIARY = 3


#: The three ``File-Function`` codes this module implements, in the numeric order
#: [copybooks/wsfnctn.cob] declares them.
POSITIONING_FUNCTIONS: Final[tuple[FileFunction, ...]] = (
    FileFunction.READ_NEXT,
    FileFunction.READ_INDEXED,
    FileFunction.START,
)


_OFFSET_LENGTH_WIDTH: Final[int] = 8

_OFFSET_LENGTH_HALF: Final[int] = 4

#: Width of `KeyName pic x(30)` [common/glpostingMT.scb:L238].
_KEY_NAME_WIDTH: Final[int] = 30

_KOR_TYPE_WIDTH: Final[int] = 3

#: Largest value `KOR-Offset pic 9(4)` and `KOR-Length pic 9(4)` can hold
#: [common/glpostingMT.scb:L239-L240]. Four unsigned digits, so 0 through 9999.
_OFFSET_LENGTH_MAX: Final[int] = 9999


@dataclass(frozen=True, slots=True)
class KeyOfReference:
    """One ``keyOfReference`` slot, field-for-field as the bridges declare it.

    ``kor_offset`` and ``kor_length`` describe BYTES OF THE WORKING-STORAGE RECORD, not
    a column ordinal and not a character index into anything else. They are load-bearing
    rather than documentation.
    """

    key_name: str

    kor_offset: int

    kor_length: int

    kor_type: str

    #: The MySQL table this key addresses. Held per key rather than per bridge because
    #: in the two-table bridges the key NUMBER selects the table too.
    table_name: str

    column_name: str

    #: `[common/<bridge>.<ext>:L<n>]` for the three declaring lines, required by rule
    #: R-5 so that every entry can be checked against the frozen source without
    #: searching for it.
    source_locator: str

    cursor_slot: CursorSlot = CursorSlot.PRIMARY

    def __post_init__(self) -> None:
        """Enforce the declared PICTURE widths and the offset/length domain.

        These checks assert that the TRANSCRIPTION matches the declaration; they are not
        new validation of run-time data, which rule R-3 forbids.
        """
        if len(self.key_name) != _KEY_NAME_WIDTH:
            raise ValueError(
                f"KeyName is pic x({_KEY_NAME_WIDTH}); "
                f"{self.key_name!r} is {len(self.key_name)} characters"
            )
        if len(self.kor_type) != _KOR_TYPE_WIDTH:
            raise ValueError(
                f"KOR-Type is pic XXX; {self.kor_type!r} is "
                f"{len(self.kor_type)} characters"
            )
        if not 1 <= self.kor_offset <= _OFFSET_LENGTH_MAX:
            raise ValueError(
                f"KOR-Offset is pic 9(4) and one-based; got {self.kor_offset}"
            )
        if not 1 <= self.kor_length <= _OFFSET_LENGTH_MAX:
            raise ValueError(
                f"KOR-Length is pic 9(4) and non-zero; got {self.kor_length}"
            )

    @property
    def name(self) -> str:
        """The key name with the ``pic x(30)`` padding removed.

        This is the form that reaches the SQL text, because the bridge writes ``KeyName
        (KOR-x1) delimited by space`` [common/glpostingMT.cbl:L730], and ``delimited by
        space`` stops at the first space.
        """
        return self.key_name.strip()

    @property
    def dictionary_key(self) -> str:
        """The ``<TABLE-NAME>.<COLUMN-NAME>`` key for this field (rule R-5)."""
        return f"{self.table_name}.{self.column_name}"

    @property
    def offset_length_string(self) -> str:
        """The packed ``pic x(8)`` form, e.g. ``"00010010"``.

        Provided so the encoding ROUND-TRIPS: :meth:`from_offset_length_string` parses
        this form and this property regenerates it, which makes the transcription
        checkable against the frozen literal rather than merely plausible.
        """
        return (
            f"{self.kor_offset:0{_OFFSET_LENGTH_HALF}d}"
            f"{self.kor_length:0{_OFFSET_LENGTH_HALF}d}"
        )

    @property
    def record_slice(self) -> slice:
        """The key's span in the working-storage record, zero-based.

        The single place the one-based COBOL reference modifier ``WS-Posting-Record
        (K:L)`` [common/glpostingMT.cbl:L734] is converted to Python indexing.
        """
        begin = self.kor_offset - 1
        return slice(begin, begin + self.kor_length)

    def key_from_record(self, record_image: str) -> str:
        """Slice this key's value out of a working-storage record image.

        Reproduces ``WS-Posting-Record (K:L)`` [common/glpostingMT.cbl:L734, :L606]
        where ``K`` and ``L`` are this key's offset and length
        [common/glpostingMT.cbl:L710-L711].

        Args:
            record_image: The record as its fixed-width character image.

        Returns:
            The ``kor_length`` bytes beginning at ``kor_offset``.
        """
        return record_image[self.record_slice]

    @classmethod
    def from_offset_length_string(
        cls,
        *,
        key_name: str,
        offset_length: str,
        kor_type: str,
        table_name: str,
        column_name: str,
        source_locator: str,
        cursor_slot: CursorSlot = CursorSlot.PRIMARY,
    ) -> KeyOfReference:
        """Build from the raw declared literals, parsing the packed form.

        This is how every entry of :data:`TABLE_OF_KEYNAMES` is built, so the table
        below reads as a transcription of the frozen ``filler`` values rather than as
        pre-digested numbers.

        Args:
            key_name: The ``pic x(30)`` literal, padded here if the frozen source wrote
                it short - as ``'IL-LINE-KEY'`` [common/slinvoiceMT.scb:L301] and
                ``'DEF-REC-KEY '`` [common/dfltMT.scb:L259] both are.
            offset_length: The ``pic x(8)`` literal, e.g. ``"00010010"``, whose first
                four characters are ``KOR-Offset`` and last four ``KOR-Length``
                [common/glpostingMT.scb:L233, :L239-L240].
            kor_type: The ``pic XXX`` literal - ``"STR"`` for twenty-one keys and
                ``"BNT"`` for ``slpostingMT``.
            table_name: The MySQL table this key addresses.
            column_name: The MySQL column the key name resolves to.
            source_locator: ``[common/<bridge>.<ext>:L<n>]``.
            cursor_slot: Which ``Most-Cursor-Set`` flag the read order uses.

        Returns:
            The parsed key of reference.

        Raises:
            ValueError: If the packed string is not eight characters or is not all
                digits.
        """
        if len(offset_length) != _OFFSET_LENGTH_WIDTH:
            raise ValueError(
                f"the offset/length filler is pic x({_OFFSET_LENGTH_WIDTH}); "
                f"{offset_length!r} is {len(offset_length)} characters"
            )
        if not offset_length.isdigit():
            raise ValueError(
                f"KOR-Offset and KOR-Length are pic 9(4), so the packed "
                f"filler must be all digits; got {offset_length!r}"
            )
        return cls(
            key_name=key_name.ljust(_KEY_NAME_WIDTH),
            kor_offset=int(offset_length[:_OFFSET_LENGTH_HALF]),
            kor_length=int(offset_length[_OFFSET_LENGTH_HALF:]),
            kor_type=kor_type,
            table_name=table_name,
            column_name=column_name,
            source_locator=source_locator,
            cursor_slot=cursor_slot,
        )


class OrderQuoting(enum.StrEnum):
    """How a bridge quotes an ordering term, which decides whether it works.

    Not a stylistic distinction.
    """

    IDENTIFIER = "BACKTICK"

    STRING_CONSTANT = "SINGLE-QUOTE"


@dataclass(frozen=True, slots=True)
class OrderTerm:
    """One term of a declared ``ORDER BY``, transcribed with its quoting."""

    column_name: str

    #: ``"ASC"`` or ``"DESC"`` as declared. Never inferred.
    direction: str

    quoting: OrderQuoting

    source_locator: str

    def __post_init__(self) -> None:
        """Enforce that the direction is one of the two SQL keywords."""
        if self.direction not in ("ASC", "DESC"):
            raise ValueError(
                f"an ORDER BY direction is ASC or DESC; got {self.direction!r}"
            )

    def to_sql(self) -> str:
        """Render the term as the bridge renders it, quoting included.

        A term the bridge single-quoted is rendered single-quoted, because rendering it
        as an identifier would FIX anomaly A8 and rule R-4 makes a defect fixed a
        failure.
        """
        if self.quoting is OrderQuoting.STRING_CONSTANT:
            # Reproduced, not fixed: single quotes make this a constant.
            # [common/otm3MT.cbl:L1005-L1008].
            escaped = self.column_name.replace("'", "''")
            return f"'{escaped}' {self.direction}"
        return f"{quote_identifier(self.column_name)} {self.direction}"


@dataclass(frozen=True, slots=True)
class SequentialReadStart:
    """How one bridge self-positions a ``READ NEXT`` on an inactive cursor.

    ANOMALY A1 - REPRODUCED, NOT FIXED. The frozen source names ``'99RNP'`` for "read
    next with no position (no start 1st)" [copybooks/mysql-procedures.cpy:L118] and then
    never tests for it.
    """

    relation: MostRelation

    low_key: str

    relation_locator: str

    low_key_locator: str

    note: str = ""


@dataclass(frozen=True, slots=True)
class ExtraReadOrder:
    """One of the four extra read verbs, with its declared ordering.

    Only the handlers whose facade publishes the corresponding verb may use it, which is
    why :attr:`owning_handlers` is carried per entry rather than left to a reader to
    infer.
    """

    file_function: FileFunction

    cursor_slot: CursorSlot

    order_terms: tuple[OrderTerm, ...]

    #: Whether the bridge builds a WHERE predicate for this verb at all. ``False`` for
    #: the two OTM sorted reads - see anomaly A8 below.
    predicate_present: bool

    owning_handlers: tuple[str, ...]

    source_locator: str

    note: str = ""


# Transcribed from the `Table-Of-Keynames` block of all TWENTY in-scope bridges.
TABLE_OF_KEYNAMES: Final[Mapping[str, tuple[KeyOfReference, ...]]] = (
    MappingProxyType(
        {
            "SYSTEM-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="SYSTEM-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSTEM-REC",
                    column_name="SYSTEM-REC-KEY",
                    source_locator="[common/systemMT.scb:L271-L273]",
                ),
            ),
            "SYSDEFLT-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="DEF-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSDEFLT-REC",
                    column_name="DEF-REC-KEY",
                    source_locator="[common/dfltMT.scb:L259-L261]",
                ),
            ),
            "SYSFINAL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="FINAL-ACC-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSFINAL-REC",
                    column_name="FINAL-ACC-REC-KEY",
                    source_locator="[common/finalMT.scb:L257-L259]",
                ),
            ),
            "SYSTOT-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="LEDGER-TOTALS-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="SYSTOT-REC",
                    column_name="LEDGER-TOTALS-REC-KEY",
                    source_locator="[common/sys4MT.scb:L259-L261]",
                ),
            ),
            "GLLEDGER-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="LEDGER-KEY",
                    offset_length="00010008",
                    kor_type="STR",
                    table_name="GLLEDGER-REC",
                    column_name="LEDGER-KEY",
                    source_locator="[common/nominalMT.scb:L245-L247]",
                ),
            ),
            # -----------------------------------------------------------------
            #  THE ONE KEY OF REFERENCE THAT RESTS ON AN OPEN QUESTION.
            #
            #  `POST-KEY` is transcribed here because that is what the frozen bridge
            #  DECLARES as its key of reference [common/glpostingMT.scb:L232-L234] --
            #  name, the offset/length pair "00010010", and the type "STR". This entry
            #  is a transcription, not an adjudication.
            #
            #  But three lines above that declaration the same file carries the
            #  maintainer's own warning, at [common/glpostingMT.scb:L229] and verbatim
            #  in the generated program at [common/glpostingMT.cbl:L229]:
            #
            #  *>  WARNING POST-KEY MAY WELL NEED CHANGING TO POST-RRN & RDB made
            #  to index fld.
            #
            #  And the schema agrees with the warning rather than the declaration:
            #  `POST-RRN` is GLPOSTING-REC's PRIMARY KEY [mysql/ACASDB.sql:L155, :L169],
            #  which is why `TABLE_PRIMARY_KEYS` below records `POST-RRN` for this same
            #  table. THIS MODULE THEREFORE CARRIES BOTH FACTS, in two tables, for one
            #  table -- and that is not an inconsistency to tidy away, it is exactly the
            #  state the frozen source is in.
            #
            #  `Q-9` in docs/migration/ambiguity-resolutions.md owns the question. Its
            #  status is PARTIAL and the OPEN half is precisely this one: the resolution
            #  settled the non-fetch WRITE path -- `initialize TD-GLPOSTING-REC` leaves
            #  `HV-POST-RRN` at zero and `bb000-HV-Load` never sets it
            #  [common/glpostingMT.cbl:L1053-L1066] -- and it explicitly does NOT claim
            #  that START/READ NEXT follows `POST-RRN`, nor erase the warning.
            #
            #   WHY IT IS STILL OPEN, WHICH IS NOT FOR WANT OF TRYING. Deciding it
            #  needs a walk over rows whose `POST-KEY` and `POST-RRN` orderings DIFFER.
            #  That seed is unreachable through the frozen loaders: because
            #  `HV-POST-RRN` is never loaded while `POST-RRN` is the primary key, every
            #  loader write targets the same key, so a scenario seed persists AT MOST
            #  ONE GLPOSTING-REC row. One row cannot distinguish two orderings. The
            #  register records the deliberately non-degenerate experiment; running it
            #  needs a seed route the frozen loaders do not provide, and inventing one
            #  would be this migration manufacturing state (R-3).
            #
            #  So the declared metadata is carried as declared (R-4: reproduce, do not
            #  adjudicate), the open half is named here rather than left for a reader to
            #  discover, and no test claims parity ON THIS POINT --
            #  tests/arithmetic/test_comp_binary.py asserts
            #  only that what is carried MATCHES the frozen declaration.
            # -----------------------------------------------------------------
            "GLPOSTING-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="POST-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="GLPOSTING-REC",
                    column_name="POST-KEY",
                    source_locator="[common/glpostingMT.scb:L232-L234]",
                ),
            ),
            "GLBATCH-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="BATCH-KEY",
                    offset_length="00010006",
                    kor_type="STR",
                    table_name="GLBATCH-REC",
                    column_name="BATCH-KEY",
                    source_locator="[common/glbatchMT.scb:L232-L234]",
                ),
            ),
            # The ONLY key declared `"BNT"` rather than `"STR"`, the bridge's own
            # comment being `*> key is bigint` [common/slpostingMT.scb:L216]. Carried,
            # never branched on - anomaly A4.
            "PSIRSPOST-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IRS-POST-KEY",
                    offset_length="00010008",
                    kor_type="BNT",
                    table_name="PSIRSPOST-REC",
                    column_name="IRS-POST-KEY",
                    source_locator="[common/slpostingMT.scb:L214-L216]",
                ),
            ),
            "SALEDGER-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="SALES-KEY",
                    offset_length="00010007",
                    kor_type="STR",
                    table_name="SALEDGER-REC",
                    column_name="SALES-KEY",
                    source_locator="[common/salesMT.scb:L229-L231]",
                ),
            ),
            "VALUEANAL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="VA-CODE",
                    offset_length="00010003",
                    kor_type="STR",
                    table_name="VALUEANAL-REC",
                    column_name="VA-CODE",
                    source_locator="[common/valueMT.scb:L238-L240]",
                ),
            ),
            "ANALYSIS-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="PA-CODE",
                    offset_length="00010003",
                    kor_type="STR",
                    table_name="ANALYSIS-REC",
                    column_name="PA-CODE",
                    source_locator="[common/analMT.scb:L232-L234]",
                ),
            ),
            # `occurs 2` [common/slinvoiceMT.scb:L305].
            "SAINVOICE-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="SINVOICE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="SAINVOICE-REC",
                    column_name="SINVOICE-KEY",
                    source_locator="[common/slinvoiceMT.scb:L297-L299]",
                ),
            ),
            "SAINV-LINES-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IL-LINE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="SAINV-LINES-REC",
                    column_name="IL-LINE-KEY",
                    source_locator="[common/slinvoiceMT.scb:L301-L303]",
                    cursor_slot=CursorSlot.SECONDARY,
                ),
            ),
            "SAITM3-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="OI3-KEY",
                    offset_length="00010015",
                    kor_type="STR",
                    table_name="SAITM3-REC",
                    column_name="OI3-KEY",
                    source_locator="[common/otm3MT.scb:L249-L251]",
                ),
            ),
            "PULEDGER-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="PURCH-KEY",
                    offset_length="00010007",
                    kor_type="STR",
                    table_name="PULEDGER-REC",
                    column_name="PURCH-KEY",
                    source_locator="[common/purchMT.scb:L228-L230]",
                ),
            ),
            "PUINVOICE-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="PINVOICE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="PUINVOICE-REC",
                    column_name="PINVOICE-KEY",
                    source_locator="[common/plinvoiceMT.scb:L298-L300]",
                ),
            ),
            "PUINV-LINES-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IL-LINE-KEY",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="PUINV-LINES-REC",
                    column_name="IL-LINE-KEY",
                    source_locator="[common/plinvoiceMT.scb:L302-L304]",
                    cursor_slot=CursorSlot.SECONDARY,
                ),
            ),
            "PUITM5-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="OI5-KEY",
                    offset_length="00010015",
                    kor_type="STR",
                    table_name="PUITM5-REC",
                    column_name="OI5-KEY",
                    source_locator="[common/otm5MT.scb:L251-L253]",
                ),
            ),
            "IRSNL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="KEY-1",
                    offset_length="00010010",
                    kor_type="STR",
                    table_name="IRSNL-REC",
                    column_name="KEY-1",
                    source_locator="[common/irsnominalMT.scb:L142-L144]",
                ),
            ),
            "IRSDFLT-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="DEF-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="IRSDFLT-REC",
                    column_name="DEF-REC-KEY",
                    source_locator="[common/irsdfltMT.scb:L267-L269]",
                ),
            ),
            "IRSPOSTING-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="KEY-4",
                    offset_length="00010005",
                    kor_type="STR",
                    table_name="IRSPOSTING-REC",
                    column_name="KEY-4",
                    source_locator="[common/irspostingMT.scb:L124-L126]",
                ),
            ),
            "IRSFINAL-REC": (
                KeyOfReference.from_offset_length_string(
                    key_name="IRS-FINAL-ACC-REC-KEY",
                    offset_length="00010001",
                    kor_type="STR",
                    table_name="IRSFINAL-REC",
                    column_name="IRS-FINAL-ACC-REC-KEY",
                    source_locator="[common/irsfinalMT.scb:L115-L117]",
                ),
            ),
        }
    )
)


# Read from the frozen `mysql/ACASDB.sql`, whose twenty-two in-scope tables each declare
# a SINGLE-COLUMN primary key and ZERO secondary indexes.
#
# `GLPOSTING-REC` is the one table whose primary key here (`POST-RRN`) is NOT the key
# of reference declared above (`POST-KEY`). That divergence is the frozen source's, not
# this module's, and it is the open half of `Q-9` -- see the annotated entry above.
TABLE_PRIMARY_KEYS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "SYSTEM-REC": "SYSTEM-REC-KEY",
        "SYSDEFLT-REC": "DEF-REC-KEY",
        "SYSFINAL-REC": "FINAL-ACC-REC-KEY",
        "SYSTOT-REC": "LEDGER-TOTALS-REC-KEY",
        "GLLEDGER-REC": "LEDGER-KEY",
        "GLPOSTING-REC": "POST-RRN",
        "GLBATCH-REC": "BATCH-KEY",
        "PSIRSPOST-REC": "IRS-POST-KEY",
        "SALEDGER-REC": "SALES-KEY",
        "VALUEANAL-REC": "VA-CODE",
        "ANALYSIS-REC": "PA-CODE",
        "SAINVOICE-REC": "SINVOICE-KEY",
        "SAINV-LINES-REC": "IL-LINE-KEY",
        "SAITM3-REC": "OI3-KEY",
        "PULEDGER-REC": "PURCH-KEY",
        "PUINVOICE-REC": "PINVOICE-KEY",
        "PUINV-LINES-REC": "IL-LINE-KEY",
        "PUITM5-REC": "OI5-KEY",
        "IRSNL-REC": "KEY-1",
        "IRSDFLT-REC": "DEF-REC-KEY",
        "IRSPOSTING-REC": "KEY-4",
        "IRSFINAL-REC": "IRS-FINAL-ACC-REC-KEY",
    }
)


# One entry per bridge, transcribed from its `ba040-Process-Read-Next`. The relation and
# low key are what that paragraph hard-codes for the `Cursor-Not-Active` branch.
SEQUENTIAL_READ_START: Final[Mapping[str, SequentialReadStart]] = MappingProxyType(
    {
        "SYSTEM-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/systemMT.cbl:L669]",
            low_key_locator="[common/systemMT.cbl:L670]",
            # Three zeros for a one-byte key, and written UNQUOTED here where every
            # other bridge quotes it.
            note="low key is 3 characters for a 1-byte key; emitted unquoted",
        ),
        "SYSDEFLT-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/dfltMT.cbl:L475]",
            low_key_locator="[common/dfltMT.cbl:L476]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "SYSFINAL-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/finalMT.cbl:L476]",
            low_key_locator="[common/finalMT.cbl:L477]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "SYSTOT-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/sys4MT.cbl:L502]",
            low_key_locator="[common/sys4MT.cbl:L503]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "GLLEDGER-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="00000000",
            relation_locator="[common/nominalMT.cbl:L466]",
            low_key_locator="[common/nominalMT.cbl:L467]",
            note="26/12/16 NOT '='",
        ),
        "GLPOSTING-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/glpostingMT.cbl:L464]",
            low_key_locator="[common/glpostingMT.cbl:L465]",
            note="nom uses >  ??",
        ),
        "GLBATCH-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000000",
            relation_locator="[common/glbatchMT.cbl:L472]",
            low_key_locator="[common/glbatchMT.cbl:L473]",
            note="nom uses >  ??",
        ),
        "PSIRSPOST-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/slpostingMT.cbl:L443]",
            low_key_locator="[common/slpostingMT.cbl:L444]",
            note="low key is 10 characters for the 8-byte IRS-POST-KEY",
        ),
        "SALEDGER-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000",
            relation_locator="[common/salesMT.cbl:L490]",
            low_key_locator="[common/salesMT.cbl:L491]",
        ),
        "VALUEANAL-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000",
            relation_locator="[common/valueMT.cbl:L476]",
            low_key_locator="[common/valueMT.cbl:L477]",
        ),
        "ANALYSIS-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/analMT.cbl:L471]",
            low_key_locator="[common/analMT.cbl:L472]",
            # analMT and valueMT hold identically shaped 3-byte code keys and disagree
            # on the relation. Reproduced, not reconciled.
            note="uses > where valueMT, with the same 3-byte key shape, uses >=",
        ),
        "SAINVOICE-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/slinvoiceMT.cbl:L646]",
            low_key_locator="[common/slinvoiceMT.cbl:L647]",
        ),
        "SAITM3-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000000000000000",
            relation_locator="[common/otm3MT.cbl:L504]",
            low_key_locator="[common/otm3MT.cbl:L505]",
        ),
        "PULEDGER-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000",
            relation_locator="[common/purchMT.cbl:L521]",
            low_key_locator="[common/purchMT.cbl:L522]",
        ),
        "PUINVOICE-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="0000000000",
            relation_locator="[common/plinvoiceMT.cbl:L645]",
            low_key_locator="[common/plinvoiceMT.cbl:L646]",
        ),
        "PUITM5-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="000000000000000",
            relation_locator="[common/otm5MT.cbl:L507]",
            low_key_locator="[common/otm5MT.cbl:L508]",
        ),
        "IRSNL-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="0000000000",
            relation_locator="[common/irsnominalMT.cbl:L409]",
            low_key_locator="[common/irsnominalMT.cbl:L410]",
            note="26/12/16 NOT '='",
        ),
        "IRSDFLT-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/irsdfltMT.cbl:L486]",
            low_key_locator="[common/irsdfltMT.cbl:L487]",
            note="low key is 3 characters for a 1-byte key",
        ),
        "IRSPOSTING-REC": SequentialReadStart(
            relation=MostRelation.of(">="),
            low_key="00000",
            relation_locator="[common/irspostingMT.cbl:L360]",
            low_key_locator="[common/irspostingMT.cbl:L361]",
            note="nom uses >",
        ),
        "IRSFINAL-REC": SequentialReadStart(
            relation=MostRelation.of(">"),
            low_key="000",
            relation_locator="[common/irsfinalMT.cbl:L338]",
            low_key_locator="[common/irsfinalMT.cbl:L339]",
            note="low key is 3 characters for a 1-byte key",
        ),
    }
)


# Some tables cannot be positioned at all, and the refusal lives in the HANDLER rather
# than the bridge - which is why the bridge still declares perfectly good key metadata
# for them.
HANDLER_REJECTED_FUNCTIONS: Final[
    Mapping[str, Mapping[FileFunction, tuple[FsReply, WeError, str]]]
] = MappingProxyType(
    {
        # `acas008` guards FOUR verbs in one body, in the order its `evaluate` lists
        # them - `when 4` read-indexed, `when 7` re-write, `when 9` start, `when 8`
        # delete - moving 988 to `WE-Error` and 99 to `fs-reply`
        # [common/acas008.cbl:L299-L307].
        "PSIRSPOST-REC": MappingProxyType(
            {
                FileFunction.READ_INDEXED: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L300]",
                ),
                FileFunction.RE_WRITE: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L301]",
                ),
                FileFunction.START: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L302]",
                ),
                FileFunction.DELETE: (
                    FsReply.ERROR,
                    WeError.ACTION_TYPE_WRONG_FOR_SEQ,
                    "[common/acas008.cbl:L303]",
                ),
            }
        ),
    }
)


# Keyed by table, then by `File-Function`.
EXTRA_READ_ORDERS: Final[Mapping[str, Mapping[FileFunction, ExtraReadOrder]]] = (
    MappingProxyType(
        {
            "SALEDGER-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_NAME: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_NAME,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="SALES-NAME",
                                direction="ASC",
                                quoting=OrderQuoting.IDENTIFIER,
                                source_locator="[common/salesMT.cbl:L1016-L1019]",
                            ),
                        ),
                        predicate_present=True,
                        owning_handlers=("acas012",),
                        source_locator="[common/salesMT.cbl:L995-L1022]",
                        note=(
                            "predicate is on SALES-KEY, ordering on the "
                            "unindexed SALES-NAME; the low key is emitted "
                            "unquoted here [common/salesMT.cbl:L1014]"
                        ),
                    ),
                }
            ),
            "PULEDGER-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_NAME: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_NAME,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="PURCH-NAME",
                                direction="ASC",
                                quoting=OrderQuoting.IDENTIFIER,
                                source_locator="[common/purchMT.cbl:L1031-L1034]",
                            ),
                        ),
                        predicate_present=True,
                        owning_handlers=("acas022",),
                        source_locator="[common/purchMT.cbl:L1010-L1037]",
                        note=(
                            "predicate is on PURCH-KEY, ordering on the "
                            "unindexed PURCH-NAME"
                        ),
                    ),
                }
            ),
            # ANOMALY A8 - REPRODUCED, NOT FIXED. Two independent defects.
            "SAITM3-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_BATCH: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_BATCH,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI3-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1005]",
                            ),
                            OrderTerm(
                                column_name="OI3-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1005]",
                            ),
                            OrderTerm(
                                column_name="OI3-TYPE",
                                direction="DESC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1007]",
                            ),
                            OrderTerm(
                                column_name="OI3-BATCH-ITEM",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1008]",
                            ),
                            OrderTerm(
                                column_name="OI3-BATCH-NOS",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1008]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas019",),
                        source_locator="[common/otm3MT.cbl:L997-L1012]",
                        note=(
                            "anomaly A8: single-quoted terms order nothing, and "
                            "WHERE carries no predicate, so the statement is a "
                            "syntax error returning (99, 911)"
                        ),
                    ),
                    FileFunction.READ_BY_CUST: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_CUST,
                        cursor_slot=CursorSlot.TERTIARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI3-CUSTOMER",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1160]",
                            ),
                            OrderTerm(
                                column_name="OI3-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1160]",
                            ),
                            OrderTerm(
                                column_name="OI3-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1161]",
                            ),
                            OrderTerm(
                                column_name="OI3-TYPE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm3MT.cbl:L1161]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas019",),
                        source_locator="[common/otm3MT.cbl:L1153-L1166]",
                        note="anomaly A8, as for READ_BY_BATCH above",
                    ),
                }
            ),
            "PUITM5-REC": MappingProxyType(
                {
                    FileFunction.READ_BY_BATCH: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_BATCH,
                        cursor_slot=CursorSlot.SECONDARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI5-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1008]",
                            ),
                            OrderTerm(
                                column_name="OI5-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1008]",
                            ),
                            OrderTerm(
                                column_name="OI5-TYPE",
                                direction="DESC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1010]",
                            ),
                            OrderTerm(
                                column_name="OI5-BATCH-ITEM",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1011]",
                            ),
                            OrderTerm(
                                column_name="OI5-BATCH-NOS",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1011]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas029",),
                        source_locator="[common/otm5MT.cbl:L1000-L1015]",
                        note="anomaly A8, as for SAITM3-REC",
                    ),
                    FileFunction.READ_BY_CUST: ExtraReadOrder(
                        file_function=FileFunction.READ_BY_CUST,
                        cursor_slot=CursorSlot.TERTIARY,
                        order_terms=(
                            OrderTerm(
                                column_name="OI5-SUPPLIER",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1166]",
                            ),
                            OrderTerm(
                                column_name="OI5-DAT",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1166]",
                            ),
                            OrderTerm(
                                column_name="OI5-INVOICE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1167]",
                            ),
                            OrderTerm(
                                column_name="OI5-TYPE",
                                direction="ASC",
                                quoting=OrderQuoting.STRING_CONSTANT,
                                source_locator="[common/otm5MT.cbl:L1167]",
                            ),
                        ),
                        predicate_present=False,
                        owning_handlers=("acas029",),
                        source_locator="[common/otm5MT.cbl:L1159-L1172]",
                        note="anomaly A8, as for SAITM3-REC",
                    ),
                }
            ),
            # `fn-Read-Next-Header` (34) shares ONE `evaluate` body with `fn-read-next`
            # (3).
            "SAINVOICE-REC": MappingProxyType(
                {
                    FileFunction.READ_NEXT_HEADER: ExtraReadOrder(
                        file_function=FileFunction.READ_NEXT_HEADER,
                        cursor_slot=CursorSlot.PRIMARY,
                        order_terms=(),
                        predicate_present=True,
                        owning_handlers=("acas016",),
                        source_locator="[common/slinvoiceMT.cbl:L624]",
                        note=(
                            "shares the fn-read-next body, so it is "
                            "behaviourally identical to function 3"
                        ),
                    ),
                }
            ),
            "PUINVOICE-REC": MappingProxyType(
                {
                    FileFunction.READ_NEXT_HEADER: ExtraReadOrder(
                        file_function=FileFunction.READ_NEXT_HEADER,
                        cursor_slot=CursorSlot.PRIMARY,
                        order_terms=(),
                        predicate_present=True,
                        owning_handlers=("acas026",),
                        source_locator="[common/plinvoiceMT.cbl:L623]",
                        note=(
                            "shares the fn-read-next body, so it is "
                            "behaviourally identical to function 3"
                        ),
                    ),
                }
            ),
        }
    )
)


_CURSOR_NOT_ACTIVE: Final[int] = 0

_CURSOR_ACTIVE: Final[int] = 1


@dataclass(slots=True)
class CursorState:
    """One cursor - one ``(table, slot)`` pair - reproducing ``01 DAL-Data``.

    Mutable, because the COBOL block is working storage the bridge writes as it
    positions. The two ``88``-level condition names become the predicates
    :meth:`cursor_not_active` and :meth:`cursor_active`, per Agent Action Plan section
    0.1.2's transformation rule 12, verbatim.
    """

    table_name: str

    slot: CursorSlot

    most_relation: MostRelation | None = None

    #: `05 Most-Cursor-Set pic 9 value zero.` - the raw flag.
    most_cursor_set: int = _CURSOR_NOT_ACTIVE

    #: The key value the cursor is positioned at. Never a binary floating-point type
    #: (rule R-2): a key compared inexactly positions on the wrong row, silently.
    positioned_key: object | None = None

    #: The key of reference in use, so a caller can see WHICH key positioned the cursor
    #: and not merely that it is active.
    key_of_reference: KeyOfReference | None = None

    stored_rows: tuple[Mapping[str, object], ...] = ()

    #: How many records of :attr:`stored_rows` ``MySQL_fetch_record`` has already handed
    #: back. The bridge holds this inside the result set.
    fetched_count: int = 0

    @property
    def count_rows(self) -> int:
        """``WS-MYSQL-Count-Rows`` - the FULL row count of the stored result."""
        return len(self.stored_rows)

    @property
    def position_inclusive(self) -> bool:
        """``True`` while the stored result's first record is still unfetched.

        so a ``START`` stores the result and consumes nothing from it, and the first
        following ``READ NEXT`` returns the row the ``START`` found.
        """
        return bool(self.stored_rows) and self.fetched_count == 0

    def store_result(self, rows: Iterable[Mapping[str, object]]) -> int:
        """Reproduce ``Mysql-1220-Store-Result`` then ``MySQL_num_rows``.

        Args:
            rows: Every qualifying row, in the order the statement returned them.

        Returns:
            The full row count - the value ``WS-MYSQL-Count-Rows`` receives.
        """
        self.stored_rows = tuple(rows)
        self.fetched_count = 0
        return len(self.stored_rows)

    def fetch_record(self) -> Mapping[str, object] | None:
        """Reproduce ``MySQL_fetch_record`` [common/glpostingMT.cbl:L536-L554].

        Returns:
            The next record, or ``None`` once the snapshot is exhausted - the ``return-
                code = -1`` the bridge tests for [common/glpostingMT.cbl:L556-L557].
        """
        if self.fetched_count >= len(self.stored_rows):
            return None
        row = self.stored_rows[self.fetched_count]
        self.fetched_count += 1
        return row

    def free_result(self) -> None:
        """Reproduce ``CALL "MySQL_free_result"`` [common/glpostingMT.cbl:L1032].

        Releases the stored result. Called ONLY from :meth:`free`, because
        ``ba998-Free`` is the only paragraph that frees it - the end-of-file sites
        merely ``set Cursor-Not-Active to true`` and leave the result allocated.
        """
        self.stored_rows = ()
        self.fetched_count = 0

    def cursor_not_active(self) -> bool:
        """`88 Cursor-Not-Active value zero.` [common/glpostingMT.scb:L250]."""
        return self.most_cursor_set == _CURSOR_NOT_ACTIVE

    def cursor_active(self) -> bool:
        """`88 Cursor-Active value 1.` [common/glpostingMT.scb:L251]."""
        return self.most_cursor_set == _CURSOR_ACTIVE

    def set_cursor_active(self) -> None:
        """Reproduce ``set Cursor-Active to true`` [common/glpostingMT.cbl:L768]."""
        self.most_cursor_set = _CURSOR_ACTIVE

    def set_cursor_not_active(self) -> None:
        """Reproduce ``set Cursor-Not-Active to true``."""
        self.most_cursor_set = _CURSOR_NOT_ACTIVE

    def free(self) -> None:
        """Reproduce ``ba998-Free`` [common/glpostingMT.cbl:L1023-L1033]."""
        self.free_result()
        self.set_cursor_not_active()
        self.positioned_key = None

    def position_at(self, key_value: object) -> None:
        """Record the key just positioned on and mark the cursor active.

        Args:
            key_value: The key of the row positioned on, exactly as the driver returned
                it - not re-parsed, not re-formatted.
        """
        self.positioned_key = key_value
        self.set_cursor_active()


class CursorStateTable:
    """The set of live cursors, one per ``(table, slot)``.

    Not thread-safe, and deliberately so: rule R-3 requires strictly sequential
    execution matching the single-threaded COBOL, so a lock here would imply a
    concurrency this migration does not have.
    """

    __slots__ = ("_states",)

    def __init__(self) -> None:
        """Create an empty set of cursors. No I/O, no clock, no entropy."""
        # A plain dict keyed by (table, slot). Insertion order is never relied upon:
        # `live_cursors()` sorts, and no iteration of this mapping reaches SQL text
        # (rule R-6).
        self._states: dict[tuple[str, CursorSlot], CursorState] = {}

    def state_for(
        self, table_name: str, slot: CursorSlot = CursorSlot.PRIMARY
    ) -> CursorState:
        """Return the cursor for a table and slot, creating it inactive.

        Creating on demand reproduces the COBOL's own initial condition: a bridge that
        has never positioned has ``Most-Cursor-Set`` at its declared ``value zero``,
        which is indistinguishable from a cursor that does not exist yet.

        Args:
            table_name: An in-scope table name.
            slot: Which read order's flag is wanted.

        Returns:
            The live cursor, created inactive on first request.

        Raises:
            KeyError: If the table declares no key of reference.
        """
        if table_name not in TABLE_OF_KEYNAMES:
            raise KeyError(
                f"{table_name!r} declares no Table-Of-Keynames entry; the "
                f"in-scope tables are {', '.join(TABLE_OF_KEYNAMES)}"
            )
        key = (table_name, slot)
        state = self._states.get(key)
        if state is None:
            state = CursorState(table_name=table_name, slot=slot)
            self._states[key] = state
        return state

    def live_cursors(self) -> tuple[CursorState, ...]:
        """Return every cursor created so far, in a fixed order.

        Sorted by table name then slot so the result is reproducible across processes
        (rule R-6). Diagnostic only - nothing here reaches SQL text.
        """
        return tuple(
            self._states[key]
            for key in sorted(self._states, key=lambda pair: (pair[0], int(pair[1])))
        )

    def reset(self, table_name: str | None = None) -> None:
        """Discard cursor state, so a following run starts clean.

        Args:
            table_name: Reset only this table's cursors when given; reset every cursor
                when ``None``.
        """
        if table_name is None:
            self._states.clear()
            return
        for key in [pair for pair in self._states if pair[0] == table_name]:
            del self._states[key]


#: The cursors the module-level verbs use when a caller passes none. One shared set is
#: correct rather than convenient.
_DEFAULT_STATES: Final[CursorStateTable] = CursorStateTable()


@dataclass(frozen=True, slots=True)
class CursorOutcome:
    """What one positioning verb returned, and what it wrote.

    The COBOL handler communicates by WRITING into the caller's ``File-Access`` linkage
    block, so this value object carries the pair it would have written plus the row, and
    :meth:`apply_to` performs the write.
    """

    #: The `FS-Reply` the bridge would leave. Meaningful only when
    #: :attr:`status_written` is ``True``; when it is ``False`` this echoes the pair
    #: that was already there.
    fs_reply: FsReply

    #: The `We-Error` the bridge would leave, as a plain ``int`` because the COBOL field
    #: is `pic 999` and end-of-file stores the literal 10 into it
    #: [common/glpostingMT.cbl:L557] rather than a named error code.
    we_error: int

    row: Mapping[str, object] | None

    statement: str

    #: The values bound to that statement. Bound, never interpolated.
    parameters: tuple[object, ...]

    #: Whether the bridge writes the status pair on this path at all. ``False`` only on
    #: the no-rows START of anomaly A7.
    status_written: bool = True

    #: The internal SQLSTATE that DESCRIBES this outcome, for diagnostics only - anomaly
    #: A3.
    sql_state: str = ""

    #: The bridge's own `WS-File-Key` log tag for this path, verbatim.
    file_key: str = ""

    def is_ok(self) -> bool:
        """Whether the verb succeeded, i.e. left ``FS-Reply`` zero."""
        return self.fs_reply == FsReply.SUCCESS

    def is_end_of_file(self) -> bool:
        """Whether the verb reported end of file, ``FS-Reply`` 10."""
        return self.fs_reply == FsReply.END_OF_FILE

    def apply_to(self, file_access: FileAccess) -> None:
        """Write this outcome into the caller's ``File-Access`` block.

        Reproduces the handler's side of the linkage contract: the bridge stores ``FS-
        Reply``, ``We-Error``, ``SQL-State`` and the logging fields into the block the
        caller passed [common/glpostingMT.cbl:L588, :L744-L745].

        Args:
            file_access: The caller's block, mutated in place.
        """
        if self.status_written:
            file_access.fs_reply = int(self.fs_reply)
            file_access.we_error = self.we_error
        if self.sql_state:
            file_access.logging_data.sql_state = self.sql_state
        if self.file_key:
            file_access.logging_data.ws_file_key = self.file_key
        file_access.logging_data.ws_log_where = self.statement


def _column_names(cursor: DatabaseCursor) -> tuple[str, ...]:
    """Return the column names of the last statement, or an empty tuple.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The names in the order the driver reports them, which for ``SELECT *`` is the
            declared column order of the frozen table.
    """
    description = cursor.description
    if not description:
        return ()
    return tuple(str(column[0]) for column in description)


def _fetch_one_row(cursor: DatabaseCursor) -> Mapping[str, object] | None:
    """Fetch at most ONE row and return it keyed by column name.

    Accepts either row shape a driver may hand back - a sequence, or a mapping when the
    driver was configured to produce one - because ``connection.py`` owns that choice
    and this module must not constrain it.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        The row keyed by column name, or ``None`` at end of result.
    """
    row = cursor.fetchone()
    if row is None:
        return None
    if isinstance(row, Mapping):
        return row
    names = _column_names(cursor)
    if not names:
        # Without column metadata a name cannot be invented. Positional keys are honest
        # about that and still let a caller reach the values.
        return MappingProxyType({str(index): value for index, value in enumerate(row)})
    return MappingProxyType(dict(zip(names, row, strict=False)))


def _store_result(cursor: DatabaseCursor) -> tuple[Mapping[str, object], ...]:
    """Materialise the ENTIRE result, reproducing ``mysql_store_result``.

    ``Mysql-1220-Store-Result`` pulls every qualifying row to the client
    [copybooks/mysql-procedures.cpy:L187-L192] before ``MySQL_num_rows`` counts it and
    ``MySQL_fetch_record`` walks it. Rule R-3 does not bar this: it bars added
    validations, added fields, schema change and concurrency.

    Args:
        cursor: The cursor the statement was issued on.

    Returns:
        Every row, keyed by column name, in the order the statement returned them.
    """
    rows: list[Mapping[str, object]] = []
    while True:
        row = _fetch_one_row(cursor)
        if row is None:
            return tuple(rows)
        rows.append(row)


def _deliver_from_stored_result(
    state: CursorState,
    key: KeyOfReference,
    *,
    empty_tag: str,
    incoming_fs_reply: FsReply,
    incoming_we_error: int,
    file_access: FileAccess | None,
    statement: str = "",
    parameters: tuple[object, ...] = (),
) -> CursorOutcome:
    """Reproduce ``ba041-Reread`` [common/glpostingMT.cbl:L523-L589].

    Args:
        state: The cursor whose stored result is being walked.
        key: The key of reference in force, whose column names the delivered key.
        empty_tag: The ``WS-File-Key`` tag for exhaustion - ``"EOF"`` when entered
            directly [common/glpostingMT.cbl:L558], ``"No Data"`` when reached through
            ``ba040``'s self-positioning [:L510].
        incoming_fs_reply: The caller's ``FS-Reply`` on entry, which anomaly A10 tests
            AFTER the fetch.
        incoming_we_error: The caller's ``We-Error`` on entry, preserved unchanged on
            the A10 path where no status is written.
        file_access: Applied to before returning when given.
        statement: The statement that materialised the snapshot, for the outcome. Empty
            when this paragraph was entered directly, as the bridge issues none there.
        parameters: That statement's bound parameters, for the same reason.

    Returns:
        The outcome - a delivered row, exhaustion, or an A10 discard.
    """
    row = state.fetch_record()

    if row is None:
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=empty_tag,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    if incoming_fs_reply == FsReply.END_OF_FILE:
        # ANOMALY A10: the row was fetched and is now THROWN AWAY, because the
        # caller's `FS-Reply` still holds 10 from a previous end of file
        # [common/glpostingMT.cbl:L580-L583]. No status is written - the stale
        # pair simply persists - and the cursor is deactivated, so the next call
        # self-positions and discards a row all over again. The record IS consumed
        # from the stored result first, exactly as the bridge consumes it.
        #  AND IT IS SILENT. `if fs-reply = 10 ... set Cursor-Not-Active` writes
        #  no status and displays nothing [common/glpostingMT.cbl:L580-L583]; the
        #  row is consumed and dropped without a trace. A record here was an
        #  invented diagnostic on a path the compiled program says nothing about,
        #  which rule R-4 forbids - the anomaly is reproduced, and it is recorded
        #  as A10 in `docs/migration/anomaly-log.md`, which is where a reader is
        #  meant to learn about it rather than from a log line the original cannot
        #  produce.
        state.set_cursor_not_active()
        outcome = CursorOutcome(
            fs_reply=incoming_fs_reply,
            we_error=incoming_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            status_written=False,
            file_key="EOF3",
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    positioned = row[key.column_name]
    state.key_of_reference = key
    state.position_at(positioned)
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement=statement,
        parameters=parameters,
        file_key=str(positioned),
    )
    if file_access is not None:
        outcome.apply_to(file_access)
    return outcome


def keys_for(table_name: str) -> tuple[KeyOfReference, ...]:
    """Return every key of reference a table declares, in ``occurs`` order.

    Args:
        table_name: An in-scope table name.

    Returns:
        The declared keys, index 0 being ``KOR-x1`` of 1.

    Raises:
        KeyError: If the table is not in scope. >>> len(keys_for("GLPOSTING-REC")) 1.
    """
    try:
        return TABLE_OF_KEYNAMES[table_name]
    except KeyError:
        raise KeyError(
            f"{table_name!r} declares no Table-Of-Keynames entry; the in-scope "
            f"tables are {', '.join(TABLE_OF_KEYNAMES)}"
        ) from None


def key_of_reference(table_name: str, key_number: int = 1) -> KeyOfReference:
    """Return one key of reference by its ``KOR-x1`` number.

    The COBOL always sets the index by literal - ``set KOR-x1 to 1``, annotated ``*> 1 =
    Primary`` [common/glpostingMT.cbl:L455, :L709], and ``set KOR-x1 to 2``, annotated
    ``*> 2 = Lines`` [common/slinvoiceMT.cbl:L2731] - so an out-of-range number is not
    reachable in the compiled system.

    Args:
        table_name: An in-scope table name.
        key_number: The one-based ``KOR-x1`` value.

    Returns:
        The requested key of reference.

    Raises:
        KeyError: If the table is not in scope.
        IndexError: If ``key_number`` is outside the table's ``occurs`` range. >>>
            key_of_reference("GLPOSTING-REC").name 'POST-KEY'.
    """
    keys = keys_for(table_name)
    if not 1 <= key_number <= len(keys):
        raise IndexError(
            f"{table_name} declares occurs {len(keys)}, so KOR-x1 must be "
            f"1..{len(keys)}; got {key_number}"
        )
    return keys[key_number - 1]


def _incoming_status(file_access: FileAccess | None) -> tuple[FsReply, int]:
    """Snapshot the status pair the caller already holds.

    Needed by exactly one path - the no-rows START of anomaly A7, where the bridge
    writes NEITHER status field [common/glpostingMT.cbl:L771-L781] and the caller's
    existing pair therefore survives the call.

    Args:
        file_access: The caller's block, or ``None`` when the verb was called without
            one.

    Returns:
        The pair as ``(FS-Reply, We-Error)``.
    """
    if file_access is None:
        return (FsReply.SUCCESS, int(WeError.SUCCESS))
    try:
        fs_reply = FsReply(file_access.fs_reply)
    except ValueError:
        fs_reply = FsReply.SUCCESS
    return (fs_reply, int(file_access.we_error))


def _driver_failure_fields(error: BaseException) -> tuple[str, str]:
    """Render one driver exception as the two typed fields that may be logged.

    Three of the positioning verbs catch a driver failure and report it, and this
    helper is the one place the three share, so none can be the weak one.

    THE DRIVER'S MESSAGE IS NOT ONE OF THE FIELDS, AND THAT IS THE POINT. That
    text is built by the server and the client library out of material that can
    include the connection's account, the host, the failing statement and key
    values from the data, and it can carry a carriage return and a line feed - so
    interpolating it leaks and lets the failure forge a second log record
    (CWE-532, CWE-117). Redacting it was not sufficient either: the rules of
    ``redact_for_log`` recognise the connection-message shapes the client library
    is known to produce, and an arbitrary SQL literal or row key is not one of
    them. What is returned instead is the driver's error NUMBER and its SQLSTATE -
    both short closed-vocabulary fields - from which
    :func:`~acas_posting.dal.status.log_handler_failure` also derives the stable
    ``db_error_log_category`` token, which is identical for every occurrence of
    the same fault and therefore alertable in a way free text never was.

    NOTHING BRANCHES ON THE RESULT. The status pair each caller then reports is
    the one the frozen source dictates - ``(21, 0)`` for `fn-start`, end of file
    for `fn-read-next` (anomaly A11) and ``(21, 911)`` for `fn-read-indexed`
    (anomaly A14) - and it is chosen by the exception being caught at all, never
    by what the exception said. Rules R-3 and R-4 are therefore untouched: the
    only thing that changes is the rendering of a log line.

    Args:
        error: the exception the driver raised.

    Returns:
        ``(error number, SQLSTATE)``, each as text and each empty when the
        exception does not carry it - which is the case for an exception raised
        before the driver reached a server.
    """
    return (
        str(getattr(error, "errno", "") or ""),
        str(getattr(error, "sqlstate", "") or ""),
    )


def _guarded_by_handler(
    table_name: str, file_function: FileFunction
) -> tuple[FsReply, WeError, str] | None:
    """Return the handler's refusal for a verb, or ``None`` if it permits it.

    Reproduces the unconditional entry guard of a handler whose store is sequential
    [common/acas008.cbl:L299-L307]. Data-driven from :data:`HANDLER_REJECTED_FUNCTIONS`,
    so a second such handler needs a table entry and no code change.
    """
    rejected = HANDLER_REJECTED_FUNCTIONS.get(table_name)
    if rejected is None:
        return None
    return rejected.get(file_function)


def _select_statement(key: KeyOfReference, relation: str) -> str:
    """Build the ONE-predicate positioning statement the bridge builds.

    Reproduces [common/glpostingMT.cbl:L729-L743] and the SELECT that consumes it
    [common/glpostingMT.cbl:L756-L761], with three deliberate fidelities.

    Args:
        key: The key of reference to position on.
        relation: The trimmed relation token.

    Returns:
        The statement text, with one ``%s`` placeholder.
    """
    column = quote_identifier(key.column_name)
    return (
        f"SELECT * FROM {quote_identifier(key.table_name)} "
        f"WHERE {column} {relation} %s "
        f"ORDER BY {column} ASC"
    )


def start(
    cursor: DatabaseCursor,
    table_name: str,
    key_value: object,
    access_type: AccessType | int,
    *,
    key_number: int = 1,
    slot: CursorSlot = CursorSlot.PRIMARY,
    states: CursorStateTable | None = None,
    file_access: FileAccess | None = None,
) -> CursorOutcome:
    """``fn-start`` (``File-Function`` 9) - position the cursor, fetch nothing.

    Reproduces ``ba060-Process-Start`` [common/glpostingMT.cbl:L691-L793] step for step,
    in the order that paragraph performs them.

    Args:
        cursor: A DB-API cursor from ``connection.py``.
        table_name: The in-scope table to position on.
        key_value: The key to compare against, as ``str``, ``int`` or ``Decimal``. Never
            a binary floating-point value (rule R-2).
        access_type: The caller's ``Access-Type``, which on a START is the relation. 5
            ``=``, 6 ``<``, 7 ``>``, 8 ``>=``.
        key_number: The ``KOR-x1`` value; the COBOL always sets it by literal.
        slot: Which ``Most-Cursor-Set`` flag to drive.
        states: The cursors to use; the module-level set when ``None``.
        file_access: When given, the outcome is applied to it before returning,
            reproducing the handler's write into the caller's linkage block.

    Returns:
        The outcome, whose status pair is the one the bridge would have left.
            :attr:`CursorOutcome.row` is ALWAYS ``None``.
    """
    table = states if states is not None else _DEFAULT_STATES
    # Anomaly A7 needs the pair the caller ALREADY holds, so snapshot it before anything
    # is issued. [common/glpostingMT.cbl:L771-L781].
    incoming_fs_reply, incoming_we_error = _incoming_status(file_access)

    refusal = _guarded_by_handler(table_name, FileFunction.START)
    if refusal is not None:
        fs_reply, we_error, locator = refusal
        #  ONE ERROR, at the level a refusal deserves. The verb was rejected and
        #  `FS-Reply` 99 goes back to the caller, so this is a failure and not a
        #  trace. At DEBUG it would leave a permanently-failing verb (anomaly A6)
        #  invisible at the level an operator watches. Only the table
        #  name, the paragraph and the frozen locator are reported: no key, no
        #  statement, no value.
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="fn-start refused by the handler for " + table_name,
        )
        outcome = CursorOutcome(
            fs_reply=fs_reply,
            we_error=int(we_error),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # the never-implemented `'99NKS'` situation, so it is reported with the SQLSTATE for
    # diagnostics and the compiled system's `(99, 911)` pair - anomaly A3.
    # [copybooks/mysql-procedures.cpy:L115, :L127-L128].
    try:
        key = key_of_reference(table_name, key_number)
    except IndexError:
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator="[copybooks/mysql-procedures.cpy:L115, :L127-L128]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            sql_state=str(SqlState.INVALID_KEY_NUMBER),
            detail="invalid key number %d for %s, which the frozen source "
            "describes and never implements" % (key_number, table_name),
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.RDB_INIT_ERROR),
            row=None,
            statement="",
            parameters=(),
            sql_state=str(SqlState.INVALID_KEY_NUMBER),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state = table.state_for(table_name, slot)

    if not start_access_type_is_valid(access_type):
        lower, upper = START_ACCESS_TYPE_RANGE
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator="[common/glpostingMT.cbl:L695-L699]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            detail="Access-Type %d rejected; the guard admits %d..%d only"
            % (access_type, lower, upper),
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.ACCESS_TYPE_WRONG),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    if state.cursor_active():
        state.free()

    relation = MostRelation.for_access_type(access_type)
    state.most_relation = relation
    state.key_of_reference = key

    statement = _select_statement(key, relation.token)
    parameters = (key_value,)

    try:
        cursor.execute(statement, parameters)
    except Exception as error:  # any driver error takes this path - see below
        # A failed statement reaches `(21, 0)` by being OVERWRITTEN, not by
        # being classified, and both steps are in the frozen source:
        #  1. `Mysql-1210-Command` calls `MySQL_query` and on a non-zero return
        #  performs `Mysql-1100-Db-Error`
        #  [copybooks/mysql-procedures.cpy:L165-L177], which sets `(99, 911)`
        #  [copybooks/mysql-procedures.cpy:L127-L128]. There is NO `go to`
        #  after it, so execution continues and leaves `WS-MYSQL-Count-Rows`
        #  at zero.
        #  2. Back in `ba060`, `if WS-MYSQL-Count-Rows = zero` is therefore
        #  true, errno is non-zero, and `move 21 to fs-reply` /
        #  `move zero to we-error` [common/glpostingMT.cbl:L779-L780]
        #  REPLACE the pair from step 1.
        #
        # So the observable status of a broken START statement is `(21, 0)` - not
        # `(99, 911)`, and not the `990`/`989` that belong to read-indexed. The
        # cursor is untouched on this path: `if ... not zero set Cursor-Active`
        # [common/glpostingMT.cbl:L767-L769] simply does not fire, and step 3
        # above has already left it inactive.
        errno, sql_state = _driver_failure_fields(error)
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba060-Process-Start",
            locator="[common/glpostingMT.cbl:L775-L781]",
            fs_reply=int(FsReply.INVALID_KEY_ON_START),
            we_error=int(WeError.SUCCESS),
            sql_err=errno,
            sql_state=sql_state,
            detail="the positioning statement failed at the driver for "
            + key.table_name
            + "."
            + key.column_name,
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.INVALID_KEY_ON_START,
            we_error=int(WeError.SUCCESS),
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=str(SqlState.COULD_NOT_GENERATE_START),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    count = state.store_result(_store_result(cursor))
    row = None if count == 0 else state.stored_rows[0]

    if row is None:
        # ANOMALY A7: no row, no driver error -> NEITHER status field written.
        # [common/glpostingMT.cbl:L771-L781]. The cursor is not touched here
        # either: L767's `if` does not fire and L771-L781 never mentions it, so
        # the inactive state established at step 3 stands.
        #
        # AND NOTHING IS REPORTED, because the bridge reports nothing. This is the
        # anomaly: a caller that asked where a key is gets its own stale status
        # pair back and no indication that the answer is stale. A log line here
        # would be a diagnostic the compiled program cannot produce and would make
        # the silence look like an oversight rather than the reproduced defect it
        # is (rule R-4). A7 is recorded in `docs/migration/anomaly-log.md`.
        outcome = CursorOutcome(
            fs_reply=incoming_fs_reply,
            we_error=incoming_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            status_written=False,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # [common/glpostingMT.cbl:L769] and `move zero to FS-Reply WE-Error`
    # [common/glpostingMT.cbl:L783]. The position is INCLUSIVE and the row is
    # DELIBERATELY NOT RETURNED.
    state.position_at(row[key.column_name])
    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=None,
        statement=statement,
        parameters=parameters,
    )
    if file_access is not None:
        outcome.apply_to(file_access)
    return outcome


def read_next(
    cursor: DatabaseCursor,
    table_name: str,
    *,
    slot: CursorSlot = CursorSlot.PRIMARY,
    states: CursorStateTable | None = None,
    file_access: FileAccess | None = None,
) -> CursorOutcome:
    """``fn-read-next`` (``File-Function`` 3) - return the next row, one row.

    Reproduces ``ba040-Process-Read-Next`` [common/glpostingMT.cbl:L448-L521] and
    ``ba041-Reread`` [common/glpostingMT.cbl:L523-L589], which it falls into. The two
    are stages of one verb: ``ba040`` positions when there is no position, ``ba041``
    delivers a row.

    Args:
        cursor: A DB-API cursor from ``connection.py``.
        table_name: The in-scope table to read.
        slot: Which ``Most-Cursor-Set`` flag to drive; the multi-slot bridges keep one
            per read order [common/otm3MT.cbl:L265-L270].
        states: The cursors to use; the module-level set when ``None``.
        file_access: When given, the outcome is applied to it before returning and its
            incoming ``FS-Reply`` participates in the A10 test, as it must.

    Returns:
        The outcome. On success :attr:`CursorOutcome.row` holds the row keyed by column
            name; at end of file the pair is ``(10, 10)`` and row is ``None``.

    Raises:
        KeyError: If the table declares no key of reference.
        LookupError: If the table has no sequential read in the frozen bridges - the two
            lines tables of anomaly A12, unreachable from COBOL.
    """
    table = states if states is not None else _DEFAULT_STATES
    # Anomaly A10 reads the caller's own field, so snapshot before anything runs.
    incoming_fs_reply, incoming_we_error = _incoming_status(file_access)

    # The handler entry guard, data-driven. `fn-read-next` is NOT among the four verbs
    # the sequential handler refuses [common/acas008.cbl:L299-L307], so this returns
    # `None` for every in-scope table.
    refusal = _guarded_by_handler(table_name, FileFunction.READ_NEXT)
    if refusal is not None:
        fs_reply, we_error, locator = refusal
        #  ONE ERROR: `FS-Reply` 99 goes back to the caller, so the verb failed.
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba050-Process-Read-Next",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="fn-read-next refused by the handler for " + table_name,
        )
        outcome = CursorOutcome(
            fs_reply=fs_reply,
            we_error=int(we_error),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state = table.state_for(table_name, slot)

    if not state.cursor_not_active():
        # advances the STORED RESULT an earlier positioning materialised.
        key = state.key_of_reference or key_of_reference(table_name, 1)
        return _deliver_from_stored_result(
            state,
            key,
            empty_tag="EOF",
            incoming_fs_reply=incoming_fs_reply,
            incoming_we_error=incoming_we_error,
            file_access=file_access,
        )

    # [common/glpostingMT.cbl:L454-L473]. `set KOR-x1 to 1` - key 1 always, per anomaly
    # A12 - and the bridge's own hard-coded relation and low key, per anomaly A9.
    key = key_of_reference(table_name, 1)
    low = SEQUENTIAL_READ_START.get(table_name)
    if low is None:
        raise LookupError(
            f"{table_name} has no ba040-Process-Read-Next in the frozen "
            f"bridges, so the compiled system cannot read it sequentially; "
            f"see anomaly A12. Reach it through its header bridge's second "
            f"key of reference instead."
        )
    relation = low.relation
    key_value: object = low.low_key
    # `"No Data"` is the log tag `ba040` writes when this stage yields nothing
    # [common/glpostingMT.cbl:L510].
    empty_tag = "No Data"

    statement = _select_statement(key, relation.token)
    parameters = (key_value,)

    try:
        cursor.execute(statement, parameters)
    except Exception as error:  # any driver error takes this path - see below
        # ANOMALY A11: the error is MASKED as end of file, because the two
        # unconditional moves overwrite `Mysql-1100-Db-Error`'s `(99, 911)`
        # [common/glpostingMT.cbl:L508-L509]. Reported at ERROR - one record, with
        # the status pair that will actually be returned - so that the masking is
        # visible to an operator at the level failures are watched at. That
        # changes no status: the `(10, 200)` below is still what the caller sees.
        errno, sql_state = _driver_failure_fields(error)
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba050-Process-Read-Next",
            locator="[common/glpostingMT.cbl:L508-L509]",
            fs_reply=int(end_of_file_status()[0]),
            we_error=int(end_of_file_status()[1]),
            sql_err=errno,
            sql_state=sql_state,
            detail="the sequential read failed at the driver for "
            + key.table_name
            + "."
            + key.column_name
            + " and is MASKED as end of file (anomaly A11)",
        )
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=str(SqlState.NO_DATA),
            file_key=empty_tag,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    count = state.store_result(_store_result(cursor))

    if count == 0:
        # `if WS-MYSQL-Count-Rows = zero ... move 10 to fs-reply / move 10 to WE-Error`
        # [common/glpostingMT.cbl:L499-L509].
        state.set_cursor_not_active()
        end_fs_reply, end_we_error = end_of_file_status()
        outcome = CursorOutcome(
            fs_reply=end_fs_reply,
            we_error=end_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            file_key=empty_tag,
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state.key_of_reference = key
    state.most_relation = relation
    state.set_cursor_active()
    return _deliver_from_stored_result(
        state,
        key,
        empty_tag=empty_tag,
        incoming_fs_reply=incoming_fs_reply,
        incoming_we_error=incoming_we_error,
        file_access=file_access,
        statement=statement,
        parameters=parameters,
    )


def read_indexed(
    cursor: DatabaseCursor,
    table_name: str,
    key_value: object,
    *,
    key_number: int = 1,
    slot: CursorSlot = CursorSlot.PRIMARY,
    states: CursorStateTable | None = None,
    file_access: FileAccess | None = None,
) -> CursorOutcome:
    """``fn-read-indexed`` (``File-Function`` 4) - fetch one row by exact key.

    Reproduces ``ba050-Process-Read-Indexed`` [common/glpostingMT.cbl:L591-L689]: an
    equality fetch on the key of reference with NO ``ORDER BY`` and NO ``LIMIT``,
    matching the statement the bridge builds, `` `KeyName`="value" `` and nothing more
    [:L600-L611, :L623-L627].

    Args:
        cursor: A DB-API cursor from ``connection.py``.
        table_name: The in-scope table to read.
        key_value: The exact key, as ``str``, ``int`` or ``Decimal`` - never a binary
            floating-point value, which rule R-2 forbids and which would make an
            equality test unreliable.
        key_number: The ``KOR-x1`` value. The paragraph hard-codes ``set KOR-x1 to 1``,
            annotated ``*> 1 = only key`` [common/glpostingMT.cbl:L596].
        slot: Which ``Most-Cursor-Set`` flag is cleared.
        states: The cursors to use; the module-level set when ``None``.
        file_access: When given, the outcome is applied to it before returning.

    Returns:
        The outcome. On success the row keyed by column name and ``(0, 0)``; when the
            key is absent, ``(21, <the caller's We-Error>)`` and no row.

    Raises:
        KeyError: If the table declares no key of reference.
    """
    table = states if states is not None else _DEFAULT_STATES
    # The reachable not-found path writes FS-Reply only, so the caller's `We-Error`
    # survives it [common/glpostingMT.cbl:L634]. Snapshot it.
    _, incoming_we_error = _incoming_status(file_access)

    # The handler entry guard.
    refusal = _guarded_by_handler(table_name, FileFunction.READ_INDEXED)
    if refusal is not None:
        fs_reply, we_error, locator = refusal
        #  ONE ERROR: `FS-Reply` 99 goes back to the caller, so the verb failed.
        #  This is the arm anomaly A6 travels on - `acas008` refuses read-indexed
        #  unconditionally - and reporting it at DEBUG made a verb that can never
        #  succeed invisible at the level an operator watches.
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba070-Process-Read-Indexed",
            locator=locator,
            fs_reply=int(fs_reply),
            we_error=int(we_error),
            detail="fn-read-indexed refused by the handler for " + table_name,
        )
        outcome = CursorOutcome(
            fs_reply=fs_reply,
            we_error=int(we_error),
            row=None,
            statement="",
            parameters=(),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # An out-of-range key number is the never-implemented `'99NKU'` situation, "No valid
    # key used" [copybooks/mysql-procedures.cpy:L116]. Anomaly A3.
    try:
        key = key_of_reference(table_name, key_number)
    except IndexError:
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba070-Process-Read-Indexed",
            locator="[copybooks/mysql-procedures.cpy:L116, :L127-L128]",
            fs_reply=int(FsReply.ERROR),
            we_error=int(WeError.RDB_INIT_ERROR),
            sql_state=str(SqlState.NO_VALID_KEY),
            detail="invalid key number %d for %s, which the frozen source "
            "describes and never implements" % (key_number, table_name),
        )
        outcome = CursorOutcome(
            fs_reply=FsReply.ERROR,
            we_error=int(WeError.RDB_INIT_ERROR),
            row=None,
            statement="",
            parameters=(),
            sql_state=str(SqlState.NO_VALID_KEY),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    state = table.state_for(table_name, slot)

    # `\`KeyName\`="value"` and nothing else [common/glpostingMT.cbl:L602-L608]. The
    # value is bound rather than interpolated into the text.
    column = quote_identifier(key.column_name)
    statement = (
        f"SELECT * FROM {quote_identifier(key.table_name)} WHERE {column} = %s"
    )
    parameters = (key_value,)

    try:
        cursor.execute(statement, parameters)
        # `PERFORM MYSQL-1220-STORE-RESULT THRU MYSQL-1239-EXIT` follows the command
        # IMMEDIATELY [common/glpostingMT.cbl:L628-L629], exactly as it does for the
        # sequential read [:L488-L489] and the START [:L762-L763].
        count = state.store_result(_store_result(cursor))
    except Exception as error:  # any driver error takes this path - see below
        # ANOMALY A14: `(21, 911)` - 21 overwrites the 99, 911 survives.
        # A FAILURE OF EITHER CALL LANDS HERE, and the frozen source is why:
        # `Mysql-1100-Db-Error` is performed both from `Mysql-1210-Command` on a
        # non-zero `MySQL_query` return [copybooks/mysql-procedures.cpy:L165-L177]
        # and from `Mysql-1220-Store-Result` when the result pointer comes back
        # null [:L188-L189]. Neither performs a `go to`, so in both cases the
        # count is left at zero and `ba050`'s first guard's `move 21 to fs-Reply`
        # [common/glpostingMT.cbl:L634] overwrites the 99 while the 911 survives.
        errno, sql_state = _driver_failure_fields(error)
        log_handler_failure(
            _LOG,
            program=_BRIDGE_PROGRAM,
            paragraph="ba070-Process-Read-Indexed",
            locator="[common/glpostingMT.cbl:L634] over "
            "[copybooks/mysql-procedures.cpy:L127-L128]",
            fs_reply=int(FsReply.INVALID_KEY_ON_START),
            we_error=int(WeError.RDB_INIT_ERROR),
            sql_err=errno,
            sql_state=sql_state,
            detail="the indexed read failed at the driver for "
            + key.table_name
            + "."
            + key.column_name
            + " and is reported as (21, 911) (anomaly A14)",
        )
        state.free()
        outcome = CursorOutcome(
            fs_reply=FsReply.INVALID_KEY_ON_START,
            we_error=int(WeError.RDB_INIT_ERROR),
            row=None,
            statement=statement,
            parameters=parameters,
            sql_state=str(SqlState.NO_DATA),
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    # `if WS-MYSQL-Count-Rows = zero move 21 to fs-Reply go to ba998-Free`
    # [common/glpostingMT.cbl:L633-L636] is the FIRST guard and, per anomaly A13 in this
    # function's docstring, the only reachable one - so the fetch is reached only when
    # the snapshot holds a record.
    row = state.fetch_record() if count > 0 else None

    # Every exit below frees the cursor, because every exit in the paragraph is `go to
    # ba998-Free` [common/glpostingMT.cbl:L635, :L674, :L681, :L689].
    state.free()

    if row is None:
        # ANOMALY A2 and A13: 21, never 23; and `We-Error` is NOT written, so the
        # caller's value survives [common/glpostingMT.cbl:L633-L636].
        #
        # AND NOTHING IS REPORTED. "Key not found" is an ORDINARY outcome that
        # every caller in the cycle tests for and branches on - it is not a
        # failure - and the frozen guard displays nothing. The comment below
        # records that the reachable guard writes no log tag either, so a record
        # here would be the only diagnostic in the whole path and would come from
        # this migration rather than from the specification (rule R-4).
        outcome = CursorOutcome(
            fs_reply=FsReply.INVALID_KEY_ON_START,
            we_error=incoming_we_error,
            row=None,
            statement=statement,
            parameters=parameters,
            # `move spaces to WS-File-Key` is written only on the two dead branches
            # [common/glpostingMT.cbl:L673, :L680]; the reachable guard writes no log
            # tag, so none is reported.
        )
        if file_access is not None:
            outcome.apply_to(file_access)
        return outcome

    outcome = CursorOutcome(
        fs_reply=FsReply.SUCCESS,
        we_error=int(WeError.SUCCESS),
        row=row,
        statement=statement,
        parameters=parameters,
        file_key=str(row[key.column_name]),
    )
    if file_access is not None:
        outcome.apply_to(file_access)
    return outcome


def reset(table_name: str | None = None) -> None:
    """Clear cursor state on the module-level set of cursors.

    Every bridge holds its ``01 DAL-Data`` in its own working storage
    [common/glpostingMT.scb:L247-L251], so in the compiled system cursors are isolated
    by construction and a fresh run starts from ``value zero``.

    Args:
        table_name: Clear only this table's cursors when given, all of them when
            ``None``.

    Raises:
        KeyError: If ``table_name`` is given and declares no key of reference.
    """
    if table_name is not None and table_name not in TABLE_OF_KEYNAMES:
        raise KeyError(
            f"{table_name!r} declares no Table-Of-Keynames entry; the in-scope "
            f"tables are {', '.join(TABLE_OF_KEYNAMES)}"
        )
    _DEFAULT_STATES.reset(table_name)
