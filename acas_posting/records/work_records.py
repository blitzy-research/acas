"""The General Ledger work-record layouts: pre-trans, post-trans and sort-trans.

Three layouts carry data between the General Ledger posting phases. `gl070`
explodes each entered posting into legs and writes the pre-transaction record;
`gl071` sorts them; `gl072` reads the post-transaction record and posts it. The
declarations are the programs' own working-storage items, mirrored field for
field.

The sort key composition is a correctness requirement, not a convenience:
`gl072` locates the nominal-ledger account with a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so it finds the right account only
because these records arrive in nominal-key order.

These files are not part of the schema, so nothing here reaches a database and
nothing here appears in a table dump; `acas_posting.workfiles` models the files
themselves.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[tuple[str, ...]] = (
    "COBOL_FIELD_METADATA_KEY",
    "PostLedger",
    "PostTransRecord",
    "PreTransRecord",
    "SortTransRecord",
)


# Each dataclass attribute below carries the `FieldDescriptor` of the COBOL item it
# mirrors, in the dataclasses-native `metadata` mapping under this key, so an attribute
# and its storage description are declared in one place and cannot drift apart.
COBOL_FIELD_METADATA_KEY: Final[str] = "cobol_field"


# pre-trans-record [general/gl070.cbl:L108-L116] = [general/gl071.cbl:L112-L120] The
# declaration `gl070` writes and `gl071` reads back.

_PRE_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-batch#109"
)

_PRE_POST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-post#110"
)

_PRE_CODE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-code#111"
)

# R-4, and the single easiest field in this module to get wrong. EIGHT characters, not
# ten.
_PRE_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-date#112"
)

# R-4 / anomaly A-14.
_PRE_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-ac#113"
)

_PRE_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-pc#114"
)

_PRE_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-amount#115"
)

_PRE_LEGEND: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "pre-trans-record.pre-legend#116"
)


# post-trans-record, `gl071`'s FLAT declaration [general/gl071.cbl:L124-L132] An `01`
# plus eight `03` items [general/gl071.cbl:L125-L132], the same eight names as the
# `pre-` record under a `post-` prefix. R-4.

_POST_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-batch#125"
)

_POST_POST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-post#126"
)

_POST_CODE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-code#127"
)

# R-4. Eight characters, inherited from [copybooks/wspost.cob:L18] through
# [general/gl070.cbl:L498]; see `_PRE_DATE`. Not a truncation.
_POST_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-date#128"
)

# R-4. `gl071`'s FLAT level-03 declaration of the account number
# [general/gl071.cbl:L129]. Second sort key [general/gl071.cbl:L174].
_POST_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ac#129"
)

# R-4. `gl071`'s FLAT level-03 declaration of the profit centre
# [general/gl071.cbl:L130]. Third sort key [general/gl071.cbl:L175].
_POST_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-pc#130"
)

# R-4. No usage clause, so the sign is trailing and included; see `_PRE_AMOUNT`.
_POST_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-amount#131"
)

_POST_LEGEND: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-legend#132"
)


# post-trans-record, `gl072`'s GROUPED declaration [general/gl072.cbl:L110-L119] R-4,
# and the reproduction site of the anomaly the module docstring calls "TWO DECLARATIONS,
# ONE FILE".

_POST_LEDGER: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ledger"
)

# The `05` children of that group.
_POST_LEDGER_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-ac#116"
)

_POST_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "post-trans-record.post-pc#117"
)


# sort-trans-record [general/gl071.cbl:L136-L144] An `01` plus eight `03` items
# [general/gl071.cbl:L137-L144], the same eight names under a `sort-` prefix. R-4.

_SORT_BATCH: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-batch"
)

_SORT_POST: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-post"
)

_SORT_CODE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-code"
)

# R-4. Eight characters, inherited from [copybooks/wspost.cob:L18]; see `_PRE_DATE`. Not
# a truncation.
_SORT_DATE: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-date"
)

_SORT_AC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-ac"
)

_SORT_PC: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-pc"
)

# R-4. No usage clause, so the sign is trailing and included; see `_PRE_AMOUNT`.
_SORT_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-amount"
)

_SORT_LEGEND: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "sort-trans-record.sort-legend"
)


# Plain dataclasses, as Agent Action Plan section 0.8.1 requires: "Plain modules and
# dataclasses.


def _blank(descriptor: FieldDescriptor) -> str:
    """Return the declared width in spaces, derived from the descriptor.

    Args:
        descriptor: The field whose `pic x(n)` width to read.

    Returns:
        That many spaces, or the empty string for an item carrying no character length -
            which none of the nine alphanumeric fields below does.
    """
    declared = descriptor.character_length
    return " " * declared if declared is not None else ""


@dataclass(slots=True)
class PreTransRecord:
    """`01 pre-trans-record.` - the exploded posting legs `gl070` writes.

    `gl070` declares it under `fd pre-trans.` [general/gl070.cbl:L106] and writes it
    three times per entered posting - a debit leg, a credit leg negated by `multiply
    pre-amount by -1 giving pre-amount` [general/gl070.cbl:L517], and a value-added-tax
    leg written only when both the tax account and the tax amount are non-zero
    [general/gl070.cbl:L521-L523].

    Attributes:
        pre_batch: `03 pre-batch pic 9(5).` The batch number, filtered against `WS-
            Batch-Nos` before any write [general/gl070.cbl:L492]. First sort key
            [general/gl071.cbl:L173].
        pre_post: `03 pre-post pic 9(5).` The posting number within the batch. FOURTH
            sort key [general/gl071.cbl:L176], although it is the second field.
        pre_code: `03 pre-code pic xx.` The two-character posting code.
        pre_date: `03 pre-date pic x(8).` EIGHT characters, inherited from `Post-Date
            pic x(8)` [copybooks/wspost.cob:L18] by an x(8) to x(8) move
            [general/gl070.cbl:L498].
        pre_ac: `03 pre-ac pic 9(6).` The nominal account number. SECOND sort key
            [general/gl071.cbl:L174].
        pre_pc: `03 pre-pc pic 99.` The profit centre. THIRD sort key
            [general/gl071.cbl:L175].
        pre_amount: `03 pre-amount pic s9(8)v99.` Signed, scale 2, sign trailing and
            included because the declaration carries no usage clause and no sign clause.
        pre_legend: `03 pre-legend pic x(32).` The posting narrative.
    """

    pre_batch: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_BATCH}
    )
    pre_post: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_POST}
    )
    pre_code: str = field(
        default=_blank(_PRE_CODE), metadata={COBOL_FIELD_METADATA_KEY: _PRE_CODE}
    )
    pre_date: str = field(
        default=_blank(_PRE_DATE), metadata={COBOL_FIELD_METADATA_KEY: _PRE_DATE}
    )
    pre_ac: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_AC})
    pre_pc: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_PC})
    pre_amount: Decimal = field(
        default=Decimal("0.00"),
        metadata={COBOL_FIELD_METADATA_KEY: _PRE_AMOUNT},
    )
    pre_legend: str = field(
        default=_blank(_PRE_LEGEND),
        metadata={COBOL_FIELD_METADATA_KEY: _PRE_LEGEND},
    )


@dataclass(slots=True)
class PostLedger:
    """`03 post-ledger.` - the eight-character composite `gl072` alone declares.

    R-4, and half of the two-declaration divergence this module reproduces rather than
    repairs. `gl071` declares the SAME two fields FLAT at level `03`
    [general/gl071.cbl:L129-L130] with no enclosing group, and `grep -n "post-ledger"` returns nothing against
    `general/gl071.cbl` or `general/gl070.cbl`.

    Attributes:
        post_ac: `05 post-ac pic 9(6).` [general/gl072.cbl:L116] - the level-05
            declaration, distinct from the level-03 one at [general/gl071.cbl:L129].
        post_pc: `05 post-pc pic 99.` [general/gl072.cbl:L117] - likewise distinct from
            [general/gl071.cbl:L130].
    """

    post_ac: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_LEDGER_AC}
    )
    post_pc: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_LEDGER_PC}
    )


@dataclass(slots=True)
class PostTransRecord:
    """`01 post-trans-record.` - the sorted stream, declared two ways.

    R-4, and the reproduction site of that divergence in full. ONE `01` name, ONE
    physical work file, TWO incompatible declarations.

    Attributes:
        post_batch: `03 post-batch pic 9(5).` FIRST sort key [general/gl071.cbl:L173].
        post_post: `03 post-post pic 9(5).` FOURTH sort key [general/gl071.cbl:L176],
            although the second field.
        post_code: `03 post-code pic xx.`.
        post_date: `03 post-date pic x(8).` EIGHT characters, inherited from
            [copybooks/wspost.cob:L18]; not a truncation.
        post_ledger: `03 post-ledger.` [general/gl072.cbl:L115] - `gl072`'s GROUPED view
            of the account number and profit centre that follow. Present because `gl072`
            moves the composite whole into `WS-Ledger-Key` [general/gl072.cbl:L405].
        post_ac: `03 post-ac pic 9(6).` [general/gl071.cbl:L129] - `gl071`'s FLAT
            level-03 declaration. SECOND sort key [:L174].
        post_pc: `03 post-pc pic 99.` [general/gl071.cbl:L130] - `gl071`'s FLAT level-03
            declaration. THIRD sort key [:L175].
        post_amount: `03 post-amount pic s9(8)v99.` Signed, scale 2, sign trailing and
            included, no usage clause. `decimal.Decimal` (R-2).
        post_legend: `03 post-legend pic x(32).`.
    """

    post_batch: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_BATCH}
    )
    post_post: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_POST}
    )
    post_code: str = field(
        default=_blank(_POST_CODE), metadata={COBOL_FIELD_METADATA_KEY: _POST_CODE}
    )
    post_date: str = field(
        default=_blank(_POST_DATE), metadata={COBOL_FIELD_METADATA_KEY: _POST_DATE}
    )
    # R-4. `gl072`'s grouped view [general/gl072.cbl:L115-L117] of the two attributes
    # that follow, which are `gl071`'s flat view [general/gl071.cbl:L129-L130] of the
    # same eight characters.
    post_ledger: PostLedger = field(
        default_factory=PostLedger,
        metadata={COBOL_FIELD_METADATA_KEY: _POST_LEDGER},
    )
    post_ac: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_AC}
    )
    post_pc: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_PC}
    )
    post_amount: Decimal = field(
        default=Decimal("0.00"),
        metadata={COBOL_FIELD_METADATA_KEY: _POST_AMOUNT},
    )
    post_legend: str = field(
        default=_blank(_POST_LEGEND),
        metadata={COBOL_FIELD_METADATA_KEY: _POST_LEGEND},
    )


@dataclass(slots=True)
class SortTransRecord:
    """`01 sort-trans-record.` - the SORT work description's record.

    R-4. That `sd` is a SORT-FILE description and not an `fd`, a distinction the frozen
    source carries through to its FILE-CONTROL entry.

    Attributes:
        sort_batch: `03 sort-batch pic 9(5).` FIRST key [general/gl071.cbl:L173].
        sort_post: `03 sort-post pic 9(5).` FOURTH key [general/gl071.cbl:L176], second
            field.
        sort_code: `03 sort-code pic xx.` Not a key.
        sort_date: `03 sort-date pic x(8).` Not a key. EIGHT characters, inherited from
            [copybooks/wspost.cob:L18]; not a truncation.
        sort_ac: `03 sort-ac pic 9(6).` SECOND key [general/gl071.cbl:L174].
        sort_pc: `03 sort-pc pic 99.` THIRD key [general/gl071.cbl:L175].
        sort_amount: `03 sort-amount pic s9(8)v99.` Not a key. Signed, scale 2, sign
            trailing and included, no usage clause; `decimal.Decimal` (R-2).
        sort_legend: `03 sort-legend pic x(32).` Not a key.
    """

    sort_batch: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _SORT_BATCH}
    )
    sort_post: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _SORT_POST}
    )
    sort_code: str = field(
        default=_blank(_SORT_CODE), metadata={COBOL_FIELD_METADATA_KEY: _SORT_CODE}
    )
    sort_date: str = field(
        default=_blank(_SORT_DATE), metadata={COBOL_FIELD_METADATA_KEY: _SORT_DATE}
    )
    sort_ac: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _SORT_AC}
    )
    sort_pc: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _SORT_PC}
    )
    sort_amount: Decimal = field(
        default=Decimal("0.00"),
        metadata={COBOL_FIELD_METADATA_KEY: _SORT_AMOUNT},
    )
    sort_legend: str = field(
        default=_blank(_SORT_LEGEND),
        metadata={COBOL_FIELD_METADATA_KEY: _SORT_LEGEND},
    )
