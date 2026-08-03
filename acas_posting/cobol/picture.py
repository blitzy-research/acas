"""The COBOL PICTURE and data-description-entry parser.

Turns the frozen copybooks' declarations into `PictureSpec` and `ParsedEntry`
values: `9`, `X`, `S`, `V`, `Z`, `A`, the repeat form `9(n)`, the implied decimal
point, `USAGE`, `SIGN`, `OCCURS`, `REDEFINES`, `VALUE` and `FILLER`.

Parsing is by declaration, not by convention: the digit count, the scale and the
sign position come out of the clause as written, so a field that is `pic 9(6)` in
the copybook is six unsigned digits here even where the bridge widens it. A
continuation line is joined before parsing, and a `*>` comment is stripped, so
the parser sees the declaration the compiler sees.

Nothing here decides storage BEHAVIOUR - that is `usage` - and nothing here
reads the data dictionary; `descriptor_for` hands a parsed entry on rather than
looking one up.
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

# Agent Action Plan section 0.4.3 lets `cobol/*.py` import `dictionary.loader` and
# nothing else from the dictionary package, so the four object-model names this grammar
# is keyed on arrive through the loader, which re-exports them for exactly this purpose
# (`loader.RE_EXPORTED_MODEL_NAMES`).
from acas_posting.dictionary.loader import (
    SOURCE_LOCATOR_PATTERN,
    SignPosition,
    Usage,
    UsageDeclaredAt,
)

__all__: Final[tuple[str, ...]] = (
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


#  THE ONE FAILURE  (rule R-3)


class PictureError(ValueError):
    """A call into this module was shaped wrongly.

    ALWAYS a programmer error about the CALL, never a judgement on a declaration and
    never reachable from an accounting value - no value reaches this module at all.
    """


class EntryKind(StrEnum):
    """What a line of a COBOL data description turned out to be.

    `StrEnum`, so a member IS its own text and a caller may compare against the string
    directly.
    """

    FIELD = "FIELD"
    """A data-description entry that describes storage, and the only kind that carries a
    `FieldDescriptor`.
    """

    CONDITION_NAME = "CONDITION_NAME"
    """An `88`-level condition name. Part of the data description and NOT a field, so it
    carries no descriptor.
    """

    COPY = "COPY"
    """A `COPY` statement. RECORDED AND NOT EXPANDED - no file is read, which is what keeps
    parsing a pure function of its argument (rule R-6).
    """

    DIRECTIVE = "DIRECTIVE"
    """A `>>` compiler directive. `>>source free` is line 1 of [copybooks/wsmaps03.cob:L1]
    and of every one of the twelve in-scope programs.
    """

    UNRECOGNISED = "UNRECOGNISED"
    """Text the closed grammar does not cover, carried verbatim with a reason."""


INLINE_COMMENT_MARKER: Final[str] = "*>"

DIRECTIVE_PREFIX: Final[str] = ">>"

# The two characters COBOL may delimit an alphanumeric literal with. Only the double
# quote occurs in the frozen sources.
LITERAL_DELIMITERS: Final[tuple[str, ...]] = ('"', "'")


def strip_comments(text: str) -> str:
    """Remove `*>` commentary from one or more physical lines, quote-aware.

    THIS MUST HAPPEN BEFORE ANY PARSING, and rule R-4 is the reason. The maintainer
    annotated three of his own declarations with digit counts that contradict them.

    Args:
        text: One physical line, or several separated by newlines.

    Returns:
        The same text with every comment removed.
    """
    kept_lines: list[str] = []
    for line in text.split("\n"):
        kept_lines.append(_strip_one_line(line))
    return "\n".join(kept_lines)


def _strip_one_line(line: str) -> str:
    """Remove commentary from a single physical line.

    Split out from `strip_comments` so the literal-tracking scan is stated once and
    reads as the small state machine it is.
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
                return line[:index].rstrip()
            index += 1
            continue
        if character == delimiter:
            if line.startswith(delimiter * 2, index):
                index += 2
                continue
            delimiter = None
        index += 1
    return line.rstrip()


# A DECLARATION IS NOT A LINE.


@dataclass(frozen=True, slots=True)
class JoinedEntry:
    """One data-description entry, with the physical lines it came from.

    Frozen and slotted so a caller cannot mutate it behind the joiner's back and two
    runs behave identically (rule R-6).

    Attributes:
        text: The entry with comments already removed and its physical lines joined by
            single spaces, INCLUDING its terminating period when it had one.
        first_line: The physical line the entry begins on, one-based. This is the line
            every `source_locator` is built from.
        last_line: The physical line its terminating period sits on. Equal to
            `first_line` for the great majority; 21 for the entry that begins at 20 in
            [copybooks/wsbatch.cob:L20-L21].
    """

    text: str
    first_line: int
    last_line: int


def join_continuations(
    lines: Iterable[str], *, first_line: int = 1
) -> tuple[JoinedEntry, ...]:
    """Accumulate physical lines into whole entries, in source order.

    THE PERIOD RULE, which is COBOL's own and is the load-bearing part of this FOLLOWED
    BY WHITESPACE OR BY THE END OF THE TEXT.

    Args:
        lines: The physical lines, WITHOUT their line terminators. Comments may still be
            present - they are removed here - so a caller may pass
            `path.read_text().splitlines()` straight in.
        first_line: The one-based number of the first line given, so that a caller
            parsing an extract of a file still gets true locators.

    Returns:
        The entries in source order, as a `tuple` because that order is part of the
            result and must not vary between runs (rule R-6).
    """
    entries: list[JoinedEntry] = []
    pending: list[str] = []
    pending_first: int = first_line

    for offset, raw_line in enumerate(lines):
        line_number = first_line + offset
        stripped = _strip_one_line(raw_line)
        if not stripped.strip():
            continue

        if not pending and stripped.lstrip().startswith(DIRECTIVE_PREFIX):
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
        # A trailing entry with no terminating period. It occurs nowhere in the frozen
        # sources, and emitting what was read beats discarding it silently (rule R-3).
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

    Returns the text up to and INCLUDING the terminating period, and whatever followed
    it, or `(text, None)` when the line holds no terminator.
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
    """Whether the period at `index` separates an entry rather than decorating."""
    following = index + 1
    if following >= len(text):
        return True
    return text[following].isspace()


# Every symbol below occurs in a real declaration; nothing is here on suspicion.
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

# The symbols that count as DIGIT positions, in the sense `digits` and `scale` use.
DIGIT_POSITION_SYMBOLS: Final[tuple[str, ...]] = ("9", "Z")

DECIMAL_POINT_SYMBOLS: Final[tuple[str, ...]] = ("V", ".")

EDIT_SYMBOLS: Final[tuple[str, ...]] = ("Z", "B", ".", "-", "CR")

SIGN_EDIT_SYMBOLS: Final[tuple[str, ...]] = ("-", "CR")

# `PIC` or `PICTURE`, with the optional `IS`.
PICTURE_KEYWORD_RE: Final[re.Pattern[str]] = re.compile(
    r"^pic(?:ture)?\s+(?:is\s+)?", re.IGNORECASE
)

# One picture symbol with its optional repeat count.
PICTURE_SYMBOL_RE: Final[re.Pattern[str]] = re.compile(
    r"(CR|[9XASVZB.\-])(?:\((\d+)\))?"
)


@dataclass(frozen=True, slots=True)
class PictureSpec:
    """Everything one PICTURE clause states about its item's storage.

    Frozen, slotted and built from tuples rather than lists, so that it cannot be
    mutated behind a holder's back and two runs behave identically (rule R-6).

    Attributes:
        text: The picture exactly as the caller wrote it, case preserved and with any
            `PIC` keyword and terminating period removed.
        digits: Total digit positions, integer plus fractional, excluding the sign and
            the decimal point. None for a picture that holds text rather than a number.
        integer_digits: Digit positions left of the decimal point, so that
            `integer_digits + scale == digits` always holds when all three are present -
            the invariant `FieldDescriptor` checks.
        scale: Digit positions right of it. ZERO IS A REAL AND IMPORTANT ANSWER, not a
            missing one.
        character_length: Character positions for a picture that holds text - 32 for
            `pic x(32)` [copybooks/wspost.cob:L24], 1 for `pic a` [irs/irs030.cbl:L352].
        signed: Whether the picture carries a sign: a leading `S`, or one of the sign
            edit symbols. `pic 9(8).99-` [general/gl051.cbl:L182] is signed by its
            trailing `-`.
        is_numeric: Whether the picture describes a number.
        is_alphanumeric: Whether it describes `X` positions.
        is_alphabetic: Whether it describes `A` positions and no `X`. True at exactly
            two in-scope sites, [irs/irs030.cbl:L352] and [irs/irs030.cbl:L359].
        is_edited: Whether the picture is numeric-EDITED - any of `Z`, `B`, `CR`, `-`,
            or an ACTUAL `.`.
        edited_character_length: The RENDERED width in characters of an edited picture,
            counting every inserted symbol - 7 for `pic 9999.99`, 13 for `pic
            z(7)9.99cr`, 9 for `pic z(4)9b(4)` [general/gl051.cbl:L305].
        digit_positions: The digit-position symbols in source order, upper case - `("9",
            "9", "9", "9", "9", "9")` for `pic 9999.99` and `("Z", "Z", "Z", "Z", "Z",
            "Z", "Z", "9", "9", "9")` for `pic z(7)9.99`.
        unrecognised_reason: Why the closed grammar could not read the picture, or None
            when it could.
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
        """Whether the closed grammar read this picture."""
        return self.unrecognised_reason is None

    @property
    def holds_text(self) -> bool:
        """Whether the item this picture describes holds characters, not a number."""
        return self.is_alphanumeric or self.is_alphabetic


def parse_picture(text: str) -> PictureSpec:
    """Read one PICTURE character-string into its storage components.

    The picture ALONE - not a whole entry. An optional leading `PIC`, `PICTURE`, `PIC
    IS` or `PICTURE IS` and an optional single terminating period are accepted and
    removed, so both `parse_picture("s9(8)v99")` and `parse_picture("pic s9(8)v99.")`
    work.

    Args:
        text: The picture character-string.

    Returns:
        Its `PictureSpec`. Out-of-grammar input comes back with `is_recognised` false
            and the reason naming the input, NEVER as an exception (rule R-3).
    """
    stated = text.strip()
    body = PICTURE_KEYWORD_RE.sub("", stated).strip()
    if body.endswith("."):
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

    Repeat counts are expanded into the count rather than into repeated pairs, so
    `z(7)9` becomes `(("Z", 7), ("9", 1))` and a 525-character picture
    [copybooks/wsfnctn.cob:L38] costs two pairs rather than 525.

    Returns:
        The pairs in source order, or a reason string when a character outside the
            closed set was met.
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

    * A digit position is `9` or `Z`, so `pic z(7)9.99cr` is ten digits
    [general/gl072.cbl:L237] while `pic bbbz9` is two [general/gl072.cbl:L238]. * The
    FIRST `V` or `.` is the decimal point; digits after it are the scale.
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


# Every usage spelling this grammar reads, mapped to the dictionary's own vocabulary so
# that nothing downstream has to know COBOL spelling.
USAGE_TOKENS: Final[Mapping[str, Usage]] = MappingProxyType(
    {
        "COMP": Usage.COMP,
        "COMPUTATIONAL": Usage.COMP,
        "COMP-3": Usage.COMP_3,
        "COMPUTATIONAL-3": Usage.COMP_3,
        # Zero occurrences in the copybooks; in the vocabulary because `model.Usage`
        # publishes it.
        "COMP-5": Usage.COMP_5,
        "COMPUTATIONAL-5": Usage.COMP_5,
        "BINARY-CHAR": Usage.BINARY_CHAR,
        "BINARY-SHORT": Usage.BINARY_SHORT,
        "BINARY-LONG": Usage.BINARY_LONG,
    }
)

# The clause keywords this grammar reads, published so a caller can see the closed set
# without reading the scanner.
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

# The phrases an OCCURS clause may carry after its count.
OCCURS_PHRASE_KEYWORDS: Final[tuple[str, ...]] = (
    "ASCENDING",
    "DESCENDING",
    "INDEXED",
)

CLAUSE_NOISE_WORDS: Final[tuple[str, ...]] = ("IS", "ARE", "TIMES", "CHARACTER")

FIGURATIVE_CONSTANTS: Final[tuple[str, ...]] = (
    "ZERO",
    "ZEROS",
    "ZEROES",
    "SPACE",
    "SPACES",
)

RANGE_WORDS: Final[tuple[str, ...]] = ("THRU", "THROUGH")

# The level number that introduces a condition name rather than a field. `88 IRS-Used
# value "Y".` [copybooks/wssystem.cob:L180].
CONDITION_NAME_LEVEL: Final[str] = "88"

FILLER_NAME: Final[str] = "FILLER"

LEVEL_RE: Final[re.Pattern[str]] = re.compile(r"^(\d{1,2})(?=\s|$)")

# `COPY "file00.cob".` and its friends - 32 of them in one copybook alone, e.g.
# [copybooks/wsnames.cob:L17]. RECORDED, NEVER EXPANDED.
COPY_RE: Final[re.Pattern[str]] = re.compile(r"^copy(?=\s|$)", re.IGNORECASE)

BLANK_WHEN_ZERO_RE: Final[re.Pattern[str]] = re.compile(
    r"^blank(?:\s+when)?\s+zero(?=\s|$)", re.IGNORECASE
)


def _tokenise_clauses(text: str) -> tuple[str, ...]:
    """Split an entry into whitespace-separated tokens, keeping literals whole.

    A quoted literal is ONE token, quotes included, because a VALUE literal may contain
    spaces and a naive split would shred it.
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
                    current.append(delimiter)
                    index += 2
                    continue
                # The literal closes here and is complete, so it is emitted at once -
                # anything hard against its closing quote then starts a token of its own
                # rather than being glued to the literal.
                delimiter = None
                tokens.append("".join(current))
                current = []
            index += 1
            continue
        if character in LITERAL_DELIMITERS:
            # ⭐ A LITERAL ALWAYS BEGINS A TOKEN OF ITS OWN, even with no separator
            # before it.
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

    Private and mutable on purpose: it is an accumulator that never leaves this module.
    Everything the module RETURNS is frozen (rule R-6).
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

    Clause order is free in COBOL and the frozen sources exercise several, so this is a
    left-to-right dispatch rather than a fixed sequence.
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
            # `Redefines` [copybooks/wssystem.cob:L63] both occur, which is why the
            # comparison is on the upper-cased token.
            index += 1
            if index < limit:
                scan.redefines = tokens[index]
                index += 1
            continue

        if upper == "USAGE":
            # No in-scope source writes the keyword - all 191 usage clauses are bare, as
            # at `pic 9(5) comp` [copybooks/wsfnctn.cob:L24] - but skipping it costs one
            # branch and refusing it would be a validation the compiler does not perform
            # (rule R-3).
            index = _skip_noise(tokens, index + 1)
            continue

        if upper in USAGE_TOKENS:
            scan.usage = USAGE_TOKENS[upper]
            scan.usage_text = token
            index += 1
            continue

        if upper == "UNSIGNED":
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
    """Step past the optional noise words a clause may carry."""
    while index < len(tokens) and tokens[index].upper() in CLAUSE_NOISE_WORDS:
        index += 1
    return index


def _scan_sign_clause(
    tokens: tuple[str, ...], index: int, scan: _ClauseScan
) -> int:
    """Read a SIGN clause, keeping the source's own spelling.

    ⛔ THE TWO LIVE SPELLINGS ARE NOT UNIFIED. `sign leading` [copybooks/wspost-
    irs.cob:L21] and `sign is leading` [copybooks/irswspost.cob:L14] both describe the
    same storage, and both resolve to the same `SignPosition`, but `sign_clause_text`
    comes back as whichever the source wrote. Rule R-4.
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
    # Joined on a single space, which is what the two live spellings already use, so the
    # text matches `usage.SIGN_LEADING_SPELLINGS` exactly.
    scan.sign_clause_text = " ".join(consumed)
    return index


def _scan_occurs_phrase(
    tokens: tuple[str, ...], index: int, scan: _ClauseScan
) -> int:
    """Read an OCCURS key or index phrase, recording its names.

    `ascending key CoA-Desc` and `indexed CoA-Index` [irs/irs030.cbl:L379-L381] - note
    the second omits the optional `BY`, which is why `BY` is accepted rather than
    required. `indexed by pc` [copybooks/glwspc.cob:L11] writes it.
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

    A quoted literal is already one token and keeps its quotes, so a literal that
    happens to spell a keyword cannot be mistaken for one.
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
    """Count the tokens a BLANK WHEN ZERO clause occupies, or return zero."""
    remainder = " ".join(tokens[index:index + 3])
    match = BLANK_WHEN_ZERO_RE.match(remainder)
    if match is None:
        return 0
    return len(match.group(0).split())


@dataclass(frozen=True, slots=True)
class ParsedEntry:
    """One data-description entry, read into its clauses and its descriptor.

    Frozen and slotted, holding tuples rather than lists, so a holder cannot mutate it
    and two runs behave identically (rule R-6).

    Attributes:
        kind: What this entry is.
        level: The level number exactly as written, so `05` stays `05`.
        name: The name as written, `FILLER` for an unnamed area, None for a directive.
        source_locator: `<path>:L<n>` for this entry, always present, because the
            descriptor it builds cannot exist without one (rule R-5).
        text: The entry verbatim after comment stripping and continuation joining.
        first_line, last_line: The physical lines it starts on and ends on.
        picture: The `PictureSpec`, or None for an item with no PICTURE, which is the
            normal case for `05 Entered binary-long.` and for every group item.
        usage: The storage class in the dictionary's own vocabulary.
        usage_declared_at: Whether it was written here, inherited, or left to default.
        usage_inherited_from: The group item it was inherited from, or None.
        usage_group_source: That group's own `<path>:L<n>`.
        signed: Whether the item holds a sign.
        unsigned: Whether the entry wrote `UNSIGNED` [copybooks/wssystem.cob:L65].
        sign_position: Where that sign lives.
        sign_clause_text: The SIGN clause verbatim, or None. NOT unified across the two
            live spellings - see `_scan_sign_clause`.
        occurs: The OCCURS count, or None. May sit on a group [sales/sl060.cbl:L219].
        occurs_key_order: `ASCENDING` or `DESCENDING` when the OCCURS names a sort key.
        occurs_keys: The key names that phrase gave, in source order.
        occurs_indexed_by: The index names an `INDEXED` phrase gave. Recorded and not
            acted on, an index being a subscript name rather than storage.
        redefines: The item this one redefines, or None.
        is_filler: Whether the item is an unnamed area.
        is_group: Whether it has subordinate items. Exact only from `parse_entries`.
        parent_group: The group immediately above it, or None at the top.
        value_keyword: `VALUE` or `VALUES` as written, or None.
        value_text: The VALUE operand verbatim, quotes and case intact.
        value_number: That operand as a number when it is a single numeric literal.
        blank_when_zero: Whether BLANK WHEN ZERO was written. Recorded only.
        condition_values: For an `88` entry, its values as written, each a `str`.
        condition_is_range: Whether those values are a THRU range rather than a list.
        descriptor: The `FieldDescriptor` for a field entry, None otherwise.
        unrecognised_reason: Why the entry could not be read, or None. Names the input
            verbatim so the grammar can be extended deliberately.
        carried_usage: The storage class this entry hands DOWN to its subordinates,
            which is not its own `usage`: a group's own usage is always `Usage.GROUP`,
            so the class it carries for its children is kept separately. `03 Amounts
            comp-3.` [copybooks/wsbatch.cob:L40] carries `COMP-3` down to four amount
            fields whose own picture lines say nothing about storage.
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

    Rule R-5 makes a locator mandatory, and `FieldDescriptor` enforces it.

    Raises:
        PictureError: The locator is empty or malformed. This is the module's one
            exception, and it is a programmer error rather than a business.
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


# The line numbers inside a locator, so that a single-entry parse can report them
# without the caller repeating itself.
LOCATOR_LINES_RE: Final[re.Pattern[str]] = re.compile(
    r":L(?P<first>[0-9]+)(?:-L(?P<last>[0-9]+))?$"
)


def _lines_from_locator(locator: str) -> tuple[int, int]:
    """Read the first and last line a locator names.

    The locator has already been matched against the dictionary's own pattern, so the
    numbers are present; the fallback exists only so the function is total.
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

    The entry may span physical lines - four in-scope declarations do, and the parser
    must not care - so newlines are collapsed before the clause scan.

    Args:
        text: The entry, with or without its terminating period. Exactly one trailing
            period is removed, so an edited picture keeps its actual decimal point.
        source_locator: `<path>:L<n>` for the declaration. REQUIRED - see
            `_require_locator` for why rule R-5 admits no default.
        inherited_usage: The storage class a group above this item carries, when one
            does.
        inherited_usage_from: The name of that group, for `usage_inherited_from`.
        inherited_usage_source: That group's own locator, for `usage_group_source`.
        parent_group: The group immediately above this item, when known.
        is_group: Whether this item has subordinates.
        first_line: The physical line the entry starts on. Defaults to the line the
            locator names.
        last_line: The line its terminator is on. Defaults likewise.

    Returns:
        The `ParsedEntry`. A field entry carries a `FieldDescriptor` with the given
            locator.

    Raises:
        PictureError: `source_locator` is empty or malformed. Nothing about the COBOL
            input can raise: an entry the grammar cannot read comes back with
            `is_recognised` false (rule R-3).
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
        # `>>source free` [copybooks/wsmaps03.cob:L1]. A compiler directive, recorded so
        # a caller can see it was there and skipped.
        return _plain_entry(
            EntryKind.DIRECTIVE, collapsed, locator, begins, ends
        )

    if COPY_RE.match(body):
        # `copy "wsnames.cob".` [general/gl071.cbl:L157], including the REPLACING form
        # that spans two lines [copybooks/slwsoi3.cob:L18-L19]. RECORDED, NEVER
        # EXPANDED.
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
    # An item that states a picture describes storage itself and so cannot be a group,
    # whatever level follows it.
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
        # Always derived, never asserted, so `FieldDescriptor.__post_init__` cross-
        # checks it against the same rule the generated dictionary states.
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

    Three cases occur. A named item spends one token on its name.
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

    Neither is a field, so neither carries a descriptor; both are returned rather than
    dropped, so that a caller counting a copybook's entries sees everything the file
    contains.
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

    A result rather than an exception, so a caller walking a whole copybook keeps going
    and the omission is visible instead of fatal (rule R-3).
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

    QUOTING CONVENTION, stated once and held to: a value comes back as a `str` exactly
    as written, and A QUOTED LITERAL KEEPS ITS QUOTES - `'"Y"'`, not `'Y'`.
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

    A trailing comma is dropped, because a list may legally be written with separators;
    none of the 154 condition names across the in-scope copybooks uses one, so this
    costs nothing and guesses nothing.
    """
    values: list[str] = []
    is_range = False
    for token in tokens:
        if token.upper() in RANGE_WORDS:
            # `values 0 thru 1` [copybooks/wssystem.cob:L122]: the word joins two values
            # into bounds rather than being a value itself.
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

    Returns:
        The usage, where it was declared, the group it came from, that group's locator,
            and the class this item carries down to its own children.
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

    `UNSIGNED` settles it outright - `05 Page-Lines binary-char unsigned.`
    [copybooks/wssystem.cob:L65]. A group holds no value and so no sign. A picture
    answers for itself: a leading `S` [copybooks/wspost.cob:L23] or a sign edit symbol
    [general/gl051.cbl:L182].
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

    * An unsigned item, and a group, have NO sign position. * A COMP, COMP-3, COMP-5 or
    BINARY-* item's sign is part of its binary or packed representation, so it is
    `IMPLICIT_BINARY` - `pic s9(8)v99 comp-3` [copybooks/wsledger.cob:L28].
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

    A group reports none, because its size is the sum of its children and nothing here
    walks them. An item with no picture reports none either, which is not a gap.
    """
    if grouped or picture is None or not picture.is_recognised:
        return (None, None, None, None)
    return (
        picture.digits,
        picture.integer_digits,
        picture.scale,
        picture.character_length,
    )


VALUE_INTEGER_RE: Final[re.Pattern[str]] = re.compile(r"^[+-]?[0-9]+$")

# A VALUE literal with a decimal point.
VALUE_DECIMAL_RE: Final[re.Pattern[str]] = re.compile(
    r"^[+-]?(?:[0-9]+\.[0-9]*|\.[0-9]+)$"
)


def _value_number(tokens: tuple[str, ...]) -> decimal.Decimal | int | None:
    """Read a single numeric VALUE literal, exactly."""
    if len(tokens) != 1:
        return None
    literal = tokens[0]
    if VALUE_INTEGER_RE.match(literal):
        return int(literal)
    if VALUE_DECIMAL_RE.match(literal):
        # An exact decimal built from the literal's own text, so the value is the digits
        # the source wrote and nothing else.
        return decimal.Decimal(literal)
    return None


def _entry_reason(picture: PictureSpec | None, scan: _ClauseScan) -> str | None:
    """Say why an entry was only partly read, or None when it was read whole.

    An entry that carries an out-of-grammar picture or an out-of-vocabulary clause still
    comes back with everything that WAS read, and with this reason naming what was not,
    so the omission is visible and the grammar can be extended deliberately (rule R-3).
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


# The levels that never nest: an independent working-storage item, a RENAMES and a
# constant.
SPECIAL_LEVELS: Final[tuple[str, ...]] = ("66", "77", "78")

TOP_LEVEL: Final[int] = 1


@dataclass(slots=True)
class _StackFrame:
    """One open group while a record is being walked.

    Private and mutable, like `_ClauseScan`: an accumulator that never leaves this
    module.
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

    ⭐ THIS IS THE FUNCTION THAT GETS GROUP-LEVEL USAGE RIGHT, and it is the one a caller
    should reach for by default. `parse_entry` cannot.

    Args:
        text: The source of the record or group, comments and all.
        source_path: The repository-relative path the text came from, used to build each
            entry's locator. Every descriptor needs one (rule R-5).
        first_line: The one-based number of the first line of `text`, so an extract
            still yields true locators - pass 35 when handing it
            [copybooks/wsbatch.cob:L35-L44].

    Returns:
        The entries in SOURCE ORDER, as a `tuple` because that order is part of the
            result and must not vary between runs (rule R-6).
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
    # The elementary or group item most recently seen, so that an 88 condition name can
    # name the item it qualifies - which is how the generated dictionary attaches one,
    # as `copybook.condition_names`.
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
                    # The group that WROTE the class keeps the credit, so a nested group
                    # passes its ancestor's name and locator through rather than
                    # substituting its own.
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

    `LEVEL_RE` has already matched digits by the time this is reached, so the fallback
    exists only so the function is total.
    """
    return int(level) if level.isdigit() else TOP_LEVEL


def _groupness(entries: tuple[ParsedEntry, ...]) -> tuple[bool, ...]:
    """Decide, for each entry, whether it has subordinate items.

    * An entry that states a picture is never a group [copybooks/slwsoi3.cob:L9].
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

    The convenience entry point for the program-local working storage this module exists
    to describe - the fields the generated dictionary does not cover, because they never
    reach a table.

    Args:
        clauses: The picture and clauses as the source writes them, with or without the
            `PIC` keyword and with or without a terminating period.
        name: The field's name, verbatim from its declaration.
        source_locator: `<path>:L<n>`. REQUIRED, and the whole point: these fields have
            no dictionary key, so the locator is the only traceability they will ever
            have (rule R-5).
        level: The level number, defaulting to the commonest. Pass `"77"` for an
            independent item [general/gl071.cbl:L149].
        inherited_usage: The class a group above the field carries, when one does -
            `Usage.COMP_3` for a field under `03 Amounts comp-3.`
            [copybooks/wsbatch.cob:L40].
        inherited_usage_from: That group's name.
        inherited_usage_source: That group's locator.
        parent_group: The group immediately above the field.
        is_group: Whether the field has subordinates. Leave None for an ordinary
            elementary item.

    Returns:
        The `FieldDescriptor`, carrying the locator.

    Raises:
        PictureError: The locator is missing or malformed, or the composed text did not
            read as a field entry - which can only happen if `clauses` or `name` was not
            what it claimed, and the message names both so the mistake is obvious.
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
    """Give a bare leading picture its `PIC` keyword, and leave anything else be."""
    if not clauses:
        return clauses
    head = clauses.split(maxsplit=1)[0].upper()
    if head in CLAUSE_KEYWORDS or head in USAGE_TOKENS:
        return clauses
    return f"pic {clauses}"
