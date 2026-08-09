"""Record layouts for the migrated ACAS posting cycle.

One module per record copybook, each declaring dataclasses whose attributes are
the copybook's `03`/`05` items in declaration order, field for field, with
nothing added and nothing dropped (R-3). Every field's storage metadata -
digits, scale, sign, usage, width - is looked up in the generated data
dictionary rather than transcribed by hand (R-5), so no picture clause is
written twice.

This layer is a leaf: a record module imports only `cobol.field` and
`dictionary.loader`. Converting between the copybook view and the bridge's host
variables belongs to the `dal` handler modules, and nothing here reaches a
database, trims, pads or reshapes a value.

Oddities in the frozen copybooks are preserved rather than corrected - a
misnamed field keeps its name, a disputed record length is recorded rather than
resolved, and a group the bridge flattens is still declared here.
"""

# Provenance. The COBOL system, its bridge programs and its schema are the maintainer's
# work and carry his own notice.

# Deliberately empty: this package publishes no aggregate surface. Import each record
# type from its own module, as the layering contract requires.
__all__: list[str] = []
