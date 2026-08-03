"""`irs030` - the IRS Nominal Ledger Posting  [irs/irs030.cbl].

BOUNDARY - THIS MODULE MIGRATES 187 OF THIS PROGRAM'S 1733 LINES.
`irs/irs030.cbl` is an interactive posting-entry program.  Only three regions of
it are in scope: ``Net section.`` [irs/irs030.cbl:L1544-L1554], ``Gross
section.`` [irs/irs030.cbl:L1556-L1567] and ``Ledger-Postings-Add section.``
[irs/irs030.cbl:L1569-L1730].  Every other line of the program is OUT OF SCOPE
and NOT reproduced here - see OMISSIONS in the traceability footer for the six
named out-of-scope sections and the eight further constructs excluded by name.

WHAT THIS SECTION DOES
======================
`Ledger-Postings-Add` walks the Sales/Purchase-to-IRS transfer file, posts each
transfer record's debit and credit legs into the IRS nominal ledger, copies the
transfer record into the internal IRS posting table, and accumulates VAT into
one of two pre-loaded VAT control-account snapshots.  The program's own remarks
state the intent [irs/irs030.cbl:L1572-L1576]::

    1572 *> This routine processes the posting file produced from SL & PL updating the IRS NL
    1573 *>   accounts and copies the posting record to the internal IRS one.
    1574 *>
    1575 *>  Open input file, get vat a/cs for both Sales and Purchases and hold records
    1576 *>   some code bits from irs080

This module is where the IRS fan-out that `sl060`, `sl100`, `pl060` and `pl100`
perform is finally consumed.  It is the IRS side of that fan-out, so it contains
no fan-out test of its own and no period-total write of its own.

THE LINKAGE IS A THIRD, MATERIALLY DIFFERENT SHAPE
==================================================
Measured verbatim [irs/irs030.cbl:L552-L554]::

     552  procedure division using IRS-System-Params
     553                           WS-System-Record
     554                           File-Defs.

THREE parameters.  There is no calling-data block and there is no run date.
The program's COPY census confirms it: `irs030` copies `irswssystem.cob`
[irs/irs030.cbl:L416] for `IRS-System-Params` and `wssystem.cob`
[irs/irs030.cbl:L419] for `WS-System-Record`, and it does NOT copy
`wscall.cob` at all.  Consequently this module has no term code, no caller
identity, no process function and no unattended-mode branch.

It also has NO DATE PARAMETER OF ANY KIND.  The posting date arrives in the
data, as `WS-IRS-Post-Date` [irs/irs030.cbl:L1662], written into the transfer
record by the Sales and Purchase posting programs from their own run date.  That
is the strongest possible confirmation of the migration's controlled-clock
finding: this module reads no clock and needs no clock injected, so `clock.py`
is deliberately NOT imported and no `to_day` argument is accepted.

The caller is `cli/irs_post.py`, transcribing [irs/irs.cbl:L668-L671]::

     668       call   "irs030" using IRS-System-Params
     669                             WS-System-Record   *> ACAS system rec.
     670                             file-defs
     671       end-call

THE FACADE CONVENTION IS THE HANDLER-NAMED ONE, AND IT HAS A HOLE IN IT
=======================================================================
`irs030` is the ONLY one of the twelve migrated programs that copies
`Proc-ZZ100-ACAS-IRS-Calls.cob` [irs/irs030.cbl:L1732]; the other eleven copy
`Proc-ACAS-FH-Calls.cob`.  The IRS convention names its facade paragraphs after
the *handler* rather than the entity, and it adds a per-handler error-check
paragraph the General/Sales/Purchase convention does not have.  The difference
is behavioural, not cosmetic: a check that fires displays a message, closes the
file and reaches `Open-Error-Continued`, which ends in ``goback.``
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364] - a hard return out of
`irs030`.  Every facade call in this module therefore uses a HANDLER-named
alias, never an entity-named one.

THE HOLE: the copybook declares five error-check paragraphs for six dispatched
handlers - `acas000-Check-4-Errors`, `acas008-Check-4-Errors`,
`irsub1-Check-4-Errors`, `irsub3-Check-4-Errors` and `irsub5-Check-4-Errors`.
There is NO `acasirsub4-Check-4-Errors`.  That absence is precisely why
`irs030` must test the reply inline after the `acasirsub4-Write`
[irs/irs030.cbl:L1674], and it is the mechanism behind the write-failure jump.

The measured verb census for the in-scope region, with each verb's check state
read from the copybook:

===========================  =====================  ==============  =============
verb                         sites                  facade check?   inline test?
===========================  =====================  ==============  =============
`acas008-Open-Input`         1578                   yes (L140)      yes (L1579)
`acas008-Read-Next`          1620                   no              yes (L1621)
`acas008-Open-Output`        1723                   yes (L146)      no
`acas008-Close`              1712, 1724             no              no
`acasirsub3` (bare form)     1586                   no              no
`acasirsub1-Read-Indexed`    1596, 1606, 1629,      no              yes (L1597,
                             1647                                   L1607, L1630,
                                                                    L1648)
`acasirsub1-Rewrite`         1641, 1657, 1705,      no              no
                             1708
`acasirsub4-Open`            1617                   no              no
`acasirsub4-Write`           1673                   no              yes (L1674)
`acasirsub4-Close`           1711                   no              no
===========================  =====================  ==============  =============

THE BARE HANDLER FORM.  [irs/irs030.cbl:L1585-L1586] sets the function code
explicitly and then performs the bare handler name, with no verb suffix::

    1585      move     3  to  file-function.
    1586      perform  acasirsub3.    *> call-irsub3.

That shape is reproduced faithfully - the function-code store is routed through
the MOVE layer and bound to the operation vocabulary's member, and the bare
handler alias is called.  It is deliberately NOT "improved" into a read-next
verb call.

`acas008-Open-Output` MEANS DELETE EVERY ROW.  The transfer-file handler
implements open-output as a delete-all, which the maintainer's own comment at
[irs/irs030.cbl:L1723] records as ``*> performs a acas008-Delete-All``.  That is
the mechanism of the end-of-job clear.

WHY EVERY STATUS TEST READS ITS OWN FIELD
=========================================
The section uses a MIXED status protocol and the two fields are not
interchangeable.  `FS-Reply` is tested at [irs/irs030.cbl:L1579] and
[irs/irs030.cbl:L1621]; `we-error` is tested at [irs/irs030.cbl:L1597],
[irs/irs030.cbl:L1607], [irs/irs030.cbl:L1630], [irs/irs030.cbl:L1648] and
[irs/irs030.cbl:L1674].  Each site reproduces its own field.  The two
record-not-found tests compare for EQUALITY WITH 2, not for "not zero", so any
other error value falls straight through into the accumulate - that exact
predicate is preserved.

Every facade verb in the IRS convention returns nothing and communicates only by
mutating the `File-Access` block, so this module reads `fs_reply` and `we_error`
from that block after each call, exactly as the COBOL does.

THREE REJECTION DISPOSITIONS, THREE DIFFERENT DATABASE EFFECTS
==============================================================
A rejected transaction must reach the same disposition AND leave the same effect
on the database.  This one section contains three distinct dispositions and they
are implemented separately; a single generic rejection path would not reproduce
them:

1. CLEAN SKIP - [irs/irs030.cbl:L1634] returns to `Input-Loop`.  The debit
   account was not found, nothing has been written, the next transfer record is
   read.  Silent: no counter, no trace beyond the display.
2. COMMIT-AND-STOP - [irs/irs030.cbl:L1678] transfers to `EOJ`, which still
   performs both VAT-snapshot rewrites and all three closes.  The partial state
   is COMMITTED, not rolled back.
3. ABORT-WITH-NOTHING - [irs/irs030.cbl:L1581], [irs/irs030.cbl:L1601] and
   [irs/irs030.cbl:L1611] transfer to `main99-exit`, which is ``exit section.``
   [irs/irs030.cbl:L1730].  `EOJ` is bypassed entirely, so no snapshot rewrite
   and no close happen at all.

There is a fourth, half-posted disposition that is not a clean class of its own
because it is a defect - see A-4 below.

THE ANOMALIES THIS MODULE OWNS (rule R-4)
=========================================
Compiled behaviour is the specification, defects included.  A defect reproduced
is correct; a defect fixed is a failure.  Four defects live in the in-scope
region and each is annotated at its reproduction site with its COBOL locator.

A-4  THE HALF-POSTED DOUBLE ENTRY.  The debit leg is rewritten at
     [irs/irs030.cbl:L1641] BEFORE the credit account is even looked up at
     [irs/irs030.cbl:L1647].  A missing credit account returns to `Input-Loop`
     at [irs/irs030.cbl:L1652], leaving an unbalanced debit committed to the
     nominal ledger, no credit, and no internal posting row at all - because the
     posting write is at [irs/irs030.cbl:L1673], after the abandoned point.
     Compounding it: `acasirsub1-Rewrite` carries neither a facade check nor an
     inline test, so a failed debit rewrite is silently ignored too.

A-5  THE LOST UPDATE ON THE TWO VAT CONTROL ACCOUNTS.  Accounts
     ``def-acs (31)`` and ``def-acs (32)`` are read into working-storage
     snapshots BEFORE the loop [irs/irs030.cbl:L1602], [irs/irs030.cbl:L1612]
     and rewritten FROM those snapshots at end of job
     [irs/irs030.cbl:L1705], [irs/irs030.cbl:L1708].  If any posting's debit or
     credit account happens to BE account 31 or 32, the in-loop rewrite at
     [irs/irs030.cbl:L1641] or [irs/irs030.cbl:L1657] is silently discarded.
     The four-way VAT ladder accumulates into the SNAPSHOTS, never the live
     rows, which is what makes the lost update inevitable rather than
     incidental.

A-19 SUPERSEDED COMMENTED-OUT VARIANTS OF BOTH VAT COMPUTES.  Dead variants at
     [irs/irs030.cbl:L1550] and [irs/irs030.cbl:L1561] sit adjacent to the live
     statements and reference a differently named rate field, `vat`, where the
     live ones reference `WS-Vat-Current`.  Both dead lines are carried into
     this module verbatim as comments beside their live translations, together
     with the maintainer's own uncertainty note at
     [irs/irs030.cbl:L1547-L1548].  Carrying them IS the reproduction.

THE WRITE-FAILURE JUMP.  [irs/irs030.cbl:L1674-L1678] jumps to `EOJ`, not to
     `Input-Loop`, and `EOJ` still performs both snapshot rewrites and all three
     closes - so the partial state is committed.  This inline test exists only
     because the facade has no `acasirsub4-Check-4-Errors`.

RULES THIS MODULE IS HELD TO
============================
There is no user rules document for this project - `review_rules` reports that
none was provided.  The six binding rules are the migration plan's own R-1..R-6,
and all six govern this file.

R-1  No COBOL at runtime.  Nothing here launches an external program, loads a
     foreign library or reaches the oracle comparison tree.  Worth stating
     positively: THE IN-SCOPE REGION OF `irs030` CONTAINS NO ``call "..."``
     STATEMENT AT ALL - no operating-system spool-out, no date-module call, no
     library routine, and no print file whatsoever - so unlike some sibling
     modules this one needs no escape hatch of any kind.
R-2  Zero binary floating-point arithmetic.  Every monetary value is an exact
     decimal, every integer count an int, and this module holds no numeric
     primitive of its own: picture semantics, storage classes, truncation,
     rounding direction and MOVE rules all live one layer down and are reached
     only through the arithmetic and MOVE verbs.  THIS MODULE OWNS TWO OF THE
     MIGRATION'S FIVE ROUNDED STORE SITES - [irs/irs030.cbl:L1551] and
     [irs/irs030.cbl:L1562-L1563].  Every other store in the region truncates,
     including the subtraction at [irs/irs030.cbl:L1564].
R-3  No new validation, no new field, no schema change, no concurrent
     execution.  Not one predicate has been added, widened, narrowed or
     reordered; execution is strictly sequential with no task or worker library
     of any kind.
R-4  Legacy anomalies reproduced, never fixed - the four above, each annotated
     in place.
R-5  Full traceability.  A named function exists for every one of the section's
     NINE labels, every one of the region's TEN ``GO TO`` sites carries a class
     annotation, every field descriptor carries a dictionary key or a source
     locator, and the footer maps program to module, paragraph to function and
     statement to call site.
R-6  Compiled behaviour is the tie-breaker.  No ambient clock of any kind is
     read - see the AMBIGUITIES section for the eight questions this module
     defers to the compiled program.

WHAT THIS MODULE MAY IMPORT, AND WHY THE LIST IS THIS SHORT
===========================================================
The layering rule permits the record layouts, the facade, the status vocabulary
and the language-semantics verbs.  Of those, this module imports only what it
actually uses, and the omissions are as informative as the inclusions:

* `cobol/condition_names.py` is NOT imported.  There is not one 88-level
  condition-name test in the in-scope region: every test is relational -
  ``FS-Reply not = zero``, ``FS-Reply = 10``, ``we-error not = zero``,
  ``we-error = 2``, ``= "CR"``, ``= "DR"``, ``= zero``, ``= 31``, ``= 32``.
  Even [irs/irs030.cbl:L1585] is a MOVE of a literal function code, not a SET of
  a condition name.
* `cobol/picture.py` is NOT imported.  No picture string is parsed here; every
  descriptor is looked up from the generated data dictionary.
* `cobol/usage.py` is outside the permitted list, so no storage-class byte image
  is constructed here - see STRUCTURAL NOTES for how the two group moves are
  realised instead.
* `clock.py` is NOT imported - this program reads no clock and takes no date.
* `dates.py` and `records/maps03.py` are NOT imported - the in-scope region
  performs no date conversion.  `Date-Validate` is out of scope and `irs030`
  does not copy the date-conversion interface copybook.
* `workfiles.py` is NOT imported - `irs030` has no work file.
* No sibling program module is imported.  The Sales and Purchase posting
  programs produce the transfer records this section consumes, but the coupling
  is through the transfer table, exactly as it is in COBOL.

AMBIGUITIES, ARBITRATED AGAINST COMPILED BEHAVIOUR (rule R-6)
=============================================================
Q-18 The compound VAT expression at [irs/irs030.cbl:L1562-L1563] is a division
     nested inside a division, and the migration plan names it as the one place
     where an intermediate-precision difference could change a stored penny.
     It is transcribed exactly as parenthesised and evaluated at the arithmetic
     layer's extended intermediate precision, with a single store at the end.
     It is deliberately NOT simplified algebraically.  Expected values come from
     the compiled program, never from reasoning about the algebra.
Q-19 The stored nominal-ledger state after A-4's half-post - specifically
     whether the debit rewritten at [irs/irs030.cbl:L1641] is durable once the
     run later reaches `EOJ` by a different path.
Q-20 The stored state after A-5's lost update when a posting's debit or credit
     account IS account 31 or 32, so that the in-loop rewrite and the end-of-job
     snapshot rewrite target the same row.
Q-21 The behaviour when `WS-IRS-Vat-AC-Def` is non-zero but neither 31 nor 32.
     The ladder at [irs/irs030.cbl:L1685-L1699] has no final `else`, so the VAT
     accumulates nowhere and nothing is reported.  Reproduced as written.
Q-22 Whether `next-post` advances when the posting write at
     [irs/irs030.cbl:L1673] fails.  The increment at [irs/irs030.cbl:L1671]
     precedes the write, so on this reading it does; the compiled program
     arbitrates.
Q-23 What `we-error` value the handler-named facade surfaces for a missing
     account other than 2.  The IRS handler's own contract documents 2 as an
     open-ended "2+" range rather than a single code, and the two tests here
     compare for equality with 2 exactly.
Q-24 The exact argument list of each facade verb.  `dal/facade.py` is a
     same-batch creation and is not yet on disk, so the argument list is bound
     to the copybook's own CALL list and to the already-written handler dispatch
     signatures, which agree - see STRUCTURAL NOTES.
Q-25 Whether the unsigned packed receivers `nl-dr` and `nl-cr` discard the sign
     of a negative VAT or posting amount on accumulation.  Their picture is
     unsigned while the transfer amounts are signed, so on the descriptors as
     generated they do; the compiled program arbitrates the stored value.
"""

from __future__ import annotations

import dataclasses
import logging
from decimal import Decimal
from typing import Final, Mapping

from acas_posting.cobol import arithmetic, move
from acas_posting.cobol.field import FieldDescriptor, descriptors_for_copybook_record

# copy "Proc-ZZ100-ACAS-IRS-Calls.cob".   [irs/irs030.cbl:L1732]
#   The handler-named facade convention.  The MODULE is imported rather than
#   individual verbs, because the copybook is a textual inclusion of a whole
#   paragraph set and the Python counterpart of that inclusion is the module.
from acas_posting.dal import facade

# copy "wsfnctn.cob".   [irs/irs030.cbl:L285]
#   The single COBOL copybook mixes a data layout with an operation vocabulary,
#   and the Python layering separates them: the record classes come from the
#   records layer, the vocabulary from the status layer.
from acas_posting.dal.status import FileFunction, FsReply, WeError

# copy "irswsdflt.cob" replacing Default-Record by WS-IRS-Default-Record.
#   [irs/irs030.cbl:L287] - the account-code table indexed at 31 and 32.
from acas_posting.records.irs_dflt import WsIrsDefaultRecord

# copy "irswsnl.cob" replacing NL-Record by WS-IRSNL-Record.
#   [irs/irs030.cbl:L286] - the IRS nominal-ledger account.
from acas_posting.records.irs_nominal import WsIrsnlRecord

# copy "irswspost.cob".   [irs/irs030.cbl:L288]
#   The INTERNAL IRS posting record.  Its amount fields are signed DISPLAY with
#   the sign carried leading, spelled `sign is leading` in this copybook.
from acas_posting.records.irs_posting import PostingRecord

# copy "irswssystem.cob" replacing system-record by IRS-System-Params.
#   [irs/irs030.cbl:L416] - the FIRST linkage parameter.  The replacement
#   renames only the group, so the inner `next-post` keeps its own name here;
#   `wssystem.cob`'s homonym is renamed away, which is what makes
#   [irs/irs030.cbl:L1670-L1671] a mutation of THIS record.
from acas_posting.records.irs_system import IrsSystemParams

# copy "wspost-irs.cob".   [irs/irs030.cbl:L289]
#   The SL/PL-to-IRS transfer record.  Its amount fields are signed DISPLAY
#   with the sign carried leading, spelled `SIGN LEADING` in this copybook.
from acas_posting.records.spl_irs_posting import WsIrsPostingRecord

# copy "wssystem.cob" replacing System-Record by WS-System-Record and more.
#   [irs/irs030.cbl:L419] - the SECOND linkage parameter.  Passed straight
#   through to every handler dispatch, exactly as the copybook's CALL list does.
from acas_posting.records.system_record import SystemRecord

# copy "Test-Data-Flags.cob".   [irs/irs030.cbl:L298]
#   Declares `ACAS-DAL-Common-data`, the fifth operand of every handler CALL
#   in [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob].
from acas_posting.records.test_data_flags import AcasDalCommonData

# copy "wsnames.cob".   [irs/irs030.cbl:L450]
from acas_posting.records.file_defs import FileDefs

# copy "wsfnctn.cob".   [irs/irs030.cbl:L285] - the File-Access block itself.
from acas_posting.records.file_access import ALL_FIELDS as _FILE_ACCESS_FIELDS
from acas_posting.records.file_access import FileAccess

#: The program's only public entry point.  Each program module exposes a single
#: `run(...)` mirroring its COBOL `PROCEDURE DIVISION USING` list, with the
#: paragraph functions private to the module: callers cannot reach into a
#: program's internals, exactly as a COBOL `CALL` cannot.
__all__: Final[tuple[str, ...]] = ("run",)

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# --- field descriptors ------------------------------------------------------
#
# Rule R-5 requires that every field descriptor be traceable.  The three record
# layouts this section touches are looked up from the generated data dictionary,
# so each descriptor arrives carrying BOTH a dictionary key and a source
# locator; nothing is transcribed by eye.  The dictionary is keyed on the
# PRE-REPLACING record names, so `NL-Record` is the lookup even though `irs030`
# copies it as `WS-IRSNL-Record` [irs/irs030.cbl:L286].


def _index(record_name: str) -> dict[str, FieldDescriptor]:
    """Index one dictionary record's flattened descriptors by field name.

    An `OCCURS` field appears once per occurrence with the same name and the
    same picture, so the first occurrence is the representative descriptor for
    every element of the table.
    """
    indexed: dict[str, FieldDescriptor] = {}
    for descriptor in descriptors_for_copybook_record(record_name):
        indexed.setdefault(descriptor.name, descriptor)
    return indexed


_NL: Final[dict[str, FieldDescriptor]] = _index("NL-Record")
_POST: Final[dict[str, FieldDescriptor]] = _index("Posting-Record")
_XFER: Final[dict[str, FieldDescriptor]] = _index("WS-IRS-Posting-Record")

# `WS-IRSNL-Record` [irs/irs030.cbl:L286] - the live nominal-ledger account.
_NL_OWNING: Final[FieldDescriptor] = _NL["NL-Owning"]
_NL_SUB_NOMINAL: Final[FieldDescriptor] = _NL["NL-Sub-Nominal"]
_NL_TYPE: Final[FieldDescriptor] = _NL["NL-Type"]
_NL_NAME: Final[FieldDescriptor] = _NL["NL-Name"]
_NL_DR: Final[FieldDescriptor] = _NL["NL-DR"]
_NL_CR: Final[FieldDescriptor] = _NL["NL-CR"]
_NL_DR_LAST: Final[FieldDescriptor] = _NL["NL-DR-Last"]
_NL_CR_LAST: Final[FieldDescriptor] = _NL["NL-CR-Last"]
_NL_AC: Final[FieldDescriptor] = _NL["NL-AC"]
_NL_POINTER: Final[FieldDescriptor] = _NL["NL-Pointer"]

# `Posting-Record` [irs/irs030.cbl:L288] - the internal IRS posting row.
_POST_KEY: Final[FieldDescriptor] = _POST["Post-Key"]
_POST_CODE: Final[FieldDescriptor] = _POST["Post-Code"]
_POST_DATE: Final[FieldDescriptor] = _POST["Post-Date"]
_POST_DR: Final[FieldDescriptor] = _POST["Post-DR"]
_POST_CR: Final[FieldDescriptor] = _POST["Post-CR"]
_POST_AMOUNT: Final[FieldDescriptor] = _POST["Post-Amount"]
_POST_LEGEND: Final[FieldDescriptor] = _POST["Post-Legend"]
_VAT_AC_DEF: Final[FieldDescriptor] = _POST["Vat-AC-Def"]
_POST_VAT_SIDE: Final[FieldDescriptor] = _POST["Post-Vat-Side"]
_VAT_AMOUNT: Final[FieldDescriptor] = _POST["Vat-Amount"]

# `WS-IRS-Posting-Record` [irs/irs030.cbl:L289] - the SL/PL transfer record.
_XFER_AMOUNT: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Amount"]
_XFER_VAT_AMOUNT: Final[FieldDescriptor] = _XFER["WS-IRS-Vat-Amount"]
_XFER_POST_DR: Final[FieldDescriptor] = _XFER["WS-IRS-Post-DR"]
_XFER_POST_CR: Final[FieldDescriptor] = _XFER["WS-IRS-Post-CR"]
_XFER_POST_CODE: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Code"]
_XFER_POST_DATE: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Date"]
_XFER_POST_LEGEND: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Legend"]
_XFER_VAT_AC_DEF: Final[FieldDescriptor] = _XFER["WS-IRS-Vat-AC-Def"]
_XFER_POST_VAT_SIDE: Final[FieldDescriptor] = _XFER["WS-IRS-Post-Vat-Side"]

# `File-Access` [copybooks/wsfnctn.cob] - only the function-code receiver is
# stored into by this module; the status fields are read, never written here.
_FILE_FUNCTION: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in _FILE_ACCESS_FIELDS
    if descriptor.name == "File-Function"
)

# `next-post` [copybooks/irswssystem.cob:L25] - the IRS posting key allocator,
# a field of the FIRST linkage parameter.  See the import banner above for why
# this name resolves to `IRS-System-Params` and not to the ACAS system record.
_NEXT_POST: Final[FieldDescriptor] = next(
    descriptor
    for descriptor in IrsSystemParams.FIELDS
    if descriptor.name == "next-post"
)

# --- module-private descriptors ---------------------------------------------
#
# Four receivers in the in-scope region are declared in `irs030`'s OWN
# WORKING-STORAGE rather than in any copybook, so the generated dictionary -
# which is built from the copybooks, the bridge and the schema - has no entry
# for them.  Rule R-5 still requires provenance, so each is derived from the
# dictionary descriptor of the field it mirrors byte for byte and re-labelled
# with its own source locator inside the frozen program.  Deriving rather than
# hand-constructing also keeps the storage class out of this module, which is
# what rule R-2 and the layering rule between them require.
_POST_RECORD_CNT: Final[FieldDescriptor] = dataclasses.replace(
    _NL_POINTER,  # pic 9(5) DISPLAY - the same picture as Post-Record-Cnt
    name="Post-Record-Cnt",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L272",
)
_NL31_DR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_DR,
    name="nl31-dr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L355",
)
_NL31_CR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_CR,
    name="nl31-cr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L356",
)
_NL32_DR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_DR,
    name="nl32-dr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L370",
)
_NL32_CR: Final[FieldDescriptor] = dataclasses.replace(
    _NL_CR,
    name="nl32-cr",
    dictionary_key=None,
    source_locator="irs/irs030.cbl:L371",
)

# --- literals from the frozen program --------------------------------------
#
# `we-error = 2` is tested for EQUALITY at [irs/irs030.cbl:L1630] and
# [irs/irs030.cbl:L1648].  The status layer's error vocabulary deliberately
# omits the IRS handler's `1+` / `2+` / `3+` codes, because they are open-ended
# ranges local to one handler's prose rather than codes of the shared
# vocabulary, and rule R-3 forbids extending that vocabulary.  The layering rule
# equally forbids importing the handler module that publishes the pair.  The
# value is therefore bound here, once, to its authoritative locator - never
# written as a bare literal at a test site.
#
#   common/acasirsub1.cbl:L87   "2+ = Indexed IRS record not found"
_IRS_WE_ERROR_RECORD_NOT_FOUND: Final[int] = 2

# The section's message identifiers, declared in `irs030`'s own WORKING-STORAGE
# and retained ONLY as log text.  Rule R-3 forbids reformatting them and the
# presentation-removal rule forbids letting them affect control flow, so they
# are carried verbatim and emitted through the logger.
_IR031: Final[str] = "IR031 No Ledger Posting file found. Process Aborted"
_IR032: Final[str] = "IR032 Invalid key 1 = "
_IR033: Final[str] = "IR033 Invalid key 2 = "
_IR03A: Final[str] = "IR03A IRSUB1-31 returns "
_IR03B: Final[str] = "IR03B IRSUB1-32 returns "
_IR914: Final[str] = "IR914 Error on irspostingMT processing, FS-Reply = "

# The two VAT control accounts, selected by the SL/PL side that produced the
# transfer record.  THE CROSS-PROGRAM CONTRACT: the sales invoice poster writes
# 32 into `WS-IRS-Vat-AC-Def` [sales/sl060.cbl:L1139] while the purchase order
# poster [purchase/pl060.cbl:L993] and the purchase payment poster
# [purchase/pl100.cbl:L640] write 31, and this section routes the VAT
# accordingly.  Those three locators are documentation of the contract this
# module consumes; nothing from those programs is reproduced here.
_VAT_AC_PURCHASE: Final[int] = 31
_VAT_AC_SALES: Final[int] = 32

# `def-acs (31)` and `def-acs (32)` [irs/irs030.cbl:L1594], [irs/irs030.cbl:L1604]
# index the IRS defaults account-code table, which OCCURS 33 times.  COBOL
# subscripts are 1-based, Python indices 0-based.
_DEF_ACS_SUBSCRIPT_31: Final[int] = _VAT_AC_PURCHASE - 1
_DEF_ACS_SUBSCRIPT_32: Final[int] = _VAT_AC_SALES - 1

# The debit and credit legs both test the transfer record's VAT side, and each
# adds the VAT to THE OPPOSITE LEG's accumulator - see the reproduction sites.
_SIDE_CR: Final[str] = "CR"
_SIDE_DR: Final[str] = "DR"


# --- the two VAT control-account snapshots ----------------------------------


@dataclasses.dataclass(slots=True)
class _NlSnapshot:
    """`nl31-record` / `nl32-record` - hand-declared in `irs030`'s WORKING-STORAGE.

    Neither snapshot is a `COPY`.  Both are written out by hand, mirroring
    `NL-Record` field for field [irs/irs030.cbl:L348-L359] and
    [irs/irs030.cbl:L363-L374]::

         348 01  nl31-record.
         349 03  nl31-key.
         350 05  nl31-owning   pic 9(5).
         351 05  nl31-sub-nominal pic 9(5).
         352 03  nl31-type         pic a.
         353 03  nl31-data.
         354 05  nl31-name     pic x(24).
         355 05  nl31-dr       pic 9(8)v99   comp.
         356 05  nl31-cr       pic 9(8)v99   comp.
         357 05  nl31-dr-last  pic 9(8)v99   comp  occurs  4.
         358 05  nl31-cr-last  pic 9(8)v99   comp  occurs  4.
         359 05  nl31-ac       pic a.

    Two divergences from the copybook are recorded rather than smoothed away,
    because a reader diffing the two declarations will find them:

    FINDING  `nl31-type` and `nl31-ac` are declared `pic a` - ALPHABETIC - where
             the copybook declares `NL-Type` and `NL-AC` as `pic x` -
             ALPHANUMERIC [copybooks/irswsnl.cob:L12], [copybooks/irswsnl.cob:L21].
             Both are one byte wide, so the group move is still an exact byte
             copy; only the class declaration differs.
    FINDING  the snapshots declare no `filler redefines NL-Data` and therefore no
             `NL-Pointer` [copybooks/irswsnl.cob:L22-L23].  A redefinition is an
             alias over bytes rather than storage of its own, and those bytes ARE
             copied by the group move, so `pointer` below carries the aliased
             value.  Carrying it is what makes the copy a byte image under this
             package's representation of the redefinition; it is not a field
             added to the COBOL declaration.
    """

    owning: int = 0
    sub_nominal: int = 0
    tipe: str = " "
    name: str = " " * 24
    dr: Decimal = Decimal("0.00")
    cr: Decimal = Decimal("0.00")
    dr_last: tuple[Decimal, ...] = (Decimal("0.00"),) * 4
    cr_last: tuple[Decimal, ...] = (Decimal("0.00"),) * 4
    ac: str = " "
    pointer: int = 0


def _move_nl_record_to_snapshot(
    source: WsIrsnlRecord,
    receiver: _NlSnapshot,
) -> None:
    """`move WS-IRSNL-Record to nl31-record.` - the group move, one direction.

    A group MOVE between identically laid-out records is a byte-image copy: with
    no receiving width of its own to truncate against, the group receives
    exactly what the sender presents.  The storage-class layer that would build
    those byte images is outside this module's permitted imports, so the byte
    image is realised the only other way that is exactly equivalent for
    identical layouts - field for field through the MOVE verb, each field
    carrying its own descriptor on both sides, so that no truncation, padding or
    conversion can arise.  See STRUCTURAL NOTES.
    """
    receiver.owning = move.move(
        source.nl_key.nl_owning, _NL_OWNING, sending_field=_NL_OWNING
    )
    receiver.sub_nominal = move.move(
        source.nl_key.nl_sub_nominal, _NL_SUB_NOMINAL, sending_field=_NL_SUB_NOMINAL
    )
    receiver.tipe = move.move(source.nl_type, _NL_TYPE, sending_field=_NL_TYPE)
    receiver.name = move.move(
        source.nl_data.nl_name, _NL_NAME, sending_field=_NL_NAME
    )
    receiver.dr = move.move(source.nl_data.nl_dr, _NL_DR, sending_field=_NL_DR)
    receiver.cr = move.move(source.nl_data.nl_cr, _NL_CR, sending_field=_NL_CR)
    receiver.dr_last = tuple(
        move.move(element, _NL_DR_LAST, sending_field=_NL_DR_LAST)
        for element in source.nl_data.nl_dr_last
    )
    receiver.cr_last = tuple(
        move.move(element, _NL_CR_LAST, sending_field=_NL_CR_LAST)
        for element in source.nl_data.nl_cr_last
    )
    receiver.ac = move.move(source.nl_data.nl_ac, _NL_AC, sending_field=_NL_AC)
    receiver.pointer = move.move(
        source.nl_pointer_view.nl_pointer, _NL_POINTER, sending_field=_NL_POINTER
    )


def _move_snapshot_to_nl_record(
    source: _NlSnapshot,
    receiver: WsIrsnlRecord,
) -> None:
    """`move nl31-record to WS-IRSNL-Record.` - the group move, other direction.

    The mirror of `_move_nl_record_to_snapshot`, and the mechanism of anomaly
    A-5: what this restores is the account as it stood BEFORE the loop, plus
    whatever the VAT ladder accumulated into the snapshot - never what the loop
    may have written to the live row.
    """
    receiver.nl_key.nl_owning = move.move(
        source.owning, _NL_OWNING, sending_field=_NL_OWNING
    )
    receiver.nl_key.nl_sub_nominal = move.move(
        source.sub_nominal, _NL_SUB_NOMINAL, sending_field=_NL_SUB_NOMINAL
    )
    receiver.nl_type = move.move(source.tipe, _NL_TYPE, sending_field=_NL_TYPE)
    receiver.nl_data.nl_name = move.move(
        source.name, _NL_NAME, sending_field=_NL_NAME
    )
    receiver.nl_data.nl_dr = move.move(source.dr, _NL_DR, sending_field=_NL_DR)
    receiver.nl_data.nl_cr = move.move(source.cr, _NL_CR, sending_field=_NL_CR)
    receiver.nl_data.nl_dr_last = tuple(
        move.move(element, _NL_DR_LAST, sending_field=_NL_DR_LAST)
        for element in source.dr_last
    )
    receiver.nl_data.nl_cr_last = tuple(
        move.move(element, _NL_CR_LAST, sending_field=_NL_CR_LAST)
        for element in source.cr_last
    )
    receiver.nl_data.nl_ac = move.move(source.ac, _NL_AC, sending_field=_NL_AC)
    receiver.nl_pointer_view.nl_pointer = move.move(
        source.pointer, _NL_POINTER, sending_field=_NL_POINTER
    )


# --- the program's WORKING-STORAGE -----------------------------------------


@dataclasses.dataclass(slots=True)
class _WorkingStorage:
    """`irs030`'s WORKING-STORAGE and LINKAGE, as one explicitly passed holder.

    COBOL working storage is visible to every paragraph of the program.  Rule
    R-5 requires one named function per paragraph, so the storage those
    paragraphs share is passed to them explicitly rather than hidden in module
    state - which also keeps the module free of mutable globals and therefore
    safely re-entrant, without introducing any concurrency.

    Nothing here is invented: each attribute is a `COPY`'d record, a linkage
    parameter, or a named WORKING-STORAGE item of the frozen program.
    """

    # LINKAGE SECTION, in declaration order  [irs/irs030.cbl:L552-L554]
    irs_system_params: IrsSystemParams
    ws_system_record: SystemRecord
    file_defs: FileDefs

    # WORKING-STORAGE
    file_access: FileAccess  # copy "wsfnctn.cob".            [L285]
    dal_common: AcasDalCommonData  # copy "Test-Data-Flags.cob".   [L298]
    ws_irsnl_record: WsIrsnlRecord  # copy "irswsnl.cob" ...        [L286]
    ws_irs_default_record: WsIrsDefaultRecord  # copy "irswsdflt.cob" ...      [L287]
    posting_record: PostingRecord  # copy "irswspost.cob".         [L288]
    ws_irs_posting_record: WsIrsPostingRecord  # copy "wspost-irs.cob".        [L289]
    nl31_record: _NlSnapshot  # 01 nl31-record.               [L348]
    nl32_record: _NlSnapshot  # 01 nl32-record.               [L363]
    post_record_cnt: int  # 03 Post-Record-Cnt pic 9(5).  [L272]

    # The answer to the end-of-job question at [irs/irs030.cbl:L1717], supplied
    # as an input because it gates a database write.  See `run`.
    clear_posting_file: bool

    # NOT A COBOL FIELD.  The caller's keyword-only handler declarations - chiefly
    # the transport-security policy - forwarded to every facade `PERFORM` this
    # section issues.  There is no COBOL counterpart because the frozen bridge has
    # none: its connect passes six values and no transport policy at all
    # [copybooks/mysql-procedures.cpy:L72-L77], transport being compiled into
    # `cobmysqlapi.c`.
    #
    # An empty mapping is the SAFE answer, not the absent one: every handler
    # declares `transport: TransportSecurity | None = None` and
    # `connection._require_permitted_connection` resolves `None` fail-closed,
    # permitting a Unix socket or a loopback address and refusing every other
    # target.  Carried opaquely - nothing here reads a key of it - and
    # `dal/facade.py` projects it onto whatever extras each handler declares.
    dal_options: Mapping[str, object]


#  Net section.   [irs/irs030.cbl:L1544]
# ---------------------------------------------------------------------------


def _net_section(
    posting_record: PostingRecord,
    ws_vat_current: Decimal,
) -> None:
    """`Net section.` - derive VAT from a VAT-EXCLUSIVE amount.

    Verbatim [irs/irs030.cbl:L1544-L1551]::

        1544  Net section.
        1545 *>----------
        1546 *>
        1547 *> Calculate vat from net  - THIS MAY NEED A TEST FOR ONLY NON ZERO VAT RATES
        1548 *>                           before compute but look like comes to zero ?
        1549 *>
        1550  *>     compute  vat-amount rounded =  post-amount *  vat  /  100.
        1551      compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.

    In scope because the posting path consumes the VAT amount this section
    produces.  Its only callers in the frozen program are the interactive
    VAT-entry paragraph, which is out of scope; the computation itself is not.

    The maintainer's own uncertainty note at [irs/irs030.cbl:L1547-L1548] is
    carried above and is NOT acted on: no test for a non-zero VAT rate is added,
    because rule R-3 forbids adding a predicate the compiled program does not
    have.  A zero rate simply produces a zero VAT amount.
    """
    # ANOMALY A-19 [irs/irs030.cbl:L1550] - a superseded, commented-out variant
    # of this compute survives adjacent to the live one, referencing a
    # differently named rate field `vat` where the live statement references
    # `WS-Vat-Current`.  Carried verbatim, exactly as the COBOL carries it:
    #
    #     1550  *>     compute  vat-amount rounded =  post-amount *  vat  /  100.
    #
    # Reproduced deliberately per R-4; DO NOT FIX.

    # 1551  compute  vat-amount rounded =  post-amount *  WS-Vat-Current  /  100.
    #       ROUNDED store 1 of the 2 this module owns - the store rounds
    #       half-up, where every un-ROUNDED store in this module truncates.
    #       The expression is evaluated at the arithmetic layer's extended
    #       intermediate precision and stored once, at the end.
    posting_record.vat_amount = arithmetic.compute(
        lambda: posting_record.post_amount * ws_vat_current / 100,
        _VAT_AMOUNT,
        rounded=True,
    )
    _net_main_exita()


#  Main-Exita.   [irs/irs030.cbl:L1553]
# ---------------------------------------------------------------------------


def _net_main_exita() -> None:
    """`Main-Exita.` - the `Net` section's exit paragraph.

    Verbatim [irs/irs030.cbl:L1553-L1554]::

        1553  Main-Exita.
        1554      exit.

    FINDING  the statement is a plain `EXIT`, not `EXIT SECTION` - a no-op
             continuation whose only purpose is to give the paragraph a body.
             It is retained as a named function because rule R-5 requires one
             function per paragraph even where the paragraph does nothing.
    FINDING  the label carries an `a` suffix, and the `Gross` section's exit
             carries a `b`, so the two are distinct labels rather than the
             repeated `main-exit` found in the Sales and Purchase programs.
             The function names are nonetheless section-qualified, for
             consistency with the rest of this folder.
    """
    return


#  Gross section.   [irs/irs030.cbl:L1556]
# ---------------------------------------------------------------------------


def _gross_section(
    posting_record: PostingRecord,
    ws_vat_current: Decimal,
) -> None:
    """`Gross section.` - extract VAT from a VAT-INCLUSIVE amount.

    Verbatim [irs/irs030.cbl:L1556-L1564]::

        1556  Gross section.
        1557 *>------------
        1558 *>
        1559 *> calculate vat from gross
        1560 *>
        1561  *>    compute  vat-amount rounded = post-amount - (post-amount / ( (vat + 100) / 100)).
        1562      compute  vat-amount rounded =
        1563               post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
        1564      subtract vat-amount from post-amount.

    Two stores, and they differ in rounding: the compute is ROUNDED, the
    subtraction that follows it is not.  See Q-18 for why the compound
    expression is transcribed exactly as parenthesised.
    """
    # ANOMALY A-19 [irs/irs030.cbl:L1561] - a superseded, commented-out variant
    # of this compute survives adjacent to the live one, again referencing `vat`
    # where the live statement references `WS-Vat-Current`.  Carried verbatim:
    #
    #     1561  *>    compute  vat-amount rounded = post-amount - (post-amount / ( (vat + 100) / 100)).
    #
    # Reproduced deliberately per R-4; DO NOT FIX.

    # 1562  compute  vat-amount rounded =
    # 1563           post-amount - (post-amount / ( (WS-Vat-Current + 100) / 100)).
    #       ROUNDED store 2 of the 2 this module owns.
    #
    #       AMBIGUITY Q-18 - a division nested inside a division, named by the
    #       migration plan as the ONE place where an intermediate-precision
    #       difference could change a stored penny.  The expression is
    #       transcribed exactly as parenthesised: it is deliberately NOT
    #       simplified to an equivalent single-division form, because the two
    #       forms need not agree once the intermediate is finite.  Every operator
    #       below runs inside the arithmetic layer's extended intermediate
    #       precision and there is exactly one store, at the end.  Expected
    #       values are taken from the compiled program, never from the algebra.
    posting_record.vat_amount = arithmetic.compute(
        lambda: posting_record.post_amount
        - (posting_record.post_amount / ((ws_vat_current + 100) / 100)),
        _VAT_AMOUNT,
        rounded=True,
    )

    # 1564  subtract vat-amount from post-amount.
    #       UN-ROUNDED: this store truncates toward zero.  The gross amount
    #       becomes the net amount, in place.
    #
    #       CITATION CORRECTION - the migration plan cites this subtraction at
    #       L1565; measured against the frozen source it is at L1564, L1565
    #       being a comment line.
    posting_record.post_amount = arithmetic.subtract_from(
        posting_record.vat_amount,
        receiver_value=posting_record.post_amount,
        receiving=_POST_AMOUNT,
    )
    _gross_main_exitb()


#  Main-Exitb.   [irs/irs030.cbl:L1566]
# ---------------------------------------------------------------------------


def _gross_main_exitb() -> None:
    """`Main-Exitb.` - the `Gross` section's exit paragraph.

    Verbatim [irs/irs030.cbl:L1566-L1567]::

        1566  Main-Exitb.
        1567      exit.

    A plain `EXIT`, as in `Main-Exita`; retained as a named function per R-5.
    """
    return


#  Ledger-Postings-Add section.   [irs/irs030.cbl:L1569]
# ---------------------------------------------------------------------------


def _ledger_postings_add(ws: _WorkingStorage) -> None:
    """`Ledger-Postings-Add section.` [irs/irs030.cbl:L1569] - the migrated surface.

    The section runs from its label at L1569 to `exit section.` at L1730.

    The section's preamble, verbatim [irs/irs030.cbl:L1578-L1617]::

        1578      perform  acas008-Open-Input.      *>    open input irs-post-file.
        1579      if       FS-Reply not = zero
        1580               display IR031 at 2301 with foreground-color 2
        1581               go to main99-exit.
        1582 *>
        1583 *>   Get default record
        1584 *>
        1585      move     3  to  file-function.
        1586      perform  acasirsub3.    *> call-irsub3.
        1587 *>
        1588 *>   Open I-O Nominal-Ledger.
        1589 *>
        1590  *>    perform  acasirsub1-Open.      *> IT is opened in intialise-main
        1591 *>
        1592 *> Get default input and output tax accounts via acs 31 & 32 and save them.
        1593 *>
        1594      move     def-acs (31) to nl-owning.
        1595      move     zero         to nl-sub-nominal.
        1596      perform  acasirsub1-Read-Indexed.
        1597      if       we-error not = zero
        1598               display IR03A at 2301 with foreground-color 4 highlight
        1599               display we-error at 2319 with foreground-color 4 highlight
        1600               accept WS-Reply at 2340
        1601               go to main99-exit.
        1602      move     WS-IRSNL-Record to nl31-record.
        1603 *>
        1604      move     def-acs (32) to nl-owning.
        1605      move     zero         to nl-sub-nominal.
        1606      perform  acasirsub1-Read-Indexed.
        1607      if       we-error not = zero
        1608               display IR03B at 2301 with foreground-color 4 highlight
        1609               display we-error at 2319 with foreground-color 4 highlight
        1610               accept WS-Reply at 2340
        1611               go to main99-exit.
        1612      move     WS-IRSNL-Record to nl32-record.
        1613 *>
        1614 *>   open    i-o post-file.
        1615 *>
        1616      display  "Updating Nominal Ledger" at 2401 with foreground-color 2.
        1617      perform  acasirsub4-Open.         *> call-irsub4.

    The three `go to main99-exit` sites above are the ABORT-WITH-NOTHING
    disposition: `main99-exit` is `exit section.` [irs/irs030.cbl:L1730], so
    `EOJ` is bypassed entirely and neither VAT-snapshot rewrite nor any close
    takes place.  That is why they are `return`s here and not `break`s: a `break`
    would fall into the post-loop block, which is the very work these paths must
    skip.
    """
    # 1578  perform  acas008-Open-Input.      *>    open input irs-post-file.
    facade.acas008_open_input(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irs_posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1579  if       FS-Reply not = zero
    #       This site reads FS-Reply.  Five later sites read we-error instead;
    #       the two fields are not interchangeable and each site keeps its own.
    #
    # FINDING - this test is UNREACHABLE-WHEN-TRUE against the facade as the
    # frozen copybook declares it.  `acas008-Open-Input`
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140] already performs
    # `acas008-Check-4-Errors`, whose predicate `fs-reply not = zero` is
    # identical to this one; on failure that check displays IR916, closes the
    # file and reaches `Open-Error-Continued`, which ends in `goback.`
    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] - a hard return out of
    # `irs030`, so control never arrives here.  On success FS-Reply is zero and
    # the predicate is false.  Rule R-3 forbids removing a predicate the
    # compiled program contains, so it is transcribed exactly as written.
    if arithmetic.compare(ws.file_access.fs_reply, FsReply.SUCCESS) != 0:
        # 1580  display IR031 at 2301 with foreground-color 2
        _LOG.error("%s", _IR031)
        # 1581  go to main99-exit.
        # GO TO class 3 - section exit.  ABORT-WITH-NOTHING: `EOJ` is skipped,
        # so no snapshot rewrite and no close happen.
        _main99_exit()
        return

    # 1585  move     3  to  file-function.
    #       The function code is bound to the operation vocabulary's own member
    #       rather than written as a bare literal; `wsfnctn.cob` names 3 as the
    #       read-next function.  The store is routed through the MOVE layer
    #       because this module holds no storage primitives of its own.
    ws.file_access.file_function = move.move(
        int(FileFunction.READ_NEXT), _FILE_FUNCTION
    )

    # 1586  perform  acasirsub3.    *> call-irsub3.
    #       THE BARE HANDLER FORM - the handler alias with no verb suffix,
    #       reached only after the function code has been set by hand above.
    #       Deliberately NOT rewritten as a read-next verb call.
    facade.acasirsub3(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irs_default_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1590  *>    perform  acasirsub1-Open.      *> IT is opened in intialise-main
    #       Carried as a comment: the nominal ledger is already open, having been
    #       opened by an out-of-scope initialisation section.  No open is issued
    #       here, exactly as the frozen program issues none.
    #
    #       That comment states this section's PRECONDITION, and `run` is where
    #       the migration establishes it - `acasirsub1-Open-Input`
    #       [irs/irs030.cbl:L1481] before the section and `acasirsub1-Close`
    #       [irs/irs030.cbl:L589] after it, at the program boundary the frozen
    #       menu loop provides.  The mode is INPUT, not I-O; see the note at
    #       `run` for why the four rewrites below succeed against it.

    # --- snapshot 1: the purchase-side VAT control account -------------------
    #
    # THE CROSS-PROGRAM CONTRACT: subscript 31 is the account the purchase
    # posting programs nominate [purchase/pl060.cbl:L993],
    # [purchase/pl100.cbl:L640]; subscript 32 is the one the sales invoice
    # poster nominates [sales/sl060.cbl:L1139].  Those citations document the
    # contract this section consumes; no line of those programs is reproduced
    # here.

    # 1594  move     def-acs (31) to nl-owning.
    ws.ws_irsnl_record.nl_key.nl_owning = move.move(
        ws.ws_irs_default_record.def_group[_DEF_ACS_SUBSCRIPT_31].def_acs,
        _NL_OWNING,
    )
    # 1595  move     zero         to nl-sub-nominal.
    ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
        move.ZERO, _NL_SUB_NOMINAL
    )
    # 1596  perform  acasirsub1-Read-Indexed.
    facade.acasirsub1_read_indexed(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )
    # 1597  if       we-error not = zero
    #       "not = zero" here, where the two in-loop account lookups test for
    #       equality with 2.  The asymmetry is the frozen program's; preserved.
    if arithmetic.compare(ws.file_access.we_error, WeError.SUCCESS) != 0:
        # 1598  display IR03A at 2301 with foreground-color 4 highlight
        # 1599  display we-error at 2319 with foreground-color 4 highlight
        _LOG.error("%s%s", _IR03A, ws.file_access.we_error)
        # 1600  accept WS-Reply at 2340
        #       An acknowledgement pause with no database effect - dropped.  The
        #       control transfer that follows it is preserved.
        # 1601  go to main99-exit.
        # GO TO class 3 - section exit.  ABORT-WITH-NOTHING.
        _main99_exit()
        return

    # 1602  move     WS-IRSNL-Record to nl31-record.
    #
    # ANOMALY A-5 [irs/irs030.cbl:L1602] - the purchase-side VAT control account
    # is snapshotted into working storage BEFORE the posting loop runs, and is
    # rewritten FROM this snapshot at end of job [irs/irs030.cbl:L1705].  Any
    # in-loop rewrite of this same account is therefore silently discarded.
    # Reproduced deliberately per R-4; DO NOT FIX.
    _move_nl_record_to_snapshot(ws.ws_irsnl_record, ws.nl31_record)

    # --- snapshot 2: the sales-side VAT control account ----------------------

    # 1604  move     def-acs (32) to nl-owning.
    ws.ws_irsnl_record.nl_key.nl_owning = move.move(
        ws.ws_irs_default_record.def_group[_DEF_ACS_SUBSCRIPT_32].def_acs,
        _NL_OWNING,
    )
    # 1605  move     zero         to nl-sub-nominal.
    #       The subscript store and the sub-nominal zeroing are repeated in full
    #       rather than hoisted, and the account is read with a second, separate
    #       indexed read.  Both would be obvious targets for an optimiser; rule
    #       R-3 and the plan's exclusion of performance work leave them exactly
    #       as the frozen program has them.
    ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
        move.ZERO, _NL_SUB_NOMINAL
    )
    # 1606  perform  acasirsub1-Read-Indexed.
    facade.acasirsub1_read_indexed(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )
    # 1607  if       we-error not = zero
    if arithmetic.compare(ws.file_access.we_error, WeError.SUCCESS) != 0:
        # 1608  display IR03B at 2301 with foreground-color 4 highlight
        # 1609  display we-error at 2319 with foreground-color 4 highlight
        _LOG.error("%s%s", _IR03B, ws.file_access.we_error)
        # 1610  accept WS-Reply at 2340   - acknowledgement pause, dropped
        # 1611  go to main99-exit.
        # GO TO class 3 - section exit.  ABORT-WITH-NOTHING.
        _main99_exit()
        return

    # 1612  move     WS-IRSNL-Record to nl32-record.
    #
    # ANOMALY A-5 [irs/irs030.cbl:L1612] - the sales-side VAT control account,
    # snapshotted before the loop and rewritten from the snapshot at
    # [irs/irs030.cbl:L1708].  Same lost update as the account above.
    # Reproduced deliberately per R-4; DO NOT FIX.
    _move_nl_record_to_snapshot(ws.ws_irsnl_record, ws.nl32_record)

    # 1616  display  "Updating Nominal Ledger" at 2401 with foreground-color 2.
    #       A progress display with no database effect - a log record.
    _LOG.info("Updating Nominal Ledger")

    # 1617  perform  acasirsub4-Open.         *> call-irsub4.
    #
    # FINDING - this open has NEITHER a facade error check nor an inline test.
    # `acasirsub4` is the one dispatched handler for which the copybook declares
    # no `Check-4-Errors` paragraph, and `irs030` tests nothing here, so a failed
    # open is silently ignored; the failure surfaces only at the write below,
    # where the inline test at [irs/irs030.cbl:L1674] catches it.
    facade.acasirsub4_open(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1619-1700  Input-Loop.
    #       Both of the loop's exits are `go to EOJ`, so the post-loop block
    #       below is reached on either.  The three `go to main99-exit` sites
    #       above return instead, and therefore skip it.  The split is exact.
    _input_loop(ws)

    # 1702  EOJ.        - reached by falling out of the loop on either exit
    _eoj(ws)
    # 1715  EOJ-q1.     - `EOJ` falls straight through into it
    _eoj_q1(ws)
    # 1729  main99-exit.
    _main99_exit()


#  Input-Loop.   [irs/irs030.cbl:L1619]
# ---------------------------------------------------------------------------


def _input_loop(ws: _WorkingStorage) -> None:
    """`Input-Loop.` - the transfer-file walk, and where anomaly A-4 lives.

    Verbatim [irs/irs030.cbl:L1619-L1700]::

        1619  Input-Loop.
        1620      perform  acas008-Read-Next.    *>    read  irs-post-file at end
        1621      if       FS-Reply = 10
        1622               go to EOJ.
        1623      add      1 to Post-Record-Cnt.
        1624 *>
        1625 *> Processing for DR
        1626 *>
        1627      move     WS-IRS-Post-DR to  nl-owning.
        1628      move     zero           to  nl-sub-nominal.
        1629      perform  acasirsub1-Read-Indexed.
        1630      if       we-error = 2
        1631               display IR032          at 2301 with foreground-color 4 highlight
        1632               display WS-IRS-Post-DR at 2325 with foreground-color 4 highlight
        1633               accept WS-Reply        at 2340
        1634               go to Input-Loop.
        1635      add      WS-IRS-Post-Amount  to  nl-dr.
        1636      if       ws-irs-post-vat-side = "CR"
        1637               add  WS-IRS-Vat-Amount  to  nl-dr.
        1638 *>
        1639 *>  rewrite
        1640 *>
        1641      perform  acasirsub1-Rewrite.
        1642 *>
        1643 *> Processing for CR
        1644 *>
        1645      move     WS-IRS-Post-CR  to  nl-owning.
        1646      move     zero            to  nl-sub-nominal.
        1647      perform  acasirsub1-Read-Indexed.
        1648      if       we-error = 2
        1649               display IR033          at 2301 with foreground-color 4 highlight
        1650               display WS-IRS-Post-CR at 2325 with foreground-color 4 highlight
        1651               accept WS-Reply        at 2340
        1652               go to Input-Loop.
        1653      add      WS-IRS-Post-Amount  to  nl-cr.
        1654      if       WS-irs-post-vat-side = "DR"
        1655               add  WS-IRS-Vat-Amount  to  nl-cr.
        1656 *>
        1657      perform  acasirsub1-Rewrite.

    FINDING  the VAT side is applied ASYMMETRICALLY, and the condition is
             INVERTED relative to the leg it affects: [irs/irs030.cbl:L1636-L1637]
             adds the VAT to the DEBIT accumulator when the side is `"CR"`, and
             [irs/irs030.cbl:L1654-L1655] adds it to the CREDIT accumulator when
             the side is `"DR"`.  That is not a transcription slip to be
             corrected here - it is what the frozen program does.
    FINDING  the field is spelled three different ways across the section -
             `ws-irs-post-vat-side` [irs/irs030.cbl:L1636], mixed-case
             `WS-irs-post-vat-side` [irs/irs030.cbl:L1654] and
             `WS-IRS-Post-Vat-Side` [irs/irs030.cbl:L1686].  COBOL is
             case-insensitive so all three name one field; the inconsistency is
             recorded rather than propagated.
    FINDING  neither `acasirsub1-Rewrite` site has a facade error check
             [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L217-L220] and neither has
             an inline test, so a failed rewrite is silently ignored.  That
             compounds A-4: the debit can fail to persist with no diagnostic at
             all.
    FINDING  the alphanumeric relations below are realised with a direct
             equality.  For two operands of equal declared width - `pic xx`
             against a two-character literal - the COBOL relation reduces to a
             byte-wise comparison in the collating sequence, which is exactly
             what this is; and because the stored side always arrives through the
             MOVE layer at its declared width, no padding asymmetry can arise.
             Numeric relations go through the arithmetic layer's comparator
             instead, because those compare algebraically after decimal-point
             alignment rather than byte-wise.
    """
    while True:
        # 1620  perform  acas008-Read-Next.    *>    read  irs-post-file at end
        facade.acas008_read_next(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irs_posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # 1621  if       FS-Reply = 10
        #       FS-Reply, not we-error.  The read-next verb carries no facade
        #       error check, so this inline test is the live end-of-file gate.
        if arithmetic.compare(ws.file_access.fs_reply, FsReply.END_OF_FILE) == 0:
            # 1622  go to EOJ.
            # GO TO class 2 - loop terminator.  The post-loop block is the
            # caller's `_eoj` / `_eoj_q1` / `_main99_exit` sequence: both class-2
            # sites in this loop reach it, and it must not be dropped, because it
            # carries the two VAT-snapshot rewrites, the three closes and the
            # conditional table truncation - the section's most consequential
            # database effects.
            break

        # 1623  add      1 to Post-Record-Cnt.
        #       A display counter only: it feeds the completion message at
        #       [irs/irs030.cbl:L1714] and reaches no table.  Retained because
        #       that log line consumes it.
        ws.post_record_cnt = arithmetic.add_to(
            1,
            receiver_value=ws.post_record_cnt,
            receiving=_POST_RECORD_CNT,
        )

        # --- Processing for DR  [irs/irs030.cbl:L1625] ----------------------

        # 1627  move     WS-IRS-Post-DR to  nl-owning.
        ws.ws_irsnl_record.nl_key.nl_owning = move.move(
            ws.ws_irs_posting_record.ws_irs_post_dr,
            _NL_OWNING,
            sending_field=_XFER_POST_DR,
        )
        # 1628  move     zero           to  nl-sub-nominal.
        ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
            move.ZERO, _NL_SUB_NOMINAL
        )
        # 1629  perform  acasirsub1-Read-Indexed.
        facade.acasirsub1_read_indexed(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # 1630  if       we-error = 2
        #       EQUALITY WITH 2 - deliberately not widened to "not = zero".  Any
        #       other non-zero error value falls straight through into the
        #       accumulate below, against a record that was not read.  That is
        #       the frozen predicate and rule R-3 forbids broadening it.
        #
        #       AMBIGUITY Q-23 - what value the handler-named facade actually
        #       surfaces for a missing account other than 2.  The IRS handler's
        #       own contract documents "2+" as an open-ended range rather than a
        #       single code [common/acasirsub1.cbl:L87], so the compiled program
        #       arbitrates which values reach this test.
        if (
            arithmetic.compare(
                ws.file_access.we_error, _IRS_WE_ERROR_RECORD_NOT_FOUND
            )
            == 0
        ):
            # 1631  display IR032          at 2301 with foreground-color 4 highlight
            # 1632  display WS-IRS-Post-DR at 2325 with foreground-color 4 highlight
            _LOG.error("%s%s", _IR032, ws.ws_irs_posting_record.ws_irs_post_dr)
            # 1633  accept WS-Reply        at 2340   - pause, dropped
            # 1634  go to Input-Loop.
            # GO TO class 1 - loop back.  CLEAN SKIP: the debit account does not
            # exist, nothing has been written for this transfer record, and the
            # next one is read.  Entirely silent in the frozen program - no
            # counter, no rejection tally - so nothing is counted here either.
            continue

        # 1635  add      WS-IRS-Post-Amount  to  nl-dr.
        #
        #       AMBIGUITY Q-25 - `nl-dr` is declared UNSIGNED
        #       [copybooks/irswsnl.cob:L17] while the transfer amount is signed
        #       [copybooks/wspost-irs.cob:L21], so a negative amount loses its
        #       sign on this store.  The storage layer owns that behaviour; the
        #       compiled program arbitrates the value that reaches the column.
        ws.ws_irsnl_record.nl_data.nl_dr = arithmetic.add_to(
            ws.ws_irs_posting_record.ws_irs_post_amount,
            receiver_value=ws.ws_irsnl_record.nl_data.nl_dr,
            receiving=_NL_DR,
        )

        # 1636  if       ws-irs-post-vat-side = "CR"
        #       INVERTED: the CREDIT side sends its VAT to the DEBIT accumulator.
        if ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_CR:
            # 1637  add  WS-IRS-Vat-Amount  to  nl-dr.
            ws.ws_irsnl_record.nl_data.nl_dr = arithmetic.add_to(
                ws.ws_irs_posting_record.ws_irs_vat_amount,
                receiver_value=ws.ws_irsnl_record.nl_data.nl_dr,
                receiving=_NL_DR,
            )

        # 1641  perform  acasirsub1-Rewrite.
        #
        # ANOMALY A-4 [irs/irs030.cbl:L1641] - THE DEBIT IS COMMITTED HERE,
        # before the credit account is so much as looked up at
        # [irs/irs030.cbl:L1647].  If that lookup then fails, the run abandons
        # this transfer record at [irs/irs030.cbl:L1652] and the debit stays
        # written: an unbalanced debit, no matching credit, and no internal
        # posting row at all - the posting write is further down, at
        # [irs/irs030.cbl:L1673].  The rewrite is NOT moved after the credit
        # lookup, no rollback is introduced and the credit account is NOT
        # pre-validated.
        # Reproduced deliberately per R-4; DO NOT FIX.
        #
        #       AMBIGUITY Q-19 - whether the debit written here is durable once
        #       the run later reaches `EOJ` by a different path.  Arbitrated
        #       against the compiled program.
        facade.acasirsub1_rewrite(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # --- Processing for CR  [irs/irs030.cbl:L1643] ----------------------

        # 1645  move     WS-IRS-Post-CR  to  nl-owning.
        ws.ws_irsnl_record.nl_key.nl_owning = move.move(
            ws.ws_irs_posting_record.ws_irs_post_cr,
            _NL_OWNING,
            sending_field=_XFER_POST_CR,
        )
        # 1646  move     zero            to  nl-sub-nominal.
        ws.ws_irsnl_record.nl_key.nl_sub_nominal = move.move_figurative(
            move.ZERO, _NL_SUB_NOMINAL
        )
        # 1647  perform  acasirsub1-Read-Indexed.
        facade.acasirsub1_read_indexed(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # 1648  if       we-error = 2
        #       Equality with 2 again, for the same reason as the debit leg.
        if (
            arithmetic.compare(
                ws.file_access.we_error, _IRS_WE_ERROR_RECORD_NOT_FOUND
            )
            == 0
        ):
            # 1649  display IR033          at 2301 with foreground-color 4 highlight
            # 1650  display WS-IRS-Post-CR at 2325 with foreground-color 4 highlight
            _LOG.error("%s%s", _IR033, ws.ws_irs_posting_record.ws_irs_post_cr)
            # 1651  accept WS-Reply        at 2340   - pause, dropped
            # 1652  go to Input-Loop.
            # GO TO class 1 - loop back.
            #
            # ANOMALY A-4 [irs/irs030.cbl:L1652] - THIS is the half-posted
            # abandon.  Control returns to the head of the loop with the debit
            # from [irs/irs030.cbl:L1641] already committed, no credit written
            # and no internal posting row created.  The transfer record is
            # simply left behind.  No compensating write, no rollback and no
            # diagnostic beyond the display are introduced.
            # Reproduced deliberately per R-4; DO NOT FIX.
            continue

        # 1653  add      WS-IRS-Post-Amount  to  nl-cr.
        ws.ws_irsnl_record.nl_data.nl_cr = arithmetic.add_to(
            ws.ws_irs_posting_record.ws_irs_post_amount,
            receiver_value=ws.ws_irsnl_record.nl_data.nl_cr,
            receiving=_NL_CR,
        )

        # 1654  if       WS-irs-post-vat-side = "DR"
        #       INVERTED: the DEBIT side sends its VAT to the CREDIT accumulator.
        if ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_DR:
            # 1655  add  WS-IRS-Vat-Amount  to  nl-cr.
            ws.ws_irsnl_record.nl_data.nl_cr = arithmetic.add_to(
                ws.ws_irs_posting_record.ws_irs_vat_amount,
                receiver_value=ws.ws_irsnl_record.nl_data.nl_cr,
                receiving=_NL_CR,
            )

        # 1657  perform  acasirsub1-Rewrite.
        #       The credit leg's commit.  Like the debit's, it is neither checked
        #       by the facade nor tested inline.
        facade.acasirsub1_rewrite(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # --- Now add SL/PL posting to IRS post file  [irs/irs030.cbl:L1659] --
        #
        # Nine field moves carry the transfer record into the internal posting
        # record, then the key is allocated.  Verbatim
        # [irs/irs030.cbl:L1661-L1671]::
        #
        #     1661      move     WS-IRS-Post-Code   to post-code.
        #     1662      move     WS-IRS-Post-Date   to post-date.
        #     1663      move     WS-IRS-Post-CR     to post-cr.
        #     1664      move     WS-IRS-Post-DR     to post-dr.
        #     1665      move     WS-IRS-Post-Amount to post-amount.
        #     1666      move     WS-IRS-Post-Legend to post-legend.
        #     1667      move     WS-IRS-Vat-AC-Def  to vat-ac-def.
        #     1668      move     WS-IRS-Post-Vat-Side to post-vat-side.
        #     1669      move     WS-IRS-Vat-Amount  to vat-amount.
        #     1670      move     next-post to post-key.
        #     1671      add      1 to next-post.
        #
        # Note the order of the credit and debit moves: the COBOL writes CR
        # before DR here, the reverse of the order in which the two legs were
        # posted above.  Transcribed in the source order.

        # 1661  move     WS-IRS-Post-Code   to post-code.
        ws.posting_record.post_code = move.move(
            ws.ws_irs_posting_record.ws_irs_post_code,
            _POST_CODE,
            sending_field=_XFER_POST_CODE,
        )
        # 1662  move     WS-IRS-Post-Date   to post-date.
        #       THE DATE ARRIVES IN THE DATA.  This is the only date the section
        #       handles and it is carried straight through, unconverted: no clock
        #       is read and no date parameter exists.  It is also the field the
        #       internal posting bridge's guarded substring rule reads when it
        #       derives its three date-component columns, so this move's fidelity
        #       feeds that anomaly - which is owned by the internal posting
        #       handler module, not by this one.
        ws.posting_record.post_date = move.move(
            ws.ws_irs_posting_record.ws_irs_post_date,
            _POST_DATE,
            sending_field=_XFER_POST_DATE,
        )
        # 1663  move     WS-IRS-Post-CR     to post-cr.
        ws.posting_record.post_cr = move.move(
            ws.ws_irs_posting_record.ws_irs_post_cr,
            _POST_CR,
            sending_field=_XFER_POST_CR,
        )
        # 1664  move     WS-IRS-Post-DR     to post-dr.
        ws.posting_record.post_dr = move.move(
            ws.ws_irs_posting_record.ws_irs_post_dr,
            _POST_DR,
            sending_field=_XFER_POST_DR,
        )
        # 1665  move     WS-IRS-Post-Amount to post-amount.
        #       Signed DISPLAY with the sign carried leading, on both sides.
        ws.posting_record.post_amount = move.move(
            ws.ws_irs_posting_record.ws_irs_post_amount,
            _POST_AMOUNT,
            sending_field=_XFER_AMOUNT,
        )
        # 1666  move     WS-IRS-Post-Legend to post-legend.
        ws.posting_record.post_legend = move.move(
            ws.ws_irs_posting_record.ws_irs_post_legend,
            _POST_LEGEND,
            sending_field=_XFER_POST_LEGEND,
        )
        # 1667  move     WS-IRS-Vat-AC-Def  to vat-ac-def.
        #       The 31/32 selector, carried from the transfer record into the
        #       internal posting row.
        ws.posting_record.vat_ac_def = move.move(
            ws.ws_irs_posting_record.ws_irs_vat_ac_def,
            _VAT_AC_DEF,
            sending_field=_XFER_VAT_AC_DEF,
        )
        # 1668  move     WS-IRS-Post-Vat-Side to post-vat-side.
        ws.posting_record.post_vat_side = move.move(
            ws.ws_irs_posting_record.ws_irs_post_vat_side,
            _POST_VAT_SIDE,
            sending_field=_XFER_POST_VAT_SIDE,
        )
        # 1669  move     WS-IRS-Vat-Amount  to vat-amount.
        ws.posting_record.vat_amount = move.move(
            ws.ws_irs_posting_record.ws_irs_vat_amount,
            _VAT_AMOUNT,
            sending_field=_XFER_VAT_AMOUNT,
        )

        # 1670  move     next-post to post-key.
        #       `next-post` is a field of the FIRST linkage parameter, not of the
        #       ACAS system record - see this module's import banner for the COPY
        #       REPLACING that settles the homonym.
        ws.posting_record.post_key = move.move(
            ws.irs_system_params.next_post,
            _POST_KEY,
            sending_field=_NEXT_POST,
        )
        # 1671  add      1 to next-post.
        #       THE INCREMENT PRECEDES THE WRITE.  It is a real, diff-visible
        #       mutation of a linkage parameter, and it happens whether or not the
        #       write below succeeds.  The ordering is preserved exactly: the
        #       increment is NOT moved after the write.
        #
        #       AMBIGUITY Q-22 - whether the allocator therefore advances across a
        #       failed write.  On this reading it does; the compiled program
        #       arbitrates.
        ws.irs_system_params.next_post = arithmetic.add_to(
            1,
            receiver_value=ws.irs_system_params.next_post,
            receiving=_NEXT_POST,
        )

        # 1673  perform  acasirsub4-Write.
        facade.acasirsub4_write(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

        # 1674  if       we-error not = zero
        #       THE INLINE TEST EXISTS BECAUSE THE FACADE HAS NO CHECK FOR THIS
        #       HANDLER.  The copybook declares five `Check-4-Errors` paragraphs
        #       for six dispatched handlers, and the internal-posting handler is
        #       the one without one, so nothing upstream would notice this
        #       failure.  Note the predicate is "not = zero" here, unlike the two
        #       account lookups above, which test for equality with 2.
        if arithmetic.compare(ws.file_access.we_error, WeError.SUCCESS) != 0:
            # 1675  display IR914 at 2301 with foreground-color 2
            # 1676  display WE-Error at 2352 with foreground-color 2
            _LOG.error("%s%s", _IR914, ws.file_access.we_error)
            # 1677  accept WS-Reply at 2355   - pause, dropped
            # 1678  go to EOJ.
            # GO TO class 2 - loop terminator.  THE WRITE-FAILURE JUMP.
            #
            # ANOMALY [irs/irs030.cbl:L1674-L1678] - this jumps to `EOJ`, NOT
            # back to `Input-Loop`, and `EOJ` still performs both VAT-snapshot
            # rewrites and all three closes.  The partial state that this
            # transfer record left behind - the posted debit, the posted credit
            # and the advanced key allocator, with no internal posting row - is
            # therefore COMMITTED, not rolled back.  This is the
            # COMMIT-AND-STOP disposition, and it is distinct from both the clean
            # skip above and the abort-with-nothing paths in the preamble.  No
            # rollback, no retry and no skipping of the end-of-job work is
            # introduced.
            # Reproduced deliberately per R-4; DO NOT FIX.
            break

        # --- Processing for VAT  [irs/irs030.cbl:L1680] ---------------------
        #
        # Verbatim [irs/irs030.cbl:L1682-L1700]::
        #
        #     1682      if       WS-IRS-Vat-AC-Def = zero
        #     1683               go to  Input-Loop.
        #     1684 *>
        #     1685      if       WS-IRS-Vat-AC-Def = 31
        #     1686          and  WS-IRS-Post-Vat-Side = "CR"
        #     1687               add  WS-IRS-Vat-Amount  to  nl31-cr
        #     1688      else
        #     1689        if     WS-IRS-Vat-AC-Def = 31
        #     1690          and  WS-IRS-Post-Vat-Side = "DR"
        #     1691               add  WS-IRS-Vat-Amount  to  nl31-dr
        #     1692        else
        #     1693         if    WS-IRS-Vat-AC-Def = 32
        #     1694           and WS-IRS-Post-Vat-Side = "CR"
        #     1695               add  WS-IRS-Vat-Amount  to  nl32-cr
        #     1696        else
        #     1697         if   WS-IRS-Vat-AC-Def = 32
        #     1698          and WS-IRS-Post-Vat-Side = "DR"
        #     1699               add  WS-IRS-Vat-Amount  to  nl32-dr.
        #     1700      go       to Input-Loop.

        # 1682  if       WS-IRS-Vat-AC-Def = zero
        if arithmetic.compare(ws.ws_irs_posting_record.ws_irs_vat_ac_def, 0) == 0:
            # 1683  go to  Input-Loop.
            # GO TO class 1 - loop back, skipping the VAT ladder entirely.  The
            # guard is preserved: a transfer record with no VAT account nominated
            # contributes nothing to either snapshot.
            continue

        # THE FOUR-WAY VAT LADDER.  A NESTED if/else CHAIN, not four sibling
        # `if`s: each `else` guards the next `if`, and the whole chain is
        # terminated by the single period at [irs/irs030.cbl:L1699].  The nesting
        # is transcribed literally rather than flattened, so that the structure a
        # reader diffs against the COBOL is the same structure.
        #
        # ANOMALY A-5 - EVERY ARM ACCUMULATES INTO A SNAPSHOT, never into the
        # live nominal-ledger row.  That is what makes the lost update at
        # [irs/irs030.cbl:L1705] and [irs/irs030.cbl:L1708] inevitable rather
        # than incidental.
        # Reproduced deliberately per R-4; DO NOT FIX.
        #
        # AMBIGUITY Q-21 - THERE IS NO FINAL `else`.  A VAT account that is
        # non-zero but neither 31 nor 32 falls off the end of the chain: the VAT
        # accumulates nowhere and nothing is reported.  No `else` and no
        # diagnostic are added.
        # 1685  if       WS-IRS-Vat-AC-Def = 31
        # 1686      and  WS-IRS-Post-Vat-Side = "CR"
        if (
            arithmetic.compare(
                ws.ws_irs_posting_record.ws_irs_vat_ac_def, _VAT_AC_PURCHASE
            )
            == 0
            and ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_CR
        ):
            # 1687  add  WS-IRS-Vat-Amount  to  nl31-cr
            ws.nl31_record.cr = arithmetic.add_to(
                ws.ws_irs_posting_record.ws_irs_vat_amount,
                receiver_value=ws.nl31_record.cr,
                receiving=_NL31_CR,
            )
        # 1688  else
        else:
            # 1689    if     WS-IRS-Vat-AC-Def = 31
            # 1690      and  WS-IRS-Post-Vat-Side = "DR"
            if (
                arithmetic.compare(
                    ws.ws_irs_posting_record.ws_irs_vat_ac_def, _VAT_AC_PURCHASE
                )
                == 0
                and ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_DR
            ):
                # 1691  add  WS-IRS-Vat-Amount  to  nl31-dr
                ws.nl31_record.dr = arithmetic.add_to(
                    ws.ws_irs_posting_record.ws_irs_vat_amount,
                    receiver_value=ws.nl31_record.dr,
                    receiving=_NL31_DR,
                )
            # 1692    else
            else:
                # 1693     if    WS-IRS-Vat-AC-Def = 32
                # 1694       and WS-IRS-Post-Vat-Side = "CR"
                if (
                    arithmetic.compare(
                        ws.ws_irs_posting_record.ws_irs_vat_ac_def, _VAT_AC_SALES
                    )
                    == 0
                    and ws.ws_irs_posting_record.ws_irs_post_vat_side == _SIDE_CR
                ):
                    # 1695  add  WS-IRS-Vat-Amount  to  nl32-cr
                    ws.nl32_record.cr = arithmetic.add_to(
                        ws.ws_irs_posting_record.ws_irs_vat_amount,
                        receiver_value=ws.nl32_record.cr,
                        receiving=_NL32_CR,
                    )
                # 1696    else
                else:
                    # 1697     if   WS-IRS-Vat-AC-Def = 32
                    # 1698      and WS-IRS-Post-Vat-Side = "DR"
                    if (
                        arithmetic.compare(
                            ws.ws_irs_posting_record.ws_irs_vat_ac_def,
                            _VAT_AC_SALES,
                        )
                        == 0
                        and ws.ws_irs_posting_record.ws_irs_post_vat_side
                        == _SIDE_DR
                    ):
                        # 1699  add  WS-IRS-Vat-Amount  to  nl32-dr.
                        ws.nl32_record.dr = arithmetic.add_to(
                            ws.ws_irs_posting_record.ws_irs_vat_amount,
                            receiver_value=ws.nl32_record.dr,
                            receiving=_NL32_DR,
                        )
                    # NO `else` HERE - see AMBIGUITY Q-21 above.  This is the
                    # end of the chain, and the frozen program supplies no
                    # fall-through arm.

        # 1700  go       to Input-Loop.
        # GO TO class 1 - loop back.  Written explicitly rather than left to fall
        # off the end of the block, because the COBOL writes it explicitly.
        continue


#  EOJ.   [irs/irs030.cbl:L1702]
# ---------------------------------------------------------------------------


def _eoj(ws: _WorkingStorage) -> None:
    """`EOJ.` - the post-loop block, and the site of anomaly A-5's lost update.

    Verbatim [irs/irs030.cbl:L1702-L1714]::

        1702  EOJ.
        1703 *>
        1704      move     nl31-record to WS-IRSNL-Record.
        1705      perform  acasirsub1-Rewrite.
        1706 *>
        1707      move     nl32-record to WS-IRSNL-Record.
        1708      perform  acasirsub1-Rewrite.
        1709 *>
        1710  *>    perform  acasirsub1-Close.                    *> Closed at EOJ
        1711      perform  acasirsub4-Close.
        1712      perform  acas008-Close.
        1713      display  space at 1201 with erase eol.
        1714      display  "Processing Complete on " Post-Record-Cnt " records".

    This is the block both class-2 transfers reach and all three class-3
    transfers skip.  Dropping any part of it would lose the section's most
    important database effects, so it is reproduced in full and in order.
    """
    # 1704  move     nl31-record to WS-IRSNL-Record.
    #
    # ANOMALY A-5 [irs/irs030.cbl:L1704] - the live nominal-ledger record is
    # OVERWRITTEN from the pre-loop snapshot.  Whatever the loop may have written
    # to account 31 is discarded here before the rewrite below.  The account is
    # NOT re-read, the snapshot is NOT merged with the live row, and the
    # collision is NOT detected.
    # Reproduced deliberately per R-4; DO NOT FIX.
    _move_snapshot_to_nl_record(ws.nl31_record, ws.ws_irsnl_record)

    # 1705  perform  acasirsub1-Rewrite.
    #
    # ANOMALY A-5 [irs/irs030.cbl:L1705] - THE LOST UPDATE.  If any posting's
    # debit or credit account was itself account 31, the in-loop rewrite at
    # [irs/irs030.cbl:L1641] or [irs/irs030.cbl:L1657] is silently discarded by
    # this write.
    # Reproduced deliberately per R-4; DO NOT FIX.
    #
    #       AMBIGUITY Q-20 - the stored state when the loop and this rewrite
    #       target the same row.  Arbitrated against the compiled program.
    facade.acasirsub1_rewrite(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1707  move     nl32-record to WS-IRSNL-Record.
    #
    # ANOMALY A-5 [irs/irs030.cbl:L1707] - as above, for account 32.
    # Reproduced deliberately per R-4; DO NOT FIX.
    _move_snapshot_to_nl_record(ws.nl32_record, ws.ws_irsnl_record)

    # 1708  perform  acasirsub1-Rewrite.
    #
    # ANOMALY A-5 [irs/irs030.cbl:L1708] - the second half of the lost update.
    # Reproduced deliberately per R-4; DO NOT FIX.
    facade.acasirsub1_rewrite(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irsnl_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1710  *>    perform  acasirsub1-Close.                    *> Closed at EOJ
    #       Carried as a comment: the nominal ledger is closed elsewhere, by an
    #       out-of-scope section.  No close is issued for it here.

    # 1711  perform  acasirsub4-Close.
    facade.acasirsub4_close(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1712  perform  acas008-Close.
    #       The transfer file is closed here - and then reopened for output at
    #       [irs/irs030.cbl:L1723] if the clear is requested.
    facade.acas008_close(
        facade.FacadeContext(
            ws.ws_system_record,
            ws.ws_irs_posting_record,
            ws.file_access,
            ws.file_defs,
            ws.dal_common,
            ws.dal_options,
        ),
    )

    # 1713  display  space at 1201 with erase eol.
    #       A screen erase carrying no content - dropped; there is nothing to
    #       log and it has no database effect.

    # 1714  display  "Processing Complete on " Post-Record-Cnt " records".
    #       The one display that carries information, and the sole consumer of
    #       the record counter maintained at [irs/irs030.cbl:L1623].
    _LOG.info("Processing Complete on %s records", ws.post_record_cnt)


#  EOJ-q1.   [irs/irs030.cbl:L1715]
# ---------------------------------------------------------------------------


def _eoj_q1(ws: _WorkingStorage) -> None:
    """`EOJ-q1.` - the end-of-job question that decides whether the table is cleared.

    Verbatim [irs/irs030.cbl:L1715-L1727]::

        1715 EOJ-q1.
        1716      display  "Can I clear the Ledgers Posting file? [Y]" at 1401 with erase eol.
        1717      accept   WS-Reply at 1440 with foreground-color 6 UPPER.
        1718      if       WS-Reply not = "Y" and not = "N"
        1719               go to EOJ-q1.
        1720      if       WS-Reply = "Y"
        1721  *>             open output irs-post-file
        1722  *>             close irs-post-file.
        1723               perform acas008-Open-Output    *>         performs a acas008-Delete-All
        1724               perform acas008-Close.
        1725      display  "Note counts and any messages" at 1401 with erase eol.
        1726      accept   WS-Reply at 1430.
        1727      display  space at 1401 with erase eol.

    THIS PROMPT IS AN INPUT, NOT DECORATION.  Answering `"Y"` opens the transfer
    file for output, and for this handler opening for output means DELETING EVERY
    ROW - the maintainer's own comment at [irs/irs030.cbl:L1723] records it as
    `*> performs a acas008-Delete-All`.  The answer therefore changes table
    state, so the presentation-removal rule keeps it as an explicit parameter of
    `run` rather than dropping it.  THE COBOL HAS NO DEFAULT ANSWER, and the
    appearance that it does is a trap: the prompt literal displays `[Y]`
    [irs/irs030.cbl:L1716], but the `accept` on the next line carries NO `WITH
    UPDATE` phrase [irs/irs030.cbl:L1717], so the literal never reaches the field;
    `WS-Reply pic x` [irs/irs030.cbl:L230] is never given the value `"Y"` anywhere
    in this program - the only moves into it are `space` [irs/irs030.cbl:L1512] and
    `spaces` [irs/irs030.cbl:L1521], and the `move "Z"` at [irs/irs030.cbl:L1530]
    is commented out - and L1718-L1719 send any other reply back to the prompt.
    That the missing `WITH UPDATE` is deliberate shows in this same file, which
    uses the phrase at six other accepts: [irs/irs030.cbl:L582], [:L732], [:L829],
    [:L848], [:L883] and [:L1015].  So a bare Enter RE-PROMPTS rather than
    clearing (finding CLI-05).

    THIS PARAMETER'S OWN DEFAULT OF `True` IS RETAINED DELIBERATELY, and it is a
    signature contract rather than a claim about the COBOL: this module's file
    brief fixes the signature, and every caller in the migration passes the value
    EXPLICITLY, so the default is never consulted.
    `acas_posting/cli/irs_post.py` makes the switch pair `required=True` with no
    default of its own, which is where the absence of a COBOL default is enforced -
    at the boundary an operator actually touches.

    `GO TO` CLASS 4 - PER-SITE PROOF for [irs/irs030.cbl:L1719].
    The transfer is a sibling re-dispatch to the head of this same paragraph, so
    it is a retry loop rather than a plain loop-back over a data cursor, which is
    why it is classified 4 and proved individually rather than folded into class
    1.  Its guard [irs/irs030.cbl:L1718] is an abbreviated relation - `WS-Reply
    not = "Y" and not = "N"` expands to `WS-Reply not = "Y" AND WS-Reply not =
    "N"` - so the paragraph re-displays and re-accepts until the reply is one of
    exactly two values.  The retry is therefore a pure input-acquisition loop: it
    performs no database operation, mutates nothing but `WS-Reply`, and
    terminates only when `WS-Reply` holds `"Y"` or `"N"`.  Replacing the accept
    with a boolean parameter supplies that already-validated two-valued answer
    directly, so the loop's post-condition holds on entry and the loop body can
    never execute.  The transfer therefore COLLAPSES: nothing observable is lost,
    because the only state the loop could have changed is the very value now
    supplied as an argument.  This is a consequence of removing the
    presentation layer, NOT a behaviour change - the two reachable outcomes,
    clear and do-not-clear, are both still reachable and still produce exactly
    the effects the COBOL produces.
    """
    # 1716  display  "Can I clear the Ledgers Posting file? [Y]" at 1401
    # 1717  accept   WS-Reply at 1440 with foreground-color 6 UPPER.
    # 1718  if       WS-Reply not = "Y" and not = "N"
    # 1719           go to EOJ-q1.
    # GO TO class 4 - sibling re-dispatch, collapsed.  See the proof above.

    # 1720  if       WS-Reply = "Y"
    if ws.clear_posting_file:
        # 1721  *>             open output irs-post-file
        # 1722  *>             close irs-post-file.
        #       Both carried as comments, exactly as the frozen program carries
        #       them: they are the superseded direct-file form of the two facade
        #       verbs below.

        # 1723  perform acas008-Open-Output    *> performs a acas008-Delete-All
        #       THE TRUNCATION.  Opening this handler's file for output deletes
        #       every row of the transfer table.  Note that the file was already
        #       closed at [irs/irs030.cbl:L1712]; it is reopened here purely to
        #       be truncated, and closed again immediately below.  Both calls are
        #       reproduced, in order.
        #
        # FINDING - `acas008-Open-Output` DOES carry a facade error check
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L142-L146], so a failed
        # truncation open hard-returns out of the program and the close below,
        # together with the two remaining displays, never runs.  `irs030` adds no
        # inline test of its own here.
        facade.acas008_open_output(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irs_posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )
        # 1724  perform acas008-Close.
        facade.acas008_close(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irs_posting_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
                ws.dal_options,
            ),
        )

    # 1725  display  "Note counts and any messages" at 1401 with erase eol.
    # 1726  accept   WS-Reply at 1430.
    # 1727  display  space at 1401 with erase eol.
    #       A pure acknowledgement pause: the display prompts, the accept blocks
    #       a terminal and the second display erases it again.  No database
    #       effect and no control transfer follows, so all three are dropped
    #       rather than logged.


#  main99-exit.   [irs/irs030.cbl:L1729]
# ---------------------------------------------------------------------------


def _main99_exit() -> None:
    """`main99-exit.` - the section's exit paragraph.

    Verbatim [irs/irs030.cbl:L1729-L1730]::

        1729  main99-exit.
        1730      exit     section.

    `EXIT SECTION`, not the plain `EXIT` of `Main-Exita` and `Main-Exitb`: it
    returns from the section, which is what makes the three class-3 transfers in
    the preamble bypass `EOJ` entirely.

    CITATION CORRECTION - the migration plan gives this section's boundary as
    L1569-L1733.  Measured against the frozen source, the last executable line is
    L1730; L1731 is a comment, L1732 is the facade `COPY` and L1733 is a comment.
    L1569-L1730 is the code boundary used throughout this module.
    """
    return


# --- the program entry point ------------------------------------------------


def run(
    irs_system_params: IrsSystemParams,
    ws_system_record: SystemRecord,
    file_defs: FileDefs,
    *,
    clear_posting_file: bool,
    file_access: FileAccess | None = None,
    dal_common: AcasDalCommonData | None = None,
    dal_options: Mapping[str, object] | None = None,
) -> None:
    """Run `irs030`'s `Ledger-Postings-Add` section.

    The three positional parameters are this program's `PROCEDURE DIVISION
    USING` list, in its exact order and with nothing added
    [irs/irs030.cbl:L552-L554]::

         552  procedure division using IRS-System-Params
         553                           WS-System-Record
         554                           File-Defs.

    THIS IS THE THIRD OF THE MIGRATION'S THREE LINKAGE SHAPES.  There is no
    calling-data block, because `irs030` does not copy `wscall.cob`, and there is
    NO RUN DATE - the posting date arrives in the data, as `WS-IRS-Post-Date`
    [irs/irs030.cbl:L1662].  A `to_day` parameter is deliberately NOT accepted:
    adding one for symmetry with the General, Sales and Purchase entry points
    would misstate this program's contract.

    Args:
        irs_system_params: `IRS-System-Params`, the IRS system record
            [irs/irs030.cbl:L416].  MUTATED: the posting key allocator
            `next-post` advances once per posting written
            [irs/irs030.cbl:L1670-L1671], which is a diff-visible effect.
        ws_system_record: `WS-System-Record`, the ACAS system record
            [irs/irs030.cbl:L419].  Passed through to every handler dispatch,
            exactly as the facade copybook's own CALL list passes it.
        file_defs: `File-Defs`, the file and work-file names
            [irs/irs030.cbl:L450].
        clear_posting_file: the answer to the end-of-job question at
            [irs/irs030.cbl:L1717].  `True` clears the transfer table by
            reopening it for output, which for this handler deletes every row.
            Defaults to `True` as a SIGNATURE CONTRACT fixed by this module's
            file brief, NOT because the COBOL has that default - it has none. The
            `[Y]` at [irs/irs030.cbl:L1716] is prompt text, the accept at L1717
            carries no `WITH UPDATE`, and L1718-L1719 re-prompt on anything that is
            not `"Y"` or `"N"`. Every caller in the migration passes this
            explicitly, so the default is never consulted, and
            `acas_posting/cli/irs_post.py` requires the answer at the boundary an
            operator touches (finding CLI-05).
        file_access: the `File-Access` block [irs/irs030.cbl:L285].  Not a
            linkage parameter - it is this program's own WORKING-STORAGE, exposed
            because the connection details the handlers need are loaded into it by
            an out-of-scope initialisation section, so the entry point must be
            able to receive one already populated.  A fresh block is created when
            omitted.
        dal_common: the `ACAS-DAL-Common-data` block
            [copybooks/Test-Data-Flags.cob:L6], copied by this program at
            [irs/irs030.cbl:L298].  Also WORKING-STORAGE rather than linkage, and
            the fifth operand of every handler CALL.  A fresh block is created
            when omitted.
        dal_options: the caller's keyword-only handler declarations, forwarded to
            every facade `PERFORM` this section issues, and the declaration it
            exists for is the transport-security policy.  NOT a linkage operand
            and NOT working storage: the frozen bridge has no transport policy to
            declare, its connect passing six values and nothing else
            [copybooks/mysql-procedures.cpy:L72-L77].  `None` - the default -
            declares nothing, which every handler resolves FAIL-CLOSED: a Unix
            socket or a loopback address is permitted and any other target
            refused.  A run against the containerised parity harness must
            therefore say so explicitly, `dal_options={"transport":
            TransportSecurity(isolated_oracle=True)}`, and a run against a real
            server should be given `TransportSecurity(ca_file=...)`.  It changes
            no status, no statement, no arithmetic and no write order.

    Returns:
        Nothing.  The section communicates entirely through the database, through
        the `File-Access` status block and through the advanced key allocator on
        `irs_system_params`.  Every disposition - clean skip, commit-and-stop,
        abort-with-nothing, and the facade copybook's own `goback`
        [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] - is a normal return; the
        frozen program raises no condition and signals no failure to its caller,
        so neither does this entry point.

    THE NOMINAL LEDGER IS OPENED AND CLOSED HERE, not in the section.  The
    section runs against a file its out-of-scope `Initialise-Main` left open for
    INPUT [irs/irs030.cbl:L1481] and which `Main-Loop-Clear` closes when the
    operator leaves the menu [irs/irs030.cbl:L589]; `run` is the only place in
    the migrated surface that corresponds to that program boundary.  The
    bracketing statements and the reason the INPUT mode is correct for the
    section's four rewrites are documented at the call site below.
    """
    # The remaining records are this program's own WORKING-STORAGE, initialised
    # as COBOL initialises WORKING-STORAGE: to the layout's own default values.
    # No validation of the arguments is performed, because the frozen program
    # performs none and rule R-3 forbids adding any.
    ws = _WorkingStorage(
        irs_system_params=irs_system_params,
        ws_system_record=ws_system_record,
        file_defs=file_defs,
        file_access=FileAccess() if file_access is None else file_access,
        dal_common=AcasDalCommonData() if dal_common is None else dal_common,
        ws_irsnl_record=WsIrsnlRecord(),  # copy "irswsnl.cob" ...       [L286]
        ws_irs_default_record=WsIrsDefaultRecord(),  # copy "irswsdflt.cob" ...  [L287]
        posting_record=PostingRecord(),  # copy "irswspost.cob".     [L288]
        ws_irs_posting_record=WsIrsPostingRecord(),  # copy "wspost-irs.cob".    [L289]
        nl31_record=_NlSnapshot(),  # 01 nl31-record.          [L348]
        nl32_record=_NlSnapshot(),  # 01 nl32-record.          [L363]
        post_record_cnt=0,  # value zero               [L272]
        clear_posting_file=clear_posting_file,
        # `None` and `{}` are the same thing - no declaration - and both leave
        # every handler at its fail-closed default.  Copied rather than aliased so
        # the caller's mapping cannot change under a run in progress.
        dal_options=dict(dal_options) if dal_options else {},
    )

    # --- THE PROGRAM-BOUNDARY NOMINAL-LEDGER STATE ---------------------------
    #
    # The migrated section issues NO open of the nominal ledger - it says so
    # itself, in a comment that survives in the frozen source
    # [irs/irs030.cbl:L1590]::
    #
    #     1590  *>    perform  acasirsub1-Open.      *> IT is opened in intialise-main
    #
    # and it then drives that already-open file with four `acasirsub1-Read-
    # Indexed` performs (L1596, L1606, L1629, L1647) and four
    # `acasirsub1-Rewrite` performs (L1641, L1657, L1705, L1708).  The two
    # statements that
    # bracket it are therefore part of this PROGRAM's contract even though they
    # sit outside the migrated SECTION, and the Python entry point is the only
    # place they can live: `run` IS the program boundary here, because
    # `Initialise-Main` and the menu loop that contain them are out of scope per
    # Agent Action Plan section 0.2.1.1 ("Partial - only `Ledger-Postings-Add`").
    #
    # Only the acasirsub1 OPEN/CLOSE pair is reproduced.  Nothing else from
    # `Initialise-Main` is - not the screen work, not the CoA table build, not
    # the VAT-account existence sweep, not the VAT-rate load - and none of it is
    # needed by the section, which reloads both VAT accounts itself at
    # [irs/irs030.cbl:L1594-L1612].
    #
    # THE MODE IS `INPUT`, NOT `I-O`, AND THAT IS NOT A TRANSCRIPTION SLIP.
    # `Initialise-Main` opens I-O first [irs/irs030.cbl:L1437], then closes and
    # RE-OPENS FOR INPUT so it can walk the whole file to build the description
    # search table [irs/irs030.cbl:L1480-L1481]::
    #
    #     1480      perform  acasirsub1-Close.
    #     1481      perform  acasirsub1-Open-Input.
    #
    # and it never reverts to I-O.  `Main-Loop` is entered with the file open for
    # INPUT, and option 66 performs the migrated section from there
    # [irs/irs030.cbl:L603].  So the four rewrites the section issues run
    # against a file opened for input - which succeeds, because the handler
    # tests `access-type` on START ONLY [common/acasirsub1.cbl:L525] and its
    # `aa090-Process-Rewrite` [common/acasirsub1.cbl:L627-L635] issues a bare
    # `rewrite Record-1` with no mode test at all.  Opening I-O here "because a
    # rewrite needs it" would be a fix, not a migration, and rule R-4 forbids it.
    #
    # THE CLOSE IS PER PROGRAM INVOCATION.  The frozen close is
    # [irs/irs030.cbl:L589], inside `Main-Loop-Clear`, guarded by `if w = zero`
    # - the operator pressing Return to leave the menu - and followed by `go to
    # Main-Exit`::
    #
    #      589      perform acasirsub1-Close        *> call-irsub1
    #      590      go to Main-Exit.
    #
    # One `run` call is one complete invocation of this program's posting
    # operation, so the close belongs at the end of `run`.  It is NOT in `EOJ`:
    # the frozen `EOJ` carries the close COMMENTED OUT, with the maintainer's own
    # note saying where it really happens [irs/irs030.cbl:L1710]::
    #
    #     1710  *>    perform  acasirsub1-Close.                    *> Closed at EOJ
    #
    # which is why the migrated `EOJ` issues none and this boundary does.  On the
    # `goback` path below no close happens at all, exactly as the frozen program
    # leaves it - see the note on the `except` clause.
    try:
        # 1481  perform  acasirsub1-Open-Input.
        facade.acasirsub1_open_input(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
            ),
        )
        #  603  perform Ledger-Postings-Add.
        _ledger_postings_add(ws)
        #  589  perform acasirsub1-Close        *> call-irsub1
        #       Reached only when the open and the section both ran to
        #       completion, because the frozen `goback` below abandons
        #       `Main-Loop` and so never reaches L589 either.  This is why the
        #       close is in the success path and NOT in a `finally`.
        facade.acasirsub1_close(
            facade.FacadeContext(
                ws.ws_system_record,
                ws.ws_irsnl_record,
                ws.file_access,
                ws.file_defs,
                ws.dal_common,
            ),
        )
    except facade.FacadeGoback:
        # THE COPYBOOK'S `goback` DISPOSITION.
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] is a `goback` at the
        # end of the shared `Open-Error-Continued` paragraph, and a `goback`
        # returns from the PROGRAM - so in `irs030` it ends `irs030` and hands
        # control back to the IRS menu.  Its Python counterpart is
        # `FacadeGoback`, which must therefore be absorbed HERE, at the program
        # boundary, and turned into the same normal subprogram return.  Letting
        # it escape `run` would propagate a condition the frozen program cannot
        # propagate, and would change the caller's disposition.
        #
        # Exactly three call sites in this program can raise it, being the three
        # whose facade paragraphs perform an error check
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140, L175-L179,
        # L142-L146]: the `acas008-Open-Input` at the head of the section
        # [irs/irs030.cbl:L1578], the `acasirsub1-Open-Input` above, and the
        # `acas008-Open-Output` that clears the transfer file at end of job
        # [irs/irs030.cbl:L1723].  The read-indexed, rewrite, write and close
        # verbs the section uses carry no check and cannot raise.
        #
        # NO CLOSE IS ADDED ON THIS PATH, and the omission is deliberate: each
        # check paragraph performs its OWN handler close before reaching the
        # shared abort - `perform acasirsub1-Close`
        # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L337] and `perform
        # acas008-Close` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L330] - so the
        # failing handler is already closed.  A second close here would be a
        # statement the frozen program does not execute.  The nominal ledger is
        # left as the frozen program leaves it, which after an `acas008` abort
        # means still open: `goback` skips L589, and rule R-4 keeps that.
        #
        # Recorded at debug because it is a disposition and not a diagnostic -
        # `Open-Error-Continued` has already logged FS-Reply, WE-Error, SQL-Err
        # and SQL-Msg at error level, and the `goback` itself displays nothing.
        _LOG.debug(
            "irs030: returning to caller via the goback at "
            "[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]; FS-Reply=%s "
            "WE-Error=%s",
            ws.file_access.fs_reply,
            ws.file_access.we_error,
        )
        return


# --- STRUCTURAL NOTES -------------------------------------------------------
#
# S-1  THE FACADE MODULE, NOT ITS SYMBOLS.  `copy "Proc-ZZ100-ACAS-IRS-Calls.cob"`
#      [irs/irs030.cbl:L1732] is a textual inclusion of a whole paragraph set, so
#      its Python counterpart is the module, imported as a module.  Nothing is
#      imported FROM it by name, which also keeps this module's import-time
#      coupling to a single edge.
#
# S-2  THE FACADE ARGUMENT LIST.  Each verb is called with the five operands the
#      copybook's own CALL list supplies, in its order
#      [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L22-L86]:
#
#          CALL "<handler>" USING WS-System-Record <record> File-Access
#                                 File-Defs ACAS-DAL-Common-data
#
#      which is also the argument order of the already-written handler dispatch
#      functions, so the two agree and a reviewer can diff the lists.  The record
#      operand differs per handler and is the one that handler owns: the transfer
#      record for `acas008`, the nominal-ledger record for `acasirsub1`, the
#      defaults record for `acasirsub3`, the internal posting record for
#      `acasirsub4`.  See AMBIGUITY Q-24.
#
# S-3  RETURN VALUES ARE IGNORED BY DESIGN.  A facade verb in the IRS convention
#      is a PERFORM of a paragraph, and a paragraph returns nothing; the reply
#      reaches the caller only through the `File-Access` block.  Every status test
#      in this module therefore reads `fs_reply` or `we_error` from that block
#      after the call, exactly as the frozen program does, and no verb's return
#      value is inspected.  That is both the faithful reading and the robust one.
#
# S-4  THE TWO GROUP MOVES.  `move WS-IRSNL-Record to nl31-record` and its three
#      siblings are group moves between identically laid-out records, which is a
#      byte-image copy.  The storage-class layer that would build those byte
#      images is outside this module's permitted imports, so the copy is realised
#      field for field through the MOVE verb, each field carrying its own
#      descriptor on both sides.  For identical layouts the two are exactly
#      equivalent: with sender and receiver descriptors equal, no truncation, no
#      padding and no class conversion can occur on any field.
#
# S-5  THE `we-error = 2` CONSTANT IS MODULE-PRIVATE, AND HAS TO BE.  The status
#      layer's error vocabulary deliberately omits the IRS handler's `1+`, `2+`
#      and `3+` codes - they are open-ended ranges local to one handler's prose
#      rather than members of the shared vocabulary, and rule R-3 forbids
#      extending that vocabulary to admit them.  The handler module that does
#      publish the pair is barred by the layering rule.  The value is therefore
#      bound once, here, to its authoritative locator
#      [common/acasirsub1.cbl:L87], and never written as a bare literal at either
#      test site.
#
# S-6  FOUR MODULE-PRIVATE DESCRIPTORS.  `Post-Record-Cnt`, `nl31-dr`, `nl31-cr`,
#      `nl32-dr` and `nl32-cr` are declared in `irs030`'s own WORKING-STORAGE, so
#      the generated data dictionary - built from the copybooks, the bridge and
#      the schema - has no entry for them.  Rule R-5 still requires provenance,
#      so each is DERIVED from the dictionary descriptor of the field it mirrors
#      byte for byte and re-labelled with its own locator inside the frozen
#      program.  Deriving rather than constructing keeps the storage class out of
#      this module entirely, which is what rule R-2 and the layering rule between
#      them require.
#
# S-7  WORKING STORAGE IS PASSED, NOT GLOBAL.  COBOL working storage is visible to
#      every paragraph, so the paragraph functions here take one explicit holder
#      rather than reading module state.  That preserves the sharing the COBOL
#      relies on while leaving the module free of mutable globals - and therefore
#      safely re-entrant - without introducing concurrency of any kind.
#
# S-8  NO PARAGRAPH BOUNDARY WAS INVENTED.  `Input-Loop` is long because the COBOL
#      paragraph is long.  It was deliberately NOT split into helper functions,
#      because every split would move a `GO TO` class annotation away from the
#      statement it transcribes and would create a function with no COBOL label
#      to trace it to.
#
# S-9  RELATION CONDITIONS.  Numeric relations go through the arithmetic layer's
#      comparator, which compares algebraically after decimal-point alignment as
#      a COBOL relation condition does.  The four alphanumeric relations - the
#      VAT-side tests - use a direct equality: both operands are of equal declared
#      width, `pic xx` against a two-character literal, so the COBOL relation
#      reduces to a byte-wise comparison in the collating sequence, and because
#      the stored side always arrives through the MOVE layer at its declared
#      width no padding asymmetry can arise.
#
#
# --- traceability -----------------------------------------------------------
#
# BOUNDARY
# ========
# `irs/irs030.cbl` is 1733 lines.  THE ONLY LINES MIGRATED HERE ARE:
#
#     L1544-L1554   Net section.                  (incl. Main-Exita.  L1553)
#     L1556-L1567   Gross section.                (incl. Main-Exitb.  L1566)
#     L1569-L1730   Ledger-Postings-Add section.  (the migrated surface)
#     L1732         copy "Proc-ZZ100-ACAS-IRS-Calls.cob".  -> an import
#
# 187 lines of 1733, PLUS EXACTLY TWO MORE STATEMENTS, named here so the count
# stays honest and the reason is not buried at the call site:
#
#     L1481         perform  acasirsub1-Open-Input.   -> at the head of `run`
#     L589          perform  acasirsub1-Close         -> at the tail of `run`
#
# 189 lines of 1733.  Those two are the nominal ledger's OPEN and CLOSE, and
# they are the section's stated precondition rather than an extension of it: the
# section drives an already-open file and says so in a surviving comment at
# L1590, then issues four read-indexed and four rewrite performs through it.
# `run` is the only place in the migrated surface that corresponds to the program
# boundary where the frozen statements sit - L1481 inside `Initialise-Main`,
# performed once at L562, and L589 inside `Main-Loop-Clear`, performed when the
# operator leaves the menu.  NOTHING ELSE from either of those out-of-scope
# paragraphs is reproduced.
#
# Everything else in the program is out of scope.  The six
# named out-of-scope sections, with their line numbers, are:
#
#     Init-Main         section  L557    program initialisation and screen setup
#     Input-Headings    section  L1239   screen headings
#     Date-Validate     section  L1285   interactive date validation
#     Initialise-Main   section  L1402   further initialisation
#     Show-Default      section  L1504   default display
#     file-init         section  L1518   file initialisation
#
# together with EVERY screen section, ACCEPT loop, amendment dialog and
# data-entry paragraph in L1-L1543 other than `Net` and `Gross`.
#
#
# PROGRAM -> MODULE
# =================
#     irs/irs030.cbl  Ledger-Postings-Add (+ Net, Gross)  ->  this module
#
#
# PARAGRAPH -> FUNCTION            (all NINE in-scope labels, in source order)
# =====================
#     Net section.                 L1544  ->  _net_section
#     Main-Exita.                  L1553  ->  _net_main_exita
#     Gross section.               L1556  ->  _gross_section
#     Main-Exitb.                  L1566  ->  _gross_main_exitb
#     Ledger-Postings-Add section. L1569  ->  _ledger_postings_add
#     Input-Loop.                  L1619  ->  _input_loop
#     EOJ.                         L1702  ->  _eoj
#     EOJ-q1.                      L1715  ->  _eoj_q1
#     main99-exit.                 L1729  ->  _main99_exit
#
# Every label has a function, including the two plain-`EXIT` paragraphs whose
# bodies do nothing, per rule R-5 and the plan's requirement that a paragraph
# retain a named function even where its `GO TO` becomes a `continue`, a `break`
# or a `return`.
#
# Two further module-private functions carry no COBOL label and are named as
# statements rather than paragraphs, so that no invented paragraph appears above:
#     _move_nl_record_to_snapshot   <-  move WS-IRSNL-Record to nl31/nl32-record
#     _move_snapshot_to_nl_record   <-  move nl31/nl32-record to WS-IRSNL-Record
# plus `_index`, a descriptor-lookup helper that transcribes no statement at all.
#
#
# STATEMENT -> CALL SITE
# ======================
#   facade verbs, handler-named throughout - the entity-named vocabulary is
#   never used, because this program copies the IRS convention:
#     L1578  acas008-Open-Input        ->  facade.acas008_open_input
#     L1586  acasirsub3   (bare form)  ->  facade.acasirsub3
#     L1596  acasirsub1-Read-Indexed   ->  facade.acasirsub1_read_indexed
#     L1606  acasirsub1-Read-Indexed   ->  facade.acasirsub1_read_indexed
#     L1617  acasirsub4-Open           ->  facade.acasirsub4_open
#     L1620  acas008-Read-Next         ->  facade.acas008_read_next
#     L1629  acasirsub1-Read-Indexed   ->  facade.acasirsub1_read_indexed
#     L1641  acasirsub1-Rewrite        ->  facade.acasirsub1_rewrite   (A-4)
#     L1647  acasirsub1-Read-Indexed   ->  facade.acasirsub1_read_indexed
#     L1657  acasirsub1-Rewrite        ->  facade.acasirsub1_rewrite
#     L1673  acasirsub4-Write          ->  facade.acasirsub4_write
#     L1705  acasirsub1-Rewrite        ->  facade.acasirsub1_rewrite   (A-5)
#     L1708  acasirsub1-Rewrite        ->  facade.acasirsub1_rewrite   (A-5)
#     L1711  acasirsub4-Close          ->  facade.acasirsub4_close
#     L1712  acas008-Close             ->  facade.acas008_close
#     L1723  acas008-Open-Output       ->  facade.acas008_open_output  (delete-all)
#     L1724  acas008-Close             ->  facade.acas008_close
#
#   arithmetic - the complete in-scope census is EIGHT distinct statements at
#   THIRTEEN sites, of which exactly TWO are ROUNDED.  By verb: two COMPUTEs,
#   one SUBTRACT and ten ADDs:
#     L1551        compute .. rounded    ->  arithmetic.compute  [ROUNDED store]
#     L1562-L1563  compute .. rounded    ->  arithmetic.compute  [ROUNDED store]
#     L1564        subtract              ->  arithmetic.subtract_from   (truncates)
#     L1623        add 1                 ->  arithmetic.add_to          (truncates)
#     L1635        add amount to nl-dr   ->  arithmetic.add_to
#     L1637        add vat    to nl-dr   ->  arithmetic.add_to
#     L1653        add amount to nl-cr   ->  arithmetic.add_to
#     L1655        add vat    to nl-cr   ->  arithmetic.add_to
#     L1671        add 1 to next-post    ->  arithmetic.add_to
#     L1687        add vat to nl31-cr    ->  arithmetic.add_to
#     L1691        add vat to nl31-dr    ->  arithmetic.add_to
#     L1695        add vat to nl32-cr    ->  arithmetic.add_to
#     L1699        add vat to nl32-dr    ->  arithmetic.add_to
#   There is no ON SIZE ERROR, no REMAINDER, no DIVIDE verb and no MULTIPLY verb
#   anywhere in the in-scope region.
#
#   relation conditions - each reads its OWN status field; the protocol is mixed
#   and the two fields are never unified:
#     L1579  FS-Reply not = zero          ->  compare(fs_reply,  SUCCESS)     != 0
#     L1597  we-error not = zero          ->  compare(we_error,  SUCCESS)     != 0
#     L1607  we-error not = zero          ->  compare(we_error,  SUCCESS)     != 0
#     L1621  FS-Reply = 10                ->  compare(fs_reply,  END_OF_FILE) == 0
#     L1630  we-error = 2                 ->  compare(we_error,  2)           == 0
#     L1648  we-error = 2                 ->  compare(we_error,  2)           == 0
#     L1674  we-error not = zero          ->  compare(we_error,  SUCCESS)     != 0
#     L1682  Vat-AC-Def = zero            ->  compare(vat_ac_def, 0)          == 0
#     L1685  Vat-AC-Def = 31              ->  compare(vat_ac_def, 31)         == 0
#     L1689  Vat-AC-Def = 31              ->  compare(vat_ac_def, 31)         == 0
#     L1693  Vat-AC-Def = 32              ->  compare(vat_ac_def, 32)         == 0
#     L1697  Vat-AC-Def = 32              ->  compare(vat_ac_def, 32)         == 0
#     L1636  post-vat-side = "CR"         ->  == "CR"   (equal-width, byte-wise)
#     L1654  post-vat-side = "DR"         ->  == "DR"
#     L1686  Post-Vat-Side = "CR"         ->  == "CR"
#     L1690  Post-Vat-Side = "DR"         ->  == "DR"
#     L1694  Post-Vat-Side = "CR"         ->  == "CR"
#     L1698  Post-Vat-Side = "DR"         ->  == "DR"
#     L1718  WS-Reply not = "Y" and not = "N"  ->  collapsed; see class 4 below
#
#   MOVE - the nine posting-record moves plus the key allocation, the four
#   account-key stores, the four sub-nominal zeroings, the function-code store
#   and the two group moves.  All go through the MOVE layer; none is a Python
#   assignment of a converted value.
#
#
# `GO TO`                (the in-scope region has exactly TEN transfer sites)
# =======
#   Class 1 - loop back  ->  `continue` inside the `while True:` of _input_loop
#     L1634  -> Input-Loop   the CLEAN SKIP when the debit account is missing
#     L1652  -> Input-Loop   A-4's half-posted abandon
#     L1683  -> Input-Loop   the zero-VAT-account guard, skipping the ladder
#     L1700  -> Input-Loop   the normal end of an iteration
#
#   Class 2 - forward terminator  ->  `break`, PLUS the post-loop block
#     L1622  -> EOJ  L1702   normal end of file
#     L1678  -> EOJ  L1702   the write-failure jump
#   The post-loop block is `_eoj` then `_eoj_q1` then `_main99_exit`, performed by
#   `_ledger_postings_add` after `_input_loop` returns.  It carries the two
#   VAT-snapshot rewrites, the three closes and the conditional table truncation,
#   so a `break` alone would silently drop the section's most consequential
#   database effects.  BOTH class-2 sites reach it; the three class-3 sites below
#   skip it.  The split is exact.
#
#   Class 3 - section exit  ->  `return`
#     L1581  -> main99-exit  L1729    transfer file would not open
#     L1601  -> main99-exit  L1729    VAT control account 31 would not read
#     L1611  -> main99-exit  L1729    VAT control account 32 would not read
#   All three bypass `EOJ` entirely: no snapshot rewrite, no close, no
#   truncation.  This is the ABORT-WITH-NOTHING disposition.
#
#   Class 4 - sibling re-dispatch  ->  named paragraph + explicit transfer
#     L1719  -> EOJ-q1  L1715
#   Classified 4 rather than 1 because it re-dispatches to the head of its own
#   paragraph as an input-acquisition retry, and because the paragraph it
#   re-enters GATES A DATABASE WRITE - the transfer-table truncation - so it
#   cannot be dismissed as presentation.  The per-site equivalence proof is in
#   `_eoj_q1`'s docstring: the retry mutates nothing but `WS-Reply`, performs no
#   database operation, and terminates only when `WS-Reply` is one of exactly two
#   values; supplying that already-validated two-valued answer as a parameter
#   makes the loop's post-condition true on entry, so the body is unreachable and
#   the transfer collapses with nothing observable lost.
#
#   `PERFORM ... THRU` DOES NOT OCCUR IN THE IN-SCOPE REGION - see CITATION
#   CORRECTIONS.
#
#
# ANOMALY REGISTER (rule R-4)                     - reproduced, never fixed
# ===========================
#   A-4   THE HALF-POSTED DOUBLE ENTRY.
#         Sites annotated: L1641 (the debit commits), L1652 (the abandon).
#         The debit is rewritten before the credit account is looked up at
#         L1647, so a missing credit leaves an unbalanced debit, no credit and
#         no internal posting row - the posting write is at L1673, past the
#         abandoned point.  Compounded by the rewrite verb having neither a
#         facade check nor an inline test.
#         NOT fixed: the rewrite stays where it is, no rollback is added and the
#         credit account is not pre-validated.
#
#   A-5   THE LOST UPDATE ON THE TWO VAT CONTROL ACCOUNTS.
#         Sites annotated: L1602, L1612 (the snapshots), L1704/L1705 and
#         L1707/L1708 (the rewrites from them), plus the ladder at L1685-L1699
#         which accumulates into the snapshots rather than the live rows.
#         Any in-loop rewrite of account 31 or 32 is silently discarded at end
#         of job.
#         NOT fixed: the accounts are not re-read, the snapshots are not merged
#         with the live rows and the collision is not detected.
#
#   A-19  SUPERSEDED COMMENTED-OUT VARIANTS OF BOTH VAT COMPUTES.
#         Sites annotated: L1550, L1561.  Both dead lines reference a differently
#         named rate field `vat` where the live statements reference
#         `WS-Vat-Current`.  Both are carried into this module verbatim as
#         comments beside their live translations, together with the maintainer's
#         uncertainty note at L1547-L1548.  Carrying them IS the reproduction.
#         NOT fixed: neither dead line is deleted and the note is not acted on.
#
#   THE WRITE-FAILURE JUMP.
#         Site annotated: L1674-L1678.  It transfers to `EOJ`, not to
#         `Input-Loop`, and `EOJ` still performs both snapshot rewrites and all
#         three closes, so the partial state is COMMITTED.
#         NOT fixed: no rollback, no retry, and none of the end-of-job work is
#         skipped.
#
#   Anomalies owned ELSEWHERE that touch this section, noted so a reader does
#   not expect them here:
#     A-6  the transfer-file handler rejects read-indexed, rewrite, start and
#          delete unconditionally, so its published rewrite verb can never
#          succeed.  This section calls none of those four verbs, which is why
#          it works.  Owned by the transfer-file handler module.
#     A-7  the internal posting bridge derives three date-component columns that
#          exist in no copybook.  This section's only contribution is the date
#          move at L1662, which is the field that rule reads.  Owned by the
#          internal posting handler module.
#
#
# FINDING LIST                       - recorded, not acted on
# ============
#   F-1  L1579-L1581 IS UNREACHABLE-WHEN-TRUE.  `acas008-Open-Input` already
#        performs `acas008-Check-4-Errors`, whose predicate is identical
#        [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140]; on failure that
#        check hard-returns out of the program, so control never arrives at
#        L1579, and on success FS-Reply is zero.  Kept regardless, because rule
#        R-3 forbids removing a predicate the compiled program contains.
#   F-2  THERE IS NO `acasirsub4-Check-4-Errors`.  The copybook declares five
#        error-check paragraphs for six dispatched handlers.  That absence is why
#        L1674 must test inline, and why the failed open at L1617 is silently
#        ignored.
#   F-3  `acasirsub1-Rewrite` has neither a facade check nor an inline test at
#        any of its four sites, so a failed rewrite is silently ignored.  This
#        compounds A-4.
#   F-4  A MIXED STATUS PROTOCOL.  Two sites read FS-Reply, five read we-error.
#        Never unified.
#   F-5  THE `we-error = 2` PREDICATE IS AN EQUALITY, not "not = zero", so any
#        other non-zero error falls through into the accumulate.  Not widened.
#   F-6  THE VAT SIDE IS APPLIED INVERTED.  L1636-L1637 adds VAT to the DEBIT
#        accumulator when the side is "CR"; L1654-L1655 adds it to the CREDIT
#        accumulator when the side is "DR".  Not corrected.
#   F-7  THE LADDER HAS NO FINAL `else`.  A VAT account that is non-zero but
#        neither 31 nor 32 accumulates nowhere and nothing is reported.  No
#        `else` and no diagnostic added.
#   F-8  `next-post` IS INCREMENTED BEFORE THE WRITE (L1671 before L1673), so the
#        allocator advances even when the write fails.  Ordering preserved.
#   F-9  FIELD-NAME CASE INCONSISTENCY.  The VAT side is spelled
#        `ws-irs-post-vat-side` (L1636), `WS-irs-post-vat-side` (L1654) and
#        `WS-IRS-Post-Vat-Side` (L1686).  COBOL is case-insensitive; recorded, not
#        propagated.
#   F-10 `EOJ-q1.` IS WRITTEN AT COLUMN 1 (L1715), unlike every other label in
#        the section, which are indented one column.  A formatting oddity only.
#   F-11 `Main-Exita.` AND `Main-Exitb.` ARE PLAIN `EXIT`s, not `EXIT SECTION`,
#        and their `a`/`b` suffixes make them distinct labels - unlike the
#        repeated `main-exit` of the Sales and Purchase programs.  Both retain a
#        named function anyway.
#   F-12 THE SNAPSHOT DECLARATIONS DIVERGE FROM THE COPYBOOK in two ways:
#        `nl31-type`/`nl31-ac` are `pic a` where the copybook has `pic x`, and
#        the snapshots carry no `filler redefines NL-Data` and therefore no
#        `NL-Pointer`.  Byte widths are identical, so the group move is still an
#        exact byte copy.  See `_NlSnapshot` and STRUCTURAL NOTE S-4.
#   F-13 THE MAINTAINER'S OWN UNCERTAINTY NOTE at L1547-L1548 asks whether the
#        VAT compute needs a non-zero-rate test.  Recorded; no test added.
#   F-14 THE CREDIT AND DEBIT MOVES AT L1663-L1664 ARE IN THE OPPOSITE ORDER to
#        the two legs that were posted at L1627-L1657.  Transcribed in source
#        order; harmless, but a reader diffing will notice.
#   F-15 THE TRANSFER FILE IS CLOSED AT L1712 AND REOPENED AT L1723 purely so
#        that opening it for output can truncate it, then closed again at L1724.
#        Both calls reproduced, in order.
#   F-16 THREE DISTINCT REJECTION DISPOSITIONS coexist in this one section and
#        leave three different database states: CLEAN SKIP (L1634 - nothing
#        written), COMMIT-AND-STOP (L1678 - partial state committed, end-of-job
#        work still performed) and ABORT-WITH-NOTHING (L1581/L1601/L1611 - no
#        rewrite, no close, no truncation).  Implemented separately; a single
#        generic rejection path would not reproduce them.
#   F-17 REPEATED WORK LEFT UNOPTIMISED.  The two VAT accounts are fetched by two
#        separate indexed reads with the sub-nominal zeroing written out twice,
#        and `nl-sub-nominal` is re-zeroed before all four lookups.  An optimiser
#        would collapse these; performance work is out of scope by construction.
#   F-18 THE FOUR REWRITES RUN THROUGH A FILE OPENED FOR *INPUT*, and the
#        handler lets them.  `Initialise-Main` opens the nominal ledger I-O at
#        L1437, then closes it at L1480 and RE-OPENS IT FOR INPUT at L1481 so it
#        can walk the whole file, and never reverts; `Main-Loop` and therefore
#        this section run from that INPUT state.  It works because
#        `common/acasirsub1.cbl` tests `access-type` on START ONLY
#        [common/acasirsub1.cbl:L525] and `aa090-Process-Rewrite`
#        [common/acasirsub1.cbl:L627-L635] issues a bare `rewrite Record-1` with
#        no mode test whatsoever.  Reproduced as measured: `run` opens INPUT.
#        Opening I-O instead "because a rewrite needs it" would be a fix, and
#        rule R-4 forbids fixes.  Compounds F-3, which records that a failed
#        rewrite is never tested for at any of its sites.
#
#
# CITATION CORRECTIONS
# ====================
#   C-1  THE UN-ROUNDED SUBTRACT IS AT L1564, NOT L1565.  The migration plan's
#        arithmetic census cites `subtract vat-amount from post-amount` at L1565;
#        measured against the frozen source it is at L1564, and L1565 is a
#        comment line.
#   C-2  THE SECTION ENDS AT L1730, NOT L1733.  The plan gives the boundary as
#        L1569-L1733.  L1730 is `exit section.`, the last executable line; L1731
#        is a comment, L1732 is the facade `COPY` and L1733 is a comment.
#        L1569-L1730 is the code boundary used throughout this module.
#   C-3  `PERFORM ... THRU` IS OUT OF SCOPE HERE.  The plan counts three such
#        sites in `irs030`, at L813, L831 and L832.  All three lie in
#        interactive code outside this module's stated boundary, so the in-scope
#        region contains ZERO `PERFORM ... THRU` and none is transformed.
#   C-4  THE FIFTH IN-SCOPE `COMPUTE` IS OUT OF SCOPE HERE.  The arithmetic
#        layer's own documentation counts `compute u-bin = u-year * 365` at L1362
#        among the cycle's live COMPUTE statements.  It sits in the out-of-scope
#        `Date-Validate` region and is not reproduced by this module.
#   C-5  THE PLAN'S "FIVE ROUNDED SITES" ARE FOUR ROUNDED COMPUTES PLUS ONE
#        ROUNDED DIVIDE.  Two of the four computes are this module's, at L1551 and
#        L1562-L1563; the other two belong to the batch control-total gate and the
#        fifth site is a divide in the end-of-cycle program.  Stated so that
#        "five ROUNDED COMPUTEs" is not inferred.
#
#
# OMISSIONS               - deliberate, so that nothing looks lost by accident
# =========
#   O-1  THE SIX OUT-OF-SCOPE SECTIONS, BY NAME AND LINE, plus every screen
#        section and ACCEPT loop in L1-L1543 other than `Net` and `Gross`.  See
#        BOUNDARY above for the list.  This is the largest omission in this
#        module and the one most likely to be mistaken for a gap: 1544 of the
#        program's 1733 lines are simply not part of this migration.
#        THE TWO EXCEPTIONS ARE NAMED IN BOUNDARY ABOVE and are the only
#        statements taken from outside the three in-scope sections: the
#        `acasirsub1-Open-Input` at L1481 and the `acasirsub1-Close` at L589.
#        `Initialise-Main`'s screen work, its CoA search-table build, its
#        VAT-account existence sweep, its VAT-rate load and its I-O open at L1437
#        are all still omitted, and none is needed - the section reloads both VAT
#        accounts itself at L1594-L1612.
#   O-2  FURTHER CONSTRUCTS EXCLUDED BY NAME, all outside the boundary and
#        therefore NOT reproduced: the eight sign flips at L947, L963, L1096,
#        L1125, L1127, L1139, L1141 and L1179; the amount scaling at L1074, L1077
#        and L1083; the leap-year divide-then-multiply at L1333-L1334; the
#        day-count computation at L1362; and the three `PERFORM ... THRU` sites
#        at L813, L831 and L832.
#        CONSEQUENCE, stated explicitly so no reader goes hunting: THIS MODULE
#        HAS ZERO IN-SCOPE SIGN FLIPS, ZERO `PERFORM ... THRU`, ZERO PERIOD-TOTAL
#        WRITES and ZERO IRS FAN-OUT TESTS.
#   O-3  `display ... at` STATEMENTS BECOME LOG RECORDS.  They must not alter
#        control flow and must not appear in any table dump, and none does:
#        L1580, L1598-L1599, L1608-L1609, L1616, L1631-L1632, L1649-L1650,
#        L1675-L1676 and L1714.  Two carry no content at all and are dropped
#        rather than logged: L1713 and L1727, both bare screen erases.  L1725 is
#        dropped with its accept - see O-4.
#   O-4  `accept WS-Reply` ACKNOWLEDGEMENT PAUSES ARE DROPPED: L1600, L1610,
#        L1633, L1651, L1677 and L1726.  Their only effect is to block a
#        terminal.  BUT EVERY CONTROL TRANSFER THAT FOLLOWS ONE IS PRESERVED -
#        L1601, L1611, L1634, L1652 and L1678 - because only the pause is
#        presentation; the transfer is behaviour.
#   O-5  `accept WS-Reply` AT L1717 IS NOT DROPPED.  It gates a database write -
#        the transfer-table truncation - so it becomes the explicit
#        `clear_posting_file` parameter of `run`.  ITS `True` DEFAULT IS A
#        SIGNATURE CONTRACT from this module's file brief and NOT a COBOL default:
#        the frozen prompt has none, because the `[Y]` at L1716 is prompt text, the
#        accept at L1717 carries no `WITH UPDATE`, `WS-Reply` is never set to `"Y"`
#        anywhere in the program, and L1718-L1719 re-prompt on anything else.  Every
#        caller passes the value explicitly, so the default is never consulted;
#        acas_posting/cli/irs_post.py requires the answer (finding CLI-05).
#   O-6  `copy "screenio.cpy"` (L344) and `copy "envdiv.cob"` (L197) map to
#        nothing.  Both are representation only: a screen-section vocabulary and
#        an environment division fragment, neither of which has a Python
#        counterpart.  Note the first is spelled `.cpy`, not `.cob`.
#   O-7  THE MESSAGE IDENTIFIERS `IR031`, `IR032`, `IR033`, `IR03A`, `IR03B` and
#        `IR914` ARE RETAINED ONLY AS LOG TEXT, verbatim.  `IR916` and `SY008` are
#        the facade's own and belong to it, not here.
#   O-8  `Post-Record-Cnt` IS MAINTAINED BUT REACHES NO TABLE.  It exists solely
#        to feed the completion message at L1714, and is kept because that log
#        line consumes it.
#   O-9  `WS-Reply` ITSELF IS NOT MODELLED.  Every one of its uses is either a
#        dropped pause or the parameter of O-5.
#   O-10 ABSENCES WORTH STATING POSITIVELY, because a reader familiar with the
#        sibling modules will look for them and find nothing:
#          - NO `call "..."` OF ANY KIND in the in-scope region.  No operating
#            system spool-out, no date-module call, no library routine.  This
#            module therefore needs no runtime escape hatch at all.
#          - NO print file and no report formatting whatsoever.
#          - NO work file.  The General Ledger phases hand data through two
#            scratch files; this section hands on nothing.
#          - NO date conversion.  `irs030` does not copy the date-conversion
#            interface copybook, and the posting date is carried through
#            unconverted at L1662.
#          - NO clock read and NO date parameter.  See the module docstring.
#          - NO facade stub block.  One General Ledger program declares unused
#            facade stubs to satisfy the linker; `irs030` declares none.
#          - NO period-total write.  All nine in the migration belong to the
#            Sales and Purchase programs.
#          - NO IRS fan-out test.  This IS the IRS side of the fan-out.
#          - NO 88-level condition-name test.  Every relation in the region is a
#            direct comparison, which is why the condition-name layer is not
#            imported.
#          - NO anomaly A-22.  The wrapper-section naming inconsistency that
#            anomaly records belongs to a General Ledger program.
#
# --- end traceability -------------------------------------------------------
