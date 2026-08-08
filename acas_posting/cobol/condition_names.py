"""88-level condition names: the frozen value sets, and predicates over them.

Every `88` level the migrated cycle tests, transcribed once from the copybook that
declares it and published as a predicate: the file function codes and access types
[copybooks/wsfnctn.cob:L89-L116], the batch status names, and the IRS fan-out
switch [copybooks/wssystem.cob:L179-L181].

A condition name is looked up by its COBOL spelling, and a name declared in more
than one copybook with DIFFERENT value clauses is refused rather than resolved:
returning one silently would make the name mean whichever copybook happened to be
transcribed first. COBOL meets the same problem and answers it the same way -
field-name collisions force qualified references, as at
[general/gl070.cbl:L497], [general/gl070.cbl:L521] and
[general/gl070.cbl:L525] - so a caller disambiguates with the copybook or the
conditional variable, exactly as the COBOL qualifies.

This module holds no business logic: it says what a condition name means, never
what to do when it holds.
"""

from __future__ import annotations

import dataclasses
import decimal
import enum
import types
from pathlib import Path
from typing import Callable, Final, Mapping

from acas_posting.cobol.field import FieldDescriptor

# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader` and
# nothing else from the dictionary package.
from acas_posting.dictionary import loader


class ConditionKind(enum.StrEnum):
    """The shape of the VALUE clause a condition name is declared with.

    Six members, one per shape the in-scope layouts actually use.

    Attributes:
        SINGLE: One numeric literal. `88 G-L value 1.` [copybooks/wssystem.cob:L85].
        FIGURATIVE: One figurative constant, spelled as the copybook spells it. The only
            one used is `zero`, which reads as the number 0. `88 No-OS value zero.`
            [copybooks/wssystem.cob:L102].
        VALUE_LIST: Two or more numeric literals, contiguous or gapped. Tested by
            membership, never by range.
        THRU_RANGE: A `thru` range, INCLUSIVE on both bounds. `88 FS-Valid-Options
            values 0 thru 1.` [copybooks/wssystem.cob:L122].
        ALPHANUMERIC: ONE quoted literal, its delimiters kept in the recorded value so a
            one-character switch is unambiguous. `88 Auto-Vat value "Y".`
            [copybooks/wssystem.cob:L174].
        ALPHANUMERIC_LIST: TWO OR MORE quoted literals, in declaration order, tested by
            membership exactly as `VALUE_LIST` is on the numeric side.
    """

    SINGLE = "SINGLE"
    FIGURATIVE = "FIGURATIVE"
    VALUE_LIST = "VALUE_LIST"
    THRU_RANGE = "THRU_RANGE"
    ALPHANUMERIC = "ALPHANUMERIC"
    ALPHANUMERIC_LIST = "ALPHANUMERIC_LIST"


# Short private aliases, bound once. The registry below is 159 entries long and reads as
# a table.
_SINGLE: Final[ConditionKind] = ConditionKind.SINGLE
_FIG: Final[ConditionKind] = ConditionKind.FIGURATIVE
_LIST: Final[ConditionKind] = ConditionKind.VALUE_LIST
_THRU: Final[ConditionKind] = ConditionKind.THRU_RANGE
_ALNUM: Final[ConditionKind] = ConditionKind.ALPHANUMERIC
_ALIST: Final[ConditionKind] = ConditionKind.ALPHANUMERIC_LIST

# The two alphanumeric shapes, as a tuple so `is_alphanumeric` and the two
# `numeric_values` guards all read from one place and cannot drift apart.
_ALPHANUMERIC_KINDS: Final[tuple[ConditionKind, ...]] = (
    ConditionKind.ALPHANUMERIC,
    ConditionKind.ALPHANUMERIC_LIST,
)

# The thirteen frozen copybooks the registry is transcribed from, as repository-relative
# paths spelled the way the generated dictionary spells them, so a locator built here
# and one read from the dictionary compare equal without either side being touched.
_WSFNCTN: Final[str] = "copybooks/wsfnctn.cob"
_WSBATCH: Final[str] = "copybooks/wsbatch.cob"
_WSSYSTEM: Final[str] = "copybooks/wssystem.cob"
_WSSL: Final[str] = "copybooks/wssl.cob"
_WSPL: Final[str] = "copybooks/wspl.cob"
_SLWSINV: Final[str] = "copybooks/slwsinv.cob"
_SLWSINV2: Final[str] = "copybooks/slwsinv2.cob"
_SLWSOI: Final[str] = "copybooks/slwsoi.cob"
_PLWSPINV: Final[str] = "copybooks/plwspinv.cob"
_PLWSPINV2: Final[str] = "copybooks/plwspinv2.cob"
_PLWSOI: Final[str] = "copybooks/plwsoi.cob"
_IRSWSNL: Final[str] = "copybooks/irswsnl.cob"
_TESTFLAGS: Final[str] = "copybooks/Test-Data-Flags.cob"

# The figurative constants a VALUE clause may use, mapped to the number each one reads
# as.
_FIGURATIVE_NUMBERS: Final[Mapping[str, int]] = types.MappingProxyType(
    {
        "zero": 0,
        "zeros": 0,
        "zeroes": 0,
    }
)

# The delimiters COBOL accepts around an alphanumeric literal. Every in-scope `88` uses
# the double quote.
_LITERAL_DELIMITERS: Final[tuple[str, ...]] = ('"', "'")


@dataclasses.dataclass(frozen=True, slots=True)
class ConditionNameSpec:
    """One `88`-level condition name, exactly as the frozen copybook declares it.

    Frozen and slotted for the same reasons the sibling value objects are: a spec is
    compared by value, may be used as a mapping key, and must not be mutated by a caller
    that received it from the registry.

    Attributes:
        cobol_name: The condition name verbatim, its case preserved.
        python_name: The snake_case predicate name for it, DERIVED from `cobol_name` by
            lowercasing, turning each hyphen into an underscore and prefixing `is_`.
        predicate_name: The row's UNIQUE published predicate name.
        values: The literals of the VALUE clause, as separate tokens, in declaration
            order, each carried as `str` (rule R-2).
        kind: The shape of the clause.
        conditional_variable: The COBOL name of the field the condition name is declared
            on - its conditional variable - taken from the generated dictionary, which
            records which field owns each condition name.
        copybook: The repository-relative path of the declaring copybook.
        locator: `<copybook>:L<line>` for this entry's own declaration.
        declaration_index: This entry's zero-based position among the condition names of
            its conditional variable, in DECLARATION order. It is what makes the out-of-
            numeric-order function codes checkable.
        notes: Free prose recording what a reader needs to know about this entry - that
            it is never tested, that its value duplicates a sibling's, that the
            declaration order is not the numeric order.
    """

    cobol_name: str
    python_name: str
    values: tuple[str, ...]
    kind: ConditionKind
    conditional_variable: str
    copybook: str
    locator: str
    declaration_index: int
    notes: str
    predicate_name: str = ""

    @property
    def value_clause_text(self) -> str:
        """The VALUE clause text, rebuilt from `values` and `kind`.

        DERIVED, not stored, so it cannot drift from `values`. The rebuilt text is byte-
        identical to `loader.ConditionName.value` for all 159 entries, which is what
        lets `cross_check_against_dictionary` compare the two sources without either
        being touched.

        Returns:
            The clause text, for example `"1 2 4"`, `"0 thru 1"`, `"zero"`, `'"Y"'` or
                `'"P" "p"'`.
        """
        if self.kind is ConditionKind.THRU_RANGE:
            return self.values[0] + " thru " + self.values[1]
        return " ".join(self.values)

    @property
    def qualified_cobol_name(self) -> str:
        """The name in COBOL's own qualified form, for an unambiguous citation.

        Fourteen of the registry's names are declared in more than one copybook, and the
        compiled cycle meets the same problem: anomaly A-21 records that field-name
        collisions across the posting copybooks force `gl070` to write qualified
        references, at [general/gl070.cbl:L497].

        Returns:
            `<name> of <conditional variable> in <copybook>`, for example `pending of
                sih-status in copybooks/slwsinv.cob`.
        """
        return (
            self.cobol_name + " of " + self.conditional_variable
            + " in " + self.copybook
        )

    @property
    def is_alphanumeric(self) -> bool:
        """Whether the clause is quoted literals rather than numbers.

        True for BOTH alphanumeric shapes, so a caller asking "is this text?" never has
        to know that a multi-literal clause is a separate member.

        Returns:
            True for `ALPHANUMERIC` and `ALPHANUMERIC_LIST`, False for every numeric
                shape.
        """
        return self.kind in _ALPHANUMERIC_KINDS

    @property
    def declaration_text(self) -> str:
        """The `88` line rebuilt in COBOL form, for a report or a log line.

        `values` for a list clause is written with the plural keyword the copybook uses,
        and a range likewise, because that is how the frozen line reads.

        Returns:
            For example `88 OS-Single values 1 2 4.`.
        """
        keyword = "value" if len(self.values) == 1 else "values"
        head = "88  " + self.cobol_name + "  "
        return head + keyword + " " + self.value_clause_text + "."

    def cite(self) -> str:
        """The locator, for quoting in a message, a comment or a document.

        Returns:
            `<copybook>:L<line>`, for example `copybooks/wsbatch.cob:L26`.
        """
        return self.locator

    def literal_text(self) -> str:
        """The characters inside the FIRST alphanumeric literal, undelimited.

        Only fully meaningful for an `ALPHANUMERIC` spec, which has exactly one literal.
        For an `ALPHANUMERIC_LIST` this returns the first of several and is therefore
        NOT the whole clause - use `literal_texts` for that, which is what `evaluate`
        does.

        Returns:
            The first literal's characters.
        """
        return _undelimit(self.values[0])

    def literal_texts(self) -> tuple[str, ...]:
        """Every alphanumeric literal's characters, in declaration order.

        The whole clause, which is what a comparison must test against: COBOL tests an
        alphanumeric condition name by membership over ALL of its literals, exactly as
        it does a numeric `VALUE_LIST`.

        Returns:
            The literals' characters, delimiters removed, in declaration order.
        """
        return tuple(_undelimit(token) for token in self.values)

    def numeric_values(self) -> tuple[decimal.Decimal, ...]:
        """The clause's literals as exact decimals, in declaration order.

        A figurative constant reads as the number it stands for, so `zero` yields
        `Decimal(0)` and compares equal to a field holding 0 - which is why
        [copybooks/wsbatch.cob:L26] writing `value 0` and [copybooks/wssl.cob:L27]
        writing `value zero` behave identically while both stay recorded as written
        (rule R-4).

        Returns:
            The literals as decimals.

        Raises:
            ValueError: The spec is alphanumeric - of either alphanumeric shape - so its
                literals are text and have no numeric reading.
        """
        if self.is_alphanumeric:
            raise ValueError(
                "Condition name " + repr(self.cobol_name) + " at " + self.locator
                + " is declared with "
                + ("an alphanumeric literal, " if len(self.values) == 1
                   else "alphanumeric literals, ")
                + ", ".join(repr(token) for token in self.values)
                + ", so it has no numeric reading. Compare it as text; "
                + "`kind` and `is_alphanumeric` state the shape."
            )
        return tuple(_read_number(token) for token in self.values)


def _read_number(token: str) -> decimal.Decimal:
    """Read one recorded numeric literal as an exact decimal.

    A figurative constant is looked up; anything else is read as digits. Exact in both
    directions and free of any rounding decision, so no `decimal` context is consulted
    (rule R-2, rule R-6).

    Args:
        token: The literal as the registry records it, for example `"15"` or `"zero"`.

    Returns:
        Its numeric reading.

    Raises:
        ValueError: The token is neither a figurative constant this module knows nor a
            number.
    """
    figurative = _FIGURATIVE_NUMBERS.get(token.casefold())
    if figurative is not None:
        return decimal.Decimal(figurative)
    return decimal.Decimal(token)


def _read_operand(value: int | str | decimal.Decimal) -> decimal.Decimal | None:
    """Read a caller's value as an exact decimal, or report that it does not read.

    Returning None rather than raising is rule R-3 in one line: a `pic 9` field holding
    spaces satisfies no condition name, and COBOL says so by failing the comparison, not
    by stopping.

    Args:
        value: The caller's value. A `float` or `complex` never reaches this function;
            `evaluate` refuses those first.

    Returns:
        The value as an exact decimal, or None when it has no numeric reading.
    """
    if isinstance(value, decimal.Decimal):
        # A quiet NaN would compare unequal to everything, which is the right answer,
        # but a signalling one raises on comparison - so it is reported as not reading
        # rather than allowed through.
        return None if not value.is_finite() else value
    if isinstance(value, int):
        return decimal.Decimal(value)
    try:
        read = decimal.Decimal(value.strip())
    except (ArithmeticError, ValueError, AttributeError):
        return None
    return None if not read.is_finite() else read


def _undelimit(token: str) -> str:
    """Strip a quoted literal's delimiters, leaving its characters.

    The delimiters belong to the source text, not to the value: the compiler compares
    the CHARACTERS of a quoted literal against an alphanumeric item, so `'"Y"'` reads as
    `Y`.

    Args:
        token: One value token as the copybook writes it.

    Returns:
        Its characters, without delimiters.
    """
    for delimiter in _LITERAL_DELIMITERS:
        if (
            len(token) >= 2
            and token.startswith(delimiter)
            and token.endswith(delimiter)
        ):
            return token[1:-1]
    return token


def _pad(text: str, width: int) -> str:
    """Space-pad text on the right to a width, the way COBOL compares.

    An alphanumeric comparison in COBOL treats the shorter operand as though it were
    padded on the right with spaces to the length of the longer.

    Args:
        text: The operand.
        width: The width to pad to.

    Returns:
        The operand, padded if it was shorter.
    """
    return text if len(text) >= width else text + " " * (width - len(text))


def _spec(
    cobol_name: str,
    values: tuple[str, ...],
    kind: ConditionKind,
    conditional_variable: str,
    copybook: str,
    line: int,
    declaration_index: int,
    notes: str = "",
) -> ConditionNameSpec:
    """Build one registry row, deriving the predicate name and the locator.

    Two members are DERIVED here rather than written 159 times, which removes 159
    chances to mistype one and makes it impossible for a name and its locator to
    disagree with the row they sit on.

    Args:
        cobol_name: The condition name verbatim, its case preserved.
        values: The clause's literals as separate tokens, in declaration order.
        kind: The shape of the clause.
        conditional_variable: The COBOL name of the owning field.
        copybook: The declaring copybook's repository-relative path.
        line: The line in that copybook that declares THIS condition name.
        declaration_index: Zero-based position among its group's condition names, in
            declaration order.
        notes: What a reader needs to know about this row, if anything.

    Returns:
        The row.
    """
    return ConditionNameSpec(
        cobol_name=cobol_name,
        python_name="is_" + cobol_name.casefold().replace("-", "_"),
        values=values,
        kind=kind,
        conditional_variable=conditional_variable,
        copybook=copybook,
        locator=copybook + ":L" + str(line),
        declaration_index=declaration_index,
        notes=notes,
    )


# THE REGISTRY (rule R-5: every row carries its own line) 159 rows - every `88`-level
# declaration in the in-scope copybook closure.

_REGISTRY_ROWS: Final[tuple[ConditionNameSpec, ...]] = (
    # copybooks/wsfnctn.cob - 30 rows. The file is 117 lines long, so the plan's
    # L88-L118 citation of the vocabulary names a line past its end.
    _spec(
        "MRMF-Move-FD", ("1",), _SINGLE,
        "Main-Record-Move-Flag", _WSFNCTN, 67, 0,
        "Declared with the maintainer's note NOT YET USED at "
        "[copybooks/wsfnctn.cob:L64].",
    ),
    _spec(
        "MRMF-Move-WS", ("2",), _SINGLE,
        "Main-Record-Move-Flag", _WSFNCTN, 68, 1,
        "Declared with the maintainer's note NOT YET USED at "
        "[copybooks/wsfnctn.cob:L64].",
    ),
    _spec(
        "FA-FS-Cobol-Files-Used", ("zero",), _FIG,
        "FA-File-System-Used", _WSFNCTN, 74, 0,
        "Figurative constant. Reads as 0, so it holds for 0 and for the text "
        '"0".',
    ),
    _spec(
        "FA-FS-RDBMS-Used", ("1",), _SINGLE,
        "FA-File-System-Used", _WSFNCTN, 75, 1,
        "The generic name that replaced a per-engine one; the superseded "
        "FA-FS-MySql-Used sits behind a comment at "
        "[copybooks/wsfnctn.cob:L76].",
    ),
    _spec(
        "FA-FS-Valid-Options", ("0", "1"), _THRU,
        "FA-File-System-Used", _WSFNCTN, 81, 2,
        "A thru range, inclusive on both bounds. The trailing comment reads "
        '"5. (not in use unless 1-5)", so the range was narrowed from five '
        "options to two and the wider intent is recorded only in that "
        "comment.",
    ),
    _spec(
        "FA-FS-Duplicate-Processing", ("1",), _SINGLE,
        "FA-File-Duplicates-In-Use", _WSFNCTN, 83, 0,
        "The field's own comment at [copybooks/wsfnctn.cob:L82] reads "
        "\"NO LONGER USED other than for a '6' = rdb\" - and 6 is not one of "
        "the values any condition name on it declares.",
    ),
    _spec("fn-open", ("1",), _SINGLE, "File-Function", _WSFNCTN, 89, 0),
    _spec("fn-close", ("2",), _SINGLE, "File-Function", _WSFNCTN, 90, 1),
    _spec("fn-read-next", ("3",), _SINGLE, "File-Function", _WSFNCTN, 91, 2),
    _spec("fn-read-indexed", ("4",), _SINGLE, "File-Function", _WSFNCTN, 92, 3),
    _spec("fn-write", ("5",), _SINGLE, "File-Function", _WSFNCTN, 93, 4),
    _spec(
        "fn-Delete-All", ("6",), _SINGLE, "File-Function", _WSFNCTN, 94, 5,
        "Mixed capitalisation, kept as declared (rule R-5). Added 10/10/16 per "
        "the trailing comment.",
    ),
    _spec("fn-re-write", ("7",), _SINGLE, "File-Function", _WSFNCTN, 95, 6),
    _spec("fn-delete", ("8",), _SINGLE, "File-Function", _WSFNCTN, 96, 7),
    _spec("fn-start", ("9",), _SINGLE, "File-Function", _WSFNCTN, 97, 8),
    # declared before 13 - `88 fn-Write-Raw value 15.` at [copybooks/wsfnctn.cob:L99],
    # `88 fn-Read-Next-Raw value 13.` at [copybooks/wsfnctn.cob:L100] - so the group's
    # declaration sequence is 1 2 3 4 5 6 7 8 9 15 13 31 32 33 34.
    _spec(
        "fn-Write-Raw", ("15",), _SINGLE, "File-Function", _WSFNCTN, 99, 9,
        "OUT OF NUMERIC ORDER: value 15 is declared at "
        "[copybooks/wsfnctn.cob:L99], BEFORE value 13 at "
        "[copybooks/wsfnctn.cob:L100], so the group runs "
        "1 2 3 4 5 6 7 8 9 15 13 31 32 33 34. Declaration order is preserved "
        "(rule R-4). Not SET anywhere in the frozen copybooks; it serves the "
        "*LD loader programs.",
    ),
    _spec(
        "fn-Read-Next-Raw", ("13",), _SINGLE, "File-Function", _WSFNCTN, 100, 10,
        "OUT OF NUMERIC ORDER: value 13 is declared at "
        "[copybooks/wsfnctn.cob:L100], AFTER value 15 at "
        "[copybooks/wsfnctn.cob:L99]. The trailing comment reads "
        '"14/11/16 - Special 4 LD." and the file header at '
        "[copybooks/wsfnctn.cob:L15] records the change: "
        '"next-read-raw changed to 13."',
    ),
    # A `*>` comment at [copybooks/wsfnctn.cob:L101] separates the raw pair from the by-
    # name reads, which is why the next four sit at L102-L105 and not at L101-L104 as
    # the plan's working note states.
    _spec(
        "fn-Read-By-Name", ("31",), _SINGLE, "File-Function", _WSFNCTN, 102, 11,
        "L102, not L101: [copybooks/wsfnctn.cob:L101] is a comment line.",
    ),
    _spec(
        "fn-Read-By-Batch", ("32",), _SINGLE, "File-Function", _WSFNCTN, 103, 12,
    ),
    _spec(
        "fn-Read-By-Cust", ("33",), _SINGLE, "File-Function", _WSFNCTN, 104, 13,
    ),
    _spec(
        "fn-Read-Next-Header", ("34",), _SINGLE, "File-Function", _WSFNCTN, 105,
        14,
        "The last row of the group, at L105 - so the group spans L89-L105.",
    ),
    _spec("fn-input", ("1",), _SINGLE, "Access-Type", _WSFNCTN, 108, 0),
    _spec("fn-i-o", ("2",), _SINGLE, "Access-Type", _WSFNCTN, 109, 1),
    _spec("fn-output", ("3",), _SINGLE, "Access-Type", _WSFNCTN, 110, 2),
    _spec(
        "fn-extend", ("4",), _SINGLE, "Access-Type", _WSFNCTN, 111, 3,
        'The trailing comment reads "not valid for ISAM".',
    ),
    _spec("fn-equal-to", ("5",), _SINGLE, "Access-Type", _WSFNCTN, 112, 4),
    _spec("fn-less-than", ("6",), _SINGLE, "Access-Type", _WSFNCTN, 113, 5),
    _spec("fn-greater-than", ("7",), _SINGLE, "Access-Type", _WSFNCTN, 114, 6),
    _spec("fn-not-less-than", ("8",), _SINGLE, "Access-Type", _WSFNCTN, 115, 7),
    _spec(
        "fn-not-greater-than", ("9",), _SINGLE, "Access-Type", _WSFNCTN, 116, 8,
        "The last condition name in the file. Activated 06/08/23 per the file "
        "header at [copybooks/wsfnctn.cob:L20].",
    ),
    # copybooks/wsbatch.cob - 8 rows. The three most load-bearing groups in the whole
    # cycle: they gate whether posting happens at all.
    _spec(
        "GL-Batch", ("1",), _SINGLE, "WS-Ledger", _WSBATCH, 16, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. Tested in "
        "the second, stricter pass over the batch file at "
        "[general/gl070.cbl:L460-L463], `if status-open or not waiting or not "
        "gl-batch / go to loop.`",
    ),
    _spec("PL-Batch", ("2",), _SINGLE, "WS-Ledger", _WSBATCH, 17, 1),
    _spec("SL-Batch", ("3",), _SINGLE, "WS-Ledger", _WSBATCH, 18, 2),
    _spec(
        "Status-Open", ("0",), _SINGLE, "Batch-Status", _WSBATCH, 26, 0,
        "Named in the Agent Action Plan section 0.3.1 example list, and the "
        "single most consequential condition name in the cycle. A batch left "
        "open is detected in the first pass at [general/gl070.cbl:L314-L315], "
        "which raises ws-term-code at [general/gl070.cbl:L289]; the menu tests "
        "that code at [general/general.cbl:L800-L814] and returns rather than "
        "continuing, so gl071 and gl072 never run at all. It is tested again "
        "in the second pass at [general/gl070.cbl:L460]. This module reports "
        "the condition; what to do about it belongs to the program modules.",
    ),
    _spec("Status-Closed", ("1",), _SINGLE, "Batch-Status", _WSBATCH, 27, 1),
    _spec(
        "Waiting", ("0",), _SINGLE, "Cleared-Status", _WSBATCH, 30, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. Appears "
        "ONLY in the second pass over the batch file, at "
        "[general/gl070.cbl:L461] - the first pass at "
        "[general/gl070.cbl:L312-L315] filters on the cycle and the open "
        "status alone. Section 0.6.4 is verbatim: \"Collapsing the two passes "
        "into one would change which batches are pre-processed.\"",
    ),
    _spec(
        "Processed", ("1",), _SINGLE, "Cleared-Status", _WSBATCH, 31, 1,
        "The value gl072 stamps at end of batch, written as a literal rather "
        "than through the condition name: `move 1 to cleared-status.` at "
        "[general/gl072.cbl:L375], immediately before "
        "`move run-date to posted.` at [general/gl072.cbl:L376] and the "
        "rewrite at [general/gl072.cbl:L377].",
    ),
    _spec("Archived", ("2",), _SINGLE, "Cleared-Status", _WSBATCH, 32, 2),
    _spec(
        "G-L", ("1",), _SINGLE, "Level-1", _WSSYSTEM, 85, 0,
        "The general ledger switch. Tested at three sites in "
        "sales/sl060.cbl - L1046, L1172 and L1177 - always as "
        "`IRS-Both-Used or G-L`, so it decides GL posting alongside the IRS "
        "fan-out rather than independently of it.",
    ),
    _spec("B-L", ("1",), _SINGLE, "Level-2", _WSSYSTEM, 87, 0),
    _spec("S-L", ("1",), _SINGLE, "Level-3", _WSSYSTEM, 89, 0),
    _spec(
        "Stock", ("1",), _SINGLE, "Level-4", _WSSYSTEM, 91, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not the out-of-scope "
        "table or bridge identifier a substring search would confuse it with. "
        "Agent Action Plan section 0.2.2 excludes those by their own exact "
        "names; this is none of them.",
    ),
    _spec(
        "IRS", ("1",), _SINGLE, "Level-5", _WSSYSTEM, 93, 0,
        'The trailing comment reads "IRS used (instead of General)."',
    ),
    _spec(
        "IRS-No", ("zero",), _FIG, "Level-5", _WSSYSTEM, 94, 1,
        "Figurative constant; reads as 0. The complement of its sibling on the "
        'same field, spelled out rather than tested as `not IRS`.',
    ),
    _spec("Payroll", ("1",), _SINGLE, "Level-6", _WSSYSTEM, 96, 0),
    _spec("Multi-User", ("1",), _SINGLE, "Host", _WSSYSTEM, 99, 0),
    _spec(
        "valid-os-type", ("1", "2", "3", "4", "5", "6"), _LIST,
        "Op-System", _WSSYSTEM, 101, 0,
        "A contiguous value list. Lower-case spelling kept as declared "
        "(rule R-5) - it is the only condition name in this copybook written "
        "entirely in lower case.",
    ),
    _spec(
        "No-OS", ("zero",), _FIG, "Op-System", _WSSYSTEM, 102, 1,
        "Figurative constant; reads as 0, and 0 is outside its sibling "
        "valid-os-type's range, so the two do not overlap.",
    ),
    _spec("Dos", ("1",), _SINGLE, "Op-System", _WSSYSTEM, 103, 2),
    _spec("Windows", ("2",), _SINGLE, "Op-System", _WSSYSTEM, 104, 3),
    _spec("Mac", ("3",), _SINGLE, "Op-System", _WSSYSTEM, 105, 4),
    _spec("Os2", ("4",), _SINGLE, "Op-System", _WSSYSTEM, 106, 5),
    _spec("Unix", ("5",), _SINGLE, "Op-System", _WSSYSTEM, 107, 6),
    _spec("Linux", ("6",), _SINGLE, "Op-System", _WSSYSTEM, 108, 7),
    _spec(
        "OS-Single", ("1", "2", "4"), _LIST, "Op-System", _WSSYSTEM, 109, 8,
        "A GAPPED value list: its members are 1, 2 and 4, and 3 is NOT one of "
        "them. It must never be collapsed into a 1-to-4 range - that would "
        "admit Mac, which the declaration excludes (rule R-4).",
    ),
    _spec(
        "FS-Cobol-Files-Used", ("zero",), _FIG,
        "File-System-Used", _WSSYSTEM, 113, 0,
        "Figurative constant; reads as 0.",
    ),
    _spec(
        "FS-MySql-Used", ("1",), _SINGLE, "File-System-Used", _WSSYSTEM, 114, 1,
        "SHARES ITS VALUE WITH A SIBLING: FS-RDBMS-Used at "
        "[copybooks/wssystem.cob:L116] is also declared `value 1` on this same "
        "field, so each of the two holds exactly when the other does. Both are "
        "registered as declared (rule R-4).",
    ),
    _spec(
        "FS-RDBMS-Used", ("1",), _SINGLE, "File-System-Used", _WSSYSTEM, 116, 2,
        "SHARES ITS VALUE WITH A SIBLING: FS-MySql-Used at "
        '[copybooks/wssystem.cob:L114]. The trailing comment reads "Was '
        'generic". Declared at L116, not L115: L115 carries the heading '
        '"THESE NOT IN USE at this time" in the comment area.',
    ),
    _spec(
        "FS-Valid-Options", ("0", "1"), _THRU,
        "File-System-Used", _WSSYSTEM, 122, 3,
        "A thru range, INCLUSIVE on both bounds: 0 holds, 1 holds, 2 does not. "
        'The trailing comment reads "5. (not in use unless 1-5)", recording a '
        "wider intent the declaration does not carry.",
    ),
    _spec(
        "FS-Duplicate-Processing", ("1",), _SINGLE,
        "File-Duplicates-In-Use", _WSSYSTEM, 124, 0,
        'The field\'s comment reads "No longer in use" and this row\'s reads '
        '"Ditto".',
    ),
    # 05 Date-Form pic 9. [copybooks/wssystem.cob:L128] Three specific formats and one
    # collective name. The collective name is never tested, and neither is the third
    # specific one.
    _spec(
        "Date-UK", ("1",), _SINGLE, "Date-Form", _WSSYSTEM, 129, 0,
        'Tested at [general/gl070.cbl:L585]. Trailing comment: "dd/mm/yyyy".',
    ),
    _spec(
        "Date-USA", ("2",), _SINGLE, "Date-Form", _WSSYSTEM, 130, 1,
        "Tested at [general/gl070.cbl:L587], where the wrapper swaps the day "
        'and month components. Trailing comment: "mm/dd/yyyy".',
    ),
    _spec(
        "Date-Intl", ("3",), _SINGLE, "Date-Form", _WSSYSTEM, 131, 2,
        "NEVER TESTED BY THE MIGRATED CYCLE. The date wrapper sections test "
        "Date-UK and Date-USA and then FALL THROUGH to the international form "
        "without naming it - the comment at [general/gl070.cbl:L591] reads "
        '"So its International date format". Searching general/gl070.cbl, '
        "general/gl072.cbl, sales/sl060.cbl and irs/irs030.cbl for this name "
        "returns zero occurrences. Registered for traceability; the migrated "
        'code must not start using a test the COBOL ignores. Trailing '
        'comment: "yyyy/mm/dd".',
    ),
    _spec(
        "Date-Valid-Formats", ("1", "2", "3"), _LIST,
        "Date-Form", _WSSYSTEM, 132, 3,
        "DECLARED AND NEVER TESTED - the anomaly this file is required to "
        "keep. The date wrapper sections do not use it: they test the "
        "conditional variable against a figurative constant and default it "
        "instead, at [general/gl070.cbl:L583-L584], `if Date-Form = zero / "
        "move 1 to Date-Form.` Searching the four in-scope programs "
        "general/gl070.cbl, general/gl072.cbl, sales/sl060.cbl and "
        "irs/irs030.cbl for this name returns zero occurrences. The folder "
        "requirement is verbatim: \"Model the predicate for traceability, but "
        "do not make the code use a test the COBOL ignores.\" So the row and "
        "its predicate exist, and nothing in the migration calls the "
        "predicate. Declared at [copybooks/wssystem.cob:L132] (rule R-4).",
    ),
    _spec(
        "DC-Cobol-Standard", ("zero",), _FIG,
        "Data-Capture-Used", _WSSYSTEM, 134, 0,
        "Figurative constant; reads as 0.",
    ),
    _spec("DC-GUI", ("1",), _SINGLE, "Data-Capture-Used", _WSSYSTEM, 135, 1),
    _spec("DC-Widget", ("2",), _SINGLE, "Data-Capture-Used", _WSSYSTEM, 136, 2),
    # 03 General-Ledger-Block. [copybooks/wssystem.cob:L150] From here to L272 every
    # conditional variable is `pic x`, one character wide, and every condition name is a
    # quoted literal.
    _spec(
        "Profit-Centres", ('"P"',), _ALNUM, "P-C", _WSSYSTEM, 152, 0,
        "Quoted literal, delimiters kept in the recorded value so a "
        "one-character switch is unambiguous.",
    ),
    _spec("Branches", ('"B"',), _ALNUM, "P-C", _WSSYSTEM, 153, 1),
    _spec("Grouped", ('"Y"',), _ALNUM, "P-C-Grouped", _WSSYSTEM, 155, 0),
    _spec("Revenue-Only", ('"R"',), _ALNUM, "P-C-Level", _WSSYSTEM, 157, 0),
    _spec("Comparatives", ('"Y"',), _ALNUM, "Comps", _WSSYSTEM, 159, 0),
    _spec(
        "Comparatives-Active", ('"Y"',), _ALNUM,
        "Comps-Active", _WSSYSTEM, 161, 0,
    ),
    _spec("Minimum-Validation", ('"Y"',), _ALNUM, "M-V", _WSSYSTEM, 163, 0),
    _spec("Archiving", ('"Y"',), _ALNUM, "Arch", _WSSYSTEM, 165, 0),
    _spec("Mandatory", ('"Y"',), _ALNUM, "Trans-Print", _WSSYSTEM, 167, 0),
    _spec("Trans-Done", ('"Y"',), _ALNUM, "Trans-Printed", _WSSYSTEM, 169, 0),
    _spec(
        "Auto-Vat", ('"Y"',), _ALNUM, "Vat", _WSSYSTEM, 174, 0,
        "The alphanumeric exemplar the folder's own shape table cites. The "
        "comparison is case-SENSITIVE, so \"y\" does not hold; see the "
        "question `evaluate` records about that.",
    ),
    _spec("Preserve-Batch", ('"Y"',), _ALNUM, "Batch-Id", _WSSYSTEM, 176, 0),
    _spec(
        "Index-2", ('"Y"',), _ALNUM, "Ledger-2nd-Index", _WSSYSTEM, 178, 0,
        "The field's own comment at [copybooks/wssystem.cob:L177] reads "
        '"But file uses SINGLE INDEX only & gl030 uses a table."',
    ),
    # 05 IRS-Instead pic x. [copybooks/wssystem.cob:L179] THE IRS FAN-OUT: a THREE-state
    # switch with only TWO condition names.
    _spec(
        "IRS-Used", ('"Y"',), _ALNUM, "IRS-Instead", _WSSYSTEM, 180, 0,
        "Named in the Agent Action Plan section 0.3.1 example list. One of the "
        "two names on a THREE-state switch whose third state, space, has no "
        "name of its own - for space both this and IRS-Both-Used are False. "
        "The switch decides WHICH TABLES A RUN TOUCHES, so it is a "
        "database-state matter: sales/sl060.cbl tests the pair at seven sites "
        "- L1039, L1046, L1126, L1144, L1172, L1175 and L1177 - of which "
        "L1039, L1126 and L1175 use the `IRS-Used OR IRS-Both-Used` shape. "
        "Section 0.6.4 requires a scenario to pin the switch explicitly, "
        "because a default would make the affected-table list ambiguous.",
    ),
    _spec(
        "IRS-Both-Used", ('"B"',), _ALNUM, "IRS-Instead", _WSSYSTEM, 181, 1,
        "The \"IRS as well as\" state; trailing comment \"26/11/16\". The "
        "second of two names on a three-state switch - for space both are "
        "False, and for \"Y\" this one is False. Tested at all seven "
        "sales/sl060.cbl sites, three of them - L1046, L1172 and L1177 - as "
        "`IRS-Both-Used or G-L`, and L1144 on its own. The site at "
        "[sales/sl060.cbl:L1172-L1178] is where anomaly A-1 lives: L1175's `if` "
        "carries no terminating period until L1178, so L1177's GL posting "
        "close is NESTED inside it and never runs in pure-GL mode. That "
        "anomaly belongs to the program module; this row only records the "
        "value set.",
    ),
    _spec(
        "P-L-Exists", ('"Y"',), _ALNUM, "Purchase-Ledger", _WSSYSTEM, 201, 0,
    ),
    _spec("S-L-Exists", ('"Y"',), _ALNUM, "Sales-Ledger", _WSSYSTEM, 217, 0),
    _spec(
        "I-Level-0", ("0",), _SINGLE, "invoicer", _WSSYSTEM, 233, 0,
        'Trailing comment: "show totals only (no net & vat) not used?"',
    ),
    _spec(
        "I-Level-1", ("1",), _SINGLE, "invoicer", _WSSYSTEM, 234, 1,
        'Trailing comment: "Show net, vat".',
    ),
    _spec(
        "I-Level-2", ("2",), _SINGLE, "invoicer", _WSSYSTEM, 235, 2,
        'Trailing comment: "show Details + vat etc looks wrong in sl910 '
        'totals only (no net & vat)".',
    ),
    _spec(
        "Not-Invoicing", ("9",), _SINGLE, "invoicer", _WSSYSTEM, 236, 3,
        "Value 9 leaves 3 to 8 satisfying no condition name on this field, "
        "which is not an error - it is simply False everywhere. The trailing "
        'comment reads "show totals only (no net & vat) but not found yet nor '
        'level 3 (see sl900)".',
    ),
    _spec("Discount", ('"D"',), _ALNUM, "Extra-Type", _WSSYSTEM, 239, 0),
    _spec("Charge", ('"C"',), _ALNUM, "Extra-Type", _WSSYSTEM, 240, 1),
    _spec(
        "Stock-Audit-On", ('"Y"',), _ALNUM,
        "SL-Stock-Audit", _WSSYSTEM, 244, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes. "
        'Trailing comment: "Invoicing will create an audit record '
        '(15/05/13)".',
    ),
    _spec(
        "SL-Comp-Pick", ('"Y"',), _ALNUM,
        "SL-Comp-Head-Pick", _WSSYSTEM, 264, 0,
        "Its conditional variable is declared `Pic x` with a capital P at "
        "[copybooks/wssystem.cob:L263], the only such spelling in the "
        "copybook.",
    ),
    _spec(
        "SL-Comp-Inv", ('"Y"',), _ALNUM, "SL-Comp-Head-Inv", _WSSYSTEM, 266, 0,
    ),
    _spec(
        "SL-Comp-Stat", ('"Y"',), _ALNUM,
        "SL-Comp-Head-Stat", _WSSYSTEM, 268, 0,
    ),
    _spec(
        "SL-Comp-Lets", ('"Y"',), _ALNUM,
        "SL-Comp-Head-Lets", _WSSYSTEM, 270, 0,
    ),
    _spec(
        "SL-VAT-Prints", ('"Y"',), _ALNUM, "SL-VAT-Printed", _WSSYSTEM, 272, 0,
    ),
    _spec(
        "Stock-Control-Exists", ('"Y"',), _ALNUM,
        "Stock-Control", _WSSYSTEM, 301, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes.",
    ),
    _spec(
        "Stock-Averaging", ("1",), _SINGLE,
        "Stk-Averaging", _WSSYSTEM, 303, 0,
        "A LEGITIMATE in-scope SYSTEM-REC condition name, not one of the "
        "out-of-scope identifiers Agent Action Plan section 0.2.2 excludes. "
        "Note the name says Stock while its conditional variable says Stk.",
    ),
    # copybooks/wssl.cob - 8 rows. Agent Action Plan section 0.4.1.4 names three source
    # copybooks for this file and this is not one of them.
    _spec("Customer-Live", ("1",), _SINGLE, "Sales-Status", _WSSL, 26, 0),
    _spec(
        "Customer-Dead", ("zero",), _FIG, "Sales-Status", _WSSL, 27, 1,
        "Figurative constant; reads as 0. Worth comparing with "
        "[copybooks/wsbatch.cob:L26], which writes `value 0` for the same "
        "idea: the two spellings behave identically and both stay recorded as "
        "written (rule R-4).",
    ),
    _spec("Late-Charges", ("1",), _SINGLE, "Sales-Late", _WSSL, 29, 0),
    _spec(
        "Dunning-Letters", ("1",), _SINGLE, "Sales-Dunning", _WSSL, 31, 0,
        'The field\'s trailing comment reads "Reminder letters".',
    ),
    _spec("Email-Invoicing", ("1",), _SINGLE, "Email-Invoice", _WSSL, 33, 0),
    _spec(
        "Email-Statementing", ("1",), _SINGLE, "Email-Statement", _WSSL, 35, 0,
    ),
    _spec(
        "Email-Dunning", ("1",), _SINGLE, "Email-Letters", _WSSL, 37, 0,
        "The name and its conditional variable disagree about the subject - "
        "Email-Letters carries Email-Dunning - which is left as declared "
        "(rule R-4).",
    ),
    _spec(
        "Sales-BO-Set", ('"Y"',), _ALNUM,
        "Sales-Partial-Ship-Flag", _WSSL, 67, 0,
        "The row the plan names explicitly. Its conditional variable is "
        "declared across TWO physical lines, [copybooks/wssl.cob:L65-L66], "
        "with this `88` on the third. Added into filler with no change to the "
        "300-byte record size per [copybooks/wssl.cob:L9-L10]; trailing "
        'comment "added 17/03/24".',
    ),
    _spec("Supplier-live", ("1",), _SINGLE, "Purch-Status", _WSPL, 19, 0),
    _spec(
        "Supplier-dead", ("0",), _SINGLE, "Purch-Status", _WSPL, 20, 1,
        "Written as the DIGIT 0, where the sales mirror `Customer-Dead` at "
        "[copybooks/wssl.cob:L27] writes the figurative `zero` for the same "
        "idea. The two behave identically and both stay recorded as written "
        "(rule R-4). LIVE at [purchase/pl060.cbl:L503].",
    ),
    # copybooks/slwsinv.cob - 12 rows. The sales invoice header and lines.
    _spec("Sih-Yearly", ('"Y"',), _ALNUM, "sih-Freq", _SLWSINV, 30, 0),
    _spec("Sih-Monthly", ('"M"',), _ALNUM, "sih-Freq", _SLWSINV, 31, 1),
    _spec("Sih-Quarterly", ('"Q"',), _ALNUM, "sih-Freq", _SLWSINV, 32, 2),
    _spec(
        "sih-Daily", ('"D"',), _ALNUM, "sih-Freq", _SLWSINV, 33, 3,
        'SHARES the value "D" with `sih-Testing` on the next line, so both '
        "hold for the same character and neither can be told from the other by "
        "its value. The maintainer's own trailing comments say so: \"These two "
        'are only for testing." and "So NOT documented and removed after '
        'tests." Reproduced as declared (rule R-4). Note also the '
        "capitalisation change mid-group - the first three names are `Sih-` "
        "and this one is `sih-`.",
    ),
    _spec(
        "sih-Testing", ('"D"',), _ALNUM, "sih-Freq", _SLWSINV, 34, 4,
        'The second of the two "D" declarations; see `sih-Daily` above.',
    ),
    _spec(
        "sih-Valid-Freqs", ('"Y"', '"M"', '"Q"', '"D"'), _ALIST,
        "sih-Freq", _SLWSINV, 35, 5,
        "The only four-literal shape in the registry, alongside its two "
        "purchase and second-sales counterparts. It INCLUDES the testing-only "
        '"D", which the maintainer\'s trailing comment flags: "Last one D, for '
        'TESTING ONLY so remove after". So a frequency of "D" is both a '
        "testing artefact and a valid frequency, and the registry keeps that "
        "as it stands.",
    ),
    _spec(
        "pending", ('"P"', '"p"'), _ALIST, "sih-status", _SLWSINV, 53, 0,
        "One of FOUR declarations of this name. Upper case FIRST here and at "
        "[copybooks/plwspinv.cob:L41]; lower case first at "
        "[copybooks/plwspinv2.cob:L41]; and a SINGLE upper-case literal at "
        "[copybooks/slwsinv2.cob:L72], which therefore does NOT hold for a "
        "lower-case \"p\". The four are never collapsed - see "
        "`DUPLICATED_COBOL_NAMES`. LIVE at [sales/sl055.cbl:L433].",
    ),
    _spec(
        "invoiced", ('"I"', '"i"'), _ALIST, "sih-status", _SLWSINV, 54, 1,
        "One of four declarations; the case order and the literal count differ "
        "between them exactly as `pending`'s do.",
    ),
    _spec(
        "sapplied", ('"Z"', '"z"'), _ALIST, "sih-status", _SLWSINV, 55, 2,
        "Spelled `sapplied` HERE ALONE. The same status flag is `applied` in "
        "[copybooks/slwsinv2.cob:L74], [copybooks/plwspinv.cob:L43] and "
        "[copybooks/plwspinv2.cob:L43], and it is `applied` that "
        "[sales/sl055.cbl:L427] tests. The leading `s` is left exactly as "
        "declared (rule R-4), which means a caller reaching for `applied` in "
        "this copybook will not find it - and should not, because the frozen "
        "line does not declare it here.",
    ),
    _spec(
        "day-booked", ('"B"', '"b"'), _ALIST,
        "sih-day-book-flag", _SLWSINV, 68, 0,
        "Its conditional variable is initialised to `space`, for which this "
        "condition name is False - the flag's unset state has no name of its "
        "own, exactly as the IRS fan-out's third state has none "
        "[copybooks/wssystem.cob:L179-L181].",
    ),
    _spec(
        "sih-analyised", ('"Z"', '"z"'), _ALIST, "sih-update", _SLWSINV, 70, 0,
        "The maintainer's own spelling of \"analysed\", kept (rule R-5).",
    ),
    _spec(
        "sil-analyised", ('"Z"',), _ALNUM, "sil-update", _SLWSINV, 96, 0,
        "ONE literal, where the three sibling `il-analyised` declarations at "
        "[copybooks/slwsinv2.cob:L105], [copybooks/plwspinv.cob:L83] and "
        "[copybooks/plwspinv2.cob:L72] each list two. This one therefore does "
        'NOT hold for a lower-case "z". Also spelled `sil-` here where the '
        "other three are `il-`, so it is the one line-level analysis flag that "
        "does not collide with its siblings.",
    ),
    _spec("ih-Yearly", ('"Y"',), _ALNUM, "ih-Freq", _SLWSINV2, 49, 0),
    _spec("ih-Monthly", ('"M"',), _ALNUM, "ih-Freq", _SLWSINV2, 50, 1),
    _spec("ih-Quarterly", ('"Q"',), _ALNUM, "ih-Freq", _SLWSINV2, 51, 2),
    _spec(
        "ih-Daily", ('"D"',), _ALNUM, "ih-Freq", _SLWSINV2, 52, 3,
        'SHARES the value "D" with `ih-Testing` on the next line, with the '
        "maintainer's testing-only comments. The same pair recurs at "
        "[copybooks/plwspinv.cob:L22-L23].",
    ),
    _spec(
        "ih-Testing", ('"D"',), _ALNUM, "ih-Freq", _SLWSINV2, 53, 4,
        'The second of the two "D" declarations; see `ih-Daily` above.',
    ),
    _spec(
        "ih-Valid-Freqs", ('"Y"', '"M"', '"Q"', '"D"'), _ALIST,
        "ih-Freq", _SLWSINV2, 54, 5,
        'Includes the testing-only "D", per the maintainer\'s trailing '
        'comment "Last one D, for TESTING ONLY so remove after".',
    ),
    _spec(
        "pending", ('"P"',), _ALNUM, "ih-status", _SLWSINV2, 72, 0,
        "A SINGLE literal, where the three sibling `pending` declarations each "
        'list two. This one is case-SENSITIVE: a lower-case "p" satisfies '
        "[copybooks/slwsinv.cob:L53] and [copybooks/plwspinv.cob:L41] but NOT "
        "this line. The difference is the frozen source's and is preserved "
        "(rule R-4). LIVE at [sales/sl055.cbl:L433].",
    ),
    _spec(
        "invoiced", ('"I"',), _ALNUM, "ih-status", _SLWSINV2, 73, 1,
        "A single literal; see `pending` above for the divergence.",
    ),
    _spec(
        "applied", ('"Z"',), _ALNUM, "ih-status", _SLWSINV2, 74, 2,
        "A single literal. The sales mirror of this flag in "
        "[copybooks/slwsinv.cob:L55] is spelled `sapplied` and lists two "
        "literals, so the two sales invoice copybooks agree on neither the "
        "name nor the value set. LIVE at [sales/sl055.cbl:L427].",
    ),
    _spec(
        "day-booked", ('"B"',), _ALNUM,
        "ih-day-book-flag", _SLWSINV2, 87, 0,
        "A single literal, and its conditional variable carries NO `value "
        "space` initialisation where [copybooks/slwsinv.cob:L67] and "
        "[copybooks/plwspinv.cob:L51] both do.",
    ),
    _spec(
        "ih-analyised", ('"Z"',), _ALNUM, "ih-update", _SLWSINV2, 89, 0,
        "A single literal. LIVE at [sales/sl055.cbl:L427] and "
        "[sales/sl055.cbl:L440].",
    ),
    _spec(
        "il-analyised", ('"Z"',), _ALNUM, "il-update", _SLWSINV2, 105, 0,
        "A single literal. LIVE at [sales/sl055.cbl:L373].",
    ),
    _spec(
        "S-Open", ("zero",), _FIG, "OI-Status", _SLWSOI, 48, 0,
        "Figurative constant; reads as 0. Declared identically at "
        "[copybooks/plwsoi.cob:L54] on a same-named carrier, which is why the "
        "two are told apart by locator rather than by name.",
    ),
    _spec(
        "S-Closed", ("1",), _SINGLE, "OI-Status", _SLWSOI, 49, 1,
        'Trailing comment "Paid". LIVE at [sales/sl060.cbl:L668], '
        "[sales/sl060.cbl:L877] and [sales/sl100.cbl:L350], reached through "
        "the nested COPY at [copybooks/slwsoi3.cob:L18]. Declared again at "
        "[copybooks/plwsoi.cob:L55] with the same value, and that one is LIVE "
        "in the purchase programs.",
    ),
    _spec("ih-Yearly", ('"Y"',), _ALNUM, "ih-Freq", _PLWSPINV, 19, 0),
    _spec("ih-Monthly", ('"M"',), _ALNUM, "ih-Freq", _PLWSPINV, 20, 1),
    _spec("ih-Quarterly", ('"Q"',), _ALNUM, "ih-Freq", _PLWSPINV, 21, 2),
    _spec(
        "ih-Daily", ('"D"',), _ALNUM, "ih-Freq", _PLWSPINV, 22, 3,
        'SHARES the value "D" with `ih-Testing` on the next line, with the '
        "maintainer's testing-only comments, exactly as "
        "[copybooks/slwsinv2.cob:L52-L53] does.",
    ),
    _spec(
        "ih-Testing", ('"D"',), _ALNUM, "ih-Freq", _PLWSPINV, 23, 4,
        'The second of the two "D" declarations; see `ih-Daily` above.',
    ),
    _spec(
        "ih-Valid-Freqs", ('"Y"', '"M"', '"Q"', '"D"'), _ALIST,
        "ih-Freq", _PLWSPINV, 24, 5,
        'Includes the testing-only "D". The maintainer\'s trailing comment '
        'here reads "LAst one for TESTING ONLY so remove after" - the '
        "transposed capitals and the missing \"D,\" are his, and the comment "
        "is not data, so only the value clause is transcribed.",
    ),
    _spec(
        "pending", ('"P"', '"p"'), _ALIST, "ih-status", _PLWSPINV, 41, 0,
        "Two literals, upper case first - the same clause as "
        "[copybooks/slwsinv.cob:L53], and the reverse case order of "
        "[copybooks/plwspinv2.cob:L41].",
    ),
    _spec(
        "invoiced", ('"I"', '"i"'), _ALIST, "ih-status", _PLWSPINV, 42, 1,
        "Two literals, upper case first.",
    ),
    _spec(
        "applied", ('"Z"', '"z"'), _ALIST, "ih-status", _PLWSPINV, 43, 2,
        "Two literals, upper case first. LIVE at [purchase/pl055.cbl:L365].",
    ),
    _spec(
        "day-booked", ('"B"', '"b"'), _ALIST,
        "ih-day-book-flag", _PLWSPINV, 51, 0,
        "The frozen line carries a space before its full stop - "
        '`values "B" "b" .` - which is whitespace to the compiler and is not '
        "part of the clause, so the tokens are transcribed without it.",
    ),
    _spec(
        "ih-analyised", ('"Z"', '"z"'), _ALIST,
        "ih-update", _PLWSPINV, 53, 0,
        "Two literals, upper case first. LIVE at [purchase/pl055.cbl:L365] "
        "and [purchase/pl055.cbl:L370].",
    ),
    _spec(
        "il-analyised", ('"z"', '"Z"'), _ALIST,
        "il-update", _PLWSPINV, 83, 0,
        "LOWER case first, unlike every other clause in this copybook, with "
        'the maintainer\'s own trailing comment "using Z hopefully" recording '
        "his uncertainty about which case the data carries. Reproduced as "
        "declared (rule R-4). LIVE at [purchase/pl055.cbl:L314].",
    ),
    _spec(
        "pending", ('"p"', '"P"'), _ALIST, "ih-status", _PLWSPINV2, 41, 0,
        "LOWER case first, the reverse of [copybooks/plwspinv.cob:L41] and "
        "[copybooks/slwsinv.cob:L53]. Which values match is unaffected; the "
        "ORDER is the frozen source's and rule R-4 keeps it.",
    ),
    _spec(
        "invoiced", ('"i"', '"I"'), _ALIST, "ih-status", _PLWSPINV2, 42, 1,
        "Lower case first.",
    ),
    _spec(
        "applied", ('"z"', '"Z"'), _ALIST, "ih-status", _PLWSPINV2, 43, 2,
        "Lower case first.",
    ),
    _spec(
        "day-booked", ('"b"', '"B"'), _ALIST,
        "ih-day-book-flag", _PLWSPINV2, 51, 0,
        "Lower case first, and no `value space` initialisation on the carrier.",
    ),
    _spec(
        "ih-analyised", ('"z"', '"Z"'), _ALIST,
        "ih-update", _PLWSPINV2, 53, 0, "Lower case first.",
    ),
    _spec(
        "il-analyised", ('"z"', '"Z"'), _ALIST,
        "il-update", _PLWSPINV2, 72, 0,
        "Lower case first - agreeing with [copybooks/plwspinv.cob:L83], which "
        "is the one clause in THAT copybook to do so.",
    ),
    _spec(
        "payment-held", ('"H"',), _ALNUM, "OI-hold-flag", _PLWSOI, 39, 0,
        "The purchase side's payment hold. It has no sales counterpart: "
        "copybooks/slwsoi.cob declares no hold flag at all.",
    ),
    _spec(
        "S-Open", ("zero",), _FIG, "OI-Status", _PLWSOI, 54, 0,
        "Figurative constant; reads as 0. The same name, carrier and value as "
        "[copybooks/slwsoi.cob:L48], which is why identity here is the "
        "declaration rather than the name.",
    ),
    _spec(
        "S-Closed", ("1",), _SINGLE, "OI-Status", _PLWSOI, 55, 1,
        "LIVE at [purchase/pl060.cbl:L594], [purchase/pl060.cbl:L799] and "
        "[purchase/pl100.cbl:L342] - the last reached through the nested COPY "
        "at [copybooks/plwsoi5C.cob:L19]. Its sales twin at "
        "[copybooks/slwsoi.cob:L49] carries the trailing comment \"Paid\"; "
        "this line carries none.",
    ),
    _spec(
        "Owner", ('"O"',), _ALNUM, "NL-Type", _IRSWSNL, 13, 0,
        "Declared `value is \"O\"`. The optional `IS` is noise words to the "
        "compiler and carries no meaning, so `value_clause_text` renders "
        "`\"O\"` and matches the generated dictionary, which records the "
        "clause the same way. LIVE at [common/acasirsub1.cbl:L577] and "
        "[common/acasirsub1.cbl:L616].",
    ),
    _spec(
        "Sub", ('"S"',), _ALNUM, "NL-Type", _IRSWSNL, 14, 1,
        "Declared `value is \"S\"`. LIVE at [common/acasirsub1.cbl:L414] and "
        "[common/acasirsub1.cbl:L506]. Its three-letter name is a substring of "
        "many identifiers, `WS-Sub-Function` among them, so a search for it "
        "needs word boundaries - which is why the liveness check that found "
        "these call sites used them.",
    ),
    _spec(
        "Testing-1", ("1",), _SINGLE, "SW-Testing", _TESTFLAGS, 11, 0,
        "Its conditional variable is initialised to 1 in the FROZEN copybook, "
        "with the maintainer's own alternative `zero` sitting beside it as a "
        "trailing comment, so file-handler logging is ON by default and cannot "
        "be turned off without editing a frozen file. That is a reproduced "
        "condition, not a defect to repair (rule R-4): the header at "
        "[copybooks/Test-Data-Flags.cob:L3-L4] says to set it to zero when "
        "testing is complete, and it was not. LIVE in every handler, e.g. "
        "[common/acas000.cbl:L495] and [common/acas000.cbl:L546].",
    ),
    _spec(
        "Testing-2", ("1",), _SINGLE, "SW-Testing-2", _TESTFLAGS, 16, 0,
        "The second switch, whose carrier IS initialised to zero, so this one "
        "is off by default - the asymmetry with `SW-Testing` is the frozen "
        "source's. The copybook's comment at "
        "[copybooks/Test-Data-Flags.cob:L13] describes it as for displays of "
        "`ws-where` and similar.",
    ),
)


def _copybook_stem(copybook: str) -> str:
    """The identifier-safe stem of a copybook path, for disambiguating a name.

    `copybooks/slwsinv2.cob` yields `slwsinv2` and `copybooks/Test-Data-Flags.cob`
    yields `test_data_flags`, so a predicate name built from it is a valid Python
    identifier in lower case, matching the `is_<name>` convention the rest of the module
    uses.

    Args:
        copybook: The copybook's repository-relative path.

    Returns:
        Its file stem, folded and with every non-alphanumeric character turned into an
            underscore.
    """
    stem = copybook.rsplit("/", 1)[-1]
    if stem.endswith(".cob"):
        stem = stem[: -len(".cob")]
    return "".join(
        character if character.isalnum() else "_" for character in stem
    ).casefold()


def _with_predicate_names(
    rows: tuple[ConditionNameSpec, ...],
) -> tuple[ConditionNameSpec, ...]:
    """Fill in each row's `predicate_name`, guaranteeing uniqueness.

    Uniqueness is a property of the whole registry, so it cannot be settled row by row
    inside `_spec`. This makes one pass to count how often each FOLDED COBOL name occurs
    and a second to name the rows.

    Args:
        rows: The registry rows, in registry order, with `predicate_name` empty.

    Returns:
        The same rows in the same order, each carrying a unique `predicate_name`.
    """
    occurrences: dict[str, int] = dict()
    for row in rows:
        folded = row.cobol_name.casefold()
        occurrences[folded] = occurrences.get(folded, 0) + 1
    return tuple(
        dataclasses.replace(
            row,
            predicate_name=(
                row.python_name
                if occurrences[row.cobol_name.casefold()] == 1
                else row.python_name + "_" + _copybook_stem(row.copybook)
            ),
        )
        for row in rows
    )


CONDITION_NAMES: Final[tuple[ConditionNameSpec, ...]] = _with_predicate_names(
    _REGISTRY_ROWS
)


# Every declaration of a name, keyed by the EXACT COBOL spelling. THE PRIMARY INDEX,
# because a name does not identify a declaration.
SPECS_BY_COBOL_NAME: Final[Mapping[str, tuple[ConditionNameSpec, ...]]] = (
    types.MappingProxyType(
        {
            name: tuple(
                spec for spec in CONDITION_NAMES if spec.cobol_name == name
            )
            for name in dict.fromkeys(
                spec.cobol_name for spec in CONDITION_NAMES
            )
        }
    )
)

# The names declared MORE THAN ONCE, each against its declarations, in registry order.
DUPLICATED_COBOL_NAMES: Final[Mapping[str, tuple[ConditionNameSpec, ...]]] = (
    types.MappingProxyType(
        {
            name: specs
            for name, specs in SPECS_BY_COBOL_NAME.items()
            if len(specs) > 1
        }
    )
)

# Keyed by the EXACT COBOL spelling for the names declared EXACTLY ONCE, so a name
# copied out of a copybook finds its row when - and only when - that row is the
# unambiguous answer.
BY_COBOL_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {
        name: specs[0]
        for name, specs in SPECS_BY_COBOL_NAME.items()
        if len(specs) == 1
    }
)

BY_PYTHON_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.python_name: spec for spec in BY_COBOL_NAME.values()}
)

# EVERY row keyed by its locator, which is unique across all 159 - one `88` per line.
BY_LOCATOR: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {spec.locator: spec for spec in CONDITION_NAMES}
)

# A case-insensitive index over the unambiguous names, private because the PUBLISHED key
# is the exact spelling.
_BY_FOLDED_NAME: Final[Mapping[str, ConditionNameSpec]] = types.MappingProxyType(
    {
        spec.cobol_name.casefold(): spec
        for spec in BY_COBOL_NAME.values()
    }
)

# Every declaration keyed by its FOLDED name, so a case-insensitive lookup of an
# ambiguous name can report all of its locators rather than merely failing.
_SPECS_BY_FOLDED_NAME: Final[Mapping[str, tuple[ConditionNameSpec, ...]]] = (
    types.MappingProxyType(
        {
            folded: tuple(
                spec
                for spec in CONDITION_NAMES
                if spec.cobol_name.casefold() == folded
            )
            for folded in dict.fromkeys(
                spec.cobol_name.casefold() for spec in CONDITION_NAMES
            )
        }
    )
)

# The per-copybook composition, published as data so the count can be checked rather
# than trusted.
COUNTS_BY_COPYBOOK: Final[Mapping[str, int]] = types.MappingProxyType(
    {
        copybook: sum(
            1 for spec in CONDITION_NAMES if spec.copybook == copybook
        )
        for copybook in dict.fromkeys(spec.copybook for spec in CONDITION_NAMES)
    }
)

# The number of condition names declared on `Fs-Reply`, read from the frozen file.
FS_REPLY_CONDITION_NAME_COUNT: Final[int] = 0


def specs_for_name(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> tuple[ConditionNameSpec, ...]:
    """Every declaration of one condition name, narrowed by copybook or carrier.

    Matching on the name is case-INSENSITIVE, because COBOL is: a caller reading
    `status-open` out of [general/gl070.cbl:L314] finds `Status-Open` as declared at
    [copybooks/wsbatch.cob:L26]. The two narrowing arguments match the same way, so
    `conditional_variable="IH-STATUS"` finds `ih-status`.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook's repository-relative path, in any
            casing - `"copybooks/slwsinv2.cob"`.
        conditional_variable: Optionally, the owning field's COBOL name, in any casing -
            `"sih-status"`.

    Returns:
        The matching declarations in registry order, or an empty tuple.
    """
    probe = cobol_name.casefold()
    matches = _SPECS_BY_FOLDED_NAME.get(probe, ())
    if copybook is not None:
        wanted_file = copybook.casefold()
        matches = tuple(
            spec for spec in matches if spec.copybook.casefold() == wanted_file
        )
    if conditional_variable is not None:
        wanted_carrier = conditional_variable.casefold()
        matches = tuple(
            spec
            for spec in matches
            if spec.conditional_variable.casefold() == wanted_carrier
        )
    return matches


def lookup(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> ConditionNameSpec:
    """Find ONE row by its COBOL condition name, unambiguously.

    The exact spelling is tried first, then a case-insensitive match, because COBOL is
    case-insensitive about names and a caller reading [general/gl070.cbl:L314] finds
    `status-open` in lower case while [copybooks/wsbatch.cob:L26] declares `Status-
    Open`. Both reach the same row.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook's repository-relative path, to pick
            between declarations of one name.
        conditional_variable: Optionally, the owning field's COBOL name, for the same
            purpose.

    Returns:
        Its row.

    Raises:
        KeyError: No row of that name, or several and no way to tell which was meant.
    """
    if copybook is None and conditional_variable is None:
        found = BY_COBOL_NAME.get(cobol_name)
        if found is not None:
            return found
        folded = _BY_FOLDED_NAME.get(cobol_name.casefold())
        if folded is not None:
            return folded

    matches = specs_for_name(
        cobol_name,
        copybook=copybook,
        conditional_variable=conditional_variable,
    )
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise KeyError(
            _unknown_name_message(
                cobol_name,
                copybook=copybook,
                conditional_variable=conditional_variable,
            )
        )
    raise KeyError(_ambiguous_name_message(cobol_name, matches))


def find(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> ConditionNameSpec | None:
    """Find one row by its COBOL condition name, or None.

    An AMBIGUOUS name returns None rather than a guess, for the same reason `lookup`
    raises: there is no single row to return. Use `specs_for_name` to see all of them,
    or `is_declared` to ask only whether the name exists.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook's repository-relative path.
        conditional_variable: Optionally, the owning field's COBOL name.

    Returns:
        Its row, or None when the registry declares no such name or declares several and
            none was singled out.
    """
    if copybook is None and conditional_variable is None:
        found = BY_COBOL_NAME.get(cobol_name)
        if found is not None:
            return found
    matches = specs_for_name(
        cobol_name,
        copybook=copybook,
        conditional_variable=conditional_variable,
    )
    return matches[0] if len(matches) == 1 else None


def is_declared(cobol_name: str) -> bool:
    """Whether the frozen copybooks declare a condition name of this name at all.

    The pure existence probe, which `find` cannot serve because `find` returns None for
    an ambiguous name that certainly does exist. A traceability report harvesting names
    from program source wants this question, not `find`'s.

    Args:
        cobol_name: The condition name, in any casing.

    Returns:
        True when at least one declaration carries that name.
    """
    return bool(_SPECS_BY_FOLDED_NAME.get(cobol_name.casefold(), ()))


def _unknown_name_message(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> str:
    """Explain an unknown condition name and offer the nearest spellings.

    Near misses are found by a plain substring test rather than an edit distance, which
    is enough to catch the realistic mistakes - a wrong prefix (`FS-` for `FA-FS-`), a
    wrong separator, a partial name - and keeps the message reproducible.

    Args:
        cobol_name: The name that was not found.
        copybook: The copybook the caller narrowed to, if any.
        conditional_variable: The carrier the caller narrowed to, if any.

    Returns:
        A message naming what was asked for, how many rows exist, and any near miss.
    """
    probe = cobol_name.casefold().replace("_", "-")
    near = tuple(
        spec.cobol_name
        for spec in CONDITION_NAMES
        if probe in spec.cobol_name.casefold()
        or spec.cobol_name.casefold() in probe
    )
    narrowed = ""
    if copybook is not None or conditional_variable is not None:
        elsewhere = _SPECS_BY_FOLDED_NAME.get(cobol_name.casefold(), ())
        narrowed = (
            " The search was narrowed to "
            + (("copybook " + repr(copybook)) if copybook is not None else "")
            + (
                " and " if copybook is not None
                and conditional_variable is not None else ""
            )
            + (
                ("conditional variable " + repr(conditional_variable))
                if conditional_variable is not None else ""
            )
            + "."
        )
        if elsewhere:
            narrowed = narrowed + (
                " The name IS declared, at "
                + ", ".join(spec.locator for spec in elsewhere)
                + "; `SPECS_BY_COBOL_NAME` lists every declaration."
            )
    opening = (
        "No 88-level condition name " + repr(cobol_name) + " is declared in "
        "the frozen copybooks this registry transcribes. It holds "
        + str(len(CONDITION_NAMES))
        + " condition names from "
        + str(len(COUNTS_BY_COPYBOOK))
        + " copybooks; `SPECS_BY_COBOL_NAME` lists every one under its exact "
        "COBOL spelling."
    )
    if not near:
        return (
            opening + narrowed
            + " Nothing similar was found. Adding a condition name the "
            "copybooks do not declare is forbidden by rule R-3."
        )
    return opening + narrowed + " Did you mean: " + ", ".join(near[:8]) + "?"


def _ambiguous_name_message(
    cobol_name: str, matches: tuple[ConditionNameSpec, ...]
) -> str:
    """Explain that a name has several declarations and how to pick one.

    Every candidate is named with its locator, its value clause and its carrier, because
    the value clauses are what differ and are therefore what the caller has to choose
    between.

    Args:
        cobol_name: The ambiguous name as the caller spelled it.
        matches: Its declarations, in registry order.

    Returns:
        A message naming every candidate and the two ways to disambiguate.
    """
    candidates = "; ".join(
        spec.cobol_name + " " + spec.value_clause_text
        + " on " + spec.conditional_variable + " [" + spec.locator + "]"
        for spec in matches
    )
    return (
        "The condition name " + repr(cobol_name) + " is declared "
        + str(len(matches))
        + " times in the frozen copybooks, with value clauses that differ, so "
        "there is no single row to return: " + candidates + ". Say which by "
        "passing copybook= or conditional_variable=, or take them all from "
        "`SPECS_BY_COBOL_NAME`. Returning one of them silently would make the "
        "name mean whichever copybook this registry happens to transcribe "
        "first, which is the collapse rule R-4 forbids. COBOL meets the same "
        "problem and answers it the same way - field-name collisions force "
        "QUALIFIED references, as at [general/gl070.cbl:L497], "
        "[general/gl070.cbl:L521] and [general/gl070.cbl:L525]; "
        "`qualified_cobol_name` renders that form."
    )


def values_for(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> tuple[str, ...]:
    """The value tokens of one condition name, in declaration order.

    Published for `dal/status.py`, which builds its call-site enumerations from this
    registry rather than transcribing the values a second time - a second transcription
    of fifteen out-of-numeric-order function codes being exactly the error rule R-5
    exists to prevent.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook, to pick between declarations of
            one name.
        conditional_variable: Optionally, the owning field's COBOL name, for the same
            purpose.

    Returns:
        Its tokens as `str`, in declaration order. `("1", "2", "4")` for `OS-Single`;
            `('"Y"',)` for `IRS-Used`; `("0", "1")` for the bounds of `FS-Valid-
            Options`.

    Raises:
        KeyError: No row of that name, or several and none singled out.
    """
    return lookup(
        cobol_name,
        copybook=copybook,
        conditional_variable=conditional_variable,
    ).values


def specs_for_variable(cobol_variable_name: str) -> tuple[ConditionNameSpec, ...]:
    """Every condition name declared on one conditional variable, in order.

    DECLARATION order, which for `File-Function` is NOT numeric order: the values come
    back `1 2 3 4 5 6 7 8 9 15 13 31 32 33 34`, because [copybooks/wsfnctn.cob:L99]
    declares 15 before [copybooks/wsfnctn.cob:L100] declares 13.

    Args:
        cobol_variable_name: The conditional variable's COBOL name, in any casing -
            `"File-Function"`, `"Batch-Status"`, `"IRS-Instead"`.

    Returns:
        Its condition names in declaration order, or an empty tuple when no condition
            name is declared on a field of that name.
    """
    probe = cobol_variable_name.casefold()
    return tuple(
        spec
        for spec in CONDITION_NAMES
        if spec.conditional_variable.casefold() == probe
    )


def specs_for_copybook(copybook: str) -> tuple[ConditionNameSpec, ...]:
    """Every condition name one copybook declares, in file order.

    Args:
        copybook: The copybook's repository-relative path, for example
            `"copybooks/wsbatch.cob"`.

    Returns:
        Its condition names in file order, or an empty tuple when the registry
            transcribes no such copybook. `COUNTS_BY_COPYBOOK` names the thirteen it
            does.
    """
    return tuple(spec for spec in CONDITION_NAMES if spec.copybook == copybook)


def conditional_variables() -> tuple[str, ...]:
    """Every conditional variable that carries a condition name, in file order.

    Built by walking `CONDITION_NAMES` and keeping first appearances, so the order is
    the registry's and no mapping is iterated (rule R-6).

    Returns:
        The COBOL names of the owning fields, each once.
    """
    return tuple(
        dict.fromkeys(spec.conditional_variable for spec in CONDITION_NAMES)
    )


def evaluate(
    spec_or_name: ConditionNameSpec | str,
    value: int | str | decimal.Decimal,
    *,
    descriptor: FieldDescriptor | None = None,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> bool:
    """Whether one value satisfies one 88-level condition name.

    A GAPPED list stays gapped. `OS-Single` [copybooks/wssystem.cob:L109] holds for 1, 2
    and 4 and NOT for 3, because membership is tested against the tokens and never
    against a range spanning them (rule R-4).

    Args:
        spec_or_name: A row from the registry, or a condition name in any casing.
        value: The conditional variable's value. An `int` (or `bool`), a `str`, or an
            exact `decimal.Decimal`.
        descriptor: Optionally, the `FieldDescriptor` of the conditional variable. Used
            only for an alphanumeric comparison, to supply the declared field width
            COBOL would pad to.
        copybook: Optionally, the declaring copybook, used only when `spec_or_name` is a
            NAME and that name has several declarations.
        conditional_variable: Optionally, the owning field's COBOL name, for the same
            purpose.

    Returns:
        True when the condition name holds for that value, otherwise False.

    Raises:
        TypeError: The value is a `float` or a `complex` (rule R-2), or is not a type a
            COBOL field can hold.
        KeyError: `spec_or_name` is a name the registry does not declare, or one it
            declares several times and neither narrowing argument said which.
    """
    # Rule R-2 first, before anything reads the value: a binary float must not reach a
    # comparison even to be rejected by it.
    if isinstance(value, (float, complex)):
        raise TypeError(
            "Rule R-2 admits no binary floating point: " + repr(value)
            + " is a " + type(value).__name__ + ", which cannot hold a COBOL "
            "field's value exactly. Pass an int, a str, or a decimal.Decimal. "
            "This is a gate on the operand's type, not a validation of data - "
            "a value that merely fails to match returns False."
        )
    if not isinstance(value, (int, str, decimal.Decimal)):
        raise TypeError(
            "A condition name is tested against a COBOL field's value, so "
            + repr(value) + " of type " + type(value).__name__ + " has no "
            "reading here. Pass an int, a str, or a decimal.Decimal."
        )

    spec = spec_or_name if isinstance(spec_or_name, ConditionNameSpec) else (
        lookup(
            spec_or_name,
            copybook=copybook,
            conditional_variable=conditional_variable,
        )
    )

    if spec.is_alphanumeric:
        return _matches_literal(spec, value, descriptor)
    return _matches_number(spec, value)


def _matches_number(
    spec: ConditionNameSpec, value: int | str | decimal.Decimal
) -> bool:
    """Test a numeric conditional variable's value against a numeric clause.

    Args:
        spec: The row, of any shape but `ALPHANUMERIC`.
        value: The value.

    Returns:
        True when it satisfies the clause.
    """
    read = _read_operand(value)
    if read is None:
        return False
    numbers = spec.numeric_values()
    if spec.kind is ConditionKind.THRU_RANGE:
        lower, upper = numbers
        return lower <= read <= upper
    # Membership, for SINGLE, FIGURATIVE and VALUE_LIST alike - so a gapped list stays
    # gapped (rule R-4).
    return any(read == number for number in numbers)


def _matches_literal(
    spec: ConditionNameSpec,
    value: int | str | decimal.Decimal,
    descriptor: FieldDescriptor | None,
) -> bool:
    """Test a text conditional variable's value against the clause's literals.

    MEMBERSHIP over every literal the clause declares, which is what COBOL does for an
    alphanumeric condition name exactly as it does for a numeric `VALUE_LIST`.

    Args:
        spec: The row, of either alphanumeric shape.
        value: The value.
        descriptor: The conditional variable's descriptor, or None. Its
            `character_length` supplies the declared field width to pad to.

    Returns:
        True when the padded value matches any padded literal character for character,
            case-SENSITIVELY. Otherwise False.
    """
    literals = spec.literal_texts()
    text = value if isinstance(value, str) else str(value)
    width = len(text)
    for literal in literals:
        width = max(width, len(literal))
    if descriptor is not None and descriptor.character_length:
        width = max(width, descriptor.character_length)
    padded = _pad(text, width)
    return any(padded == _pad(literal, width) for literal in literals)


def _build_predicate(
    spec: ConditionNameSpec,
) -> Callable[[int | str | decimal.Decimal], bool]:
    """Build the one-argument predicate for one registry row.

    Shared by `predicate_for` and by `PREDICATES`, so that a predicate obtained either
    way is built the same way and carries the same name and docstring.

    Args:
        spec: The row.

    Returns:
        A callable taking one value and returning whether that declaration holds for it.
    """

    def _predicate(value: int | str | decimal.Decimal) -> bool:
        """Whether the closed-over condition name holds for one value."""
        return evaluate(spec, value)

    _predicate.__name__ = spec.predicate_name
    _predicate.__qualname__ = spec.predicate_name
    _predicate.__doc__ = (
        "Whether `" + spec.declaration_text + "` holds for one value. "
        "Declared at [" + spec.locator + "] on " + spec.conditional_variable
        + "."
    )
    return _predicate


def predicate_for(
    cobol_name: str,
    *,
    copybook: str | None = None,
    conditional_variable: str | None = None,
) -> Callable[[int | str | decimal.Decimal], bool]:
    """A one-argument predicate for any of the registry's condition names.

    Args:
        cobol_name: The condition name, in any casing.
        copybook: Optionally, the declaring copybook, to pick between declarations of
            one name - a name declared four times has four different predicates and this
            says which is wanted.
        conditional_variable: Optionally, the owning field's COBOL name, for the same
            purpose.

    Returns:
        A callable taking one value and returning whether the condition name holds for
            it.

    Raises:
        KeyError: No row of that name, or several and none singled out.
    """
    return _build_predicate(
        lookup(
            cobol_name,
            copybook=copybook,
            conditional_variable=conditional_variable,
        )
    )


# A predicate for EVERY ONE of the 159 declarations, keyed by the row's unique
# `predicate_name`. This is the coverage guarantee rule R-5 asks for.
PREDICATES: Final[
    Mapping[str, Callable[[int | str | decimal.Decimal], bool]]
] = types.MappingProxyType(
    {spec.predicate_name: _build_predicate(spec) for spec in CONDITION_NAMES}
)


# 57 named predicates, in two groups.

# copybooks/wsfnctn.cob - 03 File-Function pic 99. [L88], names at L89-L105. BOUND IN
# DECLARATION ORDER, which is not numeric order.
_FN_OPEN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-open"]
_FN_CLOSE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-close"]
_FN_READ_NEXT: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-read-next"]
_FN_READ_INDEXED: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-read-indexed"]
_FN_WRITE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-write"]
_FN_DELETE_ALL: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Delete-All"]
_FN_RE_WRITE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-re-write"]
_FN_DELETE: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-delete"]
_FN_START: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-start"]
_FN_WRITE_RAW: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Write-Raw"]
_FN_READ_NEXT_RAW: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-Next-Raw"]
_FN_READ_BY_NAME: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-By-Name"]
_FN_READ_BY_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-By-Batch"]
_FN_READ_BY_CUST: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-Read-By-Cust"]
_FN_READ_NEXT_HEADER: Final[ConditionNameSpec] = BY_COBOL_NAME[
    "fn-Read-Next-Header"
]

_FN_INPUT: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-input"]
_FN_I_O: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-i-o"]
_FN_OUTPUT: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-output"]
_FN_EXTEND: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-extend"]
_FN_EQUAL_TO: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-equal-to"]
_FN_LESS_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-less-than"]
_FN_GREATER_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-greater-than"]
_FN_NOT_LESS_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME["fn-not-less-than"]
_FN_NOT_GREATER_THAN: Final[ConditionNameSpec] = BY_COBOL_NAME[
    "fn-not-greater-than"
]

_GL_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["GL-Batch"]
_PL_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["PL-Batch"]
_SL_BATCH: Final[ConditionNameSpec] = BY_COBOL_NAME["SL-Batch"]
_STATUS_OPEN: Final[ConditionNameSpec] = BY_COBOL_NAME["Status-Open"]
_STATUS_CLOSED: Final[ConditionNameSpec] = BY_COBOL_NAME["Status-Closed"]
_WAITING: Final[ConditionNameSpec] = BY_COBOL_NAME["Waiting"]
_PROCESSED: Final[ConditionNameSpec] = BY_COBOL_NAME["Processed"]
_ARCHIVED: Final[ConditionNameSpec] = BY_COBOL_NAME["Archived"]

_IRS_USED: Final[ConditionNameSpec] = BY_COBOL_NAME["IRS-Used"]
_IRS_BOTH_USED: Final[ConditionNameSpec] = BY_COBOL_NAME["IRS-Both-Used"]
_DATE_UK: Final[ConditionNameSpec] = BY_COBOL_NAME["Date-UK"]
_DATE_USA: Final[ConditionNameSpec] = BY_COBOL_NAME["Date-USA"]
_DATE_INTL: Final[ConditionNameSpec] = BY_COBOL_NAME["Date-Intl"]
_DATE_VALID_FORMATS: Final[ConditionNameSpec] = BY_COBOL_NAME[
    "Date-Valid-Formats"
]

_TESTING_1: Final[ConditionNameSpec] = BY_COBOL_NAME["Testing-1"]
_OWNER: Final[ConditionNameSpec] = BY_COBOL_NAME["Owner"]
_SUB: Final[ConditionNameSpec] = BY_COBOL_NAME["Sub"]
_SUPPLIER_DEAD: Final[ConditionNameSpec] = BY_COBOL_NAME["Supplier-dead"]

_PENDING_SLWSINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv.cob:L53"
]
_PENDING_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L72"
]
_PENDING_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L41"
]
_PENDING_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L41"
]

_APPLIED_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L74"
]
_APPLIED_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L43"
]
_APPLIED_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L43"
]

_IH_ANALYISED_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L89"
]
_IH_ANALYISED_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L53"
]
_IH_ANALYISED_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L53"
]

_IL_ANALYISED_SLWSINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsinv2.cob:L105"
]
_IL_ANALYISED_PLWSPINV: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv.cob:L83"
]
_IL_ANALYISED_PLWSPINV2: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwspinv2.cob:L72"
]

_S_CLOSED_SLWSOI: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/slwsoi.cob:L49"
]
_S_CLOSED_PLWSOI: Final[ConditionNameSpec] = BY_LOCATOR[
    "copybooks/plwsoi.cob:L55"
]


def is_fn_open(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-open`, value 1.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_FN_OPEN, value)


def is_fn_close(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-close`, value 2.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_FN_CLOSE, value)


def is_fn_read_next(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-read-next`, value 3.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_FN_READ_NEXT, value)


def is_fn_read_indexed(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-read-indexed`, value 4.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 4.
    """
    return evaluate(_FN_READ_INDEXED, value)


def is_fn_write(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-write`, value 5.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 5.
    """
    return evaluate(_FN_WRITE, value)


def is_fn_delete_all(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Delete-All`, value 6.

    Declared at [copybooks/wsfnctn.cob:L94], its mixed capitalisation kept in the
    registry as the copybook writes it (rule R-5).

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 6.
    """
    return evaluate(_FN_DELETE_ALL, value)


def is_fn_re_write(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-re-write`, value 7.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 7.
    """
    return evaluate(_FN_RE_WRITE, value)


def is_fn_delete(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-delete`, value 8.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 8.
    """
    return evaluate(_FN_DELETE, value)


def is_fn_start(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-start`, value 9.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 9.
    """
    return evaluate(_FN_START, value)


def is_fn_write_raw(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Write-Raw`, value 15.

    Declared at [copybooks/wsfnctn.cob:L99] - BEFORE value 13 at
    [copybooks/wsfnctn.cob:L100], so the group's declaration order is not its numeric
    order. Both are preserved as declared (rule R-4).

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 15.
    """
    return evaluate(_FN_WRITE_RAW, value)


def is_fn_read_next_raw(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-Next-Raw`, value 13.

    Declared at [copybooks/wsfnctn.cob:L100] - AFTER value 15 at
    [copybooks/wsfnctn.cob:L99]. The maintainer records the renumbering at
    [copybooks/wsfnctn.cob:L15]: "next-read-raw changed to 13" (rule R-4).

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 13.
    """
    return evaluate(_FN_READ_NEXT_RAW, value)


def is_fn_read_by_name(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-By-Name`, value 31.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 31.
    """
    return evaluate(_FN_READ_BY_NAME, value)


def is_fn_read_by_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-By-Batch`, value 32.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 32.
    """
    return evaluate(_FN_READ_BY_BATCH, value)


def is_fn_read_by_cust(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-By-Cust`, value 33.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 33.
    """
    return evaluate(_FN_READ_BY_CUST, value)


def is_fn_read_next_header(value: int | str | decimal.Decimal) -> bool:
    """Whether `File-Function` holds `fn-Read-Next-Header`, value 34.

    Args:
        value: The `File-Function` value.

    Returns:
        True when it is 34.
    """
    return evaluate(_FN_READ_NEXT_HEADER, value)


def is_fn_input(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-input`, value 1.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_FN_INPUT, value)


def is_fn_i_o(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-i-o`, value 2.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_FN_I_O, value)


def is_fn_output(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-output`, value 3.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_FN_OUTPUT, value)


def is_fn_extend(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-extend`, value 4.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 4.
    """
    return evaluate(_FN_EXTEND, value)


def is_fn_equal_to(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-equal-to`, value 5.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 5.
    """
    return evaluate(_FN_EQUAL_TO, value)


def is_fn_less_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-less-than`, value 6.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 6.
    """
    return evaluate(_FN_LESS_THAN, value)


def is_fn_greater_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-greater-than`, value 7.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 7.
    """
    return evaluate(_FN_GREATER_THAN, value)


def is_fn_not_less_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-not-less-than`, value 8.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 8.
    """
    return evaluate(_FN_NOT_LESS_THAN, value)


def is_fn_not_greater_than(value: int | str | decimal.Decimal) -> bool:
    """Whether `Access-Type` holds `fn-not-greater-than`, value 9.

    Args:
        value: The `Access-Type` value.

    Returns:
        True when it is 9.
    """
    return evaluate(_FN_NOT_GREATER_THAN, value)


def is_gl_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `WS-Ledger` holds `GL-Batch`, value 1.

    Args:
        value: The `WS-Ledger` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_GL_BATCH, value)


def is_pl_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `WS-Ledger` holds `PL-Batch`, value 2.

    Args:
        value: The `WS-Ledger` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_PL_BATCH, value)


def is_sl_batch(value: int | str | decimal.Decimal) -> bool:
    """Whether `WS-Ledger` holds `SL-Batch`, value 3.

    Args:
        value: The `WS-Ledger` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_SL_BATCH, value)


def is_status_open(value: int | str | decimal.Decimal) -> bool:
    """Whether `Batch-Status` holds `Status-Open`, value 0.

    This function reports the condition and nothing more.

    Args:
        value: The `Batch-Status` value.

    Returns:
        True when it is 0.
    """
    return evaluate(_STATUS_OPEN, value)


def is_status_closed(value: int | str | decimal.Decimal) -> bool:
    """Whether `Batch-Status` holds `Status-Closed`, value 1.

    Args:
        value: The `Batch-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_STATUS_CLOSED, value)


def is_waiting(value: int | str | decimal.Decimal) -> bool:
    """Whether `Cleared-Status` holds `Waiting`, value 0.

    Args:
        value: The `Cleared-Status` value.

    Returns:
        True when it is 0.
    """
    return evaluate(_WAITING, value)


def is_processed(value: int | str | decimal.Decimal) -> bool:
    """Whether `Cleared-Status` holds `Processed`, value 1.

    Declared at [copybooks/wsbatch.cob:L31]. gl072 stamps the value as a literal rather
    than through the condition name, at [general/gl072.cbl:L375].

    Args:
        value: The `Cleared-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_PROCESSED, value)


def is_archived(value: int | str | decimal.Decimal) -> bool:
    """Whether `Cleared-Status` holds `Archived`, value 2.

    Args:
        value: The `Cleared-Status` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_ARCHIVED, value)


# IRS-Instead - the three-state fan-out [copybooks/wssystem.cob:L180-L181] THREE states,
# TWO condition names. The third state is space, and for space BOTH predicates below are
# False.


def is_irs_used(value: int | str | decimal.Decimal) -> bool:
    """Whether `IRS-Instead` holds `IRS-Used`, the literal "Y".

    Args:
        value: The `IRS-Instead` value, one character.

    Returns:
        True when it is "Y".
    """
    return evaluate(_IRS_USED, value)


def is_irs_both_used(value: int | str | decimal.Decimal) -> bool:
    """Whether `IRS-Instead` holds `IRS-Both-Used`, the literal "B".

    Args:
        value: The `IRS-Instead` value, one character.

    Returns:
        True when it is "B".
    """
    return evaluate(_IRS_BOTH_USED, value)


def is_date_uk(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-UK`, value 1.

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_DATE_UK, value)


def is_date_usa(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-USA`, value 2.

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 2.
    """
    return evaluate(_DATE_USA, value)


def is_date_intl(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-Intl`, value 3.

    Declared at [copybooks/wssystem.cob:L131]. NEVER TESTED BY THE MIGRATED CYCLE: the
    date wrapper sections test `Date-UK` and `Date-USA` and then fall through to the
    international form without naming it. Published for traceability.

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 3.
    """
    return evaluate(_DATE_INTL, value)


def is_date_valid_formats(value: int | str | decimal.Decimal) -> bool:
    """Whether `Date-Form` holds `Date-Valid-Formats`, values 1, 2 or 3.

    Declared at [copybooks/wssystem.cob:L132]. DECLARED AND NEVER TESTED - the date
    wrapper sections ignore it and test the conditional variable against a figurative
    constant instead, at [general/gl070.cbl:L583-L584].

    Args:
        value: The `Date-Form` value.

    Returns:
        True when it is 1, 2 or 3.
    """
    return evaluate(_DATE_VALID_FORMATS, value)


# Nine COBOL names, nineteen declarations.


def is_supplier_dead(value: int | str | decimal.Decimal) -> bool:
    """Whether `Purch-Status` holds `Supplier-dead`, value 0.

    The carrier is `pic 9`, so this is the numeric 0 and not the character "0".

    Args:
        value: The `Purch-Status` value.

    Returns:
        True when it is 0.
    """
    return evaluate(_SUPPLIER_DEAD, value)


def is_pending_slwsinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `sih-status` holds `pending`, the literals "P" or "p".

    Declared `values "P" "p".` at [copybooks/slwsinv.cob:L53] - TWO literals, upper case
    first, tested by membership. This is the sales invoice layout reached by
    [common/acas016.cbl].

    Args:
        value: The `sih-status` value, one character.

    Returns:
        True when it is "P" or "p".
    """
    return evaluate(_PENDING_SLWSINV, value)


def is_pending_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `pending`, the literal "P".

    The single-literal form is the divergence, not a transcription slip: it is
    reproduced because rule R-4 makes the frozen declaration the specification.

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "P".
    """
    return evaluate(_PENDING_SLWSINV2, value)


def is_applied_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `applied`, the literal "Z".

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "Z".
    """
    return evaluate(_APPLIED_SLWSINV2, value)


def is_ih_analyised_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-update` holds `ih-analyised`, the literal "Z".

    Args:
        value: The `ih-update` value, one character.

    Returns:
        True when it is "Z".
    """
    return evaluate(_IH_ANALYISED_SLWSINV2, value)


def is_il_analyised_slwsinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `il-update` holds `il-analyised`, the literal "Z".

    Args:
        value: The `il-update` value, one character.

    Returns:
        True when it is "Z".
    """
    return evaluate(_IL_ANALYISED_SLWSINV2, value)


def is_s_closed_slwsoi(value: int | str | decimal.Decimal) -> bool:
    """Whether the sales `OI-Status` holds `S-Closed`, value 1.

    Declared at [copybooks/slwsoi.cob:L49], where the maintainer's trailing comment
    reads "Paid". LIVE at [sales/sl060.cbl:L668], [sales/sl060.cbl:L877] and
    [sales/sl100.cbl:L350] - in every case a `go to` that SKIPS the open-item record, so
    the predicate decides whether a paid item is reprocessed.

    Args:
        value: The `OI-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_S_CLOSED_SLWSOI, value)


def is_pending_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `pending`, the literals "P" or "p".

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "P" or "p".
    """
    return evaluate(_PENDING_PLWSPINV, value)


def is_applied_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `applied`, the literals "Z" or "z".

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "Z" or "z".
    """
    return evaluate(_APPLIED_PLWSPINV, value)


def is_ih_analyised_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-update` holds `ih-analyised`, the literals "Z" or "z".

    Args:
        value: The `ih-update` value, one character.

    Returns:
        True when it is "Z" or "z".
    """
    return evaluate(_IH_ANALYISED_PLWSPINV, value)


def is_il_analyised_plwspinv(value: int | str | decimal.Decimal) -> bool:
    """Whether `il-update` holds `il-analyised`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv.cob:L83] - LOWER case first, the
    one clause in that copybook to do so.

    Args:
        value: The `il-update` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_IL_ANALYISED_PLWSPINV, value)


def is_pending_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `pending`, the literals "p" or "P".

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "p" or "P".
    """
    return evaluate(_PENDING_PLWSPINV2, value)


def is_applied_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-status` holds `applied`, the literals "z" or "Z".

    Args:
        value: The `ih-status` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_APPLIED_PLWSPINV2, value)


def is_ih_analyised_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `ih-update` holds `ih-analyised`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv2.cob:L53] and LIVE at
    [purchase/pl055.cbl:L365] and [purchase/pl055.cbl:L370] - the purchase mirror of
    [sales/sl055.cbl:L427] and [sales/sl055.cbl:L440], but over two literals rather than
    one.

    Args:
        value: The `ih-update` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_IH_ANALYISED_PLWSPINV2, value)


def is_il_analyised_plwspinv2(value: int | str | decimal.Decimal) -> bool:
    """Whether `il-update` holds `il-analyised`, the literals "z" or "Z".

    Declared `values "z" "Z".` at [copybooks/plwspinv2.cob:L72] and LIVE at
    [purchase/pl055.cbl:L314] - the purchase mirror of [sales/sl055.cbl:L373], again
    over two literals rather than one.

    Args:
        value: The `il-update` value, one character.

    Returns:
        True when it is "z" or "Z".
    """
    return evaluate(_IL_ANALYISED_PLWSPINV2, value)


def is_s_closed_plwsoi(value: int | str | decimal.Decimal) -> bool:
    """Whether the purchase `OI-Status` holds `S-Closed`, value 1.

    Args:
        value: The `OI-Status` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_S_CLOSED_PLWSOI, value)


def is_owner(value: int | str | decimal.Decimal) -> bool:
    """Whether `NL-Type` holds `Owner`, the literal "O".

    Args:
        value: The `NL-Type` value, one character.

    Returns:
        True when it is "O".
    """
    return evaluate(_OWNER, value)


def is_sub(value: int | str | decimal.Decimal) -> bool:
    """Whether `NL-Type` holds `Sub`, the literal "S".

    Args:
        value: The `NL-Type` value, one character.

    Returns:
        True when it is "S".
    """
    return evaluate(_SUB, value)


def is_testing_1(value: int | str | decimal.Decimal) -> bool:
    """Whether `SW-Testing` holds `Testing-1`, value 1.

    THE FROZEN COPYBOOK INITIALISES THE CARRIER TO 1, so the switch is ON by default and
    handler logging cannot be turned off without editing a frozen file. That is anomaly
    territory, not a defect to fix.

    Args:
        value: The `SW-Testing` value.

    Returns:
        True when it is 1.
    """
    return evaluate(_TESTING_1, value)


# Rule R-5 wants field-level traceability to be MECHANICAL rather than hand-maintained,
# and this registry is a hand transcription - the one place in the migration where 159
# value clauses are typed out from thirteen frozen copybooks.

# The thirteen copybooks the registry transcribes, in registry order.
_COPYBOOKS_IN_REGISTRY_ORDER: Final[tuple[str, ...]] = (
    _WSFNCTN,
    _WSBATCH,
    _WSSYSTEM,
    _WSSL,
    _WSPL,
    _SLWSINV,
    _SLWSINV2,
    _SLWSOI,
    _PLWSPINV,
    _PLWSPINV2,
    _PLWSOI,
    _IRSWSNL,
    _TESTFLAGS,
)

# The fields of the dictionary's own condition-name record, read at import time from
# `loader.ConditionName` - the loader's binding to the one object-model definition.
_DICTIONARY_CONDITION_FIELDS: Final[tuple[str, ...]] = tuple(
    field.name for field in dataclasses.fields(loader.ConditionName)
)

# Findings carry a prefix so a caller can tell a real disagreement from a remark about
# what could not be checked.
_NOTE: Final[str] = "note: "
_MISMATCH: Final[str] = "mismatch: "


def _dictionary_condition_names(
    copybook: str, path: Path | None
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Read one copybook's condition names out of the generated dictionary.

    Args:
        copybook: The copybook's repository-relative path.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        One row per condition name, in the document's own order, as `(name, value,
            source, conditional_variable, entry_key)`. The first three are the
            dictionary's `ConditionName` fields verbatim.

    Raises:
        loader.DictionaryError: The artifact is missing, unreadable, or catalogues no
            such copybook. The caller turns that into a note.
    """
    rows: list[tuple[str, str, str, str, str]] = []
    for entry in loader.entries_for_copybook_file(copybook, path=path):
        field = entry.copybook
        if field is None:
            continue
        for condition in field.condition_names:
            rows.append(
                (
                    condition.name,
                    condition.value,
                    condition.source,
                    field.name,
                    entry.key,
                )
            )
    return tuple(rows)


def _compare_one_row(
    spec: ConditionNameSpec, row: tuple[str, str, str, str, str]
) -> tuple[str, ...]:
    """Compare one registry row against its dictionary counterpart.

    Args:
        spec: The registry's row.
        row: The dictionary's row, as `_dictionary_condition_names` builds it.

    Returns:
        One finding per field that disagrees, in a fixed order, or an empty tuple when
            the two agree on the spelling, the value clause, the locator and the owning
            conditional variable.
    """
    name, value, source, variable, key = row
    findings: list[str] = []
    lead = _MISMATCH + spec.cobol_name + " [" + spec.locator + "]: "
    if name != spec.cobol_name:
        findings.append(
            lead + "the dictionary spells it " + repr(name) + " at entry "
            + key + "; rule R-5 keeps the copybook's exact spelling."
        )
    if value != spec.value_clause_text:
        findings.append(
            lead + "value clause " + repr(spec.value_clause_text)
            + " here against " + repr(value) + " in the dictionary."
        )
    if source != spec.locator:
        findings.append(
            lead + "locator " + repr(spec.locator) + " here against "
            + repr(source) + " in the dictionary."
        )
    if variable != spec.conditional_variable:
        findings.append(
            lead + "declared on " + repr(spec.conditional_variable)
            + " here against " + repr(variable) + " in the dictionary."
        )
    return tuple(findings)


def _compare_one_copybook(
    copybook: str, rows: tuple[tuple[str, str, str, str, str], ...]
) -> tuple[str, ...]:
    """Compare one copybook's registry rows against its dictionary rows.

    Args:
        copybook: The copybook's repository-relative path.
        rows: Its dictionary rows, in document order.

    Returns:
        Every finding for that copybook, in a fixed order.
    """
    specs = specs_for_copybook(copybook)
    findings: list[str] = []

    if len(rows) != len(specs):
        findings.append(
            _MISMATCH + copybook + ": the registry carries " + str(len(specs))
            + " condition names and the dictionary " + str(len(rows)) + "."
        )

    # Index the dictionary's rows by folded name, keeping every row of a name so a
    # duplicated name is visible rather than silently overwritten.
    by_folded_name: dict[str, tuple[tuple[str, str, str, str, str], ...]] = dict()
    for row in rows:
        folded = row[0].casefold()
        by_folded_name[folded] = by_folded_name.get(folded, ()) + (row,)

    matched: dict[str, bool] = dict()
    for spec in specs:
        folded = spec.cobol_name.casefold()
        candidates = by_folded_name.get(folded, ())
        if not candidates:
            findings.append(
                _MISMATCH + spec.cobol_name + " [" + spec.locator + "]: the "
                "registry declares it and the dictionary does not catalogue it "
                "under " + copybook + "."
            )
            continue
        matched[folded] = True
        if len(candidates) > 1:
            findings.append(
                _MISMATCH + spec.cobol_name + " [" + spec.locator + "]: the "
                "dictionary catalogues the name " + str(len(candidates))
                + " times under " + copybook + ", at "
                + ", ".join(candidate[2] for candidate in candidates) + "."
            )
        findings.extend(_compare_one_row(spec, candidates[0]))

    for row in rows:
        if not matched.get(row[0].casefold(), False):
            findings.append(
                _MISMATCH + row[0] + " [" + row[2] + "]: the dictionary "
                "catalogues it on " + row[3] + " and this registry does not "
                "transcribe it. Rule R-5 wants every 88-level of the migrated "
                "cycle findable here."
            )

    findings.extend(_compare_declaration_order(copybook, specs, rows))
    findings.extend(_check_file_order(copybook, specs))
    return tuple(findings)


def _compare_declaration_order(
    copybook: str,
    specs: tuple[ConditionNameSpec, ...],
    rows: tuple[tuple[str, str, str, str, str], ...],
) -> tuple[str, ...]:
    """Compare declaration order within each conditional variable.

    Order is compared per conditional variable rather than across the whole copybook,
    because the dictionary orders a copybook's entries by record key while this registry
    orders them by source line - the difference explained at the head of this section.

    Args:
        copybook: The copybook's repository-relative path.
        specs: Its registry rows, in registry order.
        rows: Its dictionary rows, in document order.

    Returns:
        One finding per conditional variable whose two orders differ.
    """
    findings: list[str] = []
    variables = tuple(dict.fromkeys(spec.conditional_variable for spec in specs))
    for variable in variables:
        folded = variable.casefold()
        here = tuple(
            spec.cobol_name
            for spec in specs
            if spec.conditional_variable.casefold() == folded
        )
        there = tuple(
            row[0] for row in rows if row[3].casefold() == folded
        )
        if here != there:
            findings.append(
                _MISMATCH + copybook + " " + variable + ": declaration order "
                "differs. Registry " + " ".join(here) + "; dictionary "
                + " ".join(there) + ". Declaration order is not numeric order "
                "for File-Function [copybooks/wsfnctn.cob:L99-L100] and "
                "dal/status.py builds enumeration members from it, so the two "
                "have to agree."
            )
    return tuple(findings)


def _check_file_order(
    copybook: str, specs: tuple[ConditionNameSpec, ...]
) -> tuple[str, ...]:
    """Check that one copybook's registry rows ascend by source line.

    File order across groups is a guarantee this registry owns alone, the dictionary
    ordering by record key instead, so it is tested against the locators rather than
    against the artifact.

    Args:
        copybook: The copybook's repository-relative path.
        specs: Its registry rows, in registry order.

    Returns:
        One finding per row that sits below an earlier one, or an empty tuple.
    """
    findings: list[str] = []
    previous = 0
    previous_name = ""
    for spec in specs:
        line = int(spec.locator.rsplit(":L", 1)[1])
        if line < previous:
            findings.append(
                _MISMATCH + copybook + ": " + spec.cobol_name + " at line "
                + str(line) + " follows " + previous_name + " at line "
                + str(previous) + ", so the rows are not in file order."
            )
        previous = line
        previous_name = spec.cobol_name
    return tuple(findings)


def cross_check_against_dictionary(*, path: Path | None = None) -> tuple[str, ...]:
    """Check this registry against the generated data dictionary (rule R-5).

    Re-reads the same 88-level condition names from
    `data_dictionary/acas_posting_dictionary.json`, which
    `acas_posting/dictionary/generate.py` parses out of the frozen copybooks
    independently of this hand transcription, and reports every disagreement.

    Args:
        path: An explicit artifact path, for a test pointing at a fixture, or None for
            the repository's own dictionary.

    Returns:
        The findings, in a fixed order: the whole-registry count first, then one
            copybook at a time in registry order. Each is prefixed `"mismatch.
    """
    findings: list[str] = []
    total = 0

    for copybook in _COPYBOOKS_IN_REGISTRY_ORDER:
        try:
            rows = _dictionary_condition_names(copybook, path)
        except loader.DictionaryError as unavailable:
            findings.append(
                _NOTE + copybook + " was not checked: "
                + type(unavailable).__name__ + " - "
                + _first_line(str(unavailable))
                + " The registry stands on its own transcription of the frozen "
                "copybook; regenerate data_dictionary/"
                "acas_posting_dictionary.json to have it corroborated."
            )
            continue
        total = total + len(rows)
        findings.extend(_compare_one_copybook(copybook, rows))

    if total and total != len(CONDITION_NAMES):
        findings.insert(
            0,
            _MISMATCH + "the registry carries " + str(len(CONDITION_NAMES))
            + " condition names and the dictionary " + str(total)
            + " across the same "
            + str(len(_COPYBOOKS_IN_REGISTRY_ORDER))
            + " copybooks. Compared on "
            + ", ".join(_DICTIONARY_CONDITION_FIELDS) + ".",
        )
    return tuple(findings)


def _first_line(message: str) -> str:
    """The first line of a message, for quoting inside a one-line finding.

    Args:
        message: A message that may run to several lines.

    Returns:
        Its first non-empty line, ending in a full stop so the finding reads as prose.
    """
    for line in message.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped if stripped.endswith(".") else stripped + "."
    return "no explanation was given."


# `FsReply`, `FileFunction` and `AccessType` are DELIBERATELY ABSENT.

__all__ = [
    "CONDITION_NAMES",
    "ConditionKind",
    "ConditionNameSpec",
    "BY_COBOL_NAME",
    "BY_LOCATOR",
    "BY_PYTHON_NAME",
    "COUNTS_BY_COPYBOOK",
    "DUPLICATED_COBOL_NAMES",
    "FS_REPLY_CONDITION_NAME_COUNT",
    "SPECS_BY_COBOL_NAME",
    "conditional_variables",
    "find",
    "is_declared",
    "lookup",
    "specs_for_copybook",
    "specs_for_name",
    "specs_for_variable",
    "values_for",
    # The one generic predicate, a predicate for any row, and the mapping that holds one
    # for EVERY row - the coverage guarantee behind rule R-5.
    "PREDICATES",
    "evaluate",
    "predicate_for",
    "is_fn_open",
    "is_fn_close",
    "is_fn_read_next",
    "is_fn_read_indexed",
    "is_fn_write",
    "is_fn_delete_all",
    "is_fn_re_write",
    "is_fn_delete",
    "is_fn_start",
    "is_fn_write_raw",
    "is_fn_read_next_raw",
    "is_fn_read_by_name",
    "is_fn_read_by_batch",
    "is_fn_read_by_cust",
    "is_fn_read_next_header",
    "is_fn_input",
    "is_fn_i_o",
    "is_fn_output",
    "is_fn_extend",
    "is_fn_equal_to",
    "is_fn_less_than",
    "is_fn_greater_than",
    "is_fn_not_less_than",
    "is_fn_not_greater_than",
    "is_gl_batch",
    "is_pl_batch",
    "is_sl_batch",
    "is_status_open",
    "is_status_closed",
    "is_waiting",
    "is_processed",
    "is_archived",
    "is_irs_used",
    "is_irs_both_used",
    "is_date_uk",
    "is_date_usa",
    "is_date_intl",
    "is_date_valid_formats",
    "is_supplier_dead",
    "is_pending_slwsinv",
    "is_pending_slwsinv2",
    "is_applied_slwsinv2",
    "is_ih_analyised_slwsinv2",
    "is_il_analyised_slwsinv2",
    "is_s_closed_slwsoi",
    "is_pending_plwspinv",
    "is_applied_plwspinv",
    "is_ih_analyised_plwspinv",
    "is_il_analyised_plwspinv",
    "is_pending_plwspinv2",
    "is_applied_plwspinv2",
    "is_ih_analyised_plwspinv2",
    "is_il_analyised_plwspinv2",
    "is_s_closed_plwsoi",
    "is_owner",
    "is_sub",
    "is_testing_1",
    # The rule R-5 corroboration.
    "cross_check_against_dictionary",
]
