"""The `File-Defs` record: the file names the ACAS cycle is handed.

This module declares NAMES. It reaches no file system, holds no handle and
creates nothing on disk. `File-Defs` [copybooks/wsnames.cob] is the block of
fixed-width name fields that is the last parameter of all three linkage shapes,
so every program receives its file names rather than deciding them.

Two of the names are the General Ledger work files, `pretrans.tmp` and
`postrans.tmp` [copybooks/wsnames.cob:L15-L16], which the maintainer annotates as
belonging to `gl071`. They are transient scratch files, not part of the schema,
and `acas_posting.workfiles` models them.

A name's width is load-bearing: a value longer than its field is truncated by the
`MOVE` that stores it, exactly as in COBOL, so the widths are looked up rather
than assumed.
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


_DICTIONARY_RECORD: Final[str] = "File-Defs"

# The declared width shared by all 58 elements and by the table that redefines them:
# `pic x(532)`.
_ELEMENT_WIDTH: Final[int] = 532


@dataclass(slots=True)
class FileDefsA:
    """`02 file-defs-a.` [copybooks/wsnames.cob:L14] - the 58 name fields.

    Mutable on purpose, and NOT frozen.
    """

    # Assigned immediately after the class body, because both derive from this class's
    # own declared fields and so cannot be built until the class exists.
    GROUP: ClassVar[FieldDescriptor]
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]]


    pre_trans_name: str = "pretrans.tmp"

    post_trans_name: str = "postrans.tmp"


    file_0: str = "system.dat"

    # THE FIRST NUMBERING GAP. There is no `file-1`. The copybook says so itself, in a
    # comment standing where the declaration would be: "No file 1"
    # [copybooks/wsnames.cob:L18].

    file_2: str = "archive.dat"

    file_3: str = "final.dat"

    file_4: str = "slautogen.dat"

    file_5: str = "ledger.dat"

    file_6: str = "posting.dat"

    file_7: str = "batch.dat"

    file_8: str = "postings2irs.dat"

    file_9: str = "tmp-stock.dat"

    file_10: str = "staudit.dat"

    file_11: str = "stockctl.dat"

    file_12: str = "salesled.dat"

    file_13: str = "value.dat"

    file_14: str = "delivery.dat"

    file_15: str = "analysis.dat"

    file_16: str = "invoice.dat"

    file_17: str = "delinvno.dat"

    file_18: str = "openitm2.dat"

    file_19: str = "openitm3.dat"

    file_20: str = "oisort.wrk"

    file_21: str = "work.tmp"

    file_22: str = "purchled.dat"

    file_23: str = "delfolio.dat"

    # element 26. 03 file-24 pic x(532) value spaces. [copybooks/file24.cob:L1] incl.
    # [copybooks/wsnames.cob:L41] THE ONE ELEMENT WITH NO FILENAME (rule R-4).
    file_24: str = " " * _ELEMENT_WIDTH

    # THE SECOND NUMBERING GAP. There is no `file-25`, and again the copybook says so
    # where the declaration would stand: "No file 25" [copybooks/wsnames.cob:L42].

    file_26: str = "pinvoice.dat"

    file_27: str = "poisort.wrk"

    file_28: str = "openitm4.dat"

    file_29: str = "openitm5.dat"

    file_30: str = "plautogen.dat"

    file_31: str = "bostkitm.dat"

    file_32: str = "pay.dat"

    file_33: str = "cheque.dat"


    file_34: str = "irsacnts.dat"

    file_35: str = "irsdflt.dat"

    file_36: str = "irspost.dat"

    file_37: str = "irsfinal.dat"

    file_38: str = "postsort.dat"

    # The whole payroll subsystem is out of scope per section 0.2.2, and no in-scope
    # code path reads any of these.

    file_39: str = "pyact.dat"

    file_40: str = "pychk.dat"

    file_41: str = "pycoh.dat"

    file_42: str = "pyded.dat"

    file_43: str = "pyemp.dat"

    file_44: str = "pyhis.dat"

    file_45: str = "pyhrs.dat"

    file_46: str = "pypay.dat"

    file_47: str = "pypr1.dat"

    file_48: str = "pypr2.dat"


    file_49: str = "pycalm.dat"

    file_50: str = "pycals.dat"

    file_51: str = "pycalh.dat"

    file_52: str = "pycalx.dat"

    file_53: str = "pylwt.dat"

    file_54: str = "pyswtaa.dat"

    file_55: str = "pyglcoann.dat"

    file_56: str = "pyglgjbss.dat"

    # element 58. 03 file-57 pic x(532) value "pycal.dat". *> PY ??? calm,s,h etc
    # [copybooks/wsnames.cob:L78] THE LAST ELEMENT, and the copybook is unsure of it.
    file_57: str = "pycal.dat"


# Assigned here rather than in the class body because both are DERIVED FROM THE CLASS'S
# OWN DECLARED FIELDS, which do not exist until the class does.
FileDefsA.GROUP = FieldDescriptor.from_dictionary_key(
    f"{_DICTIONARY_RECORD}.file-defs-a"
)
FileDefsA.FIELDS = tuple(
    FieldDescriptor.from_dictionary_key(
        f"{_DICTIONARY_RECORD}.{declared.name.replace('_', '-')}"
    )
    for declared in dataclasses.fields(FileDefsA)
)


# The content the redefining table holds, in `OCCURS` order, taken from the declared
# fields above. `System-File-Names` has none.
_DECLARED_TABLE_CONTENT: Final[tuple[str, ...]] = tuple(
    declared.default for declared in dataclasses.fields(FileDefsA)
)


@dataclass(slots=True)
class SystemFileNamesView:
    """The redefining table: `02 filler redefines file-defs-a.` [:L80].

    recorded where the copybook puts them rather than fused together.
    """

    GROUP: ClassVar[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
        f"{_DICTIONARY_RECORD}.filler"
    )

    # The `03` table item. Carries the OCCURS of 58 and the declared width of 532
    # [copybooks/wsnames.cob:L81]. One entry, because the group declares one item.
    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        FieldDescriptor.from_dictionary_key(
            f"{_DICTIONARY_RECORD}.System-File-Names"
        ),
    )

    # 03 System-File-Names pic x(532) occurs 58. *> 39 chg for sales BO file plus py
    # [copybooks/wsnames.cob:L81] A tuple rather than a list.
    system_file_names: tuple[str, ...] = _DECLARED_TABLE_CONTENT


@dataclass(slots=True)
class FileDefs:
    """`01 File-Defs.` [copybooks/wsnames.cob:L13] - the whole record."""

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

    file_defs_a: FileDefsA = dataclasses.field(default_factory=FileDefsA)

    # 02 filler redefines file-defs-a. [copybooks/wsnames.cob:L80] The COBOL name of the
    # anonymous group, as the dictionary keys it (`File-Defs.filler`). Its own storage
    # is the storage of `file_defs_a`.
    filler: SystemFileNamesView = dataclasses.field(
        default_factory=SystemFileNamesView
    )

    # 02 File-Defs-Count binary-short value 58. *> MUST be the same as above occurs
    # [copybooks/wsnames.cob:L82] `binary-short` - a signed 16-bit integer, domain
    # -32768 ..
    file_defs_count: int = 58

    # 02 File-Defs-os-Delimiter pic x. [copybooks/wsnames.cob:L83] One character, and
    # THE ONLY ITEM IN THIS RECORD WITH NO `VALUE` CLAUSE.
    file_defs_os_delimiter: str = " "
