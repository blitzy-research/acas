"""General Ledger posting record - ``01 WS-Posting-Record``.

A CREATE from ``copybooks/wspost.cob``, whose ``01`` level sits at
[copybooks/wspost.cob:L12] and whose last field sits at
[copybooks/wspost.cob:L28]. Fourteen dataclass attributes, one per column
of the table, in copybook declaration order. Nothing is added and nothing
is repaired.

Its place in the entity spine, obtained from
``loader.table_for("GLPOSTING-REC")`` rather than written down here::

    entity facade   GL-Posting
    handler         acas006
    bridge          glpostingMT
    MySQL table     GLPOSTING-REC   14 columns, primary key POST-RRN
                    [mysql/ACASDB.sql:L169]
    copybook        copybooks/wspost.cob

THE COPYBOOK'S OWN SIZE HISTORY, VERBATIM
-----------------------------------------
Two comment lines record a size change and, unusually for this codebase,
its cause [copybooks/wspost.cob:L6-L7]::

    *> 98 bytes 26/03/09
    *> 96 bytes 20/12/11 (leading sign removed)

The batch record moved on the very same two dates in the OPPOSITE
direction and its author could not account for it
[copybooks/wsbatch.cob:L7-L9] - that contradiction is register entry A-15,
reproduced in ``records/gl_batch.py``. Here the two bytes are explained: a
leading sign was taken off the two money fields. This file records the
mirror image and settles neither.

The removal is why the two amounts below carry no SIGN clause at all: at
[copybooks/wspost.cob:L23] and [copybooks/wspost.cob:L28] they read
``pic s9(8)v99.`` and nothing more, so the sign is overpunched on the
trailing digit and included in the field's ten bytes. The two IRS posting
copybooks did not follow, and the divergence is left standing::

    copybooks/wspost.cob:L23      pic s9(8)v99.
    copybooks/wspost.cob:L28      pic s9(8)v99.
    copybooks/wspost-irs.cob:L21  pic s9(7)v99   sign leading.
    copybooks/wspost-irs.cob:L25  pic s9(7)v99   sign leading.
    copybooks/irswspost.cob:L14   pic s9(7)v99  sign is leading.
    copybooks/irswspost.cob:L18   pic s9(7)v99   sign is leading.

Three differences at once, not one: where the sign sits, how the clause is
spelt - ``sign leading`` against ``sign is leading``, which the dictionary
keeps distinguishable rather than folding together - and the digit count,
ten here against nine there. None of the three is smoothed away.

THE BYTE ARITHMETIC, AND WHERE IT STOPS ADDING UP
-------------------------------------------------
Ten of the fifteen items carry the maintainer's own running byte offset,
each reproduced verbatim on its attribute below. Read as cumulative end
positions over the fields that existed when they were written - that is,
before ``WS-Post-rrn`` was added - they run::

    Post-Code       12     Post-Amount     46
    Post-Date       20     Post-Legend     76
    Post-DR         26     Vat-AC          82
    Post-CR         34     Post-Vat-Side   86
    CR-PC           36     Vat-Amount      96

and close at 96, agreeing with the header. The first six agree with the
declared pictures exactly: 5 + 5 = 10, + 2 = 12, + 8 = 20, + 6 = 26,
(+ 2 = 28), + 6 = 34, + 2 = 36, + 10 = 46.

From ``Post-Legend`` on they do not. It is declared ``pic x(32)``
[copybooks/wspost.cob:L24], so 46 + 32 = 78, not the 76 written there; and
every later offset is short by the same two bytes, closing at 98 rather
than 96. The chain would be self-consistent only if that field were
``x(30)``. It is not, and the other two layers agree with the copybook: the
bridge declares ``HV-POST-LEGEND PIC X(32)``
[common/glpostingMT.cbl:L291], the schema declares ``POST-LEGEND char(32)``
[mysql/ACASDB.sql:L164], and ``loader.drift_for`` reports no disagreement
at all for that field. So the picture stands at 32 and the offsets are
stale.

Adding ``WS-Post-rrn pic 9(5)`` [copybooks/wspost.cob:L13] - which
postdates every one of those offsets, per the note at
[copybooks/wspost.cob:L10] - carries the declared layout to 103 bytes.
The three figures 96, 98 and 103 are recorded here side by side and none is
adjudicated. What the compiled program actually reads is a question for the
oracle, and it is logged in the migration's ambiguity-resolutions document.

WHAT THIS FILE IS NOT
---------------------
This record is the input to the three-leg double-entry explosion in
``gl070``, which reads every field declared here [general/gl070.cbl:L495-
L533]: a debit leg, a credit leg turned round by ``multiply pre-amount
by -1 giving pre-amount`` [general/gl070.cbl:L517] and again at
[general/gl070.cbl:L530], and a VAT leg written only when both the VAT
account and the VAT amount are non-zero [general/gl070.cbl:L521-L523].

None of that lives here. This module is a layout: no leg builder, no
turning of a sign, no VAT guard, no joining of the key group into one
value, no reading of the date text, no predicate over the VAT side. Those
belong to the `gl070` program module, the `acas006` handler module,
``acas_posting/dates.py`` and ``acas_posting/cobol/condition_names.py``
respectively. Rule R-3 forbids this file to hold any of them, and the
arithmetic parity suite locks the behaviour where it does belong.

ANOMALIES RECORDED HERE, REPRODUCED AND NOT REPAIRED (R-4)
----------------------------------------------------------
From the preserved user requirement, section 0.8.2: "There is no test
suite: compiled COBOL execution is the behavioral specification, defects
included. A defect reproduced is correct; a defect fixed is a failure."

Ten findings attach to this record. Each is commented at its attribute with
its locator, so the summaries here are deliberately short; the register is
the migration's anomaly log.

1.  **The primary key's host variable is never loaded.** Of the fourteen
    host variables the bridge declares [common/glpostingMT.cbl:L281-L295],
    thirteen are loaded from the record in ``bb000-HV-Load``
    [common/glpostingMT.cbl:L1045], at L1054 through L1066.
    ``HV-POST-RRN`` [common/glpostingMT.cbl:L282] is the one that is not,
    and ``POST-RRN`` is the table's primary key - declared at
    [mysql/ACASDB.sql:L155] and named by the ``PRIMARY KEY`` clause at
    [mysql/ACASDB.sql:L169]. See ``ws_post_rrn`` below for the full
    account and for the maintainer's own warning about it.

2.  **The key group is flattened and widened at the bridge.**
    ``WS-Post-Key`` [copybooks/wspost.cob:L14] groups two five-digit
    fields; the bridge joins them into ``HV-POST-KEY PIC 9(18) COMP``
    [common/glpostingMT.cbl:L283] and the schema stores
    ``POST-KEY bigint(10) unsigned`` [mysql/ACASDB.sql:L156]. Ten digits
    become eighteen and then ten again. The joining rule is offered by
    ``loader.derivation_for`` and performed at the bridge boundary, not
    here; ``WsPostKey`` below carries the detail.

3.  **The byte offsets and the header total contradict the declared
    pictures**, as set out above. 96 written, 98 declared without the
    relative-record field, 103 with it.

4.  **The sign clauses diverge across the three posting copybooks**, as
    set out above, in position, spelling and digit count.

5.  **The same conceptual date is text here and binary elsewhere.**
    ``Post-Date pic x(8)`` [copybooks/wspost.cob:L18] is eight characters
    of text, while ``Run-Date binary-long`` [copybooks/wssystem.cob:L67]
    is a binary day number. Both are in scope; neither is converted to
    the other's storage class.

6.  **The VAT side is tested against bare literals with no condition
    name.** ``Post-Vat-Side`` [copybooks/wspost.cob:L27] is compared
    against ``"CR"`` at [general/gl070.cbl:L503], against ``"DR"`` at
    [general/gl070.cbl:L512] and against ``"CR"`` again at
    [general/gl070.cbl:L529]. The copybook declares no ``88`` level to
    name either state, and none is invented here.

7.  **Two field names collide, forcing qualified references in
    ``gl070``.** Register entry A-21; see "THE NAME COLLISION" below.

8.  **The maintainer's own note names a field that does not exist.**
    [copybooks/wspost.cob:L10] reads ``Added WS-P-rrn to replace relative
    processing``, but the field declared at L13 is ``WS-Post-rrn``.
    ``WS-P-rrn`` occurs exactly once in the whole frozen tree - in that
    comment.

9.  **Not one numeric item is binary on the copybook side.** All eleven
    are zoned DISPLAY and the other four items are alphanumeric: there is
    no ``COMP``, no ``COMP-3`` and no ``binary-`` item anywhere in this
    record, which is unusual in this codebase and the reason the layout is
    character bytes end to end. Nine of the eleven get a host variable of
    their own and EVERY one of those nine is ``COMP``, which
    ``loader.drift_for`` reports as a usage disagreement on each; the
    remaining two, ``Batch`` and ``Post-Number``, get none because the
    bridge folds them into ``POST-KEY``.

10. **The bridge's load paragraph is itself untidy.** ``move CR-PC to
    HV-CR-PC`` [common/glpostingMT.cbl:L1060] carries no terminating
    period, and the paragraph moves the two account fields before the two
    percentage fields, transposing them against both the copybook order
    and the host-variable group's own order. Neither changes a stored
    value; both are evidence that the bridge is hand-edited, which is why
    it is read as the mapping this migration is generated from.

THE NAME COLLISION - A-21, WITH ITS FROZEN-SOURCE SITES AND PARTNER
-------------------------------------------------------------------
``gl070`` qualifies two of this record's fields at three places::

    L497  move     post-code in WS-Posting-Record   to  pre-code.
    L521  if       vat-ac of WS-Posting-Record = zero
    L525  move     vat-ac of WS-Posting-Record  to  pre-ac.

The Agent Action Plan cites this finding at [general/gl070.cbl:L510].
That line reads ``move post-cr to pre-ac.`` and carries no qualifier at
all, so the three locators above are the ones to follow; the plan's is
restated here rather than repeated silently, so that
the migration's traceability document records the difference.

The collision partner is ``copybooks/wssystem.cob``, which ``gl070``
copies at L240 alongside this copybook at L128::

    copybooks/wspost.cob:L17     Post-Code  pic xx.        posting type
    copybooks/wssystem.cob:L77   Post-Code  pic x(12).     client ZIP
    copybooks/wspost.cob:L25     Vat-AC     pic 9(6).      DISPLAY
    copybooks/wssystem.cob:L187  Vat-Ac     binary-long.   binary

One name, two widths and two unrelated meanings in the first pair; one
name differing only in the case of a letter - which COBOL ignores when
matching identifiers - and two different storage classes in the second.
``gl070`` copies neither ``copybooks/wspost-irs.cob`` nor
``copybooks/irswspost.cob``, so those two are not what forces the
qualification there, although ``copybooks/irswspost.cob:L10`` does declare
a bare ``Post-Code`` of its own.

Python's module namespace keeps the three posting records apart without
any qualifier, because each is its own module. The collision is recorded
all the same, so a reader can see why the COBOL must say ``of
WS-Posting-Record`` and cannot be tidied. The three records are three
different tables and are never merged or aliased across
[copybooks/wspost-irs.cob:L6-L7]::

    GLPOSTING-REC   14 columns  acas006      glpostingMT
    PSIRSPOST-REC   10 columns  acas008      slpostingMT
    IRSPOSTING-REC  13 columns  acasirsub4   irspostingMT

THE DESCRIPTOR CONTRACT - LOOKED UP, NEVER TRANSCRIBED (R-5)
------------------------------------------------------------
Not one picture clause, digit count, scale, sign position or storage class
is written by hand below; `records/__init__.py` sets out that convention
for the whole folder, and section 0.8.1 makes the ordering binding rather
than advisory - the dictionary is generated from the bridge before the
record definitions are written, because "it is what prevents fields being
transcribed by eye".

One subtlety is specific to this record and is the reason no key is ever
spelt out by hand: the two halves of it are keyed differently, and guessing
would get three fields wrong::

    the 14 column-backed items    GLPOSTING-REC.<COLUMN-NAME>
    the 3 copybook-only items     WS-Posting-Record.<FIELD-NAME>

``_KEY_BY_COBOL_NAME`` below is therefore built by walking
``loader.entries_for_table("GLPOSTING-REC")`` and then
``loader.entries_for_copybook_record("WS-Posting-Record")`` and reading
each entry's ``copybook.name``. ``Batch`` and ``Post-Number`` fall in the
second group, having no column of their own because the bridge folds them
into ``POST-KEY``; a key naming the table would not exist for either. The
left side of a key is the table name, not the copybook's ``01`` name, and
the right side is the column name, which is not always the field name -
``Post-Date`` is stored in ``POST-DAT``.

``FieldDescriptor.from_dictionary_key`` covers all seventeen entries,
including the two group items, so this module needs no working-storage
fallback. ``loader.cite``, ``loader.drift_for`` and
``loader.derivation_for`` are surfaced through the descriptor and never
reimplemented, and the disagreement between the three layer views is
carried untouched: no one of the three is ever elevated over the other
two here, and none may be.

LAYERING, TYPES AND DETERMINISM
-------------------------------
A leaf module on the terms `records/__init__.py` sets out for the whole
folder: ``acas_posting.cobol.field`` and
``acas_posting.dictionary.loader`` and the standard library, and nothing
else - "this keeps the record layer a leaf". Worth naming here: the two IRS
posting records this docstring compares against are cited by locator and
never imported.

No accounting value passes through a binary floating-point type (R-2)::

    Post-Amount, Vat-Amount     decimal.Decimal   10 digits, scale 2,
                                                  signed, sign trailing
                                                  and included
    the nine unsigned numerics   int              scale 0
    the four alphanumerics       str              at the declared width
    the two group items          no storage of their own

The carrier is taken from each dictionary entry, so the choice between
``Decimal`` and ``int`` is data-driven rather than typed by eye, and money
defaults are ``Decimal("0.00")``.

Attribute order is copybook declaration order, so this file can be set
beside its copybook and read down, and ``FIELDS`` is a tuple. Nothing here
consults a clock, draws an unpredictable value, inspects the process
environment or looks at the filesystem; the only work done at import is
the loader's own lazily cached read of the generated artifact. Two imports
in two processes produce identical state, and execution is strictly
sequential throughout (R-6).
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__ = ["WsPostKey", "WsPostingRecord"]


#  KEY LOOKUP  (R-5)  -  asked of the dictionary, never spelled out

# The two names the dictionary is keyed by for this record. The table name is
# the left half of a column-backed key and the copybook 01-name is the left
# half of a copybook-only key; both are needed because this record has some of
# each. They are the only two literals in the file that name a frozen artifact
# rather than cite one, and every field key is derived from them below.
_TABLE_NAME: Final[str] = "GLPOSTING-REC"
_RECORD_NAME: Final[str] = "WS-Posting-Record"


def _key_by_cobol_name() -> dict[str, str]:
    """Map every COBOL field name in this record to its dictionary key.

    Two passes, because the record is keyed two ways and a single pass
    would miss three fields.

    The first pass walks ``loader.entries_for_table`` and reads each
    entry's ``copybook.name``, which yields the fourteen column-backed
    items under ``GLPOSTING-REC.<COLUMN-NAME>``. It is the table pass that
    supplies ``Post-Date -> GLPOSTING-REC.POST-DAT``, a key no reading of
    the copybook alone would produce.

    The second pass walks ``loader.entries_for_copybook_record`` and takes
    only the entries with no column, which yields the three items the
    bridge carries no host variable for - the ``01`` group itself and the
    two members of the key group, whose digits the bridge folds into
    ``POST-KEY``. Those are keyed
    ``WS-Posting-Record.<FIELD-NAME>``; a key naming the table would not
    exist for them.

    Returns:
        COBOL field name, verbatim from the copybook, to dictionary key.
    """
    mapping: dict[str, str] = {}
    for entry in loader.entries_for_table(_TABLE_NAME):
        if entry.copybook is not None:
            mapping[entry.copybook.name] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD_NAME):
        if entry.copybook is not None and entry.column is None:
            mapping[entry.copybook.name] = entry.key
    return mapping


_KEY_BY_COBOL_NAME: Final[dict[str, str]] = _key_by_cobol_name()


def _descriptor(cobol_name: str) -> FieldDescriptor:
    """Return the descriptor the dictionary holds for one COBOL field.

    The single point at which this module reaches the dictionary for
    storage metadata. Memoised upstream on the key, so the repeated calls
    below cost one lookup each.

    Args:
        cobol_name: The field name exactly as the copybook spells it,
            hyphens and mixed case intact - ``"WS-Post-rrn"``, not
            ``"ws_post_rrn"`` and not ``"WS-POST-RRN"``.

    Returns:
        The descriptor, carrying the copybook view of the field's storage
        plus the provenance that makes it auditable against the frozen
        source.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_BY_COBOL_NAME[cobol_name])


def _spaces(cobol_name: str) -> str:
    """Return the declared width of an alphanumeric field, in spaces.

    The default for every ``str`` attribute below, and the reason they are
    space-filled rather than empty: this is the state a COBOL
    ``INITIALIZE`` leaves an alphanumeric item in, and it is the state the
    bridge's own ``initialize TD-GLPOSTING-REC``
    [common/glpostingMT.cbl:L1053] produces before a write. Defaulting to
    the empty string would put the attribute in a state the COBOL never
    holds, and would then need padding somewhere - and padding belongs to
    ``acas_posting/cobol/move.py``, not to a record layout.

    The width is read from the dictionary, never written down, so a
    28-space legend cannot drift from the copybook's ``pic x(32)``.

    Args:
        cobol_name: The field name exactly as the copybook spells it.

    Returns:
        That many spaces, or the empty string for an item the dictionary
        gives no character length - which none of this record's four
        alphanumeric fields does.
    """
    declared = _descriptor(cobol_name).character_length
    return " " * declared if declared is not None else ""


# Both money fields default to a scale-2 zero. `decimal.Decimal` is immutable,
# so one shared object is safe as a dataclass default and keeps the two amounts
# identical by construction. Never a binary floating-point carrier, and never
# a plain `0`, which would lose the scale (R-2):
# these are the two figures `gl070` adds together at [general/gl070.cbl:L504]
# and [general/gl070.cbl:L513], and the scale has to survive that.
_MONEY_ZERO: Final[decimal.Decimal] = decimal.Decimal("0.00")


#  THE KEY GROUP


@dataclass(slots=True)
class WsPostKey:
    """``03  WS-Post-Key.`` [copybooks/wspost.cob:L14].

    The posting's identity: a batch number and a number within that batch.
    A group item, so it holds no storage of its own - its two five-digit
    members do, and the dictionary describes it as ``usage=GROUP`` with no
    picture, no digit count and no carrier.

    Not frozen. ``gl070`` assigns through this group field by field, at
    [general/gl070.cbl:L495-L496], so the attributes must be settable.

    A-2, recorded and not acted on. The bridge does not keep these two
    fields apart. ``bb000-HV-Load`` moves the group whole -
    ``move WS-Post-Key to HV-POST-KEY`` [common/glpostingMT.cbl:L1054] -
    into ``HV-POST-KEY PIC 9(18) COMP`` [common/glpostingMT.cbl:L283],
    and the schema stores the result as ``POST-KEY bigint(10) unsigned``
    [mysql/ACASDB.sql:L156]. So ten declared digits are joined, carried in
    eighteen, and stored in ten again.

    Note that ``loader.drift_for("GLPOSTING-REC.POST-KEY")`` flags only the
    name disagreement, not the digit widening, and the reason is worth
    knowing: the copybook view is a group with no picture, so there is no
    digit count on that side to disagree with the bridge's eighteen. The
    widening is visible only by adding the two members below - 5 + 5 - and
    comparing. ``loader.derivation_for`` names the joining rule and its
    source line. Neither is performed here; joining the key is
    the `acas006` handler module's work, at the bridge
    boundary where the COBOL does it.

    Attributes:
        batch: Batch number. ``05  Batch  pic 9(5).``
        post_number: Number within the batch. ``05  Post-Number
            pic 9(5).``
    """

    # Batch  pic 9(5)  DISPLAY, unsigned, scale 0    no byte offset comment
    # [copybooks/wspost.cob:L15]  ->  key WS-Posting-Record.Batch
    # Keyed under the copybook record, not the table: this field reaches no
    # column of its own, because the bridge folds it into POST-KEY. The
    # dictionary marks the entry one-sided for exactly that reason.
    batch: int = 0

    # Post-Number  pic 9(5)  DISPLAY, unsigned, scale 0   no offset comment
    # [copybooks/wspost.cob:L16]  ->  key WS-Posting-Record.Post-Number
    # Column-less for the same reason as `batch` above.
    post_number: int = 0

    # Declaration order, as a tuple so it cannot be added to at runtime
    # (R-6). Every element is a dictionary lookup, so nothing about either
    # field's storage is written down twice.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Batch"),
        _descriptor("Post-Number"),
    )


#  THE POSTING RECORD


@dataclass(slots=True)
class WsPostingRecord:
    """``01  WS-Posting-Record.`` [copybooks/wspost.cob:L12].

    The General Ledger posting record, fourteen attributes in copybook
    declaration order, L13 through L28. One attribute per column of
    ``GLPOSTING-REC``, which is what makes the count exactly fourteen: the
    key group stands where the single ``POST-KEY`` column stands, and its
    two members live in ``WsPostKey``.

    Not frozen, and deliberately so. ``gl070`` reads this record and
    ``gl072``'s work stream is built from it; the posting programs assign
    into it one field at a time, so a frozen dataclass would be unusable.

    No ``COMP``, no ``COMP-3`` and no ``binary-`` item appears anywhere in
    this record - every numeric field is zoned ``DISPLAY``. That is
    unusual in this codebase, where the batch, ledger and customer records
    all mix packed and binary storage, and it is why this layout is
    character bytes end to end. The bridge restates all nine numerics as
    ``COMP``, which the dictionary reports as a usage disagreement on each
    one and which this file leaves standing.

    Attributes:
        ws_post_rrn: Relative-record replacement, and the table's primary
            key. See its comment for A-1, the anomaly this module records.
        ws_post_key: The batch and post number, as a group.
        post_code: Posting type code.
        post_date: Posting date, as eight characters of text.
        post_dr: Debit account number.
        dr_pc: Debit profit centre.
        post_cr: Credit account number.
        cr_pc: Credit profit centre.
        post_amount: Posted amount, signed, scale 2.
        post_legend: Free-text narrative.
        vat_ac: VAT account number.
        vat_pc: VAT profit centre.
        post_vat_side: Which side of the posting the VAT falls on.
        vat_amount: VAT amount, signed, scale 2.
    """

    # WS-Post-rrn  pic 9(5)  DISPLAY, unsigned, scale 0  [copybooks/wspost.cob:L13]
    #   -> key GLPOSTING-REC.POST-RRN.   The mixed case is the COBOL's own.
    # A-8: the note at [copybooks/wspost.cob:L10] names `WS-P-rrn`, which is declared nowhere in
    # the frozen tree; the field one line later is `WS-Post-rrn`.
    # A-1: `HV-POST-RRN` [common/glpostingMT.cbl:L282] is the fourteenth host variable and the
    # only one `bb000-HV-Load` never loads - L1053 initializes the group and L1054-L1066 move
    # the other thirteen. `loader.host_variable_for` reports `loaded_from_record=False`,
    # `load_source=None`, `group_initialised_before_load=True`. It is still written out: INSERT
    # [:L1122], UPDATE [:L1311], fetch lists [:L538] and [:L645] - so the zero that `initialize`
    # left reaches PRIMARY KEY `POST-RRN` [mysql/ACASDB.sql:L169]. The maintainer's own warning
    # is [common/glpostingMT.scb:L229]. Nothing is done about it (R-4, section 0.2.2); what the
    # column ends up holding is an R-6 question.
    ws_post_rrn: int = 0

    # WS-Post-Key  group, no picture, no storage of its own, no offset
    # [copybooks/wspost.cob:L14]  ->  key GLPOSTING-REC.POST-KEY
    # A-2: joined into one host variable and widened 10 -> 18 digits at the
    # bridge, then stored in a 10-digit column. Recorded on `WsPostKey`
    # itself, above, and never performed here.
    ws_post_key: WsPostKey = field(default_factory=WsPostKey)

    # Post-Code  pic xx  alphanumeric, 2 characters            *> 12
    # [copybooks/wspost.cob:L17]  ->  key GLPOSTING-REC.POST-CODE
    # A-21, one of the two colliding names. `gl070` must write
    # `post-code in WS-Posting-Record` at [general/gl070.cbl:L497] because
    # `copybooks/wssystem.cob:L77` also declares a `Post-Code`, there a
    # client ZIP code `pic x(12)`. Same name, five times the width, no
    # relation in meaning.
    post_code: str = _spaces("Post-Code")

    # Post-Date  pic x(8)  alphanumeric, 8 characters          *> 20
    # [copybooks/wspost.cob:L18]  ->  key GLPOSTING-REC.POST-DAT
    # EIGHT characters of text. Not ten, not a binary day number. Nothing
    # here reads it, widens it or turns it into a date: all date conversion
    # is `acas_posting/dates.py`'s, and the two-digit against four-digit
    # year forms the schema holds side by side are the dump comparison's
    # business, per section 0.6.6.
    # A-5: the same conceptual date is `Run-Date binary-long` at
    # [copybooks/wssystem.cob:L67] - text in one record and a binary day
    # number in the other. Left as it is.
    # The column is `POST-DAT`, not `POST-DATE` - a name drift the
    # dictionary flags and the reason a bare field name is never a key.
    post_date: str = _spaces("Post-Date")

    # Post-DR  pic 9(6)  DISPLAY, unsigned, scale 0            *> 26
    # [copybooks/wspost.cob:L19]  ->  key GLPOSTING-REC.POST-DR
    # The debit leg's account. Read at [general/gl070.cbl:L501].
    post_dr: int = 0

    # DR-PC  pic 99  DISPLAY, unsigned, scale 0    no byte offset comment
    # [copybooks/wspost.cob:L20]  ->  key GLPOSTING-REC.DR-PC
    # One of the two fields the maintainer left without a running offset.
    dr_pc: int = 0

    # Post-CR  pic 9(6)  DISPLAY, unsigned, scale 0            *> 34
    # [copybooks/wspost.cob:L21]  ->  key GLPOSTING-REC.POST-CR
    # The credit leg's account. Read at [general/gl070.cbl:L510] - which is
    # the line the Agent Action Plan cites for A-21 and which carries no
    # qualifier at all; see the module docstring.
    post_cr: int = 0

    # CR-PC  pic 99  DISPLAY, unsigned, scale 0                *> 36
    # [copybooks/wspost.cob:L22]  ->  key GLPOSTING-REC.CR-PC
    # A-10: the bridge's move into this field's host variable,
    # [common/glpostingMT.cbl:L1060], carries no terminating period, and
    # the paragraph moves the two account fields ahead of the two
    # percentage fields, transposing them against this declaration order.
    # Neither alters a stored value; both are left as found.
    cr_pc: int = 0

    # Post-Amount  pic s9(8)v99  DISPLAY zoned, signed, sign TRAILING and
    #   INCLUDED, 10 digits, scale 2, 10 bytes                    *> 46
    # [copybooks/wspost.cob:L23]  ->  key GLPOSTING-REC.POST-AMOUNT
    # `decimal.Decimal`, never a binary floating-point carrier and never an int - it has a scale
    # (R-2). No USAGE and no SIGN clause is written, so the storage class is the language
    # default and the sign is overpunched on the trailing digit and counted inside the ten
    # bytes. A-4: that bare declaration is what the removal noted at [copybooks/wspost.cob:L7]
    # left behind, and it is why the two IRS posting copybooks disagree with this one; the
    # module docstring carries all six locators.
    # One of the two figures the three-leg explosion works on [general/gl070.cbl:L504], [:L513]
    # and [:L517] - none of which happens here. Digits and scale agree at all three layers; only
    # the storage class differs, DISPLAY against COMP against DECIMAL.
    post_amount: decimal.Decimal = _MONEY_ZERO

    # Post-Legend  pic x(32)  alphanumeric, 32 characters      *> 76
    # [copybooks/wspost.cob:L24]  ->  key GLPOSTING-REC.POST-LEGEND
    # A-3 begins here: 46 + 32 = 78, not the 76 the copybook writes, and
    # every offset after this one is short by the same two bytes. The
    # picture stands at 32 - the bridge says 32
    # [common/glpostingMT.cbl:L291], the schema says 32
    # [mysql/ACASDB.sql:L164], and the dictionary reports no disagreement
    # whatever for this field. The offsets are what went stale. Not
    # widened, not narrowed, not reconciled.
    post_legend: str = _spaces("Post-Legend")

    # Vat-AC  pic 9(6)  DISPLAY, unsigned, scale 0             *> 82
    # [copybooks/wspost.cob:L25]  ->  key GLPOSTING-REC.VAT-AC
    # A-21, the second colliding name, and the subtler of the two.
    # `copybooks/wssystem.cob:L187` declares `Vat-Ac  binary-long.` -
    # differing from this only in the case of one letter, which COBOL
    # ignores when matching an identifier, and carrying an entirely
    # different storage class. Hence `vat-ac of WS-Posting-Record` at
    # [general/gl070.cbl:L521] and again at [general/gl070.cbl:L525].
    vat_ac: int = 0

    # Vat-PC  pic 99  DISPLAY, unsigned, scale 0   no byte offset comment
    # [copybooks/wspost.cob:L26]  ->  key GLPOSTING-REC.VAT-PC
    # The second of the two fields left without a running offset.
    vat_pc: int = 0

    # Post-Vat-Side  pic xx  alphanumeric, 2 characters        *> 86
    # [copybooks/wspost.cob:L27]  ->  key GLPOSTING-REC.POST-VAT-SIDE
    # A-6. This field decides which leg the VAT joins, and it is tested
    # against bare literals: `"CR"` at [general/gl070.cbl:L503], `"DR"` at
    # [general/gl070.cbl:L512], and `"CR"` again at
    # [general/gl070.cbl:L529]. The copybook declares no `88` level naming
    # either state - `grep -c ' 88 ' copybooks/wspost.cob` returns 0 for
    # the whole file - and none is invented here. Were one ever wanted it
    # would belong to `acas_posting/cobol/condition_names.py`, per section
    # 0.4.1.4, and not to a record layout.
    post_vat_side: str = _spaces("Post-Vat-Side")

    # Vat-Amount  pic s9(8)v99  DISPLAY zoned, signed,         *> 96
    #   sign TRAILING and INCLUDED, 10 digits, scale 2, 10 bytes
    # [copybooks/wspost.cob:L28]  ->  key GLPOSTING-REC.VAT-AMOUNT
    # The record's last field, and the offset that closes the copybook's
    # own arithmetic at 96 while the declared pictures reach 98 without
    # `WS-Post-rrn` and 103 with it (A-3). All three figures stand.
    # Declared exactly as `post_amount` is, and read alongside it in the
    # explosion's guard at [general/gl070.cbl:L521-L523], where a VAT leg
    # is written only if this and `vat_ac` are both non-zero. That guard
    # lives in the program module, not here.
    vat_amount: decimal.Decimal = _MONEY_ZERO

    # Declaration order, L13 through L28, as a tuple (R-6). Fourteen
    # descriptors for fourteen attributes and fourteen columns; the key
    # group's own two members are on `WsPostKey.FIELDS`. Every element is a
    # dictionary lookup against a key derived from the artifact, so no
    # picture, digit count, scale, sign position or storage class in this
    # file is written twice or written by hand.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("WS-Post-rrn"),
        _descriptor("WS-Post-Key"),
        _descriptor("Post-Code"),
        _descriptor("Post-Date"),
        _descriptor("Post-DR"),
        _descriptor("DR-PC"),
        _descriptor("Post-CR"),
        _descriptor("CR-PC"),
        _descriptor("Post-Amount"),
        _descriptor("Post-Legend"),
        _descriptor("Vat-AC"),
        _descriptor("Vat-PC"),
        _descriptor("Post-Vat-Side"),
        _descriptor("Vat-Amount"),
    )
