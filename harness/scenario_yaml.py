#!/usr/bin/env python3
"""The ONE scenario-definition parser, shared by every consumer in this project.

⭐ WHY THIS MODULE EXISTS (finding MJ-17 / S-3)
================================================================================
`yaml.safe_load` applies LAST-ONE-WINS to a duplicate mapping key, silently and with
no diagnostic. Eight places in this project parsed a scenario definition that way:
`harness/seed.sh`, `harness/run_parity.sh`, `harness/dump_tables.py`,
`harness/diff_states.py` (twice), `harness/scenario_stream.py` and
`tests/conftest.py`. A scenario definition is not an ordinary configuration file:

  * it carries the DESTRUCTIVE answers - `irs_clear_postings` decides whether
    `PSIRSPOST-REC` is emptied, `gl080_proceed` and `disk_change_option` decide
    whether the end-of-cycle run writes at all;
  * it carries `irs_instead`, the three-state fan-out switch that decides which
    tables a run touches;
  * it carries `affected_tables`, which the runners assert their declared effect
    against;
  * and it carries `expected_status`, which is what makes a term code a PASS rather
    than a behavioural difference.

A shadowed key therefore means one consumer reads the value the file appears to state
and another reads a different one, and an empty diff drawn across that pair is
meaningless. The documentation already claimed duplicates were errors. They were not.

Now every consumer parses through `load_scenario_yaml` and a duplicate key is a hard
parse failure naming the key and its line.

WHY A LOADER SUBCLASS AND NOT A POST-PARSE CHECK. By the time `safe_load` returns, the
duplicate is gone - the surviving value is indistinguishable from a value that was
never shadowed. The rejection has to happen while the mapping is being constructed,
which is where the two key nodes still both exist.

NO BEHAVIOUR OF THE MIGRATED CYCLE DEPENDS ON THIS MODULE. It is harness-side only
(rule R-1: nothing under `acas_posting/` imports it) and it adds no validation of a
scenario's CONTENTS, which rule R-3 forbids - only of the document's well-formedness.

⭐ RESOURCE BUDGETS (finding SEC-07)
================================================================================
`yaml.safe_load` is safe against arbitrary object construction. It is NOT bounded in
what one document may cost to parse: an anchor referenced repeatedly expands
multiplicatively at compose time ("billion laughs"), deep nesting recurses, and a large
document is read whole before anything looks at it. None of that is a code-execution
risk here, and none of it is hypothetical either - the parser runs against files the
harness is pointed at, including ones a caller passes on the command line.

Four budgets are applied, and EVERY LIMIT IS DERIVED FROM THE COMMITTED MAXIMA WITH
WIDE HEADROOM, so no scenario in this repository parses differently than before. The
measured maxima across `harness/scenarios/*.yaml` are 101,222 bytes, depth 7, 1,500
nodes, and - decisively - ZERO anchors and ZERO aliases.

That last measurement is what makes the strongest defence also the cheapest: an alias
is refused outright rather than counted, which removes the multiplicative-expansion
class entirely instead of trying to bound it. A scenario definition is a flat record of
seed rows, inputs and expected statuses; it has never needed to reuse a subtree, and a
definition that suddenly did would be a change worth reading rather than accepting.

These are bounds on the DOCUMENT, not checks on its values - the same well-formedness
footing as the duplicate-key rejection above, and equally not the content validation
R-3 forbids. A budget rejection names the budget and the measured value so the file can
be looked at, and never repairs or truncates anything.
"""

from __future__ import annotations

from typing import Any

import yaml

__all__ = (
    "DuplicateScenarioKeyError",
    "load_scenario_yaml",
    "ScenarioBudgetError",
    "ScenarioYamlLoader",
)

#: Largest document accepted, in bytes of UTF-8. Measured maximum 101,222 (~99 KiB);
#: this is ~40x that, so it bounds the cost without constraining the scenario set.
MAX_DOCUMENT_BYTES = 4 * 1024 * 1024

#: Deepest nesting accepted. Measured maximum 7.
MAX_DEPTH = 32

#: Most nodes accepted in one document. Measured maximum 1,500.
MAX_NODES = 100_000


class ScenarioBudgetError(yaml.YAMLError):
    """A scenario definition exceeds a parse budget, or uses an alias.

    Subclasses `yaml.YAMLError`, so every existing consumer - all of which already
    handle that - reports a budget rejection with no change.
    """


class DuplicateScenarioKeyError(yaml.constructor.ConstructorError):
    """A scenario definition declares the same mapping key twice."""


class ScenarioYamlLoader(yaml.SafeLoader):
    """`yaml.SafeLoader` that refuses a repeated key, an alias, or an over-budget document.

    Safe in the same sense `SafeLoader` is - no arbitrary object construction, no
    `!!python/` tags - and strictly stricter.
    """

    def __init__(self, stream: Any) -> None:
        """Initialise the loader and its budget counters.

        Args:
            stream: Whatever `yaml.load` was given; passed straight through.
        """
        super().__init__(stream)
        self._acas_depth = 0
        self._acas_nodes = 0

    def compose_node(self, parent: Any, index: Any) -> Any:
        """Compose one node, refusing an alias and enforcing the depth and node budgets.

        This is the single hook every node passes through, and it is where an alias is
        still visible as an alias - by the time a document is constructed, an expanded
        alias is indistinguishable from a subtree that was written out in full.

        Args:
            parent: The node being composed into, as PyYAML passes it.
            index: The position within `parent`, as PyYAML passes it.

        Returns:
            The composed node.

        Raises:
            ScenarioBudgetError: The document uses an alias, nests deeper than
                `MAX_DEPTH`, or holds more than `MAX_NODES` nodes.
        """
        if self.check_event(yaml.events.AliasEvent):
            event = self.peek_event()
            raise ScenarioBudgetError(
                f"this scenario definition uses a YAML ALIAS (*{event.anchor}) at "
                f"{event.start_mark}. Aliases are refused rather than bounded: an "
                f"anchor referenced repeatedly expands multiplicatively while the "
                f"document is composed, so a few lines can cost unbounded memory. No "
                f"definition in this repository uses one - a scenario is a flat record "
                f"of seed rows, inputs and expected statuses - so write the value out "
                f"in full instead."
            )

        self._acas_nodes += 1
        if self._acas_nodes > MAX_NODES:
            raise ScenarioBudgetError(
                f"this scenario definition holds more than {MAX_NODES} nodes, which is "
                f"the parse budget. The largest definition in this repository holds "
                f"1,500, so a document this size is not a scenario that grew - check "
                f"the file is the one you meant to pass."
            )

        self._acas_depth += 1
        try:
            if self._acas_depth > MAX_DEPTH:
                raise ScenarioBudgetError(
                    f"this scenario definition nests deeper than {MAX_DEPTH} levels, "
                    f"which is the parse budget. The deepest definition in this "
                    f"repository nests 7 levels, so this is not a scenario that grew - "
                    f"deep nesting is how a small document forces unbounded recursion."
                )
            return super().compose_node(parent, index)
        finally:
            self._acas_depth -= 1

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        """Construct one mapping, refusing a key that has already been seen.

        Args:
            node: The mapping node being constructed.
            deep: Passed through to the base implementation.

        Returns:
            The mapping.

        Raises:
            DuplicateScenarioKeyError: A key appears more than once in this mapping.
        """
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                already = key in seen
            except TypeError:
                # An unhashable key cannot be tracked, and cannot be a scenario key
                # either - every key in every definition is a plain string. Left to
                # the base implementation rather than guessed at.
                continue
            if already:
                raise DuplicateScenarioKeyError(
                    "while constructing a scenario definition",
                    node.start_mark,
                    f"found a DUPLICATE KEY {key!r}. PyYAML's default is "
                    f"last-one-wins, which would let one consumer read the value "
                    f"the file appears to state and another read a different one - "
                    f"and a scenario definition carries the destructive answers, "
                    f"the fan-out switch that decides which tables a run touches, "
                    f"the comparison bound and the expected statuses. Remove one of "
                    f"the two occurrences.",
                    key_node.start_mark,
                )
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


def load_scenario_yaml(text: str) -> Any:
    """Parse one scenario definition's text, refusing a duplicate key or an over-budget document.

    The size budget is checked BEFORE the parser is handed the text, because the point
    of a size budget is not to parse the document first.

    Args:
        text: The definition's contents.

    Returns:
        Whatever the document holds - normally a mapping. The shape is the caller's
        to check, because each consumer already reports it in its own vocabulary.

    Raises:
        yaml.YAMLError: The text is not valid YAML, a mapping repeats a key, or the
            document exceeds a parse budget. `DuplicateScenarioKeyError` and
            `ScenarioBudgetError` are both subclasses, so a caller already handling
            `yaml.YAMLError` reports either without any change.
    """
    size = len(text.encode("utf-8", errors="surrogatepass"))
    if size > MAX_DOCUMENT_BYTES:
        raise ScenarioBudgetError(
            f"this scenario definition is {size} bytes, over the "
            f"{MAX_DOCUMENT_BYTES}-byte parse budget. The largest definition in this "
            f"repository is 101,222 bytes, so nothing legitimate is near this limit - "
            f"check the file is the one you meant to pass. Nothing was parsed: the "
            f"size is checked before the text reaches the parser."
        )
    return yaml.load(text, Loader=ScenarioYamlLoader)
