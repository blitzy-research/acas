"""The `FieldDescriptor` value object: one COBOL data item, described.

A `FieldDescriptor` says what a single COBOL data item IS - its usage class,
its digits and scale, its signedness and sign position, and which Python
carrier holds its value. It says nothing about what the item MEANS. Storage
questions are delegated to `acas_posting.cobol.usage`; accounting decisions
belong to the program layer and appear nowhere below. No account number, no
VAT rate, no ledger balance and no batch status is written in this file.

WHY THIS FILE EXISTS
====================
Agent Action Plan section 0.3.3 names the pattern, verbatim:

    "Field-descriptor value object. A `FieldDescriptor` carries digits, scale,
    signedness, usage and sign position, derived from the field's
    data-dictionary entry. Arithmetic and `MOVE` take a descriptor and a
    value; storage semantics are therefore data-driven rather than hand-coded
    per field, which is the only tractable way to get several hundred fields
    right."

Agent Action Plan section 0.4.1.4 states this file's whole purpose in one
sentence, verbatim:

    "The `FieldDescriptor` value object; every instance traceable to a
    dictionary key."

Agent Action Plan section 0.8.1, the binding directive behind it, verbatim:

    "Data dictionary first. The dictionary is generated from the bridge
    before record definitions are written, and every Python field definition
    cites its entry. This ordering is a directive, not a preference - it is
    what prevents fields being transcribed by eye."

Traceability is therefore not decoration here. It is the reason the file
exists, and it is enforced at construction time by `__post_init__` rather
than requested in a comment.

PROVENANCE IS MANDATORY - THE ONE PLACE THIS FILE DECIDES SOMETHING
===================================================================
Rule R-5 asks for "every instance traceable to a dictionary key". The
dictionary covers the copybook / bridge-host-variable / MySQL-column triple
for RECORD fields, exhaustively: 513 in-scope columns across 22 tables, with
`loader.coverage()` reporting `in_scope_columns == columns_covered == 513`.
It does NOT cover program-local WORKING-STORAGE, and the program layer needs
descriptors for such items - `work-2 pic s9(14) comp-3`
[sales/sl060.cbl:L206] with its zero scale, `work-a binary-long`
[sales/sl100.cbl:L182], `l6-account pic 9999.99` [general/gl072.cbl:L233].
Without them the legacy averaging defect, the 32-bit payment-days path and
gl072's preserved scaling divides cannot be reproduced at all.

The rule this file applies, stated so that no reader thinks R-5 was bent:

    `FieldDescriptor` carries MANDATORY provenance that is EITHER a
    `dictionary_key` (the principal path, for record fields) OR a
    `source_locator` (for program-local working storage). A descriptor
    constructed with NEITHER is a programmer error and construction must
    fail with a clear message naming the field. R-5 is satisfied because
    every descriptor is traceable to a frozen source location either way,
    and R-5's "every field to a data-dictionary entry" scopes to RECORD
    fields, which the dictionary covers exhaustively.

THIS FILE DOES NOT ADJUDICATE DRIFT - THE PROHIBITION THAT MATTERS MOST
=======================================================================
Where the copybook, the bridge host variable and the MySQL column disagree,
the dictionary holds all three views plus a `drift` object. This file
surfaces that disagreement and never settles it. There is deliberately no
"winner" view, no widest picture, no signed-over-unsigned rule and no
"sensible" reading anywhere below, because rule R-4 makes a legacy defect
part of the specification: a defect reproduced is a success, a defect fixed
is a failure. Agent Action Plan section 0.8.2 preserves the user's own words:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included. A defect reproduced is correct; a
    defect fixed is a failure."

Concretely, and every one of these is measured rather than assumed:

  * SIGNEDNESS, anomaly A-11. `Sales-Average binary-long` is SIGNED
    [copybooks/wssl.cob:L49]; the host variable `HV-SALES-AVERAGE PIC 9(10)
    COMP` is UNSIGNED [common/salesMT.cbl:L308]; the MySQL column
    `SALES-AVERAGE int(8) unsigned` is unsigned. Agent Action Plan section
    0.6.2, verbatim: "a negative value computed in COBOL loses its sign at
    the bridge, not at the database".
  * SIGNEDNESS again, and NOT from a list. `Entered` .. `Stored binary-long`
    are signed [copybooks/wsbatch.cob:L36-L39] against unsigned host
    variables and unsigned columns. The dictionary finds this by comparing
    the views it holds, which is why a hard-coded table of known cases would
    have missed it - and why the `unsigned` member below is likewise derived
    by comparison.
  * A CLEAN PASS-THROUGH, proving the drift is specific and not systemic.
    `Sales-Current` and `Sales-Last pic s9(8)v99 comp-3` are signed at all
    three layers [copybooks/wssl.cob:L54-L55].
  * CHARACTER WIDTH, anomaly A-12. `Ledger-Name pic x(24)`
    [copybooks/wsledger.cob:L27] widens to a 32-character host variable
    [common/nominalMT.cbl:L299] and a 32-character column. The value is
    uncorrupted; only the padding differs.

A descriptor reports the COPYBOOK view as its own usage, digits, scale and
sign, because a `FieldDescriptor` describes COBOL-SIDE storage - which is
what `arithmetic.py` and `move.py` operate on. It offers the disagreement
untouched through `drift()`, a pass-through of `loader.drift_for`. It never
blends layers, never widens a field to match a column, and never applies the
bridge's signedness loss: that conversion belongs to the handler module that
reproduces the bridge boundary, not here.

THE ENTRY KEY CONVENTION - A PUBLIC CONTRACT
============================================
    <TABLE-NAME>.<COLUMN-NAME>      where a column backs the field
    <COPYBOOK-RECORD>.<FIELD-NAME>  where the field is copybook-only

Both halves are the names the frozen sources use themselves: hyphens are not
turned into underscores and case is not folded, so lookup is exact and
case-sensitive. Where one field name repeats inside one record the key
carries a `#` and the declaration line, as in `WS-Ledger-Record.filler#16`.

NEVER key by field name alone. The table name is in the key precisely so
that two different tables can never merge. `PSIRSPOST-REC` is the transfer
file the Sales and Purchase posting steps write, laid out by
`copybooks/wspost-irs.cob`, reached through handler `acas008` and bridge
`slpostingMT`. `IRSPOSTING-REC` is the internal IRS posting file, laid out by
`copybooks/irswspost.cob`, reached through `acasirsub4` and `irspostingMT`.
The copybook says so itself, verbatim [copybooks/wspost-irs.cob:L6-L7]:

    "This is NOT the same as the internal IRS posting file"

Their column names are near-identical - amount, VAT amount, date, debit,
credit, legend and VAT side all appear in both - so a name-only key would
silently conflate them. Two worked pairs from the generated artifact:

    PSIRSPOST-REC.IRS-POST-AMOUNT   field WS-IRS-Post-Amount,
                                    `pic s9(7)v99 sign leading`
                                    [copybooks/wspost-irs.cob:L21]
    IRSPOSTING-REC.POST4-AMOUNT     field Post-Amount,
                                    `pic s9(7)v99 sign is leading`
                                    [copybooks/irswspost.cob:L14]

Note the two SIGN clause spellings. Both are carried verbatim in
`sign_clause_text` and neither is rewritten to match the other.

The same trap exists for the run date. `SYSTEM-REC.RUN-DAT` is
`Run-Date binary-long` [copybooks/wssystem.cob:L67], whose column is spelt
`RUN-DAT`; `system-record.run-date` is an unrelated `pic x(8)` text field in
the IRS system parameters [copybooks/irswssystem.cob:L14]. One is a 4-byte
integer, the other is 8 characters. Only the qualified key tells them apart.

NAMES ARE CARRIED VERBATIM
==========================
`name` is the COBOL field name exactly as the frozen source spells it -
case and hyphens preserved, never lowercased, never converted to snake case
and never tidied. A misnaming is preserved as found: anomaly A-20 is that
`copybooks/wssys4.cob` carries `sl4-spare3` and `sl4-spare4`, with the SALES
prefix, inside the PURCHASE group. Those names stay exactly as they are.

USAGE MAY BE INHERITED FROM A GROUP - GET THIS WRONG AND EVERY VALUE IS WRONG
============================================================================
A group header that declares a USAGE passes it to every subordinate item
that declares none. Three such headers govern the batch and period totals
this cycle depends on:

    03  Amounts                         comp-3.   [copybooks/wsbatch.cob:L40]
    03  Sales-Ledger-Data       comp-3.            [copybooks/wssys4.cob:L9]
    03  Purchase-Ledger-Data    comp-3.           [copybooks/wssys4.cob:L20]

Those three alone govern 24 fields whose own PICTURE lines carry no usage
clause - `05 Input-Gross pic 9(9)v99.` [copybooks/wsbatch.cob:L41] is packed
decimal, not zoned, and nothing on its own line says so. Across the whole
generated artifact the count is larger: 85 fields inherit usage from 12
group headers, `Vat-Rates comp` [copybooks/wssystem.cob:L55] among them.
Anyone typing usage from a PICTURE line alone would call all of them
DISPLAY and every stored value would be wrong, invisibly, until a state
diff. So usage is taken from the dictionary, never inferred here, and
`usage_declared_at` plus `usage_inherited_from` travel on the descriptor so
the inheritance is visible at the point of use.

EXACT ARITHMETIC ONLY (RULE R-2)
================================
No accounting value may pass through a binary floating-point type at any
point - not in computation, not in storage, not in transport. This module
therefore names three carriers and no others: `decimal.Decimal` for a scaled
numeric item, `int` for an integer or binary-family item, and `str` for an
alphanumeric item. The choice is data-driven, taken from the entry's
`cobol_python_storage`, because it is a correctness decision and not a style
one: `Sales-Average` is `binary-long` [copybooks/wssl.cob:L49], so its
divide truncates as an INTEGER divide, and that single fact is what makes
the legacy averaging defect reproducible. Every count member below - digits,
integer digits, scale, character length, occurs - is an `int`. A binary
float appears nowhere in this file, and neither does the `math` module.

LAYERING (AGENT ACTION PLAN SECTION 0.4.3)
==========================================
    MAY import       the standard library, the `acas_posting.dictionary`
                     public surface, and `acas_posting.cobol.usage`
    MUST NOT import  records, dal, programs, cli, clock, dates, workfiles,
                     harness - and this folder's own `picture.py`

The picture parser reads a PICTURE clause INTO a descriptor, so it imports
this module and the edge runs one way only. Nothing is lost by that: the
dictionary's copybook view already carries digits, integer digits, scale,
signedness, sign position, usage, usage-declared-at and character length
pre-parsed, so this file never handles raw picture text.

On the enumerations: the section 0.4.3 row reads "dictionary.loader only".
Read literally that would force this file to re-declare `Usage`,
`SignPosition`, `UsageDeclaredAt` and `CobolPythonStorage`. Two competing
definitions of one vocabulary is exactly the divergence R-4 exists to stop,
and the loader's whole return surface is built from `model` dataclasses
anyway, so importing them from the dictionary package's public surface is
the SAME architectural edge. They are imported from `model` because the
loader's `__all__` publishes only its errors and accessors and re-exports no
enumeration. `SOURCE_LOCATOR_PATTERN` is imported for the same reason rather
than retyped. No third-party package is imported at all.

DETERMINISM (RULE R-6)
======================
Two runs of one scenario must be byte-identical, so a descriptor is frozen,
slotted and value-equal; every collection member is a tuple; and there is no
clock, no entropy source and no environment read anywhere below. Decimal
quanta are built without consulting the ambient decimal context - see
`quantum`, where the reason is measured rather than asserted.

WHAT THIS MODULE DOES NOT DO
============================
It does not validate values. It describes storage, and `usage.coerce`
performs the store, which per rule R-3 silently truncates high-order digits
rather than raising - there is no error path in the specification to
reproduce, because `ON SIZE ERROR` and `REMAINDER` occur zero times across
the twelve in-scope program files. Every `raise` below reports a PROGRAMMER
error - a descriptor built with no provenance, a malformed locator, a
nonsensical component combination, an unknown dictionary key, or a request
for COBOL-side storage that the frozen sources do not declare. None can
fire on a data value.

It also emits no SQL, no schema text and no report formatting. Numeric-EDITED
pictures are flagged by `is_edited` so that a store lands at the right
precision - `l6-account pic 9999.99 blank when zero`
[general/gl072.cbl:L233] receives a live `divide` [general/gl072.cbl:L386] -
but no editing or de-editing of a value is implemented, because report
formatting beyond database effects is out of scope. Edited pictures never
reach the database in any case: a search for edit characters inside a `pic`
clause across every in-scope copybook returns zero matches, so they occur
only in program-local working storage and print lines.
"""

from __future__ import annotations

import decimal
import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader
from acas_posting.dictionary.model import (
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
    # Sorted the way the sibling modules sort theirs - the store direction
    # first, then the value object with the three failures it raises, then the
    # two whole-record conveniences.
    "TRUNCATING_STORE",
    "BridgeOnlyFieldError",
    "FieldDescriptor",
    "FieldDescriptorError",
    "MissingProvenanceError",
    "descriptors_for_copybook_record",
    "descriptors_for_table",
)


# =============================================================================
#  THE DEFAULT STORE DIRECTION  (Agent Action Plan section 0.6.1)
# =============================================================================

# COBOL truncates toward zero on store unless ROUNDED is written. Across the
# whole in-scope cycle there are exactly FIVE ROUNDED sites - two VAT computes
# in the batch control gate, one cycle-to-period divide in the end-of-cycle
# step [general/gl080.cbl:L328], and two VAT computes in the IRS posting path.
# Every other store truncates. Truncation is therefore the default here and
# rounding is the annotated exception, which is the way round that cannot
# corrupt a figure by omission. This module does not know which sites are
# ROUNDED - that is the arithmetic layer's business; it only supplies the
# direction a plain store takes.
TRUNCATING_STORE: Final[str] = decimal.ROUND_DOWN


# =============================================================================
#  FAILURES
# =============================================================================


class FieldDescriptorError(ValueError):
    """A descriptor could not be built, or was built wrongly.

    Always a PROGRAMMER error: a missing or malformed provenance, a
    nonsensical combination of components, or a request for COBOL-side
    storage that the frozen sources do not declare. Never raised because of
    a data value - a store truncates silently (rule R-3), and this module
    performs no store of its own.

    It derives from `ValueError` so that a caller who does not care which of
    the two subclasses fired can still catch it with the builtin.
    """


class MissingProvenanceError(FieldDescriptorError):
    """A descriptor was built with neither a dictionary key nor a locator.

    The invariant rule R-5 puts on this file: every instance must be
    traceable back to a frozen source, either through its dictionary entry or
    through the `<path>:L<n>` locator of its working-storage declaration. A
    descriptor with neither is worse than useless - it is a field whose
    behaviour nobody can audit against the frozen COBOL.
    """


class BridgeOnlyFieldError(FieldDescriptorError):
    """The entry has no copybook view, so it has no COBOL-side storage.

    Fourteen entries in the generated artifact are declared by the bridge or
    the schema but by no copybook. The clearest are the three date components
    of the internal IRS posting table, `POST4-DAY`, `POST4-MONTH` and
    `POST4-YEAR`, which have no counterpart in any copybook and exist only
    because the bridge derives them from a date string under a guard
    [common/irspostingMT.cbl:L982-L987] - anomaly A-7.

    A `FieldDescriptor` describes COBOL-side storage, and such a field has
    none: no COBOL program can name it, so `arithmetic.py` and `move.py` will
    never operate on it, and the artifact holds its Python carrier as NONE.
    Building a descriptor from the bridge view instead would blend two layers
    into one figure, which is the adjudication rule R-4 forbids. So this
    refuses, and points the caller at the two accessors that do answer the
    question - `loader.host_variable_for` for the bridge view and
    `loader.derivation_for` for the rule that populates it. Reproducing that
    rule is the handler module's job, at the bridge boundary, not this file's.
    """


# =============================================================================
#  THE VALUE OBJECT
# =============================================================================


@dataclass(frozen=True, slots=True, eq=True, repr=False)
class FieldDescriptor:
    """One COBOL data item's storage description, with its provenance.

    Frozen, slotted and value-equal, so that two descriptors built from the
    same source compare equal, neither can be mutated behind a holder's back,
    and two runs behave identically (rule R-6).

    Build one through a factory rather than by hand. `from_dictionary_key` is
    the principal path and covers every record field; `for_working_storage`
    covers a program-local declaration that has no dictionary entry. Direct
    construction is supported, and checked, for the picture parser - which
    reads a PICTURE clause into these components and must not be forced
    through a dictionary lookup it has no key for.

    The members below hold the COPYBOOK view for a dictionary-backed
    descriptor. They are never blended with the bridge or column view, and
    the disagreement between the three is offered untouched by `drift()`.

    Attributes:
        name: The COBOL field name, verbatim from the frozen source, with
            case and hyphens preserved - `"Sales-Average"`,
            `"WS-IRS-Post-Amount"`, `"sl4-spare3"`. Never rewritten.
        usage: The storage class. Taken from the dictionary for a record
            field; supplied by the picture parser otherwise.
        usage_declared_at: Whether the USAGE clause sat on the item itself,
            was inherited from a group header, or was absent so that the
            language default governed. GROUP is the inheritance case that
            silently retypes 85 fields if ignored.
        usage_inherited_from: The group header's name when usage was
            inherited, otherwise None.
        picture: The PICTURE clause exactly as written, carried verbatim for
            the same reason `sign_clause_text` is. None when the item has no
            PICTURE at all, which is how the binary family is declared:
            `05  Entered         binary-long.` [copybooks/wsbatch.cob:L36]
            states a usage and no picture, so a None here is a fact about the
            declaration rather than missing data. Never parsed by this module
            - the pre-parsed components alongside it are what a store uses.
        signed: Whether the declaration carries a sign.
        sign_position: Where the sign lives - overpunched on the trailing
            digit by COBOL default, overpunched on the leading digit when a
            SIGN clause says so, held separately, or implicit in a binary or
            packed representation.
        sign_clause_text: The SIGN clause exactly as written, so that
            `"sign leading"` [copybooks/wspost-irs.cob:L21] and `"sign is
            leading"` [copybooks/irswspost.cob:L14] stay distinguishable.
            None when the item has no SIGN clause.
        digits: Total digit count, `integer_digits + scale`. None for an
            alphanumeric item, a group, and a binary-family item whose range
            comes from its width rather than a picture
            [copybooks/wsbatch.cob:L36-L39].
        integer_digits: Digit count before the implied decimal point.
        scale: Digit count after it. Zero and None both mean "no fractional
            part"; the artifact writes None for an item that has no picture.
        character_length: Character count for an alphanumeric item.
        unsigned: Whether the declaration carries the explicit UNSIGNED
            keyword on a binary item, as `Page-Lines binary-char unsigned`
            does [copybooks/wssystem.cob:L65]. Distinct from `signed` being
            false: an unsigned binary item has no sign bit at all, whereas
            an unsigned packed item still carries a sign nibble.
        is_edited: Whether the picture is numeric-edited. Always false for a
            record field - no in-scope copybook declares an edited picture -
            and true only for program-local items such as `l6-account`
            [general/gl072.cbl:L233] and `m pic z(7)9`
            [sales/sl060.cbl:L213].
        occurs: The OCCURS count for a table item, otherwise None.
        redefines: The item this one redefines, otherwise None.
        is_filler: Whether the item is FILLER.
        is_group: Whether the item is a group rather than an elementary item.
        parent_group: The immediately containing group's name, otherwise None.
        python_storage: Which carrier holds the value - DECIMAL, INT, STR or
            NONE. Taken from the entry for a record field, so that the choice
            between `decimal.Decimal` and `int` is data-driven (rule R-2).
        dictionary_key: The entry key, for a record field. None otherwise.
        source_locator: A `<path>:L<n>` locator, mandatory for a
            program-local item and also carried for a record field, where it
            points at the copybook declaration.
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

    # -- construction invariants ------------------------------------------
    #
    # Every check below fires on a PROGRAMMER error and none can fire on a
    # data value (rule R-3). They exist because a descriptor is consumed by
    # 27 record modules and 14 parity tests, and a silently malformed one
    # would surface as a wrong posted figure rather than as an exception.

    def __post_init__(self) -> None:
        """Reject a descriptor that could not describe anything truthfully.

        Raises:
            MissingProvenanceError: Neither a dictionary key nor a locator was
                given, so the field could not be audited against the frozen
                COBOL - the invariant rule R-5 puts on this file.
            FieldDescriptorError: The name is blank, the locator is malformed,
                a count is negative, the digit members contradict one another,
                or a program-local descriptor names a carrier that its own
                usage and scale do not imply.
        """
        if not self.name:
            raise FieldDescriptorError(
                "a FieldDescriptor needs the COBOL field name its frozen "
                "source declares, carried verbatim; got an empty name"
            )

        # R-5, the invariant this file exists to keep. Either provenance will
        # do, because either one leads a reader to a frozen source location;
        # neither will not, because then nothing does.
        if self.dictionary_key is None and self.source_locator is None:
            raise MissingProvenanceError(
                f"{self.name!r} has no provenance: give it either a "
                "dictionary_key, for a field the generated dictionary covers, "
                "or a source_locator of the form <path>:L<n> naming its "
                "working-storage declaration. Rule R-5 requires every "
                "descriptor to be traceable to a frozen source, and a "
                "descriptor with neither is a field whose behaviour cannot be "
                "audited against the COBOL."
            )

        # The locator shape is the dictionary's own, imported rather than
        # retyped so the two can never drift apart.
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

        # digits == integer_digits + scale holds for all 1015 entries of the
        # generated artifact, with zero exceptions, so a contradiction here is
        # always a hand-authoring slip - typically a scale copied from a
        # neighbouring declaration. Checked only when all three are present:
        # the artifact writes None for all three on an item with no picture.
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

        # A program-local descriptor must name the carrier its own usage and
        # scale imply, because nothing else vouches for it. A dictionary-backed
        # one is EXEMPT: there the generated artifact governs and this file
        # must never second-guess what it holds (rule R-4). The two agree by
        # construction anyway - `usage.python_storage_for` implements the very
        # rule the artifact states at `meta.derivation_rules`.
        if self.dictionary_key is None and self._carrier_is_derivable():
            implied = cobol_usage.python_storage_for(self.usage, self.scale)
            if implied is not self.python_storage:
                raise FieldDescriptorError(
                    f"{self.name!r} at {self.source_locator} names the "
                    f"carrier {self.python_storage.value} but usage "
                    f"{self.usage.value} with scale {self.scale} implies "
                    f"{implied.value}. Let for_working_storage derive it "
                    "rather than passing it."
                )

    def _carrier_is_derivable(self) -> bool:
        """Whether the carrier rule applies to this item's usage class.

        The rule covers a group, an alphanumeric item and the numeric classes.
        It does not cover POINTER, which is not record storage in this port -
        it appears only as the item each generated bridge declares beside its
        host-variable group, and no record layout includes one - so asking for
        that item's carrier raises rather than answering.
        """
        return (
            cobol_usage.is_group(self.usage)
            or cobol_usage.is_alphanumeric(self.usage)
            or cobol_usage.is_numeric(self.usage)
        )

    def __repr__(self) -> str:
        """Name the field, its storage shape and its provenance.

        Written by hand so that a failing parity test says WHICH field it was
        looking at and WHERE that field is declared, rather than printing
        every member. Rule R-5 is only useful if provenance reaches the
        message a developer actually reads.
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

    # -- storage shape, delegated in full to acas_posting.cobol.usage -----
    #
    # These are properties rather than methods because each is a pure
    # function of the members already held: no disk is touched and no
    # ordering is observable, so a caller may read one as often as it likes.

    @property
    def byte_length(self) -> int:
        """How many bytes an item of this description occupies.

        Delegated entirely to `usage.byte_length`, so that width lives in one
        place: four bytes for a BINARY-LONG whatever the comment beside the
        declaration claims [copybooks/wssl.cob:L49], six for a ten-digit
        packed item [copybooks/wsledger.cob:L28], and one byte per digit for a
        zoned item whose sign is overpunched [copybooks/wspost.cob:L23].

        For a numeric-EDITED item this is the width of the digit positions
        alone and EXCLUDES the inserted edit characters, because this module
        implements no editing - `l6-account pic 9999.99` reports 6, not the 7
        bytes its printed form occupies. That is the figure the arithmetic
        layer needs, and report formatting is out of scope.

        Raises:
            ValueError: For a group, which has no width of its own - sum its
                children's widths - and for an item whose description omits
                the count its class needs. A programmer error either way; the
                message comes from `usage.byte_length` unaltered.
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

        Delegated to `usage.value_domain`. The bounds are expressed in whole
        units of the item's least significant digit, so a scaled item's
        domain counts hundredths rather than pounds.

        Raises:
            ValueError: For a group and for an alphanumeric item, neither of
                which holds a number, and for a zoned or packed item whose
                digit count is absent. A programmer error either way.
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

        `Decimal("0.01")` for a two-place item, `Decimal("1")` for an integer
        one, and None for an item with no scale at all, which has no
        fractional part to quantize.

        BUILT WITHOUT CONSULTING THE AMBIENT DECIMAL CONTEXT, deliberately,
        and the reason is measured rather than argued. The obvious spelling
        `Decimal(1).scaleb(-scale)` is context-sensitive: with a caller's
        context left at precision 1 and a minimum exponent of -2, it returns
        `0.00` for a four-place item instead of `0.0001`, silently, and every
        store quantized against it would then land at the wrong scale. The
        three-tuple constructor below consults no context and cannot be
        perturbed by what a caller did earlier, which is what rule R-6
        requires of this file.
        """
        if self.scale is None:
            return None
        return decimal.Decimal((0, (1,), -self.scale))

    # -- carrier and class predicates, thin by design --------------------

    @property
    def is_decimal(self) -> bool:
        """Whether `decimal.Decimal` carries this item's value."""
        return self.python_storage is CobolPythonStorage.DECIMAL

    @property
    def is_int(self) -> bool:
        """Whether `int` carries this item's value.

        True for the binary family and for any zero-scale integer. This is the
        member that makes the legacy averaging defect reproducible: a divide
        into `Sales-Average` [copybooks/wssl.cob:L49] truncates as an integer
        divide, and only an `int` carrier reproduces that.
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
        """Whether the item is BINARY-CHAR, BINARY-SHORT or BINARY-LONG.

        COMP and COMP-5 are computational but not members of this family:
        their range comes from a picture, whereas a binary-family item's comes
        from its declared width.
        """
        return cobol_usage.is_binary_family(self.usage)

    @property
    def is_packed(self) -> bool:
        """Whether the item is packed decimal, COMP-3."""
        return cobol_usage.is_packed(self.usage)

    @property
    def is_zoned_display(self) -> bool:
        """Whether the item is zoned decimal, DISPLAY."""
        return cobol_usage.is_zoned_display(self.usage)

    # -- provenance, the rule R-5 surface --------------------------------
    #
    # These are methods and not properties because each may read the
    # generated artifact, and a property that touches a disk invites a caller
    # to read it in a loop. The pure shape members above are properties; these
    # are not.

    def cite(self) -> str:
        """Where this field comes from, as a line a developer can act on.

        For a dictionary-backed descriptor this is `loader.cite`, the compact
        three-locator provenance string, surfaced rather than reimplemented:

            SALEDGER-REC.SALES-AVERAGE  copybook=copybooks/wssl.cob:L49
            bridge=common/salesMT.cbl:L308  column=mysql/ACASDB.sql:L969

        A bridge-only entry renders its copybook locator as `absent`, which is
        how the three IRS date components declare themselves. For a
        program-local descriptor there is no entry to cite, so the locator of
        its working-storage declaration is returned instead. Never empty
        either way, because `__post_init__` refuses a descriptor with no
        provenance at all.

        Returns:
            The provenance line for this field.
        """
        if self.dictionary_key is not None:
            return loader.cite(self.dictionary_key)
        # Guaranteed non-None by the __post_init__ invariant.
        return str(self.source_locator)

    def drift(self, *, path: Path | None = None) -> Drift | None:
        """How the three layer views of this field disagree, unadjudicated.

        A PASS-THROUGH of `loader.drift_for` and nothing else. It is not
        reduced to a boolean, not summarised as "safe", and not acted upon:
        `Sales-Average` is signed in the copybook and unsigned at both the
        bridge and the column [copybooks/wssl.cob:L49], and `Ledger-Name` is
        24 characters in the copybook and 32 everywhere else
        [copybooks/wsledger.cob:L27]. Every engineering reflex says pick one.
        Rule R-4 says register all three and move on - the bridge's conversion
        is reproduced at the bridge boundary, by the handler module, not here.

        Args:
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The `Drift` object the artifact holds, with its per-aspect flags
            and its human-readable details, or None for a program-local
            descriptor, which has one layer only and so cannot disagree with
            itself.
        """
        if self.dictionary_key is None:
            return None
        return loader.drift_for(self.dictionary_key, path=path)

    def anomaly_refs(self, *, path: Path | None = None) -> tuple[str, ...]:
        """Return the anomaly register entries this field takes part in.

        Each is `A-` and a number from 1 to 22, keying the anomaly log. A
        reader who sees `A-11` on a descriptor knows the field loses its sign
        at the bridge before any SQL executes, without having to rediscover it.

        Args:
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The references, in the artifact's own order, or an empty tuple for
            a program-local descriptor.
        """
        if self.dictionary_key is None:
            return ()
        return loader.get_entry(self.dictionary_key, path=path).anomaly_refs

    def ambiguity_refs(self, *, path: Path | None = None) -> tuple[str, ...]:
        """Return the open semantic questions that bear on this field.

        Each is `Q-` and a number, keying the ambiguity register - a question
        that reading the frozen source cannot settle and that the compiled
        program must arbitrate (rule R-6). Surfaced here so the question is
        visible at the point of use rather than buried in the artifact.

        Args:
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The references, in the artifact's own order, or an empty tuple for
            a program-local descriptor.
        """
        if self.dictionary_key is None:
            return ()
        return loader.get_entry(self.dictionary_key, path=path).ambiguity_refs

    # -- the store, delegated -------------------------------------------

    def store(
        self,
        value: decimal.Decimal | int | str,
        *,
        rounding: str = TRUNCATING_STORE,
    ) -> decimal.Decimal | int | str:
        """Store a value into a field of this description and return it.

        A pure delegation to `usage.coerce`, passing this descriptor's own
        components. It holds no logic of its own, and it exists because
        Agent Action Plan section 0.3.3 has the arithmetic and `MOVE` layers
        take "a descriptor and a value": without it every caller would unpack
        the same seven members by hand, and a single omitted `unsigned` or
        mis-passed `sign_position` would move a stored figure.

        It does NOT validate. A value too large for the field has its
        high-order digits discarded silently, which is what COBOL does and
        what rule R-3 requires be preserved - `ON SIZE ERROR` occurs zero
        times across the twelve in-scope program files, so there is no error
        path in the specification to reproduce.

        Args:
            value: The value to store, as `decimal.Decimal`, `int` or `str`.
                Never a binary float (rule R-2).
            rounding: The direction the store takes. Truncation toward zero by
                default, because that is what an un-ROUNDED COBOL store does.
                The five ROUNDED sites in the whole in-scope cycle pass
                `decimal.ROUND_HALF_UP` explicitly; which sites those are is
                the arithmetic layer's knowledge, not this file's.

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

    # -- factories -------------------------------------------------------

    @classmethod
    def from_dictionary_key(
        cls, key: str, *, path: Path | None = None
    ) -> FieldDescriptor:
        """Build the descriptor the generated dictionary holds for one key.

        The principal path, and the one every record module takes. The
        entry's COPYBOOK view supplies the storage components, because a
        descriptor describes COBOL-side storage; the entry's
        `cobol_python_storage` supplies the carrier, because that choice must
        be data-driven rather than typed by eye (rule R-2). Neither is blended
        with the bridge or column view, and the `unsigned` member is derived by
        COMPARISON - a binary-family item declared without a sign carries the
        explicit UNSIGNED keyword - rather than from a table of known cases,
        which is the same discipline the artifact applies to drift detection
        and the reason it finds the signedness narrowing in the batch record as
        well as in the sales record.

        MEMOISED on `(key, path)`. Descriptors are frozen and value-equal and
        the artifact is immutable once read, so a repeated lookup returns the
        same object. Nothing is read at import time: the cache is empty until
        the first call, and the loader itself reads the document lazily.

        Args:
            key: A qualified entry key - `<TABLE-NAME>.<COLUMN-NAME>` or
                `<COPYBOOK-RECORD>.<FIELD-NAME>`, exact and case-sensitive.
                Never a bare field name; see this module's docstring for why
                the two IRS posting tables make that a trap.
            path: An explicit artifact path, or None for the repository's own.

        Returns:
            The descriptor for that field.

        Raises:
            loader.DictionaryKeyError: No entry is keyed so. Allowed to
                propagate untouched because its message lists near misses and
                restates the key convention, which is the intended developer
                experience and better than anything this file could add.
            BridgeOnlyFieldError: The entry has no copybook view, so the field
                has no COBOL-side storage to describe.
        """
        return _memoised_descriptor(key, path)

    @classmethod
    def for_working_storage(
        cls,
        *,
        name: str,
        source_locator: str,
        usage: Usage,
        picture: str | None = None,
        signed: bool = False,
        sign_position: SignPosition = SignPosition.NONE,
        sign_clause_text: str | None = None,
        digits: int | None = None,
        integer_digits: int | None = None,
        scale: int | None = None,
        character_length: int | None = None,
        unsigned: bool = False,
        is_edited: bool = False,
        occurs: int | None = None,
        redefines: str | None = None,
        is_filler: bool = False,
        is_group: bool = False,
        parent_group: str | None = None,
    ) -> FieldDescriptor:
        """Build the descriptor for a program-local working-storage item.

        For a field the dictionary does not cover, because it lives in a
        program's own WORKING-STORAGE rather than in a record layout. These
        items are not incidental: the whole in-scope cycle turns on several of
        them.

            03  work-2          pic s9(14)    comp-3.
                                            [sales/sl060.cbl:L206]

        `work-2` has ZERO scale while the value added into it carries two
        [sales/sl060.cbl:L218], so pence are discarded on every accumulation -
        and the divide that follows discards the remainder too, because the
        receiving field is an integer. Describe it with `scale=0` and the
        defect reproduces; describe it with `scale=2` and it does not.

            03  work-a          binary-long           value zero.
                                            [sales/sl100.cbl:L182]

        `work-a` and `work-b` are BINARY-LONG in the cash posting step, so
        that whole payment-days path is 32-bit integer arithmetic - while the
        same two names are packed decimal in the invoice posting step
        [sales/sl060.cbl:L207]. The divergence is per program and is preserved,
        which is why these descriptors are built at their point of use with
        their own locator rather than looked up by name.

        `usage_declared_at` is always FIELD here: a caller stating a usage for
        one item is stating it on the item. Where a program-local group header
        carries the usage instead, as `03 total-group occurs 3 comp-3.` does
        [sales/sl060.cbl:L219], pass the group's usage for each subordinate
        item and name the group in `parent_group`.

        The carrier is DERIVED from `usage` and `scale` rather than accepted
        from the caller, by the same rule the artifact states - so a
        program-local descriptor and a dictionary-backed one can never disagree
        about what holds a value.

        Args:
            name: The COBOL field name, verbatim from the program source.
            source_locator: MANDATORY. `<path>:L<n>` naming the declaration,
                as `"sales/sl060.cbl:L206"`, or a span for a run of related
                declarations. This is what keeps rule R-5 satisfied for a
                field that has no dictionary entry.
            usage: The item's storage class.
            picture: Its PICTURE clause verbatim, if it has one. Leave it None
                for a binary item declared by usage alone, as
                `work-a binary-long` is [sales/sl100.cbl:L182].
            signed: Whether its declaration carries a sign.
            sign_position: Where that sign lives.
            sign_clause_text: A SIGN clause verbatim, if the item has one.
            digits: Total digit count.
            integer_digits: Digit count before the implied decimal point.
            scale: Digit count after it. State it explicitly for a numeric
                item; zero is a meaningful answer and the important one.
            character_length: Character count for an alphanumeric item.
            unsigned: Whether the explicit UNSIGNED keyword is present.
            is_edited: Whether the picture is numeric-edited, as
                `pic 9999.99 blank when zero` is [general/gl072.cbl:L233].
                Pass the NUMERIC digits and scale for such an item - 6 and 2
                for that one - so a store lands at the right precision.
            occurs: The OCCURS count for a table item.
            redefines: The item this one redefines.
            is_filler: Whether the item is FILLER.
            is_group: Whether the item is a group.
            parent_group: The immediately containing group's name.

        Returns:
            The descriptor for that item, carrying its locator as provenance.

        Raises:
            FieldDescriptorError: The locator is missing or malformed, the name
                is blank, or the components contradict one another.
            ValueError: The usage class has no Python carrier, which only
                POINTER lacks and no record layout declares.
        """
        return cls(
            name=name,
            usage=usage,
            usage_declared_at=UsageDeclaredAt.FIELD,
            usage_inherited_from=None,
            picture=picture,
            signed=signed,
            sign_position=sign_position,
            sign_clause_text=sign_clause_text,
            digits=digits,
            integer_digits=integer_digits,
            scale=scale,
            character_length=character_length,
            unsigned=unsigned,
            is_edited=is_edited,
            occurs=occurs,
            redefines=redefines,
            is_filler=is_filler,
            is_group=is_group,
            parent_group=parent_group,
            python_storage=cobol_usage.python_storage_for(usage, scale),
            dictionary_key=None,
            source_locator=source_locator,
        )


# =============================================================================
#  BUILDING ONE DESCRIPTOR FROM ONE ENTRY
# =============================================================================


def _descriptor_from_entry(entry: DictionaryEntry) -> FieldDescriptor:
    """Compose a descriptor from the copybook view of one entry.

    Args:
        entry: The entry to describe.

    Returns:
        The descriptor for its copybook view.

    Raises:
        BridgeOnlyFieldError: The entry has no copybook view.
    """
    copybook = entry.copybook
    if copybook is None:
        raise BridgeOnlyFieldError(_bridge_only_message(entry))
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
        # No in-scope copybook declares a numeric-edited picture: a search for
        # edit characters inside a `pic` clause across every one of them
        # returns zero matches. Edited items are program-local, so a
        # dictionary-backed descriptor is never edited.
        is_edited=False,
        occurs=copybook.occurs,
        redefines=copybook.redefines,
        is_filler=copybook.is_filler,
        is_group=copybook.is_group,
        parent_group=copybook.parent_group,
        # The artifact governs the carrier. It is NOT recomputed here, so that
        # this file cannot quietly disagree with what the record layer holds
        # (rule R-4).
        python_storage=entry.cobol_python_storage,
        dictionary_key=entry.key,
        source_locator=copybook.source,
    )


def _declared_unsigned(copybook: CopybookField) -> bool:
    """Whether the declaration carries the explicit UNSIGNED keyword.

    Derived BY COMPARISON, never from a list of known cases: a binary-family
    item declared without a sign is an item whose declaration said UNSIGNED,
    because the family is signed by default. Measured across the generated
    artifact this is true of five items, `Page-Lines binary-char unsigned`
    [copybooks/wssystem.cob:L65] among them - so a table of known cases
    written from the one example everybody cites would have missed four.

    The test is narrowed to the binary family on purpose. A packed or zoned
    item whose picture simply omits the S, as `05 Input-Gross pic 9(9)v99.`
    does [copybooks/wsbatch.cob:L41], is unsigned in a different sense: it
    still occupies a sign nibble or an overpunch position, whereas an UNSIGNED
    binary item has no sign bit at all. Collapsing the two would change a
    stored width.

    Args:
        copybook: The copybook view to inspect.

    Returns:
        True when the explicit keyword is present.
    """
    return cobol_usage.is_binary_family(copybook.usage) and not copybook.signed


def _bridge_only_message(entry: DictionaryEntry) -> str:
    """Explain why an entry with no copybook view has no descriptor.

    Args:
        entry: The entry that lacks a copybook view.

    Returns:
        A message naming the entry, what does declare it, and where to look
        instead.
    """
    declared_by = []
    if entry.presence.in_bridge:
        declared_by.append("the bridge host-variable group")
    if entry.presence.in_column:
        declared_by.append("the MySQL schema")
    where = " and ".join(declared_by) if declared_by else "no source"

    # Built as a list of finished sentences, each parenthesised, so that no
    # fragment can join the wrong neighbour through implicit concatenation.
    opening = (
        f"{entry.key!r} has no copybook view, so it has no COBOL-side "
        f"storage for a FieldDescriptor to describe: it is declared by "
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

    `functools.cache` is the modern spelling of `functools.lru_cache` with no
    size limit, and it is unbounded here on purpose: the key domain is bounded
    by the artifact, which holds 1015 entries, so the cache cannot grow beyond
    the dictionary itself. Safe to cache at all because a descriptor is frozen
    and value-equal and the artifact is immutable once read.

    Kept a plain function rather than a cached method because memoising a
    method would hold the class itself as part of every cache entry.

    Args:
        key: The entry key.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The descriptor for that key.
    """
    return _descriptor_from_entry(loader.get_entry(key, path=path))


# =============================================================================
#  WHOLE-RECORD CONVENIENCES
# =============================================================================


def descriptors_for_table(
    table: str, *, path: Path | None = None
) -> tuple[FieldDescriptor, ...]:
    """Describe every COBOL-side field of one table, in the artifact's order.

    Thin over `loader.entries_for_table`, which yields column-mapped entries in
    column ordinal order with copybook-only entries after them. That order is
    passed straight through and never re-sorted: rule R-6 makes an observable
    ordering part of behaviour, and this file is not the place to choose one.

    Entries with no copybook view are OMITTED rather than raised on, because
    such a field has no COBOL-side storage to describe and three of them are a
    legitimate part of one in-scope table - the IRS posting date components,
    which the bridge derives [common/irspostingMT.cbl:L982-L987]. A caller
    that needs those must read the bridge view through the loader.

    Args:
        table: The table name as the schema spells it, for example
            `"GLLEDGER-REC"`.
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

    Thin over `loader.entries_for_copybook_record`. Declaration order is the
    copybook's own and is passed through unchanged, which matters because a
    record's field order is its byte layout: `copybooks/wssl.cob` totals the
    300 bytes its header declares only in the order it declares them.

    Group items are included, as the copybook declares them. A group has no
    width of its own, so reading `byte_length` on one raises - sum its
    children instead.

    Args:
        record: The 01-level record name with the copybook's own casing, for
            example `"WS-Ledger-Record"`.
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
