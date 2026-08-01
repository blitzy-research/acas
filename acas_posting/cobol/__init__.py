"""COBOL language semantics. No business logic lives here.

Everything COBOL provides for free - picture-clause arithmetic, packed-decimal
storage, `MOVE` truncation, condition-name evaluation and `SORT` key ordering -
is factored into this package so that business behaviour lives in exactly one
place per program and the semantics can be tested in isolation, with no
database and no scenario setup.

Modules, in layer order
    picture             parses a PIC clause into a field descriptor
    field               the `FieldDescriptor` value object: digits, scale,
                        sign, usage and sign position
    usage               the six storage classes - DISPLAY, COMP, COMP-3,
                        DISPLAY with SIGN LEADING, and the BINARY-CHAR /
                        BINARY-SHORT / BINARY-LONG family
    arithmetic          ADD, SUBTRACT, MULTIPLY, DIVIDE and COMPUTE
    move                MOVE truncation, padding and justification
    condition_names     the `88`-level predicates
    sortverb            SORT with COBOL key semantics and stability

That order is the layer order and must not be alphabetised: a picture clause
yields a field descriptor, which carries a usage, which the arithmetic and
`MOVE` rules store through, after which come the condition-name predicates and
the `SORT` ordering.

The two rules that decide most of the arithmetic
    * Truncation is the default. A COBOL store truncates toward zero unless
      `ROUNDED` is written, so `quantize(..., ROUND_DOWN)` is the ordinary
      path.
    * Rounding is the annotated exception. The whole in-scope cycle contains
      exactly five `ROUNDED` sites - [general/gl080.cbl:L328],
      [general/gl051.cbl:L791], [general/gl051.cbl:L796],
      [irs/irs030.cbl:L1551] and [irs/irs030.cbl:L1562] - and each rounds half
      away from zero. Getting this backwards would corrupt essentially every
      posted figure.

Exact numerics only: `decimal.Decimal` for monetary and quantity values, `int`
for the binary family, and no binary floating point anywhere (rule R-2). The
integer truncation of the binary family is load-bearing, not incidental - it is
what makes the moving-average defect reproducible.

Sort stability is a correctness requirement, not a nicety: gl072 locates the
nominal-ledger account for a posting with a sequential read rather than an
indexed one, so it finds the right account only because the upstream sort
emitted the stream in nominal-key order. A perturbed order misposts silently.

Field metadata is data-driven. Descriptors are built from the generated data
dictionary rather than hand-coded per field, which is the only tractable way to
get several hundred fields right.

A module here may import `acas_posting.dictionary.loader` and the standard
library. It may not import `records`, `dal` or `programs`, and it never
executes, embeds or shells out to COBOL (rule R-1).

This marker declares the submodule inventory as data and imports none of it.
"""

# The submodule inventory as data, in layer order. A plain
# `import acas_posting.cobol` binds none of them, which is what keeps the
# package cheap and I/O-free to import. A tuple, so the inventory cannot be
# reordered or mutated in place.
# THE ORDER MUST NOT BE ALPHABETISED: it is the layer order of the semantics
# runtime, and it is the order the plan's transformation table and the module
# docstring above both use. A linter suggesting a sort is to be declined.
__all__: tuple[str, ...] = (
    "picture",
    "field",
    "usage",
    "arithmetic",
    "move",
    "condition_names",
    "sortverb",
)
