#!/usr/bin/env python3
"""Read one ACAS harness scenario definition and emit it as a flat record stream.

WHY THIS FILE EXISTS (finding F-32)
===================================
The parity protocol has two runners -- ``harness/run_cobol_scenario.sh`` drives the
compiled oracle and ``harness/run_python_scenario.sh`` drives the migrated cycle --
and they read ONE scenario definition each time, expecting to receive the same
values from it. They did not read it the same way. The Python side parsed the file
with PyYAML; the oracle side used a bespoke ``awk`` subset that recognised only
unindented ``key:`` lines, treated PyYAML as optional, and continued without it.

That is not a stylistic difference, it is a correctness one: a valid YAML document
could mean two different things to the two sides of a comparison whose entire
purpose is that both sides receive identical inputs. An anchor, a merge key, a
quoted colon, a flow mapping, a block scalar, a duplicated key, a tab-indented
block -- each is read one way by a real parser and another way (or not at all) by a
line matcher. The comparison would still have produced a verdict, and the verdict
would have been meaningless.

So the parser lives HERE, once, and both runners invoke it. There is no second
implementation to drift, and a scenario file cannot be interpreted two ways.

WHAT IT EMITS
=============
A TAB-delimited, newline-terminated stream on stdout, one record per line, in
DOCUMENT ORDER (which is what makes an ordered ``operations:`` list an ordered list
rather than a set):

    K<TAB><key>                 the key is present at top level, whatever its value
    S<TAB><key><TAB><value>     a scalar value
    L<TAB><key><TAB><value>     one item of a flat list, repeated in order
    G<TAB><key>                 the key carries a nested block, recorded NOT read

Keys are normalised by replacing ``-`` with ``_``, so ``run-date`` and ``run_date``
are one key; two spellings of one key are a hard error rather than a silent
last-one-wins. Every record kind is emitted for the same document regardless of
which runner asked, so a key either travels to both sides or to neither.

EXIT STATUS -- the two runners map these onto their own bands
============================================================
    0  the document was read and the stream was emitted
    3  PyYAML is not importable by this interpreter
    4  the file could not be read
    5  the document is not a mapping of scalars, flat lists and blocks

NOTHING IS OPTIONAL. Status 3 is a REFUSAL, not a degradation: a runner that
carried on without the parser would be reading the scenario by some other rule than
the one its counterpart used, which is the defect this file closes.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

try:
    import yaml

    #  ⭐ THE SHARED DUPLICATE-REJECTING LOADER (finding MJ-17). `yaml.safe_load`
    #  applies last-one-wins to a repeated key, silently, and a scenario definition
    #  carries the destructive answers, the fan-out switch that decides which tables a
    #  run touches and the comparison bound - so a shadowed key means two consumers
    #  read two different files.
    import scenario_yaml
except ModuleNotFoundError as exc:
    sys.stderr.write(
        "PyYAML is not importable by this interpreter (%s). It is the one "
        "third-party import the harness tree permits itself besides the "
        "database driver, and the scenario definitions are YAML.\n" % exc
    )
    raise SystemExit(3)

path = pathlib.Path(sys.argv[1])
try:
    text = path.read_text(encoding="utf-8")
except OSError as exc:
    sys.stderr.write("the scenario file could not be read: %s\n" % exc)
    raise SystemExit(4)

try:
    document = scenario_yaml.load_scenario_yaml(text)
except yaml.YAMLError as exc:
    sys.stderr.write("the scenario file is not valid YAML: %s\n" % exc)
    raise SystemExit(5)

if document is None:
    document = {}
if not isinstance(document, dict):
    sys.stderr.write(
        "the scenario file must be a mapping at top level; got %s\n"
        % type(document).__name__
    )
    raise SystemExit(5)


def render(key, value):
    """Render one scalar as text, refusing anything that cannot travel."""
    if value is None:
        text = ""
    elif isinstance(value, bool):
        text = "true" if value else "false"
    elif isinstance(value, int):
        text = str(value)
    elif isinstance(value, str):
        text = value
    elif isinstance(value, float):
        sys.stderr.write(
            "key %r carries a real number, which is refused: no scenario value "
            "is a real number, and rule R-2 forbids binary floating point from "
            "entering the comparison by accident. Quote it if it is text.\n"
            % key
        )
        raise SystemExit(5)
    else:
        sys.stderr.write(
            "key %r carries an unsupported %s value; this stage reads scalars "
            "and flat lists of scalars, and records a nested block without "
            "reading it. A date written unquoted becomes a date object here, so "
            "quote it to keep it text.\n" % (key, type(value).__name__)
        )
        raise SystemExit(5)
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        #  A CONTROL CHARACTER IS FOLDED, NOT REFUSED - and the distinction is the
        #  reader's own protocol rather than a relaxation of it. The stream this
        #  reader emits is TAB-delimited and newline-terminated, so a value
        #  carrying either would forge a record boundary; replacing each control
        #  character with ONE SPACE keeps that property absolutely, because no
        #  emitted byte is a control character afterwards.
        #
        #  It is folded rather than refused because a scenario legitimately
        #  carries a multi-line documentation block: `description: |` in
        #  harness/scenarios/clean_batch_gl.yaml is a YAML literal scalar of
        #  several hundred lines, and no key this runner consumes is documentation.
        #  Refusing it would have made a documented scenario unreadable.
        #
        #  ONLY a value that actually holds a control character is touched, so
        #  every value that travels arrives byte for byte - `irs_instead: ' '`, the
        #  single SPACE that selects General-Ledger-only posting
        #  [copybooks/wssystem.cob:L179-L181], included. Folding whitespace
        #  generally would have emptied it and silently changed the fan-out.
        text = "".join(
            " " if (ord(character) < 32 or ord(character) == 127) else character
            for character in text
        )
    return text


def is_block(value):
    """True for a nested structure: a mapping, a sequence or a set."""
    return isinstance(value, (dict, list, tuple, set, frozenset))


emitted = {}
out = []
blocks = []
for key in document:
    if not isinstance(key, str):
        sys.stderr.write(
            "every top-level key must be text; got a %s\n" % type(key).__name__
        )
        raise SystemExit(5)
    normalised = key.replace("-", "_")
    if normalised in emitted:
        sys.stderr.write(
            "keys %r and %r are the same key: '-' and '_' are "
            "interchangeable, so one of them must go.\n"
            % (emitted[normalised], key)
        )
        raise SystemExit(5)
    emitted[normalised] = key
    out.append("K\t%s" % normalised)
    value = document[key]
    if isinstance(value, (list, tuple)):
        #  A LIST IS EMITTED ONLY WHEN EVERY ITEM IS A SCALAR. A part-read list is
        #  worse than an unread one: the affected-table list BOUNDS the comparison
        #  and the operation list ORDERS the run, so half of either would look like
        #  a complete answer. So a list holding a nested item is recorded whole and
        #  read not at all.
        if any(is_block(item) for item in value):
            out.append("G\t%s" % normalised)
            blocks.append((key, "list whose items are themselves blocks"))
            continue
        for item in value:
            out.append("L\t%s\t%s" % (normalised, render(key, item)))
    elif is_block(value):
        #  A NESTED BLOCK IS RECORDED, NOT READ. A scenario file documents the
        #  state it seeds in `clock:', `system:' and `seed:' blocks, and states the
        #  values this runner reads as top-level scalars beside them; the
        #  oracle-side reader passes over a nested block in exactly the same way,
        #  which is what lets ONE scenario file drive both runners. The caller
        #  refuses a block that appears under a key this runner does read, so this
        #  tolerance cannot turn into a silent mis-read.
        out.append("G\t%s" % normalised)
        blocks.append((key, "%s block" % type(value).__name__))
    else:
        out.append("S\t%s\t%s" % (normalised, render(key, value)))

sys.stdout.write("".join(line + "\n" for line in out))
for key, shape in blocks:
    sys.stderr.write(
        "note: key %r is a %s. It is recorded as present and its members are "
        "not read: this stage reads scalars and flat lists of scalars, and no "
        "key this runner reads is declared as a block.\n" % (key, shape)
    )
