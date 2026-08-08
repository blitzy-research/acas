"""The three-leg double-entry explosion of `gl070` Phase 2, locked against repair.

One entered posting record becomes THREE `pre-trans-record` writes: a debit leg, a
credit leg that is ALWAYS negated, and a value-added-tax leg that is written only
when both the tax account and the tax amount are non-zero and that is negated
only SOMETIMES. This module asserts the values those three legs carry, for every
`post-vat-side` case and for every combination of the two-part guard, and it locks
anomaly A-21 - the field-name collisions that force `gl070` to write qualified
references, mixing the `in` and `of` synonyms.

THE BLOCK, VERBATIM FROM THE FROZEN SOURCE [general/gl070.cbl:L495-L533]. Read out
of the checkout and reproduced here character for character, because every expected
value below is an assertion about these thirty-nine lines - thirty statements
and nine `*>` separators, kept so that the listing and the line numbers agree::

     495:     move     batch        to  pre-batch.
     496:     move     post-number  to  pre-post.
     497:     move     post-code in WS-Posting-Record   to  pre-code.
     498:     move     post-date    to  pre-date.
     499:     move     post-legend  to  pre-legend.
     500:*>
     501:     move     post-dr      to  pre-ac.
     502:     move     dr-pc        to  pre-pc.
     503:     if       post-vat-side = "CR"
     504:              add  post-amount  vat-amount  giving  pre-amount
     505:     else
     506:              move post-amount  to  pre-amount.
     507:*>
     508:     write    pre-trans-record.
     509:*>
     510:     move     post-cr      to  pre-ac.
     511:     move     cr-pc        to  pre-pc.
     512:     if       post-vat-side = "DR"
     513:              add  post-amount  vat-amount  giving  pre-amount
     514:     else
     515:              move post-amount  to  pre-amount.
     516:*>
     517:     multiply pre-amount  by  -1  giving  pre-amount.
     518:*>
     519:     write    pre-trans-record.
     520:*>
     521:     if       vat-ac of WS-Posting-Record = zero
     522:           or vat-amount = zero
     523:              go to  loop.
     524:*>
     525:     move     vat-ac of WS-Posting-Record  to  pre-ac.
     526:     move     vat-pc           to      pre-pc.
     527:     move     vat-amount       to      pre-amount.
     528:*>
     529:     if       post-vat-side = "CR"
     530:              multiply  pre-amount  by  -1 giving pre-amount.
     531:*>
     532:     write    pre-trans-record.
     533:     go       to loop.

THE TWO `-1` MULTIPLIES ARE NOT THE SAME STATEMENT TWICE. This is the single fact
most likely to be lost to a well-meant refactor, so it is asserted from both
directions:

    [general/gl070.cbl:L517]      UNCONDITIONAL. The credit leg is negated on
                                  EVERY posting, whatever `post-vat-side` holds.
                                  It is a statement of its own, at the same
                                  indentation as the `write` that follows it.
    [general/gl070.cbl:L529-L530] CONDITIONAL on `post-vat-side = "CR"`. The tax
                                  leg is negated only when the side is credit,
                                  and is left POSITIVE otherwise.

`grep -nE "multiply.*by +-1" general/gl070.cbl` returns exactly those two lines and
no others. Factor them into one shared negation helper and the debit-side case
silently starts negating the tax leg; `test_unifying_the_two_negations_would_break`
is the test that fails when someone does.

THE VAT-INCLUSIVE LOGIC IS DELIBERATELY CROSSED, AND IS NOT A BUG TO BE FIXED.
THE LEG THAT ABSORBS THE TAX IS THE OPPOSITE OF THE NAMED SIDE:

    [general/gl070.cbl:L503-L504]  the DEBIT leg absorbs the tax when the side is
                                   `"CR"`.
    [general/gl070.cbl:L512-L513]  the CREDIT leg absorbs the tax when the side is
                                   `"DR"`.

That reads backwards and it is correct: `post-vat-side` names the side the TAX
itself is posted to, so the OTHER leg is the one that must carry the tax-inclusive
gross. Every cell of the three-by-three table in
`test_crossed_vat_inclusive_logic_every_cell` is asserted, and no test in this file
asserts that the three legs sum to zero - see the R-4 note below.

THE TAX LEG IS SKIPPED ON A TWO-PART DISJUNCTION [general/gl070.cbl:L521-L523], so
it is written only when BOTH the account and the amount are non-zero. All four
combinations are tested, and on each of the three skip paths the debit and credit
legs HAVE STILL BEEN PRODUCED - the `go to loop` at L523 sits AFTER the writes at
L508 and L519, so a skip removes the third leg and nothing else.

ANOMALY A-21 - FIELD-NAME COLLISIONS FORCE QUALIFIED REFERENCES, AND THE TWO
SYNONYMS ARE MIXED. `gl070` COPYs both `wspost.cob` [general/gl070.cbl:L128] and
`wssystem.cob` [general/gl070.cbl:L240], and each of those declares a field the
other also declares, so three references in this block must name their record:

    [general/gl070.cbl:L497]  `move post-code IN WS-Posting-Record to pre-code.`
    [general/gl070.cbl:L521]  `if vat-ac OF WS-Posting-Record = zero`
    [general/gl070.cbl:L525]  `move vat-ac OF WS-Posting-Record to pre-ac.`

CITATION CORRECTION, recorded because the Agent Action Plan's anomaly register
cites `[general/gl070.cbl:L510]` as the A-21 site for this program: L510 is `move
post-cr to pre-ac.` and is NOT qualified. The three qualified references are at
L497, L521 and L525, and L497 spells the qualifier `in` while L521 and L525 spell
it `of` - COBOL synonyms, used inconsistently within twenty-nine lines.

`gl070` HAS NO `ROUNDED` SITE. `grep -ciE "\\brounded\\b" general/gl070.cbl`
returns 0. The whole migrated cycle contains exactly FIVE `ROUNDED` stores -
[general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
[irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - and not one of them is in this
program, so every store composed below is made with `rounded=False`. Agent Action
Plan section 0.1.1: "Getting this backwards would corrupt essentially every posted
figure."

THE SIX BINDING RULES R-1 to R-6 live in Agent Action Plan section 0.7.2, and their
exact wording is retrievable from the requirements; where they are silent,
enterprise-standard best practice applies. Summarised in this module's own words,
and each named at the site that honours it:

    R-1  No COBOL at runtime. This module executes no COBOL, opens no database,
         spawns no subprocess and reads no `.cbl` file. Note what the three legs
         are: `write pre-trans-record` statements to `pretrans.tmp`, a transient
         work file that is NOT part of the schema [copybooks/wsnames.cob:L15-L16],
         so this module asserts the record VALUES the block produces and never a
         write. The migration's own work-file module, which models the two General
         Ledger scratch files, is deliberately NOT imported here - it sits outside
         this tier's allowance, and nothing below needs it.
    R-2  Zero binary floating point. Every value here is a `decimal.Decimal`, an
         `int` or a `str`. There is no float literal, no tolerance, no epsilon, no
         approximate comparison, and no `pandas` or `numpy`. The ambient
         `decimal` context is neither read nor mutated: `acas_posting.cobol
         .arithmetic` enters its own context for every operation.
    R-3  No new validations, fields or schema changes; no concurrency. The tax-leg
         skip reproduced here is EXACTLY the two-part disjunction at L521-L523 and
         nothing more. Nothing checks that the debit and credit legs balance;
         nothing checks that `post-vat-side` is one of `"DR"` or `"CR"`, because
         `post-vat-side` is `pic xx` [copybooks/wspost.cob:L27] and the frozen
         program validates it nowhere. Strictly sequential; no parallel runner.
    R-4  Legacy anomalies are reproduced, never fixed. A defect reproduced is
         correct; a defect fixed is a failure. Its corollary governs what this file
         may assert: a test that asserted CORRECT ACCOUNTING rather than OBSERVED
         BEHAVIOUR would itself be the defect, so NO TEST HERE ASSERTS THAT THE
         THREE LEGS SUM TO ZERO. For the two named sides they happen to; for any
         third `post-vat-side` value they do not, and both outcomes are recorded as
         values rather than as a balance rule. Every reproduction site carries a
         comment naming its anomaly and its `[general/gl070.cbl:Lnnn]` locator.
    R-5  Full traceability. Every test names the line or lines it locks. Every
         descriptor is reached through a table-qualified data-dictionary key, or
         through the program-source key of a work-record field, and never by a bare
         field name. Coverage is evidence, never a gate.
    R-6  Compiled behaviour is the tie-breaker. The file contained exactly ONE
         un-arbitrated observable and it is now MEASURED, so there is
         no `xfail` here; the reading the marker used to assert is asserted AGAINST,
         so a change back to it fails by name:

             Q-70f  The ON-THE-WIRE SIGN of a NEGATED ZERO. `multiply pre-amount
                    by -1 giving pre-amount` [general/gl070.cbl:L517] applied to a
                    zero amount: does the compiled program leave the positive
                    overpunch in the sign-carrying digit of the zoned item, or
                    write the negative one? `-0.00 == 0.00` is True, so the sign of
                    zero is invisible to every comparison and only the stored bytes
                    could tell them apart. MEASURED: the compiled program leaves the
                    POSITIVE overpunch, byte 10 reading `0` (0x30) after the frozen
                    multiply and after a `compute` of the same shape, while a
                    LITERAL `move -0.00` writes `p` (0x70) - so the sign
                    normalisation belongs to the ZERO and not to the statement, and
                    the frozen statement is arithmetic rather than a literal move.
                    The id continues `gl070`'s own question family, which runs
                    Q-70a, Q-70b, Q-70d and Q-70e in
                    `acas_posting/programs/gl070_transaction_pre_process.py`.

         Everything else this file asserts is settled: the block itself was read
         out of the frozen checkout, and the storage shapes come from the generated
         data dictionary. The two questions those shapes rest on HAVE since been
         measured - `acas_posting.cobol.arithmetic`'s question Q-2 and
         `acas_posting.cobol.usage`'s Q-5.1 to Q-5.3 are all `RESOLVED BY ORACLE`
         (2026-08-07), so the values those modules carry are confirmed readings
         rather than documented defaults. No figure in this file reaches either
         question in any case: every operand is a two-place decimal or an integer,
         and this file still asserts no measurement of its own.

    Also binding - Agent Action Plan section 0.8.4: no timing assertion and no
    performance measurement appears anywhere in this file.

INFRASTRUCTURE: NONE. This module runs on a bare host with no Docker, no MariaDB
and no GnuCOBOL. Its one prerequisite is
`data_dictionary/acas_posting_dictionary.json`, which
`FieldDescriptor.from_dictionary_key` reads at import.
"""

from __future__ import annotations

import dataclasses
import decimal
from decimal import Decimal
from pathlib import Path

import pytest

from acas_posting.cobol import arithmetic
from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import move as cobol_move
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model
from acas_posting.records import work_records

# Imports carried in with the merged group below, which was
# test_shipped_close_and_rejection_paths.py. Only the pieces the block above did not
# already provide are listed (Agent Action Plan section 0.3.1 inventory).
import contextlib
import importlib
import logging
import sys
import types
from collections.abc import Iterator, Mapping
from typing import Any, Final

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
# Defensive dictionary-key resolution, local to this file.
#
# The generated artifact keys every entry by QUALIFIER, and the qualifier is what
# makes anomaly A-21 tractable: `<TABLE-NAME>.<COLUMN-NAME>` for a field that
# reaches a table, `<COPYBOOK-RECORD>.<FIELD-NAME>` for one that does not, and
# `<PROGRAM-RECORD>.<FIELD-NAME>#<declaration line>` for a working-storage or
# file-section field a program declares for itself. The trailing `#<line>` segment
# is the only part of a key that can legitimately move when the artifact is
# regenerated - a field keeps its name and its record but its declaration line is
# a coordinate into a frozen file that this test tree does not read. So the exact
# key is tried first, and a miss falls back to a name match within the same
# qualifier rather than failing the whole module at import.
#
# `loader.DictionaryKeyError` and `loader.DictionaryLookupError` are both `KeyError`
# subclasses, which is what makes a near-miss catchable without swallowing anything
# else.
# ---------------------------------------------------------------------------


class _UnresolvableKey(LookupError):
    """No dictionary entry answers a key, even after the near-miss fallback.

    A PROGRAMMER error rather than a data condition: it means this file names a
    field the generated artifact does not carry at all, which no fallback can
    repair and which must not be papered over with a synthesised descriptor.
    """


def _entries_under(qualifier: str) -> tuple[model.DictionaryEntry, ...]:
    """Return every entry whose key sits under one qualifier.

    `loader.entries_for_table` is tried first because it is the artifact's own
    index and is the cheap path for the twenty-two in-scope tables. It raises for a
    qualifier that is not a table name - a copybook record, or a program record
    such as `pre-trans-record` - so the fall-back is a scan of the key list, which
    answers for every qualifier the artifact carries.

    Args:
        qualifier: The part of an entry key before its final dot.

    Returns:
        The entries under that qualifier, in artifact order. Empty when the
            qualifier is unknown.
    """
    try:
        return loader.entries_for_table(qualifier)
    except KeyError:
        # Not a table. Fall through to the universal scan below rather than
        # guessing which of the other two key forms applies.
        pass
    folded = qualifier.casefold()
    return tuple(
        loader.get_entry(key)
        for key in loader.entry_keys()
        if key.rpartition(".")[0].casefold() == folded
    )


def _descriptor(key: str) -> cobol_field.FieldDescriptor:
    """Resolve one dictionary key to its `FieldDescriptor`, tolerating a near miss.

    Args:
        key: A qualified entry key, exact and case-sensitive, with the `#<line>`
            segment where the artifact carries one.

    Returns:
        The descriptor the artifact holds for that field.

    Raises:
        _UnresolvableKey: Neither the exact key nor any field of the same name
            under the same qualifier is in the artifact.
    """
    try:
        return cobol_field.FieldDescriptor.from_dictionary_key(key)
    except KeyError:
        # A near miss: same field, moved declaration line, or a case difference in
        # a qualifier. Anything else falls through to _UnresolvableKey below.
        pass

    qualifier, _, tail = key.rpartition(".")
    wanted = tail.partition("#")[0].casefold()
    for entry in _entries_under(qualifier):
        candidate = entry.key.rpartition(".")[2].partition("#")[0]
        if candidate.casefold() == wanted:
            return cobol_field.FieldDescriptor.from_dictionary_key(entry.key)
    raise _UnresolvableKey(
        f"the ACAS posting data dictionary carries no entry for {key!r}, and no "
        f"field named {tail!r} under qualifier {qualifier!r}"
    )


# ---------------------------------------------------------------------------
# The two records the block moves between.
# ---------------------------------------------------------------------------

#: `01 WS-Posting-Record.` [copybooks/wspost.cob:L12-L28] - the SENDING record. Keyed
#: by TABLE for every field that reaches `GLPOSTING-REC`, and by COPYBOOK RECORD for
#: the two `05` children of `WS-Post-Key`, which the table stores as one column. The
#: qualification is the whole point: `Post-Code` and `Vat-AC` are also declared in
#: `wssystem.cob`, which is why L497, L521 and L525 must name their record (A-21).
_SENDING: dict[str, cobol_field.FieldDescriptor] = {
    # `05 Batch pic 9(5).` [copybooks/wspost.cob:L15] - sender of L495.
    "batch": _descriptor("WS-Posting-Record.Batch"),
    # `05 Post-Number pic 9(5).` [copybooks/wspost.cob:L16] - sender of L496.
    "post_number": _descriptor("WS-Posting-Record.Post-Number"),
    # `03 Post-Code pic xx.` [copybooks/wspost.cob:L17] - sender of L497, the first
    # A-21 site.
    "post_code": _descriptor("GLPOSTING-REC.POST-CODE"),
    # `03 Post-Date pic x(8).` [copybooks/wspost.cob:L18] - sender of L498. The
    # column is spelled POST-DAT, which is why the key is not POST-DATE.
    "post_date": _descriptor("GLPOSTING-REC.POST-DAT"),
    # `03 Post-Legend pic x(32).` [copybooks/wspost.cob:L24] - sender of L499.
    "post_legend": _descriptor("GLPOSTING-REC.POST-LEGEND"),
    # `03 Post-DR pic 9(6).` / `03 DR-PC pic 99.` [copybooks/wspost.cob:L19-L20] -
    # senders of L501 and L502.
    "post_dr": _descriptor("GLPOSTING-REC.POST-DR"),
    "dr_pc": _descriptor("GLPOSTING-REC.DR-PC"),
    # `03 Post-CR pic 9(6).` / `03 CR-PC pic 99.` [copybooks/wspost.cob:L21-L22] -
    # senders of L510 and L511.
    "post_cr": _descriptor("GLPOSTING-REC.POST-CR"),
    "cr_pc": _descriptor("GLPOSTING-REC.CR-PC"),
    # `03 Post-Amount pic s9(8)v99.` [copybooks/wspost.cob:L23] - operand of the two
    # `add ... giving` at L504 and L513, and sender of L506 and L515.
    "post_amount": _descriptor("GLPOSTING-REC.POST-AMOUNT"),
    # `03 Vat-AC pic 9(6).` [copybooks/wspost.cob:L25] - tested at L521 and sent at
    # L525, qualified at BOTH sites (A-21).
    "vat_ac": _descriptor("GLPOSTING-REC.VAT-AC"),
    # `03 Vat-PC pic 99.` [copybooks/wspost.cob:L26] - sender of L526.
    "vat_pc": _descriptor("GLPOSTING-REC.VAT-PC"),
    # `03 Post-Vat-Side pic xx.` [copybooks/wspost.cob:L27] - the two-character
    # switch tested at L503, L512 and L529. NOTHING VALIDATES IT (R-3).
    "post_vat_side": _descriptor("GLPOSTING-REC.POST-VAT-SIDE"),
    # `03 Vat-Amount pic s9(8)v99.` [copybooks/wspost.cob:L28] - operand of L504 and
    # L513, tested at L522, sender of L527.
    "vat_amount": _descriptor("GLPOSTING-REC.VAT-AMOUNT"),
}


def _receiving() -> dict[str, cobol_field.FieldDescriptor]:
    """Map each `pre-trans-record` attribute to the descriptor it carries.

    `acas_posting.records.work_records` attaches the `FieldDescriptor` of every
    field of `01 pre-trans-record.` [general/gl070.cbl:L108-L116] to the dataclass
    member's `metadata`, and its module docstring publishes this loop as the way to
    read them back. Going through the record rather than through eight literal keys
    is what guarantees this file and the migrated program describe the same eight
    fields: the record is the one place their shapes are declared.

    Returns:
        Attribute name to descriptor, for all eight members, in declaration order.
    """
    return {
        member.name: member.metadata[work_records.COBOL_FIELD_METADATA_KEY]
        for member in dataclasses.fields(work_records.PreTransRecord)
    }


#: `01 pre-trans-record.` [general/gl070.cbl:L108-L116], mirrored field for field at
#: [general/gl071.cbl:L112-L120] - the RECEIVING record. It has no copybook, no
#: bridge and no table, so its dictionary entries are program-source entries keyed
#: `pre-trans-record.<field>#<declaration line>` and they carry ZERO drift.
_RECEIVING: dict[str, cobol_field.FieldDescriptor] = _receiving()


# ---------------------------------------------------------------------------
# The literals and the vocabulary the block itself uses.
# ---------------------------------------------------------------------------

#: `if post-vat-side = "CR"` [general/gl070.cbl:L503], [general/gl070.cbl:L529].
_SIDE_CREDIT = "CR"

#: `if post-vat-side = "DR"` [general/gl070.cbl:L512].
_SIDE_DEBIT = "DR"

#: A third value for the two-character switch. `post-vat-side` is `pic xx`
#: [copybooks/wspost.cob:L27] and no statement in the frozen program constrains it,
#: so a batch entered with anything else takes the `else` of BOTH L503 and L512 and
#: fails the test at L529. Spaces are the value an unset `pic xx` holds.
_SIDE_UNSET = "  "

#: A fourth value, chosen to show that the third case is about "not CR and not DR"
#: rather than about spaces in particular.
_SIDE_OTHER = "XX"

#: `= zero` [general/gl070.cbl:L521-L522]. A `decimal.Decimal`, so a scale-2 amount
#: and a scale-0 account number both compare against it without any coercion.
_ZERO = Decimal(0)

#: The literal the two negations multiply by [general/gl070.cbl:L517],
#: [general/gl070.cbl:L530]. An `int`, exactly as the COBOL writes an integer
#: literal, never a float (R-2).
_MINUS_ONE = -1

#: The scale `pre-amount` imposes on every amount the block stores
#: [general/gl070.cbl:L115]. `Decimal.as_tuple().exponent` is the negative of it.
_AMOUNT_SCALE = 2

#: `pic s9(8)v99` DISPLAY occupies TEN bytes, one per digit, with the sign
#: overpunched onto the last digit rather than spending a byte of its own. Proven
#: twice over by the copybook's own running offset comments, which are cumulative
#: byte positions: `CR-PC` ends at 36 [copybooks/wspost.cob:L22] and `Post-Amount`
#: ends at 46 [copybooks/wspost.cob:L23], a span of ten; independently
#: `Post-Vat-Side` ends at 86 [copybooks/wspost.cob:L27] and `Vat-Amount` ends at 96
#: [copybooks/wspost.cob:L28], the same ten. A HARD FACT, asserted plainly.
_AMOUNT_BYTES = 10


# ---------------------------------------------------------------------------
# The entered posting the block reads, and the transcription of the block itself.
#
# There is deliberately NO `explode`, `double_entry` or `post_legs` helper anywhere
# in `acas_posting`, and this file creates none: the function below is not a
# business abstraction but this MODULE'S OWN TRANSCRIPTION of thirty frozen
# lines, one statement at a time, each carrying the line it reproduces. It composes
# nothing but `acas_posting.cobol.arithmetic` and `acas_posting.cobol.move` calls,
# and it exists in exactly one place so that a single edit to the transcription -
# unifying the two negations, say - breaks every test that depends on the
# difference rather than one.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class _EnteredPosting:
    """The `01 WS-Posting-Record.` fields [general/gl070.cbl:L495-L533] reads.

    Frozen, because the block reads the posting and never writes back to it: every
    store in those thirty statements lands in `pre-trans-record`.

    Attributes:
        batch: `05 Batch pic 9(5).` [copybooks/wspost.cob:L15].
        post_number: `05 Post-Number pic 9(5).` [copybooks/wspost.cob:L16].
        post_code: `03 Post-Code pic xx.` [copybooks/wspost.cob:L17].
        post_date: `03 Post-Date pic x(8).` [copybooks/wspost.cob:L18].
        post_legend: `03 Post-Legend pic x(32).` [copybooks/wspost.cob:L24].
        post_dr: `03 Post-DR pic 9(6).` [copybooks/wspost.cob:L19].
        dr_pc: `03 DR-PC pic 99.` [copybooks/wspost.cob:L20].
        post_cr: `03 Post-CR pic 9(6).` [copybooks/wspost.cob:L21].
        cr_pc: `03 CR-PC pic 99.` [copybooks/wspost.cob:L22].
        post_amount: `03 Post-Amount pic s9(8)v99.` [copybooks/wspost.cob:L23].
        vat_ac: `03 Vat-AC pic 9(6).` [copybooks/wspost.cob:L25].
        vat_pc: `03 Vat-PC pic 99.` [copybooks/wspost.cob:L26].
        post_vat_side: `03 Post-Vat-Side pic xx.` [copybooks/wspost.cob:L27].
        vat_amount: `03 Vat-Amount pic s9(8)v99.` [copybooks/wspost.cob:L28].
    """

    batch: int
    post_number: int
    post_code: str
    post_date: str
    post_legend: str
    post_dr: int
    dr_pc: int
    post_cr: int
    cr_pc: int
    post_amount: Decimal
    vat_ac: int
    vat_pc: int
    post_vat_side: str
    vat_amount: Decimal


def _entered(**overrides: Decimal | int | str) -> _EnteredPosting:
    """Build one entered posting, defaulting every field this block does not vary.

    A tax-inclusive sales posting of 1200.00 net with 240.00 tax, debiting a
    receivables account and crediting a revenue account, with the tax account
    non-zero so that the third leg is reached unless a test says otherwise.

    Args:
        **overrides: Fields to replace, by attribute name.

    Returns:
        The posting.
    """
    base = _EnteredPosting(
        batch=17,
        post_number=3,
        post_code="SI",
        post_date="21092025",
        post_legend="INVOICE 100317",
        post_dr=110500,
        dr_pc=1,
        post_cr=400100,
        cr_pc=2,
        post_amount=Decimal("1200.00"),
        vat_ac=220300,
        vat_pc=3,
        post_vat_side=_SIDE_CREDIT,
        vat_amount=Decimal("240.00"),
    )
    return dataclasses.replace(base, **overrides)


def _transcribe_lines_495_to_533(
    posting: _EnteredPosting,
) -> tuple[work_records.PreTransRecord, ...]:
    """Drive the MIGRATED explosion for one posting and return the legs it wrote.

    THIS FUNCTION USED TO BE A TRANSCRIPTION AND IS NOW A DRIVER, AND THE CHANGE
    MATTERS MORE THAN IT LOOKS. It previously re-executed
    [general/gl070.cbl:L495-L533] statement by statement in this file - over the
    production primitives, but as its own sequence - which made the file a SECOND
    SOURCE for the double-entry explosion. Seventeen assertions consumed it, so
    seventeen assertions were checking a copy of the program against the reasoning
    that produced the copy. The two could drift apart in either direction and every
    one of them would stay green.

    Now it drives `acas_posting.programs.gl070_transaction_pre_process`'s own
    `_gl071b_pre_process_loop` - the paragraph that IS the migration - and returns
    what that paragraph actually wrote. The seventeen call sites are unchanged: the
    return shape is the same tuple of snapshots in write order. What changed is that
    they now assert against the shipped code instead of against a paraphrase of it,
    and the fixed expectations each of them carries became the independent side of the
    comparison rather than the only side.

    THE LINE-BY-LINE MAP SURVIVES, because it was the documentary value of the old
    body and it is what makes the assertions below citable. Each frozen statement and
    the production statement that reproduces it:

        495  move batch to pre-batch.            -> pre_batch, from ws_post_key.batch
        496  move post-number to pre-post.       -> pre_post
        497  move post-code IN WS-Posting-Record to pre-code.
                 ANOMALY A-21, the first of three QUALIFIED references in the block.
                 The qualifier is forced: `Post-Code` is declared BOTH at
                 [copybooks/wspost.cob:L17] as the two-character posting code and at
                 [copybooks/wssystem.cob:L77] as the twelve-character postal code, and
                 gl070 COPYs both [general/gl070.cbl:L128], [general/gl070.cbl:L240].
        498  move post-date to pre-date.         -> pre_date
        499  move post-legend to pre-legend.     -> pre_legend
        501  move post-dr to pre-ac.             -> the DEBIT leg's account
        502  move dr-pc to pre-pc.
        503  if post-vat-side = "CR" -> add post-amount vat-amount giving pre-amount
             else                    -> move post-amount to pre-amount
                 THE CROSSED LOGIC: the DEBIT leg absorbs the tax when the tax is
                 declared on the CREDIT side.
        508  write pre-trans-record.             -> leg 1
        510  move post-cr to pre-ac.             -> the CREDIT leg's account
        511  move cr-pc to pre-pc.
        512  if post-vat-side = "DR" -> add post-amount vat-amount giving pre-amount
             else                    -> move post-amount to pre-amount
        517  multiply pre-amount by -1 giving pre-amount.
                 UNCONDITIONAL. Every credit leg is negated, tax or no tax.
        519  write pre-trans-record.             -> leg 2
        521  if vat-ac = zero or vat-amount = zero -> go to loop.
                 The guard that makes the third leg optional. An OR, so either
                 condition alone suppresses it.
        525  move vat-ac IN WS-Posting-Record to pre-ac.   ANOMALY A-21 again
        526  move vat-pc to pre-pc.
        527  move vat-amount to pre-amount.
        529  if post-vat-side = "CR" -> multiply pre-amount by -1 giving pre-amount.
                 CONDITIONAL, and DISTINCT from L517.
        532  write pre-trans-record.             -> leg 3
        533  go to loop.

    ONE RECORD AREA, WRITTEN UP TO THREE TIMES. The three `write` statements all name
    `pre-trans-record`, so each leg is a SNAPSHOT of the area as it stood at that
    moment - which is what makes the fields the block does NOT reassign between writes
    observable: `pre-code`, `pre-date`, `pre-legend`, `pre-batch` and `pre-post` are
    moved once at L495-L499 and carried into all three legs unchanged. The snapshot is
    the work sequence's own doing, not this file's: `write` stores
    `_record_area_snapshot(record)` [acas_posting/workfiles.py], which is how the
    migration models a COBOL record area.

    NO DATABASE AND NO CONNECTION. The paragraph's only outward call is
    `perform GL-Posting-Read-Next` [general/gl070.cbl:L486], replaced here by a reader
    that presents this one posting and then reports AT END; the work sequence it writes
    into is in-process (`self._records`, not a file). The facade attribute is restored
    in a `finally`, so nothing leaks to another test.

    Args:
        posting: The entered posting the block reads.

    Returns:
        The legs written, in write order: the debit leg from L508, the credit leg from
            L519, and - only when L521-L523 does not skip - the tax leg from L532. Two
            or three elements, never fewer and never more.
    """
    from acas_posting.dal import facade
    from acas_posting.programs import gl070_transaction_pre_process as gl070
    from acas_posting.records.calling_data import WsCallingData
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.gl_batch import GlBatchRecord
    from acas_posting.records.gl_posting import WsPostingRecord
    from acas_posting.records.maps03 import Maps03Ws
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData
    from acas_posting.dates import WsDateFormats
    from acas_posting.workfiles import general_ledger_work_files

    entered = WsPostingRecord()
    entered.ws_post_key.batch = posting.batch
    entered.ws_post_key.post_number = posting.post_number
    entered.post_code = posting.post_code
    entered.post_date = posting.post_date
    entered.post_legend = posting.post_legend
    entered.post_dr = posting.post_dr
    entered.dr_pc = posting.dr_pc
    entered.post_cr = posting.post_cr
    entered.cr_pc = posting.cr_pc
    entered.post_amount = posting.post_amount
    entered.vat_ac = posting.vat_ac
    entered.vat_pc = posting.vat_pc
    entered.post_vat_side = posting.post_vat_side
    entered.vat_amount = posting.vat_amount

    batch = GlBatchRecord()
    #  The batch the paragraph is pre-processing. `if batch not = WS-Batch-Nos go to
    #  loop` [general/gl070.cbl:L492-L493] would otherwise discard the posting, and the
    #  explosion would never be reached at all.
    batch.ws_batch_key.ws_batch_nos = posting.batch

    system_record = SystemRecord()
    file_access = FileAccess()
    file_defs = FileDefs()
    common = AcasDalCommonData()
    files = general_ledger_work_files()

    store = gl070._WorkingStorage(
        ws_calling_data=WsCallingData(),
        system_record=system_record,
        to_day="21/09/2025",
        file_defs=file_defs,
        file_access=file_access,
        dal_common=common,
        batch=batch,
        posting=entered,
        pre_trans_record=work_records.PreTransRecord(),
        maps03_ws=Maps03Ws(),
        ws=WsDateFormats(),
        detector=0,
        work_files=files,
        batch_ctx=facade.FacadeContext(
            system=system_record,
            record=batch,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=common,
        ),
        posting_ctx=facade.FacadeContext(
            system=system_record,
            record=entered,
            file_access=file_access,
            file_defs=file_defs,
            dal_common=common,
        ),
    )

    #  `perform GL-Posting-Read-Next` presents the posting once, then reports AT END.
    #  `10` is `FS-Reply`'s end-of-file value, which the paragraph tests through the
    #  program's own `_at_end` [general/gl070.cbl:L487-L488].
    presented = {"count": 0}

    def _read_next(ctx: object) -> None:
        presented["count"] += 1
        ctx.file_access.fs_reply = 0 if presented["count"] == 1 else 10

    original = facade.gl_posting_read_next
    files.pre_trans.open_output()
    try:
        facade.gl_posting_read_next = _read_next
        gl070._gl071b_pre_process_loop(store)
    finally:
        facade.gl_posting_read_next = original
    files.pre_trans.close()

    assert presented["count"] == 2, (
        f"the reader was called {presented['count']} time(s); the paragraph must take "
        f"the posting once and then meet AT END, or the legs below are not one "
        f"posting's explosion"
    )

    files.pre_trans.open_input()
    written: list[work_records.PreTransRecord] = []
    while True:
        leg = files.pre_trans.read_next()
        if leg is None:
            break
        written.append(leg)
    files.pre_trans.close()
    return tuple(written)


# ===========================================================================
# GROUP 1 - the storage shapes the block moves between.
# ===========================================================================


@pytest.mark.parametrize(
    ("descriptor", "locator"),
    [
        pytest.param(
            _SENDING["post_amount"], "copybooks/wspost.cob:L23", id="post-amount"
        ),
        pytest.param(
            _SENDING["vat_amount"], "copybooks/wspost.cob:L28", id="vat-amount"
        ),
        pytest.param(
            _RECEIVING["pre_amount"], "general/gl070.cbl:L115", id="pre-amount"
        ),
    ],
)
def test_amount_fields_are_signed_zoned_decimal_ten_bytes_wide(
    descriptor: cobol_field.FieldDescriptor, locator: str
) -> None:
    """All three amounts in the block are `pic s9(8)v99` DISPLAY, ten bytes wide.

    `post-amount` and `vat-amount` are the operands of the two `add ... giving` at
    [general/gl070.cbl:L504] and [general/gl070.cbl:L513]; `pre-amount` is the
    receiving field of both, and of both negations. They share one shape, which is
    why no add in this block can truncate: sender and receiver are the same scale.

    THE TEN-BYTE WIDTH IS ASSERTED PLAINLY, NOT DEFERRED TO A QUESTION. It follows
    from the copybook's own cumulative offset comments twice over - see
    `_AMOUNT_BYTES` - and from the sign being OVERPUNCHED onto the last digit rather
    than occupying a byte of its own. (`sign leading` on a nine-digit IRS amount is
    a genuinely open width question, but that is a different clause in a different
    copybook and belongs to `test_sign_leading_display.py`.)
    """
    assert descriptor.picture == "s9(8)v99"
    assert descriptor.usage is model.Usage.DISPLAY
    assert descriptor.signed is True
    assert descriptor.unsigned is False
    assert descriptor.sign_position is model.SignPosition.TRAILING_INCLUDED
    # No SIGN clause is written at any of the three declarations, so the position is
    # the language default rather than a stated one.
    assert descriptor.sign_clause_text is None
    assert descriptor.digits == 10
    assert descriptor.integer_digits == 8
    assert descriptor.scale == _AMOUNT_SCALE
    assert descriptor.byte_length == _AMOUNT_BYTES
    assert descriptor.python_storage is model.CobolPythonStorage.DECIMAL
    assert descriptor.is_decimal is True
    assert descriptor.is_int is False
    assert descriptor.quantum == Decimal("0.01")
    # R-5: the descriptor names the frozen line it was derived from.
    assert locator in descriptor.cite()


@pytest.mark.parametrize(
    ("descriptor", "picture", "digits", "locator"),
    [
        pytest.param(
            _SENDING["post_dr"], "9(6)", 6, "copybooks/wspost.cob:L19", id="post-dr"
        ),
        pytest.param(
            _SENDING["dr_pc"], "99", 2, "copybooks/wspost.cob:L20", id="dr-pc"
        ),
        pytest.param(
            _SENDING["post_cr"], "9(6)", 6, "copybooks/wspost.cob:L21", id="post-cr"
        ),
        pytest.param(
            _SENDING["cr_pc"], "99", 2, "copybooks/wspost.cob:L22", id="cr-pc"
        ),
        pytest.param(
            _SENDING["vat_ac"], "9(6)", 6, "copybooks/wspost.cob:L25", id="vat-ac"
        ),
        pytest.param(
            _SENDING["vat_pc"], "99", 2, "copybooks/wspost.cob:L26", id="vat-pc"
        ),
        pytest.param(
            _RECEIVING["pre_ac"], "9(6)", 6, "general/gl070.cbl:L113", id="pre-ac"
        ),
        pytest.param(
            _RECEIVING["pre_pc"], "99", 2, "general/gl070.cbl:L114", id="pre-pc"
        ),
    ],
)
def test_account_and_centre_fields_are_unsigned_integers(
    descriptor: cobol_field.FieldDescriptor,
    picture: str,
    digits: int,
    locator: str,
) -> None:
    """Every account number and profit centre in the block is UNSIGNED.

    This is why no leg's account number can ever carry a sign, however the amount on
    that leg is signed: the three `move ... to pre-ac` at [general/gl070.cbl:L501],
    [general/gl070.cbl:L510] and [general/gl070.cbl:L525] all send an unsigned
    `pic 9(n)` item into an unsigned `pic 9(6)` one.
    """
    assert descriptor.picture == picture
    assert descriptor.usage is model.Usage.DISPLAY
    assert descriptor.signed is False
    assert descriptor.digits == digits
    assert descriptor.integer_digits == digits
    assert descriptor.scale == 0
    assert descriptor.byte_length == digits
    assert descriptor.python_storage is model.CobolPythonStorage.INT
    assert descriptor.is_int is True
    # An unsigned item's domain starts at zero, which is the sign drop stated as a
    # range rather than as a branch.
    assert descriptor.value_domain == (0, 10**digits - 1)
    assert locator in descriptor.cite()


@pytest.mark.parametrize(
    ("descriptor", "picture", "length", "locator"),
    [
        pytest.param(
            _SENDING["post_code"],
            "xx",
            2,
            "copybooks/wspost.cob:L17",
            id="post-code",
        ),
        pytest.param(
            _SENDING["post_vat_side"],
            "xx",
            2,
            "copybooks/wspost.cob:L27",
            id="post-vat-side",
        ),
        pytest.param(
            _RECEIVING["pre_code"], "xx", 2, "general/gl070.cbl:L111", id="pre-code"
        ),
        pytest.param(
            _RECEIVING["pre_date"], "x(8)", 8, "general/gl070.cbl:L112", id="pre-date"
        ),
        pytest.param(
            _RECEIVING["pre_legend"],
            "x(32)",
            32,
            "general/gl070.cbl:L116",
            id="pre-legend",
        ),
    ],
)
def test_alphanumeric_fields_carry_a_character_length_and_no_number(
    descriptor: cobol_field.FieldDescriptor,
    picture: str,
    length: int,
    locator: str,
) -> None:
    """`post-vat-side` is TEXT, which is why nothing validates it (R-3).

    `03 Post-Vat-Side pic xx.` [copybooks/wspost.cob:L27] can hold any two
    characters. The three tests of it - [general/gl070.cbl:L503],
    [general/gl070.cbl:L512] and [general/gl070.cbl:L529] - are equality
    comparisons against literals with no `else` that rejects anything, so a third
    value is a reachable state rather than an error.
    """
    assert descriptor.picture == picture
    assert descriptor.usage is model.Usage.ALPHANUMERIC
    assert descriptor.character_length == length
    assert descriptor.byte_length == length
    assert descriptor.python_storage is model.CobolPythonStorage.STR
    assert descriptor.is_str is True
    assert descriptor.is_numeric is False
    assert descriptor.digits is None
    assert descriptor.scale is None
    assert locator in descriptor.cite()
    # A text item has no arithmetic store at all: putting a number into one is a
    # MOVE between categories, not a COMPUTE.
    with pytest.raises(TypeError):
        arithmetic.store(Decimal("1.00"), descriptor)


def test_pre_trans_record_declares_eight_fields_in_source_order() -> None:
    """`01 pre-trans-record.` [general/gl070.cbl:L108-L116] - eight fields, in order.

    The order is not decoration: `gl071` sorts this record on four of these fields
    by position [general/gl071.cbl:L112-L120], so a reordering would change the
    stream `gl072` reads sequentially.
    """
    assert tuple(_RECEIVING) == (
        "pre_batch",
        "pre_post",
        "pre_code",
        "pre_date",
        "pre_ac",
        "pre_pc",
        "pre_amount",
        "pre_legend",
    )
    # `pre-batch` and `pre-post` are `pic 9(5)`, narrower than the `pic 9(6)`
    # accounts, and are moved once at L495-L496.
    assert _RECEIVING["pre_batch"].picture == "9(5)"
    assert _RECEIVING["pre_post"].picture == "9(5)"


def test_work_record_descriptors_have_program_provenance_and_no_drift() -> None:
    """The receiving record has NO copybook, NO bridge and NO table - and no drift.

    `pre-trans-record` is `gl070`'s own file-section declaration
    [general/gl070.cbl:L106-L116]; `pretrans.tmp` is a transient work file, not part
    of the schema [copybooks/wsnames.cob:L15-L16]. So every one of its dictionary
    entries is a PROGRAM-SOURCE entry, and because there is no second view of the
    field there is nothing for a shape to drift against. That is what makes these
    eight descriptors the one group in the whole migration that can be trusted
    without consulting a bridge (R-5).
    """
    for attribute, descriptor in _RECEIVING.items():
        entry = loader.get_entry(str(descriptor.dictionary_key))
        assert entry.presence.in_program_source is True
        assert entry.presence.in_copybook is False
        assert entry.presence.in_bridge is False
        assert entry.presence.in_column is False
        assert entry.program_source is not None
        assert entry.program_source.file == "general/gl070.cbl"
        assert entry.program_source.parent_group == "pre-trans-record"
        # The key carries the declaration line, which is what distinguishes these
        # program-record fields from the table-keyed ones.
        assert "#" in str(descriptor.dictionary_key)
        assert descriptor.source_locator is not None
        assert descriptor.source_locator.startswith("general/gl070.cbl:L")
        cite = descriptor.cite()
        assert "bridge=absent" in cite
        assert "column=absent" in cite
        drift = descriptor.drift()
        assert drift is not None
        assert drift.signedness is False, attribute
        assert drift.usage is False, attribute
        assert drift.digits is False, attribute
        assert drift.scale is False, attribute
        assert drift.character_length is False, attribute
        assert drift.name is False, attribute
        assert drift.details == ()


def test_record_metadata_and_dictionary_key_yield_the_same_descriptor() -> None:
    """Both published routes to a work-record shape answer identically.

    `acas_posting.records.work_records` attaches each descriptor to its dataclass
    member's `metadata`, and `FieldDescriptor.from_dictionary_key` mints one from the
    artifact. If those two ever disagreed, this file and the migrated program would
    be describing different fields under the same name.
    """
    for descriptor in _RECEIVING.values():
        key = str(descriptor.dictionary_key)
        assert cobol_field.FieldDescriptor.from_dictionary_key(key) == descriptor


def test_descriptors_come_from_the_dictionary_the_suite_names(
    data_dictionary_path: Path,
) -> None:
    """The artifact these shapes are read from is the one `tests/conftest.py` names.

    R-5. `from_dictionary_key` resolves the artifact itself - through the packaged
    copy, falling back to the repository sibling - so this test pins that resolution
    to the single path the whole suite agrees on rather than leaving it implicit.

    Args:
        data_dictionary_path: The session fixture from `tests/conftest.py`.
    """
    for descriptor in (*_SENDING.values(), *_RECEIVING.values()):
        explicit = cobol_field.FieldDescriptor.from_dictionary_key(
            str(descriptor.dictionary_key), path=data_dictionary_path
        )
        assert explicit == descriptor


# ===========================================================================
# GROUP 2 - the two `multiply ... by -1` sites are DISTINCT statements.
# ===========================================================================


def test_credit_leg_negation_at_l517_is_unconditional() -> None:
    """[general/gl070.cbl:L517] negates the credit leg on EVERY posting.

    The statement sits outside every `if` in the block, at the same indentation as
    the `write` that follows it, so `post-vat-side` cannot reach it. Asserted across
    all four values the two-character switch is exercised with here, including two
    the frozen program never anticipated.
    """
    for side in (_SIDE_CREDIT, _SIDE_DEBIT, _SIDE_UNSET, _SIDE_OTHER):
        legs = _transcribe_lines_495_to_533(_entered(post_vat_side=side))
        credit_leg = legs[1]
        # Negative on every side, without exception. That is the whole claim.
        assert credit_leg.pre_amount < 0, side
        assert credit_leg.pre_ac == 400100
        assert credit_leg.pre_pc == 2


def test_vat_leg_negation_at_l529_l530_is_conditional_on_credit() -> None:
    """[general/gl070.cbl:L529-L530] negates the tax leg ONLY on the credit side.

    The `multiply` is the object of `if post-vat-side = "CR"`, so on the debit side -
    and on every other value the switch can hold - the tax leg is left POSITIVE.
    """
    credit_side = _transcribe_lines_495_to_533(_entered(post_vat_side=_SIDE_CREDIT))
    assert credit_side[2].pre_amount == Decimal("-240.00")

    for side in (_SIDE_DEBIT, _SIDE_UNSET, _SIDE_OTHER):
        legs = _transcribe_lines_495_to_533(_entered(post_vat_side=side))
        # Un-negated, because L529's test is false.
        assert legs[2].pre_amount == Decimal("240.00"), side
        assert legs[2].pre_ac == 220300
        assert legs[2].pre_pc == 3


def test_unifying_the_two_negations_would_break() -> None:
    """The test that FAILS if [L517] and [L529-L530] are factored into one helper.

    R-4, and the reason this file exists in the form it does. The debit-side case is
    the one that separates them: the credit leg IS negated there while the tax leg is
    NOT, so the two statements demonstrably do not share a condition. Both candidate
    unifications are computed here and both are shown to produce a figure the frozen
    block does not produce:

        unify under L529's guard  ->  the credit leg would stay POSITIVE on the
                                     debit side, +1440.00 instead of -1440.00.
        unify under L517's absence of a guard  ->  the tax leg would be NEGATED on
                                     the debit side, -240.00 instead of +240.00.

    A future reader who "simplifies" the two into one hits whichever of these two
    assertions their choice contradicts.
    """
    posting = _entered(post_vat_side=_SIDE_DEBIT)
    legs = _transcribe_lines_495_to_533(posting)
    _, credit_leg, vat_leg = legs

    # What the block actually produces on the debit side.
    assert credit_leg.pre_amount == Decimal("-1440.00")
    assert vat_leg.pre_amount == Decimal("240.00")

    # Candidate unification 1 - apply L529's `= "CR"` guard to L517 as well. The
    # credit leg would then never be negated on a debit-side posting.
    gross = arithmetic.add_giving(
        posting.post_amount,
        posting.vat_amount,
        receiving=_RECEIVING["pre_amount"],
    )
    assert credit_leg.pre_amount != gross
    assert credit_leg.pre_amount == arithmetic.multiply_by_giving(
        gross, _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
    )

    # Candidate unification 2 - drop L529's guard so both negations are
    # unconditional. The tax leg would then be negated on a debit-side posting.
    always_negated = arithmetic.multiply_by_giving(
        posting.vat_amount, _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
    )
    assert always_negated == Decimal("-240.00")
    assert vat_leg.pre_amount != always_negated

    # And the pair really is a pair: on the credit side BOTH are negated, so no
    # single condition distinguishes them by outcome alone.
    credit_legs = _transcribe_lines_495_to_533(_entered(post_vat_side=_SIDE_CREDIT))
    assert credit_legs[1].pre_amount < 0
    assert credit_legs[2].pre_amount < 0


# ===========================================================================
# GROUP 3 - the crossed tax-inclusive logic, every cell of the table.
# ===========================================================================

#: The whole observable behaviour of [general/gl070.cbl:L503-L530], as data.
#:
#: READ THE FIRST TWO ROWS TOGETHER AND THE CROSS IS PLAIN: the leg that absorbs the
#: tax is the OPPOSITE of the side `post-vat-side` names. `post-vat-side` says where
#: the TAX is posted, so the other leg is the one that must carry the tax-inclusive
#: gross. It is not an inversion to be corrected.
#:
#: post-vat-side, debit leg (L508), credit leg (L519), tax leg (L532)
_CROSSED_TABLE = (
    pytest.param(
        _SIDE_CREDIT,
        # L504: the DEBIT leg absorbs the tax.
        Decimal("1440.00"),
        # L515 then L517: net, negated.
        Decimal("-1200.00"),
        # L527 then L530: tax, negated because the side IS credit.
        Decimal("-240.00"),
        id="side-CR",
    ),
    pytest.param(
        _SIDE_DEBIT,
        # L506: net, untouched.
        Decimal("1200.00"),
        # L513 then L517: the CREDIT leg absorbs the tax, then is negated.
        Decimal("-1440.00"),
        # L527, with L530 NOT taken.
        Decimal("240.00"),
        id="side-DR",
    ),
    pytest.param(
        _SIDE_UNSET,
        # Both L503 and L512 take their `else`, so NEITHER leg absorbs the tax.
        Decimal("1200.00"),
        Decimal("-1200.00"),
        Decimal("240.00"),
        id="side-spaces",
    ),
    pytest.param(
        _SIDE_OTHER,
        Decimal("1200.00"),
        Decimal("-1200.00"),
        Decimal("240.00"),
        id="side-XX",
    ),
)


@pytest.mark.parametrize(
    ("side", "debit_amount", "credit_amount", "vat_amount"), _CROSSED_TABLE
)
def test_crossed_vat_inclusive_logic_every_cell(
    side: str,
    debit_amount: Decimal,
    credit_amount: Decimal,
    vat_amount: Decimal,
) -> None:
    """Every cell of the crossed-tax table, for every value of the switch.

    [general/gl070.cbl:L503-L506] gives the debit leg, [general/gl070.cbl:L512-L517]
    the credit leg and [general/gl070.cbl:L525-L530] the tax leg.

    NO ASSERTION HERE SAYS THE THREE LEGS SUM TO ZERO, and that omission is
    deliberate (R-4). They do sum to zero on the two named sides - 1440 - 1200 - 240
    and 1200 - 1440 + 240 - and they do NOT on any third value, where the total is
    +240.00 because neither leg absorbed the tax while the tax leg was still written
    at its full positive value. Asserting a balance rule would be asserting correct
    accounting instead of observed behaviour, and it would hide exactly the case this
    block gets wrong.
    """
    legs = _transcribe_lines_495_to_533(_entered(post_vat_side=side))
    assert len(legs) == 3

    debit_leg, credit_leg, vat_leg = legs
    assert debit_leg.pre_amount == debit_amount
    assert credit_leg.pre_amount == credit_amount
    assert vat_leg.pre_amount == vat_amount

    # Every stored amount lands on `pre-amount`'s own scale, whichever branch
    # produced it - the `add ... giving`, the plain `move`, or the negation.
    for leg in legs:
        assert leg.pre_amount.as_tuple().exponent == -_AMOUNT_SCALE

    # The account and centre of each leg, so the table is a statement about whole
    # records rather than about three numbers.
    assert (debit_leg.pre_ac, debit_leg.pre_pc) == (110500, 1)
    assert (credit_leg.pre_ac, credit_leg.pre_pc) == (400100, 2)
    assert (vat_leg.pre_ac, vat_leg.pre_pc) == (220300, 3)


def test_the_absorbing_leg_is_the_opposite_of_the_named_side() -> None:
    """The cross, stated once as a comparison rather than as four constants.

    [general/gl070.cbl:L503-L504] versus [general/gl070.cbl:L512-L513]. Naming the
    side `"CR"` moves the tax-inclusive gross onto the DEBIT leg, and naming it
    `"DR"` moves it onto the CREDIT leg. Anyone who reads those two `if`s as a
    copy-paste slip and "corrects" one of them fails here.
    """
    net = _entered().post_amount
    tax = _entered().vat_amount
    gross = arithmetic.add_giving(net, tax, receiving=_RECEIVING["pre_amount"])
    assert gross == Decimal("1440.00")

    credit_side = _transcribe_lines_495_to_533(_entered(post_vat_side=_SIDE_CREDIT))
    debit_side = _transcribe_lines_495_to_533(_entered(post_vat_side=_SIDE_DEBIT))

    # The negations below are spelled `copy_negate()` rather than `-`. Unary minus on
    # a `Decimal` is a CONTEXT operation - it rounds its result to the ambient
    # `prec` - so `-net` would compare the stored leg against a figure the caller's
    # context had reshaped, and the assertion would report that context instead of
    # [general/gl070.cbl:L517] and [general/gl070.cbl:L530]. `copy_negate` is the
    # sign-only operation: no rounding, no signal, no context (R-2). It is also the
    # idiom this test already uses for magnitude, two lines further down.
    #
    # Side "CR": the gross is on the DEBIT leg, and the credit leg carries bare net.
    assert credit_side[0].pre_amount == gross
    assert credit_side[1].pre_amount == net.copy_negate()

    # Side "DR": the gross is on the CREDIT leg, and the debit leg carries bare net.
    assert debit_side[1].pre_amount == gross.copy_negate()
    assert debit_side[0].pre_amount == net

    # Which is to say the absorbing leg swaps when the side does.
    assert credit_side[0].pre_amount.copy_abs() == debit_side[1].pre_amount.copy_abs()
    assert credit_side[1].pre_amount.copy_abs() == debit_side[0].pre_amount.copy_abs()


def test_third_post_vat_side_value_produces_legs_and_not_an_error() -> None:
    """A `post-vat-side` that is neither "DR" nor "CR" is a REACHABLE state (R-3).

    `03 Post-Vat-Side pic xx.` [copybooks/wspost.cob:L27] with no `88` level, no
    range test and no `else` that rejects: the frozen program validates it nowhere,
    so this file adds no check either. Both `if`s at [general/gl070.cbl:L503] and
    [general/gl070.cbl:L512] take their `else`, [general/gl070.cbl:L529] is false,
    and three legs are written whose totals do not balance.
    """
    for side in (_SIDE_UNSET, _SIDE_OTHER, "cr", "Cr", "C", "\x00\x00"):
        legs = _transcribe_lines_495_to_533(_entered(post_vat_side=side))
        assert len(legs) == 3, side
        assert legs[0].pre_amount == Decimal("1200.00"), side
        assert legs[1].pre_amount == Decimal("-1200.00"), side
        assert legs[2].pre_amount == Decimal("240.00"), side

    # Lower case is NOT the credit side: the comparison at L503 is against the
    # literal "CR", and COBOL alphanumeric comparison is case-SENSITIVE even though
    # its identifiers are not. Recorded because it is the likeliest wrong guess.
    assert _SIDE_CREDIT.lower() != _SIDE_CREDIT


# ===========================================================================
# GROUP 4 - the tax leg's two-part guard, all four combinations.
# ===========================================================================

#: The full truth table of [general/gl070.cbl:L521-L523]:
#:
#:     if       vat-ac of WS-Posting-Record = zero
#:           or vat-amount = zero
#:              go to  loop.
#:
#: A DISJUNCTION of two zero tests guarding a `go to`, so the tax leg survives only
#: when BOTH operands are non-zero. Three of the four combinations skip it.
#:
#: vat-ac, vat-amount, legs written
_GUARD_TABLE = (
    pytest.param(0, Decimal("0.00"), 2, id="both-zero-skip"),
    pytest.param(0, Decimal("240.00"), 2, id="account-zero-skip"),
    pytest.param(220300, Decimal("0.00"), 2, id="amount-zero-skip"),
    pytest.param(220300, Decimal("240.00"), 3, id="both-non-zero-written"),
)


@pytest.mark.parametrize(("vat_ac", "vat_amount", "expected_legs"), _GUARD_TABLE)
def test_vat_leg_guard_truth_table(
    vat_ac: int, vat_amount: Decimal, expected_legs: int
) -> None:
    """The tax leg is written only when BOTH the account and the amount are non-zero.

    R-3: the guard reproduced is exactly this two-part disjunction and nothing more.
    There is no third condition, no check that the account exists, and no check that
    the amount is consistent with the two legs already written.
    """
    legs = _transcribe_lines_495_to_533(
        _entered(post_vat_side=_SIDE_DEBIT, vat_ac=vat_ac, vat_amount=vat_amount)
    )
    assert len(legs) == expected_legs


@pytest.mark.parametrize(("vat_ac", "vat_amount", "expected_legs"), _GUARD_TABLE)
def test_debit_and_credit_legs_survive_every_skip(
    vat_ac: int, vat_amount: Decimal, expected_legs: int
) -> None:
    """A skip costs the THIRD leg and nothing else - it is not a rejection.

    The `go to loop` at [general/gl070.cbl:L523] lands AFTER the writes at
    [general/gl070.cbl:L508] and [general/gl070.cbl:L519], so on each of the three
    skip paths two legs have already been produced and remain produced. This is a
    behavioural fact about where the transfer sits, and reading it as "the posting
    was rejected" is the error the test guards against: nothing is undone, nothing is
    reported, and the two legs carry their normal values.
    """
    posting = _entered(
        post_vat_side=_SIDE_DEBIT, vat_ac=vat_ac, vat_amount=vat_amount
    )
    legs = _transcribe_lines_495_to_533(posting)

    assert len(legs) >= 2
    debit_leg, credit_leg = legs[0], legs[1]

    # L506 on the debit side: bare net, because L503's test is false.
    assert debit_leg.pre_amount == posting.post_amount
    assert (debit_leg.pre_ac, debit_leg.pre_pc) == (110500, 1)

    # L513 then L517 on the debit side: the tax is still absorbed into the credit
    # leg even when the tax leg is about to be skipped, because L512 tests
    # `post-vat-side` and not the tax amount. With a zero tax amount the absorption
    # simply adds nothing.
    assert credit_leg.pre_amount == arithmetic.multiply_by_giving(
        arithmetic.add_giving(
            posting.post_amount,
            posting.vat_amount,
            receiving=_RECEIVING["pre_amount"],
        ),
        _MINUS_ONE,
        _RECEIVING["pre_amount"],
        rounded=False,
    )
    assert (credit_leg.pre_ac, credit_leg.pre_pc) == (400100, 2)

    # The header fields moved once at L495-L499 are carried into every leg,
    # skipped-third or not.
    for leg in legs:
        assert leg.pre_batch == posting.batch
        assert leg.pre_post == posting.post_number
        assert leg.pre_code == posting.post_code
        assert leg.pre_date == posting.post_date
        assert leg.pre_legend.rstrip() == posting.post_legend.rstrip()


@pytest.mark.parametrize(
    "zero",
    [
        pytest.param(Decimal(0), id="scale-0"),
        pytest.param(Decimal("0.00"), id="scale-2"),
        pytest.param(Decimal("-0.00"), id="negative-scale-2"),
        pytest.param(Decimal("0E-2"), id="exponent-notation"),
        pytest.param(0, id="int"),
    ],
)
def test_the_zero_test_is_algebraic(zero: Decimal | int) -> None:
    """`= zero` [general/gl070.cbl:L521-L522] is a VALUE test, not a byte test.

    COBOL's figurative `ZERO` compares numerically, so every representation of zero
    satisfies it whatever its scale or its sign. A NEGATIVE ZERO IS ZERO: the block
    can produce one - `multiply pre-amount by -1 giving pre-amount` applied to a zero
    amount - and no comparison in the frozen program can tell it from a positive
    zero.

    Never compared by byte pattern and never by `str`: `str(Decimal("0.00"))` is
    `'0.00'` while `str(Decimal("0"))` is `'0'`, so a text comparison would make the
    guard depend on a field's scale.
    """
    assert arithmetic.compare(zero, _ZERO) == 0
    # The same fact from the plain operator, so the claim does not rest on one helper.
    assert zero == 0

    # And it really does skip the tax leg. Both operands are tried, because the
    # disjunction has two arms and only one of them takes a scaled amount.
    by_amount = _transcribe_lines_495_to_533(
        _entered(post_vat_side=_SIDE_DEBIT, vat_amount=Decimal(zero))
    )
    assert len(by_amount) == 2
    by_account = _transcribe_lines_495_to_533(
        _entered(post_vat_side=_SIDE_DEBIT, vat_ac=int(zero))
    )
    assert len(by_account) == 2


def test_negative_zero_is_indistinguishable_from_zero_by_comparison() -> None:
    """`-0.00 == 0.00` is True, which is why the sign of zero is not observable.

    Stated on its own because it is the premise of question Q-70f below: comparison
    cannot separate the two, so if the compiled program's negated zero differs from
    this migration's, only the stored bytes could reveal it.
    """
    negative_zero = Decimal("-0.00")
    assert negative_zero == Decimal("0.00")
    assert arithmetic.compare(negative_zero, Decimal("0.00")) == 0
    # The representations DO differ, which is the whole reason a byte-level question
    # exists at all. This is an observation about `decimal`, not about the guard.
    assert negative_zero.as_tuple().sign == 1
    assert Decimal("0.00").as_tuple().sign == 0
    # A store normalises it away, so nothing downstream of `pre-amount` sees it.
    assert arithmetic.store(
        negative_zero, _RECEIVING["pre_amount"], rounded=False
    ).as_tuple() == Decimal("0.00").as_tuple()


# ===========================================================================
# GROUP 5 - `add post-amount vat-amount giving pre-amount` is a VARIADIC
#           `ADD ... GIVING` that quantizes ONCE.
# ===========================================================================


def test_add_giving_two_sources_quantizes_once_into_pre_amount() -> None:
    """[general/gl070.cbl:L504] and [general/gl070.cbl:L513] are the TWO-SOURCE form.

    `ADD a b GIVING c` sums its operand list and stores the total; the receiver is
    NOT itself an operand, which is what distinguishes it from `ADD a TO b`. Across
    the twelve in-scope programs `ADD ... GIVING` appears on exactly 32 lines, and
    these two are among them.

    The store lands on `pre-amount`'s scale, which is what fixes the result exponent
    at -2 whatever the operands' own exponents were.
    """
    total = arithmetic.add_giving(
        Decimal("1200.00"), Decimal("240.00"), receiving=_RECEIVING["pre_amount"]
    )
    assert total == Decimal("1440.00")
    assert total.as_tuple().exponent == -_AMOUNT_SCALE

    # Both operands share the receiver's scale here, so an unscaled sender proves the
    # receiver is what decides: 1200 has exponent 0 and the result still has -2.
    unscaled = arithmetic.add_giving(
        Decimal(1200), Decimal(240), receiving=_RECEIVING["pre_amount"]
    )
    assert unscaled == Decimal("1440.00")
    assert unscaled.as_tuple().exponent == -_AMOUNT_SCALE

    # THE RECEIVER IS NOT AN OPERAND. `pre-amount` already holds the previous leg's
    # figure when L504 and L513 run, and the `GIVING` form discards it: the two
    # verbs agree only because `ADD ... TO` is given 1200.00 as its receiver here.
    # Transcribing L504 as `ADD ... TO` would add whatever `pre-amount` last held,
    # which on the second and later postings of a batch is not zero.
    assert arithmetic.add_to(
        Decimal("240.00"),
        receiver_value=Decimal("1200.00"),
        receiving=_RECEIVING["pre_amount"],
    ) == total
    stale = arithmetic.add_to(
        Decimal("1200.00"),
        Decimal("240.00"),
        receiver_value=Decimal("-999.00"),
        receiving=_RECEIVING["pre_amount"],
    )
    assert stale == Decimal("441.00")
    assert stale != total

    # `GIVING` names a receiving field, so the sum is STORED and therefore quantized.
    # The contrast is with arithmetic that has no receiving field at all - the form
    # inside a relation condition - which is evaluated at intermediate precision and
    # not quantized. Asserted here because it is the whole reason a `GIVING` result
    # can differ from the exact sum.
    unquantized = arithmetic.intermediate(lambda: Decimal("0.004") + Decimal("0.004"))
    assert unquantized == Decimal("0.008")
    assert unquantized.as_tuple().exponent == -3
    assert arithmetic.add_giving(
        Decimal("0.004"), Decimal("0.004"), receiving=_RECEIVING["pre_amount"]
    ) == Decimal("0.00")


def test_add_giving_accepts_five_sources_and_quantizes_once() -> None:
    """The `GIVING` form is variadic, and the single quantize is OBSERVABLE.

    Five operands of four thousandths total twenty thousandths, which lands as two
    hundredths in a two-place field. Truncating each operand into the field FIRST
    would land nothing at all, because four thousandths truncates to zero. The
    divergence is therefore not a rounding nicety but the difference between 0.02 and
    0.00 - and it is the reason `ADD` must total at intermediate precision and store
    once.

    Neither of gl070's two `add ... giving` can reach this, because both send two
    scale-2 fields into a scale-2 field. It is exercised on the layer so that the
    QUANTIZE-ONCE property the two lines rely on is locked, not left to inference.
    """
    thousandths = [Decimal("0.004")] * 5

    once = arithmetic.add_giving(*thousandths, receiving=_RECEIVING["pre_amount"])
    assert once == Decimal("0.02")
    assert once.as_tuple().exponent == -_AMOUNT_SCALE

    # The wrong way round, computed explicitly so the divergence is visible in the
    # test rather than asserted as a bare inequality.
    per_source = [
        arithmetic.store(source, _RECEIVING["pre_amount"], rounded=False)
        for source in thousandths
    ]
    assert per_source == [Decimal("0.00")] * 5
    per_source_total = arithmetic.add_giving(
        *per_source, receiving=_RECEIVING["pre_amount"]
    )
    assert per_source_total == Decimal("0.00")
    assert once != per_source_total

    # Two, three, four and five operands, so "variadic" is a property of the verb and
    # not of a five-argument special case. The expected values are the exact totals
    # truncated toward zero at scale 2: 0.008, 0.012, 0.016 and 0.020 in turn.
    expected_by_count = {
        2: Decimal("0.00"),
        3: Decimal("0.01"),
        4: Decimal("0.01"),
        5: Decimal("0.02"),
    }
    for count, expected in expected_by_count.items():
        partial = arithmetic.add_giving(
            *thousandths[:count], receiving=_RECEIVING["pre_amount"]
        )
        assert partial == expected, count
        assert partial.as_tuple().exponent == -_AMOUNT_SCALE

    # A verb written with no operand at all is a transcription slip, not a data
    # condition, and is refused rather than silently storing the receiver over itself.
    with pytest.raises(ValueError):
        arithmetic.add_giving(receiving=_RECEIVING["pre_amount"])


# ===========================================================================
# GROUP 6 - ANOMALY A-21: field-name collisions force qualified references,
#           and the two synonyms are mixed.
# ===========================================================================

#: `[copybooks/wspost-irs.cob:L6-L7]`, verbatim - the maintainer's own warning that
#: two of the three posting layouts are different files describing different things
#: while sharing field names::
#:
#:     *> This is NOT the same as the internal IRS *
#:     *>   posting file                           *
#:
#: Quoted because it is the clearest evidence in the checkout that the collision is
#: real and known, and it is why a bare field name can never be a key.
_WSPOST_IRS_WARNING = (
    "*> This is NOT the same as the internal IRS *",
    "*>   posting file                           *",
)


def test_a21_the_collision_that_forces_gl070_to_qualify() -> None:
    """ANOMALY A-21 - `gl070` COPYs two records that each declare the same names.

    [general/gl070.cbl:L128] copies `wspost.cob` and [general/gl070.cbl:L240] copies
    `wssystem.cob`, and the two collide on exactly the names this block reads:

        `Post-Code`  [copybooks/wspost.cob:L17]   `pic xx`, the posting code
                     [copybooks/wssystem.cob:L77] `pic x(12)`, the POSTAL code
        `Vat-AC`     [copybooks/wspost.cob:L25]   `pic 9(6)`
                     [copybooks/wssystem.cob:L187] `binary-long`, a different field
                                                   with a different width entirely

    Hence the qualifiers at [general/gl070.cbl:L497], [general/gl070.cbl:L521] and
    [general/gl070.cbl:L525]. Proven through the DICTIONARY because its keys are
    table-qualified: the same bare name resolves to two different entries with two
    different shapes, and only the qualifier separates them.

    CITATION CORRECTION: the anomaly register cites [general/gl070.cbl:L510] for this
    program, but L510 is `move post-cr to pre-ac.` and carries no qualifier. The
    qualified sites are L497, L521 and L525.
    """
    posting_code = _descriptor("GLPOSTING-REC.POST-CODE")
    postal_code = _descriptor("SYSTEM-REC.POST-CODE")

    # Same bare name in both copybooks - COBOL identifiers are case-insensitive, so
    # the comparison is folded.
    assert posting_code.name.casefold() == postal_code.name.casefold() == "post-code"
    # Different shapes, so picking the wrong one is not a cosmetic error.
    assert posting_code.character_length == 2
    assert postal_code.character_length == 12
    assert posting_code != postal_code
    assert "copybooks/wspost.cob:L17" in posting_code.cite()
    assert "copybooks/wssystem.cob:L77" in postal_code.cite()

    posting_vat_ac = _descriptor("GLPOSTING-REC.VAT-AC")
    system_vat_ac = _descriptor("SYSTEM-REC.VAT-AC")

    assert posting_vat_ac.name.casefold() == system_vat_ac.name.casefold() == "vat-ac"
    # The posting record's is a six-digit zoned account number; the system record's
    # is a four-byte native binary. Nothing but the qualifier distinguishes them at
    # the point of use.
    assert posting_vat_ac.usage is model.Usage.DISPLAY
    assert posting_vat_ac.digits == 6
    assert posting_vat_ac.byte_length == 6
    assert system_vat_ac.usage is model.Usage.BINARY_LONG
    assert system_vat_ac.byte_length == 4
    assert system_vat_ac.signed is True
    assert posting_vat_ac != system_vat_ac
    assert "copybooks/wspost.cob:L25" in posting_vat_ac.cite()
    assert "copybooks/wssystem.cob:L187" in system_vat_ac.cite()

    # The block reads the POSTING record's pair at all three qualified sites, which
    # is what the transcription above sends.
    assert _SENDING["post_code"] == posting_code
    assert _SENDING["vat_ac"] == posting_vat_ac


def test_a21_across_the_posting_copybooks_same_name_different_shape() -> None:
    """The collision is not confined to `gl070`: the posting layouts collide too.

    `Post-Amount` is declared under BOTH `01 WS-Posting-Record.`
    [copybooks/wspost.cob:L23] and `01 Posting-Record.`
    [copybooks/irswspost.cob:L14], with different digits, a different integer width
    and a different SIGN POSITION. The dictionary can tell them apart only because
    its keys carry the table: `GLPOSTING-REC.POST-AMOUNT` against
    `IRSPOSTING-REC.POST4-AMOUNT`, whose COLUMN name differs while its COPYBOOK name
    does not.
    """
    general_ledger = _descriptor("GLPOSTING-REC.POST-AMOUNT")
    internal_irs = _descriptor("IRSPOSTING-REC.POST4-AMOUNT")

    # ONE bare copybook name, TWO entries.
    assert general_ledger.name == internal_irs.name == "Post-Amount"

    # Ten digits, eight of them integral, sign overpunched on the LAST digit and no
    # SIGN clause written.
    assert general_ledger.digits == 10
    assert general_ledger.integer_digits == 8
    assert general_ledger.sign_position is model.SignPosition.TRAILING_INCLUDED
    assert general_ledger.sign_clause_text is None

    # Nine digits, seven of them integral, sign overpunched on the FIRST digit
    # because the declaration says so in as many words.
    assert internal_irs.digits == 9
    assert internal_irs.integer_digits == 7
    assert internal_irs.sign_position is model.SignPosition.LEADING_INCLUDED
    assert internal_irs.sign_clause_text == "sign is leading"

    assert general_ledger != internal_irs
    assert general_ledger.scale == internal_irs.scale == _AMOUNT_SCALE
    assert "copybooks/wspost.cob:L23" in general_ledger.cite()
    assert "copybooks/irswspost.cob:L14" in internal_irs.cite()

    # The maintainer's own warning that these are different files, quoted verbatim.
    assert _WSPOST_IRS_WARNING[0].startswith("*> This is NOT the same as the")
    assert "posting file" in _WSPOST_IRS_WARNING[1]


#: Every bare field name declared under BOTH `01 WS-Posting-Record.`
#: [copybooks/wspost.cob:L12-L28] and `01 Posting-Record.`
#: [copybooks/irswspost.cob:L8-L18]. Eight names, and the block reads six of them.
_POSTING_COPYBOOK_COLLISIONS = frozenset(
    {
        "post-amount",
        "post-code",
        "post-cr",
        "post-date",
        "post-dr",
        "post-legend",
        "post-vat-side",
        "vat-amount",
    }
)


def test_a21_the_full_collision_set_across_the_posting_copybooks() -> None:
    """Eight names collide between the two posting copybooks - and two do NOT.

    Derived from the dictionary rather than transcribed, so the set cannot drift from
    the artifact: the copybook VIEW of each entry carries the name the copybook wrote,
    and the intersection of the two records' names is the collision set.

    TWO NAMES ARE NOT IN IT, and saying so is the point of the test as much as the
    eight that are: `Vat-AC` and `Vat-PC` are declared only in `wspost.cob`
    [copybooks/wspost.cob:L25-L26], because `irswspost.cob` spells its equivalent
    `Vat-AC-Def` [copybooks/irswspost.cob:L16] and declares no profit centre at all.
    `Vat-AC` nonetheless has to be qualified at [general/gl070.cbl:L521] and
    [general/gl070.cbl:L525] - just against `wssystem.cob` rather than against
    `irswspost.cob`.

    The THIRD posting layout is the counter-example that shows the collision is
    avoidable: `01 WS-IRS-Posting-Record.` [copybooks/wspost-irs.cob:L13-L25] prefixes
    every field `WS-IRS-`, so it collides with neither of the other two and no caller
    of it ever needs a qualifier.
    """

    def copybook_names(table: str) -> dict[str, str]:
        return {
            entry.copybook.name.casefold(): entry.key
            for entry in loader.entries_for_table(table)
            if entry.copybook is not None
        }

    general_ledger = copybook_names("GLPOSTING-REC")
    internal_irs = copybook_names("IRSPOSTING-REC")
    transfer_file = copybook_names("PSIRSPOST-REC")

    assert (
        set(general_ledger) & set(internal_irs)
    ) == set(_POSTING_COPYBOOK_COLLISIONS)

    # The two that do not collide there.
    assert "vat-ac" in general_ledger
    assert "vat-ac" not in internal_irs
    assert "vat-ac-def" in internal_irs
    assert "vat-pc" in general_ledger
    assert "vat-pc" not in internal_irs

    # The prefixed third layout collides with neither.
    assert not set(transfer_file) & set(general_ledger)
    assert not set(transfer_file) & set(internal_irs)
    assert all(name.startswith("ws-irs-") for name in transfer_file)

    # Six of the eight collisions are names this block reads, which is why a reader
    # of `gl070` meets the problem at all.
    read_by_this_block = {
        "post-code",
        "post-date",
        "post-dr",
        "post-cr",
        "post-amount",
        "post-legend",
        "post-vat-side",
        "vat-amount",
    }
    assert read_by_this_block <= _POSTING_COPYBOOK_COLLISIONS


def test_move_dispatches_by_category_to_the_same_answer() -> None:
    """The generic `MOVE` and the two category-specific forms agree, field by field.

    Every one of the block's ten `move` statements is transcribed with the generic
    entry point, exactly as the migrated program writes them, so this test pins that
    the generic form routes a numeric receiver to the numeric rules and an
    alphanumeric receiver to the alphanumeric ones. A mis-route would silently change
    `pre-legend`'s padding or `pre-amount`'s scale.
    """
    posting = _entered()

    numeric_moves = (
        # L495, L496, L501, L502 and their credit-side and tax-side counterparts.
        (posting.batch, _RECEIVING["pre_batch"], _SENDING["batch"]),
        (posting.post_number, _RECEIVING["pre_post"], _SENDING["post_number"]),
        (posting.post_dr, _RECEIVING["pre_ac"], _SENDING["post_dr"]),
        (posting.dr_pc, _RECEIVING["pre_pc"], _SENDING["dr_pc"]),
        (posting.post_cr, _RECEIVING["pre_ac"], _SENDING["post_cr"]),
        (posting.cr_pc, _RECEIVING["pre_pc"], _SENDING["cr_pc"]),
        (posting.vat_ac, _RECEIVING["pre_ac"], _SENDING["vat_ac"]),
        (posting.vat_pc, _RECEIVING["pre_pc"], _SENDING["vat_pc"]),
        # L506 and L515, and L527.
        (posting.post_amount, _RECEIVING["pre_amount"], _SENDING["post_amount"]),
        (posting.vat_amount, _RECEIVING["pre_amount"], _SENDING["vat_amount"]),
    )
    for value, receiving, sending in numeric_moves:
        generic = cobol_move.move(value, receiving, sending_field=sending)
        specific = cobol_move.move_numeric(value, receiving, sending_field=sending)
        assert generic == specific
        assert type(generic) is type(specific)

    alphanumeric_moves = (
        # L497, L498, L499.
        (posting.post_code, _RECEIVING["pre_code"], _SENDING["post_code"]),
        (posting.post_date, _RECEIVING["pre_date"], _SENDING["post_date"]),
        (posting.post_legend, _RECEIVING["pre_legend"], _SENDING["post_legend"]),
    )
    for text, receiving, sending in alphanumeric_moves:
        generic_text = cobol_move.move(text, receiving, sending_field=sending)
        specific_text = cobol_move.move_alphanumeric(
            text, receiving, sending_field=sending
        )
        assert generic_text == specific_text
        # An alphanumeric receiver is filled to its full declared width, so the
        # legend arrives space-padded to thirty-two rather than trimmed.
        assert len(specific_text) == receiving.character_length

    # `pre-legend` is wider than the legend supplied, so the padding is observable.
    padded = cobol_move.move(
        posting.post_legend,
        _RECEIVING["pre_legend"],
        sending_field=_SENDING["post_legend"],
    )
    assert padded.startswith(posting.post_legend)
    assert len(padded) == 32
    assert padded.rstrip() == posting.post_legend


def test_a_bare_field_name_is_never_a_dictionary_key() -> None:
    """A field name alone cannot key an entry, and this file never uses one.

    R-5, and the mechanical guarantee behind A-21. The artifact's key grammar
    requires a qualifier before the dot, so `POST-AMOUNT` on its own cannot match any
    key at all: the strict lookup raises and the tolerant one returns nothing. Every
    key in `_SENDING` and `_RECEIVING` carries its qualifier.
    """
    for bare in ("POST-AMOUNT", "Post-Amount", "VAT-AC", "POST-CODE", "pre-amount"):
        # The grammar itself refuses it - there is no qualifier to key it under.
        assert model.ENTRY_KEY_PATTERN.match(bare) is None
        # And so does the loader, through both of its lookup shapes.
        assert loader.find_entry(bare) is None
        with pytest.raises(KeyError):
            loader.get_entry(bare)
        # Including through this file's own tolerant resolver, whose fallback keys on
        # a name only WITHIN a qualifier and so has nothing to scan.
        with pytest.raises(LookupError):
            _descriptor(bare)

    # Every key this file relies on is qualified, and resolves.
    for descriptor in (*_SENDING.values(), *_RECEIVING.values()):
        key = str(descriptor.dictionary_key)
        assert model.ENTRY_KEY_PATTERN.match(key) is not None
        assert loader.find_entry(key) is not None
        assert "." in key


def test_qualified_references_name_the_record_the_dictionary_records() -> None:
    """`WS-Posting-Record` really is the record the three qualifiers name.

    The qualifier written at [general/gl070.cbl:L497], [general/gl070.cbl:L521] and
    [general/gl070.cbl:L525] is the `01` group each field sits under, and the
    dictionary records that group independently, so the citation can be checked
    rather than taken on trust.
    """
    for key in ("GLPOSTING-REC.POST-CODE", "GLPOSTING-REC.VAT-AC"):
        entry = loader.get_entry(key)
        assert entry.copybook is not None
        assert entry.copybook.parent_group == "WS-Posting-Record"
        assert entry.copybook.file == "copybooks/wspost.cob"

    # Reading the same record from the other direction: the copybook record resolves
    # to TABLE-qualified keys, which is exactly the indirection that lets one
    # copybook name map onto one table without either owning the other.
    under_record = loader.entries_for_copybook_record("WS-Posting-Record")
    keys = {entry.key for entry in under_record}
    assert "GLPOSTING-REC.POST-CODE" in keys
    assert "GLPOSTING-REC.VAT-AC" in keys
    # The two `05` children of `WS-Post-Key` keep the copybook record as their
    # qualifier, because the table stores the group as a single column.
    assert "WS-Posting-Record.Batch" in keys
    assert "WS-Posting-Record.Post-Number" in keys


# ===========================================================================
# GROUP 7 - silent overflow. No ON SIZE ERROR anywhere in the cycle.
# ===========================================================================


def test_add_giving_overflow_keeps_the_low_order_digits_silently() -> None:
    """A sum wider than eight integer digits keeps the LOW-ORDER digits, silently.

    Reachable from valid data, which is why it is tested rather than argued away:
    `post-amount` and `vat-amount` are each `pic s9(8)v99`, so
    [general/gl070.cbl:L504] and [general/gl070.cbl:L513] can total up to
    199999999.98 - nine integer digits - into an eight-integer-digit field.

    Across all twelve in-scope programs there are ZERO `ON SIZE ERROR` phrases and
    ZERO `REMAINDER` phrases, so there is no branch for the program to take. The
    high-order digits are discarded, the low-order ones are kept, and the sign of the
    pre-truncation result is preserved. R-3 and R-4: NOTHING here raises, clamps,
    warns or logs, because the frozen program does none of those.
    """
    ceiling = Decimal("99999999.99")
    # Built from a STRING rather than as `-ceiling`. `Decimal.__neg__` is a CONTEXT
    # operation, so under a reduced ambient `prec` the negation of a ten-digit figure
    # would be rounded and the negative case below would then be adding two numbers
    # this test never meant to add. A string prefix is exact under any context (R-2).
    negated_ceiling = Decimal("-99999999.99")

    # 99999999.99 + 0.02 = 100000000.01, whose low-order ten digits are 0000000001.
    overflowed = arithmetic.add_giving(
        ceiling, Decimal("0.02"), receiving=_RECEIVING["pre_amount"]
    )
    assert overflowed == Decimal("0.01")
    assert overflowed.as_tuple().exponent == -_AMOUNT_SCALE

    # The same the other way, and the sign survives the truncation.
    negative = arithmetic.add_giving(
        negated_ceiling, Decimal("-0.02"), receiving=_RECEIVING["pre_amount"]
    )
    assert negative == Decimal("-0.01")

    # The widest sum two of these fields can produce, reached from both fields at
    # their own ceilings: 199999999.98 keeps 99999999.98.
    widest = arithmetic.add_giving(
        ceiling, ceiling, receiving=_RECEIVING["pre_amount"]
    )
    assert widest == Decimal("99999999.98")

    # In range, nothing is discarded, so the truncation is a property of the width
    # and not of the verb.
    assert arithmetic.add_giving(
        ceiling, Decimal("0.00"), receiving=_RECEIVING["pre_amount"]
    ) == ceiling

    # The field's own domain says the same thing in units of its quantum: ten digits,
    # signed both ways because the picture carries an S.
    assert _RECEIVING["pre_amount"].value_domain == (-9999999999, 9999999999)


def test_storing_a_signed_amount_into_an_account_number_drops_the_sign() -> None:
    """An unsigned receiver drops the sign rather than reporting it.

    The three `move ... to pre-ac` in this block - [general/gl070.cbl:L501],
    [general/gl070.cbl:L510] and [general/gl070.cbl:L525] - all send an unsigned
    `pic 9(n)` item into the unsigned `pic 9(6)` at [general/gl070.cbl:L113], so no
    leg's account number can carry a sign FROM THIS BLOCK. The drop is asserted on
    the layer anyway, because it is the receiver's declaration and not the block's
    choice of senders that guarantees it.
    """
    account = _RECEIVING["pre_ac"]
    assert account.signed is False

    # A negative value loses its sign on the way in - no exception, no clamp.
    assert arithmetic.store(-110500, account, rounded=False) == 110500
    # And a value wider than six digits keeps its low-order six.
    assert arithmetic.store(1110500, account, rounded=False) == 110500

    # Which is why every leg's account number is non-negative for every side.
    for side in (_SIDE_CREDIT, _SIDE_DEBIT, _SIDE_UNSET, _SIDE_OTHER):
        for leg in _transcribe_lines_495_to_533(_entered(post_vat_side=side)):
            assert leg.pre_ac >= 0
            assert leg.pre_pc >= 0


# ===========================================================================
# GROUP 8 - the sign behaviour of `multiply ... by -1 giving ...`.
# ===========================================================================


@pytest.mark.parametrize(
    ("value", "negated"),
    [
        pytest.param(Decimal("1200.00"), Decimal("-1200.00"), id="positive"),
        pytest.param(Decimal("-1200.00"), Decimal("1200.00"), id="negative"),
        pytest.param(Decimal("1440.00"), Decimal("-1440.00"), id="gross"),
        pytest.param(Decimal("0.01"), Decimal("-0.01"), id="one-penny"),
        pytest.param(
            Decimal("99999999.99"), Decimal("-99999999.99"), id="field-ceiling"
        ),
    ],
)
def test_negation_preserves_magnitude_and_exponent(
    value: Decimal, negated: Decimal
) -> None:
    """[general/gl070.cbl:L517] flips the sign and changes nothing else.

    An UN-`ROUNDED` store, like every store in this program: there is nothing to
    round, because multiplying a scale-2 value by an integer cannot produce a third
    decimal place. The exponent is nonetheless asserted, because it is the receiving
    field that fixes it and a receiver of a different scale would show here.
    """
    result = arithmetic.multiply_by_giving(
        value, _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
    )
    assert result == negated
    assert result.copy_abs() == value.copy_abs()
    assert result.as_tuple().exponent == -_AMOUNT_SCALE


def test_double_negation_returns_the_original_exactly() -> None:
    """Negating twice is the identity, exactly and not approximately.

    Worth asserting because it is the cheapest available proof that the negation
    neither rounds nor rescales: any loss on the way out would survive the way back.
    """
    for value in (
        Decimal("1200.00"),
        Decimal("-1440.00"),
        Decimal("0.01"),
        Decimal("0.00"),
        Decimal("99999999.99"),
    ):
        once = arithmetic.multiply_by_giving(
            value, _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
        )
        twice = arithmetic.multiply_by_giving(
            once, _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
        )
        assert twice == value
        assert twice.as_tuple() == arithmetic.store(
            value, _RECEIVING["pre_amount"], rounded=False
        ).as_tuple()


def test_negating_zero_yields_a_zero_by_comparison() -> None:
    """A negated zero IS zero, algebraically, and that is all a comparison can say.

    Reachable: a posting entered with a zero amount takes [general/gl070.cbl:L506] or
    [general/gl070.cbl:L515] and then [general/gl070.cbl:L517] negates it. Because
    `-0.00 == 0.00` is True, the sign of the result is invisible to every comparison
    the frozen program makes, so this test asserts the VALUE and says nothing about
    the sign. The byte-level question is Q-70f, immediately below.
    """
    negated = arithmetic.multiply_by_giving(
        Decimal("0.00"), _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
    )
    assert negated == Decimal("0.00")
    assert negated == Decimal("-0.00")
    assert negated == 0
    assert arithmetic.compare(negated, _ZERO) == 0
    assert negated.as_tuple().exponent == -_AMOUNT_SCALE

    # And the whole block with a zero amount: the credit leg is still negated at
    # L517, and the tax leg is still skipped at L521-L523 by its own zero test.
    legs = _transcribe_lines_495_to_533(
        _entered(
            post_vat_side=_SIDE_DEBIT,
            post_amount=Decimal("0.00"),
            vat_amount=Decimal("0.00"),
        )
    )
    assert len(legs) == 2
    assert legs[0].pre_amount == Decimal("0.00")
    assert legs[1].pre_amount == Decimal("0.00")


def test_q70f_a_negated_zero_keeps_the_positive_overpunch_on_the_wire() -> None:
    """Q-70f is SETTLED: an arithmetically negated zero carries the POSITIVE overpunch.

    `multiply pre-amount by -1 giving pre-amount` [general/gl070.cbl:L517] applied to a
    zero amount. Comparison cannot answer this - `Decimal("-0.00") == Decimal("0.00")`
    is True - so the two candidate layouts differ only in the stored BYTE, and the sign
    is overpunched onto the last digit of the zoned `pic s9(8)v99`
    [general/gl070.cbl:L115]. Only the compiled program could say which byte it writes.

    THE MEASUREMENT. GnuCOBOL 3.2.0, `cobc -x -free`, default flags, with
    a `####` sentinel immediately after the item so byte 10 is unambiguously the
    sign-carrying digit and byte 11 is the neighbour:

        move 0.00 to pre-amount                            -> byte 10 = '0'  (0x30)
        multiply pre-amount by -1 giving pre-amount         -> byte 10 = '0'  (0x30)
        compute pre-amount = pre-amount * -1                -> byte 10 = '0'  (0x30)
        move -0.00 to pre-amount        (a LITERAL)         -> byte 10 = 'p'  (0x70)
        12.34 then multiply by -1       (a NON-zero)        -> byte 10 = 't'  (0x74)

    So the ARITHMETIC negation of zero leaves the POSITIVE overpunch: the compiler
    normalises the result's sign to positive because the value is zero. Only a LITERAL
    `-0.00` writes the negative overpunch, and the frozen statement is arithmetic, not a
    literal move. The non-zero row is included to show the negative overpunch IS written
    when the value is actually negative - 't' is 0x74, the negative overpunch of digit 4
    - so the positive byte above is a property of the ZERO and not of the statement.

    This is what `acas_posting/cobol/usage.encode` already emits, so the measurement
    confirms the implementation. The former `xfail(strict=True)` asserted the negative
    form; it is asserted against below so a change in that direction fails by name.
    """
    amount = _RECEIVING["pre_amount"]
    negated = arithmetic.multiply_by_giving(
        Decimal("0.00"), _MINUS_ONE, amount, rounded=False
    )
    encoded = cobol_usage.encode(
        negated,
        usage=amount.usage,
        digits=amount.digits,
        scale=amount.scale,
        signed=amount.signed,
        unsigned=amount.unsigned,
        sign_position=amount.sign_position,
    )
    # Ten bytes, the width being settled independently by the sibling test below.
    assert len(encoded) == _AMOUNT_BYTES

    # THE MEASURED BYTE: the POSITIVE overpunch of digit zero, 0x30.
    assert encoded[-1] == cobol_usage.ZONED_POSITIVE_BASE[0], (
        f"a negated ZERO must carry the POSITIVE overpunch in its sign-carrying "
        f"digit. GnuCOBOL 3.2.0 measures 0x30 for "
        f"`multiply pre-amount by -1 giving pre-amount` on 0.00 - the arithmetic "
        f"normalises a zero result's sign - and 0x70 only for a LITERAL `move -0.00`. "
        f"This encoding ends 0x{encoded[-1]:02x}."
    )
    # AND NOT the negative overpunch, which is the reading the measurement refutes.
    assert encoded[-1] != cobol_usage.ZONED_NEGATIVE_BASE[0]

    # A GENUINELY NEGATIVE amount DOES carry the negative overpunch, so the assertion
    # above is about the zero and not about the layer having lost the sign.
    negative = arithmetic.multiply_by_giving(
        Decimal("12.34"), _MINUS_ONE, amount, rounded=False
    )
    negative_encoded = cobol_usage.encode(
        negative,
        usage=amount.usage,
        digits=amount.digits,
        scale=amount.scale,
        signed=amount.signed,
        unsigned=amount.unsigned,
        sign_position=amount.sign_position,
    )
    assert negative == Decimal("-12.34")
    assert negative_encoded[-1] != cobol_usage.ZONED_POSITIVE_BASE[0]


def test_the_zoned_layout_of_a_negated_amount_is_settled() -> None:
    """What IS settled about the wire form, asserted plainly beside Q-70f.

    Ten bytes, one per digit, the sign overpunched onto the LAST digit and never
    spending a byte of its own, and a round trip through `decode` that returns the
    value unchanged. Only the sign of ZERO is open.
    """
    amount = _RECEIVING["pre_amount"]

    def encode(value: Decimal) -> bytes:
        return cobol_usage.encode(
            value,
            usage=amount.usage,
            digits=amount.digits,
            scale=amount.scale,
            signed=amount.signed,
            unsigned=amount.unsigned,
            sign_position=amount.sign_position,
        )

    positive = encode(Decimal("1200.00"))
    negative = encode(
        arithmetic.multiply_by_giving(
            Decimal("1200.00"), _MINUS_ONE, amount, rounded=False
        )
    )

    assert len(positive) == len(negative) == _AMOUNT_BYTES
    assert cobol_usage.byte_length(
        amount.usage,
        digits=amount.digits,
        scale=amount.scale,
        sign_position=amount.sign_position,
    ) == _AMOUNT_BYTES
    # The two differ in the LAST byte and in no other, which is the overpunch.
    assert positive[:-1] == negative[:-1]
    assert positive[-1] == cobol_usage.ZONED_POSITIVE_BASE[0]
    assert negative[-1] == cobol_usage.ZONED_NEGATIVE_BASE[0]

    # Round trip, so the layout is a representation of the value and not a lossy one.
    for value in (Decimal("1440.00"), Decimal("-1440.00"), Decimal("0.00")):
        assert (
            cobol_usage.decode(
                encode(value),
                usage=amount.usage,
                digits=amount.digits,
                scale=amount.scale,
                signed=amount.signed,
                unsigned=amount.unsigned,
                sign_position=amount.sign_position,
            )
            == value
        )


# ===========================================================================
# GROUP 9 - `gl070` HAS NO `ROUNDED` SITE.
# ===========================================================================

#: The five `ROUNDED` stores in the whole migrated cycle, as data so the census can
#: be read rather than believed. NOT ONE IS IN `gl070`, and
#: `grep -ciE "\\brounded\\b" general/gl070.cbl` returns 0. Agent Action Plan section
#: 0.1.1: "Getting this backwards would corrupt essentially every posted figure."
_ROUNDED_SITES = (
    "general/gl051.cbl:L791",
    "general/gl051.cbl:L796",
    "general/gl080.cbl:L328",
    "irs/irs030.cbl:L1551",
    "irs/irs030.cbl:L1562",
)


def test_the_rounded_census_excludes_gl070() -> None:
    """Five `ROUNDED` sites in the cycle, none of them in this program.

    Recorded as a list rather than as a count so that a reader can check each one,
    and asserted against the arithmetic layer's own two-member rounding vocabulary so
    that the correspondence between the COBOL keyword and the `decimal` mode is
    pinned in this file too.
    """
    assert len(_ROUNDED_SITES) == 5
    assert len(set(_ROUNDED_SITES)) == 5
    assert not [site for site in _ROUNDED_SITES if site.startswith("general/gl070")]
    assert not [site for site in _ROUNDED_SITES if site.startswith("general/gl071")]

    # TRUNCATION IS THE DEFAULT AND ROUNDING IS THE EXCEPTION.
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP
    # COBOL ROUNDED is half AWAY FROM ZERO, which is not Python's banker's rounding.
    assert arithmetic.ROUNDING_DIRECTIONS[True] != decimal.ROUND_HALF_EVEN
    # Two directions and no more, because COBOL has two.
    assert set(arithmetic.ROUNDING_DIRECTIONS) == {False, True}


def test_every_store_in_this_block_is_un_rounded() -> None:
    """The default is truncation, and the default is what all four stores take.

    The block's four arithmetic statements - the two `add ... giving` at
    [general/gl070.cbl:L504] and [general/gl070.cbl:L513], and the two `multiply ...
    by -1 giving` at [general/gl070.cbl:L517] and [general/gl070.cbl:L529-L530] -
    are all written without `ROUNDED`, so all four truncate.

    IN THIS BLOCK THE TWO DIRECTIONS AGREE, and that is worth stating rather than
    hiding: every operand and every receiver is scale 2, so no store has a third
    decimal place to discard. The difference is therefore demonstrated on the layer,
    with an operand no field in `wspost.cob` could supply, to prove which direction
    the default actually is.
    """
    posting = _entered()

    # Explicit `rounded=False` and the omitted default agree, statement by statement.
    assert arithmetic.add_giving(
        posting.post_amount,
        posting.vat_amount,
        receiving=_RECEIVING["pre_amount"],
    ) == arithmetic.add_giving(
        posting.post_amount,
        posting.vat_amount,
        receiving=_RECEIVING["pre_amount"],
        rounded=False,
    )
    assert arithmetic.multiply_by_giving(
        Decimal("1440.00"), _MINUS_ONE, _RECEIVING["pre_amount"]
    ) == arithmetic.multiply_by_giving(
        Decimal("1440.00"), _MINUS_ONE, _RECEIVING["pre_amount"], rounded=False
    )

    # Rounding would make no difference to this block's own data either, which is why
    # the absence of `ROUNDED` here is invisible in a table dump.
    for side in (_SIDE_CREDIT, _SIDE_DEBIT, _SIDE_UNSET):
        truncating = _transcribe_lines_495_to_533(_entered(post_vat_side=side))
        assert [leg.pre_amount for leg in truncating] == [
            arithmetic.store(leg.pre_amount, _RECEIVING["pre_amount"], rounded=True)
            for leg in truncating
        ]

    # And the direction the default takes, shown where it IS observable: eight
    # thousandths truncates to nothing and rounds to a penny.
    eight_thousandths = Decimal("0.008")
    assert arithmetic.store(
        eight_thousandths, _RECEIVING["pre_amount"], rounded=False
    ) == Decimal("0.00")
    assert arithmetic.store(
        eight_thousandths, _RECEIVING["pre_amount"], rounded=True
    ) == Decimal("0.01")
    # Half away from zero on both signs, which `ROUND_HALF_EVEN` would not give for
    # the first of these.
    assert arithmetic.store(
        Decimal("0.005"), _RECEIVING["pre_amount"], rounded=True
    ) == Decimal("0.01")
    assert arithmetic.store(
        Decimal("-0.005"), _RECEIVING["pre_amount"], rounded=True
    ) == Decimal("-0.01")
    # Truncation is toward ZERO, not toward negative infinity.
    assert arithmetic.store(
        Decimal("-0.008"), _RECEIVING["pre_amount"], rounded=False
    ) == Decimal("0.00")


# ==========================================================================
#
#  THE TWO BEHAVIOURS A TABLE DUMP CANNOT SEE, LOCKED BY CALL SEQUENCE INSTEAD.
#
#  Two anomaly locks rule R-4 requires, neither of which can be held by a state
#  comparison, for the same structural reason: the behaviour under test is
#  a call that changes no row.
#
#    * ANOMALY A-1, `[sales/sl060.cbl:L1172-L1178]` - the missing terminating period nests
#      `GL-Posting-Close` inside `if IRS-Used OR IRS-Both-Used`, so in PURE GENERAL LEDGER
#      mode the posting file is never closed. A CLOSE writes nothing. Adding the missing
#      period - the single most likely well-meaning correction to that paragraph, and the
#      likeliest slip in any fresh translation of it - changes which verbs are performed
#      and changes NO TABLE. `tests/scenarios/test_clean_batch_post_sl.py` compares
#      `GLPOSTING-REC` on both sides and passes either way, which makes it a witness that
#      the two implementations agree rather than a lock on A-1.
#
#    * ANOMALY A-4's SIBLING PATH, `[irs/irs030.cbl:L1630-L1634]` - the IR032 clean
#      rejection. When the DEBIT account is missing the program reports and loops, writing
#      no nominal row and no posting row. Its whole signature is an ABSENCE, and an absence
#      is invisible in a diff of two runs that both produce it: a transcription that
#      aborted the run instead of continuing, or that committed the debit anyway, is
#      indistinguishable from the frozen one by any comparison of end state on the
#      fixture this scenario seeds.
#
#  WHAT THIS FILE THEREFORE DOES. It drives the SHIPPED paragraphs - not a transcription of
#  them - with a recording stand-in in the module's `facade` slot, and asserts the sequence
#  of verbs performed. That is the observable the frozen behaviour actually differs in, and
#  it is the only one that discriminates. Each lock below was verified to FAIL against the
#  specific wrong implementation it exists to catch.
#
#  NOTHING HERE ASSERTS A FIGURE THE ORACLE HAS NOT ARBITRATED, and nothing here repairs
#  anything. A-1 is asserted in its DEFECTIVE form: the assertion is that in pure General
#  Ledger mode `gl_posting_close` is NOT performed. Rule R-4 is explicit - "a defect
#  reproduced is correct; a defect fixed is a failure" - so this file turns RED if the
#  period is added, which is the entire point of it.
#
#  INFRASTRUCTURE: NONE. No Docker, no MariaDB, no GnuCOBOL and no database connection.
#  The facade is replaced before any verb runs, so no handler and no driver is reached; the
#  only prerequisite is `data_dictionary/acas_posting_dictionary.json`, which the record
#  layer loads for its descriptors.
#
#  Agent Action Plan references: section 0.6.7 entries A-1 and A-4; section 0.6.5 on
#  rejection paths and their database effect; section 0.4.3, which permits this tier
#  `cobol` and `records` and requires a program import to be deferred into function scope.
#
# ==========================================================================


#: The dotted names this file drives. Strings rather than imports, so nothing crosses
#: the tier boundary at COLLECTION time - Agent Action Plan section 0.4.3, and the
#: property `test_no_arithmetic_module_imports_a_program_or_dal_at_module_level` holds.
_SL060: Final[str] = "acas_posting.programs.sl060_invoice_posting"
_IRS030: Final[str] = "acas_posting.programs.irs030_posting"


#: Prefixes this tier must not leave resident, copied from the sibling shipped-paragraph
#: files so that one file's import cannot make another's freshness claim vacuous.
_TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
    "harness",
    "mysql",
    "numpy",
    "pandas",
    "sqlalchemy",
)


#: `to-day pic x(10)` in DD/MM/CCYY form, pinned so two runs are byte-identical.
_TO_DAY: Final[str] = "21/09/2025"

#: `88 IRS-Used value "Y".` and `88 IRS-Both-Used value "B".`
#: [copybooks/wssystem.cob:L179-L181]. The third state is the LITERAL SPACE the field is
#: declared `pic x` for, and it is what "pure General Ledger mode" means here - not the
#: absence of a value and not a token `N`, which the switch has no value for.
_IRS_USED: Final[str] = "Y"
_IRS_BOTH_USED: Final[str] = "B"
_IRS_NEITHER: Final[str] = " "

#: `88 G-L value 1.` on `07 Level-1 pic 9.` [copybooks/wssystem.cob:L84-L85]. NOT on the
#: fan-out switch: pure General Ledger mode is the TWO-FIELD statement
#: `Level-1 = 1` AND `IRS-Instead = space`, which is exactly what makes A-1 observable.
_LEVEL_1_GENERAL_LEDGER: Final[int] = 1
_LEVEL_1_NOT_GENERAL_LEDGER: Final[int] = 0

#: `if we-error = 2` [irs/irs030.cbl:L1630] - the handler's "record not found". The
#: frozen test is EQUALITY with 2 and is deliberately not widened to "not = zero".
_WE_ERROR_RECORD_NOT_FOUND: Final[int] = 2
_WE_ERROR_SUCCESS: Final[int] = 0

#: `IR032` [irs/irs030.cbl:L1631] - the message identifier the clean rejection reports.
_IR032: Final[str] = "IR032"


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix this tier must not leave loaded?

    Args:
        name: A `sys.modules` key.

    Returns:
        Whether it is tier-isolated.
    """
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped(dotted_name: str) -> Iterator[types.ModuleType]:
    """Import a shipped program FOR REAL for one test, leaving `sys.modules` as found.

    NOT `pytest.importorskip`. A shipped module that cannot be imported is a FAILURE,
    not a skip: `mysql-connector-python==26.7.0` is a hard `requirements.txt` pin, so an
    installed tree always has it, and an anomaly lock that can vanish into a skip line
    is not a lock.

    NOT memoised. Eviction first, so the import really re-executes the module's
    top-level code and the purge afterwards really removes what it added.

    Args:
        dotted_name: The importable name.

    Yields:
        The imported module.

    Raises:
        AssertionError: The name survived the eviction, or residue survived the purge.
        ImportError: The module could not be imported. Deliberately not a skip.
    """
    for resident in sorted(
        (name for name in sys.modules if _is_tier_isolated_name(name)), reverse=True
    ):
        del sys.modules[resident]
    assert dotted_name not in sys.modules, (
        f"{dotted_name} survived the eviction, so its top-level code will not "
        f"re-execute and the purge below would remove nothing."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(dotted_name)
        assert sys.modules.get(dotted_name) is module
        yield module
        completed = True
    finally:
        for name in sorted(set(sys.modules) - before, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name for name in set(sys.modules) - before if _is_tier_isolated_name(name)
        )
        if completed:
            assert not residue, f"{dotted_name} left {residue} resident after the purge."


@contextlib.contextmanager
def _driving(module: types.ModuleType, double: object) -> Iterator[None]:
    """Put `double` in `module`'s `facade` slot for the duration, then put it back.

    Args:
        module: The shipped program module.
        double: The recording stand-in. It must publish `FacadeContext`, because the
            program builds its contexts through the same module attribute.

    Yields:
        Nothing; the block runs with the double installed.
    """
    real = module.facade
    assert hasattr(real, "FacadeContext")
    assert hasattr(double, "FacadeContext")
    module.facade = double
    try:
        yield
    finally:
        module.facade = real


@contextlib.contextmanager
def _program_log(logger_name: str) -> Iterator[list[logging.LogRecord]]:
    """Collect every record ONE shipped program's own logger emits.

    A handler on that one logger rather than `caplog`, so the semantics layer's records
    - which belong to their own tests - cannot be mistaken for the program's.

    Args:
        logger_name: The program module's dotted name, which is its logger name.

    Yields:
        The records, in emission order.
    """
    records: list[logging.LogRecord] = []

    class _Collect(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger(logger_name)
    handler = _Collect()
    previous = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)


# ---------------------------------------------------------------------------
#  1.  ANOMALY A-1 - THE NESTED POSTING CLOSE IN `sl060`
#
#  [sales/sl060.cbl] `ca000-BL-Close section.` opens at L1158. The four lines that
#  matter, verbatim:
#
#      L1174       perform  GL-Batch-Close.                *>  close Batch-file.
#      L1175       if       IRS-Used OR IRS-Both-Used
#      L1176                perform SPL-Posting-Close      *>  close irs-post-file
#      L1177       if       IRS-Both-Used or G-L
#      L1178                perform GL-Posting-Close.      *>  close posting-file.
#
#  L1176 carries NO terminating period, so L1177's IF is NESTED INSIDE L1175's and the
#  single period at the end of L1178 closes BOTH. `GL-Posting-Close` therefore runs only
#  when
#
#      (IRS-Used OR IRS-Both-Used)  AND  (IRS-Both-Used OR G-L)
#
#  and in pure General Ledger mode the OUTER test is false, so it never runs at all.
#  The three sibling sites all HAVE the period - [purchase/pl060.cbl:L1031],
#  [sales/sl100.cbl:L694], [purchase/pl100.cbl:L675] - which is what makes A-1 an
#  accident of transcription rather than a house idiom.
#
#  A truth table over the two fields is the discriminating observable, and there is no
#  other: closing a file writes nothing.
# ---------------------------------------------------------------------------


class _Sl060CloseDouble:
    """The four facade verbs `ca000-BL-Close` performs, with a call log.

    Attributes:
        calls: Verb names in invocation order.
    """

    def __init__(self, facade_module: types.ModuleType) -> None:
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []

    def _served(self, verb: str, ctx: Any) -> None:
        self.calls.append(verb)
        #  Every verb reports success, so the fs-reply diagnostic at
        #  [sales/sl060.cbl:L1162-L1171] stays out of these tests: it is a DISPLAY with
        #  no control transfer and no table effect, and its own behaviour is not what
        #  A-1 is about.
        ctx.file_access.fs_reply = 0

    def gl_batch_write(self, ctx: Any) -> None:
        self._served("gl_batch_write", ctx)

    def gl_batch_close(self, ctx: Any) -> None:
        self._served("gl_batch_close", ctx)

    def spl_posting_close(self, ctx: Any) -> None:
        self._served("spl_posting_close", ctx)

    def gl_posting_close(self, ctx: Any) -> None:
        self._served("gl_posting_close", ctx)


def _sl060_state(sl060: types.ModuleType, *, irs_instead: str, level_1: int) -> Any:
    """A bound `sl060` state with the two fields the close paragraph reads.

    Args:
        sl060: The shipped module.
        irs_instead: `05 IRS-Instead pic x.` - "Y", "B" or the literal space.
        level_1: `07 Level-1 pic 9.` - 1 is `88 G-L`.

    Returns:
        The state.
    """
    from acas_posting import workfiles
    from acas_posting.records.calling_data import WsCallingData
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.otm3 import OiHeader
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.system_record_4 import SystemRecord4

    state = sl060._new_state(
        WsCallingData(),
        SystemRecord(),
        SystemRecord4(),
        _TO_DAY,
        FileDefs(),
        workfiles.open_item_work_file("otm2-in-memory", OiHeader),
    )
    state.system_record.general_ledger_block.irs_instead = irs_instead
    state.system_record.system_data_block.level.level_1 = level_1
    return state


#: The full truth table of `ca000-BL-Close`'s two nested tests, as the frozen nesting
#: produces it. `(irs_instead, level_1, spl_posting_close?, gl_posting_close?)`.
#:
#: ROW 1 IS A-1. `IRS-Instead = space` and `Level-1 = 1` is pure General Ledger mode:
#: IF#3 would be TRUE on its own, and it is unreachable because IF#2 is false. THAT
#: UNREACHABILITY IS THE DEFECT, and it is what row 1 asserts.
_CLOSE_TRUTH_TABLE: Final[tuple[tuple[str, int, bool, bool], ...]] = (
    (_IRS_NEITHER, _LEVEL_1_GENERAL_LEDGER, False, False),
    (_IRS_NEITHER, _LEVEL_1_NOT_GENERAL_LEDGER, False, False),
    (_IRS_USED, _LEVEL_1_GENERAL_LEDGER, True, True),
    (_IRS_USED, _LEVEL_1_NOT_GENERAL_LEDGER, True, False),
    (_IRS_BOTH_USED, _LEVEL_1_GENERAL_LEDGER, True, True),
    (_IRS_BOTH_USED, _LEVEL_1_NOT_GENERAL_LEDGER, True, True),
)


@pytest.mark.parametrize(
    ("irs_instead", "level_1", "expect_spl", "expect_gl"),
    _CLOSE_TRUTH_TABLE,
    ids=[
        f"irs={'space' if irs else irs!r}-level1={level}"
        for irs, level, _, _ in _CLOSE_TRUTH_TABLE
    ],
)
def test_a1_the_posting_close_follows_the_nested_predicate(
    irs_instead: str, level_1: int, expect_spl: bool, expect_gl: bool
) -> None:
    """A-1's LOCK: `GL-Posting-Close` obeys the NESTED test, not a sibling one.

    Driven over the whole two-field truth table, because the defect is precisely a
    disagreement between the nested reading and the sibling reading, and they differ in
    exactly ONE row - `IRS-Instead = space` with `Level-1 = 1`. A test that exercised
    only the IRS states would pass against both readings and prove nothing.

    DO NOT ADD THE MISSING PERIOD to [sales/sl060.cbl:L1176]. This test exists so that
    doing so, or writing the "obviously correct" sibling `if` in a fresh translation of
    `ca000-BL-Close`, turns the suite RED instead of passing unnoticed (R-4).

    Args:
        irs_instead: The fan-out switch value.
        level_1: The installed-ledger level byte.
        expect_spl: Whether `SPL-Posting-Close` is performed.
        expect_gl: Whether `GL-Posting-Close` is performed.
    """
    with _shipped(_SL060) as sl060:
        double = _Sl060CloseDouble(sl060.facade)
        state = _sl060_state(sl060, irs_instead=irs_instead, level_1=level_1)
        with _driving(sl060, double):
            sl060._ca000_bl_close(state)

    #  The two UNCONDITIONAL verbs ran, whatever the switch says. L1161's write and
    #  L1174's close sit outside both tests, so their presence is what establishes that
    #  the paragraph ran at all and the absences below are real.
    assert double.calls[:2] == ["gl_batch_write", "gl_batch_close"], (
        f"the unconditional head of the paragraph did not run in source order; the "
        f"call log was {double.calls!r}. [sales/sl060.cbl:L1161] writes the batch and "
        f"L1174 closes it, and L1173's period is what makes L1174 unconditional."
    )

    assert ("spl_posting_close" in double.calls) is expect_spl, (
        f"IF#2 [sales/sl060.cbl:L1175] `if IRS-Used OR IRS-Both-Used` was evaluated "
        f"wrongly for IRS-Instead={irs_instead!r}: expected "
        f"spl_posting_close={expect_spl}, call log {double.calls!r}."
    )

    assert ("gl_posting_close" in double.calls) is expect_gl, (
        f"ANOMALY A-1 IS NOT REPRODUCED for IRS-Instead={irs_instead!r}, "
        f"Level-1={level_1}: expected gl_posting_close={expect_gl} and the call log "
        f"was {double.calls!r}.\n"
        f"  [sales/sl060.cbl:L1176] CARRIES NO TERMINATING PERIOD, so L1177's `if "
        f"IRS-Both-Used or G-L` is NESTED INSIDE L1175's `if IRS-Used OR "
        f"IRS-Both-Used` and the period at the end of L1178 closes both. "
        f"`GL-Posting-Close` therefore runs only when BOTH tests pass.\n"
        f"  IF THIS FAILED ON THE FIRST ROW - space / 1 - THE PERIOD HAS BEEN ADDED, "
        f"or the two tests have been written as siblings. That is a defect FIXED, "
        f"which rule R-4 makes a failure: 'a defect reproduced is correct; a defect "
        f"fixed is a failure.' Restore the nesting. Recorded as A-1 in "
        f"docs/migration/anomaly-log.md."
    )


def test_a1_the_nested_and_sibling_readings_differ_on_exactly_one_row() -> None:
    """The DETECTOR detects: the two readings disagree, and only in pure GL mode.

    Without this, the truth table above could be a table of the SIBLING reading and
    every row would still pass. So the two predicates are evaluated independently over
    the same six rows and required to disagree on exactly one - which is both the proof
    that the table discriminates and the statement of what A-1 costs.
    """
    disagreements: list[tuple[str, int]] = []
    for irs_instead, level_1, _, nested in _CLOSE_TRUTH_TABLE:
        #  The SIBLING reading - what the code would do WITH the period at L1176 - is
        #  IF#3 alone.
        sibling = irs_instead == _IRS_BOTH_USED or level_1 == _LEVEL_1_GENERAL_LEDGER
        if sibling != nested:
            disagreements.append((irs_instead, level_1))

    assert disagreements == [(_IRS_NEITHER, _LEVEL_1_GENERAL_LEDGER)], (
        f"the nested and sibling readings disagree on {disagreements!r}. A-1's whole "
        f"cost is that they disagree on PURE GENERAL LEDGER MODE and nowhere else - "
        f"which is why [purchase/pl060.cbl:L1031]'s identical statement WITH the "
        f"period is A-1's control, and why the sales clean-batch scenario is the only "
        f"journey on which the defect is even reachable."
    )


def test_a1_is_not_observable_in_any_table_and_this_file_says_why() -> None:
    """The premise of this section: a CLOSE has no database effect.

    Stated as an assertion rather than left in a comment, because it is the reason the
    lock lives here and not in `tests/scenarios/test_clean_batch_post_sl.py`. Both
    posting-close verbs are pure lifecycle calls: neither takes a value, neither returns
    one, and the record area each is handed is the one the program is already holding.
    A run that performed them and a run that did not leave the same rows, so the
    scenario comparison is a WITNESS to the two sides agreeing and not a detector.
    """
    with _shipped(_SL060) as sl060:
        real = sl060.facade
        for verb in ("gl_posting_close", "spl_posting_close", "gl_batch_close"):
            assert hasattr(real, verb), f"the facade does not publish {verb}"

        #  The two runs that differ ONLY in whether the posting file was closed produce
        #  the same record areas. Compared field by field on the two records the close
        #  verbs are handed, so the claim is measured rather than asserted.
        import dataclasses

        observed = []
        for irs_instead in (_IRS_NEITHER, _IRS_USED):
            double = _Sl060CloseDouble(sl060.facade)
            state = _sl060_state(
                sl060,
                irs_instead=irs_instead,
                level_1=_LEVEL_1_GENERAL_LEDGER,
            )
            with _driving(sl060, double):
                sl060._ca000_bl_close(state)
            observed.append(
                (
                    "gl_posting_close" in double.calls,
                    dataclasses.astuple(state.ws_posting_record),
                    dataclasses.astuple(state.ws_irs_posting_record),
                )
            )

    #  The verb sets DIFFER ...
    assert observed[0][0] is False and observed[1][0] is True
    #  ... and the record areas the verbs were handed are IDENTICAL, so no dump of
    #  GLPOSTING-REC or PSIRSPOST-REC could tell the two runs apart.
    assert observed[0][1] == observed[1][1], (
        "the posting record differs between the two runs, which would mean a close "
        "verb mutates it - it does not, and if it ever did this section's premise "
        "would need re-deriving."
    )
    assert observed[0][2] == observed[1][2]


# ---------------------------------------------------------------------------
#  2.  THE IR032 CLEAN REJECTION IN `irs030`
#
#  [irs/irs030.cbl:L1626-L1634]. `Input-Loop` moves the transfer record's DEBIT account
#  into the nominal key, reads it, and then:
#
#      L1630       if       we-error = 2
#      L1631                display  IR032 ...
#      L1632                display  WS-IRS-Post-DR ...
#      L1633                accept   WS-Reply at 2340
#      L1634                go to    Input-Loop.
#
#  So a missing DEBIT account is a CLEAN REJECTION: report, and take the next transfer
#  record. Nothing is written - which is the whole difference from anomaly A-4 twenty
#  lines later, where the DEBIT is committed at L1641 BEFORE the CREDIT account is
#  looked up at L1647, leaving a half-posted double entry when the CREDIT is the one
#  that is missing.
#
#  THE TWO PATHS ARE ADJACENT, DIFFER IN THEIR DATABASE EFFECT, AND ARE EASY TO
#  CONFLATE. Agent Action Plan section 0.6.5 separates them for exactly that reason.
#  A fixture cannot: the missing-debit path writes nothing, so on any seed both a
#  faithful implementation and one that aborted the run - or that committed the debit
#  anyway and then failed - can be made to leave the same rows. Only the verb sequence,
#  and whether the NEXT record is still processed, tells them apart.
# ---------------------------------------------------------------------------


class _Irs030Double:
    """The transfer file, the IRS nominal file and the posting file, in memory.

    Attributes:
        calls: Verb names in invocation order.
        rewrites: `(nl_owning, nl_dr, nl_cr)` per `acasirsub1-Rewrite`.
        writes: `Post-Key` per `acasirsub4-Write`.
        lookups: The `NL-Owning` each `acasirsub1-Read-Indexed` was asked for.
    """

    def __init__(
        self,
        facade_module: types.ModuleType,
        *,
        transfers: tuple[Mapping[str, object], ...] = (),
        missing_accounts: frozenset[int] = frozenset(),
    ) -> None:
        self.FacadeContext = facade_module.FacadeContext
        self.calls: list[str] = []
        self.rewrites: list[tuple[int, Decimal, Decimal]] = []
        self.writes: list[int] = []
        self.lookups: list[int] = []
        self._transfers = list(transfers)
        self._missing = missing_accounts

    def acas008_read_next(self, ctx: Any) -> None:
        """`acas008-Read-Next` - one transfer record, or at end."""
        self.calls.append("acas008_read_next")
        if not self._transfers:
            ctx.file_access.fs_reply = 10
            return
        row = self._transfers.pop(0)
        for attribute, value in row.items():
            setattr(ctx.record, attribute, value)
        ctx.file_access.fs_reply = 0
        ctx.file_access.we_error = _WE_ERROR_SUCCESS

    def acasirsub1_read_indexed(self, ctx: Any) -> None:
        """`acasirsub1-Read-Indexed` - the account, or `we-error = 2`."""
        self.calls.append("acasirsub1_read_indexed")
        requested = ctx.record.nl_key.nl_owning
        self.lookups.append(requested)
        if requested in self._missing:
            #  `we-error = 2` is the handler's RECORD NOT FOUND, and the frozen tests
            #  at [irs/irs030.cbl:L1630] and [:L1648] are EQUALITY with 2.
            ctx.file_access.we_error = _WE_ERROR_RECORD_NOT_FOUND
            ctx.file_access.fs_reply = 21
            return
        ctx.file_access.we_error = _WE_ERROR_SUCCESS
        ctx.file_access.fs_reply = 0
        ctx.record.nl_data.nl_dr = Decimal("0.00")
        ctx.record.nl_data.nl_cr = Decimal("0.00")

    def acasirsub1_rewrite(self, ctx: Any) -> None:
        """`acasirsub1-Rewrite` - persist one side of the double entry."""
        self.calls.append("acasirsub1_rewrite")
        record = ctx.record
        self.rewrites.append(
            (record.nl_key.nl_owning, record.nl_data.nl_dr, record.nl_data.nl_cr)
        )
        ctx.file_access.we_error = _WE_ERROR_SUCCESS
        ctx.file_access.fs_reply = 0

    def acasirsub4_write(self, ctx: Any) -> None:
        """`acasirsub4-Write` - the posting record."""
        self.calls.append("acasirsub4_write")
        #  `01 Posting-Record` [copybooks/irswspost.cob] names its key `Post-Key`;
        #  the COLUMN it lands in is `KEY-4` [mysql/ACASDB.sql], which is the
        #  bridge's renaming and not this record's field name.
        self.writes.append(ctx.record.post_key)
        ctx.file_access.we_error = _WE_ERROR_SUCCESS
        ctx.file_access.fs_reply = 0


def _irs030_ws(irs030: types.ModuleType) -> Any:
    """`irs030`'s working storage, bound with the two VAT snapshots zeroed.

    Args:
        irs030: The shipped module.

    Returns:
        The `_WorkingStorage`.
    """
    #  Each name from the module the SHIPPED program imports it from, so a record
    #  moving between modules breaks this helper rather than silently binding a
    #  different class: `WsIrsPostingRecord` is the SPL/IRS transfer layout in
    #  `spl_irs_posting`, NOT the internal posting record in `irs_posting`, and
    #  `AcasDalCommonData` lives with the test-data flags.
    from acas_posting.records.file_access import FileAccess
    from acas_posting.records.file_defs import FileDefs
    from acas_posting.records.irs_dflt import WsIrsDefaultRecord
    from acas_posting.records.irs_nominal import WsIrsnlRecord
    from acas_posting.records.irs_posting import PostingRecord
    from acas_posting.records.irs_system import IrsSystemParams
    from acas_posting.records.spl_irs_posting import WsIrsPostingRecord
    from acas_posting.records.system_record import SystemRecord
    from acas_posting.records.test_data_flags import AcasDalCommonData

    return irs030._WorkingStorage(
        irs_system_params=IrsSystemParams(),
        ws_system_record=SystemRecord(),
        file_defs=FileDefs(),
        file_access=FileAccess(),
        dal_common=AcasDalCommonData(),
        ws_irsnl_record=WsIrsnlRecord(),
        ws_irs_default_record=WsIrsDefaultRecord(),
        posting_record=PostingRecord(),
        ws_irs_posting_record=WsIrsPostingRecord(),
        nl31_record=irs030._NlSnapshot(),
        nl32_record=irs030._NlSnapshot(),
        post_record_cnt=0,
        clear_posting_file=False,
        dal_options={},
    )


def _transfer(*, debit: int, credit: int, amount: str) -> dict[str, object]:
    """One transfer record, as `acas008-Read-Next` would deliver it.

    Args:
        debit: `WS-IRS-Post-DR`.
        credit: `WS-IRS-Post-CR`.
        amount: `WS-IRS-Post-Amount`, as a STRING so no binary float is built (R-2).

    Returns:
        The attribute values to set on the record area.
    """
    return {
        "ws_irs_post_dr": debit,
        "ws_irs_post_cr": credit,
        "ws_irs_post_amount": Decimal(amount),
        "ws_irs_vat_amount": Decimal("0.00"),
        "ws_irs_vat_ac_def": 0,
        "ws_irs_post_vat_side": " ",
    }


def test_ir032_a_missing_debit_account_writes_nothing_at_all() -> None:
    """THE CLEAN REJECTION: no nominal rewrite, no posting write.

    One transfer record whose DEBIT account is absent. The frozen path reports IR032 and
    loops [irs/irs030.cbl:L1630-L1634], so the run must reach the next read having
    written NOTHING - and in particular must not have committed the debit, which is what
    the ADJACENT missing-CREDIT path does twenty lines later as anomaly A-4.
    """
    with _shipped(_IRS030) as irs030:
        double = _Irs030Double(
            irs030.facade,
            transfers=(_transfer(debit=1010, credit=2020, amount="100.00"),),
            missing_accounts=frozenset({1010}),
        )
        ws = _irs030_ws(irs030)
        with _program_log(_IRS030) as log:
            with _driving(irs030, double):
                irs030._input_loop(ws)

    #  NOTHING WAS WRITTEN. Both absences asserted, because they are different claims:
    #  no nominal side was persisted, and no posting record was created.
    assert double.rewrites == [], (
        f"a nominal account was rewritten on the missing-DEBIT path: "
        f"{double.rewrites!r}. [irs/irs030.cbl:L1634] takes the next transfer record "
        f"BEFORE reaching the rewrite at L1641, so this path is a CLEAN rejection. "
        f"Committing the debit here would turn it into anomaly A-4, which is the "
        f"missing-CREDIT path and a different behaviour."
    )
    assert double.writes == [], (
        f"a posting record was written on the missing-DEBIT path: {double.writes!r}. "
        f"`acasirsub4-Write` is at [irs/irs030.cbl:L1670] and is unreachable from "
        f"L1634."
    )
    assert "acasirsub1_rewrite" not in double.calls
    assert "acasirsub4_write" not in double.calls

    #  THE DEBIT ACCOUNT WAS LOOKED UP, so the rejection is the one this test means and
    #  not a loop that never got started.
    assert double.lookups == [1010], (
        f"the debit account was not the only lookup: {double.lookups!r}. If the CREDIT "
        f"account was also read, control passed L1634 and this is not the clean path."
    )

    #  IT REPORTED, and reported the frozen identifier. The account number is
    #  deliberately withheld from the log (CWE-532) - the DISPOSITION is what is
    #  asserted, not the screen text.
    messages = [record.getMessage() for record in log]
    assert any(_IR032 in message for message in messages), (
        f"the clean rejection reported nothing recognisable; the log was {messages!r}. "
        f"[irs/irs030.cbl:L1631] displays IR032, and section 0.3.4 makes a diagnostic "
        f"with no database effect a log record."
    )


def test_ir032_processing_CONTINUES_to_the_next_transfer_record() -> None:
    """The rejection is a `GO TO Input-Loop`, NOT an abort.

    THE DISCRIMINATING HALF, and the reason the test above is not sufficient on its own:
    an implementation that ABORTED the run on a missing debit account would satisfy
    every "wrote nothing" assertion while being a different program. So two transfer
    records are served - the first with a missing debit, the second sound - and the
    SECOND must be posted in full.

    [irs/irs030.cbl:L1634] is `go to Input-Loop`, class 1 in the four-class taxonomy: a
    loop-back, which becomes `continue`. A `break` there would be class 2 and would end
    the walk.
    """
    with _shipped(_IRS030) as irs030:
        double = _Irs030Double(
            irs030.facade,
            transfers=(
                _transfer(debit=1010, credit=2020, amount="100.00"),
                _transfer(debit=3030, credit=4040, amount="250.00"),
            ),
            missing_accounts=frozenset({1010}),
        )
        ws = _irs030_ws(irs030)
        with _driving(irs030, double):
            irs030._input_loop(ws)

    #  THREE reads: the rejected record, the sound record, and the at-end that ends the
    #  walk. Two would mean the rejection ended it.
    assert double.calls.count("acas008_read_next") == 3, (
        f"the transfer file was read {double.calls.count('acas008_read_next')} "
        f"time(s); three are required - the rejected record, the sound record and the "
        f"at-end. Fewer means the missing debit ENDED the walk, which makes "
        f"[irs/irs030.cbl:L1634] a class-2 terminator instead of the class-1 loop-back "
        f"it is.\n  call log: {double.calls!r}"
    )

    #  The SECOND record was posted in full: both sides of the double entry and the
    #  posting record.
    assert [key for key, _, _ in double.rewrites] == [3030, 4040], (
        f"the sound record's double entry was not posted to both accounts: "
        f"{double.rewrites!r}. The debit is rewritten at [irs/irs030.cbl:L1641] and "
        f"the credit at [irs/irs030.cbl:L1660]."
    )
    assert len(double.writes) == 1, (
        f"the sound record produced {len(double.writes)} posting record(s); exactly "
        f"one is required [irs/irs030.cbl:L1670]."
    )

    #  And the counter counted BOTH records, because `add 1 to Post-Record-Cnt`
    #  [irs/irs030.cbl:L1623] precedes the account lookup and is therefore reached by
    #  the rejected record too. A display counter only - it reaches no table - and it is
    #  asserted here because it is the one field that distinguishes "the record was
    #  seen" from "the record was skipped before being counted".
    assert ws.post_record_cnt == 2, (
        f"Post-Record-Cnt is {ws.post_record_cnt}; it counts every record READ, and "
        f"[irs/irs030.cbl:L1623] sits BEFORE the missing-account test at L1630."
    )


def test_ir032_and_a4_are_different_paths_with_different_effects() -> None:
    """The missing-DEBIT and missing-CREDIT paths are not interchangeable.

    Both are "an account was not found", they are twenty lines apart, and they have
    OPPOSITE database effects: the debit path writes nothing, and the credit path leaves
    the debit already committed. Agent Action Plan section 0.6.5 separates them, and
    this test is what makes the separation checkable rather than a matter of reading.

    A-4 is asserted in its DEFECTIVE form - one rewrite, unbalanced, and no posting
    record. Rule R-4 forbids repairing it, and a transcription that looked the credit
    account up BEFORE committing the debit would be exactly that repair.
    """
    with _shipped(_IRS030) as irs030:
        #  Missing DEBIT.
        debit_double = _Irs030Double(
            irs030.facade,
            transfers=(_transfer(debit=1010, credit=2020, amount="100.00"),),
            missing_accounts=frozenset({1010}),
        )
        with _driving(irs030, debit_double):
            irs030._input_loop(_irs030_ws(irs030))

        #  Missing CREDIT - anomaly A-4.
        credit_double = _Irs030Double(
            irs030.facade,
            transfers=(_transfer(debit=1010, credit=2020, amount="100.00"),),
            missing_accounts=frozenset({2020}),
        )
        with _driving(irs030, credit_double):
            irs030._input_loop(_irs030_ws(irs030))

    #  The debit path: nothing.
    assert debit_double.rewrites == [] and debit_double.writes == []

    #  The credit path: THE DEBIT IS ALREADY COMMITTED, and there is no posting record -
    #  a half-posted double entry, which is anomaly A-4 exactly as recorded.
    assert [key for key, _, _ in credit_double.rewrites] == [1010], (
        f"ANOMALY A-4 IS NOT REPRODUCED. The missing-CREDIT path must leave the DEBIT "
        f"already rewritten, because [irs/irs030.cbl:L1641] commits it BEFORE the "
        f"credit account is looked up at L1647. Observed rewrites: "
        f"{credit_double.rewrites!r}.\n"
        f"  If this shows NO rewrite, the credit lookup has been moved ahead of the "
        f"debit commit - a defect FIXED, which rule R-4 makes a failure."
    )
    assert credit_double.writes == [], (
        f"the missing-credit path wrote a posting record: {credit_double.writes!r}. "
        f"[irs/irs030.cbl:L1652] leaves for the next record before L1670."
    )

    #  Stated as the comparison it is, so the asymmetry is the assertion rather than an
    #  observation about two separate numbers.
    assert len(credit_double.rewrites) > len(debit_double.rewrites), (
        "the two missing-account paths left the same database effect, so one of them "
        "has been made to behave like the other. They are deliberately different: "
        "section 0.6.5 classes the debit path as a CLEAN rejection and the credit path "
        "as a PARTIAL one."
    )
