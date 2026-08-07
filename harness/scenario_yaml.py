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
"""

from __future__ import annotations

from typing import Any

import yaml

__all__ = ("DuplicateScenarioKeyError", "load_scenario_yaml", "ScenarioYamlLoader")


class DuplicateScenarioKeyError(yaml.constructor.ConstructorError):
    """A scenario definition declares the same mapping key twice."""


class ScenarioYamlLoader(yaml.SafeLoader):
    """`yaml.SafeLoader` that refuses a mapping with a repeated key.

    Safe in the same sense `SafeLoader` is - no arbitrary object construction, no
    `!!python/` tags - and strictly stricter.
    """

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
    """Parse one scenario definition's text, refusing a duplicate mapping key.

    Args:
        text: The definition's contents.

    Returns:
        Whatever the document holds - normally a mapping. The shape is the caller's
        to check, because each consumer already reports it in its own vocabulary.

    Raises:
        yaml.YAMLError: The text is not valid YAML, or a mapping repeats a key.
            `DuplicateScenarioKeyError` is a subclass, so a caller already handling
            `yaml.YAMLError` reports the duplicate without any change.
    """
    return yaml.load(text, Loader=ScenarioYamlLoader)
