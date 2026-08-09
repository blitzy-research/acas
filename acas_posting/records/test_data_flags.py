"""Record layout for `01 ACAS-DAL-Common-data.` [copybooks/Test-Data-Flags.cob:L6].

NOT a test module, despite the name it inherits from the copybook: it is the
record layout for the block every handler call carries, and pytest must not
collect it. The name is the copybook's and is kept for traceability.

The block's one switch is the compile-time logging flag the frozen tree uses as
its only test instrumentation. It is carried as configuration - a field with a
value - rather than as a behaviour, so nothing here branches on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from acas_posting.cobol.field import FieldDescriptor

__all__: list[str] = ["AcasDalCommonData"]


# One lookup per storage item, keyed <COPYBOOK-RECORD>.<FIELD-NAME> in the copybook's
# own casing.

SW_TESTING: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "ACAS-DAL-Common-data.SW-Testing"
)

SW_TESTING_2: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "ACAS-DAL-Common-data.SW-Testing-2"
)

LOG_FILE_REC_WRITTEN: Final[FieldDescriptor] = FieldDescriptor.from_dictionary_key(
    "ACAS-DAL-Common-data.Log-File-Rec-Written"
)

# Declaration order, L10 then L15 then L18, matching the attribute order of the record
# below.
FIELDS: Final[tuple[FieldDescriptor, ...]] = (
    SW_TESTING,
    SW_TESTING_2,
    LOG_FILE_REC_WRITTEN,
)


@dataclass(slots=True)
class AcasDalCommonData:
    """``01 ACAS-DAL-Common-data.`` [copybooks/Test-Data-Flags.cob:L6].

    MUTABLE, deliberately.

    Attributes:
        sw_testing: ``SW-Testing``, the file-handler logging switch. 1 in the frozen
            source, which means logging ON.
        sw_testing_2: ``SW-Testing-2``, the display-tracing switch. Zero in the frozen
            source.
        log_file_rec_written: ``Log-File-Rec-Written``, the count of log records
            written. Zero in the frozen source.
    """

    # SW-Testing pic 9 value 1 [copybooks/Test-Data-Flags.cob:L10] "log file reporting
    # for testing otherwise zero" [L8]. The default is the copybook's own `value 1`,
    # PRESERVED.
    sw_testing: int = 1

    # SW-Testing-2 pic 9 value zero [copybooks/Test-Data-Flags.cob:L15] "Testing only
    # for displays ws-where etc otherwise zero" [L13].
    sw_testing_2: int = 0

    log_file_rec_written: int = 0
