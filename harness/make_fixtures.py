#!/usr/bin/env python3
# The shebang is load-bearing: harness/build_fixtures.sh and the canonical recipe in
# harness/docker-compose.yml name this file by path, and a file whose first line is a
# docstring is refused by the kernel with "exec format error" and then interpreted by
# the shell, which executes the docstring line by line.
"""Materialise a scenario's declared flat seed files, non-interactively.

WHY THIS EXISTS
The nine scenario definitions under [harness/scenarios] each declare the flat files
they seed from, and the checkout ships none of them: every invocation of
[harness/seed.sh] therefore refused with its fixture exit code, and the parity
protocol could not reach its first stage. The frozen loaders read those files, so the
files have to exist before anything else in the protocol means anything.

WHY THE FILES CANNOT SIMPLY BE COMMITTED
Fifteen of the seventeen distinct seed files are ORGANIZATION INDEXED or RELATIVE.
An indexed file under GnuCOBOL is a Berkeley DB database whose on-disk form depends on
the library version the image was built with, and a relative file is a fixed-length
record image with an implementation-defined layout. Committing either would commit an
opaque, unreviewable, version-specific binary and would tie the repository to one
build of one library. So the RECORDS are declared as text in the scenario file - which
is reviewable, diffable and version-independent - and the files are BUILT here.

HOW A FILE IS BUILT, AND WHY THIS WAY
Nothing about a record's layout is reimplemented. For every file except `system.dat`
the frozen loaders reach the flat file through a numbered handler with
`File-System-Used' set to zero [common/glbatchLD.cbl:L295-L304], so the handler owns
the SELECT, the FD, the key and the write. This tool therefore generates a driver
program that CALLS THAT SAME HANDLER, and it builds the driver's data division out of
THE HANDLER'S OWN LINKAGE COPY BLOCK, read from the frozen source at build time. The
record name, its layout, every picture clause and every `REPLACING' the handler applies
are consequently identical by construction rather than by transcription - there is no
table of record names in this file to fall out of date, and no packed-decimal layout is
computed here. COBOL's own MOVE performs every store, so the store semantics are the
frozen ones (R-2: no value is rendered to bytes by Python).

`system.dat' is the one exception, and the frozen code is the reason: every loader
reads it DIRECTLY through [copybooks/selsys.cob] - ORGANIZATION RELATIVE, relative key
`rrn' - and [copybooks/fdsys.cob], not through a handler [common/glbatchLD.cbl:L129],
[common/glbatchLD.cbl:L136]. Its writer therefore copies that select and that FD, and
still writes not one byte of layout of its own.

WHAT IS NEVER TAKEN FROM THE SCENARIO FILE
The system record carries the database account the loaders authenticate with -
`RDBMS-DB-Name', `RDBMS-User' and `RDBMS-Passwd' at [copybooks/wssystem.cob:L137-L139],
moved into `DB-Schema', `DB-UName' and `DB-UPass' by every handler's RDB path
(for example [common/acas000.cbl:L558]). Those three are filled from the ENVIRONMENT,
never from the committed YAML, and a scenario that tries to declare them is refused.
A credential in a committed scenario file would be a credential in the repository.

WHAT THIS TOOL DOES NOT DO
It does not touch the database, it issues no SQL and it needs no server. It writes
only inside the directory it is given. It never writes to $ACAS_REPO. It does not run
the loaders - that is [harness/seed.sh] - and it does not decide whether a scenario's
data is *right*, only that every declared file was written and reads back through the
frozen FD.

EXIT CODES
    0   every declared file was built and read back
    64  usage error
    65  a precondition failed - missing cobc, unwritable output, absent copybook
    66  the scenario file is missing, unreadable or malformed
    67  a declared field does not exist in the record, or its value is unusable
    68  cobc rejected a generated program
    69  a generated program failed at run time, or the read-back did not agree
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Final

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - the image installs it
    sys.stderr.write(
        "make_fixtures.py: PyYAML is not installed; it is required to read a "
        "scenario declaration.\n"
    )
    raise SystemExit(65) from None


EX_OK: Final[int] = 0
EX_USAGE: Final[int] = 64
EX_PRECONDITION: Final[int] = 65
EX_SCENARIO: Final[int] = 66
EX_DECLARATION: Final[int] = 67
EX_COMPILE: Final[int] = 68
EX_RUNTIME: Final[int] = 69

# Every file a scenario may declare, mapped to what the FROZEN code says about it.
#
#   handler   the numbered handler the loaders reach the file through, or None for the
#             one file they open themselves
#   defs      the File-Defs field the handler's SELECT assigns to, so the driver can
#             put the absolute path there. The names come from [copybooks/wsnames.cob]
#             and the per-file copybooks it includes, e.g. [copybooks/file07.cob]
#   loader    the load program [common/masterLD.sh] pairs the file with, recorded so a
#             reader of a generated program can find the frozen consumer
#
# The list is closed on purpose: a scenario naming a file that is not here is refused,
# because the twenty in-scope loaders are the only consumers the protocol has.
SEED_FILES: Final[dict[str, dict[str, str | None]]] = {
    "system.dat": {"handler": None, "defs": "file-0", "loader": "systemLD"},
    "ledger.dat": {"handler": "acas005", "defs": "file-5", "loader": "nominalLD"},
    "posting.dat": {"handler": "acas006", "defs": "file-6", "loader": "glpostingLD"},
    "batch.dat": {"handler": "acas007", "defs": "file-7", "loader": "glbatchLD"},
    "postings2irs.dat": {
        "handler": "acas008",
        "defs": "file-8",
        "loader": "slpostingLD",
    },
    "salesled.dat": {"handler": "acas012", "defs": "file-12", "loader": "salesLD"},
    "value.dat": {"handler": "acas013", "defs": "file-13", "loader": "valueLD"},
    "analysis.dat": {"handler": "acas015", "defs": "file-15", "loader": "analLD"},
    "invoice.dat": {"handler": "acas016", "defs": "file-16", "loader": "slinvoiceLD"},
    "openitm3.dat": {"handler": "acas019", "defs": "file-19", "loader": "otm3LD"},
    "purchled.dat": {"handler": "acas022", "defs": "file-22", "loader": "purchLD"},
    # THE ONE FILE WHOSE LAYOUT IS NOT READ FROM ITS HANDLER'S LINKAGE, and the reason
    # is a real divergence in the frozen tree rather than a convenience. acas026 copies
    # [copybooks/plwspinv.cob], whose 100-byte header is the record it lists in USING
    # [common/acas026.cbl:L227-L231] but whose LINE view is a SEPARATE 01 carrying an
    # OCCURS 40 table [copybooks/plwspinv.cob:L65-L66] that the USING clause does not
    # mention -- so through that copybook a line row cannot be named at all. The
    # posting program itself copies [copybooks/plwspinv2.cob:L135 of purchase/pl055.cbl]
    # instead, where the SAME 100 bytes carry a header view
    # [copybooks/plwspinv2.cob:L21] and a line view [copybooks/plwspinv2.cob:L56] as
    # REDEFINES, and where the base record is already named WS-PInvoice-Record -- the
    # very name acas026 uses, so no REPLACING is needed and the two are compatible at
    # the linkage boundary by construction. pl055 distinguishes the two row kinds by
    # item number exactly as its Sales counterpart does, branching to header analysis
    # on zero [purchase/pl055.cbl:L310-L311]. The Agent Action Plan names both members
    # of this pair for the same reason (section 0.4.1.3).
    # THE VIEW THE FROZEN PROGRAM READS THROUGH IS THEREFORE THE VIEW THE DATA MUST
    # SATISFY, and the record-name check in read_layout is what proves the substitution
    # is storage-compatible rather than merely plausible.
    "pinvoice.dat": {
        "handler": "acas026",
        "defs": "file-26",
        "loader": "plinvoiceLD",
        "layout": "plwspinv2.cob",
    },
    "openitm5.dat": {"handler": "acas029", "defs": "file-29", "loader": "otm5LD"},
    "irsacnts.dat": {
        "handler": "acasirsub1",
        "defs": "file-34",
        "loader": "irsnominalLD",
    },
    # SINGLE-RECORD HANDLER. acasirsub3 opens, reads or writes ONE record and closes
    # on every call [common/acasirsub3.cbl:L259-L310], [common/acasirsub3.cbl:L312-L338],
    # treating open and close as no-ops [common/acasirsub3.cbl:L199-L208] because "IRS
    # only does a read or write and not a direct open or close"
    # [common/acasirsub3.cbl:L168-L178]. Two consequences the builder MUST honour: a
    # second declared record would silently replace the first, because each write
    # re-opens OUTPUT and truncates; and a read-back loop would never terminate,
    # because EOF is never reported.
    "irsdflt.dat": {
        "handler": "acasirsub3",
        "defs": "file-35",
        "loader": "irsdfltLD",
        "single_record": True,
    },
    "irspost.dat": {
        "handler": "acasirsub4",
        "defs": "file-36",
        "loader": "irspostingLD",
    },
    # SINGLE-RECORD HANDLER, for the same reason: acasirsub5 is the final-accounts
    # twin of acasirsub3 and the latter's own header names them together as the two
    # modules that behave this way [common/acasirsub3.cbl:L168-L172].
    "irsfinal.dat": {
        "handler": "acasirsub5",
        "defs": "file-37",
        "loader": "irsfinalLD",
        "single_record": True,
    },
}

# system.dat IS FOUR DIFFERENT RECORDS IN ONE RELATIVE FILE, and this is the single
# most surprising fact about the seed contract. [copybooks/selsys.cob] declares it
# ORGANIZATION RELATIVE with relative key `rrn', and the four system loaders each read
# a DIFFERENT relative record out of it, each through its own copybook:
#   rrn 1  systemLD [common/systemLD.cbl:L227]  wssystem.cob  System-Record    -> SYSTEM-REC
#   rrn 2  dfltLD   [common/dfltLD.cbl:L221]    wsdflt.cob    Default-Record   -> SYSDEFLT-REC
#   rrn 3  finalLD  [common/finalLD.cbl:L221]   wsfinal.cob   Final-Record     -> SYSFINAL-REC
#   rrn 4  sys4LD   [common/sys4LD.cbl:L226]    wssys4.cob    System-Record-4  -> SYSTOT-REC
# The frozen handler agrees: acas000 dispatches by moving File-Key-No straight into rrn
# [common/acas000.cbl:L461], [common/acas000.cbl:L473], [common/acas000.cbl:L481], and
# rejects a key outside 1 to 5 [common/acas000.cbl:L335].
# ALL FOUR ARE 1024 BYTES, each copybook saying so in its own header, which is why they
# can share one relative file at all.
# CONSEQUENCE, AND THE REASON THIS TOOL REFUSES A PARTIAL DECLARATION: masterLD runs all
# four loaders unconditionally [common/masterLD.sh:L50-L88], so a system.dat carrying
# only the parameter record would leave three of them reading a relative slot that was
# never written -- and the last of the four is tested against zero rather than 63
# [common/masterLD.sh:L83-L86], so that failure ABORTS the seed. A scenario therefore
# states all four, and states them explicitly even when three are all-zero, because an
# undefined pre-state is a difference waiting to happen.
SYSTEM_RELATIVE_RECORDS: Final[dict[str, tuple[str, str, str]]] = {
    "1": ("wssystem.cob", "System-Record", "SYSTEM-REC via systemLD"),
    "2": ("wsdflt.cob", "Default-Record", "SYSDEFLT-REC via dfltLD"),
    "3": ("wsfinal.cob", "Final-Record", "SYSFINAL-REC via finalLD"),
    "4": ("wssys4.cob", "System-Record-4", "SYSTOT-REC via sys4LD"),
}

# The six system-record connection fields filled from the environment and refused in a
# scenario. The widths are the actual declarations in wssystem.cob rather than the
# narrower x(12) RDB-Data fields used after the frozen handler copies them.
CONNECTION_FIELD_BINDINGS: Final[tuple[tuple[str, str, int, bool], ...]] = (
    ("RDBMS-DB-Name", "ACAS_DB_NAME", 12, True),
    ("RDBMS-User", "ACAS_DB_USER", 12, True),
    ("RDBMS-Passwd", "ACAS_DB_PASSWORD", 12, True),
    ("RDBMS-Host", "ACAS_DB_HOST", 32, True),
    ("RDBMS-Port", "ACAS_DB_PORT", 5, True),
    # An empty socket is the frozen TCP-only declaration and is therefore valid.
    ("RDBMS-Socket", "ACAS_DB_SOCKET", 64, False),
)
CREDENTIAL_FIELDS: Final[tuple[str, ...]] = tuple(
    field for field, _environment, _width, _required in CONNECTION_FIELD_BINDINGS
)

# A COBOL data name, as this tool is willing to emit it. Deliberately narrow in its
# CHARACTER SET -- the name is interpolated into generated source, so anything that
# could carry a statement separator, a quote or a period is refused rather than escaped
# -- but not in its length: the frozen copybooks contain names longer than the 30
# characters COBOL-85 allowed, `System-Record-Version-Secondary' at
# [copybooks/wssystem.cob:L54] being 31, and a limit that refused a name the frozen
# code declares would be this tool disagreeing with the specification.
NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z][A-Za-z0-9-]{0,62}$")

# A value this tool will emit as a NUMERIC literal. Everything else becomes an
# alphanumeric literal, and the choice is checked against the field's own picture so a
# mismatch is a refusal rather than a silently wrong store.
NUMERIC_RE: Final[re.Pattern[str]] = re.compile(r"^[+-]?[0-9]+(\.[0-9]+)?$")


def fail(code: int, headline: str, *detail: str) -> "NoReturn":  # type: ignore[name-defined]
    """Report and stop. One shape for every refusal, as the shell scripts have."""
    sys.stderr.write(f"make_fixtures.py: {headline}\n")
    for line in detail:
        sys.stderr.write(f"    {line}\n")
    raise SystemExit(code)


# =============================================================================
# READING THE FROZEN SOURCES.  Read-only, every one of them, and never modified.
# =============================================================================
def handler_linkage_copies(repo: Path, handler: str) -> list[str]:
    """The copy statements a handler's LINKAGE SECTION contains, in order.

    This is what makes the generated driver agree with the handler about the record:
    the same five copy statements, with the same REPLACING clauses, produce the same
    names and the same layout. Comments are dropped and continuation lines are joined,
    because a copy statement in this codebase routinely spans several lines.
    """
    source = repo / "common" / f"{handler}.cbl"
    if not source.is_file():
        fail(
            EX_PRECONDITION,
            f"the frozen handler {source} is not in the checkout.",
            "It supplies the record layout the generated writer uses, so nothing can",
            "be built without it.",
        )
    text = source.read_text(encoding="utf-8", errors="replace")
    lowered = text.lower()
    start = lowered.find("linkage section")
    if start < 0:
        fail(
            EX_PRECONDITION,
            f"{source} has no LINKAGE SECTION, so its record layout cannot be read.",
        )
    end = lowered.find("procedure division", start)
    if end < 0:
        end = len(text)

    statements: list[str] = []
    buffer: str | None = None
    for raw in text[start:end].splitlines():
        line = raw.strip()
        if not line or line.startswith("*>"):
            continue
        if buffer is None:
            if not line.lower().startswith("copy "):
                continue
            buffer = line
        else:
            buffer = f"{buffer} {line}"
        if buffer.rstrip().endswith("."):
            # A trailing inline comment is legal after the period and is dropped.
            statements.append(re.sub(r"\s+", " ", buffer).strip())
            buffer = None
    if not statements:
        fail(
            EX_PRECONDITION,
            f"{source} declares no copybook in its LINKAGE SECTION.",
        )
    return statements


def copybook_of(statement: str) -> str:
    """The copybook a copy statement names."""
    match = re.match(r'copy\s+"([^"]+)"', statement, re.IGNORECASE)
    if match is None:
        fail(EX_PRECONDITION, f"could not read a copybook name from: {statement}")
    return match.group(1)


def replacements_of(statement: str) -> dict[str, str]:
    """The REPLACING pairs a copy statement applies, lowercased on the left.

    Needed because a declared field name has to be matched against the record as the
    HANDLER sees it: acas013 renames `VA-Code' to `WS-VA-Code'
    [common/acas013.cbl], and a scenario declaring either spelling must resolve.
    """
    match = re.search(r"\breplacing\b(.*)$", statement, re.IGNORECASE | re.DOTALL)
    if match is None:
        return {}
    body = match.group(1).rstrip(". ")
    tokens = [t for t in re.split(r"\s+", body.strip()) if t]
    pairs: dict[str, str] = {}
    index = 0
    while index + 2 < len(tokens) + 1:
        if index + 2 >= len(tokens) + 1:
            break
        if index + 2 > len(tokens):
            break
        left, by, right = tokens[index], tokens[index + 1], tokens[index + 2]
        if by.lower() != "by":
            break
        pairs[left.lower()] = right
        index += 3
    return pairs


class Layout:
    """The elementary fields of one record copybook, and what each will accept.

    Only what a MOVE needs is read: the name, whether the picture is numeric or
    alphanumeric, and whether the item is a group, a REDEFINES or an OCCURS. Nothing
    here computes an offset or a byte width - COBOL does the storing.
    """

    def __init__(self) -> None:
        self.numeric: dict[str, str] = {}
        self.alphanumeric: dict[str, str] = {}
        self.groups: set[str] = set()
        self.excluded: dict[str, str] = {}
        # Character width of every elementary field held in DISPLAY, which is the only
        # kind a `raw' declaration can address. A COMP-3 or binary field has no
        # character view to write bytes into, so it is deliberately absent here.
        self.display_width: dict[str, int] = {}
        # The 01-level group each field actually descends from, which is NOT always the
        # record the handler is called with. Several in-scope copybooks describe one
        # buffer through more than one 01-level view: the invoice record is declared
        # once and then REDEFINED twice, as a header at
        # [copybooks/slwsinv2.cob:L38] and as a line at [copybooks/slwsinv2.cob:L92],
        # so `ih-net' and `il-net' are subordinate to those views and NOT to the base
        # record. Qualifying them with the base record does not compile, which is how
        # this was found. The views share storage, so a MOVE through the right
        # qualifier lands in the same bytes the handler is handed.
        self.root: dict[str, str] = {}
        # Fields that live inside an OCCURS and therefore REQUIRE a subscript, mapped
        # to (table name, bound). Some in-scope records are nothing but a table: the
        # IRS defaults record is a single `Def-Group occurs 33'
        # [copybooks/irswsdflt.cob:L8-L12] and the posting section indexes entries 31
        # and 32 of it by name [irs/irs030.cbl:L871], so a tool that could not address
        # a table entry could not seed the IRS scenario at all.
        self.subscripted: dict[str, tuple[str, int]] = {}

    def qualifier(self, name: str, fallback: str) -> str:
        """The 01-level group a MOVE to this field must be qualified with."""
        return self.root.get(name.lower(), fallback)

    def raw_target(self, name: str) -> tuple[str, int]:
        """Return (declared name, character width) for a field a `raw' value may set.

        Refuses anything a byte-exact store would be meaningless on, so the escape
        hatch cannot quietly do the wrong thing.
        """
        kind, declared = self.classify(name)
        width = self.display_width.get(name.lower())
        if width is None:
            fail(
                EX_DECLARATION,
                f"{declared} is not held in DISPLAY, so a raw value cannot be stored "
                "in it.",
                "A COMP-3 or binary field has no character view; declare the value as "
                "ordinary text and let COBOL's own MOVE perform the store.",
            )
        if kind == "alphanumeric":
            fail(
                EX_DECLARATION,
                f"{declared} is already an alphanumeric field, so raw adds nothing.",
                "Declare the value as ordinary text.",
            )
        return declared, width

    def classify(self, name: str) -> tuple[str, str]:
        """Return ("numeric"|"alphanumeric", the name as declared)."""
        key = name.lower()
        if key in self.numeric:
            return "numeric", self.numeric[key]
        if key in self.alphanumeric:
            return "alphanumeric", self.alphanumeric[key]
        if key in self.excluded:
            fail(
                EX_DECLARATION,
                f"the field {name} cannot be set by this tool: {self.excluded[key]}",
                "Declare an elementary field that is neither a REDEFINES nor a table.",
            )
        if key in self.groups:
            fail(
                EX_DECLARATION,
                f"{name} is a group item, and a group cannot be given a value here.",
                "Declare its elementary members instead.",
            )
        fail(
            EX_DECLARATION,
            f"the record has no field named {name}.",
            "Field names are spelled exactly as the frozen copybook spells them.",
        )


# The usages that make an item numeric even with no PICTURE of its own. All of them
# occur in the in-scope record copybooks: `Run-Date binary-long'
# [copybooks/wssystem.cob:L67] and the seven `binary-long' statistics fields
# [copybooks/wssl.cob:L46-L52] are the ones a scenario is most likely to declare.
_NUMERIC_USAGE: Final[re.Pattern[str]] = re.compile(
    r"\b(binary-char|binary-short|binary-long|binary-double|binary"
    r"|comp-1|comp-2|comp-3|comp-4|comp-5|comp|computational[0-9-]*"
    r"|packed-decimal|index)\b"
)


def _display_width(picture: str) -> int:
    """Character width of a DISPLAY picture, or zero if it cannot be read.

    Only the symbols the in-scope copybooks actually use are counted. `V' and `P' are
    implied positions that occupy no byte, and an `S' occupies none either, because
    none of these copybooks writes SIGN IS SEPARATE -- the sign rides in the final
    digit, which is exactly why a signed DISPLAY field is the same width as its
    unsigned twin.
    """
    expanded = re.sub(
        r"([9xaz])\((\d+)\)",
        lambda m: m.group(1) * int(m.group(2)),
        picture.lower(),
    )
    if re.search(r"[^9xazsvp]", expanded):
        return 0
    return sum(1 for character in expanded if character in "9xaz")


def _replace_tokens(text: str, replacements: dict[str, str]) -> str:
    """Apply COPY REPLACING to a whole declaration, token by whole token.

    Whole-token only, which matters here: `Invoice-Nos' is a replacement operand and
    `WS-Invoice-Nos' contains it, so a substring rewrite would corrupt names the
    compiler leaves alone.
    """
    if not replacements:
        return text

    def swap(match: re.Match[str]) -> str:
        return replacements.get(match.group(0).lower(), match.group(0))

    return re.sub(r"[A-Za-z][A-Za-z0-9-]*", swap, text)


def _copybook_declarations(
    repo: Path, copybooks: list[str], replacements: dict[str, str]
) -> list[tuple[int, str, str]]:
    """Every data declaration of one or more copybooks, in source order.

    Returns (level, name-as-the-handler-sees-it, the rest of the declaration). A
    copybook may itself COPY another -- `fdsys.cob' copies `wssystem.cob' -- and the
    include is expanded IN PLACE, because level numbers only mean anything in order.
    """
    declarations: list[tuple[int, str, str]] = []
    seen: set[str] = set()

    def expand(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        path = repo / "copybooks" / name
        if not path.is_file():
            fail(EX_PRECONDITION, f"the frozen copybook {path} is not in the checkout.")
        # A declaration may span lines; join to the terminating period first, so a
        # picture or usage clause on a continuation line is still seen.
        joined: list[str] = []
        buffer = ""
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("*>"):
                continue
            # Strip a trailing inline comment; it can carry stray punctuation.
            line = re.sub(r"\*>.*$", "", line).strip()
            if not line:
                continue
            buffer = f"{buffer} {line}".strip() if buffer else line
            if buffer.endswith("."):
                joined.append(buffer)
                buffer = ""
        if buffer:
            joined.append(buffer)
        for statement in joined:
            nested = re.match(r'copy\s+"([^"]+)"', statement, re.IGNORECASE)
            if nested is not None:
                expand(nested.group(1))
                continue
            match = re.match(
                r"^(\d\d)\s+([A-Za-z][A-Za-z0-9-]*)\b(.*)$", statement
            )
            if match is None:
                continue
            level_text, field, rest = match.groups()
            level = int(level_text)
            # An 88 is a condition name, not a field, and a 66 renames one.
            if level in (66, 88):
                continue
            # COPY REPLACING SUBSTITUTES THE TOKEN EVERYWHERE, not only where a name is
            # declared -- so it also rewrites the operand of a REDEFINES. Applying it to
            # the declared name alone was a real bug: acas016 renames `Invoice-Record'
            # [common/acas016.cbl:L220-L223], which makes
            # [copybooks/slwsinv2.cob:L38] read `Invoice-Header redefines
            # WS-Invoice-Record' in the compiler's eyes, and a reader that left the
            # operand un-renamed concluded the header view was a DETACHED buffer and
            # refused every `ih-' field. The rest of the declaration is rewritten here
            # for the same reason the compiler rewrites it.
            declarations.append(
                (
                    level,
                    replacements.get(field.lower(), field),
                    _replace_tokens(rest, replacements),
                )
            )

    for entry in copybooks:
        expand(entry)
    return declarations


def read_layout(
    repo: Path,
    copybooks: list[str],
    replacements: dict[str, str],
    *,
    record: str | None = None,
) -> Layout:
    """Classify every field of a record: elementary numeric, elementary text, or not
    settable.

    GROUP OR ELEMENTARY IS DECIDED BY THE LEVEL NUMBERS, not by whether a PICTURE is
    present. Both readings are needed and only one is right: `03 Amounts comp-3.'
    [copybooks/wsbatch.cob] is a GROUP that carries a usage clause and no picture,
    while `05 Run-Date binary-long.' [copybooks/wssystem.cob:L67] is ELEMENTARY with
    no picture either. An item is a group exactly when the declaration that follows it
    has a HIGHER level number.
    """
    layout = Layout()
    declarations = _copybook_declarations(repo, copybooks, replacements)
    root = ""
    # 01-level groups that describe the SAME BYTES the handler is handed: the record
    # itself, plus anything that REDEFINES it directly or transitively. Anything else
    # at 01 level is a SEPARATE BUFFER, and a MOVE into it would be silently discarded
    # -- see the class comment on Layout.root, and note the case that forced this:
    # [copybooks/plwspinv.cob:L65] declares `Pinvoice-Bodies' as an independent 01 that
    # acas026 carries in LINKAGE but does NOT list in its USING clause
    # [common/acas026.cbl:L227-L231], so its `il-' fields reach no file at all.
    attached: set[str] = set()
    detached: set[str] = set()
    # (level, the innermost OCCURS in effect for anything subordinate, as
    # (table name, bound), or None when there is none)
    stack: list[tuple[int, tuple[str, int] | None]] = []
    for index, (level, field, rest) in enumerate(declarations):
        key = field.lower()
        body = rest.lower()
        while stack and stack[-1][0] >= level:
            stack.pop()
        under_occurs = stack[-1][1] if stack else None
        if level == 1:
            root = field
            target = re.search(r"\bredefines\s+([A-Za-z][A-Za-z0-9-]*)", body)
            if not attached and target is None:
                # The first 01 of a record copybook IS the record.
                attached.add(key)
            elif target is not None and target.group(1).lower() in attached:
                attached.add(key)
            else:
                detached.add(key)
        elif root:
            layout.root[key] = root
        is_group = (
            index + 1 < len(declarations) and declarations[index + 1][0] > level
        )
        occurs = re.search(r"\boccurs\s+(\d+)", body)
        if is_group:
            layout.groups.add(key)
            own = (field, int(occurs.group(1))) if occurs is not None else None
            stack.append((level, own or under_occurs))
            continue
        if root.lower() in detached:
            layout.excluded[key] = (
                f"it belongs to {root}, which is a SEPARATE 01-level buffer and not "
                "the record the handler writes, so a value here would be discarded"
            )
            continue
        if "redefines" in body:
            layout.excluded[key] = "it REDEFINES another field"
            continue
        if occurs is not None:
            layout.excluded[key] = (
                "it is itself a table (OCCURS), so declare the elementary members of "
                "its entries rather than the table"
            )
            continue
        if under_occurs is not None:
            # Settable, but ONLY through the subscripted form. Recorded rather than
            # excluded, because refusing it would make the IRS defaults unseedable.
            layout.subscripted[key] = under_occurs
        if field.lower() == "filler":
            continue
        picture = re.search(r"\bpic(?:ture)?\s+(?:is\s+)?([^\s.]+)", body)
        if picture is not None:
            text = picture.group(1)
            if re.search(r"[9szvp]", text):
                layout.numeric[key] = field
            else:
                layout.alphanumeric[key] = field
            if not _NUMERIC_USAGE.search(body):
                width = _display_width(text)
                if width:
                    layout.display_width[key] = width
            continue
        if _NUMERIC_USAGE.search(body):
            layout.numeric[key] = field
            continue
        layout.excluded[key] = (
            "it declares neither a picture nor a numeric usage, so this tool cannot "
            "tell what a value for it would mean"
        )
    # Turn the "first 01 is the record" reading into a CHECK rather than a belief. If a
    # copybook ever ordered its views differently, the attached/detached split above
    # would be inverted and values would be silently discarded, which is the one
    # failure mode this tool must never have.
    if record is not None and record.lower() not in attached:
        fail(
            EX_DECLARATION,
            f"{record} is the record {copybooks[0]} is used as, but it is not the "
            "first 01-level group of that copybook nor a REDEFINES of it.",
            "This tool decides which 01-level views share the handler's bytes from",
            "that relationship, so it refuses rather than guess.",
        )
    return layout


# =============================================================================
# GENERATING A WRITER
# =============================================================================
def refuse_unplaceable_text(text: str, *, what: str, code: int) -> None:
    """Refuse text that cannot be placed inside a generated COBOL literal.

    ⭐ ONE RULE, STATED ONCE. Everything this tool interpolates into generated source
    -- a declared VALUE, a declared raw byte image, an output path -- is going into
    source that is then COMPILED AND RUN, so all of it has to survive the same two
    hazards, and until now each site spelled the rule for itself:

      * a double quote CLOSES the literal, and whatever follows it becomes generated
        COBOL rather than data. That is arbitrary statements from an input;
      * any control character ends or corrupts the line. A newline is the obvious one
        and was the only one three of the four sites checked, but a carriage return
        does it too, and NUL and DEL make the emitted source undiagnosable.

    Neither is escaped. There is no escaping that makes arbitrary text safe inside a
    fixed-format-descended literal, and an escape that half-works is worse than a
    refusal because it fails silently at compile time instead of loudly here.

    Args:
        text: The text about to be interpolated.
        what: What it is, for the diagnosis.
        code: The exit status to fail with -- declaration inputs and command-line
            inputs are different faults and get different statuses.
    """
    if '"' in text:
        fail(
            code,
            f"{what} contains a double quote: {text!r}.",
            "It is interpolated into a COBOL alphanumeric literal in source this tool",
            "compiles and runs, so a quote would close the literal and leave the",
            "remainder as generated COBOL. It is refused rather than escaped.",
        )
    for index, character in enumerate(text):
        if ord(character) < 0x20 or ord(character) == 0x7F:
            fail(
                code,
                f"{what} contains a control character (0x{ord(character):02X}) at "
                f"offset {index}: {text!r}.",
                "It is interpolated into generated COBOL source, where a line break",
                "ends the line and starts another one, and where a NUL or a DEL makes",
                "the emitted source undiagnosable. Refused rather than escaped.",
            )


def cobol_literal(kind: str, value: str, field: str) -> str:
    """A COBOL literal for a declared text value, checked against the field's kind."""
    if kind == "numeric":
        if not NUMERIC_RE.match(value):
            fail(
                EX_DECLARATION,
                f"{field} is a numeric field and {value!r} is not a number.",
                "Declare digits, with an optional sign and an optional decimal point.",
            )
        # Emitted verbatim: COBOL aligns it on the receiving field's implied decimal
        # point and truncates toward zero, which is the frozen store semantics.
        return value
    refuse_unplaceable_text(
        value, what=f"the value for {field}", code=EX_DECLARATION
    )
    return f'"{value}"'


#: The longest path this tool will interpolate into a generated COBOL literal.
#: A COBOL alphanumeric literal has a maximum length and a source line has a fixed
#: area; a path long enough to need continuation would produce source that either
#: does not compile or -- worse -- compiles with the tail silently dropped, so it is
#: refused. The frozen file-name field it is moved into is itself bounded:
#: `wsnames.cob' declares each as `pic x(n)', so a path past that is not usable by
#: the loaders either.
COBOL_PATH_LITERAL_MAX: Final[int] = 160


def cobol_path_literal(path: str, *, what: str) -> str:
    """Return `path` as a COBOL alphanumeric literal, or refuse it.

    ⭐ EVERY PATH THIS TOOL PUTS INTO GENERATED COBOL COMES THROUGH HERE. The output
    directory arrives on the command line, each seed file's path is derived from it,
    and the result is interpolated into four `move "<path>" to <field>.' statements
    and two comment lines of source that is then COMPILED AND RUN. Declared VALUES
    were already held to this standard; the paths were the gap, and they are the input
    an operator supplies directly.
    The quote-and-control-character rule itself lives in `refuse_unplaceable_text' so
    that this function and the two declared-value paths cannot drift apart -- they
    previously spelled it three different ways, and only this one covered a carriage
    return, a NUL or a DEL. What this function adds on top of the shared rule is the
    LENGTH budget, which applies to a path (it is derived, and can be arbitrarily
    long) but not to a declared raw value (it must equal its field's width exactly).
    A comment line is checked by the same rule: `*>' cannot execute anything, but a
    newline inside one still ends the comment and hands the remainder to the compiler.

    Args:
        path: The path to interpolate.
        what: What it is, for the diagnosis - e.g. `the --out directory`.

    Returns:
        The path unchanged, once it has been shown to be placeable. It is returned
        WITHOUT quotes because the two call sites need different framing -- a `move'
        statement supplies its own pair, a `*>' comment wants none -- and because a
        caller that forgets the quotes generates COBOL that fails to compile, which
        is a loud failure rather than a silent one.
    """
    if not path:
        fail(EX_PRECONDITION, f"{what} is empty, and it has to name a file.")
    # The shared rule -- the same one every declared VALUE and raw byte image is held
    # to -- under the command-line status, because a path is what the operator typed.
    refuse_unplaceable_text(path, what=what, code=EX_PRECONDITION)
    if len(path) > COBOL_PATH_LITERAL_MAX:
        fail(
            EX_PRECONDITION,
            f"{what} is {len(path)} characters, past the "
            f"{COBOL_PATH_LITERAL_MAX} this tool will place in a COBOL literal.",
            "A longer literal would need continuation, and source that needs it",
            "either fails to compile or compiles with the tail dropped. Choose a",
            "shorter --out directory.",
        )
    return path


def moves_for(
    layout: Layout, record: str, fields: dict[str, str], *, where: str
) -> list[str]:
    """The MOVE statements one declared record needs, in declaration order."""
    lines: list[str] = []
    for name, value in fields.items():
        if not isinstance(name, str) or not NAME_RE.match(name):
            fail(
                EX_DECLARATION,
                f"{name!r} in {where} is not a plain COBOL data name.",
                "It is interpolated into generated source, so it is refused.",
            )
        if isinstance(value, list):
            lines.extend(
                table_moves_for(layout, record, name, value, where=where)
            )
            continue
        if name.lower() in layout.subscripted:
            table, bound = layout.subscripted[name.lower()]
            fail(
                EX_DECLARATION,
                f"{name} in {where} is inside the table {table} (OCCURS {bound}), so "
                "it needs a subscript and a bare value cannot say which entry.",
                "Declare a list of entries instead, each an `at' and a `value':",
                f"  {name}:",
                '    - at: "31"',
                '      value: "..."',
            )
        if isinstance(value, dict):
            lines.append(raw_move_for(layout, record, name, value, where=where))
            continue
        if not isinstance(value, str):
            fail(
                EX_DECLARATION,
                f"the value for {name} in {where} must be a quoted string.",
                "Every value is declared as text so that YAML cannot parse a money",
                "figure into a binary float (R-2). Quote it.",
            )
        kind, declared = layout.classify(name)
        literal = cobol_literal(kind, value, declared)
        owner = layout.qualifier(name, record)
        lines.append(f"     move     {literal} to {declared} in {owner}")
    return lines


def connection_accepts_for(
    layout: Layout, record: str, bindings: dict[str, str]
) -> list[str]:
    """The six connection fields, accepted from the environment at RUN time.

    ⭐ WHY `ACCEPT ... FROM ENVIRONMENT` AND NOT `MOVE "..."` (finding F-31). The
    values reach the same fields with the same bytes either way, but a `MOVE` puts
    them in the GENERATED SOURCE, where a kept build directory or an echoed compiler
    diagnostic publishes the database account. `ACCEPT` names the variable and reads
    it when the writer runs, so the source is credential-free and can be kept,
    listed or attached to a bug report without redaction.

    The statement form is the literal-name one - `accept <item> from environment
    "NAME"` - which GnuCOBOL 3.2 accepts directly. Every field is preceded by
    `initialize <record>`, so a variable that is absent or empty leaves the field at
    spaces, which is exactly what an empty `RDBMS-Socket` means
    [copybooks/wssystem.cob:L137-L144] and what the frozen TCP-only declaration
    carries.

    Args:
        layout: the parameter record's layout, for the declared spelling and owner
            of each field.
        record: the record the fields belong to, for qualification.
        bindings: field name to environment variable name, as
            `credentials_from_env` returned it - so the names emitted are the ones
            whose presence and width that function has already checked, and there is
            no second list to drift.

    Returns:
        One `accept` line per connection field, in declaration order.
    """
    lines: list[str] = []
    for field, _environment, _width, _required in CONNECTION_FIELD_BINDINGS:
        environment = bindings[field]
        _kind, declared = layout.classify(field)
        owner = layout.qualifier(field, record)
        lines.append(
            f"     accept   {declared} in {owner} from environment "
            f'"{environment}"'
        )
    return lines


def table_moves_for(
    layout: Layout,
    record: str,
    name: str,
    entries: list,
    *,
    where: str,
) -> list[str]:
    """The MOVEs for a table field declared as a list of `at'/`value' entries.

    THE SUBSCRIPT IS EMITTED UNQUALIFIED, which is the shape the frozen code itself
    uses -- `def-acs (31)' at [irs/irs030.cbl:L871] and `def-codes (w)' at
    [irs/irs030.cbl:L794] -- and is unambiguous here because a generated driver copies
    one record layout and the four shared copybooks, none of which repeats these names.
    The index is BOUNDS-CHECKED against the OCCURS clause, because writing past a table
    is the one mistake a fixture can make that no read-back would reveal.
    """
    key = name.lower()
    if key not in layout.subscripted:
        _kind, declared = layout.classify(name)
        fail(
            EX_DECLARATION,
            f"{declared} in {where} is not inside a table, so a list of entries is "
            "not what it takes.",
            "Declare a single quoted value.",
        )
    table, bound = layout.subscripted[key]
    kind, declared = layout.classify(name)
    lines: list[str] = []
    seen: set[int] = set()
    for position, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or "at" not in entry:
            fail(
                EX_DECLARATION,
                f"entry {position} of {declared} in {where} must be a mapping with an "
                "`at' and a `value'.",
            )
        extra = set(entry) - {"at", "value", "raw"}
        if extra or not ({"value", "raw"} & set(entry)):
            fail(
                EX_DECLARATION,
                f"entry {position} of {declared} in {where} must hold `at' and exactly "
                f"one of `value' or `raw'. It holds: {sorted(entry)}.",
            )
        index_text = entry["at"]
        if not isinstance(index_text, str) or not index_text.isdigit():
            fail(
                EX_DECLARATION,
                f"the `at' of entry {position} of {declared} in {where} must be a "
                "quoted whole number.",
            )
        index = int(index_text)
        if index < 1 or index > bound:
            fail(
                EX_DECLARATION,
                f"entry {position} of {declared} in {where} addresses {index}, and "
                f"{table} holds entries 1 to {bound} [OCCURS {bound}].",
                "Writing past a table is the one fixture mistake a read-back would not",
                "reveal, so it is refused here.",
            )
        if index in seen:
            fail(
                EX_DECLARATION,
                f"{declared} in {where} declares entry {index} more than once, so one "
                "of the two would silently win.",
            )
        seen.add(index)
        if "raw" in entry:
            width = layout.display_width.get(key)
            text = entry["raw"]
            if width is None or kind == "alphanumeric":
                fail(
                    EX_DECLARATION,
                    f"a raw value is not available for {declared}: it is either not "
                    "held in DISPLAY or already alphanumeric.",
                )
            if not isinstance(text, str) or len(text) != width:
                fail(
                    EX_DECLARATION,
                    f"the raw value for {declared} entry {index} must be a quoted "
                    f"string of exactly {width} character(s).",
                )
            refuse_unplaceable_text(
                text,
                what=f"the raw value for {declared} entry {index}",
                code=EX_DECLARATION,
            )
            lines.append(
                f'     move     "{text}" to {declared} ({index}) (1:{width})'
            )
            continue
        value = entry["value"]
        if not isinstance(value, str):
            fail(
                EX_DECLARATION,
                f"the value of entry {index} of {declared} in {where} must be a quoted "
                "string (rule R-2).",
            )
        literal = cobol_literal(kind, value, declared)
        lines.append(f"     move     {literal} to {declared} ({index})")
    return lines


def raw_move_for(
    layout: Layout,
    record: str,
    name: str,
    value: dict,
    *,
    where: str,
) -> str:
    """The MOVE for a `{raw: "..."}' declaration: bytes stored verbatim.

    WHY THIS EXISTS AT ALL, AND WHY IT IS OPT-IN. Some frozen guards can only be
    reached by a field holding something its own picture does not describe. The one
    this harness needs is `if post-batch not numeric' [general/gl072.cbl:L291-L292],
    which tests a work-file field written from `Batch pic 9(5)'
    [copybooks/wspost.cob:L15]: an ordinary MOVE of digits can never make it true, so
    a scenario that means to exercise that skip has to be able to say so. Removing the
    data an anomaly needs is forbidden (rule R-4), and quietly coercing it would be
    the same removal wearing a different hat.
    Storing bytes into a numeric-display item is done by reference modification, which
    yields an alphanumeric receiving item and therefore performs no numeric
    conversion. That it does so in this compiler, and that the guard becomes reachable
    as a result, was MEASURED against GnuCOBOL 3.2 rather than assumed.
    The form is a one-key mapping so that it can never be mistaken for data: an
    ordinary value is a plain string, and a value that bypasses the field's own
    picture has to be written as one deliberately.
    """
    if set(value) != {"raw"}:
        fail(
            EX_DECLARATION,
            f"the value for {name} in {where} is a mapping, so it must hold exactly "
            f"one key, raw. It holds: {sorted(value) or 'nothing'}.",
        )
    text = value["raw"]
    if not isinstance(text, str):
        fail(
            EX_DECLARATION,
            f"the raw value for {name} in {where} must be a quoted string.",
        )
    refuse_unplaceable_text(
        text, what=f"the raw value for {name} in {where}", code=EX_DECLARATION
    )
    declared, width = layout.raw_target(name)
    if len(text) != width:
        fail(
            EX_DECLARATION,
            f"the raw value for {declared} in {where} is {len(text)} character(s) and "
            f"the field holds exactly {width}.",
            "A raw value is stored byte for byte, so it is neither padded nor",
            "truncated: state all of it or none of it.",
        )
    owner = layout.qualifier(name, record)
    return f'     move     "{text}" to {declared} in {owner} (1:{width})'


def writer_via_handler(
    *,
    handler: str,
    record: str,
    defs_field: str,
    linkage: list[str],
    path: str,
    records: list[list[str]],
) -> str:
    """A driver that writes one flat file by calling its frozen handler.

    The shape is the loaders' own: set File-System-Used to zero so the handler takes
    its Cobol-file path [common/glbatchLD.cbl:L295-L304], open output, write each
    record, close. Every status is checked, because a handler reports through
    `fs-reply' and never through a process status.
    """
    body: list[str] = []
    for index, moves in enumerate(records, start=1):
        body.append(f"*>   record {index}")
        body.append(f"     initialize {record}")
        body.extend(moves)
        body.append(f'     move     {index} to WS-Fixture-Seq')
        body.append("     perform  fx-write")
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfx.",
            "*>",
            "*>  GENERATED by harness/make_fixtures.py. Not committed, not frozen, and",
            "*>  never edited by hand: rebuild it by re-running the builder.",
            "*>",
            f'*>  Writes {cobol_path_literal(path, what="the seed file path")}',
            f"*>  through the frozen handler {handler}, whose own LINKAGE copy block is",
            "*>  reproduced verbatim below so that the record name and every picture",
            "*>  clause are the handler's, not this generator's.",
            "*>",
            "       environment division.",
            "       configuration section.",
            "       data division.",
            "       working-storage section.",
            "*>",
            "*>  The frozen handler's own linkage declarations, in its own order.",
            *(f" {statement}" for statement in linkage),
            "*>",
            " 01  WS-Fixture-Seq        pic 9(4) value zero.",
            " 01  WS-Fixture-Written    pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            "*>",
            "*>  Zero means: take the Cobol flat-file path, not the RDB path. The RDB",
            "*>  path would need the generated bridge programs and a live server, and a",
            "*>  fixture builder has no business touching either.",
            "*>",
            "     move     zero to File-System-Used",
            "                      FA-File-System-Used.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     set      fn-open to true.",
            "     set      fn-output to true.",
            f'     perform  fx-call.',
            "     if       fs-reply not = zero",
            '              display "acasfx: open output failed, fs-reply = "',
            "                      fs-reply \" we-error = \" we-error",
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "*>",
            *body,
            "*>",
            "     set      fn-close to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfx: close failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            '     display  "acasfx: wrote " WS-Fixture-Written " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "*>",
            " fx-write.",
            "     set      fn-write to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfx: write failed on record "',
            "                      WS-Fixture-Seq \" fs-reply = \" fs-reply",
            "                      \" we-error = \" we-error",
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "     add      1 to WS-Fixture-Written.",
            "*>",
            " fx-call.",
            f'     call     "{handler}" using System-Record',
            f"                              {record}",
            "                              File-Access",
            "                              File-Defs",
            "                              ACAS-DAL-Common-data.",
            "",
        ]
    )


def writer_for_system(
    *, defs_field: str, path: str, records: dict[str, list[str]]
) -> str:
    """A writer for `system.dat', which every loader opens itself.

    [copybooks/selsys.cob] declares it ORGANIZATION RELATIVE with relative key `rrn'
    and [copybooks/fdsys.cob] gives it the system record, so the select and the FD are
    copied here exactly as the loaders copy them
    [common/glbatchLD.cbl:L129], [common/glbatchLD.cbl:L136]. `System-Record' comes
    from the FD, so it is deliberately NOT also declared in working storage.
    """
    body: list[str] = []
    for key in sorted(SYSTEM_RELATIVE_RECORDS):
        _copybook, record, purpose = SYSTEM_RELATIVE_RECORDS[key]
        body.append(f"*>   relative record {key} -- {record} -- {purpose}")
        body.append(f"     initialize {record}")
        body.extend(records.get(key, []))
        if record != "System-Record":
            # Records 2, 3 and 4 are built in working storage and then copied into the
            # FD record, because the FD declares only the parameter record
            # [copybooks/fdsys.cob:L10-L12] while all four share its 1024 bytes.
            body.append(f"     move     {record} to System-Record")
        body.append(f"     move     {key} to rrn")
        body.append("     perform  fx-write")
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfxsys.",
            "*>",
            "*>  GENERATED by harness/make_fixtures.py. Not committed, not frozen.",
            "*>",
            f'*>  Writes {cobol_path_literal(path, what="the seed file path")} '
            "using the frozen select and FD every loader uses for it.",
            "*>",
            "       environment division.",
            "       configuration section.",
            "       input-output section.",
            "       file-control.",
            ' copy "selsys.cob".',
            "       data division.",
            "       file section.",
            ' copy "fdsys.cob".',
            "       working-storage section.",
            ' copy "wsfnctn.cob".',
            ' copy "wsnames.cob".',
            *(
                f' copy "{SYSTEM_RELATIVE_RECORDS[key][0]}".'
                for key in sorted(SYSTEM_RELATIVE_RECORDS)
                if SYSTEM_RELATIVE_RECORDS[key][1] != "System-Record"
            ),
            " 01  WS-Fixture-Seq        pic 9(4) value zero.",
            " 01  WS-Fixture-Written    pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     open     output system-file.",
            "     if       fs-reply not = zero",
            '              display "acasfxsys: open output failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            *body,
            "     close    system-file.",
            "     if       fs-reply not = zero",
            '              display "acasfxsys: close failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            '     display  "acasfxsys: wrote " WS-Fixture-Written " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "*>",
            " fx-write.",
            "     move     rrn to WS-Fixture-Seq.",
            "     write    System-Record invalid key",
            '              display "acasfxsys: write failed at rrn " WS-Fixture-Seq',
            "                      \" fs-reply = \" fs-reply",
            "              move 69 to return-code",
            "              stop run",
            "     end-write.",
            "     add      1 to WS-Fixture-Written.",
            "",
        ]
    )


def reader_via_handler(
    *,
    handler: str,
    record: str,
    defs_field: str,
    linkage: list[str],
    path: str,
    single: bool = False,
) -> str:
    """A reader that proves the file loads through the SAME frozen handler.

    This is the read-back check, and it is the only assurance that matters: a file the
    handler cannot open and walk is not a fixture, whatever it looks like on disk. The
    count it prints is compared with the count the writer reported.

    `single' SUPPRESSES THE LOOP, and it is not an optimisation -- it is required for
    correctness on two of the seventeen handlers. acasirsub3 and acasirsub5 are
    SINGLE-RECORD handlers: their own comments say IRS "only does a read or write and
    not a direct open or close" [common/acasirsub3.cbl:L168-L178], their EVALUATE turns
    function 1 and function 2 into no-ops returning zero
    [common/acasirsub3.cbl:L199-L208], and the read path OPENS, reads one record and
    CLOSES on every single call, logging itself as "Open Dflt, Read, Close on 1"
    [common/acasirsub3.cbl:L259-L310]. It therefore NEVER REPORTS EOF, and a
    read-until-ten loop against it spins forever -- which is exactly how this was
    found, as a silent twelve-minute hang with no output at all.
    """
    loop = (
        [
            "     set      fn-read-next to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfxrd: single read failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "     add      1 to WS-Fixture-Read.",
        ]
        if single
        else [
            " fx-010-loop.",
            "     set      fn-read-next to true.",
            "     perform  fx-call.",
            "     if       fs-reply = 10",
            "              go to fx-020-end",
            "     end-if.",
            "     if       fs-reply not = zero",
            '              display "acasfxrd: read next failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            "     add      1 to WS-Fixture-Read.",
            "     go       to fx-010-loop.",
        ]
    )
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfxrd.",
            "*>  GENERATED by harness/make_fixtures.py. Read-back proof only.",
            "       environment division.",
            "       configuration section.",
            "       data division.",
            "       working-storage section.",
            *(f" {statement}" for statement in linkage),
            " 01  WS-Fixture-Read       pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            "     move     zero to File-System-Used",
            "                      FA-File-System-Used.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     set      fn-open to true.",
            "     set      fn-input to true.",
            "     perform  fx-call.",
            "     if       fs-reply not = zero",
            '              display "acasfxrd: open input failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            *loop,
            " fx-020-end.",
            "     set      fn-close to true.",
            "     perform  fx-call.",
            '     display  "acasfxrd: read " WS-Fixture-Read " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "*>",
            " fx-call.",
            f'     call     "{handler}" using System-Record',
            f"                              {record}",
            "                              File-Access",
            "                              File-Defs",
            "                              ACAS-DAL-Common-data.",
            "",
        ]
    )


def reader_for_system(*, defs_field: str, path: str) -> str:
    """The read-back proof for `system.dat', through its frozen select and FD."""
    return "\n".join(
        [
            "       identification division.",
            "       program-id.     acasfxsysrd.",
            "*>  GENERATED by harness/make_fixtures.py. Read-back proof only.",
            "       environment division.",
            "       configuration section.",
            "       input-output section.",
            "       file-control.",
            ' copy "selsys.cob".',
            "       data division.",
            "       file section.",
            ' copy "fdsys.cob".',
            "       working-storage section.",
            ' copy "wsfnctn.cob".',
            ' copy "wsnames.cob".',
            " 01  WS-Fixture-Read       pic 9(4) value zero.",
            "*>",
            "       procedure division.",
            " fx-main section.",
            " fx-000-start.",
            f'     move     "{cobol_path_literal(path, what="the seed file path")}"'
            f" to {defs_field}.",
            "     open     input system-file.",
            "     if       fs-reply not = zero",
            '              display "acasfxsysrd: open input failed, fs-reply = " fs-reply',
            "              move 69 to return-code",
            "              stop run",
            "     end-if.",
            # EACH SLOT IS READ BY NUMBER, not walked. A sequential walk would report
            # a count without proving WHICH relative records exist, and the whole
            # point of this file is that four specific slots must be readable because
            # four different loaders each go straight to one of them.
            *(
                line
                for key in sorted(SYSTEM_RELATIVE_RECORDS)
                for line in (
                    f"     move     {key} to rrn.",
                    "     read     system-file invalid key",
                    f'              display "acasfxsysrd: relative record {key} '
                    f'({SYSTEM_RELATIVE_RECORDS[key][2]}) is missing"',
                    "              move 69 to return-code",
                    "              stop run",
                    "     end-read.",
                    "     add      1 to WS-Fixture-Read.",
                )
            ),
            " fx-020-end.",
            "     close    system-file.",
            '     display  "acasfxsysrd: read " WS-Fixture-Read " record(s)".',
            "     move     zero to return-code.",
            "     stop     run.",
            "",
        ]
    )


# =============================================================================
# BUILDING
# =============================================================================
def run(
    argv: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 600
) -> subprocess.CompletedProcess[str]:
    """Run one bounded external command and return it, output captured.

    stdin is DEVNULL on purpose. Several frozen handlers reach an `accept' on an error
    path -- [common/acasirsub3.cbl:L400] is one -- and a fixture build must fail rather
    than wait for a keypress that will never come.
    """
    return subprocess.run(  # noqa: S603 - argv is built here, never from a string
        argv,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def compile_and_run(
    *,
    label: str,
    source: str,
    work: Path,
    repo: Path,
    env: dict[str, str],
    modules: Path | None,
) -> str:
    """Compile one generated program with cobc, run it, and return its output."""
    stem = f"acasfx_{label}"
    program = work / f"{stem}.cbl"
    program.write_text(source, encoding="utf-8")
    binary = work / stem
    argv = [
        "cobc",
        "-x",
        "-free",
        "-o",
        str(binary),
        f"-I{repo / 'copybooks'}",
        "-fmissing-statement=ok",
        str(program),
    ]
    compiled = run(argv, cwd=work, env=env)
    if compiled.returncode != 0:
        fail(
            EX_COMPILE,
            f"cobc rejected the generated program for {label} (status {compiled.returncode}).",
            f"source: {program}",
            *(compiled.stderr or compiled.stdout or "").splitlines()[:20],
        )
    child = dict(env)
    if modules is not None:
        existing = child.get("COB_LIBRARY_PATH", "")
        child["COB_LIBRARY_PATH"] = (
            f"{modules}:{existing}" if existing else str(modules)
        )
    # A GENERATED PROGRAM GETS A SHORT LEASH, DELIBERATELY. It writes or reads a
    # handful of records and nothing else, so anything past a minute is a hang and not
    # slow progress -- and a hang here is the worst failure this tool can have, because
    # it produces no output at all to diagnose from. The read-back of the IRS defaults
    # was exactly that until the single-record property of acasirsub3 was found; this
    # bound is what turns the next such surprise into a report instead of a stall.
    try:
        executed = run([str(binary)], cwd=work, env=child, timeout=60)
    except subprocess.TimeoutExpired:
        fail(
            EX_RUNTIME,
            f"the generated program for {label} did not finish within 60 seconds.",
            "It writes or reads only a few records, so this is a hang rather than slow",
            "progress. The likeliest causes, both properties of the frozen handler:",
            "  - the handler never reports EOF, so the read-back loop cannot end. Two",
            "    of the seventeen behave this way and are marked single_record above.",
            "  - the handler reached an interactive `accept' on an error path. stdin is",
            "    /dev/null here, so it cannot be satisfied and must not be waited on.",
            f"source: {program}",
        )
    if executed.returncode != 0:
        fail(
            EX_RUNTIME,
            f"the generated program for {label} failed (status {executed.returncode}).",
            *(executed.stdout or "").splitlines()[:12],
            *(executed.stderr or "").splitlines()[:12],
        )
    return executed.stdout


def system_blocks(document: dict) -> dict[str, dict]:
    """The four relative records a scenario declares for `system.dat'.

    The declaration is a mapping keyed by RELATIVE RECORD NUMBER, quoted, mirroring the
    frozen dispatch that moves File-Key-No straight into rrn
    [common/acas000.cbl:L461]. All four keys are REQUIRED -- see the comment on
    SYSTEM_RELATIVE_RECORDS for why a partial declaration aborts the seed rather than
    degrading -- and a slot with nothing to pin is declared as an empty mapping, which
    writes an INITIALIZEd record. Empty is a statement about the pre-state; ABSENT is a
    slot no loader can read.
    """
    block = document.get("seed_records")
    if not isinstance(block, dict) or "system.dat" not in block:
        fail(
            EX_SCENARIO,
            "the scenario declares no seed_records for system.dat.",
            "All four system loaders read it, unconditionally and first",
            "[common/masterLD.sh:L50-L88], and it carries the run date, the fan-out",
            "switch and the database account, so it cannot be defaulted.",
        )
    declared = block["system.dat"]
    if not isinstance(declared, dict):
        fail(
            EX_SCENARIO,
            "seed_records[system.dat] must be a mapping keyed by relative record "
            "number, because that one file holds FOUR different records.",
            "The four keys and what each becomes:",
            *(
                f'  "{key}": {SYSTEM_RELATIVE_RECORDS[key][1]:16} -> '
                f"{SYSTEM_RELATIVE_RECORDS[key][2]}"
                for key in sorted(SYSTEM_RELATIVE_RECORDS)
            ),
            "A slot with nothing to pin is declared as {} and is written INITIALIZEd.",
        )
    unknown = sorted(set(map(str, declared)) - set(SYSTEM_RELATIVE_RECORDS))
    if unknown:
        fail(
            EX_SCENARIO,
            f"seed_records[system.dat] declares relative record(s) {unknown}, and the "
            "frozen loaders read only 1, 2, 3 and 4.",
            "acas000 rejects a key outside that range itself",
            "[common/acas000.cbl:L335].",
        )
    resolved: dict[str, dict] = {}
    for key in sorted(SYSTEM_RELATIVE_RECORDS):
        if key not in {str(k) for k in declared}:
            _copybook, record, purpose = SYSTEM_RELATIVE_RECORDS[key]
            fail(
                EX_SCENARIO,
                f'seed_records[system.dat] does not declare relative record "{key}" '
                f"({record}, {purpose}).",
                "All four are required. masterLD runs all four loaders",
                "unconditionally, and the last is tested against zero rather than 63",
                "[common/masterLD.sh:L83-L86], so an unwritten slot ABORTS the seed.",
                'Declare it as {} if there is nothing to pin in it.',
            )
        value = next(v for k, v in declared.items() if str(k) == key)
        if value is None:
            value = {}
        if isinstance(value, list):
            if len(value) > 1:
                fail(
                    EX_SCENARIO,
                    f'seed_records[system.dat]["{key}"] holds {len(value)} records and '
                    "a relative slot holds exactly one.",
                )
            value = value[0] if value else {}
        if not isinstance(value, dict):
            fail(
                EX_SCENARIO,
                f'seed_records[system.dat]["{key}"] must be a mapping of field names '
                "to quoted values, or {} for an INITIALIZEd record.",
            )
        resolved[key] = value
    return resolved


def declared_records(document: dict, name: str) -> list[dict[str, str]]:
    """The records a scenario declares for one file, or an empty list."""
    block = document.get("seed_records")
    if block is None:
        return []
    if not isinstance(block, dict):
        fail(
            EX_SCENARIO,
            "seed_records must be a mapping of file name to a list of records.",
        )
    records = block.get(name, [])
    if records is None:
        records = []
    if not isinstance(records, list):
        fail(EX_SCENARIO, f"seed_records[{name}] must be a list of records.")
    for entry in records:
        if not isinstance(entry, dict):
            fail(
                EX_SCENARIO,
                f"every record in seed_records[{name}] must be a mapping of field to value.",
            )
    return records


def credentials_from_env() -> dict[str, str]:
    """Validate all six connection fields and return the ENVIRONMENT NAME of each.

    ⭐ THE VALUES ARE VALIDATED HERE AND EMITTED NOWHERE (finding F-31). This used to
    return the values, which `moves_for` then wrote into the generated COBOL as
    `move "PaSsWoRd" to RDBMS-Passwd' - so a build kept for diagnosis, or a compiler
    diagnostic echoing the offending line, published the database account. The
    generated writer now performs `accept RDBMS-Passwd from environment
    "ACAS_DB_PASSWORD"' instead, which reaches the same field with the same bytes at
    RUN time and leaves nothing in the source.

    The width and presence checks stay HERE rather than moving into the generated
    program, because a refusal a human can read beats a truncation a COBOL move
    performs silently - and `pic x(12)` is what the frozen loader passes on
    [copybooks/wssystem.cob:L137-L144].

    Returns:
        The field name mapped to the ENVIRONMENT VARIABLE NAME it is accepted from -
        never to its value.
    """
    values: dict[str, str] = {}
    for field, environment, width, required in CONNECTION_FIELD_BINDINGS:
        raw_value = os.environ.get(environment) or ""
        value = raw_value if field == "RDBMS-Passwd" else raw_value.strip()
        if required and not value:
            fail(
                EX_PRECONDITION,
                f"{field} has no value: {environment} does not supply it.",
                "The system record carries all six connection parameters used by",
                "the frozen loaders [copybooks/wssystem.cob:L137-L144], and they",
                "come from the environment so no deployment value is committed.",
            )
        if len(value) > width:
            fail(
                EX_PRECONDITION,
                f"{field} is {len(value)} characters long; the field is pic x({width}).",
                "A longer value is silently truncated before the frozen loader",
                "connects [copybooks/wssystem.cob:L137-L144].",
            )
        values[field] = environment
    return values


def build_one(
    *,
    name: str,
    document: dict,
    out: Path,
    work: Path,
    repo: Path,
    env: dict[str, str],
    modules: Path | None,
    verbose: bool,
) -> int:
    """Build one declared flat file and prove it reads back. Returns the row count."""
    spec = SEED_FILES[name]
    handler = spec["handler"]
    defs_field = spec["defs"]
    assert isinstance(defs_field, str)
    target = out / name
    # system.dat is declared by RELATIVE RECORD NUMBER rather than as a list, because
    # that one file holds four different records -- see SYSTEM_RELATIVE_RECORDS -- so
    # its own reader validates the shape and the generic list reader is not used.
    records = [] if name == "system.dat" else declared_records(document, name)

    if name == "system.dat":
        #  Validated here, emitted nowhere: the return value is the map of field to
        #  ENVIRONMENT VARIABLE NAME, and the check that each is present and fits its
        #  `pic x(n)` happens on this call (finding F-31).
        forced = credentials_from_env()
        declared_blocks = system_blocks(document)
        rendered: dict[str, list[str]] = {}
        for key in sorted(SYSTEM_RELATIVE_RECORDS):
            copybook, record, purpose = SYSTEM_RELATIVE_RECORDS[key]
            layout = read_layout(repo, [copybook], {}, record=record)
            fields = dict(declared_blocks[key])
            if key == "1":
                for reserved in CREDENTIAL_FIELDS:
                    if any(k.lower() == reserved.lower() for k in fields):
                        fail(
                            EX_SCENARIO,
                            f"the scenario declares {reserved}, which is refused.",
                            "The six connection fields are filled from the environment",
                            "so no credential or deployment endpoint is committed to",
                            "the repository.",
                        )
            elif any(k.lower() in {f.lower() for f in CREDENTIAL_FIELDS} for k in fields):
                fail(
                    EX_SCENARIO,
                    f"relative record {key} declares a credential field, which is "
                    "refused. Only the parameter record carries the database account.",
                )
            rendered[key] = moves_for(
                layout,
                record,
                fields,
                where=f"seed_records[system.dat][{key}] ({purpose})",
            )
            if key == "1":
                #  APPENDED AFTER THE DECLARED MOVES, so an `initialize' followed by
                #  the scenario's own fields is followed by the environment's six -
                #  the same order the old literal MOVEs occupied, with no value in
                #  the source (finding F-31). `forced` holds the VARIABLE NAMES and
                #  has already refused an absent or over-wide value.
                rendered[key].extend(
                    connection_accepts_for(layout, record, forced)
                )
        records = [fields for fields in declared_blocks.values() if fields]
        source = writer_for_system(
            defs_field=defs_field, path=str(target), records=rendered
        )
        wrote = compile_and_run(
            label="system_w",
            source=source,
            work=work,
            repo=repo,
            env=env,
            modules=None,
        )
        read = compile_and_run(
            label="system_r",
            source=reader_for_system(defs_field=defs_field, path=str(target)),
            work=work,
            repo=repo,
            env=env,
            modules=None,
        )
    else:
        assert isinstance(handler, str)
        linkage = handler_linkage_copies(repo, handler)
        record_copy = linkage[0]
        record_name = record_name_of(repo, handler)
        override = spec.get("layout")
        if override:
            # The substitution has to reach the GENERATED SOURCE too, not just the
            # field classification: the driver's data division is built from these copy
            # statements, so a name classified from one copybook and declared from
            # another would not compile. Replacing the record copybook -- the first
            # statement -- and leaving the other four exactly as the handler writes
            # them is what keeps the driver and the handler agreeing about everything
            # else. No REPLACING is needed because the substituted copybook already
            # names the record as the handler's USING clause names it, and
            # read_layout's record check is what proves that.
            linkage = [f'copy "{override}".'] + linkage[1:]
            record_copy = linkage[0]
        layout = read_layout(
            repo,
            [copybook_of(record_copy)],
            replacements_of(record_copy),
            record=record_name,
        )
        single = bool(spec.get("single_record"))
        if single and len(records) > 1:
            fail(
                EX_SCENARIO,
                f"{name} declares {len(records)} records and {handler} holds exactly "
                "one.",
                "That handler re-opens the file for OUTPUT on every write",
                f"[common/{handler}.cbl], so a second record would silently REPLACE",
                "the first and the fixture would not be what the scenario says it is.",
                "Declare a single record.",
            )
        rendered = [
            moves_for(
                layout,
                record_name,
                fields,
                where=f"seed_records[{name}][{index}]",
            )
            for index, fields in enumerate(records, start=1)
        ]
        source = writer_via_handler(
            handler=handler,
            record=record_name,
            defs_field=defs_field,
            linkage=linkage,
            path=str(target),
            records=rendered,
        )
        wrote = compile_and_run(
            label=f"{handler}_w",
            source=source,
            work=work,
            repo=repo,
            env=env,
            modules=modules,
        )
        read = compile_and_run(
            label=f"{handler}_r",
            source=reader_via_handler(
                handler=handler,
                record=record_name,
                defs_field=defs_field,
                linkage=linkage,
                path=str(target),
                single=single,
            ),
            work=work,
            repo=repo,
            env=env,
            modules=modules,
        )

    written = count_in(wrote)
    reread = count_in(read)
    if not target.exists():
        fail(
            EX_RUNTIME,
            f"{name} was reported written but is not on disk at {target}.",
        )
    if written != reread:
        fail(
            EX_RUNTIME,
            f"{name} was written with {written} record(s) but reads back as {reread}.",
            "A fixture that does not read back through the frozen handler is not a",
            "fixture, whatever it looks like on disk.",
        )
    if verbose:
        sys.stdout.write(
            f"    {name:<18} {written:>4} record(s)  read back {reread:>4}  "
            f"{target.stat().st_size:>9} bytes\n"
        )
    return written


def record_name_of(repo: Path, handler: str) -> str:
    """The record name a handler's PROCEDURE DIVISION USING list puts second.

    Read from the frozen source rather than tabulated here, for the same reason the
    linkage block is: a name this generator held its own copy of could drift.
    """
    text = (repo / "common" / f"{handler}.cbl").read_text(
        encoding="utf-8", errors="replace"
    )
    match = re.search(r"procedure\s+division\s+using(.*?)\.", text, re.IGNORECASE | re.DOTALL)
    if match is None:
        fail(
            EX_PRECONDITION,
            f"{handler} has no PROCEDURE DIVISION USING list, so its record name "
            f"cannot be read.",
        )
    words = [w for w in re.split(r"\s+", match.group(1).strip()) if w]
    if len(words) < 2:
        fail(EX_PRECONDITION, f"{handler}'s USING list is shorter than expected.")
    return words[1]


def count_in(output: str) -> int:
    """The record count a generated program reported."""
    match = re.search(r"(?:wrote|read)\s+(\d+)\s+record", output)
    if match is None:
        fail(
            EX_RUNTIME,
            "a generated program did not report a record count.",
            *output.splitlines()[:10],
        )
    return int(match.group(1))


def report_fields(repo: Path, name: str) -> None:
    """Print the settable fields of one seed file's record.

    Read from the SAME frozen definitions the writer is generated from -- the
    handler's own LINKAGE copy block, with the handler's own REPLACING clauses applied
    -- so what this prints and what a build will accept cannot disagree.
    """
    spec = SEED_FILES[name]
    handler = spec["handler"]
    if handler is None:
        copybooks, replacements, record = ["fdsys.cob"], {}, "System-Record"
        origin = "[copybooks/fdsys.cob], opened directly by the loaders"
    else:
        statements = handler_linkage_copies(repo, handler)
        copybooks = [copybook_of(statement) for statement in statements]
        replacements = {}
        for statement in statements:
            replacements.update(replacements_of(statement))
        record = record_name_of(repo, handler)
        origin = f"[common/{handler}.cbl] LINKAGE SECTION: " + ", ".join(copybooks)
        override = spec.get("layout")
        if override:
            copybooks, replacements = [str(override)], {}
            origin = (
                f"[copybooks/{override}], the view the POSTING PROGRAM reads through; "
                f"see the SEED_FILES note for {name}"
            )
    layout = read_layout(repo, copybooks[:1], replacements, record=record)
    sys.stdout.write(f"\n{name} -> {record}\n  from {origin}\n")
    if replacements:
        pairs = ", ".join(f"{a} -> {b}" for a, b in sorted(replacements.items()))
        sys.stdout.write(f"  REPLACING {pairs}\n")
    for kind, table in (("numeric", layout.numeric), ("text", layout.alphanumeric)):
        for key in sorted(table):
            declared = table[key]
            width = layout.display_width.get(key)
            shape = f"DISPLAY({width})" if width else "COMP/COMP-3/binary"
            note = ""
            if key in layout.subscripted:
                owner, bound = layout.subscripted[key]
                note = f"   <- needs at: 1..{bound} in {owner}"
            sys.stdout.write(f"    {kind:8} {shape:18} {declared}{note}\n")
    for key in sorted(layout.excluded):
        sys.stdout.write(f"    -        NOT SETTABLE       {key}: {layout.excluded[key]}\n")


#: The marker a `--work` directory must carry when it is not the default
#: `<out>/.build` (finding F-28). Written by this tool for a directory that is empty,
#: and required thereafter, so a work root cannot be a path that happens to exist.
WORK_ROOT_MARKER: Final[str] = ".acas-harness-work-root"


def assert_work_directory(
    work: Path, *, repo: Path, out: Path, explicit: bool
) -> None:
    """Refuse a work directory that could overwrite something that matters.

    ⭐ WHY THIS EXISTS (finding F-28). `--work` was accepted unchecked, and this tool
    WRITES GENERATED COBOL into it and compiles there. Pointed at the checkout it
    would create programs inside frozen specification directories; pointed at a
    populated directory it would litter, and `harness/build_fixtures.sh` removes the
    default one recursively. Two directions of containment are checked, because both
    are wrong: the work directory must not be inside the checkout, AND the checkout
    must not be inside the work directory.

    THE DEFAULT IS EXEMPT FROM THE MARKER, NOT FROM THE CONTAINMENT. `<out>/.build`
    is created by this tool underneath a directory `build_fixtures.sh` has already
    claimed, so requiring a second marker there would be ceremony; an explicitly
    named root has no such provenance and must carry one.

    Args:
        work: The resolved work directory, already created.
        repo: The frozen checkout.
        out: The resolved output directory.
        explicit: True when `--work` named it, False for the default.

    Raises:
        SystemExit: Through `fail`, with `EX_PRECONDITION`.
    """
    resolved = work.resolve()

    if resolved == repo or str(resolved).startswith(f"{repo}{os.sep}"):
        fail(
            EX_PRECONDITION,
            f"the work directory {resolved} is inside the frozen checkout {repo}.",
            "This tool writes generated COBOL there and compiles it; the checkout is",
            "read-only specification and nothing here may write to it (R-3).",
        )
    if str(repo).startswith(f"{resolved}{os.sep}"):
        fail(
            EX_PRECONDITION,
            f"the frozen checkout {repo} is inside the work directory {resolved}.",
            "A work root above the checkout puts the specification inside a directory",
            "this tool and harness/build_fixtures.sh treat as disposable.",
        )
    if resolved == Path(resolved.anchor) or len(resolved.parts) <= 2:
        fail(
            EX_PRECONDITION,
            f"refusing {resolved} as a work directory: it is a filesystem or",
            "top-level directory. Name a directory created for the purpose.",
        )
    home = Path.home()
    if resolved == home:
        fail(
            EX_PRECONDITION,
            f"refusing the home directory {resolved} as a work directory.",
        )

    if not explicit:
        #  The default `<out>/.build`, underneath a root build_fixtures.sh claimed.
        return

    if resolved == out or str(resolved).startswith(f"{out}{os.sep}"):
        #  Inside the fixture root this run is publishing into: same provenance as
        #  the default, so the marker is not demanded.
        return

    marker = resolved / WORK_ROOT_MARKER
    if marker.is_file():
        return

    existing = [entry for entry in resolved.iterdir()]
    if existing:
        fail(
            EX_PRECONDITION,
            f"refusing {resolved} as a work directory: it holds content this tool",
            "did not create and carries no harness marker.",
            f"  first entry found: {existing[0]}",
            f"  expected marker  : {marker}",
            "Generated programs are written and compiled here, so a directory whose",
            "provenance cannot be established is not used. Point --work at an empty",
            "directory, or create the marker deliberately.",
        )
    try:
        marker.write_text(
            "# harness/make_fixtures.py work root.\n"
            "# Generated COBOL is written and compiled here; delete this file to\n"
            "# revoke that.\n",
            encoding="utf-8",
        )
        marker.chmod(0o600)
    except OSError as exc:
        fail(
            EX_PRECONDITION,
            f"could not claim the work directory by writing {marker}: {exc}",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="make_fixtures.py",
        description=(
            "Build the flat seed files a scenario declares, from the records it "
            "declares, using the frozen handlers and copybooks."
        ),
        epilog=(
            "The records live in the scenario file under seed_records, as text, so "
            "that no money figure is ever parsed by YAML into a binary float. The "
            "six RDBMS connection fields of the system record are filled from the "
            "environment and refused in the scenario file."
        ),
    )
    parser.add_argument("scenario", help="path of the scenario YAML")
    parser.add_argument(
        "--list-fields",
        metavar="SEED-FILE",
        default=None,
        help="do not build anything; report the settable fields of one seed file's "
        "record, spelled exactly as the frozen copybook spells them, with the "
        "handler and copybook they were read from. Pass ALL for every declared "
        "file. This exists so that a scenario's seed_records are transcribed from "
        "the frozen definitions BY THIS TOOL rather than by eye.",
    )
    parser.add_argument(
        "--out",
        required=False,
        help="directory the flat files are written into. Created if absent, and "
        "CLEARED of any file this builder would write, so a stale fixture from an "
        "earlier build cannot be seeded by mistake.",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("ACAS_REPO", "/repo"),
        help="the frozen checkout (default $ACAS_REPO, or /repo)",
    )
    parser.add_argument(
        "--modules",
        default=os.environ.get("ACAS_BUILD", "/build"),
        help="the build tree whose common/ holds the compiled handlers "
        "(default $ACAS_BUILD, or /build)",
    )
    parser.add_argument(
        "--work",
        default=None,
        help="where the generated programs are compiled (default <out>/.build). A "
        "directory OUTSIDE the checkout, with the checkout not inside it, and - "
        "unless it is under --out - either empty or carrying the "
        f"{WORK_ROOT_MARKER} marker this tool writes for an empty one.",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="report only failures"
    )
    args = parser.parse_args(argv)

    # The same discipline the five shell scripts of this harness set for themselves.
    # It has to be set before any directory or file is created, and it propagates to
    # the compiler and to the generated writer programs, which are the processes that
    # actually create the flat files.
    os.umask(0o077)

    scenario = Path(args.scenario)
    if not scenario.is_file():
        fail(EX_SCENARIO, f"the scenario file does not exist: {scenario}")
    try:
        document = yaml.safe_load(scenario.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(EX_SCENARIO, f"{scenario} could not be parsed: {exc}")
    if not isinstance(document, dict):
        fail(EX_SCENARIO, f"{scenario} does not hold a YAML mapping at the top level.")

    declared = document.get("seed_files") or document.get("seed-files")
    if not isinstance(declared, list) or not declared:
        fail(
            EX_SCENARIO,
            f"{scenario} declares no seed_files, so there is nothing to build.",
        )
    unknown = [n for n in declared if n not in SEED_FILES]
    if unknown:
        fail(
            EX_SCENARIO,
            f"the scenario declares seed file(s) this builder does not know: {unknown}",
            "The known set is exactly the files the twenty in-scope loaders read:",
            ", ".join(sorted(SEED_FILES)),
        )

    repo = Path(args.repo).resolve()
    if not (repo / "copybooks").is_dir():
        fail(EX_PRECONDITION, f"{repo} does not look like the checkout: no copybooks/")

    if args.list_fields is not None:
        wanted = (
            list(declared)
            if args.list_fields.upper() == "ALL"
            else [args.list_fields]
        )
        for name in wanted:
            if name not in SEED_FILES:
                fail(EX_USAGE, f"{name} is not one of the seed files this tool knows.")
            report_fields(repo, name)
        return EX_OK

    if args.out is None:
        parser.error("--out is required unless --list-fields is given")
    out = Path(args.out)
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fail(EX_PRECONDITION, f"the output directory could not be created: {exc}")
    resolved_out = out.resolve()
    if resolved_out == repo or str(resolved_out).startswith(f"{repo}{os.sep}"):
        fail(
            EX_PRECONDITION,
            f"the output directory {resolved_out} is inside the frozen checkout.",
            "The checkout is read-only specification and nothing here may write to it.",
        )

    # ⭐ CHECKED HERE AS WELL AS AT EVERY INTERPOLATION SITE, and the difference is
    # which failure the operator gets. Each seed file's path is derived from this
    # directory and lands in a COBOL literal in source this tool compiles and runs, so
    # `cobol_path_literal' refuses a quote, a control character or an over-long path
    # at each site. That refusal names a generated line; this one names `--out', which
    # is what the operator actually typed. The longest file name adds to the length,
    # so the budget is measured against the worst case rather than the directory.
    longest = max(len(name) for name in SEED_FILES)
    cobol_path_literal(
        f"{resolved_out}{os.sep}{'x' * longest}",
        what="the --out directory, plus the longest seed file name it will hold,",
    )

    if shutil.which("cobc") is None:
        fail(
            EX_PRECONDITION,
            "cobc is not on the PATH.",
            "Fifteen of the seventeen seed files are ORGANIZATION INDEXED or RELATIVE,",
            "so GnuCOBOL itself has to write them. Run this inside the harness image.",
        )

    work = Path(args.work) if args.work else resolved_out / ".build"
    try:
        work.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fail(EX_PRECONDITION, f"the work directory could not be created: {exc}")
    assert_work_directory(work, repo=repo, out=resolved_out, explicit=bool(args.work))

    modules_dir: Path | None = None
    candidate = Path(args.modules) / "common"
    if candidate.is_dir():
        modules_dir = candidate

    env = dict(os.environ)
    env.setdefault("COB_EXIT_WAIT", "off")
    # An indexed file GnuCOBOL creates alongside a stale one of a different shape is a
    # confusing failure, so anything this build would write is removed first.
    for name in declared:
        for stale in resolved_out.glob(f"{name}*"):
            if stale.is_file():
                stale.unlink()

    if not args.quiet:
        sys.stdout.write(
            f"make_fixtures.py: building {len(declared)} file(s) for "
            f"{document.get('name', scenario.stem)} into {resolved_out}\n"
        )
    total = 0
    for name in declared:
        total += build_one(
            name=name,
            document=document,
            out=resolved_out,
            work=work,
            repo=repo,
            env=env,
            modules=modules_dir,
            verbose=not args.quiet,
        )
    if not args.quiet:
        sys.stdout.write(
            f"make_fixtures.py: built {len(declared)} file(s), {total} record(s) in "
            f"total, every one read back through the frozen definitions\n"
        )
    return EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
