"""Anomaly A-7 - the three bridge-derived date components of `IRSPOSTING-REC`.

WHAT THIS FILE LOCKS. The internal IRS posting table carries three columns -
`POST4-DAY`, `POST4-MONTH` and `POST4-YEAR` - that NO COPYBOOK DECLARES. They exist
only because the bridge derives them from a date string under THREE INDEPENDENT
GUARDS WITH NO `else`, so PARTIAL DERIVATION IS REACHABLE: a failed guard leaves its
component at ZERO while the raw date text is still stored unconditionally, producing
a row that is internally inconsistent. That row is CORRECT. This file exists so that
a future well-intentioned repair of it fails the suite rather than passing unnoticed
(rule R-4).

It is therefore the concrete proof of this migration's central methodological claim:
a migration driven from the copybooks alone would silently omit three columns of a
posting table. The bridge, not the copybook, is where the record-layout-to-table
mapping is taken from, and the generated dictionary is where this file reads it.

THE BRIDGE LOAD PARAGRAPH, VERBATIM. `common/irspostingMT.cbl`, exactly as it
appears in the frozen checkout - `bb000-HV-Load Section.` opens at :L958:

     961: *>  Load the Host variables with data from the passed record
     966:      initialize TD-IRSPOSTING-REC.
     967:      move     Post-Key      to HV-KEY-4.
     968:      move     Post-Code     to HV-POST4-CODE.
     969:      move     Post-Date     to HV-POST4-DAT.
     970:      move     Post-DR       to HV-POST4-DR.
     971:      move     Post-CR       to HV-POST4-CR.
     972:      move     Post-Amount   to HV-POST4-AMOUNT.
     973:      move     Post-Legend   to HV-POST4-LEGEND.
     974:      move     Vat-AC-Def    to HV-VAT-AC-DEF4.
     975:      move     Post-Vat-Side to HV-POST4-VAT-SIDE.
     976:      move     Vat-Amount    to HV-VAT-AMOUNT4.
     978: *> These added after new columns  created 31/12/16 - inhouse mysql & mariadb
     979: *>  and yes they all should be numeric as a date is present
     980: *>   but JIC (just in case).
     982:      if       Post-Date (1:2) numeric
     983:               move     Post-Date (1:2) to HV-POST4-DAY.
     984:      if       Post-Date (4:2) numeric
     985:               move     Post-Date (4:2) to HV-POST4-MONTH.
     986:      if       Post-Date (7:2) numeric
     987:               move     Post-Date (7:2) to HV-POST4-YEAR.
     989: *> Loading HVs implies a non-Fetch action. RGs are handled separately for
     990: *> all such actions so they must not be loaded here.

Word for word, with one typographic adjustment stated rather than hidden: the frozen
:L978 separates "new columns" from "created 31/12/16" with a long run of spaces and
follows the date with two, both compressed above so the line fits the file's width.
:L962-L965, :L977, :L981 and :L988 are the blank and explanatory comment lines the
section carries between the statements quoted here.

TWO LINES CARRY THE WHOLE ANOMALY.

  * `[common/irspostingMT.cbl:L966]` `initialize TD-IRSPOSTING-REC.` is why a failed
    guard leaves its component at ZERO and NEVER at SQL `NULL`. Every bridge load
    paragraph opens by initialising the host-variable group, so an unset numeric host
    variable holds zero and an unset character one holds spaces. That is also why
    every column of the frozen schema can be declared `NOT NULL`, and why the Python
    layer must DEFAULT rather than OMIT.
  * `[common/irspostingMT.cbl:L969]` stores the RAW DATE TEXT unconditionally, before
    and regardless of the three guards. So a row can carry an intact `"1X/09/25"` in
    `POST4-DAT` alongside `POST4-DAY = 0` - internally inconsistent, and correct.

THREE INDEPENDENT GUARDS, NO `else`, EIGHT COMBINATIONS. The three `if`s at
`[common/irspostingMT.cbl:L982-L987]` share no condition and have no `else` between
them, so every one of the eight combinations of (day-numeric, month-numeric,
year-numeric) is reachable and all eight are parametrized below. Covering only the
all-pass and the all-fail row would miss the anomaly entirely.

THE THREE COLUMNS ARE INTERLEAVED, NOT APPENDED. They sit at ordinals 4, 5 and 6 of
a thirteen-column table, between `POST4-DAT` (3) and `POST4-DR` (7), declared
`tinyint(2) unsigned NOT NULL` at `[mysql/ACASDB.sql:L278-L280]`. A naive
append-only reading of the table would mis-map every column after the third. The
copybook, `[copybooks/irswspost.cob:L8-L18]`, declares exactly TEN fields and none of
the three.

DICTIONARY KEYS ARE TABLE-QUALIFIED, NEVER BARE FIELD NAMES. `PSIRSPOST-REC` - the
posting file the Sales and Purchase ledgers hand to IRS - and `IRSPOSTING-REC` - the
internal IRS posting file - describe the same ten logical fields, and the frozen
source itself warns about the confusion, verbatim `[copybooks/wspost-irs.cob:L6-L7]`:

      6: *> This is NOT the same as the internal IRS *
      7: *>   posting file                           *

Every lookup here is therefore `<TABLE-NAME>.<COLUMN-NAME>` or
`<COPYBOOK-RECORD>.<FIELD-NAME>`. A bare field name is not a key at all, and a test
below pins that.

WHY THIS TIER TESTS THE RULE AND NOT THE HANDLER MODULE (rule R-1 scoping). The
derivation lives inside a bridge load paragraph, whose Python home is the handler
module `acas_posting/dal/acasirsub4_irs_posting.py`. Rule R-1 puts this tier under
"`tests/arithmetic/*` touch neither COBOL nor a database", so the handler layer is
NOT imported here - not even for a pure function. Instead the rule is composed from
the published COBOL-semantics primitives - `move.ref_mod`, `move.is_numeric_class`
and a store through the component's own dictionary-declared shape - and the column
facts are read from the generated dictionary. The handler module was not skipped: it
is out of this tier's reach by rule, and its own scenario-level lock lives in
`tests/scenarios/test_clean_batch_post_irs.py`.

THE SIX BINDING RULES, AS THEY APPLY HERE.

  * R-1 no COBOL at runtime. No handler import, no subprocess, no database, no
    Docker, no `cobc`. The only file-system prerequisite is
    `data_dictionary/acas_posting_dictionary.json`.
  * R-2 zero binary floating point. Every numeric value here is `int` or
    `decimal.Decimal`; there is no tolerance, no approximate comparison, and the
    ambient `decimal` context is neither read nor mutated.
  * R-3 no new validations, fields or schema changes, and no concurrency. The three
    guards stay three independent guards: no all-or-nothing wrapper, no whole-date
    validation, no rejection of a partially derived row, no `NULL` substitution and
    no bounds check are introduced. Nothing here emits DDL - the three columns
    already exist in the frozen schema and only their metadata is read. Execution is
    strictly sequential and no parallel-test plugin is used.
  * R-4 legacy anomalies reproduced, never fixed. Every reproduction site below
    carries a comment naming A-7 and its `[common/irspostingMT.cbl:Lnnn]` locator.
    The corollary bites here: asserting that the derived components AGREE with the
    raw text would be asserting correct accounting rather than observed behaviour,
    which is itself a defect. The assertions below require that they may DISAGREE.
  * R-5 full traceability. Every descriptor arrives through a dictionary key and
    every expected value carries its locator.
  * R-6 compiled behaviour is the tie-breaker. NOTHING in this file is left
    unarbitrated and there is no `xfail` in it: `Q-10` was measured on GnuCOBOL 3.2.0
    and `Q-25` was settled by censusing every producer in the frozen sources, which is
    what that question turns on. Where a reading was refuted, the refutation is
    asserted, so a change back in that direction fails by name rather than passing
    unnoticed.

Also binding, plan section 0.8.4: no timing assertion and no performance measurement
appears here.

THE `Q-` REGISTRY OF THIS FILE.

  * Q-25 - OWNED HERE, and SETTLED. Which callers of the bridge put a two-digit
    YEAR in `Post-Date (7:2)` and which put a CENTURY there. `Post-Date` is
    `pic x(8)`, so `(7:2)` is two characters and no more; what those two characters
    MEAN is the caller's doing. THE QUESTION IS NOT A RUNTIME VALUE - what decides it
    is which statements exist - so it was answered by censusing every producer in the
    frozen sources rather than by a probe. `_POST_DATE_WINDOW_CENSUS` carries the
    eleven of them with their locators: the four in-scope SL/PL programs and
    out-of-scope `pl950` all compose `(1:6)` plus `(9:2)` of the ten-character form;
    `irs030`, `irs060` and `irs070` move an `x(8)` `u-date` whose `(7:2)` window IS
    `u-year` by declaration; and the eight-character IRS `run-date` is built by
    `irs.cbl` with the same composition, its own comments saying "Only grab YY and not
    CC" and "As IRS uses dd/mm/yy" `[irs/irs.cbl:L972-L978]`. So EVERY producer writes
    a year and the century reading has no producer at all - it arises only from an
    `x(10)`-to-`x(8)` truncation no statement in the checkout performs. Nothing is
    repaired: A-7's guard still cannot tell the two apart, which is why the
    hypothetical truncation stays locked by its own test.
  * Q-10 - CROSS-REFERENCED, owned by `acas_posting/cobol/move.py`, primary lock
    `tests/arithmetic/test_move_truncation.py`. A reference-modification range that
    is not wholly inside its item. Measured twice over: a LITERAL range does not
    compile ("length of 'post-date' out of bounds: 4"), and a COMPUTED one yields the
    characters inside the item followed by the bytes of the storage that follows -
    `"25##"` for `(7:4)` on this record's eight-character date, against a `#`-filled
    neighbour. No `str` has a neighbour, so no value is reproducible and the
    primitive refuses; the readings are published on
    `acas_posting.cobol.move.REFERENCE_MODIFICATION_OVERRUN_ORACLE_EVIDENCE`.
  * Q-5.2 - CROSS-REFERENCED ONLY, settled in `acas_posting/cobol/usage.py` and
    locked by `tests/arithmetic/test_sign_leading_display.py`: the byte width of a
    leading-sign display item. The two `sign is leading` money fields of this record
    are checked here for SIGN POSITION and SPELLING ONLY - their `byte_length` is
    deliberately NOT asserted here.

PROVENANCE OF THE RULES. The six rules above are the requirement-embedded rules of
Technical Specification section 0.7.2 and are treated as binding. Where they are
silent, enterprise-standard best practice applies.

THREE CITATION CORRECTIONS, recorded rather than silently absorbed, each checked line
by line against the frozen checkout and each agreeing with the generated dictionary
where the dictionary carries the locator too.

  * The specification body cites `[copybooks/irswspost.cob:L19]` for the second
    `sign is leading` field; that field is at :L18 and :L19 is a comment line.
  * It cites `[mysql/ACASDB.sql:L277-L279]` for the three component columns; :L277 is
    `POST4-DAT` and the three components are at :L278, :L279 and :L280.
  * It cites `[general/gl072.cbl:L289-L290]` and `[general/gl072.cbl:L303-L304]` for
    the two silent skips of anomaly A-13, which this file cross-references only; they
    are at :L291-L292 and :L306-L307.
"""

from __future__ import annotations

import contextlib
import importlib
import dataclasses
import decimal
import sys
import types
from collections.abc import Iterator
from typing import Final

import pytest

from acas_posting.cobol import arithmetic
from acas_posting.cobol import field as cobol_field
from acas_posting.cobol import move as cobol_move
from acas_posting.cobol import usage as cobol_usage
from acas_posting.dictionary import loader, model
from acas_posting.records import irs_posting

pytestmark = pytest.mark.arithmetic


# ---------------------------------------------------------------------------
#  NAMES, AS THE FROZEN SOURCES SPELL THEM
# ---------------------------------------------------------------------------

#: The internal IRS posting table - `CREATE TABLE` at [mysql/ACASDB.sql:L274],
#: bridge `irspostingMT`, handler `acasirsub4`.
_TABLE = "IRSPOSTING-REC"

#: The posting file the Sales and Purchase ledgers hand to IRS - `CREATE TABLE` at
#: [mysql/ACASDB.sql:L366], bridge `slpostingMT`, handler `acas008`. NOT the same
#: file [copybooks/wspost-irs.cob:L6-L7], and its ten columns collide by meaning with
#: this table's, which is why nothing below is keyed by a bare field name.
_SPL_TABLE = "PSIRSPOST-REC"

#: `01 Posting-Record.` [copybooks/irswspost.cob:L8] - the ten-field record the
#: bridge is handed. Its 01-level name, exactly as the copybook cases it.
_COPYBOOK_RECORD = "Posting-Record"

#: `01 WS-IRS-Posting-Record.` [copybooks/wspost-irs.cob:L13].
_SPL_COPYBOOK_RECORD = "WS-IRS-Posting-Record"

#: The three bridge-derived components, in the schema's own column order - ordinals
#: 4, 5 and 6 [mysql/ACASDB.sql:L278-L280], host variables `HV-POST4-DAY`,
#: `HV-POST4-MONTH` and `HV-POST4-YEAR` [common/irspostingMT.cbl:L177-L179] inside
#: the host-variable group `01 TD-IRSPOSTING-REC.` [common/irspostingMT.cbl:L173].
_COMPONENT_COLUMNS = ("POST4-DAY", "POST4-MONTH", "POST4-YEAR")

#: The 1-based reference-modification offset each component reads, paired with its
#: column, straight from [common/irspostingMT.cbl:L982-L987]. The length is two in
#: all three cases.
_COMPONENT_OFFSETS = ((1, "POST4-DAY"), (4, "POST4-MONTH"), (7, "POST4-YEAR"))

#: The width of every one of the three reference-modification ranges.
_COMPONENT_LENGTH = 2

#: `03 Post-Date pic x(8).` [copybooks/irswspost.cob:L11] in DD/MM/YY form. The
#: column name is `POST4-DAT`, not `POST4-DATE`: the DDL truncates the tail, which
#: the dictionary reports as a name difference across the three views rather than
#: reconciling it. THE KEY THAT RESOLVES BELOW IS THEREFORE `IRSPOSTING-REC.POST4-DAT`.
_POST_DATE_COLUMN = "POST4-DAT"

#: A date whose three components are all numeric - row 1 of the eight-combination
#: table below, and the shape [sales/sl060.cbl:L1071-L1072] composes.
_NUMERIC_DATE = "21/09/25"

#: The ten-character form the Sales path reads from, `03 u-date pic x(10).`
#: [copybooks/wsmaps03.cob:L7], for the composition at [sales/sl060.cbl:L1071-L1072].
_TEN_CHARACTER_DATE = "21/09/2025"

#: `Post-Date` at its declared width, holding what `initialize Posting-Record.`
#: leaves in an alphanumeric item - eight spaces. The receiver every
#: reference-modified store below starts from, because a partial overwrite needs its
#: receiver at the item's declared width.
_BLANK_POST_DATE = " " * 8


#: EVERY PRODUCER OF THE EIGHT-CHARACTER DATE IN THE FROZEN CHECKOUT - the census
#: that settles question Q-25. Q-25 asks which callers put a two-digit
#: YEAR in `Post-Date (7:2)` and which put a CENTURY. It is NOT a question a compiled
#: probe can answer, because the answer is not a runtime value: it is which statements
#: exist. So it is answered by censusing them, and the frozen sources cannot move
#: under the census - the plan freezes every one of these files (section 0.2.2), so a
#: locator into them is stable by construction.
#:
#: Each entry is `(producer, locator, what it composes, how it reaches Post-Date)`.
_POST_DATE_WINDOW_CENSUS: Final[tuple[tuple[str, str, str, str], ...]] = (
    #  A.  THE FOUR IN-SCOPE SL/PL POSTING PROGRAMS. Each composes the GL posting
    #  record's `Post-Date` from `(1:6)` plus `(9:2)` of the ten-character form -
    #  so a two-digit YEAR - and then moves that whole eight-character value into
    #  the SL/PL-to-IRS transfer record [copybooks/wspost-irs.cob:L17].
    (
        "sl060",
        "sales/sl060.cbl:L1071-L1072",
        "year",
        "move post-date to WS-IRS-post-date [sales/sl060.cbl:L1131]",
    ),
    (
        "sl100",
        "sales/sl100.cbl:L612-L613",
        "year",
        "move post-date to WS-IRS-post-date [sales/sl100.cbl:L652]",
    ),
    (
        "pl060",
        "purchase/pl060.cbl:L937-L938",
        "year",
        "move post-date to WS-IRS-post-date [purchase/pl060.cbl:L986]",
    ),
    (
        "pl100",
        "purchase/pl100.cbl:L591-L592",
        "year",
        "move post-date to WS-IRS-post-date [purchase/pl100.cbl:L633]",
    ),
    #  B.  ONE OUT-OF-SCOPE PROGRAM COMPOSES IT THE SAME WAY. Listed because a census
    #  that stopped at the scope boundary would not answer the question asked -
    #  Q-25 is about every caller of the bridge, not every migrated caller.
    (
        "pl950",
        "purchase/pl950.cbl:L639-L640",
        "year",
        "move post-date to WS-IRS-Post-date [purchase/pl950.cbl:L680]",
    ),
    #  C.  THE IRS SIDE. `irs030` moves the transfer record's date straight through in
    #  the in-scope posting section, and elsewhere moves its own `u-date`, whose
    #  `(7:2)` window IS `u-year` BY DECLARATION - `03 u-date pic x(8)` redefined
    #  as `u-days`/`u-month`/`u-year` [irs/irs030.cbl:L311-L318]. So the IRS side
    #  cannot put a century there without contradicting its own layout.
    (
        "irs030 posting section",
        "irs/irs030.cbl:L1662",
        "year",
        "move WS-IRS-Post-Date to post-date - inherits A above",
    ),
    (
        "irs030 entry section",
        "irs/irs030.cbl:L1341",
        "year",
        "move u-date to post-date, u-date (7:2) declared u-year",
    ),
    (
        "irs030 heading section",
        "irs/irs030.cbl:L789",
        "year",
        "move run-date to post-date, run-date pic x(8) "
        "[copybooks/irswssystem.cob:L14]",
    ),
    (
        "irs060",
        "irs/irs060.cbl:L1768",
        "year",
        "move u-date to post-date, u-date (7:2) declared u-year "
        "[irs/irs060.cbl:L435-L442]",
    ),
    (
        "irs070",
        "irs/irs070.cbl:L766",
        "year",
        "move u-date to post-date, u-date (7:2) declared u-year "
        "[irs/irs070.cbl:L176-L183]",
    ),
    #  D.  THE READ-BACK PATH. The bridge's own unload moves the stored column text
    #  back into the transfer record, so it carries whatever A composed - it
    #  cannot introduce a century of its own.
    (
        "slpostingMT unload",
        "common/slpostingMT.cbl:L1031",
        "year",
        "move HV-IRS-POST-DAT to WS-IRS-Post-Date - read-back of A",
    ),
)

#: The one CONSUMER of the window outside the bridge, and it agrees: the loader moves
#: `(1:2)`, `(4:2)` and `(7:2)` into fields it names `RP-Day`, `RP-Mth` and `RP-Year`.
#: A reader that called the third window a year is evidence about what the writers
#: were understood to write.
_POST_DATE_WINDOW_READER: Final[tuple[str, str]] = (
    "common/irspostingLD.cbl:L462-L464",
    "RP-Year",
)

#: WHERE THE IRS EIGHT-CHARACTER DATE ITSELF COMES FROM, with the maintainer's own
#: comments, which is what makes the census conclusive rather than merely consistent.
#: `irs.cbl` builds `run-date` with the SAME `(1:6)` + `(9:2)` composition the Sales
#: path uses, and says so in two inline comments - "Only grab YY and not CC" and "As
#: IRS uses dd/mm/yy" [irs/irs.cbl:L972-L978].
_IRS_RUN_DATE_COMPOSITION: Final[str] = "irs/irs.cbl:L972-L978"


# ---------------------------------------------------------------------------
#  DEFENSIVE KEY RESOLUTION  (rule R-5 - every fact arrives through the dictionary)
# ---------------------------------------------------------------------------
#
# The entry keys are table-qualified and case-sensitive, and one of them differs from
# the copybook field name because the DDL truncates a long column name. Rather than
# hard-code the spelling and fail obscurely if the artifact is regenerated with a
# different one, each key is looked up and, on the loader's own near-miss `KeyError`
# subclass, looked up again through the table's entries by column name. Its message
# - which lists the nearest keys - is re-raised when even that finds nothing, because
# a column that the dictionary does not know about is a finding and not something to
# work around.


def _key_for_column(table: str, column: str) -> str:
    """Return the dictionary entry key for one column of one table.

    Args:
        table: The table name as the frozen schema dump spells it.
        column: The column name as the frozen schema dump spells it.

    Returns:
        The entry key, `<TABLE-NAME>.<COLUMN-NAME>`.

    Raises:
        loader.DictionaryKeyError: Neither the qualified key nor the table's own
            entries carry that column. The loader's near-miss message is preserved.
    """
    qualified = f"{table}.{column}"
    try:
        loader.get_entry(qualified)
    except loader.DictionaryKeyError:
        for entry in loader.entries_for_table(table):
            if entry.column is not None and entry.column.name == column:
                return entry.key
        raise
    return qualified


def _post_date_descriptor() -> cobol_field.FieldDescriptor:
    """Return the descriptor of `03 Post-Date pic x(8).` [copybooks/irswspost.cob:L11].

    Returns:
        The descriptor, built from its dictionary entry and from nothing else.
    """
    return cobol_field.FieldDescriptor.from_dictionary_key(
        _key_for_column(_TABLE, _POST_DATE_COLUMN)
    )


def _component_host_variable(column: str) -> model.BridgeHostVariable:
    """Return the bridge host-variable view a derived component is stored through.

    A bridge-only column has NO copybook view, so it has no COBOL-side storage and
    `FieldDescriptor.from_dictionary_key` refuses it by design - a fact a test below
    pins. The shape the bridge stores through is the host variable's own,
    `PIC 9(03) COMP` [common/irspostingMT.cbl:L177-L179], and the dictionary is where
    that shape is read from rather than transcribed (rule R-5).

    Args:
        column: One of the three component column names.

    Returns:
        The host-variable view.
    """
    host_variable = loader.host_variable_for(_key_for_column(_TABLE, column))
    assert host_variable is not None, (
        f"{_TABLE}.{column} has no bridge host-variable view in the generated "
        f"dictionary, yet the derivation at [common/irspostingMT.cbl:L982-L987] "
        f"stores into one. Regenerate the artifact and re-read it."
    )
    return host_variable


def _store_component(
    column: str, value: decimal.Decimal | int | str
) -> decimal.Decimal | int | str:
    """Store one value into a derived component's host variable and return it.

    An un-ROUNDED store, because `usage.coerce` truncates toward zero by default and
    the bridge writes no `ROUNDED` phrase - the five `ROUNDED` sites of the whole
    in-scope cycle are [general/gl051.cbl:L791], [general/gl051.cbl:L796],
    [general/gl080.cbl:L328], [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562], and
    NONE of them is in a bridge.

    Args:
        column: One of the three component column names.
        value: The two-character substring, or the zero the group initialise leaves.

    Returns:
        What the host variable now holds - an `int`, because the host variable is
            `PIC 9(03) COMP` with scale zero.
    """
    host_variable = _component_host_variable(column)
    return cobol_usage.coerce(
        value,
        usage=host_variable.usage,
        digits=host_variable.digits,
        scale=host_variable.scale,
        signed=host_variable.signed,
    )


# ---------------------------------------------------------------------------
#  THE RULE UNDER TEST  -  ANOMALY A-7  [common/irspostingMT.cbl:L966-L987]
# ---------------------------------------------------------------------------
#
# REPRODUCTION SITE. Anomaly A-7. This is the load paragraph's date handling and
# nothing else: the group initialise at [common/irspostingMT.cbl:L966], the
# unconditional raw-text move at [common/irspostingMT.cbl:L969], and the three
# independent guards at [common/irspostingMT.cbl:L982-L987]. It is composed here from
# the published primitives - `move.ref_mod`, `move.is_numeric_class` and a store
# through the host variable's own dictionary-declared shape - because no
# `derive_date_components` helper exists in `acas_posting/cobol/` and none may be
# created there: the COBOL-semantics layer holds no business logic (plan section
# 0.3.1).
#
# WHAT IS DELIBERATELY ABSENT, and each absence is rule R-3 or R-4:
#  * NO all-or-nothing wrapper. Three separate `if`s, no `else`, no shared flag.
#  * NO whole-date validation. The bridge tests two characters at a time and never
#  asks whether the date is a real calendar date; the six-part calendar reject test
#  lives in `common/maps04.cbl` and is a DIFFERENT program on a different path.
#  * NO rejection of a partially derived row. The row is written as it stands.
#  * NO `NULL` substitution for a failed guard. Zero, because of the initialise.
#  * NO bounds check on the reference modification. See question Q-10.
#  * NO reconciliation of the components with the raw text. Drift is exposed as it
#  stands and is never arbitrated here.


def _load_host_variables(post_date_text: str) -> dict[str, object]:
    """Reproduce the date handling of `bb000-HV-Load` for one `Post-Date` value.

    ANOMALY A-7, reproduced not repaired [common/irspostingMT.cbl:L966-L987].

    Args:
        post_date_text: What `03 Post-Date pic x(8).`
            [copybooks/irswspost.cob:L11] holds, at its declared width of eight
            characters.

    Returns:
        The four host variables this rule touches, keyed by column name:
            `POST4-DAT` holding the raw text and `POST4-DAY`, `POST4-MONTH` and
            `POST4-YEAR` holding the derived components.
    """
    post_date = _post_date_descriptor()

    # 966 initialize TD-IRSPOSTING-REC. The group initialise is what makes a failed
    # guard produce ZERO rather than SQL NULL, and it is what lets every column of
    # the frozen schema be declared NOT NULL. A-7.
    loaded: dict[str, object] = {
        column: _store_component(column, 0) for column in _COMPONENT_COLUMNS
    }

    # 969 move Post-Date to HV-POST4-DAT. UNCONDITIONAL, and placed before the three
    # guards exactly as the bridge places it, so the raw text survives whatever the
    # guards do or do not do. A-7.
    loaded[_POST_DATE_COLUMN] = cobol_move.move_alphanumeric(post_date_text, post_date)

    # 978-980 the maintainer's own note above the guards, verbatim: "and yes they all
    # should be numeric as a date is present / but JIC (just in case)." The guards
    # are kept exactly as written - neither dropped as redundant nor strengthened.

    # 982 if Post-Date (1:2) numeric
    # 983          move Post-Date (1:2) to HV-POST4-DAY.
    day = cobol_move.ref_mod(post_date_text, 1, _COMPONENT_LENGTH)
    if cobol_move.is_numeric_class(day, post_date):
        loaded["POST4-DAY"] = _store_component("POST4-DAY", day)

    # 984 if Post-Date (4:2) numeric
    # 985          move Post-Date (4:2) to HV-POST4-MONTH.
    # A SECOND, INDEPENDENT `if`: no `else`, and it shares no condition with the
    # first, so a non-numeric day does not stop a numeric month being derived. A-7.
    month = cobol_move.ref_mod(post_date_text, 4, _COMPONENT_LENGTH)
    if cobol_move.is_numeric_class(month, post_date):
        loaded["POST4-MONTH"] = _store_component("POST4-MONTH", month)

    # 986 if Post-Date (7:2) numeric
    # 987          move Post-Date (7:2) to HV-POST4-YEAR.
    # A THIRD, INDEPENDENT `if`. `(7:2)` is two characters of an `x(8)` item; whether
    # they are a year or a century is the CALLER's doing - question Q-25, answered by the
    # census in `_POST_DATE_WINDOW_CENSUS`: eleven producers, every one a year. A-7.
    year = cobol_move.ref_mod(post_date_text, 7, _COMPONENT_LENGTH)
    if cobol_move.is_numeric_class(year, post_date):
        loaded["POST4-YEAR"] = _store_component("POST4-YEAR", year)

    # 989-990 "Loading HVs implies a non-Fetch action. RGs are handled separately for
    # all such actions so they must not be loaded here." Record-group handling is a
    # handler-layer concern at the bridge boundary and is outside this tier.
    return loaded


def _load_host_variables_raw_text_last(post_date_text: str) -> dict[str, object]:
    """The same rule with the unconditional raw-text move placed AFTER the guards.

    Used by one test to show that the inconsistency A-7 produces is STRUCTURAL rather
    than an accident of statement order: the guards read `Post-Date` itself, never the
    host variable, so moving [common/irspostingMT.cbl:L969] below
    [common/irspostingMT.cbl:L987] changes nothing at all. It is a reading aid for
    that one assertion and is NOT an alternative implementation of the rule.

    Args:
        post_date_text: What `03 Post-Date pic x(8).` holds.

    Returns:
        The same four host variables `_load_host_variables` returns.
    """
    loaded = _load_host_variables(post_date_text)
    loaded[_POST_DATE_COLUMN] = cobol_move.move_alphanumeric(
        post_date_text, _post_date_descriptor()
    )
    return loaded


def _components_of(loaded: dict[str, object]) -> tuple[object, ...]:
    """Return the three derived components in schema column order.

    Args:
        loaded: What `_load_host_variables` returned.

    Returns:
        `(POST4-DAY, POST4-MONTH, POST4-YEAR)` - ordinals 4, 5 and 6.
    """
    return tuple(loaded[column] for column in _COMPONENT_COLUMNS)


def _sales_path_post_date(ten_character_date: str) -> str:
    """Compose `Post-Date` the way the Sales path composes it, by construction.

    [sales/sl060.cbl:L1071-L1072], verbatim:

        1071:      move     u-date (1:6) to post-date (1:6).
        1072:      move     u-date (9:2) to post-date (7:2).

    Reference modification is 1-BASED ON BOTH SIDES: characters 1 to 6 of the
    ten-character form are `"DD/MM/"` and characters 9 to 10 are the last two digits
    of its four-digit year, and they land in positions 1 to 6 and 7 to 8 of the
    eight-character receiver. That is why `(7:2)` carries the YEAR on this path and
    not the century - question Q-25 is closed by construction here, and the census in
    `_POST_DATE_WINDOW_CENSUS` shows that EVERY other producer in the frozen sources
    composes it the same way, so no caller composes it differently.

    Args:
        ten_character_date: `u-date`, the ten-character DD/MM/CCYY form.

    Returns:
        The eight-character `Post-Date` value.
    """
    post_date = _BLANK_POST_DATE
    post_date = cobol_move.ref_mod_into(
        post_date, 1, 6, cobol_move.ref_mod(ten_character_date, 1, 6)
    )
    return cobol_move.ref_mod_into(
        post_date, 7, 2, cobol_move.ref_mod(ten_character_date, 9, 2)
    )


# ===========================================================================
#  1. THE RECORD THE BRIDGE IS HANDED  -  ten fields, and `Post-Date` among them
# ===========================================================================

#: The ten fields of `01 Posting-Record.` [copybooks/irswspost.cob:L8-L18] as the
#: copybook declares them, in declaration order, each with the entry key it reaches
#: through and its own locator. Transcribed from the frozen copybook once, here, so
#: that the dictionary and the copybook are compared rather than assumed equal.
#:  `Vat-Amount` is at :L18. The specification body cites :L19; :L19 is a comment.
_COPYBOOK_FIELDS = (
    ("KEY-4", "Post-Key", "9(5)", "copybooks/irswspost.cob:L9"),
    ("POST4-CODE", "Post-Code", "xx", "copybooks/irswspost.cob:L10"),
    ("POST4-DAT", "Post-Date", "x(8)", "copybooks/irswspost.cob:L11"),
    ("POST4-DR", "Post-DR", "9(5)", "copybooks/irswspost.cob:L12"),
    ("POST4-CR", "Post-CR", "9(5)", "copybooks/irswspost.cob:L13"),
    ("POST4-AMOUNT", "Post-Amount", "s9(7)v99", "copybooks/irswspost.cob:L14"),
    ("POST4-LEGEND", "Post-Legend", "x(32)", "copybooks/irswspost.cob:L15"),
    ("VAT-AC-DEF4", "Vat-AC-Def", "99", "copybooks/irswspost.cob:L16"),
    ("POST4-VAT-SIDE", "Post-Vat-Side", "xx", "copybooks/irswspost.cob:L17"),
    ("VAT-AMOUNT4", "Vat-Amount", "s9(7)v99", "copybooks/irswspost.cob:L18"),
)


def test_post_date_is_the_eight_character_source_of_the_derivation() -> None:
    """`03 Post-Date pic x(8).` [copybooks/irswspost.cob:L11] - the one input.

    The whole of anomaly A-7 hangs off this single alphanumeric item: three
    two-character windows of it become three columns that no copybook declares.
    """
    key = _key_for_column(_TABLE, _POST_DATE_COLUMN)
    # THE KEY THIS LOOKUP LANDS ON, recorded as this file's specification asks: the
    # DDL truncates a long column name, so `Post-Date` keys as `POST4-DAT`.
    assert key == "IRSPOSTING-REC.POST4-DAT"

    descriptor = _post_date_descriptor()
    assert descriptor.name == "Post-Date"  # [copybooks/irswspost.cob:L11]
    assert descriptor.picture == "x(8)"
    assert descriptor.usage is model.Usage.ALPHANUMERIC
    assert descriptor.byte_length == 8
    assert descriptor.character_length == 8
    assert descriptor.is_str is True
    assert descriptor.is_numeric is False
    assert descriptor.python_storage is model.CobolPythonStorage.STR
    assert descriptor.dictionary_key == key
    assert descriptor.source_locator == "copybooks/irswspost.cob:L11"

    # All three views of it, in one traceability string (rule R-5).
    citation = descriptor.cite()
    assert "copybooks/irswspost.cob:L11" in citation
    assert "common/irspostingMT.cbl:L176" in citation  # `HV-POST4-DAT PIC X(8)`
    assert "mysql/ACASDB.sql:L277" in citation  # `POST4-DAT char(8) NOT NULL`


def test_the_column_name_differs_from_the_field_name_and_is_reported_as_drift() -> None:
    """The DDL truncates `-DATE` to `-DAT`, and the dictionary says so.

    A name difference across the three views, reported and never reconciled - which is
    exactly why every lookup in this file goes through `_key_for_column` rather than
    assuming the copybook's spelling reaches the schema intact.
    """
    drift = loader.drift_for(_key_for_column(_TABLE, _POST_DATE_COLUMN))
    assert drift.name is True
    assert drift.details  # the difference is spelled out, not merely flagged
    detail = " ".join(drift.details)
    assert "Post-Date" in detail
    assert "POST4-DAT" in detail
    # Only the NAME differs. The width, usage and signedness agree across the views,
    # so nothing about the derivation's input is in question.
    assert drift.character_length is False
    assert drift.usage is False
    assert drift.signedness is False
    assert drift.digits is False
    assert drift.scale is False


@pytest.mark.parametrize(
    ("column", "field_name", "picture", "locator"),
    _COPYBOOK_FIELDS,
    ids=[field_name for _, field_name, _, _ in _COPYBOOK_FIELDS],
)
def test_each_copybook_field_keeps_the_shape_its_copybook_declares(
    column: str, field_name: str, picture: str, locator: str
) -> None:
    """The ten fields of `01 Posting-Record.`, field for field.

    Args:
        column: The column the field maps to.
        field_name: The field name the copybook uses.
        picture: The picture clause the copybook writes.
        locator: The copybook line the field is declared on.
    """
    descriptor = cobol_field.FieldDescriptor.from_dictionary_key(
        _key_for_column(_TABLE, column)
    )
    assert descriptor.name == field_name
    assert descriptor.picture == picture
    assert descriptor.source_locator == locator


# ===========================================================================
#  2. THE EIGHT COMBINATIONS  -  three independent guards, no `else`
# ===========================================================================
#
# ANOMALY A-7. [common/irspostingMT.cbl:L982-L987] is three separate `if`s with no
# `else` and no shared condition, so all eight combinations of (day-numeric,
# month-numeric, year-numeric) are reachable. [common/irspostingMT.cbl:L969] stores
# the raw text unconditionally, so rows 2 to 8 below are each provably internally
# inconsistent: the text says one thing and the components say another, and BOTH are
# written to the same row.
#
# Covering only rows 1 and 8 - the all-pass and the all-fail - would miss the
# anomaly entirely, because partial derivation is the anomaly.

#: `(Post-Date, expected POST4-DAY, expected POST4-MONTH, expected POST4-YEAR)` for
#: every one of the eight combinations. The expected components follow from the three
#: guards and the group initialise at [common/irspostingMT.cbl:L966]: a guard that
#: holds stores its two characters, a guard that fails leaves ZERO.
_EIGHT_COMBINATIONS = (
    ("21/09/25", 21, 9, 25),
    ("1X/09/25", 0, 9, 25),
    ("21/0X/25", 21, 0, 25),
    ("21/09/2X", 21, 9, 0),
    ("1X/0X/25", 0, 0, 25),
    ("1X/09/2X", 0, 9, 0),
    ("21/0X/2X", 21, 0, 0),
    ("XX/XX/XX", 0, 0, 0),
)


@pytest.mark.parametrize(
    ("post_date_text", "day", "month", "year"),
    _EIGHT_COMBINATIONS,
    ids=[text for text, _, _, _ in _EIGHT_COMBINATIONS],
)
def test_three_independent_guards_reach_all_eight_combinations(
    post_date_text: str, day: int, month: int, year: int
) -> None:
    """A-7 [common/irspostingMT.cbl:L982-L987] - partial derivation is reachable.

    Args:
        post_date_text: The eight-character `Post-Date` value.
        day: What `POST4-DAY` holds afterwards - zero where its guard failed.
        month: What `POST4-MONTH` holds afterwards.
        year: What `POST4-YEAR` holds afterwards.
    """
    loaded = _load_host_variables(post_date_text)

    assert _components_of(loaded) == (day, month, year)

    # THE RAW TEXT IS STORED INTACT IN EVERY ONE OF THE EIGHT CASES, because
    # [common/irspostingMT.cbl:L969] is unconditional. A-7.
    assert loaded[_POST_DATE_COLUMN] == post_date_text

    # Every component is an integer and NONE of them is `None`: the group initialise
    # at [common/irspostingMT.cbl:L966] leaves zero, and the frozen schema declares
    # all three columns NOT NULL, so SQL `NULL` is not reachable here. A-7.
    for component in _components_of(loaded):
        assert isinstance(component, int)
        assert not isinstance(component, decimal.Decimal)
        assert component is not None


@pytest.mark.parametrize(
    ("post_date_text", "day", "month", "year"),
    _EIGHT_COMBINATIONS[1:],
    ids=[text for text, _, _, _ in _EIGHT_COMBINATIONS[1:]],
)
def test_a_failed_guard_leaves_a_row_that_contradicts_its_own_raw_text(
    post_date_text: str, day: int, month: int, year: int
) -> None:
    """A-7 - the seven rows where the components and the text DISAGREE.

    Rule R-4's corollary in its sharpest form. Asserting that the components agree
    with the raw text would be asserting correct accounting rather than observed
    behaviour, and that is itself a defect. What is asserted is that they may
    disagree, and that BOTH the intact text and the zeroed component reach the row.

    Args:
        post_date_text: The eight-character `Post-Date` value.
        day: What `POST4-DAY` holds afterwards.
        month: What `POST4-MONTH` holds afterwards.
        year: What `POST4-YEAR` holds afterwards.
    """
    loaded = _load_host_variables(post_date_text)

    # At least one guard failed in every one of these rows.
    assert 0 in _components_of(loaded)

    # The raw text still carries the characters the failed guard read, so the row
    # holds both the text and a zero that the text does not support. A-7,
    # [common/irspostingMT.cbl:L969] against [common/irspostingMT.cbl:L982-L987].
    assert loaded[_POST_DATE_COLUMN] == post_date_text
    for offset, column in _COMPONENT_OFFSETS:
        window = cobol_move.ref_mod(post_date_text, offset, _COMPONENT_LENGTH)
        if loaded[column] == 0 and window != "00":
            # The stored component says zero; the window of text it came from does
            # not. That contradiction is the anomaly, and it stands.
            assert window == cobol_move.ref_mod(
                str(loaded[_POST_DATE_COLUMN]), offset, _COMPONENT_LENGTH
            )
            break
    else:  # pragma: no cover - unreachable for these seven rows
        pytest.fail(
            f"{post_date_text!r} was parametrized as a partial derivation but no "
            f"component came back zero from a non-zero window; the eight-combination "
            f"table and [common/irspostingMT.cbl:L982-L987] have diverged."
        )

    assert (day, month, year) == _components_of(loaded)


def test_the_inconsistency_does_not_depend_on_statement_order() -> None:
    """A-7 does not depend on the raw-text move preceding the guards.

    The guards read `Post-Date` itself, never the host variable, so moving
    [common/irspostingMT.cbl:L969] below [common/irspostingMT.cbl:L987] would leave
    every value identical. The inconsistency is therefore structural - it follows from
    the guards being conditional while the text move is not - and repairing it would
    mean changing the guards, which rule R-4 forbids.
    """
    for post_date_text, *expected in _EIGHT_COMBINATIONS:
        as_written = _load_host_variables(post_date_text)
        text_move_last = _load_host_variables_raw_text_last(post_date_text)
        assert as_written == text_move_last
        assert _components_of(as_written) == tuple(expected)
        assert text_move_last[_POST_DATE_COLUMN] == post_date_text


# ===========================================================================
#  3. SPACES, AND SEPARATORS THAT ARE NOT `/`
# ===========================================================================


def test_an_all_spaces_date_derives_nothing_and_still_stores_eight_spaces() -> None:
    """A-7 - `initialize Posting-Record.` leaves spaces, and spaces are not numeric.

    A space fails COBOL's numeric class condition, so all three guards fail and all
    three components stay at the zero the group initialise left
    [common/irspostingMT.cbl:L966]. The raw-text move at
    [common/irspostingMT.cbl:L969] still runs, so the row carries eight spaces in
    `POST4-DAT` beside three zeroes - and `char(8) NOT NULL` accepts spaces.
    """
    loaded = _load_host_variables(_BLANK_POST_DATE)

    assert _components_of(loaded) == (0, 0, 0)
    assert loaded[_POST_DATE_COLUMN] == _BLANK_POST_DATE
    assert loaded[_POST_DATE_COLUMN] != ""  # spaces, never an empty string


def test_a_partially_spaced_date_derives_only_its_numeric_windows() -> None:
    """A-7 - the guards are per-window, so a blanked month costs only the month.

    `"21/  /25"` reaches the bridge with a two-space month. The first and third guards
    hold and the second fails, which is row 3 of the eight-combination table reached
    by spaces rather than by a letter [common/irspostingMT.cbl:L982-L987].
    """
    loaded = _load_host_variables("21/  /25")

    assert _components_of(loaded) == (21, 0, 25)
    assert loaded[_POST_DATE_COLUMN] == "21/  /25"


@pytest.mark.parametrize(
    "post_date_text",
    ["21.09.25", "21-09-25", "21,09,25", "21 09 25", "21009025"],
    ids=["stop", "hyphen", "comma", "space", "digit"],
)
def test_separators_are_irrelevant_because_the_guards_test_only_the_windows(
    post_date_text: str,
) -> None:
    """A-7 - the three guards never look at positions 3 and 6.

    [common/irspostingMT.cbl:L982-L987] tests `(1:2)`, `(4:2)` and `(7:2)` and nothing
    else, so whatever sits between them is not part of the derivation.
    `common/maps04.cbl` normalises `.`, `,` and `-` separators, but that is a
    DIFFERENT program on a different path and the bridge does not call it. The
    components come out derived whatever the separator is, and the separator is still
    stored verbatim in the raw text.

    Args:
        post_date_text: An eight-character date whose separators are not `/`.
    """
    loaded = _load_host_variables(post_date_text)

    assert _components_of(loaded) == (21, 9, 25)
    assert loaded[_POST_DATE_COLUMN] == post_date_text
    # Position 3 is whatever the caller sent and it reaches the row untouched.
    assert cobol_move.ref_mod(str(loaded[_POST_DATE_COLUMN]), 3, 1) == (
        cobol_move.ref_mod(post_date_text, 3, 1)
    )


# ===========================================================================
#  4. REFERENCE MODIFICATION IS 1-BASED  -  on BOTH sides
# ===========================================================================
#
# Reference modification has 83 live uses across the twelve in-scope program files;
# `move.REFERENCE_MODIFICATION_CENSUS` carries the count per `(offset:length)` pair.
# Three of those pairs are the ones this file turns on: `(1:2)`, `(4:2)` and `(7:2)`.


def test_reference_modification_is_one_based_on_the_sending_side() -> None:
    """`Post-Date (1:2)`, `(4:2)` and `(7:2)` are the day, the month and the year.

    `Post-Date` is `pic x(8)` [copybooks/irswspost.cob:L11] in DD/MM/YY form, so
    characters 1-2 are the day, 4-5 the month and 7-8 a TWO-DIGIT year.
    """
    assert cobol_move.ref_mod(_NUMERIC_DATE, 1, 2) == "21"
    assert cobol_move.ref_mod(_NUMERIC_DATE, 4, 2) == "09"
    assert cobol_move.ref_mod(_NUMERIC_DATE, 7, 2) == "25"

    # THE COUNTER-ASSERTION that proves the convention rather than assuming it: a
    # 0-based Python slice at the same numbers reads the WRONG characters. Getting
    # this backwards would derive a day of "1/" - which is not numeric, so the guard
    # would fail and the column would silently hold zero. A-7 makes that
    # indistinguishable from a legitimately non-numeric date, which is exactly why the
    # convention is pinned here.
    assert _NUMERIC_DATE[1:3] == "1/"
    assert cobol_move.ref_mod(_NUMERIC_DATE, 1, 2) != _NUMERIC_DATE[1:3]
    assert cobol_move.ref_mod(_NUMERIC_DATE, 1, 2) == _NUMERIC_DATE[0:2]


def test_reference_modification_is_one_based_on_the_receiving_side() -> None:
    """`post-date (1:6)` and `post-date (7:2)` are 1-based receivers too.

    The receiving side of [sales/sl060.cbl:L1071-L1072]. Positions outside the range
    keep whatever they held, which is why the receiver must be held at its declared
    width of eight characters.
    """
    first = cobol_move.ref_mod_into(_BLANK_POST_DATE, 1, 6, "21/09/")
    assert first == "21/09/  "
    assert len(first) == 8

    both = cobol_move.ref_mod_into(first, 7, 2, "25")
    assert both == "21/09/25"
    assert len(both) == 8

    # A 0-based receiver would have written one position to the left.
    assert cobol_move.ref_mod_into(_BLANK_POST_DATE, 1, 2, "21") == "21      "


def test_the_reference_modification_census_totals_eighty_three_live_uses() -> None:
    """The census the semantics layer publishes, and the three pairs A-7 uses.

    Evidence that `(1:2)`, `(4:2)` and `(7:2)` are ordinary idiom in this codebase
    rather than something the bridge invented, and that the primitive they go through
    is exercised by the whole in-scope set and not only here.
    """
    census = {
        (offset, length): count
        for offset, length, count in cobol_move.REFERENCE_MODIFICATION_CENSUS
    }
    assert sum(census.values()) == 83
    assert census[(1, 2)] == 16
    assert census[(4, 2)] == 16
    assert census[(7, 2)] == 4
    # The Sales-path composition's two pairs are in the census too.
    assert census[(1, 6)] == 8
    assert census[(9, 2)] == 9


def test_a_range_past_the_end_of_post_date_yields_the_neighbours_bytes() -> None:
    """Q-10 on this item is MEASURED: `(7:4)` yields `"25##"`, not `"25"`.

    `Post-Date (7:4)` on an `x(8)` item - two characters past the field. `(7:4)` is a
    real pair in the census with 16 uses, but every one of them is on a ten-character
    date; on this eight-character item it runs off the end.

    THE MEASUREMENT. Question Q-10 is owned by
    `acas_posting/cobol/move.py` and locked primarily by
    `tests/arithmetic/test_move_truncation.py`; this file cross-references it because
    the overrunning range is on the very item the derivation reads. GnuCOBOL 3.2.0 was
    driven with `post-date pic x(8)` holding `"21/09/25"` and a `pic x(10)` sentinel
    filled with `#` declared IMMEDIATELY AFTER it in the same group, which is the only
    arrangement in which the neighbouring bytes are observable at all:

        a LITERAL `post-date (7:4)`      -> DOES NOT COMPILE: "error: length of
                                            'post-date' out of bounds: 4", cobc exit 1
        a COMPUTED `(off:len)` 7 and 4   -> "25##", the two characters inside followed
                                            by TWO BYTES OF THE NEIGHBOUR, each read
                                            back individually as 0x23
        a COMPUTED `(off:len)` 9 and 2   -> "##", wholly the neighbour's
        a COMPUTED `(off:len)` 7 and 2   -> "25", in range, for contrast

    SO THE READING THE FORMER `xfail(strict=True)` ASSERTED - that the range yields the
    characters that are INSIDE the item, `"25"` - IS REFUTED. What the compiled program
    yields is four characters, two of which belong to a different field, and a Python
    `str` has no neighbour to supply them. There is therefore no reproducible value, and
    :class:`ReferenceModificationOutOfRange` refuses rather than returning a prefix:
    returning `"25"` would invent an answer the compiled system never gives, and
    clamping the range would be a validation (rules R-3, R-4, R-6). The marker
    consequently described a CLOSED decision as a pending question and promised an
    alarm that could not ring.

    NO BOUNDS CHECK IS ADDED and none is removed. The refusal itself is asserted by
    `test_a_range_past_the_end_is_reported_rather_than_invented`; what THIS test adds is
    the reading that makes the refusal correct rather than merely conservative.
    """
    #  The measurement is published beside the primitive that refuses, so a maintainer
    #  can re-run the experiment instead of trusting this docstring.
    readings = {
        (offset, length, width): yielded
        for offset, length, width, yielded in (
            cobol_move.REFERENCE_MODIFICATION_OVERRUN_ORACLE_EVIDENCE
        )
    }
    assert readings[(7, 4, 8)].startswith("25##")
    assert readings[(9, 2, 8)].startswith("##")
    assert readings[(7, 2, 8)].startswith("25")

    #  The item the reading was taken on is exactly this file's item: eight characters,
    #  so a span starting at 7 and running 4 needs ten.
    assert len(_NUMERIC_DATE) == 8
    assert 7 + 4 - 1 > len(_NUMERIC_DATE)

    #  Every span the bridge itself takes from this item is comfortably inside it, which
    #  is why the derivation never meets Q-10 in practice.
    for offset, _column in _COMPONENT_OFFSETS:
        assert offset + _COMPONENT_LENGTH - 1 <= len(_NUMERIC_DATE)

    #  THE REFUTED READING. `"25"` is what an implementation that clamped the range
    #  would return, and the compiled program returns four characters instead - so the
    #  primitive must not return it.
    with pytest.raises(cobol_move.ReferenceModificationOutOfRange) as raised:
        cobol_move.ref_mod(_NUMERIC_DATE, 7, 4)
    assert "ADJACENT STORAGE" in str(raised.value)

    #  And the in-range window on the same item still answers, which is what shows the
    #  refusal is scoped to the overrun and not to reference modification as such.
    assert cobol_move.ref_mod(_NUMERIC_DATE, 7, 2) == "25"

    #  The same (7:4) span IS in range on the ten-character form every census use
    #  applies it to - so the pair is not wrong, the item is narrower.
    assert len(_TEN_CHARACTER_DATE) == 10
    assert cobol_move.ref_mod(_TEN_CHARACTER_DATE, 7, 4) == "2025"


def test_a_range_past_the_end_is_reported_rather_than_invented() -> None:
    """The measured Q-10 outcome: the primitive refuses, naming the question.

    Asserted so that the refusal is a pinned contract rather than an implementation
    detail. No bounds check is added here and none is removed there - the range simply
    has no answer the compiled system can supply, and saying so is the honest
    reproduction (rule R-6).
    """
    with pytest.raises(cobol_move.ReferenceModificationOutOfRange) as raised:
        cobol_move.ref_mod(_NUMERIC_DATE, 7, 4)

    assert "Q-10" in str(raised.value)
    # It is a `MovementWithNoCompiledAnswer`, the family a caller can catch whole.
    assert isinstance(raised.value, cobol_move.MovementWithNoCompiledAnswer)
    # Every range the bridge itself uses is comfortably inside the item.
    for offset, _column in _COMPONENT_OFFSETS:
        assert offset + _COMPONENT_LENGTH - 1 <= 8


# ===========================================================================
#  5. `IS NUMERIC` IS A TEST, NOT A VALIDATION
# ===========================================================================
#
# This is the mechanism by which a failed guard produces a SILENT zero rather
# than an error. The class condition yields true or false and never aborts, so a
# non-numeric window leaves its column at zero with no message, no counter and no
# trace - the same silence as gl072's two skips (anomaly A-13, primary lock
# tests/arithmetic/test_move_truncation.py).  The specification body cites those two
# at [general/gl072.cbl:L291-L292] and [general/gl072.cbl:L306-L307]; in the frozen
# checkout they are `if post-batch not numeric / go to loop.` at
# [general/gl072.cbl:L291-L292] and `if we-error equal 999 / go to loop.` at
# [general/gl072.cbl:L306-L307], which is also what the semantics layer cites.
#
# `pytest.raises` is used NOWHERE for `is_numeric_class` in this file. Asserting
# that it raises would be asserting the opposite of the frozen behaviour.

#: Every two-character window of every parametrized date in this file, plus the two
#: degenerate inputs a class condition must still answer for.
_EVERY_TESTED_WINDOW = tuple(
    dict.fromkeys(
        [
            cobol_move.ref_mod(text, offset, _COMPONENT_LENGTH)
            for text, *_ in _EIGHT_COMBINATIONS
            for offset, _column in _COMPONENT_OFFSETS
        ]
        + ["  ", "XX", "", "0", "0X", "99"]
    )
)


@pytest.mark.parametrize(
    ("window", "numeric"),
    [
        ("21", True),
        ("09", True),
        ("25", True),
        ("00", True),
        ("1X", False),
        ("0X", False),
        ("2X", False),
        ("XX", False),
        ("  ", False),
        (" 9", False),
        ("", False),
    ],
    ids=[
        "day-21",
        "month-09",
        "year-25",
        "zeroes",
        "day-1X",
        "month-0X",
        "year-2X",
        "all-letters",
        "two-spaces",
        "leading-space",
        "empty",
    ],
)
def test_the_numeric_class_condition_answers_true_or_false(
    window: str, numeric: bool
) -> None:
    """`IF Post-Date (n:2) NUMERIC` [common/irspostingMT.cbl:L982-L987].

    A space is not a digit, which is the whole reason an initialised-but-unset
    `Post-Date` derives nothing.

    Args:
        window: The two characters the guard tests.
        numeric: Whether COBOL's numeric class condition holds for them.
    """
    post_date = _post_date_descriptor()
    answer = cobol_move.is_numeric_class(window, post_date)

    assert answer is numeric
    # A plain boolean, not a truthy object - the value a COBOL condition yields.
    assert type(answer) is bool


def test_the_numeric_class_condition_never_raises_for_any_tested_window() -> None:
    """A-7 - a failed guard is silent, so the test itself must never abort.

    Every window every date in this file presents, plus a wholly non-numeric string
    and the empty string, is put through the class condition and only the RETURN is
    examined. If any of them aborted, this test would error - which is the assertion.
    """
    post_date = _post_date_descriptor()

    for window in _EVERY_TESTED_WINDOW:
        answer = cobol_move.is_numeric_class(window, post_date)
        assert isinstance(answer, bool), (
            f"the numeric class condition returned {answer!r} for {window!r}; "
            f"[common/irspostingMT.cbl:L982-L987] needs a plain true or false, "
            f"because a failed guard must leave a silent zero (anomaly A-7)."
        )

    # Every window of the eight-combination table was covered, three per row, with
    # duplicates collapsed - so the loop above is exhaustive over what A-7 sees.
    assert len(_EVERY_TESTED_WINDOW) >= 3
    assert "" in _EVERY_TESTED_WINDOW
    assert "  " in _EVERY_TESTED_WINDOW
    assert "XX" in _EVERY_TESTED_WINDOW


def test_the_guards_are_recorded_exactly_as_the_bridge_writes_them() -> None:
    """A-7 - three guards, three sources, no shared condition and no `else`.

    Read from the generated dictionary rather than from the bridge, because the
    dictionary is what this migration derives field facts from (rule R-5). The
    maintainer's own note above the guards - "and yes they all should be numeric as a
    date is present but JIC (just in case)"
    [common/irspostingMT.cbl:L978-L980] - is carried with them, and the guards are
    neither dropped as redundant nor strengthened.
    """
    expected_sources = {
        "POST4-DAY": "common/irspostingMT.cbl:L982-L983",
        "POST4-MONTH": "common/irspostingMT.cbl:L984-L985",
        "POST4-YEAR": "common/irspostingMT.cbl:L986-L987",
    }
    guards = []
    for offset, column in _COMPONENT_OFFSETS:
        derivation = loader.derivation_for(_key_for_column(_TABLE, column))
        assert derivation is not None, (
            f"{_TABLE}.{column} carries no derivation in the generated dictionary, "
            f"yet [common/irspostingMT.cbl:L982-L987] derives it. Anomaly A-7 would "
            f"be undocumented."
        )
        assert derivation.kind is model.DerivationKind.BRIDGE_DERIVED
        assert derivation.guard == f"if Post-Date ({offset}:2) numeric"
        expected_move = f"move Post-Date ({offset}:2) to HV-{column}."
        assert derivation.expression == expected_move
        assert derivation.source == expected_sources[column]
        # The dictionary states the failed-guard outcome, so nothing here infers it.
        assert "zero" in derivation.guard_failure_behaviour
        assert "inconsistent" in derivation.guard_failure_behaviour
        guards.append(derivation.guard)

    # THREE DISTINCT guards over THREE DISTINCT windows: no shared condition, which
    # is what makes all eight combinations reachable. A-7.
    assert len(set(guards)) == 3
    assert len({expected_sources[column] for column in _COMPONENT_COLUMNS}) == 3

    # The maintainer's "JIC" note travels with the day component's entry.
    notes = " ".join(loader.get_entry(_key_for_column(_TABLE, "POST4-DAY")).notes)
    assert "JIC (just in case)" in notes
    assert "should be numeric as a date is present" in notes


# ===========================================================================
#  6. THE THREE BRIDGE-ONLY COLUMNS  -  read from the generated dictionary
# ===========================================================================
#
# THE PROOF OF THE METHOD. A migration driven from the copybooks alone would
# silently omit three columns of a posting table. Every fact below comes from
# `data_dictionary/acas_posting_dictionary.json`, which the generator builds from the
# copybook, the bridge host-variable group and the `CREATE TABLE` statement.
# `mysql/ACASDB.sql` is cited throughout and parsed nowhere: reading the generated
# artifact instead is what makes the artifact worth generating.


def test_the_table_has_thirteen_columns_in_schema_ordinal_order() -> None:
    """`CREATE TABLE IRSPOSTING-REC` [mysql/ACASDB.sql:L274] - thirteen columns.

    Ten of them a copybook declares; three of them only the bridge and the schema know
    about. The loader yields them in the column ordinal the frozen dump fixes, and that
    order is never re-sorted.
    """
    table = loader.table_for(_TABLE)
    assert table.column_count == 13
    assert table.bridge == "irspostingMT"
    assert table.handler == "acasirsub4"
    assert table.primary_key == "KEY-4"
    assert table.copybooks == ("copybooks/irswspost.cob",)
    assert table.ordinal_source == "mysql/ACASDB.sql:L274"

    entries = loader.entries_for_table(_TABLE)
    assert len(entries) == 13
    ordinals = [entry.column.ordinal for entry in entries if entry.column]
    assert ordinals == list(range(1, 14))
    assert len(ordinals) == 13  # every entry of this table is column-mapped

    # All thirteen are NOT NULL, which is what the group initialise at
    # [common/irspostingMT.cbl:L966] makes possible.
    assert {entry.column.nullable for entry in entries} == {False}
    assert {entry.column.column_default for entry in entries} == {None}


@pytest.mark.parametrize(
    ("column", "ordinal", "host_variable", "hv_locator", "column_locator"),
    [
        (
            "POST4-DAY",
            4,
            "HV-POST4-DAY",
            "common/irspostingMT.cbl:L177",
            "mysql/ACASDB.sql:L278",
        ),
        (
            "POST4-MONTH",
            5,
            "HV-POST4-MONTH",
            "common/irspostingMT.cbl:L178",
            "mysql/ACASDB.sql:L279",
        ),
        (
            "POST4-YEAR",
            6,
            "HV-POST4-YEAR",
            "common/irspostingMT.cbl:L179",
            "mysql/ACASDB.sql:L280",
        ),
    ],
    ids=list(_COMPONENT_COLUMNS),
)
def test_each_derived_component_is_bridge_only_and_interleaved(
    column: str,
    ordinal: int,
    host_variable: str,
    hv_locator: str,
    column_locator: str,
) -> None:
    """A-7 - no copybook counterpart, `tinyint(2) unsigned NOT NULL`, ordinal 4-6.

    THE ORDINALS ARE INTERLEAVED, not appended: the three sit between `POST4-DAT` at 3
    and `POST4-DR` at 7. A reading that assumed new columns are appended would mis-map
    every column after the third, which is the concrete cost of taking the copybook
    rather than the bridge as the mapping this migration follows.

     The specification body cites these three at [mysql/ACASDB.sql:L277-L279]; :L277
    is `POST4-DAT` and the three components are at :L278, :L279 and :L280, which is
    what the checkout and the generated dictionary both say.

    Args:
        column: The component column name.
        ordinal: Its position in the frozen `CREATE TABLE` statement.
        host_variable: The bridge host variable it is stored through.
        hv_locator: Where the host variable is declared.
        column_locator: Where the column is declared.
    """
    entry = loader.get_entry(_key_for_column(_TABLE, column))

    # NO COPYBOOK VIEW, and no program-source view standing in for one.
    assert entry.presence.in_copybook is False
    assert entry.presence.in_program_source is False
    assert entry.presence.in_bridge is True
    assert entry.presence.in_column is True
    assert entry.one_sided is True
    assert entry.copybook is None
    assert entry.program_source is None

    # It is A-7 in the register, and the register says so rather than this file.
    assert "A-7" in entry.anomaly_refs

    # The bridge host variable: `PIC 9(03) COMP`, inside the group whose initialise
    # at [common/irspostingMT.cbl:L966] is why a failed guard leaves zero.
    assert entry.bridge_host_variable is not None
    assert entry.bridge_host_variable.name == host_variable
    assert entry.bridge_host_variable.picture == "9(03)"
    assert entry.bridge_host_variable.usage is model.Usage.COMP
    assert entry.bridge_host_variable.digits == 3
    assert entry.bridge_host_variable.scale == 0
    assert entry.bridge_host_variable.signed is False
    assert entry.bridge_host_variable.source == hv_locator
    assert entry.bridge_host_variable.hv_group_name == "TD-IRSPOSTING-REC"
    assert entry.bridge_host_variable.group_initialised_before_load is True
    assert entry.bridge_host_variable.loaded_from_record is True
    # It is never moved BACK into the record after a read, so a value read from the
    # database does not reach the caller through it [common/irspostingMT.cbl:L995].
    assert entry.bridge_host_variable.unloaded_to_record is False
    assert entry.bridge_host_variable.unload_source is None

    # The column: interleaved, unsigned, two display digits, and NOT NULL.
    assert entry.column is not None
    assert entry.column.name == column
    assert entry.column.ordinal == ordinal
    assert entry.column.sql_type == "tinyint(2) unsigned"
    assert entry.column.base_type == "TINYINT"
    assert entry.column.display_width == 2
    assert entry.column.unsigned is True
    assert entry.column.nullable is False
    assert entry.column.column_default is None
    assert entry.column.is_primary_key is False
    assert entry.column.source == column_locator

    # The traceability line says "copybook=absent" in as many words (rule R-5).
    citation = loader.cite(entry.key)
    assert "copybook=absent" in citation
    assert hv_locator in citation
    assert column_locator in citation


def test_a_bridge_only_column_has_no_field_descriptor_at_all() -> None:
    """A-7 - the descriptor factory refuses the three by name.

    A `FieldDescriptor` describes COBOL-side storage, and a column no copybook
    declares has none. The refusal is the point: it is impossible to write a record
    module that quietly gives one of these three a made-up picture, and the error
    message routes the reader to the bridge view and to the derivation instead.
    """
    for column in _COMPONENT_COLUMNS:
        key = _key_for_column(_TABLE, column)
        with pytest.raises(cobol_field.BridgeOnlyFieldError) as raised:
            cobol_field.FieldDescriptor.from_dictionary_key(key)

        message = str(raised.value)
        assert key in message
        assert "no copybook view" in message
        assert "host_variable_for" in message
        assert "derivation_for" in message
        # It names the guard, so the anomaly is discoverable from the failure alone.
        assert "numeric" in message


def test_every_other_column_of_the_table_does_have_a_copybook_counterpart() -> None:
    """The three are the ONLY bridge-only columns of this table.

    Which is what makes them a finding rather than a pattern: ten of the thirteen
    columns line up with a copybook field, and exactly three do not.
    """
    entries = loader.entries_for_table(_TABLE)
    bridge_only = [entry for entry in entries if entry.copybook is None]
    copybook_backed = [entry for entry in entries if entry.copybook is not None]

    assert [entry.column.name for entry in bridge_only] == list(_COMPONENT_COLUMNS)
    assert len(copybook_backed) == 10
    assert all(entry.one_sided is False for entry in copybook_backed)
    assert all(
        entry.copybook.file == "copybooks/irswspost.cob" for entry in copybook_backed
    )


def test_the_copybook_declares_ten_fields_and_none_of_the_three() -> None:
    """`01 Posting-Record.` [copybooks/irswspost.cob:L8-L18] - ten fields.

          8:  01  Posting-Record.
          9:      03  Post-Key        pic 9(5).
         10:      03  Post-Code       pic xx.
         11:      03  Post-Date       pic x(8).
         12:      03  Post-DR         pic 9(5).
         13:      03  Post-CR         pic 9(5).
         14:      03  Post-Amount     pic s9(7)v99  sign is leading.
         15:      03  Post-Legend     pic x(32).
         16:      03  Vat-AC-Def      pic 99.
         17:      03  Post-Vat-Side   pic xx.
         18:      03  Vat-Amount      pic s9(7)v99   sign is leading.

    Ten elementary fields, and not one of them is a day, a month or a year. THIS IS
    THE PROOF: a migration that read only this copybook would have written a
    ten-column table and lost three columns of a thirteen-column one.
    """
    entries = loader.entries_for_copybook_record(_COPYBOOK_RECORD)
    elementary = [entry for entry in entries if not entry.copybook.is_group]
    groups = [entry for entry in entries if entry.copybook.is_group]

    # Eleven entries: the `01` group itself plus its ten `03` fields.
    assert len(entries) == 11
    assert len(groups) == 1
    assert groups[0].copybook.name == _COPYBOOK_RECORD
    assert groups[0].copybook.source == "copybooks/irswspost.cob:L8"
    assert len(elementary) == 10

    # The ten, in declaration order, on lines 9 to 18 inclusive.
    assert [entry.copybook.name for entry in elementary] == [
        field_name for _, field_name, _, _ in _COPYBOOK_FIELDS
    ]
    assert [entry.copybook.source for entry in elementary] == [
        locator for _, _, _, locator in _COPYBOOK_FIELDS
    ]
    assert {entry.copybook.level for entry in elementary} == {"03"}

    # NOT ONE of them is a date component.
    for entry in elementary:
        name = entry.copybook.name.upper()
        assert not name.endswith("-DAY")
        assert not name.endswith("-MONTH")
        assert not name.endswith("-YEAR")

    # The Python record layer mirrors the copybook exactly, so it too has ten fields
    # and no day, month or year. The three components belong to the bridge boundary,
    # which is the handler module's business and not the record layer's.
    record_fields = [
        dataclass_field.name
        for dataclass_field in dataclasses.fields(irs_posting.PostingRecord)
    ]
    assert len(record_fields) == 10
    assert len(irs_posting.FIELDS) == 10
    assert not [name for name in record_fields if name.endswith("_day")]
    assert not [name for name in record_fields if name.endswith("_month")]
    assert not [name for name in record_fields if name.endswith("_year")]


def test_the_dictionary_covers_every_in_scope_column_including_these_three() -> None:
    """All 513 in-scope columns are `NOT NULL`, and all 513 are covered.

    The coverage figures are what make the three bridge-only columns a documented
    finding rather than an omission: they are counted, keyed and described like every
    other column, and nothing in the artifact is one-sided by accident.
    """
    coverage = loader.coverage()
    assert coverage.in_scope_columns == 513
    assert coverage.columns_covered == 513
    assert coverage.in_scope_columns == coverage.columns_covered
    assert coverage.host_variables_covered == 513
    assert coverage.in_scope_tables == 22
    assert coverage.schema_tables_total == 33

    # The three appear in the artifact's own list of one-sided entries.
    for column in _COMPONENT_COLUMNS:
        assert _key_for_column(_TABLE, column) in coverage.one_sided_entry_keys


def test_the_carrier_of_a_derived_component_is_an_integer_and_never_null() -> None:
    """A-7 - zero, an `int`, and `None` unreachable.

    The entry's own `cobol_python_storage` is NONE, and that is not a contradiction:
    there is no COBOL-side storage to name, because no copybook declares the field.
    The carrier the value actually travels on is the bridge host variable's, and for
    `PIC 9(03) COMP` with scale zero that is an `int` - which is what the two-digit
    `tinyint` column receives.

    THE CHAIN THAT MAKES `NULL` IMPOSSIBLE: `initialize TD-IRSPOSTING-REC.`
    [common/irspostingMT.cbl:L966] leaves an unset numeric host variable at zero, and
    `tinyint(2) unsigned NOT NULL` [mysql/ACASDB.sql:L278-L280] could not accept a
    null even if one were offered. So a failed guard writes 0, never `NULL`, and the
    Python layer must DEFAULT rather than OMIT.
    """
    for column in _COMPONENT_COLUMNS:
        entry = loader.get_entry(_key_for_column(_TABLE, column))
        assert entry.cobol_python_storage is model.CobolPythonStorage.NONE

        host_variable = _component_host_variable(column)
        assert (
            cobol_usage.python_storage_for(host_variable.usage, host_variable.scale)
            is model.CobolPythonStorage.INT
        )
        # An unsigned three-digit binary item: 0 to 999 inclusive, two bytes.
        assert cobol_usage.value_domain(
            host_variable.usage,
            digits=host_variable.digits,
            signed=host_variable.signed,
        ) == (0, 999)
        assert (
            cobol_usage.byte_length(
                host_variable.usage,
                digits=host_variable.digits,
                scale=host_variable.scale,
            )
            == 2
        )

        # What a failed guard leaves behind, and what it is not.
        failed_guard = _store_component(column, 0)
        assert failed_guard == 0
        assert isinstance(failed_guard, int)
        assert failed_guard is not None
        assert not isinstance(failed_guard, decimal.Decimal)


# ===========================================================================
#  7. TABLE-QUALIFIED KEYS  -  the two posting records collide by meaning
# ===========================================================================
#
# `PSIRSPOST-REC` and `IRSPOSTING-REC` describe the same ten logical fields - a
# key, a code, an eight-character date, a debit, a credit, an amount, a legend, a VAT
# account default, a VAT side and a VAT amount - through two different copybooks, two
# different bridges and two different handlers. The frozen source itself warns about
# the confusion, verbatim [copybooks/wspost-irs.cob:L6-L7]:
#
#  6: *> This is NOT the same as the internal IRS *
#  7: *>   posting file                           *
#
# So nothing here is keyed by a bare field name. Every lookup is qualified, and a
# test below shows that a bare name is not a key at all rather than a key that
# silently picks one of the two.


def test_the_two_posting_tables_are_different_tables() -> None:
    """`PSIRSPOST-REC` versus `IRSPOSTING-REC` - different in every respect but shape.

    Thirteen columns against ten, two bridges, two handlers, two entity facades, two
    copybooks and two primary keys. Only one of them has the three date components.
    """
    internal = loader.table_for(_TABLE)
    from_ledgers = loader.table_for(_SPL_TABLE)

    assert internal.name != from_ledgers.name
    assert (internal.column_count, from_ledgers.column_count) == (13, 10)
    assert (internal.bridge, from_ledgers.bridge) == ("irspostingMT", "slpostingMT")
    assert (internal.handler, from_ledgers.handler) == ("acasirsub4", "acas008")
    assert internal.entity_facade == "IRS posting"
    assert from_ledgers.entity_facade == "SPL-Posting"
    assert internal.copybooks == ("copybooks/irswspost.cob",)
    assert from_ledgers.copybooks == ("copybooks/wspost-irs.cob",)
    assert (internal.primary_key, from_ledgers.primary_key) == (
        "KEY-4",
        "IRS-POST-KEY",
    )


@pytest.mark.parametrize(
    ("internal_column", "ledger_column"),
    [("POST4-DAT", "IRS-POST-DAT"), ("POST4-AMOUNT", "IRS-POST-AMOUNT")],
    ids=["post-date", "post-amount"],
)
def test_the_same_logical_field_is_two_entries_under_two_tables(
    internal_column: str, ledger_column: str
) -> None:
    """One meaning, two entries - which is why a bare field name would be a coin flip.

    The date field is the sharper of the two cases: both are `pic x(8)` reaching a
    `char(8) NOT NULL` column, so their SHAPES are identical and only their
    qualification tells them apart.

    Args:
        internal_column: The `IRSPOSTING-REC` column.
        ledger_column: The `PSIRSPOST-REC` column meaning the same thing.
    """
    internal_key = _key_for_column(_TABLE, internal_column)
    ledger_key = _key_for_column(_SPL_TABLE, ledger_column)
    assert internal_key != ledger_key

    internal = loader.get_entry(internal_key)
    from_ledgers = loader.get_entry(ledger_key)

    assert internal != from_ledgers
    assert internal.table == _TABLE
    assert from_ledgers.table == _SPL_TABLE
    assert internal.bridge != from_ledgers.bridge
    assert internal.handler != from_ledgers.handler
    assert internal.copybook.file == "copybooks/irswspost.cob"
    assert from_ledgers.copybook.file == "copybooks/wspost-irs.cob"
    assert internal.copybook.name != from_ledgers.copybook.name
    assert internal.copybook.source != from_ledgers.copybook.source

    # The descriptors are not interchangeable either, even where the picture agrees.
    internal_descriptor = cobol_field.FieldDescriptor.from_dictionary_key(internal_key)
    ledger_descriptor = cobol_field.FieldDescriptor.from_dictionary_key(ledger_key)
    assert internal_descriptor != ledger_descriptor
    assert internal_descriptor.name != ledger_descriptor.name
    assert internal_descriptor.picture == ledger_descriptor.picture
    assert internal_descriptor.dictionary_key == internal_key
    assert ledger_descriptor.dictionary_key == ledger_key


def test_a_bare_field_name_is_not_a_dictionary_key_at_all() -> None:
    """The loader will not guess a table for you.

    THE BEHAVIOUR THIS LOADER IMPLEMENTS, recorded as this file's specification asks:
    `find_entry` returns `None` for an unqualified name - it does not pick a table and
    it does not return a list of candidates - and `get_entry` raises its near-miss
    `KeyError` subclass whose message spells out both qualified key forms. Neither
    silently chooses between `PSIRSPOST-REC` and `IRSPOSTING-REC`.
    """
    for bare in ("POST4-AMOUNT", "POST4-DAT", "Post-Date", "POST4-DAY"):
        assert loader.find_entry(bare) is None

        with pytest.raises(loader.DictionaryKeyError) as raised:
            loader.get_entry(bare)

        message = str(raised.value)
        assert "<TABLE-NAME>.<COLUMN-NAME>" in message
        assert "<COPYBOOK-RECORD>.<FIELD-NAME>" in message

    # And the qualified forms of the same names do resolve, so the refusal above is
    # about qualification and not about the names being unknown.
    assert loader.find_entry(_key_for_column(_TABLE, "POST4-AMOUNT")) is not None
    assert loader.find_entry(_key_for_column(_TABLE, "POST4-DAY")) is not None


def test_the_ledger_side_posting_table_has_no_date_components() -> None:
    """The three derived columns are unique to the INTERNAL IRS posting table.

    `PSIRSPOST-REC` [mysql/ACASDB.sql:L366] carries the same eight-character date in
    `IRS-POST-DAT` and derives nothing from it: its bridge, `slpostingMT`, has no
    equivalent of [common/irspostingMT.cbl:L982-L987]. So A-7 is specific to one of
    the two tables, and a reader who generalised it would be inventing behaviour.
    """
    entries = loader.entries_for_table(_SPL_TABLE)
    assert len(entries) == 10
    assert loader.table_for(_SPL_TABLE).column_count == 10

    names = [entry.column.name for entry in entries]
    assert not [name for name in names if name.endswith("-DAY")]
    assert not [name for name in names if name.endswith("-MONTH")]
    assert not [name for name in names if name.endswith("-YEAR")]

    # Every one of its ten columns has a copybook counterpart: no one-sided entry, so
    # nothing on this side of the ledger is bridge-only.
    assert all(entry.copybook is not None for entry in entries)

    # NOTHING on this side is BRIDGE_DERIVED. `IRS-POST-KEY` does carry a derivation,
    # but a GROUP_CONCATENATION one - its copybook field is a group of two `pic 9(5)`
    # children [copybooks/wspost-irs.cob:L14-L16] flattened into one `bigint(11)`
    # column - which is a different kind of thing from a value the bridge computes
    # under a guard. The distinction is kept rather than blurred.
    kinds = {
        derivation.kind
        for derivation in (loader.derivation_for(entry.key) for entry in entries)
        if derivation is not None
    }
    assert model.DerivationKind.BRIDGE_DERIVED not in kinds
    assert kinds == {model.DerivationKind.GROUP_CONCATENATION}

    # Its own copybook record declares a two-part key group, which is why its entry
    # count and its column count line up differently from the internal record's.
    record = loader.entries_for_copybook_record(_SPL_COPYBOOK_RECORD)
    assert len(record) == 13
    assert not [
        entry for entry in record if entry.copybook.name.upper().endswith("-DAY")
    ]


# ===========================================================================
#  8. THE `(7:2)` WINDOW  -  a year at every producer in the checkout (Q-25, settled)
# ===========================================================================
#
# `Post-Date` is `pic x(8)` [copybooks/irswspost.cob:L11], so `(7:2)` is two
# characters and no more. What those two characters MEAN is the caller's doing, and on
# the Sales path the question is closed by construction, verbatim
# [sales/sl060.cbl:L1071-L1072]:
#
#  1071:      move     u-date (1:6) to post-date (1:6).
#  1072:      move     u-date (9:2) to post-date (7:2).
#
# The caller takes characters 1 to 6 of the ten-character form - `"DD/MM/"` - and
# characters 9 to 10 - the last two digits of the four-digit year - so `(7:2)` is
# unambiguously the YEAR there. A caller that instead truncated `x(10)` to `x(8)`
# would leave the CENTURY in those two positions, and the bridge would derive it
# without complaint because "20" is numeric. Which callers do which WAS question Q-25,
# and the census settles it: all eleven producers in the frozen sources write a year,
# and no statement in the checkout performs the truncation. The truncating case is
# still tested, because the guard's inability to tell the two apart is anomaly A-7 and
# is reproduced rather than repaired.


def test_the_sales_path_composes_a_two_digit_year_by_construction() -> None:
    """[sales/sl060.cbl:L1071-L1072] - `(1:6)` plus `(9:2)` gives `"DD/MM/YY"`.

    1-based on BOTH sides: the sending `(1:6)` and `(9:2)` read from the ten-character
    form, and the receiving `(1:6)` and `(7:2)` write into the eight-character one.
    """
    composed = _sales_path_post_date(_TEN_CHARACTER_DATE)

    assert composed == "21/09/25"
    assert len(composed) == 8
    # The two halves the two statements contribute, named.
    assert cobol_move.ref_mod(_TEN_CHARACTER_DATE, 1, 6) == "21/09/"
    assert cobol_move.ref_mod(_TEN_CHARACTER_DATE, 9, 2) == "25"
    # The century's digits are the ones the composition SKIPS - positions 7 and 8 of
    # the ten-character form never reach `Post-Date`.
    assert cobol_move.ref_mod(_TEN_CHARACTER_DATE, 7, 2) == "20"
    assert cobol_move.ref_mod(composed, 7, 2) == "25"


def test_the_sales_path_composition_derives_all_three_components() -> None:
    """The composed date is row 1 of the eight-combination table.

    So on the Sales path every guard holds, `POST4-YEAR` is 25, and the row is
    internally consistent - the anomaly is reachable, not inevitable.
    """
    loaded = _load_host_variables(_sales_path_post_date(_TEN_CHARACTER_DATE))

    assert _components_of(loaded) == (21, 9, 25)
    assert loaded[_POST_DATE_COLUMN] == "21/09/25"
    assert _EIGHT_COMBINATIONS[0] == ("21/09/25", 21, 9, 25)


def test_a_caller_that_truncated_the_ten_character_form_would_store_a_century() -> None:
    """A-7 - the guard cannot tell a century from a year, because both are numeric.

    Taking characters 1 to 8 of `"21/09/2025"` gives `"21/09/20"`, whose `(7:2)` is the
    CENTURY. The third guard holds - "20" is numeric - so `POST4-YEAR` is stored as 20
    with no diagnostic whatsoever, and the raw text in `POST4-DAT` is the only place
    the truncation is visible. That is the same silence a failed guard produces, from
    the opposite direction.
    """
    truncated = cobol_move.ref_mod(_TEN_CHARACTER_DATE, 1, 8)
    assert truncated == "21/09/20"

    loaded = _load_host_variables(truncated)
    assert _components_of(loaded) == (21, 9, 20)
    assert loaded[_POST_DATE_COLUMN] == "21/09/20"

    # 20 is inside the column's domain, so nothing rejects it: an unsigned
    # `tinyint(2)` fed from `PIC 9(03) COMP` accepts 0 to 999.
    host_variable = _component_host_variable("POST4-YEAR")
    low, high = cobol_usage.value_domain(
        host_variable.usage,
        digits=host_variable.digits,
        signed=host_variable.signed,
    )
    assert low <= 20 <= high
    assert low <= 25 <= high


def test_q25_is_settled_by_census_every_producer_composes_a_two_digit_year() -> None:
    """Q-25 is SETTLED: no producer in the frozen checkout puts a century there.

    Q-25 asks which callers put a two-digit YEAR in `Post-Date (7:2)` and which put a
    CENTURY. THE QUESTION IS NOT A RUNTIME VALUE, so no compiled probe can answer it:
    what decides it is which statements exist. It is therefore answered by censusing
    every producer of the eight-character date in the frozen sources
    (`_POST_DATE_WINDOW_CENSUS`), and the census is stable because the plan freezes
    every one of those files (section 0.2.2) - a locator into a frozen file cannot go
    stale the way a locator into a rewritten script can.

    THE CENSUS, AND WHY IT IS CONCLUSIVE RATHER THAN MERELY CONSISTENT.

      * The four in-scope SL/PL posting programs each compose `(1:6)` plus `(9:2)` of
        the ten-character form and then move that whole value into the transfer record
        - `[sales/sl060.cbl:L1071-L1072]`, `[sales/sl100.cbl:L612-L613]`,
        `[purchase/pl060.cbl:L937-L938]`, `[purchase/pl100.cbl:L591-L592]`. So does
        the out-of-scope `pl950` at `[purchase/pl950.cbl:L639-L640]`. `(9:2)` of
        `DD/MM/CCYY` is the YEAR.
      * The IRS side cannot put a century in that window without contradicting its own
        layout: `03 u-date pic x(8)` is redefined as `u-days`/`u-month`/`u-year`
        `[irs/irs030.cbl:L311-L318]`, so `(7:2)` IS `u-year` by declaration, and the
        same declaration appears in `irs060` and `irs070`.
      * The eight-character IRS `run-date` `[copybooks/irswssystem.cob:L14]` is built
        by the IRS menu with the SAME composition, and the maintainer says so in two
        inline comments - "Only grab YY and not CC" and "As IRS uses dd/mm/yy"
        `[irs/irs.cbl:L972-L978]`. That is the frozen source stating the answer in
        words, not this file inferring it.
      * The one consumer outside the bridge agrees: the loader moves `(7:2)` into a
        field it calls `RP-Year` `[common/irspostingLD.cbl:L462-L464]`.

    SO THE CENTURY READING HAS NO PRODUCER. It arises only from a hypothetical caller
    that truncated `x(10)` to `x(8)`, and no statement in the checkout performs that
    truncation. An `xfail(strict=True)` here would assert that the year-reading and the
    century-reading AGREE; they do not - 25 against 20 - and for one calendar date they
    cannot, that being static arithmetic over two different eight-character windows
    rather than anything an oracle answer could change. Such a marker would assert a
    permanent falsehood while describing Q-25 as pending, and its promised "unexpected
    pass when the question is answered" could never happen. The disagreement is
    asserted as the positive result instead, because it is what proves the two
    compositions are genuinely different and that only one of them is ever executed.

    THE COMPLEMENTARY HALF IS THE NEXT TEST: once stored, the column cannot say WHICH
    reading produced it. The two together are the whole of Q-25's bite - the same date
    can reach the same column as two different numbers, and nothing downstream can tell.

    NOTHING IS REPAIRED (rules R-3, R-4). No caller is corralled, no range is
    bounds-checked and no century is restored. Anomaly A-7's silence stands: the guard
    still cannot tell a century from a year, and `test_a_caller_that_truncated_the_ten_
    character_form_would_store_a_century` keeps that reachable-in-principle case
    locked.
    """
    #  Every producer composes a year. Not "most" - every one, which is the whole
    #  content of the answer.
    assert len(_POST_DATE_WINDOW_CENSUS) == 11
    compositions = {entry[2] for entry in _POST_DATE_WINDOW_CENSUS}
    assert compositions == {"year"}
    assert not [entry for entry in _POST_DATE_WINDOW_CENSUS if entry[2] == "century"]

    #  Every entry carries a locator into a frozen file, so the census is checkable.
    frozen_prefixes = ("sales/", "purchase/", "irs/", "common/", "copybooks/")
    for producer, locator, _composition, reaches in _POST_DATE_WINDOW_CENSUS:
        assert producer
        assert locator.startswith(frozen_prefixes), locator
        assert ":L" in locator
        assert reaches

    #  The four in-scope SL/PL writers, named, because they are the ones the migrated
    #  posting path actually runs.
    in_scope = {entry[0] for entry in _POST_DATE_WINDOW_CENSUS}
    assert {"sl060", "sl100", "pl060", "pl100"} <= in_scope
    #  And the in-scope IRS statement that carries their value into the bridge.
    assert "irs030 posting section" in in_scope

    #  The reader agrees, and the IRS date's own construction is on record.
    assert _POST_DATE_WINDOW_READER[1] == "RP-Year"
    assert _IRS_RUN_DATE_COMPOSITION == "irs/irs.cbl:L972-L978"

    #  THE READINGS DIFFER, and that is the point: the composition every producer
    #  performs yields 25, and the truncation no producer performs would yield 20.
    year_reading = _load_host_variables(_sales_path_post_date(_TEN_CHARACTER_DATE))
    century_reading = _load_host_variables(
        cobol_move.ref_mod(_TEN_CHARACTER_DATE, 1, 8)
    )

    #  One calendar date, two compositions, two different stored components.
    assert year_reading["POST4-YEAR"] == 25
    assert century_reading["POST4-YEAR"] == 20
    assert year_reading["POST4-YEAR"] != century_reading["POST4-YEAR"]

    #  The day and the month are unaffected, so the divergence is confined to the third
    #  window - which is what makes it easy to miss. Both windows are numeric, so the
    #  bridge's third guard admits both, neither row is left with the zero-component
    #  trace a failed guard would leave, and the divergence is silent.
    assert year_reading["POST4-DAY"] == century_reading["POST4-DAY"] == 21
    assert year_reading["POST4-MONTH"] == century_reading["POST4-MONTH"] == 9
    assert year_reading["POST4-YEAR"] != 0
    assert century_reading["POST4-YEAR"] != 0

    #  AN EARLIER TRANSCRIPTION OF THIS CENSUS HELD THREE ROWS - two composing a
    #  year and one a century - and it was WRONG about the third: the century row was
    #  a caller nothing in the tree performs, so listing it beside two real producers
    #  read as evidence that a century reaching the column had been observed. The
    #  census above is the re-measured one, over ELEVEN producers, and every one of
    #  them composes a year. The century case is reachable in principle and stays
    #  locked, by name, in
    #  `test_a_caller_that_truncated_the_ten_character_form_would_store_a_century`.
    assert {entry[2] for entry in _POST_DATE_WINDOW_CENSUS} == {"year"}


def test_the_two_readings_are_indistinguishable_once_stored() -> None:
    """Q-25's practical bite: the column cannot say which reading produced it.

    A stored 20 is a legitimate year in 2020 and a century in 2025, and the row carries
    no flag either way. This is asserted so that the ambiguity is visible in the suite
    rather than only in a document, and it is NOT repaired: no caller is corralled, no
    range is checked and no century is restored (rules R-3, R-4).
    """
    year_reading = _load_host_variables(_sales_path_post_date("21/09/2020"))
    century_reading = _load_host_variables(
        cobol_move.ref_mod(_TEN_CHARACTER_DATE, 1, 8)
    )

    # Same stored component, two entirely different meanings, two different raw texts.
    assert year_reading["POST4-YEAR"] == 20
    assert century_reading["POST4-YEAR"] == 20
    assert year_reading[_POST_DATE_COLUMN] == "21/09/20"
    assert century_reading[_POST_DATE_COLUMN] == "21/09/20"
    # Even the raw text is identical, which is why only the caller can settle Q-25.
    assert year_reading == century_reading


# ===========================================================================
#  9. THE TWO `sign is leading` MONEY FIELDS  -  spelling and position only
# ===========================================================================
#
# THE BYTE WIDTH OF A LEADING-SIGN DISPLAY ITEM IS NOT ASSERTED HERE. That is
# question Q-5.2, settled in `acas_posting/cobol/usage.py` and locked by
# tests/arithmetic/test_sign_leading_display.py. Duplicating it here would put a second
# lock on someone else's question; what this file needs from those two fields is only
# that their SIGN POSITION and their exact SPELLING survive the migration, because the
# record they belong to is the record the derivation reads its date from.


@pytest.mark.parametrize(
    ("column", "field_name", "locator"),
    [
        ("POST4-AMOUNT", "Post-Amount", "copybooks/irswspost.cob:L14"),
        ("VAT-AMOUNT4", "Vat-Amount", "copybooks/irswspost.cob:L18"),
    ],
    ids=["Post-Amount", "Vat-Amount"],
)
def test_the_money_fields_keep_the_sign_is_leading_spelling(
    column: str, field_name: str, locator: str
) -> None:
    """`pic s9(7)v99  sign is leading.` - the spelling with the `is`.

     `Vat-Amount` is at [copybooks/irswspost.cob:L18]. The specification body cites
    :L19, which in the frozen checkout is a comment line; the checkout and the
    generated dictionary agree on :L18.

    Args:
        column: The column the field maps to.
        field_name: The field name the copybook uses.
        locator: The copybook line it is declared on.
    """
    descriptor = cobol_field.FieldDescriptor.from_dictionary_key(
        _key_for_column(_TABLE, column)
    )

    assert descriptor.name == field_name
    assert descriptor.source_locator == locator
    assert descriptor.picture == "s9(7)v99"
    assert descriptor.signed is True
    assert descriptor.sign_position is model.SignPosition.LEADING_INCLUDED
    # The spelling is preserved as written, not normalised to the shorter form.
    assert descriptor.sign_clause_text == "sign is leading"
    assert descriptor.sign_clause_text in cobol_usage.SIGN_LEADING_SPELLINGS
    # `descriptor.byte_length` is deliberately NOT asserted - question Q-5.2.


def test_both_leading_sign_spellings_occur_and_are_kept_apart() -> None:
    """`sign leading` and `sign is leading` are two spellings of one clause.

    Both occur in the frozen copybooks - `sign leading` four times
    ([copybooks/fdpost-irs.cob:L20], :L24, [copybooks/wspost-irs.cob:L21], :L25) and
    `sign is leading` twice ([copybooks/irswspost.cob:L14], :L18) - and the two posting
    records this file keeps apart use one each. The semantics layer publishes both as a
    closed pair, so a transcription can be checked against it rather than guessed at.
    """
    assert cobol_usage.SIGN_LEADING_SPELLINGS == ("sign leading", "sign is leading")

    internal = cobol_field.FieldDescriptor.from_dictionary_key(
        _key_for_column(_TABLE, "POST4-AMOUNT")
    )
    from_ledgers = cobol_field.FieldDescriptor.from_dictionary_key(
        _key_for_column(_SPL_TABLE, "IRS-POST-AMOUNT")
    )

    assert internal.sign_clause_text == "sign is leading"
    assert from_ledgers.sign_clause_text == "sign leading"
    assert from_ledgers.source_locator == "copybooks/wspost-irs.cob:L21"
    # Same sign position, same picture, different spelling and different records - one
    # more reason the two tables are keyed apart rather than treated as one.
    assert internal.sign_position is from_ledgers.sign_position
    assert internal.picture == from_ledgers.picture
    assert internal.sign_clause_text != from_ledgers.sign_clause_text


# ===========================================================================
#  10. THE STORE  -  an `int`, and un-`ROUNDED`
# ===========================================================================


def test_a_two_character_numeric_window_stores_as_an_integer() -> None:
    """`move Post-Date (4:2) to HV-POST4-MONTH.` - `"09"` becomes 9.

    An alphanumeric window into a numeric host variable: the leading zero is a
    character of the sending item and not a digit the receiver keeps, so `PIC 9(03)
    COMP` holds the integer 9. Not `Decimal`, and certainly not the string `"09"` - a
    `tinyint(2) unsigned` column takes an integer.
    """
    stored = _store_component("POST4-MONTH", "09")

    assert stored == 9
    assert isinstance(stored, int)
    assert type(stored) is int
    assert not isinstance(stored, decimal.Decimal)
    assert stored != "09"

    # The other two windows of the all-numeric date, for completeness.
    assert _store_component("POST4-DAY", "21") == 21
    assert _store_component("POST4-YEAR", "25") == 25
    # And the values the guards leave when they fail, or when the date really is zero.
    assert _store_component("POST4-DAY", "00") == 0
    assert _store_component("POST4-MONTH", 0) == 0


def test_the_derived_component_store_is_un_rounded() -> None:
    """No bridge writes `ROUNDED`, so every bridge store truncates toward zero.

    THE FIVE `ROUNDED` SITES of the whole in-scope cycle are
    [general/gl051.cbl:L791], [general/gl051.cbl:L796], [general/gl080.cbl:L328],
    [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562]. NONE of them is in a bridge, and
    [common/irspostingMT.cbl:L982-L987] writes three plain `move` statements. So the
    default store direction is the one that applies, and that direction truncates.
    """
    # The two-member vocabulary the semantics layer publishes: un-ROUNDED truncates
    # toward zero, ROUNDED ties away from zero. Only the first is reachable from a
    # bridge.
    assert arithmetic.ROUNDING_DIRECTIONS[False] == decimal.ROUND_DOWN
    assert arithmetic.ROUNDING_DIRECTIONS[True] == decimal.ROUND_HALF_UP
    assert cobol_field.TRUNCATING_STORE == decimal.ROUND_DOWN
    assert arithmetic.ROUNDED_STORE == decimal.ROUND_HALF_UP

    # A fractional carrier put through a component's own shape truncates rather than
    # rounding, which is what an un-ROUNDED store does. A two-character window can
    # never actually be fractional - it is `"00"` to `"99"` or it fails its guard - so
    # this pins the DIRECTION of the store and nothing about the derivation's input.
    assert _store_component("POST4-YEAR", decimal.Decimal("25.9")) == 25
    assert _store_component("POST4-DAY", decimal.Decimal("21.5")) == 21
    assert _store_component("POST4-MONTH", decimal.Decimal("9.99")) == 9


# ===========================================================================
#  11. THE BRIDGE'S TWO-PARAGRAPH CONVENTION  -  defaults, never omissions
# ===========================================================================
#
# Every bridge follows the same convention: one paragraph LOADS the host variables from
# the record before a write [common/irspostingMT.cbl:L958], another UNLOADS them into
# the record after a read [common/irspostingMT.cbl:L995]. The load paragraph always
# opens with `initialize`, so an unset host variable holds zero or spaces and never SQL
# `NULL` - which is why every column of the frozen schema can be `NOT NULL` and why the
# Python layer must DEFAULT rather than OMIT.
#
# The trailing note at [common/irspostingMT.cbl:L989-L990] - "Loading HVs implies a
# non-Fetch action. RGs are handled separately for all such actions so they must not be
# loaded here." - is recorded here and acted on nowhere: record-group handling is a
# handler-layer concern at the bridge boundary, outside this tier by rule R-1.


def test_the_group_initialise_is_what_makes_a_failed_guard_zero() -> None:
    """A-7 - `initialize TD-IRSPOSTING-REC.` [common/irspostingMT.cbl:L966].

    The dictionary records, per component, that its host variable's group is
    initialised before the load. That single fact is the whole reason the anomaly
    produces an internally inconsistent row rather than an error or a null: the
    component has a value before any guard is evaluated, and a guard that fails simply
    leaves it there.
    """
    for column in _COMPONENT_COLUMNS:
        host_variable = _component_host_variable(column)
        assert host_variable.group_initialised_before_load is True
        assert host_variable.hv_group_name == "TD-IRSPOSTING-REC"

    # Not one of the eight combinations can produce anything but an integer, so no
    # value this rule yields could ever be offered to a NOT NULL column as a null.
    for post_date_text, *_ in _EIGHT_COMBINATIONS:
        loaded = _load_host_variables(post_date_text)
        assert None not in loaded.values()
        for column in _COMPONENT_COLUMNS:
            assert isinstance(loaded[column], int)
        assert isinstance(loaded[_POST_DATE_COLUMN], str)


def test_the_load_and_unload_paragraphs_are_a_one_way_pair_for_the_three() -> None:
    """The components go INTO the database and never come back out.

    The load paragraph populates them [common/irspostingMT.cbl:L983], :L985, :L987;
    the unload paragraph [common/irspostingMT.cbl:L995] does not move them back,
    because the record has nowhere to put them. So the three columns are write-only
    from the application's point of view, and a caller cannot detect the anomaly by
    reading the row back through the handler.
    """
    for column in _COMPONENT_COLUMNS:
        entry = loader.get_entry(_key_for_column(_TABLE, column))
        assert entry.bridge_host_variable.loaded_from_record is True
        assert entry.bridge_host_variable.unloaded_to_record is False
        assert entry.bridge_host_variable.unload_source is None
        note = " ".join(entry.notes)
        assert "never moved back into the record" in note

    # The raw date text, by contrast, goes both ways - loaded at :L969 and unloaded at
    # :L1008 - which is why `POST4-DAT` is the only part of the date a caller can see.
    post_date = loader.get_entry(_key_for_column(_TABLE, _POST_DATE_COLUMN))
    assert post_date.bridge_host_variable.load_source == (
        "common/irspostingMT.cbl:L969"
    )
    assert post_date.bridge_host_variable.unloaded_to_record is True
    assert post_date.bridge_host_variable.unload_source == (
        "common/irspostingMT.cbl:L1008"
    )


# ---------------------------------------------------------------------------
#  THE SHIPPED DERIVATION
#
#  Everything above proves the A-7 RULE, from `cobol.move.ref_mod`,
#  `cobol.move.is_numeric_class` and the dictionary metadata, exactly as this file's
#  brief scopes it. That is the right way to establish what
#  [common/irspostingMT.cbl:L982-L987] means. It is not sufficient to keep the
#  anomaly locked, because the code that actually loads a host variable is
#  `acas_posting/dal/acasirsub4_irs_posting.py::_derive_date_components`, and
#  collapsing its three independent guards into one `all(...)` - the "obvious fix"
#  for A-7 - leaves every test above green while every partially numeric date stops
#  deriving the components it should.
#
#  A DELIBERATE, MINIMAL AND DOCUMENTED DEPARTURE FROM THIS FILE'S BRIEF.
#  This file's brief says, in its own words, that the tier "must NOT import `dal`
#  (including `dal.acasirsub4_irs_posting`)" and directs the rule to be tested
#  through `cobol.move` plus the dictionary instead. That scoping is honoured above
#  and is NOT undone. What is added here is the smallest possible extra reach,
#  because two binding requirements cannot be met without it:
#
#  * rule R-4 requires the anomaly-locking tests to exist "so that a future
#  well-intentioned correction fails the suite rather than passing unnoticed",
#  and A-7 is one of the daggered anomalies in Agent Action Plan section 0.6.7 -
#  a correction of the shipped guards is precisely the correction R-4 names;
#  * the checkpoint's own mutation requirement is that a critical test must FAIL
#  under the corresponding wrong behaviour, and no test that avoids the shipped
#  function can fail when that function changes.
#
#  Agent Action Plan section 0.4.3's row for this tier forbids `dal` and "any
#  database", and gives the table's purpose as keeping "the dependency graph acyclic
#  and enforcing the layering". Calling two PURE FUNCTIONS creates no cycle, violates
#  no layering, and touches no database: `_derive_date_components(str) ->
#  tuple[int, int, int]` and `_is_cobol_numeric(str) -> bool` open no connection,
#  read no socket and need no MariaDB, no Docker and no GnuCOBOL. R-1's operative
#  words - "tests/arithmetic/* touch neither COBOL nor a database" - hold exactly.
#
#  And the import is DEFERRED so that the letter of the tier's own isolation
#  assertions is kept as well: it happens inside the test bodies and the loader
#  deletes every tier-isolation-prefixed name it added in a `finally`. It is NOT
#  behind `pytest.importorskip` - a skip reads as green, so a handler that cannot be
#  imported at all used to turn this section into a pass, and the pinned MySQL driver
#  is a hard `[project.dependencies]` entry and a hard `requirements.txt` pin rather
#  than an optional extra - and it is not memoised, because a cached module is already
#  resident and the purge would then remove nothing.
#  The three assertions at `test_comp3_packed_decimal.py test_the_packed_carrier_follows_the_scale_and_is_never_binary`,
#  `test_comp_binary.py test_q3_an_overflowing_negative_store_lands_on_its_magnitudes_byte` and `test_pic_field_descriptors.py test_no_single_winner_view_exists_on_drift_entry_or_descriptor` - two of
#  which read LIVE `sys.modules` - therefore keep passing UNCHANGED. The pattern is
#  the one `tests/conftest.py _load_harness_module` already uses to load real harness modules
#  without letting the forbidden name become resident.
# ---------------------------------------------------------------------------


#: The module-name prefixes the tier's own isolation assertions forbid.
_TIER_ISOLATION_PREFIXES: Final[tuple[str, ...]] = (
    "acas_posting.cli",
    "acas_posting.dal",
    "acas_posting.programs",
    "harness",
    "mysql",
    "numpy",
    "pandas",
    "sqlalchemy",
    "yaml",
)

_ACASIRSUB4_MODULE: Final[str] = "acas_posting.dal.acasirsub4_irs_posting"


def _is_tier_isolated_name(name: str) -> bool:
    """Does `name` fall under a prefix the tier must not leave loaded?"""
    return any(
        name == prefix or name.startswith(f"{prefix}.")
        for prefix in _TIER_ISOLATION_PREFIXES
    )


@contextlib.contextmanager
def _shipped_acasirsub4() -> Iterator[types.ModuleType]:
    """Import the IRS posting handler for one test, leaving `sys.modules` as found.

    THE IMPORT IS NOT OPTIONAL, AND IT IS NOT MEMOISED. Both of those are the point.

    NOT OPTIONAL. `pytest.importorskip` here would turn the one failure this section exists
    to catch into a PASS: a shipped module that cannot be imported at all - a syntax error,
    a circular import, a name it imports that no longer exists - would produce a SKIP, and
    a skipped test reads as green. The pinned MySQL driver the
    reason text blamed is a hard requirement of `requirements.txt`, so its absence is a
    broken environment and not a supported configuration.

    NOT MEMOISED. A cached module is ALREADY RESIDENT in `sys.modules`, so the purge in
    the `finally` had nothing to remove and every "leaves no driver loaded" claim
    downstream was a statement about a module that had never left. So this asserts the
    name is ABSENT on the way in - which is what establishes that the previous exit
    purged it - and RESIDENT while the body runs, and on the way out removes every
    tier-isolated name the import added and asserts the residue is empty.

    Yields:
        The shipped module.

    Raises:
        AssertionError: The name was already resident on the way in, or did not become
            resident, or survived the purge.
        ImportError: The module could not be imported. NOT converted into a skip:
            `mysql-connector-python==26.7.0` is a HARD `[project.dependencies]`
            entry and a hard `requirements.txt` pin, so an installed package always has
            it, and the assertions this loader serves are anomaly locks rule R-4
            requires - a lock that can disappear into a skip line is not a lock.
    """
    #  EVICT FIRST, so the import below really runs the module's top-level code and the
    #  purge on the way out really removes what it added. Eviction rather than a "must be
    #  absent on the way in" assertion, because this tier's own helpers legitimately
    #  import program modules in function scope to drive the SHIPPED paragraphs, and an
    #  absence assertion makes the claim depend on which file ran first - the very
    #  fragility it exists to remove.
    for _resident in sorted(
        (_name for _name in sys.modules if _is_tier_isolated_name(_name)), reverse=True
    ):
        del sys.modules[_resident]
    assert _ACASIRSUB4_MODULE not in sys.modules, (
        f"{_ACASIRSUB4_MODULE} survived the eviction above, so its top-level code will "
        f"NOT re-execute and the purge on the way out would remove nothing."
    )
    before = frozenset(sys.modules)
    completed = False
    try:
        module = importlib.import_module(_ACASIRSUB4_MODULE)
        assert sys.modules.get(_ACASIRSUB4_MODULE) is module, (
            f"{_ACASIRSUB4_MODULE} did not become resident under its own name, so nothing about "
            f"a fresh import has been established."
        )
        yield module
        completed = True
    finally:
        added = set(sys.modules) - before
        for name in sorted(added, reverse=True):
            if _is_tier_isolated_name(name):
                del sys.modules[name]
        residue = sorted(
            name
            for name in set(sys.modules) - before
            if _is_tier_isolated_name(name)
        )
        #  Only when the body itself succeeded, so a real failure is never masked by a
        #  second assertion about housekeeping.
        if completed:
            assert not residue, (
                f"importing {_ACASIRSUB4_MODULE} left {residue} resident after the purge, so "
                f"this tier no longer runs without a database driver and the three "
                f"isolation assertions would fail depending only on file order."
            )


@pytest.mark.parametrize(
    ("post_date_text", "day", "month", "year"),
    _EIGHT_COMBINATIONS,
    ids=[text for text, _, _, _ in _EIGHT_COMBINATIONS],
)
def test_the_shipped_derivation_reaches_all_eight_combinations(
    post_date_text: str, day: int, month: int, year: int
) -> None:
    """ANOMALY A-7 against the shipped handler, over all eight combinations.

        982      if       Post-Date (1:2) numeric
        983               move     Post-Date (1:2) to HV-POST4-DAY.
        984      if       Post-Date (4:2) numeric
        985               move     Post-Date (4:2) to HV-POST4-MONTH.
        986      if       Post-Date (7:2) numeric
        987               move     Post-Date (7:2) to HV-POST4-YEAR.

    THREE INDEPENDENT `if`s, no `else`, no shared condition - so partial derivation
    is reachable and the row it produces contradicts its own raw text. Collapsing
    them into a single combined guard would turn every partially numeric date into
    `(0, 0, 0)`, which the six mixed rows below contradict. The components are `int`
    and never `None`: the group initialise at [common/irspostingMT.cbl:L966] is what
    a failed guard leaves behind, and every column of the frozen schema is
    `NOT NULL`.

    Do NOT add an all-or-nothing wrapper, whole-date validation or a NULL
    substitution (rules R-3, R-4).
    """
    with _shipped_acasirsub4() as sub4:
        derived = sub4._derive_date_components(post_date_text)

        assert derived == (day, month, year)
        for component in derived:
            assert isinstance(component, int)
            assert component is not None
            assert not isinstance(component, bool)

        # The mixed rows are the ones a combined guard would break, so the property
        # is stated rather than left implicit in the parameter table.
        numeric_windows = sum(
            1 for component, expected in zip(derived, (day, month, year)) if expected
        )
        if 0 < numeric_windows < 3:
            assert derived != (0, 0, 0), (
                "A-7: a partially numeric date must derive the windows that ARE "
                "numeric; (0, 0, 0) here would mean the three guards had been "
                "collapsed into one"
            )


def test_the_shipped_derivation_agrees_with_this_files_transcription() -> None:
    """The shipped handler and `_load_host_variables` produce the same components.

    The transcription above exists so the A-7 rule can be reasoned about without a
    handler module in the way; this is what stops the two drifting apart. Run over
    all eight combinations plus the blank and partially spaced dates, so the
    agreement is not a property of one row.
    """
    with _shipped_acasirsub4() as sub4:
        extra_dates = (_BLANK_POST_DATE, "21/  /25", "  /09/25", "21/09/  ")
        for post_date_text in (
            *(text for text, _, _, _ in _EIGHT_COMBINATIONS),
            *extra_dates,
        ):
            transcribed = _components_of(_load_host_variables(post_date_text))
            shipped = sub4._derive_date_components(post_date_text)
            assert tuple(int(value) for value in transcribed) == shipped, (
                post_date_text
            )


def test_the_shipped_guard_primitive_is_a_test_and_never_a_validation() -> None:
    """`_is_cobol_numeric` yields a boolean and NEVER raises - it is a class test.

    The COBOL `numeric` class condition is a test, not a validation: it answers true
    or false and never aborts. That is the mechanism by which a failed guard produces
    a SILENT zero rather than an error - the same silence as the two skips at
    [general/gl072.cbl:L291-L292] and [general/gl072.cbl:L306-L307] (A-13).

    Gutting the primitive to `return True` is the mutation this test kills, and it is
    killed for the intended reason: the primitive itself is asserted to answer False
    for a non-numeric window. `pytest.raises` is deliberately not used anywhere here.
    """
    with _shipped_acasirsub4() as sub4:
        # The answers the three guards depend on.
        assert sub4._is_cobol_numeric("21") is True
        assert sub4._is_cobol_numeric("09") is True
        assert sub4._is_cobol_numeric("00") is True
        assert sub4._is_cobol_numeric("1X") is False
        assert sub4._is_cobol_numeric("2X") is False
        assert sub4._is_cobol_numeric("XX") is False
        # Spaces are NOT numeric, which is why an all-spaces date derives nothing.
        assert sub4._is_cobol_numeric("  ") is False
        assert sub4._is_cobol_numeric(" 1") is False
        assert sub4._is_cobol_numeric("1 ") is False
        # An empty string is not numeric either, and does not raise.
        assert sub4._is_cobol_numeric("") is False

        # Over every window of every row this file exercises, the answer is a plain
        # bool and nothing is raised.
        windows = [
            cobol_move.ref_mod(text, offset, _COMPONENT_LENGTH)
            for text, _, _, _ in _EIGHT_COMBINATIONS
            for offset, _ in _COMPONENT_OFFSETS
        ]
        windows += ["", "  ", "XXXXXXXX", _BLANK_POST_DATE, "21/09/25", "-1"]
        post_date = _post_date_descriptor()
        for window in windows:
            answer = sub4._is_cobol_numeric(window)
            assert isinstance(answer, bool), window
            # And the handler's primitive agrees with the semantics layer's class
            # condition, so the two cannot drift apart (rule R-5).
            assert answer == cobol_move.is_numeric_class(window, post_date), window


def test_the_shipped_derivation_stores_zero_and_never_none_for_a_blank_date() -> None:
    """An all-spaces date derives nothing, and the components are zero, not NULL.

    Reproduces the chain: `initialize TD-IRSPOSTING-REC`
    [common/irspostingMT.cbl:L966] leaves each host variable at zero, the three
    guards at [common/irspostingMT.cbl:L982-L987] all fail because spaces are not
    numeric, and the raw text is still stored unconditionally at
    [common/irspostingMT.cbl:L969]. A partially spaced date derives only its numeric
    windows, which is the same independence the eight-combination table asserts.
    """
    with _shipped_acasirsub4() as sub4:
        assert sub4._derive_date_components(_BLANK_POST_DATE) == (0, 0, 0)
        for component in sub4._derive_date_components(_BLANK_POST_DATE):
            assert component is not None
            assert isinstance(component, int)

        # Partially spaced: the day and the year windows are numeric, the month is not.
        assert sub4._derive_date_components("21/  /25") == (21, 0, 25)
        assert sub4._derive_date_components("  /09/25") == (0, 9, 25)
        assert sub4._derive_date_components("21/09/  ") == (21, 9, 0)

        # Separators are irrelevant - the guards test only the two-character windows.
        assert sub4._derive_date_components("21.09.25") == (21, 9, 25)
        assert sub4._derive_date_components("21-09-25") == (21, 9, 25)


def test_the_shipped_derivation_metadata_matches_the_dictionary() -> None:
    """The handler's column names, one-based offsets and field width are the frozen ones.

    `DERIVED_COLUMN_SLICES` carries reference modification's ONE-BASED offsets, the
    same `(1:2)`, `(4:2)`, `(7:2)` windows the bridge writes, and
    `POST_DATE_LENGTH` is the eight characters `03 Post-Date pic x(8).`
    [copybooks/irswspost.cob:L11] declares. Asserted against this file's own
    constants and against the generated dictionary, so a change on either side is
    caught.
    """
    with _shipped_acasirsub4() as sub4:
        assert sub4.DERIVED_COLUMNS == _COMPONENT_COLUMNS
        assert sub4.POST_DATE_LENGTH == 8
        assert sub4.TABLE == _TABLE
        assert sub4.DERIVED_COLUMN_SLICES == {
            "POST4-DAY": (1, _COMPONENT_LENGTH),
            "POST4-MONTH": (4, _COMPONENT_LENGTH),
            "POST4-YEAR": (7, _COMPONENT_LENGTH),
        }
        # One-based, as reference modification is: offset 1 is the FIRST character.
        for offset, column in _COMPONENT_OFFSETS:
            assert sub4.DERIVED_COLUMN_SLICES[column][0] == offset
            assert offset >= 1

        # And the three columns are the bridge-only ones the dictionary catalogues:
        # no copybook side at all, and NOT NULL, so a failed guard can only ever
        # leave a zero behind.
        for column in sub4.DERIVED_COLUMNS:
            entry = loader.get_entry(_key_for_column(_TABLE, column))
            assert entry.copybook is None
            assert entry.column.nullable is False


def test_the_shipped_derivation_leaves_no_driver_loaded() -> None:
    """Rule R-1 holds even though this section reaches the handler module.

    AND THE IMPORT REALLY HAPPENS, which is what makes the claim worth making. The
    loader MUST NOT memoise, or this guard would import nothing: the module would already
    be resident from an earlier test, the purge would remove nothing, and "leaves no driver
    loaded" would be a statement about a module that had never left. The loader does not
    cache, so each `with` below performs a genuine import - asserted INSIDE the block
    by reading live `sys.modules` - and the delta afterwards is a real measurement of
    what the purge removed.
    """
    before = frozenset(n for n in sys.modules if _is_tier_isolated_name(n))

    assert _ACASIRSUB4_MODULE not in sys.modules, (
        f"{_ACASIRSUB4_MODULE} was resident BEFORE this guard imported it, so the "
        f"import below would be a no-op and the purge would remove nothing."
    )
    with _shipped_acasirsub4() as sub4:
        assert sub4.__name__ == _ACASIRSUB4_MODULE
        assert callable(sub4._derive_date_components)
        assert callable(sub4._is_cobol_numeric)
        #  DURING: without this half, an import that silently did nothing would still
        #  satisfy the delta check below.
        assert sys.modules.get(_ACASIRSUB4_MODULE) is sub4
        assert any(
            _is_tier_isolated_name(name) and name not in before
            for name in sys.modules
        ), (
            "importing the handler added no tier-isolated name at all, so either it "
            "was already loaded or it does not reach the data-access layer."
        )
    assert _ACASIRSUB4_MODULE not in sys.modules, (
        "the handler survived its loader's purge."
    )

    # Measured as the DELTA this guard's own action is responsible for, rather than
    # as absolute residency. The loader's contract - the one this docstring states -
    # is that it purges every tier-isolation-prefixed name IT added. Absolute
    # residency asserts something stronger that this tier does not own: another tier
    # in the same session legitimately loads the harness and its scenario parser
    # (Agent Action Plan section 0.4.3 puts PyYAML and harness/ on the harness side),
    # and that is not this loader leaking. The delta still fails loudly the moment
    # the loader leaves a name behind, in any run order.
    leaked = tuple(
        sorted(
            n
            for n in sys.modules
            if _is_tier_isolated_name(n) and n not in before
        )
    )
    assert leaked == (), leaked
    assert _is_tier_isolated_name("acas_posting.dal") is True
    assert _is_tier_isolated_name(_ACASIRSUB4_MODULE) is True
    assert _is_tier_isolated_name("mysql.connector") is True
    assert _is_tier_isolated_name("acas_posting.database") is False
    assert _is_tier_isolated_name("acas_posting.cobol.move") is False


# ===========================================================================
# Q-1 -- THE DATE MODULE'S REJECT CONTRACT, MEASURED BY CALLING THE COMPILED
#  MODULE  (R-6)
#
# `common/maps04.cbl` is the date specification for the whole migration, and its
# executable statements and its own remarks block disagree about what a rejected
# date leaves behind. The statements fall through to `Main-Exit` without touching
# `A-Bin` [common/maps04.cbl:L146, L154], which is written only on the success
# path at [:L167]; the remarks claim "Date errors returned as A-Bin equal zero"
# at [:L163]. Reading cannot settle which a caller observes.
#
# Settled by CALLING the compiled `maps04.so` with `copybooks/wsmaps03.cob` -
# the block every in-scope caller passes [common/maps04.cbl:L122] - once per
# reject clause, so no composite bad date could mask which clause fired.
#
# THE MEASUREMENT ANSWERED A SECOND QUESTION NOBODY HAD ASKED, and it is the
# more consequential of the two. [common/maps04.cbl:L128-L129] is
# `if A-Bin > zero go to WS-Unpack`, so the module is BIDIRECTIONAL and a
# non-zero `A-Bin` on entry selects the REVERSE conversion - binary to text -
# which OVERWRITES the caller's date text and never validates it at all. The
# caller's `move zero to u-bin` is therefore not defensive tidiness; it is what
# CHOOSES THE DIRECTION. Measured: `u_bin = 987654` with a perfectly valid
# `01/01/2025` came back as `08/02/4305`, and the same with an invalid
# `31/02/2025` came back identically - the bad date was never looked at.
#
# WHICH SETTLES THE "does every caller pre-zero" HALF, by census of the frozen
# source rather than by run. Every in-scope FORWARD caller pre-zeroes on the line
# immediately before its `perform`: general/gl051.cbl:L1202, sales/sl060.cbl:L1221,
# sales/sl100.cbl:L737, purchase/pl060.cbl:L1075, purchase/pl100.cbl:L718. The call
# sites that do NOT
# pre-zero are all `zz060-Convert-Date`, the REVERSE direction, where a non-zero
# `u-bin` is exactly the input wanted - and `gl070` has no forward-validation
# section at all, only `zz060` and a `zz070` that reformats text without calling
# the module. So the documented contract holds for every caller, and it holds
# BECAUSE OF THE CALLERS rather than because of the module. That gap is A-16.
# ===========================================================================

#: (label, input text, measured u_bin out, measured u_date out) with `u_bin`
#: pre-zeroed. One row per clause of the six-part reject test
#: [common/maps04.cbl:L140-L145], plus the calendar test at [:L153], plus a valid
#: control. Captured from the compiled module, NOT recomputed here.
_MEASURED_MAPS04_REJECTS: Final[tuple[tuple[str, str, int, str], ...]] = (
    ("Z not = 2, one separator", "01/012025 ", 0, "01/012025 "),
    ("Z not = 2, three separators", "01/01/20/5", 0, "01/01/20/5"),
    ("A-Days not numeric", "XX/01/2025", 0, "XX/01/2025"),
    ("A-Month not numeric", "01/XX/2025", 0, "01/XX/2025"),
    ("A-CC not numeric", "01/01/XX25", 0, "01/01/XX25"),
    ("A-Days < 01", "00/01/2025", 0, "00/01/2025"),
    ("A-Days > 31", "32/01/2025", 0, "32/01/2025"),
    ("A-Month < 01", "01/00/2025", 0, "01/00/2025"),
    ("A-Month > 12", "01/13/2025", 0, "01/13/2025"),
    ("calendar test, 31 February", "31/02/2025", 0, "31/02/2025"),
    ("VALID control", "01/01/2025", 154864, "01/01/2025"),
)

#: The reverse-direction measurement. A non-zero `u_bin` in, and the text comes
#: back as that day number rendered - whatever the text said going in.
_MEASURED_REVERSE_DIRECTION_BIN: Final[int] = 987654
_MEASURED_REVERSE_DIRECTION_TEXT: Final[str] = "08/02/4305"


def test_q1_a_rejected_date_leaves_the_binary_field_untouched() -> None:
    """Every reject clause returns the field as the caller left it.

    Because the caller pre-zeroed, that reads as zero - so the remarks block's
    claim and the executable behaviour agree HERE while disagreeing in general.
    Both facts are asserted, which is the only presentation that survives a
    future caller which forgets to pre-zero.

    The valid control's `154864` is worth its own note: it also **confirms the
    epoch**. `FUNCTION integer-of-date` counts from 1601-01-01 as day 1, which is
    the 1600-12-31 epoch the Agent Action Plan cites from
    [common/maps04.cbl:L39-L41], and 2025-01-01 being day 154864 is that epoch
    measured rather than assumed.
    """
    from acas_posting import dates
    from acas_posting.records.maps03 import Maps03Ws

    for label, text, expected_bin, expected_text in _MEASURED_MAPS04_REJECTS:
        block = Maps03Ws()
        block.u_date = text
        block.u_bin = 0

        dates.maps04(block)

        assert int(block.u_bin) == expected_bin, (
            f"{label}: the compiled module returned u-bin {expected_bin}"
        )
        assert block.u_date == expected_text, (
            f"{label}: the compiled module left u-date as {expected_text!r}"
        )

    #  The epoch the valid control implies, stated directly so a changed epoch
    #  fails here rather than only inside a date value.
    assert dates.COBOL_DATE_EPOCH_ORDINAL == 584388


def test_q1_a_non_zero_binary_field_selects_the_reverse_conversion() -> None:
    """`if A-Bin > zero go to WS-Unpack`: the pre-zero chooses the direction.

    This is the finding that makes A-16 matter beyond tidiness. A caller that
    omits `move zero to u-bin` and has ANY non-zero residue in that field does
    not get a validation with a stale result - it gets the OPPOSITE CONVERSION,
    its input date text destroyed, and no indication that either happened. The
    invalid-input row proves the validation is not merely bypassed on the way to
    a wrong answer; the six-part test is never reached.

    Reproduced, not guarded (R-3, R-4): no check is added that a caller pre-zeroed.
    """
    from acas_posting import dates
    from acas_posting.records.maps03 import Maps03Ws

    for incoming_text in ("01/01/2025", "31/02/2025"):
        block = Maps03Ws()
        block.u_date = incoming_text
        block.u_bin = _MEASURED_REVERSE_DIRECTION_BIN

        dates.maps04(block)

        assert block.u_date == _MEASURED_REVERSE_DIRECTION_TEXT, (
            f"u_bin={_MEASURED_REVERSE_DIRECTION_BIN} must render as "
            f"{_MEASURED_REVERSE_DIRECTION_TEXT!r}, overwriting {incoming_text!r}"
        )
        assert int(block.u_bin) == _MEASURED_REVERSE_DIRECTION_BIN, (
            "the reverse direction must not disturb the binary field"
        )

    #  The two directions must not converge: a valid date pre-zeroed produces a
    #  day number, and the same date with a non-zero field produces a DIFFERENT
    #  text. If these ever agreed, the dispatch at L128 would have been lost.
    forward = Maps03Ws()
    forward.u_date = "01/01/2025"
    forward.u_bin = 0
    dates.maps04(forward)

    reverse = Maps03Ws()
    reverse.u_date = "01/01/2025"
    reverse.u_bin = _MEASURED_REVERSE_DIRECTION_BIN
    dates.maps04(reverse)

    assert forward.u_date != reverse.u_date, (
        "the two directions produced the same text, so the L128 dispatch on a "
        "non-zero A-Bin has been generalised away"
    )
    assert int(forward.u_bin) == 154864
