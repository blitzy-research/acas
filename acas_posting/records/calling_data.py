"""The `WS-Calling-Data` linkage block: how one ACAS program calls another.

The seven-field block a menu shell fills in before it `CALL`s a posting program,
and the first parameter of the General Ledger and Sales/Purchase linkage shapes
[copybooks/wscall.cob:L6-L14]: `WS-Called`, `WS-Caller` and `WS-Del-Link`
`pic x(8)`, `WS-Term-Code pic 99`, `WS-Process-Func` and `WS-Sub-Function pic 9`,
and `WS-CD-Args pic x(13)`.

`WS-Term-Code` is the one field that travels back: a callee writes it and the
caller tests it, which is how the abort gate works
[general/general.cbl:L810-L811] and how a serious error above 7 ends a run
[common/ACAS.cbl:L578]. Its `pic 99` domain is 0 through 99, so no value it can
hold is out of range for a process exit status.

The IRS shape does not carry this block at all [irs/irs030.cbl:L552-L554].
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[list[str]] = ["WsCallingData"]


RECORD_NAME: Final[str] = "WS-Calling-Data"

#: The frozen copybook this module is a CREATE from. Named, never read: no COBOL source
#: is consulted at run time (R-1).
COPYBOOK: Final[str] = "copybooks/wscall.cob"

RECORD_LOCATOR: Final[str] = "copybooks/wscall.cob:L6-L14"

#: The dictionary key of the `01` group itself.
RECORD_KEY: Final[str] = "WS-Calling-Data.WS-Calling-Data"


# Python attribute name, then the dictionary key of the COBOL field it carries, in
# copybook DECLARATION order. Order is behaviour here twice over.
_ATTRIBUTE_KEYS: Final[tuple[tuple[str, str], ...]] = (
    ("ws_called", "WS-Calling-Data.WS-Called"),
    ("ws_caller", "WS-Calling-Data.WS-Caller"),
    ("ws_del_link", "WS-Calling-Data.WS-Del-Link"),
    ("ws_term_code", "WS-Calling-Data.WS-Term-Code"),
    ("ws_process_func", "WS-Calling-Data.WS-Process-Func"),
    ("ws_sub_function", "WS-Calling-Data.WS-Sub-Function"),
    ("ws_cd_args", "WS-Calling-Data.WS-CD-Args"),
)


#  THE DESCRIPTORS  (rule R-5)

RECORD_DESCRIPTOR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    RECORD_KEY
)

DESCRIPTORS: Final[Mapping[str, FieldDescriptor]] = MappingProxyType(
    {
        attribute: FieldDescriptor.from_dictionary_key(key)
        for attribute, key in _ATTRIBUTE_KEYS
    }
)

DICTIONARY_KEYS: Final[tuple[str, ...]] = tuple(key for _, key in _ATTRIBUTE_KEYS)

FIELDS: Final[tuple[FieldDescriptor, ...]] = tuple(DESCRIPTORS.values())

#: The record's width in bytes, SUMMED from the descriptors rather than stated: 8 + 8 +
#: 8 + 2 + 1 + 1 + 13.
RECORD_BYTE_LENGTH: Final[int] = sum(descriptor.byte_length for descriptor in FIELDS)


def _spaces(attribute: str) -> str:
    """Return one alphanumeric field's declared width, as spaces.

    A `pic x(n)` item occupies n character positions whether or not anything has been
    moved into it, so the width-preserving starting value for such a field is n spaces.

    Args:
        attribute: The Python attribute name, as `"ws_called"`. A name that is not one
            of the seven raises `KeyError` from the mapping itself.

    Returns:
        That field's declared width in space characters.
    """
    return " " * (DESCRIPTORS[attribute].character_length or 0)


@dataclass(slots=True)
class WsCallingData:
    """`01 WS-Calling-Data.` - the inter-program call block.

    COBOL linkage is shared storage, not an argument copy: a called program writes into
    the caller's own record. `WS-Term-Code` is the case that matters, and it is load-
    bearing.
    """

    ws_called: str = _spaces("ws_called")

    ws_caller: str = _spaces("ws_caller")

    # 03 WS-Del-Link pic x(8). [copybooks/wscall.cob:L9] Spelling preserved exactly as
    # the copybook declares it; not expanded to anything longer or more explanatory
    # (R-4).
    ws_del_link: str = _spaces("ws_del_link")

    # 03 WS-Term-Code pic 99. [copybooks/wscall.cob:L10] THE ABORT CHANNEL. Set by the
    # callee, read by the caller.
    ws_term_code: int = 0

    # 03 WS-Process-Func pic 9. [copybooks/wscall.cob:L12] Added 18/5/13 per the comment
    # at [copybooks/wscall.cob:L11] - the line that makes this field L12 rather than
    # L11.
    ws_process_func: int = 0

    ws_sub_function: int = 0

    ws_cd_args: str = _spaces("ws_cd_args")


#  TRACEABILITY SURFACE  (rule R-5)


def descriptor_for(attribute: str) -> FieldDescriptor:
    """Return the descriptor of the COBOL field one attribute carries.

    Args:
        attribute: The Python attribute name, as `"ws_term_code"`.

    Returns:
        Its `FieldDescriptor`, carrying the picture, usage, digits, scale, character
            width and Python carrier the generated dictionary holds, plus both halves of
            its provenance - the dictionary key and the copybook locator.

    Raises:
        KeyError: The name is not one of the seven, raised by the mapping itself.
            Nothing is added on top of it.
    """
    return DESCRIPTORS[attribute]


def cite(attribute: str) -> str:
    """Return where the COBOL field behind one attribute comes from.

    Args:
        attribute: The Python attribute name, as `"ws_term_code"`.

    Returns:
        The provenance line for that field. Never empty: a descriptor with no provenance
            at all cannot be constructed.

    Raises:
        KeyError: The name is not one of the seven; see `descriptor_for`.
    """
    return DESCRIPTORS[attribute].cite()
