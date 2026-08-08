"""The `01 System-Record.` layout: the widest record in the migration.

`SYSTEM-REC` is the ACAS system record - 1024 bytes in six blocks and 169 MySQL
columns, declared across `copybooks/wssystem.cob`. Mirrored field for field with
descriptors looked up in the generated dictionary (R-5), which is the only
tractable way to get 169 fields right.

Two fields govern the whole cycle. `Run-Date binary-long`
[copybooks/wssystem.cob:L67] is one of the two observables the controlled clock
pins, so every run-date-derived value in the cycle comes from it rather than from
a clock. And the IRS fan-out switch with its two condition names
[copybooks/wssystem.cob:L179-L181] decides whether a Sales or Purchase posting
run writes the General Ledger posting file, the IRS transfer file or both -
so its state changes which tables a run touches at all.

    entity facade  System
    handler        acas000, file-key number 1
    bridge         systemMT
    MySQL table    SYSTEM-REC   (169 columns, primary key SYSTEM-REC-KEY,
                                 no secondary index, no TIMESTAMP and no
                                 AUTO_INCREMENT)
    copybook       copybooks/wssystem.cob

One correction to plan section 0.6.6, which describes the in-scope tables
as having no column-level DEFAULT: `PASS-WORD char(4) NOT NULL DEFAULT ''`
[mysql/ACASDB.sql:L1219], from `Pass-Word pic x(4)`
[copybooks/wssystem.cob:L97], carries the only one in the whole 33-table
frozen schema. It changes nothing here, since the default is reachable
only by a writer that omits the column and every bridge load paragraph
initialises its host-variable group first.

`acas_posting/records/__init__.py` sets out the conventions every record
module follows: descriptors looked up rather than typed by hand (rule
R-5), the six numeric storage classes, exact decimals (R-2), the two
permitted imports, and condition names living in
`acas_posting.cobol.condition_names`.
"""

from __future__ import annotations

import decimal
from dataclasses import dataclass, field
from typing import ClassVar, Final

from acas_posting.cobol.field import FieldDescriptor
from acas_posting.dictionary import loader

__all__: Final[tuple[str, ...]] = (
    "FROZEN_PLACEHOLDER_RDBMS_DB_NAME",
    "FROZEN_PLACEHOLDER_RDBMS_PASSWD",
    "FROZEN_PLACEHOLDER_RDBMS_PORT",
    "FROZEN_PLACEHOLDER_RDBMS_USER",
    "GeneralLedgerBlock",
    "IrsDataBlock",
    "IrsEntryBlock",
    "Level",
    "MapsSer",
    "PlAppropAc6Parts",
    "PurchaseLedgerBlock",
    "RdbmsFlatStatuses",
    "SalesLedgerBlock",
    "StockControlBlock",
    "Suser",
    "SystemDataBlock",
    "SystemRecord",
    "VatGroup",
    "VatRates",
    "VatRates2",
    "carries_frozen_placeholder_rdbms_credentials",
)


# DICTIONARY LOOKUP (rule R-5, and plan section 0.8.1 "data dictionary first").

# The `01` record name the copybook declares, and the MySQL table the bridge maps it to.
_RECORD: Final[str] = "System-Record"
_MYSQL_TABLE: Final[str] = "SYSTEM-REC"


def _line_of(source_locator: str) -> int:
    """Return the first line number of a `<path>:L<n>` source locator."""
    return int(source_locator.rsplit(":L", 1)[1].split("-")[0])


def _entry_key_index() -> dict[tuple[str, int], str]:
    """Index every dictionary entry key by COBOL name and declaration line.

    A dictionary entry key is `<TABLE>.<COLUMN>` when the item reaches a MySQL column
    and `<COPYBOOK-RECORD>.<FIELD>` when it does not, with a `#<line>` suffix
    disambiguating a repeated name. Neither form can be derived from the copybook name
    by rule.
    """
    index: dict[tuple[str, int], str] = {}
    for entry in loader.entries_for_table(_MYSQL_TABLE):
        item = entry.copybook
        if item is None:
            continue
        index[(item.name, _line_of(item.source))] = entry.key
    for entry in loader.entries_for_copybook_record(_RECORD):
        item = entry.copybook
        index[(item.name, _line_of(item.source))] = entry.key
    return index


_KEY_INDEX: Final[dict[tuple[str, int], str]] = _entry_key_index()


def _descriptor(cobol_name: str, line: int) -> FieldDescriptor:
    """Describe one item of this record, by verbatim COBOL name and line.

    The lookup is deliberately total: an item named or numbered wrongly fails the index
    lookup at import time with a `KeyError` naming the pair, rather than producing a
    descriptor that quietly describes the wrong storage.
    """
    return FieldDescriptor.from_dictionary_key(_KEY_INDEX[(cobol_name, line)])


# The 169 dictionary keys of the columns of SYSTEM-REC, in column ordinal order, kept so
# that a consumer counting the table's width reads the artifact rather than this file.
_COLUMN_KEYS: Final[tuple[str, ...]] = tuple(
    entry.key for entry in loader.entries_for_table(_MYSQL_TABLE)
)


@dataclass(slots=True)
class VatRates:
    """The `05 Vat-Rates comp.` group [copybooks/wssystem.cob:L55]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Vat-Rate-1", 56),
        _descriptor("Vat-Rate-2", 57),
        _descriptor("Vat-Rate-3", 58),
        _descriptor("Vat-Rate-4", 59),
        _descriptor("Vat-Rate-5", 60),
    )

    vat_rate_1: decimal.Decimal = decimal.Decimal("0.00")

    vat_rate_2: decimal.Decimal = decimal.Decimal("0.00")

    vat_rate_3: decimal.Decimal = decimal.Decimal("0.00")

    vat_rate_4: decimal.Decimal = decimal.Decimal("0.00")

    vat_rate_5: decimal.Decimal = decimal.Decimal("0.00")


@dataclass(slots=True)
class Suser:
    """The `05 Suser.` group [copybooks/wssystem.cob:L70].

    One child, and the group rather than the child is what the bridge maps to a column.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Usera", 71),
    )

    usera: str = " " * 32


@dataclass(slots=True)
class Level:
    """The `05 Level.` group [copybooks/wssystem.cob:L83]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Level-1", 84),
        _descriptor("Level-2", 86),
        _descriptor("Level-3", 88),
        _descriptor("Level-4", 90),
        _descriptor("Level-5", 92),
        _descriptor("Level-6", 95),
    )

    level_1: int = 0

    level_2: int = 0

    level_3: int = 0

    level_4: int = 0

    level_5: int = 0

    level_6: int = 0


@dataclass(slots=True)
class RdbmsFlatStatuses:
    """The `05 RDBMS-Flat-Statuses.` group [copybooks/wssystem.cob:L111]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("File-System-Used", 112),
        _descriptor("File-Duplicates-In-Use", 123),
    )

    file_system_used: int = 0

    file_duplicates_in_use: int = 0


@dataclass(slots=True)
class MapsSer:
    """The `05 Maps-Ser.` group [copybooks/wssystem.cob:L125]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Maps-Ser-xx", 126),
        _descriptor("Maps-Ser-nn", 127),
    )

    maps_ser_xx: str = " " * 2

    maps_ser_nn: int = 0


@dataclass(slots=True)
class SystemDataBlock:
    """The `03 System-Data-Block.` [copybooks/wssystem.cob:L52]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("System-Record-Version-Prime", 53),
        _descriptor("System-Record-Version-Secondary", 54),
        _descriptor("Vat-Rates", 55),
        _descriptor("Vat-Rate", 61),
        _descriptor("Cyclea", 62),
        _descriptor("Scycle", 63),
        _descriptor("Period", 64),
        _descriptor("Page-Lines", 65),
        _descriptor("Next-Invoice", 66),
        _descriptor("Run-Date", 67),
        _descriptor("Start-Date", 68),
        _descriptor("End-Date", 69),
        _descriptor("Suser", 70),
        _descriptor("User-Code", 72),
        _descriptor("Address-1", 73),
        _descriptor("Address-2", 74),
        _descriptor("Address-3", 75),
        _descriptor("Address-4", 76),
        _descriptor("Post-Code", 77),
        _descriptor("Country", 78),
        _descriptor("Print-Spool-Name", 79),
        _descriptor("Phone-No", 80),
        _descriptor("FILLER", 81),
        _descriptor("Pass-Value", 82),
        _descriptor("Level", 83),
        _descriptor("Pass-Word", 97),
        _descriptor("Host", 98),
        _descriptor("Op-System", 100),
        _descriptor("Current-Quarter", 110),
        _descriptor("RDBMS-Flat-Statuses", 111),
        _descriptor("Maps-Ser", 125),
        _descriptor("Date-Form", 128),
        _descriptor("Data-Capture-Used", 133),
        _descriptor("RDBMS-DB-Name", 137),
        _descriptor("RDBMS-User", 138),
        _descriptor("RDBMS-Passwd", 139),
        _descriptor("VAT-Reg-Number", 140),
        _descriptor("Param-Restrict", 141),
        _descriptor("RDBMS-Port", 142),
        _descriptor("RDBMS-Host", 143),
        _descriptor("RDBMS-Socket", 144),
        _descriptor("Stats-Date-Period", 145),
        _descriptor("Company-Email", 146),
    )

    system_record_version_prime: int = 0

    system_record_version_secondary: int = 0

    # 05 Vat-Rates comp group item - no storage of its own [copybooks/wssystem.cob:L55]
    # GROUP USAGE.
    vat_rates: VatRates = field(default_factory=VatRates)

    # 05 Vat-Rate redefines Vat-Rates pic 99v99 comp occurs 5 decimal, digits 4, scale 2
    # [copybooks/wssystem.cob:L61] REDEFINES the five items above as a 5-element table
    # over the SAME bytes.
    vat_rate: list[decimal.Decimal] = field(
        default_factory=lambda: [decimal.Decimal("0.00")] * 5
    )

    cyclea: int = 0

    @property
    def scycle(self) -> int:
        """Read ``Scycle`` through the bytes owned by ``Cyclea``.

        ``Scycle REDEFINES Cyclea`` [copybooks/wssystem.cob:L62-L63], so the two
        names are not two values. Keeping one dataclass field also means
        ``INITIALIZE`` clears the storage once, as the record layout does.
        """
        return self.cyclea

    @scycle.setter
    def scycle(self, value: int) -> None:
        """Store through the ``Scycle`` view of ``Cyclea``'s byte."""
        self.cyclea = int(value)

    period: int = 0

    # 05 Page-Lines binary-char unsigned int, unsigned [copybooks/wssystem.cob:L65]
    # column SYSTEM-REC.PAGE-LINES tinyint(3) unsigned DECLARATION BEATS COMMENT (R-4).
    page_lines: int = 0

    # 05 Next-Invoice binary-long int, signed [copybooks/wssystem.cob:L66] column
    # SYSTEM-REC.NEXT-INVOICE int(8) unsigned Incremented by the invoice posting path,
    # so this record is mutable working storage and is never frozen.
    next_invoice: int = 0

    # 05 Run-Date binary-long -> int, signed [copybooks/wssystem.cob:L67] column SYSTEM-
    # REC.RUN-DAT int(8) unsigned THE CONTROLLED-CLOCK OBSERVABLE. Plan section 0.1.1.
    run_date: int = 0

    # 05 Start-Date binary-long int, signed [copybooks/wssystem.cob:L68] column SYSTEM-
    # REC.START-DAT int(8) unsigned Renamed ACAS-Start-Date where irs030 copies this
    # record [irs/irs030.cbl:L422], because copybooks/irswssystem.cob declares its own
    # `start-date pic x(8)` - text where this one is binary.
    start_date: int = 0

    # 05 End-Date binary-long int, signed [copybooks/wssystem.cob:L69] column SYSTEM-
    # REC.END-DAT int(8) unsigned Renamed ACAS-End-Date where irs030 copies this record
    # [irs/irs030.cbl:L423]. Column name drift: END-DAT. Anomaly A-11 applies.
    end_date: int = 0

    suser: Suser = field(default_factory=Suser)

    user_code: str = " " * 32

    address_1: str = " " * 24

    address_2: str = " " * 24

    address_3: str = " " * 24

    address_4: str = " " * 24

    post_code: str = " " * 12

    country: str = " " * 24

    print_spool_name: str = " " * 48

    phone_no: str = " " * 12

    # THE ONE ATTRIBUTE IN THE PACKAGE THAT HAD NO ROUTE TO ITS ENTRY.
    #
    # Rule R-5 requires that every record field be traceable to a data-dictionary
    # entry, and `acas_posting/dictionary/loader.py` normally finds one without help
    # by trying, in order: field metadata, a class constant, the class's and module's
    # named descriptor maps, then POSITION within `FIELDS`. Of 976 dataclass
    # attributes across the 27 record modules this was the only one that reached the
    # end of that list, and it did so because two ordinary facts about THIS record
    # combine badly:
    #
    #  1. The POSITIONAL route is unavailable here. It requires `FIELDS` and the
    #     dataclass fields to be the same length, and they are not: `FIELDS` carries
    #     46 descriptors against 45 fields, because `Scycle REDEFINES Cyclea`
    #     [copybooks/wssystem.cob:L62-L63] is one storage location with two COBOL
    #     names, correctly modelled as one field plus the `scycle` property above.
    #     The record is right and the count mismatch is a consequence of it.
    #  2. The NAME route cannot match either. The descriptor's COBOL name is the bare
    #     `FILLER` [copybooks/wssystem.cob:L81], and `FILLER` is not unique in this
    #     copybook, so the attribute has to carry the line number to be a distinct
    #     Python name -- and `filler_81` then equals no form of `FILLER`.
    #
    # So the field states its key outright, which is the loader's FIRST route. The key
    # is taken from `_KEY_INDEX` rather than written as a literal, deliberately: that
    # lookup is total, so a wrong name or line fails at IMPORT with a `KeyError`
    # naming the pair, exactly as `_descriptor` does. A literal string would have been
    # a second place for the key to drift out of agreement with the artifact.
    #
    # `tests/arithmetic/test_pic_field_descriptors.py` asserts that ZERO record
    # attributes are unrouted, so a future field that lands in this same gap fails a
    # test rather than quietly losing its traceability.
    filler_81: str = field(
        default=" " * 20,
        metadata={"dictionary_key": _KEY_INDEX[("FILLER", 81)]},
    )

    pass_value: int = 0

    level: Level = field(default_factory=Level)

    pass_word: str = " " * 4

    host: int = 0

    op_system: int = 0

    current_quarter: int = 0

    rdbms_flat_statuses: RdbmsFlatStatuses = field(
        default_factory=RdbmsFlatStatuses
    )

    maps_ser: MapsSer = field(default_factory=MapsSer)

    # 05 Date-Form pic 9 -> int, digits 1, scale 0 [copybooks/wssystem.cob:L128] column
    # SYSTEM-REC.DATE-FORM tinyint(1) unsigned 88 condition names, verbatim - predicates
    # belong to acas_posting/cobol/condition_names.py (plan section 0.4.1.4).
    date_form: int = 0

    data_capture_used: int = 0

    # 05 RDBMS-DB-Name pic x(12) value "ACASDB" str, 12 chars
    # [copybooks/wssystem.cob:L137] column SYSTEM-REC.RDBMS-DB-NAME char(12) port at
    # L142).
    rdbms_db_name: str = "ACASDB".ljust(12)

    rdbms_user: str = "ACAS-User".ljust(12)

    # 05 RDBMS-Passwd pic x(12) value <the shipped placeholder>
    # str, 12 chars   [copybooks/wssystem.cob:L139]
    # column SYSTEM-REC.RDBMS-PASSWD char(12)
    #
    # `repr=False`, AND NOTHING ELSE ABOUT THIS FIELD CHANGES. It is still
    # declared here, in this position, as `x(12)`, with the copybook's own
    # placeholder `VALUE` padded to twelve characters exactly as before - so the
    # layout, the declaration order, the default, the `FIELDS` tuple above and
    # every dictionary and descriptor lookup are byte-for-byte what they were
    # (rules R-3 and R-5). The column it maps to is untouched, and the value still
    # reaches `RDB-Data.DB-UPass` through the six frozen moves
    # [common/acas008.cbl:L558-L563].
    #
    # What changes is the DEFAULT `__repr__` this dataclass generates. SYSTEM-REC
    # is the largest record in the migration - 169 columns of company identity,
    # addresses and operator names - and rendering it whole put a password in the
    # middle of that. Nothing in the cycle renders the block today, which is why
    # this is INFO rather than a live leak; but the hazard is one
    # `_LOG.debug("%s", system_record)` or one failing assertion away, and a
    # password written to a log cannot be taken back (CWE-532).
    #
    # THE VALUE IS NOT MASKED, only its rendering omitted, and the credential
    # question itself is settled elsewhere and is not reopened here:
    # `carries_frozen_placeholder_rdbms_credentials` still reads this field, and
    # `dal/connection.py` still refuses to authenticate with the shipped
    # placeholder unless the caller declares the server disposable.
    rdbms_passwd: str = field(default="PaSsWoRd".ljust(12), repr=False)

    vat_reg_number: str = " " * 11

    param_restrict: str = " "

    rdbms_port: str = "3306".ljust(5)

    rdbms_host: str = " " * 32

    rdbms_socket: str = " " * 64

    stats_date_period: int = 0

    company_email: str = " " * 30


# =============================================================================
#  THE FROZEN PLACEHOLDER RDBMS CREDENTIALS  (declared above, published here)
# =============================================================================
#  The four items at [copybooks/wssystem.cob:L137-L139] and L142 are the only
#  place in the whole migrated cycle where a user name, a password, a schema
#  name and a port arrive from a SOURCE LITERAL rather than from a stored row,
#  and the maintainer annotated every one of the four lines `*> change in
#  setup`. They are shipped placeholders: an installer is expected to replace
#  them before the system ever reaches a real server.
#
#  This module DECLARES them and must keep declaring them byte-for-byte, for
#  two reasons that are both hard constraints. `SYSTEM-REC` is one of the 22
#  tables the scenario comparison dumps, so its 169 declared defaults are
#  diff-visible and changing one would move a compared value (rule R-4). And
#  reading a credential from the process environment, a dotenv file or a
#  parameter file would introduce an ambient input the frozen source does not
#  have, which rule R-6 (determinism) and rule R-3 (nothing added) both forbid.
#
#  What this section adds is therefore NOT a change of behaviour but a way to
#  ASK a question: "is this record still carrying the shipped placeholders?"
#  `acas_posting/dal/connection.py` is the one module that reaches a real
#  server, and on a yes it reports the exposure - and refuses only when the
#  deployment's installed policy asked it to, since the compiled program applies
#  no such check (rule R-3). Publishing the four values here - read out of
#  this module's own declared defaults, never transcribed a second time - is
#  what lets that module do so without owning a copy of the literals.
#
#  Nothing below is applied by this module: constructing a `SystemDataBlock` or
#  a `SystemRecord` behaves exactly as it did before, and the predicate is a
#  pure query over a record the caller already holds.


def _declared_system_data_block() -> SystemDataBlock:
    """Return a fresh `System-Data-Block` holding only its declared defaults.

    Returns:
        A `SystemDataBlock` whose items carry exactly what the frozen copybook declares.
    """
    return SystemDataBlock()


FROZEN_PLACEHOLDER_RDBMS_DB_NAME: Final[str] = (
    _declared_system_data_block().rdbms_db_name
)

FROZEN_PLACEHOLDER_RDBMS_USER: Final[str] = (
    _declared_system_data_block().rdbms_user
)

# `05 RDBMS-Passwd pic x(12)` carries a shipped placeholder `value` clause
# [copybooks/wssystem.cob:L139] - a password in plain source text.
FROZEN_PLACEHOLDER_RDBMS_PASSWD: Final[str] = (
    _declared_system_data_block().rdbms_passwd
)

# `05 RDBMS-Port pic x(5) value "3306"` [copybooks/wssystem.cob:L142]. Not a credential.
FROZEN_PLACEHOLDER_RDBMS_PORT: Final[str] = (
    _declared_system_data_block().rdbms_port
)


def carries_frozen_placeholder_rdbms_credentials(
    system_record: SystemRecord,
) -> bool:
    """Report whether `SYSTEM-REC` still carries the shipped credentials.

    The test is an OR rather than an AND, and that is deliberately the weaker condition
    to satisfy.

    Args:
        system_record: the record a caller is about to open a connection from. Read
            only; never mutated.

    Returns:
        `True` when the user name or the password still equals its declared placeholder,
            `False` when both have been replaced.
    """
    block = system_record.system_data_block
    user_is_placeholder = (
        block.rdbms_user.rstrip() == FROZEN_PLACEHOLDER_RDBMS_USER.rstrip()
    )
    passwd_is_placeholder = (
        block.rdbms_passwd.rstrip() == FROZEN_PLACEHOLDER_RDBMS_PASSWD.rstrip()
    )
    return user_is_placeholder or passwd_is_placeholder


@dataclass(slots=True)
class GeneralLedgerBlock:
    """The `03 General-Ledger-Block.` [copybooks/wssystem.cob:L150]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("P-C", 151),
        _descriptor("P-C-Grouped", 154),
        _descriptor("P-C-Level", 156),
        _descriptor("Comps", 158),
        _descriptor("Comps-Active", 160),
        _descriptor("M-V", 162),
        _descriptor("Arch", 164),
        _descriptor("Trans-Print", 166),
        _descriptor("Trans-Printed", 168),
        _descriptor("Header-Level", 170),
        _descriptor("Sales-Range", 171),
        _descriptor("Purchase-Range", 172),
        _descriptor("Vat", 173),
        _descriptor("Batch-Id", 175),
        _descriptor("Ledger-2nd-Index", 177),
        _descriptor("IRS-Instead", 179),
        _descriptor("Ledger-Sec", 182),
        _descriptor("Updates", 183),
        _descriptor("Postings", 184),
        _descriptor("Next-Batch", 185),
        _descriptor("Extra-Charge-Ac", 186),
        _descriptor("Vat-Ac", 187),
        _descriptor("Print-Spool-Name2", 188),
    )

    p_c: str = " "

    p_c_grouped: str = " "

    p_c_level: str = " "

    comps: str = " "

    comps_active: str = " "

    m_v: str = " "

    arch: str = " "

    trans_print: str = " "

    trans_printed: str = " "

    header_level: int = 0

    sales_range: int = 0

    purchase_range: int = 0

    vat: str = " "

    # 05 Batch-Id pic x str, 1 chars [copybooks/wssystem.cob:L175] column SYSTEM-
    # REC.BATCH-ID char(1) 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4).
    batch_id: str = " "

    ledger_2nd_index: str = " "

    # 05 IRS-Instead pic x -> str, 1 chars [copybooks/wssystem.cob:L179] column SYSTEM-
    # REC.IRS-INSTEAD char(1) 88 condition names, verbatim - predicates belong to
    # acas_posting/cobol/condition_names.py (plan section 0.4.1.4).
    irs_instead: str = " "

    ledger_sec: int = 0

    updates: int = 0

    postings: int = 0

    next_batch: int = 0

    extra_charge_ac: int = 0

    vat_ac: int = 0

    print_spool_name2: str = " " * 48


@dataclass(slots=True)
class PurchaseLedgerBlock:
    """The `03 Purchase-Ledger-Block.` [copybooks/wssystem.cob:L192]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Next-Folio", 193),
        _descriptor("BL-Pay-Ac", 194),
        _descriptor("P-Creditors", 195),
        _descriptor("BL-Purch-Ac", 196),
        _descriptor("BL-End-Cycle-Date", 197),
        _descriptor("BL-Next-Batch", 198),
        _descriptor("Age-To-Pay", 199),
        _descriptor("Purchase-Ledger", 200),
        _descriptor("PL-Delim", 202),
        _descriptor("Entry-Level", 203),
        _descriptor("P-Flag-A", 204),
        _descriptor("P-Flag-I", 205),
        _descriptor("P-Flag-P", 206),
        _descriptor("PL-Stock-Link", 207),
        _descriptor("Print-Spool-Name3", 208),
        _descriptor("PL-Autogen", 209),
        _descriptor("PL-Next-Rec", 210),
        _descriptor("FILLER", 211),
    )

    next_folio: int = 0

    bl_pay_ac: int = 0

    p_creditors: int = 0

    bl_purch_ac: int = 0

    # 05 BL-End-Cycle-Date binary-long int, signed [copybooks/wssystem.cob:L197] column
    # SYSTEM-REC.BL-END-CYCLE-DAT int(1) unsigned Column name drift: BL-END-CYCLE-DAT.
    # Anomaly A-11 applies.
    bl_end_cycle_date: int = 0

    bl_next_batch: int = 0

    age_to_pay: int = 0

    purchase_ledger: str = " "

    pl_delim: str = " "

    entry_level: int = 0

    p_flag_a: int = 0

    p_flag_i: int = 0

    p_flag_p: int = 0

    pl_stock_link: str = " "

    print_spool_name3: str = " " * 48

    pl_autogen: str = " "

    pl_next_rec: int = 0

    filler_211: str = " " * 7


@dataclass(slots=True)
class SalesLedgerBlock:
    """The `03 Sales-Ledger-Block.` [copybooks/wssystem.cob:L215].

    128 bytes, and the widest of the five subordinate blocks.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Sales-Ledger", 216),
        _descriptor("SL-Delim", 218),
        _descriptor("Oi-3-Flag", 219),
        _descriptor("Cust-Flag", 220),
        _descriptor("Oi-5-Flag", 221),
        _descriptor("S-Flag-Oi-3", 222),
        _descriptor("Full-Invoicing", 223),
        _descriptor("S-Flag-A", 224),
        _descriptor("S-Flag-I", 225),
        _descriptor("S-Flag-P", 226),
        _descriptor("SL-Dunning", 227),
        _descriptor("SL-Charges", 228),
        _descriptor("Sl-Own-Nos", 229),
        _descriptor("SL-Stats-Run", 230),
        _descriptor("Sl-Day-Book", 231),
        _descriptor("invoicer", 232),
        _descriptor("Extra-Desc", 237),
        _descriptor("Extra-Type", 238),
        _descriptor("Extra-Print", 241),
        _descriptor("SL-Stock-Link", 242),
        _descriptor("SL-Stock-Audit", 243),
        _descriptor("SL-Late-Per", 245),
        _descriptor("SL-Disc", 246),
        _descriptor("Extra-Rate", 247),
        _descriptor("SL-Days-1", 248),
        _descriptor("SL-Days-2", 249),
        _descriptor("SL-Days-3", 250),
        _descriptor("SL-Credit", 251),
        _descriptor("FILLER", 252),
        _descriptor("SL-Min", 253),
        _descriptor("SL-Max", 254),
        _descriptor("PF-Retention", 255),
        _descriptor("First-Sl-Batch", 256),
        _descriptor("First-Sl-Inv", 257),
        _descriptor("SL-Limit", 258),
        _descriptor("SL-Pay-Ac", 259),
        _descriptor("S-Debtors", 260),
        _descriptor("SL-Sales-Ac", 261),
        _descriptor("S-End-Cycle-Date", 262),
        _descriptor("SL-Comp-Head-Pick", 263),
        _descriptor("SL-Comp-Head-Inv", 265),
        _descriptor("SL-Comp-Head-Stat", 267),
        _descriptor("SL-Comp-Head-Lets", 269),
        _descriptor("SL-VAT-Printed", 271),
        _descriptor("SL-Invoice-Lines", 273),
        _descriptor("SL-Autogen", 274),
        _descriptor("SL-Next-Rec", 275),
        _descriptor("SL-BO-Flag", 276),
        _descriptor("SL-BO-Default", 277),
        _descriptor("FILLER", 278),
        _descriptor("GL-BL-Pay-Ac", 280),
        _descriptor("GL-P-Creditors", 281),
        _descriptor("GL-BL-Purch-Ac", 282),
        _descriptor("GL-SL-Pay-Ac", 283),
        _descriptor("GL-S-Debtors", 284),
        _descriptor("GL-SL-Sales-Ac", 285),
    )

    sales_ledger: str = " "

    sl_delim: str = " "

    oi_3_flag: str = " "

    cust_flag: str = " "

    oi_5_flag: str = " "

    s_flag_oi_3: str = " "

    full_invoicing: int = 0

    s_flag_a: int = 0

    s_flag_i: int = 0

    s_flag_p: int = 0

    sl_dunning: int = 0

    sl_charges: int = 0

    sl_own_nos: str = " "

    sl_stats_run: int = 0

    sl_day_book: int = 0

    invoicer: int = 0

    extra_desc: str = " " * 14

    extra_type: str = " "

    extra_print: str = " "

    sl_stock_link: str = " "

    sl_stock_audit: str = " "

    sl_late_per: decimal.Decimal = decimal.Decimal("0.00")

    sl_disc: decimal.Decimal = decimal.Decimal("0.00")

    extra_rate: decimal.Decimal = decimal.Decimal("0.00")

    sl_days_1: int = 0

    sl_days_2: int = 0

    sl_days_3: int = 0

    sl_credit: int = 0

    filler_252: int = 0

    sl_min: int = 0

    sl_max: int = 0

    pf_retention: int = 0

    first_sl_batch: int = 0

    first_sl_inv: int = 0

    sl_limit: int = 0

    sl_pay_ac: int = 0

    s_debtors: int = 0

    sl_sales_ac: int = 0

    # 05 S-End-Cycle-Date binary-long int, signed [copybooks/wssystem.cob:L262] column
    # SYSTEM-REC.S-END-CYCLE-DAT int(8) unsigned Column name drift: S-END-CYCLE-DAT.
    # Anomaly A-11 applies.
    s_end_cycle_date: int = 0

    sl_comp_head_pick: str = " "

    sl_comp_head_inv: str = " "

    sl_comp_head_stat: str = " "

    sl_comp_head_lets: str = " "

    sl_vat_printed: str = " "

    sl_invoice_lines: int = 0

    sl_autogen: str = " "

    sl_next_rec: int = 0

    sl_bo_flag: str = " "

    sl_bo_default: str = " "

    filler_278: str = " " * 14

    # 05 GL-BL-Pay-Ac binary-long int, signed [copybooks/wssystem.cob:L280] column
    # SYSTEM-REC.GL-BL-PAY-AC int(8) unsigned MISPLACED BLOCK (R-4).
    gl_bl_pay_ac: int = 0

    gl_p_creditors: int = 0

    gl_bl_purch_ac: int = 0

    gl_sl_pay_ac: int = 0

    gl_s_debtors: int = 0

    gl_sl_sales_ac: int = 0


@dataclass(slots=True)
class StockControlBlock:
    """The `03 Stock-Control-Block.` [copybooks/wssystem.cob:L290]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Stk-Abrev-Ref", 291),
        _descriptor("Stk-Debug", 292),
        _descriptor("Stk-Manu-Used", 293),
        _descriptor("Stk-OE-Used", 294),
        _descriptor("Stk-Audit-Used", 295),
        _descriptor("Stk-Mov-Audit", 296),
        _descriptor("Stk-Period-Cur", 297),
        _descriptor("Stk-Period-dat", 298),
        _descriptor("FILLER", 299),
        _descriptor("Stock-Control", 300),
        _descriptor("Stk-Averaging", 302),
        _descriptor("Stk-Activity-Rep-Run", 304),
        _descriptor("Stk-BO-Active", 305),
        _descriptor("Stk-Page-Lines", 306),
        _descriptor("Stk-Audit-No", 307),
        _descriptor("FILLER", 308),
    )

    stk_abrev_ref: str = " " * 6

    stk_debug: int = 0

    stk_manu_used: int = 0

    stk_oe_used: int = 0

    stk_audit_used: int = 0

    stk_mov_audit: int = 0

    stk_period_cur: str = " "

    stk_period_dat: str = " "

    filler_299: str = " "

    stock_control: str = " "

    stk_averaging: int = 0

    stk_activity_rep_run: int = 0

    stk_bo_active: str = " "

    stk_page_lines: int = 0

    stk_audit_no: int = 0

    filler_308: str = " " * 68


@dataclass(slots=True)
class VatRates2:
    """The `05 Vat-Rates2.` group [copybooks/wssystem.cob:L312].

    Three IRS VAT rates. Deliberately NOT the same storage class as the five-rate group
    at L55: no usage clause appears on this group header, so these three are zoned
    display. See the note on the attributes below.
    """

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("vat1", 313),
        _descriptor("vat2", 314),
        _descriptor("vat3", 315),
    )

    vat1: decimal.Decimal = decimal.Decimal("0.00")

    vat2: decimal.Decimal = decimal.Decimal("0.00")

    vat3: decimal.Decimal = decimal.Decimal("0.00")


@dataclass(slots=True)
class VatGroup:
    """The `Vat-Group` view over `Vat-Rates2` [copybooks/wssystem.cob:L316]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Vat-Psent", 317),
    )

    vat_psent: list[decimal.Decimal] = field(
        default_factory=lambda: [decimal.Decimal("0.00")] * 3
    )


@dataclass(slots=True)
class PlAppropAc6Parts:
    """The anonymous view over `PL-Approp-AC6` [copybooks/wssystem.cob:L323]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("FILLER", 324),
        _descriptor("PL-Approp-AC", 325),
    )

    filler_324: int = 0

    pl_approp_ac: int = 0


@dataclass(slots=True)
class IrsEntryBlock:
    """The `03 IRS-Entry-Block.` [copybooks/wssystem.cob:L309]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("Client", 310),
        _descriptor("Next-Post", 311),
        _descriptor("Vat-Rates2", 312),
        _descriptor("Vat-Group", 316),
        _descriptor("IRS-Pass-Value", 318),
        _descriptor("Save-Sequ", 319),
        _descriptor("System-Work-Group", 320),
        _descriptor("PL-App-Created", 321),
        _descriptor("PL-Approp-AC6", 322),
        _descriptor("FILLER", 323),
        _descriptor("1st-Time-Flag", 326),
        _descriptor("FILLER", 327),
    )

    client: str = " " * 24

    next_post: int = 0

    # 05 Vat-Rates2 group item - no storage of its own [copybooks/wssystem.cob:L312] NO
    # GROUP USAGE on this line, so the three items at L313-L315 are genuinely DISPLAY -
    # zoned decimal.
    vat_rates2: VatRates2 = field(default_factory=VatRates2)

    vat_group: VatGroup = field(default_factory=VatGroup)

    irs_pass_value: int = 0

    save_sequ: int = 0

    system_work_group: str = " " * 18

    pl_app_created: str = " "

    pl_approp_ac6: int = 0

    filler_323: PlAppropAc6Parts = field(default_factory=PlAppropAc6Parts)

    # 05 1st-Time-Flag pic 9 int, digits 1, scale 0 [copybooks/wssystem.cob:L326] column
    # SYSTEM-REC.1ST-TIME-FLAG tinyint(1) unsigned RENAMED ATTRIBUTE (R-4).
    first_time_flag: int = 0

    filler_327: str = " " * 59


@dataclass(slots=True)
class IrsDataBlock:
    """The `IRS-Data-Block` view [copybooks/wssystem.cob:L328]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("FILLER-Dummy4", 329),
    )

    filler_dummy4: str = " " * 128


@dataclass(slots=True)
class SystemRecord:
    """The `01 System-Record.` [copybooks/wssystem.cob:L48]."""

    FIELDS: ClassVar[tuple[FieldDescriptor, ...]] = (
        _descriptor("System-Data-Block", 52),
        _descriptor("General-Ledger-Block", 150),
        _descriptor("Purchase-Ledger-Block", 192),
        _descriptor("Sales-Ledger-Block", 215),
        _descriptor("Stock-Control-Block", 290),
        _descriptor("IRS-Entry-Block", 309),
        _descriptor("IRS-Data-Block", 328),
    )

    system_data_block: SystemDataBlock = field(default_factory=SystemDataBlock)

    general_ledger_block: GeneralLedgerBlock = field(
        default_factory=GeneralLedgerBlock
    )

    purchase_ledger_block: PurchaseLedgerBlock = field(
        default_factory=PurchaseLedgerBlock
    )

    sales_ledger_block: SalesLedgerBlock = field(
        default_factory=SalesLedgerBlock
    )

    stock_control_block: StockControlBlock = field(
        default_factory=StockControlBlock
    )

    irs_entry_block: IrsEntryBlock = field(default_factory=IrsEntryBlock)

    irs_data_block: IrsDataBlock = field(default_factory=IrsDataBlock)
