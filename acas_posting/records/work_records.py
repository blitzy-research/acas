"""The General Ledger work-record layouts: pre-trans, post-trans and sort-trans.

Three record layouts carry data between the four General Ledger posting phases.
`gl070` explodes each entered posting into legs and writes them; `gl071` sorts
that stream; `gl072` walks the sorted stream and posts to the nominal ledger.
This module declares those layouts and nothing else - no sequence, no buffer,
no cursor, no reader, no writer, no sort and no file name.

Agent Action Plan section 0.4.1.3 gives the module its whole mandate:

    acas_posting/records/work_records.py | CREATE |
    general/gl070.cbl + general/gl071.cbl |
    "The pre-trans and post-trans work-record layouts used across the three GL
    phases"

Two further frozen sources are read as specification alongside those two.
`general/gl072.cbl` declares the SAME `01 post-trans-record` with a DIFFERENT
structure - see "TWO DECLARATIONS, ONE FILE" below - and
`copybooks/wspost.cob` is where every value moved into a work record comes
from, which is what proves the eight-character date is inherited rather than
truncated.

THE FOUR FILE DESCRIPTIONS, AND WHERE EACH IS DECLARED
======================================================
    fd  pre-trans.     [general/gl070.cbl:L106]   writes the stream
    01  pre-trans-record.                         [general/gl070.cbl:L108]
    fd  pre-trans.     [general/gl071.cbl:L110]   reads it back to sort
    01  pre-trans-record.                         [general/gl071.cbl:L112]
    fd  post-trans.    [general/gl071.cbl:L122]   receives the sorted stream
    01  post-trans-record.                        [general/gl071.cbl:L124]
    sd  sort-trans.    [general/gl071.cbl:L134]   the SORT work description
    01  sort-trans-record.                        [general/gl071.cbl:L136]
    fd  post-trans.    [general/gl072.cbl:L108]   reads the sorted stream
    01  post-trans-record.                        [general/gl072.cbl:L110]

`gl071`'s `pre-trans-record` [general/gl071.cbl:L112-L120] is byte-for-byte
identical to `gl070`'s [general/gl070.cbl:L108-L116]: the same eight fields,
the same pictures, the same order, the same `03` levels. Two programs, one
layout, declared twice - duplication the COBOL never factored into a copybook,
even though `fdpost.cob`, `fdbatch.cob` and `fdledger.cob` exist and sit
commented out beside the declarations [general/gl070.cbl:L118-L119],
[general/gl072.cbl:L121-L122]. That duplication is a source oddity and is
preserved, not tidied: this module declares the layout once per COBOL `01`
name, exactly as the frozen source does.

NO COPYBOOK, NO BRIDGE, NO TABLE - WHY THIS MODULE IS THE ONE EXCEPTION (R-5)
============================================================================
Every other module in this package derives from a `copybooks/*.cob` file that a
`common/*MT.cbl` bridge maps to a MySQL table, and every one of its fields
cites a generated dictionary entry. This module can do neither, and the reason
is structural rather than an omission:

  * The layouts are declared INLINE in the programs' FILE SECTIONs, listed
    above. No copybook declares them.
  * The two files are `organization line sequential` scratch files
    [general/gl071.cbl:L92-L95], [general/gl071.cbl:L97-L100] - transient work
    files named at [copybooks/wsnames.cob:L15-L16], both carrying the
    maintainer's own `*> gl071` annotation.
  * There is no `.scb` directive block, no bridge program and no table
    declaration in the frozen schema for any of these fields.

Agent Action Plan section 0.3.1 states the consequence, verbatim:

    "Work files are in-process sequences, not tables and not temporary files.
    ... These are transient scratch files, not part of the schema ... Nothing
    about them reaches the database, so nothing about them appears in a table
    dump."

The absence was probed rather than assumed, against the generated artifact:
`loader.find_entry` returns None for every field of all three records;
`loader.entries_for_copybook_record` raises for all three record names; and no
table of the 22 in scope has a name containing TRANS. `loader.coverage()`
reports 513 in-scope columns, 513 covered, across those 22 tables - complete,
and none of them a work file.

So rule R-5's traceability is delivered here by the OTHER half of the
descriptor provenance invariant. Every descriptor in this module is built by
`FieldDescriptor.for_working_storage(...)` with a MANDATORY `source_locator`
naming the exact file-description line, and carries `dictionary_key` as None.
A reader of `docs/migration/traceability.md` who finds these fields citing a
program line rather than a dictionary key is looking at the documented
exception, not at a gap.

ZERO DRIFT - THE ONLY MODULE IN THIS PACKAGE THAT HAS NONE
==========================================================
Drift is disagreement between the copybook view, the bridge host variable and
the MySQL column. With no bridge and no column there is no third and second
view to disagree with the first, so there is no signedness narrowing here, no
character-width change, no name truncation and no type-class change. Every
`descriptor.drift()` in this module returns None, and `anomaly_refs()` and
`ambiguity_refs()` both return empty. Said plainly because a reader arriving
from `otm3.py` or `sales_ledger.py` will expect a drift section and deserves to
be told why there is not one.

The field metadata is still not typed by eye. The eight pictures below are
IDENTICAL to eight in `copybooks/wspost.cob`, which the generated dictionary
does cover, so each argument was cross-checked against the artifact's own
recorded metadata for the same picture text - `s9(8)v99` at
[copybooks/wspost.cob:L23] is recorded as DISPLAY, signed, sign trailing
included, 10 digits, 8 integer digits, scale 2, carried by `decimal.Decimal`,
and that is what this module states for every `-amount`.

THE MOST LOAD-BEARING LAYOUT IN THE MIGRATION  (anomaly A-14)
=============================================================
`gl072` locates the nominal-ledger account for a posting with a SEQUENTIAL
read, not an indexed one:

    405      move     post-ledger  to  WS-Ledger-Key.
    407      if       read-ledger not = "R"
    408               perform  GL-Nominal-Read-Next.

[general/gl072.cbl:L405], [general/gl072.cbl:L407-L408]. It finds the right
account ONLY because `gl071` has already emitted the stream in nominal-key
order. Agent Action Plan section 0.6.4, verbatim:

    "Any change in sort stability or key composition produces silent
    misposting - no error, no diagnostic, wrong balances."

The sort that establishes that order, verbatim [general/gl071.cbl:L172-L178]:

    172      sort     sort-trans
    173               on ascending key sort-batch
    174                                sort-ac
    175                                sort-pc
    176                                sort-post
    177               using  pre-trans
    178               giving post-trans.

Four keys, all ascending, in the order batch, ac, pc, post - which is NOT the
record's declaration order (batch, post, code, date, ac, pc, amount, legend).
`sort-post` is the fourth key although it is the second field. The whole of
`gl071` contains no arithmetic at all.

That statement is quoted here for traceability and is deliberately NOT turned
into a key list this module publishes. The keys are `gl071`'s behaviour, not
this record's data: the stable sort with COBOL key semantics belongs to
`acas_posting/cobol/sortverb.py` and the phase that performs it to
`acas_posting/programs/gl071_batch_sort.py`. What this module owns is the field
widths and their order, and if either is wrong the keys are wrong with them.

TWO DECLARATIONS, ONE FILE - `01 post-trans-record` IS DECLARED TWICE, DIFFERENTLY
=================================================================================
`gl071` writes `post-trans` with `post-ac` and `post-pc` FLAT at level `03`:

    124  01  post-trans-record.
    129      03  post-ac         pic 9(6).
    130      03  post-pc         pic 99.

`gl072` reads the SAME physical file with the same two fields wrapped in a
group:

    110  01  post-trans-record.
    115      03  post-ledger.
    116          05  post-ac     pic 9(6).
    117          05  post-pc     pic 99.

Same `01` name, same eight characters (6 + 2), two incompatible COBOL views.
The reason is in the source rather than inferred: `gl072` consumes the group AS
A UNIT at exactly three sites, and `grep -n "post-ledger"` returns nothing at
all against `gl070` or `gl071`.

    309      if       post-ledger not = save-ledger      [general/gl072.cbl:L309]
    317      move     post-ledger  to  save-ledger.      [general/gl072.cbl:L317]
    405      move     post-ledger  to  WS-Ledger-Key.    [general/gl072.cbl:L405]

`gl070` and `gl071` only ever touch `-ac` and `-pc` individually, so they have
no use for a group; `gl072` needs an eight-character composite to move into
`WS-Ledger-Key` [copybooks/wsledger.cob] before the sequential read above.

BOTH views are carried below - `PostTransRecord`'s flat attributes for
`gl071`'s declaration and a `PostLedger` value on the same record for
`gl072`'s. Neither is described as the settled one, and the two are NOT kept
in step with one another: the COBOL does not keep them in step either, they
are two views over the same characters, and rule R-3 forbids adding the logic
that would align them.

THE EIGHT-CHARACTER DATE IS INHERITED, NOT TRUNCATED
====================================================
`-date` is `pic x(8)`. It is EIGHT characters, and a reader who assumes those
eight are a truncation of the ten-character run date will hunt a bug that is
not there. The provenance is exact:

    18      03  Post-Date       pic x(8).    *> 20   [copybooks/wspost.cob:L18]

    498      move     post-date    to  pre-date.     [general/gl070.cbl:L498]

An `x(8)` sending field into an `x(8)` receiving field. The eight-character
form originates in the GL posting record itself. It is NOT derived from
`to-day pic x(10)` [general/gl071.cbl:L159], which is a separate linkage
parameter this module never touches. Nothing here reads a clock or formats a
date; the run date reaches the cycle only through the controlled clock at the
command-line boundary (rule R-6).

`-amount` CARRIES NO USAGE CLAUSE, SO ITS SIGN IS TRAILING AND INCLUDED
=======================================================================
`pic s9(8)v99` with no usage clause and no SIGN clause is a zoned DISPLAY item
whose sign overpunches the last digit: ten characters, ten digits, scale 2,
signed, sign trailing included. It is not packed and not binary. Contrast the
two in-scope copybooks that DO write a sign clause, and spell it differently -
`pic s9(7)v99   sign leading` [copybooks/wspost-irs.cob:L21] and
`pic s9(7)v99  sign is leading` [copybooks/irswspost.cob:L14]. Here there is
no clause at all, so `sign_clause_text` is None on every `-amount` below.

The same picture with no usage clause governs `Post-Amount` and `Vat-Amount`
[copybooks/wspost.cob:L23], [copybooks/wspost.cob:L28], so the choice is
consistent from the posting record through to the work record. And it matters
in practice: [general/gl070.cbl:L517] negates every credit leg with
`multiply pre-amount by -1 giving pre-amount`, so MOST records in the stream
carry a negative amount.

WIDTHS, AND THE ARITHMETIC THAT CLOSES
======================================
    1   -batch    pic 9(5)       5 characters
    6   -post     pic 9(5)       5
    11  -code     pic xx         2
    13  -date     pic x(8)       8
    21  -ac       pic 9(6)       6
    27  -pc       pic 99         2
    29  -amount   pic s9(8)v99  10
    39  -legend   pic x(32)     32
                                --
                                70 characters

The eight leaf widths sum to seventy, and there is nothing in the frozen source
for that figure to contradict: no `record contains` clause, no size comment and
no `01`-level buffer picture appears in any of the four file descriptions. Two
records of this package close cleanly and this is one of them.

No length or offset constant is declared here even so. The figure above is
prose, the widths live in the descriptors, and the sum is recomputed by the
verification suite from `descriptor.byte_length` rather than read from a name
that could drift away from them.

WHAT THIS MODULE DELIBERATELY DOES NOT DO
=========================================
    * No input or output of any kind, no file name and no directory. The two
      work files are real files on disk in the COBOL, which makes the
      temptation structurally close; this module declares layouts only (R-1).
      The file names belong to `records/file_defs.py`, which models
      `copybooks/wsnames.cob`.
    * No sequence, buffer, cursor, iterator, reader or writer. Those belong to
      `acas_posting/workfiles.py`, which imports this module. The edge runs
      one way only, and importing it back from here would be a circular import
      that breaks the infrastructure-free arithmetic test tier.
    * No sort and no key list, per the sort section above.
    * No `fs-reply`. `gl071` declares it as an independent `77` item,
      `77  fs-reply            pic xx.` [general/gl071.cbl:L150] -
      ALPHANUMERIC - while [copybooks/wsfnctn.cob:L25] declares the same
      logical status field as `Fs-Reply pic 99`, NUMERIC. Two pictures for one
      status field, in two files. The divergence is noted for traceability;
      the field itself belongs to `records/file_access.py`.
    * No `prog-name`, the other `77` at [general/gl071.cbl:L149]. A `77` is an
      independent elementary item and part of no record.
    * No condition names. None of the four file descriptions declares an `88`,
      verified by grep across all three programs, and none is invented here.
    * No FILLER, no OCCURS and no REDEFINES clause, for the same reason: the
      frozen source declares none in any of the four file descriptions.
    * No screen handling. `gl071` opens with
      `display  "Sorting.......Please wait            " at 0801` with a colour
      attribute [general/gl071.cbl:L170]; per Agent Action Plan section 0.3.4
      that becomes a log line in the program module, and it has no database
      effect and no place here.
    * No numeric test on `-batch`. `if post-batch not numeric`
      [general/gl072.cbl:L291] is `gl072`'s silent skip - anomaly A-13 - and
      belongs to `programs/gl072_transaction_update.py`. Adding a check at
      construction would add validation the migration may not add (R-3).

LAYERING  (Agent Action Plan section 0.4.3)
===========================================
    MAY import       `acas_posting.cobol.field`, the `acas_posting.dictionary`
                     public surface, and the standard library
    MUST NOT import  dal, programs, cli, clock, dates, workfiles,
                     cobol.arithmetic, cobol.move, cobol.picture, cobol.usage,
                     cobol.condition_names, cobol.sortverb,
                     dictionary.generate, the comparison oracle in its sibling
                     tree - and ANY other module of this package

Four sibling record modules are cited by this one and imported by none of them.
`records/gl_posting.py` models `copybooks/wspost.cob`, whose field names shadow
these almost exactly, which is precisely why `gl070` has to qualify three
references (see the anomaly register below); `records/gl_ledger.py` models the
`WS-Ledger-Key` that [general/gl072.cbl:L405] moves the group into;
`records/file_defs.py` owns the work-file names; `records/file_access.py` owns
`Fs-Reply`. Citing is traceability. Importing would dissolve the leaf layer
that lets `tests/arithmetic/*` run with no database at all.

The two enumerations below come from `acas_posting.dictionary.model` because
the loader publishes only its errors and accessors and re-exports no
enumeration, and because `for_working_storage` takes a usage and a sign
position as arguments. `acas_posting.cobol.field` reaches them by the same
edge. No competing copy of either is defined in this package.

ANOMALY REGISTER FOR THIS MODULE  (rule R-4: reproduced, never repaired)
=======================================================================
Each item below is reproduced with a comment citing its locator at the site.
The register of every such site across the migration is
`docs/migration/anomaly-log.md`.

    A-14  The nominal account is found by a sequential read, so correctness
          depends entirely on the upstream sort order and on these widths
          [general/gl072.cbl:L405], [general/gl072.cbl:L407-L408], fed by
          [general/gl071.cbl:L172-L178].
    new   `01 post-trans-record` declared two different ways for one physical
          file [general/gl071.cbl:L124-L132] against
          [general/gl072.cbl:L110-L119], with the three group-consuming
          statements as the reason.
    A-21  Field-name collisions force qualified references, and the two
          qualifier keywords are mixed within 28 lines:
          `post-code in WS-Posting-Record` [general/gl070.cbl:L497] uses IN,
          while `vat-ac of WS-Posting-Record` [general/gl070.cbl:L521] and
          [general/gl070.cbl:L525] use OF. COBOL treats the two as exact
          synonyms. On the locator: the Agent Action Plan cites this anomaly at
          [general/gl070.cbl:L510]; that line is
          `move     post-cr      to  pre-ac.`, an unqualified move. The three
          qualified sites are L497, L521 and L525, established by grep against
          the frozen file.
    A-15  The same shape as the batch-record size contradiction, here closed
          by a dated note rather than left standing: `copybooks/wspost.cob`
          records its own size twice, `*> 98 bytes 26/03/09` then `*> 96 bytes
          20/12/11 (leading sign removed)` [copybooks/wspost.cob:L6-L7].
          Quoted, nothing added.
    --    The eight-character date is inherited, not truncated
          [copybooks/wspost.cob:L18].
    --    `-amount` carries no usage clause, so the sign is trailing and
          included, unlike the two explicit sign-leading spellings.
    --    `77  fs-reply  pic xx.` [general/gl071.cbl:L150] against
          `Fs-Reply pic 99` [copybooks/wsfnctn.cob:L25].
    --    The debit leg tests `= "CR"` [general/gl070.cbl:L503] while the
          credit leg tests `= "DR"` [general/gl070.cbl:L512]. Two nearly
          identical blocks that are not the same condition - which is what a
          reader skimming them will assume.
    --    Eight commented-out COPY statements surround these file
          descriptions, and they come in matched SELECT/FD pairs - one pair
          per file the program no longer reaches through a copybook:
          `*> copy "selpost.cob".` with `*> copy "selbatch.cob".`
          [general/gl070.cbl:L98-L99] and `*> copy "fdpost.cob".` with
          `*> copy "fdbatch.cob".` [general/gl070.cbl:L118-L119]; then
          `*> copy "seledger.cob".` with `*> copy "selbatch.cob".`
          [general/gl072.cbl:L99-L100] and `*> copy "fdledger.cob".` with
          `*> copy "fdbatch.cob".` [general/gl072.cbl:L121-L122]. `gl071`
          carries none at all, which fits: it opens only the three work
          files and reaches no posting, batch or ledger file. All eight are
          quoted; nothing is modelled from any of them.
    --    `sd sort-trans.` [general/gl071.cbl:L134] is a SORT-FILE description
          rather than an `fd`, and it is the only one of the three assigned to
          a numbered handle: `select  sort-trans  assign file-21.`
          [general/gl071.cbl:L102] against the two work-file names.
    --    The sort key order is not the declaration order
          [general/gl071.cbl:L173-L176].
    --    Every field name in all four file descriptions is entirely lower
          case, unusually for this codebase, and every descriptor below
          carries it that way verbatim.
    --    `pre-trans-record` is declared twice, identically, in two programs
          [general/gl070.cbl:L108-L116] and [general/gl071.cbl:L112-L120].

QUESTIONS FOR THE COMPILED ORACLE  (rule R-6)
=============================================
These cannot be settled by reading the source, so the compiled program settles
them and the arbitration is written down in
`docs/migration/ambiguity-resolutions.md`.

    1.  Does `gl072` read exactly the characters `gl071` wrote, given the two
        different `01` declarations? The flat and grouped forms occupy the same
        eight characters on paper; only execution confirms that line-sequential
        input and output agree.
    2.  How is `pic s9(8)v99` with no usage clause rendered in a line-
        sequential file? A trailing included sign is the expected form, but the
        exact byte for a negative value - and whether an overpunch is emitted
        at all - must be measured. Most records carry a negative amount
        [general/gl070.cbl:L517], so this is not a corner case.
    3.  What exactly do the eight characters of `-date` contain? Eight from
        [copybooks/wspost.cob:L18], but whether the separators are solidus
        characters and whether the year is two digits must be read from a real
        posting row rather than inferred.
    4.  Is the sort stable, and does the compiled SORT preserve input order for
        equal keys? Section 0.4.1.4 requires the Python sort to guarantee
        stability BECAUSE `gl072` reads sequentially; the compiled behaviour
        establishes whether stability is relied upon in practice.
    5.  Does line-sequential organization pad or trim the trailing spaces of
        `-legend pic x(32)`?
    6.  What reaches `-batch` when it is not numeric [general/gl072.cbl:L291]?
        The disposition is `gl072`'s to reproduce, but the test implies such
        records can exist in the file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary.model import SignPosition, Usage

__all__: Final[tuple[str, ...]] = (
    "COBOL_FIELD_METADATA_KEY",
    "PostLedger",
    "PostTransRecord",
    "PreTransRecord",
    "SortTransRecord",
)


# =============================================================================
#  HOW A FIELD CITES ITS FROZEN SOURCE  (rule R-5)
# =============================================================================

# Each dataclass attribute below carries the `FieldDescriptor` of the COBOL item
# it mirrors, in the dataclasses-native `metadata` mapping under this key. The
# binding is therefore mechanical: an attribute and its storage description are
# declared in one place and cannot drift apart, and the description is reachable
# at runtime without this module publishing a loose constant per field.
#
#     from dataclasses import fields
#     from acas_posting.records.work_records import (
#         COBOL_FIELD_METADATA_KEY, PreTransRecord,
#     )
#     for member in fields(PreTransRecord):
#         cobol = member.metadata[COBOL_FIELD_METADATA_KEY]
#         print(member.name, cobol.name, cobol.cite())
#
# Every descriptor in this module is built by
# `FieldDescriptor.for_working_storage(...)` and carries a `source_locator`
# naming its file-description line, never a `dictionary_key`: the generated
# dictionary covers copybook records mapped to tables, and these three layouts
# are declared in program FILE SECTIONs and mapped to no table at all. The
# provenance invariant is satisfied by the locator half of it, which is the
# documented exception the module docstring sets out.
COBOL_FIELD_METADATA_KEY: Final[str] = "cobol_field"


# =============================================================================
#  pre-trans-record   [general/gl070.cbl:L108-L116] = [general/gl071.cbl:L112-L120]
# =============================================================================
#
# The declaration `gl070` writes and `gl071` reads back, verbatim from
# [general/gl070.cbl:L108-L116]:
#
#     108  01  pre-trans-record.
#     109      03  pre-batch       pic 9(5).
#     110      03  pre-post        pic 9(5).
#     111      03  pre-code        pic xx.
#     112      03  pre-date        pic x(8).
#     113      03  pre-ac          pic 9(6).
#     114      03  pre-pc          pic 99.
#     115      03  pre-amount      pic s9(8)v99.
#     116      03  pre-legend      pic x(32).
#
# [general/gl071.cbl:L113-L120] repeats those eight lines byte for byte. The
# locators below cite `gl070`, which declares AND writes the record; `gl071`'s
# identical lines are recorded in the class docstring so that a reader following
# either program finds the declaration it is looking at. Field names are carried
# entirely lower case, as the frozen source spells them.

_PRE_BATCH: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-batch",
    source_locator="general/gl070.cbl:L109",
    usage=Usage.DISPLAY,
    picture="9(5)",
    digits=5,
    integer_digits=5,
    scale=0,
    parent_group="pre-trans-record",
)

_PRE_POST: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-post",
    source_locator="general/gl070.cbl:L110",
    usage=Usage.DISPLAY,
    picture="9(5)",
    digits=5,
    integer_digits=5,
    scale=0,
    parent_group="pre-trans-record",
)

_PRE_CODE: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-code",
    source_locator="general/gl070.cbl:L111",
    usage=Usage.ALPHANUMERIC,
    picture="xx",
    character_length=2,
    parent_group="pre-trans-record",
)

# R-4, and the single easiest field in this module to get wrong. EIGHT
# characters, not ten. `move post-date to pre-date` [general/gl070.cbl:L498] is
# an x(8) sending field into an x(8) receiving field, because the eight-
# character form is declared at source by `03  Post-Date       pic x(8).`
# [copybooks/wspost.cob:L18]. It is not a truncation of `to-day pic x(10)`
# [general/gl071.cbl:L159] and the missing century is not restored here.
_PRE_DATE: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-date",
    source_locator="general/gl070.cbl:L112",
    usage=Usage.ALPHANUMERIC,
    picture="x(8)",
    character_length=8,
    parent_group="pre-trans-record",
)

# R-4 / anomaly A-14. This field and `pre-pc` below become the second and third
# sort keys [general/gl071.cbl:L174-L175], and their sorted order is the only
# reason `gl072`'s sequential nominal read [general/gl072.cbl:L405],
# [general/gl072.cbl:L407-L408] finds the right account. Six digits, and a
# wrong width here misposts money with no error and no diagnostic.
_PRE_AC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-ac",
    source_locator="general/gl070.cbl:L113",
    usage=Usage.DISPLAY,
    picture="9(6)",
    digits=6,
    integer_digits=6,
    scale=0,
    parent_group="pre-trans-record",
)

_PRE_PC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-pc",
    source_locator="general/gl070.cbl:L114",
    usage=Usage.DISPLAY,
    picture="99",
    digits=2,
    integer_digits=2,
    scale=0,
    parent_group="pre-trans-record",
)

# R-4. `pic s9(8)v99` carries NO usage clause and NO sign clause, so it is a
# zoned DISPLAY item of ten characters whose sign overpunches the last digit -
# `sign_clause_text` is None, unlike `sign leading`
# [copybooks/wspost-irs.cob:L21] and `sign is leading`
# [copybooks/irswspost.cob:L14]. Carried by `decimal.Decimal` at scale 2 and
# never by a binary fraction (R-2): [general/gl072.cbl:L331] accumulates it
# straight into `ledger-balance`, which is `pic s9(8)v99 comp-3`
# [copybooks/wsledger.cob] and a `decimal(10,2)` column, so an inexact carrier
# would corrupt every posted balance. [general/gl070.cbl:L517] negates every
# credit leg, so most values here are negative.
_PRE_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-amount",
    source_locator="general/gl070.cbl:L115",
    usage=Usage.DISPLAY,
    picture="s9(8)v99",
    signed=True,
    sign_position=SignPosition.TRAILING_INCLUDED,
    sign_clause_text=None,
    digits=10,
    integer_digits=8,
    scale=2,
    parent_group="pre-trans-record",
)

_PRE_LEGEND: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="pre-legend",
    source_locator="general/gl070.cbl:L116",
    usage=Usage.ALPHANUMERIC,
    picture="x(32)",
    character_length=32,
    parent_group="pre-trans-record",
)


# =============================================================================
#  post-trans-record, `gl071`'s FLAT declaration   [general/gl071.cbl:L124-L132]
# =============================================================================
#
# Verbatim [general/gl071.cbl:L124-L132]:
#
#     124  01  post-trans-record.
#     125      03  post-batch      pic 9(5).
#     126      03  post-post       pic 9(5).
#     127      03  post-code       pic xx.
#     128      03  post-date       pic x(8).
#     129      03  post-ac         pic 9(6).
#     130      03  post-pc         pic 99.
#     131      03  post-amount     pic s9(8)v99.
#     132      03  post-legend     pic x(32).
#
# R-4. `post-ac` and `post-pc` sit FLAT at level 03 here. `gl072` declares the
# same two fields as `05` children of a `03 post-ledger.` group
# [general/gl072.cbl:L115-L117], so both levels are carried - the flat pair
# below and the grouped pair further down - and neither declaration is described
# as the settled one.

_POST_BATCH: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-batch",
    source_locator="general/gl071.cbl:L125",
    usage=Usage.DISPLAY,
    picture="9(5)",
    digits=5,
    integer_digits=5,
    scale=0,
    parent_group="post-trans-record",
)

_POST_POST: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-post",
    source_locator="general/gl071.cbl:L126",
    usage=Usage.DISPLAY,
    picture="9(5)",
    digits=5,
    integer_digits=5,
    scale=0,
    parent_group="post-trans-record",
)

_POST_CODE: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-code",
    source_locator="general/gl071.cbl:L127",
    usage=Usage.ALPHANUMERIC,
    picture="xx",
    character_length=2,
    parent_group="post-trans-record",
)

# R-4. Eight characters, inherited from [copybooks/wspost.cob:L18] through
# [general/gl070.cbl:L498]; see `_PRE_DATE`. Not a truncation.
_POST_DATE: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-date",
    source_locator="general/gl071.cbl:L128",
    usage=Usage.ALPHANUMERIC,
    picture="x(8)",
    character_length=8,
    parent_group="post-trans-record",
)

# R-4. `gl071`'s FLAT level-03 declaration of the account number
# [general/gl071.cbl:L129]. Second sort key [general/gl071.cbl:L174].
_POST_AC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-ac",
    source_locator="general/gl071.cbl:L129",
    usage=Usage.DISPLAY,
    picture="9(6)",
    digits=6,
    integer_digits=6,
    scale=0,
    parent_group="post-trans-record",
)

# R-4. `gl071`'s FLAT level-03 declaration of the profit centre
# [general/gl071.cbl:L130]. Third sort key [general/gl071.cbl:L175].
_POST_PC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-pc",
    source_locator="general/gl071.cbl:L130",
    usage=Usage.DISPLAY,
    picture="99",
    digits=2,
    integer_digits=2,
    scale=0,
    parent_group="post-trans-record",
)

# R-4. No usage clause, so the sign is trailing and included; see `_PRE_AMOUNT`.
# This is the value [general/gl072.cbl:L331] adds straight into the nominal
# ledger balance with `add post-amount to ledger-balance.`
_POST_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-amount",
    source_locator="general/gl071.cbl:L131",
    usage=Usage.DISPLAY,
    picture="s9(8)v99",
    signed=True,
    sign_position=SignPosition.TRAILING_INCLUDED,
    sign_clause_text=None,
    digits=10,
    integer_digits=8,
    scale=2,
    parent_group="post-trans-record",
)

_POST_LEGEND: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-legend",
    source_locator="general/gl071.cbl:L132",
    usage=Usage.ALPHANUMERIC,
    picture="x(32)",
    character_length=32,
    parent_group="post-trans-record",
)


# =============================================================================
#  post-trans-record, `gl072`'s GROUPED declaration  [general/gl072.cbl:L110-L119]
# =============================================================================
#
# R-4, and the reproduction site of the anomaly the module docstring calls
# "TWO DECLARATIONS, ONE FILE". Verbatim [general/gl072.cbl:L110-L119]:
#
#     110  01  post-trans-record.
#     111      03  post-batch      pic 9(5).
#     112      03  post-post       pic 9(5).
#     113      03  post-code       pic xx.
#     114      03  post-date       pic x(8).
#     115      03  post-ledger.
#     116          05  post-ac     pic 9(6).
#     117          05  post-pc     pic 99.
#     118      03  post-amount     pic s9(8)v99.
#     119      03  post-legend     pic x(32).
#
# Same `01` name as [general/gl071.cbl:L124], same physical file, same eight
# characters (6 + 2) - and no group at all in `gl071`. `gl070` and `gl071` only
# ever touch `-ac` and `-pc` individually; `gl072` consumes the composite as a
# unit at exactly three sites, and it needs those eight characters whole in
# order to move them into `WS-Ledger-Key` [copybooks/wsledger.cob]:
#
#     309      if       post-ledger not = save-ledger
#     317      move     post-ledger  to  save-ledger.
#     405      move     post-ledger  to  WS-Ledger-Key.
#
# `grep -n "post-ledger"` returns nothing against `general/gl070.cbl` or
# `general/gl071.cbl`, which is why the group is declared for `gl072`'s view
# alone.
#
# ON `redefines`: it is left as None. `gl072` writes no REDEFINES clause - the
# group IS its declaration - and stating one would transcribe a construct the
# frozen source does not contain. The redefines-SHAPED relationship here is not
# between two items of one program but between two programs' declarations of one
# `01` record, which no REDEFINES clause in either file expresses. Both views
# are carried and both are cited; neither is settled in favour of the other.

_POST_LEDGER: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-ledger",
    source_locator="general/gl072.cbl:L115",
    usage=Usage.GROUP,
    is_group=True,
    redefines=None,
    parent_group="post-trans-record",
)

# The `05` children of that group. Their names are identical to `_POST_AC` and
# `_POST_PC` above and their pictures are identical too, but the declarations
# are a different level in a different program at a different line, so they are
# described separately rather than shared.
_POST_LEDGER_AC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-ac",
    source_locator="general/gl072.cbl:L116",
    usage=Usage.DISPLAY,
    picture="9(6)",
    digits=6,
    integer_digits=6,
    scale=0,
    parent_group="post-ledger",
)

_POST_LEDGER_PC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="post-pc",
    source_locator="general/gl072.cbl:L117",
    usage=Usage.DISPLAY,
    picture="99",
    digits=2,
    integer_digits=2,
    scale=0,
    parent_group="post-ledger",
)


# =============================================================================
#  sort-trans-record   [general/gl071.cbl:L136-L144]
# =============================================================================
#
# Verbatim [general/gl071.cbl:L136-L144]:
#
#     136  01  sort-trans-record.
#     137      03  sort-batch      pic 9(5).
#     138      03  sort-post       pic 9(5).
#     139      03  sort-code       pic xx.
#     140      03  sort-date       pic x(8).
#     141      03  sort-ac         pic 9(6).
#     142      03  sort-pc         pic 99.
#     143      03  sort-amount     pic s9(8)v99.
#     144      03  sort-legend     pic x(32).
#
# R-4. Its file description is `sd  sort-trans.` [general/gl071.cbl:L134] - a
# SORT-FILE description rather than an `fd` - and it is the only one of the three
# assigned to a numbered handle, `select  sort-trans  assign file-21.`
# [general/gl071.cbl:L102], where the other two take work-file names.
#
# R-4. Four of these eight fields are the sort keys, in the order batch, ac, pc,
# post [general/gl071.cbl:L173-L176] - which is NOT this declaration order, and
# `sort-post` is the fourth key although it is the second field. The keys are
# quoted in the module docstring for traceability and are deliberately not
# published from here: they are `gl071`'s behaviour, not this record's data.

_SORT_BATCH: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-batch",
    source_locator="general/gl071.cbl:L137",
    usage=Usage.DISPLAY,
    picture="9(5)",
    digits=5,
    integer_digits=5,
    scale=0,
    parent_group="sort-trans-record",
)

_SORT_POST: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-post",
    source_locator="general/gl071.cbl:L138",
    usage=Usage.DISPLAY,
    picture="9(5)",
    digits=5,
    integer_digits=5,
    scale=0,
    parent_group="sort-trans-record",
)

_SORT_CODE: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-code",
    source_locator="general/gl071.cbl:L139",
    usage=Usage.ALPHANUMERIC,
    picture="xx",
    character_length=2,
    parent_group="sort-trans-record",
)

# R-4. Eight characters, inherited from [copybooks/wspost.cob:L18]; see
# `_PRE_DATE`. Not a truncation.
_SORT_DATE: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-date",
    source_locator="general/gl071.cbl:L140",
    usage=Usage.ALPHANUMERIC,
    picture="x(8)",
    character_length=8,
    parent_group="sort-trans-record",
)

_SORT_AC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-ac",
    source_locator="general/gl071.cbl:L141",
    usage=Usage.DISPLAY,
    picture="9(6)",
    digits=6,
    integer_digits=6,
    scale=0,
    parent_group="sort-trans-record",
)

_SORT_PC: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-pc",
    source_locator="general/gl071.cbl:L142",
    usage=Usage.DISPLAY,
    picture="99",
    digits=2,
    integer_digits=2,
    scale=0,
    parent_group="sort-trans-record",
)

# R-4. No usage clause, so the sign is trailing and included; see `_PRE_AMOUNT`.
_SORT_AMOUNT: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-amount",
    source_locator="general/gl071.cbl:L143",
    usage=Usage.DISPLAY,
    picture="s9(8)v99",
    signed=True,
    sign_position=SignPosition.TRAILING_INCLUDED,
    sign_clause_text=None,
    digits=10,
    integer_digits=8,
    scale=2,
    parent_group="sort-trans-record",
)

_SORT_LEGEND: Final[FieldDescriptor] = FieldDescriptor.for_working_storage(
    name="sort-legend",
    source_locator="general/gl071.cbl:L144",
    usage=Usage.ALPHANUMERIC,
    picture="x(32)",
    character_length=32,
    parent_group="sort-trans-record",
)


# =============================================================================
#  THE RECORDS
# =============================================================================
#
# Plain dataclasses, as Agent Action Plan section 0.8.1 requires: "Plain modules
# and dataclasses; no ORM entity layer." Nothing here derives from a base class,
# declares a schema, emits a statement or runs a check on a value.
#
# MUTABLE ON PURPOSE - not frozen. `gl070` fills a record area field by field
# and then writes it three times over, rewriting only `-ac`, `-pc` and `-amount`
# between the debit and credit legs [general/gl070.cbl:L495-L519] while
# `-batch`, `-post`, `-code`, `-date` and `-legend` carry over from the first
# write. A frozen record could not reproduce that, and `gl072` mutates a record
# area as it reads too.
#
# `slots=True` closes each record at exactly the attributes its file description
# declares, so a typo raises instead of quietly inventing a ninth field. It adds
# no field, no check and no behaviour of its own.
#
# FIELD ORDER FOLLOWS DECLARATION ORDER, never sort-key order: batch, post,
# code, date, ac, pc, amount, legend. A reader can set `dataclasses.fields` of
# any record below beside a `sed -n` of its file description and read the two
# line for line, which is what makes the paragraph-level traceability of R-5
# checkable and what keeps the widths - and therefore the sort keys - honest.
#
# The default on each attribute is the empty value of its carrier, so that a
# record area can be brought into existence and then filled the way the COBOL
# fills it. It is a construction convenience of the Python translation and is
# NOT a claim about what a COBOL file record area holds before its first move;
# nothing in this module depends on that, and only the compiled program could
# settle it.


@dataclass(slots=True)
class PreTransRecord:
    """`01  pre-trans-record.` - the exploded posting legs `gl070` writes.

    Declared identically in TWO programs, and either may be cited:

        01  pre-trans-record.            [general/gl070.cbl:L108-L116]
        01  pre-trans-record.            [general/gl071.cbl:L112-L120]

    `gl070` declares it under `fd  pre-trans.` [general/gl070.cbl:L106] and
    writes it three times per entered posting - a debit leg, a credit leg
    negated by `multiply pre-amount by -1 giving pre-amount`
    [general/gl070.cbl:L517], and a value-added-tax leg written only when both
    the tax account and the tax amount are non-zero [general/gl070.cbl:L521-L523].
    `gl071` declares the same eight fields under its own `fd  pre-trans.`
    [general/gl071.cbl:L110] and names the file as the SORT input
    [general/gl071.cbl:L177]. The duplication is the frozen source's, not this
    module's: the two declarations are byte for byte the same, and the COBOL
    never factored them into a copybook even though three file-description
    copybooks sit commented out beside them [general/gl070.cbl:L118-L119],
    [general/gl072.cbl:L121-L122].

    The file is `organization line sequential`, accessed sequentially, with its
    status in `fs-reply` [general/gl071.cbl:L92-L95]. It is a transient work
    file named at [copybooks/wsnames.cob:L15-L16]; it is not a table, and
    nothing about it appears in a table dump.

    Every value in a record of this shape arrives from `WS-Posting-Record`
    [copybooks/wspost.cob] through the moves at [general/gl070.cbl:L495-L527].
    Three of those moves have to be qualified because the names collide -
    `post-code in WS-Posting-Record` [general/gl070.cbl:L497] and `vat-ac of
    WS-Posting-Record` [general/gl070.cbl:L521], [general/gl070.cbl:L525] -
    which is anomaly A-21, and is also why `records/gl_posting.py` is cited
    here and imported nowhere.

    Attributes:
        pre_batch: `03  pre-batch       pic 9(5).` The batch number, filtered
            against `WS-Batch-Nos` before any write [general/gl070.cbl:L492].
            First sort key [general/gl071.cbl:L173].
        pre_post: `03  pre-post        pic 9(5).` The posting number within the
            batch. FOURTH sort key [general/gl071.cbl:L176], although it is the
            second field.
        pre_code: `03  pre-code        pic xx.` The two-character posting code.
        pre_date: `03  pre-date        pic x(8).` EIGHT characters, inherited
            from `Post-Date pic x(8)` [copybooks/wspost.cob:L18] by an x(8) to
            x(8) move [general/gl070.cbl:L498]. Not a truncation of the ten-
            character run date, and the century is not restored.
        pre_ac: `03  pre-ac          pic 9(6).` The nominal account number.
            SECOND sort key [general/gl071.cbl:L174].
        pre_pc: `03  pre-pc          pic 99.` The profit centre. THIRD sort key
            [general/gl071.cbl:L175].
        pre_amount: `03  pre-amount      pic s9(8)v99.` Signed, scale 2, sign
            trailing and included because the declaration carries no usage
            clause and no sign clause. `decimal.Decimal`, never a binary
            fraction (R-2). Negative on every credit leg
            [general/gl070.cbl:L517].
        pre_legend: `03  pre-legend      pic x(32).` The posting narrative.
    """

    pre_batch: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_BATCH}
    )
    pre_post: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_POST}
    )
    pre_code: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _PRE_CODE}
    )
    pre_date: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _PRE_DATE}
    )
    pre_ac: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_AC})
    pre_pc: int = field(default=0, metadata={COBOL_FIELD_METADATA_KEY: _PRE_PC})
    pre_amount: Decimal = field(
        default=Decimal("0.00"),
        metadata={COBOL_FIELD_METADATA_KEY: _PRE_AMOUNT},
    )
    pre_legend: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _PRE_LEGEND}
    )


@dataclass(slots=True)
class PostLedger:
    """`03  post-ledger.` - the eight-character composite `gl072` alone declares.

    Declared at [general/gl072.cbl:L115] with two `05` children:

        115      03  post-ledger.
        116          05  post-ac     pic 9(6).
        117          05  post-pc     pic 99.

    R-4, and half of the anomaly this module reproduces rather than repairs.
    `gl071` declares the SAME two fields FLAT at level `03`
    [general/gl071.cbl:L129-L130] with no enclosing group, and `grep -n
    "post-ledger"` returns nothing against `general/gl071.cbl` or
    `general/gl070.cbl`. `gl070` and `gl071` only ever touch the account number
    and the profit centre one at a time, so a group would be of no use to
    them; `gl072` needs the six and the two characters WHOLE, because it
    consumes the composite as a unit at three sites:

        309      if       post-ledger not = save-ledger
        317      move     post-ledger  to  save-ledger.
        405      move     post-ledger  to  WS-Ledger-Key.

    [general/gl072.cbl:L309], [general/gl072.cbl:L317],
    [general/gl072.cbl:L405]. The third of those loads the nominal-ledger key
    modelled by `records/gl_ledger.py`, immediately before the sequential read
    at [general/gl072.cbl:L407-L408] that anomaly A-14 turns into a
    correctness requirement.

    This class is defined ahead of `PostTransRecord` only because it is the type
    of one of that record's attributes and Python needs the name first. In the
    frozen source the group is declared INSIDE the record, between `post-date`
    [general/gl072.cbl:L114] and `post-amount` [general/gl072.cbl:L118], and the
    attribute below sits at that same position.

    Attributes:
        post_ac: `05  post-ac     pic 9(6).` [general/gl072.cbl:L116] - the
            level-05 declaration, distinct from the level-03 one at
            [general/gl071.cbl:L129].
        post_pc: `05  post-pc     pic 99.` [general/gl072.cbl:L117] - likewise
            distinct from [general/gl071.cbl:L130].
    """

    post_ac: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_LEDGER_AC}
    )
    post_pc: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_LEDGER_PC}
    )


@dataclass(slots=True)
class PostTransRecord:
    """`01  post-trans-record.` - the sorted stream, declared two ways.

    R-4, and the reproduction site of the anomaly in full. ONE `01` name, ONE
    physical work file, TWO incompatible declarations:

        01  post-trans-record.   FLAT     [general/gl071.cbl:L124-L132]
        01  post-trans-record.   GROUPED  [general/gl072.cbl:L110-L119]

    `gl071` receives the sorted stream into the flat form
    [general/gl071.cbl:L178] under `fd  post-trans.`
    [general/gl071.cbl:L122], where `post-ac` and `post-pc` are level-03
    fields side by side. `gl072` reads the very same file under its own `fd
    post-trans.` [general/gl072.cbl:L108], where those two fields are the `05`
    children of a `03  post-ledger.` group [general/gl072.cbl:L115]. Both
    occupy the same eight characters, six then two. Both are carried here, and
    neither is described as the settled reading of the file.

    The eight flat attributes below are `gl071`'s declaration in its own order.
    `post_ledger` is `gl072`'s view of the fifth and sixth of them, and it sits
    at the position the group occupies in `gl072`'s own declaration - after
    `post_date`, before `post_ac`.

    THE TWO VIEWS ARE NOT KEPT IN STEP. Assigning `post_ledger.post_ac` does
    not move `post_ac`, and assigning `post_ac` does not move
    `post_ledger.post_ac`. That is deliberate and must not be "tidied": the
    COBOL keeps no such linkage either - the two declarations live in two
    separate programs, each compiled against its own view of the record area -
    and rule R-3 forbids adding logic the frozen source does not contain. There
    is therefore no property, no attribute interception and no
    post-construction hook anywhere in this class.

    The file is `organization line sequential`, accessed sequentially, status in
    `fs-reply` [general/gl071.cbl:L97-L100], and is the transient work file
    named at [copybooks/wsnames.cob:L15-L16]. Note that `gl071` declares
    `fs-reply` as `77  fs-reply            pic xx.`
    [general/gl071.cbl:L150] - alphanumeric - where
    [copybooks/wsfnctn.cob:L25] declares the same logical field as `Fs-Reply
    pic 99`, numeric. Two pictures for one status field; the field belongs to
    `records/file_access.py` and is not declared here.

    Attributes:
        post_batch: `03  post-batch      pic 9(5).` FIRST sort key
            [general/gl071.cbl:L173]. `gl072` skips any record whose value here
            is not numeric [general/gl072.cbl:L291], silently - anomaly A-13,
            reproduced in `programs/gl072_transaction_update.py` and not here.
        post_post: `03  post-post       pic 9(5).` FOURTH sort key
            [general/gl071.cbl:L176], although the second field.
        post_code: `03  post-code       pic xx.`
        post_date: `03  post-date       pic x(8).` EIGHT characters, inherited
            from [copybooks/wspost.cob:L18]; not a truncation.
        post_ledger: `03  post-ledger.` [general/gl072.cbl:L115] - `gl072`'s
            GROUPED view of the account number and profit centre that follow.
            Present because `gl072` moves the composite whole into
            `WS-Ledger-Key` [general/gl072.cbl:L405]; absent from
            `gl071`'s declaration entirely.
        post_ac: `03  post-ac         pic 9(6).` [general/gl071.cbl:L129] -
            `gl071`'s FLAT level-03 declaration. SECOND sort key
            [general/gl071.cbl:L174].
        post_pc: `03  post-pc         pic 99.` [general/gl071.cbl:L130] -
            `gl071`'s FLAT level-03 declaration. THIRD sort key
            [general/gl071.cbl:L175].
        post_amount: `03  post-amount     pic s9(8)v99.` Signed, scale 2, sign
            trailing and included, no usage clause. `decimal.Decimal` (R-2):
            [general/gl072.cbl:L331] adds it straight into `ledger-balance`,
            and [general/gl072.cbl:L321-L328] routes it to the debit or the
            credit column of the printed line by its sign.
        post_legend: `03  post-legend     pic x(32).`
    """

    post_batch: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_BATCH}
    )
    post_post: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _POST_POST}
    )
    post_code: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _POST_CODE}
    )
    post_date: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _POST_DATE}
    )
    # R-4. `gl072`'s grouped view [general/gl072.cbl:L115-L117] of the two
    # attributes that follow, which are `gl071`'s flat view
    # [general/gl071.cbl:L129-L130] of the same eight characters. Carried at the
    # position `gl072` declares it. Not kept in step with them, by design.
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
        default="", metadata={COBOL_FIELD_METADATA_KEY: _POST_LEGEND}
    )


@dataclass(slots=True)
class SortTransRecord:
    """`01  sort-trans-record.` - the SORT work description's record.

    Declared at [general/gl071.cbl:L136-L144] under `sd  sort-trans.`
    [general/gl071.cbl:L134].

    R-4. That `sd` is a SORT-FILE description and not an `fd`, a distinction the
    frozen source carries through to its FILE-CONTROL entry: `select
    sort-trans  assign file-21.` [general/gl071.cbl:L102] names a NUMBERED
    file handle, while `pre-trans` and `post-trans` are assigned the two
    work-file names and each carries `access sequential`, `status fs-reply`
    and `organization line sequential` [general/gl071.cbl:L92-L100]. The `sd`
    has none of those three clauses.

    R-4. Four of the eight fields are the sort keys, and the key order is NOT
    the declaration order [general/gl071.cbl:L172-L178]:

        172      sort     sort-trans
        173               on ascending key sort-batch
        174                                sort-ac
        175                                sort-pc
        176                                sort-post
        177               using  pre-trans
        178               giving post-trans.

    batch, ac, pc, post - so `sort-post` is the fourth key although it is the
    second field, and `sort-code`, `sort-date`, `sort-amount` and `sort-legend`
    are carried through untouched. That statement is the whole of `gl071`'s
    procedure division apart from a screen message and a `goback`
    [general/gl071.cbl:L167-L181], and the program contains no arithmetic at
    all. The key list is not published from this module: the stable sort with
    COBOL key semantics belongs to `acas_posting/cobol/sortverb.py` and the
    phase to `acas_posting/programs/gl071_batch_sort.py`. What this record owns
    is the eight widths the keys are cut from.

    Attributes:
        sort_batch: `03  sort-batch      pic 9(5).` FIRST key
            [general/gl071.cbl:L173].
        sort_post: `03  sort-post       pic 9(5).` FOURTH key
            [general/gl071.cbl:L176], second field.
        sort_code: `03  sort-code       pic xx.` Not a key.
        sort_date: `03  sort-date       pic x(8).` Not a key. EIGHT characters,
            inherited from [copybooks/wspost.cob:L18]; not a truncation.
        sort_ac: `03  sort-ac         pic 9(6).` SECOND key
            [general/gl071.cbl:L174].
        sort_pc: `03  sort-pc         pic 99.` THIRD key
            [general/gl071.cbl:L175].
        sort_amount: `03  sort-amount     pic s9(8)v99.` Not a key. Signed,
            scale 2, sign trailing and included, no usage clause;
            `decimal.Decimal` (R-2).
        sort_legend: `03  sort-legend     pic x(32).` Not a key.
    """

    sort_batch: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _SORT_BATCH}
    )
    sort_post: int = field(
        default=0, metadata={COBOL_FIELD_METADATA_KEY: _SORT_POST}
    )
    sort_code: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _SORT_CODE}
    )
    sort_date: str = field(
        default="", metadata={COBOL_FIELD_METADATA_KEY: _SORT_DATE}
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
        default="", metadata={COBOL_FIELD_METADATA_KEY: _SORT_LEGEND}
    )
