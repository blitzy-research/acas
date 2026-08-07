"""Runtime lookup into the generated ACAS posting data dictionary.

Reads the committed artifact and serves it to the layers that need field
metadata: the record modules build every `FieldDescriptor` from it, and the
handler modules take their column lists and their conversions from it. Nothing
here parses COBOL, opens a bridge or schema source, launches a process or reaches
the comparison oracle - it reads one JSON file, so it imports cleanly on a host
with no COBOL toolchain and no database. The COBOL locators throughout the module
are citations for a reader, as rule R-5 asks; nothing here opens one.

The accessors

    load_dictionary, clear_cache      the document, memoised per path
    meta, sources, coverage          the document's three headers
    entries, entry_keys              every entry, in document order
    get_entry, find_entry            one entry by key: raising, non-raising
    entries_for_table                one table's entries, in column order
    entries_for_copybook_record, entries_for_copybook_file
    copybook_field_for, host_variable_for, column_for
                                     the three views; None is a recorded fact
    drift_for, derivation_for        the cross-view facts, never merged
    tables, table_names, table_for, find_table, tables_for_handler
                                     the entity/handler/bridge/table spine
    bridge_for                       one bridge pair with its key metadata
    cite                             a one-line provenance citation (R-5)
    RecordLayout, FieldTrace, trace_record, field_keys_for, entry_for_field,
    cite_field                       per-record-field tracing, so a record
                                     module can cite each field's entry

A lookup that cannot be satisfied raises rather than returning a plausible
default: a descriptor silently built from the wrong entry would produce a record
that still looked right.
"""

# Every fact this module serves is derived from the maintainer's own one-way COBOL-to-
# MySQL bridge (common/*MT.scb and common/*MT.cbl), the record copybooks under
# copybooks/, and the frozen schema mysql/ACASDB.sql.

import dataclasses
import difflib
import json
import os
import stat
import sys
from collections.abc import Mapping
from importlib import resources
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar, Final, Protocol

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

# RE-EXPORTED OBJECT MODEL (Agent Action Plan section 0.4.3, rule R-5) Agent Action Plan
# section 0.4.3 grants `cobol/*.py` this module and nothing else from the package, and
# `records/*.py` this module plus `cobol.field`.

RE_EXPORTED_MODEL_NAMES: Final[tuple[str, ...]] = (
    "ENTRY_KEY_PATTERN",
    "REPO_PATH_PATTERN",
    "SOURCE_LOCATOR_PATTERN",
    "CobolPythonStorage",
    "SignPosition",
    "Usage",
    "UsageDeclaredAt",
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

# Six classes, each with one job, and each one a subclass of a built-in the caller would
# already be catching.


class DictionaryError(Exception):
    """Base for every failure this module raises.

    Attributes:
        message: The failure, in full, as `str()` also returns it.
    """

    def __init__(self, message: str) -> None:
        """Record the message on the exception and on `args`.

        Args:
            message: The complete failure text, ready to be read as it stands. It is
                never assembled from the environment.
        """
        super().__init__(message)
        self.message: str = message

    def __str__(self) -> str:
        """Return the message unaltered, without repr quoting."""
        return self.message


class DictionaryNotFoundError(DictionaryError, FileNotFoundError):
    """The dictionary artifact is not present at the path asked for.

    The artifact is committed as a repository sibling of the package AND installed as
    package data, so this means one of three things.
    """


class DictionaryParseError(DictionaryError, ValueError):
    """The bytes at the path are not a readable dictionary document.

    Raised for text the JSON reader cannot parse, and for a document whose top level is
    not an object. The original failure is chained, so the line and column the reader
    reported survive.
    """


class DictionaryNumericPolicyError(DictionaryParseError):
    """A parsed value falls outside the scalar shapes the model admits.

    Rule R-2 keeps binary floating point out of this migration entirely, and
    `model.JsonValue` admits text, a dimensionless whole number, a flag, absence, arrays
    and objects - and nothing else.
    """


class DictionaryUntrustedError(DictionaryParseError):
    """The document parsed, but it is not the dictionary it claims to be.

    This is a distinct failure from `DictionaryParseError` because the two ask a caller
    to do different things. Unparseable bytes are a damaged file.
    """


class DictionaryKeyError(DictionaryError, KeyError):
    """No entry in the dictionary carries the key asked for.

    The message quotes the key, states both key forms, warns against keying by field
    name alone, and offers the nearest keys the document does carry - because the fix is
    to correct the key, never to hand-write the field's metadata.
    """


class DictionaryLookupError(DictionaryError, KeyError):
    """Nothing matches a name that is not an entry key.

    Distinct from `DictionaryKeyError` so that a caller resolving the entity-to-table
    spine can tell a misspelt table name from a misspelt entry key. Both are `KeyError`
    subclasses, so a caller that does not care can catch just `KeyError`.
    """


#  THE PARSE BOUNDARY  (rules R-2 and R-3)

#: The scalar shapes `model.JsonValue` admits, as an ALLOW-LIST. Stated this way round
#: on purpose.
_ADMITTED_SCALARS: Final[tuple[type, ...]] = (str, int, bool, type(None))

#: How many near-miss suggestions a failure message offers. Small on purpose: a message
#: that lists fifty candidates teaches nothing.
_SUGGESTION_LIMIT: Final[int] = 5

#: What a citation prints where one of the three views is absent.
_ABSENT_VIEW: Final[str] = "absent"


# --------------------------------------------------------------------------------------
#  READ BUDGETS (finding SEC-07)
#
#  The read below is otherwise unbounded in two ways: it loops until the file ends, and
#  `json.loads` recurses once per level of nesting. Neither is a code-execution risk -
#  the reader constructs no objects of its own and admits only four scalar shapes - but
#  both are unbounded cost driven by the file's contents, and the path this reads is not
#  always the committed artifact: `load` accepts a caller-supplied path.
#
#  BOTH LIMITS ARE DERIVED FROM THE COMMITTED ARTIFACTS WITH WIDE HEADROOM, so neither
#  changes how the real dictionary reads. Measured: `acas_posting_dictionary.json` is
#  2,558,638 bytes at depth 7 with 144,414 nodes, and the schema beside it is 97,129
#  bytes at depth 8.
#
#  No node budget is stated because JSON has no aliases and therefore no multiplicative
#  expansion: every node costs at least one byte of source, so the byte budget already
#  bounds the node count. There is nothing here to validate a dictionary's CONTENTS with
#  - these are bounds on the document as a document, the same footing as the existing
#  refusal of a repeated member or a non-object root, and not the content validation
#  rule R-3 forbids.
# --------------------------------------------------------------------------------------

#: Largest artifact read, in bytes. Measured 2,558,638 (~2.44 MiB); this is ~13x that.
_MAX_DOCUMENT_BYTES: Final[int] = 32 * 1024 * 1024

#: Deepest nesting accepted. Measured 7 for the dictionary, 8 for its schema.
_MAX_DOCUMENT_DEPTH: Final[int] = 64


#: The artifact's file name, taken from the repository constant so that the packaged
#: candidate and the repository candidate can never name different files.
_DOCUMENT_NAME: Final[str] = DATA_DICTIONARY_PATH.name


def _packaged_document_dir() -> Path | None:
    """This distribution's own copy of the dictionary directory, or None.

    Asked of `importlib.resources` rather than assembled from `__file__`, because the
    packaged copy's location is a property of how the distribution was installed and
    `importlib.resources` is the interface that knows it. `resources.files()` returns a
    Traversable rooted at the package.

    Returns:
        The absolute directory holding the PACKAGED copy of the artifact, or None when
            this distribution is not one that keeps its data on a real filesystem.
    """
    try:
        root = resources.files("acas_posting")
    # Exotic import machinery only - excluded from coverage because no ordinary
    # installation reaches it.
    except (ImportError, TypeError):  # pragma: no cover
        return PACKAGE_DATA_DICTIONARY_DIR
    if isinstance(root, Path):
        return root / PACKAGE_DATA_DICTIONARY_DIR.name
    return None


def _default_document_candidates() -> tuple[Path, ...]:
    """The absolute paths the DEFAULT document may occupy, in the order to try.

    The order comes from `acas_posting.DATA_DICTIONARY_SEARCH_PATH` and is not re-
    decided here.

    Returns:
        One entry per legitimate location, packaged copy first and repository sibling
            second, each absolute and symlink-free. Never empty.
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

    order: the packaged copy, which is the only one an installed distribution carries,
    then the repository copy, which is the only one a source checkout carries.

    Args:
        path: An explicit artifact path, or None for this distribution's own default.

    Returns:
        The location to read, expressed absolutely, so that two spellings of one file -
            a relative path, a path through a symbolic link - share a single memo entry
            and therefore a single read.
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

    This walks types, never values: it does not test a count against a range, a string
    against a pattern or a member against the schema, so it adds no validation of what
    the document says (rule R-3).

    Args:
        value: One node of the freshly parsed tree.
        trail: Where the node sits, as `.member` and `[index]` steps from the document
            root, so a failure names the offending member rather than only its type.
        path: The document being read, named in the failure.

    Raises:
        DictionaryNumericPolicyError: The node is outside the four scalar shapes
            `model.JsonValue` admits and is not an array or an object.
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

    Private and deliberately narrow: it exists only to carry the offending name out of
    the object hook and into `_read_document`, which is the only place that knows which
    file is being read and can therefore say so.
    """

    def __init__(self, name: str) -> None:
        """Record the repeated member name."""
        super().__init__(name)
        self.name: str = name


def _object_from_pairs(
    pairs: list[tuple[str, object]],
) -> dict[str, object]:
    """Build one JSON object from its member pairs, refusing any repeated name.

    WHY THIS HOOK EXISTS. JSON permits a repeated member name and the standard reader
    resolves it by keeping the LAST occurrence silently. That makes a forged document
    trivial to hide inside a real one.

    Args:
        pairs: The members of one object, in the order the document wrote them, as the
            JSON reader hands them over.

    Returns:
        The object as a mapping, identical to what the reader would have built on its
            own for a document with no repeated member.

    Raises:
        _RepeatedMember: A member name occurs more than once.
    """
    obj: dict[str, object] = {}
    for name, value in pairs:
        if name in obj:
            raise _RepeatedMember(name)
        obj[name] = value
    return obj


def _document_depth_exceeds(tree: object, limit: int) -> bool:
    """Report whether `tree` nests deeper than `limit`, without recursing to find out.

    Walked with an explicit stack rather than recursively: a depth guard that recursed
    once per level would be liable to the very exhaustion it exists to prevent. Returns
    as soon as the limit is passed, so an over-budget document is not walked in full.

    Args:
        tree: The parsed document, or any part of one.
        limit: The deepest nesting accepted.

    Returns:
        True if any path through `tree` is deeper than `limit`.
    """
    stack: list[tuple[object, int]] = [(tree, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > limit:
            return True
        if isinstance(node, dict):
            stack.extend((value, depth + 1) for value in node.values())
        elif isinstance(node, list):
            stack.extend((value, depth + 1) for value in node)
    return False


def _read_text_without_following_links(path: Path) -> str:
    """Read one file's text, refusing a symbolic link or anything but a plain file.

    `Path.resolve()` has already followed every symbolic link in the path, so what
    remains is the window between that resolution and the open.

    Args:
        path: The absolute path of the artifact to read.

    Returns:
        The file's contents decoded as UTF-8.

    Raises:
        DictionaryNotFoundError: Nothing is at `path`, or what is there is not a plain
            file.
        DictionaryParseError: The file is larger than `_MAX_DOCUMENT_BYTES`. Raised
            while reading rather than afterwards, so an oversized file is never held in
            memory whole just to be rejected.
        OSError: The file exists and is plain but cannot be read.
    """
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except FileNotFoundError:
        raise DictionaryNotFoundError(_absence_message(path)) from None
    except OSError as error:
        # ELOOP from O_NOFOLLOW, ENOTDIR from a path component that is not a directory,
        # EACCES from an unreadable file.
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
        read_so_far = 0
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            read_so_far += len(chunk)
            if read_so_far > _MAX_DOCUMENT_BYTES:
                raise DictionaryParseError(
                    f"The file at {path} is larger than the "
                    f"{_MAX_DOCUMENT_BYTES}-byte read budget, so it was not read to "
                    f"the end.\n"
                    "The committed artifact is about 2.44 MiB, so nothing legitimate "
                    "is near this limit. Either the path names something other than a "
                    "data dictionary, or the artifact is not the one this project "
                    "generates -- regenerate it with "
                    "python -m acas_posting.dictionary.generate."
                )
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    return b"".join(chunks).decode("utf-8")


def _read_document(path: Path) -> DataDictionary:
    """Read, parse, check and map one dictionary document. No memo, no fallback.

    `parse_float=str` is the numeric guard's first half: a real-number literal comes
    back as its own text rather than as a binary approximation of it, so no such value
    can be constructed even while the document is being read.

    Args:
        path: The absolute path of the artifact to read.

    Returns:
        The document as the immutable record tree `model` defines.

    Raises:
        DictionaryNotFoundError: Nothing readable is at `path`, or what is there is not
            a plain file.
        DictionaryParseError: The text is not parseable JSON, an object carries the same
            member name twice, or the top level is not an object.
        DictionaryNumericPolicyError: A parsed value is outside the shapes the model
            admits (rule R-2).
        DictionaryUntrustedError: The document parses but does not hold up as the
            dictionary it claims to be.
    """
    if not path.is_file():
        raise DictionaryNotFoundError(_absence_message(path))
    text = _read_text_without_following_links(path)
    try:
        tree = json.loads(text, parse_float=str,
                          object_pairs_hook=_object_from_pairs)
    except RecursionError as error:
        # Nesting deeper than the interpreter's recursion limit. Caught so the read
        # fails as a refusal naming the cause, rather than as a bare RecursionError
        # from inside the JSON scanner (finding SEC-07).
        raise DictionaryParseError(
            f"The data dictionary at {path} nests too deeply to parse: the JSON "
            f"reader exhausted the interpreter's recursion limit.\n"
            f"The committed artifact nests 7 levels, and this reader accepts up to "
            f"{_MAX_DOCUMENT_DEPTH}. Deep nesting is how a small file forces unbounded "
            "recursion, so nothing is retried at a raised limit: correct the file, or "
            "pass the path of an intact copy."
        ) from error
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
    if _document_depth_exceeds(tree, _MAX_DOCUMENT_DEPTH):
        raise DictionaryParseError(
            f"The data dictionary at {path} nests deeper than "
            f"{_MAX_DOCUMENT_DEPTH} levels, which is the read budget.\n"
            "The committed artifact nests 7 levels and its schema nests 8, so nothing "
            "legitimate is near this limit. Either the path names something other than "
            "a data dictionary, or the artifact is not the one this project generates "
            "-- regenerate it with python -m acas_posting.dictionary.generate."
        )
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
        A message naming that path and every other candidate the default lookup
            considered, explaining why each can legitimately be missing, and giving the
            remedies - and no more, since this module neither empties nor regenerates.
    """
    candidates = _default_document_candidates()
    if path in candidates:
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
        # An explicit path= was given. It is honoured exactly as passed and no search
        # happened, so claiming otherwise would misdirect the reader.
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

    Private on purpose: what this module publishes is accessors, not indexes, so that no
    caller can hold a mapping and mutate it.
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
            document: The mapped document to index. Held as it stands; it is immutable,
                so the index cannot drift from it.
        """
        entries_by_key: dict[EntryKey, DictionaryEntry] = {}
        entries_by_table: dict[TableName, list[DictionaryEntry]] = {}
        entries_by_copybook_file: dict[RepoPath, list[DictionaryEntry]] = {}
        for entry in document.entries:
            entries_by_key[entry.key] = entry
            # A null table is the ordinary case for a copybook-only field - 502 of the
            # 1015 entries - and never an error.
            if entry.table is not None:
                entries_by_table.setdefault(entry.table, []).append(entry)
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
        # A bridge is indexed under the name `TableRecord.bridge` gives it, reached by
        # joining through the tables the bridge itself declares.
        bridges_by_name: dict[BridgeName, BridgeSource] = {}
        for bridge in document.sources.bridges:
            for bridge_table in bridge.tables:
                named_by = tables_by_name.get(bridge_table.name)
                if named_by is not None:
                    bridges_by_name.setdefault(named_by.bridge, bridge)
        self.bridges_by_name: dict[BridgeName, BridgeSource] = bridges_by_name


# A plain mapping from absolute path to the document read from it, and a second from the
# same path to that document's index.

_DOCUMENTS: dict[Path, DataDictionary] = {}
_INDEXES: dict[Path, _DocumentIndex] = {}


def load_dictionary(path: Path | None = None) -> DataDictionary:
    """Return the whole data dictionary, reading it at most once per path.

    Two spellings of one file share one entry, because the path is made absolute before
    it is used as the memo key. Nothing is read at import time.

    Args:
        path: An explicit artifact path, or None for the location
            `acas_posting/__init__.py` resolved - the installed package data at
            `acas_posting/data_dictionary/`, or the repository sibling
            `data_dictionary/` when this is an uninstalled checkout.

    Returns:
        The document as an immutable tree of `model` records: `meta`, `sources`,
            `tables`, `entries` and `coverage`.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
        DictionaryNumericPolicyError: A parsed value is outside the shapes the model
            admits (rule R-2).
    """
    absolute_path = _absolute_document_path(path)
    document = _DOCUMENTS.get(absolute_path)
    if document is None:
        document = _read_document(absolute_path)
        _DOCUMENTS[absolute_path] = document
    return document


def clear_cache() -> None:
    """Discard every memoised document and index."""
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
        DictionaryNumericPolicyError: A parsed value is outside the shapes the model
            admits (rule R-2).
    """
    absolute_path = _absolute_document_path(path)
    index = _INDEXES.get(absolute_path)
    if index is None:
        index = _DocumentIndex(load_dictionary(absolute_path))
        _INDEXES[absolute_path] = index
    return index


# A record module reaches this module because rule R-5 requires every field to cite a
# dictionary entry.


def _nearest(name: str, candidates: tuple[str, ...]) -> tuple[str, ...]:
    """Return the candidates closest to `name`, best first, at most five.

    This is the ONE place in this module where an order other than document order is
    produced, and it is deterministic.

    Args:
        name: The name that matched nothing.
        candidates: Every name the document does carry, in document order.

    Returns:
        Up to `_SUGGESTION_LIMIT` near misses, or the members of the same qualified
            group when nothing is close enough - a wrong column name under a right table
            name is the common slip, and listing that table's real columns answers it
            directly.
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
        A single line, always ending in a newline, so a caller can concatenate it into a
            longer message without deciding spacing.
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
        path: The document that was read, so the reader knows which file was searched
            when an override path is in play.

    Returns:
        The complete message.
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
        The complete message: the name, the suggestions, the source of the document and
            the guidance.
    """
    return (
        f"The ACAS posting data dictionary carries no entry for {noun[:-1]} "
        f"{name!r}.\n"
        f"{_nearest_sentence(name, candidates, noun)}"
        f"{guidance}\n"
        f"Read from: {path}"
    )


def meta(*, path: Path | None = None) -> Meta:
    """Return the document's identity block.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Meta` - the dictionary's name and version, the reference to its JSON Schema,
            what generated it, the statement of whose authority it carries, the
            determinism contract it was written under, the derivation rules it followed,
            and the binding rules it was built to satisfy.

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
        `Sources` - the frozen schema dump, the twenty in-scope bridge pairs and the in-
            scope copybooks.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return load_dictionary(path).sources


def coverage(*, path: Path | None = None) -> Coverage:
    """Return the tallies that make the document's completeness checkable.

    A one-sided entry is a finding, not a fault: a copybook-only working storage field
    and a bridge-derived column with no copybook counterpart are both legitimate, and
    both are recorded rather than dropped.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Coverage` - how many tables the frozen schema declares and how many are in
            scope, how many bridges each way, how many in-scope columns there are and
            how many the document covers, how many host variables and copybook fields it
            covers, and the keys of every one-sided entry.

    Raises:
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return load_dictionary(path).coverage


def entries(*, path: Path | None = None) -> tuple[DictionaryEntry, ...]:
    """Return every entry, in document order.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        All entries as the document records them - tables by name ascending, within a
            table by column ordinal, then that table's copybook-only fields, then the
            copybook-only fields belonging to no table.

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

    What comes back is reported, never adjudicated. Where the three views disagree the
    entry carries all three and flags the disagreement in `drift`; this module names no
    winner (rule R-4).

    Args:
        key: `<TABLE-NAME>.<COLUMN-NAME>` where a column backs the field, or `<COPYBOOK-
            RECORD>.<FIELD-NAME>` where it is copybook-only.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The entry: the three views, the drift between them, any derivation, the storage
            class this migration gives it, and its notes, anomaly references and
            ambiguity references.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
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
        The entry, or None.

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
        table: A table name as the frozen schema dump declares it, upper case with
            hyphens - for example `SALEDGER-REC`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Every entry the document maps to that table, in document order, which for a
            table is the column ordinal the frozen dump fixes.

    Raises:
        DictionaryLookupError: The document knows no such table. The message offers the
            nearest table names.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
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

    One-sided entries are included, and that is the point of this accessor for the
    record layer.

    Args:
        record: A record name exactly as its copybook declares it - for example `WS-
            Batch-Record`, `File-Access` or the lower-case `maps03-ws`. Case-sensitive,
            like every other name here.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Every entry whose copybook view belongs to a copybook whose record is that one,
            in document order.

    Raises:
        DictionaryLookupError: No catalogued copybook declares that record.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
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
        file: The copybook's repository-relative path, exactly as the document records
            it - for example `copybooks/wssl.cob`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Every entry whose copybook view comes from that file, in document order.

    Raises:
        DictionaryLookupError: The document catalogues no such copybook, or catalogues
            it with no field of its own.
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


# Three accessors, one per layer, and no fourth that merges them. Each may answer None,
# and None is a RECORDED FACT rather than a failure.


def copybook_field_for(
    key: str, *, path: Path | None = None
) -> CopybookField | None:
    """Return the copybook view of one field, or None where it has none.

    This is the view `acas_posting/cobol/field.py` builds a descriptor from, and reading
    `usage` from here rather than from the picture line is not a nicety.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `CopybookField` - the declaring file and line, the level, the picture text, the
            usage with where that usage was declared and which group it was inherited
            from, signedness with the sign position and the sign clause text verbatim,
            the digit counts and scale, the character length, any REDEFINES or OCCURS,
            and the 88-level condition names.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return get_entry(key, path=path).copybook


def host_variable_for(
    key: str, *, path: Path | None = None
) -> BridgeHostVariable | None:
    """Return the bridge host-variable view of one field, or None.

    `loaded_from_record` and `unloaded_to_record` are the two members a naive reading
    would assume rather than check.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `BridgeHostVariable` - the declaring bridge file and line, the host-variable
            group and its suffix, the name, the picture text, the usage, signedness,
            digit counts, scale and character length, whether the bridge's load
            paragraph actually moves the record's field into it and where, whether the
            unload paragraph moves it back and where, and whether the group is
            INITIALIZEd before the load.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return get_entry(key, path=path).bridge_host_variable


def column_for(key: str, *, path: Path | None = None) -> MysqlColumn | None:
    """Return the column view of one field, or None where it has none.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `MysqlColumn` - the schema file and line, the column name, the SQL type as
            written with its base type, the display width and scale, whether it is
            unsigned, whether it is nullable, its default, whether it is the primary
            key, its ordinal within the table, and any comment.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return get_entry(key, path=path).column


def drift_for(key: str, *, path: Path | None = None) -> Drift:
    """Return what disagrees between the three views of one field.

    THIS REPORTS THE DISAGREEMENT AND SETTLES NOTHING. Agent Action Plan section 0.6.2
    is explicit about why the data-access layer needs it.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Drift` - a flag per axis (signedness, usage, digits, scale, character length,
            name) and a line of detail per disagreement. Never None.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return get_entry(key, path=path).drift


def derivation_for(
    key: str, *, path: Path | None = None
) -> Derivation | None:
    """Return how the bridge derives a column that no record supplies.

    The case this exists for is IRSPOSTING-REC.POST4-DAY, POST4-MONTH and POST4-YEAR,
    whose guarded moves are at [common/irspostingMT.cbl:L982-L987].

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `Derivation` - the kind of derivation, the expression as the bridge writes it,
            the guard that expression sits under, what happens when that guard does not
            hold, and the locator of both.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return get_entry(key, path=path).derivation


# What the data-access layer resolves a call through. The correspondence is not one-to-
# one in either direction.


def tables(*, path: Path | None = None) -> tuple[TableRecord, ...]:
    """Return every in-scope table with its place in the spine.

    Args:
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        A `TableRecord` per in-scope table, in document order.

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
        That table's `TableRecord`, or None - which for one of the eleven out-of-scope
            tables of the frozen schema is the right answer rather than a failure, since
            the posting cycle never touches them.

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
        handler: A handler program name - `acas000` through `acas029`, or `acasirsub1`
            through `acasirsub5`.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The tables that handler owns. Usually one.

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

    The key metadata is what `acas_posting/dal/cursor_state.py` emulates ISAM
    positioning from: a START followed by READ NEXT is reproduced against the key the
    bridge itself declares, not against an ordering invented in Python.

    Args:
        bridge: A bridge pair's stem, lower case and ending in `MT` - for example
            `glpostingMT`. This is the name `TableRecord.bridge` carries.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        `BridgeSource` - the pair's two paths, the database the embedded directive
            names, the locator of that directive, the tables and host-variable groups it
            declares, its keys with each one's name in the database, offset, length,
            type and locator, the names and locators of its load and unload paragraphs,
            and whether the host-variable group is INITIALIZEd before a load.

    Raises:
        DictionaryLookupError: The document catalogues no such bridge.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
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
        The view's `source` locator - a repository-relative path and a line reference -
            or `absent`, which is itself a fact worth printing.
    """
    return _ABSENT_VIEW if view is None else view.source


def cite(key: str, *, path: Path | None = None) -> str:
    """Return a one-line provenance citation for one field.

    This is rule R-5 made usable.

    Args:
        key: The entry key, exact and case-sensitive.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The key followed by the locator of each of its three views, in layer order, two
            spaces between segments and no newline - short enough for a log line, a
            comment or a docstring.

    Raises:
        DictionaryKeyError: No entry carries that key.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    entry = get_entry(key, path=path)
    # The copybook and program-source views never coexist: a record is declared by a
    # copybook or inline by a program, never both.
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


# RECORD LAYOUT TRACING (rule R-5) Section 0.4.1.6 gives this module its mandate in one
# line - "Runtime lookup so every record field cites its entry" - and it names the 27
# `acas_posting/records/*.py` modules as a caller needing "per-record enumeration of
# fields in declaration order, and the key for each".

#: Field metadata names whose value is a descriptor object - anything carrying a
#: `dictionary_key`.
_DESCRIPTOR_METADATA_KEYS: Final[tuple[str, ...]] = ("descriptor", "cobol_field")

#: Field metadata names whose value is an entry key already, in the form `get_entry`
#: takes. `twin_dictionary_key` is last.
_KEY_METADATA_KEYS: Final[tuple[str, ...]] = (
    "dictionary_key",
    "acas_posting.dictionary_key",
    "twin_dictionary_key",
)

_NAMED_FIELD_MAPS: Final[tuple[str, ...]] = (
    "DESCRIPTORS",
    "FIELD_DESCRIPTORS",
    "DICTIONARY_KEYS",
    "FIELDS",
    "ALL_FIELDS",
)

_CLASS_CONSTANT_ROUTE: Final[str] = "class constant"

#: The route a parallel `FIELDS` tuple gives, matched by position rather than by name.
_POSITIONAL_ROUTE: Final[str] = "class FIELDS by position"

_GROUP_ROUTE: Final[str] = "group item"

#: Every route a record field's key can arrive by, in the order they are tried.
RECORD_FIELD_ROUTES: Final[tuple[str, ...]] = (
    *(f"metadata[{name}]" for name in _DESCRIPTOR_METADATA_KEYS),
    *(f"metadata[{name}]" for name in _KEY_METADATA_KEYS),
    _CLASS_CONSTANT_ROUTE,
    *(f"class {name}" for name in _NAMED_FIELD_MAPS),
    *(f"module {name}" for name in _NAMED_FIELD_MAPS),
    _POSITIONAL_ROUTE,
    _GROUP_ROUTE,
)


class RecordLayout(Protocol):
    """A record dataclass, or an instance of one.

    Structural rather than nominal because it has to be: every one of the 27
    `acas_posting/records/*.py` modules imports this module, so this module cannot
    import them back (Agent Action Plan section 0.4.3).
    """

    __dataclass_fields__: ClassVar[Mapping[str, object]]


@dataclasses.dataclass(frozen=True, slots=True)
class FieldTrace:
    """One record attribute, the key it reaches, and how it reached it.

    Frozen, so a trace cannot be edited into disagreement with the record it describes,
    and comparable by value, so two traces of the same layout are equal - which is what
    lets a determinism test compare them directly.

    Attributes:
        attribute: The Python attribute name, as the record module spells it.
        dictionary_key: The entry key the attribute reaches, or None for a group item
            and for an attribute no route describes.
        route: Which member of `RECORD_FIELD_ROUTES` carried it, or None when none did.
        entry: The entry itself, when `trace_record` was asked to attach it and the
            document carries the key.
        group_type: For a group item, the record type whose own fields carry the keys.
            None for every other attribute.
    """

    attribute: str
    dictionary_key: str | None
    route: str | None
    entry: DictionaryEntry | None
    group_type: type | None

    @property
    def is_group(self) -> bool:
        """Whether this attribute is a group container rather than a field."""
        return self.group_type is not None


def _attribute_form(name: str) -> str:
    """Return the Python attribute form of a COBOL or dotted name.

    Written with string operations rather than a pattern so the transformation is
    legible at the point of use. It renames nothing in any record module - it only
    recognises a name a module already chose.

    Args:
        name: A descriptor name, a mapping key or a dotted path, optionally carrying the
            `#<line>` suffix a repeated field name takes.

    Returns:
        The name reduced to the form a record module gives the attribute.
    """
    stem = name.split("#")[0].rpartition(".")[2]
    spaced: list[str] = []
    for position, character in enumerate(stem):
        previous = stem[position - 1] if position else ""
        if character.isupper() and (previous.islower() or previous.isdigit()):
            spaced.append("_")
        spaced.append(character)
    collapsed: list[str] = []
    for character in "".join(spaced).lower():
        if character.isdigit() or "a" <= character <= "z":
            collapsed.append(character)
        elif collapsed and collapsed[-1] != "_":
            collapsed.append("_")
    return "".join(collapsed).strip("_")


def _entry_key_of(candidate: object) -> str | None:
    """Return the entry key a candidate carries, or None.

    A bare string is admitted only if `ENTRY_KEY_PATTERN` matches it in full, which is
    what keeps a field NAME from being mistaken for a key.

    Args:
        candidate: A value found on a record layout - a descriptor object, an entry key,
            or something that is neither.

    Returns:
        The key, when the candidate is a string in entry-key form or an object carrying
            a `dictionary_key` that is. None otherwise.
    """
    if isinstance(candidate, str):
        return candidate if ENTRY_KEY_PATTERN.fullmatch(candidate) else None
    carried = getattr(candidate, "dictionary_key", None)
    if isinstance(carried, str) and ENTRY_KEY_PATTERN.fullmatch(carried):
        return carried
    return None


def _named_bindings(
    owner: object, scope: str
) -> tuple[tuple[str, object], ...]:
    """Return each recognised collection bound directly on one owner.

    `vars` is deliberate for a class: it reports only the class's own attributes, so a
    collection inherited from a base is not read as though the subclass had published
    it.

    Args:
        owner: A record class or the module that defines it.
        scope: The route prefix - `class` or `module`.

    Returns:
        A `(route, value)` pair for every member of `_NAMED_FIELD_MAPS` bound on the
            owner itself, in that tuple's order.
    """
    bound = vars(owner)
    return tuple(
        (f"{scope} {name}", bound[name])
        for name in _NAMED_FIELD_MAPS
        if name in bound
    )


def _from_named_bindings(
    owner: object, scope: str, attribute: str
) -> tuple[object | None, str | None]:
    """Return the candidate one owner's collections hold for an attribute.

    A mapping is matched by its own key, verbatim first and then through
    `_attribute_form`, because one module keys by dotted path
    (`sales_address.sales_addr1`) and another by the COBOL name. A sequence is matched
    by each member's own `name`.

    Args:
        owner: A record class or the module that defines it.
        scope: The route prefix - `class` or `module`.
        attribute: The Python attribute name being traced.

    Returns:
        The candidate and the route that found it, or `(None, None)`.
    """
    for route, value in _named_bindings(owner, scope):
        if isinstance(value, Mapping):
            for name, candidate in value.items():
                text = str(name)
                if text == attribute or _attribute_form(text) == attribute:
                    return candidate, route
        elif isinstance(value, (tuple, list)):
            for candidate in value:
                carried = getattr(candidate, "name", None)
                text = carried if isinstance(carried, str) else str(candidate)
                if _attribute_form(text) == attribute:
                    return candidate, route
    return None, None


def _group_type(field: object) -> type | None:
    """Return the record type a group item contains, or None.

    A dataclass cannot carry both a default and a default factory, so the two tests
    cannot disagree.

    Args:
        field: One `dataclasses.Field` of a record layout.

    Returns:
        The nested record type, taken from the attribute's default or its default
            factory, or None when the attribute is a plain field.
    """
    default = getattr(field, "default", dataclasses.MISSING)
    if dataclasses.is_dataclass(default) and not isinstance(default, type):
        return type(default)
    factory = getattr(field, "default_factory", dataclasses.MISSING)
    if (
        factory is not dataclasses.MISSING
        and isinstance(factory, type)
        and dataclasses.is_dataclass(factory)
    ):
        return factory
    return None


def _trace_field(
    layout: type,
    module: object | None,
    layout_fields: tuple[object, ...],
    field: object,
    path: Path | None,
    attach: bool,
) -> FieldTrace:
    """Return the trace for one attribute of one record layout.

    The order of the attempts is the order of `RECORD_FIELD_ROUTES`, and it is not
    arbitrary.

    Args:
        layout: The record class.
        module: The module that defines it, or None when it is not in `sys.modules`.
        layout_fields: Every field of the layout, in declaration order.
        field: The field being traced.
        path: An explicit artifact path, or None for the repository's own.
        attach: Whether to look the entry up as well as the key.

    Returns:
        The trace, with `route` naming the first member of `RECORD_FIELD_ROUTES` that
            described the attribute.
    """
    attribute = str(getattr(field, "name", ""))
    metadata = getattr(field, "metadata", None)
    found: object | None = None
    route: str | None = None

    if isinstance(metadata, Mapping):
        for name in (*_DESCRIPTOR_METADATA_KEYS, *_KEY_METADATA_KEYS):
            if name in metadata:
                found, route = metadata[name], f"metadata[{name}]"
                break

    if found is None:
        constant = getattr(layout, attribute.upper(), None)
        if not isinstance(constant, str) and _entry_key_of(constant) is not None:
            found, route = constant, _CLASS_CONSTANT_ROUTE

    if found is None:
        found, route = _from_named_bindings(layout, "class", attribute)

    if found is None and module is not None:
        found, route = _from_named_bindings(module, "module", attribute)

    if found is None:
        parallel = vars(layout).get("FIELDS")
        if (
            isinstance(parallel, tuple)
            and len(parallel) == len(layout_fields)
            and all(_entry_key_of(member) is not None for member in parallel)
        ):
            for sibling, member in zip(layout_fields, parallel):
                if getattr(sibling, "name", None) == attribute:
                    found, route = member, _POSITIONAL_ROUTE
                    break

    if found is None:
        group = _group_type(field)
        if group is not None:
            return FieldTrace(attribute, None, _GROUP_ROUTE, None, group)
        return FieldTrace(attribute, None, None, None, None)

    key = _entry_key_of(found)
    entry = find_entry(key, path=path) if attach and key is not None else None
    return FieldTrace(attribute, key, route, entry, None)


def _traces(
    record: RecordLayout | type[RecordLayout],
    path: Path | None,
    attach: bool,
) -> tuple[FieldTrace, ...]:
    """Return a trace for every attribute of one record layout.

    Args:
        record: A record dataclass or an instance of one.
        path: An explicit artifact path, or None for the repository's own.
        attach: Whether to look each entry up as well as its key.

    Returns:
        One trace per attribute, in the layout's declaration order - which is the
            copybook's own order, so the sequence can be read beside the frozen source
            (rule R-6).

    Raises:
        DictionaryLookupError: The argument is not a record dataclass.
    """
    layout = record if isinstance(record, type) else type(record)
    if not dataclasses.is_dataclass(layout):
        raise DictionaryLookupError(
            f"{layout.__module__}.{layout.__qualname__} is not a record "
            "dataclass, so it has no fields to trace.\n"
            "Pass one of the dataclasses an acas_posting.records module "
            "declares, or an instance of one."
        )
    layout_fields = tuple(dataclasses.fields(layout))
    module = sys.modules.get(layout.__module__)
    return tuple(
        _trace_field(layout, module, layout_fields, field, path, attach)
        for field in layout_fields
    )


def trace_record(
    record: RecordLayout | type[RecordLayout], *, path: Path | None = None
) -> tuple[FieldTrace, ...]:
    """Return every attribute of a record layout with its dictionary entry.

    This is the one accessor that spans every convention the record modules use, so a
    consumer needing the key for an arbitrary attribute no longer has to know which of
    the 27 modules it is looking at.

    Args:
        record: A record dataclass, or an instance of one.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        One `FieldTrace` per attribute, in declaration order, each carrying the entry
            key, the route that found it and the entry itself.

    Raises:
        DictionaryLookupError: The argument is not a record dataclass.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return _traces(record, path, True)


def field_keys_for(
    record: RecordLayout | type[RecordLayout],
) -> Mapping[str, str | None]:
    """Return each attribute of a record layout mapped to its entry key.

    Reads no document at all, so it answers with the artifact absent - useful to a
    caller checking a record's coverage before deciding to load, and consistent with
    this module never reading a file on import.

    Args:
        record: A record dataclass, or an instance of one.

    Returns:
        A read-only mapping from attribute name to entry key, in declaration order, with
            None where an attribute is a group item or no route describes it.

    Raises:
        DictionaryLookupError: The argument is not a record dataclass.
    """
    return MappingProxyType(
        {
            trace.attribute: trace.dictionary_key
            for trace in _traces(record, None, False)
        }
    )


def entry_for_field(
    record: RecordLayout | type[RecordLayout],
    attribute: str,
    *,
    path: Path | None = None,
) -> DictionaryEntry:
    """Return the entry one attribute of a record layout cites.

    Args:
        record: A record dataclass, or an instance of one.
        attribute: The Python attribute name.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        The same entry `get_entry` returns for that attribute's key, from the same
            cached document - the identical object, not a copy.

    Raises:
        DictionaryLookupError: The layout declares no such attribute, or the attribute
            carries no key because it is a group item or because no route describes it.
        DictionaryKeyError: The attribute names a key the document does not carry.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    traces = _traces(record, None, False)
    layout = record if isinstance(record, type) else type(record)
    for trace in traces:
        if trace.attribute != attribute:
            continue
        if trace.dictionary_key is not None:
            return get_entry(trace.dictionary_key, path=path)
        raise DictionaryLookupError(
            f"{layout.__module__}.{layout.__qualname__}.{attribute} carries "
            "no dictionary key: "
            + (
                f"it is a group item holding {trace.group_type.__name__}, "
                "whose own fields carry the keys - trace that type instead."
                if trace.group_type is not None
                else "no route describes it. `RECORD_FIELD_ROUTES` lists "
                "every convention that is searched."
            )
        )
    raise _no_such_attribute(
        layout, attribute, tuple(trace.attribute for trace in traces)
    )


def _no_such_attribute(
    layout: type, attribute: str, candidates: tuple[str, ...]
) -> DictionaryLookupError:
    """Return the failure for an attribute a record layout does not declare.

    The message teaches the same lesson `DictionaryKeyError` does one layer down: the
    fix is to correct the name, never to hand-write the field's metadata (rule R-5).

    Args:
        layout: The record class.
        attribute: The name that matched nothing, quoted back verbatim.
        candidates: Every attribute the layout does declare, in declaration order.

    Returns:
        The exception, for the caller to raise. Built here rather than raised here so
            the caller's control flow stays visible at the call site.
    """
    suggestions = _nearest(attribute, candidates)
    nearest = (
        f"Nearest attributes: {', '.join(suggestions)}\n"
        if suggestions
        else f"This layout declares {len(candidates)} attributes, none of "
        "them close.\n"
    )
    return DictionaryLookupError(
        f"{layout.__module__}.{layout.__qualname__} declares no attribute "
        f"{attribute!r}.\n"
        f"{nearest}"
        "Attribute names are the record module's own, in the copybook's "
        "declaration order; `trace_record` lists every one of them with the "
        "route that carries its key."
    )


def cite_field(
    record: RecordLayout | type[RecordLayout],
    attribute: str,
    *,
    path: Path | None = None,
) -> str:
    """Return the one-line provenance citation for one record attribute.

    `cite` is rule R-5 made usable from a key; this is the same thing made usable from a
    Python attribute, which is where a reader actually starts.

    Args:
        record: A record dataclass, or an instance of one.
        attribute: The Python attribute name.
        path: An explicit artifact path, or None for the repository's own.

    Returns:
        Exactly what `cite` returns for that attribute's key.

    Raises:
        DictionaryLookupError: The layout declares no such attribute, or it carries no
            key.
        DictionaryKeyError: The attribute names a key the document does not carry.
        DictionaryNotFoundError: Nothing readable is at that path.
        DictionaryParseError: The bytes there are not a readable document.
    """
    return cite(entry_for_field(record, attribute, path=path).key, path=path)


# The failures first, then the accessors, each group in alphabetical order.

__all__: Final[tuple[str, ...]] = (
    # The re-exported object model.
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
    "FieldTrace",
    "RECORD_FIELD_ROUTES",
    "RecordLayout",
    "DictionaryError",
    "DictionaryKeyError",
    "DictionaryLookupError",
    "DictionaryNotFoundError",
    "DictionaryNumericPolicyError",
    "DictionaryParseError",
    "DictionaryUntrustedError",
    "bridge_for",
    "cite",
    "cite_field",
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
    "entry_for_field",
    "entry_keys",
    "field_keys_for",
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
    "trace_record",
)
