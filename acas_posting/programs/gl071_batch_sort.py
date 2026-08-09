"""`gl071` - the General Ledger batch transaction sort [general/gl071.cbl].

The whole program, and it contains no arithmetic at all: it reads the
pre-transaction work file, sorts it and writes the post-transaction work file.
The `SORT` verbs become stable sorts on the identical key tuples.

The output ordering is a hard contract, not a convenience. gl072 locates the
nominal-ledger account for each posting with a SEQUENTIAL read
[general/gl072.cbl:L408], guarded at L407, so it finds the right account only
because this program emitted the stream in nominal-key order. A perturbed sort
misposts silently - no error, no diagnostic, wrong balances - which is why the
sort is stable and why the ordering is asserted directly rather than left to be
caught downstream.
"""

from __future__ import annotations

from typing import Final

from acas_posting.records.calling_data import WsCallingData

from acas_posting.records.file_defs import FileDefs

# copy "wssystem.cob". [general/gl071.cbl:L156] `SYSTEM-REC`, the 169-column system
# record. Imported for the second parameter's declaration; never tested here, which is
# question Q-15.
from acas_posting.records.system_record import SystemRecord

# The work-file layer: the three sequences, and the `SORT` statement itself.
from acas_posting.workfiles import (
    SORT_TRANS_ASCENDING_KEYS,
    GeneralLedgerWorkFiles,
    general_ledger_work_files,
    sort_using_giving,
)

#: The whole public surface: the program's single entry point, mirroring its `PROCEDURE
#: DIVISION USING` list [general/gl071.cbl:L161-L164]. Agent Action Plan section 0.3.3,
#: verbatim.
__all__: Final[tuple[str, ...]] = ("run",)


def _main(work_files: GeneralLedgerWorkFiles) -> None:
    """`main.` - the screen message and the sort [general/gl071.cbl:L167-L178].

    The paragraph's whole body is two statements, and both are reproduced here. A
    PARAGRAPH, NOT A SECTION.

    Args:
        work_files: The three sequences this program's FILE-CONTROL entries declare
            [general/gl071.cbl:L92-L102] - `pre_trans`, `post_trans` and `sort_trans`,
            in the container that stands in for the filesystem the compiled program
            passes them through.

    Raises:
        acas_posting.workfiles.WorkFileError: A record description does not have the
            shape the group move between the three field-identical layouts
            [general/gl071.cbl:L112-L144] requires. A PROGRAMMER error.
    """
    # 172 sort sort-trans 173 on ascending key sort-batch 174 sort-ac 175 sort-pc 176
    # sort-post 177 using pre-trans 178 giving post-trans.
    sort_using_giving(
        work_files.sort_trans,
        on_ascending_key=SORT_TRANS_ASCENDING_KEYS,
        using=work_files.pre_trans,
        giving=work_files.post_trans,
    )


def _main_exit() -> None:
    """`main-exit.` - the `goback` [general/gl071.cbl:L180-L181].

    THE PARAGRAPH'S ENTIRE BODY IS `goback.`, so this function's entire body is a
    `return`. That is a faithful one-to-one mapping and NOT a stub.
    """
    return


def run(
    ws_calling_data: WsCallingData,
    system_record: SystemRecord,
    to_day: str,
    file_defs: FileDefs,
    *,
    work_files: GeneralLedgerWorkFiles | None = None,
) -> None:
    """Run `gl071` - sort the pre-trans stream into nominal-key order.

    The four positional parameters below are that list, in that order, under those names
    - the four-parameter General Ledger call shape, verified character-for-character
    identical in all five programs that take it.

    Args:
        ws_calling_data: `01 WS-Calling-Data` [copybooks/wscall.cob:L6-L14], accepted
            and unread. Not written back either: `WS-Term-Code` keeps whatever the
            caller put there, which `load00.` sets to zero before the `CALL`
            [general/general.cbl:L714].
        system_record: `SYSTEM-REC`, the 169-column system record, accepted and unread.
            `gl071` tests no system flag, no accounting cycle and no `Run-Date`.
        to_day: `to-day pic x(10)` in DD/MM/CCYY form, accepted and UNUSED. Declared
            because the linkage declares it.
        file_defs: `01 File-Defs.` [copybooks/wsnames.cob:L13], the file-name buffers.
            Used indirectly: `pre-trans-name` and `post-trans-name`
            [copybooks/wsnames.cob:L15-L16] and `file-21` [copybooks/file21.cob:L1] are
            what this program's three FILE-CONTROL entries assign
            [general/gl071.cbl:L92-L102].
        work_files: The cycle's three work-file sequences.

    Raises:
        acas_posting.workfiles.WorkFileError: A record description does not have the
            shape the group move between the three field-identical layouts requires. A
            PROGRAMMER error; see `_main`.
    """
    # NECESSITY RATHER THAN A VALIDATION. `gl071` contains ZERO conditional statements,
    # so no test of any value reaching this program is added anywhere below (rule R-3).
    files = general_ledger_work_files() if work_files is None else work_files

    _main(files)

    # 180 main-exit. -> 181 goback. Reached by fall-through, not by a transfer; called
    # explicitly so the fall-through is visible rather than implied.
    _main_exit()
