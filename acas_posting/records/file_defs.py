"""The `File-Defs` record: the file names the ACAS cycle is handed.

This module declares NAMES. It reaches no file system, holds no handle and
creates nothing on disk. `File-Defs` is a block of 58 fixed-width name fields,
a 58-element table redefining them, a declared element count and a
one-character delimiter - every one an item of WORKING STORAGE that a calling
program fills in and passes along.

WHY THIS RECORD MATTERS
=======================
`File-Defs` is present in EVERY in-scope linkage: the fourth parameter of the
General / Sales / Purchase shape [general/gl071.cbl:L161-L164], the third of
the IRS shape, which takes neither the calling-data block nor the run date
[irs/irs030.cbl:L552-L554], and the fourth argument of every file-handler
call, which section 0.4.3 states as a transformation pair::

    call "acas007" using System-Record WS-Batch-Record File-Access
                         File-Defs ACAS-DAL-Common-Data
    ->  acas007_gl_batch.dispatch(system, batch, file_access, file_defs,
                                  dal_common)

Section 0.4.1.3 names this file's source and content verbatim -
"`acas_posting/records/file_defs.py` | CREATE | `copybooks/wsnames.cob` | File
names plus the two work-file names" - and its folder mandate requires each
`05`/`03` field to become an attribute whose descriptor is looked up in the
generated dictionary, with oddities in the source preserved rather than fixed.
That last clause is restated rather than quoted, because the plan's own
wording uses one of the very terms rule R-4 bans from this codebase.

WHERE THE COPYBOOK ACTUALLY LIVES - THIRTY-THREE FILES, NOT ONE
===============================================================
Two line-citation facts have to be stated plainly, because a reader following
the plan's own locators will otherwise look in the wrong place.

FIRST, A CITATION CORRECTION. Sections 0.3.1 and 0.4.1.3 both cite the two
work-file names as `[copybooks/wsnames.cob:L14-L17]`. Read against the frozen
source the span is `L13-L16`: the `01` group head is at L13, the `02
file-defs-a` group at L14, and the two work-file names at L15 and L16. L17 is
not a declaration at all - it is the first `copy` statement. The corrected
span is used throughout this module and is recorded here so that the
traceability document a later boundary writes picks up the real one.

SECOND, ONLY 26 OF THE 58 ELEMENTS ARE DECLARED IN `wsnames.cob` AT ALL. The
copybook pulls the other 32 in one per file::

    L15   03  pre-trans-name   pic x(532)  value "pretrans.tmp". *> gl071
    L16   03  post-trans-name  pic x(532)  value "postrans.tmp". *> gl071
    L17    copy "file00.cob".    *> "system"
    L18   *>                        No file 1
    L19    copy "file02.cob".    *> "archive".
          (L20-L49, thirty more copy statements and the second gap marker)
    L50    copy "file33.cob".    *> "cheque.dat"
    L51   03  file-34          pic x(532)  value "irsacnts.dat".
          (L52-L77, the rest of the IRS run and the payroll run)
    L78     03  file-57          pic x(532)  value "pycal.dat".
    L80   02  filler         redefines file-defs-a.
    L81       03  System-File-Names   pic x(532) occurs 58.
    L82   02  File-Defs-Count         binary-short value 58.
    L83   02  File-Defs-os-Delimiter  pic x.

Each `copybooks/fileNN.cob` is a ONE-LINE file holding the whole declaration,
so the true locator of those 32 elements is `copybooks/fileNN.cob:L1` and the
`wsnames.cob` line is the INCLUSION site. Both are carried in the comment
beside every such attribute, because a reader diffing this module against
`wsnames.cob` alone would find 32 of its 58 attributes unaccounted for. The
generated dictionary already models this correctly and the loader says so
itself: a record name may be declared by more than one copybook, "`File-Defs`
by thirty-three of them".

One consequence for anyone extending this module: because the record spans 33
copybooks, `loader.entries_for_copybook_record("File-Defs")` returns its 64
entries GROUPED BY FILE rather than in declaration order. Declaration order is
stated here, by the order of the attributes themselves, and is never taken
from that accessor.

FIFTY-EIGHT ELEMENTS, AND WHY THE COUNT IS LOAD-BEARING
=======================================================
    2   the two work-file names               [copybooks/wsnames.cob:L15-L16]
 + 24   file-0, then file-2 .. file-24        included at L17-L41
 +  8   file-26 .. file-33                    included at L43-L50
 +  5   file-34 .. file-38                    inline at L51-L55
 + 19   file-39 .. file-57                    inline at L58-L78
 ----
   58   =  `occurs 58` [copybooks/wsnames.cob:L81]
         =  `File-Defs-Count binary-short value 58` [:L82]

The count is not bookkeeping. The redefining table addresses the same storage
as the 58 named elements, so an element added, dropped or renumbered would
silently shift every subscript after it. The two numbers in the copybook and
the 58 attributes below must agree, and the maintainer's own comment on L82
says as much: "MUST be the same as above occurs".

THE REDEFINES - THE CENTRAL DESIGN DECISION
===========================================
    02  filler         redefines file-defs-a.               [:L80]
        03  System-File-Names   pic x(532) occurs 58.       [:L81]

This is not decoration: it is how the file handlers address the block, and the
two work-file names are elements 1 and 2 of that table.

Python has NO STORAGE ALIASING. There is therefore no way to make one object
be both views at once, and no attempt is made to fake it. The relationship is
recorded as METADATA ON DESCRIPTORS - `occurs` on the table item, `redefines`
on the group that carries it - and nowhere else. Specifically, and by
deliberate omission: no third merged representation, no accessor projecting
the named elements into the table or back, no subscript helper, and no
post-initialisation hook keeping the two in step. `SystemFileNamesView` is
this module's name for the group, which is FILLER in the copybook and so has
no name of its own; the dictionary keys it `File-Defs.filler` and this module
follows that spelling.

The REDEFINES and the OCCURS sit at DIFFERENT LEVELS, and the pair is recorded
at the levels the copybook declares them rather than fused onto one
descriptor. `SystemFileNamesView.GROUP` is the `02` group and reports
`redefines == "file-defs-a"`; `SystemFileNamesView.FIELDS[0]` is the `03`
table item and reports `occurs == 58`. Fusing them would contradict the frozen
source and would mean writing metadata by hand instead of looking it up, which
is exactly what rule R-5 exists to prevent.

COBOL `OCCURS` IS 1-BASED; PYTHON INDEXING IS 0-BASED. `System-File-Names (1)`
is `pre-trans-name` and `(2)` is `post-trans-name`, so those two are
`system_file_names[0]` and `[1]` here. The offset is stated rather than hidden:
no 1-based wrapper is provided, because a wrapper would be one more thing
between a reader and the frozen source.

WHAT THIS MODULE DOES NOT DO (RULE R-1)
=======================================
For this module R-1 reaches further than COBOL, because the temptation here is
not a compiler - it is the file system. `pretrans.tmp` and `postrans.tmp` are
STRINGS. They are not created, not looked for, not deleted and not turned into
paths. Section 0.3.1 is explicit about what becomes of them: "Work files are
in-process sequences, not tables and not temporary files", modelled as ordered
sequences in `acas_posting/workfiles.py`. Nothing below touches a file, a
directory, a temporary area, an external process or a foreign function; the
imports are the standard library plus one module of this package.

DESCRIPTOR PROVENANCE - LOOKED UP, NEVER TRANSCRIBED (RULE R-5)
===============================================================
Every descriptor here comes from `FieldDescriptor.from_dictionary_key`, the
only path there is - all 64 of this record's entries are in the generated
artifact, so not one width, level or storage class is typed by hand. Keys follow `<COPYBOOK-RECORD>.<FIELD-NAME>`
with both halves spelled as the frozen source spells them:
`File-Defs.pre-trans-name`, `File-Defs.System-File-Names`,
`File-Defs.File-Defs-os-Delimiter`. Case is not folded and hyphens are not
turned into underscores, so a key built by upper-casing -
`FILE-DEFS.PRE-TRANS-NAME` - matches nothing. Never a bare field name.

Each descriptor carries `dictionary_key` and `source_locator`, and
`FieldDescriptor.cite()` returns the compact three-locator provenance line.
`cite()` is already a pass-through of the loader's own `cite`, so this module
surfaces that primitive through the descriptor and reimplements nothing -
which is also why the loader itself is not imported here. `FIELDS` on each
class is a tuple in declaration order, and `GROUP` is the descriptor of the
group item the class stands for.

ANOMALIES REPRODUCED HERE, NEVER FIXED (RULE R-4)
=================================================
Six oddities of this copybook are carried below, each with its locator at the
site that reproduces it:

  * THE NUMBERING GAPS. There is no `file-1` and no `file-25`. The sequence
    runs file-0, file-2 .. file-24, then jumps to file-26. The copybook says
    so in its own words - "No file 1" [copybooks/wsnames.cob:L18] and "No file
    25" [:L42]. Nothing is renumbered and no placeholder closes the gaps.
  * `file-24` IS SPACES, NOT A FILENAME [copybooks/file24.cob:L1]. It still
    occupies element 26 of the table, and the maintainer's note on its
    inclusion line calls it a "dummy to build file-02" [:L41].
  * THE UNIFORM 532-CHARACTER WIDTH. Every element is `pic x(532)`, however
    short its name - `pay.dat` is eight characters in a field of 532.
  * THE `*> gl071` ANNOTATIONS on both work-file names [:L15-L16], kept
    verbatim. They are the maintainer telling a reader which program owns
    those two files, and section 0.3.1 relies on them.
  * OUT-OF-SCOPE SUBSYSTEM FILENAMES IN AN IN-SCOPE COPYBOOK. The sales and
    purchase autogen names, the stock names, the two payment names and the
    nineteen payroll names belong to subsystems section 0.2.2 excludes. They
    are declared all the same, because the record must mirror the copybook
    field for field and because `occurs 58` counts them. No in-scope code path
    reads them; they are here for layout fidelity.
  * A STALE COMMENT ON THE OCCURS LINE. L81 carries "39 chg for sales BO file
    plus py" beside `occurs 58`, and the copybook's own change log stops
    counting at 39 [:L8-L9] while the count is 58. Left as found.

There is deliberately no "settled", merged or preferential view of any of
this, and none may be introduced. Where the copybook looks wrong it is
reproduced; the register of every such site is the migration's anomaly log.

TYPE DISCIPLINE (R-2), LAYERING (SECTION 0.4.3) AND DETERMINISM (R-6)
=====================================================================
    every `pic x(532)` element        ->  `str`, declared width 532
    `System-File-Names ... occurs 58` ->  a 58-element tuple of `str`
    `File-Defs-Count binary-short`    ->  `int`, signed 16 bits, scale 0
    `File-Defs-os-Delimiter pic x`    ->  `str`, declared width 1

No binary floating-point type appears here and neither does a scaled numeric
carrier: this record holds no money and no quantity. The one number in it is a
declared element count, and `binary-short` makes it an `int` - the storage
class decides, never a reading of what the field "means".

Of the two imports a record module is granted, only `acas_posting.cobol.field`
is needed, so only it is taken. The live temptation is `records/work_records
.py`, and the edge runs ONE WAY: the work files named at L15-L16 are read by
`acas_posting/workfiles.py`, which imports its layouts from that module, so
the dependency is workfiles -> records and never the reverse. An import the
other way would close a cycle and drag the work-file machinery into the
arithmetic test tier, which section 0.4.3 promises "imports only `cobol` and
`records` and touches no database, so it runs anywhere".

Attribute order is copybook declaration order throughout, so this module can
be set beside its copybooks and diffed by eye; fixed collections are tuples.
Nothing consults a clock, draws an unpredictable value or inspects the process
environment, and - the one that matters for this record -
`File-Defs-os-Delimiter` is NOT derived from the host operating system. It is a
declared field whose value the calling program sets, and its default is the
state the copybook's own comment describes as not yet set. The only import-time
work is the descriptor lookup, which reads the committed dictionary once
through the loader's lazy cache, so two imports in two processes produce
identical state. See `acas_posting.records` for the shared conventions.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor

__all__: Final[tuple[str, ...]] = (
    # Sorted, so the export list is stable between runs (rule R-6).
    "FileDefs",
    "FileDefsA",
    "SystemFileNamesView",
)


# The record name half of every dictionary key below, spelled as the
# copybook spells the `01` group it names [copybooks/wsnames.cob:L13].
# Keys are `<COPYBOOK-RECORD>.<FIELD-NAME>` and are case-sensitive.
_DICTIONARY_RECORD: Final[str] = "File-Defs"

# The declared width shared by all 58 elements and by the table that
# redefines them: `pic x(532)`. Named once so the figurative constant on
# `file-24` can be written at the width the copybook gives it - see that
# attribute's own comment. Every descriptor reports the same 532 as its
# `character_length`, taken from the dictionary rather than from here.
_ELEMENT_WIDTH: Final[int] = 532


@dataclass(slots=True)
class FileDefsA:
    """`02  file-defs-a.` [copybooks/wsnames.cob:L14] - the 58 name fields.

    The group the file-name table redefines, and the only place the names
    themselves are declared. One attribute per `03` element, in copybook
    declaration order, each defaulting to that element's own `VALUE`
    clause. Attribute names are the COBOL names with hyphens turned into
    underscores and nothing else changed, so `file-0` is `file_0` - the
    numeral is kept and the elements are NOT renumbered to close the two
    gaps in the sequence.

    The comment above each attribute gives its verbatim COBOL declaration
    and its locator. For the 32 elements pulled in by a `copy` statement
    the declaration locator is the one-line copybook that holds it and the
    inclusion locator is the `wsnames.cob` line that pulls it in; both are
    shown. `element N` is the 1-based `OCCURS` subscript that element has
    in `System-File-Names`, so element 1 is `system_file_names[0]`.

    Mutable on purpose, and NOT frozen: a calling program fills these in
    before it dispatches - the delimiter comment on
    [copybooks/wsnames.cob:L83] describes exactly that, paths being set
    into the block - so this is working storage rather than a value object.

    Nothing pads a value to the declared 532 characters here.
    `acas_posting/cobol/move.py` owns padding, and every descriptor below
    records the declared width for it to work from.
    """

    # Assigned immediately after the class body, because both derive from
    # this class's own declared fields and so cannot be built until the
    # class exists. `GROUP` is the `02 file-defs-a` group itself; `FIELDS`
    # is the 58 element descriptors in declaration order.
    GROUP: ClassVar[FieldDescriptor]
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]]

    # -- the two General Ledger work files -------------------------------
    # Declared inline, and the only two elements the plan cites directly.
    # The `*> gl071` on each is the maintainer's own annotation, kept
    # verbatim: it records which program owns the file. These are NAMES,
    # not files - `acas_posting/workfiles.py` models the work files as
    # ordered in-process sequences and nothing on disk is ever created.

    # element 1.  03  pre-trans-name   pic x(532)  value "pretrans.tmp".
    #             *> gl071                       [copybooks/wsnames.cob:L15]
    pre_trans_name: str = "pretrans.tmp"

    # element 2.  03  post-trans-name  pic x(532)  value "postrans.tmp".
    #             *> gl071                       [copybooks/wsnames.cob:L16]
    post_trans_name: str = "postrans.tmp"

    # -- the 32 elements pulled in one per copybook -----------------------
    # `wsnames.cob` L17-L50 are `copy` statements, not declarations. Each
    # named file below holds its whole `03` line and nothing else.

    # element 3.  03  file-0   pic x(532)  value "system.dat".
    #             [copybooks/file00.cob:L1]  incl. [copybooks/wsnames.cob:L17]
    file_0: str = "system.dat"

    # THE FIRST NUMBERING GAP. There is no `file-1`. The copybook says so
    # itself, in a comment standing where the declaration would be:
    # "No file 1" [copybooks/wsnames.cob:L18]. Not renumbered, and no
    # placeholder element is inserted (rule R-4).

    # element 4.  03  file-2   pic x(532)  value "archive.dat".
    #             [copybooks/file02.cob:L1]  incl. [copybooks/wsnames.cob:L19]
    file_2: str = "archive.dat"

    # element 5.  03  file-3   pic x(532)  value "final.dat".
    #             [copybooks/file03.cob:L1]  incl. [copybooks/wsnames.cob:L20]
    file_3: str = "final.dat"

    # element 6.  03  file-4   pic x(532)  value "slautogen.dat".
    #             [copybooks/file04.cob:L1]  incl. [copybooks/wsnames.cob:L21]
    #             Sales autogen - out of scope per section 0.2.2, declared
    #             for layout fidelity. No in-scope code path reads it.
    file_4: str = "slautogen.dat"

    # element 7.  03  file-5   pic x(532)  value "ledger.dat".
    #             [copybooks/file05.cob:L1]  incl. [copybooks/wsnames.cob:L22]
    file_5: str = "ledger.dat"

    # element 8.  03  file-6   pic x(532)  value "posting.dat".
    #             [copybooks/file06.cob:L1]  incl. [copybooks/wsnames.cob:L23]
    file_6: str = "posting.dat"

    # element 9.  03  file-7   pic x(532)  value "batch.dat".
    #             [copybooks/file07.cob:L1]  incl. [copybooks/wsnames.cob:L24]
    file_7: str = "batch.dat"

    # element 10. 03  file-8   pic x(532)  value "postings2irs.dat".
    #             [copybooks/file08.cob:L1]  incl. [copybooks/wsnames.cob:L25]
    file_8: str = "postings2irs.dat"

    # element 11. 03  file-9   pic x(532)  value "tmp-stock.dat".
    #             [copybooks/file09.cob:L1]  incl. [copybooks/wsnames.cob:L26]
    #             Stock subsystem - out of scope, declared for fidelity.
    file_9: str = "tmp-stock.dat"

    # element 12. 03  file-10  pic x(532)  value "staudit.dat".
    #             [copybooks/file10.cob:L1]  incl. [copybooks/wsnames.cob:L27]
    #             Stock audit - out of scope, declared for fidelity.
    file_10: str = "staudit.dat"

    # element 13. 03  file-11  pic x(532)  value "stockctl.dat".
    #             [copybooks/file11.cob:L1]  incl. [copybooks/wsnames.cob:L28]
    #             Stock control - out of scope, declared for fidelity.
    file_11: str = "stockctl.dat"

    # element 14. 03  file-12  pic x(532)  value "salesled.dat".
    #             [copybooks/file12.cob:L1]  incl. [copybooks/wsnames.cob:L29]
    file_12: str = "salesled.dat"

    # element 15. 03  file-13  pic x(532)  value "value.dat".
    #             [copybooks/file13.cob:L1]  incl. [copybooks/wsnames.cob:L30]
    file_13: str = "value.dat"

    # element 16. 03  file-14  pic x(532)  value "delivery.dat".
    #             [copybooks/file14.cob:L1]  incl. [copybooks/wsnames.cob:L31]
    #             Delivery - out of scope, declared for fidelity.
    file_14: str = "delivery.dat"

    # element 17. 03  file-15  pic x(532)  value "analysis.dat".
    #             [copybooks/file15.cob:L1]  incl. [copybooks/wsnames.cob:L32]
    file_15: str = "analysis.dat"

    # element 18. 03  file-16  pic x(532)  value "invoice.dat".
    #             [copybooks/file16.cob:L1]  incl. [copybooks/wsnames.cob:L33]
    file_16: str = "invoice.dat"

    # element 19. 03  file-17  pic x(532)  value "delinvno.dat".
    #             [copybooks/file17.cob:L1]  incl. [copybooks/wsnames.cob:L34]
    #             Delivery invoice numbers - out of scope, for fidelity.
    file_17: str = "delinvno.dat"

    # element 20. 03  file-18  pic x(532)  value "openitm2.dat".
    #             [copybooks/file18.cob:L1]  incl. [copybooks/wsnames.cob:L35]
    file_18: str = "openitm2.dat"

    # element 21. 03  file-19  pic x(532)  value "openitm3.dat".
    #             [copybooks/file19.cob:L1]  incl. [copybooks/wsnames.cob:L36]
    file_19: str = "openitm3.dat"

    # element 22. 03  file-20  pic x(532)  value "oisort.wrk".
    #             [copybooks/file20.cob:L1]  incl. [copybooks/wsnames.cob:L37]
    file_20: str = "oisort.wrk"

    # element 23. 03  file-21  pic x(532)  value "work.tmp".
    #             [copybooks/file21.cob:L1]  incl. [copybooks/wsnames.cob:L38]
    file_21: str = "work.tmp"

    # element 24. 03  file-22  pic x(532)  value "purchled.dat".
    #             [copybooks/file22.cob:L1]  incl. [copybooks/wsnames.cob:L39]
    file_22: str = "purchled.dat"

    # element 25. 03  file-23  pic x(532)  value "delfolio.dat".
    #             [copybooks/file23.cob:L1]  incl. [copybooks/wsnames.cob:L40]
    #             Delivery folio - out of scope, declared for fidelity.
    file_23: str = "delfolio.dat"

    # element 26. 03  file-24  pic x(532)  value spaces.
    #             [copybooks/file24.cob:L1]  incl. [copybooks/wsnames.cob:L41]
    # THE ONE ELEMENT WITH NO FILENAME (rule R-4). Its `VALUE` is the figurative constant
    # `spaces`, and the maintainer's inclusion-line note calls it a "dummy to build file-02"
    # [:L41]. Kept, because dropping it would shift every later subscript and break the count of
    # 58 that `occurs 58` and `File-Defs-Count` both declare.
    # The default is spaces AT THE DECLARED WIDTH, not the empty string - the difference between
    # this copybook's two kinds of `VALUE`: an alphanumeric literal carries its own length and
    # is stored left-justified, while `spaces` has none and takes the receiving item's, all 532.
    file_24: str = " " * _ELEMENT_WIDTH

    # THE SECOND NUMBERING GAP. There is no `file-25`, and again the
    # copybook says so where the declaration would stand: "No file 25"
    # [copybooks/wsnames.cob:L42]. The sequence jumps from 24 to 26.

    # element 27. 03  file-26  pic x(532)  value "pinvoice.dat".
    #             [copybooks/file26.cob:L1]  incl. [copybooks/wsnames.cob:L43]
    file_26: str = "pinvoice.dat"

    # element 28. 03  file-27  pic x(532)  value "poisort.wrk".
    #             [copybooks/file27.cob:L1]  incl. [copybooks/wsnames.cob:L44]
    file_27: str = "poisort.wrk"

    # element 29. 03  file-28  pic x(532)  value "openitm4.dat".
    #             [copybooks/file28.cob:L1]  incl. [copybooks/wsnames.cob:L45]
    file_28: str = "openitm4.dat"

    # element 30. 03  file-29  pic x(532)  value "openitm5.dat".
    #             [copybooks/file29.cob:L1]  incl. [copybooks/wsnames.cob:L46]
    file_29: str = "openitm5.dat"

    # element 31. 03  file-30  pic x(532)  value "plautogen.dat".
    #             [copybooks/file30.cob:L1]  incl. [copybooks/wsnames.cob:L47]
    #             Purchase autogen - out of scope, declared for fidelity.
    file_30: str = "plautogen.dat"

    # element 32. 03  file-31  pic x(532)  value "bostkitm.dat".
    #             [copybooks/file31.cob:L1]  incl. [copybooks/wsnames.cob:L48]
    #             Sales back-ordered stock items, the maintainer's "NEw
    #             16/03/24" [:L48] - out of scope, declared for fidelity.
    file_31: str = "bostkitm.dat"

    # element 33. 03  file-32  pic x(532)  value "pay.dat".
    #             [copybooks/file32.cob:L1]  incl. [copybooks/wsnames.cob:L49]
    #             Purchase payments - out of scope, for fidelity. Note the
    #             eight-character name in a field of 532.
    file_32: str = "pay.dat"

    # element 34. 03  file-33  pic x(532)  value "cheque.dat".
    #             [copybooks/file33.cob:L1]  incl. [copybooks/wsnames.cob:L50]
    #             Cheques - out of scope, declared for fidelity.
    file_33: str = "cheque.dat"

    # -- the five IRS files, declared inline ------------------------------
    # The maintainer's note on the first of them: "IRS ex file 1  These 4
    # added 19/10/16 for IRS integration" [copybooks/wsnames.cob:L51], and
    # on the second: "all name have 'irs' prefix." [:L52]. Four were added
    # then and the fifth, the sort file, later [:L7].

    # element 35. 03  file-34  pic x(532)  value "irsacnts.dat".
    #             *> IRS ex file 1               [copybooks/wsnames.cob:L51]
    file_34: str = "irsacnts.dat"

    # element 36. 03  file-35  pic x(532)  value "irsdflt.dat".
    #             *> IRS ex file 3               [copybooks/wsnames.cob:L52]
    file_35: str = "irsdflt.dat"

    # element 37. 03  file-36  pic x(532)  value "irspost.dat".
    #             *> IRS ex file 4               [copybooks/wsnames.cob:L53]
    file_36: str = "irspost.dat"

    # element 38. 03  file-37  pic x(532)  value "irsfinal.dat".
    #             *> IRS ex file 5               [copybooks/wsnames.cob:L54]
    file_37: str = "irsfinal.dat"

    # element 39. 03  file-38  pic x(532)  value "postsort.dat".
    #             *> IRS ex irs055 sort file.    [copybooks/wsnames.cob:L55]
    #             The sort program that owns it is out of scope per
    #             section 0.2.2; the name is declared for fidelity.
    file_38: str = "postsort.dat"

    # -- the nineteen payroll files, declared inline ----------------------
    # The whole payroll subsystem is out of scope per section 0.2.2, and no
    # in-scope code path reads any of these. All nineteen are declared
    # because the record mirrors the copybook field for field and because
    # `occurs 58` counts them. The maintainer's block heading is a standing
    # warning to anyone extending the group: "Code for Payroll  AND
    # INCREASE occurs both times" [copybooks/wsnames.cob:L57]. His own
    # per-file notes are kept, question marks and all.

    # element 40. 03  file-39  pic x(532)  value "pyact.dat".
    #             *> PY account                  [copybooks/wsnames.cob:L58]
    file_39: str = "pyact.dat"

    # element 41. 03  file-40  pic x(532)  value "pychk.dat".
    #             *> PY check / bacs             [copybooks/wsnames.cob:L59]
    file_40: str = "pychk.dat"

    # element 42. 03  file-41  pic x(532)  value "pycoh.dat".
    #             *> PY company history          [copybooks/wsnames.cob:L60]
    file_41: str = "pycoh.dat"

    # element 43. 03  file-42  pic x(532)  value "pyded.dat".
    #             *> PY deduction {/ earnings}   [copybooks/wsnames.cob:L61]
    file_42: str = "pyded.dat"

    # element 44. 03  file-43  pic x(532)  value "pyemp.dat".
    #             *> PY employee master          [copybooks/wsnames.cob:L62]
    file_43: str = "pyemp.dat"

    # element 45. 03  file-44  pic x(532)  value "pyhis.dat".
    #             *> PY employee (pay) history   [copybooks/wsnames.cob:L63]
    file_44: str = "pyhis.dat"

    # element 46. 03  file-45  pic x(532)  value "pyhrs.dat".
    #             *> PY pay trans                [copybooks/wsnames.cob:L64]
    file_45: str = "pyhrs.dat"

    # element 47. 03  file-46  pic x(532)  value "pypay.dat".
    #             *> PY pay detail jrn + header ???
    #                                            [copybooks/wsnames.cob:L65]
    file_46: str = "pypay.dat"

    # element 48. 03  file-47  pic x(532)  value "pypr1.dat".
    #             *> PY param 1                  [copybooks/wsnames.cob:L66]
    file_47: str = "pypr1.dat"

    # element 49. 03  file-48  pic x(532)  value "pypr2.dat".
    #             *> PY param 2                  [copybooks/wsnames.cob:L67]
    file_48: str = "pypr2.dat"

    # The maintainer's second heading, "TABLES Blk 1" [:L68], stands over
    # the eight that follow. Note the gap in the copybook's line numbering
    # from L67 to L69: L68 is that heading, not a declaration.

    # element 50. 03  file-49  pic x(532)  value "pycalm.dat".
    #             *> PY  calx - x = s,m,h, x?    [copybooks/wsnames.cob:L69]
    file_49: str = "pycalm.dat"

    # element 51. 03  file-50  pic x(532)  value "pycals.dat".
    #             *> PY                          [copybooks/wsnames.cob:L70]
    file_50: str = "pycals.dat"

    # element 52. 03  file-51  pic x(532)  value "pycalh.dat".
    #             *> PY                          [copybooks/wsnames.cob:L71]
    file_51: str = "pycalh.dat"

    # element 53. 03  file-52  pic x(532)  value "pycalx.dat".
    #             *> PY  california special tables ???
    #                                            [copybooks/wsnames.cob:L72]
    file_52: str = "pycalx.dat"

    # element 54. 03  file-53  pic x(532)  value "pylwt.dat".
    #             *> PY  tax table ???           [copybooks/wsnames.cob:L73]
    file_53: str = "pylwt.dat"

    # element 55. 03  file-54  pic x(532)  value "pyswtaa.dat".
    #             *> PY  swt aa = State abbrev. code Only one used
    #                                            [copybooks/wsnames.cob:L74]
    file_54: str = "pyswtaa.dat"

    # element 56. 03  file-55  pic x(532)  value "pyglcoann.dat".
    #             *> PY gl CoA transfer ??       [copybooks/wsnames.cob:L75]
    file_55: str = "pyglcoann.dat"

    # element 57. 03  file-56  pic x(532)  value "pyglgjbss.dat".
    #             *> PY  ???                     [copybooks/wsnames.cob:L76]
    file_56: str = "pyglgjbss.dat"

    # element 58. 03  file-57  pic x(532)  value "pycal.dat".
    #             *> PY  ??? calm,s,h etc        [copybooks/wsnames.cob:L78]
    # THE LAST ELEMENT, and the copybook is unsure of it: "Not sure about
    # these two up/down" [:L77]. Its `03` also sits two columns further in
    # than every other element in the group [:L78]. The indentation is
    # cosmetic and the level is unchanged, so the element is the 58th
    # either way; the oddity is recorded rather than tidied (rule R-4).
    file_57: str = "pycal.dat"


#   THE DESCRIPTORS FOR THE 58 ELEMENTS  (rule R-5)
# Assigned here rather than in the class body because both are DERIVED FROM THE CLASS'S OWN
# DECLARED FIELDS, which do not exist until the class does. Deriving them is the point: with 58
# elements a hand-kept parallel list of keys would be one transcription slip away from
# describing the wrong field, and section 0.3.3 asks for metadata "derived, not transcribed"
# precisely to close that.
# Every element of this group is lower case with hyphens in the copybook, so turning an
# attribute name's underscores back into hyphens reproduces the COBOL name exactly - `file_0`
# gives `file-0`. The transform covers this group only; the six items outside it carry mixed
# case and are written out in full below.
FileDefsA.GROUP = FieldDescriptor.from_dictionary_key(
    f"{_DICTIONARY_RECORD}.file-defs-a"
)
FileDefsA.FIELDS = tuple(
    FieldDescriptor.from_dictionary_key(
        f"{_DICTIONARY_RECORD}.{declared.name.replace('_', '-')}"
    )
    for declared in dataclasses.fields(FileDefsA)
)


# The content the redefining table holds, in `OCCURS` order, taken from the
# declared fields above.
# COBOL FORBIDS A `VALUE` CLAUSE ON A REDEFINING ITEM, so
# `System-File-Names` has none: the storage it addresses is initialised by
# the `VALUE` clauses of the group it redefines. Sourcing this from those
# same declarations reproduces that fact instead of inventing a second
# one - blanking the table would state something the compiled program
# never does.
# This is a constant computed ONCE, at import. It is not an accessor, and
# no accessor exists: Python has no storage aliasing, so after a
# `SystemFileNamesView` is constructed its tuple and a `FileDefsA`'s
# attributes are independent objects, and nothing here pretends otherwise.
_DECLARED_TABLE_CONTENT: Final[tuple[str, ...]] = tuple(
    declared.default for declared in dataclasses.fields(FileDefsA)
)


@dataclass(slots=True)
class SystemFileNamesView:
    """The redefining table: `02 filler redefines file-defs-a.` [:L80].

        02  filler         redefines file-defs-a.            [:L80]
            03  System-File-Names   pic x(532) occurs 58.    [:L81]

    THE COBOL GROUP HAS NO NAME - it is `FILLER` - so this class name is
    this module's, chosen for the table it carries. Its COBOL original is
    the anonymous `02 filler redefines file-defs-a` at
    [copybooks/wsnames.cob:L80], and the generated dictionary keys that
    group `File-Defs.filler`, which is the spelling the attribute holding
    this class uses on `FileDefs`.

    This is how the file handlers address the block: by subscript, over the
    same storage the 58 named elements of `FileDefsA` occupy. The two
    General Ledger work-file names are elements 1 and 2 of it.

    THE `REDEFINES` AND THE `OCCURS` ARE AT DIFFERENT LEVELS, and are
    recorded where the copybook puts them rather than fused together:

        GROUP     the `02` group  [:L80]  ->  redefines == "file-defs-a"
        FIELDS[0] the `03` item   [:L81]  ->  occurs == 58

    Fusing the pair onto one descriptor would contradict the frozen source
    and would mean writing metadata by hand rather than looking it up, so
    it is not done (rules R-4 and R-5).

    `OCCURS` IS 1-BASED AND PYTHON IS 0-BASED. `System-File-Names (1)` is
    `pre-trans-name`, so it is `system_file_names[0]` here, and
    `System-File-Names (58)` is `system_file_names[57]`. The offset is
    stated and left alone: there is no 1-based wrapper, no subscript
    helper and no name-to-index mapping in this module, because Python
    cannot alias storage and machinery that suggested otherwise would
    mislead rather than help.
    """

    # The `02` group. Carries the REDEFINES, and reports itself as both a
    # group and FILLER, exactly as [copybooks/wsnames.cob:L80] declares it.
    GROUP: ClassVar[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
        f"{_DICTIONARY_RECORD}.filler"
    )

    # The `03` table item. Carries the OCCURS of 58 and the declared width
    # of 532 [copybooks/wsnames.cob:L81]. One entry, because the group
    # declares one item.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        FieldDescriptor.from_dictionary_key(
            f"{_DICTIONARY_RECORD}.System-File-Names"
        ),
    )

    # 03  System-File-Names   pic x(532) occurs 58.
    #     *> 39 chg for sales BO file plus py     [copybooks/wsnames.cob:L81]
    # A tuple rather than a list: the table has a fixed 58 elements and a
    # fixed order, and a fixed collection is a tuple throughout this
    # package (rule R-6). The maintainer's trailing comment on the line
    # reads 39 while the `occurs` beside it reads 58, and the copybook's
    # change log likewise stops counting at 39 [:L8-L9]; the stale comment
    # is quoted as found and not brought up to date (rule R-4).
    system_file_names: tuple[str, ...] = _DECLARED_TABLE_CONTENT


@dataclass(slots=True)
class FileDefs:
    """`01  File-Defs.` [copybooks/wsnames.cob:L13] - the whole record.

    The block every in-scope program is handed: fourth parameter of the
    General / Sales / Purchase linkage [general/gl071.cbl:L161-L164],
    third of the IRS linkage [irs/irs030.cbl:L552-L554], and fourth
    argument of every file-handler call.

    Four `02` items, in copybook declaration order:

        file_defs_a            02  file-defs-a.               [:L14]
        filler                 02  filler redefines ...       [:L80]
        file_defs_count        02  File-Defs-Count            [:L82]
        file_defs_os_delimiter 02  File-Defs-os-Delimiter     [:L83]

    `filler` keeps the COBOL name of the anonymous redefining group, which
    is how the generated dictionary keys it; the table itself is
    `file_defs.filler.system_file_names`, nested exactly as the copybook
    nests it under `File-Defs`.

    Mutable and NOT frozen, for the same reason `FileDefsA` is: a caller
    fills the block in - not least the delimiter - before dispatching.
    """

    # The `01` group itself, and the four `02` items in declaration order.
    GROUP: ClassVar[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
        f"{_DICTIONARY_RECORD}.File-Defs"
    )
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        FieldDescriptor.from_dictionary_key(
            f"{_DICTIONARY_RECORD}.file-defs-a"
        ),
        FieldDescriptor.from_dictionary_key(f"{_DICTIONARY_RECORD}.filler"),
        FieldDescriptor.from_dictionary_key(
            f"{_DICTIONARY_RECORD}.File-Defs-Count"
        ),
        FieldDescriptor.from_dictionary_key(
            f"{_DICTIONARY_RECORD}.File-Defs-os-Delimiter"
        ),
    )

    # 02  file-defs-a.                            [copybooks/wsnames.cob:L14]
    file_defs_a: FileDefsA = dataclasses.field(default_factory=FileDefsA)

    # 02  filler         redefines file-defs-a.   [copybooks/wsnames.cob:L80]
    # The COBOL name of the anonymous group, as the dictionary keys it
    # (`File-Defs.filler`). Its own storage is the storage of
    # `file_defs_a`; Python cannot express that, so the two are separate
    # objects here and no accessor is provided that would suggest they are
    # not.
    filler: SystemFileNamesView = dataclasses.field(
        default_factory=SystemFileNamesView
    )

    # 02  File-Defs-Count         binary-short value 58.
    #     *> MUST be the same as above occurs     [copybooks/wsnames.cob:L82]
    # `binary-short` - a signed 16-bit integer, domain -32768 .. 32767, scale 0 - so the carrier
    # is `int`, defaulting to the copybook's own `VALUE`.
    # DELIBERATELY THE LITERAL 58 AND NOT A COUNT OF THE ELEMENTS. The copybook declares the
    # number and separately declares 58 elements, and the maintainer's comment shows he knows
    # the two can drift. Computing it here would make them agree by construction and so hide any
    # future disagreement - the same shape of defect as the batch record's declared length
    # contradicting the sum of its fields [copybooks/wsbatch.cob:L7-L9]. The declared value is
    # reproduced; the agreement is asserted in the test suite, never enforced here.
    file_defs_count: int = 58

    # 02  File-Defs-os-Delimiter  pic x.          [copybooks/wsnames.cob:L83]
    # One character, and THE ONLY ITEM IN THIS RECORD WITH NO `VALUE` CLAUSE. The default is a
    # single space, and the copybook's own comment on the line says why: it reads, of this
    # field, "if = [reverse solidus] or / then paths have been set". A space is neither set
    # state - it is the not-yet-set state, where a freshly initialised block starts, and it
    # matches how the runtime space-fills an alphanumeric working-storage item declaring no
    # value.
    # NOT taken from the host operating system. There is no separator lookup here and no
    # inspection of the running system: this is a declared field the calling program sets, and
    # deriving it would make two runs on two hosts differ (rule R-6).
    file_defs_os_delimiter: str = " "
