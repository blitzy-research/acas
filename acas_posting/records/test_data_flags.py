"""Record layout for ``01 ACAS-DAL-Common-data.`` [copybooks/Test-Data-Flags.cob:L6].

THIS MODULE IS NOT A TEST - READ THIS BEFORE MOVING IT
------------------------------------------------------
This package holds one module per in-scope COBOL copybook, named after the
copybook it migrates. The copybook here is ``copybooks/Test-Data-Flags.cob``,
so the module is ``test_data_flags.py`` - a name that collides with the default
collection pattern of the pytest runner, ``test_*.py``. The collision is a
naming accident, and the facts are these:

    * this module declares a RECORD LAYOUT and nothing else;
    * it belongs to ``acas_posting/records/`` and never to ``tests/``;
    * it defines no function or class whose name begins with ``test``, makes no
      claim about any value at run time, and imports no test runner.

Do not move it onto a test path and do not rename it. Every handler module in
``acas_posting/dal/`` takes the record declared here as its last parameter, so
this is production code on the write path of the migrated posting cycle; only
the file name suggests otherwise.

WHY A 19-LINE COPYBOOK EARNS A MODULE OF ITS OWN
------------------------------------------------
Because it is the entire test instrumentation of the system being migrated.
From the Agent Action Plan, section 0.1.1: "the only test instrumentation is a
compile-time logging switch [copybooks/Test-Data-Flags.cob:SW-Testing]", and,
restating it beside the only test double in the checkout, section 0.8.2: "the
only test double present anywhere is a stub whose program identifier is itself
misspelled, and the only test instrumentation is a compile-time logging switch
[copybooks/Test-Data-Flags.cob]". That is the corroborating evidence for the
preserved user requirement this whole migration turns on:

    "There is no test suite: compiled COBOL execution is the behavioral
    specification, defects included.
    A defect reproduced is correct; a defect fixed is a failure."

A 484-program accounting system whose only instrumentation is one logging
switch is why the comparison oracle and the anomaly register exist. With no
suite to inherit, the compiled program is the only thing that can say what
correct means - and this record is the switch.

WHAT THE RECORD IS, AND WHERE IT TRAVELS
----------------------------------------
Two switches and one counter of data-access-layer working storage, declared by
a copybook whose own header line reads "This data is present in ALL ACAS
modules" [copybooks/Test-Data-Flags.cob:L2]. Despite the copybook's file name
the record is not test data: its ``01`` line annotates itself "For DAL
processing" [:L6], and it travels as the LAST argument of every file-handler
call in the cycle. From section 0.4.3, the translation that fixes the parameter
order::

    FROM:  call "acas007" using System-Record WS-Batch-Record File-Access
                                File-Defs ACAS-DAL-Common-Data
    TO:    acas007_gl_batch.dispatch(system, batch, file_access, file_defs,
                                     dal_common)

``dal_common`` is an instance of the class below. The dependency runs from
``dal`` to ``records`` and never the other way.

It declares the record and no more. It does not write a log record, read a
switch, step the counter or dispatch anything. The switches are consulted by
whatever holds the record, and the two ``88`` condition names over them belong
to ``acas_posting/cobol/condition_names.py`` (section 0.4.1.4). Rule R-3 -
nothing added - is why there is no helper here of any kind: no predicate, no
counter step, no convenience reading of "logging on", no check on a value.

THE FIELDS, AND THE VALUE CLAUSES THAT SET THEIR DEFAULTS
---------------------------------------------------------
The copybook is 19 lines and declares three storage items under one group::

     01 ACAS-DAL-Common-data.     *> For DAL processing.           L6
         03  SW-Testing            pic 9    value 1.   *>  zero.   L10
             88  Testing-1                  value 1.               L11
         03  SW-Testing-2          pic 9    value zero.            L15
             88  Testing-2                  value 1.               L16
         03  Log-File-Rec-Written  pic 9(6) value zero.            L18

Each ``value`` clause above is the default of the corresponding attribute
below. The defaults are the copybook's, not this file's, and one of them
matters a great deal: ``SW-Testing`` is declared ``value 1``, so file-handler
logging is ON in the frozen source. See ANOMALIES.

All three items are ``DISPLAY`` of scale zero and carry no sign - their
pictures have no leading ``S`` - so all three are held by the Python ``int``
type. That choice is not made here either: it is read from the generated data
dictionary, which reports the carrier as INT for each of the three (rule R-2).
No accounting value passes through this record. It holds a switch, a switch and
a count.

PROVENANCE - LOOKED UP, NEVER TRANSCRIBED  (rule R-5)
-----------------------------------------------------
Nothing below writes a picture clause, a digit count or a scale by hand. Each
field takes its storage description from the generated data dictionary through
``FieldDescriptor.from_dictionary_key``, keyed
``<COPYBOOK-RECORD>.<FIELD-NAME>``: ``ACAS-DAL-Common-data.SW-Testing``,
``.SW-Testing-2`` and ``.Log-File-Rec-Written``. Note the casing - the
dictionary keys these entries exactly as the copybook spells them, so an
upper-cased key such as ``ACAS-DAL-COMMON-DATA.SW-TESTING`` names no entry at
all. Section 0.3.3 gives the reason the lookup exists: "Field metadata is
therefore derived, not transcribed, which eliminates an entire class of
transcription error across several hundred fields."

This record maps to NO MySQL table. It is working storage of the data-access
layer, absent from the entity-to-table spine of section 0.2.1.1, and the
dictionary says so itself - each field's provenance line renders its bridge
host variable and its column as ``absent``::

    ACAS-DAL-Common-data.SW-Testing
        copybook=copybooks/Test-Data-Flags.cob:L10
        bridge=absent  column=absent

That line comes from ``FieldDescriptor.cite()``, which delegates to
``acas_posting.dictionary.loader.cite``. It is surfaced, never reimplemented,
and the loader is reached through the descriptor rather than imported directly.

ANOMALIES REPRODUCED HERE, NEVER FIXED  (rule R-4)
--------------------------------------------------
Four oddities live in these 19 lines. All four are preserved, and each is
commented at the point it is reproduced with its locator, as section 0.7.4
requires.

1.  ``SW-Testing`` defaults to 1, so logging is ON in the frozen source
    [copybooks/Test-Data-Flags.cob:L10]. The maintainer's own header says what
    the switch is for, typo included - "When testing comlete you can set
    SW-Testing to zero to stop the logging file being produced" [:L3-L4] - and
    he left an inline ``*> zero.`` beside the live ``value 1`` as a note of the
    alternative he never took [:L10]. Testing was evidently never declared
    complete: the shipped value is 1. Defaulting ``sw_testing`` to 0 here is
    the obvious modern instinct and it is forbidden - a defect reproduced is
    correct, a defect fixed is a failure. The consequence is concrete rather
    than theoretical: at the frozen default the file-handler log grows without
    bound, and reached 473 MB within three minutes during an oracle bootstrap
    on this project. Rotate the log; do not move the default.

2.  The two switches carry identically shaped condition names - ``88 Testing-1
    value 1`` [:L11] over one and ``88 Testing-2 value 1`` [:L16] over the
    other - yet their defaults differ, 1 against 0. Recorded, not smoothed.

3.  The copybook is called ``Test-Data-Flags.cob`` while the record it declares
    is ``ACAS-DAL-Common-data``, annotated "For DAL processing" [:L6]. Name and
    role disagree. Neither side is renamed.

4.  The ``01`` name mixes its own casing - ``ACAS-DAL-Common-data``, with a
    lower-case ``d`` on ``data``. It is quoted verbatim throughout, and this
    package's mechanical naming rule - drop the hyphens, capitalise each part -
    turns it into ``AcasDalCommonData``. File name, record name and type name
    therefore all differ, and all three are right.

    The call sites do not agree with the declaration either. COBOL names are
    case-insensitive, so the frozen tree carries both spellings: counted over
    the seven frozen COBOL directories - ``common``, ``copybooks``,
    ``general``, ``sales``, ``purchase``, ``irs`` and ``stock`` - the declared
    ``ACAS-DAL-Common-data`` appears 414 times and ``ACAS-DAL-Common-Data`` 19
    times, the latter only in ``common`` and ``copybooks``. The capital ``D``
    in the ``CALL`` quoted further up is therefore the source's own, reproduced
    rather than tidied; the declaration at L6 is what this module follows.

There is deliberately no tidied or settled reading of any of these, and none
may be introduced. The register of every such site is the migration's anomaly
log.

LAYERING (0.4.3), DETERMINISM (R-6) AND NO COBOL AT RUNTIME (R-1)
-----------------------------------------------------------------
``dal`` is the live temptation, because every handler module takes this record
as a parameter. The arrow points one way: ``dal`` imports ``records``.
Reversing it would drag a database driver into the arithmetic parity tier,
which section 0.4.3 promises "imports only ``cobol`` and ``records`` and
touches no database, so it runs anywhere".

Attribute order is copybook declaration order - L10, then L15, then L18 - so
this module can be set beside its copybook and diffed by eye. ``FIELDS`` is a
tuple and not a list, because a fixed collection that cannot be reordered in
place cannot make two runs differ. Nothing here consults a clock, draws an
unpredictable value, inspects the process environment or performs any
import-time input or output beyond the loader's own lazily cached read of the
generated dictionary.

One instinct is worth naming because it is both obvious and wrong: reading
``SW-Testing`` from an environment variable. A switch that ambient state can
move is a switch that makes two runs of one scenario differ. This one's value
comes from the copybook's ``value`` clause and from whatever a caller assigns
to it - never from outside the process.

The COBOL tree is frozen: read as the specification for this migration and
never modified. This module opens ``copybooks/Test-Data-Flags.cob`` at no point
during execution - that copybook's content reached it through the generated
dictionary - and it executes, embeds and shells out to nothing. It runs on a
host with no COBOL compiler and no COBOL runtime present. See
``acas_posting.records`` for the conventions every record module shares.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from acas_posting.cobol.field import FieldDescriptor

__all__: list[str] = ["AcasDalCommonData"]


#   THE STORAGE DESCRIPTION OF EACH ITEM  (rule R-5)
# One lookup per storage item, keyed <COPYBOOK-RECORD>.<FIELD-NAME> in the copybook's own
# casing. The dictionary reports all three as DISPLAY of scale zero with no sign, held by int,
# and each descriptor arrives carrying both halves of its provenance - the dictionary key and
# the copybook locator - so cite() can render the full line for any of them.
# The group item itself, ACAS-DAL-Common-data at L6, is catalogued too and is deliberately NOT
# looked up here: a group has no storage of its own, and the class below IS the group. Reading
# the record back out of the dictionary therefore yields four entries where this module declares
# three attributes. That is the copybook's own shape, not a disagreement.
# These three names are module attributes and not exports; __all__ at L224 publishes the record
# type alone, per the import contract of section 0.4.3.

SW_TESTING: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "ACAS-DAL-Common-data.SW-Testing"
)

SW_TESTING_2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "ACAS-DAL-Common-data.SW-Testing-2"
)

LOG_FILE_REC_WRITTEN: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "ACAS-DAL-Common-data.Log-File-Rec-Written"
)

# Declaration order, L10 then L15 then L18, matching the attribute order of
# the record below. A tuple, so no holder can reorder it in place (rule R-6).
FIELDS: Final[tuple[FieldDescriptor, ...]] = (
    SW_TESTING,
    SW_TESTING_2,
    LOG_FILE_REC_WRITTEN,
)


#  THE RECORD


@dataclass(slots=True)
class AcasDalCommonData:
    """``01 ACAS-DAL-Common-data.`` [copybooks/Test-Data-Flags.cob:L6].

    The data-access layer's common state: two switches and one counter. The
    COBOL name is quoted above exactly as the maintainer wrote it, mixed casing
    and all - upper-case ``ACAS-DAL``, capitalised ``Common``, lower-case
    ``data``.

    MUTABLE, deliberately. ``Log-File-Rec-Written`` is a counter that the file
    handlers and the data-access layer step as log records are written - the
    copybook says as much, annotating it "in both acas0nn and a DAL"
    [copybooks/Test-Data-Flags.cob:L18] - so the record is working storage its
    holder updates in place, and freezing it would make the count impossible
    to keep. It is slotted so that a fourth attribute cannot be attached by
    accident: the copybook declares three items, and rule R-3 forbids adding
    a fourth.

    Every default below is the ``value`` clause of the corresponding copybook
    item, reproduced rather than chosen, so constructing the record with no
    arguments reproduces the state a COBOL program starts with::

        >>> AcasDalCommonData()
        AcasDalCommonData(sw_testing=1, sw_testing_2=0, log_file_rec_written=0)

    The storage description of each attribute is in the matching module
    constant - ``SW_TESTING``, ``SW_TESTING_2`` and ``LOG_FILE_REC_WRITTEN`` -
    and ``FIELDS`` holds all three in declaration order.

    Attributes:
        sw_testing: ``SW-Testing``, the file-handler logging switch. 1 in the
            frozen source, which means logging ON.
        sw_testing_2: ``SW-Testing-2``, the display-tracing switch. Zero in
            the frozen source.
        log_file_rec_written: ``Log-File-Rec-Written``, the count of log
            records written. Zero in the frozen source.
    """

    # SW-Testing  pic 9  value 1          [copybooks/Test-Data-Flags.cob:L10]
    # "log file reporting for testing otherwise zero" [L8]. The default is the
    # copybook's own `value 1`, PRESERVED: logging is on in the frozen source,
    # and the maintainer's inline `*> zero.` on that same line records the
    # alternative he never took. Defaulting this to 0 would fix a defect the
    # specification requires be reproduced (rule R-4).
    # `88 Testing-1 value 1` [L11] is declared over this item. The predicate
    # that evaluates it belongs to acas_posting/cobol/condition_names.py
    # (section 0.4.1.4), not here.
    sw_testing: int = 1

    # SW-Testing-2  pic 9  value zero     [copybooks/Test-Data-Flags.cob:L15]
    # "Testing only for displays ws-where etc  otherwise zero" [L13]. Zero in
    # the frozen source, where the other switch defaults to 1 - and both carry
    # an identically shaped condition name. The asymmetry is the copybook's
    # and is left as it stands (rule R-4).
    # `88 Testing-2 value 1` [L16] is declared over this item; its predicate
    # also belongs to acas_posting/cobol/condition_names.py.
    sw_testing_2: int = 0

    # Log-File-Rec-Written  pic 9(6)  value zero
    #                                     [copybooks/Test-Data-Flags.cob:L18]
    # The count of log records written, "in both acas0nn and a DAL" [L18] -
    # the file handlers and the data-access layer share the one counter. Six
    # digits, no sign, scale zero, so LOG_FILE_REC_WRITTEN reports the domain
    # 0 through 999999; what a store does at that boundary is the arithmetic
    # layer's business, not this record's. Stepping the counter is the
    # caller's business too. This module only declares it.
    log_file_rec_written: int = 0
