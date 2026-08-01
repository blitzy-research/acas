"""The `WS-Calling-Data` linkage block: how one ACAS program calls another.

`WS-Calling-Data` is the seven-field block a menu shell fills in before it
`CALL`s a posting program, and it is the first parameter of the General
Ledger, Sales and Purchase linkage shapes. This module is a CREATE from
`copybooks/wscall.cob` - field for field, with nothing added, nothing renamed
and nothing widened. The Agent Action Plan states its whole content in one
line, at section 0.4.1.3: "`acas_posting/records/calling_data.py` | CREATE |
`copybooks/wscall.cob` | Seven-field linkage block".

Seven fields are declared here, and seven is the whole of it. This is the
smallest record in the package and therefore the easiest place to be tempted
into a convenience; nothing has been added. `WS-Del-Link`'s spelling,
`WS-CD-Args`'s abbreviation and `WS-Term-Code`'s two-digit width all stand
exactly as declared.

THE COPYBOOK, AS IT ACTUALLY READS
==================================
Traced to the frozen source, which is 15 lines long::

    L6      01  WS-Calling-Data.
    L7          03  WS-Called       pic x(8).
    L8          03  WS-Caller       pic x(8).
    L9          03  WS-Del-Link     pic x(8).
    L10         03  WS-Term-Code    pic 99.
    L11     *>                                 new 18/5/13
    L12         03  WS-Process-Func pic 9.
    L13         03  WS-Sub-Function pic 9.
    L14         03  WS-CD-Args      pic x(13).    *> Changed / Added 14/03/18

No REDEFINES, no OCCURS, no 88-level condition name and no VALUE clause
appears anywhere in the block, so this module declares no predicate and no
initialised constant either. Summing the pictures gives a 41-byte record:
8 + 8 + 8 + 2 + 1 + 1 + 13, which `RECORD_BYTE_LENGTH` computes rather than
restates.

A LOCATOR CORRECTION, RECORDED RATHER THAN QUIETLY APPLIED
==========================================================
The Agent Action Plan cites this block as `[copybooks/wscall.cob:L6-L13]`.
That span is one line short at the tail. Line L11 is a COMMENT - `*> new
18/5/13`, marking when the two function fields were added - so the last three
declarations sit one line lower than a reader counting fields would assume:
`WS-Process-Func` at L12, `WS-Sub-Function` at L13, `WS-CD-Args` at L14, and
the block spans L6-L14.

Every locator quoted in this module comes from the generated dictionary, whose
generator parsed the same copybook, so the correction needed no editing here -
it simply never arose. That is the failure mode the "data dictionary first"
directive exists to prevent, and it is recorded rather than silently absorbed,
because a wrong locator in a traceability document is worse than none. The
frozen source is never touched to make a citation true: the copybook is the
authority, the plan's prose is not.

WHY THIS BLOCK MATTERS
======================
None of the in-scope posting programs is a main program. Every one is a
`CALL`ed sub-program with a fixed parameter list, so its LINKAGE SECTION is
its batch invocation contract, already written down. `general/gl071.cbl` - the
batch sort, and the reason that program is one of this module's two source
references - shows the four-parameter General Ledger shape::

    linkage section.                            [general/gl071.cbl:L152]
    copy "wscall.cob".                          [general/gl071.cbl:L155]
    procedure division using ws-calling-data    [general/gl071.cbl:L161-L164]
    system-record  to-day  file-defs.

Sales and Purchase use the same first parameter and add a fourth system
record. The IRS posting program is the exception: it takes neither this block
nor the run date, declaring `using IRS-System-Params, WS-System-Record,
File-Defs` [irs/irs030.cbl:L552-L554]. That is why the migrated command line
has three argument shapes rather than one, and why this record appears in two
of the three. Binding argv to these seven fields belongs to
`acas_posting/cli/args.py`, which section 0.4.1.1 describes as "a faithful
binding rather than an invention". This module declares the data and stops.

WS-TERM-CODE CARRIES AN ABORT CHAIN ACROSS THREE PROGRAMS
=========================================================
`WS-Term-Code` looks like a spare status byte and is nothing of the kind. It
is the return channel by which a called program stops the rest of a posting
run, and section 0.6.4 traces the chain: a batch left open sets a status
condition, `gl070` detects it and raises the terminate code, and the menu
tests that code and returns to the menu rather than continuing. The whole gate
is the menu's posting-cycle dispatch at [general/general.cbl:L805-L815] -
`load08.` calls `gl070`, then `if ws-term-code = 5 go to display-menu.` at
L810-L811 short-circuits the two calls that follow. The consequence, in the
plan's own words: "The effect is that `gl071` and `gl072` never run at all."

So the observable database effect of that rejection is the ABSENCE of
everything the later phases would have written. Section 0.4.1.1 requires the
migrated command line to reproduce it as a hard gate between phases, not as a
warning - and that gate belongs to the GL posting-cycle CLI entry point. It
is deliberately NOT here: this module declares a field, not a policy, and a
predicate named for the gate would invite a caller to re-implement it at the
wrong layer.

Provenance worth keeping visible: the field was widened from `pic 9` to
`pic 99` in version 1.02 of the copybook, dated 14/11/25
[copybooks/wscall.cob:L4]. Its documented values are single digits, and it
stays two digits wide regardless, because the copybook declares two.

WS-CD-ARGS IS A POSITIONAL BLOB AND STAYS ONE
=============================================
The copybook's own header explains the field, and it is the only field in the
block with a stated purpose [copybooks/wscall.cob:L1-L3]: it exists "for
passing extra info to called process that will help in a cron call by time via
menu program", and its contents are "picked by position within WS-Args".

It is therefore 13 characters of caller-agreed positional text. This module
does not parse it, split it, index it or give it a structure the copybook does
not declare - there are no sub-fields at L14, so there are none here. Callers
that need a position slice it themselves, as the COBOL programs do.

THIS BLOCK MAPS TO NO MYSQL TABLE, AND THE DICTIONARY SAYS SO
=============================================================
`WS-Calling-Data` is pure linkage working storage. It is absent from the
entity-to-table spine of section 0.2.1.1, and none of the 22 in-scope tables
corresponds to it. The dictionary was probed rather than assumed, and it holds
eight entries for the record - the `01` group plus the seven `03` fields -
every one of them one-sided, with `table`, `bridge` and `column` all absent
and `in_copybook=True, in_bridge=False, in_column=False`. `cite` therefore
renders, for the first field::

    WS-Calling-Data.WS-Called  copybook=copybooks/wscall.cob:L7
    bridge=absent  column=absent

Because each entry has a single layer it cannot disagree with itself: every
`drift` aspect is False and no anomaly or ambiguity reference attaches to any
of the seven. Contrast `Sales-Average`, signed in the copybook and unsigned at
both bridge and column [copybooks/wssl.cob:L49]. Nothing of that kind arises
here, and no `<TABLE-NAME>.<COLUMN-NAME>` key was fabricated for a record that
has no table.

Keys are `<COPYBOOK-RECORD>.<FIELD-NAME>` in the source's own casing, so the
key is `WS-Calling-Data.WS-Called` and NOT `WS-CALLING-DATA.WS-CALLED`; a
probe for the upper-cased form returns nothing. The qualifier is in the key so
that two similar layouts can never merge - `PSIRSPOST-REC` and
`IRSPOSTING-REC` carry near-identical field names and are different records,
as the copybook says verbatim [copybooks/wspost-irs.cob:L6-L7]: "This is NOT
the same as the internal IRS posting file". `acas_posting.dictionary.loader`
documents both key forms in full.

DELIBERATELY ABSENT (R-3), AND THE LAYERING
===========================================
No eighth attribute, and no property, method or module function a caller could
mistake for a stored field. No post-initialisation hook, so no padding, no
truncation and no check on any value: `MOVE` semantics belong to
`acas_posting/cobol/move.py`. No schema definition, declarative metadata or
ORM base; no concurrency primitive. Of the two imports `records/*.py` is
granted, only `acas_posting.cobol.field` is taken - `FieldDescriptor.cite`
already delegates to the loader's own primitive. Section 0.4.3 promises the
arithmetic test tier "imports only `cobol` and `records` and touches no
database, so it runs anywhere", and one import reaching into `dal` would drag
a driver into that tier.

Attribute order is copybook declaration order, so this module can be set
beside its copybook and diffed by eye. No clock is consulted and no
unpredictable value drawn, so two imports in two processes produce identical
state (R-6). `PIC X(n)` becomes `str` and the three unsigned scale-zero
`DISPLAY` items become `int`; this block carries no monetary or quantity value
at all, so no `Decimal` is needed and no binary float appears (R-2). See
`acas_posting.records` for the conventions every record module shares.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[list[str]] = ["WsCallingData"]


#  THE BLOCK'S IDENTITY IN THE FROZEN SOURCE

#: The `01`-level name, with the copybook's own casing - the left half of
#: every dictionary key below [copybooks/wscall.cob:L6].
RECORD_NAME: Final[str] = "WS-Calling-Data"

#: The frozen copybook this module is a CREATE from. Named, never read: no
#: COBOL source is consulted at run time (R-1).
COPYBOOK: Final[str] = "copybooks/wscall.cob"

#: The block's true span. L6 is the group header and L14 the last field; the
#: gap at L11 is the comment discussed in the module docstring.
RECORD_LOCATOR: Final[str] = "copybooks/wscall.cob:L6-L14"

#: The dictionary key of the `01` group itself. A group has no width of its
#: own, so its descriptor is exposed for its locator and its name, and its
#: byte length is never asked for.
RECORD_KEY: Final[str] = "WS-Calling-Data.WS-Calling-Data"


#  ATTRIBUTE TO DICTIONARY KEY - THE ONE PLACE THE MAPPING IS WRITTEN
# Python attribute name, then the dictionary key of the COBOL field it
# carries, in copybook DECLARATION order. Order is behaviour here twice over:
# it is the record's byte layout, and rule R-6 makes an observable ordering
# part of what this migration must preserve. Above each row is the field's
# COBOL declaration and locator, quoted verbatim from the frozen copybook.
# Attribute names are mechanical - the COBOL name lower-cased with hyphens
# turned into underscores - so a reader can go from either name to the other
# without a lookup table. `WS-Del-Link` keeps its own spelling and
# `WS-CD-Args` keeps its abbreviation; neither is expanded (R-4).
# This tuple is the single source for the three surfaces below it, so the
# seven keys are written once and cannot drift apart.
_ATTRIBUTE_KEYS: Final[tuple[tuple[str, str], ...]] = (
    # 03  WS-Called       pic x(8).        [copybooks/wscall.cob:L7]
    ("ws_called", "WS-Calling-Data.WS-Called"),
    # 03  WS-Caller       pic x(8).        [copybooks/wscall.cob:L8]
    ("ws_caller", "WS-Calling-Data.WS-Caller"),
    # 03  WS-Del-Link     pic x(8).        [copybooks/wscall.cob:L9]
    ("ws_del_link", "WS-Calling-Data.WS-Del-Link"),
    # 03  WS-Term-Code    pic 99.          [copybooks/wscall.cob:L10]
    ("ws_term_code", "WS-Calling-Data.WS-Term-Code"),
    # 03  WS-Process-Func pic 9.           [copybooks/wscall.cob:L12]
    ("ws_process_func", "WS-Calling-Data.WS-Process-Func"),
    # 03  WS-Sub-Function pic 9.           [copybooks/wscall.cob:L13]
    ("ws_sub_function", "WS-Calling-Data.WS-Sub-Function"),
    # 03  WS-CD-Args      pic x(13).       [copybooks/wscall.cob:L14]
    ("ws_cd_args", "WS-Calling-Data.WS-CD-Args"),
)


#  THE DESCRIPTORS  (rule R-5)

#: The `01` group as the dictionary describes it, carrying the record-level
#: locator `copybooks/wscall.cob:L6`.
RECORD_DESCRIPTOR: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    RECORD_KEY
)

#: Attribute name to descriptor, insertion-ordered and therefore in copybook
#: declaration order. Wrapped in a read-only view so no caller can add,
#: replace or drop an entry: the mapping describes a frozen record layout and
#: has to be as fixed as the layout is.
DESCRIPTORS: Final[Mapping[str, FieldDescriptor]] = MappingProxyType(
    {
        attribute: FieldDescriptor.from_dictionary_key(key)
        for attribute, key in _ATTRIBUTE_KEYS
    }
)

#: The seven dictionary keys, in declaration order - the machine-readable
#: half of this module's traceability entry, which a later boundary writes.
DICTIONARY_KEYS: Final[tuple[str, ...]] = tuple(key for _, key in _ATTRIBUTE_KEYS)

#: The seven descriptors, in declaration order.
FIELDS: Final[tuple[FieldDescriptor, ...]] = tuple(DESCRIPTORS.values())

#: The record's width in bytes, SUMMED from the descriptors rather than
#: stated: 8 + 8 + 8 + 2 + 1 + 1 + 13. Computing it is what makes it evidence
#: about the frozen copybook instead of one more number to keep in step.
RECORD_BYTE_LENGTH: Final[int] = sum(descriptor.byte_length for descriptor in FIELDS)


#  DEFAULTS, TAKEN FROM THE DECLARED WIDTH RATHER THAN TYPED


def _spaces(attribute: str) -> str:
    """Return one alphanumeric field's declared width, as spaces.

    A `pic x(n)` item occupies n character positions whether or not anything
    has been moved into it, so the width-preserving starting value for such a
    field is n spaces. That is also what the calling program actually puts
    there, which is why this default is evidence rather than taste - the
    General Ledger menu clears the block by moving SPACES into the
    alphanumeric fields [general/general.cbl:L513] and ZEROS into the numeric
    ones [general/general.cbl:L505], [general/general.cbl:L514] before every
    dispatch.

    An empty string would be the wrong length for the field it models, and a
    hand-typed `" " * 8` would be exactly the transcription by eye that the
    "data dictionary first" directive forbids. The width therefore comes from
    the descriptor.

    `character_length` is declared on every alphanumeric item in this block -
    8, 8, 8 and 13 - so the zero fallback is unreachable for the four callers
    below. It is written as part of the expression rather than as a check,
    because a check on a value is exactly what rule R-3 keeps out of this
    layer.

    Args:
        attribute: The Python attribute name, as `"ws_called"`. A name that is
            not one of the seven raises `KeyError` from the mapping itself.

    Returns:
        That field's declared width in space characters.
    """
    return " " * (DESCRIPTORS[attribute].character_length or 0)


#  THE RECORD


@dataclass(slots=True)
class WsCallingData:
    """`01 WS-Calling-Data.` - the inter-program call block.

    A CREATE from `copybooks/wscall.cob` [copybooks/wscall.cob:L6-L14], seven
    fields, in the copybook's own declaration order. The class name is the COBOL
    `01`-name in PascalCase with the hyphens dropped, which makes the consumer's
    import line mechanical - one symbol out of one module, exactly as the import
    contract of section 0.4.3 has it::

        >>> from acas_posting.records.calling_data import WsCallingData

    Each attribute name is likewise mechanical - the COBOL name lower-cased with
    hyphens turned into underscores - and each carries its COBOL declaration and
    locator in a comment, so this class and its copybook can be read side by side.
    The storage metadata behind every attribute is in `DESCRIPTORS`, keyed by
    attribute name, and `cite` prints where any one of them comes from.

    MUTABLE ON PURPOSE - NOT FROZEN
    -------------------------------
    COBOL linkage is shared storage, not an argument copy: a called program writes
    into the caller's own record. `WS-Term-Code` is the case that matters, and it
    is load-bearing. `gl070` SETS it when it finds a batch left open, the menu
    READS it and returns to the menu instead of continuing
    [general/general.cbl:L810-L811], and the result is that `gl071` and `gl072`
    never run at all (section 0.6.4).

    A frozen record could not express that - the callee would have to hand back a
    new object, which is not what the COBOL does and would leave the caller's copy
    stale. So this record is mutable, exactly as the storage it models is.

    `slots=True` is the counterweight: the seven attributes are the whole record
    and an instance cannot grow an eighth at run time, which is the right property
    for a fixed-length 41-byte layout and a structural restatement of R-3's
    "nothing added".

    DEFAULTS
    --------
    The four alphanumeric fields start as spaces at their declared width and the
    three numeric fields start at zero, matching what the calling program puts
    there: the General Ledger menu clears `ws-called` and `ws-del-link` with
    SPACES [general/general.cbl:L513], and zeroes `ws-process-func` and
    `ws-sub-function` [:L505] and `ws-term-code` [:L514], immediately before each
    dispatch. `ws-caller` then receives the calling program's own name [:L512],
    and `ws-cd-args` is left as the invoker set it.

    Widths come from the descriptors via `_spaces`, never from a literal. Nothing
    reshapes, pads, truncates or checks an assigned value afterwards:
    sending-field-to-receiving-field semantics belong to
    `acas_posting/cobol/move.py`, and added validation belongs to no layer of this
    migration, because the COBOL performs none here and introducing any would be a
    behaviour change (R-3).

    NOT DECLARED HERE
    -----------------
    There is no predicate for the terminate code and no helper of any kind. The
    abort gate is the GL posting-cycle CLI entry point's to reproduce, and the
    copybook declares no 88-level condition name to draw a predicate from in any
    case. This class declares data.
    """

    # 03  WS-Called       pic x(8).        [copybooks/wscall.cob:L7]
    # The program being called - one of the twelve in-scope posting programs
    # when this block enters the migrated cycle.
    ws_called: str = _spaces("ws_called")

    # 03  WS-Caller       pic x(8).        [copybooks/wscall.cob:L8]
    # The program doing the calling: a menu shell in the COBOL system - which
    # writes its own name in, as `move "general" to ws-caller`
    # [general/general.cbl:L512] - and a command-line entry point under
    # `acas_posting/cli/` here.
    ws_caller: str = _spaces("ws_caller")

    # 03  WS-Del-Link     pic x(8).        [copybooks/wscall.cob:L9]
    # Spelling preserved exactly as the copybook declares it; not expanded to
    # anything longer or more explanatory (R-4).
    ws_del_link: str = _spaces("ws_del_link")

    # 03  WS-Term-Code    pic 99.          [copybooks/wscall.cob:L10]
    # THE ABORT CHANNEL. Set by the callee, read by the caller: `gl070` raises
    # it on an open batch, and `if ws-term-code = 5 / go to display-menu`
    # [general/general.cbl:L810-L811] then skips `gl071` and `gl072`
    # entirely. The command line reproduces that as a hard gate between
    # phases (section 0.4.1.1); this is only the field it travels in. Two
    # digits wide because version 1.02 of the copybook widened it from
    # `pic 9` [copybooks/wscall.cob:L4], and it stays two digits wide even
    # though its documented values are single digits.
    # Do not narrow it, and do not give it a predicate.
    ws_term_code: int = 0

    # 03  WS-Process-Func pic 9.           [copybooks/wscall.cob:L12]
    # Added 18/5/13 per the comment at [copybooks/wscall.cob:L11] - the line
    # that makes this field L12 rather than L11.
    ws_process_func: int = 0

    # 03  WS-Sub-Function pic 9.           [copybooks/wscall.cob:L13]
    ws_sub_function: int = 0

    # 03  WS-CD-Args      pic x(13).       [copybooks/wscall.cob:L14]
    # Thirteen characters of caller-agreed positional text, added in version
    # 1.01 to carry extra information into an unattended, time-triggered call
    # [copybooks/wscall.cob:L1-L3]. Its contents are "picked by position
    # within WS-Args", so it is one opaque string here: no sub-fields are
    # declared at L14 and none are added.
    ws_cd_args: str = _spaces("ws_cd_args")


#  TRACEABILITY SURFACE  (rule R-5)


def descriptor_for(attribute: str) -> FieldDescriptor:
    """Return the descriptor of the COBOL field one attribute carries.

    Args:
        attribute: The Python attribute name, as `"ws_term_code"`.

    Returns:
        Its `FieldDescriptor`, carrying the picture, usage, digits, scale,
        character width and Python carrier the generated dictionary holds,
        plus both halves of its provenance - the dictionary key and the
        copybook locator.

    Raises:
        KeyError: The name is not one of the seven, raised by the mapping
            itself. Nothing is added on top of it: the seven names are fixed
            by the copybook and a caller asking for an eighth has made a
            programming error, not supplied bad data.
    """
    return DESCRIPTORS[attribute]


def cite(attribute: str) -> str:
    """Return where the COBOL field behind one attribute comes from.

    The compact three-locator provenance line, SURFACED from the dictionary
    loader through the descriptor rather than reassembled here, so that this
    module and the traceability document can never quote different locators.
    Both remaining layers read `absent` for every field of this block, because
    it maps to no table::

        WS-Calling-Data.WS-Term-Code  copybook=copybooks/wscall.cob:L10
        bridge=absent  column=absent

    Args:
        attribute: The Python attribute name, as `"ws_term_code"`.

    Returns:
        The provenance line for that field. Never empty: a descriptor with no
        provenance at all cannot be constructed.

    Raises:
        KeyError: The name is not one of the seven; see `descriptor_for`.
    """
    return DESCRIPTORS[attribute].cite()
