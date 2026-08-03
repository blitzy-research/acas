"""PIC-clause field descriptors: the foundation of the arithmetic parity tier.

WHAT THIS FILE PROVES
    That a `FieldDescriptor` models one COBOL data item exactly as the frozen source
    declares it - its usage class, its sign and where the sign lives, its digit count,
    its integer digits, its scale, its character length, its byte length, its value
    domain, its quantum and its Python carrier - and that where the copybook, the
    generated bridge and the MySQL column DISAGREE, the disagreement is exposed as
    disagreement rather than reconciled into one winning answer.

    File 1 of 14 in `tests/arithmetic/`. Every later file in the folder assumes the
    descriptors are right, so nothing here may be taken on trust.

PROVENANCE OF THE RULES
    THERE IS NO USER RULES DOCUMENT for this project: `review_rules` returns exactly
    "No user rules provided.", so no rules file exists on disk and none should be looked
    for. The six binding rules R-1 .. R-6 live in the Technical Specification section
    0.7.2, and where that specification is silent this file holds to enterprise-standard
    best practice and invents nothing.

HOW THE SIX RULES BIND HERE
    R-1  No COBOL at runtime. This module imports `pytest`, `decimal` and four
         `acas_posting` modules. It spawns no process, binds no foreign library, and
         reaches neither the oracle harness, nor the data-access layer, nor a database
         driver, nor a SQL toolkit; `test_tier_touches_no_database_and_no_oracle`
         asserts that mechanically from the modules the run actually loaded. The whole
         file runs on a bare host with no Docker, no MariaDB and no GnuCOBOL. Its one
         file-system prerequisite is that `data_dictionary/acas_posting_dictionary.json`
         is on disk, which is a FILE prerequisite and not an infrastructure one.

    R-2  Zero binary floating point. Every scaled quantity here is a `decimal.Decimal`
         built from a string and every unscaled one is an `int`. There is no
         binary-float literal, no coercion to one, no approximate-comparison helper, no
         closeness test and no tolerance of any kind: a descriptor either models the
         declaration exactly or it does not. Nothing reads or mutates the ambient
         decimal context, because a test that shifted the global context could change a
         posted figure in an unrelated test.

    R-3  No new validation, no new field, no schema change, no concurrency. Every
         assertion below reads a declaration; none adds a rule the COBOL does not have,
         and where the frozen sources contradict themselves the contradiction is
         recorded and left standing. Execution is strictly sequential - there is no
         parallel-execution plugin, which is deliberately absent from the pinned
         dependency set, and no randomised ordering.

    R-4  Legacy anomalies are reproduced, never fixed. "A defect reproduced is correct;
         a defect fixed is a failure." A test that asserted CORRECT ACCOUNTING instead
         of OBSERVED BEHAVIOUR would itself be a defect. Five anomalies are locked in
         place here, each in its own named test so that a failure names the anomaly:

             A-7   the three IRS date-component columns the bridge derives and no
                   copybook declares  [common/irspostingMT.cbl:L982-L987]
             A-11  a signed value narrowed to an unsigned host variable, losing its sign
                   at the bridge before any SQL runs  [copybooks/wssl.cob:L43-L53]
             A-12  the ledger name at 24 characters in the copybook and 32 in both the
                   host variable and the column  [common/nominalMT.cbl:L299]
             A-15  the batch record's two contradictory declared lengths
                   [copybooks/wsbatch.cob:L7-L9]
             A-20  two spare fields carrying the Sales prefix inside the Purchase group
                   [copybooks/wssys4.cob:L29-L30]

         And THE DECLARATION WINS OVER THE MAINTAINER'S OWN COMMENT. Three of his
         declarations carry a trailing comment that contradicts them; each is asserted
         against the DECLARATION, with the comment recorded in the test's own provenance
         note and settled nowhere.

    R-5  Full traceability. Every descriptor in this file carries either a
         `dictionary_key` or a `<path>:L<n>` `source_locator`, and
         `test_a_descriptor_with_neither_a_key_nor_a_locator_cannot_be_built` proves
         such a descriptor cannot be built at all. Every anomaly-locking test names its
         number and its `[path:Lnnn]`. Coverage measurement is EVIDENCE, never a gate:
         nothing here adds a coverage failure threshold, because a coverage number never
         decides whether this migration is correct.

         There is deliberately no reconciled, single-winner type, view, value or picture
         anywhere in this system, and
         `test_no_single_winner_view_exists_on_drift_entry_or_descriptor` enforces that
         structurally over a list of forbidden member names.

    R-6  Compiled behaviour is the tie-breaker, and this file cites zero oracle runs
         BECAUSE IT ASSERTS NO COMPUTED VALUE. Every expectation below is a DECLARATION
         read out of a frozen line - a picture clause, a USAGE clause, a SIGN clause, a
         group header, a schema column - carried into
         `data_dictionary/acas_posting_dictionary.json` by
         `acas_posting.dictionary.generate`, which parses the frozen sources rather than
         reasoning about them. Running the compiled program cannot change what a picture
         clause says, so there is nothing here for an oracle to arbitrate.

         Where a question about a STORED VALUE genuinely is open, this file asserts only
         that the open question is RECORDED and never what its answer is:

             Q-3  what a negative binary value becomes once it has passed through an
                  unsigned host variable into an unsigned column
             Q-4  which of the batch record's two declared lengths governs the record
                  that is actually read

         Both are asserted through `ambiguity_refs()` alone. Consequently this file
         carries NO expected-failure marker: one would have to stand in for a value
         nobody has measured, and no such value is asserted here. Section 0.8.4 also
         applies - there is no timing assertion and no performance measurement anywhere.

WHERE THIS FILE DIVERGES FROM ITS OWN BRIEF, AND WHY
    The brief for this file was written against an earlier shape of the API and three of
    its statements do not match the code as committed. In each case the CODE governs,
    because a test must bind to the module it tests:

      * `FieldDescriptor.for_working_storage` no longer exists - see the note at
        [acas_posting/cobol/field.py:L533-L534]. A program-local field is therefore
        described through `picture.descriptor_for`, which is precisely the route
        `FieldDescriptor.__post_init__` names for a bare `<path>:L<n>` locator.
      * Two keys in the brief are near misses: `SYSTEM-REC.RUN-DATE` is really
        `SYSTEM-REC.RUN-DAT` and `PSIRSPOST-REC.POST-AMOUNT` is really
        `PSIRSPOST-REC.IRS-POST-AMOUNT`. Both are found at run time by
        `_dictionary_key_for`, never by a hard-coded guess.
      * `work-2` at [sales/sl060.cbl:L206] is `pic s9(14) comp-3`, so its scale is zero
        and `usage.python_storage_for` gives it an `int` carrier, not a `Decimal` one.
        The observed carrier is asserted.

    Three line numbers in the brief were also checked against the checkout and are
    restated here from the source: the nine `binary-long` host variables span
    [common/salesMT.cbl:L304-L312] and the full signed-to-unsigned block spans
    L302-L312; `line-cnt` is declared `binary-char` at [sales/sl100.cbl:L173];
    and the bridge-only `POST4-DAY` column sits at [mysql/ACASDB.sql:L278].
"""

from __future__ import annotations

import copy
import json
import pathlib
import re
import sys
from decimal import Decimal
from typing import Any, Final

import pytest

from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import picture as cobol_picture
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model

pytestmark = pytest.mark.arithmetic


#  THE DEFENSIVE KEY RESOLVER  (R-5)
#
#  An entry key is `<TABLE-NAME>.<COLUMN-NAME>`, and the COLUMN name is the schema's,
#  not the copybook's. The frozen DDL demonstrably shortens a `-DATE` suffix to `-DAT`:
#  the host variable is `HV-SALES-CREATE-DAT` [common/salesMT.cbl:L312] and the columns
#  are `GLPOSTING-REC.POST-DAT`, `IRSPOSTING-REC.POST4-DAT` and
#  `PSIRSPOST-REC.IRS-POST-DAT`. A test that hard-coded `SYSTEM-REC.RUN-DATE` would fail
#  for a reason that has nothing to do with the field it is describing.
#
#  So the key is asked for by the pair a reader can verify against the frozen source -
#  the table, and the COPYBOOK field name declared in it - and the column spelling is
#  DISCOVERED. This helper is deliberately local to this file rather than shared: it is
#  a reading convenience for these tests and not a part of the migrated system.


def _dictionary_key_for(table: str, copybook_field: str) -> str:
    """Find the entry key for one copybook field of one table.

    Args:
        table: The table name as the frozen schema spells it, for example
            `"SALEDGER-REC"`.
        copybook_field: The field name as the COPYBOOK spells it, case and hyphens
            verbatim, for example `"Run-Date"`.

    Returns:
        The single entry key whose copybook view declares that field.

    Raises:
        AssertionError: No entry of that table declares the field, or more than one
            does. Both are reported rather than papered over, because either would mean
            the assertion below was describing something other than the field named.
    """
    matches = tuple(
        entry.key
        for entry in loader.entries_for_table(table)
        if entry.copybook is not None and entry.copybook.name == copybook_field
    )
    if len(matches) == 1:
        return matches[0]
    declared = sorted(
        entry.copybook.name
        for entry in loader.entries_for_table(table)
        if entry.copybook is not None
    )
    raise AssertionError(
        f"expected exactly one entry of {table} to declare the copybook field "
        f"{copybook_field!r}, found {len(matches)}: {matches}. The fields "
        f"{table} declares are {declared}."
    )


def _descriptor_for(table: str, copybook_field: str) -> cobol_field.FieldDescriptor:
    """Describe one copybook field of one table, by discovered key.

    Args:
        table: The table name as the frozen schema spells it.
        copybook_field: The field name as the copybook spells it.

    Returns:
        The descriptor the generated dictionary holds for that field.
    """
    return cobol_field.FieldDescriptor.from_dictionary_key(
        _dictionary_key_for(table, copybook_field)
    )


#  The words this system deliberately has no member named, anywhere. Drift is exposed
#  unadjudicated (R-4), so there is no single-winner view to name.
_FORBIDDEN_MEMBER_WORDS: tuple[str, ...] = (
    "resolved",
    "canonical",
    "effective",
    "authoritative",
    "corrected",
    "recommended",
    "preferred",
)


#  GROUP 1  -  DESCRIPTOR ROUND-TRIPS FROM DICTIONARY KEYS
#
#  Provenance for every row of the table below, and for every row of every table in this
#  file: the expectation is a DECLARATION read out of the frozen line cited beside it,
#  carried into data_dictionary/acas_posting_dictionary.json by
#  acas_posting.dictionary.generate, which parses the frozen sources rather than
#  reasoning about them. No oracle run is cited because no computed value is asserted -
#  running the compiled program cannot change what a picture clause says (R-6).


@pytest.mark.parametrize(
    (
        "table",
        "copybook_field",
        "usage",
        "signed",
        "picture",
        "digits",
        "integer_digits",
        "scale",
        "character_length",
        "storage",
        "byte_length",
        "quantum",
        "locator",
    ),
    [
        # spec: [copybooks/wssl.cob:L49]
        #           03  Sales-Average      binary-long. *> 9(8) comp
        #       -> [common/salesMT.cbl:L308]
        #           05  HV-SALES-AVERAGE                  PIC  9(10) COMP.
        #       -> [mysql/ACASDB.sql:L969]
        #           `SALES-AVERAGE` int(8) unsigned NOT NULL,
        #       No picture and no scale: the width comes from the class, so the carrier
        #       is int and a store into it has no quantum to round to. This is the
        #       carrier that makes the legacy moving-average truncation reproducible.
        pytest.param(
            "SALEDGER-REC",
            "Sales-Average",
            model.Usage.BINARY_LONG,
            True,
            None,
            None,
            None,
            None,
            None,
            model.CobolPythonStorage.INT,
            4,
            None,
            "copybooks/wssl.cob:L49",
            id="SALEDGER-REC.Sales-Average-binary-long",
        ),
        # spec: [copybooks/wssl.cob:L54]
        #           03  Sales-Current      pic s9(8)v99       comp-3.
        #       -> [common/salesMT.cbl:L313]
        #           05  HV-SALES-CURRENT                  PIC S9(08)V9(02) COMP.
        #       Signed at all three layers, so it passes through cleanly. Ten digits in
        #       six bytes: one digit per nibble plus a sign nibble, rounded up.
        pytest.param(
            "SALEDGER-REC",
            "Sales-Current",
            model.Usage.COMP_3,
            True,
            "s9(8)v99",
            10,
            8,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            6,
            Decimal("0.01"),
            "copybooks/wssl.cob:L54",
            id="SALEDGER-REC.Sales-Current-comp-3",
        ),
        # spec: [copybooks/wssl.cob:L42]
        #           03  Sales-Discount     pic 99v99          comp.
        #       -> [common/salesMT.cbl:L301]
        #           05  HV-SALES-DISCOUNT                 PIC  9(02)V9(02) COMP.
        #       COMP *with* a scale. Four digits fit a two-byte binary field, and the
        #       scale is the picture's, not the storage class's.
        pytest.param(
            "SALEDGER-REC",
            "Sales-Discount",
            model.Usage.COMP,
            False,
            "99v99",
            4,
            2,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            2,
            Decimal("0.01"),
            "copybooks/wssl.cob:L42",
            id="SALEDGER-REC.Sales-Discount-comp-with-scale",
        ),
        # spec: [copybooks/wsbatch.cob:L40-L41]
        #           03  Amounts                         comp-3.
        #               05  Input-Gross     pic 9(9)v99.
        #       Eleven digits, UNSIGNED, in six bytes - the sign nibble is spent even
        #       though there is no sign to put in it. The usage is the group's; see
        #       GROUP 3.
        pytest.param(
            "GLBATCH-REC",
            "Input-Gross",
            model.Usage.COMP_3,
            False,
            "9(9)v99",
            11,
            9,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            6,
            Decimal("0.01"),
            "copybooks/wsbatch.cob:L41",
            id="GLBATCH-REC.Input-Gross-group-inherited-comp-3",
        ),
        # spec: [copybooks/wsbatch.cob:L36]
        #           05  Entered         binary-long.
        #       -> [common/glbatchMT.cbl:L287]
        #           05  HV-ENTERED                        PIC  9(10) COMP.
        #       A binary item may carry NO PICTURE AT ALL, and this one does not.
        pytest.param(
            "GLBATCH-REC",
            "Entered",
            model.Usage.BINARY_LONG,
            True,
            None,
            None,
            None,
            None,
            None,
            model.CobolPythonStorage.INT,
            4,
            None,
            "copybooks/wsbatch.cob:L36",
            id="GLBATCH-REC.Entered-binary-long-no-picture",
        ),
        # spec: [copybooks/wsledger.cob:L27]
        #           03  Ledger-Name       pic x(24).
        #       -> [common/nominalMT.cbl:L299]
        #           05  HV-LEDGER-NAME                    PIC X(32).
        #       -> [mysql/ACASDB.sql:L127]
        #           `LEDGER-NAME` char(32) NOT NULL,
        #       The COPYBOOK view is twenty-four characters and stays twenty-four here.
        #       Anomaly A-12; see GROUP 5.
        pytest.param(
            "GLLEDGER-REC",
            "Ledger-Name",
            model.Usage.ALPHANUMERIC,
            False,
            "x(24)",
            None,
            None,
            None,
            24,
            model.CobolPythonStorage.STR,
            24,
            None,
            "copybooks/wsledger.cob:L27",
            id="GLLEDGER-REC.Ledger-Name-alphanumeric-24",
        ),
        # spec: [copybooks/wsledger.cob:L28]
        #           03  Ledger-Balance    pic s9(8)v99   comp-3.
        #       -> [mysql/ACASDB.sql:L128]
        #           `LEDGER-BALANCE` decimal(10,2) NOT NULL,
        #       The one accumulator gl072 posts into, and it maps cleanly.
        pytest.param(
            "GLLEDGER-REC",
            "Ledger-Balance",
            model.Usage.COMP_3,
            True,
            "s9(8)v99",
            10,
            8,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            6,
            Decimal("0.01"),
            "copybooks/wsledger.cob:L28",
            id="GLLEDGER-REC.Ledger-Balance-comp-3",
        ),
        # spec: [copybooks/wspost.cob:L23]
        #           03  Post-Amount     pic s9(8)v99.  *> 46
        #       Zoned DISPLAY with the sign overpunched on the trailing digit, so ten
        #       digits occupy ten bytes. Proved from the copybook's own running byte
        #       offsets in GROUP 2.
        pytest.param(
            "GLPOSTING-REC",
            "Post-Amount",
            model.Usage.DISPLAY,
            True,
            "s9(8)v99",
            10,
            8,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            10,
            Decimal("0.01"),
            "copybooks/wspost.cob:L23",
            id="GLPOSTING-REC.Post-Amount-zoned-trailing-sign",
        ),
        # spec: [copybooks/wspost-irs.cob:L21]
        #           03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.
        #       Nine digits, leading sign INCLUDED in the first digit position, so nine
        #       bytes. Distinct from the record below; see GROUP 1's pairing test.
        pytest.param(
            "PSIRSPOST-REC",
            "WS-IRS-Post-Amount",
            model.Usage.DISPLAY,
            True,
            "s9(7)v99",
            9,
            7,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            9,
            Decimal("0.01"),
            "copybooks/wspost-irs.cob:L21",
            id="PSIRSPOST-REC.WS-IRS-Post-Amount-sign-leading",
        ),
        # spec: [copybooks/irswspost.cob:L14]
        #           03  Post-Amount     pic s9(7)v99  sign is leading.
        #       The INTERNAL IRS posting record. Same storage shape, different record,
        #       different sign-clause spelling.
        pytest.param(
            "IRSPOSTING-REC",
            "Post-Amount",
            model.Usage.DISPLAY,
            True,
            "s9(7)v99",
            9,
            7,
            2,
            None,
            model.CobolPythonStorage.DECIMAL,
            9,
            Decimal("0.01"),
            "copybooks/irswspost.cob:L14",
            id="IRSPOSTING-REC.Post-Amount-sign-is-leading",
        ),
        # spec: [copybooks/wssystem.cob:L67]
        #           05  Run-Date        binary-long. *> 9(8) comp.
        #       One of the two observables acas_posting/clock.py pins. Its COLUMN is
        #       spelled RUN-DAT, which is why the key is discovered and never written
        #       out.
        pytest.param(
            "SYSTEM-REC",
            "Run-Date",
            model.Usage.BINARY_LONG,
            True,
            None,
            None,
            None,
            None,
            None,
            model.CobolPythonStorage.INT,
            4,
            None,
            "copybooks/wssystem.cob:L67",
            id="SYSTEM-REC.Run-Date-binary-long",
        ),
        # spec: [copybooks/wssystem.cob:L65]
        #           05  Page-Lines      binary-char  unsigned. *> 999. Portrait/default
        #       The explicit UNSIGNED keyword, which is not the same thing as merely
        #       being unsigned; see GROUP 4 for the domain it really has.
        pytest.param(
            "SYSTEM-REC",
            "Page-Lines",
            model.Usage.BINARY_CHAR,
            False,
            None,
            None,
            None,
            None,
            None,
            model.CobolPythonStorage.INT,
            1,
            None,
            "copybooks/wssystem.cob:L65",
            id="SYSTEM-REC.Page-Lines-binary-char-unsigned",
        ),
    ],
)
def test_descriptor_round_trips_from_its_dictionary_key(
    table: str,
    copybook_field: str,
    usage: model.Usage,
    signed: bool,
    picture: str | None,
    digits: int | None,
    integer_digits: int | None,
    scale: int | None,
    character_length: int | None,
    storage: model.CobolPythonStorage,
    byte_length: int,
    quantum: Decimal | None,
    locator: str,
) -> None:
    """Prove a descriptor reproduces its declaration's storage shape exactly.

    Twelve fields covering all six numeric storage classes plus the alphanumeric one,
    each asserted against the frozen line named in the parameter's own comment.
    """
    descriptor = _descriptor_for(table, copybook_field)

    assert descriptor.name == copybook_field
    assert descriptor.usage is usage
    assert descriptor.signed is signed
    assert descriptor.picture == picture
    assert descriptor.digits == digits
    assert descriptor.integer_digits == integer_digits
    assert descriptor.scale == scale
    assert descriptor.character_length == character_length
    assert descriptor.python_storage is storage
    assert descriptor.byte_length == byte_length
    assert descriptor.quantum == quantum
    assert descriptor.source_locator == locator

    # R-5: the descriptor carries a key, and its citation leads a reader to the line.
    assert descriptor.dictionary_key == _dictionary_key_for(table, copybook_field)
    assert locator in descriptor.cite()


def test_quantum_is_built_without_reading_the_ambient_decimal_context() -> None:
    """Prove the quantum of a scaled field is the exponent its scale names.

    R-2. `quantum` is what an un-ROUNDED store quantizes to, so it must be exact and it
    must not depend on the ambient context - a fixture that had widened or narrowed the
    global precision would otherwise change a posted figure.
    """
    # spec: [copybooks/wsledger.cob:L28]
    #           03  Ledger-Balance    pic s9(8)v99   comp-3.
    balance = _descriptor_for("GLLEDGER-REC", "Ledger-Balance")
    assert balance.quantum == Decimal("0.01")
    assert balance.quantum is not None
    assert balance.quantum.as_tuple().exponent == -2

    # spec: [copybooks/wssl.cob:L49]  03  Sales-Average      binary-long.
    #       No scale at all, so there is no exponent to quantize to.
    average = _descriptor_for("SALEDGER-REC", "Sales-Average")
    assert average.scale is None
    assert average.quantum is None


def test_the_two_leading_sign_records_stay_distinct() -> None:
    """Prove the external and internal IRS posting records never merge.

    Their field names are near-identical and their storage shapes are identical, so only
    the qualified key and the sign-clause spelling tell them apart. The copybook says so
    itself at [copybooks/wspost-irs.cob:L6-L7]:

        *> This is NOT the same as the internal IRS *
        *>   posting file                           *
    """
    # spec: [copybooks/wspost-irs.cob:L21]
    #           03  WS-IRS-Post-Amount     pic s9(7)v99   sign leading.
    #       -> table PSIRSPOST-REC, handler acas008, bridge slpostingMT
    external = _descriptor_for("PSIRSPOST-REC", "WS-IRS-Post-Amount")
    # spec: [copybooks/irswspost.cob:L14]
    #           03  Post-Amount     pic s9(7)v99  sign is leading.
    #       -> table IRSPOSTING-REC, handler acasirsub4, bridge irspostingMT
    internal = _descriptor_for("IRSPOSTING-REC", "Post-Amount")

    # The SIGN clause is carried verbatim, un-normalised, so the two spellings the
    # frozen sources actually use stay distinguishable (R-3, R-4).
    assert external.sign_clause_text == "sign leading"
    assert internal.sign_clause_text == "sign is leading"
    assert external.sign_clause_text != internal.sign_clause_text
    assert cobol_usage.SIGN_LEADING_SPELLINGS == ("sign leading", "sign is leading")
    assert external.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS
    assert internal.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS

    # Both put the sign on the leading digit position, and both are their record's own
    # entry: same shape, different identity.
    assert external.sign_position is model.SignPosition.LEADING_INCLUDED
    assert internal.sign_position is model.SignPosition.LEADING_INCLUDED
    assert external.dictionary_key != internal.dictionary_key
    assert external != internal
    assert external.name == "WS-IRS-Post-Amount"
    assert internal.name == "Post-Amount"


#  GROUP 2  -  BYTE LENGTHS AND VALUE DOMAINS


def test_zoned_display_ten_digit_amount_occupies_exactly_ten_bytes() -> None:
    """Prove the trailing sign is overpunched into the last digit, not held separately.

    NOT AN INFERENCE. [copybooks/wspost.cob] carries the maintainer's own running byte
    offsets in its inline comments, and they settle the question twice over:

        03  CR-PC           pic 99.      *> 36
        03  Post-Amount     pic s9(8)v99.  *> 46
        03  Post-Legend     pic x(32).     *> 76
        03  Vat-AC          pic 9(6).      *> 82
        03  Vat-PC          pic 99.
        03  Post-Vat-Side   pic xx.        *> 86
        03  Vat-Amount      pic s9(8)v99.  *> 96

    CR-PC ends at 36 and Post-Amount ends at 46, so Post-Amount is 46 - 36 = 10 bytes
    for its 10 digit positions; independently Post-Vat-Side ends at 86 and Vat-Amount
    ends at 96, so Vat-Amount is 96 - 86 = 10 bytes for its 10. A separate sign byte
    would have made each eleven and would have pushed every later offset out by one.
    """
    # spec: [copybooks/wspost.cob:L23]  03  Post-Amount     pic s9(8)v99.  *> 46
    amount = _descriptor_for("GLPOSTING-REC", "Post-Amount")
    # spec: [copybooks/wspost.cob:L28]  03  Vat-Amount      pic s9(8)v99.  *> 96
    vat = _descriptor_for("GLPOSTING-REC", "Vat-Amount")

    for descriptor in (amount, vat):
        assert descriptor.usage is model.Usage.DISPLAY
        assert descriptor.is_zoned_display is True
        assert descriptor.signed is True
        assert descriptor.sign_position is model.SignPosition.TRAILING_INCLUDED
        assert descriptor.digits == 10
        assert descriptor.integer_digits == 8
        assert descriptor.scale == 2
        # One byte per digit position and no thirteenth byte for the sign.
        assert descriptor.byte_length == 10
        assert descriptor.byte_length == descriptor.digits


@pytest.mark.parametrize(
    ("table", "copybook_field", "byte_length", "domain", "locator"),
    [
        # spec: [copybooks/wssystem.cob:L65]
        #           05  Page-Lines      binary-char  unsigned. *> 999.
        pytest.param(
            "SYSTEM-REC",
            "Page-Lines",
            1,
            (0, 255),
            "copybooks/wssystem.cob:L65",
            id="binary-char-unsigned",
        ),
        # spec: [copybooks/wssl.cob:L43]  03  Sales-Late-Min     binary-short.
        pytest.param(
            "SALEDGER-REC",
            "Sales-Late-Min",
            2,
            (-32768, 32767),
            "copybooks/wssl.cob:L43",
            id="binary-short-signed",
        ),
        # spec: [copybooks/wssl.cob:L45]  03  Sales-Limit        binary-long.
        pytest.param(
            "SALEDGER-REC",
            "Sales-Limit",
            4,
            (-2147483648, 2147483647),
            "copybooks/wssl.cob:L45",
            id="binary-long-signed",
        ),
        # spec: [copybooks/wsledger.cob:L28]
        #           03  Ledger-Balance    pic s9(8)v99   comp-3.
        #       A packed item's domain is picture-declared: ten nines, signed. The
        #       bounds count HUNDREDTHS, because they are expressed in units of the
        #       item's least significant digit.
        pytest.param(
            "GLLEDGER-REC",
            "Ledger-Balance",
            6,
            (-9999999999, 9999999999),
            "copybooks/wsledger.cob:L28",
            id="comp-3-signed-picture-declared",
        ),
        # spec: [copybooks/wsbatch.cob:L40-L41]
        #           03  Amounts                         comp-3.
        #               05  Input-Gross     pic 9(9)v99.
        pytest.param(
            "GLBATCH-REC",
            "Input-Gross",
            6,
            (0, 99999999999),
            "copybooks/wsbatch.cob:L41",
            id="comp-3-unsigned-picture-declared",
        ),
        # spec: [copybooks/wspost.cob:L23]  03  Post-Amount     pic s9(8)v99.  *> 46
        pytest.param(
            "GLPOSTING-REC",
            "Post-Amount",
            10,
            (-9999999999, 9999999999),
            "copybooks/wspost.cob:L23",
            id="zoned-display-signed",
        ),
    ],
)
def test_byte_length_and_value_domain_follow_the_storage_class(
    table: str,
    copybook_field: str,
    byte_length: int,
    domain: tuple[int, int],
    locator: str,
) -> None:
    """Prove width and range come from the declaration, class by class.

    The binary family takes its range from its HARDWARE WIDTH; the packed and zoned
    classes take theirs from their PICTURE. Collapsing the two rules would silently
    change what fits.
    """
    descriptor = _descriptor_for(table, copybook_field)

    assert descriptor.source_locator == locator
    assert descriptor.byte_length == byte_length
    assert descriptor.value_domain == domain
    assert descriptor.min_value == domain[0]
    assert descriptor.max_value == domain[1]
    # The bounds are whole units of the last digit, so they are ints and never Decimals.
    assert isinstance(descriptor.min_value, int)
    assert isinstance(descriptor.max_value, int)


def test_binary_family_widths_are_the_hardware_widths() -> None:
    """Prove the three binary widths are 1, 2 and 4 bytes and nothing else.

    The published table is the single place width lives, so the descriptors and it must
    agree - otherwise a field could be described one way and stored another.
    """
    # spec: [copybooks/wssystem.cob:L65]  binary-char  -> 1 byte
    #       [copybooks/wssl.cob:L43]      binary-short -> 2 bytes
    #       [copybooks/wssl.cob:L45]      binary-long  -> 4 bytes
    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_CHAR] == 1
    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_SHORT] == 2
    assert cobol_usage.BINARY_WIDTH_BYTES[model.Usage.BINARY_LONG] == 4

    for table, copybook_field in (
        ("SYSTEM-REC", "Page-Lines"),
        ("SALEDGER-REC", "Sales-Late-Min"),
        ("SALEDGER-REC", "Sales-Average"),
    ):
        descriptor = _descriptor_for(table, copybook_field)
        assert descriptor.is_binary_family is True
        assert descriptor.is_int is True
        assert descriptor.byte_length == cobol_usage.BINARY_WIDTH_BYTES[
            descriptor.usage
        ]


#  GROUP 3  -  GROUP-LEVEL USAGE INHERITANCE
#
#  A USAGE clause on a group header governs every subordinate item that does not write
#  one of its own. Reading the picture line alone would class all twenty-four of the
#  fields below as DISPLAY, and every one of them would then be stored - and diffed -
#  wrongly.


@pytest.mark.parametrize(
    "copybook_field",
    ["Input-Gross", "Input-Vat", "Actual-Gross", "Actual-Vat"],
)
def test_batch_amounts_inherit_comp_3_from_their_group_header(
    copybook_field: str,
) -> None:
    """Prove the four batch control amounts are packed, unsigned, 11 digits, 6 bytes.

    These four are the batch control totals gl051's gate compares, so their storage is
    load-bearing for the accept-or-reject decision.
    """
    # spec: [copybooks/wsbatch.cob:L40-L44]
    #           03  Amounts                         comp-3.
    #               05  Input-Gross     pic 9(9)v99.
    #               05  Input-Vat       pic 9(9)v99.
    #               05  Actual-Gross    pic 9(9)v99.
    #               05  Actual-Vat      pic 9(9)v99.
    descriptor = _descriptor_for("GLBATCH-REC", copybook_field)

    assert descriptor.usage is model.Usage.COMP_3
    assert descriptor.is_packed is True
    # The USAGE clause is NOT on this item; it is on the group header above it.
    assert descriptor.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert descriptor.usage_inherited_from == "Amounts"
    assert descriptor.parent_group == "Amounts"
    # Unsigned: the picture writes no S, so the sign nibble is spent on nothing.
    assert descriptor.signed is False
    assert descriptor.sign_position is model.SignPosition.NONE
    assert descriptor.digits == 11
    assert descriptor.integer_digits == 9
    assert descriptor.scale == 2
    assert descriptor.byte_length == 6
    assert descriptor.python_storage is model.CobolPythonStorage.DECIMAL
    assert descriptor.quantum == Decimal("0.01")


@pytest.mark.parametrize(
    ("copybook_field", "locator"),
    [
        ("Vat-Rate-1", "copybooks/wssystem.cob:L56"),
        ("Vat-Rate-2", "copybooks/wssystem.cob:L57"),
        ("Vat-Rate-3", "copybooks/wssystem.cob:L58"),
        ("Vat-Rate-4", "copybooks/wssystem.cob:L59"),
        ("Vat-Rate-5", "copybooks/wssystem.cob:L60"),
    ],
)
def test_system_vat_rates_inherit_comp_from_their_group_header(
    copybook_field: str, locator: str
) -> None:
    """Prove the five VAT rates are binary COMP with a two-place scale.

    A second inheritance shape, one level deeper than the batch amounts: the
    header is at 05 and the rates at 07.
    """
    # spec: [copybooks/wssystem.cob:L55-L60]
    #           05  Vat-Rates                    comp.
    #               07 Vat-Rate-1   pic 99v99.   *> Standard rate
    #               07 Vat-Rate-2   pic 99v99.   *> Reduced rate
    #               07 Vat-Rate-3   pic 99v99.   *> Minimal or exempt
    #               07 Vat-Rate-4   pic 99v99.   *> 2b used for local sales tax  Not UK
    #               07 Vat-Rate-5   pic 99v99.   *> 2b used for local sales tax  Not UK
    descriptor = _descriptor_for("SYSTEM-REC", copybook_field)

    assert descriptor.usage is model.Usage.COMP
    assert descriptor.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert descriptor.usage_inherited_from == "Vat-Rates"
    assert descriptor.parent_group == "Vat-Rates"
    assert descriptor.picture == "99v99"
    assert descriptor.digits == 4
    assert descriptor.integer_digits == 2
    assert descriptor.scale == 2
    assert descriptor.byte_length == 2
    assert descriptor.python_storage is model.CobolPythonStorage.DECIMAL
    assert descriptor.source_locator == locator


@pytest.mark.parametrize("copybook_field", ["vat1", "vat2", "vat3"])
def test_the_second_vat_block_inherits_nothing_and_takes_the_language_default(
    copybook_field: str,
) -> None:
    """Prove a field under a bare group header is DISPLAY by language default.

    THE CONTRAST that makes the two tests above mean something. `Vat-Rates2` writes no
    USAGE clause, so its three subordinates get none to inherit and fall to the language
    default - zoned DISPLAY, four bytes for four digits rather than the two a COMP field
    of the same picture takes. Same picture, same scale, different storage.
    """
    # spec: [copybooks/wssystem.cob:L312-L315]
    #           05  Vat-Rates2.        *> these can be replaced by the other VAT blk
    #               07  vat1           pic 99v99.  *> Standard  changed from vat
    #               07  vat2           pic 99v99.  *> reduced 1 [not yet used]
    #               07  vat3           pic 99v99.  *> reduced 2 [not yet used]
    descriptor = _descriptor_for("SYSTEM-REC", copybook_field)

    assert descriptor.usage is model.Usage.DISPLAY
    # Not GROUP: there is no group USAGE clause to inherit. Not FIELD either - the item
    # writes none of its own - so the language default governs, which is what DEFAULT
    # records.
    assert descriptor.usage_declared_at is model.UsageDeclaredAt.DEFAULT
    assert descriptor.usage_inherited_from is None
    assert descriptor.parent_group == "Vat-Rates2"
    assert descriptor.picture == "99v99"
    assert descriptor.digits == 4
    assert descriptor.scale == 2
    # Four zoned bytes where the COMP twin above takes two.
    assert descriptor.byte_length == 4
    assert _descriptor_for("SYSTEM-REC", "Vat-Rate-1").byte_length == 2
    # The names are the maintainer's own lower-case spellings, preserved (R-3).
    assert descriptor.name == copybook_field


#  GROUP 4  -  THE DECLARATION WINS OVER THE COMMENT  (R-4)
#
#  Three of the maintainer's declarations carry a trailing comment that contradicts
#  them. The ruling is: trust the DECLARATION, record the comment, settle nothing. Each
#  test below quotes the comment verbatim so a reader sees the contradiction, and then
#  asserts what the declaration says.


def test_binary_short_keeps_its_true_sixteen_bit_domain() -> None:
    """Prove `binary-short` is a true 16-bit item, whatever the comment claims.

    The comment says four digits, which would cap the field at 9999. The declaration
    says `binary-short`, which is two bytes and therefore reaches 32767. The
    declaration governs; the comment is recorded here and settled nowhere.
    """
    # spec: [copybooks/wssl.cob:L43-L44]
    #           03  Sales-Late-Min     binary-short. *> 9999 comp
    #           03  Sales-Late-Max     binary-short. *> 9999 comp
    for copybook_field in ("Sales-Late-Min", "Sales-Late-Max"):
        descriptor = _descriptor_for("SALEDGER-REC", copybook_field)
        assert descriptor.usage is model.Usage.BINARY_SHORT
        assert descriptor.signed is True
        assert descriptor.byte_length == 2
        assert descriptor.value_domain == (-32768, 32767)
        # NOT the comment's four-digit range.
        assert descriptor.value_domain != (0, 9999)
        assert descriptor.max_value > 9999
        # No picture is written, so no digit count is declared either.
        assert descriptor.picture is None
        assert descriptor.digits is None


def test_binary_long_keeps_its_true_thirty_two_bit_domain() -> None:
    """Prove `binary-long` is a true 32-bit item, whatever the comment claims.

    The comment says `9(8) comp`, which would cap the field at 99999999. The
    declaration says `binary-long`, which is four bytes and therefore reaches
    2147483647.
    """
    # spec: [copybooks/wssl.cob:L45]
    #           03  Sales-Limit        binary-long. *> 9(8) comp
    descriptor = _descriptor_for("SALEDGER-REC", "Sales-Limit")

    assert descriptor.usage is model.Usage.BINARY_LONG
    assert descriptor.signed is True
    assert descriptor.byte_length == 4
    assert descriptor.value_domain == (-2147483648, 2147483647)
    # NOT the comment's eight-digit range.
    assert descriptor.value_domain != (0, 99999999)
    assert descriptor.max_value > 99999999
    assert descriptor.picture is None
    assert descriptor.digits is None


def test_binary_char_unsigned_maxes_at_255_not_at_the_comment_s_999() -> None:
    """Prove an unsigned `binary-char` stops at 255, whatever the comment claims.

    The most consequential of the three, because the gap is small enough to look
    plausible: the comment says 999 and the declaration gives 255. A page length of 660
    lines - the comment's range would allow it - cannot be stored in this field at all.
    """
    # spec: [copybooks/wssystem.cob:L65]
    #           05  Page-Lines      binary-char  unsigned. *> 999. Portrait / default
    descriptor = _descriptor_for("SYSTEM-REC", "Page-Lines")

    assert descriptor.usage is model.Usage.BINARY_CHAR
    # The explicit UNSIGNED keyword. Distinct from `signed` merely being false: the
    # binary family is signed by DEFAULT, so an unsigned member said so out loud.
    assert descriptor.unsigned is True
    assert descriptor.signed is False
    assert descriptor.byte_length == 1
    assert descriptor.value_domain == (0, 255)
    # NOT the comment's 999.
    assert descriptor.max_value == 255
    assert descriptor.value_domain != (0, 999)


@pytest.mark.parametrize(
    ("copybook_field", "locator"),
    [
        ("Sales-Limit", "copybooks/wssl.cob:L45"),
        ("Sales-Activety", "copybooks/wssl.cob:L46"),
        ("Sales-Last-Inv", "copybooks/wssl.cob:L47"),
        ("Sales-Last-Pay", "copybooks/wssl.cob:L48"),
        ("Sales-Average", "copybooks/wssl.cob:L49"),
        ("Sales-Pay-Activety", "copybooks/wssl.cob:L50"),
        ("Sales-Pay-Average", "copybooks/wssl.cob:L51"),
        ("Sales-Pay-Worst", "copybooks/wssl.cob:L52"),
        ("Sales-Create-Date", "copybooks/wssl.cob:L53"),
    ],
)
def test_all_nine_sales_binary_long_statistics_fields_carry_an_int(
    copybook_field: str, locator: str
) -> None:
    """Prove every one of the NINE `binary-long` sales fields is a 4-byte `int`.

    NINE, not the seven a summary of this copybook gives: the block runs from
    `Sales-Limit` to `Sales-Create-Date` inclusive. The carrier matters beyond
    bookkeeping: `Sales-Average` and `Sales-Pay-Average` are divided into, and an
    `int` carrier is what makes that divide truncate as integer arithmetic does,
    which is the whole reason the migrated moving averages can match the compiled
    ones.
    """
    # spec: [copybooks/wssl.cob:L45-L53]  nine consecutive declarations, each of
    #       the form
    #           03  <name>             binary-long. *> 9(8) comp
    descriptor = _descriptor_for("SALEDGER-REC", copybook_field)

    assert descriptor.source_locator == locator
    assert descriptor.usage is model.Usage.BINARY_LONG
    assert descriptor.python_storage is model.CobolPythonStorage.INT
    assert descriptor.is_int is True
    assert descriptor.is_decimal is False
    assert descriptor.byte_length == 4
    assert descriptor.signed is True
    assert descriptor.value_domain == (-2147483648, 2147483647)
    # An int carrier has no quantum, because there is no fractional place to reach.
    assert descriptor.quantum is None


#  GROUP 5  -  DRIFT, EXPOSED AND NOT ADJUDICATED  (A-11, A-12)
#
#  The bridge is not a transparent pipe. For some fields the copybook, the host variable
#  and the column disagree, and the disagreement changes the value BEFORE ANY SQL RUNS.
#  Every test here asserts that the disagreement is RECORDED. None asserts which layer
#  is right, because none of them is: that is what R-4 means here.


def test_a11_signed_binary_long_narrowed_to_unsigned_at_the_bridge() -> None:
    """Lock anomaly A-11 for `Sales-Average` - signed copybook, unsigned host variable.

    A-11.  [copybooks/wssl.cob:L49] -> [common/salesMT.cbl:L308]
                                    -> [mysql/ACASDB.sql:L969]

    The copybook declares a signed 32-bit item; the host variable is `PIC 9(10) COMP`,
    unsigned; the column is `int(8) unsigned`. A negative value therefore loses its sign
    AT THE BRIDGE, before any SQL runs, and not at the database. What it becomes instead
    is the open question Q-3, which only running the compiled program can settle -
    so this test asserts that the drift and the question are both recorded, and
    asserts no stored value.
    """
    # spec: [copybooks/wssl.cob:L49]
    #           03  Sales-Average      binary-long. *> 9(8) comp
    #       [common/salesMT.cbl:L308]
    #           05  HV-SALES-AVERAGE                  PIC  9(10) COMP.
    #       [mysql/ACASDB.sql:L969]
    #           `SALES-AVERAGE` int(8) unsigned NOT NULL,
    descriptor = _descriptor_for("SALEDGER-REC", "Sales-Average")
    drift = descriptor.drift()

    assert drift is not None
    assert drift.signedness is True
    # The copybook view keeps its sign; the drift flag is how the disagreement is
    # carried, not by rewriting either side.
    assert descriptor.signed is True
    assert "A-11" in descriptor.anomaly_refs()
    # R-6: the stored value of a negative is NOT asserted - only that the question is on
    # the register.
    assert "Q-3" in descriptor.ambiguity_refs()
    assert drift.details != ()


def test_a11_clean_pass_through_proves_the_narrowing_is_specific_not_systemic() -> None:
    """Prove A-11 is a per-field fact by naming a clean field of the same record.

    A-11 contrast.  [copybooks/wssl.cob:L54] -> [common/salesMT.cbl:L313]

    `Sales-Current` is signed in the copybook, signed in the host variable
    (`PIC S9(08)V9(02) COMP`) and signed in the column, so it passes through untouched.
    Without this contrast the drift flag could be true everywhere and the suite would
    still pass - which would prove nothing at all.
    """
    # spec: [copybooks/wssl.cob:L54]
    #           03  Sales-Current      pic s9(8)v99       comp-3.
    #       [common/salesMT.cbl:L313]
    #           05  HV-SALES-CURRENT                  PIC S9(08)V9(02) COMP.
    clean = _descriptor_for("SALEDGER-REC", "Sales-Current")
    clean_drift = clean.drift()

    assert clean_drift is not None
    assert clean_drift.signedness is False
    assert clean.signed is True
    assert "A-11" not in clean.anomaly_refs()
    assert clean.anomaly_refs() == ()

    # And it really is the same record and the same bridge as the narrowed field.
    narrowed = _descriptor_for("SALEDGER-REC", "Sales-Average")
    narrowed_drift = narrowed.drift()
    assert narrowed_drift is not None
    assert narrowed_drift.signedness is True
    assert loader.get_entry(str(clean.dictionary_key)).bridge == loader.get_entry(
        str(narrowed.dictionary_key)
    ).bridge


@pytest.mark.parametrize(
    ("copybook_field", "copybook_locator", "bridge_locator"),
    [
        ("Entered", "copybooks/wsbatch.cob:L36", "common/glbatchMT.cbl:L287"),
        ("Proofed", "copybooks/wsbatch.cob:L37", "common/glbatchMT.cbl:L288"),
        ("Posted", "copybooks/wsbatch.cob:L38", "common/glbatchMT.cbl:L289"),
        ("Stored", "copybooks/wsbatch.cob:L39", "common/glbatchMT.cbl:L290"),
    ],
)
def test_a11_second_instance_in_the_batch_date_group(
    copybook_field: str, copybook_locator: str, bridge_locator: str
) -> None:
    """Lock a SECOND, independently narrowed group - the four batch date stamps.

    A-11 (second instance).  [copybooks/wsbatch.cob:L36-L39]
                          -> [common/glbatchMT.cbl:L287-L290]

    These four are not in the Sales ledger at all, and no list in this file names them
    as narrowed: the flag is set BY COMPARING the three views, so finding it true here
    proves the detection is real rather than transcribed. `gl072` stamps `Posted` when
    it clears a batch, so this is the posting cycle's own write path.
    """
    # spec: [copybooks/wsbatch.cob:L35-L39]
    #           03  Dates.
    #               05  Entered         binary-long.
    #               05  Proofed         binary-long.
    #               05  Posted          binary-long.
    #               05  Stored          binary-long.
    #       [common/glbatchMT.cbl:L287-L290]
    #           05  HV-ENTERED                        PIC  9(10) COMP.
    #           05  HV-PROOFED                        PIC  9(10) COMP.
    #           05  HV-POSTED                         PIC  9(10) COMP.
    #           05  HV-STORED                         PIC  9(10) COMP.
    descriptor = _descriptor_for("GLBATCH-REC", copybook_field)
    drift = descriptor.drift()
    entry = loader.get_entry(str(descriptor.dictionary_key))

    assert descriptor.source_locator == copybook_locator
    assert descriptor.usage is model.Usage.BINARY_LONG
    assert descriptor.signed is True
    assert descriptor.parent_group == "Dates"
    assert drift is not None
    assert drift.signedness is True
    assert "A-11" in descriptor.anomaly_refs()
    assert "Q-3" in descriptor.ambiguity_refs()

    # The host variable really is the unsigned one the locator names.
    assert entry.bridge_host_variable is not None
    assert entry.bridge_host_variable.source == bridge_locator
    assert entry.bridge_host_variable.signed is False


@pytest.mark.parametrize(
    ("copybook_field", "bridge_locator"),
    [
        ("Sales-Late-Min", "common/salesMT.cbl:L302"),
        ("Sales-Late-Max", "common/salesMT.cbl:L303"),
    ],
)
def test_a11_third_instance_is_a_binary_short_flavour(
    copybook_field: str, bridge_locator: str
) -> None:
    """Lock a THIRD instance, in the other binary width.

    A-11 (third instance).  [copybooks/wssl.cob:L43-L44]
                         -> [common/salesMT.cbl:L302-L303]

    A `binary-short` narrowing, distinct from the two `binary-long` cases above, which
    matters because the two widths lose their sign into different column types -
    `smallint(4) unsigned` here against `int(8) unsigned` there.

    For the record, and settled nowhere: the signed-to-unsigned block in the sales
    bridge spans L302-L312, ELEVEN host variables, of which the nine `binary-long` ones
    are L304-L312. A shorter span would leave `HV-SALES-LIMIT` at L304 out.
    """
    # spec: [copybooks/wssl.cob:L43-L44]
    #           03  Sales-Late-Min     binary-short. *> 9999 comp
    #           03  Sales-Late-Max     binary-short. *> 9999 comp
    #       [common/salesMT.cbl:L302-L303]
    #           05  HV-SALES-LATE-MIN                 PIC  9(05) COMP.
    #           05  HV-SALES-LATE-MAX                 PIC  9(05) COMP.
    descriptor = _descriptor_for("SALEDGER-REC", copybook_field)
    drift = descriptor.drift()
    entry = loader.get_entry(str(descriptor.dictionary_key))

    assert descriptor.usage is model.Usage.BINARY_SHORT
    assert descriptor.signed is True
    assert descriptor.byte_length == 2
    assert drift is not None
    assert drift.signedness is True
    assert "A-11" in descriptor.anomaly_refs()
    assert entry.bridge_host_variable is not None
    assert entry.bridge_host_variable.source == bridge_locator
    assert entry.bridge_host_variable.signed is False
    assert entry.column is not None
    assert entry.column.sql_type == "smallint(4) unsigned"


def test_a12_ledger_name_width_drifts_from_twenty_four_to_thirty_two() -> None:
    """Lock anomaly A-12 - the ledger name is 24 characters, then 32, then 32.

    A-12.  [copybooks/wsledger.cob:L27] -> [common/nominalMT.cbl:L299]
                                        -> [mysql/ACASDB.sql:L127]

    Width drift rather than sign drift, so no value is corrupted - but the PADDING
    differs, and padding is visible in a table dump. That is why the harness normaliser
    reduces trailing spaces in fixed-character columns to one agreed form instead of
    comparing raw bytes. The copybook view stays at twenty-four here; the flag is how
    the disagreement is carried.
    """
    # spec: [copybooks/wsledger.cob:L27]
    #           03  Ledger-Name       pic x(24).
    #       [common/nominalMT.cbl:L299]
    #           05  HV-LEDGER-NAME                    PIC X(32).
    #       [mysql/ACASDB.sql:L127]
    #           `LEDGER-NAME` char(32) NOT NULL,
    descriptor = _descriptor_for("GLLEDGER-REC", "Ledger-Name")
    drift = descriptor.drift()
    entry = loader.get_entry(str(descriptor.dictionary_key))

    assert descriptor.usage is model.Usage.ALPHANUMERIC
    assert descriptor.character_length == 24
    assert descriptor.byte_length == 24
    assert descriptor.python_storage is model.CobolPythonStorage.STR
    assert descriptor.is_str is True
    assert drift is not None
    assert drift.character_length is True
    assert "A-12" in descriptor.anomaly_refs()

    # The other two views, each eight characters wider, both recorded.
    assert entry.bridge_host_variable is not None
    assert entry.bridge_host_variable.picture == "X(32)"
    assert entry.bridge_host_variable.source == "common/nominalMT.cbl:L299"
    assert entry.column is not None
    assert entry.column.sql_type == "char(32)"
    assert entry.column.source == "mysql/ACASDB.sql:L127"


#  GROUP 6  -  ANOMALIES RECORDED RATHER THAN SETTLED  (A-15, A-20, A-7)


def test_a15_both_of_the_batch_record_s_declared_lengths_are_recorded() -> None:
    """Lock anomaly A-15 - the batch record's length contradicts itself, and stays so.

    A-15.  [copybooks/wsbatch.cob:L7-L9], verbatim:

        *> 96 bytes 26/03/09
        *> 98 bytes 20/12/11 (no, dont understand as I count 96)
        *>   but function length (Batch-record) says 98?

    The maintainer records two lengths and disputes his own second one. THIS TEST DOES
    NOT ASSERT WHICH IS RIGHT, and could not: the declared lengths live in an ARRAY
    precisely so a contradiction can be carried instead of adjudicated, and which length
    governs the record actually read is the open question Q-4. Only running the compiled
    program can settle it.
    """
    batch_sources = tuple(
        copybook
        for copybook in loader.sources().copybooks
        if copybook.path == "copybooks/wsbatch.cob"
    )
    assert len(batch_sources) == 1
    batch = batch_sources[0]

    # BOTH lengths, in the order the copybook writes them. Two entries in the array is
    # the whole point; one would mean a winner had been picked.
    assert batch.declared_lengths == ("96", "98")
    assert len(batch.declared_lengths) == 2
    assert batch.record_name == "WS-Batch-Record"

    # A single-length record for contrast, so the two-length case is visibly a fact
    # about this copybook and not about how the array is built. spec:
    # [copybooks/wssys4.cob:L6]
    #           *>  Record size 1024 bytes to match system-record 07/11/10
    totals_sources = tuple(
        copybook
        for copybook in loader.sources().copybooks
        if copybook.path == "copybooks/wssys4.cob"
    )
    assert len(totals_sources) == 1
    assert totals_sources[0].declared_lengths == ("1024",)

    # Every field of the record carries the anomaly and the open question, so a reader
    # arriving at any one of them is led to the contradiction.
    # spec: [copybooks/wsbatch.cob:L41]  05  Input-Gross     pic 9(9)v99.
    gross = _descriptor_for("GLBATCH-REC", "Input-Gross")
    assert "A-15" in gross.anomaly_refs()
    assert "Q-4" in gross.ambiguity_refs()


@pytest.mark.parametrize(
    ("copybook_field", "parent_group", "locator", "anomalous"),
    [
        ("sl4-spare1", "Sales-Ledger-Data", "copybooks/wssys4.cob:L18", False),
        ("sl4-spare2", "Sales-Ledger-Data", "copybooks/wssys4.cob:L19", False),
        ("sl4-spare3", "Purchase-Ledger-Data", "copybooks/wssys4.cob:L29", True),
        ("sl4-spare4", "Purchase-Ledger-Data", "copybooks/wssys4.cob:L30", True),
    ],
)
def test_a20_sales_prefixed_spares_keep_their_names_inside_the_purchase_group(
    copybook_field: str, parent_group: str, locator: str, anomalous: bool
) -> None:
    """Lock anomaly A-20 - two `sl4-` spares sit in the Purchase group, named so.

    A-20.  [copybooks/wssys4.cob:L20] `03  Purchase-Ledger-Data   comp-3.`
           holds `05  sl4-spare3` at L29 and `05  sl4-spare4` at L30, while the Sales
           group at L9 holds `sl4-spare1` and `sl4-spare2` at L18-L19.

    The name is preserved EXACTLY. Renaming `sl4-spare3` to `pl4-spare1` would be a fix,
    and a fix is a failure: the column is spelled `SL4-SPARE3` in the frozen schema too,
    so a "tidied" name would no longer address the column it maps to.
    """
    descriptor = _descriptor_for("SYSTOT-REC", copybook_field)

    # Verbatim, lower case, `sl4-` prefix intact whichever group it is in.
    assert descriptor.name == copybook_field
    assert descriptor.name.startswith("sl4-")
    assert descriptor.parent_group == parent_group
    assert descriptor.source_locator == locator
    # Both groups carry COMP-3 on the header, so all four spares are packed.
    assert descriptor.usage is model.Usage.COMP_3
    assert descriptor.usage_declared_at is model.UsageDeclaredAt.GROUP
    assert descriptor.usage_inherited_from == parent_group
    assert descriptor.picture == "s9(8)v99"

    # Only the two in the WRONG group are on the anomaly register; the two in the right
    # one are ordinary fields. That contrast is what makes the register meaningful.
    assert ("A-20" in descriptor.anomaly_refs()) is anomalous


def test_a7_the_bridge_derived_date_components_have_no_cobol_storage() -> None:
    """Lock anomaly A-7 - three columns the bridge derives and no copybook declares.

    A-7.  [common/irspostingMT.cbl:L982-L987], verbatim:

        if       Post-Date (1:2) numeric
                 move     Post-Date (1:2) to HV-POST4-DAY.
        if       Post-Date (4:2) numeric
                 move     Post-Date (4:2) to HV-POST4-MONTH.
        if       Post-Date (7:2) numeric
                 move     Post-Date (7:2) to HV-POST4-YEAR.

    THE PROOF THAT THE BRIDGE IS THE DATA DICTIONARY AND THE COPYBOOK IS NOT: these
    three columns exist in the schema and in the host-variable group and in NO copybook
    at all, so a migration driven from the copybooks alone would silently omit three
    columns of a posting table.

    Because such a field has no COBOL-side storage, asking for a descriptor is an error
    rather than a guess - and the error names the bridge and the derivation, which is
    where reproducing it belongs.
    """
    # spec: [mysql/ACASDB.sql:L278-L280]
    #           `POST4-DAY` tinyint(2) unsigned NOT NULL,
    #           `POST4-MONTH` tinyint(2) unsigned NOT NULL,
    #           `POST4-YEAR` tinyint(2) unsigned NOT NULL,
    for column in ("POST4-DAY", "POST4-MONTH", "POST4-YEAR"):
        key = f"IRSPOSTING-REC.{column}"
        entry = loader.get_entry(key)

        # Declared by the bridge and the schema; by no copybook and no program source.
        assert entry.presence.in_copybook is False
        assert entry.presence.in_program_source is False
        assert entry.presence.in_bridge is True
        assert entry.presence.in_column is True
        assert entry.copybook is None
        assert entry.program_source is None
        assert "A-7" in entry.anomaly_refs

        # The guarded derivation, recorded as data so the handler can reproduce it
        # without calling the bridge (R-1).
        assert entry.derivation is not None
        assert entry.derivation.guard is not None
        assert "numeric" in entry.derivation.guard
        assert entry.derivation.source.startswith("common/irspostingMT.cbl:L")
        # When the guard fails the component stays zero while the raw text is still
        # stored, so the row is internally inconsistent - stated, not repaired.
        assert entry.derivation.guard_failure_behaviour != ""

        # No COBOL-side storage means no descriptor, and the refusal names the field.
        with pytest.raises(cobol_field.BridgeOnlyFieldError, match=re.escape(key)):
            cobol_field.FieldDescriptor.from_dictionary_key(key)

    # And the whole date IS still stored, in its own column, which is what makes the
    # inconsistency observable rather than theoretical.
    # spec: [mysql/ACASDB.sql:L277]  `POST4-DAT` char(8) NOT NULL,
    whole_date = loader.get_entry("IRSPOSTING-REC.POST4-DAT")
    assert whole_date.presence.in_copybook is True
    assert whole_date.copybook is not None
    assert whole_date.copybook.name == "Post-Date"


#  GROUP 7  -  THE PROVENANCE INVARIANT  (R-5)
#
#  A descriptor must be traceable to a frozen line, or it must not exist. The
#  invariant is enforced in `FieldDescriptor.__post_init__`, so it holds however a
#  descriptor is built.


def test_a_program_local_descriptor_is_traceable_by_its_locator() -> None:
    """Prove a field with no dictionary key still carries provenance - its locator.

    Route one of the two. A program's own working storage never reaches a table, so it
    has no entry to key on; the `<path>:L<n>` locator is the only traceability it will
    ever have, and `cite()` hands it straight back.
    """
    # spec: [sales/sl060.cbl:L206]
    #           03  work-2          pic s9(14)    comp-3.
    descriptor = cobol_picture.descriptor_for(
        "pic s9(14)    comp-3",
        name="work-2",
        source_locator="sales/sl060.cbl:L206",
    )

    assert descriptor.dictionary_key is None
    assert descriptor.source_locator == "sales/sl060.cbl:L206"
    assert descriptor.cite() == "sales/sl060.cbl:L206"
    # A program-local field has one layer, so it cannot disagree with itself and carries
    # no register references.
    assert descriptor.drift() is None
    assert descriptor.anomaly_refs() == ()
    assert descriptor.ambiguity_refs() == ()


def test_a_catalogued_descriptor_is_traceable_by_its_key_to_all_three_layers() -> None:
    """Prove a catalogued field cites its copybook, its bridge and its column.

    Route two of the two, and the reason R-5 is satisfied mechanically rather than by
    hand: the citation is composed from the artifact, so it cannot fall out of step with
    the field it describes.
    """
    # spec: [copybooks/wsledger.cob:L28]
    #           03  Ledger-Balance    pic s9(8)v99   comp-3.
    descriptor = cobol_field.FieldDescriptor.from_dictionary_key(
        "GLLEDGER-REC.LEDGER-BALANCE"
    )

    assert descriptor.dictionary_key == "GLLEDGER-REC.LEDGER-BALANCE"
    citation = descriptor.cite()
    assert "GLLEDGER-REC.LEDGER-BALANCE" in citation
    assert "copybooks/wsledger.cob:L28" in citation
    assert "common/nominalMT.cbl:L300" in citation
    assert "mysql/ACASDB.sql:L128" in citation
    # The same string the loader publishes, surfaced rather than reimplemented.
    assert citation == loader.cite("GLLEDGER-REC.LEDGER-BALANCE")


def test_a_descriptor_with_neither_a_key_nor_a_locator_cannot_be_built() -> None:
    """Prove the invariant fires, and that its message names the field.

    Reached by constructing the dataclass directly, because both public factories supply
    one provenance or the other - which is itself the point: there is no route to an
    untraceable descriptor.
    """
    # spec: the invariant at [acas_posting/cobol/field.py:L191-L206]
    with pytest.raises(cobol_field.MissingProvenanceError, match="work-2"):
        cobol_field.FieldDescriptor(
            name="work-2",
            usage=model.Usage.COMP_3,
            digits=14,
            integer_digits=14,
            scale=0,
            signed=True,
            python_storage=model.CobolPythonStorage.INT,
        )

    # It is a FieldDescriptorError, so a caller catching the family catches this too.
    assert issubclass(
        cobol_field.MissingProvenanceError, cobol_field.FieldDescriptorError
    )


@pytest.mark.parametrize(
    "malformed",
    [
        pytest.param("sales/sl060.cbl", id="no-line-part"),
        pytest.param("sl060 line 206", id="prose-not-a-locator"),
        pytest.param("sales/sl060.cbl:206", id="missing-L"),
        pytest.param("sales/sl060.cbl:L", id="L-with-no-number"),
    ],
)
def test_a_malformed_locator_is_refused(malformed: str) -> None:
    """Prove a locator that a reader could not follow is refused outright.

    R-5 is about CHECKABLE citations. A citation nobody can follow is the same as no
    traceability at all, so the shape is enforced rather than hoped for.
    """
    # spec: the published shape, imported rather than retyped so the two cannot drift:
    #       loader.SOURCE_LOCATOR_PATTERN
    with pytest.raises(cobol_field.FieldDescriptorError, match="work-2"):
        cobol_field.FieldDescriptor(
            name="work-2",
            usage=model.Usage.COMP_3,
            digits=14,
            integer_digits=14,
            scale=0,
            signed=True,
            python_storage=model.CobolPythonStorage.INT,
            source_locator=malformed,
        )

    assert loader.SOURCE_LOCATOR_PATTERN.match(malformed) is None


@pytest.mark.parametrize(
    "well_formed",
    [
        pytest.param("sales/sl060.cbl:L206", id="single-line"),
        pytest.param("copybooks/wsbatch.cob:L36-L39", id="line-span"),
    ],
)
def test_a_well_formed_locator_is_accepted(well_formed: str) -> None:
    """Prove both shapes a frozen citation takes are accepted.

    A single line for one declaration, a span for a block of them - the two forms the
    frozen sources actually need.
    """
    # spec: [sales/sl060.cbl:L206] one declaration;
    #       [copybooks/wsbatch.cob:L36-L39] the four batch date stamps as a block.
    assert loader.SOURCE_LOCATOR_PATTERN.match(well_formed) is not None
    descriptor = cobol_field.FieldDescriptor(
        name="work-2",
        usage=model.Usage.COMP_3,
        digits=14,
        integer_digits=14,
        scale=0,
        signed=True,
        python_storage=model.CobolPythonStorage.INT,
        source_locator=well_formed,
    )
    assert descriptor.cite() == well_formed


#  GROUP 8  -  PROGRAM-LOCAL WORKING STORAGE
#
#  The fields the generated dictionary does not cover, because they never reach a table.
#  They are nonetheless where the posting arithmetic happens, so their storage shape
#  decides posted figures just as a record field's does.
#
#  `FieldDescriptor.for_working_storage` no longer exists - see the note at
#  [acas_posting/cobol/field.py:L533-L534] - so these are minted by the picture
#  parser, which is the route `__post_init__` names for a bare locator. The
#  locator is MANDATORY.


@pytest.mark.parametrize(
    (
        "name",
        "clauses",
        "level",
        "locator",
        "usage",
        "signed",
        "picture",
        "digits",
        "integer_digits",
        "scale",
        "is_edited",
        "storage",
        "byte_length",
        "quantum",
    ),
    [
        # spec: [sales/sl060.cbl:L206]
        #           03  work-2          pic s9(14)    comp-3.
        #       Fourteen digits and NO scale - the widest intermediate in the invoice
        #       path. Zero scale gives it an int carrier and a quantum of one, so a
        #       store into it drops any fractional part outright.
        pytest.param(
            "work-2",
            "pic s9(14)    comp-3",
            "03",
            "sales/sl060.cbl:L206",
            model.Usage.COMP_3,
            True,
            "s9(14)",
            14,
            14,
            0,
            False,
            model.CobolPythonStorage.INT,
            8,
            Decimal("1"),
            id="sl060.work-2-comp-3-scale-zero",
        ),
        # spec: [sales/sl060.cbl:L218]
        #           03  work-goods      pic s9(7)v99  comp-3.
        #       Nine digits in five bytes: one nibble per digit plus the sign nibble.
        pytest.param(
            "work-goods",
            "pic s9(7)v99  comp-3",
            "03",
            "sales/sl060.cbl:L218",
            model.Usage.COMP_3,
            True,
            "s9(7)v99",
            9,
            7,
            2,
            False,
            model.CobolPythonStorage.DECIMAL,
            5,
            Decimal("0.01"),
            id="sl060.work-goods-comp-3",
        ),
        # spec: [sales/sl060.cbl:L213]
        #           03  m               pic z(7)9.
        #       Numeric-EDITED: seven zero-suppressed positions and one forced digit. It
        #       is a print field, and it is described and never rendered - PictureSpec
        #       has no formatting method and none is called here.
        pytest.param(
            "m",
            "pic z(7)9",
            "03",
            "sales/sl060.cbl:L213",
            model.Usage.DISPLAY,
            False,
            "z(7)9",
            8,
            8,
            0,
            True,
            model.CobolPythonStorage.INT,
            8,
            Decimal("1"),
            id="sl060.m-numeric-edited",
        ),
        # spec: [general/gl051.cbl:L178]
        #           03  account-in          pic 9(4)v99.
        #       The scaled account number the control-total gate reads. Unsigned zoned
        #       DISPLAY, six digits in six bytes.
        pytest.param(
            "account-in",
            "pic 9(4)v99",
            "03",
            "general/gl051.cbl:L178",
            model.Usage.DISPLAY,
            False,
            "9(4)v99",
            6,
            4,
            2,
            False,
            model.CobolPythonStorage.DECIMAL,
            6,
            Decimal("0.01"),
            id="gl051.account-in-zoned-unsigned",
        ),
        # spec: [general/gl072.cbl:L233]
        #           03  l6-account          pic 9999.99 blank when zero.
        #       An ACTUAL decimal point, which makes the picture edited; BLANK WHEN ZERO
        #       is print behaviour and changes no digit count.
        pytest.param(
            "l6-account",
            "pic 9999.99 blank when zero",
            "03",
            "general/gl072.cbl:L233",
            model.Usage.DISPLAY,
            False,
            "9999.99",
            6,
            4,
            2,
            True,
            model.CobolPythonStorage.DECIMAL,
            6,
            Decimal("0.01"),
            id="gl072.l6-account-edited-actual-point",
        ),
        # spec: [general/gl080.cbl:L182-L183]
        #           77  y                   pic 99     value zero.
        #           77  a                   pic 99     value zero.
        #       Level 77 independent items - the end-of-cycle program's own counters.
        pytest.param(
            "y",
            "pic 99     value zero",
            "77",
            "general/gl080.cbl:L182",
            model.Usage.DISPLAY,
            False,
            "99",
            2,
            2,
            0,
            False,
            model.CobolPythonStorage.INT,
            2,
            Decimal("1"),
            id="gl080.y-level-77",
        ),
        pytest.param(
            "a",
            "pic 99     value zero",
            "77",
            "general/gl080.cbl:L183",
            model.Usage.DISPLAY,
            False,
            "99",
            2,
            2,
            0,
            False,
            model.CobolPythonStorage.INT,
            2,
            Decimal("1"),
            id="gl080.a-level-77",
        ),
    ],
)
def test_program_local_working_storage_descriptor(
    name: str,
    clauses: str,
    level: str,
    locator: str,
    usage: model.Usage,
    signed: bool,
    picture: str | None,
    digits: int | None,
    integer_digits: int | None,
    scale: int | None,
    is_edited: bool,
    storage: model.CobolPythonStorage,
    byte_length: int,
    quantum: Decimal | None,
) -> None:
    """Prove a program's own field is described exactly as its own line declares it."""
    descriptor = cobol_picture.descriptor_for(
        clauses, name=name, source_locator=locator, level=level
    )

    assert descriptor.name == name
    assert descriptor.usage is usage
    assert descriptor.signed is signed
    assert descriptor.picture == picture
    assert descriptor.digits == digits
    assert descriptor.integer_digits == integer_digits
    assert descriptor.scale == scale
    assert descriptor.is_edited == is_edited
    assert descriptor.python_storage is storage
    assert descriptor.byte_length == byte_length
    assert descriptor.quantum == quantum
    # R-5: no key, so the locator is the traceability, and it is present.
    assert descriptor.dictionary_key is None
    assert descriptor.source_locator == locator
    assert descriptor.cite() == locator


def test_work_a_and_work_b_diverge_between_sl060_and_sl100() -> None:
    """Prove two same-named working fields in two programs are NOT the same field.

    A per-program divergence, preserved rather than unified. `sl060` declares `work-a`
    and `work-b` as packed decimal with two fractional places; `sl100` declares them as
    `binary-long`, which is an integer carrier. Unifying them into one shared descriptor
    would change one program's arithmetic to match the other's, which is exactly the
    class of tidying R-4 forbids.
    """
    # spec: [sales/sl060.cbl:L207-L208]
    #           03  work-a          pic s9(7)v99  comp-3   value zero.
    #           03  work-b          pic s9(7)v99  comp-3   value zero.
    #       [sales/sl100.cbl:L182-L183]
    #           03  work-a          binary-long           value zero.
    #           03  work-b          binary-long           value zero.
    for name, invoice_locator, cash_locator in (
        ("work-a", "sales/sl060.cbl:L207", "sales/sl100.cbl:L182"),
        ("work-b", "sales/sl060.cbl:L208", "sales/sl100.cbl:L183"),
    ):
        invoice = cobol_picture.descriptor_for(
            "pic s9(7)v99  comp-3   value zero",
            name=name,
            source_locator=invoice_locator,
        )
        cash = cobol_picture.descriptor_for(
            "binary-long           value zero",
            name=name,
            source_locator=cash_locator,
        )

        assert invoice.usage is model.Usage.COMP_3
        assert invoice.picture == "s9(7)v99"
        assert invoice.scale == 2
        assert invoice.byte_length == 5
        assert invoice.python_storage is model.CobolPythonStorage.DECIMAL
        assert invoice.quantum == Decimal("0.01")

        assert cash.usage is model.Usage.BINARY_LONG
        assert cash.picture is None
        assert cash.scale is None
        assert cash.byte_length == 4
        assert cash.python_storage is model.CobolPythonStorage.INT
        assert cash.quantum is None

        # Same name, different fields. Not unified.
        assert invoice.name == cash.name == name
        assert invoice != cash


def test_line_cnt_diverges_between_sl060_and_sl100() -> None:
    """Prove the page-line counter is a different storage class in each program.

    A second per-program divergence, and a narrower one: `sl060` writes `pic 99 comp`,
    `sl100` writes `binary-char`. Both end up one byte wide, so the divergence is in the
    DECLARED DIGIT RANGE rather than the width - two digits against a full signed byte -
    and both are kept as written.
    """
    # spec: [sales/sl060.cbl:L223]
    #           03  line-cnt        pic 99        comp    value zero.
    invoice = cobol_picture.descriptor_for(
        "pic 99        comp    value zero",
        name="line-cnt",
        source_locator="sales/sl060.cbl:L223",
    )
    # spec: [sales/sl100.cbl:L173]
    #           03  line-cnt        binary-char           value zero.
    cash = cobol_picture.descriptor_for(
        "binary-char           value zero",
        name="line-cnt",
        source_locator="sales/sl100.cbl:L173",
    )

    assert invoice.usage is model.Usage.COMP
    assert invoice.picture == "99"
    assert invoice.digits == 2
    assert invoice.scale == 0
    assert invoice.signed is False
    assert invoice.value_domain == (0, 99)

    assert cash.usage is model.Usage.BINARY_CHAR
    assert cash.picture is None
    assert cash.digits is None
    assert cash.signed is True
    assert cash.value_domain == (-128, 127)

    # Both one byte, both int-carried, and still not the same field.
    assert invoice.byte_length == cash.byte_length == 1
    assert invoice.python_storage is cash.python_storage
    assert invoice.python_storage is model.CobolPythonStorage.INT
    assert invoice != cash


#  GROUP 9  -  PICTURE PARSING: THE THREE TRAPS
#
#  Every descriptor in this file rests on the parser reading a declaration the way the
#  compiler reads it. Three ways that can go wrong, all present in the frozen sources.


def test_a_data_description_entry_may_span_two_physical_lines() -> None:
    """Prove a continued entry is joined before it is parsed, not read line by line.

    TRAP ONE. A data-description entry is terminated by its PERIOD, not by its
    newline, so a parser that took one physical line at a time would see
    `03 WS-Batch-Key9 redefines WS-Batch-Key` with no picture at all and then a
    stray `pic 9(6).` belonging to nothing. Four in-scope declarations are
    written this way.
    """
    # spec: [copybooks/wsbatch.cob:L20-L21], verbatim:
    #           03  WS-Batch-Key9 redefines WS-Batch-Key
    #                                   pic 9(6).
    #       The same shape occurs at [copybooks/wsledger.cob:L21-L22] and
    #       [copybooks/wssl.cob:L65-L66].
    continued = (
        "     03  WS-Batch-Key9 redefines WS-Batch-Key\n"
        "                             pic 9(6).\n"
    )

    joined = cobol_picture.join_continuations(continued.splitlines(), first_line=20)
    assert len(joined) == 1
    assert joined[0].text == "03  WS-Batch-Key9 redefines WS-Batch-Key pic 9(6)."
    assert joined[0].first_line == 20
    assert joined[0].last_line == 21

    entries = cobol_picture.parse_entries(
        continued, source_path="copybooks/wsbatch.cob", first_line=20
    )
    assert len(entries) == 1
    entry = entries[0]
    assert entry.kind is cobol_picture.EntryKind.FIELD
    assert entry.name == "WS-Batch-Key9"
    assert entry.level == "03"
    assert entry.first_line == 20
    assert entry.last_line == 21

    descriptor = entry.descriptor
    assert descriptor is not None
    assert descriptor.name == "WS-Batch-Key9"
    assert descriptor.redefines == "WS-Batch-Key"
    assert descriptor.picture == "9(6)"
    assert descriptor.digits == 6
    assert descriptor.integer_digits == 6
    assert descriptor.scale == 0
    assert descriptor.usage is model.Usage.DISPLAY
    assert descriptor.source_locator == "copybooks/wsbatch.cob:L20"


def test_comments_are_stripped_before_the_declaration_is_parsed() -> None:
    """Prove commentary is removed first, and that stripping changes nothing else.

    TRAP TWO, and it is mandated by R-4. The maintainer annotated three of his own
    declarations with digit counts that contradict them, so a parser that let a comment
    reach the clause scan could pick up `9999` and describe a 16-bit field as a
    four-digit one. Stripping first makes that impossible by construction rather than
    by care.
    """
    # spec: [copybooks/wssl.cob:L43], verbatim:
    #           03  Sales-Late-Min     binary-short. *> 9999 comp
    raw = "     03  Sales-Late-Min     binary-short. *> 9999 comp"

    stripped = cobol_picture.strip_comments(raw)
    assert stripped == "     03  Sales-Late-Min     binary-short."
    assert "9999" not in stripped
    # The declaration itself is untouched, including its leading whitespace.
    assert stripped.strip() == "03  Sales-Late-Min     binary-short."

    # Parsing the raw line and the stripped line give the SAME descriptor, which is the
    # property that matters: the comment has no influence at all.
    from_raw = cobol_picture.parse_entry(raw, source_locator="copybooks/wssl.cob:L43")
    from_stripped = cobol_picture.parse_entry(
        stripped, source_locator="copybooks/wssl.cob:L43"
    )
    assert from_raw.descriptor == from_stripped.descriptor
    assert from_raw.descriptor is not None
    assert from_raw.descriptor.usage is model.Usage.BINARY_SHORT
    assert from_raw.descriptor.byte_length == 2
    # The comment's four-digit claim reached nothing.
    assert from_raw.descriptor.digits is None
    assert from_raw.descriptor.value_domain == (-32768, 32767)


def test_a_binary_field_may_carry_no_picture_at_all() -> None:
    """Prove a `binary-*` declaration parses with no PICTURE clause present.

    TRAP THREE. Fifteen in-scope record fields are declared by storage class alone, with
    no picture: the four batch date stamps [copybooks/wsbatch.cob:L36-L39] and the
    eleven sales statistics fields [copybooks/wssl.cob:L43-L53]. A parser that required
    a picture would fail on every one of them, and a descriptor that invented one -
    eight digits, say, from the comment - would give the field the wrong range.
    """
    # spec: [copybooks/wsbatch.cob:L36]  05  Entered         binary-long.
    entry = cobol_picture.parse_entry(
        "05  Entered         binary-long.",
        source_locator="copybooks/wsbatch.cob:L36",
    )

    assert entry.kind is cobol_picture.EntryKind.FIELD
    assert entry.name == "Entered"
    # No PICTURE clause, so no PictureSpec, and the descriptor says so too.
    assert entry.picture is None
    descriptor = entry.descriptor
    assert descriptor is not None
    assert descriptor.picture is None
    assert descriptor.digits is None
    assert descriptor.integer_digits is None
    assert descriptor.scale is None
    # The class alone gives the width, the sign and the range.
    assert descriptor.usage is model.Usage.BINARY_LONG
    assert descriptor.signed is True
    assert descriptor.byte_length == 4
    assert descriptor.value_domain == (-2147483648, 2147483647)
    assert descriptor.python_storage is model.CobolPythonStorage.INT

    # The catalogued descriptor for the very same declaration agrees, so the parser and
    # the generated artifact are describing one field and not two.
    catalogued = _descriptor_for("GLBATCH-REC", "Entered")
    assert catalogued.picture is None
    assert catalogued.usage is descriptor.usage
    assert catalogued.byte_length == descriptor.byte_length
    assert catalogued.value_domain == descriptor.value_domain
    assert catalogued.source_locator == descriptor.source_locator


#  GROUP 10  -  COVERAGE, THE OUT-OF-SCOPE BOUNDARY, AND THE STRUCTURAL PROHIBITIONS


def test_dictionary_coverage_tallies_are_a_comparison_not_a_claim() -> None:
    """Prove the completeness claim is checkable by arithmetic.

    `in_scope_columns` and `columns_covered` are recorded SEPARATELY so that complete
    coverage is a comparison of two independently counted numbers rather than an
    assertion that one of them is enough. If a column of an in-scope table ever lost its
    entry, the two would part company here.
    """
    # spec: [mysql/ACASDB.sql] declares 33 CREATE TABLE statements and zero ALTER TABLE
    #       and zero CREATE INDEX; the posting cycle reaches 22 of them through 20
    #       bridge pairs, leaving 11 tables and 8 bridges out of scope (22 + 11 == 33).
    coverage = loader.coverage()

    assert coverage.schema_tables_total == 33
    assert coverage.in_scope_tables == 22
    assert coverage.out_of_scope_tables == 11
    assert coverage.in_scope_tables + coverage.out_of_scope_tables == 33
    assert coverage.in_scope_bridges == 20
    assert coverage.out_of_scope_bridges == 8
    assert coverage.in_scope_columns == 513
    assert coverage.columns_covered == 513
    assert coverage.columns_covered == coverage.in_scope_columns
    # More entries than columns, necessarily: a copybook field that reaches no column
    # and a work-file field that reaches no table each still need an entry.
    assert coverage.entry_count > coverage.in_scope_columns


@pytest.mark.parametrize(
    ("table", "column_count"),
    [
        ("ANALYSIS-REC", 4),
        ("GLBATCH-REC", 21),
        ("GLLEDGER-REC", 11),
        ("GLPOSTING-REC", 14),
        ("IRSDFLT-REC", 4),
        ("IRSFINAL-REC", 3),
        ("IRSNL-REC", 15),
        ("IRSPOSTING-REC", 13),
        ("PSIRSPOST-REC", 10),
        ("PUINV-LINES-REC", 14),
        ("PUINVOICE-REC", 30),
        ("PUITM5-REC", 29),
        ("PULEDGER-REC", 29),
        ("SAINV-LINES-REC", 14),
        ("SAINVOICE-REC", 31),
        ("SAITM3-REC", 28),
        ("SALEDGER-REC", 37),
        ("SYSDEFLT-REC", 4),
        ("SYSFINAL-REC", 2),
        ("SYSTEM-REC", 169),
        ("SYSTOT-REC", 21),
        ("VALUEANAL-REC", 10),
    ],
)
def test_in_scope_table_has_an_entry_for_every_one_of_its_columns(
    table: str, column_count: int
) -> None:
    """Prove each in-scope table's column count is matched entry for entry.

    Per-table, so a shortfall names the table rather than only the total.
    """
    # spec: [mysql/ACASDB.sql] - the column count of each in-scope CREATE TABLE.
    record = loader.table_for(table)
    assert record.name == table
    assert record.column_count == column_count

    entries = loader.entries_for_table(table)
    column_backed = tuple(entry for entry in entries if entry.presence.in_column)
    assert len(column_backed) == column_count


def test_the_twenty_two_in_scope_tables_account_for_all_513_columns() -> None:
    """Prove the per-table counts sum to the coverage total.

    The arithmetic that ties the twenty-two rows above to the single number the coverage
    block publishes. Either could be wrong alone; both cannot be wrong together.
    """
    # spec: 4+21+11+14+4+3+15+13+10+14+30+29+29+14+31+28+37+4+2+169+21+10 == 513
    per_table = sum(record.column_count for record in loader.tables())
    assert len(loader.table_names()) == 22
    assert per_table == 513
    assert per_table == loader.coverage().in_scope_columns


@pytest.mark.parametrize(
    "out_of_scope_table",
    [
        "STOCK-REC",
        "STOCKAUDIT-REC",
        "DELIVERY-REC",
        "PUDELINV-REC",
        "SADELINV-REC",
        "SAAUTOGEN-REC",
        "SAAUTOGEN-LINES-REC",
        "PUAUTOGEN-REC",
        "PUAUTOGEN-LINES-REC",
        "PLPAY-REC",
        "PLPAY-RECrg01",
    ],
)
def test_no_out_of_scope_table_is_catalogued(out_of_scope_table: str) -> None:
    """Prove the eleven tables the posting cycle never touches stay out.

    They are present in the frozen schema and reached by no in-scope program, so an
    entry for one of them would mean the dictionary had grown past its own boundary -
    and a scenario diff would then compare tables no migrated code writes.
    """
    # spec: [mysql/ACASDB.sql] declares all 33; these 11 belong to the stock, delivery,
    #       autogen and payments subsystems, none of which the posting cycle reaches.
    assert out_of_scope_table not in loader.table_names()
    assert loader.find_entry(f"{out_of_scope_table}.ANY-COLUMN") is None


@pytest.mark.parametrize("forbidden_word", _FORBIDDEN_MEMBER_WORDS)
def test_no_single_winner_view_exists_on_drift_entry_or_descriptor(
    forbidden_word: str,
) -> None:
    """Prove no member anywhere names one winning answer among the three layers.

    THE STRUCTURAL ENFORCEMENT OF R-4 AND R-5. Because no member of a drift record, an
    entry or a descriptor names a single winning type, width, sign or picture, a future
    generator CANNOT quietly reconcile the views: there is nowhere to put the reconciled
    value. The prohibition is asserted over the member names rather than trusted to
    review.
    """
    # spec: Technical Specification section 0.7.2, R-4 and R-5 - drift is exposed
    #       unadjudicated, so the seven words below name nothing in this system.
    drift = _descriptor_for("SALEDGER-REC", "Sales-Average").drift()
    entry = loader.get_entry("SALEDGER-REC.SALES-AVERAGE")
    descriptor = _descriptor_for("SALEDGER-REC", "Sales-Average")

    for subject in (drift, entry, descriptor, model.Drift, model.DictionaryEntry):
        offenders = sorted(
            member
            for member in dir(subject)
            if forbidden_word in member.lower()
        )
        assert offenders == [], (
            f"{subject!r} exposes {offenders}: drift is exposed unadjudicated, so "
            f"no member may name a single winning view"
        )


def test_drift_exposes_exactly_six_flags_and_its_details() -> None:
    """Prove the drift record is the six comparisons plus its plain-words detail.

    Six flags, one per kind of disagreement, and a details tuple that says what each
    layer claims. Nothing else: no summary, no severity, no verdict.
    """
    # spec: Technical Specification section 0.7.2 R-4 - "all three views are recorded
    #       independently, the drift flags are set by comparison".
    drift = _descriptor_for("SALEDGER-REC", "Sales-Average").drift()
    assert drift is not None

    public_members = {
        member for member in dir(drift) if not member.startswith("_")
    }
    # The six flags and the details, plus the two serialisation helpers every record in
    # the object model carries.
    assert public_members == {
        "signedness",
        "usage",
        "digits",
        "scale",
        "character_length",
        "name",
        "details",
        "from_json_obj",
        "to_json_obj",
    }
    for flag in (
        drift.signedness,
        drift.usage,
        drift.digits,
        drift.scale,
        drift.character_length,
        drift.name,
    ):
        assert isinstance(flag, bool)
    assert isinstance(drift.details, tuple)
    assert all(isinstance(detail, str) for detail in drift.details)


def test_tier_touches_no_database_and_no_oracle() -> None:
    """Prove R-1 and R-2 mechanically, from the modules this run actually imported.

    R-1: this tier must run on a bare host, so no database driver, no SQL toolkit, no
    compiled-oracle harness and no data-access module may be reachable from it - and the
    surest evidence is that none of them is loaded.

    R-2: `numpy` and `pandas` compute in binary floating point by default, which is
    prohibited outright for accounting work, so neither may be present either.
    """
    # spec: Technical Specification section 0.7.2 R-1 - "tests/arithmetic/* touch
    #       neither COBOL nor a database"; R-2 excludes pandas and numpy by name.
    loaded = set(sys.modules)

    assert "sqlalchemy" not in loaded
    assert "mysql.connector" not in loaded
    assert "harness" not in loaded
    assert "numpy" not in loaded
    assert "pandas" not in loaded
    assert not any(name.startswith("sqlalchemy.") for name in loaded)
    assert not any(name.startswith("mysql") for name in loaded)
    assert not any(name.startswith("harness.") for name in loaded)
    assert not any(name.startswith("acas_posting.dal") for name in loaded)
    assert not any(name.startswith("acas_posting.programs") for name in loaded)
    assert not any(name.startswith("acas_posting.cli") for name in loaded)


#  GROUP 12  -  THE COMMITTED DICTIONARY AGAINST ITS COMMITTED JSON SCHEMA
#
#  Agent Action Plan section 0.4.1.6 describes
#  `data_dictionary/acas_posting_dictionary.schema.json` as the "JSON Schema
#  validating the generated artifact in CI-less form, EXERCISED BY A TEST", and
#  section 0.8.5 makes "the machine-readable data dictionary validates against its
#  schema" one of the five completion criteria. Both files are declared dependencies
#  of this module, which is why the exercise lives here rather than anywhere else:
#  this is the file that owns dictionary provenance.
#
#  WHY THE VALIDATOR IS WRITTEN OUT HERE INSTEAD OF INSTALLED.
#  The third-party JSON-Schema validator library is NOT a pinned dependency, and the
#  tier contract names it among the modules this file must not import: section 0.5.1
#  froze the dependency set deliberately, and widening it in order to validate a
#  committed artifact would be a poor trade. So the keywords the schema ACTUALLY uses
#  are implemented below,
#  and only those. The set is CLOSED, and a test asserts it stays closed, so a schema
#  that started using a keyword this validator does not implement fails loudly rather
#  than being silently under-validated:
#
#      $schema  $id  title  description  type  required  additionalProperties
#      properties  $defs  $ref  items  minItems  uniqueItems  pattern  minLength
#      minimum  enum  const  examples
#
#  Nineteen keywords, and no combinator at all - no anyOf, oneOf, allOf, not, if,
#  then, else, prefixItems, patternProperties or format. `additionalProperties` is
#  literal `false` at all 25 sites, and all 66 `$ref` sites point into `#/$defs`.
#
#  `description` and `examples` are annotations and carry no assertion; they are
#  named in the closed set because they appear, not because they constrain.
#
#  R-2 is respected: nothing here parses a number into a binary float. `json.loads`
#  produces `int` for the integer literals the artifact contains, and the numeric
#  keywords the schema uses - `minimum`, `minItems`, `minLength` - are compared as
#  integers. No binary floating-point value is constructed anywhere in this group.


#: The repository root, derived from THIS FILE's location rather than from the process
#: working directory. `tests/conftest.py:L99` derives `REPO_ROOT` the same way and for
#: the same reason: the working directory is the caller's business, and a suite that
#: only passes when it is invoked from one particular directory is not a property of
#: the code under test. `tests/arithmetic/<this file>` is two levels below the root.
_REPO_ROOT: Final[pathlib.Path] = pathlib.Path(__file__).resolve().parents[2]

#: The two committed artifacts, addressed absolutely so the group below reads the same
#: two files whatever directory pytest was started from.
_DICTIONARY_JSON: Final[pathlib.Path] = (
    _REPO_ROOT / "data_dictionary" / "acas_posting_dictionary.json"
)
_DICTIONARY_SCHEMA_JSON: Final[pathlib.Path] = (
    _REPO_ROOT / "data_dictionary" / "acas_posting_dictionary.schema.json"
)

#: Exactly the keywords the committed schema uses. Asserted to be closed, so the
#: validator below can never be silently out of date.
_IMPLEMENTED_SCHEMA_KEYWORDS: Final[frozenset[str]] = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "type",
        "required",
        "additionalProperties",
        "properties",
        "$defs",
        "$ref",
        "items",
        "minItems",
        "uniqueItems",
        "pattern",
        "minLength",
        "minimum",
        "enum",
        "const",
        "examples",
    }
)

#: The JSON type names the schema uses, mapped to the Python types `json.loads`
#: produces. `bool` is checked BEFORE `int` everywhere below, because in Python
#: `True` is an `int` and a boolean must never satisfy an integer constraint.
_JSON_TYPE_CHECKS: Final[dict[str, tuple[type, ...]]] = {
    "object": (dict,),
    "array": (list,),
    "string": (str,),
    "boolean": (bool,),
    "integer": (int,),
    "null": (type(None),),
}


class _SchemaValidationCounters:
    """How much work a validation run did, so a vacuous pass is detectable.

    Attributes:
        nodes: Instance nodes visited.
        refs_followed: `$ref` indirections taken.
        keywords_applied: Constraint keywords actually evaluated.
    """

    __slots__ = ("nodes", "refs_followed", "keywords_applied")

    def __init__(self) -> None:
        self.nodes = 0
        self.refs_followed = 0
        self.keywords_applied = 0


def _json_type_matches(value: object, type_name: str) -> bool:
    """Does `value` satisfy the JSON type named `type_name`?

    Args:
        value: A node of the parsed instance document.
        type_name: One of the names in `_JSON_TYPE_CHECKS`.

    Returns:
        True when the value is of that JSON type.
    """
    expected = _JSON_TYPE_CHECKS[type_name]
    if type_name == "integer":
        # A JSON boolean is not a JSON integer, even though `bool` subclasses `int`.
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    return isinstance(value, expected)


def _validate_against_schema(
    instance: object,
    schema: Any,
    root: Any,
    path: str,
    errors: list[str],
    counters: _SchemaValidationCounters,
) -> None:
    """Check one instance node against one schema node, appending any failures.

    Implements only the keywords in `_IMPLEMENTED_SCHEMA_KEYWORDS`. An unimplemented
    keyword is itself reported as an error rather than ignored, which is what stops
    the validator drifting behind the schema.

    Args:
        instance: The instance node.
        schema: The schema node applying to it.
        root: The whole schema document, for `$ref` lookups.
        path: A JSON-pointer-ish trail, used in messages.
        errors: Accumulator, appended to in place.
        counters: Work counters, incremented in place.
    """
    counters.nodes += 1

    if not isinstance(schema, dict):
        errors.append(f"{path}: schema node is not an object")
        return

    unimplemented = set(schema) - _IMPLEMENTED_SCHEMA_KEYWORDS
    if unimplemented:
        errors.append(
            f"{path}: schema uses keyword(s) this validator does not implement: "
            f"{sorted(unimplemented)}"
        )
        return

    if "$ref" in schema:
        reference = schema["$ref"]
        if not reference.startswith("#/$defs/"):
            errors.append(f"{path}: unsupported $ref target {reference!r}")
            return
        name = reference[len("#/$defs/") :]
        target = root.get("$defs", {}).get(name)
        if target is None:
            errors.append(f"{path}: $ref {reference!r} does not name a $defs entry")
            return
        counters.refs_followed += 1
        _validate_against_schema(instance, target, root, path, errors, counters)
        # In draft 2020-12 `$ref` is an applicator that sits ALONGSIDE its siblings
        # rather than replacing them, so the remaining keywords are applied too. In
        # this schema every `$ref` sibling is an annotation - asserted by
        # `test_every_ref_node_carries_only_annotations_beside_it` - so the loop
        # below has nothing to do; it is written this way so that it would still be
        # correct if a constraint were ever added next to a `$ref`.
        siblings = {
            key: value for key, value in schema.items() if key != "$ref"
        }
        if set(siblings) - {"description", "title", "examples"}:
            _validate_against_schema(
                instance, siblings, root, path, errors, counters
            )
        return

    if "type" in schema:
        counters.keywords_applied += 1
        declared = schema["type"]
        names = declared if isinstance(declared, list) else [declared]
        if not any(_json_type_matches(instance, name) for name in names):
            errors.append(
                f"{path}: expected type {declared!r}, got "
                f"{type(instance).__name__}"
            )
            return

    if "const" in schema:
        counters.keywords_applied += 1
        if instance != schema["const"]:
            errors.append(f"{path}: expected const {schema['const']!r}")

    if "enum" in schema:
        counters.keywords_applied += 1
        if instance not in schema["enum"]:
            errors.append(f"{path}: {instance!r} is not one of {schema['enum']!r}")

    if isinstance(instance, str):
        if "minLength" in schema:
            counters.keywords_applied += 1
            if len(instance) < schema["minLength"]:
                errors.append(
                    f"{path}: shorter than minLength {schema['minLength']}"
                )
        if "pattern" in schema:
            counters.keywords_applied += 1
            if re.search(schema["pattern"], instance) is None:
                errors.append(
                    f"{path}: {instance!r} does not match {schema['pattern']!r}"
                )

    if isinstance(instance, int) and not isinstance(instance, bool):
        if "minimum" in schema:
            counters.keywords_applied += 1
            if instance < schema["minimum"]:
                errors.append(f"{path}: below minimum {schema['minimum']}")

    if isinstance(instance, list):
        if "minItems" in schema:
            counters.keywords_applied += 1
            if len(instance) < schema["minItems"]:
                errors.append(f"{path}: fewer than minItems {schema['minItems']}")
        if schema.get("uniqueItems") is True:
            counters.keywords_applied += 1
            rendered = [json.dumps(item, sort_keys=True) for item in instance]
            if len(set(rendered)) != len(rendered):
                errors.append(f"{path}: items are not unique")
        if "items" in schema:
            for index, item in enumerate(instance):
                _validate_against_schema(
                    item, schema["items"], root, f"{path}[{index}]", errors, counters
                )

    if isinstance(instance, dict):
        properties = schema.get("properties", {})
        for name in schema.get("required", ()):
            counters.keywords_applied += 1
            if name not in instance:
                errors.append(f"{path}: required property {name!r} is missing")
        if schema.get("additionalProperties") is False:
            counters.keywords_applied += 1
            extra = sorted(set(instance) - set(properties))
            if extra:
                errors.append(f"{path}: additional propert(ies) {extra} not allowed")
        for name, value in instance.items():
            subschema = properties.get(name)
            if subschema is not None:
                _validate_against_schema(
                    value, subschema, root, f"{path}/{name}", errors, counters
                )


def _validate_document(
    document: object, schema: Any
) -> tuple[list[str], _SchemaValidationCounters]:
    """Validate a whole instance document against a whole schema document.

    Args:
        document: The parsed instance.
        schema: The parsed schema.

    Returns:
        The error list - empty on success - and the work counters.
    """
    errors: list[str] = []
    counters = _SchemaValidationCounters()
    # The three document-level annotation keywords are not constraints, so the root
    # is validated with them removed rather than being reported as unimplemented.
    root_schema = {
        key: value
        for key, value in schema.items()
        if key not in ("$schema", "$id", "title", "$defs")
    }
    _validate_against_schema(document, root_schema, schema, "", errors, counters)
    return errors, counters


def test_the_committed_dictionary_validates_against_its_committed_schema() -> None:
    """The mandated deliverable, exercised: zero validation errors.

    Agent Action Plan section 0.8.5's completion criterion, asserted rather than
    believed. The two files are read from disk exactly as committed and nothing is
    regenerated: this test is a drift alarm on the artifacts, not a re-derivation of
    them.

    The work counters are asserted as well, because "no errors" is also what a
    validator that visited nothing would report. Several thousand nodes and several
    hundred `$ref` indirections are the floor; the real figures are far higher, and
    a floor rather than an exact count keeps the test from breaking every time a
    field is added to the dictionary.
    """
    assert _DICTIONARY_JSON.is_file(), _DICTIONARY_JSON
    assert _DICTIONARY_SCHEMA_JSON.is_file(), _DICTIONARY_SCHEMA_JSON

    document = json.loads(_DICTIONARY_JSON.read_text(encoding="utf-8"))
    schema = json.loads(_DICTIONARY_SCHEMA_JSON.read_text(encoding="utf-8"))

    errors, counters = _validate_document(document, schema)

    assert errors == [], errors[:10]
    # Measured on the committed pair: 100,869 instance nodes visited, 26,508 `$ref`
    # indirections taken and 184,413 constraint keywords evaluated. Asserted as
    # FLOORS rather than as equalities, because the artifact grows when a field is
    # catalogued and an equality would then fail for a legitimate regeneration -
    # while a floor still refuses a validator that walked almost nothing.
    assert counters.nodes > 50_000
    assert counters.refs_followed > 20_000
    assert counters.keywords_applied > 100_000
    # And the document really is the dictionary the loader reads, so this test and
    # every descriptor test above are looking at the same file.
    assert len(document["entries"]) == 1_061
    assert len(document["tables"]) == 22
    assert document["coverage"]["in_scope_columns"] == 513


def test_the_schema_reference_in_the_dictionary_cannot_rot() -> None:
    """`meta.schema_ref` names the schema file that sits beside the dictionary.

    The reference is a bare file name rather than a path, so it is only meaningful
    while the two files are siblings - which is asserted here by resolving it against
    the dictionary's own directory and requiring the result to be the committed
    schema.
    """
    document = json.loads(_DICTIONARY_JSON.read_text(encoding="utf-8"))
    reference = document["meta"]["schema_ref"]

    assert reference == _DICTIONARY_SCHEMA_JSON.name
    beside_the_dictionary = _DICTIONARY_JSON.parent / reference
    assert beside_the_dictionary.is_file()
    assert beside_the_dictionary == _DICTIONARY_SCHEMA_JSON

    schema = json.loads(_DICTIONARY_SCHEMA_JSON.read_text(encoding="utf-8"))
    # Draft 2020-12, which is the dialect the validator above implements a subset of.
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:acas:data-dictionary:acas_posting_dictionary:1"
    assert schema["required"] == ["meta", "sources", "tables", "entries", "coverage"]


def test_the_schemas_keyword_set_is_closed_and_fully_implemented() -> None:
    """Every keyword the schema uses is one this validator evaluates.

    This is what makes the subset validator honest. If the schema ever starts using
    `anyOf`, `format`, `patternProperties` or anything else, the set below stops
    being a subset of the implemented set and this test fails - rather than the
    document being validated against a schema whose new constraint was skipped.

    Two structural facts are asserted with it, because the validator relies on both:
    `additionalProperties` is literal `false` everywhere it appears, and every `$ref`
    points into `#/$defs`.
    """
    schema = json.loads(_DICTIONARY_SCHEMA_JSON.read_text(encoding="utf-8"))

    used: set[str] = set()
    additional_property_values: list[object] = []
    reference_targets: list[str] = []

    def visit(node: object, at_schema_position: bool) -> None:
        if isinstance(node, list):
            for item in node:
                visit(item, False)
            return
        if not isinstance(node, dict):
            return
        if at_schema_position:
            used.update(node)
            if "additionalProperties" in node:
                additional_property_values.append(node["additionalProperties"])
            if "$ref" in node:
                reference_targets.append(node["$ref"])
            for key, value in node.items():
                if key in ("properties", "$defs"):
                    for sub in value.values():
                        visit(sub, True)
                elif key == "items":
                    visit(value, True)
                else:
                    visit(value, False)
            return
        for value in node.values():
            visit(value, False)

    visit(schema, True)

    assert used, "no schema keywords were seen - the walk is wrong"
    assert used <= _IMPLEMENTED_SCHEMA_KEYWORDS, sorted(
        used - _IMPLEMENTED_SCHEMA_KEYWORDS
    )
    # No combinator, and no keyword whose absence the validator relies on.
    for absent in (
        "anyOf",
        "oneOf",
        "allOf",
        "not",
        "if",
        "then",
        "else",
        "prefixItems",
        "patternProperties",
        "format",
        "$dynamicRef",
        "unevaluatedProperties",
    ):
        assert absent not in used, absent

    assert set(map(repr, additional_property_values)) == {"False"}
    assert len(additional_property_values) == 25
    assert len(reference_targets) == 66
    assert all(target.startswith("#/$defs/") for target in reference_targets)
    assert len(schema["$defs"]) == 40


@pytest.mark.parametrize(
    "perturbation",
    [
        "extra-property",
        "drop-required",
        "wrong-type",
        "break-pattern",
        "empty-required-array",
        "break-const",
    ],
    ids=[
        "an unexpected property is refused",
        "a missing required key is refused",
        "a wrong JSON type is refused",
        "a pattern violation is refused",
        "a minItems violation is refused",
        "a const violation is refused",
    ],
)
def test_the_subset_validator_is_discriminating_not_vacuous(
    perturbation: str,
) -> None:
    """A perturbed IN-MEMORY copy of the document MUST be rejected.

    Without this, "zero errors" would be worth nothing: a validator that returned an
    empty list unconditionally would pass the test above. Six independent keyword
    families are perturbed, one per run, and each must produce at least one error.

    THE COMMITTED FILES ARE NEVER TOUCHED. Every perturbation is applied to a
    `copy.deepcopy` of the parsed document, and the committed dictionary is re-read
    and re-validated at the end of each run to prove it is still clean.
    """
    document = json.loads(_DICTIONARY_JSON.read_text(encoding="utf-8"))
    schema = json.loads(_DICTIONARY_SCHEMA_JSON.read_text(encoding="utf-8"))
    perturbed = copy.deepcopy(document)

    if perturbation == "extra-property":
        perturbed["meta"]["a_property_the_schema_does_not_declare"] = "x"
    elif perturbation == "drop-required":
        del perturbed["coverage"]["in_scope_columns"]
    elif perturbation == "wrong-type":
        perturbed["coverage"]["in_scope_columns"] = "513"
    elif perturbation == "break-pattern":
        perturbed["entries"][0]["key"] = "no dot, no table, not a key"
    elif perturbation == "empty-required-array":
        perturbed["entries"] = []
    elif perturbation == "break-const":
        perturbed["meta"]["schema_ref"] = "some-other-schema.json"

    errors, counters = _validate_document(perturbed, schema)

    assert errors != [], (
        f"the {perturbation} perturbation was accepted, so the validator is not "
        f"discriminating on that keyword family"
    )
    assert counters.nodes > 0

    # The committed artifact is untouched and still validates.
    still_clean, _ = _validate_document(
        json.loads(_DICTIONARY_JSON.read_text(encoding="utf-8")), schema
    )
    assert still_clean == []


def test_the_subset_validator_refuses_a_schema_keyword_it_cannot_evaluate() -> None:
    """An unknown keyword is an ERROR, never a silent skip.

    This is the property that makes the closed-keyword test above load-bearing
    rather than decorative: if the schema gained a constraint the validator does not
    implement, validation reports it instead of quietly passing. Exercised on a
    deep copy of the committed schema, so the committed file is untouched.
    """
    document = json.loads(_DICTIONARY_JSON.read_text(encoding="utf-8"))
    schema = json.loads(_DICTIONARY_SCHEMA_JSON.read_text(encoding="utf-8"))

    widened = copy.deepcopy(schema)
    widened["$defs"]["coverage"]["properties"]["in_scope_columns"]["multipleOf"] = 7

    errors, _ = _validate_document(document, widened)

    assert errors != []
    assert any("does not implement" in message for message in errors), errors[:5]

    # And a constraint is detectable in the other direction too: tightening the
    # entry-key pattern - which lives in `$defs.entryKey`, reached through the `$ref`
    # at `$defs.entry.properties.key` - to something no key can satisfy must fail
    # once per entry, proving the pattern really is applied to all 1,061 of them
    # through the indirection rather than only at the top level.
    tightened = copy.deepcopy(schema)
    tightened["$defs"]["entryKey"]["pattern"] = r"^ZZZ-NOTHING\."
    tightened_errors, _ = _validate_document(document, tightened)
    assert len(tightened_errors) >= 1_000, len(tightened_errors)


def test_neither_committed_artifact_carries_a_repeated_json_member() -> None:
    """A repeated JSON member would silently discard a constraint.

    `json.loads` follows the permissive reading: a member that appears twice in one
    object keeps the LAST occurrence and drops the first without complaint. So an
    edit that added `"pattern": ...` beside an existing `"pattern"` in the schema
    would parse cleanly, would validate cleanly, and would have no effect - the new
    constraint silently ignored. `acas_posting/dictionary/loader.py` refuses exactly
    this for the dictionary, citing the same reasoning; the schema is read here with
    plain `json.loads`, so the check has to be made explicitly.

    Learned the hard way: a mutation of the schema that inserted a second `pattern`
    beside the entry-key one appeared to be accepted by this group, and the reason was
    this permissive reading rather than any weakness in the validator.
    """
    seen_repeats: list[tuple[str, str]] = []

    def refuse_repeats(label: str):
        def hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
            names = [name for name, _ in pairs]
            # `dict.fromkeys` keeps first-seen order and de-duplicates, so a name
            # repeated twice is reported once rather than once per occurrence.
            for name in dict.fromkeys(names):
                if names.count(name) > 1:
                    seen_repeats.append((label, name))
            return dict(pairs)

        return hook

    for label, path in (
        ("dictionary", _DICTIONARY_JSON),
        ("schema", _DICTIONARY_SCHEMA_JSON),
    ):
        json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=refuse_repeats(label),
        )

    assert seen_repeats == [], seen_repeats

    # And the detection detects: a synthetic document with a repeated member is
    # caught, so the empty result above is evidence and not an artefact.
    seen_repeats.clear()
    json.loads(
        '{"a": 1, "a": 2}', object_pairs_hook=refuse_repeats("synthetic")
    )
    assert seen_repeats == [("synthetic", "a")]


def test_every_ref_node_carries_only_annotations_beside_it() -> None:
    """A `$ref` in this schema never sits next to a constraint.

    The validator applies a `$ref`'s siblings as draft 2020-12 requires, but this
    schema only ever puts `description` beside a `$ref`. Asserting that keeps the
    reading unambiguous, and means the 66 indirections cannot hide a constraint that
    a careless reader of the schema would miss.
    """
    schema = json.loads(_DICTIONARY_SCHEMA_JSON.read_text(encoding="utf-8"))
    annotations = {"description", "title", "examples"}
    offenders: list[tuple[str, list[str]]] = []

    def visit(node: object, trail: str) -> None:
        if isinstance(node, list):
            for index, item in enumerate(node):
                visit(item, f"{trail}[{index}]")
            return
        if not isinstance(node, dict):
            return
        if "$ref" in node:
            beside = sorted(set(node) - {"$ref"} - annotations)
            if beside:
                offenders.append((trail, beside))
        for key, value in node.items():
            visit(value, f"{trail}/{key}")

    visit(schema, "")

    assert offenders == [], offenders
