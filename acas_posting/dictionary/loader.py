"""Runtime lookup into the generated ACAS posting data dictionary.

This module is how field-level traceability reaches run time. Agent Action
Plan section 0.4.1.6 states its whole mandate in one line - "Runtime lookup
so every record field cites its entry" - and rule R-5 names it directly.

It reads exactly one file, `data_dictionary/acas_posting_dictionary.json`,
read-only and lazily, and hands back the immutable record tree that
`acas_posting.dictionary.model` defines. It computes nothing, coerces
nothing and repairs nothing.

WHY A LOOKUP MODULE EXISTS AT ALL
=================================
Section 0.3.3 names the pattern - field metadata "derived, not transcribed" -
and section 0.8.1 makes the ordering a directive: the dictionary is generated
from the bridge BEFORE record definitions are written. The authority is not
the copybooks' but the maintainer's one-way bridge, preserved in section
0.8.2 as the user's own requirement:

    "The maintainer's one-way COBOL-to-MySQL bridge defines the
    authoritative record-layout <-> table mapping - it is the data
    dictionary for this migration."

So a record module needing a field's places, scale, signedness, usage or sign
position asks here, by key, rather than reading a picture clause by eye. That
is not stylistic: the sales-ledger statistics fields are declared
`binary-long` [copybooks/wssl.cob:L46-L52], so truncation on divide is
INTEGER truncation - exactly what makes the moving-average defect of
[sales/sl060.cbl:L826-L827] reproducible.

THE KEY CONVENTION - AND WHY IT IS ALWAYS QUALIFIED
===================================================
An entry is addressed by one key, in one of two forms:

    <TABLE-NAME>.<COLUMN-NAME>      a column backs the field, for example
                                    IRSPOSTING-REC.POST4-DAY
    <COPYBOOK-RECORD>.<FIELD-NAME>  copybook-only, for example
                                    File-Access.Fs-Reply

Both halves are the names the frozen sources use, unaltered: hyphens stay
hyphens and case is not folded, so a key can be searched for in the COBOL and
in the schema exactly as it stands. Lookup is exact and case-sensitive.

NEVER KEY BY FIELD NAME ALONE. Qualification keeps apart two tables that
would otherwise merge: PSIRSPOST-REC is the transfer file the Sales and
Purchase programs write, through `acas008` and `slpostingMT`, ten columns;
IRSPOSTING-REC is the internal IRS posting file, through `acasirsub4` and
`irspostingMT`, thirteen. Their field names are near-identical and
[copybooks/wspost-irs.cob:L6-L7] says so: "This is NOT the same as the
internal IRS posting file". Where one field name repeats inside one record -
`filler` occurs four times in copybooks/wsledger.cob - the key carries a `#`
and the declaration line.

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!  THIS MODULE RESOLVES NOTHING  (rule R-4)                            !!
!!                                                                      !!
!!  A DEFECT REPRODUCED IS CORRECT; A DEFECT FIXED IS A FAILURE.        !!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

An entry records the copybook field, the bridge host variable and the column
as three independent sibling views, plus the drift between them, and stops
there. There is deliberately no accessor - and none may be added - naming one
winning type across the views: no resolved, canonical, effective, corrected,
recommended or preferred type, because a caller handed one would use it and
the disagreement would leave the system. A caller wanting "the type" must say
which layer it means. The disagreements are load-bearing behaviour:

  * `Sales-Average` is signed `binary-long` [copybooks/wssl.cob:L49], becomes
    the unsigned `HV-SALES-AVERAGE PIC 9(10) COMP` [common/salesMT.cbl:L308]
    and lands in an unsigned column, so a negative value LOSES ITS SIGN AT
    THE BRIDGE, not at the database - section 0.6.2 requires the data-access
    layer to reproduce that conversion field by field.
    `SALEDGER-REC.SALES-CURRENT` proves the drift specific rather than
    systemic: signed at all three layers, no drift at all.
  * `Ledger-Name` is 24 characters in the copybook and 32 in both the host
    variable [common/nominalMT.cbl:L299] and the column
    [mysql/ACASDB.sql:L127], so a table dump's padding is not the copybook's.
  * POST4-DAY, POST4-MONTH and POST4-YEAR have NO copybook view at all. The
    bridge derives them from two-character slices of a date string under a
    guard [common/irspostingMT.cbl:L982-L987]; when a guard does not hold the
    move is simply not made, so the component keeps the zero left by the
    group INITIALIZE while the raw date text is stored anyway.
  * `HV-POST-RRN` is declared [common/glpostingMT.cbl:L282] and never loaded
    from the record, so `loaded_from_record` is false and `notes` says why.

`notes`, `anomaly_refs`, `ambiguity_refs`, `drift` and `derivation` are DATA
THIS MODULE RETURNS, never a reason to complain: a loader logging "signedness
drift" would invite exactly the correction rule R-4 forbids. `ambiguity_refs`
keeps an unsettled question visible - the batch-record length contradiction
[copybooks/wsbatch.cob:L7-L9] is one of the five in section 0.6.8.

WHERE THE ARTIFACT LIVES, AND WHICH COPY IS READ
================================================
There are two spellings of one artifact, and this module is where the choice
between them is made - because making it means asking the filesystem which
one is there, and `acas_posting/__init__.py` deliberately touches no file.

  1. THE PACKAGED COPY, `acas_posting/data_dictionary/…`, reached through
     `importlib.resources`. pyproject.toml maps the committed directory into
     the distribution as package data, so an INSTALLED distribution carries
     it. This copy is preferred, and it has to exist, because twenty-five
     record modules and two of the COBOL semantics modules resolve their
     field metadata AT IMPORT TIME: without it, `import
     acas_posting.records.gl_posting` would fail inside a wheel long before
     any caller could reach the `path=` override below.
  2. THE REPOSITORY COPY, `data_dictionary/…` beside the package, which is
     what `DATA_DICTIONARY_PATH` names. It is the committed original - the
     one `acas_posting.dictionary.generate` writes and the one the oracle
     scripts and the test suites read - and it is the copy present in a
     SOURCE CHECKOUT, where the build-time mapping has not run.

The two are the same bytes by construction: the build copies the committed
file rather than regenerating it, so there is exactly one source of truth and
no way for the two to disagree. Both paths come from `acas_posting/__init__`
by name rather than being re-derived here, because two derivations of one
fact drift apart eventually.

On top of that ordered lookup this module owns two behaviours:

  * every accessor takes an explicit `path` override, which is the
    sanctioned escape hatch for a test or a relocated deployment;
  * absence of BOTH copies raises `DictionaryNotFoundError` naming each
    candidate that was looked at and the remedies. It does NOT fall back to
    an empty dictionary, and it does NOT regenerate the artifact.

With the artifact shipped, an absence now means a damaged installation, a
checkout the generator has never been run in, or an explicit `path` naming
somewhere wrong - not the ordinary consequence of installing the package.

LAYERING - THE NARROWEST IMPORT SURFACE IN THE PACKAGE
======================================================
Section 0.4.3 fixes the layering, and two whole layers reach their field
metadata through this module and nothing else: `cobol/*.py` may import
`dictionary.loader` ONLY, and `records/*.py` may import `cobol.field` and
`dictionary.loader` only, "this keeps the record layer a leaf". Seven
semantics modules and twenty-seven record modules sit on that path. So this
module imports, from the whole of `acas_posting`, exactly two things: the
path constants from the package marker, and `dictionary.model`. Above all NOT
`dictionary.generate` - a build-time tool parsing the frozen COBOL tree and
schema, whose import here would put those parsers on the import path of every
record module and break section 0.4.3's promise that the arithmetic tier
"imports only `cobol` and `records` and touches no database, so it runs
anywhere". Any further import becomes a cycle the moment `cobol/field.py`
imports this module.

THIS MODULE IS THE ONLY DOOR ONTO THE OBJECT MODEL
==================================================
Because section 0.4.3 grants `cobol/*.py` and `records/*.py` this module and
NOT `dictionary.model`, and because every value those two layers receive from
an accessor here IS an instance of a `model` dataclass or enumeration, a
caller cannot annotate what it holds without naming those types. This module
therefore RE-EXPORTS them, under `RE-EXPORTED OBJECT MODEL` below, and they
are published in `__all__` alongside the accessors.

    CORRECT, from a `cobol/*.py` or `records/*.py` module:

        from acas_posting.dictionary.loader import ConditionName, Usage

    FORBIDDEN above this module: naming `dictionary.model` in an import at all.
    Section 0.4.3 does not list it for either layer, so reaching it there is a
    layering violation however narrow the need looks - and after the re-export
    below there is no need left.

Three properties make the re-export the right shape rather than a workaround:

  * It is a BINDING, not a copy. `loader.Usage is model.Usage` holds for every
    re-exported name, so there is exactly one definition of each vocabulary in
    the migration and no second source of truth for field metadata can appear
    (rule R-5). Re-declaring a competing enumeration in a consumer would be
    precisely the transcription error the dictionary exists to prevent.
  * It costs nothing at import time. `model` imports only the standard library,
    so it is already on this module's import path; naming its types here adds
    no file read, no dependency and no cycle.
  * It closes the layering hole structurally. With the types reachable from the
    sanctioned module, no consumer needs a local exception to section 0.4.3,
    and a reviewer can enforce the rule with one grep for
    `dictionary.model` outside `acas_posting/dictionary/`.

What is re-exported is exactly what the two layers annotate with: the three
view records, the cross-view records, the entry, the four enumerations, and
the locator pattern that `cobol/field.py` and `cobol/picture.py` validate a
`source_locator` against. Nothing that only the generator needs is re-exported
- no parser input record, no `to_json_obj` - because a runtime consumer has no
use for it and publishing it would widen this surface for nothing.

NO IMPORT-TIME WORK, ONE READ PER PROCESS
=========================================
Importing this module reads no file, opens no connection and cannot fail for
an environmental reason: it binds names and nothing else. Loading is lazy and
explicit, and the parsed document is memoised per absolute path, so
twenty-seven record modules importing at start-up cost ONE read between them
and share one immutable tree - safe because every record in `model` is a
frozen dataclass whose collections are tuples.

DOCUMENT ORDER IS THE ORDER  (rule R-6)
=======================================
Every sequence returned here is in the order the document records it, and
nothing here re-sorts: the document's own ordering IS the determinism
contract, stated in `meta.determinism.array_order` - tables by name
ascending, within a table by the column ordinal the frozen dump fixes, then
that table's copybook-only fields in copybook declaration order, then the
copybook-only fields corresponding to no table at all. So
`entries_for_table` returns IRSPOSTING-REC with POST4-DAY, POST4-MONTH and
POST4-YEAR at positions 4, 5 and 6 - INTERLEAVED between POST4-DAT and
POST4-DR, as the frozen dump has them, not appended after the copybook's own
columns - and `entries_for_copybook_record` uses that same order, so a caller
needing strict copybook declaration order must sort by each field's own
`copybook.source` line itself.

Every accessor is otherwise a pure function of the document. Nothing here
consults a clock, an entropy source, the environment, distribution metadata
or the checkout, and no directory is listed anywhere.

NUMERIC POLICY  (rule R-2)
==========================
This module holds no value at all - it describes precision, it never carries
it - so it constructs no arithmetic type and imports no arithmetic module.
Places, scales, lengths, ordinals, widths and coverage counts come back as
`int`; pictures, SQL type names and sign clause text as `str`. Two guards
make that structural: the parse hands any real-number literal back as its own
text rather than a binary approximation, and the tree is then walked against
an ALLOW-LIST of the four scalar shapes `model.JsonValue` admits - text, a
dimensionless whole number, a flag and absence. Anything else fails with
`DictionaryNumericPolicyError`.

NO NEW VALIDATION, NO CONCURRENCY  (rule R-3)
=============================================
This module adds no member the document does not carry and synthesises no
default for one it lacks: `model.from_json_obj` fetches every member by name
with no fallback, and that failure surfaces exactly as raised. Nor is the
document checked against its JSON Schema here - that belongs to a test, and
no schema-checking library is in the pinned dependency set. No data
definition statement is emitted, no index or constraint proposed, no returned
string tidied. Execution is strictly sequential, matching the single-threaded
COBOL: the memo below is a plain mapping, with no thread, event loop, process
pool, connection pool or synchronisation primitive.

NO COBOL AT RUNTIME  (rule R-1)
===============================
This module is the proof of that rule, because it sits on the import path of
thirty-four others. It reads ONE JSON file: it parses no COBOL text, opens no
bridge, copybook or schema source, launches no child process, loads no
foreign library, looks for no compiler and reaches no part of the sibling
oracle tree, so it imports cleanly on a host with no COBOL toolchain and no
database. The COBOL locators throughout this file are citations for a reader,
which is what rule R-5 asks for; nothing here opens one.

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

The migration's traceability, anomaly and ambiguity documents are to be
written at a later boundary; when they exist they carry the wider mapping,
the reproduced defects and the open questions respectively.
"""

# PROVENANCE
# Every fact this module serves is derived from the maintainer's own one-way
# COBOL-to-MySQL bridge (common/*MT.scb and common/*MT.cbl), the record
# copybooks under copybooks/, and the frozen schema mysql/ACASDB.sql. Those
# trees are the specification for this migration and are never modified,
# reformatted, commented, relocated or built from here.

import difflib
import json
import os
import stat
from importlib import resources
from pathlib import Path
from typing import Final

from acas_posting import (
    DATA_DICTIONARY_PATH,
    DATA_DICTIONARY_SEARCH_PATH,
    PACKAGE_DATA_DICTIONARY_DIR,
)
from acas_posting.dictionary.model import (
    ENTRY_KEY_PATTERN,
    REPO_PATH_PATTERN,
    SOURCE_LOCATOR_PATTERN,
    BridgeHostVariable,
    BridgeName,
    BridgeSource,
    CobolPythonStorage,
    ConditionName,
    CopybookField,
    Coverage,
    DataDictionary,
    Derivation,
    DictionaryEntry,
    DictionaryIntegrityError,
    Drift,
    EntryKey,
    HandlerName,
    JsonObject,
    Meta,
    MysqlColumn,
    RepoPath,
    SignPosition,
    Sources,
    TableName,
    TableRecord,
    Usage,
    UsageDeclaredAt,
    from_json_obj,
)

# =============================================================================
#  RE-EXPORTED OBJECT MODEL  (Agent Action Plan section 0.4.3, rule R-5)
#
#  Agent Action Plan section 0.4.3 grants `cobol/*.py` this module and nothing
#  else from the package, and `records/*.py` this module plus `cobol.field`.
#  Every value the accessors below hand those layers is an instance of one of
#  the types imported above, so they are re-exported here and published in
#  `__all__`: this module is the sanctioned door onto the object model, and a
#  consumer above it must never import `acas_posting.dictionary.model`.
#
#  These are BINDINGS to the one definition, not copies - `loader.Usage is
#  model.Usage` - so no second source of truth for field metadata can appear
#  (rule R-5). The names are listed once, in the import above, and nowhere
#  re-declared; the tuple below exists only so that a reader, and a test, can
#  see which part of the object model the runtime layers are entitled to and
#  can assert the identity.
#
#  `SOURCE_LOCATOR_PATTERN` is included because `cobol/field.py` and
#  `cobol/picture.py` validate a caller-supplied `source_locator` against the
#  same pattern the generated artifact was written with; a second copy of that
#  pattern would be able to drift from the artifact. `ENTRY_KEY_PATTERN` and
#  `REPO_PATH_PATTERN` are included for the same reason: `cobol/field.py`
#  refuses to build a descriptor from an entry whose key or copybook path does
#  not match the shape the artifact was generated with, and that check has to
#  use the artifact's own patterns rather than a local restatement of them.
# =============================================================================

RE_EXPORTED_MODEL_NAMES: Final[tuple[str, ...]] = (
    # The locator pattern the artifact's own `source` strings are shaped by,
    # and the two provenance patterns an admitted entry is checked against.
    "ENTRY_KEY_PATTERN",
    "REPO_PATH_PATTERN",
    "SOURCE_LOCATOR_PATTERN",
    # The enumerations the two runtime layers key their behaviour on.
    "CobolPythonStorage",
    "SignPosition",
    "Usage",
    "UsageDeclaredAt",
    # The records an accessor returns, or returns a member of.
    "BridgeHostVariable",
    "ConditionName",
    "CopybookField",
    "Coverage",
    "DataDictionary",
    "Derivation",
    "DictionaryEntry",
    "Drift",
    "Meta",
    "MysqlColumn",
    "Sources",
    "TableRecord",
)

# =============================================================================
#  FAILURES
#  Six classes, each with one job, and each one a subclass of a built-in the
#  caller would already be catching: absence is also a `FileNotFoundError`, an
#  unreadable document is also a `ValueError`, and a miss is also a `KeyError`
#  because rule R-5's own instruction for the primary accessor is to raise a
#  `KeyError` subclass.
#  `DictionaryError` carries the message plainly. That matters for the two
#  `KeyError` subclasses in particular: `KeyError` renders as the REPR of its
#  argument, which would wrap a multi-line teaching message in quotes and
#  escape every newline in it, and the whole point of that message is to be
#  read.


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
                `acas_posting.DATA_DICTIONARY_PATH` did not supply.
        """
        super().__init__(message)
        self.message: str = message

    def __str__(self) -> str:
        """Return the message unaltered, without repr quoting."""
        return self.message


class DictionaryNotFoundError(DictionaryError, FileNotFoundError):
    """The dictionary artifact is not present at the path asked for.

    The artifact is committed as a repository sibling of the package AND
    installed as package data, so this means one of three things: the
    installation is damaged, the generator has never been run in this
    checkout, or an explicit `path` names somewhere wrong. The message
    names the absolute path that was looked at, both locations
    `acas_posting/__init__.py` resolves between, and the remedies.

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


class DictionaryUntrustedError(DictionaryParseError):
    """The document parsed, but it is not the dictionary it claims to be.

    Raised when `model.check_integrity` rejects the document: a member the
    records do not declare, a member missing, a value outside its domain, a
    string that does not match its pattern, a pinned value replaced, an
    identifier repeated, a presence flag disagreeing with the view it
    describes, a coverage tally that does not match the entries actually
    present, or a source manifest that does not bind to itself.

    This is a distinct failure from `DictionaryParseError` because the two ask
    a caller to do different things. Unparseable bytes are a damaged file. A
    document that parses but does not hold up is a file that has been changed
    - by hand, by a partial regeneration, or by substitution - and the fix is
    to regenerate it from the frozen sources with
    `python -m acas_posting.dictionary.generate`, never to adjust it until it
    is accepted.

    Rule R-5 is why this stops the read rather than warning. Every record
    module cites this document for its field metadata; a document that is not
    the one the generator produced silently rewrites the picture, scale,
    signedness and storage class of several hundred fields, and no consumer
    downstream is in a position to notice.
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


#  THE PARSE BOUNDARY  (rules R-2 and R-3)

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


#: The artifact's file name, taken from the repository constant so that the
#: packaged candidate and the repository candidate can never name different
#: files.
_DOCUMENT_NAME: Final[str] = DATA_DICTIONARY_PATH.name


def _packaged_document_dir() -> Path | None:
    """This distribution's own copy of the dictionary directory, or None.

    Returns:
        The absolute directory holding the PACKAGED copy of the artifact, or
        None when this distribution is not one that keeps its data on a real
        filesystem.

    Asked of `importlib.resources` rather than assembled from `__file__`,
    because the packaged copy's location is a property of how the distribution
    was installed and `importlib.resources` is the interface that knows it.
    `resources.files()` returns a Traversable rooted at the package; for every
    ordinary installation - a wheel unpacked into site-packages, an editable
    install, a source checkout - that Traversable IS a `pathlib.Path`, so the
    packaged directory is one join away.

    A distribution imported from inside a zip archive would hand back a
    `zipfile.Path` instead. This function returns None for that case rather
    than adapting it, and the reason is worth stating instead of hiding: every
    path this module memoises, compares and prints is a real filesystem path,
    and widening that to an arbitrary Traversable would change the memo key,
    the `resolve()` call below and every error message for the sake of a
    deployment shape the Agent Action Plan does not describe. Returning None
    degrades to the repository candidate and, failing that, to a
    `DictionaryNotFoundError` that names where it looked - which is a truthful
    outcome rather than a silent one. `PACKAGE_DATA_DICTIONARY_DIR` is the
    fallback when the lookup itself is unavailable, so the answer never depends
    on import machinery being cooperative.
    """
    try:
        root = resources.files("acas_posting")
    # Exotic import machinery only - excluded from coverage because no
    # ordinary installation reaches it.
    except (ImportError, TypeError):  # pragma: no cover
        return PACKAGE_DATA_DICTIONARY_DIR
    if isinstance(root, Path):
        return root / PACKAGE_DATA_DICTIONARY_DIR.name
    return None


def _default_document_candidates() -> tuple[Path, ...]:
    """The absolute paths the DEFAULT document may occupy, in the order to try.

    Returns:
        One entry per legitimate location, packaged copy first and repository
        sibling second, each absolute and symlink-free. Never empty: the
        repository sibling is always a candidate, so a caller always has a
        path to name when reporting an absence.

    The order comes from `acas_posting.DATA_DICTIONARY_SEARCH_PATH` and is not
    re-decided here. An installed wheel holds only the packaged copy, a source
    checkout only the repository sibling, and an editable install can hold
    both - where the packaged copy is the one the distribution declares, which
    is why it is tried first.
    """
    packaged = _packaged_document_dir()
    out: list[Path] = []
    for directory in DATA_DICTIONARY_SEARCH_PATH:
        if directory == PACKAGE_DATA_DICTIONARY_DIR:
            if packaged is None:
                continue
            directory = packaged
        candidate = (directory / _DOCUMENT_NAME).resolve()
        if candidate not in out:
            out.append(candidate)
    return tuple(out)


def _absolute_document_path(path: Path | None) -> Path:
    """Return the absolute, symlink-free path of the document to read.

    Args:
        path: An explicit artifact path, or None for this distribution's own
            default. The override is the sanctioned escape hatch for a test, a
            regeneration workflow or a relocated deployment, and it is taken
            exactly as given - no search, no fallback, no second guess.

    Returns:
        The location to read, expressed absolutely, so that two spellings of
        one file - a relative path, a path through a symbolic link - share a
        single memo entry and therefore a single read. For the default, the
        first candidate that is actually a file; when none is, the LAST
        candidate, which is the repository sibling and therefore the most
        useful path to name in the absence message.

    THE DEFAULT LOOKUP IS ORDERED AND HAS EXACTLY TWO CANDIDATES, in this
    order: the packaged copy, which is the only one an installed distribution
    carries, then the repository copy, which is the only one a source
    checkout carries. Exactly one of the two exists in each of those two
    situations, so the order is a tie-break that never has to fire - but it
    is fixed rather than left to chance, because a lookup whose result could
    depend on which copy happened to be found first would put rule R-6's
    determinism in the hands of the deployment layout.

    When NEITHER exists, the repository path is returned so that the reader
    below reports a real, nameable location; `_absence_message` then names
    both candidates. Returning a path is not a claim that it is there:
    `Path.resolve()` asks the operating system to make the path absolute and
    symlink-free. It opens nothing, reads no content and - defaulting to
    non-strict - cannot raise for a path that is not there, so absence is
    reported by the reader below with a message that can explain itself,
    never by this helper. The `is_file()` probe on the default is a SELECTION
    between two declared locations, not a validation: it cannot raise, and
    when it finds nothing it still returns a path rather than an error.
    """
    if path is not None:
        return Path(path).resolve()
    candidates = _default_document_candidates()
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[-1]


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


class _RepeatedMember(Exception):
    """One JSON object carried the same member name twice.

    Private and deliberately narrow: it exists only to carry the offending
    name out of the object hook and into `_read_document`, which is the only
    place that knows which file is being read and can therefore say so.
    """

    def __init__(self, name: str) -> None:
        """Record the repeated member name."""
        super().__init__(name)
        self.name: str = name


def _object_from_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    """Build one JSON object from its member pairs, refusing any repeated name.

    Args:
        pairs: The members of one object, in the order the document wrote
            them, as the JSON reader hands them over.

    Returns:
        The object as a mapping, identical to what the reader would have built
        on its own for a document with no repeated member.

    Raises:
        _RepeatedMember: A member name occurs more than once.

    WHY THIS HOOK EXISTS. JSON permits a repeated member name and the standard
    reader resolves it by keeping the LAST occurrence silently. That makes a
    forged document trivial to hide inside a real one: append a second
    `"picture"` to an entry's copybook view, or a second `"scale"`, and the
    document still parses, still satisfies every later check - because by then
    the first value is simply gone - and quietly redefines a field. The
    duplicate is only visible while the members are still a list of pairs,
    which is here.

    The rest of the document's integrity is checked by
    `model.check_integrity`; a repetition is the one departure that cannot be
    detected after parsing, so it is the one this hook has to catch.
    """
    obj: dict[str, object] = {}
    for name, value in pairs:
        if name in obj:
            raise _RepeatedMember(name)
        obj[name] = value
    return obj


def _read_text_without_following_links(path: Path) -> str:
    """Read one file's text, refusing a symbolic link or anything but a plain file.

    Args:
        path: The absolute path of the artifact to read.

    Returns:
        The file's contents decoded as UTF-8.

    Raises:
        DictionaryNotFoundError: Nothing is at `path`, or what is there is not
            a plain file.
        OSError: The file exists and is plain but cannot be read.

    `Path.resolve()` has already followed every symbolic link in the path, so
    what remains is the window between that resolution and the open: a link
    substituted for the final component in that window would redirect this read
    to a file of the substituter's choosing, and the document read from it would
    be handed to every record module as authoritative field metadata (CWE-59,
    CWE-367). `O_NOFOLLOW` closes the window by refusing to open a final
    component that is a link at the moment of opening.

    The descriptor is then checked to be a regular file before a byte is read.
    A named pipe at the path would otherwise block the process indefinitely, and
    a character device would return contents that have nothing to do with a
    dictionary; both are absence as far as this module is concerned, and both
    are reported with the message that explains where the artifact should be.
    """
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        raise DictionaryNotFoundError(_absence_message(path)) from None
    except OSError as error:
        # ELOOP from O_NOFOLLOW, ENOTDIR from a path component that is not a
        # directory, EACCES from an unreadable file: none of them is a readable
        # artifact, and each is reported the same way so a caller has one thing
        # to handle.
        raise DictionaryNotFoundError(
            f"{_absence_message(path)}\n"
            f"The attempt to open it failed with: {error}"
        ) from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise DictionaryNotFoundError(
                f"{_absence_message(path)}\n"
                "Something is at that path, but it is not a plain file, so it "
                "is not the committed artifact."
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks).decode("utf-8")


def _read_document(path: Path) -> DataDictionary:
    """Read, parse, check and map one dictionary document. No memo, no fallback.

    Args:
        path: The absolute path of the artifact to read.

    Returns:
        The document as the immutable record tree `model` defines.

    Raises:
        DictionaryNotFoundError: Nothing readable is at `path`, or what is
            there is not a plain file.
        DictionaryParseError: The text is not parseable JSON, an object
            carries the same member name twice, or the top level is not an
            object.
        DictionaryNumericPolicyError: A parsed value is outside the shapes
            the model admits (rule R-2).
        DictionaryUntrustedError: The document parses but does not hold up as
            the dictionary it claims to be.

    `parse_float=str` is the numeric guard's first half: a real-number
    literal comes back as its own text rather than as a binary approximation
    of it, so no such value can be constructed even while the document is
    being read. The artifact carries no such literal - its numeric members
    are dimensionless counts - and the walk that follows is the second half,
    catching anything the reader still produces of its own accord.

    A member the document does not carry is NOT defaulted here. That failure
    belongs to `model.from_json_obj`, which fetches every member by name with
    no fallback, and it is allowed to surface exactly as raised (rule R-3).

    The order of the four steps is the point of this function. Nothing is read
    until the path is proved to be a plain file that is not a link; nothing is
    parsed until it is read; nothing is mapped to a record until the parsed
    tree has been proved to be the document the generator produced; and no
    caller - and no cache - is ever handed a partially trusted document.
    """
    if not path.is_file():
        raise DictionaryNotFoundError(_absence_message(path))
    text = _read_text_without_following_links(path)
    try:
        tree = json.loads(text, parse_float=str,
                          object_pairs_hook=_object_from_pairs)
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
    except _RepeatedMember as error:
        raise DictionaryParseError(
            f"The data dictionary at {path} carries the member "
            f"{error.name!r} twice inside one object.\n"
            "A JSON reader resolves a repeated member by keeping the last "
            "occurrence and discarding the first without complaint, which is "
            "how an edit to this document could redefine a field's picture, "
            "scale, signedness or storage class while leaving a file that "
            "still parses and still passes every later check. The read stops "
            "here instead.\n"
            "The generator never emits a repeated member: regenerate the "
            "artifact with "
            "python -m acas_posting.dictionary.generate."
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
    try:
        return from_json_obj(document)
    except DictionaryIntegrityError as error:
        raise DictionaryUntrustedError(
            f"The data dictionary at {path} parsed, but it is not the "
            f"document it claims to be.\n{error}\n"
            "Every record module cites this document for the picture, scale, "
            "signedness and storage class of its fields (rule R-5), so a "
            "document that is not the one the generator produced would "
            "silently redefine several hundred fields. Regenerate it from "
            "the frozen sources with "
            "python -m acas_posting.dictionary.generate, and use "
            "--check to see exactly how the file on disk differs from a "
            "fresh parse."
        ) from error


def _absence_message(path: Path) -> str:
    """Return the failure text for an artifact that is not there.

    Args:
        path: The absolute path that was looked at.

    Returns:
        A message naming that path and every other candidate the default
        lookup considered, explaining why each can legitimately be missing,
        and giving the remedies - and no more, since this module neither
        empties nor regenerates.
    """
    candidates = _default_document_candidates()
    if path in candidates:
        # The default was used, so every legitimate location was tried and the
        # message can say so and name them.
        looked_in = "\n".join(f"    {candidate}" for candidate in candidates)
        preamble = (
            "Two locations are legitimate and both were looked at, in this "
            "order:\n"
            f"{looked_in}\n"
            "\n"
            "The first is the copy carried inside an installed distribution, "
            "put there by the package-dir mapping in pyproject.toml that "
            "makes the repository's data_dictionary/ tree the acas_posting "
            "package's data directory. The second is the repository artifact "
            "itself, where Agent Action Plan sections 0.3.1 and 0.4.1.6 place "
            "it. A source checkout normally has only the second, an installed "
            "wheel only the first, so one of them being absent is ordinary; "
            "BOTH being absent is what produced this error.\n"
        )
    else:
        # An explicit path= was given. It is honoured exactly as passed and no
        # search happened, so claiming otherwise would misdirect the reader.
        preamble = (
            "That path was given explicitly, through the path= argument, so "
            "it was used exactly as passed and no default location was "
            "consulted. Omitting path= searches the two locations this "
            "distribution considers legitimate: the copy inside an installed "
            "distribution first, then the repository's own "
            "data_dictionary/acas_posting_dictionary.json.\n"
        )
    return (
        f"The ACAS posting data dictionary was not found at {path}\n"
        "\n"
        f"{preamble}"
        "\n"
        "The artifact is not optional: rule R-5 binds every field of every "
        "record module to a dictionary entry, and those modules read it while "
        "they are being imported. So this is a damaged installation, a "
        "checkout the generator has never been run in, or a path= override "
        "naming somewhere wrong.\n"
        "\n"
        "Four remedies, and no fifth:\n"
        "  1. run from a source checkout of the repository, where "
        "data_dictionary/acas_posting_dictionary.json sits beside the "
        "acas_posting package; or\n"
        "  2. regenerate the artifact - python -m "
        "acas_posting.dictionary.generate - which rebuilds it from the frozen "
        "bridge, the copybooks and the schema, and writes the repository "
        "location; or\n"
        "  3. reinstall a distribution built from that checkout, so the "
        "packaged copy is carried into acas_posting/data_dictionary/; or\n"
        "  4. pass an explicit path - load_dictionary(Path(...)), or the "
        "path= keyword of any accessor in this module - naming an intact "
        "copy of the artifact.\n"
        "\n"
        "This module does not fall back to an empty dictionary, because a "
        "record module would then bind field metadata that no frozen source "
        "supports. Nor does it regenerate the artifact itself: that is the "
        "job of the generator beside this module, whose COBOL and schema "
        "parsers must never reach the import path of the record layer (Agent "
        "Action Plan section 0.4.3), which is why remedy 2 is a command to "
        "run and not something attempted from here."
    )


class _DocumentIndex:
    """Lookup tables over one document, built once and never mutated after.

    Private on purpose: what this module publishes is accessors, not indexes,
    so that no caller can hold a mapping and mutate it. Every collection
    below preserves the order the document records - the artifact's own
    `meta.determinism.array_order` is the contract, and re-ordering it here
    would discard exactly the guarantee rule R-6 rests on.

    The mapping from key to entry takes the document as it stands, and it can
    afford to: by the time a document reaches this class, `check_integrity` has
    already refused any document that repeats an entry key, a table name, a
    manifest path or a binding-rule identifier. Uniqueness is therefore an
    established fact here rather than an assumption, which is exactly what a
    key-to-entry mapping needs - a repeated key would otherwise shadow one
    field's metadata with another's, silently and with no error anywhere.
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


#  THE MEMO
#  A plain mapping from absolute path to the document read from it, and a
#  second from the same path to that document's index. Both are private, both
#  are keyed by a path made absolute first, and neither is touched at import
#  time - importing this module reads nothing.
#  This is a cache and not a lock: execution is strictly sequential, matching
#  the single-threaded COBOL, so there is no synchronisation primitive here
#  and none is needed (rule R-3). Two reads of one path in one process would
#  be harmless anyway - the document is immutable - but twenty-seven record
#  modules importing at start-up should cost one read between them, not
#  twenty-seven.

_DOCUMENTS: dict[Path, DataDictionary] = {}
_INDEXES: dict[Path, _DocumentIndex] = {}


def load_dictionary(path: Path | None = None) -> DataDictionary:
    """Return the whole data dictionary, reading it at most once per path.

    Args:
        path: An explicit artifact path, or None for the location
            `acas_posting/__init__.py` resolved - the installed package data
            at `acas_posting/data_dictionary/`, or the repository sibling
            `data_dictionary/` when this is an uninstalled checkout. The
            override is the sanctioned escape hatch for a test, or for a
            deployment that keeps the artifact somewhere else.

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


#  FAILURE MESSAGES THAT TEACH  (rule R-5)
#  A record module reaches this module because rule R-5 requires every field
#  to cite a dictionary entry. When a key does not match, the wrong outcome is
#  for its author to give up and hand-write the metadata instead - that is the
#  transcription error the data-dictionary-first directive exists to prevent.
#  So a miss states the convention, shows the nearest keys the document really
#  carries, and says outright not to hand-code the field.


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


#  THE DOCUMENT'S OWN THREE HEADERS


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


#  ENTRIES


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


#  THE THREE VIEWS, HANDED OVER SEPARATELY  (rule R-4)
#  Three accessors, one per layer, and no fourth that merges them. Each may
#  answer None, and None is a RECORDED FACT rather than a failure: a
#  copybook-only working-storage field has no host variable and no column, and
#  the three date components the bridge derives at
#  [common/irspostingMT.cbl:L982-L987] have no copybook at all. A caller must
#  say which layer it means, because the layers disagree and the disagreement
#  is behaviour that has to be reproduced.


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


#  THE ENTITY - HANDLER - BRIDGE - TABLE SPINE
#  What the data-access layer resolves a call through. The correspondence is
#  not one-to-one in either direction: seventeen handlers reach twenty-two
#  tables through twenty bridges, `acas000` dispatches to four tables by
#  file-key number, and `acas016` and `acas026` each own a header table and a
#  lines table - so the spine is looked up, never inferred from a name.


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


#  CITATION  (rule R-5 made usable)


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

        A work-file field - one of the records a General Ledger program
        declares inline in its own FILE SECTION - has no copybook view by
        nature, so its first segment is spelt `program=` and names the
        program's own declaration line. The two never coexist, so the segment
        count does not change:

            sort-trans-record.sort-amount  program=general/gl071.cbl:L143
            bridge=absent  column=absent

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
    # The copybook and program-source views never coexist: a record is declared
    # by a copybook or inline by a program, never both. So the first segment
    # names whichever declares this field, and `copybook=absent` is reserved
    # for a field no COBOL declaration carries at all - a bridge-derived
    # column.
    declaring = (
        f"program={_view_locator(entry.program_source)}"
        if entry.program_source is not None
        else f"copybook={_view_locator(entry.copybook)}"
    )
    return "  ".join(
        (
            entry.key,
            declaring,
            f"bridge={_view_locator(entry.bridge_host_variable)}",
            f"column={_view_locator(entry.column)}",
        )
    )


#  PUBLIC SURFACE
#  The failures first, then the accessors, each group in alphabetical order. A
#  tuple rather than a list, so the surface cannot be reordered, extended or
#  mutated in place at run time, and alphabetical so the order is a mechanical
#  consequence of the names instead of an editorial choice - both small
#  determinism guarantees in the spirit of rule R-6.
#  Everything else here is private: the index, the memo, the parse boundary
#  and the message builders. A caller gets accessors, never a mapping it
#  could mutate.

__all__: Final[tuple[str, ...]] = (
    # The re-exported object model. Agent Action Plan section 0.4.3 grants
    # `cobol/*.py` and `records/*.py` this module and not `dictionary.model`,
    # and every value an accessor below returns is an instance of one of these,
    # so they are published here. Bindings to the one definition, never copies
    # (rule R-5); `RE_EXPORTED_MODEL_NAMES` lists the same set as data.
    "ENTRY_KEY_PATTERN",
    "REPO_PATH_PATTERN",
    "SOURCE_LOCATOR_PATTERN",
    "BridgeHostVariable",
    "CobolPythonStorage",
    "ConditionName",
    "CopybookField",
    "Coverage",
    "DataDictionary",
    "Derivation",
    "DictionaryEntry",
    "Drift",
    "Meta",
    "MysqlColumn",
    "RE_EXPORTED_MODEL_NAMES",
    "SignPosition",
    "Sources",
    "TableRecord",
    "Usage",
    "UsageDeclaredAt",
    # The failures.
    "DictionaryError",
    "DictionaryKeyError",
    "DictionaryLookupError",
    "DictionaryNotFoundError",
    "DictionaryNumericPolicyError",
    "DictionaryParseError",
    "DictionaryUntrustedError",
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
