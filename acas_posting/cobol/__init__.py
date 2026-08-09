"""COBOL language semantics. No business logic lives here.

Everything COBOL gives a program for free - picture-clause arithmetic, the six
numeric storage classes, `MOVE`'s receiving-field rules, 88-level condition names
and `SORT` key ordering - is implemented here so that the program modules read as
accounting logic and nothing else.

    picture         PICTURE and data-description-entry parsing
    field           the `FieldDescriptor` value object
    usage           the six storage classes and their coercions
    arithmetic      ADD, SUBTRACT, MULTIPLY, DIVIDE, COMPUTE and the store rule
    move            `MOVE` truncation, padding and justification
    condition_names the frozen 88-level value sets, as predicates
    sortverb        `SORT` with COBOL key semantics and guaranteed stability

The split is what makes exactness testable: every rule here can be checked
against values captured from the compiled program with no database and no
scenario, so a parity failure localises to this layer or to a program module, not
to both at once. A module here may import `dictionary.loader` and nothing else
from the package.
"""

# The submodule inventory as data, in layer order.
__all__: tuple[str, ...] = (
    "picture",
    "field",
    "usage",
    "arithmetic",
    "move",
    "condition_names",
    "sortverb",
)
