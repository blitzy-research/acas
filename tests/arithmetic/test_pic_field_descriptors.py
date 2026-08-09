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
    The six binding rules R-1 .. R-6 live in the Technical Specification section
    0.7.2, and where that specification is silent this file holds to
    enterprise-standard best practice.

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

         Where a question about a STORED VALUE arises, this file asserts what the
         dictionary RECORDS about it and never a value of its own:

             Q-3  what a negative binary value becomes once it has passed through an
                  unsigned host variable into an unsigned column. MEASURED on GnuCOBOL
                  3.2.0: the absolute value, then bounded by the
                  receiving digit count. The 91 affected entries now carry that
                  measurement in their notes and no longer publish `Q-3` in
                  `ambiguity_refs()`, while anomaly `A-11` stays on every one - and
                  this file asserts exactly that state.
             Q-4  which of the batch record's two declared lengths governs the record
                  that is actually read. MEASURED on GnuCOBOL 3.2.0: `Q-4` is
                  `RESOLVED BY ORACLE` (2026-08-07) and the answer is NEITHER of the
                  maintainer's two readings taken as a contest - both record copies
                  measure 96, `FUNCTION LENGTH` agrees with the field sum, and the 98
                  is false. That answer changes NOTHING here, because the field sum is
                  already what these descriptors encode, so `Q-4` remains published in
                  `ambiguity_refs()` on all 28 affected entries as a CROSS-REFERENCE to
                  the register - the same way `A-15` stays on them. Contrast `Q-3`,
                  whose measurement changed what a STORED VALUE becomes and therefore
                  moved into the entries' notes and out of `ambiguity_refs()`.

         Consequently this file carries NO expected-failure marker: neither question
         needs one, because this file asserts no value of its own for either - for `Q-4`
         it asserts only the two DECLARED lengths and the published cross-references,
         and for `Q-3` the measurement is on record and is asserted plainly. Section
         0.8.4 also applies - there is no timing assertion and no performance
         measurement anywhere.

WHERE THIS FILE DIVERGES FROM ITS OWN BRIEF, AND WHY
    The brief for this file was written against an earlier shape of the API and three of
    its statements do not match the code as committed. In each case the CODE governs,
    because a test must bind to the module it tests:

      * `FieldDescriptor.for_working_storage` no longer exists - see the note at
        [acas_posting/cobol/field.py _require_dictionary_provenance]. A program-local field is therefore
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
import importlib
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

# Imports carried in with the merged group below, which was
# test_deployment_contract_boundaries.py. Only the pieces the block above did not
# already provide are listed (Agent Action Plan section 0.3.1 inventory).
import argparse
import ast
import builtins
import dataclasses
import doctest
import hashlib
import importlib.util
import inspect
import pkgutil
import symtable
import textwrap
import tomllib
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType

pytestmark = pytest.mark.arithmetic

# A SNAPSHOT OF THE IMPORT GRAPH the instant this module finished importing, taken at
# module scope precisely because it must be taken THEN and not later. R-1's claim is
# about what THIS TIER pulls in, and the arithmetic tier is the one that "touches
# neither COBOL nor a database" (Technical Specification section 0.7.2). Live
# `sys.modules` inside a test body measures something else entirely: the scenario and
# determinism tiers load a database driver and `harness/*` quite legitimately - section
# 0.4.3 puts both on the harness side - so whenever one of their tests has already run
# in the same process, an absolute check on live residency fails for a reason that has
# nothing to do with this tier. That made the guard below ORDER-DEPENDENT: green in the
# default alphabetical order and red under `pytest tests/scenarios tests/arithmetic`,
# which is a property of the run and not of the code under test.
#
# The snapshot is safe as well as sufficient: no test module in this suite, and not
# `tests/conftest.py`, imports a driver, PyYAML or the harness at module scope - every
# one of them is loaded lazily inside a fixture - so at the moment this module is
# imported none of the forbidden names can be resident however the files were ordered.
#
# `tests/arithmetic/test_comp3_packed_decimal.py` takes the same snapshot for the same
# reason, and `tests/arithmetic/test_comp_binary.py` demonstrates the stronger form in a
# FRESH INTERPRETER; between them the tier keeps both readings of the property.
_MODULES_PRESENT_AT_IMPORT: Final[frozenset[str]] = frozenset(sys.modules)


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
    was question Q-3, and only running the compiled program could settle it. It has
    been run: the bridge stores the ABSOLUTE VALUE, bounded by the
    receiving digit count. So this test asserts that the drift is recorded, that the
    measurement is in the entry's notes and that `Q-3` is no longer published as open -
    and it still asserts no stored value of its own, because the stored value belongs to
    `tests/arithmetic/test_comp_binary.py`, which owns the measurement.
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
    # R-6: no stored value is INVENTED here. What is asserted is the MEASUREMENT the
    # register recorded, read out of the entry's own notes rather than restated.
    # Q-3 IS RESOLVED: GnuCOBOL 3.2.0 stores the ABSOLUTE VALUE,
    # bounded by the receiving digit count. So the entry no longer publishes it as
    # an OPEN question - it publishes the measurement - while anomaly A-11, the
    # sign loss itself, stays exactly as it was (rule R-4).
    assert "Q-3" not in descriptor.ambiguity_refs()
    assert any(
        "MEASURED against GnuCOBOL" in note
        for note in loader.get_entry(descriptor.dictionary_key).notes
    )
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
    # Q-3 IS RESOLVED: GnuCOBOL 3.2.0 stores the ABSOLUTE VALUE,
    # bounded by the receiving digit count. So the entry no longer publishes it as
    # an OPEN question - it publishes the measurement - while anomaly A-11, the
    # sign loss itself, stays exactly as it was (rule R-4).
    assert "Q-3" not in descriptor.ambiguity_refs()
    assert any(
        "MEASURED against GnuCOBOL" in note
        for note in loader.get_entry(descriptor.dictionary_key).notes
    )

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
    NOT ASSERT WHICH IS RIGHT, and must not: the declared lengths live in an ARRAY
    precisely so the contradiction is CARRIED rather than adjudicated here. Only running
    the compiled program could settle which length governs the record actually read, and
    it has: `Q-4` in `docs/migration/ambiguity-resolutions.md` is `RESOLVED BY ORACLE`
    (2026-08-07), the answer is NEITHER - both copies measure 96 and `FUNCTION LENGTH`
    agrees with the field sum - and `docs/migration/anomaly-log.md` carries A-15 as
    `REPRODUCED - VALUE MEASURED`. The array below still holds BOTH lengths, because
    measuring the contradiction did not repair the copybook and nothing may (R-4).
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

    # Every field of the record carries the anomaly and the ambiguity cross-reference,
    # so a reader arriving at any one of them is led to the contradiction and to the
    # measured answer recorded against it. `Q-4` is RESOLVED, and the reference is kept
    # for exactly that reason: it is the route from a field to the measurement.
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
    # spec: the invariant at [acas_posting/cobol/field.py MissingProvenanceError]
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
#  [acas_posting/cobol/field.py _require_dictionary_provenance] - so these are minted by the picture
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


def test_the_committed_dictionary_is_reproducible_from_the_frozen_sources() -> None:
    """RUN THE PRODUCER, not only read what it produced.

    Rule R-5 makes the dictionary the single source of field truth, and every other
    dictionary test in this file reads the COMMITTED artifact. That leaves the
    GENERATOR - `acas_posting/dictionary/generate.py`, the largest module in the package
    - executed by nothing: measured with `--cov`, 0.0 % of its statements ran under the
    whole corpus. A generator regression was therefore invisible until someone
    regenerated by hand, and at that point the diff would be attributed to whatever else
    had changed in between.

    `main(["--check"])` is the right invocation for a test, and the only one that is: it
    re-parses the frozen bridge sources, the copybooks and `mysql/ACASDB.sql`, renders
    the document, compares it against the committed file and WRITES NOTHING - so the
    artifact under test cannot be repaired by the act of testing it. Exit 0 means the
    committed dictionary is exactly what the frozen sources produce today; exit 1 means
    it has drifted and prints the unified diff; 2 a parse or coverage failure; 3 an
    unreadable comparison file.

    BOTH INVOCATION SHAPES ARE DRIVEN, because they were not equivalent. `--repo-root`
    alone used to leave `--output` defaulted to a path derived from the INSTALLED package
    rather than from the root just given, so from a wheel install the tool parsed
    `/repo` and then compared against `site-packages/../data_dictionary/…`. The default
    now follows `--repo-root`, and passing one option is as coherent as passing both.

    It needs no database, no oracle and no Docker - only the frozen checkout - so it
    belongs in the tier that runs anywhere.
    """
    generate = importlib.import_module("acas_posting.dictionary.generate")

    assert generate.main(["--check"]) == 0, (
        "the committed data_dictionary/acas_posting_dictionary.json is NOT what a fresh "
        "parse of the frozen sources produces. Either a frozen source changed - which "
        "AAP section 0.8.1 makes a defect in the migration - or the generator drifted. "
        "Run `python -m acas_posting.dictionary.generate --check` for the unified diff."
    )

    assert generate.main(["--check", "--repo-root", str(_REPO_ROOT)]) == 0, (
        "`--check --repo-root <root>` with no `--output` disagreed with the committed "
        "artifact. The output default must follow the root it was given, or a caller "
        "who names one of the pair silently compares against the other's tree."
    )

    #  And the failure direction, so exit 0 is not merely the only outcome this tool can
    #  produce: checked against an output path that does not exist, the tool must report
    #  3 rather than claiming agreement.
    assert generate.main(
        ["--check", "--output", str(_REPO_ROOT / "no-such-dictionary.json")]
    ) == 3


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

    MEASURED AT THIS MODULE'S IMPORT, NOT AT ITS RUN. `_MODULES_PRESENT_AT_IMPORT` is
    the snapshot; live `sys.modules` is deliberately NOT consulted. A scenario test that
    has already run in the same process has legitimately loaded a driver and the
    harness, so an absolute check on live residency would report THE RUN ORDER as an
    R-1 violation - which is a false failure, and was one: the guard used to pass under
    `pytest tests` and fail under `pytest tests/scenarios tests/arithmetic`. What R-1
    constrains is this tier's own import surface, and that is exactly what the snapshot
    holds.
    """
    # spec: Technical Specification section 0.7.2 R-1 - "tests/arithmetic/* touch
    #       neither COBOL nor a database"; R-2 excludes pandas and numpy by name.
    loaded = _MODULES_PRESENT_AT_IMPORT

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

    # THE SNAPSHOT ITSELF MUST BE REAL. A snapshot taken too early - before this
    # module's own imports had run - would hold almost nothing and every assertion
    # above would pass vacuously, which is precisely the failure mode the rest of this
    # suite is being hardened against.
    assert "acas_posting.cobol.picture" in loaded, (
        "the import snapshot does not contain this module's own dependency "
        "`acas_posting.cobol.picture`, so it was taken before the imports it is "
        "supposed to describe. Every assertion above would then hold vacuously."
    )
    assert "acas_posting.dictionary.loader" in loaded, (
        "the import snapshot does not contain `acas_posting.dictionary.loader`, which "
        "this module imports in its own import block. The snapshot must be taken AFTER "
        "that block, not before it."
    )


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
#: working directory. `tests/conftest.py REPO_ROOT` derives `REPO_ROOT` the same way and for
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
    assert len(document["entries"]) == 1_067
    assert len(document["tables"]) == 22
    assert document["coverage"]["in_scope_columns"] == 513


def test_every_physical_copybook_declaration_has_its_own_entry() -> None:
    """R-5 closure over the DECLARATION MULTISET, never over an aggregate.

    WHY A TOTAL IS NOT ENOUGH, stated as the defect it hid. Before this test the
    artifact reported 1001 copybook fields covered against 1001 physical declarations,
    and both numbers were right while the mapping between them was wrong:
    `copybooks/plwsoi5C.cob` had ONE entry for its SEVEN declarations, and
    `copybooks/irswsnl.cob` had TWENTY entries for its FOURTEEN, because six of its
    declarations carry `OCCURS` and one entry per occurrence cites the same physical
    line. The six extra citations made up the exact shortfall, so the totals agreed and
    six fields a reader can point at in a frozen file had no structured entry at all -
    which rule R-5 does not permit.

    So this compares the two populations FILE BY FILE AND LINE BY LINE. It is the
    assertion the aggregate could not make, and it fails loudly if a future change to the
    generator's signature or election logic re-collapses two variant declarations into
    one entry.
    """
    generate = importlib.import_module("acas_posting.dictionary.generate")

    declared: dict[str, set[tuple[int, str]]] = {}
    for rel in generate._copybook_closure(_REPO_ROOT):
        items = generate._parse_copybook(_REPO_ROOT, rel)
        # Every item parsed from a file must claim that file, or the comparison below
        # would be measuring two different populations.
        assert {item.file for item in items} <= {rel}, rel
        declared[rel] = {(item.line, item.name.lower()) for item in items}

    document = json.loads(_DICTIONARY_JSON.read_text(encoding="utf-8"))
    cited: dict[str, set[tuple[int, str]]] = {}
    for entry in document["entries"]:
        copybook = entry["copybook"]
        if copybook is None:
            continue
        locator = copybook["source"]
        rel, _, line = locator.rpartition(":L")
        assert rel == copybook["file"], locator
        cited.setdefault(rel, set()).add((int(line), copybook["name"].lower()))

    assert set(cited) == set(declared), (
        "the set of copybook FILES the dictionary cites is not the closure it was built "
        f"from: only-cited={sorted(set(cited) - set(declared))!r}, "
        f"only-declared={sorted(set(declared) - set(cited))!r}"
    )
    for rel in sorted(declared):
        assert cited[rel] == declared[rel], (
            f"{rel}: the declarations cited by the dictionary are not the declarations "
            f"the file makes. Uncited={sorted(declared[rel] - cited[rel])!r}, "
            f"cited-but-not-declared={sorted(cited[rel] - declared[rel])!r}"
        )

    # The two published figures, and the fact that they DIFFER, which is what keeps the
    # distinction visible: 1001 distinct declarations, 1007 entries citing them.
    total_declarations = sum(len(lines) for lines in declared.values())
    assert total_declarations == 1_001
    assert document["coverage"]["copybook_declarations_covered"] == total_declarations
    assert document["coverage"]["copybook_fields_covered"] == 1_007
    assert (
        document["coverage"]["copybook_fields_covered"]
        > document["coverage"]["copybook_declarations_covered"]
    ), (
        "the entry tally is no longer larger than the declaration tally, so either the "
        "OCCURS expansion has stopped producing one entry per occurrence or a "
        "declaration has lost its entry"
    )

    # And the six that were missing are present under their file-qualified keys, named
    # individually so a regression cannot be read as a rounding difference.
    keys = {entry["key"] for entry in document["entries"]}
    for missing_before in (
        "WS-OTM5-Record.WS-OTM5-Record@plwsoi5C",
        "Open-Item-Record-5.Open-Item-Record-5@plwsoi5C",
        "Open-Item-Record-5.oi5-supplier@plwsoi5C",
        "Open-Item-Record-5.oi5-invoice@plwsoi5C",
        "Open-Item-Record-5.oi5-date@plwsoi5C",
        "Open-Item-Record-5.filler@plwsoi5C",
    ):
        assert missing_before in keys, missing_before
    # The canonical unqualified spellings stay with plwsoi5B, and `oi5-key` stays with
    # plwsoi5C because the column pass consumed 5B's copy - the key must not move.
    by_key = {entry["key"]: entry for entry in document["entries"]}
    assert by_key["Open-Item-Record-5.oi5-supplier"]["copybook"]["file"] == (
        "copybooks/plwsoi5B.cob"
    )
    assert by_key["Open-Item-Record-5.oi5-key"]["copybook"]["file"] == (
        "copybooks/plwsoi5C.cob"
    )


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
    # once per entry, proving the pattern really is applied to all 1,067 of them
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


# ---------------------------------------------------------------------------
#  EVERY RECORD ATTRIBUTE REACHES A DICTIONARY ENTRY
#
#  Rule R-5 requires field-level traceability: every record field maps to a
#  data-dictionary entry. `acas_posting/dictionary/loader.py` makes that mechanical by
#  trying a fixed sequence of routes - field metadata, a class constant, the class's
#  and module's named descriptor maps, then position within `FIELDS`, then group
#  membership. The claim "every field is traceable" is therefore only as good as that
#  sequence covering every field, and nothing was checking that it did.
#
#  Exactly one attribute of 976 did not route: `SystemDataBlock.filler_81`, where two
#  ordinary facts combined badly. The positional route needs `FIELDS` and the dataclass
#  fields to be the same length, and `SYSTEM-REC` has 46 descriptors against 45 fields
#  because `Scycle REDEFINES Cyclea` [copybooks/wssystem.cob:L62-L63] is one storage
#  location modelled as one field plus a property. And the name route cannot help,
#  because the descriptor's COBOL name is the bare `FILLER` [copybooks/wssystem.cob:L81]
#  while the attribute must carry its line number to be a distinct Python name.
#
#  This asserts the property as a COUNT over the whole package, so a future field that
#  lands in the same gap fails here instead of silently losing its traceability. It is
#  the census the finding was raised from, kept.
def _record_dataclasses() -> list[type]:
    """Every record dataclass the package defines, discovered rather than listed.

    Discovery matters: a hand-written list would not cover a record module added
    later, which is exactly the case this census exists to catch.

    Returns:
        The dataclasses, each defined by the module it is found in.
    """
    import dataclasses as _dc
    import importlib
    import pkgutil

    import acas_posting.records as records_package

    found: list[type] = []
    for module_info in pkgutil.iter_modules(records_package.__path__):
        module = importlib.import_module(f"acas_posting.records.{module_info.name}")
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and _dc.is_dataclass(value)
                and value.__module__ == module.__name__
            ):
                found.append(value)
    return found


def test_every_record_attribute_routes_to_a_dictionary_entry() -> None:
    """No record attribute is left without a dictionary key or a group type.

    A `FieldTrace` carries `dictionary_key` for a scalar and `group_type` for a group
    item, so an attribute is traced when it has either. One with neither has no route
    at all, and R-5's field-level traceability claim does not hold of it.
    """
    layouts = _record_dataclasses()
    assert len(layouts) >= 27, (
        f"only {len(layouts)} record dataclasses were discovered; the package defines "
        "at least one per copybook across 27 modules, so discovery has broken and this "
        "census would pass by looking at almost nothing"
    )

    traced = 0
    unrouted: list[str] = []
    for layout in layouts:
        for trace in loader.trace_record(layout):
            traced += 1
            if trace.dictionary_key is None and trace.group_type is None:
                unrouted.append(
                    f"{layout.__module__}.{layout.__qualname__}.{trace.attribute} "
                    f"(route tried: {trace.route!r})"
                )

    assert traced >= 976, (
        f"only {traced} attributes were traced; the census covered 976 when this was "
        "written, so a sharp drop means whole records stopped being discovered and a "
        "green result here would mean nothing"
    )
    assert not unrouted, (
        f"{len(unrouted)} of {traced} record attributes reach no dictionary entry, so "
        "rule R-5's field-level traceability does not hold of them:\n  "
        + "\n  ".join(unrouted)
        + "\n\n  Give the field an explicit route, e.g. "
        'field(metadata={"dictionary_key": ...}), taking the key from the module\'s '
        "own key index rather than writing it as a literal."
    )


def test_the_repeated_filler_that_had_no_route_now_has_one() -> None:
    """`SystemDataBlock.filler_81` routes by stated key, to the entry it names.

    Named specifically as well as counted, because the count alone would go green
    again if the attribute were deleted rather than routed - and deleting a `FILLER`
    the frozen record declares would be a change to the layout, not a fix.
    """
    from acas_posting.records.system_record import SystemDataBlock

    traces = {trace.attribute: trace for trace in loader.trace_record(SystemDataBlock)}
    assert "filler_81" in traces, (
        "SystemDataBlock no longer declares filler_81. The frozen record declares that "
        "FILLER at [copybooks/wssystem.cob:L81]; removing it changes the layout."
    )
    trace = traces["filler_81"]
    assert trace.dictionary_key == "System-Record.FILLER#81", (
        f"filler_81 routes to {trace.dictionary_key!r}, not to the entry for the FILLER "
        "declared at [copybooks/wssystem.cob:L81]."
    )
    assert trace.route == "metadata[dictionary_key]", (
        f"filler_81 routes by {trace.route!r}. The explicit metadata route is the one "
        "that must find it: the positional route is unavailable here because FIELDS "
        "carries 46 descriptors against 45 dataclass fields (Scycle REDEFINES Cyclea), "
        "and no name route can match a suffixed attribute against a bare FILLER."
    )
    assert trace.entry is not None, (
        "filler_81 carries a key that resolves to no entry in the artifact, which is a "
        "dangling route rather than a route."
    )

    # The key must come from the module's own total index, not a literal - so a wrong
    # name or line fails at import. Proven by checking the pair is what the index holds.
    from acas_posting.records import system_record

    assert system_record._KEY_INDEX[("FILLER", 81)] == trace.dictionary_key, (
        "the key stated in metadata is not the one the module's key index yields for "
        "(FILLER, 81), so the two can drift apart."
    )


# ==========================================================================
#
#  Regression locks for the deployment contract and the IRS bind boundary.
#
#  WHY THIS FILE IS IN THE `arithmetic` TIER, WHICH IS OTHERWISE ABOUT PICTURE
#  CLAUSES. That tier's defining property is not its subject but its dependencies:
#  it needs no database, no COBOL and no Docker, so it runs anywhere. Every
#  assertion below reads a declaration or calls a pure function, so it belongs to
#  that tier and NOT to `tests/scenarios/`, whose fixtures require the Compose
#  stack. `tests/arithmetic/test_comp_binary.py` set the
#  precedent for a stack-free structural lock living here.
#
#  WHAT IS LOCKED, AND WHICH DEFECT EACH LOCK CLOSES:
#
#    * ONE transport environment contract. There were two: this package
#      declared four flag variables that nothing in the shipped stack set, while
#      `acas_posting/cli/args.py` read a fifth with a DIFFERENT rule for what counts
#      as an affirmative value. The tests here assert that every row of
#      `cli_args.TRANSPORT_CONTRACT` has a consumer (a field of
#      `TransportPolicyParams`, which `install_connection_policy` turns into the
#      installed `ConnectionPolicy`), that the row the harness provides is the one
#      `harness/docker-compose.yml` actually sets, and that a command-line
#      declaration can no longer annul the contract's refusal switches.
#
#    * the three driver deadlines are finite, and the two layers that name
#      their defaults agree. `dal/connection.py` may not import the entry-point
#      layer, so the defaults are declared twice by necessity; this is what stops
#      them drifting.
#
#    * the IRS route binds once. `bind_irs_route` publishes the snapshot its
#      single `zz090` pass captured, and `bind_irs_linkage` delegates to it rather
#      than repeating the bind.
#
#    * cross-file references into the harness scripts name a SYMBOL and not a
#      line number. 91 distinct line-number locators had accumulated across the nine
#      scenario YAMLs, the migration documents and the scenario tests, and they were
#      stale by construction: they point into files this project edits, so every edit
#      moves them, and the stale reference then reads as present evidence for
#      whatever happens to sit at that line. The four tests at the end of this file
#      assert that no such locator has come back -- into a harness script or into a
#      scenario definition -- and that every symbol and every quoted section heading
#      named actually exists in the file named. Locators into the FROZEN tree -- the
#      `.cbl`, `.cob`, `.sql` and `.sh` files under `common/`, `copybooks/`,
#      `general/`, `sales/`, `purchase/`, `irs/`, `stock/`, `mysql/` -- are exempt and
#      deliberately so: those files cannot change (AAP 0.8.1), so a line number in
#      them is permanently valid and is the most precise reference available.
#
#  EVERY SHIPPED MODULE HERE IS IMPORTED WITH `importlib.import_module` AND NOT WITH
#  `pytest.importorskip`. That is deliberate and it matches the discipline the rest of
#  this tier states at length: `acas_posting.cli.args` (whose SECTION 0 carries the RDBMS connection contract),
#  `acas_posting.cli.gl_post_cycle` and `acas_posting.dal.connection` are all part of the
#  shipped package, and `mysql-connector-python` is a hard `[project.dependencies]` entry
#  and a hard `requirements.txt` pin -- so a module that cannot be imported at all is a
#  BROKEN ENVIRONMENT or a broken module, never a supported configuration. An
#  `importorskip` here reported exactly that condition as a PASS, which is the one outcome
#  a regression lock must not have; `importlib.import_module` lets the `ImportError` reach
#  pytest as the failure it is. The same argument, at greater length, is in
#  `tests/arithmetic/test_compute_truncate_unrounded.py`'s `_shipped_module`.
#
# ==========================================================================


#: A complete six-parameter connection contract, with values that reach nothing.
#: `_bind_system_record` refuses an environment carrying none of the six rather
#: than binding the copybook's placeholder literals, so a binder test has to state
#: them; these are obviously synthetic and no connection is opened by any test in
#: this file.
_FAKE_CONTRACT: dict[str, str] = {
    "ACAS_DB_HOST": "127.0.0.1",
    "ACAS_DB_PORT": "3306",
    "ACAS_DB_NAME": "ACASDB",
    "ACAS_DB_USER": "unit-test",
    "ACAS_DB_PASSWORD": "unit-test",
    "ACAS_DB_SOCKET": "",
}


_COMPOSE = (
    Path(__file__).resolve().parents[2] / "harness" / "docker-compose.yml"
)


def _compose_environment_names() -> frozenset[str]:
    """Return every `ACAS_DB_*` variable the compose file sets in an env block.

    Read with a line regex rather than a YAML parser: the assertion is about the
    literal names a reader of the file sees being set, and the tier is the one
    that must import with nothing installed but pytest.

    Returns:
        The set of variable names assigned in the file, without values - so a
        credential in the file could never reach a failure message.
    """
    text = _COMPOSE.read_text(encoding="utf-8")
    return frozenset(
        match.group(1)
        for match in re.finditer(
            r"^\s{6}(ACAS_DB_[A-Z0-9_]+):", text, flags=re.MULTILINE
        )
    )


def test_every_transport_contract_row_has_a_consumer() -> None:
    """No declared knob may be unread: each names a TransportPolicyParams field."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    fields = {
        field.name
        for field in dataclasses.fields(cli_args.TransportPolicyParams)
    }
    assert fields, "TransportPolicyParams declares no fields"

    for entry in cli_args.TRANSPORT_CONTRACT:
        assert entry.field in fields, (
            f"{entry.variable} resolves into {entry.field!r}, which is not a "
            f"field of TransportPolicyParams; a knob nothing reads is a knob "
            f"that lies about what it does"
        )


def test_every_transport_policy_field_has_a_provider() -> None:
    """No field may be unreachable: each is named by at least one contract row."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    declared = {entry.field for entry in cli_args.TRANSPORT_CONTRACT}
    for field in dataclasses.fields(cli_args.TransportPolicyParams):
        assert field.name in declared, (
            f"TransportPolicyParams.{field.name} is resolved from no declared "
            f"variable, so a deployment cannot set it"
        )


def test_contract_variable_names_are_unique_and_alias_targets_exist() -> None:
    """One name means one thing, and an alias names a row that is really there."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    names = [entry.variable for entry in cli_args.TRANSPORT_CONTRACT]
    assert len(names) == len(set(names)), f"duplicate contract variable: {names}"

    canonical = {
        entry.variable
        for entry in cli_args.TRANSPORT_CONTRACT
        if entry.alias_of is None
    }
    for entry in cli_args.TRANSPORT_CONTRACT:
        if entry.alias_of is not None:
            assert entry.alias_of in canonical, (
                f"{entry.variable} is declared an alias of {entry.alias_of!r}, "
                f"which is not a canonical row of the contract"
            )


def test_the_harness_provides_exactly_the_rows_marked_provided() -> None:
    """`provided_by_harness` is a claim about docker-compose.yml, so check it."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    if not _COMPOSE.is_file():  # pragma: no cover - the file is committed
        pytest.skip(f"{_COMPOSE} is absent, so its claims cannot be checked")

    supplied = _compose_environment_names()
    for entry in cli_args.TRANSPORT_CONTRACT:
        if entry.provided_by_harness:
            assert entry.variable in supplied, (
                f"{entry.variable} is marked provided_by_harness but "
                f"harness/docker-compose.yml does not set it"
            )


def test_the_facades_transport_partition_is_the_measured_one() -> None:
    """`dal/facade.py` states HOW MANY handlers take a policy by which route. Check it.

    THE CLAIM, verbatim from that module: "eleven handlers declare a keyword-only
    ``transport`` on their ``dispatch``", "Two more accept one ONLY through a
    module-level declaration function of their own", "and four accept none at all, so
    those four always open under the INSTALLED PROCESS POLICY".

    WHY IT NEEDS A LOCK RATHER THAN A READER'S TRUST. The claim used to be that EVERY
    connection-opening handler declared the keyword, which was not true of three of
    them, and the correction was made in prose — where the next signature change can
    quietly falsify it again. The partition is not decoration: it decides whether
    ``options={"transport": …}`` reaches a handler or is projected away, and a handler
    the facade cannot reach opens under the installed process policy instead. That is
    fail-closed, so the risk is not an insecure connection; it is a caller believing a
    per-run policy applies where it does not.

    ASSERTED FROM SIGNATURES, never from a transcribed list, so the test cannot drift
    from the code the way the prose did. The three counts and the two-way membership
    are all checked, and the module-level setter table is checked to be exactly the
    handlers that have such a slot — including `acas007_gl_batch`, which is reachable
    BOTH ways and therefore belongs to the eleven as well as to the setter table.
    """
    facade = importlib.import_module("acas_posting.dal.facade")

    dal = importlib.import_module("acas_posting.dal")
    handler_names = sorted(
        found.name
        for found in pkgutil.iter_modules(dal.__path__)
        if found.name.startswith(("acas0", "acasirsub"))
    )
    assert len(handler_names) == 17, (
        f"the data-access layer publishes {len(handler_names)} handler modules; the "
        f"Agent Action Plan's entity-to-table spine names seventeen."
    )

    by_dispatch: list[str] = []
    without: list[str] = []
    for name in handler_names:
        module = importlib.import_module(f"acas_posting.dal.{name}")
        dispatch = getattr(module, "dispatch", None)
        assert dispatch is not None, f"{name} publishes no dispatch"
        keyword_only = {
            parameter.name
            for parameter in inspect.signature(dispatch).parameters.values()
            if parameter.kind is inspect.Parameter.KEYWORD_ONLY
        }
        (by_dispatch if "transport" in keyword_only else without).append(name)

    assert len(by_dispatch) == 11, (
        f"{len(by_dispatch)} handlers declare a keyword-only `transport` on their "
        f"dispatch: {by_dispatch}. acas_posting/dal/facade.py says ELEVEN, and the "
        f"count is the reachability of the options channel, not a description."
    )

    setters = {name for name, _ in facade._MODULE_LEVEL_POLICY_SETTERS}
    assert len(setters) == 3, (
        f"the module-level policy-setter table names {sorted(setters)}; facade.py's "
        f"comment describes three."
    )
    module_level_only = sorted(setters - set(by_dispatch))
    assert len(module_level_only) == 2, (
        f"{module_level_only} accept a policy ONLY through a module-level setter; "
        f"facade.py says TWO. A handler that gained a dispatch keyword should leave "
        f"this set, and one that lost its setter should leave the table."
    )

    neither = sorted(set(without) - setters)
    assert len(neither) == 4, (
        f"{neither} accept a transport policy by NEITHER route; facade.py says FOUR, "
        f"and each of them therefore opens under the installed process policy. That "
        f"is fail-closed, which is why it is acceptable - and it is only true while "
        f"nobody assumes the options channel reaches them."
    )

    # The three sets partition the seventeen exactly: no handler is in two of them and
    # none is in none of them.
    assert sorted(set(by_dispatch) | set(module_level_only) | set(neither)) == (
        handler_names
    )
    assert not set(module_level_only) & set(neither)
    assert not set(by_dispatch) & set(neither)


def test_the_canonical_isolated_oracle_name_is_the_harness_spelling() -> None:
    """The Python and shell halves must read ONE variable, and only that one.

    The defect was two spellings for one decision - the harness exported
    `ACAS_DB_ALLOW_PLAINTEXT` while this module also read `ACAS_DB_ISOLATED_ORACLE`,
    so a deployment could set the one nothing read and believe it had declared
    something. Reading the second name as an ALIAS closes the silent case; reading
    ONE NAME closes it and leaves nothing to explain, which is what the contract
    does now.
    """
    cli_args = importlib.import_module("acas_posting.cli.args")

    assert (
        cli_args.TRANSPORT_ALLOW_PLAINTEXT_VARIABLE
        == "ACAS_DB_ALLOW_PLAINTEXT"
    )

    #  Exactly one contract row resolves the grant, and it is that name.
    rows = [
        entry
        for entry in cli_args.TRANSPORT_CONTRACT
        if entry.field == "isolated_oracle"
    ]
    assert [entry.variable for entry in rows] == ["ACAS_DB_ALLOW_PLAINTEXT"]
    assert rows[0].alias_of is None


def test_the_superseded_spelling_is_not_read_at_all() -> None:
    """The second name declares NOTHING, and no row or attribute names it.

    A deployment that exports only the superseded spelling gets no grant - which is
    the fail-closed answer, because the value governs whether a credential and every
    posted figure may cross a network in the clear. Asserted three ways so the name
    cannot creep back as a row, as a constant, or as a reader.
    """
    cli_args = importlib.import_module("acas_posting.cli.args")

    superseded = "ACAS_DB_ISOLATED_ORACLE"

    from_superseded = cli_args.resolve_transport_policy({superseded: "1"})
    assert from_superseded.isolated_oracle is False

    both = cli_args.resolve_transport_policy(
        {"ACAS_DB_ALLOW_PLAINTEXT": "0", superseded: "1"}
    )
    assert both.isolated_oracle is False

    assert superseded not in {
        entry.variable for entry in cli_args.TRANSPORT_CONTRACT
    }
    assert superseded not in {
        entry.alias_of for entry in cli_args.TRANSPORT_CONTRACT
    }
    assert not [
        name
        for name in dir(cli_args)
        if getattr(cli_args, name, None) == superseded
    ]


def test_affirmative_spellings_match_the_shell_scripts_closed_set() -> None:
    """`false` must not mean yes, and a spelling in NEITHER set stops the run.

    THE SET IS CLOSED AT BOTH ENDS, and that is the whole of the rule. Reading an
    unrecognised value as "no" is the same defect in reverse: `false` read as yes,
    `maybe` read as no, and either way the operator who typed it is never told.
    `harness/seed.sh acas_plaintext_declared` matches `1|true|yes|on` and
    `''|0|false|no|off` case-insensitively and DIES on anything else; this module's
    `read_declared_flag` raises on anything else. `Y` is in neither set, in either
    half, so it is refused rather than guessed at.
    """
    cli_args = importlib.import_module("acas_posting.cli.args")

    assert cli_args.AFFIRMATIVE_SPELLINGS == frozenset({"1", "true", "yes", "on"})
    assert cli_args.NEGATIVE_SPELLINGS == frozenset({"", "0", "false", "no", "off"})

    #  Case and surrounding space are normalised, and nothing else is.
    for spelling in ("1", "true", "yes", "on", " TRUE ", "On", "YES"):
        assert cli_args.resolve_transport_policy(
            {"ACAS_DB_ALLOW_PLAINTEXT": spelling}
        ).isolated_oracle, spelling

    for spelling in ("", "  ", "0", "false", "no", "off", "FALSE"):
        assert not cli_args.resolve_transport_policy(
            {"ACAS_DB_ALLOW_PLAINTEXT": spelling}
        ).isolated_oracle, spelling

    for spelling in ("Y", "N", "maybe", "2", "true-ish"):
        with pytest.raises(cli_args.RdbmsParamError):
            cli_args.resolve_transport_policy(
                {"ACAS_DB_ALLOW_PLAINTEXT": spelling}
            )


def test_driver_deadlines_are_finite_and_agree_across_the_two_layers() -> None:
    """The DAL may not import the CLI, so the two default sets must be equal."""
    cli_args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")

    assert (
        cli_args.CONNECT_TIMEOUT_DEFAULT
        == connection.DEFAULT_CONNECT_TIMEOUT_SECONDS
    )
    assert (
        cli_args.READ_TIMEOUT_DEFAULT
        == connection.DEFAULT_READ_TIMEOUT_SECONDS
    )
    assert (
        cli_args.WRITE_TIMEOUT_DEFAULT
        == connection.DEFAULT_WRITE_TIMEOUT_SECONDS
    )

    deadlines = connection.ConnectionPolicy().driver_deadlines()
    assert set(deadlines) == {
        "connection_timeout",
        "read_timeout",
        "write_timeout",
    }
    assert all(isinstance(value, int) and value > 0 for value in deadlines.values())


def test_a_configured_deadline_reaches_the_policy() -> None:
    """A deployment that asks for a different budget gets it."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    resolved = cli_args.resolve_transport_policy(
        {
            "ACAS_DB_CONNECT_TIMEOUT": "5",
            "ACAS_DB_READ_TIMEOUT": "60",
            "ACAS_DB_WRITE_TIMEOUT": "90",
        }
    )
    assert resolved.connect_timeout_seconds == 5
    assert resolved.read_timeout_seconds == 60
    assert resolved.write_timeout_seconds == 90


@pytest.mark.parametrize("value", ["0", "-1", "abc", "86401", "1.5"])
def test_a_malformed_deadline_is_refused_rather_than_replaced(value: str) -> None:
    """An unbounded or unreadable budget is a refusal, not a silent default."""
    cli_args = importlib.import_module("acas_posting.cli.args")

    with pytest.raises(cli_args.RdbmsParamError):
        cli_args.resolve_transport_policy({"ACAS_DB_READ_TIMEOUT": value})


def test_a_command_line_declaration_cannot_annul_the_contract() -> None:
    """There is no command line to annul it WITH: the option surface is withdrawn.

    TWO REMEDIATIONS, AND THE TREE CARRIES THE STRONGER. Publishing
    `--db-tls-ca/-cert/-key` and `--db-allow-plaintext` and then returning
    `ConnectionPolicy(transport=stated)` the moment one was typed SILENTLY DROPPED the
    refusal-and-allowance knobs and the three driver deadlines. Merging the typed
    declaration over the contract field by field fixes that. WITHDRAWING the options
    fixes it and removes the surface as well: a program input and two refusal outcomes
    the compiled program has not got are themselves a behaviour change (rule R-3),
    and a certificate path on a command line is a process-listing leak
    [common/acas-get-params.cbl:L30].

    So the property this test defends is now stated positively: the contract is read
    ONCE, every field of it survives, and there is no argv path into the policy at
    all - asserted on the absent binder, the absent parameter and the absent option
    strings, because any one of those returning is the overlay coming back.
    """
    args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")

    assert not hasattr(args, "add_transport_security_arguments")
    assert not hasattr(args, "bind_transport_security")
    assert "namespace" not in inspect.signature(
        args.install_connection_policy
    ).parameters

    #  No route publishes a transport option either, which is what makes the
    #  paragraph above true of the shipped CLI rather than of one function.
    cli_dir = Path(args.__file__).resolve().parent
    for module in sorted(cli_dir.glob("*.py")):
        text = module.read_text(encoding="utf-8")
        for option in ("--db-tls-ca", "--db-tls-cert", "--db-tls-key"):
            assert f'"{option}"' not in text, f"{module.name} publishes {option}"

    try:
        policy = args.install_connection_policy(
            {
                "ACAS_DB_ALLOW_PLAINTEXT": "1",
                "ACAS_DB_REQUIRE_TLS": "1",
                "ACAS_DB_REQUIRE_DECLARED_CREDENTIALS": "1",
                "ACAS_DB_READ_TIMEOUT": "45",
            }
        )

        #  THE WHOLE CONTRACT SURVIVES: the transport material, both refusal knobs
        #  and the deadline. This is the assertion the overlay defect broke.
        assert policy.transport is not None
        assert policy.transport.isolated_oracle is True
        assert policy.require_encrypted_transport is True
        assert policy.require_declared_placeholder_credentials is True
        assert policy.read_timeout_seconds == 45
    finally:
        connection.reset_connection_policy()


def test_the_contract_alone_installs_the_same_transport_declaration() -> None:
    """The contract is the only source, and it is honoured on its own."""
    args = importlib.import_module("acas_posting.cli.args")
    connection = importlib.import_module("acas_posting.dal.connection")

    try:
        policy = args.install_connection_policy({"ACAS_DB_ALLOW_PLAINTEXT": "1"})
        assert policy.transport is not None
        assert policy.transport.isolated_oracle is True
        assert policy.require_encrypted_transport is False
    finally:
        connection.reset_connection_policy()


def test_bind_irs_route_publishes_the_snapshot_of_its_single_zz090_pass() -> None:
    """One bind, one key-1 load, one remap, and the snapshot comes back."""
    args = importlib.import_module("acas_posting.cli.args")

    parser = argparse.ArgumentParser()
    args.add_irs_linkage_arguments(parser)
    namespace = parser.parse_args(["--run-date", "21/09/2025"])

    binding = args.bind_irs_route(namespace, env=_FAKE_CONTRACT)

    assert isinstance(binding, args.IrsRouteBinding)
    assert isinstance(binding.linkage, args.IrsLinkage)
    #  No `menu_state`, so `zz090` is not performed at all - exactly as a caller
    #  that never reaches [irs/irs.cbl:L556] leaves it.
    assert binding.pre_dispatch_snapshot is None
    assert binding.linkage.irs_system_params.run_date == "21/09/25"
    assert binding.linkage.ws_system_record.system_data_block.run_date == 155127


def test_bind_irs_linkage_delegates_to_bind_irs_route() -> None:
    """Two entry points, ONE implementation, so they cannot drift."""
    args = importlib.import_module("acas_posting.cli.args")

    parser = argparse.ArgumentParser()
    args.add_irs_linkage_arguments(parser)
    namespace = parser.parse_args(["--run-date", "21/09/2025"])

    linkage = args.bind_irs_linkage(namespace, env=_FAKE_CONTRACT)
    route = args.bind_irs_route(namespace, env=_FAKE_CONTRACT)

    assert type(linkage) is type(route.linkage)
    assert linkage.irs_system_params.run_date == route.linkage.irs_system_params.run_date
    assert (
        linkage.ws_system_record.system_data_block.run_date
        == route.linkage.ws_system_record.system_data_block.run_date
    )


def test_load00_publishes_no_transport_parameter() -> None:
    """The unused keyword-only parameter must stay absent."""
    import inspect

    gl_post_cycle = importlib.import_module("acas_posting.cli.gl_post_cycle")

    parameters = inspect.signature(gl_post_cycle.load00).parameters
    assert "transport" not in parameters
    assert list(parameters) == [
        "linkage",
        "program",
        "program_id",
        "menu_state",
        "work_files",
    ]


# ---------------------------------------------------------------------------
# Cross-file references into the harness scripts
# ---------------------------------------------------------------------------

#: The FROZEN tree, verbatim from AAP 0.8.1 plus the maintainer's own documents. A
#: line number into any of these is permanently valid, because the file cannot
#: change, and is therefore the most precise reference available. Everything else in
#: the repository is written by this migration and moves.
_FROZEN_PREFIXES: tuple[str, ...] = (
    "common/",
    "copybooks/",
    "general/",
    "sales/",
    "purchase/",
    "irs/",
    "stock/",
    "mysql/",
    "etc/",
    "payroll/",
    "Basic-Code/",
    "ACAS-Manuals/",
    "home/",
    "presql2-package/",
)

#: Individual frozen files at the repository root.
_FROZEN_FILES: frozenset[str] = frozenset(
    {
        "README.TXT",
        "README",
        "README.SVN",
        "README.nightly",
        "Changelog",
        "comp-all.sh",
        "comp-all-noflags.sh",
    }
)

#: The harness files whose line numbers move whenever this project edits them, and
#: which are therefore referenced by symbol. `harness/scenario_stream.py` and
#: `harness/parity_stages.sh` are NOT listed: both are MODES of `harness/normalize.py`,
#: which is listed in its own right.
#: `harness/build_fixtures.sh` and `harness/make_fixtures.py` are likewise modes, of
#: `harness/seed.sh --build-fixtures` and `harness/dump_tables.py --make-fixtures`; both
#: owners are listed.
#: THERE IS NO `harness/run_parity.sh` AND NO TEN-STAGE DRIVER SCRIPT. The ten-stage
#: orchestration is implemented programmatically in `tests/conftest.py`, and the three
#: gates such a script would own live in the stages that own the state they protect - the
#: oracle-provenance gate and the seed pre-flight in `harness/reset_db.sh`, the cross-side
#: operations check in `harness/run_cobol_scenario.sh`. All three of those files are
#: listed here.
_EDITABLE_HARNESS_FILES: tuple[str, ...] = (
    "run_cobol_scenario.sh",
    "run_python_scenario.sh",
    "seed.sh",
    "reset_db.sh",
    "build_oracle.sh",
    "dump_tables.py",
    "normalize.py",
    "diff_states.py",
)

#: Where cross-file references are written: the scenario definitions, the four
#: migration documents and the test suites. Not the harness scripts themselves --
#: a script referring to its own neighbour by line is a separate matter and none
#: does.
_REFERENCE_SOURCES: tuple[str, ...] = (
    "harness/scenarios/*.yaml",
    "docs/migration/*.md",
    "tests/arithmetic/*.py",
    "tests/scenarios/*.py",
    "tests/determinism/*.py",
    "tests/*.py",
)

_LINE_LOCATOR = re.compile(
    r"harness/(" + "|".join(re.escape(name) for name in _EDITABLE_HARNESS_FILES)
    + r"):L\d+"
)

#: `[harness/<file> <symbol>]` -- the shape every converted reference takes. The
#: SQUARE BRACKETS are part of the pattern and must stay: without them this also
#: matches ordinary prose such as "harness/seed.sh reproduces the loader contract",
#: where the following word is English rather than a symbol name.
_SYMBOL_REFERENCE = re.compile(
    r"\[harness/(" + "|".join(re.escape(name) for name in _EDITABLE_HARNESS_FILES)
    + r")\s+([A-Za-z_][A-Za-z0-9_]*)\]"
)

#: The same idea for a `.py` module of this project, referenced either bracketed or
#: in backticks: `[acas_posting/cobol/usage.py byte_length]` and
#: `` `tests/conftest.py REPO_ROOT` ``. The delimiter is again what keeps prose out:
#: "acas_posting/cobol/usage.py states the rule" must not be read as a symbol.
_MODULE_SYMBOL_REFERENCE = re.compile(
    r"[\[`]((?:acas_posting|tests|harness)/[A-Za-z0-9_./\-]+\.py)"
    r"\s+([A-Za-z_][A-Za-z0-9_]*)[\]`]"
)

_SHELL_FUNCTION = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)")
_SHELL_VARIABLE = re.compile(
    r"^\s*(?:readonly\s+)?(?:declare\s+)?(?:-a\s+|-i\s+|-r\s+)?"
    r"([A-Z_][A-Z0-9_]*)="
)
_PYTHON_DEF = re.compile(r"^(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")
_PYTHON_CLASS = re.compile(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)")
_PYTHON_CONSTANT = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*(?::|=)")


def _reference_source_files() -> list[Path]:
    """Every file in which a cross-file reference may legitimately appear."""
    root = Path(__file__).resolve().parents[2]
    found: list[Path] = []
    for pattern in _REFERENCE_SOURCES:
        found.extend(sorted(root.glob(pattern)))
    return found


_PYTHON_METHOD = re.compile(r"^\s{4}(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)")


def _symbols_in(relative_path: str) -> frozenset[str]:
    """Return every symbol the file at `relative_path` defines.

    Shell functions, upper-case shell variables, Python defs, classes, module-level
    constants and four-space-indented methods -- the six shapes a reference can
    legitimately name. Deliberately a line scan rather than an `ast` parse: the shell
    files are half the corpus, and a reference is checked against what a reader of
    the file sees declared.

    Args:
        relative_path: repository-relative path, e.g. `harness/seed.sh`.

    Returns:
        The names that file declares, empty when the file does not exist.
    """
    path = Path(__file__).resolve().parents[2] / relative_path
    if not path.is_file():
        return frozenset()
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        for pattern in (
            _SHELL_FUNCTION,
            _SHELL_VARIABLE,
            _PYTHON_DEF,
            _PYTHON_CLASS,
            _PYTHON_CONSTANT,
            _PYTHON_METHOD,
        ):
            match = pattern.match(line)
            if match:
                names.add(match.group(1))
    return frozenset(names)


def _defined_symbols(harness_file: str) -> frozenset[str]:
    """Return every top-level symbol `harness/<harness_file>` defines.

    Args:
        harness_file: bare file name under `harness/`.

    Returns:
        The names defined at the top level of that file.
    """
    return _symbols_in(f"harness/{harness_file}")


#: `[harness/scenarios/<file>.yaml "SOME HEADING"]` -- the same idea for a file that
#: has no symbols. A scenario definition is prose under keys, so the durable handle
#: is a section heading, quoted verbatim. The heading may wrap across source lines,
#: so the match is taken over the whole file text rather than line by line.
_YAML_HEADING_REFERENCE = re.compile(
    r"\[harness/scenarios/([a-z_0-9]+\.yaml)\s*\n?\s*\"([^\"]{8,})\"\]"
)


#: `<some/path.ext>:L<n>` in any shape this repository writes.
_ANY_LINE_LOCATOR = re.compile(
    r"\b((?:[A-Za-z0-9_.\-]+/)*[A-Za-z0-9_.\-]+"
    r"\.(?:py|sh|yml|yaml|toml|json|md|cbl|cob|sql|scb|txt|conf))"
    r":L\d+"
)


def _is_frozen(path_text: str) -> bool:
    """True when `path_text` names a file the migration may not modify.

    Args:
        path_text: a repository-relative path as it appears inside a locator.

    Returns:
        Whether the path is under a frozen directory or is a frozen root file.
    """
    return path_text.startswith(_FROZEN_PREFIXES) or path_text in _FROZEN_FILES


def test_no_reference_names_a_line_in_a_file_this_migration_writes() -> None:
    """The general form of the rule, so the defect cannot come back somewhere new.

    A line number is a perfectly good reference into the FROZEN tree, where the file
    cannot change. Into a file this migration writes it is stale at the next edit --
    and the stale reference then reads as present evidence for whatever now sits at
    that line, which is how `period_end_totals.yaml` came to cite a `trap` statement
    as the operation/subsystem cross-check and how a locator into
    `acas_posting/dal/connection.py` came to be cited as where `autocommit` is set
    while pointing three paragraphs of docstring away from the assignment.

    Name a symbol, or quote a section heading for a file that has none. Both forms
    are then verified by the tests that follow.
    """
    offenders: list[str] = []
    for path in _reference_source_files():
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in _ANY_LINE_LOCATOR.finditer(line):
                if _is_frozen(match.group(1)):
                    continue
                offenders.append(f"{path.name}:{number}: {match.group(0)}")
    assert not offenders, (
        "these references name a line in a file this migration writes, so each will "
        "be stale at the next edit of that file. Name the function, class, variable "
        "or constant instead, or quote a section heading for a file with no "
        "symbols:\n  " + "\n  ".join(offenders)
    )


def test_every_scenario_heading_reference_resolves() -> None:
    """A quoted heading must appear, verbatim, in the definition it names."""
    root = Path(__file__).resolve().parents[2]
    unresolved: list[str] = []
    checked = 0
    for path in _reference_source_files():
        text = path.read_text(encoding="utf-8")
        for match in _YAML_HEADING_REFERENCE.finditer(text):
            scenario_file, heading = match.group(1), match.group(2)
            checked += 1
            target = root / "harness" / "scenarios" / scenario_file
            # The reference itself may be wrapped, so the heading is re-joined on
            # single spaces before the search, and the target is collapsed the same
            # way. Nothing else about either text is altered.
            wanted = " ".join(heading.split())
            haystack = " ".join(target.read_text(encoding="utf-8").split())
            if not target.is_file() or wanted not in haystack:
                unresolved.append(f"{path.name}: {scenario_file} has no {wanted!r}")
    assert checked, (
        "no `[harness/scenarios/<file>.yaml \"HEADING\"]` reference was found, so "
        "this test is asserting nothing."
    )
    assert not unresolved, (
        "these references quote a heading their scenario definition does not "
        "carry:\n  " + "\n  ".join(unresolved)
    )


def test_no_reference_names_a_harness_script_line_number() -> None:
    """A line number into an editable harness script is stale by construction.

    It moves with every edit of that script, and the moved reference then reads as
    present evidence for whatever now sits at that line -- which is how
    `period_end_totals.yaml` came to cite a `trap` statement as the operation and
    subsystem cross-check. Symbols are used instead.
    """
    offenders: list[str] = []
    for path in _reference_source_files():
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for match in _LINE_LOCATOR.finditer(line):
                offenders.append(f"{path.name}:{number}: {match.group(0)}")
    assert not offenders, (
        "these references name a line in a harness script this project edits, so "
        "they will be stale at the next edit of that script. Name the function, "
        "variable or constant instead:\n  " + "\n  ".join(offenders)
    )


def test_every_harness_symbol_reference_resolves() -> None:
    """A symbol reference is only better than a line number if it is checked.

    An unresolvable name is a louder failure than a moved line number, which is
    the point: renaming a function breaks the reference here rather than leaving
    the prose quietly describing something that no longer exists.
    """
    unresolved: list[str] = []
    checked = 0
    for path in _reference_source_files():
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            for match in _SYMBOL_REFERENCE.finditer(line):
                harness_file, symbol = match.group(1), match.group(2)
                checked += 1
                if symbol not in _defined_symbols(harness_file):
                    unresolved.append(
                        f"{path.name}:{number}: harness/{harness_file} "
                        f"defines no {symbol!r}"
                    )
    assert checked, (
        "no `harness/<file> <symbol>` reference was found at all, so this test is "
        "asserting nothing. The 129 symbol-named references should be here."
    )
    assert not unresolved, (
        "these cross-file references name a symbol their target does not "
        "define:\n  " + "\n  ".join(unresolved)
    )


#: `<number word> ... under|of `<directory>`` -- how the migration documents state an
#: inventory count. The word is checked against the tree, so a document cannot claim
#: fifteen files where sixteen exist. Three documents held three DIFFERENT numbers for
#: `tests/arithmetic/`.
_NUMBER_WORDS: dict[str, int] = {
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "twenty-one": 21,
    "twenty-two": 22,
    "twenty-eight": 28,
}

#: directory -> (glob, whether `__init__.py` is counted). A package directory is
#: quoted BOTH ways in the documents -- `acas_posting/programs/` as "thirteen
#: modules", counting the package marker, and `acas_posting/cobol/` as "the seven",
#: not counting it -- so both readings are accepted and only a number matching
#: NEITHER fails.
_INVENTORY_DIRECTORIES: dict[str, str] = {
    "tests/arithmetic": "test_*.py",
    "tests/scenarios": "test_*.py",
    "harness/scenarios": "*.yaml",
    "docs/migration": "*.md",
    "data_dictionary": "*.json",
    "acas_posting/programs": "*.py",
    "acas_posting/dal": "*.py",
    "acas_posting/cli": "*.py",
    "acas_posting/cobol": "*.py",
    "acas_posting/records": "*.py",
    "acas_posting/dictionary": "*.py",
}

#: A NUMBER, spelled or in digits. Digits are accepted because the README states two of
#: the three tier counts as digits in a table, and QA found the guard blind to exactly
#: those cells: a pattern that only reads words creates the impression of coverage while
#: half the counts in the document are unreadable to it.
_NUMBER_TOKEN = (
    r"(?:"
    + "|".join(sorted(_NUMBER_WORDS, key=len, reverse=True))
    + r"|\d{1,3})"
)

#: FORM 1 -- `<number> ... under|of|in `<directory>``, the prose form. `in` joins
#: `under` and `of` because "nineteen files in `tests/arithmetic/`" is the same claim
#: and was silently unguarded.
_INVENTORY_CLAIM = re.compile(
    r"\b(" + _NUMBER_TOKEN + r")\b"
    r"((?:\s+[a-z]+){0,4}?\s+(?:under|of|in)\s+)`([A-Za-z_0-9/.]+?)/?`"
)

#: TIER NAME -> the directory it counts. A tier caption names the tier, never the path,
#: so no directory-anchored pattern can see it -- which is how "**The arithmetic tier -
#: fifteen files**" stood three paragraphs from three correct statements of nineteen,
#: and how "**The scenario tier - eight files**" sat above a table of arithmetic files.
_TIER_DIRECTORIES: dict[str, str] = {
    "arithmetic": "tests/arithmetic",
    "scenario": "tests/scenarios",
    "determinism": "tests/determinism",
}

#: FORM 2 -- the tier-caption form: `<tier> tier -- <number> file(s)`, with an em dash,
#: an en dash or a hyphen between, and optional bold around either part.
#: Deliberately `file`/`files` ONLY. A tier is also quoted as "the scenario tier - 107
#: tests", which is a count of collected TESTS, not of files; comparing it to a
#: directory listing would fail on a true sentence, so this guard leaves test counts to
#: the run that produces them and asserts only what the tree can answer.
_TIER_CAPTION_CLAIM = re.compile(
    r"\b(arithmetic|scenario|determinism)\b\s+tier\**\s*[-\u2013\u2014]+\s*"
    r"\**(" + _NUMBER_TOKEN + r")\**\s+files?\b"
)

#: FORM 3 -- a markdown table row whose first cell is a backticked in-scope directory
#: and whose second cell is a bare count, which is how section 12's tier table states
#: all three. The row form carries no `of`/`under`/`in` at all. A trailing `/` or `/*`
#: is absorbed so `tests/arithmetic`, `tests/arithmetic/` and `tests/arithmetic/*` all
#: resolve to one directory key.
_INVENTORY_ROW_CLAIM = re.compile(
    r"^\|\s*`([A-Za-z_0-9/.]+?)(?:/\*|/)?`[^|]*\|\s*\**(" + _NUMBER_TOKEN + r")\**\s*\|",
    re.M,
)


def _inventory_documents() -> list[Path]:
    """The documents that state inventory counts."""
    root = Path(__file__).resolve().parents[2]
    return sorted(root.glob("docs/migration/*.md")) + sorted(
        root.glob("README-python-migration.md")
    )


def _inventory_claims(text: str, collapsed: str) -> list[tuple[str, str, str]]:
    """Every inventory claim in one document, as `(directory, number, form)`.

    Three forms, because the counts that drifted were stated in three different shapes
    and a guard that reads one shape reports coverage it does not have. `collapsed` is
    the whitespace-collapsed whole document, for the two forms that WRAP; `text` keeps
    its line structure, for the table-row form, which cannot wrap.
    """
    claims: list[tuple[str, str, str]] = []
    for match in _INVENTORY_CLAIM.finditer(collapsed):
        claims.append((match.group(3), match.group(1), "prose"))
    for match in _TIER_CAPTION_CLAIM.finditer(collapsed):
        claims.append((_TIER_DIRECTORIES[match.group(1)], match.group(2), "tier caption"))
    for match in _INVENTORY_ROW_CLAIM.finditer(text):
        claims.append((match.group(1), match.group(2), "table row"))
    return claims


def test_documented_inventory_counts_match_the_tree() -> None:
    """A stated count must be what the directory holds.

    The defect this guards is a document preserving the count it was authored with. The
    numbers are small and written as English words, which is exactly why nobody
    noticed three documents disagreeing about one directory. This reads the tree.
    """
    root = Path(__file__).resolve().parents[2]
    wrong: list[str] = []
    checked = 0
    forms: set[str] = set()
    for document in _inventory_documents():
        raw = document.read_text(encoding="utf-8")
        # Collapsed to one line, because a claim WRAPS: "the sixteen test\nfiles
        # under `tests/arithmetic/`" is one claim and a line-by-line scan would
        # silently skip it -- which is how a wrapped claim stayed wrong while the
        # unwrapped one beside it was corrected.
        collapsed = " ".join(raw.split())
        for directory, number, form in _inventory_claims(raw, collapsed):
            glob = _INVENTORY_DIRECTORIES.get(directory)
            if glob is None:
                continue
            checked += 1
            forms.add(form)
            present = list((root / directory).glob(glob))
            actual = len(present)
            without_marker = len(
                [path for path in present if path.name != "__init__.py"]
            )
            claimed = _NUMBER_WORDS.get(number)
            if claimed is None:
                claimed = int(number)
            if claimed not in (actual, without_marker):
                wrong.append(
                    f"{document.name}: claims {number} ({claimed}) "
                    f"for {directory}/ in a {form} claim, which holds {actual} "
                    f"({without_marker} excluding __init__.py)"
                )
    assert checked, (
        "no inventory claim was matched, so this test is asserting nothing. The "
        "documents state counts as English words or digits followed by `of`, `under` "
        "or `in` and a backtick-quoted directory, as a `<tier> tier - N files` "
        "caption, or as a markdown table row pairing the directory with a count."
    )
    # ALL THREE FORMS MUST BE EXERCISED, not merely available. A broadened pattern that
    # matches nothing is indistinguishable from the narrow one it replaced, and that is
    # precisely the false coverage QA found: the guard passed while five stale counts
    # sat in phrasings it could not see.
    assert forms == {"prose", "tier caption", "table row"}, (
        "the inventory guard did not exercise all three claim forms; it saw "
        f"{sorted(forms)}. A form that matches nothing gives the false coverage this "
        "test exists to prevent."
    )
    assert not wrong, (
        "these documented inventory counts do not match the checkout:\n  "
        + "\n  ".join(wrong)
    )


def test_every_module_symbol_reference_resolves() -> None:
    """The same guarantee for references into this project's own `.py` modules.

    These carried the same defect and one of them proved it: a locator cited as the
    place `autocommit` is set pointed at a docstring paragraph three screens away,
    and three references into sibling test modules pointed at a blank line, a closing
    parenthesis and an unrelated `for` statement.
    """
    unresolved: list[str] = []
    checked = 0
    for path in _reference_source_files():
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for match in _MODULE_SYMBOL_REFERENCE.finditer(line):
                module, symbol = match.group(1), match.group(2)
                checked += 1
                if symbol not in _symbols_in(module):
                    unresolved.append(
                        f"{path.name}:{number}: {module} defines no {symbol!r}"
                    )
    assert checked, (
        "no `<module>.py <symbol>` reference was found at all, so this test is "
        "asserting nothing."
    )
    assert not unresolved, (
        "these references name a symbol their module does not define:\n  "
        + "\n  ".join(unresolved)
    )


# ---------------------------------------------------------------------------
#  CR-02 - NO FUNCTION MAY READ A NAME NOTHING DEFINES
#
#  `tests/conftest.py`'s ten-stage helper referenced two names that existed only in
#  its CALLER's scope: `cache_key`, read on the success path of every run, and
#  `requested_operations`, read on the operation-mismatch branch. Python resolves an
#  unqualified name inside a function against the function's locals and then the
#  MODULE globals, never the caller's frame, so each read raised `NameError` - and it
#  did so AFTER an otherwise complete ten-stage protocol, so the crash landed on the
#  ordinary consumer of a successful parity run. The mismatch branch was worse: the
#  `NameError` replaced the harness-fault diagnosis with a second, unrelated failure.
#
#  Neither defect is visible to a test that never reaches the branch, and every
#  scenario module reaches the first one, which is precisely why this is a STATIC gate
#  rather than a runtime one. It costs nothing, needs no database, and it catches the
#  whole class rather than the two instances.
#
#  WHY `symtable` AND NOT A LINTER. The check has to run in this suite, on this
#  interpreter, with no tool outside `[project.optional-dependencies].test` - and
#  `symtable` is the compiler's own scope analysis, so it agrees with what the
#  interpreter will do by construction rather than by imitation. A name is reported
#  only when the compiler classified it as global AND the module binds no such name
#  AND it is not a builtin, which is exactly the condition that raises at run time.
_SCOPE_CHECKED_SOURCES: tuple[str, ...] = (
    "tests/conftest.py",
    "tests/arithmetic/*.py",
    "tests/scenarios/*.py",
    "tests/determinism/*.py",
    "harness/dump_tables.py",
    "harness/normalize.py",
    "harness/diff_states.py",
)

#: The names every module has without writing them down. The import system binds
#: these before the first statement runs, so a function reading one is reading a
#: real binding even though `symtable` sees no assignment for it.
_IMPLICIT_MODULE_NAMES: frozenset[str] = frozenset(
    {
        "__annotations__",
        "__builtins__",
        "__cached__",
        "__debug__",
        "__dict__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__path__",
        "__spec__",
    }
)


def _unresolved_global_reads(path: Path) -> list[str]:
    """Return every `<scope>: <name>` a function reads but nothing can bind.

    Args:
        path: The module to analyse.

    Returns:
        One entry per offending read, empty when the module is clean.
    """
    source = path.read_text(encoding="utf-8")
    table = symtable.symtable(source, str(path), "exec")
    module_names = set(table.get_identifiers())
    builtin_names = set(dir(builtins))
    offenders: list[str] = []

    def visit(scope: symtable.SymbolTable, trail: str) -> None:
        for child in scope.get_children():
            here = f"{trail}.{child.get_name()}" if trail else child.get_name()
            if child.get_type() == "function":
                for symbol in child.get_symbols():
                    name = symbol.get_name()
                    if (
                        symbol.is_global()
                        and not symbol.is_assigned()
                        and name not in module_names
                        and name not in builtin_names
                        and name not in _IMPLICIT_MODULE_NAMES
                    ):
                        offenders.append(f"{here}: {name}")
            visit(child, here)

    visit(table, "")
    return offenders


def test_no_function_reads_a_name_nothing_defines() -> None:
    """Every global read in the harness and test seam resolves to a binding.

    THE REGRESSION THIS CLOSES is `tests/conftest.py`'s
    `_run_scenario_parity_stages`, which read `cache_key` and `requested_operations`
    from its caller's scope. Both are now parameters. A future edit that moves a
    stage out of one function and into another without carrying its inputs across
    fails here instead of at the end of a ten-stage run.
    """
    root = Path(__file__).resolve().parents[2]
    files: list[Path] = []
    for pattern in _SCOPE_CHECKED_SOURCES:
        files.extend(sorted(root.glob(pattern)))
    assert files, (
        "no module was analysed at all, so this test is asserting nothing. "
        f"Patterns: {_SCOPE_CHECKED_SOURCES!r}"
    )

    offenders: list[str] = []
    for path in files:
        for entry in _unresolved_global_reads(path):
            offenders.append(f"{path.relative_to(root)}  {entry}")

    assert not offenders, (
        "these functions read a name that neither their own scope nor their "
        "module's binds, so the read raises `NameError` the moment the line "
        "executes:\n  " + "\n  ".join(offenders) + "\n\n"
        "  A name read inside a function resolves against that function's locals "
        "and then its MODULE globals - never against the frame that called it. If "
        "the value belongs to the caller, pass it as a parameter."
    )


# ---------------------------------------------------------------------------
#  THE ADMITTED-STATUS BAND IS DECLARED TWICE AND MUST AGREE
#
#  A status the Python runner admits as a DISPOSITION becomes evidence: the wrapper
#  exits 69, the protocol continues past stage 6 so the capture can
#  corroborate it, harness/dump_tables.py attests that capture as comparable, and
#  tests/conftest.py bands it as a behavioural difference rather than a broken rig.
#  Every one of those steps is downstream of one question - "is this status a
#  disposition at all" - and that question is answered by a table in the shell runner
#  and a table in the test seam. The two are necessarily separate: a shell script
#  cannot import a Python `Final`, and tests/conftest.py must not be imported at
#  module scope by this tier. So they are held together here.
#
#  THE AUTHORITY IS THE FROZEN SOURCE, and it is short: `move 5 to ws-term-code`
#  [general/gl070.cbl:L289], `move 8 to ws-term-code` [sales/sl055.cbl:L344] and
#  [purchase/pl055.cbl:L286]. Three sites, three codes, four operations that set none.
_CONFTEXT_TERM_CODES_NAME = "TERM_CODES"
_SHELL_TERM_CODE_MAP = re.compile(
    r"^\s*'(?P<operation>[a-z_]+)\|(?P<codes>[0-9 ]*)'\s*$"
)


def _declared_term_codes_from_conftest() -> dict[str, tuple[int, ...]]:
    """Parse `TERM_CODES` out of `tests/conftest.py` without importing it.

    Returns:
        The operation-to-term-codes mapping the test seam declares.
    """
    root = Path(__file__).resolve().parents[2]
    tree = ast.parse((root / "tests" / "conftest.py").read_text(encoding="utf-8"))
    for node in tree.body:
        target = None
        if isinstance(node, ast.AnnAssign):
            target = node.target
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        if (
            isinstance(target, ast.Name)
            and target.id == _CONFTEXT_TERM_CODES_NAME
            and node.value is not None
        ):
            return {
                str(ast.literal_eval(key)): tuple(ast.literal_eval(value))
                for key, value in zip(node.value.keys, node.value.values)
            }
    raise AssertionError(
        f"tests/conftest.py declares no module-level {_CONFTEXT_TERM_CODES_NAME}"
    )


def _declared_term_codes_from_runner() -> dict[str, tuple[int, ...]]:
    """Parse `ACAS_PY_TERM_CODE_MAP` out of the Python runner.

    Returns:
        The operation-to-term-codes mapping the runner declares.
    """
    root = Path(__file__).resolve().parents[2]
    lines = (
        (root / "harness" / "run_python_scenario.sh")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    try:
        start = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("readonly -a ACAS_PY_TERM_CODE_MAP=(")
        )
    except StopIteration as absent:  # pragma: no cover - asserted below
        raise AssertionError(
            "harness/run_python_scenario.sh declares no ACAS_PY_TERM_CODE_MAP"
        ) from absent
    declared: dict[str, tuple[int, ...]] = {}
    for line in lines[start + 1 :]:
        if line.strip() == ")":
            break
        match = _SHELL_TERM_CODE_MAP.match(line)
        assert match, f"unreadable ACAS_PY_TERM_CODE_MAP entry: {line!r}"
        declared[match.group("operation")] = tuple(
            int(code) for code in match.group("codes").split()
        )
    return declared


def test_term_codes_match_the_runner_table() -> None:
    """The runner and the test seam admit exactly the same statuses.

    A code in one table and not the other is the drift this lock exists for: an
    operation the runner admits but the seam bands as a fault reports a real
    behavioural difference as a broken rig, and an operation the seam admits but the
    runner refuses can never reach it at all.
    """
    from_conftest = _declared_term_codes_from_conftest()
    from_runner = _declared_term_codes_from_runner()

    assert from_runner, "the runner's term-code table parsed as empty"
    assert set(from_runner) == set(from_conftest), (
        "the two tables name different operations:\n"
        f"  harness/run_python_scenario.sh: {sorted(from_runner)}\n"
        f"  tests/conftest.py            : {sorted(from_conftest)}"
    )
    disagreements = {
        operation: (from_runner[operation], from_conftest[operation])
        for operation in sorted(from_runner)
        if tuple(sorted(from_runner[operation]))
        != tuple(sorted(from_conftest[operation]))
    }
    assert not disagreements, (
        "these operations admit different statuses on the two sides "
        "(runner, conftest):\n  "
        + "\n  ".join(f"{name}: {pair}" for name, pair in disagreements.items())
    )


def test_only_three_term_codes_exist_and_they_are_the_frozen_ones() -> None:
    """The whole admitted set is `{5, 8}`, held by three frozen `MOVE` statements.

    Stated as its own assertion so that ADDING a term code is a deliberate act with a
    frozen citation behind it, rather than a table entry nobody reviews. `gl070` sets
    5; `sl055` and `pl055` each set 8; the other four operations set none.
    """
    from_runner = _declared_term_codes_from_runner()
    assert from_runner["gl_post_cycle"] == (5,)
    assert from_runner["sl_invoice_post"] == (8,)
    assert from_runner["pl_order_post"] == (8,)
    for operation in (
        "gl_end_of_cycle",
        "sl_cash_post",
        "pl_payment_post",
        "irs_post",
    ):
        assert from_runner[operation] == (), (
            f"{operation} declares a term code. No frozen program on that route sets "
            f"one, so zero is its only semantic status; admitting another would let a "
            f"fault be attested as a measured difference."
        )
    everything = {code for codes in from_runner.values() for code in codes}
    assert everything == {5, 8}, (
        f"the admitted non-zero set is {sorted(everything)} and the frozen cycle sets "
        f"only 5 and 8 -- [general/gl070.cbl:L289], [sales/sl055.cbl:L344], "
        f"[purchase/pl055.cbl:L286]."
    )


# ---------------------------------------------------------------------------
#  ONE DUPLICATE-REJECTING SCENARIO PARSER, AND NO OTHER
#
#  `yaml.safe_load` applies last-one-wins to a repeated mapping key, silently. A
#  scenario definition carries the destructive answers (`irs_clear_postings`,
#  `gl080_proceed`, `disk_change_option`), the three-state fan-out switch that decides
#  which tables a run touches, the `affected_tables` list the runners assert against
#  and the `expected_status` that makes a term code a PASS. A shadowed key therefore
#  means one consumer reads the value the file appears to state and another reads a
#  different one, and an empty diff drawn across that pair measures nothing.
#
#  Eight call sites parsed definitions that way. All of them now go through
#  `load_scenario_yaml` in `harness/normalize.py`, and these tests assert both halves:
#  the loader rejects a duplicate, and no consumer has quietly gone back to
#  `yaml.safe_load`.
#
#  `harness/normalize.py` is NOT listed: it is the OWNER of the loader, not a consumer
#  of it, and the flat record stream both runners read - once
#  `harness/scenario_stream.py`, a consumer in its own right - is now a mode of that same
#  file, so it reads the loader by calling it directly.
#  `harness/make_fixtures.py` is likewise absent: it is now the `--make-fixtures` mode of
#  `harness/dump_tables.py`, which is listed, and it reaches the loader
#  through that module's own by-path resolver rather than a second import of its own.
#  There is NO `harness/run_parity.sh` and so no eighth consumer: the ten stages such a
#  script would drive are driven by `tests/conftest.py`, which is listed and which reads a
#  definition through the same loader.
_SCENARIO_YAML_CONSUMERS: tuple[str, ...] = (
    "harness/seed.sh",
    "harness/dump_tables.py",
    "harness/diff_states.py",
    "tests/conftest.py",
)


def _scenario_yaml_module():
    """Load the module that owns the shared scenario parser, by explicit path (rule R-1).

    It is `harness/normalize.py`, and NOT `harness/scenario_yaml.py`, which the Agent
    Action Plan section 0.3.1 harness inventory does not name.

    REGISTERED IN `sys.modules` BEFORE EXECUTION, and removed again if execution fails.
    Not optional: the module declares `@dataclass(frozen=True, slots=True)` records, and
    `slots=True` rebuilds each class, which makes `dataclasses` resolve the defining
    module by name - so an unregistered module fails with an `AttributeError` raised from
    inside the standard library, naming neither this call nor the real cause.

    Returns:
        The executed module.
    """
    root = Path(__file__).resolve().parents[2]
    path = root / "harness" / "normalize.py"
    assert path.is_file(), f"the shared scenario parser is absent: {path}"
    name = "acas_scenario_parser_probe"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def test_the_shared_loader_rejects_a_duplicate_key() -> None:
    """A repeated mapping key is a parse failure naming the key.

    The DISCRIMINATING half of this pair: a loader that merely subclassed
    `SafeLoader` without overriding `construct_mapping` would pass every other
    assertion here and still silently drop the shadowed value.
    """
    yaml = pytest.importorskip("yaml")
    module = _scenario_yaml_module()

    good = module.load_scenario_yaml("irs_instead: ' '\nexpected_status:\n  - 0\n")
    assert good == {"irs_instead": " ", "expected_status": [0]}

    with pytest.raises(yaml.YAMLError) as caught:
        module.load_scenario_yaml("irs_clear_postings: 'N'\nirs_clear_postings: 'Y'\n")
    assert "DUPLICATE KEY" in str(caught.value)
    assert "irs_clear_postings" in str(caught.value)

    # A duplicate NESTED inside a mapping is refused too, since the destructive
    # answers and the seed records both live under nested keys.
    with pytest.raises(yaml.YAMLError):
        module.load_scenario_yaml("seed_records:\n  batch.dat: [1]\n  batch.dat: [2]\n")

    # And it is still a SAFE loader: an arbitrary Python tag must not construct.
    with pytest.raises(yaml.YAMLError):
        module.load_scenario_yaml("!!python/object/apply:os.system ['true']\n")


def test_every_committed_scenario_parses_within_the_budgets() -> None:
    """The budgets admit every committed definition unchanged.

    Stated FIRST and separately from the refusal test, because this is the half that
    would make the hardening a regression. A budget derived from anything other than the
    measured maxima could reject a real scenario, and the failure would surface as a
    parity run that cannot start rather than as an obviously wrong limit.
    """
    root = Path(__file__).resolve().parents[2]
    module = _scenario_yaml_module()

    definitions = sorted((root / "harness" / "scenarios").glob("*.yaml"))
    assert definitions, "no scenario definition was found; this test would be vacuous"

    widest = 0
    for path in definitions:
        text = path.read_text(encoding="utf-8")
        widest = max(widest, len(text.encode("utf-8")))
        parsed = module.load_scenario_yaml(text)
        assert isinstance(parsed, dict) and parsed, (
            f"{path.name} did not parse to a non-empty mapping under the parse "
            "budgets, so a budget is rejecting a committed definition."
        )

    # Headroom, asserted rather than assumed: a budget that the committed set already
    # sits near is one edit away from rejecting a real file.
    assert widest * 4 <= module.MAX_DOCUMENT_BYTES, (
        f"the largest committed definition is {widest} bytes against a budget of "
        f"{module.MAX_DOCUMENT_BYTES}, which leaves under 4x headroom. Raise the "
        "budget rather than trimming a scenario."
    )


def test_the_shared_loader_refuses_an_over_budget_document() -> None:
    """Each parse budget refuses what it exists for, and an alias is refused outright.

    The DISCRIMINATING half: constants alone prove nothing, since a limit that is never
    consulted reads exactly like one that is. Every budget is driven past its bound here
    and the alias case is a real multiplicative-expansion document, not a token one.
    """
    yaml = pytest.importorskip("yaml")
    module = _scenario_yaml_module()

    # 1. Size, checked BEFORE the parser sees the text.
    oversized = "a: " + "x" * (module.MAX_DOCUMENT_BYTES + 1)
    with pytest.raises(module.ScenarioBudgetError) as size_error:
        module.load_scenario_yaml(oversized)
    assert "parse budget" in str(size_error.value)

    # 2. An alias, which is the multiplicative-expansion class. Refused, not counted.
    laughs = (
        'a: &anchor ["x","x","x","x","x","x","x","x","x"]\n'
        "b: [*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor]\n"
        "c: [*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor,*anchor]\n"
    )
    with pytest.raises(module.ScenarioBudgetError) as alias_error:
        module.load_scenario_yaml(laughs)
    assert "ALIAS" in str(alias_error.value)

    # 3. Depth.
    deep = (
        "a:\n"
        + "".join("  " * level + "k:\n" for level in range(1, module.MAX_DEPTH + 4))
        + "  " * (module.MAX_DEPTH + 4)
        + "v"
    )
    with pytest.raises(module.ScenarioBudgetError) as depth_error:
        module.load_scenario_yaml(deep)
    assert "nests deeper" in str(depth_error.value)

    # 4. Node count.
    wide = "root: [" + ",".join(str(n) for n in range(module.MAX_NODES + 10)) + "]"
    with pytest.raises(module.ScenarioBudgetError) as node_error:
        module.load_scenario_yaml(wide)
    assert "nodes" in str(node_error.value)

    # Every budget rejection is a `yaml.YAMLError`, so the eight consumers -- all of
    # which already handle that -- report one with no change of their own.
    assert issubclass(module.ScenarioBudgetError, yaml.YAMLError)


def test_the_dictionary_reader_bounds_what_it_reads() -> None:
    """The dictionary read is bounded in size and depth, and still reads the artifact.

    Both halves in one test because they are one contract: the committed dictionary must
    load exactly as before, and a document that is oversized, deeper than the budget, or
    deep enough to exhaust the interpreter's own recursion limit must be refused as a
    named `DictionaryParseError` rather than crashing the reader.
    """
    import json
    import tempfile

    loader = importlib.import_module("acas_posting.dictionary.loader")

    # The real artifact, unchanged.
    document = loader.load_dictionary()
    assert document.entries, "the committed dictionary no longer loads"

    root = Path(__file__).resolve().parents[2]
    artifact = root / "data_dictionary" / "acas_posting_dictionary.json"
    measured = artifact.stat().st_size
    assert measured * 4 <= loader._MAX_DOCUMENT_BYTES, (
        f"the committed dictionary is {measured} bytes against a read budget of "
        f"{loader._MAX_DOCUMENT_BYTES}, which leaves under 4x headroom."
    )

    # The depth helper does not recurse, so it can bound a document too deep to walk
    # recursively. Asserted directly, since that is the property that makes it usable.
    assert not loader._document_depth_exceeds(json.loads(artifact.read_text()), 64)
    assert loader._document_depth_exceeds(json.loads("[" * 200 + "]" * 200), 64)

    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)

        oversized = scratch / "oversized.json"
        oversized.write_bytes(
            b'{"x":"' + b"a" * (loader._MAX_DOCUMENT_BYTES + 16) + b'"}'
        )
        with pytest.raises(loader.DictionaryParseError) as size_error:
            loader.load_dictionary(oversized)
        assert "read budget" in str(size_error.value)

        # Deeper than the budget, but shallow enough that `json.loads` itself succeeds --
        # so this exercises the post-parse bound rather than the recursion guard.
        over_depth = scratch / "deep.json"
        over_depth.write_text('{"a":' * 100 + "1" + "}" * 100, encoding="utf-8")
        with pytest.raises(loader.DictionaryParseError) as depth_error:
            loader.load_dictionary(over_depth)
        assert "nests deeper" in str(depth_error.value)

        # Deep enough that the JSON scanner exhausts the recursion limit. Without the
        # guard this leaves the reader as a bare RecursionError.
        recursive = scratch / "recursive.json"
        recursive.write_text("[" * 100_000 + "]" * 100_000, encoding="utf-8")
        with pytest.raises(loader.DictionaryParseError) as recursion_error:
            loader.load_dictionary(recursive)
        assert "too deeply" in str(recursion_error.value)


def test_the_dictionary_reader_follows_no_symbolic_link() -> None:
    """An explicit artifact path is opened link by link, and a link is REFUSED.

    The guarantee the loader states has to be the guarantee it enforces. It used to pass
    an explicit path through `Path.resolve()` before the `O_NOFOLLOW` open, which follows
    every link in the path and leaves that open nothing to refuse - so a caller-supplied
    link, or a path through a linked directory, loaded an artifact from somewhere else
    under a name that looked committed. Four properties are asserted together because
    they are one contract: the ordinary paths still work, a linked FILE is refused, a
    linked DIRECTORY component is refused, and a component that is merely not a
    directory is not mislabelled as a link.

    Infrastructure-free: a temporary directory and the committed artifact's own bytes.
    """
    import tempfile

    loader = importlib.import_module("acas_posting.dictionary.loader")

    root = Path(__file__).resolve().parents[2]
    artifact = root / "data_dictionary" / "acas_posting_dictionary.json"
    payload = artifact.read_bytes()

    #  The default lookup is unaffected: it resolves the one candidate in
    #  DATA_DICTIONARY_SEARCH_PATH, the committed repository sibling.
    assert loader.load_dictionary().entries, "the committed dictionary no longer loads"

    with tempfile.TemporaryDirectory() as directory:
        scratch = Path(directory)

        plain = scratch / "plain.json"
        plain.write_bytes(payload)
        assert loader.load_dictionary(plain).entries, "a plain explicit path must load"

        #  An explicit path is made absolute rather than resolved, so a relative one
        #  still names the same file.
        assert loader._absolute_document_path(plain).is_absolute()

        linked_file = scratch / "linked.json"
        linked_file.symlink_to(plain)
        with pytest.raises(loader.DictionaryNotFoundError) as file_link:
            loader.load_dictionary(linked_file)
        assert "SYMBOLIC LINK" in str(file_link.value)

        real_directory = scratch / "real"
        real_directory.mkdir()
        (real_directory / "held.json").write_bytes(payload)
        linked_directory = scratch / "linked"
        linked_directory.symlink_to(real_directory, target_is_directory=True)
        with pytest.raises(loader.DictionaryNotFoundError) as directory_link:
            loader.load_dictionary(linked_directory / "held.json")
        assert "SYMBOLIC LINK" in str(directory_link.value)

        #  `..` is walked rather than collapsed, and through real directories it still
        #  arrives: refusing links must not refuse ordinary paths.
        assert loader.load_dictionary(real_directory / ".." / "plain.json").entries

        #  A component that is an ordinary file reports the same ENOTDIR the platform
        #  reports for a linked directory, and must NOT be described as a link.
        with pytest.raises(loader.DictionaryNotFoundError) as not_a_directory:
            loader.load_dictionary(plain / "under-a-file.json")
        assert "SYMBOLIC LINK" not in str(not_a_directory.value)


def test_no_artifact_recommends_an_unhashed_install() -> None:
    """Install guidance names the hash-verified route, never a bare `pip install`.

    A `pip install <name>==<version>` in remediation text teaches the reader to fetch an
    unverified artifact, which is exactly the route the rest of this project refuses. The
    editable routes are permitted where they are labelled as development conveniences,
    so what is banned is an unqualified install of a PINNED DISTRIBUTION.
    """
    root = Path(__file__).resolve().parents[2]
    checked = (
        "pyproject.toml",
        "requirements.txt",
        "README-python-migration.md",
        "harness/run_cobol_scenario.sh",
        "harness/Dockerfile.gnucobol",
    )

    # `pip install name==version` with no --require-hashes on the same line.
    unhashed = re.compile(r"pip install(?![^\n]*--require-hashes)[^\n]*[A-Za-z0-9_.-]+==")

    offenders: list[str] = []
    for relative in checked:
        path = root / relative
        assert path.is_file(), f"a checked artifact is absent: {path}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if unhashed.search(line):
                offenders.append(f"{relative}:{number}: {line.strip()[:96]}")

    assert not offenders, (
        "these lines recommend installing a pinned distribution without hash "
        "verification, which is the defect:\n  " + "\n  ".join(offenders) + "\n"
        "  Point at `pip install --require-hashes -r requirements.txt` instead."
    )


def test_every_scenario_yaml_consumer_uses_the_shared_loader() -> None:
    """No consumer calls `yaml.safe_load` on a scenario definition.

    Read as TEXT rather than by import, because three of the seven consumers are shell
    scripts whose parsing happens inside an embedded Python heredoc, and one is
    `tests/conftest.py`, which this tier must not import at module scope.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    missing: list[str] = []
    for relative in _SCENARIO_YAML_CONSUMERS:
        path = root / relative
        assert path.is_file(), f"a declared consumer is absent: {path}"
        text = path.read_text(encoding="utf-8")
        if "load_scenario_yaml" not in text:
            missing.append(relative)
        if relative.endswith(".py"):
            # AST rather than text, so that PROSE naming the defect - a docstring
            # explaining why the shared loader exists - is not itself reported as the
            # defect. Every real use is an attribute access, whether called directly
            # or bound to a name first, so walking Attribute nodes catches both.
            for node in ast.walk(ast.parse(text, filename=str(path))):
                if (
                    isinstance(node, ast.Attribute)
                    and node.attr in ("safe_load", "safe_load_all")
                    and isinstance(node.value, ast.Name)
                    and node.value.id == "yaml"
                ):
                    offenders.append(f"{relative}:{node.lineno}: yaml.{node.attr}")
            continue
        # A shell script has no docstring, and its Python lives in a heredoc the shell
        # never parses, so a text scan is both sufficient and the only option.
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "yaml.safe_load" in line:
                offenders.append(f"{relative}:{number}: {stripped}")

    assert not missing, (
        "these scenario-definition consumers do not reference the shared "
        "duplicate-rejecting loader at all:\n  " + "\n  ".join(missing)
    )
    assert not offenders, (
        "these lines call `yaml.safe_load`, whose last-one-wins on a duplicate key "
        "is the defect:\n  " + "\n  ".join(offenders) + "\n\n"
        "  Parse scenario definitions through harness/normalize.py's "
        "`load_scenario_yaml` instead."
    )


# ---------------------------------------------------------------------------
#  SECOND HALF - A CONSUMER MUST RESOLVE THE SHARED PARSER BY ITSELF
#
#  Wiring every consumer to the shared loader removes the last-one-wins defect and opens
#  a quieter one. The loader's owner - `harness/normalize.py`, not
#  `harness/scenario_yaml.py` - is a SIBLING FILE, not an installed package, so a bare
#  `import` of it resolves only when something has already put
#  `harness/` on `sys.path` - true when the consumer runs as a script from that
#  directory, false when a test loads it by path. The import was therefore
#  ORDER-DEPENDENT, and `diff_states.py` reported the failure as "PyYAML is not
#  importable", which is a different fault with a different remedy, so the refusal that
#  should have followed was never produced.
#
#  What that cost, measured: `pytest tests/scenarios/` on its own failed TWELVE tests
#  while the whole suite passed, because in the whole suite an earlier module both
#  inserted the path and left the parser in `sys.modules` for the bare import to find
#  in cache. A green full suite was therefore not evidence, and these two tests
#  exist so that it is: the first refuses the pattern statically, the second reproduces
#  the exact masking conditions - no `harness/` on the path AND no cached module - and
#  requires a real scenario read to still succeed.
_HARNESS_SIBLING_SELF_RESOLVERS: tuple[str, ...] = (
    "diff_states",
    "dump_tables",
)


def _harness_module_names(root: Path) -> frozenset[str]:
    """Every module name that is resolvable as a `harness/` sibling.

    Args:
        root: The repository root.

    Returns:
        The importable stems of the harness modules.
    """
    return frozenset(path.stem for path in (root / "harness").glob("*.py"))


def test_no_harness_module_resolves_a_sibling_by_name_unguarded() -> None:
    """A by-name sibling import must be guarded by the module's own path insert.

    Two shapes are acceptable and one is not. Resolving the sibling from
    `Path(__file__)` is acceptable and mutates nothing. Importing it by name after
    inserting the module's own directory on `sys.path` is acceptable because the
    guarantee is self-contained. Importing it by name with neither is the
    order-dependent defect, and it passes for as long as some other module happens to
    run first.
    """
    root = Path(__file__).resolve().parents[2]
    siblings = _harness_module_names(root)
    assert {"normalize", "diff_states", "dump_tables"} <= siblings, (
        "the harness module inventory is not what this test was written against; "
        f"found {sorted(siblings)}"
    )

    unguarded: list[str] = []
    for path in sorted((root / "harness").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        # A guard is a `sys.path` insert derived from THIS module's own location.
        # `__file__` on the same statement is what makes it self-contained; an insert
        # of some other directory would not be.
        guards_itself = any(
            "sys.path.insert" in line and "__file__" in line
            for line in text.splitlines()
        )
        for node in ast.walk(ast.parse(text, filename=str(path))):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                imported = [node.module.split(".")[0]]
            for name in imported:
                if name in siblings and name != path.stem and not guards_itself:
                    unguarded.append(
                        f"harness/{path.name}:{node.lineno}: import {name}"
                    )

    assert not unguarded, (
        "these imports resolve a `harness/` sibling BY NAME without the importing "
        "module guaranteeing its own `sys.path`, so whether they resolve depends on "
        "what ran first:\n  " + "\n  ".join(unguarded) + "\n\n"
        "  Resolve the sibling from `Path(__file__).resolve().parent` instead, as "
        "harness/diff_states.py and harness/dump_tables.py do, or insert this "
        "module's own directory on `sys.path` before the import."
    )


@pytest.mark.parametrize("module_name", _HARNESS_SIBLING_SELF_RESOLVERS)
def test_a_scenario_reads_with_harness_off_the_path_and_out_of_cache(
    module_name: str,
) -> None:
    """The DISCRIMINATING half: reproduce both masking conditions, then read.

    The static test above cannot see a resolution that succeeds from the
    `sys.modules` cache, and cache is half of why this hid: a bare `import
    normalize` finds an already-imported module even with nothing on the path. So
    this test removes `harness/` from `sys.path` AND evicts every cached spelling of
    the parser, which is the state `pytest tests/scenarios/` runs in, and then requires
    a real scenario definition to still parse.

    Args:
        module_name: The harness module under test.
    """
    pytest.importorskip("yaml")
    root = Path(__file__).resolve().parents[2]
    harness = (root / "harness").resolve()
    scenario = harness / "scenarios" / "clean_batch_gl.yaml"
    assert scenario.is_file(), f"the scenario definition is absent: {scenario}"

    saved_path = list(sys.path)
    #  EVERY CACHED SPELLING OF THE PARSER'S OWNER, matched on a whole underscore-
    #  separated segment so that `normalize`, `_acas_harness_normalize` and
    #  `acas_harness_normalize_scenario_parser` are all evicted while an unrelated
    #  module whose name merely contains the letters is not.
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if "normalize" in name.split("_")
    }
    try:
        kept: list[str] = []
        for entry in sys.path:
            try:
                same = Path(entry or ".").resolve() == harness
            except OSError:  # pragma: no cover - unresolvable entry
                same = False
            if not same:
                kept.append(entry)
        sys.path[:] = kept
        for name in saved_modules:
            sys.modules.pop(name, None)

        probe = f"acas_sibling_probe_{module_name}"
        spec = importlib.util.spec_from_file_location(
            probe, harness / f"{module_name}.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[probe] = module
        try:
            spec.loader.exec_module(module)
            tables = module.scenario_tables(scenario)
        finally:
            sys.modules.pop(probe, None)
    finally:
        sys.path[:] = saved_path
        sys.modules.update(saved_modules)

    assert tables, (
        f"harness/{module_name}.py read no tables from {scenario.name} with "
        f"harness/ off sys.path. Before this was fixed the refusal blamed PyYAML, "
        f"which is why the real cause went unnoticed."
    )
    assert "GLBATCH-REC" in tables, (
        f"harness/{module_name}.py parsed {scenario.name} but did not return its "
        f"declared tables; got {tables}"
    )


# ---------------------------------------------------------------------------
#  EVERY KEYSTROKE A SCENARIO SUPPLIES IS ESCAPED AT THE PLAN BOUNDARY
#
#  The pty driver's `decode_send` expands `\r`, `\n`, `\e`, `\t` and `\\` anywhere in a
#  plan row's send field. That is correct for the terminator the runner appends and
#  wrong for the scenario value it is appended to: a backslash in scenario text would
#  be read as the start of a control sequence, so `run_date_text: 01\r02\r2025` would
#  be typed at the compiled program as three ENTER-terminated fields.
#
#  The parity consequence is the reason this is locked. The migrated leg receives
#  scenario values as argv - no escape layer - so a value the oracle leg reinterpreted
#  and the migrated leg took literally means the two legs were driven with DIFFERENT
#  logical inputs, and the diff measures the escape layer rather than the accounting.
#
#  Every send field that interpolates anything must therefore pass it through
#  `acas_plan_escape_data`. Asserted statically, because the validation that currently
#  keeps these values backslash-free sits hundreds of lines from the send site.
_PLAN_SEND_ARGUMENT = re.compile(r'"\$\{?ACAS_[A-Za-z0-9_]+\}?\\\\[rnet]"')


def test_every_scenario_supplied_keystroke_is_escaped() -> None:
    """No plan send field interpolates a variable without the escaping helper."""
    root = Path(__file__).resolve().parents[2]
    path = root / "harness" / "run_cobol_scenario.sh"
    text = path.read_text(encoding="utf-8")

    assert "acas_plan_escape_data()" in text, (
        "harness/run_cobol_scenario.sh no longer defines acas_plan_escape_data, the "
        "boundary between trusted plan controls and untrusted scenario data."
    )

    raw: list[str] = []
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if _PLAN_SEND_ARGUMENT.search(line):
            raw.append(f"{path.name}:{number}: {stripped}")

    assert not raw, (
        "these plan send fields interpolate a variable directly, so a backslash in "
        "the value would be expanded by decode_send into a control sequence and the "
        "two parity legs would receive different bytes:\n  "
        + "\n  ".join(raw)
        + '\n\n  Wrap the value: "$(acas_plan_escape_data "$VAR")\\\\r"'
    )

    # And the escaping is actually REACHED - at least once per scenario-supplied
    # keystroke this runner types. A helper defined and never called would satisfy
    # every assertion above.
    assert text.count('acas_plan_escape_data "') >= 4, (
        "acas_plan_escape_data is defined but reaches fewer send sites than the "
        "runner has scenario-supplied keystrokes (date text, two payment "
        "confirmations, the IRS clear answer)."
    )


def test_the_escape_boundary_round_trips_every_byte() -> None:
    """`acas_plan_escape_data` then `decode_send` is the identity on the data.

    The DISCRIMINATING half: it reimplements both halves of the boundary from the
    shell and the driver source respectively and asserts the composition returns the
    input unchanged, with the appended terminator as the ONLY control byte. Text
    containing `\\r` is the case the old code got wrong.
    """
    root = Path(__file__).resolve().parents[2]
    script = root / "harness" / "run_cobol_scenario.sh"
    text = script.read_text(encoding="utf-8")

    # decode_send, lifted from the driver heredoc so the test cannot drift from it.
    start = text.index("def decode_send(spec):")
    end = text.index("class Rule(object):", start)
    namespace: dict[str, Any] = {}
    exec(compile(textwrap.dedent(text[start:end]), "<decode_send>", "exec"), namespace)
    decode_send = namespace["decode_send"]

    def escape(value: str) -> str:
        """`acas_plan_escape_data`: `${raw//\\/\\\\}`."""
        return value.replace("\\", "\\\\")

    for data in (
        "21/09/2025",
        "2025/09/21",
        "Y",
        "N",
        "YES",
        "NO",
        "",
        r"01\r02\r2025",
        r"a\\b",
        r"\e[1m",
        r"\t\n",
        "\\",
    ):
        got = decode_send(escape(data) + "\\r")
        assert got == data.encode("utf-8") + b"\r", (
            f"the escape boundary is not byte-transparent for {data!r}: the compiled "
            f"leg would be typed {got!r} while the migrated leg receives {data!r} as "
            "argv, so the two legs would not share one logical input."
        )

    # Proof the escaping is what achieves it: unescaped, the CR-bearing case really
    # does become three ENTER-terminated fields.
    unescaped = decode_send(r"01\r02\r2025" + "\\r")
    assert unescaped.count(b"\r") == 3, (
        "this test no longer demonstrates the defect it locks; decode_send's escape "
        "table may have changed."
    )


# ---------------------------------------------------------------------------
#  MN-09 - NO DIAGNOSTIC LOSES ITS TAIL TO A MISSING LINE CONTINUATION
#
#  A multi-line `acas_die` argument list is held together by trailing backslashes. Drop
#  one and the command ENDS there: the remaining quoted lines become a fresh command
#  whose name is the concatenation of those strings. Because `acas_die` exits, that
#  command never runs, so the advice in it is simply never printed - and the sentences
#  most likely to be lost this way are the ones appended last, which is to say the ones
#  telling an operator how to recover.
#
#  `bash -n` does not catch it: the result is syntactically valid. shellcheck does not
#  either, since a bare word command is legal. It is only visible by looking at where
#  an argument list stops relative to what follows it, which is what this does.
_DIAGNOSTIC_COMMAND = re.compile(
    r"^\s*(acas_(?:[a-z_]*_)?(?:die|note|warn|log|ok)|acas_refuse_target)\b"
)


def test_no_diagnostic_argument_list_is_broken_by_a_missing_continuation() -> None:
    """Every multi-line harness diagnostic keeps its whole argument list."""
    root = Path(__file__).resolve().parents[2]
    scripts = sorted((root / "harness").glob("*.sh"))
    assert scripts, "no harness shell scripts were found to check"

    broken: list[str] = []
    for path in scripts:
        lines = path.read_text(encoding="utf-8").splitlines()
        index = 0
        while index < len(lines):
            match = _DIAGNOSTIC_COMMAND.match(lines[index])
            if not (match and lines[index].rstrip().endswith("\\")):
                index += 1
                continue
            # Walk to the last continued line of this argument list.
            last = index
            while last < len(lines) - 1 and lines[last].rstrip().endswith("\\"):
                last += 1
            # The next non-blank line: an indented quoted string there means the list
            # stopped early and the remainder became an unreachable command.
            following = last + 1
            while following < len(lines) and not lines[following].strip():
                following += 1
            if following < len(lines) and re.match(r"^\s{2,}['\"]", lines[following]):
                broken.append(
                    f"{path.name}:{following + 1}: orphaned after "
                    f"{match.group(1)} at line {index + 1}\n"
                    f"      last argument: {lines[last].strip()[:78]}\n"
                    f"      orphaned     : {lines[following].strip()[:78]}"
                )
            index = last + 1

    assert not broken, (
        "these diagnostic argument lists end before the quoted lines that follow "
        "them, so that text becomes an unreachable command and its advice is never "
        "printed (MN-09):\n  " + "\n  ".join(broken) + "\n\n"
        "  Add the missing trailing backslash, or merge the text into the call."
    )


# ---------------------------------------------------------------------------
#  THE END-OF-CYCLE DESTRUCTIVE ANSWERS
#
#  `acas_posting/cli/args.py` carries an explicit-intent gate. `require_stated`
#  refuses to run until each destructive answer has been STATED, and
#  `stated_explicitly` decides that by asking whether the option was PRESENT ON THE
#  COMMAND LINE. The Python runner then composed `--run-confirmed` and
#  `--disk-change-option <v>` onto argv unconditionally, sourcing the value from its
#  own default when the scenario omitted it - so an omission arrived at the entry
#  point indistinguishable from a deliberate instruction, and the one component whose
#  job is to refuse un-stated consent was told consent had been given.
#
#  the oracle leg listed `disk_change_option` and `archive_path_override` among
#  its known keys and read NEITHER, hard-coding `0`. A scenario declaring `9` was
#  accepted, honoured by the migrated leg and contradicted by the compiled one.
#
#  Both are locked here as SOURCE properties, because the behaviour they concern is
#  reachable only with a live oracle and the defect is visible without one.
_GL080_RUNNERS = ("harness/run_python_scenario.sh", "harness/run_cobol_scenario.sh")


def test_neither_end_of_cycle_answer_can_be_defaulted() -> None:
    """No runner supplies `gl080_proceed` or `disk_change_option` on the scenario's behalf.

    The DISCRIMINATING assertion is the `_default` one: a runner that read the key
    but fell back to `'Y'` or `'0'` would still pass a mere "is the key mentioned"
    check, and would still launder a silent omission into stated consent.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    for relative in _GL080_RUNNERS:
        path = root / relative
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for key in ("gl080_proceed", "disk_change_option"):
                # `<something>_default <key> '<value>'` is the laundering shape.
                if re.search(rf"_default\s+{key}\s+'", line):
                    offenders.append(f"{relative}:{number}: {stripped[:96]}")
    assert not offenders, (
        "these lines default a DESTRUCTIVE end-of-cycle answer, which the runner then "
        "passes as an option and the entry point reads as consent explicitly stated "
        ":\n  " + "\n  ".join(offenders) + "\n\n"
        "  Read the key without a fallback and refuse when it is absent."
    )

    # And the refusal must actually be there - a key read without a fallback and
    # without a refusal would simply run with an empty answer.
    for relative in _GL080_RUNNERS:
        text = (root / relative).read_text(encoding="utf-8")
        for key in ("gl080_proceed", "disk_change_option"):
            assert re.search(rf"does not declare {key}", text), (
                f"{relative} does not refuse a scenario that omits {key}; without "
                "the refusal, removing the default just substitutes an empty answer "
                "for an invented one."
            )


def test_the_oracle_leg_reads_the_disk_change_answer_it_types() -> None:
    """The compiled leg drives the declared option rather than a hard-coded one."""
    root = Path(__file__).resolve().parents[2]
    text = (root / "harness" / "run_cobol_scenario.sh").read_text(encoding="utf-8")

    assert re.search(r"ACAS_RUN_DISK_CHANGE=\"\$\(acas_scenario_scalar disk_change_option\)\"", text), (
        "harness/run_cobol_scenario.sh does not READ disk_change_option. It listed the "
        "key among those it accepts while ignoring it, so a scenario declaring 9 was "
        "driven as 0 on this leg and as 9 on the other."
    )
    # The GL084 step must send the READ value, not a literal.
    assert not re.search(r"'gl080-archive' react 'GL084' '0", text), (
        "the GL084 plan step still hard-codes 0, so the two legs can be driven with "
        "different disk-change answers."
    )
    assert re.search(r"'gl080-archive' react 'GL084'", text) and re.search(
        r'acas_plan_escape_data "\$ACAS_RUN_DISK_CHANGE"', text
    ), "the GL084 step no longer sends the declared value through the escape boundary."

    # The second prompt - which this plan had no step for at all - must be answered.
    assert "'gl080-archive-path'" in text and "Current path/name is" in text, (
        "the plan has no step for the archive-path accept at "
        "[general/gl080.cbl:L555]. Answering GL084 falls through to it, so without a "
        "step the run would stall there and report a pty timeout rather than the "
        "missing step it actually is."
    )


def test_inputs_with_no_oracle_counterpart_are_refused_by_both_legs() -> None:
    """Neither leg accepts an input the other cannot reproduce.

    Asymmetry here is the whole defect: one leg honouring an input the other cannot
    means the two were driven differently, and the diff then measures the harness.
    """
    root = Path(__file__).resolve().parents[2]
    for relative in _GL080_RUNNERS:
        text = (root / relative).read_text(encoding="utf-8")
        assert "cannot be driven through this leg provably" in text or (
            "has no oracle counterpart" in text
        ), f"{relative} does not refuse the unsupported end-of-cycle inputs."
        assert "archive_path_override" in text and re.search(
            r"archive_path_override (cannot be driven|has no oracle counterpart)", text
        ), f"{relative} still accepts archive_path_override."
        # The arbitration must be NAMED, not gestured at, so the refusal is findable.
        # `Q-GL084-ACCEPT-SEMANTICS` is `RESOLVED BY ORACLE` (2026-08-08): the two
        # ACCEPT statements were measured by a standalone cobc 3.2.0 probe over a real
        # pty. The refusals survive that resolution because what they lack is not the
        # semantics but a compiled JOURNEY - `disk-change` is unreachable in every
        # fixture - so the identifier still has to be findable from the diagnostic.
        assert "Q-GL084-ACCEPT-SEMANTICS" in text, (
            f"{relative} refuses these inputs without naming the register entry that "
            "records why, so a reader cannot find the arbitration (R-5, R-6)."
        )

    register = (root / "docs" / "migration" / "ambiguity-resolutions.md").read_text(
        encoding="utf-8"
    )
    assert "Q-GL084-ACCEPT-SEMANTICS" in register, (
        "both runners cite Q-GL084-ACCEPT-SEMANTICS and the register does not carry "
        "it, so the citation dangles."
    )
    assert '<a id="q-gl084-accept-semantics"></a>' in register, (
        "the entry has no anchor, so a fragment citation to it cannot resolve."
    )


def test_no_scenario_declares_an_input_its_runners_refuse() -> None:
    """Every committed scenario is runnable under the tightened input contract."""
    yaml = pytest.importorskip("yaml")
    root = Path(__file__).resolve().parents[2]
    probe = "acas_scenario_parser_probe2"
    spec = importlib.util.spec_from_file_location(
        probe, root / "harness" / "normalize.py"
    )
    assert spec is not None and spec.loader is not None
    loader = importlib.util.module_from_spec(spec)
    #  Registered before execution for the `slots=True` reason `_scenario_yaml_module`
    #  records; a second probe name so the two cannot share a half-executed module.
    sys.modules[probe] = loader
    try:
        spec.loader.exec_module(loader)
    except BaseException:
        sys.modules.pop(probe, None)
        raise

    scenarios = sorted((root / "harness" / "scenarios").glob("*.yaml"))
    assert scenarios, "no scenario definitions were found"

    problems: list[str] = []
    for path in scenarios:
        try:
            declared = loader.load_scenario_yaml(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:  # a duplicate key is the parser test's business
            problems.append(f"{path.name}: does not parse: {exc}")
            continue
        operations = declared.get("operations") or []
        if isinstance(operations, str):
            operations = [operations]
        selects = "gl_end_of_cycle" in operations or (
            declared.get("operation") == "gl_end_of_cycle"
        )
        if declared.get("archive_path_override"):
            problems.append(
                f"{path.name}: declares archive_path_override, which both runners refuse"
            )
        if str(declared.get("disk_change_option") or "") == "9":
            problems.append(
                f"{path.name}: declares disk_change_option 9, which both runners refuse"
            )
        if selects:
            for key in ("gl080_proceed", "disk_change_option"):
                if not declared.get(key):
                    problems.append(
                        f"{path.name}: selects gl_end_of_cycle without declaring {key}, "
                        "which both runners now require"
                    )
    assert not problems, (
        "these committed scenarios can no longer be run by their own runners:\n  "
        + "\n  ".join(problems)
    )


# ---------------------------------------------------------------------------
#  THE DECLARED CLOSURE IS THE PLAN'S, AND THE IMPORTED SET IS
#  EXACTLY THE DRIVER
#
#  THIS PAIR CAN BE WRONG IN TWO OPPOSITE DIRECTIONS, and both are locked.
#
#  TOO WIDE: declaring `SQLAlchemy`, `greenlet` and `typing_extensions` as runtime
#  dependencies, describing SQLAlchemy as "CORE LEVEL ONLY: text() statements on an
#  explicit Connection", pinning all three with hashes and documenting that boundary as
#  ACTIVE - while no module under `acas_posting/` imports any of them. That would have
#  three artifacts describing an execution path the code does not take, and it would sit
#  alongside the same file's correct statement that the package imports "exactly one
#  third-party top-level module, `mysql`".
#
#  TOO NARROW: deleting those three pins from both manifests so that declared and
#  imported coincide. That is self-consistent and NARROWER THAN THE FROZEN PLAN: AAP
#  section 0.5.1 states the runtime inventory as four names at exact versions --
#  mysql-connector-python 26.7.0, SQLAlchemy 2.0.51, and in its own words "Pulls
#  `greenlet` 3.5.4 as a transitive dependency", with typing_extensions travelling with
#  it. The plan is the agreed contract for what this distribution DECLARES and is not
#  editable by the implementation, so a manifest that drops one of its names diverges
#  from it.
#
#  WHAT IS LOCKED, THEREFORE, IS THE PAIR AND NOT EITHER HALF:
#    * the DECLARED runtime closure is EXACTLY the plan's four names - no wider, so a
#      package cannot be smuggled into the shipped graph, and no narrower, so the plan
#      cannot be quietly re-written by deletion;
#    * the IMPORTED third-party set under `acas_posting/` is EXACTLY {mysql}, so the
#      execution path stays auditable from the source;
#    * the DIFFERENCE between them is exactly the three names the plan declares as the
#      alternative Core-level boundary, so a fourth declared-and-unimported package
#      cannot join them unnoticed;
#    * `requirements.txt` pins exactly the union of the manifest's sets, so the hashed
#      route the container and the parity protocol use installs neither more nor less;
#    * and no artifact describes the Core boundary as ACTIVE, which is the too-wide
#      defect itself and is a property of prose that no import census can see.
#
#  Declaring more than is imported is therefore permitted HERE AND ONLY HERE, only for
#  the names the plan itself declares, and only while every artifact says so in as many
#  words. That is what makes it an auditable decision rather than undetected drift.
_PACKAGE_ROOT = "acas_posting"

#: Distribution name -> the top-level module it provides, for the runtime set. A
#: distribution whose import name differs from its package name needs an entry here.
_DISTRIBUTION_MODULES: Mapping[str, str] = MappingProxyType(
    {
        "mysql-connector-python": "mysql",
        "sqlalchemy": "sqlalchemy",
        "greenlet": "greenlet",
        "typing_extensions": "typing_extensions",
        "typing-extensions": "typing_extensions",
    }
)

#: The runtime closure AAP section 0.5.1 fixes, canonicalised the way pip canonicalises
#: a distribution name (lower-case, `_` and `.` folded to `-`). Changing this set means
#: claiming the plan says something different, so it is spelled out here rather than
#: derived from the manifest it is used to check.
_PLAN_RUNTIME_CLOSURE: Mapping[str, str] = MappingProxyType(
    {
        "mysql-connector-python": "26.7.0",
        "sqlalchemy": "2.0.51",
        "greenlet": "3.5.4",
        "typing-extensions": "4.16.0",
    }
)

#: The names the plan declares that the code deliberately does not import. Their
#: presence in the manifest is an auditable decision; a FOURTH name in this position
#: would be drift, so the tests pin the set rather than merely tolerating a non-empty
#: difference.
_DECLARED_AND_NOT_IMPORTED: frozenset[str] = frozenset(
    {"sqlalchemy", "greenlet", "typing-extensions"}
)

#: The one third-party top-level module the shipped package may import.
_IMPORTED_THIRD_PARTY_SET: frozenset[str] = frozenset({"mysql"})


def _canonical_distribution(name: str) -> str:
    """Canonicalise a distribution name the way pip does.

    Args:
        name: A distribution name as written in a manifest or a lock file.

    Returns:
        The name lower-cased with runs of `-`, `_` and `.` folded to a single `-`.
    """
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _declared_runtime_distributions() -> list[str]:
    """Return `pyproject.toml`'s `[project].dependencies`, names only.

    Returns:
        The canonicalised distribution names, in declaration order.
    """
    parsed = _parsed_manifest()
    declared = parsed["project"]["dependencies"]
    return [
        _canonical_distribution(re.split(r"[=<>!~\[;]", entry, maxsplit=1)[0])
        for entry in declared
    ]


def _parsed_manifest() -> dict[str, Any]:
    """Return `pyproject.toml`, parsed.

    Returns:
        The parsed manifest.
    """
    root = Path(__file__).resolve().parents[2]
    manifest = root / "pyproject.toml"
    assert manifest.is_file(), f"the manifest is absent: {manifest}"
    return tomllib.loads(manifest.read_text(encoding="utf-8"))


def _declared_runtime_pins() -> dict[str, str]:
    """Return `pyproject.toml`'s `[project].dependencies` as name -> pinned version.

    Returns:
        Canonical distribution name -> the exact version it is pinned to. An entry that
        is not pinned with `==` maps to the empty string, which the caller reports.
    """
    parsed = _parsed_manifest()
    pins: dict[str, str] = {}
    for entry in parsed["project"]["dependencies"]:
        name, separator, remainder = entry.partition("==")
        pins[_canonical_distribution(name)] = remainder.strip() if separator else ""
    return pins


def _imported_third_party_modules() -> dict[str, set[str]]:
    """Return the third-party top-level modules `acas_posting/` imports.

    Walks every module with `ast` rather than importing them, so the census is a
    property of the source rather than of what a particular run happened to load, and
    so a deferred import inside a function body is counted exactly like a top-level one.

    Returns:
        Top-level module name -> the files that import it.
    """
    root = Path(__file__).resolve().parents[2] / _PACKAGE_ROOT
    standard = set(sys.stdlib_module_names)
    found: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top in standard or top == _PACKAGE_ROOT:
                    continue
                found.setdefault(top, set()).add(path.name)
    return found


def test_the_declared_runtime_closure_is_exactly_the_plans_closure() -> None:
    """`[project].dependencies` is the plan's four names at the plan's versions.

    Both directions matter and for different reasons. A name the plan does not declare
    would put a package into the shipped dependency graph on no authority. A plan name
    that is missing would narrow the frozen closure by deletion, which is a defect in the
    opposite direction and no more permitted than the first.
    """
    declared = _declared_runtime_pins()

    extra = sorted(set(declared) - set(_PLAN_RUNTIME_CLOSURE))
    assert not extra, (
        "pyproject.toml declares these RUNTIME dependencies and AAP section 0.5.1's "
        f"dependency inventory does not name them: {', '.join(extra)}.\n"
        "  The plan fixes the runtime closure at "
        f"{', '.join(sorted(_PLAN_RUNTIME_CLOSURE))}. A package outside it belongs in "
        "an optional-dependency group, or nowhere."
    )

    missing = sorted(set(_PLAN_RUNTIME_CLOSURE) - set(declared))
    assert not missing, (
        "AAP section 0.5.1 declares these in the runtime dependency inventory and "
        f"pyproject.toml no longer does: {', '.join(missing)}.\n"
        "  The plan is FROZEN: aligning the manifest to it is "
        "the standing rule, and a name may not be dropped because nothing imports it. "
        "Declaring a name the code does not import is permitted for exactly "
        f"{', '.join(sorted(_DECLARED_AND_NOT_IMPORTED))} and is stated as such in "
        "pyproject.toml, requirements.txt and README-python-migration.md."
    )

    wrong = sorted(
        f"{name}: manifest {declared[name] or '(not pinned with ==)'}, "
        f"plan {_PLAN_RUNTIME_CLOSURE[name]}"
        for name in sorted(_PLAN_RUNTIME_CLOSURE)
        if name in declared and declared[name] != _PLAN_RUNTIME_CLOSURE[name]
    )
    assert not wrong, (
        "these runtime dependencies are not pinned to the version AAP section 0.5.1 "
        "states:\n  " + "\n  ".join(wrong) + "\n"
        "  Every version in section 0.5.1 was resolved rather than recalled, and a "
        "driver or runtime change can move a stored penny (R-6)."
    )


def test_the_imported_third_party_set_is_exactly_the_driver() -> None:
    """`acas_posting/` imports exactly one third-party module, `mysql`.

    This is the too-wide half, expressed positively. The manifest declares
    four names; the source may reach for only one of them, so that the execution path
    stays auditable from the source rather than inferred from the manifest.
    """
    imported = _imported_third_party_modules()
    observed = frozenset(imported)

    unexpected = sorted(
        f"{module} (imported by {', '.join(sorted(imported[module]))})"
        for module in observed - _IMPORTED_THIRD_PARTY_SET
    )
    assert not unexpected, (
        "acas_posting imports third-party modules beyond the one driver:\n  "
        + "\n  ".join(unexpected)
        + "\n  The shipped package's third-party surface is exactly "
        f"{{{', '.join(sorted(_IMPORTED_THIRD_PARTY_SET))}}}. In particular an "
        "`import sqlalchemy` here would take the Core-level data-access path the "
        "project deliberately does not take: acas_posting/dal/connection.py reproduces "
        "the frozen bridges' connection ownership, which an Engine is built to own "
        "instead, and re-routing it would change which physical session a statement "
        "runs on (R-4, R-6)."
    )

    absent = sorted(_IMPORTED_THIRD_PARTY_SET - observed)
    assert not absent, (
        f"acas_posting no longer imports {', '.join(absent)}. The database driver is "
        "the package's one third-party import; if it has genuinely gone, this census "
        "and every document describing it need re-stating, not this assertion relaxing."
    )


def test_the_declared_but_unimported_set_is_exactly_the_three_the_plan_declares() -> None:
    """Declaring-without-importing is confined to the plan's three names.

    The difference between the declared closure and the imported set is where the drift
    lives. Leaving it merely "allowed to be non-empty" would let a fourth package settle
    there unnoticed, which is the same defect with a different name in it, so the set is
    pinned exactly.
    """
    declared = set(_declared_runtime_distributions())
    imported = _imported_third_party_modules()

    unmapped = sorted(name for name in declared if name not in _DISTRIBUTION_MODULES)
    assert not unmapped, (
        "these runtime dependencies have no entry in _DISTRIBUTION_MODULES, so this "
        f"census cannot say whether they are imported: {', '.join(unmapped)}. Add the "
        "distribution-to-module mapping rather than removing the assertion."
    )

    unused = {name for name in declared if _DISTRIBUTION_MODULES[name] not in imported}

    joined = sorted(unused - _DECLARED_AND_NOT_IMPORTED)
    assert not joined, (
        "these packages are declared as RUNTIME dependencies of acas_posting, no module "
        f"in the package imports them, and the plan does not declare them either: "
        f"{', '.join(joined)}.\n"
        "  A manifest that advertises an execution path the code does not take makes "
        "the shipped architecture unauditable from the artifact. Either use the "
        "package or stop declaring it -- and if it belongs to the harness or the test "
        "tooling, declare it in the matching optional-dependency group instead."
    )

    started_being_imported = sorted(_DECLARED_AND_NOT_IMPORTED - unused)
    assert not started_being_imported, (
        "these packages are recorded across pyproject.toml, requirements.txt, "
        "README-python-migration.md and harness/Dockerfile.gnucobol as DECLARED AND NOT "
        f"IMPORTED, and acas_posting now imports them: {', '.join(started_being_imported)}"
        ".\n  If that is intended it is a change of data-access architecture, not a "
        "test to relax: those four artifacts state the opposite, and "
        "test_no_document_claims_an_unused_data_access_boundary forbids describing the "
        "Core boundary as active while it is not taken."
    )


def test_every_imported_third_party_module_is_declared() -> None:
    """The package imports nothing it does not declare - the other direction.

    Without this half, satisfying the first would be as easy as deleting a needed pin:
    an install reproduced from the manifest would then fail at import instead.
    """
    declared = _declared_runtime_distributions()
    provided = {
        _DISTRIBUTION_MODULES[name]
        for name in declared
        if name in _DISTRIBUTION_MODULES
    }
    imported = _imported_third_party_modules()

    undeclared = sorted(
        f"{module} (imported by {', '.join(sorted(files))})"
        for module, files in imported.items()
        if module not in provided
    )
    assert not undeclared, (
        "acas_posting imports these third-party modules and pyproject.toml's "
        f"[project].dependencies declares none of them:\n  {chr(10).join(undeclared)}\n"
        "  An environment built from the manifest would fail at import."
    )


def test_the_manifests_agree_on_the_runtime_set() -> None:
    """`requirements.txt` pins exactly the manifest's names, with no orphan.

    The lock file is what the container and the parity protocol install from, so it is
    the artifact that decides what actually lands in every environment that matters. A
    name pinned there and not declared in `pyproject.toml` would install silently; a name
    declared and not pinned would be missing from the one route that is hash-verified.
    Both are asserted, over the WHOLE manifest -- runtime, harness, dev and the build
    backend -- because a hashed install of this file installs all of them at once.
    """
    root = Path(__file__).resolve().parents[2]
    lock = (root / "requirements.txt").read_text(encoding="utf-8")

    pinned = {
        _canonical_distribution(match.group(1)): match.group(2)
        for match in re.finditer(
            r"^([A-Za-z][A-Za-z0-9_.-]*)==([^\s\\]+)", lock, re.MULTILINE
        )
    }

    parsed = _parsed_manifest()
    manifest_entries: list[str] = list(parsed["project"]["dependencies"])
    for group, entries in parsed["project"]["optional-dependencies"].items():
        for entry in entries:
            # The `test` group is defined BY REFERENCE (`acas-posting[dev,harness]`) so
            # the two sets can never drift apart; it names no distribution of its own.
            if _canonical_distribution(
                re.split(r"[=<>!~\[;]", entry, maxsplit=1)[0]
            ) == _canonical_distribution(parsed["project"]["name"]):
                continue
            manifest_entries.append(entry)
    manifest_entries.extend(parsed["build-system"]["requires"])

    declared_pins: dict[str, str] = {}
    for entry in manifest_entries:
        name, separator, remainder = entry.partition("==")
        declared_pins[_canonical_distribution(name)] = (
            remainder.strip() if separator else ""
        )

    missing = sorted(set(declared_pins) - set(pinned))
    assert not missing, (
        f"pyproject.toml declares {', '.join(missing)} and requirements.txt does not "
        "pin them, so the hash-verified route -- the one the container and the parity "
        "protocol use -- would not provide them."
    )

    orphans = sorted(set(pinned) - set(declared_pins))
    assert not orphans, (
        f"requirements.txt pins {', '.join(orphans)} and no group of pyproject.toml "
        "declares them. A hashed install would place them in the container and the "
        "parity environment while the manifest looked clean, which is exactly how such a "
        "divergence survives unnoticed."
    )

    disagreements = sorted(
        f"{name}: pyproject {declared_pins[name] or '(not pinned with ==)'}, "
        f"requirements.txt {pinned[name]}"
        for name in sorted(declared_pins)
        if declared_pins[name] != pinned[name]
    )
    assert not disagreements, (
        "these names are pinned to different versions in the two dependency "
        "artifacts:\n  " + "\n  ".join(disagreements) + "\n"
        "  A version that differs between them is a defect, not a variation: the two "
        "install routes would then produce different environments and only one of them "
        "could be the one parity evidence was taken on (R-6)."
    )


def test_every_pin_in_the_lock_is_hash_verified() -> None:
    """Every `requirements.txt` pin carries at least one `--hash`, so nothing floats.

    `pip install --require-hashes` refuses the whole file if ANY requirement lacks a
    hash, so a missing one does not weaken the install quietly -- it breaks the
    documented route outright, including the image build in
    `harness/Dockerfile.gnucobol`. Asserting it here names the offending pin instead.
    """
    root = Path(__file__).resolve().parents[2]
    text = (root / "requirements.txt").read_text(encoding="utf-8")

    # A requirement is its `name==version` line plus the continuation lines it joins
    # with a trailing backslash. Splitting on that keeps each pin with its own hashes.
    logical = re.sub(r"\\\n\s*", " ", text)
    unhashed = [
        match.group(1)
        for match in re.finditer(
            r"^([A-Za-z][A-Za-z0-9_.-]*==[^\s]+)([^\n]*)$", logical, re.MULTILINE
        )
        if "--hash=sha256:" not in match.group(2)
    ]
    assert not unhashed, (
        "these requirements.txt pins carry no --hash, which makes "
        "`pip install --require-hashes -r requirements.txt` refuse the entire file:\n  "
        + "\n  ".join(unhashed)
    )


def test_the_documented_pin_and_hash_counts_match_the_lock() -> None:
    """README section 7 quotes the pin and hash counts; both must be measured, not stale.

    A pin change that leaves the documented figure behind makes the README describe a
    lock the tree has not got - a 13-pin lock where the tree carries ten. A count in
    prose is a claim about the tree, and this ties it to the tree so the next pin change
    cannot leave it behind.
    """
    root = Path(__file__).resolve().parents[2]
    lock = (root / "requirements.txt").read_text(encoding="utf-8")
    readme_text = (root / "README-python-migration.md").read_text(encoding="utf-8")
    # The claim wraps across source lines, so compare against unwrapped text.
    readme = " ".join(readme_text.split())

    pins = len(set(re.findall(r"^([A-Za-z][A-Za-z0-9_.-]*)==", lock, re.MULTILINE)))
    hashes = lock.count("--hash=sha256:")

    quoted = re.search(r"\*\*(\d+) hashes across (\d+) pins\*\*", readme)
    assert quoted, (
        "README section 7 no longer states the pin and hash counts in the form "
        "'**<N> hashes across <M> pins**'. Restore the claim or update this test -- the "
        "install section is where a reader checks the lock is complete."
    )

    documented_hashes, documented_pins = int(quoted.group(1)), int(quoted.group(2))
    assert (documented_hashes, documented_pins) == (hashes, pins), (
        f"README section 7 documents {documented_hashes} hashes across "
        f"{documented_pins} pins; requirements.txt actually carries {hashes} hashes "
        f"across {pins} pins.\n"
        "  A stale count here means the prose is describing a closure the lock does not "
        "have."
    )

    # The prose also spells the pin count as a word ("all thirteen pinned
    # distributions"), and a spelled count drifts just as silently as a digit.
    spelled = [
        word
        for word, value in _NUMBER_WORDS.items()
        if f"all {word} pinned distributions" in readme.lower() and value != pins
    ]
    assert not spelled, (
        f"README section 7 spells the pin count as {', '.join(spelled)} while "
        f"requirements.txt pins {pins} distributions."
    )


def test_no_document_claims_an_unused_data_access_boundary() -> None:
    """No artifact describes SQLAlchemy Core as the active boundary.

    Text rather than imports, because the defect was three documents describing an
    execution path the code does not take, and no import census can see prose. The pins
    fix what the manifests DECLARE, not what the code executes, so a document may say the
    name is declared and may quote what the plan contemplates -- and may not say the
    boundary is live. A sentence recording the decision is exempt; a sentence asserting the boundary
    is active is not.
    """
    root = Path(__file__).resolve().parents[2]
    # The ASSERTIVE forms only. A decision record has to be able to quote what the
    # plan says - AAP section 0.1.2's diagram label "SQLAlchemy Core / connector" is
    # itself an either/or and was never a claim in these files - so the patterns match
    # the shapes that actually asserted the boundary was live, not every mention of it.
    claims = (
        "sqlalchemy is used at",
        "used at core level only",
        "used at **core level only**",
        "used at CORE level only",
        "| **core level only**",
        "sqlalchemy core is",
        #  The bare declarative shape, added because `acas_posting/dal/__init__.py`
        #  stated the constraint that way - "SQLAlchemy at Core level; no ORM entity
        #  layer" - and matched none of the patterns above. A constraint list is
        #  precisely where a reader looks to learn what the layer does, so the
        #  shortest spelling of the claim needs a pattern of its own.
        "sqlalchemy at core level",
    )
    # And a sentence that names a finding, or that states the declared-not-imported pair
    # in as many words, is the record of the decision rather than a claim.
    exempt = (
        "mj-20",
        "dep-01",
        "deliberately absent",
        "is absent from",
        "not imported",
        "does not take",
    )
    offenders: list[str] = []
    for relative in (
        "pyproject.toml",
        "requirements.txt",
        "README-python-migration.md",
        #  The package docstring of the layer itself, which was NOT scanned and was
        #  the one place a reader arrives at by reading the code rather than the
        #  documentation. Its constraint list described the boundary as active while
        #  the three artifacts above had already been corrected, so the scan's own
        #  omission was what let the last copy of the claim survive.
        "acas_posting/dal/__init__.py",
    ):
        path = root / relative
        assert path.is_file(), f"a declared artifact is absent: {path}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            lowered = line.lower()
            if any(word in lowered for word in exempt):
                continue
            for claim in claims:
                if claim in lowered:
                    offenders.append(f"{relative}:{number}: {line.strip()[:96]}")
    assert not offenders, (
        "these lines describe a SQLAlchemy Core boundary as active, while no module in "
        "acas_posting imports SQLAlchemy at all:\n  " + "\n  ".join(offenders)
    )


def test_the_declared_and_unimported_decision_is_stated_in_every_artifact() -> None:
    """Every artifact that carries the three pins also says they are not imported.

    Declaring a package the code does not import is only auditable if the artifact says
    so. The failure mode is exactly this omission: three artifacts carrying the pins and
    none recording that nothing imports them, leaving a reader unable to tell a decision
    from a mistake. Carrying the pins therefore carries the obligation to state the pair,
    and this test holds the two together.
    """
    root = Path(__file__).resolve().parents[2]
    # Each artifact must contain a phrase asserting the DECLARED / NOT IMPORTED pair. The
    # alternatives per file are wording variants of one statement, not different claims.
    required: Mapping[str, tuple[str, ...]] = MappingProxyType(
        {
            "pyproject.toml": ("declared here and is not imported",),
            "requirements.txt": ("declared is not the same as imported",),
            "README-python-migration.md": ("declared and is not imported",),
            "harness/Dockerfile.gnucobol": ("declared is not imported",),
        }
    )
    missing: list[str] = []
    for relative, phrases in required.items():
        path = root / relative
        assert path.is_file(), f"a declared artifact is absent: {path}"
        lowered = path.read_text(encoding="utf-8").lower()
        if not any(phrase in lowered for phrase in phrases):
            missing.append(f"{relative} (expected one of: {', '.join(phrases)})")
    assert not missing, (
        "these artifacts carry the SQLAlchemy pin, or assert on it, and none of them "
        "states that nothing imports it:\n  " + "\n  ".join(missing) + "\n"
        "  A declared-and-unimported dependency is an auditable decision only while "
        "every artifact says so; unstated, it is undetectable drift."
    )


# ==========================================================================
#  DOCSTRING EXAMPLE INTEGRITY  (R-5)
#
#  WHAT WENT WRONG, AND WHY A SHAPE CHECK IS NOT ENOUGH ON ITS OWN. A reflow pass over
#  the data-access docstrings wrapped thirteen doctest blocks INTO the prose of the
#  `Returns:` and `Raises:` sections they sat under, so that several `>>>` prompts and
#  their expected outputs ran together on one line - `... pair to store into
#  ``FileAccess``. >>> end_of_file_status() (<FsReply.END_OF_FILE: 10>, 10).` One of
#  them was truncated mid-call and showed no result at all. Every one had stopped being
#  an executable example, and none of them could fail, because
#  `--doctest-modules` is deliberately absent from `pyproject.toml`'s `addopts`: the
#  config excludes it along with every other flag that changes collection.
#
#  SO BOTH PROPERTIES ARE ASSERTED, AND THEY CATCH DIFFERENT THINGS.
#
#   (1) THE SHAPE. A `>>>` must begin its own line and a line must carry at most one.
#   That is the exact damage the reflow did, and it is checkable without importing
#   anything, so it holds for every module in the package including ones this tier
#   would otherwise never load.
#
#   (2) THE EXECUTION. The examples must actually run and produce what they claim.
#   A shape check alone would pass an example whose expected output had gone stale,
#   which is the slower version of the same defect. This runs `doctest` over the
#   package IN PROCESS rather than by enabling `--doctest-modules`, so the config's
#   own decision about collection is left exactly as it is.
#
#  WHY THE EXAMPLES MATTER AT ALL, given they are documentation. Under R-5 a docstring
#  is the traceable statement of what a paragraph does, and a `>>>` line is the part of
#  it a reader will trust without checking. An example that cannot run is a claim
#  nothing tests; one that runs and is wrong is worse.
# ==========================================================================


def test_no_docstring_example_is_reflowed_into_prose() -> None:
    """Every `>>>` begins its own line, and no line carries two.

    The reflow defect is mechanically recognisable: it leaves a prompt in the middle of
    a sentence, or two prompts on one line with an expected output wedged between them.
    Asserted over the whole shipped package by TEXT, so a module this tier does not
    import is covered exactly as well as one it does.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []
    scanned = 0
    for path in sorted((root / "acas_posting").rglob("*.py")):
        scanned += 1
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if ">>>" not in line:
                continue
            stripped = line.strip()
            if line.count(">>>") > 1:
                offenders.append(
                    f"{path.relative_to(root)}:{number}: two prompts on one line: "
                    f"{stripped[:96]}"
                )
            elif not stripped.startswith(">>>"):
                offenders.append(
                    f"{path.relative_to(root)}:{number}: prompt inside prose: "
                    f"{stripped[:96]}"
                )

    assert scanned, "no module was scanned, so this assertion is vacuous"
    assert offenders == [], (
        "these lines carry a doctest prompt that is not at the start of its own line, "
        "which is what a reflow pass does to an example and what stops it being "
        "executable:\n  " + "\n  ".join(offenders) + "\n"
        "  Move the example into an `Examples:` section, one statement per `>>>` line "
        "with its expected output on the following line."
    )


def test_every_docstring_example_in_the_package_runs_and_passes() -> None:
    """The examples execute, and produce what they say they produce.

    Run in process with `doctest` rather than by adding `--doctest-modules` to
    `addopts`, because `pyproject.toml` excludes that flag deliberately - along with
    every other flag that changes collection - and a documentation guard is not a
    reason to reopen that decision.

    The attempted count is asserted non-zero as well. Deleting every example would
    otherwise satisfy a "no failures" assertion perfectly, which is the one way this
    test could go quiet while the property it protects disappeared.
    """
    import acas_posting

    names = ["acas_posting"] + sorted(
        found.name
        for found in pkgutil.walk_packages(acas_posting.__path__, "acas_posting.")
    )

    failures: list[str] = []
    attempted = 0
    for name in names:
        module = importlib.import_module(name)
        reported: list[str] = []
        runner = doctest.DocTestRunner(verbose=False)
        for test in doctest.DocTestFinder().find(module, name):
            runner.run(test, out=reported.append)
        attempted += runner.tries
        if runner.failures:
            failures.append(f"{name}: {runner.failures} failing example(s)")
            failures.extend(
                line for line in "".join(reported).splitlines() if line.strip()
            )

    assert attempted, (
        "no docstring example was found anywhere in acas_posting, so this assertion "
        "is vacuous. The package carried thirty-eight; if they were removed "
        "deliberately, remove this test in the same change and say why."
    )
    assert failures == [], (
        f"{attempted} examples were attempted and these did not produce what they "
        "claim:\n  " + "\n  ".join(failures[:60])
    )


#: The bare identifier shapes `docs/migration/anomaly-log.md` section 15 forbids, each
#: written so that a legitimate scoped form cannot match it. A tag is bare when the
#: digits follow the letter directly with no owning program between them:
#:
#:      A14           bare        <- refused
#:      F-14          bare        <- refused
#:      A-14          canonical   <- allowed, it IS the register's own id
#:      A-NEW-14      canonical   <- allowed, it IS the register's candidate namespace
#:      A-CURSOR-14   scoped      <- allowed
#:      F-PL100-14    scoped      <- allowed
#:      F-ARGS-1      scoped      <- allowed
#:
#: `A-NEW-<n>` is deliberately NOT among the refused shapes, and the distinction is
#: worth stating because section 15's rule names it. What that rule forbids is
#: ALLOCATING a fresh `A-NEW-<n>` inside one module, not citing the register's own
#: candidate namespace - and a text scan cannot tell those apart, since
#: `programs/pl060_order_posting.py` legitimately cites `A-NEW-1` (the one number the
#: register and the module agree on) while `programs/pl100_payment_posting.py`
#: legitimately quotes `A-NEW-5` as the OLD alias section 15.1 renamed. The allocation
#: case is bounded instead by the range check below.
_BARE_ANOMALY_TAG_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"(?<![-\w])A\d+\b", "a bare A<n>"),
    (r"(?<![-\w])F-\d+\b", "a bare F-<n>"),
)

#: The register's `A-NEW-` namespace is 18 entries [docs/migration/anomaly-log.md
#: section 15]. A module citing a higher number is allocating its own, which is the
#: case the patterns above cannot see.
_REGISTER_A_NEW_HIGHEST: Final[int] = 18


def test_no_module_allocates_a_bare_anomaly_identifier() -> None:
    """No shipped module tags an anomaly with a bare `A<n>` or a bare `F-<n>`.

    THE RULE IS THE REGISTER'S OWN, and it exists because the digits alone do not say
    which register a reader is in. `docs/migration/anomaly-log.md` section 15 closes with
    it: *"A bare `A<n>`, a bare `A-NEW-<n>` and a bare `F-<n>` allocated inside a single
    module are each not an acceptable identifier."*

    WHAT WENT WRONG WHILE THE RULE WAS ONLY WRITTEN DOWN. Six modules had opened families
    numbered from 1 with no prefix, so `A14` meant the discarded row of a `READ NEXT` in
    `dal/cursor_state.py`, a commented-out `open extend` in `dal/acas029_otm5.py`, and
    `gl072`'s sequential nominal read in the register itself - three defects at one
    spelling. Three other modules were using a bare `A6` to mean the register's `A-6`, so
    one shape carried both scopes at once. Section 15.2 renamed all of them and declared
    the families; this test is what stops a seventh from being opened the same way, since
    a rule enforced only by review is a rule that returns.

    TWO EXEMPTIONS, BOTH NARROW. A line carrying the word "bare" is a line that names the
    shape in order to forbid it - every family declaration ends with one - so it is a
    DECLARATION of the convention rather than an allocation under it. And
    `A-NEW-<n>` is not scanned as a shape at all, for the reason given above the
    patterns; what is checked instead is that no module cites a number beyond the
    register's own 18.

    Scope: every `.py` file under `acas_posting/`. The tests and the harness are excluded
    deliberately - a test may legitimately quote a bare form while asserting against it,
    as this file's own patterns above do.
    """
    root = Path(__file__).resolve().parents[2]
    package = root / "acas_posting"
    assert package.is_dir(), f"the shipped package is absent: {package}"

    compiled = tuple(
        (re.compile(pattern), description)
        for pattern, description in _BARE_ANOMALY_TAG_PATTERNS
    )
    a_new = re.compile(r"(?<![-\w])A-NEW-(\d+)\b")
    offenders: list[str] = []
    over_range: list[str] = []
    scanned = 0
    for path in sorted(package.rglob("*.py")):
        scanned += 1
        relative = path.relative_to(root).as_posix()
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            for allocated in a_new.finditer(line):
                if int(allocated.group(1)) > _REGISTER_A_NEW_HIGHEST:
                    over_range.append(
                        f"{relative}:{number}: {allocated.group(0)} is beyond the "
                        f"register's {_REGISTER_A_NEW_HIGHEST}: {line.strip()[:80]}"
                    )
            if "bare" in line.lower():
                #  The declaration of the convention, not an allocation under it.
                continue
            for expression, description in compiled:
                match = expression.search(line)
                if match is not None:
                    offenders.append(
                        f"{relative}:{number}: {description} "
                        f"({match.group(0)}): {line.strip()[:88]}"
                    )
    assert scanned >= 89, (
        f"only {scanned} modules were scanned; the package holds at least 89, so the "
        f"scan is not reaching the tree it is meant to police."
    )
    assert not offenders, (
        f"{len(offenders)} bare anomaly identifier(s) in the shipped package. Each one "
        f"means a different defect depending on which file a reader is in, which is the "
        f"collision docs/migration/anomaly-log.md section 15.2 exists to have removed. "
        f"Give the tag its owning program - `A-CURSOR-14`, `A-ACAS029-14`, "
        f"`F-ARGS-1` - and declare the family in section 15:\n  "
        + "\n  ".join(offenders)
    )
    assert not over_range, (
        "these citations allocate a candidate number the register does not have, which "
        "is the ambiguity section 15.1 removed once already:\n  "
        + "\n  ".join(over_range)
    )



# ---------------------------------------------------------------------------
#  THE DATABASE SUPERUSER CREDENTIAL REACHES TWO STAGES OF TEN
#
#  `harness/docker-compose.yml` must declare ACAS_DB_ADMIN_USER / ACAS_DB_ADMIN_PASSWORD
#  at service level, because all ten protocol stages run inside the one `gnucobol`
#  service - `tests/conftest.py` drives them from a single pytest process and an operator
#  drives the same ten by hand - and stages 1 and 5, both `reset_db.sh`, drop and
#  re-apply the frozen schema. A service-level variable is inherited by every descendant,
#  so that put the superuser password into the environment of the GnuCOBOL compiler, the
#  preSQL translator, every bridge and menu binary, the migrated Python cycle and pytest.
#
#  Three independent mechanisms now remove it everywhere it is not needed, and the
#  tests below assert each one plus the CENSUS that makes all three safe.
# ---------------------------------------------------------------------------

#: The two names. Spelled here rather than imported, so the test would notice a rename
#: in either direction instead of following it silently.
_ADMIN_CREDENTIAL_NAMES: tuple[str, ...] = (
    "ACAS_DB_ADMIN_USER",
    "ACAS_DB_ADMIN_PASSWORD",
)

#: The harness scripts that perform NO schema administration. Each must drop the pair
#: at entry, so a direct invocation is scoped just as a driven one is.
#:
#: `harness/build_fixtures.sh` was here and is gone: the fixture builder is now the
#: `--build-fixtures` MODE of `harness/seed.sh`, whose SEEDING path
#: legitimately consumes the pair for `SET GLOBAL autocommit'. A header-level `unset`
#: would therefore break the script, so the drop moved INTO the mode - and
#: `test_the_fixture_build_mode_drops_the_credential_before_its_first_child` asserts it
#: there rather than letting the guarantee lapse with the file.
_NON_ADMINISTRATIVE_SCRIPTS: tuple[str, ...] = (
    "harness/build_oracle.sh",
    "harness/run_cobol_scenario.sh",
    "harness/run_python_scenario.sh",
)

#: The only two scripts that legitimately consume the credential.
_ADMINISTRATIVE_SCRIPTS: tuple[str, ...] = ("harness/reset_db.sh", "harness/seed.sh")


def test_only_the_administrative_scripts_consume_the_credential() -> None:
    """THE CENSUS THAT MAKES THE SCRUB SAFE, and that would notice it stopping to be.

    Removing a variable from a child's environment is only correct while no child needs
    it. So rather than trusting that, this counts actual references: the pair may be
    consumed by the two schema-administration scripts and named in documentation
    anywhere, but a NON-administrative script that started reading it would mean the
    scrub had begun breaking something - and this test is how that surfaces, instead of
    as a confusing authentication failure inside a stage.
    """
    root = Path(__file__).resolve().parents[2]

    for relative in _ADMINISTRATIVE_SCRIPTS:
        text = (root / relative).read_text(encoding="utf-8")
        assert any(name in text for name in _ADMIN_CREDENTIAL_NAMES), (
            f"{relative} no longer references the administrative credential at all. "
            "If schema administration has moved elsewhere, the scrub lists in this "
            "module and the `administrative=True` call sites in tests/conftest.py have "
            "to move with it."
        )

    offenders: list[str] = []
    for relative in _NON_ADMINISTRATIVE_SCRIPTS:
        path = root / relative
        assert path.is_file(), f"a declared script is absent: {path}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            # A comment may name it - the scrub block itself does - and the `unset`
            # is the point of this whole exercise.
            if stripped.startswith("#") or stripped.startswith("unset "):
                continue
            if any(name in line for name in _ADMIN_CREDENTIAL_NAMES):
                offenders.append(f"{relative}:{number}: {stripped[:80]}")

    assert not offenders, (
        "these scripts are declared non-administrative and drop the superuser "
        "credential at entry, yet they now READ it, so they cannot work:\n  "
        + "\n  ".join(offenders)
        + "\n  Either the reference is wrong, or the script has become administrative "
        "and must be moved out of the scrub list deliberately."
    )


def test_every_non_administrative_script_drops_the_credential_at_entry() -> None:
    """Mechanism 2: the pair is gone before the script's first child exists.

    Asserted as ordering, not just presence: an `unset` placed after the first
    subprocess would leave exactly the exposure it is meant to close. `set -Eeuo
    pipefail` is used as the marker for "the script has started", and the `unset` must
    come within the header rather than somewhere down in a function.
    """
    root = Path(__file__).resolve().parents[2]
    problems: list[str] = []

    for relative in _NON_ADMINISTRATIVE_SCRIPTS:
        lines = (root / relative).read_text(encoding="utf-8").splitlines()
        unset_at = next(
            (
                number
                for number, line in enumerate(lines, start=1)
                if line.strip().startswith("unset ")
                and all(name in line for name in _ADMIN_CREDENTIAL_NAMES)
            ),
            None,
        )
        if unset_at is None:
            problems.append(
                f"{relative}: never unsets {' and '.join(_ADMIN_CREDENTIAL_NAMES)}"
            )
            continue
        # It must be in the script's header, before any function body or command that
        # could spawn something.
        first_function = next(
            (
                number
                for number, line in enumerate(lines, start=1)
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*\(\)\s*\{", line)
            ),
            len(lines),
        )
        if unset_at > first_function:
            problems.append(
                f"{relative}: unsets the pair at line {unset_at}, AFTER the first "
                f"function at line {first_function} - too late to be a guarantee"
            )

    assert not problems, (
        "the administrative credential is not dropped early enough to be a guarantee "
        ":\n  " + "\n  ".join(problems)
    )


def test_the_fixture_build_mode_drops_the_credential_before_its_first_child() -> None:
    """Mechanism 2, for the one non-administrative path inside an administrative script.

    `harness/seed.sh` is administrative - its seeding path issues `SET GLOBAL autocommit'
    as the superuser - so it cannot drop the pair in its header. Its `--build-fixtures`
    mode needs no database at all and compiles COBOL, which is precisely the exposure
    this guards: the GnuCOBOL compiler inheriting a superuser password.

    So the drop is the FIRST EXECUTABLE STATEMENT of `acas_bf_main`, and that is what is
    asserted - position, not mere presence, because an `unset` after the first child is
    the exposure it exists to close. The mode is also required to reference the pair
    NOWHERE else, so the drop cannot be undone further down.
    """
    root = Path(__file__).resolve().parents[2]
    lines = (root / "harness" / "seed.sh").read_text(encoding="utf-8").splitlines()

    start = next(
        (n for n, line in enumerate(lines) if line.startswith("acas_bf_main() {")),
        None,
    )
    assert start is not None, (
        "harness/seed.sh no longer defines acas_bf_main, so the fixture-build mode "
        "has moved. The superuser-credential drop has to move with it, and this "
        "assertion with that."
    )

    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("}"):
            break
        body.append(line)
    assert body, "acas_bf_main has an empty body"

    first = next(
        (
            line.strip()
            for line in body
            if line.strip() and not line.strip().startswith("#")
        ),
        "",
    )
    assert first.startswith("unset ") and all(
        name in first for name in _ADMIN_CREDENTIAL_NAMES
    ), (
        "the first executable statement of acas_bf_main must drop the administrative "
        f"credential; it is {first[:90]!r}. Anything before it - including a single "
        "command substitution - runs with the database superuser password in its "
        "environment."
    )

    later = [
        f"acas_bf_main+{number}: {line.strip()[:70]}"
        for number, line in enumerate(body, start=1)
        if line.strip()
        and not line.strip().startswith("#")
        and not line.strip().startswith("unset ")
        and any(name in line for name in _ADMIN_CREDENTIAL_NAMES)
    ]
    assert not later, (
        "the fixture-build mode drops the administrative credential and then names it "
        "again, so either the drop or the reference is wrong:\n  " + "\n  ".join(later)
    )


def test_every_harness_script_is_classified_for_the_credential() -> None:
    """Mechanism 1, at its new locus: the FILE SET decides who may hold the pair.

    A ten-stage driver used to decide this per stage, scrubbing the pair out of every
    stage's environment except the two resets'. Folding that driver away
    removes the single invocation a per-stage scrub belonged to: each of the ten stages
    is now either a script an operator runs directly or a stage `tests/conftest.py`
    runs, so the pair is scoped by WHAT IS BEING RUN rather than by a wrapper that
    happened to wrap it.

    The mechanism therefore becomes the classification itself, and a classification is
    only worth anything while it is EXHAUSTIVE: `harness/docker-compose.yml` declares
    the pair at service level, so a harness script nobody classified inherits the
    database superuser password silently. This test is how that surfaces - a new
    `harness/*.sh` fails here until it is deliberately placed in one list or the other,
    and the two lists are what mechanism 2 and the census then enforce.
    """
    root = Path(__file__).resolve().parents[2]
    present = sorted(f"harness/{path.name}" for path in (root / "harness").glob("*.sh"))
    assert present, "harness/ carries no shell script at all"

    administrative = set(_ADMINISTRATIVE_SCRIPTS)
    non_administrative = set(_NON_ADMINISTRATIVE_SCRIPTS)

    overlap = sorted(administrative & non_administrative)
    assert not overlap, (
        f"{overlap} are listed as both administrative and non-administrative, so the "
        "census and the entry-drop assertion contradict each other about the same file."
    )

    unclassified = sorted(set(present) - administrative - non_administrative)
    assert not unclassified, (
        "these harness scripts are in neither credential list:\n  "
        + "\n  ".join(unclassified)
        + "\n  Each inherits ACAS_DB_ADMIN_USER / ACAS_DB_ADMIN_PASSWORD from the "
        "service environment until it is classified. Add it to "
        "_ADMINISTRATIVE_SCRIPTS if it performs schema administration, or to "
        "_NON_ADMINISTRATIVE_SCRIPTS - and drop the pair at its entry - if it does not."
    )

    stale = sorted((administrative | non_administrative) - set(present))
    assert not stale, (
        f"these scripts are classified but no longer exist: {stale}. A stale entry "
        "makes the census pass over a file that is not there while saying nothing about "
        "whatever replaced it."
    )


def test_the_test_protocol_scrubs_the_credential_by_default() -> None:
    """Mechanism 3: `_run_script` withholds the pair unless a caller asks for it.

    The POLARITY is what is asserted. A helper that scrubbed only when asked would put
    the burden on every future call site to remember; scrubbing by default means a new
    stage is least-privileged unless someone deliberately says otherwise.
    """
    conftest = importlib.import_module("conftest")

    signature = inspect.signature(conftest._run_script)
    administrative = signature.parameters.get("administrative")
    assert administrative is not None, (
        "tests/conftest.py::_run_script no longer takes `administrative`, so every "
        "stage it runs receives the database superuser password again."
    )
    assert administrative.default is False, (
        f"`administrative` defaults to {administrative.default!r}; it must default to "
        "False so a stage is least-privileged unless it deliberately opts in."
    )

    # The helper itself, exercised rather than read.
    scrubbed = conftest.without_admin_credentials(
        {
            "ACAS_DB_ADMIN_USER": "root",
            "ACAS_DB_ADMIN_PASSWORD": "SENTINEL-SUPERUSER-SECRET",
            "ACAS_DB_USER": "acas",
            "ACAS_DB_PASSWORD": "app-secret",
        }
    )
    for name in _ADMIN_CREDENTIAL_NAMES:
        assert name not in scrubbed, f"{name} survived the scrub"
    assert "SENTINEL-SUPERUSER-SECRET" not in scrubbed.values(), (
        "the superuser password survived the scrub under some other name"
    )
    # Application access must be untouched, or every scrubbed stage loses the database.
    assert scrubbed["ACAS_DB_USER"] == "acas"
    assert scrubbed["ACAS_DB_PASSWORD"] == "app-secret"

    # Exactly the schema-administration stages opt in: the seed and the two resets.
    source = (Path(conftest.__file__).read_text(encoding="utf-8"))
    assert source.count("administrative=True") == 3, (
        f"{source.count('administrative=True')} call site(s) request the "
        "administrative credential; exactly three should - the seed and the two "
        "resets. A fourth means some other stage has been handed the superuser."
    )


# ---------------------------------------------------------------------------
#  NO ACCOUNTING VALUE REACHES AN ASSERTION MESSAGE
#
#  `harness/diff_states.py` ships two renderers and only one of them is safe to put in
#  a failure message:
#
#    render(tree)     every differing value AND every primary key. Its purpose is the
#                     on-disk report, where that detail belongs.
#    summarise(tree)  table, column name and ordinal, counts. No value, no key.
#
#  The scenario and determinism tiers interpolated `render` into assertion messages, so
#  a failing parity run printed real ledger balances, VAT amounts and account
#  identifiers into pytest output and from there into any log that collects it. The
#  route is now `ParityRun.diagnose()`, `DeterminismRun.diagnose()` and the `withheld`
#  fixture, all defined once in `tests/conftest.py`.
#
#  This is a STATIC test on purpose. The tier it polices is stack-bound - without the
#  Compose stack those tests skip - so the messages themselves are not exercised by an
#  ordinary run, and a regression here would otherwise be invisible until the day a
#  parity run actually failed. Reading the source needs no stack.
# ---------------------------------------------------------------------------

#: The tiers whose assertion messages describe a comparison of real table state.
_STATE_ASSERTING_TIERS: tuple[str, ...] = ("tests/scenarios", "tests/determinism")


def _assertion_message_interpolations(path: Path) -> list[tuple[int, str]]:
    """Every expression interpolated into an `assert` MESSAGE in one module.

    The message is what reaches a log. An expression in the assert CONDITION is not
    printed by pytest unless it is also in the message, so only the message is read.

    Args:
        path: The module to read.

    Returns:
        `(line number, source of the interpolated expression)` for each one.
    """
    found: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
        if isinstance(node, ast.Assert) and node.msg is not None:
            for inner in ast.walk(node.msg):
                if isinstance(inner, ast.FormattedValue):
                    found.append((inner.lineno, ast.unparse(inner.value)))
    return found


def test_no_assertion_message_renders_a_value_bearing_report() -> None:
    """No `diff_states.render` reaches an assertion message.

    `render` is not banned outright, because it is the right function for writing the
    report and for asserting that an EMPTY comparison renders to nothing. What is
    banned is putting its output where pytest will print it.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for tier in _STATE_ASSERTING_TIERS:
        directory = root / tier
        assert directory.is_dir(), f"a declared tier is absent: {directory}"
        modules = sorted(directory.glob("test_*.py"))
        assert modules, f"{tier} holds no test module; this test would be vacuous"
        for module in modules:
            for line, expression in _assertion_message_interpolations(module):
                if re.search(r"(^|\.)_?render\s*\(", expression):
                    offenders.append(f"{tier}/{module.name}:{line}: {expression[:74]}")

    assert not offenders, (
        "these assertion messages interpolate the value-bearing report, which copies "
        "real accounting figures and account identifiers into pytest output:\n  "
        + "\n  ".join(offenders)
        + "\n  Use `parity.diagnose()` / `run.diagnose()` instead - the same comparison, "
        "summarised without values, naming the report and its digest so the figures are "
        "still reachable by anyone who should see them."
    )


def test_the_value_free_route_exists_and_actually_withholds() -> None:
    """The DISCRIMINATING half: `summarise` and `withheld` withhold what they promise.

    A test that only banned `render` would pass just as well against a `diagnose()`
    that had been quietly repointed back at the value-bearing renderer. So sentinel
    values and a sentinel key are pushed through both value-free routes and the output
    is searched for them. `render` is checked too, in the same breath, because the ban
    above is only worth having while the two really do differ.
    """
    root = Path(__file__).resolve().parents[2]
    # Loaded by explicit path, like `_scenario_yaml_module` above, so this tier keeps
    # importing no harness module by package path (rule R-1).
    path = root / "harness" / "diff_states.py"
    assert path.is_file(), f"the comparison module is absent: {path}"
    module_name = "acas_diff_states_probe"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    diff_states = importlib.util.module_from_spec(spec)
    # Registered BEFORE execution, and removed again on failure, exactly as
    # `tests/conftest.py` does it: the module's records are `@dataclass(slots=True)`,
    # and that decorator resolves `cls.__module__` through `sys.modules` while the
    # class is being built, so an unregistered module fails to execute at all.
    sys.modules[module_name] = diff_states
    try:
        spec.loader.exec_module(diff_states)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise

    value_difference = diff_states.ValueDifference(
        column="LEDGER-BALANCE", ordinal=7,
        cobol="SENTINEL-COBOL-VALUE", python="SENTINEL-PYTHON-VALUE",
    )
    tree = diff_states.TreeDiff(
        tables=(
            diff_states.TableDiff(
                table="GLLEDGER-REC", primary_key="LEDGER-KEY",
                in_cobol=True, in_python=True,
                cobol_columns=("LEDGER-KEY", "LEDGER-BALANCE"),
                python_columns=("LEDGER-KEY", "LEDGER-BALANCE"),
                cobol_row_count=1, python_row_count=1,
                missing_in_python=("SENTINEL-MISSING-KEY",), missing_in_cobol=(),
                value_differences=(
                    diff_states.RowDifference(
                        key="SENTINEL-ROW-KEY", values=(value_difference,)
                    ),
                ),
                rows_compared=1,
                cobol_key_types=("str",), python_key_types=("str",),
            ),
        ),
        cobol_dir=None, python_dir=None,
    )
    sentinels = (
        "SENTINEL-COBOL-VALUE", "SENTINEL-PYTHON-VALUE",
        "SENTINEL-ROW-KEY", "SENTINEL-MISSING-KEY",
    )

    summary = diff_states.summarise(tree, report_path=None)
    leaked = [sentinel for sentinel in sentinels if sentinel in summary]
    assert not leaked, (
        f"`summarise` disclosed {leaked}, so the route the scenario tier now relies on "
        "is no longer value-free and an accounting value can reach a log."
    )
    # It must still be a USEFUL diagnosis: naming the table and column is the whole
    # point of summarising rather than saying nothing.
    assert "GLLEDGER-REC" in summary and "LEDGER-BALANCE" in summary, (
        "`summarise` withheld the values AND the table and column names, which leaves a "
        f"failure message that cannot be acted on at all: {summary!r}"
    )

    # And the ban above is only meaningful while `render` really does disclose them.
    rendered = diff_states.render(tree)
    assert all(sentinel in rendered for sentinel in sentinels), (
        "`render` no longer discloses values or keys, so the two renderers no longer "
        "differ and this test pair has stopped measuring anything. Re-derive the "
        "value-free-message policy against what the module now does."
    )


def test_the_withheld_helper_handles_every_shape_the_tier_passes_it() -> None:
    """`withheld` is exercised here because a failure message is not exercised anywhere.

    An assertion message is only formatted WHEN THE ASSERTION FAILS, and the tier that
    calls `withheld` is stack-bound, so on a green run these expressions are never
    evaluated - not locally, and not inside the harness image either. A `TypeError`
    raised while formatting a failure message would therefore stay hidden until the one
    moment it destroys a real diagnosis.

    So every argument SHAPE the call sites actually pass is driven through the helper
    here: a scalar string, an integer, a mapping (one dumped row), a sequence of rows, a
    set of keys, and a tuple of projected cells. Each is checked to render and to
    withhold.
    """
    conftest = importlib.import_module("conftest")
    withheld = conftest._withheld

    sentinel = "SENTINEL-9876.54"
    shapes: tuple[tuple[str, Any], ...] = (
        ("scalar string", sentinel),
        ("integer", 4242),
        ("one dumped row", {"LEDGER-KEY": sentinel, "LEDGER-BALANCE": sentinel}),
        ("a sequence of rows", [{"k": sentinel}, {"k": sentinel}]),
        ("a set of keys", {sentinel, sentinel + "-B"}),
        ("a tuple of cells", (sentinel, 1, None)),
        ("None", None),
    )

    for label, value in shapes:
        rendered = withheld(value, column="LEDGER-BALANCE", artifact="/out/x.json")
        assert isinstance(rendered, str) and rendered.startswith("<") and rendered.endswith(">"), (
            f"withheld({label}) produced {rendered!r}, which is not the bracketed "
            "stand-in every call site interpolates."
        )
        assert sentinel not in rendered, (
            f"withheld({label}) disclosed the value it exists to withhold: {rendered!r}"
        )
        assert "LEDGER-BALANCE" in rendered, (
            f"withheld({label}) dropped the column name, which is the part of the "
            f"message a reader acts on: {rendered!r}"
        )

    # Called the way most sites call it - no column, no artifact - it must still render.
    assert withheld(sentinel).startswith("<"), "withheld() needs its optional arguments"


def test_the_parity_run_memo_is_keyed_by_request_and_written_under_the_callers_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The composed protocol's memo: one run per request, and ONE key per memo entry.

    WHY THIS TEST EXISTS, AND WHY IT IS HERE RATHER THAN IN THE SCENARIO TIER. The memo
    is written by `_run_scenario_parity_stages` at its LAST statement, under a key its
    CALLER computed. When that key was a local of the caller and not a parameter of the
    helper, every scenario fixture raised `NameError: name 'cache_key' is not defined`
    AFTER all ten stages had succeeded - so a green parity produced a red tier, and the
    only tier that could have caught it was the one that needs a Compose stack and a
    built oracle. This node needs neither: the memo is plain Python, so it is locked
    where it can run on a bare host, in the tier that is never skipped.

    THE THREE CLAIMS, each of which the original defect or an over-hasty repair breaks:

    1. THE KEY IS A PARAMETER OF THE HELPER. A helper that derives the key itself, or
       reads a module-level one, is the defect or its worst repair: a single
       module-level key would make every scenario share one entry and hand one scenario
       another scenario's `ParityRun`.
    2. A SECOND REQUEST FOR THE SAME SCENARIO IS SERVED FROM THE MEMO. The stage helper
       runs ONCE and both callers get the SAME object, which is what makes a scenario
       module's nine assertions claims about one run rather than nine.
    3. A REQUEST FOR A DIFFERENT SCENARIO IS NOT. Its key differs, the helper runs
       again, and the two answers are distinct objects.

    NO STAGE IS DRIVEN AND NO DATABASE IS TOUCHED. `_run_scenario_parity_stages` is
    replaced by a stub that records the key it was handed and writes the memo exactly
    where the real helper writes it; `_requested_operations` and `in_scope_tables` are
    replaced so that neither PyYAML nor `harness/dump_tables.py` is imported, keeping
    this tier's import surface unchanged (rule R-1). Everything between the call and
    the stub - the name validation, the key composition and the memo lookup - is the
    shipped code.

    Args:
        tmp_path: The output root, so `scenario_paths` needs no `$ACAS_OUT`.
        monkeypatch: Restores every replacement, including on failure.
    """
    conftest = importlib.import_module("conftest")

    #  CLAIM 1 - the key travels as a keyword argument.
    signature = inspect.signature(conftest._run_scenario_parity_stages)
    parameter = signature.parameters.get("cache_key")
    assert parameter is not None, (
        "tests/conftest.py::_run_scenario_parity_stages no longer takes `cache_key`, so "
        "it must be deriving the memo key itself or reading it from an enclosing scope. "
        "The first hands one scenario another scenario's ParityRun as soon as the two "
        "derivations differ; the second is the NameError this node exists to prevent."
    )
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, (
        f"`cache_key` is {parameter.kind.name}; every other argument of this helper is "
        f"keyword-only so that a call site reads as the protocol it drives."
    )

    driven: list[tuple[str, tuple[object, ...]]] = []
    answers: dict[str, object] = {}

    def stub(scenario: str, **kwargs: Any) -> object:
        """Stand in for the ten stages: record the key, write the memo, answer."""
        cache_key = kwargs["cache_key"]
        driven.append((scenario, cache_key))
        answer = answers.setdefault(scenario, object())
        conftest._PARITY_RUN_CACHE[cache_key] = answer
        return answer

    monkeypatch.setattr(conftest, "_run_scenario_parity_stages", stub)
    monkeypatch.setattr(
        conftest, "_requested_operations", lambda *args, **kwargs: ("gl_post_cycle",)
    )
    monkeypatch.setattr(conftest, "in_scope_tables", lambda: ("GLBATCH-REC",))

    preserved = dict(conftest._PARITY_RUN_CACHE)
    try:
        first = conftest.run_scenario_parity("clean_batch_gl", out_dir=tmp_path)
        again = conftest.run_scenario_parity("clean_batch_gl", out_dir=tmp_path)
        other = conftest.run_scenario_parity("clean_batch_sl", out_dir=tmp_path)
    finally:
        #  The memo outlives a test, so this node's entries are removed rather than
        #  left for a scenario module to be served a stub object from.
        conftest._PARITY_RUN_CACHE.clear()
        conftest._PARITY_RUN_CACHE.update(preserved)

    #  CLAIM 2 - the repeat was served from the memo, so the stages ran once.
    assert first is again, (
        "a second request for clean_batch_gl produced a DIFFERENT run, so the memo the "
        "caller looked up is not the memo the helper wrote. Nine assertions in one "
        "scenario module would then be nine claims about nine runs that are reported as "
        "agreement between them."
    )

    #  CLAIM 3 - a different scenario is a different key and a different run.
    assert other is not first, (
        "clean_batch_sl was served clean_batch_gl's run: the memo is not keyed by the "
        "request. This is what a single module-level key produces."
    )
    assert [scenario for scenario, _ in driven] == ["clean_batch_gl", "clean_batch_sl"], (
        f"the stage helper was driven for {[scenario for scenario, _ in driven]}; it "
        f"must run exactly once per distinct request - once for each scenario, and not "
        f"again for the repeat."
    )

    #  AND THE KEY ITSELF IS THE REQUEST, spelled as the module documents it:
    #  (scenario, operation, out_dir-as-text, max_differences).
    assert driven[0][1] == ("clean_batch_gl", None, str(tmp_path), None), (
        f"the key handed to the helper was {driven[0][1]!r}, which is not the documented "
        f"(scenario, operation, out_dir, max_differences) tuple. A key that omits an "
        f"argument that changes what the protocol does collapses two different runs "
        f"into one memo entry."
    )
    assert driven[0][1] != driven[1][1], (
        "the two scenarios were handed the SAME key, so one of them would have been "
        "served the other's ParityRun."
    )


# ---------------------------------------------------------------------------
#  AN ARTIFACT-INTEGRITY FAULT IS EXIT 2, AND NEVER EXIT 1
#
#  `harness/diff_states.py` publishes three statuses and they are not interchangeable:
#  0 an empty diff, 1 A REAL BEHAVIOURAL DIFFERENCE, 2 the comparison could not be
#  performed. The distinction is the whole reason the tool is trustworthy - 1 is a
#  finding about the MIGRATION, 2 is a finding about the EVIDENCE - and every caller
#  that branches on the status depends on it.
#
#  The stage that verifies the two published trees did not honour it. `verify_trees`
#  reads each manifest AND discovers what the tree actually holds, and the discovery
#  half refuses an unexpected `<NAME>.json` through `table_spec`:
#  `TableNotInScopeError` for one of the eleven out-of-scope tables,
#  `UnknownTableError` for a name that is not a table of the frozen schema. Neither is
#  a `ManifestError`, which was the only class `main` caught there, so both escaped as
#  an unhandled traceback - and the interpreter then exited 1, announcing a corrupt or
#  mixed artifact tree as a parity FAILURE.
#
#  This test is DB-FREE and drives the shipped module end to end - argv in, exit status
#  out - over trees it builds itself from the module's own published constants, so it
#  runs on a bare host and tracks the manifest shape instead of freezing a copy of it.
#  The control case matters as much as the two probes: it proves the planted file is
#  the ONLY reason for the refusal.
# ---------------------------------------------------------------------------


def _load_diff_states_module() -> Any:
    """Load `harness/diff_states.py` by explicit file path (rule R-1).

    The same recipe `tests/conftest.py::_load_harness_module` uses, repeated here so
    this tier still imports no harness module by package path: `harness/` is
    deliberately not a Python package.

    Returns:
        The executed module.
    """
    root = Path(__file__).resolve().parents[2]
    path = root / "harness" / "diff_states.py"
    assert path.is_file(), f"the comparison module is absent: {path}"
    module_name = "acas_diff_states_exit_status_probe"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    #  Registered BEFORE execution and removed again on failure: the module's records
    #  are `@dataclass(slots=True)`, and that decorator resolves `cls.__module__`
    #  through `sys.modules` while the class is being built.
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def _publish_normalized_pair(diff_states: Any, root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    """Write a minimal COMPLETE normalised tree pair, byte-identical on both sides.

    Every key is taken from the module's own constants rather than transcribed, so a
    change to the manifest shape reaches this fixture instead of leaving it asserting
    against a shape nothing writes any more.

    Args:
        diff_states: The loaded comparison module.
        root: A writable directory to build the two trees under.

    Returns:
        The `cobol` and `python` normalised tree paths.
    """
    table = "GLBATCH-REC"
    dump = {
        "table": table,
        "primary_key": diff_states.IN_SCOPE[table].primary_key,
        "columns": [diff_states.IN_SCOPE[table].primary_key, "BCYCLE"],
        "row_count": 1,
        "rows": [["100001", "1"]],
    }
    #  A real digest, because `seed_marker_sha256` must match _SHA256_PATTERN and be
    #  EQUAL on both sides before a row is compared.
    seed_marker = hashlib.sha256(b"one seed, both legs").hexdigest()
    published: list[pathlib.Path] = []
    for side in diff_states.SIDES:
        tree = root / f"{side}{diff_states.NORMALIZED_SUFFIX}"
        tree.mkdir(parents=True)
        member = tree / f"{table}{diff_states.DUMP_SUFFIX}"
        member.write_text(
            json.dumps(dump, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
        manifest = {
            "manifest_version": diff_states.MANIFEST_VERSION,
            "producer": "tests/arithmetic/test_pic_field_descriptors.py",
            "stage": diff_states.MANIFEST_STAGE_NORMALIZED,
            "scenario": "clean_batch_gl",
            "side": side,
            "selector": "tables",
            "provenance": {
                "run_id": "exit-status-probe-1",
                "scenario_file": "harness/scenarios/clean_batch_gl.yaml",
                "scenario_file_sha256": hashlib.sha256(b"scenario").hexdigest(),
                "frozen_schema_sha256": hashlib.sha256(b"schema").hexdigest(),
                #  THE ORACLE DISPOSITION, present because manifest version 4 requires
                #  it and absent from no capture. `no` is the truthful value for a tree
                #  this fixture built in process without compiling anything, and it is
                #  deliberately not `yes`: a probe must never be able to publish a tree
                #  that claims the frozen specification produced it.
                "oracle_source_is_frozen": "no",
                "source_transform_set_sha256": hashlib.sha256(
                    b"in-process probe, nothing compiled"
                ).hexdigest(),
                "producer_sha256": hashlib.sha256(b"producer").hexdigest(),
                "python_version": sys.version.split()[0],
                "command": "in-process",
                "source_manifest_sha256": hashlib.sha256(b"source").hexdigest(),
            },
            "attestation": {
                "attested": True,
                "source": "in-process probe",
                "run_id": "exit-status-probe-1",
                "run_status": 0,
                "wrapper_status": 0,
                "behavioural": 0,
                "assert_failures": 0,
                "seed_fingerprint_sha256": hashlib.sha256(b"fingerprint").hexdigest(),
                "seed_marker_sha256": seed_marker,
                "operations": [],
                "detail": "built in process by the exit-status regression test",
            },
            "table_count": 1,
            "tables": [
                {
                    "table": table,
                    "row_count": 1,
                    "sha256": hashlib.sha256(member.read_bytes()).hexdigest(),
                }
            ],
        }
        (tree / diff_states.MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=False) + "\n", encoding="utf-8"
        )
        published.append(tree)
    return published[0], published[1]


def test_an_unexpected_dump_in_a_published_tree_exits_2_and_not_1(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An out-of-scope or unknown `<NAME>.json` is "cannot compare", not "differs".

    Three cases, and the first is the control: the pair as published must compare
    clean, so the two probes cannot pass for any reason other than the planted file.
    """
    diff_states = _load_diff_states_module()
    left, right = _publish_normalized_pair(diff_states, tmp_path)
    table = "GLBATCH-REC"
    argv = [
        f"--cobol={left}",
        f"--python={right}",
        "--tables",
        table,
        "--quiet",
    ]

    # CONTROL. Nothing planted: 0, and not one byte on stdout.
    assert diff_states.main(list(argv)) == diff_states.EX_IDENTICAL, (
        "the control pair does not compare clean, so the two probes below would "
        "prove nothing. Rebuild the fixture against the current manifest shape."
    )
    captured = capsys.readouterr()
    assert captured.out == "", (
        f"the pass condition is an EMPTY diff with an empty stdout; got {captured.out!r}"
    )

    #  One file per probe, planted into the published tree AFTER it was published -
    #  exactly the shape a stale file from an earlier run, or a hand-copied tree, has.
    probes = {
        "STOCK-REC": "one of the eleven tables the posting cycle never touches",
        "ZZZ-NOT-A-TABLE": "a name that is not a table of the frozen schema at all",
    }
    for planted, why in probes.items():
        intruder = right / f"{planted}{diff_states.DUMP_SUFFIX}"
        intruder.write_text(
            (right / f"{table}{diff_states.DUMP_SUFFIX}").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        try:
            status = diff_states.main(list(argv))
        finally:
            intruder.unlink()
        captured = capsys.readouterr()

        assert status == diff_states.EX_ERROR, (
            f"a published tree holding {planted}.json ({why}) returned "
            f"{status}, not EX_ERROR ({diff_states.EX_ERROR}). "
            f"EX_DIFFERENT ({diff_states.EX_DIFFERENT}) means the two states really "
            f"differ, which is a finding about the MIGRATION; this is a finding about "
            f"the EVIDENCE, and any caller branching on the status would "
            f"mis-classify it."
        )
        assert "Traceback (most recent call last)" not in captured.err, (
            f"{planted}.json produced a raw traceback naming internal paths and line "
            f"numbers rather than a one-line diagnosis:\n{captured.err}"
        )
        assert planted in captured.err, (
            f"the diagnosis for {planted}.json does not name the offending table, "
            f"which is the one fact an operator needs to remove it:\n{captured.err}"
        )
        assert captured.out == "", (
            f"a refusal wrote {captured.out!r} to stdout; the value-free summary "
            f"belongs to exit 1 alone and stdout must stay empty on exit 2."
        )

    # And the pair still compares clean once the intruder is gone, so the refusal was
    # about the planted file and left nothing behind.
    assert diff_states.main(list(argv)) == diff_states.EX_IDENTICAL
    assert capsys.readouterr().out == ""


def test_the_discovery_refusals_are_not_manifest_errors(tmp_path: pathlib.Path) -> None:
    """The reason `main` must catch the ROOT class, pinned as an assertion.

    `TableNotInScopeError` and `UnknownTableError` are raised by the DISCOVERY half of
    tree verification and are deliberately not `ManifestError` subclasses - they are
    not faults in a manifest. A handler enumerating `ManifestError` therefore cannot
    catch them however carefully it is written, which is why the clause catches
    `DiffStatesError`, the module's documented root ("Always exit 2"). If a future
    refactor made them `ManifestError` subclasses this assertion would fail and the
    comment above the clause would need re-deriving - which is the point.
    """
    diff_states = _load_diff_states_module()

    for name in ("TableNotInScopeError", "UnknownTableError"):
        error = getattr(diff_states, name)
        assert issubclass(error, diff_states.DiffStatesError), (
            f"{name} is no longer a DiffStatesError, so the single clause in `main` "
            f"that maps every verification refusal to exit 2 no longer covers it."
        )
        assert not issubclass(error, diff_states.ManifestError), (
            f"{name} has become a ManifestError subclass. That is not wrong in "
            f"itself, but the comment in `main` explains the exit-code defect in "
            f"terms of it NOT being one; re-derive that comment."
        )

    # And the tree-verification path really does raise one of them, rather than
    # converting it into something else on the way out.
    tree = tmp_path / f"cobol{diff_states.NORMALIZED_SUFFIX}"
    tree.mkdir()
    (tree / f"STOCK-REC{diff_states.DUMP_SUFFIX}").write_text("{}", encoding="utf-8")
    with pytest.raises(diff_states.TableNotInScopeError):
        diff_states.discover_tables(tree)


# ---------------------------------------------------------------------------
#  ADV-01 - THE ADVISORY REGISTER STAYS TRUE TO WHAT THE TREE ACTUALLY DOES
#
#  README section 7.1 records an advisory review of every pinned component. A review is
#  a point-in-time record and no offline test can re-run the queries, so what IS tested
#  here is the two claims the register makes ABOUT THIS REPOSITORY -- the parts that can
#  silently stop being true:
#
#    1. every pinned distribution was actually reviewed, so adding a pin without
#       reviewing it is a failure rather than an omission nobody notices; and
#    2. none of the standard-library modules named by the ten applicable CPython
#       advisories is imported anywhere, which is the register's stated reason those
#       advisories are unreachable rather than merely accepted.
#
#  Neither test asserts a vulnerability verdict. They assert that the register cannot
#  drift away from the tree it describes.
# ---------------------------------------------------------------------------

#: The standard-library modules named by the ten CPython advisories that apply to the
#: pinned interpreter. Recorded as top-level module names because that is the
#: granularity an import census can decide.
_ADVISORY_NAMED_STDLIB: Mapping[str, str] = MappingProxyType(
    {
        "plistlib": "CVE-2025-13837",
        "xml": "CVE-2025-12084, CVE-2026-7210",
        "base64": "CVE-2025-12781",
        "tarfile": "CVE-2025-13462",
        "http": "CVE-2026-3644, CVE-2026-6019",
        "html": "CVE-2026-15308",
        "webbrowser": "CVE-2026-4519",
    }
)

#: Named separately because it is a CALL, not an import: `shutil` is entirely fine.
_ADVISORY_NAMED_CALL = "unpack_archive"

_CENSUS_ROOTS: tuple[str, ...] = ("acas_posting", "harness", "tests")


def test_every_pinned_distribution_appears_in_the_advisory_register() -> None:
    """A pin nobody reviewed is the ADV-01 gap reopening.

    The register in README section 7.1 lists the distributions it reviewed. If a pin is
    added to the lock and the register is not extended, the project is carrying a
    component whose advisory status was never examined -- which is precisely the state
    the finding was raised about. Asserted against the lock rather than against
    `pyproject.toml` because the lock is what every environment installs from.
    """
    root = Path(__file__).resolve().parents[2]
    register = (root / "README-python-migration.md").read_text(encoding="utf-8").lower()
    lock = (root / "requirements.txt").read_text(encoding="utf-8")

    pinned = sorted(
        {
            _canonical_distribution(match.group(1))
            for match in re.finditer(
                r"^([A-Za-z][A-Za-z0-9_.-]*)==", lock, re.MULTILINE
            )
        }
    )
    assert pinned, "no pin was parsed from requirements.txt; the census is vacuous"

    unreviewed = [
        name
        for name in pinned
        # The register may spell a name either way round, as PyPI itself does.
        if name not in register and name.replace("-", "_") not in register
    ]
    assert not unreviewed, (
        "requirements.txt pins these distributions and README section 7.1 does not "
        f"name them, so their advisory status is unrecorded: {', '.join(unreviewed)}\n"
        "  Re-run the two queries the register documents and extend it; do not edit "
        "the verdict by hand."
    )


def test_no_advisory_named_stdlib_module_is_imported() -> None:
    """The register calls ten CPython advisories unreachable. This is why.

    Every one of them lives in a module this migration does not use -- consistent with
    the plan's own list of load-bearing standard-library modules (`decimal`, `datetime`,
    `dataclasses`, `argparse`, `pathlib`, `csv`, `json`). Importing one does not create a
    vulnerability by itself, but it DOES falsify the register's stated basis, so the
    correct response to this test failing is to re-review and rewrite section 7.1 --
    not to work around the assertion.
    """
    root = Path(__file__).resolve().parents[2]
    offenders: list[str] = []

    for relative in _CENSUS_ROOTS:
        for path in sorted((root / relative).rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            shown = path.relative_to(root)
            if f".{_ADVISORY_NAMED_CALL}(" in text or f" {_ADVISORY_NAMED_CALL}(" in text:
                offenders.append(f"{shown}: calls {_ADVISORY_NAMED_CALL} (CVE-2026-3087)")
            for node in ast.walk(ast.parse(text, filename=str(path))):
                imported: list[str] = []
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported = [node.module]
                for name in imported:
                    top = name.split(".")[0]
                    if top in _ADVISORY_NAMED_STDLIB:
                        offenders.append(
                            f"{shown}:{node.lineno}: imports {name} "
                            f"({_ADVISORY_NAMED_STDLIB[top]})"
                        )

    assert not offenders, (
        "README section 7.1 records that no module named by an applicable CPython "
        "advisory is imported, and that is the register's basis for calling those "
        "advisories unreachable. These imports contradict it:\n  "
        + "\n  ".join(offenders)
        + "\n  Re-review the affected advisories and rewrite section 7.1 to say what is "
        "actually true."
    )


# ---------------------------------------------------------------------------
#  ONE GLOBAL RESOLUTION STATE FOR EVERY R-6 QUESTION
#
#  `docs/migration/ambiguity-resolutions.md` is the SINGLE place a question's status is
#  declared. Its consumers - the test headers, the traceability document, the anomaly
#  log and the evidence register - then DESCRIBE that status in prose, and prose does
#  not follow a status when it changes. The measured result was a register declaring
#  `Q-2`, `Q-3`, `Q-4`, `Q-5.1`, `Q-5.2` and `Q-SORT-TIE-ORDER` `RESOLVED BY ORACLE`
#  while consumers still called them "pending", "unmeasured", "still open" and, in one
#  case, `PENDING - AWAITING ORACLE EXECUTION` verbatim. Under R-6 that is not a
#  cosmetic drift: a reader cannot tell which statement is current, so the project's
#  arbitration state stops being knowable, and the register's own §17 self-audit was
#  counting statuses that its consumers contradicted.
#
#  The invariant this locks is deliberately POSITIVE rather than a blacklist of stale
#  phrases, because a blacklist has to anticipate the wording and this does not: IF a
#  consumer describes a question in open language AT ALL, the register's own resolution
#  must appear beside it. Historical narrative therefore passes by construction - "was a
#  question for the oracle, and the oracle has ANSWERED it" carries the resolution in the
#  same breath - while a bare "Q-4 is pending" cannot pass however it is phrased.
_REGISTER_RELATIVE: Final[str] = "docs/migration/ambiguity-resolutions.md"

#: Wording that presents a question as NOT YET measured.
_OPEN_LANGUAGE: Final[re.Pattern[str]] = re.compile(
    r"\bstill open\b|\bstill pending\b|\bremains open\b|\bis pending\b|\bare pending\b"
    r"|\bawaiting oracle\b|\bAWAITING ORACLE EXECUTION\b|\bpending measurement\b"
    r"|\bunmeasured\b|\bnobody has measured\b|\bopen question\b|\bopen half\b"
    r"|\bnot (?:yet )?(?:been )?(?:resolved|settled|measured|arbitrated)\b"
    r"|\bonly execution shows\b|\bis a question for the oracle\b|\bnever resolved\b",
    re.IGNORECASE,
)

#: Wording that names the register's resolution, so openness is never stated alone.
_RESOLUTION_LANGUAGE: Final[re.Pattern[str]] = re.compile(
    r"\bRESOLVED\b|\bMEASURED\b|\bANSWERED\b|\bsettled by the language\b"
    r"|\bsettled by\b|\bsettled BY\b",
    re.IGNORECASE,
)


def _register_statuses(root: Path) -> dict[str, str]:
    """Read every question's DECLARED status out of the register.

    Args:
        root: The repository root.

    Returns:
        Question identifier to the status text the register declares for it.
    """
    lines = (root / _REGISTER_RELATIVE).read_text(encoding="utf-8").splitlines()
    heading = re.compile(r"^#{3,4}\s+`(Q-[A-Za-z0-9._-]+)`")
    status = re.compile(r"\*\*Status:\s*(.+?)\*\*", re.S)
    declared: dict[str, str] = {}
    for index, line in enumerate(lines):
        match = heading.match(line)
        if match is None:
            continue
        # The status sits on the heading's own line or within the next few, after the
        # blank line the register's house style puts between them.
        found = status.search("\n".join(lines[index : index + 8]))
        declared[match.group(1)] = found.group(1).strip() if found else ""
    return declared


def test_the_register_declares_a_status_for_every_question_it_enters() -> None:
    """Every `Q-` heading carries a parseable `**Status:**`.

    The precondition for the lock below: a question whose status cannot be read cannot
    be checked against its consumers, and would pass silently.
    """
    root = Path(__file__).resolve().parents[2]
    declared = _register_statuses(root)
    assert len(declared) >= 22, (
        f"the register entered {len(declared)} questions; it carried 22 when this lock "
        f"was written, and entries are never removed."
    )
    unstated = sorted(qid for qid, text in declared.items() if not text)
    assert not unstated, (
        "these register entries have no parseable `**Status:**` line, so their "
        "resolution state cannot be compared with what consumers say about them:\n  "
        + "\n  ".join(unstated)
    )
    # The three statuses that PERMIT open language must still be distinguishable from
    # the ones that do not, or the lock below would vacuously pass everything.
    permits = {
        qid
        for qid, text in declared.items()
        if "PENDING" in text.upper()
        or "PARTIALLY" in text.upper()
        or "different statuses" in text
    }
    assert permits, (
        "no register entry has a status that permits open language, which means the "
        "classification below cannot be discriminating. Q-9 is PARTIALLY RESOLVED and "
        "is what carries this lock; Q-GL084-ACCEPT-SEMANTICS does not, having been "
        "measured on 2026-08-08. If Q-9 also goes, re-derive this lock."
    )


def test_no_consumer_describes_a_resolved_question_as_open() -> None:
    """A consumer may state openness only alongside the register's resolution.

    Read as TEXT across the test suite and the three sibling migration documents,
    because the statements at issue are docstrings, block comments, assertion messages
    and Markdown prose in roughly equal measure - there is no single syntactic node to
    walk. The register itself is excluded: it is the source of truth, and it
    deliberately preserves the readings it has rejected as evidence.
    """
    root = Path(__file__).resolve().parents[2]
    declared = _register_statuses(root)
    # Only questions the register declares FULLY resolved are governed. A `PENDING` or
    # `PARTIALLY RESOLVED` question is entitled to be described as open, because it is.
    governed = {
        qid: text
        for qid, text in declared.items()
        if "PENDING" not in text.upper()
        and "PARTIALLY" not in text.upper()
        and "different statuses" not in text
    }
    assert governed, "no fully resolved question was found; re-derive this lock."

    # A boundary on the right, so `Q-5` does not match inside `Q-5.1` and `Q-2` does not
    # match inside `Q-20`.
    patterns = {
        qid: re.compile(re.escape(qid) + r"(?![0-9A-Za-z._-])") for qid in governed
    }

    consumers = sorted(root.joinpath("tests").rglob("*.py"))
    consumers += [
        path
        for path in sorted(root.joinpath("docs", "migration").glob("*.md"))
        if path.name != Path(_REGISTER_RELATIVE).name
    ]

    violations: list[str] = []
    for path in consumers:
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            hits = [qid for qid, pattern in patterns.items() if pattern.search(line)]
            if not hits:
                continue
            window = "\n".join(lines[max(0, index - 5) : index + 7])
            if _OPEN_LANGUAGE.search(window) is None:
                continue
            if _RESOLUTION_LANGUAGE.search(window) is not None:
                continue
            relative = path.relative_to(root)
            violations.append(
                f"{relative}:{index + 1}: {', '.join(sorted(hits))} described as open "
                f"with no resolution named nearby: {line.strip()[:80]}"
            )

    assert not violations, (
        "these consumers describe a question the register declares RESOLVED using "
        "open language, without naming the resolution anywhere nearby, so the "
        "project's R-6 arbitration state reads differently depending on which file "
        "you open:\n  " + "\n  ".join(violations) + "\n\n"
        "  Either state the register's declared status beside the open language - "
        "which is what a historical account does - or remove the open language. The "
        "register at "
        + _REGISTER_RELATIVE
        + " is the single place a status is declared."
    )


def _repo_root() -> Path:
    """The repository root, by this module's own convention."""
    return Path(__file__).resolve().parents[2]


def _harness_dir() -> Path:
    """The harness tree, which is a SIBLING of the package (rule R-1)."""
    return _repo_root() / "harness"


def _tests_dir() -> Path:
    """The test tree, which owns the tier-availability probe."""
    return _repo_root() / "tests"


# ---------------------------------------------------------------------------
#  THE ORACLE'S PROVENANCE IS THE IDENTITY OF THE SPECIFICATION
#
#  Under R-6 the compiled COBOL *is* the behavioural specification, so "which bytes
#  were compiled" is not an operational detail -- it decides what the migration is
#  being measured against. A build that repairs IF scope, connection lifetime,
#  credential propagation and stale reply pairs has repaired the specification, and
#  an empty diff against it shows agreement with a PATCHED system.
#
#  The defect these close is a quiet one. The transformations were applied
#  unconditionally, so no frozen build was reachable at all, and the parity protocol
#  merely WARNED about the result before printing `identical`. A reader taking the
#  verdict at face value would have read a parity claim that nothing established.
#  The refusal now lives in `harness/reset_db.sh`, which will not set up a comparison it
#  cannot make evidence of (exit 77) - see the test two below.
# ---------------------------------------------------------------------------


def test_the_frozen_oracle_is_the_default_and_transformation_is_opt_in() -> None:
    """A build with no flags applies no source transformation.

    The catalogue of available transformations must not be the register of applied
    ones: the attestation's `oracle-source-is-frozen` is derived from what was
    APPLIED, so a build that applies nothing can answer `yes`. When the two were the
    same array, and that array was a non-empty `readonly`, the answer could only ever
    be `no`.
    """
    build = (_harness_dir() / "build_oracle.sh").read_text(encoding="utf-8")

    # The default is frozen, and the opt-in is a distinct, explicit request. The
    # check is ^-anchored to the DECLARATION: `--frozen-oracle` also assigns 0, but
    # indented, and an unanchored substring test is satisfied by that assignment even
    # when the declaration itself has been flipped to 1.
    declaration = re.search(
        r"^ACAS_ALLOW_SOURCE_TRANSFORMS=(\d+)", build, re.MULTILINE
    )
    assert declaration is not None, "build_oracle.sh declares no transform switch"
    assert declaration.group(1) == "0", (
        "the shipped default applies source transformations, so no frozen oracle is "
        f"reachable and `oracle-source-is-frozen=yes` is unattainable; got "
        f"{declaration.group(1)!r}"
    )
    assert "--transformed-oracle" in build
    assert "--frozen-oracle" in build

    # The APPLIED register exists and is what the attestation is derived from.
    assert "ACAS_SOURCE_TRANSFORMS_APPLIED" in build
    assert "if (( ACAS_ALLOW_SOURCE_TRANSFORMS )); then" in build

    # `source_is_frozen` must be computed from the APPLIED register. Deriving it
    # from the available catalogue is the original defect: that catalogue is a
    # non-empty `readonly` array, so `yes` was unreachable by construction. The
    # assertion is on the ASSIGNMENT's own line so a comment cannot satisfy it.
    derivations = [
        line.strip()
        for line in build.splitlines()
        if "source_is_frozen=" in line and not line.strip().startswith("#")
    ]
    assert derivations, "nothing assigns source_is_frozen"
    assert any("ACAS_SOURCE_TRANSFORMS_APPLIED" in line for line in derivations), (
        "source_is_frozen is not derived from the APPLIED transform register: "
        f"{derivations!r}. Deriving it from the available catalogue makes `yes` "
        "unreachable, which is how a transformed oracle passed as frozen."
    )
    assert not any(
        "ACAS_SOURCE_TRANSFORMS[@]" in line
        and "APPLIED" not in line
        for line in derivations
    ), f"source_is_frozen still reads the available catalogue: {derivations!r}"


def test_the_reset_refuses_a_transformed_oracle_as_evidence() -> None:
    """A non-frozen oracle ends the run, and not with a difference status.

    The distinction is the point. `69`/`1` mean the two states disagree, which is a
    finding ABOUT the migration. `77` means nothing was compared, which is a finding
    about the harness's inputs. Collapsing them would let "we could not measure" be
    read as "we measured and it matched", or as a behavioural defect that does not
    exist.

    The gate lives in `harness/reset_db.sh` (rather than in a ten-stage driver, which folded
    the ten-stage driver away). That is the stronger home, not merely a surviving one:
    reset is the stage that DESTROYS the database, so refusing here means the refusal
    lands before a single table is dropped and a hand-driven operator is stopped exactly
    where a driven one was. The ordering below is asserted for that reason.
    """
    reset = (_harness_dir() / "reset_db.sh").read_text(encoding="utf-8")

    assert "EX_EVIDENCE_UNAVAILABLE=77" in reset
    # Distinct from every other status this script uses - 77 sits deliberately below
    # its 80-91 band so it cannot collide with one of them.
    for other in ("EX_OK=0", "EX_USAGE=80", "EX_PRECONDITION=81", "EX_DATABASE=82"):
        assert other in reset, f"{other} is missing, so 77's distinctness is unproven"
        assert not other.endswith("=77")

    # The refusal is a die, not a warn.
    assert 'acas_die "$EX_EVIDENCE_UNAVAILABLE"' in reset

    # An ABSENT attestation is the same class of answer, because the commonest reason
    # for one on this checkout is that the default frozen build failed.
    marker = 'local attestation="$ACAS_BUILD/$ACAS_RESET_ATTESTATION_BASENAME"'
    assert marker in reset, (
        "the provenance gate no longer resolves the attestation path from "
        "$ACAS_RESET_ATTESTATION_BASENAME, so this window cannot be located"
    )
    absent_gate = reset.split(marker)[1][:1500]
    assert "EX_EVIDENCE_UNAVAILABLE" in absent_gate, (
        "an absent attestation is still reported as a precondition rather than as "
        "evidence-unavailable, so a failed frozen build reads as operator error"
    )

    # The escape hatch exists, is explicit, and taints the run rather than silently
    # restoring it.
    assert "--accept-transformed-oracle" in reset
    assert "ACAS_RESET_ORACLE_IS_DIAGNOSTIC" in reset
    assert "NO PARITY CLAIM" in reset

    # THE TAINT MUST BE READ, NOT MERELY SET. A flag nothing consults is a comment:
    # the waiver has to reach the operator's terminal on the paths that SUCCEED, because
    # those are the runs whose captures get quoted. Asserted as definition plus at least
    # two live call sites, one per successful exit path.
    assert "acas_reset_disclose_diagnostic_oracle() {" in reset, (
        "nothing discloses the waiver, so a run made with --accept-transformed-oracle "
        "looks exactly like a frozen one in its own output"
    )
    calls = [
        line.strip()
        for line in reset.splitlines()
        if line.strip() == "acas_reset_disclose_diagnostic_oracle"
    ]
    assert len(calls) >= 2, (
        f"the disclosure is called {len(calls)} time(s); it must be called on every "
        "successful exit path, or a diagnostic reset can finish quietly."
    )
    assert "an empty diff drawn against this oracle" in reset, (
        "the disclosure does not state the consequence - that an empty diff taken "
        "against a repaired specification says the migrated cycle matches a PATCHED "
        "system (R-4, R-6) - which is the whole reason the waiver is disclosed"
    )

    # And the gate runs BEFORE the drop, so a refusal leaves the database untouched.
    gate_at = reset.index("\n  acas_assert_oracle_attestation\n")
    apply_at = reset.index("\n  acas_apply_schema\n")
    assert gate_at < apply_at, (
        "the provenance gate is invoked after the schema apply, so a refused run has "
        "already dropped 33 tables - the refusal would destroy the state it declined "
        "to measure"
    )

    #  THE TWO ACKNOWLEDGEMENTS MUST BE ONE DECISION, and this half was MEASURED
    #  broken. Moving the gate into `reset_db.sh` left `tests/conftest.py` setting only
    #  its own switch: `ACAS_ACCEPT_TRANSFORMED_ORACLE=1` un-skipped the stack-bound
    #  tiers and all 73 of them then ERRORED at stage 1 on exit 77, because the script's
    #  gate wants its own flag. A diagnostic route that un-skips and then cannot run is
    #  worse than one that skips, so the variable is translated into the flag.
    #
    #  Asserted BOTH ways: the translation exists, and it is conditional. A conftest
    #  that passed the flag unconditionally would waive the gate for every run,
    #  including one where nobody asked - which is exactly the fail-open the gate is
    #  for.
    conftest = (_tests_dir() / "conftest.py").read_text(encoding="utf-8")
    assert "def _transformed_oracle_waiver(" in conftest, (
        "tests/conftest.py no longer translates ACAS_ACCEPT_TRANSFORMED_ORACLE into "
        "reset_db.sh's --accept-transformed-oracle, so the documented diagnostic route "
        "un-skips the stack-bound tiers and then fails all of them at stage 1 on exit "
        "77 (two acknowledgements for one decision, only one of them given)."
    )
    waiver = conftest[conftest.index("def _transformed_oracle_waiver(") :]
    waiver = waiver[: waiver.index("\ndef ", 1)]
    assert 'os.environ.get("ACAS_ACCEPT_TRANSFORMED_ORACLE"' in waiver, (
        "the waiver does not read ACAS_ACCEPT_TRANSFORMED_ORACLE, so it is not the "
        "operator's decision it is passing on."
    )
    assert '"--accept-transformed-oracle"' in waiver and "return []" in waiver, (
        "the waiver must return the flag when the variable is set to 1 and NOTHING "
        "otherwise. Passing it unconditionally waives the provenance gate for every "
        "run, which is the fail-open this whole test exists to prevent."
    )
    #  Both reset stages carry it, because stage 5 destroys the database exactly as
    #  stage 1 does; a waiver on one and not the other fails the protocol halfway.
    assert conftest.count("_transformed_oracle_waiver()") == 3, (
        "the waiver is defined but is not applied at both reset stages (1 and 5); "
        f"found {conftest.count('_transformed_oracle_waiver()')} references where 3 "
        "are expected - the definition plus one use in each of prepare_scenario and "
        "reset."
    )


def test_the_test_tier_skips_rather_than_asserting_parity_on_a_stale_oracle() -> None:
    """The scenario tier reports itself unavailable against a transformed oracle.

    A tier that PASSED here would publish a parity claim nobody had measured, and a
    passing test is far less visible than a skip. The judgement must match
    `harness/reset_db.sh`'s so the two cannot disagree about what counts as evidence.
    """
    conftest = (_tests_dir() / "conftest.py").read_text(encoding="utf-8")

    assert "_probe_oracle_is_frozen" in conftest
    assert "oracle-source-is-frozen" in conftest
    assert "oracle:not-frozen" in conftest
    # Wired into the probe that decides tier availability, not merely defined.
    assert "_probe_oracle_is_frozen(build_root, missing, detail)" in conftest
    # The diagnosis opt-in mirrors harness/reset_db.sh's --accept-transformed-oracle.
    assert "ACAS_ACCEPT_TRANSFORMED_ORACLE" in conftest
    # And the skip reason must carry the measured cause, not a vague pointer.
    assert "exit 74" in conftest
    assert "ACAS-SQLstate-error-list.cob" in conftest


def test_the_missing_member_is_never_written_into_the_frozen_tree() -> None:
    """The absent copybook is not fabricated, and the include it needs is GENERATED.

    Inventing a frozen source file would breach R-3 (no new validations) and R-4
    (reproduce, never fix), and AAP section 0.8.1 makes any diff touching
    `copybooks/*.cob` a defect however authentic the content. So the compatibility
    include exists only inside the writable build copy, and it is
    not a repository file either: `harness/build_oracle.sh` emits it at build time.

    Three things are asserted, because each closes a different way the guarantee could
    lapse: the frozen tree stays clean, no committed copy has come back, and the
    generator's own comment-only self-check still runs on what it wrote. Being
    comment-only is what makes it behaviour-neutral -- measured: the generated C is
    byte-identical with this include, with a zero-byte member, and with different
    comment text.
    """
    harness = _harness_dir()
    repo = harness.parent
    assert not (repo / "copybooks" / "ACAS-SQLstate-error-list.cob").exists(), (
        "the missing archive member has been written into the FROZEN tree; R-3 and "
        "R-4 forbid inventing it, and it must be supplied by the maintainer"
    )
    assert not (harness / "copybook-shims").exists(), (
        "harness/copybook-shims/ has come back. The include is generated into "
        "$ACAS_BUILD by harness/build_oracle.sh; a committed copy is a "
        "file a reader can mistake for archive material, and the Agent Action Plan's "
        "harness inventory does not name it."
    )

    build = (harness / "build_oracle.sh").read_text(encoding="utf-8")

    # It is EMITTED, and only under the build copy.
    assert "acas_install_sqlstate_comment_shim() {" in build, (
        "nothing generates the compatibility include, so no bridge can compile"
    )
    body = build.split("acas_install_sqlstate_comment_shim() {", 1)[1].split(
        "\n}\n", 1
    )[0]
    assert 'local target="$ACAS_BUILD/copybooks/ACAS-SQLstate-error-list.cob"' in body, (
        "the generated include no longer resolves under $ACAS_BUILD. Anywhere else "
        "risks writing it into the frozen checkout."
    )
    assert "$ACAS_REPO" not in body, (
        "the generator names $ACAS_REPO, which holds the frozen artifacts: the "
        "include must be written under $ACAS_BUILD and read from nowhere else"
    )

    # Every emitted line is a comment or blank - checked on the heredoc itself.
    emitted = body.split("<<'SQLSTATE_SHIM_EOF'\n", 1)[1].split(
        "\nSQLSTATE_SHIM_EOF", 1
    )[0]
    assert emitted.strip(), "the generated include would be empty"
    for number, line in enumerate(emitted.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        assert stripped.startswith("*>"), (
            f"generated line {number} is not a comment: {stripped!r}. Executable text "
            f"here would make the include a behavioural change rather than a "
            f"compatibility include"
        )

    # And the generator re-reads what it wrote, so a future edit cannot slip past.
    assert "grep -Ev '^[[:space:]]*(\\*>.*)?$' \"$target\"" in body, (
        "the comment-only self-check no longer runs on the materialised file, so the "
        "grammar that makes the include behaviour-neutral is unenforced"
    )
    # The transformation is registered, so the attestation reports the build as
    # transformed and no verdict from it can be a parity claim.
    assert (
        "'copybooks/ACAS-SQLstate-error-list.cob|supplies the comment-only archive "
        "member" in build
    ), (
        "the generated include is no longer in ACAS_SOURCE_TRANSFORMS, so a build "
        "carrying it could attest `oracle-source-is-frozen yes` and a diff against it "
        "would read as parity with the frozen specification"
    )


# ---------------------------------------------------------------------------
#  THE EVIDENCE VOLUME HAS A STATED LIFETIME (CWE-459)
#
#  The harness publishes every parity run into a named volume, one tree per scenario
#  run and so at most the eight of `harness/scenarios/`. The captures are `SELECT *`
#  over the in-scope tables, so they carry monetary amounts and the primary keys
#  identifying the accounts, customers and suppliers those amounts belong to. An
#  accumulating store of accounting data needs a documented disposal contract, and
#  these assertions are what keep the documented one honest.
#
#  WHY THE DISPOSAL COMMAND'S SHAPE IS ASSERTED, NOT JUST ITS PRESENCE. Sibling
#  clones each own an `acas-harness-<CLONE_INDEX>-out` volume in the same daemon, so
#  `docker volume prune` -- the command an operator reaches for by reflex -- destroys
#  other runs' evidence. Documenting a guarded command and leaving an unguarded one
#  in the same file would defeat the point, so the unguarded forms are asserted
#  ABSENT outside a prohibition.
# ---------------------------------------------------------------------------

#: Every document that must carry the retention and disposal contract.
_RETENTION_DOCUMENTS: tuple[str, ...] = (
    "README-python-migration.md",
    "docs/migration/scenario-diff-evidence.md",
    "harness/docker-compose.yml",
)

#: Commands that reach volumes this clone does not own. Each may appear only as a
#: prohibition -- on a line that also warns against it.
_UNGUARDED_DISPOSAL: tuple[str, ...] = (
    "docker volume prune",
    "docker volume rm $(docker volume ls -q)",
)


@pytest.mark.parametrize("relative_path", _RETENTION_DOCUMENTS)
def test_the_evidence_retention_and_disposal_contract_is_stated(
    relative_path: str,
) -> None:
    """Retention, protection and disposal are documented where an operator looks.

    All three of these files are read by someone deciding what to do with a finished
    run: the README is the narrative, the evidence register is what cites the
    artifacts, and the Compose file is where the volume is declared. A contract
    stated in only one of them is a contract most readers never see.
    """
    text = (_repo_root() / relative_path).read_text(encoding="utf-8")
    lowered = text.lower()

    assert "retention" in lowered or "retain" in lowered, (
        f"{relative_path} says nothing about how long evidence is kept"
    )
    assert "dispos" in lowered, (
        f"{relative_path} says nothing about how evidence is disposed of"
    )
    # The guarded, clone-scoped command, which is the whole mechanism.
    assert "acas-harness-${CLONE_INDEX}-out" in text, (
        f"{relative_path} does not name the clone-scoped volume, so a reader has no "
        f"target-guarded command to copy"
    )


@pytest.mark.parametrize("relative_path", _RETENTION_DOCUMENTS)
def test_no_document_offers_an_unguarded_disposal_command(
    relative_path: str,
) -> None:
    """A broad delete may appear only as a prohibition, never as instruction.

    `docker volume prune` reaches every sibling clone's evidence in the same daemon.
    Naming it is useful -- an operator who has been told not to run it is better
    informed than one who has not -- so the test allows the mention and requires the
    warning on the same line.
    """
    text = (_repo_root() / relative_path).read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        for command in _UNGUARDED_DISPOSAL:
            if command not in line:
                continue
            assert "never" in line.lower() or "not" in line.lower(), (
                f"{relative_path} line {number} offers `{command}` without warning "
                f"against it. It reaches every sibling clone's evidence volume in "
                f"this daemon: {line.strip()!r}"
            )


def test_the_evidence_volume_cannot_default_to_a_sibling_clone() -> None:
    """`CLONE_INDEX` is required for the evidence volume, not defaulted.

    This is what makes the documented disposal command safe: the volume cannot
    silently resolve to a name another run owns, so `docker volume rm
    "acas-harness-${CLONE_INDEX}-out"` either names this clone's volume or fails.
    A `${CLONE_INDEX:-000}` style default would reintroduce the hazard.
    """
    compose = (_harness_dir() / "docker-compose.yml").read_text(encoding="utf-8")
    out_declaration = [
        line for line in compose.splitlines() if "-out" in line and "name:" in line
    ]
    assert out_declaration, "the evidence volume declares no name"
    for line in out_declaration:
        assert "${CLONE_INDEX:?" in line, (
            f"the evidence volume's name does not REQUIRE CLONE_INDEX, so it can "
            f"resolve to a sibling clone's volume: {line.strip()!r}"
        )
        assert "${CLONE_INDEX:-" not in line, (
            f"the evidence volume's name DEFAULTS CLONE_INDEX, which is the hazard "
            f"the required form exists to prevent: {line.strip()!r}"
        )
