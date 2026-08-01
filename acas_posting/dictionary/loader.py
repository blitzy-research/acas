"""Runtime lookup into the generated ACAS posting data dictionary.

This module is how field-level traceability reaches run time. Agent Action
Plan section 0.4.1.6 states its entire mandate in one line - "Runtime lookup
so every record field cites its entry" - and rule R-5 names it directly:
"`acas_posting/dictionary/loader.py` lets every record field cite its
dictionary key at runtime."

It reads exactly one file, `data_dictionary/acas_posting_dictionary.json`,
read-only and lazily, and hands back the immutable record tree that
`acas_posting.dictionary.model` defines. It computes nothing, coerces
nothing and repairs nothing.

WHY A LOOKUP MODULE EXISTS AT ALL
=================================
Agent Action Plan section 0.3.3 names the pattern it serves - "Dictionary as
single source of truth ... Field metadata is therefore derived, not
transcribed, which eliminates an entire class of transcription error across
several hundred fields" - and section 0.8.1 makes the ordering a directive
rather than a preference:

    "Data dictionary first. The dictionary is generated from the bridge
    before record definitions are written, and every Python field definition
    cites its entry. This ordering is a directive, not a preference - it is
    what prevents fields being transcribed by eye."

The authority the dictionary carries is not the copybooks'. It is the
maintainer's one-way COBOL-to-MySQL bridge, and that is the user's own
requirement, preserved verbatim in Agent Action Plan section 0.8.2:

    "The maintainer's one-way COBOL-to-MySQL bridge defines the
    authoritative record-layout <-> table mapping - it is the data
    dictionary for this migration."

So a record module that needs to know a field's places, scale, signedness,
usage or sign position asks here, by key, and gets the answer the frozen
bridge itself gives. It does not read a picture clause by eye. The
difference is not stylistic: the statistics fields of the sales ledger are
declared `binary-long` [copybooks/wssl.cob:L46-L52], so their truncation on
divide is INTEGER truncation, and that is exactly what makes the
moving-average defect of [sales/sl060.cbl:L826-L827] reproducible. An
integer-versus-decimal choice taken from this module is reproducible; the
same choice taken by eye is not.

THE KEY CONVENTION - AND WHY IT IS ALWAYS QUALIFIED
==================================================
An entry is addressed by one key, in one of two forms:

    <TABLE-NAME>.<COLUMN-NAME>      where a column backs the field, for
                                    example IRSPOSTING-REC.POST4-DAY
    <COPYBOOK-RECORD>.<FIELD-NAME>  where the field is copybook-only, for
                                    example File-Access.Fs-Reply

Both halves are the names the frozen sources use themselves, unaltered:
hyphens are not turned into underscores and case is not folded, so a key can
be searched for in the COBOL and in the schema exactly as it stands. Lookup
here is therefore exact and case-sensitive.

NEVER KEY BY FIELD NAME ALONE. The qualification is what keeps two tables
apart that would otherwise merge: PSIRSPOST-REC is the transfer file the
Sales and Purchase programs write, reached through `acas008` and the
`slpostingMT` bridge with ten columns, while IRSPOSTING-REC is the internal
IRS posting file, reached through `acasirsub4` and the `irspostingMT` bridge
with thirteen. Their field names are near-identical and
[copybooks/wspost-irs.cob:L6-L7] says so in as many words: "This is NOT the
same as the internal IRS posting file". Because the key embeds the table or
record name, no two entries can be conflated by field name.

Where one field name repeats inside one record - `filler` occurs four times
in copybooks/wsledger.cob - the key carries a `#` and the declaration line.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  THIS MODULE RESOLVES NOTHING  (rule R-4)                            !!
!!                                                                      !!
!!  A DEFECT REPRODUCED IS CORRECT; A DEFECT FIXED IS A FAILURE.        !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

That line is the user's own requirement, which Agent Action Plan section
0.8.2 preserves verbatim: "There is no test suite: compiled COBOL execution
is the behavioral specification, defects included. A defect reproduced is
correct; a defect fixed is a failure."

An entry records the copybook field, the bridge host variable and the column
as three independent sibling views, plus the drift between them, and it
stops there. This module hands those views over as they stand. There is
deliberately no accessor - and none may be added - that names one winning
type across the views: no resolved, canonical, effective, corrected,
recommended or preferred type is offered here, because a caller handed one
would use it and the disagreement would leave the system. A caller that
wants "the type" must say which of the three layers it means. Those six
words appear nowhere else in this file, and the one further word of that
family that does - "authoritative", in the preserved user requirement quoted
above - describes WHICH SOURCE the dictionary is built from, never a type
this module hands back.

The disagreements are load-bearing behaviour, not noise:

  * `Sales-Average` is declared signed `binary-long`
    [copybooks/wssl.cob:L49], becomes the unsigned host variable
    `HV-SALES-AVERAGE PIC 9(10) COMP` [common/salesMT.cbl:L308] and lands
    in an unsigned column, so a negative value LOSES ITS SIGN AT THE BRIDGE
    and not at the database. Agent Action Plan section 0.6.2: "the Python
    data-access layer must reproduce the bridge's conversion, not merely
    write the computed value and let MySQL complain ... the drift is
    specific rather than systemic and must be handled field by field from
    the dictionary". `SALEDGER-REC.SALES-CURRENT` proves the "specific"
    half: signed at all three layers, no drift at all.
  * `Ledger-Name` is 24 characters wide in the copybook and 32 in both the
    host variable [common/nominalMT.cbl:L299] and the column
    [mysql/ACASDB.sql:L127], so the padding a table dump shows is not the
    copybook's padding.
  * POST4-DAY, POST4-MONTH and POST4-YEAR have NO copybook view at all.
    They exist because the bridge derives them from two-character slices of
    a date string under a guard [common/irspostingMT.cbl:L982-L987]; when a
    guard does not hold the move is simply not made, so the component keeps
    the zero left by the group INITIALIZE while the raw date text is stored
    anyway. `derivation.guard` and `derivation.guard_failure_behaviour`
    carry that fact to the data-access layer, which reproduces it.
  * `HV-POST-RRN` is declared [common/glpostingMT.cbl:L282] and never
    loaded from the record, so `loaded_from_record` is false and `notes`
    says why.

None of that is a warning. `notes`, `anomaly_refs`, `ambiguity_refs`,
`drift` and `derivation` are DATA THIS MODULE RETURNS, never a reason to
complain: a loader that logged "signedness drift" would invite exactly the
correction rule R-4 forbids. `ambiguity_refs` in particular keeps an
unsettled question visible - Agent Action Plan section 0.6.8 lists five,
and the batch-record length contradiction [copybooks/wsbatch.cob:L7-L9] and
the negative binary value through an unsigned host variable both surface
through entries served here.

WHERE THE ARTIFACT LIVES, AND THE WHEEL-ABSENCE CAVEAT
======================================================
The dictionary is a top-level repository SIBLING of `acas_posting` and
deliberately not package data: pyproject.toml includes "acas_posting*" in
package discovery and names "data_dictionary*" in its exclude list. One
consequence is stated plainly rather than discovered later - THE ARTIFACT IS
NOT PRESENT INSIDE AN INSTALLED WHEEL. That is intended. The dictionary is
repository data, consumed from a source checkout, which is how the oracle
scripts and the test suites run.

`acas_posting/__init__.py` derives the path once and hands the absence case
to this module by name. So this module reuses `DATA_DICTIONARY_PATH` rather
than walking up the tree a second time - two derivations of one fact drift
apart eventually - and owns the two behaviours that follow:

  * every accessor takes an explicit `path` override, which is the
    sanctioned escape hatch for a test or a relocated deployment;
  * absence raises `DictionaryNotFoundError` naming the expected absolute
    path, the reason it may be missing and both remedies. It does NOT fall
    back to an empty dictionary, and it does NOT regenerate the artifact.

LAYERING - THE NARROWEST IMPORT SURFACE IN THE PACKAGE
======================================================
Agent Action Plan section 0.4.3 fixes the layering, and two whole layers
reach their field metadata through this module and through nothing else:
`cobol/*.py` may import `dictionary.loader` ONLY, and `records/*.py` may
import `cobol.field` and `dictionary.loader` only, "this keeps the record
layer a leaf". Seven semantics modules and twenty-seven record modules sit
on that path.

So this module imports, from the whole of `acas_posting`, exactly two
things: the path constants from the package marker, and
`acas_posting.dictionary.model`. Nothing else - not `cobol`, `records`,
`dal`, `programs`, `cli`, `clock`, `dates`, `workfiles`, not the sibling
oracle tree, and above all not `acas_posting.dictionary.generate`. The
generator is a build-time tool that parses the frozen COBOL tree and the
frozen schema; importing it here would put those parsers on the import path
of every record module and would break Agent Action Plan section 0.4.3's
promise that the arithmetic test tier "imports only `cobol` and `records`
and touches no database, so it runs anywhere". Any further import becomes a
cycle the moment `cobol/field.py` imports this module.

NO IMPORT-TIME WORK, ONE READ PER PROCESS
=========================================
Importing this module reads no file, opens no connection and cannot fail for
an environmental reason: it binds names and nothing else. Loading is lazy
and explicit, and the parsed document is memoised per absolute path, so
twenty-seven record modules importing at start-up cost ONE read between
them and share one immutable tree. Sharing is safe because every record in
`model` is a frozen dataclass whose collections are tuples.

DOCUMENT ORDER IS THE ORDER  (rule R-6)
=======================================
Every sequence returned here is in the order the document records it, and
nothing here re-sorts: the document's own ordering IS the determinism
contract, and re-sorting would silently discard it. The artifact states the
contract in `meta.determinism.array_order`, and for entries it reads:
tables by name ascending, within a table by the column ordinal the frozen
dump fixes, then that table's copybook-only fields in copybook declaration
order, then the copybook-only fields that correspond to no table at all.

Two consequences worth knowing before reading an accessor:

  * `entries_for_table` returns a table's column-mapped entries in column
    ordinal order. IRSPOSTING-REC therefore comes back with POST4-DAY,
    POST4-MONTH and POST4-YEAR at positions 4, 5 and 6 - INTERLEAVED
    between POST4-DAT and POST4-DR, as the frozen dump has them, not
    appended after the copybook's own columns.
  * `entries_for_copybook_record` returns a record's entries in that same
    document order, which for a record backed by a table means column
    ordinal order first and the record's copybook-only fields after. Where
    a caller needs strict copybook declaration order it has each field's
    own `copybook.source` line to order by; this module will not reorder
    the document on its behalf.

Every accessor is otherwise a pure function of the document: the same
document yields the same answer, in the same order, in every process.
Nothing here consults a clock, an entropy source, the process environment,
installed distribution metadata or the version-control checkout, and no
directory is listed anywhere.

NUMERIC POLICY  (rule R-2)
==========================
No accounting value may pass through a binary floating-point type at any
point. This module holds no value at all - it describes precision, it never
carries it - so it constructs no arithmetic type and imports no arithmetic
module. Places, scales, character lengths, ordinals, display widths and
every coverage count come back as `int`; pictures, SQL type names and sign
clause text come back as `str`.

Two guards make that structural rather than incidental. The parse is asked
to hand any real-number literal back as its own text rather than as a
binary approximation of it, and the parsed tree is then walked against an
ALLOW-LIST of the four scalar shapes `model.JsonValue` admits - text, a
dimensionless whole number, a flag and absence. Anything else fails
immediately with `DictionaryNumericPolicyError`, which is how a binary
approximation is rejected without this module ever having to name that type.

NO NEW VALIDATION, NO CONCURRENCY  (rule R-3)
=============================================
This module adds no member the document does not carry and synthesises no
default for one it lacks: `model.from_json_obj` fetches every member by
name with no fallback, and that failure is allowed to surface exactly as it
is raised. Nor is the document checked against its JSON Schema here - that
check belongs to a test, which is where a check that is allowed to fail
belongs, and no schema-checking library is in the pinned dependency set.
No data definition statement is emitted and no index or constraint is
proposed. No returned string is tidied.

Execution is strictly sequential, matching the single-threaded COBOL: the
memo below is a plain mapping, and there is no thread, event loop, process
pool, connection pool or synchronisation primitive anywhere in this module.

NO COBOL AT RUNTIME  (rule R-1)
===============================
This module is the proof of that rule, because it sits on the import path of
thirty-four others. It reads ONE JSON file. It parses no COBOL text, opens
no bridge, copybook or schema source, launches no child process, loads no
foreign library, looks for no compiler and reaches no part of the sibling
oracle tree. It imports cleanly on a host with no COBOL toolchain and no
database. The COBOL locators throughout this file are citations for a
reader, which is what rule R-5 asks for; nothing here opens one.

THE ACCESSORS
=============
    load_dictionary            the whole document, memoised per path
    clear_cache                discard the memo (test support)
    meta / sources / coverage  the document's own three headers
    entries / entry_keys       every entry, in document order
    get_entry / find_entry     one entry by key: raising and non-raising
    entries_for_table          one table's entries, column ordinal order
    entries_for_copybook_record / entries_for_copybook_file
                               one record's or one file's entries
    copybook_field_for / host_variable_for / column_for
                               the three views; None is a recorded fact
    drift_for / derivation_for the cross-view facts, never merged
    tables / table_names / table_for / find_table / tables_for_handler
                               the entity <-> handler <-> bridge <-> table
                               spine, for the data-access layer
    bridge_for                 one bridge pair, with its key metadata
    cite                       a one-line provenance citation (rule R-5)

FURTHER READING
===============
    data_dictionary/acas_posting_dictionary.json   the artifact read here
    acas_posting/dictionary/model.py               the records returned
    docs/migration/traceability.md                 the wider mapping
    docs/migration/anomaly-log.md                  the reproduced defects
    docs/migration/ambiguity-resolutions.md        the open questions
"""

# PROVENANCE
# Every fact this module serves is derived from the maintainer's own one-way
# COBOL-to-MySQL bridge (common/*MT.scb and common/*MT.cbl), the record
# copybooks under copybooks/, and the frozen schema mysql/ACASDB.sql. Those
# trees are the specification for this migration and are never modified,
# reformatted, commented, relocated or built from here.

import difflib
import json
from pathlib import Path
from typing import Final

from acas_posting import DATA_DICTIONARY_PATH
from acas_posting.dictionary.model import (
    BridgeHostVariable,
    BridgeName,
    BridgeSource,
    CopybookField,
    Coverage,
    DataDictionary,
    Derivation,
    DictionaryEntry,
    Drift,
    EntryKey,
    HandlerName,
    JsonObject,
    Meta,
    MysqlColumn,
    RepoPath,
    Sources,
    TableName,
    TableRecord,
    from_json_obj,
)

# =============================================================================
#  FAILURES
#
#  Six classes, each with one job, and each one a subclass of a built-in the
#  caller would already be catching: absence is also a `FileNotFoundError`, an
#  unreadable document is also a `ValueError`, and a miss is also a `KeyError`
#  because rule R-5's own instruction for the primary accessor is to raise a
#  `KeyError` subclass.
#
#  `DictionaryError` carries the message plainly. That matters for the two
#  `KeyError` subclasses in particular: `KeyError` renders as the REPR of its
#  argument, which would wrap a multi-line teaching message in quotes and
#  escape every newline in it, and the whole point of that message is to be
#  read.
# =============================================================================


class DictionaryError(Exception):
    """Base for every failure this module raises.

    Attributes:
        message: The failure, in full, as `str()` also returns it.
    """

    def __init__(self, message: str) -> None:
        """Record the message on the exception and on `args`.

        Args:
            message: The complete failure text, ready to be read as it
                stands. It is never assembled from the environment: no path
                appears in it that the caller did not supply or that
                `acas_posting.__init__` did not derive.
        """
        super().__init__(message)
        self.message: str = message

    def __str__(self) -> str:
        """Return the message unaltered, without repr quoting."""
        return self.message


class DictionaryNotFoundError(DictionaryError, FileNotFoundError):
    """The dictionary artifact is not present at the path asked for.

    Almost always the wheel-absence caveat in this module's docstring: the
    artifact is a repository sibling of the package and pyproject.toml keeps
    it out of the installed distribution deliberately. The message names the
    expected absolute path and both remedies.

    This is never answered with an empty dictionary and never answered by
    regenerating the artifact.
    """


class DictionaryParseError(DictionaryError, ValueError):
    """The bytes at the path are not a readable dictionary document.

    Raised for text the JSON reader cannot parse, and for a document whose
    top level is not an object. The original failure is chained, so the line
    and column the reader reported survive; nothing is repaired, defaulted or
    guessed (rule R-3).
    """


class DictionaryNumericPolicyError(DictionaryParseError):
    """A parsed value falls outside the scalar shapes the model admits.

    Rule R-2 keeps binary floating point out of this migration entirely, and
    `model.JsonValue` admits text, a dimensionless whole number, a flag,
    absence, arrays and objects - and nothing else. A value of any other
    shape stops the read here rather than travelling into a record, an
    arithmetic module or a table.
    """


class DictionaryKeyError(DictionaryError, KeyError):
    """No entry in the dictionary carries the key asked for.

    The message quotes the key, states both key forms, warns against keying
    by field name alone, and offers the nearest keys the document does carry
    - because the fix is to correct the key, never to hand-write the field's
    metadata. Rule R-5: a hand-written descriptor is precisely the
    transcription error the data-dictionary-first directive exists to
    prevent.
    """


class DictionaryLookupError(DictionaryError, KeyError):
    """No table, copybook record, copybook file, handler or bridge matches.

    Distinct from `DictionaryKeyError` so that a caller resolving the
    entity-to-table spine can tell a misspelt table name from a misspelt
    entry key. Both are `KeyError` subclasses, so a caller that does not care
    can catch just `KeyError`.
    """


# =============================================================================
#  THE PARSE BOUNDARY  (rules R-2 and R-3)
# =============================================================================

#: The scalar shapes `model.JsonValue` admits, as an ALLOW-LIST. Stated this
#: way round on purpose: an allow-list rejects a binary approximation of a
#: real number - and anything else exotic a document might carry - without
#: this module ever naming that type, and it stays correct if the JSON reader
#: ever learns a new one. `bool` is listed for clarity even though it is a
#: subclass of `int`, because a flag and a count are different facts here.
_ADMITTED_SCALARS: Final[tuple[type, ...]] = (str, int, bool, type(None))

#: How many near-miss suggestions a failure message offers. Small on purpose:
#: a message that lists fifty candidates teaches nothing.
#:
#: The similarity threshold is deliberately NOT stated here. The standard
#: library's own default is used, which keeps this file free of any
#: real-number literal whatsoever - so the claim that this module never
#: constructs a binary approximation of a real number holds without a
#: carve-out, even in a failure message (rule R-2).
_SUGGESTION_LIMIT: Final[int] = 5

#: What a citation prints where one of the three views is absent. Absence is
#: itself a recorded fact - `presence` and `one_sided` carry it - so it is
#: shown rather than omitted: a citation with a segment silently missing
#: would read as a formatting slip instead of as evidence.
_ABSENT_VIEW: Final[str] = "absent"


def _absolute_document_path(path: Path | None) -> Path:
    """Return the absolute, symlink-free path of the document to read.

    Args:
        path: An explicit artifact path, or None for the repository's own
            `data_dictionary/acas_posting_dictionary.json` as
            `acas_posting.__init__` derives it. The override is the
            sanctioned escape hatch for a test or a relocated deployment.

    Returns:
        The same location expressed absolutely, so that two spellings of one
        file - a relative path, a path through a symbolic link - share a
        single memo entry and therefore a single read.

    `Path.resolve()` asks the operating system to make the path absolute and
    symlink-free. It opens nothing, reads no content and - defaulting to
    non-strict - cannot raise for a path that is not there, so absence is
    reported by the reader below with a message that can explain itself,
    never by this helper.
    """
    return (DATA_DICTIONARY_PATH if path is None else Path(path)).resolve()


def _admit_json_value(value: object, trail: str, path: Path) -> None:
    """Fail unless `value` and everything under it is a shape the model admits.

    Args:
        value: One node of the freshly parsed tree.
        trail: Where the node sits, as `.member` and `[index]` steps from the
            document root, so a failure names the offending member rather
            than only its type.
        path: The document being read, named in the failure.

    Raises:
        DictionaryNumericPolicyError: The node is outside the four scalar
            shapes `model.JsonValue` admits and is not an array or an object.

    This walks types, never values: it does not test a count against a
    range, a string against a pattern or a member against the schema, so it
    adds no validation of what the document says (rule R-3). It is the
    numeric policy of rule R-2 made structural at the one point where an
    outside document becomes Python objects.
    """
    if isinstance(value, dict):
        for member, item in value.items():
            _admit_json_value(item, f"{trail}.{member}", path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _admit_json_value(item, f"{trail}[{index}]", path)
        return
    if isinstance(value, _ADMITTED_SCALARS):
        return
    raise DictionaryNumericPolicyError(
        f"The data dictionary at {path} carries a value at {trail} of type "
        f"{type(value).__name__!r}, which is outside the shapes "
        "acas_posting.dictionary.model.JsonValue admits - text, a "
        "dimensionless whole number, a flag, absence, an array or an "
        "object.\n"
        "Rule R-2 keeps binary floating point out of this migration at "
        "every point, in computation, in storage and in transport, so the "
        "read stops here rather than letting that value reach a record, an "
        "arithmetic module or a table.\n"
        "The artifact this module expects records places, scales, character "
        "lengths, ordinals, display widths and counts as whole numbers, and "
        "pictures, SQL type names and sign clause text as strings."
    )


def _read_document(path: Path) -> DataDictionary:
    """Read, parse and map one dictionary document. No memo, no fallback.

    Args:
        path: The absolute path of the artifact to read.

    Returns:
        The document as the immutable record tree `model` defines.

    Raises:
        DictionaryNotFoundError: Nothing readable is at `path`.
        DictionaryParseError: The text is not parseable JSON, or its top
            level is not an object.
        DictionaryNumericPolicyError: A parsed value is outside the shapes
            the model admits (rule R-2).

    `parse_float=str` is the numeric guard's first half: a real-number
    literal comes back as its own text rather than as a binary approximation
    of it, so no such value can be constructed even while the document is
    being read. The artifact carries no such literal - its numeric members
    are dimensionless counts - and the walk that follows is the second half,
    catching anything the reader still produces of its own accord.

    A member the document does not carry is NOT defaulted here. That failure
    belongs to `model.from_json_obj`, which fetches every member by name with
    no fallback, and it is allowed to surface exactly as raised (rule R-3).
    """
    if not path.is_file():
        raise DictionaryNotFoundError(_absence_message(path))
    text = path.read_text(encoding="utf-8")
    try:
        tree = json.loads(text, parse_float=str)
    except json.JSONDecodeError as error:
        raise DictionaryParseError(
            f"The data dictionary at {path} could not be parsed as JSON: "
            f"{error}\n"
            "The artifact is a committed repository file with a fixed shape "
            "- UTF-8, no byte-order mark, LF line endings, a two-space "
            "indent and one trailing newline - and its root members are "
            "meta, sources, tables, entries and coverage. Nothing is "
            "repaired or guessed here: correct the file, or pass the path of "
            "an intact copy."
        ) from error
    _admit_json_value(tree, "<document>", path)
    if not isinstance(tree, dict):
        raise DictionaryParseError(
            f"The data dictionary at {path} parsed to "
            f"{type(tree).__name__!r} rather than to an object. The root of "
            "the artifact is an object whose members are meta, sources, "
            "tables, entries and coverage."
        )
    document: JsonObject = tree
    return from_json_obj(document)


def _absence_message(path: Path) -> str:
    """Return the failure text for an artifact that is not there.

    Args:
        path: The absolute path that was looked at.

    Returns:
        A message naming that path, explaining why it can legitimately be
        missing, and giving both remedies - and no third, since this module
        neither empties nor regenerates.
    """
    return (
        f"The ACAS posting data dictionary was not found at {path}\n"
        "\n"
        "That file is a repository artifact rather than package data, and "
        "pyproject.toml keeps it out of the installed distribution "
        "deliberately: package discovery includes acas_posting* and names "
        "data_dictionary* in its exclude list. So it is present in a source "
        "checkout - which is how the oracle scripts and the test suites run "
        "- and absent from an installed wheel.\n"
        "\n"
        "Two remedies, and no third:\n"
        "  1. run from a source checkout of the repository, where "
        "data_dictionary/acas_posting_dictionary.json sits beside the "
        "acas_posting package; or\n"
        "  2. pass an explicit path - load_dictionary(Path(...)), or the "
        "path= keyword of any accessor in this module - naming an intact "
        "copy of the artifact.\n"
        "\n"
        "This module does not fall back to an empty dictionary, because a "
        "record module would then bind field metadata that no frozen source "
        "supports. Nor does it regenerate the artifact: that is the job of "
        "the build-time generator beside this module, whose COBOL and schema "
        "parsers must never reach the import path of the record layer "
        "(Agent Action Plan section 0.4.3)."
    )


class _DocumentIndex:
    """Lookup tables over one document, built once and never mutated after.

    Private on purpose: what this module publishes is accessors, not indexes,
    so that no caller can hold a mapping and mutate it. Every collection
    below preserves the order the document records - the artifact's own
    `meta.determinism.array_order` is the contract, and re-ordering it here
    would discard exactly the guarantee rule R-6 rests on.

    The mapping from key to entry takes the document as it stands. The
    artifact's keys are unique by construction, and this module does not
    police that: a duplicate would be the generator's defect to report, and
    checking for one here would be a validation this migration may not add
    (rule R-3).
    """

    __slots__ = (
        "bridges_by_name",
        "copybook_files_by_record",
        "copybook_record_names",
        "document",
        "entries_by_copybook_file",
        "entries_by_key",
        "entries_by_table",
        "entry_keys",
        "tables_by_handler",
        "tables_by_name",
    )

    def __init__(self, document: DataDictionary) -> None:
        """Walk the document once and build every lookup table from it.

        Args:
            document: The mapped document to index. Held as it stands; it is
                immutable, so the index cannot drift from it.
        """
        entries_by_key: dict[EntryKey, DictionaryEntry] = {}
        entries_by_table: dict[TableName, list[DictionaryEntry]] = {}
        entries_by_copybook_file: dict[RepoPath, list[DictionaryEntry]] = {}
        for entry in document.entries:
            entries_by_key[entry.key] = entry
            # A null table is the ordinary case for a copybook-only field -
            # 502 of the 1015 entries - and never an error. The working
            # storage of copybooks/wsfnctn.cob reaches no table at all, and
            # those entries are indexed here exactly like any other.
            if entry.table is not None:
                entries_by_table.setdefault(entry.table, []).append(entry)
            # A null copybook view is equally ordinary: the three date
            # components the bridge derives at
            # [common/irspostingMT.cbl:L982-L987] have no copybook to belong
            # to, so they are absent from this index and present in the
            # table index above.
            if entry.copybook is not None:
                entries_by_copybook_file.setdefault(
                    entry.copybook.file, []
                ).append(entry)

        copybook_files_by_record: dict[str, list[RepoPath]] = {}
        for copybook in document.sources.copybooks:
            copybook_files_by_record.setdefault(
                copybook.record_name, []
            ).append(copybook.path)

        tables_by_name: dict[TableName, TableRecord] = {}
        tables_by_handler: dict[HandlerName, list[TableRecord]] = {}
        for table in document.tables:
            tables_by_name[table.name] = table
            # One handler can own several tables, and the data-access layer
            # depends on that: acas000 dispatches to four tables by file-key
            # number, and acas016 and acas026 each own a header table and a
            # lines table.
            tables_by_handler.setdefault(table.handler, []).append(table)

        self.document: DataDictionary = document
        self.entries_by_key: dict[EntryKey, DictionaryEntry] = entries_by_key
        self.entry_keys: tuple[EntryKey, ...] = tuple(entries_by_key)
        self.entries_by_table: dict[TableName, tuple[DictionaryEntry, ...]] = {
            name: tuple(group) for name, group in entries_by_table.items()
        }
        self.entries_by_copybook_file: dict[
            RepoPath, tuple[DictionaryEntry, ...]
        ] = {
            file: tuple(group)
            for file, group in entries_by_copybook_file.items()
        }
        self.copybook_files_by_record: dict[str, tuple[RepoPath, ...]] = {
            record: tuple(files)
            for record, files in copybook_files_by_record.items()
        }
        self.copybook_record_names: tuple[str, ...] = tuple(
            copybook_files_by_record
        )
        self.tables_by_name: dict[TableName, TableRecord] = tables_by_name
        self.tables_by_handler: dict[
            HandlerName, tuple[TableRecord, ...]
        ] = {
            handler: tuple(group)
            for handler, group in tables_by_handler.items()
        }
        # A bridge is indexed under the name `TableRecord.bridge` gives it,
        # reached by joining through the tables the bridge itself declares.
        # That name is DERIVED FROM THE DOCUMENT rather than from string
        # surgery on a path, so the key is exactly the value a caller already
        # holds - `table_for("GLPOSTING-REC").bridge` is `glpostingMT` - and
        # the two can never disagree. A bridge that declares no in-scope
        # table would not be indexed here and stays reachable through
        # `sources().bridges`; all twenty in-scope pairs declare at least one.
        bridges_by_name: dict[BridgeName, BridgeSource] = {}
        for bridge in document.sources.bridges:
            for bridge_table in bridge.tables:
                named_by = tables_by_name.get(bridge_table.name)
                if named_by is not None:
                    bridges_by_name.setdefault(named_by.bridge, bridge)
        self.bridges_by_name: dict[BridgeName, BridgeSource] = bridges_by_name


# =============================================================================
#  THE MEMO
#
#  A plain mapping from absolute path to the document read from it, and a
#  second from the same path to that document's index. Both are private, both
#  are keyed by a path made absolute first, and neither is touched at import
#  time - importing this module reads nothing.
#
#  This is a cache and not a lock: execution is strictly sequential, matching
#  the single-threaded COBOL, so there is no synchronisation primitive here
#  and none is needed (rule R-3). Two reads of one path in one process would
#  be harmless anyway - the document is immutable - but twenty-seven record
#  modules importing at start-up should cost one read between them, not
#  twenty-seven.
# =============================================================================

_DOCUMENTS: dict[Path, DataDictionary] = {}
_INDEXES: dict[Path, _DocumentIndex] = {}


def load_dictionary(path: Path | None = None) -> DataDictionary:
    """Return the whole data dictionary, reading it at most once per path.

    Args:
        path: An explicit artifact path, or None for the repository's own
            `data_dictionary/acas_posting_dictionary.json`. The override is
            the sanctioned escape hatch for a test, or for a deployment that
            keeps the artifact somewhere else - see the wheel-absence caveat
            in this module's docstring.

    Returns:
        The document as an immutable tree of `model` records: `meta`,
        `sources`, `tables`, `entries` and `coverage`. Repeated calls for one
        path return THE SAME OBJECT, so a caller may compare with `is`. That
        is safe because every record is a frozen dataclass whose collections
        are tuples, so no holder can alter what another holder sees.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
        DictionaryNumericPolicyError: A parsed value is outside the shapes
            the model admits (rule R-2).

    Two spellings of one file share one entry, because the path is made
    absolute before it is used as the memo key. Nothing is read at import
    time: the first call to this function is the first time this module
    touches a disk.
    """
    absolute_path = _absolute_document_path(path)
    document = _DOCUMENTS.get(absolute_path)
    if document is None:
        document = _read_document(absolute_path)
        _DOCUMENTS[absolute_path] = document
    return document


def clear_cache() -> None:
    """Discard every memoised document and index.

    Support for a test that needs a genuinely cold read in a process that has
    already taken a warm one - for instance one asserting that a missing
    artifact reports itself properly. It is not part of ordinary use: the
    artifact is a committed file and does not change under a running program.

    Nothing else in this module mutates state, so calling this leaves every
    accessor a pure function of whatever document it next reads.
    """
    _DOCUMENTS.clear()
    _INDEXES.clear()


def _index(path: Path | None) -> _DocumentIndex:
    """Return the lookup tables for one document, building them at most once.

    Args:
        path: The artifact path, or None for the repository's own.

    Returns:
        The private index over that document.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
        DictionaryNumericPolicyError: A parsed value is outside the shapes
            the model admits (rule R-2).
    """
    absolute_path = _absolute_document_path(path)
    index = _INDEXES.get(absolute_path)
    if index is None:
        index = _DocumentIndex(load_dictionary(absolute_path))
        _INDEXES[absolute_path] = index
    return index


# =============================================================================
#  FAILURE MESSAGES THAT TEACH  (rule R-5)
#
#  A record module reaches this module because rule R-5 requires every field
#  to cite a dictionary entry. When a key does not match, the wrong outcome is
#  for its author to give up and hand-write the metadata instead - that is the
#  transcription error the data-dictionary-first directive exists to prevent.
#  So a miss states the convention, shows the nearest keys the document really
#  carries, and says outright not to hand-code the field.
# =============================================================================


def _nearest(name: str, candidates: tuple[str, ...]) -> tuple[str, ...]:
    """Return the candidates closest to `name`, best first, at most five.

    Args:
        name: The name that matched nothing.
        candidates: Every name the document does carry, in document order.

    Returns:
        Up to `_SUGGESTION_LIMIT` near misses, or the members of the same
        qualified group when nothing is close enough - a wrong column name
        under a right table name is the common slip, and listing that table's
        real columns answers it directly. Empty when neither applies.

    This is the ONE place in this module where an order other than document
    order is produced, and it is deterministic: the standard library's
    similarity ranking is a pure function of the two strings, and the
    fallback preserves document order. Nothing here reaches a returned
    entry, a table or a citation - only a failure message.
    """
    close = tuple(
        difflib.get_close_matches(name, candidates, _SUGGESTION_LIMIT)
    )
    if close:
        return close
    qualifier, separator, _ = name.partition(".")
    if separator:
        within = tuple(
            candidate
            for candidate in candidates
            if candidate.partition(".")[0] == qualifier
        )
        if within:
            return within[:_SUGGESTION_LIMIT]
    return ()


def _nearest_sentence(
    name: str, candidates: tuple[str, ...], noun: str
) -> str:
    """Return one line of suggestions, or a line saying there are none.

    Args:
        name: The name that matched nothing.
        candidates: Every name the document does carry, in document order.
        noun: What the candidates are, for the sentence - "keys", "tables".

    Returns:
        A single line, always ending in a newline, so a caller can
        concatenate it into a longer message without deciding spacing.
    """
    suggestions = _nearest(name, candidates)
    if not suggestions:
        return (
            f"This dictionary carries {len(candidates)} {noun}, none of them "
            "close.\n"
        )
    return f"Nearest {noun} in this dictionary: {', '.join(suggestions)}\n"


def _unknown_entry_key_message(
    key: str, index: _DocumentIndex, path: Path
) -> str:
    """Return the failure text for a key no entry carries.

    Args:
        key: The key that matched nothing, quoted back verbatim.
        index: The document's index, for the candidate keys and the tally.
        path: The document that was read, so the reader knows which file was
            searched when an override path is in play.

    Returns:
        The complete message: the key, both key forms, the warning against
        keying by field name alone, the nearest keys, and the instruction not
        to hand-code the field's metadata.
    """
    return (
        f"No entry in the ACAS posting data dictionary is keyed {key!r}.\n"
        "\n"
        "An entry key takes one of two forms, and both are qualified:\n"
        "    <TABLE-NAME>.<COLUMN-NAME>      where a column backs the "
        "field, for example IRSPOSTING-REC.POST4-DAY\n"
        "    <COPYBOOK-RECORD>.<FIELD-NAME>  where the field is "
        "copybook-only, for example File-Access.Fs-Reply\n"
        "Both halves are the names the frozen sources use themselves: "
        "hyphens are not turned into underscores and case is not folded, so "
        "lookup is exact and case-sensitive. Where one field name repeats "
        "inside one record the key carries a '#' and the declaration line.\n"
        "\n"
        "Never key by field name alone. PSIRSPOST-REC (the transfer file "
        "the Sales and Purchase programs write, ten columns, handler "
        "acas008) and IRSPOSTING-REC (the internal IRS posting file, "
        "thirteen columns, handler acasirsub4) have near-identical field "
        "names, and [copybooks/wspost-irs.cob:L6-L7] says so outright: "
        '"This is NOT the same as the internal IRS posting file".\n'
        "\n"
        f"{_nearest_sentence(key, index.entry_keys, 'keys')}"
        f"Read from: {path}\n"
        "\n"
        "Correct the key rather than hand-writing the field's metadata. Rule "
        "R-5 requires every field to cite its dictionary entry, and a "
        "hand-written descriptor is precisely the transcription error that "
        "requirement exists to prevent."
    )


def _unknown_name_message(
    noun: str,
    name: str,
    candidates: tuple[str, ...],
    path: Path,
    guidance: str,
) -> str:
    """Return the failure text for a spine name the document does not carry.

    Args:
        noun: The plural noun for what was looked up - "tables", "handlers".
        name: The name that matched nothing, quoted back verbatim.
        candidates: Every such name the document carries, in document order.
        path: The document that was read.
        guidance: One sentence on where the right name comes from.

    Returns:
        The complete message: the name, the suggestions, the source of the
        document and the guidance.
    """
    return (
        f"The ACAS posting data dictionary carries no entry for {noun[:-1]} "
        f"{name!r}.\n"
        f"{_nearest_sentence(name, candidates, noun)}"
        f"{guidance}\n"
        f"Read from: {path}"
    )


# =============================================================================
#  THE DOCUMENT'S OWN THREE HEADERS
# =============================================================================


def meta(*, path: Path | None = None) -> Meta:
    """Return the document's identity block.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Meta` - the dictionary's name and version, the reference to its JSON
        Schema, what generated it, the statement of whose authority it
        carries, the determinism contract it was written under, the
        derivation rules it followed, and the binding rules it was built to
        satisfy.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return load_dictionary(path).meta


def sources(*, path: Path | None = None) -> Sources:
    """Return the catalogue of the frozen sources the document was built from.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Sources` - the frozen schema dump, the twenty in-scope bridge pairs
        and the in-scope copybooks. The bridge records carry the key metadata
        the data-access layer needs to emulate ISAM positioning: each key's
        name in the database, its offset, its length and its type, with the
        locator of the directive that declares it.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return load_dictionary(path).sources


def coverage(*, path: Path | None = None) -> Coverage:
    """Return the tallies that make the document's completeness checkable.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Coverage` - how many tables the frozen schema declares and how many
        are in scope, how many bridges each way, how many in-scope columns
        there are and how many the document covers, how many host variables
        and copybook fields it covers, and the keys of every one-sided entry.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    A one-sided entry is a finding, not a fault: a copybook-only working
    storage field and a bridge-derived column with no copybook counterpart
    are both legitimate, and both are recorded rather than dropped.
    """
    return load_dictionary(path).coverage


# =============================================================================
#  ENTRIES
# =============================================================================


def entries(*, path: Path | None = None) -> tuple[DictionaryEntry, ...]:
    """Return every entry, in document order.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        All entries as the document records them - tables by name ascending,
        within a table by column ordinal, then that table's copybook-only
        fields, then the copybook-only fields belonging to no table. Nothing
        is filtered: one-sided entries are included, because their existence
        is the point.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return load_dictionary(path).entries


def entry_keys(*, path: Path | None = None) -> tuple[EntryKey, ...]:
    """Return every entry key, in document order.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The key of every entry, in the same order `entries` yields them.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return _index(path).entry_keys


def get_entry(key: str, *, path: Path | None = None) -> DictionaryEntry:
    """Return the entry a key names. The primary accessor.

    Args:
        key: `<TABLE-NAME>.<COLUMN-NAME>` where a column backs the field, or
            `<COPYBOOK-RECORD>.<FIELD-NAME>` where it is copybook-only.
            Exact and case-sensitive, because both halves are the names the
            frozen sources use themselves.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The entry: the three views, the drift between them, any derivation,
        the storage class this migration gives it, and its notes, anomaly
        references and ambiguity references. Each view carries its own
        `source` locator into the frozen tree, which is what makes rule R-5's
        field-level traceability mechanical.

    Raises:
        DictionaryKeyError: No entry carries that key. The message states
            both key forms, warns against keying by field name alone, offers
            the nearest keys and says not to hand-code the metadata instead.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    What comes back is reported, never adjudicated. Where the three views
    disagree the entry carries all three and flags the disagreement in
    `drift`; this module names no winner (rule R-4).
    """
    index = _index(path)
    entry = index.entries_by_key.get(key)
    if entry is None:
        raise DictionaryKeyError(
            _unknown_entry_key_message(
                key, index, _absolute_document_path(path)
            )
        )
    return entry


def find_entry(
    key: str, *, path: Path | None = None
) -> DictionaryEntry | None:
    """Return the entry a key names, or None when no entry carries it.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The entry, or None. The non-raising variant of `get_entry`, for a
        caller that is genuinely asking whether a field is catalogued - a
        report, or a test over a whole record. A record module defining a
        field should use `get_entry` instead, so that a mistyped key fails
        loudly rather than quietly yielding no metadata.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return _index(path).entries_by_key.get(key)


def entries_for_table(
    table: TableName, *, path: Path | None = None
) -> tuple[DictionaryEntry, ...]:
    """Return one table's entries, in the column ordinal order of the schema.

    Args:
        table: A table name as the frozen schema dump declares it, upper case
            with hyphens - for example `SALEDGER-REC`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Every entry the document maps to that table, in document order, which
        for a table is the column ordinal the frozen dump fixes. IRSPOSTING-REC
        therefore comes back with POST4-DAY, POST4-MONTH and POST4-YEAR at
        positions four, five and six - interleaved between POST4-DAT and
        POST4-DR as the dump has them, not appended after the copybook's own
        columns, which is exactly why a positional reading of that table
        needs this order and not the copybook's.

    Raises:
        DictionaryLookupError: The document knows no such table. The message
            offers the nearest table names.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    The copybook-only fields of the records behind a table are NOT part of
    this result: they map to no column and the document gives them no table.
    Reach them through `entries_for_copybook_record`.
    """
    index = _index(path)
    if table not in index.tables_by_name:
        raise DictionaryLookupError(
            _unknown_name_message(
                "tables",
                table,
                tuple(index.tables_by_name),
                _absolute_document_path(path),
                "The twenty-two in-scope table names are the ones the frozen "
                "schema dump declares; `tables()` lists them with their "
                "handler, bridge, entity facade and primary key.",
            )
        )
    return index.entries_by_table.get(table, ())


def entries_for_copybook_record(
    record: str, *, path: Path | None = None
) -> tuple[DictionaryEntry, ...]:
    """Return the entries of every field of one copybook record.

    Args:
        record: A record name exactly as its copybook declares it - for
            example `WS-Batch-Record`, `File-Access` or the lower-case
            `maps03-ws`. Case-sensitive, like every other name here.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Every entry whose copybook view belongs to a copybook whose record is
        that one, in document order. For a record backed by a table that
        means its column-mapped entries first, in column ordinal order, then
        its copybook-only fields; for a working-storage record such as
        `File-Access` it is copybook declaration order throughout. Where a
        record name is declared by more than one copybook - `File-Defs` by
        thirty-three of them, `Default-Record`, `Final-Record`, `OI-Header`
        and `WS-OTM5-Record` by two each - the entries of all of them come
        back together; use `entries_for_copybook_file` to separate them, and
        `sources().copybooks` to see which files carry the record.

    Raises:
        DictionaryLookupError: No catalogued copybook declares that record.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    One-sided entries are included, and that is the point of this accessor
    for the record layer: the working storage of copybooks/wsfnctn.cob
    reaches no table at all, and a record module that dropped those fields
    would be missing `We-Error`, `Fs-Reply` and the rest of the status block
    the whole data-access protocol is expressed in.

    This will not reorder the document. A caller that needs strict copybook
    declaration order has each entry's own `copybook.source` line to order
    by; re-sorting here would discard the ordering the artifact guarantees
    (rule R-6).
    """
    index = _index(path)
    files = index.copybook_files_by_record.get(record)
    if files is None:
        raise DictionaryLookupError(
            _unknown_name_message(
                "copybook records",
                record,
                index.copybook_record_names,
                _absolute_document_path(path),
                "A record name is the name on the group item the copybook "
                "declares; `sources().copybooks` lists every catalogued "
                "copybook with its record name.",
            )
        )
    if len(files) == 1:
        return index.entries_by_copybook_file.get(files[0], ())
    collected: list[DictionaryEntry] = []
    for file in files:
        collected.extend(index.entries_by_copybook_file.get(file, ()))
    return tuple(collected)


def entries_for_copybook_file(
    file: RepoPath, *, path: Path | None = None
) -> tuple[DictionaryEntry, ...]:
    """Return the entries of every field one copybook file declares.

    Args:
        file: The copybook's repository-relative path, exactly as the
            document records it - for example `copybooks/wssl.cob`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Every entry whose copybook view comes from that file, in document
        order. The precise form of `entries_for_copybook_record`, for the
        five record names that more than one copybook declares.

    Raises:
        DictionaryLookupError: The document catalogues no such copybook, or
            catalogues it with no field of its own.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    index = _index(path)
    entries_of_file = index.entries_by_copybook_file.get(file)
    if entries_of_file is None:
        raise DictionaryLookupError(
            _unknown_name_message(
                "copybook files",
                file,
                tuple(index.entries_by_copybook_file),
                _absolute_document_path(path),
                "A copybook path is repository-relative with forward "
                "slashes; `sources().copybooks` lists every catalogued "
                "copybook.",
            )
        )
    return entries_of_file


# =============================================================================
#  THE THREE VIEWS, HANDED OVER SEPARATELY  (rule R-4)
#
#  Three accessors, one per layer, and no fourth that merges them. Each may
#  answer None, and None is a RECORDED FACT rather than a failure: a
#  copybook-only working-storage field has no host variable and no column, and
#  the three date components the bridge derives at
#  [common/irspostingMT.cbl:L982-L987] have no copybook at all. A caller must
#  say which layer it means, because the layers disagree and the disagreement
#  is behaviour that has to be reproduced.
# =============================================================================


def copybook_field_for(
    key: str, *, path: Path | None = None
) -> CopybookField | None:
    """Return the copybook view of one field, or None where it has none.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `CopybookField` - the declaring file and line, the level, the picture
        text, the usage with where that usage was declared and which group it
        was inherited from, signedness with the sign position and the sign
        clause text verbatim, the digit counts and scale, the character
        length, any REDEFINES or OCCURS, and the 88-level condition names.
        None where no copybook declares the field.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    This is the view `acas_posting/cobol/field.py` builds a descriptor from,
    and reading `usage` from here rather than from the picture line is not a
    nicety: twenty-four in-scope fields inherit COMP-3 from a group -
    `03 Amounts comp-3.` [copybooks/wsbatch.cob:L40] over four batch amounts,
    and two group items in copybooks/wssys4.cob over ten period totals each -
    so `usage_declared_at` is GROUP and `usage_inherited_from` names the
    group. A caller that read the picture line alone would class every one of
    them as DISPLAY and store every one of them wrongly.

    `sign_clause_text` comes back exactly as written, which means both
    spellings survive: `sign leading` at [copybooks/wspost-irs.cob:L21] and
    `sign is leading` at [copybooks/irswspost.cob:L14]. Neither is
    normalised (rule R-4).
    """
    return get_entry(key, path=path).copybook


def host_variable_for(
    key: str, *, path: Path | None = None
) -> BridgeHostVariable | None:
    """Return the bridge host-variable view of one field, or None.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `BridgeHostVariable` - the declaring bridge file and line, the
        host-variable group and its suffix, the name, the picture text, the
        usage, signedness, digit counts, scale and character length, whether
        the bridge's load paragraph actually moves the record's field into it
        and where, whether the unload paragraph moves it back and where, and
        whether the group is INITIALIZEd before the load. None where no
        bridge carries the field.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    `loaded_from_record` and `unloaded_to_record` are the two members a naive
    reading would assume rather than check. `HV-POST-RRN` is declared at
    [common/glpostingMT.cbl:L282] and the load paragraph makes no move into
    it, so nothing from the passed record reaches it and nothing read comes
    back through it; both flags are false and `notes` says why. The
    data-access layer reproduces that, and `group_initialised_before_load` is
    why every column of the frozen schema can be NOT NULL: an unset host
    variable holds zero or space, never SQL NULL, so the Python layer must
    default rather than omit.
    """
    return get_entry(key, path=path).bridge_host_variable


def column_for(key: str, *, path: Path | None = None) -> MysqlColumn | None:
    """Return the column view of one field, or None where it has none.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `MysqlColumn` - the schema file and line, the column name, the SQL
        type as written with its base type, the display width and scale,
        whether it is unsigned, whether it is nullable, its default, whether
        it is the primary key, its ordinal within the table, and any comment.
        None for a copybook-only field, which is the ordinary case for
        working storage.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return get_entry(key, path=path).column


def drift_for(key: str, *, path: Path | None = None) -> Drift:
    """Return what disagrees between the three views of one field.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Drift` - a flag per axis (signedness, usage, digits, scale,
        character length, name) and a line of detail per disagreement. Never
        None: an entry always carries this record, with every flag false and
        no details where the views agree.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    THIS REPORTS THE DISAGREEMENT AND SETTLES NOTHING. Agent Action Plan
    section 0.6.2 is explicit about why the data-access layer needs it:
    `Sales-Average` is signed `binary-long` in the copybook
    [copybooks/wssl.cob:L49], unsigned in the host variable
    [common/salesMT.cbl:L308] and unsigned in the column, so "a negative
    value computed in COBOL loses its sign at the bridge, not at the database
    - so the Python data-access layer must reproduce the bridge's conversion,
    not merely write the computed value and let MySQL complain. By contrast
    the monetary fields are declared signed at all three layers and pass
    through cleanly, so the drift is specific rather than systemic and must
    be handled field by field from the dictionary."

    `SALEDGER-REC.SALES-CURRENT` is that contrast: same record, same bridge,
    no signedness drift at all. Which is why there is no accessor here that
    reports one signedness for a field.
    """
    return get_entry(key, path=path).drift


def derivation_for(
    key: str, *, path: Path | None = None
) -> Derivation | None:
    """Return how the bridge derives a column that no record supplies.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Derivation` - the kind of derivation, the expression as the bridge
        writes it, the guard that expression sits under, what happens when
        that guard does not hold, and the locator of both. None for the great
        majority of fields, which the bridge simply moves.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    The case this exists for is IRSPOSTING-REC.POST4-DAY, POST4-MONTH and
    POST4-YEAR, whose guarded moves are at
    [common/irspostingMT.cbl:L982-L987]. When a guard does not hold the move
    is not made, so the component keeps the zero left by the group
    INITIALIZE while the whole date text is still stored in POST4-DAT - a row
    that is internally inconsistent. `guard_failure_behaviour` states that,
    and the data-access layer reproduces it rather than repairing it
    (rule R-4, anomaly A-7).
    """
    return get_entry(key, path=path).derivation


# =============================================================================
#  THE ENTITY - HANDLER - BRIDGE - TABLE SPINE
#
#  What the data-access layer resolves a call through. The correspondence is
#  not one-to-one in either direction: seventeen handlers reach twenty-two
#  tables through twenty bridges, `acas000` dispatches to four tables by
#  file-key number, and `acas016` and `acas026` each own a header table and a
#  lines table - so the spine is looked up, never inferred from a name.
# =============================================================================


def tables(*, path: Path | None = None) -> tuple[TableRecord, ...]:
    """Return every in-scope table with its place in the spine.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        A `TableRecord` per in-scope table, in document order: the table
        name, the bridge pair that maps it, the handler the posting programs
        call to reach it, the entity facade they address it through, the
        copybooks behind it, its primary key, its column count and the
        locator of the schema lines that fix its column ordinals.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return load_dictionary(path).tables


def table_names(*, path: Path | None = None) -> tuple[TableName, ...]:
    """Return the name of every in-scope table, in document order.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The twenty-two in-scope table names.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return tuple(_index(path).tables_by_name)


def table_for(
    table: TableName, *, path: Path | None = None
) -> TableRecord:
    """Return one table's place in the spine.

    Args:
        table: A table name as the frozen schema dump declares it.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        That table's `TableRecord`.

    Raises:
        DictionaryLookupError: The document knows no such table.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    index = _index(path)
    table_record = index.tables_by_name.get(table)
    if table_record is None:
        raise DictionaryLookupError(
            _unknown_name_message(
                "tables",
                table,
                tuple(index.tables_by_name),
                _absolute_document_path(path),
                "The twenty-two in-scope table names are the ones the frozen "
                "schema dump declares; `tables()` lists them with their "
                "handler, bridge, entity facade and primary key.",
            )
        )
    return table_record


def find_table(
    table: TableName, *, path: Path | None = None
) -> TableRecord | None:
    """Return one table's place in the spine, or None when it has none.

    Args:
        table: A table name as the frozen schema dump declares it.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        That table's `TableRecord`, or None - which for one of the eleven
        out-of-scope tables of the frozen schema is the right answer rather
        than a failure, since the posting cycle never touches them.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return _index(path).tables_by_name.get(table)


def tables_for_handler(
    handler: HandlerName, *, path: Path | None = None
) -> tuple[TableRecord, ...]:
    """Return every table one file handler reaches, in document order.

    Args:
        handler: A handler program name - `acas000` through `acas029`, or
            `acasirsub1` through `acasirsub5`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The tables that handler owns. Usually one; four for `acas000`, which
        dispatches by file-key number, and two each for `acas016` and
        `acas026`, which own a header table and a lines table.

    Raises:
        DictionaryLookupError: No in-scope table names that handler.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    index = _index(path)
    handled = index.tables_by_handler.get(handler)
    if handled is None:
        raise DictionaryLookupError(
            _unknown_name_message(
                "handlers",
                handler,
                tuple(index.tables_by_handler),
                _absolute_document_path(path),
                "The seventeen in-scope handlers are the numbered file "
                "handlers the posting programs call; `tables()` shows which "
                "handler reaches which table.",
            )
        )
    return handled


def bridge_for(
    bridge: BridgeName, *, path: Path | None = None
) -> BridgeSource:
    """Return one bridge pair, with the key metadata the DAL positions on.

    Args:
        bridge: A bridge pair's stem, lower case and ending in `MT` - for
            example `glpostingMT`. This is the name `TableRecord.bridge`
            carries.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `BridgeSource` - the pair's two paths, the database the embedded
        directive names, the locator of that directive, the tables and
        host-variable groups it declares, its keys with each one's name in the
        database, offset, length, type and locator, the names and locators of
        its load and unload paragraphs, and whether the host-variable group is
        INITIALIZEd before a load.

    Raises:
        DictionaryLookupError: The document catalogues no such bridge.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    The key metadata is what `acas_posting/dal/cursor_state.py` emulates ISAM
    positioning from: a START followed by READ NEXT is reproduced against the
    key the bridge itself declares, not against an ordering invented in
    Python.
    """
    index = _index(path)
    bridge_source = index.bridges_by_name.get(bridge)
    if bridge_source is None:
        raise DictionaryLookupError(
            _unknown_name_message(
                "bridges",
                bridge,
                tuple(index.bridges_by_name),
                _absolute_document_path(path),
                "The twenty in-scope bridges are the pairs the posting cycle "
                "reaches; `tables()` shows which bridge maps which table.",
            )
        )
    return bridge_source


# =============================================================================
#  CITATION  (rule R-5 made usable)
# =============================================================================


def _view_locator(
    view: CopybookField | BridgeHostVariable | MysqlColumn | None,
) -> str:
    """Return one view's source locator, or the marker for an absent view.

    Args:
        view: One of an entry's three views, or None.

    Returns:
        The view's `source` locator - a repository-relative path and a line
        reference - or `absent`, which is itself a fact worth printing.
    """
    return _ABSENT_VIEW if view is None else view.source


def cite(key: str, *, path: Path | None = None) -> str:
    """Return a one-line provenance citation for one field.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The key followed by the locator of each of its three views, in layer
        order, two spaces between segments and no newline - short enough for
        a log line, a comment or a docstring:

            SALEDGER-REC.SALES-AVERAGE  copybook=copybooks/wssl.cob:L49
            bridge=common/salesMT.cbl:L308  column=mysql/ACASDB.sql:L969

        An absent view prints as `absent` rather than being dropped, so a
        one-sided field states its one-sidedness:

            IRSPOSTING-REC.POST4-DAY  copybook=absent
            bridge=common/irspostingMT.cbl:L177  column=mysql/ACASDB.sql:L278

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.

    This is rule R-5 made usable. It is how a record module, a log line or a
    docstring literally cites its dictionary entry, and it is the cheapest
    path a reviewer has from a line of Python to the frozen COBOL or SQL line
    that defines the field - paste a segment into an editor and the
    specification is on screen. The locators come from the document, so a
    citation cannot drift from what was catalogued.

    Nothing is echoed but locators. The connection block of
    copybooks/wsfnctn.cob is catalogued as field layouts only - the frozen
    source holds no credential, `DB-UPass` being `pic x(12) value spaces` -
    and no accessor here prints or logs a value of any field.
    """
    entry = get_entry(key, path=path)
    return "  ".join(
        (
            entry.key,
            f"copybook={_view_locator(entry.copybook)}",
            f"bridge={_view_locator(entry.bridge_host_variable)}",
            f"column={_view_locator(entry.column)}",
        )
    )


# =============================================================================
#  PUBLIC SURFACE
#
#  The failures first, then the accessors, each group in alphabetical order. A
#  tuple rather than a list, so the surface cannot be reordered, extended or
#  mutated in place at run time, and alphabetical so the order is a mechanical
#  consequence of the names instead of an editorial choice - both small
#  determinism guarantees in the spirit of rule R-6.
#
#  Everything else here is private: the index, the memo, the parse boundary
#  and the message builders. A caller gets accessors, never a mapping it
#  could mutate.
# =============================================================================

__all__: Final[tuple[str, ...]] = (
    # The failures.
    "DictionaryError",
    "DictionaryKeyError",
    "DictionaryLookupError",
    "DictionaryNotFoundError",
    "DictionaryNumericPolicyError",
    "DictionaryParseError",
    # The accessors.
    "bridge_for",
    "cite",
    "clear_cache",
    "column_for",
    "copybook_field_for",
    "coverage",
    "derivation_for",
    "drift_for",
    "entries",
    "entries_for_copybook_file",
    "entries_for_copybook_record",
    "entries_for_table",
    "entry_keys",
    "find_entry",
    "find_table",
    "get_entry",
    "host_variable_for",
    "load_dictionary",
    "meta",
    "sources",
    "table_for",
    "table_names",
    "tables",
    "tables_for_handler",
)
