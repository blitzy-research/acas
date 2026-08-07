"""The RDBMS connection contract: `acas-get-params` reimplemented natively.

Puts real connection parameters into the six `RDBMS-*` fields of `SYSTEM-REC`
before that record reaches a program module, so the data-access layer connects
to the database the operator provisioned.

This is a reproduction, not an invention. `SYSTEM-REC` is the only carrier by
which a connection parameter reaches the handlers [common/acas008.cbl:L558-L563],
and the frozen tree solves that with a named program of its own,
`common/acas-get-params.cbl`, which every `common/*LD.cbl` loader calls before
moving the six values across (for example
[common/glbatchLD.cbl:L262-L267]). The six keywords are that program's own.

The environment is read rather than a file, and no CLI option is added: a
credential on a command line appears in the process table and in shell history,
and adding an option would also add a surface the frozen program does not have
(R-3). A parameter value is never logged or echoed - only the name of a missing
one.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from acas_posting.records.system_record import SystemRecord

__all__: Final[tuple[str, ...]] = (
    "RDB_RETURN_OK",
    "RDB_RETURN_MALFORMED",
    "RDB_RETURN_NO_SOURCE",
    "ACAS_PARAM_CONTRACT",
    "RdbmsParams",
    "RdbmsParamError",
    "resolve_rdbms_params",
    "bind_rdbms_connection",
    # ---- the deployment transport declaration, which has no frozen -------
    #      counterpart and is entirely optional
    "AFFIRMATIVE_SPELLINGS",
    "NEGATIVE_SPELLINGS",
    "CONNECT_TIMEOUT_DEFAULT",
    "READ_TIMEOUT_DEFAULT",
    "WRITE_TIMEOUT_DEFAULT",
    "TRANSPORT_ALLOW_PLACEHOLDER_CREDENTIALS_VARIABLE",
    "TRANSPORT_ALLOW_PLAINTEXT_VARIABLE",
    "TRANSPORT_CA_VARIABLE",
    "TRANSPORT_CERTIFICATE_VARIABLE",
    "TRANSPORT_CONNECT_TIMEOUT_VARIABLE",
    "TRANSPORT_KEY_VARIABLE",
    "TRANSPORT_READ_TIMEOUT_VARIABLE",
    "TRANSPORT_REQUIRE_DECLARED_CREDENTIALS_VARIABLE",
    "TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE",
    "TRANSPORT_WRITE_TIMEOUT_VARIABLE",
    #  The one authoritative inventory of the contract above: every variable, the
    #  field that consumes it and whether the shipped stack provides it (F-07).
    "TRANSPORT_CONTRACT",
    "TransportContractEntry",
    "TransportPolicyParams",
    "read_declared_flag",
    "resolve_transport_policy",
    # ---- deployment policy, deliberately OFF the parity path (M-06) -------
    "audit_deployment_contract",
)


#: "0 = Valid data read." Never raised; recorded so the set is complete and so a caller
#: can compare against it without transcribing the literal.
RDB_RETURN_OK: Final[int] = 0

#: "1 = No valid keyword terminator i.e., = or :" - the frozen code for "the
#: source is present but malformed" [common/acas-get-params.cbl:L200-L203].
#:
#: ⭐ M-06. NOT RAISED BY THIS TRANSPORT, and recorded so the frozen set is
#: complete rather than because anything reaches it. It used to be raised for a
#: blank, spaced or over-long VALUE; the frozen program refuses none of those - it
#: transforms them - so `_as_the_frozen_reader_would` now reproduces the
#: transformation and the refusals moved to `audit_deployment_contract`, which
#: warns instead. The condition this code actually names, a keyword terminator that
#: is neither "=" nor ":", cannot arise over an environment mapping at all: the
#: mapping is already split into names and values, so there is no terminator to
#: get wrong.
RDB_RETURN_MALFORMED: Final[int] = 1

RDB_RETURN_NO_SOURCE: Final[int] = 8


@dataclass(frozen=True, slots=True)
class _ParamSpec:
    """One of the six parameters, described end to end.

    Attributes:
        keyword: The `acas.param` keyword the frozen reader dispatches on, matched on
            its first six characters [common/acas-get-params.cbl:L204-L220].
        variable: The environment variable that carries the same value in a container.
            Set for the `gnucobol` service by `harness/docker-compose.yml`, and read by
            `harness/dump_tables.py`.
        attribute: The `SYSTEM-REC` `System-Data-Block` attribute the value is moved
            into - the receiving item of one of the six frozen `MOVE` statements at
            [common/glbatchLD.cbl:L262-L267].
        carrier_width: The NARROWEST frozen carrier the value must traverse to reach the
            client library.
        stored_width: The receiving `RDBMS-*` item's own `pic x(n)` width. The value is
            space-padded to exactly this many characters, which is what `MOVE` into an
            alphanumeric item does.
        required: Whether a blank value is a fault. Five are required; the socket is
            legitimately blank, which means "connect over TCP", and `harness/docker-
            compose.yml` sets `ACAS_DB_SOCKET: ""` explicitly.
        locator: Where the receiving item is declared, for traceability.
    """

    keyword: str
    variable: str
    attribute: str
    carrier_width: int
    stored_width: int
    required: bool
    locator: str


#: The six parameters, IN THE ORDER OF THE FROZEN `MOVE` STATEMENTS at
#: [common/glbatchLD.cbl:L262-L267] - Host, User, Passwd, DB-Name, Port, Socket.
ACAS_PARAM_CONTRACT: Final[tuple[_ParamSpec, ...]] = (
    _ParamSpec(
        keyword="DBHOST",
        variable="ACAS_DB_HOST",
        attribute="rdbms_host",
        carrier_width=32,
        stored_width=32,
        required=True,
        locator="copybooks/wssystem.cob:L143",
    ),
    _ParamSpec(
        keyword="DBUSER",
        variable="ACAS_DB_USER",
        attribute="rdbms_user",
        carrier_width=12,
        stored_width=12,
        required=True,
        locator="copybooks/wssystem.cob:L138",
    ),
    _ParamSpec(
        keyword="DBPASS",
        variable="ACAS_DB_PASSWORD",
        attribute="rdbms_passwd",
        carrier_width=12,
        stored_width=12,
        required=True,
        locator="copybooks/wssystem.cob:L139",
    ),
    _ParamSpec(
        keyword="DBNAME",
        variable="ACAS_DB_NAME",
        attribute="rdbms_db_name",
        carrier_width=12,
        stored_width=12,
        required=True,
        locator="copybooks/wssystem.cob:L137",
    ),
    _ParamSpec(
        keyword="DBPORT",
        variable="ACAS_DB_PORT",
        attribute="rdbms_port",
        # FOUR, not five. `LK-Port-Number pic x(4)` [common/acas-get-params.cbl:L158] on
        # the fallback path, and `01 Ws-Mysql-Port-Number pic x(4)` [copybooks/mysql-
        # variables.cpy:L91] on every bridge path [common/glpostingMT.cbl:L410-L413].
        carrier_width=4,
        stored_width=5,
        required=True,
        locator="copybooks/wssystem.cob:L142",
    ),
    _ParamSpec(
        keyword="DBSOCK",
        variable="ACAS_DB_SOCKET",
        attribute="rdbms_socket",
        carrier_width=64,
        stored_width=64,
        required=False,
        locator="copybooks/wssystem.cob:L144",
    ),
)


class RdbmsParamError(ValueError):
    """The connection contract is absent or unusable, so the run cannot start.

    Subclasses `ValueError` because a caller naturally expects one when a supplied value
    is wrong - the convention `acas_posting/dictionary/loader.py` and
    `harness/dump_tables.py` both follow.

    Attributes:
        return_code: The frozen counterpart from
            [common/acas-get-params.cbl:L37-L42]. In practice always
            `RDB_RETURN_NO_SOURCE` (8) - the contract is absent entirely -
            because that is the frozen program's only refusal this transport can
            express (M-06). `RDB_RETURN_MALFORMED` (1) is published on the class
            so the frozen set is complete and so a caller may compare against it,
            but nothing in this module raises it: a present-but-awkward value is
            transformed as the frozen reader transforms it, and
            `audit_deployment_contract` reports the concern instead.
    """

    def __init__(self, return_code: int, message: str) -> None:
        """Build the error with its frozen return code.

        Args:
            return_code: `RDB_RETURN_NO_SOURCE` or `RDB_RETURN_MALFORMED`.
            message: What is wrong and what to do about it. Must not contain a parameter
                value.
        """
        super().__init__(message)
        self.return_code: int = return_code


@dataclass(frozen=True, slots=True, repr=False)
class RdbmsParams:
    """The six resolved values, as `LK-RDB-Vars` holds them.

    Frozen, because a resolved contract is a fact about the environment as it was read;
    slotted, because there is exactly one instance per run and it needs no per-object
    dictionary.

    Attributes:
        host: `DBHOST` -> `LK-Host-Name` -> `RDBMS-Host`.
        user: `DBUSER` -> `LK-Implementation` -> `RDBMS-User`.
        password: `DBPASS` -> `LK-Password` -> `RDBMS-Passwd`. NEVER logged.
        database: `DBNAME` -> `LK-Base-Name` -> `RDBMS-DB-Name`.
        port: `DBPORT` -> `LK-Port-Number` -> `RDBMS-Port`. Text, not an `int`.
        socket: `DBSOCK` -> `LK-Socket` -> `RDBMS-Socket`. Blank means "connect over
            TCP".
    """

    host: str
    user: str
    password: str
    database: str
    port: str
    socket: str

    def __repr__(self) -> str:
        """Describe the parameters WITHOUT the password.

        The password is replaced by a fixed marker rather than by its length, because a
        length is itself information about a credential.

        Returns:
            A representation safe to write to a log or a traceback.
        """
        return (
            f"{type(self).__name__}(host={self.host!r}, user={self.user!r}, "
            f"password=<redacted>, database={self.database!r}, "
            f"port={self.port!r}, socket={self.socket!r})"
        )


def _pic_x(text: str, width: int) -> str:
    """Fit a value to an alphanumeric picture of `width` characters.

    COBOL `MOVE` into a `pic x(n)` item truncates on the right and pads on the
    right with spaces. Reproduced locally, mirroring the same private helper in
    `acas_posting/dal/connection.py` and `acas_posting/dal/status.py`, because
    this layer may not import `acas_posting/cobol/move.py`: the Agent Action
    Plan's import table (section 0.4.3) does not permit a `cli` module to reach
    the `cobol` package.

    ⭐ M-06. TRUNCATION IS NOW REACHABLE, and this note used to say the opposite:
    "the caller has already refused anything longer than its carrier". That
    refusal has been removed as an added validation, so an over-long value now
    arrives here and is truncated - which is what the frozen `MOVE` does, and the
    reason this helper was written as the full rule rather than as a pad.

    Args:
        text: The sending value.
        width: The receiving item's declared character count.

    Returns:
        Exactly `width` characters.
    """
    return text[:width].ljust(width)


#: The UNSTRING delimiter set of [common/acas-get-params.cbl:L193-L199]:
#:
#:     unstring ACAS-Params-Record delimited by "="
#:                                           or ":"
#:                                           or space
#:                     into WS-RDB-Keyword
#:                              DELIMITER IN WS-RDB-Equal
#:                          WS-RDB-Value
#:
#: THREE CHARACTERS AND NO MORE. `space` in COBOL is X'20' - it is not "any
#: whitespace" - so a TAB inside a value is NOT a delimiter and travels intact,
#: while a space, an "=" or a ":" ends the value there. The second receiving item
#: is delimited by the same set as the first, which is why a value is cut at the
#: next delimiter rather than running to the end of the record.
_UNSTRING_DELIMITERS: Final[tuple[str, ...]] = ("=", ":", " ")

#: `03 WS-RDB-Value pic x(64).` [common/acas-get-params.cbl:L135] - the UNSTRING's
#: second receiving item, and the sender of every one of the six `MOVE`s at
#: [common/acas-get-params.cbl:L204-L221]. A value longer than this is truncated
#: by the UNSTRING before any `MOVE` is reached.
_WS_RDB_VALUE_WIDTH: Final[int] = 64


def _as_the_frozen_reader_would(value: str, spec: _ParamSpec) -> str:
    """Put one value through the frozen reader's own three transformations.

    ⭐ M-06.  THIS IS WHAT REPLACED THREE REFUSALS. `acas-get-params` never
    objects to a value's emptiness, spacing or length; it disposes of all three
    silently, and each disposal is a statement in the frozen source rather than a
    policy:

      1. THE UNSTRING CUTS AT THE FIRST DELIMITER
         [common/acas-get-params.cbl:L193-L199]. `DBPASS=my pass` yields
         `WS-RDB-Value` = "my", and the rest of the line is discarded. So a value
         with a space in it is SHORTENED, which is precisely what the refusal that
         used to stand here said would happen - and then refused instead of
         reproducing.
      2. THE UNSTRING RECEIVER IS `pic x(64)`
         [common/acas-get-params.cbl:L135], so anything longer is already gone
         before a `MOVE` is reached.
      3. THE `MOVE` TRUNCATES TO THE CARRIER
         [common/acas-get-params.cbl:L204-L221]. This one is not theoretical: the
         port travels `move WS-RDB-Value to LK-Port-Number` into
         `pic x(4)` [common/acas-get-params.cbl:L158], a 64-to-4 narrowing that
         truncates every port longer than four digits without a word.

    A MISSING VARIABLE NEEDS NO CASE OF ITS OWN. `initialise LK-RDB-Vars`
    [common/acas-get-params.cbl:L180-L182] over a group declared
    `value spaces` [common/acas-get-params.cbl:L152] leaves an unmatched keyword's
    carrier space-filled, and the `evaluate` simply never reaches it. Passing "" in
    and letting step 3 pad is the same outcome by the same rule.

    Args:
        value: The raw environment value - this transport's counterpart of the
            characters after the "=" on an `acas.param` line.
        spec: The parameter's contract entry, which carries the receiving
            carrier's width.

    Returns:
        The value as the frozen reader would have left it in `LK-RDB-Vars`,
        UNPADDED - `bind_rdbms_connection`'s own `MOVE` does the padding, so
        padding here would pad twice.
    """
    #  1.  `unstring ... delimited by "=" or ":" or space` - cut at the first one.
    cut = len(value)
    for delimiter in _UNSTRING_DELIMITERS:
        position = value.find(delimiter)
        if position != -1:
            cut = min(cut, position)
    unstrung = value[:cut]

    #  2.  ...into `WS-RDB-Value pic x(64)`.
    #  3.  `move WS-RDB-Value to LK-<carrier>`, which truncates on the right.
    #  `_pic_x` applies the full `MOVE` rule and then `.rstrip()` undoes only its
    #  padding, because this function's contract is to return the value unpadded.
    return _pic_x(unstrung[:_WS_RDB_VALUE_WIDTH], spec.carrier_width).rstrip(" ")


def audit_deployment_contract(
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Report deployment concerns about the contract. NOT on the parity path.

    ⭐ M-06.  THE POLICY THAT USED TO LIVE INSIDE `resolve_rdbms_params`, MOVED
    HERE INTACT. It was three refusals, and they were right about the operational
    risk and wrong about where the risk belongs: `acas-get-params` refuses only an
    absent source, a bad keyword terminator and an unrecognised keyword, so
    refusing a blank, a spaced or an over-long VALUE added dispositions the
    compiled program has not got, and rule R-3 forbids that.

    So the concerns are published as WARNINGS from a function the migrated cycle
    never calls. Nothing in `acas_posting` calls it - verify with a grep - which is
    what makes it "outside the parity path" structurally rather than by
    convention. An orchestrator, a harness script or an operator may call it
    before a run and act on what it says; a posting program cannot be affected by
    it, because it is not reachable from one.

    WHY THE CONCERNS ARE STILL WORTH REPORTING. Each describes a way the two
    halves of a scenario comparison could connect DIFFERENTLY while both appear to
    succeed, and a diff between two differently-connected runs says nothing about
    the migration:

      * A blank required value leaves its carrier space-filled and the run
        connects as spaces, or to no host.
      * A value containing a space is cut at the space
        [common/acas-get-params.cbl:L193-L199], so the credential actually used is
        shorter than the one supplied.
      * A value longer than its carrier is truncated
        [common/acas-get-params.cbl:L204-L221] - the port narrows 64 to 4 - so the
        run may reach a different port, database or user than intended.

    THE VALUES THEMSELVES ARE NEVER INCLUDED in a message. One of the six is a
    password, and a warning that echoed it would put it in a log.

    Args:
        env: The mapping to audit. `os.environ` when omitted.

    Returns:
        One string per concern, in contract order, or an empty tuple when the
        contract is clean. An empty tuple is not a guarantee that a connection
        will succeed; it only means these three shapes of silent divergence are
        absent.
    """
    source: Mapping[str, str] = os.environ if env is None else env
    concerns: list[str] = []

    if not any(spec.variable in source for spec in ACAS_PARAM_CONTRACT):
        concerns.append(
            "no database connection contract is present: not one of "
            + ", ".join(spec.variable for spec in ACAS_PARAM_CONTRACT)
            + " is set. resolve_rdbms_params raises RDB_RETURN_NO_SOURCE (8) for "
            "this, reproducing the frozen `move 8 to LK-Return / goback` "
            "[common/acas-get-params.cbl:L174-L178]."
        )
        return tuple(concerns)

    for spec in ACAS_PARAM_CONTRACT:
        value = source.get(spec.variable, "")

        if spec.required and not value:
            concerns.append(
                f"{spec.variable} is not set, or is empty, but it carries the "
                f"{spec.keyword} parameter the frozen reader moves into "
                f"{spec.attribute} [{spec.locator}]. Five of the six are needed "
                f"for a working connection; only ACAS_DB_SOCKET may be empty, "
                f"which means connect over TCP. The run will NOT stop - the "
                f"carrier is simply left space-filled, exactly as "
                f"`initialise LK-RDB-Vars` over a group declared `value spaces` "
                f"[common/acas-get-params.cbl:L152] leaves it."
            )

        if any(character.isspace() for character in value):
            concerns.append(
                f"{spec.variable} contains whitespace. The frozen reader "
                f"UNSTRINGs its value 'delimited by \"=\" or \":\" or space' "
                f"[common/acas-get-params.cbl:L193-L199] and every bridge then "
                f"extracts the item 'delimited by space' "
                f"[common/glpostingMT.cbl:L394-L417], so the value actually used "
                f"is CUT AT THE FIRST SPACE. Both halves of a comparison will cut "
                f"it identically, but neither will use what was supplied. (The "
                f"value itself is deliberately not shown.)"
            )

        if len(value) > spec.carrier_width:
            concerns.append(
                f"{spec.variable} is {len(value)} characters long but the COBOL "
                f"side can carry at most {spec.carrier_width}: the value reaches "
                f"the client library through {spec.attribute} [{spec.locator}] "
                f"and the RDB-Data group [copybooks/wsfnctn.cob:L56-L62]"
                + (
                    ", narrowing again into "
                    "`01 Ws-Mysql-Port-Number pic x(4)` "
                    "[copybooks/mysql-variables.cpy:L91] before the connect"
                    if spec.keyword == "DBPORT"
                    else ""
                )
                + ". MOVE truncates it silently, here as in the frozen source, so "
                "the run may authenticate as a different user or reach a "
                "different database or port than intended. (The value itself is "
                "deliberately not shown.)"
            )

    return tuple(concerns)


# =============================================================================
#  THE READER  -  `acas-get-params` over the environment
# =============================================================================


def resolve_rdbms_params(
    env: Mapping[str, str] | None = None,
) -> RdbmsParams:
    """Read the six connection parameters, as `acas-get-params` reads them.

    Reproduces `common/acas-get-params.cbl` over the environment transport: the
    same six keywords, the same closed set, and the ONE refusal that transport can
    express - an absent source. Nothing is defaulted, guessed or repaired, and
    equally nothing is refused that the frozen program would have accepted: a
    blank, spaced or over-long value is put through the frozen reader's own
    UNSTRING-and-MOVE transformations by `_as_the_frozen_reader_would` (M-06).
    `audit_deployment_contract` reports those three as warnings for a caller that
    wants to act on them before a run; this function does not, because a refusal
    here would be a disposition the compiled cycle has not got (rule R-3).

    THE ENVIRONMENT IS READ ONCE, HERE. Every value is taken from `env` in one
    pass, in the frozen `MOVE` order, so two calls given the same mapping
    resolve identically (rule R-6). Nothing else in the shipped package reads
    the environment.

    Args:
        env: The mapping to resolve from. `os.environ` when omitted, which is the case
            in a real run.

    Returns:
        The six resolved values, unpadded and transformed exactly as the frozen
        reader would have left them in `LK-RDB-Vars` - see
        `_as_the_frozen_reader_would`.

    Raises:
        RdbmsParamError: With `return_code` `RDB_RETURN_NO_SOURCE` (8) when not
            one of the six variables is present - this transport's "No file
            found" [common/acas-get-params.cbl:L39], and reproducing
            `move 8 to LK-Return / goback` [common/acas-get-params.cbl:L174-L178].
            THAT IS THE ONLY REFUSAL (M-06). A blank, spaced or over-long value is
            transformed rather than refused, because the frozen program transforms
            it; call `audit_deployment_contract` to be WARNED about those three
            instead.
    """
    source: Mapping[str, str] = os.environ if env is None else env

    # `call "CBL_CHECK_FILE_EXIST" using "acas.param"` / `if Return-Code not = zero /
    # move 8 to LK-Return / goback` [common/acas-get-params.cbl:L174-L178] is "is there
    # a source at all?".
    if not any(spec.variable in source for spec in ACAS_PARAM_CONTRACT):
        raise RdbmsParamError(
            RDB_RETURN_NO_SOURCE,
            "no database connection contract is present in the environment: "
            "not one of "
            + ", ".join(spec.variable for spec in ACAS_PARAM_CONTRACT)
            + " is set. The migrated cycle takes its connection parameters "
            "from these six variables, which are the container-native "
            "transport of the six acas.param keywords the frozen "
            "common/acas-get-params.cbl reads (DBHOST, DBUSER, DBPASS, "
            "DBNAME, DBPORT, DBSOCK). harness/docker-compose.yml sets all six "
            "for the gnucobol service, so run inside that service, or export "
            "them before invoking an entry point. Without them SYSTEM-REC "
            "keeps the copybook's placeholder literals "
            "[copybooks/wssystem.cob:L137-L144] and the run would connect as "
            "ACAS-User to a blank host.",
        )

    #  ⭐ M-06.  THE THREE REFUSALS THAT USED TO STAND HERE ARE REPLACED BY THE
    #  TRANSFORMATIONS THE FROZEN READER ACTUALLY PERFORMS. They refused a
    #  required-and-blank value, a value containing whitespace, and a value longer
    #  than its carrier, each on the reasoning that the COBOL's silence would let
    #  the two halves of a comparison connect differently. Every word of that
    #  reasoning is true and none of it makes a refusal faithful: rule R-3 forbids
    #  adding a validation, and `acas-get-params` has exactly THREE refusals - code
    #  8 for no source at all [common/acas-get-params.cbl:L174-L178], code 1 for a
    #  keyword terminator that is neither "=" nor ":"
    #  [common/acas-get-params.cbl:L200-L203], and code 2 for an unrecognised
    #  keyword [common/acas-get-params.cbl:L217-L219]. NOT ONE of them is about a
    #  value's emptiness, its spacing or its length, because the frozen program
    #  disposes of all three by TRANSFORMING rather than by objecting - and
    #  reproducing the transformation preserves the parity that refusing destroyed.
    #
    #  THE POLICY IS NOT DISCARDED, ONLY MOVED OFF THIS PATH. Call
    #  `audit_deployment_contract` explicitly and it returns the same three
    #  concerns as warnings. Nothing in the migrated cycle calls it, which is
    #  exactly what "outside the parity path" means.
    resolved: dict[str, str] = {}
    for spec in ACAS_PARAM_CONTRACT:
        resolved[spec.keyword] = _as_the_frozen_reader_would(
            source.get(spec.variable, ""), spec
        )

    return RdbmsParams(
        host=resolved["DBHOST"],
        user=resolved["DBUSER"],
        password=resolved["DBPASS"],
        database=resolved["DBNAME"],
        port=resolved["DBPORT"],
        socket=resolved["DBSOCK"],
    )


def bind_rdbms_connection(
    system_record: SystemRecord,
    *,
    env: Mapping[str, str] | None = None,
) -> RdbmsParams:
    """Put the resolved connection parameters into `SYSTEM-REC`.

    THE one adapter between the deployment contract and the migrated cycle.
    After this returns, `SYSTEM-REC` carries real values in its six `RDBMS-*`
    fields, and `acas_posting/dal/connection.py` needs no change at all: it
    goes on copying those fields into `RDB-Data` exactly as
    [common/acas008.cbl:L558-L563] does, and it goes on being the only module
    that talks to the driver.

    Reproduces the six `MOVE` statements every load program performs after its
    `call "acas-get-params"` - [common/glbatchLD.cbl:L262-L267], identically at
    [common/nominalLD.cbl:L248-L253] and [common/glpostingLD.cbl:L263-L268] -
    IN THEIR SOURCE ORDER, which is Host, User, Passwd, DB-Name, Port, Socket.

    Each value is stored space-padded to its receiving item's own `pic x(n)`
    width, which is what `MOVE` into an alphanumeric item does; the frozen
    port narrowing to `pic x(4)` is left to the data-access layer, which
    already reproduces it.

    THE FROZEN GUARD IS DELIBERATELY NOT REPRODUCED, and this is the one place
    the reproduction departs from the letter of the source. The load programs
    wrap the whole block in `if RDBMS-DB-Name = spaces or FS-Cobol-Files-Used`
    [common/glbatchLD.cbl:L238-L239], because there the record has just been
    READ from `system.dat` and may already hold usable settings. Here it has
    not: this function runs BEFORE the store is read, on a `SYSTEM-REC` still at
    the record layer's declared defaults, and it has to - the six fields it
    fills are the only carrier by which a connection parameter reaches the
    data-access layer, so nothing could be read without them (the load itself is
    `aa010_get_system_recs`, and `Q-CLI-SYSREC-LOAD` in
    `acas_posting/cli/args.py` records the ordering). `RDBMS-DB-Name` is
    therefore never spaces at this point - it is the
    literal "ACASDB" [copybooks/wssystem.cob:L137] - and a literal
    reproduction of the guard would skip the load on every single run and leave
    the placeholder password in place. The guard's INTENT is "load them if they
    are not already set", and under the declared defaults they are never set,
    so the load always runs. Recorded as a documented divergence in this
    module's footer.

    Args:
        system_record: The record to fill.
        env: The mapping to resolve from, passed through to `resolve_rdbms_params`.
            `os.environ` when omitted.

    Returns:
        The resolved parameters, so a caller can record WHICH endpoint a run used
            without re-reading the environment. Its representation redacts the password.

    Raises:
        RdbmsParamError: The contract is absent or unusable. Raised by
            `resolve_rdbms_params` BEFORE any field is written, so a failed call leaves
            `system_record` exactly as it found it.
    """
    parameters = resolve_rdbms_params(env)

    # Resolve fully before writing anything, so the record is never left half filled:
    # the reader above raises before this point or not at all.
    values: dict[str, str] = {
        "DBHOST": parameters.host,
        "DBUSER": parameters.user,
        "DBPASS": parameters.password,
        "DBNAME": parameters.database,
        "DBPORT": parameters.port,
        "DBSOCK": parameters.socket,
    }

    # All six receiving items are `05` items of `03 System-Data-Block.`
    # [copybooks/wssystem.cob:L52], so the record layer exposes them on
    # `SystemRecord.system_data_block`.
    system_data_block = system_record.system_data_block

    for spec in ACAS_PARAM_CONTRACT:
        setattr(
            system_data_block,
            spec.attribute,
            _pic_x(values[spec.keyword], spec.stored_width),
        )

    return parameters


# =============================================================================
#  THE DEPLOYMENT TRANSPORT DECLARATION  -  NO FROZEN COUNTERPART
# =============================================================================
#
#  ⛔ THIS IS NOT PART OF THE SIX-PARAMETER CONTRACT, AND `ACAS_PARAM_CONTRACT`
#  STAYS CLOSED AT SIX. `common/acas-get-params.cbl` has no seventh keyword and
#  the frozen `evaluate` closes the set [common/acas-get-params.cbl:L204-L220];
#  the four names below are DEPLOYMENT settings for a facility the compiled
#  system does not have at all - the C interface passes a literal zero
#  client-flag word and negotiates no TLS whatsoever
#  [copybooks/mysql-procedures.cpy:L72-L77].
#
#  They are read here, and not in `args.py`, because this module is the one
#  adapter in the shipped package that reads the surroundings. Every one is
#  OPTIONAL: with none of them set the resolved declaration is empty, the
#  data-access layer's own default applies, and the migrated cycle behaves
#  exactly as the compiled one does - so nothing is added to the behaviour under
#  comparison (rule R-3). Two runs given the same mapping resolve identically
#  (rule R-6).
# =============================================================================

#: The certificate authority bundle the server's certificate is verified
#: against. Setting it turns the session into a verified, encrypted one.
TRANSPORT_CA_VARIABLE: Final[str] = "ACAS_DB_TLS_CA"

#: A client certificate and its private key, for a server that requires one.
#: Both or neither: the data-access layer refuses a half-configured pair,
#: because a certificate cannot authenticate without its key.
TRANSPORT_CERTIFICATE_VARIABLE: Final[str] = "ACAS_DB_TLS_CERT"
TRANSPORT_KEY_VARIABLE: Final[str] = "ACAS_DB_TLS_KEY"

#: Declares that the target is the comparison harness on a private network whose
#: server has no TLS configured, so a plaintext connection to it is intended.
#: This is what silences the unprotected-transport warning for a harness run,
#: and it is a DECLARATION - nothing infers it from the address.
#:
#: ⭐ ONE KEY, AND THIS IS IT. The spelling is the harness's own, published by
#: `harness/docker-compose.yml` and read by `harness/build_oracle.sh`,
#: `harness/seed.sh`, `harness/reset_db.sh`, `harness/run_cobol_scenario.sh` and
#: `harness/run_python_scenario.sh`. An earlier revision of this module read a
#: SECOND name here, `ACAS_DB_ISOLATED_ORACLE`, which nothing set: a harness run
#: exported the Compose spelling, this resolver looked for the other one, and the
#: declaration silently did not arrive - so a non-loopback target was refused
#: even though the operator had declared it. There is now exactly one name for
#: this decision across Python, shell, Compose, the tests and the documentation.
TRANSPORT_ALLOW_PLAINTEXT_VARIABLE: Final[str] = "ACAS_DB_ALLOW_PLAINTEXT"

#: FORCES the refusal even where the plaintext declaration was made, for a
#: deployment that wants no unencrypted path at all. Strictness outranks
#: permission: with both set the connection is refused.
TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE: Final[str] = "ACAS_DB_REQUIRE_TLS"

#: FORCES the placeholder-credential refusal even where the placeholder
#: declaration was made, on the same terms.
TRANSPORT_REQUIRE_DECLARED_CREDENTIALS_VARIABLE: Final[str] = (
    "ACAS_DB_REQUIRE_DECLARED_CREDENTIALS"
)

#: Declares that the shipped placeholder credentials of
#: [copybooks/wssystem.cob:L138-L139] are the intended ones and the server is
#: disposable, which is the harness's situation.
TRANSPORT_ALLOW_PLACEHOLDER_CREDENTIALS_VARIABLE: Final[str] = (
    "ACAS_DB_ALLOW_PLACEHOLDER_CREDENTIALS"
)

#: The spellings read as YES, compared case-insensitively after stripping. A
#: The three driver deadlines, in whole seconds (finding F-05). The frozen C
#: interface passes none - `mysql_real_connect` is called with a literal zero
#: client-flag word and no option is set on the handle
#: [copybooks/mysql-procedures.cpy:L72-L77] - so an unreachable or wedged server
#: blocks the compiled program indefinitely too. That is not a behaviour worth
#: reproducing in a headless batch process: it produces no different table state,
#: only a run that never ends. Each is therefore bounded by default and
#: configurable, and each is a DEPLOYMENT setting rather than part of the
#: six-parameter contract.
TRANSPORT_CONNECT_TIMEOUT_VARIABLE: Final[str] = "ACAS_DB_CONNECT_TIMEOUT"
TRANSPORT_READ_TIMEOUT_VARIABLE: Final[str] = "ACAS_DB_READ_TIMEOUT"
TRANSPORT_WRITE_TIMEOUT_VARIABLE: Final[str] = "ACAS_DB_WRITE_TIMEOUT"

#: The defaults, chosen so that no posting run this migration can produce is cut
#: short by them. A connect to a healthy server on the harness's internal network
#: completes in milliseconds; the two per-statement budgets are two orders of
#: magnitude above the slowest statement the cycle issues, which is a full
#: sequential walk of one seeded table.
CONNECT_TIMEOUT_DEFAULT: Final[int] = 10
READ_TIMEOUT_DEFAULT: Final[int] = 300
WRITE_TIMEOUT_DEFAULT: Final[int] = 300

#: A day, the same ceiling `harness/run_python_scenario.sh` puts on its own
#: budgets. Past this a "bound" is indistinguishable from none.
_TIMEOUT_CEILING_SECONDS: Final[int] = 86_400

#: The spellings read as true, compared case-insensitively after stripping. A
#: closed set rather than "anything non-empty": a variable left as `"0"` or
#: `"false"` by a deployment template must not silently mean yes.
#:
#: ⭐ THE SET IS THE HARNESS SHELL'S OWN, CHARACTER FOR CHARACTER. Every reader
#: in the tree matches on `1|true|yes|on` - `harness/seed.sh`,
#: `harness/reset_db.sh`, `harness/build_oracle.sh`,
#: `harness/run_cobol_scenario.sh` and the preflight embedded in
#: `harness/run_python_scenario.sh` - so one exported value cannot mean two
#: different things to the two halves of the harness. `y` used to be accepted
#: here and nowhere else, which is precisely the kind of drift this constant
#: exists to remove.
AFFIRMATIVE_SPELLINGS: Final[frozenset[str]] = frozenset(
    {"1", "true", "yes", "on"}
)

#: The spellings read as NO, on the same terms. The empty string is here because
#: an unset or blank variable is a declaration of nothing, which is the default.
NEGATIVE_SPELLINGS: Final[frozenset[str]] = frozenset(
    {"", "0", "false", "no", "off"}
)


@dataclass(frozen=True, slots=True)
class TransportContractEntry:
    """One row of the transport environment contract.

    Attributes:
        variable: The environment variable name.
        field: The :class:`TransportPolicyParams` field it resolves into, which is
            this row's CONSUMER - every field is read by
            :func:`acas_posting.cli.args.install_connection_policy` and turned into
            the one installed ``dal.connection.ConnectionPolicy``.
        provided_by_harness: ``True`` when `harness/docker-compose.yml` sets the
            variable for the comparison stack. A row that is ``False`` is optional
            everywhere and has a documented default - never a knob that has to be
            set for the harness to be correct.
        alias_of: The canonical variable this row is an alias for, or ``None``.
        meaning: What declaring it does, in one line.
    """

    variable: str
    field: str
    provided_by_harness: bool
    alias_of: str | None
    meaning: str


#: THE WHOLE TRANSPORT ENVIRONMENT CONTRACT, IN ONE PLACE (finding F-07).
#:
#: There used to be two: this module declared four flag variables while
#: `acas_posting/cli/args.py` read a fifth of its own and the harness set only
#: that fifth - so the four this module declared had no provider, and the
#: command-line path returned before the refusal knobs were ever consulted. One
#: table now names every variable, the field it resolves into (its consumer) and
#: whether the shipped stack provides it, and `tests/` asserts that every row has
#: both a provider and a consumer, so a knob that nothing sets or nothing reads
#: cannot be added again unnoticed.
TRANSPORT_CONTRACT: Final[tuple[TransportContractEntry, ...]] = (
    TransportContractEntry(
        variable=TRANSPORT_CA_VARIABLE,
        field="ca_file",
        provided_by_harness=False,
        alias_of=None,
        meaning=(
            "PEM bundle the server certificate must chain to; supplying it turns "
            "the session into a verified, encrypted one"
        ),
    ),
    TransportContractEntry(
        variable=TRANSPORT_CERTIFICATE_VARIABLE,
        field="certificate_file",
        provided_by_harness=False,
        alias_of=None,
        meaning="client certificate, for a server that requires one",
    ),
    TransportContractEntry(
        variable=TRANSPORT_KEY_VARIABLE,
        field="key_file",
        provided_by_harness=False,
        alias_of=None,
        meaning="the client certificate's private key; both or neither",
    ),
    TransportContractEntry(
        variable=TRANSPORT_ALLOW_PLAINTEXT_VARIABLE,
        field="isolated_oracle",
        provided_by_harness=True,
        alias_of=None,
        meaning=(
            "declares the target the isolated comparison oracle, so plaintext to "
            "it is intended rather than accidental"
        ),
    ),
    TransportContractEntry(
        variable=TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE,
        field="require_encrypted_transport",
        provided_by_harness=False,
        alias_of=None,
        meaning=(
            "turns the unprotected-transport REPORT into a refusal; off unless "
            "set, because the compiled program applies no such check (R-3)"
        ),
    ),
    TransportContractEntry(
        variable=TRANSPORT_REQUIRE_DECLARED_CREDENTIALS_VARIABLE,
        field="require_declared_placeholder_credentials",
        provided_by_harness=False,
        alias_of=None,
        meaning="turns the placeholder-credential report into a refusal",
    ),
    TransportContractEntry(
        variable=TRANSPORT_ALLOW_PLACEHOLDER_CREDENTIALS_VARIABLE,
        field="allow_frozen_placeholder_credentials",
        provided_by_harness=False,
        alias_of=None,
        meaning=(
            "declares the frozen placeholder credentials of "
            "[copybooks/wssystem.cob:L138-L139] intended and the server disposable"
        ),
    ),
    TransportContractEntry(
        variable=TRANSPORT_CONNECT_TIMEOUT_VARIABLE,
        field="connect_timeout_seconds",
        provided_by_harness=False,
        alias_of=None,
        meaning=(
            f"driver connect deadline in seconds; default "
            f"{CONNECT_TIMEOUT_DEFAULT}"
        ),
    ),
    TransportContractEntry(
        variable=TRANSPORT_READ_TIMEOUT_VARIABLE,
        field="read_timeout_seconds",
        provided_by_harness=False,
        alias_of=None,
        meaning=f"driver read deadline in seconds; default {READ_TIMEOUT_DEFAULT}",
    ),
    TransportContractEntry(
        variable=TRANSPORT_WRITE_TIMEOUT_VARIABLE,
        field="write_timeout_seconds",
        provided_by_harness=False,
        alias_of=None,
        meaning=(
            f"driver write deadline in seconds; default {WRITE_TIMEOUT_DEFAULT}"
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class TransportPolicyParams:
    """The deployment's transport declaration, as resolved from the contract.

    Frozen and slotted, like :class:`RdbmsParams`. Deliberately NOT a
    ``dal.connection`` type: this module knows nothing of the data-access layer,
    and the entry-point layer turns these values into the one installed
    ``ConnectionPolicy``.

    ⭐ THE DEFAULTS FAIL CLOSED, AND THAT IS THE POINT OF THIS TYPE.
    An environment that sets none of the variables resolves to
    ``require_encrypted_transport=True`` and
    ``require_declared_placeholder_credentials=True``: a loopback address or a
    Unix socket still connects - those never leave the machine, and they are what
    a normal ACAS installation uses [copybooks/wsfnctn.cob:L57-L64] - while any
    OTHER target, and any run still carrying the credentials published at
    [copybooks/wssystem.cob:L138-L139], is REFUSED until the deployment says
    otherwise. Reporting-and-permitting was the previous default and it is a
    CWE-319/CWE-798 exposure at a production boundary: a warning in a log nobody
    reads is not a decision anybody made.

    NOTHING COMPARED MOVES BECAUSE OF THIS. The refusal happens before the
    connect, so it cannot alter a posted figure, a statement or a write order; the
    parity harness declares :data:`TRANSPORT_ALLOW_PLAINTEXT_VARIABLE` in
    ``harness/docker-compose.yml`` and connects exactly as before (rule R-6).

    Attributes:
        ca_file: :data:`TRANSPORT_CA_VARIABLE`, or ``None`` when unset.
        certificate_file: :data:`TRANSPORT_CERTIFICATE_VARIABLE`, or ``None``.
        key_file: :data:`TRANSPORT_KEY_VARIABLE`, or ``None``.
        isolated_oracle: :data:`TRANSPORT_ALLOW_PLAINTEXT_VARIABLE`, read as a
            boolean by :func:`read_declared_flag`, the one closed spelling set
            the shell half of the harness matches on. The narrow opt-out from
            the transport refusal.
        require_encrypted_transport: ``True`` unless ``isolated_oracle`` was
            declared, and ``True`` regardless when
            :data:`TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE` is set - strictness
            outranks permission.
        require_declared_placeholder_credentials: ``True`` unless
            ``allow_frozen_placeholder_credentials`` was declared, and ``True``
            regardless when
            :data:`TRANSPORT_REQUIRE_DECLARED_CREDENTIALS_VARIABLE` is set.
        allow_frozen_placeholder_credentials:
            :data:`TRANSPORT_ALLOW_PLACEHOLDER_CREDENTIALS_VARIABLE`, read as a
            boolean. The narrow opt-out from the credential refusal.
            :data:`TRANSPORT_ALLOW_PLACEHOLDER_CREDENTIALS_VARIABLE`, likewise.
        connect_timeout_seconds: :data:`TRANSPORT_CONNECT_TIMEOUT_VARIABLE`, or
            :data:`CONNECT_TIMEOUT_DEFAULT`. Always finite.
        read_timeout_seconds: :data:`TRANSPORT_READ_TIMEOUT_VARIABLE`, or
            :data:`READ_TIMEOUT_DEFAULT`. Always finite.
        write_timeout_seconds: :data:`TRANSPORT_WRITE_TIMEOUT_VARIABLE`, or
            :data:`WRITE_TIMEOUT_DEFAULT`. Always finite.
    """

    ca_file: str | None = None
    certificate_file: str | None = None
    key_file: str | None = None
    isolated_oracle: bool = False
    require_encrypted_transport: bool = True
    require_declared_placeholder_credentials: bool = True
    allow_frozen_placeholder_credentials: bool = False
    connect_timeout_seconds: int = CONNECT_TIMEOUT_DEFAULT
    read_timeout_seconds: int = READ_TIMEOUT_DEFAULT
    write_timeout_seconds: int = WRITE_TIMEOUT_DEFAULT


def _optional_path(env: Mapping[str, str], variable: str) -> str | None:
    """Read an optional path setting.

    Args:
        env: The mapping to read from.
        variable: The variable name.

    Returns:
        The stripped value, or ``None`` when the variable is absent or blank. A
        blank is read as absent rather than as an empty path, matching the way
        the frozen socket parameter treats one [common/acas-get-params.cbl].
    """
    value = env.get(variable, "").strip()
    return value or None


def read_declared_flag(env: Mapping[str, str], variable: str) -> bool:
    """Read one boolean deployment setting from its closed set of spellings.

    THE ONE PARSER FOR THE ONE CONTRACT. Every boolean the deployment can set is
    read through here, by this module and by
    :func:`acas_posting.cli.args.install_connection_policy`, so a value cannot be
    affirmative to one reader and not to another. The recognised spellings are
    :data:`AFFIRMATIVE_SPELLINGS` and :data:`NEGATIVE_SPELLINGS`, compared
    case-insensitively after stripping, and they are the shell half's own set.

    ⭐ UNRECOGNISED TEXT IS REFUSED, NOT GUESSED. An earlier revision of the
    entry-point layer read "any value other than empty and ``0``" as yes, so
    ``ACAS_DB_ALLOW_PLAINTEXT=false`` DECLARED PLAINTEXT - the opposite of what
    was written - while this module read the same word as no. Silently picking
    either reading is worse than stopping: the value governs whether a
    credential and every posted figure may cross a network in the clear, and the
    operator who typed it is the only party who knows what was meant. Nothing
    accounting is validated here (rule R-3): this is deployment configuration,
    it has no frozen counterpart at all, and it is read before any statement
    with a COBOL counterpart runs.

    Args:
        env: The mapping to read from.
        variable: The variable name.

    Returns:
        ``True`` for a recognised affirmative spelling, ``False`` for a
        recognised negative one and for an unset or blank variable.

    Raises:
        RdbmsParamError: The value is neither, carrying
            :data:`RDB_RETURN_MALFORMED` - the frozen reader's own code for
            "the source is present but malformed"
            [common/acas-get-params.cbl:L200-L203]. The message names the
            variable and the accepted spellings and NEVER the value, which may
            have been mistyped over a secret.
    """
    value = env.get(variable, "").strip().lower()
    if value in AFFIRMATIVE_SPELLINGS:
        return True
    if value in NEGATIVE_SPELLINGS:
        return False
    raise RdbmsParamError(
        RDB_RETURN_MALFORMED,
        f"{variable} is set to a value this contract does not recognise. "
        f"Use one of {', '.join(sorted(AFFIRMATIVE_SPELLINGS))} for yes or one "
        f"of {', '.join(sorted(spelling for spelling in NEGATIVE_SPELLINGS if spelling))} "
        f"for no, or leave it unset. The same closed set is read by "
        f"harness/build_oracle.sh, harness/seed.sh, harness/reset_db.sh, "
        f"harness/run_cobol_scenario.sh and harness/run_python_scenario.sh, so "
        f"one exported value means one thing everywhere.",
    )


def _optional_seconds(
    env: Mapping[str, str], variable: str, default: int
) -> int:
    """Read one finite, positive timeout in whole seconds.

    THE DEFAULT IS FINITE AND THERE IS NO SPELLING FOR "NO TIMEOUT" (finding
    F-05). A connect, read or write with no deadline turns an unreachable or wedged
    server into a process that never returns, which outside the harness's outer
    deadline is indistinguishable from a long posting run. The value is a
    DEPLOYMENT setting, exactly as the six connection parameters are: it changes no
    posted figure, no status and no statement, so two runs of one scenario against
    a healthy server resolve identically whatever it is set to (rule R-6).

    Args:
        env: The mapping to read from.
        variable: The variable name.
        default: The value used when the variable is absent or blank.

    Returns:
        The configured whole-second budget, or ``default``.

    Raises:
        RdbmsParamError: The value is not a positive whole number of seconds, or
            exceeds :data:`_TIMEOUT_CEILING_SECONDS`. A malformed budget is
            refused rather than silently replaced, because a deployment that
            asked for a bound is entitled to know its request was not honoured.
    """
    raw = env.get(variable, "").strip()
    if not raw:
        return default
    try:
        seconds = int(raw, 10)
    except ValueError as exc:
        raise RdbmsParamError(
            f"{variable} must be a whole number of seconds; it is {raw!r}",
            RDB_RETURN_MALFORMED,
        ) from exc
    if seconds <= 0 or seconds > _TIMEOUT_CEILING_SECONDS:
        raise RdbmsParamError(
            f"{variable} must be between 1 and {_TIMEOUT_CEILING_SECONDS} "
            f"seconds; it is {seconds}",
            RDB_RETURN_MALFORMED,
        )
    return seconds


def resolve_transport_policy(
    env: Mapping[str, str] | None = None,
) -> TransportPolicyParams:
    """Resolve the deployment's transport declaration. All fields optional.

    Read in one pass, in declaration order, from the same transport the six
    connection parameters come from - so a deployment configures its database
    reachability and its database protection in one place.

    Args:
        env: The mapping to resolve from. ``os.environ`` when omitted, which is
            the case in a real run; a test or an orchestrator passes an explicit
            mapping and touches the real environment not at all.

    Returns:
        The resolved declaration. With nothing set the two ``require_*`` fields
        are ``True`` and the two opt-outs are ``False``, which is the fail-closed
        policy argued on :class:`TransportPolicyParams`.

    Raises:
        RdbmsParamError: One of the four boolean settings carries text that is
            neither affirmative nor negative - see :func:`read_declared_flag`
            for why that is refused rather than guessed. An UNSET variable never
            raises; it resolves to the fail-closed default.
    """
    mapping = os.environ if env is None else env
    allow_plaintext = read_declared_flag(
        mapping, TRANSPORT_ALLOW_PLAINTEXT_VARIABLE
    )
    allow_placeholder = read_declared_flag(
        mapping, TRANSPORT_ALLOW_PLACEHOLDER_CREDENTIALS_VARIABLE
    )
    return TransportPolicyParams(
        ca_file=_optional_path(mapping, TRANSPORT_CA_VARIABLE),
        certificate_file=_optional_path(mapping, TRANSPORT_CERTIFICATE_VARIABLE),
        key_file=_optional_path(mapping, TRANSPORT_KEY_VARIABLE),
        isolated_oracle=allow_plaintext,
        #  FAIL CLOSED UNLESS DECLARED, and strictness outranks permission: an
        #  explicit `ACAS_DB_REQUIRE_TLS` refuses even where the plaintext
        #  declaration was made, so a deployment that wants no unencrypted path
        #  cannot have one granted by a stale variable in its environment.
        require_encrypted_transport=(
            read_declared_flag(mapping, TRANSPORT_REQUIRE_ENCRYPTION_VARIABLE)
            or not allow_plaintext
        ),
        require_declared_placeholder_credentials=(
            read_declared_flag(
                mapping, TRANSPORT_REQUIRE_DECLARED_CREDENTIALS_VARIABLE
            )
            or not allow_placeholder
        ),
        allow_frozen_placeholder_credentials=allow_placeholder,
        #  THE THREE DRIVER DEADLINES, always finite. The frozen C interface passes
        #  none, so a wedged server blocks the compiled program for ever; that
        #  produces no different table state, only a run that never ends, so each
        #  deadline is bounded by default and configurable from the contract.
        connect_timeout_seconds=_optional_seconds(
            mapping, TRANSPORT_CONNECT_TIMEOUT_VARIABLE, CONNECT_TIMEOUT_DEFAULT
        ),
        read_timeout_seconds=_optional_seconds(
            mapping, TRANSPORT_READ_TIMEOUT_VARIABLE, READ_TIMEOUT_DEFAULT
        ),
        write_timeout_seconds=_optional_seconds(
            mapping, TRANSPORT_WRITE_TIMEOUT_VARIABLE, WRITE_TIMEOUT_DEFAULT
        ),
    )


# -----------------------------------------------------------------------------
#  TRACEABILITY  (rule R-5)
# -----------------------------------------------------------------------------
#
# MODULE -> COBOL PROGRAM
#   acas_posting.cli.rdbms_params  <-  common/acas-get-params.cbl (224 lines,
#   program-id at L10), plus the six-statement MOVE block every load program
#   performs after calling it, e.g. common/glbatchLD.cbl:L262-L267.
#   Both are REFERENCE only: frozen, read as specification, never modified.
#
# PARAGRAPH -> FUNCTION
#   aa000-Main.                          -> resolve_rdbms_params
#     L173      move zero to LK-Return      the RDB_RETURN_OK path
#     L174-L178 CBL_CHECK_FILE_EXIST /      the "is there a source?" gate;
#               move 8 to LK-Return         RDB_RETURN_NO_SOURCE
#     L180-L182 initialise LK-RDB-Vars      the `value spaces` starting state,
#                                           which is why an incomplete source
#                                           is treated as malformed
#     L183-L221 open / perform until /      the one-pass read, in contract order
#               read / unstring
#     L193-L199 unstring ... delimited by   the whitespace gate
#               "=" or ":" or space
#     L200-L203 if WS-RDB-Equal not = "="   RDB_RETURN_MALFORMED
#               and not = ":" / move 1
#     L204-L220 evaluate WS-RDB-Keyword     ACAS_PARAM_CONTRACT, six entries
#               (1:6) ... when other        (`when other` -> see OMISSIONS)
#     L222-L223 close / goback              return RdbmsParams
#
#   the caller-side MOVE block           -> bind_rdbms_connection
#     common/glbatchLD.cbl:L262           move WS-Host-Name      to RDBMS-Host
#                          L263           move WS-Implementation to RDBMS-User
#                          L264           move WS-Password       to RDBMS-Passwd
#                          L265           move WS-Base-Name      to RDBMS-DB-Name
#                          L266           move WS-Port-Number    to RDBMS-Port
#                          L267           move WS-Socket         to RDBMS-Socket
#
# RECORD -> CLASS
#   01 LK-RDB-Vars     common/acas-get-params.cbl:L152-L159  -> RdbmsParams
#   01 LK-Return       common/acas-get-params.cbl:L150       -> RdbmsParamError
#                                                               .return_code
#
# FIELD -> RECEIVING ITEM -> COLUMN  (each also carried in ACAS_PARAM_CONTRACT)
#   DBHOST  ACAS_DB_HOST      RDBMS-Host     x(32)  wssystem.cob:L143
#                                                   SYSTEM-REC.RDBMS-HOST
#   DBUSER  ACAS_DB_USER      RDBMS-User     x(12)  wssystem.cob:L138
#                                                   SYSTEM-REC.RDBMS-USER
#   DBPASS  ACAS_DB_PASSWORD  RDBMS-Passwd   x(12)  wssystem.cob:L139
#                                                   SYSTEM-REC.RDBMS-PASSWD
#   DBNAME  ACAS_DB_NAME      RDBMS-DB-Name  x(12)  wssystem.cob:L137
#                                                   SYSTEM-REC.RDBMS-DB-NAME
#   DBPORT  ACAS_DB_PORT      RDBMS-Port     x(5)   wssystem.cob:L142
#                                                   SYSTEM-REC.RDBMS-PORT
#                             carried through Ws-Mysql-Port-Number x(4)
#                                                   mysql-variables.cpy:L91
#   DBSOCK  ACAS_DB_SOCKET    RDBMS-Socket   x(64)  wssystem.cob:L144
#                                                   SYSTEM-REC.RDBMS-SOCKET
#
# RETURN CODE -> CONSTANT      common/acas-get-params.cbl:L37-L42
#   0  RDB_RETURN_OK           "Valid data read."
#   1  RDB_RETURN_MALFORMED    "No valid keyword terminator i.e., = or :"
#   8  RDB_RETURN_NO_SOURCE    "No file found."
#   2  no counterpart          see OMISSIONS
#
# DOCUMENTED DIVERGENCES  -  two, each deliberate and each argued at the site.
#
#   1. THE SOURCE IS THE ENVIRONMENT, NOT `acas.param`. The frozen reader opens
#      a file in the current directory [common/acas-get-params.cbl:L30, L103].
#      This module reads six environment variables instead, because that is
#      where harness/docker-compose.yml publishes the values, because
#      harness/dump_tables.py already reads the identical six names, and
#      because a current-directory file would make a run depend on where it was
#      launched from - which rule R-6 forbids. The keywords, their order, their
#      closed set and the return codes are unchanged, so the reproduction is of
#      the program's BEHAVIOUR with a different transport, not of its file I/O.
#      `acas.param` itself is untouched and remains the compiled oracle's own
#      mechanism.
#
#   2. THE `if RDBMS-DB-Name = spaces or FS-Cobol-Files-Used` GUARD IS NOT
#      REPRODUCED [common/glbatchLD.cbl:L238-L239]. Argued in full in
#      `bind_rdbms_connection`: in the load programs the record has just been
#      read from `system.dat` and may already hold settings, whereas here it is
#      built at the record layer's declared defaults, where RDBMS-DB-Name is
#      the literal "ACASDB" and RDBMS-Passwd is the literal "PaSsWoRd". A
#      literal guard would therefore skip the load on every run and keep the
#      placeholder credentials - the exact defect this module closes. The
#      guard's intent, "load them if they are not already set", is honoured.
#
# OMISSIONS  -  recorded so that a reader comparing the two trees does not
# conclude something was lost (Agent Action Plan section 0.4.3).
#
#   * RETURN CODE 2, "Invalid Keyword - keyword not expected"
#     [common/acas-get-params.cbl:L42], raised by the frozen `when other` at
#     [common/acas-get-params.cbl:L217-L219]. It cannot arise here: this module
#     looks up exactly six named variables and NEVER enumerates the
#     environment, so an unrelated variable is not read, not parsed and not an
#     error. Shipping an unreachable branch for it would be dead code.
#
#   * THE `01 File-Info` BLOCK [common/acas-get-params.cbl:L137-L145]. The
#     frozen program declares an eight-member file-information group for
#     `CBL_CHECK_FILE_EXIST` and reads NOTHING out of it - only `Return-Code`
#     is tested [L176]. There is no file here and no size or modification stamp
#     to collect, and collecting one would be a wall-clock reading that rule
#     R-6 forbids in any case.
#
#   * `01 APR-Variable-Size` [common/acas-get-params.cbl:L122-L125], which the
#     frozen source itself annotates "Thrse are NOT used in program - just to
#     show record layout" [L120]. A layout comment, not a construct: its
#     content is documented in this module's header instead.
#
#   * THE DISPLAY STATEMENTS the load programs make around the call -
#     "acas-param file NOT found - Aborted", "Invalid keyword terminator
#     found - Aborted", "acas-param file found and being used", and the five
#     `display "User = " RDBMS-User` echoes at
#     [common/glbatchLD.cbl:L268-L272]. Screen output with no database effect,
#     excluded by Agent Action Plan sections 0.2.2 and 0.3.4. The abort
#     CONTROL FLOW those displays accompany is preserved: it becomes
#     `RdbmsParamError`, which stops the run before anything is written. The
#     credential echoes are not reproduced under any circumstance.
#
# RULES  (no user rules document exists for this project; these are the Agent
# Action Plan's own six, section 0.7.2)
#   R-1  satisfied structurally: `acas-get-params` is reimplemented, not
#        called. The imports of this module are `os`, `collections.abc`,
#        `dataclasses`, `typing` and one record module - no child process, no
#        foreign-function interface, no toolchain lookup, and no import path to
#        the compiled comparison oracle.
#   R-2  satisfied by type: all six values are `str`, as their `pic x(n)`
#        declarations make them. No numeric conversion occurs here at all, so
#        no binary-radix type can appear - the port stays text and the
#        data-access layer converts it the way the C interface does.
#   R-3  satisfied by scope: the six fields filled already exist in
#        [copybooks/wssystem.cob:L137-L144] and as columns of SYSTEM-REC, so no
#        field is added; no DDL, no SQL and no database contact occurs; no
#        accounting value is examined, let alone validated; and execution is a
#        single pass with no worker, pool or event loop. The width, blank and
#        whitespace checks apply to harness CONFIGURATION before any statement
#        with a COBOL counterpart runs, and each is a property of a frozen
#        carrier rather than a new business rule.
#   R-4  reproductions, each carrying its locator at the site: the six MOVEs in
#        their frozen order with their frozen receiving widths; the port
#        narrowing left to the data-access layer rather than "fixed" here; the
#        return codes kept as the frozen program's own; and no malformed value
#        silently repaired.
#   R-5  this footer, plus the per-symbol locators throughout and the
#        `locator` member every `ACAS_PARAM_CONTRACT` entry carries.
#   R-6  nothing here reads a clock, an entropy source, the current directory
#        or a process identifier; the environment is read in one pass in a
#        fixed order; and `env` can be supplied explicitly, so two runs given
#        the same mapping resolve byte-identically.
# -----------------------------------------------------------------------------
