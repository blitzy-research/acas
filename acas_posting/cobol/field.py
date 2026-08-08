"""The `FieldDescriptor` value object: one COBOL data item, described.

Carries the digits, scale, signedness, usage and sign position of a single field,
so arithmetic and `MOVE` take a descriptor and a value rather than hard-coded
per-field rules - the only tractable way to get several hundred fields right.

Every descriptor is BUILT FROM A DICTIONARY ENTRY, never from a hand-written
picture clause (R-5): `from_dictionary_key` is the constructor the record modules
use, and it fails loudly rather than guessing. A key that names a column with no
copybook counterpart - the three IRS date components the bridge derives
[common/irspostingMT.cbl:L982-L987] - raises `BridgeOnlyFieldError`, because such
a field has no copybook view to describe and belongs to the handler that derives
it.
"""

from __future__ import annotations

import decimal
import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader

# The object model reaches this layer through `dictionary.loader` and through nothing
# else.
from acas_posting.dictionary.loader import (
    ENTRY_KEY_PATTERN,
    REPO_PATH_PATTERN,
    SOURCE_LOCATOR_PATTERN,
    CobolPythonStorage,
    CopybookField,
    DictionaryEntry,
    Drift,
    SignPosition,
    Usage,
    UsageDeclaredAt,
)

__all__: Final[tuple[str, ...]] = (
    "TRUNCATING_STORE",
    "BridgeOnlyFieldError",
    "FieldDescriptor",
    "FieldDescriptorError",
    "MissingProvenanceError",
    "UntrustedEntryError",
    "descriptors_for_copybook_record",
    "descriptors_for_table",
)


# COBOL truncates toward zero on store unless ROUNDED is written.
TRUNCATING_STORE: Final[str] = decimal.ROUND_DOWN


class FieldDescriptorError(ValueError):
    """A descriptor could not be built, or was built wrongly.

    Always a PROGRAMMER error: a missing or malformed provenance, a nonsensical
    combination of components, or a request for COBOL-side storage that the frozen
    sources do not declare.
    """


class MissingProvenanceError(FieldDescriptorError):
    """A descriptor was built with neither a dictionary key nor a locator.

    The invariant rule R-5 puts on this file. Every field a frozen source declares must
    arrive through its `dictionary_key`, which is what makes the field-to-entry mapping
    R-5 asks for real rather than nominal.
    """


class BridgeOnlyFieldError(FieldDescriptorError):
    """The entry has no declaring COBOL view, so it has no COBOL-side storage.

    "Declaring view" means the copybook view, or the program-source view for a work-file
    field that no copybook declares; an entry with neither is one that only the bridge
    and the schema know about.
    """


class UntrustedEntryError(FieldDescriptorError):
    """An entry offered as a descriptor's source does not carry dictionary provenance.

    Every descriptor for a field a frozen source declares arrives through one door,
    `from_dictionary_key`, because rule R-5 makes the dictionary the ONLY sanctioned
    source of that field's picture, scale, signedness and carrier - a hand-written
    descriptor for such a field is precisely the transcription error the data-
    dictionary-first directive exists to prevent.
    """


@dataclass(frozen=True, slots=True, eq=True, repr=False)
class FieldDescriptor:
    """One COBOL data item's storage description, with its provenance.

    Frozen, slotted and value-equal, so that two descriptors built from the same source
    compare equal, neither can be mutated behind a holder's back, and two runs behave
    identically (rule R-6).

    Attributes:
        name: The COBOL field name, verbatim from the frozen source, with case and
            hyphens preserved - `"Sales-Average"`, `"sl4-spare3"`.
        usage: The storage class. Taken from the dictionary for a record field; supplied
            by the picture parser otherwise.
        usage_declared_at: Whether the USAGE clause sat on the item, was inherited from
            a group header, or was absent so the language default governed.
        usage_inherited_from: The group header's name when usage was inherited,
            otherwise None.
        picture: The PICTURE clause exactly as written, verbatim for the same reason
            `sign_clause_text` is.
        signed: Whether the declaration carries a sign.
        sign_position: Where the sign lives - overpunched on the trailing digit by COBOL
            default, on the leading digit when a SIGN clause says so, held separately,
            or implicit in a binary or packed representation.
        sign_clause_text: The SIGN clause exactly as written, so `"sign leading"`
            [copybooks/wspost-irs.cob:L21] and `"sign is leading"`
            [copybooks/irswspost.cob:L14] stay distinguishable. None if absent.
        digits: Total digit count, `integer_digits + scale`. None for an alphanumeric
            item, a group, and a binary-family item whose range comes from its width
            [copybooks/wsbatch.cob:L36-L39].
        integer_digits: Digit count before the implied decimal point.
        scale: Digit count after it. Zero and None both mean "no fractional part"; the
            artifact writes None for an item with no picture.
        character_length: Character count for an alphanumeric item.
        unsigned: Whether the declaration carries the explicit UNSIGNED keyword on a
            binary item, as `Page-Lines binary-char unsigned` does
            [copybooks/wssystem.cob:L65]. Distinct from `signed` being false.
        is_edited: Whether the picture is numeric-edited.
        occurs: The OCCURS count for a table item, otherwise None.
        redefines: The item this one redefines, otherwise None.
        is_filler: Whether the item is FILLER.
        is_group: Whether the item is a group rather than an elementary item.
        parent_group: The immediately containing group's name, otherwise None.
        python_storage: Which carrier holds the value - DECIMAL, INT, STR or NONE.
        dictionary_key: The entry key.
        source_locator: A `<path>:L<n>` locator, carried alongside the key for a
            catalogued field, where it points at the declaration the descriptor was
            built from - a copybook line, or a program's own file-description line for a
            work-file field.
    """

    name: str
    usage: Usage
    usage_declared_at: UsageDeclaredAt = UsageDeclaredAt.DEFAULT
    usage_inherited_from: str | None = None
    picture: str | None = None
    signed: bool = False
    sign_position: SignPosition = SignPosition.NONE
    sign_clause_text: str | None = None
    digits: int | None = None
    integer_digits: int | None = None
    scale: int | None = None
    character_length: int | None = None
    unsigned: bool = False
    is_edited: bool = False
    occurs: int | None = None
    redefines: str | None = None
    is_filler: bool = False
    is_group: bool = False
    parent_group: str | None = None
    python_storage: CobolPythonStorage = CobolPythonStorage.NONE
    dictionary_key: str | None = None
    source_locator: str | None = None

    # Every check below fires on a PROGRAMMER error and none can fire on a data value
    # (rule R-3).

    def __post_init__(self) -> None:
        """Reject a descriptor that could not describe anything truthfully.

        Raises:
            MissingProvenanceError: Neither a dictionary key nor a locator was given, so
                the field could not be audited against the frozen COBOL - the invariant
                rule R-5 puts on this file.
            FieldDescriptorError: The name is blank, the locator is malformed, a count
                is negative, the digit members contradict one another, or a key-less
                descriptor names a carrier that its own usage and scale do not imply.
        """
        if not self.name:
            raise FieldDescriptorError(
                "a FieldDescriptor needs the COBOL field name its frozen "
                "source declares, carried verbatim; got an empty name"
            )

        # R-5, the invariant this file exists to keep. A field a frozen source declares
        # must arrive by its dictionary key.
        if self.dictionary_key is None and self.source_locator is None:
            raise MissingProvenanceError(
                f"{self.name!r} has no provenance: give it a dictionary_key. "
                "The generated artifact catalogues every field the frozen "
                "sources declare - the copybook record layouts, the "
                "bridge-derived columns, and the work-file records the "
                "General Ledger programs declare inline in their own FILE "
                "SECTIONs - so FieldDescriptor.from_dictionary_key is the "
                "route for all of them. A bare source_locator of the form "
                "<path>:L<n> is "
                "provenance for the picture parser's product alone, which "
                "describes a PICTURE clause rather than a catalogued "
                "declaration. Rule R-5 requires every descriptor to be "
                "traceable, and a descriptor with neither is a field whose "
                "behaviour cannot be audited against the COBOL."
            )

        # The locator shape is the dictionary's own, imported rather than retyped so the
        # two can never drift apart.
        locator = self.source_locator
        if locator is not None and not SOURCE_LOCATOR_PATTERN.match(locator):
            raise FieldDescriptorError(
                f"{self.name!r} carries the malformed source_locator "
                f"{self.source_locator!r}: it must be a repository-relative "
                "path, a colon, then L and the line - 'sales/sl060.cbl:L206' "
                "for a single line, 'copybooks/wsbatch.cob:L36-L39' for a span"
            )

        for label, count in (
            ("digits", self.digits),
            ("integer_digits", self.integer_digits),
            ("scale", self.scale),
            ("character_length", self.character_length),
            ("occurs", self.occurs),
        ):
            if count is not None and count < 0:
                raise FieldDescriptorError(
                    f"{self.name!r} has {label}={count}: a count of digits, "
                    "characters or table entries cannot be negative"
                )

        # digits == integer_digits + scale holds for every one of the 388 entries of the
        # generated artifact that carries a digit count, with zero exceptions, so a
        # contradiction here is always a hand-authoring slip - typically a scale copied
        # from a neighbouring declaration.
        if (
            self.digits is not None
            and self.integer_digits is not None
            and self.scale is not None
            and self.integer_digits + self.scale != self.digits
        ):
            raise FieldDescriptorError(
                f"{self.name!r} has digits={self.digits} but "
                f"integer_digits={self.integer_digits} + scale={self.scale} = "
                f"{self.integer_digits + self.scale}: digits is the total, so "
                "the three cannot disagree"
            )

        # A key-less descriptor - the picture parser's - must name the carrier its own
        # usage and scale imply, because nothing else vouches for it.
        if self.dictionary_key is None and self._carrier_is_derivable():
            implied = cobol_usage.python_storage_for(self.usage, self.scale)
            if implied is not self.python_storage:
                raise FieldDescriptorError(
                    f"{self.name!r} at {self.source_locator} names the "
                    f"carrier {self.python_storage.value} but usage "
                    f"{self.usage.value} with scale {self.scale} implies "
                    f"{implied.value}. Derive it from the usage and the scale "
                    "rather than passing it, as picture.py does."
                )

    def _carrier_is_derivable(self) -> bool:
        """Whether the carrier rule applies to this item's usage class.

        The rule covers a group, an alphanumeric item and the numeric classes.
        """
        return (
            cobol_usage.is_group(self.usage)
            or cobol_usage.is_alphanumeric(self.usage)
            or cobol_usage.is_numeric(self.usage)
        )

    def __repr__(self) -> str:
        """Name the field, its storage shape and its provenance.

        Written by hand so that a failing parity test says WHICH field it was looking at
        and WHERE that field is declared, rather than printing every member.
        """
        shape = self.usage.value
        if self.digits is not None:
            shape += f" {self.digits}"
            if self.scale:
                shape += f".{self.scale}"
        elif self.character_length is not None:
            shape += f" x{self.character_length}"
        if self.signed:
            shape += " signed"
        if self.unsigned:
            shape += " unsigned"
        if self.is_edited:
            shape += " edited"
        provenance = self.dictionary_key or self.source_locator
        return (
            f"FieldDescriptor({self.name!r} {shape} "
            f"-> {self.python_storage.value} @ {provenance})"
        )

    # These are properties rather than methods because each is a pure function of the
    # members already held.

    @property
    def byte_length(self) -> int:
        """How many bytes an item of this description occupies.

        Delegated entirely to `usage.byte_length`, so that width lives in one place.

        Raises:
            ValueError: For a group, which has no width of its own - sum its children's
                widths - and for an item whose description omits the count its class
                needs.
        """
        return cobol_usage.byte_length(
            self.usage,
            digits=self.digits,
            scale=self.scale,
            character_length=self.character_length,
            sign_position=self.sign_position,
            unsigned=self.unsigned,
        )

    @property
    def value_domain(self) -> tuple[int, int]:
        """The inclusive bounds an item of this description can hold.

        Delegated to `usage.value_domain`. The bounds are expressed in whole units of
        the item's least significant digit, so a scaled item's domain counts hundredths
        rather than pounds.

        Raises:
            ValueError: For a group and for an alphanumeric item, neither of which holds
                a number, and for a zoned or packed item whose digit count is absent.
        """
        return cobol_usage.value_domain(
            self.usage,
            digits=self.digits,
            signed=self.signed,
            unsigned=self.unsigned,
        )

    @property
    def min_value(self) -> int:
        """The lowest value this item can hold, in units of its last digit."""
        return self.value_domain[0]

    @property
    def max_value(self) -> int:
        """The highest value this item can hold, in units of its last digit."""
        return self.value_domain[1]

    @property
    def quantum(self) -> decimal.Decimal | None:
        """The exponent a store into this item quantizes to, or None.

        BUILT WITHOUT CONSULTING THE AMBIENT DECIMAL CONTEXT, deliberately, and the
        reason is shown rather than asserted. The obvious spelling
        `Decimal(1).scaleb(-scale)` is context-sensitive.
        """
        if self.scale is None:
            return None
        return decimal.Decimal((0, (1,), -self.scale))


    @property
    def is_decimal(self) -> bool:
        """Whether `decimal.Decimal` carries this item's value."""
        return self.python_storage is CobolPythonStorage.DECIMAL

    @property
    def is_int(self) -> bool:
        """Whether `int` carries this item's value.

        True for the binary family and for any zero-scale integer. This is the member
        that makes the legacy averaging defect reproducible: a divide into `Sales-
        Average` [copybooks/wssl.cob:L49] truncates as an integer divide, and only an
        `int` carrier reproduces that.
        """
        return self.python_storage is CobolPythonStorage.INT

    @property
    def is_str(self) -> bool:
        """Whether `str` carries this item's value."""
        return self.python_storage is CobolPythonStorage.STR

    @property
    def is_numeric(self) -> bool:
        """Whether the item's usage class holds a number."""
        return cobol_usage.is_numeric(self.usage)

    @property
    def is_binary_family(self) -> bool:
        """Whether the item is BINARY-CHAR, BINARY-SHORT or BINARY-LONG."""
        return cobol_usage.is_binary_family(self.usage)

    @property
    def is_packed(self) -> bool:
        """Whether the item is packed decimal, COMP-3."""
        return cobol_usage.is_packed(self.usage)

    @property
    def is_zoned_display(self) -> bool:
        """Whether the item is zoned decimal, DISPLAY."""
        return cobol_usage.is_zoned_display(self.usage)

    # These are methods and not properties because each may read the generated artifact,
    # and a property that touches a disk invites a caller to read it in a loop.

    def cite(self) -> str:
        """Where this field comes from, as a line a developer can act on.

        For a dictionary-backed descriptor this is `loader.cite`, the compact three-
        locator provenance string, surfaced rather than reimplemented.

        Returns:
            The provenance line for this field.
        """
        if self.dictionary_key is not None:
            return loader.cite(self.dictionary_key)
        # Guaranteed non-None by the __post_init__ invariant.
        return str(self.source_locator)

    def drift(self, *, path: Path | None = None) -> Drift | None:
        """How the three layer views of this field disagree, unadjudicated.

        A PASS-THROUGH of `loader.drift_for` and nothing else. It is not reduced to a
        boolean, not summarised as "safe", and not acted upon.

        Args:
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The `Drift` object the artifact holds, with its per-aspect flags and its
                human-readable details, or None for a program-local descriptor, which
                has one layer only and so cannot disagree with itself.
        """
        if self.dictionary_key is None:
            return None
        return loader.drift_for(self.dictionary_key, path=path)

    def anomaly_refs(self, *, path: Path | None = None) -> tuple[str, ...]:
        """Return the anomaly register entries this field takes part in.

        Each is `A-` and a number from 1 to 22, keying the anomaly log.

        Args:
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The references, in the artifact's own order, or an empty tuple for a
                program-local descriptor.
        """
        if self.dictionary_key is None:
            return ()
        return loader.get_entry(self.dictionary_key, path=path).anomaly_refs

    def ambiguity_refs(self, *, path: Path | None = None) -> tuple[str, ...]:
        """Return the open semantic questions that bear on this field.

        Each is `Q-` and a number, keying the ambiguity register - a question that
        reading the frozen source cannot settle and that the compiled program must
        arbitrate (rule R-6).

        Args:
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The references, in the artifact's own order, or an empty tuple for a
                program-local descriptor.
        """
        if self.dictionary_key is None:
            return ()
        return loader.get_entry(self.dictionary_key, path=path).ambiguity_refs


    def store(
        self,
        value: decimal.Decimal | int | str,
        *,
        rounding: str = TRUNCATING_STORE,
    ) -> decimal.Decimal | int | str:
        """Store a value into a field of this description and return it.

        A pure delegation to `usage.coerce`, passing this descriptor's own components.
        It holds no logic of its own, and it exists because Agent Action Plan section
        0.3.3 has the arithmetic and `MOVE` layers take "a descriptor and a value".

        Args:
            value: The value to store, as `decimal.Decimal`, `int` or `str`. Never a
                binary float (rule R-2).
            rounding: The direction the store takes. Truncation toward zero by default,
                because that is what an un-ROUNDED COBOL store does.

        Returns:
            What the field now holds, on the carrier `python_storage` names.
        """
        return cobol_usage.coerce(
            value,
            usage=self.usage,
            digits=self.digits,
            scale=self.scale,
            character_length=self.character_length,
            signed=self.signed,
            unsigned=self.unsigned,
            sign_position=self.sign_position,
            rounding=rounding,
        )


    @classmethod
    def from_dictionary_key(
        cls, key: str, *, path: Path | None = None
    ) -> FieldDescriptor:
        """Build the descriptor the generated dictionary holds for one key.

        The only factory, and the one every record module takes.

        Args:
            key: A qualified entry key - `<TABLE-NAME>.<COLUMN-NAME>`, `<COPYBOOK-
                RECORD>.<FIELD-NAME>` or `<PROGRAM-RECORD>.<FIELD-NAME>`, exact and
                case-sensitive, with the `#` declaration-line segment where the artifact
                carries one.
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The descriptor for that field.

        Raises:
            loader.DictionaryKeyError: No entry is keyed so.
            BridgeOnlyFieldError: The entry has neither a copybook view nor a program-
                source view, so the field has no COBOL-side storage to describe.
        """
        return _memoised_descriptor(key, path)


# There was a second factory above, `for_working_storage`, which minted a descriptor for
# a declared field from a `<path>:L<n>` locator with no dictionary key.


def _require_dictionary_provenance(
    entry: DictionaryEntry, declaring: CopybookField
) -> None:
    """Refuse an entry that does not carry the provenance a dictionary entry carries.

    The citation checks in particular are not decoration. A malformed or escaping
    locator is a citation a reader cannot follow, and a citation nobody can follow is
    the same as no traceability at all.

    Args:
        entry: The entry a descriptor is about to be composed from.
        declaring: Its DECLARING COBOL view, already known to be present - the copybook
            view where the entry has one, and the program-source view otherwise.

    Raises:
        UntrustedEntryError: The entry's key, citation, presence block or one of its
            vocabulary members is not what a dictionary-derived entry carries.
    """
    if ENTRY_KEY_PATTERN.match(entry.key) is None:
        raise UntrustedEntryError(
            f"{entry.key!r} is not a dictionary entry key: an entry key is "
            "<TABLE-NAME>.<COLUMN-NAME> or <COPYBOOK-RECORD>.<FIELD-NAME>, "
            "optionally with a #<n> tail where a field name repeats inside one "
            "record. A descriptor is only dictionary-backed if the entry it "
            "came from is one the generated artifact carries (rule R-5)."
        )

    # The presence block is what every consumer tests before reading a view, so a flag
    # that disagrees with the view beside it is the one inconsistency that reliably
    # produces a confidently wrong answer rather than an error.
    if not (entry.presence.in_copybook or entry.presence.in_program_source):
        raise UntrustedEntryError(
            f"{entry.key!r} carries a declaring COBOL view while its presence "
            "block says it has neither a copybook nor a program-source one. "
            "The generator sets each flag from the view it belongs to, so "
            "they cannot disagree in the committed artifact; an entry in which "
            "they do was not derived from it."
        )

    if REPO_PATH_PATTERN.match(declaring.file) is None:
        raise UntrustedEntryError(
            f"{entry.key!r} cites the declaring file {declaring.file!r}, "
            "which is not a contained repository-relative path. A citation "
            "that could point outside the repository is one a reader cannot "
            "check, "
            "and checkable citations are the whole of rule R-5."
        )

    if SOURCE_LOCATOR_PATTERN.match(declaring.source) is None:
        raise UntrustedEntryError(
            f"{entry.key!r} cites {declaring.source!r}, which is not a "
            "contained <path>:L<n> locator. Every descriptor must lead a "
            "reader to the frozen line that declares the field (rule R-5)."
        )

    # A dataclass annotation is not a runtime guarantee.
    for label, value, vocabulary in (
        ("cobol_python_storage", entry.cobol_python_storage, CobolPythonStorage),
        ("declaring.usage", declaring.usage, Usage),
        ("declaring.usage_declared_at", declaring.usage_declared_at,
         UsageDeclaredAt),
        ("declaring.sign_position", declaring.sign_position, SignPosition),
    ):
        if not isinstance(value, vocabulary):
            raise UntrustedEntryError(
                f"{entry.key!r} carries {label}={value!r}, which is not a "
                f"member of {vocabulary.__name__}. The artifact records only "
                "members of these vocabularies, so an entry carrying anything "
                "else was not derived from it."
            )


def _descriptor_from_entry(entry: DictionaryEntry) -> FieldDescriptor:
    """Compose a descriptor from the DECLARING COBOL view of one entry.

    The declaring view is the copybook view where the entry has one, and the program-
    source view otherwise - the work-file records the General Ledger programs declare
    inline in their own FILE SECTIONs.

    Args:
        entry: The entry to describe.

    Returns:
        The descriptor for its declaring COBOL view.

    Raises:
        BridgeOnlyFieldError: The entry has neither a copybook view nor a program-source
            view, so nothing in COBOL declares it.
        UntrustedEntryError: The entry does not carry dictionary provenance.
    """
    copybook = (
        entry.copybook if entry.copybook is not None else entry.program_source
    )
    if copybook is None:
        raise BridgeOnlyFieldError(_bridge_only_message(entry))
    _require_dictionary_provenance(entry, copybook)
    return FieldDescriptor(
        name=copybook.name,
        usage=copybook.usage,
        usage_declared_at=copybook.usage_declared_at,
        usage_inherited_from=copybook.usage_inherited_from,
        picture=copybook.picture,
        signed=copybook.signed,
        sign_position=copybook.sign_position,
        sign_clause_text=copybook.sign_clause_text,
        digits=copybook.digits,
        integer_digits=copybook.integer_digits,
        scale=copybook.scale,
        character_length=copybook.character_length,
        unsigned=_declared_unsigned(copybook),
        # Neither an in-scope copybook nor an inline work-file record declares a
        # numeric-edited picture.
        is_edited=False,
        occurs=copybook.occurs,
        redefines=copybook.redefines,
        is_filler=copybook.is_filler,
        is_group=copybook.is_group,
        parent_group=copybook.parent_group,
        # The artifact governs the carrier - for a work-file field exactly as for a
        # column-backed one, because the generator applies one rule to the declaring
        # view whichever view that is.
        python_storage=entry.cobol_python_storage,
        dictionary_key=entry.key,
        source_locator=copybook.source,
    )


def _declared_unsigned(copybook: CopybookField) -> bool:
    """Whether the declaration carries the explicit UNSIGNED keyword.

    Derived BY COMPARISON, never from a list of known cases: a binary-family item
    declared without a sign is an item whose declaration said UNSIGNED, because the
    family is signed by default.

    Args:
        copybook: The copybook view to inspect.

    Returns:
        True when the explicit keyword is present.
    """
    return cobol_usage.is_binary_family(copybook.usage) and not copybook.signed


def _bridge_only_message(entry: DictionaryEntry) -> str:
    """Explain why an entry with no declaring COBOL view has no descriptor.

    Args:
        entry: The entry that lacks both a copybook and a program-source view.

    Returns:
        A message naming the entry, what does declare it, and where to look instead.
    """
    declared_by = []
    if entry.presence.in_bridge:
        declared_by.append("the bridge host-variable group")
    if entry.presence.in_column:
        declared_by.append("the MySQL schema")
    where = " and ".join(declared_by) if declared_by else "no source"

    # Built as a list of finished sentences, each parenthesised, so that no fragment can
    # join the wrong neighbour through implicit concatenation.
    opening = (
        f"{entry.key!r} has no copybook view and no program-source view, so "
        f"it has no COBOL-side storage for a FieldDescriptor to describe: "
        f"it is "
        f"declared by "
        f"{where} only, and the artifact holds its Python carrier as "
        f"{entry.cobol_python_storage.value}."
    )
    closing = (
        "Reproducing that derivation belongs to the handler module at the "
        "bridge boundary, not here. For the bridge view use "
        "loader.host_variable_for; for the rule that populates it use "
        "loader.derivation_for."
    )
    sentences = [opening]
    if entry.derivation is not None:
        guard = (
            f", guarded by {entry.derivation.guard!r}"
            if entry.derivation.guard
            else ""
        )
        sentences.append(
            f"Its value is derived at the bridge by "
            f"{entry.derivation.expression!r} "
            f"[{entry.derivation.source}]{guard}."
        )
    sentences.append(closing)
    return " ".join(sentences)


@functools.cache
def _memoised_descriptor(key: str, path: Path | None) -> FieldDescriptor:
    """Look one entry up and describe it, at most once per key and path.

    `functools.cache` is the modern spelling of `functools.lru_cache` with no size
    limit, and it is unbounded here on purpose: the key domain is bounded by the
    artifact, which holds 1061 entries, so the cache cannot grow beyond the dictionary
    itself.

    Args:
        key: The entry key.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The descriptor for that key.
    """
    return _descriptor_from_entry(loader.get_entry(key, path=path))


def descriptors_for_table(
    table: str, *, path: Path | None = None
) -> tuple[FieldDescriptor, ...]:
    """Describe every COBOL-side field of one table, in the artifact's order.

    Thin over `loader.entries_for_table`, which yields column-mapped entries in column
    ordinal order with copybook-only entries after them. That order is passed straight
    through and never re-sorted.

    Args:
        table: The table name as the schema spells it, for example `"GLLEDGER-REC"`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The descriptors, in the loader's documented order.

    Raises:
        loader.DictionaryLookupError: No such table, with near misses listed.
    """
    return tuple(
        _descriptor_from_entry(entry)
        for entry in loader.entries_for_table(table, path=path)
        if entry.copybook is not None
    )


def descriptors_for_copybook_record(
    record: str, *, path: Path | None = None
) -> tuple[FieldDescriptor, ...]:
    """Describe every field of one copybook record, in declaration order.

    Thin over `loader.entries_for_copybook_record`. Declaration order is the copybook's
    own and is passed through unchanged, which matters because a record's field order is
    its byte layout.

    Args:
        record: The 01-level record name with the copybook's own casing, for example
            `"WS-Ledger-Record"`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The descriptors, in copybook declaration order.

    Raises:
        loader.DictionaryLookupError: No such record, with near misses listed.
    """
    return tuple(
        _descriptor_from_entry(entry)
        for entry in loader.entries_for_copybook_record(record, path=path)
        if entry.copybook is not None
    )
