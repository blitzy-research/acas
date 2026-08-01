"""The RDBMS connection contract: `acas-get-params` reimplemented natively.

`acas_posting.cli.rdbms_params` owns exactly one thing: it puts REAL connection
parameters into the six `RDBMS-*` fields of `SYSTEM-REC` before that record is
handed to a program module, so that the data-access layer connects to the
database the operator actually provisioned.

WHY THIS MODULE EXISTS AT ALL
=============================
Without it the migrated cycle cannot connect anywhere useful, and the reason is
worth stating precisely rather than in outline.

`acas_posting/dal/connection.py` takes its six connection values from
`SYSTEM-REC` and from nowhere else. It reproduces the six frozen `MOVE`
statements at [common/acas008.cbl:L558-L563]::

    move     RDBMS-DB-Name to DB-Schema
    move     RDBMS-User    to DB-UName
    move     RDBMS-Passwd  to DB-UPass
    move     RDBMS-Port    to DB-Port
    move     RDBMS-Host    to DB-Host
    move     RDBMS-Socket  to DB-Socket

and then hands `RDB-Data` to the driver. That is correct and is not changed
here. But `SYSTEM-REC` reaches the data-access layer through the CLI, which
builds it at the record layer's DECLARED DEFAULTS - and those defaults are the
copybook's own placeholder literals [copybooks/wssystem.cob:L137-L144]::

    05  RDBMS-DB-Name   pic x(12)   value "ACASDB"
    05  RDBMS-User      pic x(12)   value "ACAS-User"
    05  RDBMS-Passwd    pic x(12)   value "PaSsWoRd"
    05  RDBMS-Port      pic x(5)    value "3306"
    05  RDBMS-Host      pic x(32)   value spaces
    05  RDBMS-Socket    pic x(64)   value spaces

A run with those values connects as `ACAS-User` with the literal password
`PaSsWoRd` to whatever a blank host resolves to. The infrastructure, meanwhile,
publishes the real values as six environment variables that no module of the
shipped package read: `harness/docker-compose.yml` sets `ACAS_DB_HOST`,
`ACAS_DB_PORT`, `ACAS_DB_NAME`, `ACAS_DB_USER`, `ACAS_DB_PASSWORD` and
`ACAS_DB_SOCKET` for the `gnucobol` service. This module is the adapter that
closes that gap, and it is the ONLY place in the package that reads the
environment.

THIS IS A REPRODUCTION, NOT AN INVENTION
========================================
The COBOL has a named program for exactly this job, and this module is its
native counterpart: `common/acas-get-params.cbl`, whose own remarks state its
purpose at [common/acas-get-params.cbl:L19-L24] - "Used for ACAS v3.02 and
later to load up the rdbms params from acas.param file. For use if the acas
parameter file system.dat does not current hold settings for RDB processing".

Every `common/*LD.cbl` loader calls it and then performs six `MOVE` statements
into the very fields this module fills. [common/glbatchLD.cbl:L262-L267],
verbatim, and identically at [common/nominalLD.cbl:L248-L253],
[common/glpostingLD.cbl:L263-L268] and the rest of the family::

    move     WS-Host-Name      to RDBMS-Host
    move     WS-Implementation to RDBMS-User
    move     WS-Password       to RDBMS-Passwd
    move     WS-Base-Name      to RDBMS-DB-Name
    move     WS-Port-Number    to RDBMS-Port
    move     WS-Socket         to RDBMS-Socket

The six moves below are those six statements, in that order. The order is
preserved because rule R-6 makes statement ordering part of behaviour, and
because a reviewer must be able to diff this block against the frozen source
line for line.

THE SIX KEYWORDS ARE THE FROZEN PROGRAM'S OWN
=============================================
`acas-get-params` reads a `Keyword=value` line-sequential file and dispatches
on the FIRST SIX CHARACTERS of the keyword
[common/acas-get-params.cbl:L204-L220]::

    evaluate WS-RDB-Keyword (1:6)
             when     = "DBHOST"
                      move WS-RDB-Value to LK-Host-Name
             when     = "DBUSER"
                      move WS-RDB-Value to LK-Implementation
             when     = "DBPASS"
                      move WS-RDB-Value to LK-Password
             when     = "DBNAME"
                      move WS-RDB-Value to LK-Base-Name
             when     = "DBPORT"
                      move WS-RDB-Value to LK-Port-Number
             when     = "DBSOCK"
                      move WS-RDB-Value to LK-Socket
             when other
                      move 2 to LK-Return
                      goback
    end-evaluate

So the parameter set is closed at six, and each of the six environment
variables below is the container-native transport of one of those keywords.
Nothing is added: there is no seventh parameter, no alias and no default that
the frozen program does not have.

WHY THE ENVIRONMENT RATHER THAN THE FILE
========================================
`acas-get-params` reads `acas.param` from the CURRENT DIRECTORY and says so
[common/acas-get-params.cbl:L30] - "Uses Current directory only." That file
remains the COBOL side's own mechanism and the harness writes it for the
compiled oracle; nothing here reads, writes or requires it.

The migrated cycle takes the same six values from the environment instead,
because that is where the deployment contract publishes them and because a
current-directory file would make the run depend on where it was launched from,
which rule R-6 forbids. `harness/dump_tables.py` already reads the identical
six names, so the whole harness and the shipped package now agree on one
contract rather than two.

NO CLI OPTION IS ADDED
======================
Deliberately. `acas-get-params` takes its values from a source OUTSIDE the
command line, and so does this module. Three consequences, each of which is a
requirement rather than a preference:

  * `acas_posting/cli/args.py` gains no new option, so the closed list of two
    settable `SYSTEM-REC` fields it publishes stays closed;
  * a password never appears in `argv`, never in a process listing and never in
    a shell history - the same guarantee `harness/reset_db.sh` makes for the
    `mariadb` client, which passes the password through `MYSQL_PWD` and states
    that it "is never printed, never logged and never passed in argv"; and
  * the run date is untouched by this module. It continues to arrive ONLY as
    `--run-date` through the controlled clock: no date, no clock and no
    entropy source is read here (rule R-6).

WIDTH AWARENESS IS THE WHOLE POINT
==================================
A value the COBOL side cannot carry is worse than a value it rejects, because
`MOVE` truncates silently: the compiled oracle would then authenticate as a
different user, or against a different database, than the Python cycle - and
two runs made against different databases produce a diff that says nothing
about the migration. So each value is measured against the NARROWEST frozen
carrier it must traverse, and an over-long one is REFUSED rather than
truncated:

    keyword   variable            narrowest carrier                  limit
    -------   -----------------   --------------------------------   -----
    DBHOST    ACAS_DB_HOST        RDBMS-Host / DB-Host   pic x(32)      32
    DBUSER    ACAS_DB_USER        RDBMS-User / DB-UName  pic x(12)      12
    DBPASS    ACAS_DB_PASSWORD    RDBMS-Passwd/DB-UPass  pic x(12)      12
    DBNAME    ACAS_DB_NAME        RDBMS-DB-Name/DB-Schema pic x(12)     12
    DBPORT    ACAS_DB_PORT        Ws-Mysql-Port-Number   pic x(4)        4
    DBSOCK    ACAS_DB_SOCKET      RDBMS-Socket/DB-Socket pic x(64)      64

The port limit is FOUR, not five, and both paths agree on it: the fallback
program declares `LK-Port-Number pic x(4)`
[common/acas-get-params.cbl:L158], and every bridge narrows `DB-Port` into
`01 Ws-Mysql-Port-Number pic x(4)` [copybooks/mysql-variables.cpy:L91] with
`string DB-Port delimited by space` before the connect
[common/glpostingMT.cbl:L410-L413]. A five-character port therefore loses its
fifth character on the COBOL side no matter how it arrived, which
`acas_posting/dal/connection.py` reproduces exactly. Refusing it here stops the
two sides connecting to different ports.

A value containing whitespace is refused for the same reason and with the same
double citation: `acas-get-params` reads its value with
`unstring ... delimited by "=" or ":" or space`
[common/acas-get-params.cbl:L193-L199], so a space ENDS the value there; and
every bridge extracts each item with `delimited by space`
[common/glpostingMT.cbl:L394-L417], so a space ends it again. An embedded space
is thus silently dropped twice over.

WHAT IS NOT VALIDATED, AND WHY
==============================
The port is measured but NOT parsed. `acas_posting/dal/connection.py` sets out
the reasoning in full at its `_atoi` helper: the C interface the bridges link
converts the port with a bare `atoi`, which has no failure mode, so a malformed
port makes the compiled program connect somewhere else rather than report an
error. Raising on a non-numeric port would be a new validation (rule R-3) and a
defect fixed (rule R-4). This module therefore performs no digit test, no range
test and no reachability test, and it never contacts the database.

Nor is any ACCOUNTING value validated, examined or touched here. The checks
below apply exclusively to harness CONFIGURATION, before any statement with a
COBOL counterpart executes, and no record field acquires a rule it did not
have. That distinction is what keeps rule R-3 intact: a fixed-width transport
limit is a property of the frozen carriers, not a new business rule.

THE RETURN CODES ARE THE FROZEN PROGRAM'S OWN
=============================================
`acas-get-params` documents four outcomes at
[common/acas-get-params.cbl:L37-L42]::

    0 = Valid data read.
    8 = No file found.
    1 = No valid keyword terminator i.e., = or :
    2 = Invalid Keyword - keyword not expected.

Three of the four have an exact counterpart here and are carried on the raised
error, so a caller can distinguish "nothing was configured" from "what was
configured cannot work":

  * 0 - every value resolved and stored;
  * 8 - the parameter source is absent: not one of the six variables is
    present, which is this transport's "No file found";
  * 1 - the source is present but malformed: a required value is blank, or a
    value is too long for its frozen carrier, or a value contains whitespace.

Code 2 has NO counterpart and none is invented. It fires when the frozen reader
meets a keyword it does not expect, which cannot arise here: this module looks
up exactly six named variables and never enumerates the environment, so an
unrelated variable is not read, not parsed and not an error. Recorded in the
footer as an omission rather than shipped as an unreachable branch.

NO IMPORT-TIME SIDE EFFECTS
===========================
Importing this module binds names and evaluates a tuple of frozen dataclasses.
It reads no environment variable, opens no file, builds no parser, starts
nothing and cannot fail for an environmental reason. The environment is read
only when `resolve_rdbms_params` or `bind_rdbms_connection` is CALLED, and both
accept an explicit mapping so that a caller can supply one and touch the real
environment not at all.

NO CREDENTIAL IS EVER ECHOED
============================
No message this module raises contains a parameter VALUE. A length and a limit
are reported; the value is not, and `RdbmsParams` overrides its own
representation so that a traceback, a log line or a debugger cannot leak the
password.

THE RULES THAT BIND THIS FILE
=============================
`review_rules` reports NO user rules document for this project, so the binding
constraints are the Agent Action Plan's own six (section 0.7.2):

R-1 No COBOL at run time. `acas-get-params` is REIMPLEMENTED, not called: this
    module spawns no child process, loads no foreign library, reaches no
    GnuCOBOL toolchain and has no import path to the compiled oracle.
R-2 Zero binary floating point. All six values are `str`, exactly as their
    `pic x(n)` declarations make them. No numeric conversion happens here at
    all - the port stays text, and the data-access layer converts it the way
    the C interface does.
R-3 No added validation of accounting data, no added field, no schema change,
    no concurrency. The six fields filled here already exist in
    [copybooks/wssystem.cob:L137-L144] and in the `SYSTEM-REC` table; nothing
    reaches a database; and there is no worker, pool or event loop.
R-4 Legacy behaviour is reproduced, never corrected. The six `MOVE` statements
    keep their frozen order and their receiving widths, including the port's
    `pic x(4)` narrowing, and no malformed value is silently repaired.
R-5 Full traceability - see the footer.
R-6 Compiled behaviour is the tie-breaker. Nothing here reads a clock, an
    entropy source, the current directory or a process identifier, so two runs
    given the same environment resolve byte-identically.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from acas_posting.records.system_record import SystemRecord

__all__: Final[tuple[str, ...]] = (
    # ---- the frozen program's return codes --------------------------------
    "RDB_RETURN_OK",
    "RDB_RETURN_MALFORMED",
    "RDB_RETURN_NO_SOURCE",
    # ---- the closed six-parameter contract --------------------------------
    "ACAS_PARAM_CONTRACT",
    # ---- the resolved values, and the one failure they can produce --------
    "RdbmsParams",
    "RdbmsParamError",
    # ---- the reader, and THE adapter --------------------------------------
    "resolve_rdbms_params",
    "bind_rdbms_connection",
)


# =============================================================================
#  RETURN CODES  -  [common/acas-get-params.cbl:L37-L42]
# =============================================================================

#: "0 = Valid data read." Never raised; recorded so the set is complete and so
#: a caller can compare against it without transcribing the literal.
RDB_RETURN_OK: Final[int] = 0

#: "1 = No valid keyword terminator i.e., = or :" - the frozen code for "the
#: source is present but malformed". Carried on the error when a required value
#: is blank, when a value exceeds its frozen carrier, or when a value contains
#: whitespace that the frozen readers would silently drop.
RDB_RETURN_MALFORMED: Final[int] = 1

#: "8 = No file found." Carried on the error when NOT ONE of the six variables
#: is present, which is this transport's exact counterpart of a missing
#: `acas.param`.
RDB_RETURN_NO_SOURCE: Final[int] = 8


# =============================================================================
#  THE CLOSED SIX-PARAMETER CONTRACT
# =============================================================================


@dataclass(frozen=True, slots=True)
class _ParamSpec:
    """One of the six parameters, described end to end.

    Frozen and slotted: the contract is a fact about the frozen source, so
    nothing may mutate it and no instance needs a per-object dictionary.

    Attributes:
        keyword: The `acas.param` keyword the frozen reader dispatches on,
            matched on its first six characters
            [common/acas-get-params.cbl:L204-L220].
        variable: The environment variable that carries the same value in a
            container. Set for the `gnucobol` service by
            `harness/docker-compose.yml`, and read by `harness/dump_tables.py`.
        attribute: The `SYSTEM-REC` `System-Data-Block` attribute the value is
            moved into - the receiving item of one of the six frozen `MOVE`
            statements at [common/glbatchLD.cbl:L262-L267].
        carrier_width: The NARROWEST frozen carrier the value must traverse to
            reach the client library. A longer value is refused, because `MOVE`
            would truncate it silently and the two sides of the comparison
            would then connect differently.
        stored_width: The receiving `RDBMS-*` item's own `pic x(n)` width. The
            value is space-padded to exactly this many characters, which is
            what `MOVE` into an alphanumeric item does.
        required: Whether a blank value is a fault. Five are required; the
            socket is legitimately blank, which means "connect over TCP", and
            `harness/docker-compose.yml` sets `ACAS_DB_SOCKET: ""` explicitly.
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
#: [common/glbatchLD.cbl:L262-L267] - Host, User, Passwd, DB-Name, Port,
#: Socket. That is neither the declaration order of `SYSTEM-REC`
#: [copybooks/wssystem.cob:L137-L144] nor the order of the six moves in
#: [common/acas008.cbl:L558-L563]; it is the order of the statements this
#: module reproduces, and rule R-6 makes statement order part of behaviour.
#:
#: A tuple, so the contract cannot be extended at run time. Six entries, and
#: the frozen `evaluate` closes the set at six.
ACAS_PARAM_CONTRACT: Final[tuple[_ParamSpec, ...]] = (
    _ParamSpec(
        keyword="DBHOST",
        variable="ACAS_DB_HOST",
        attribute="rdbms_host",
        # `RDBMS-Host pic x(32)` [copybooks/wssystem.cob:L143] and
        # `DB-Host pic x(32)` [copybooks/wsfnctn.cob:L60] agree, so 32 is the
        # narrowest carrier. The fallback program's `LK-Host-Name` is x(64)
        # [common/acas-get-params.cbl:L153], i.e. wider, so it does not bind.
        carrier_width=32,
        stored_width=32,
        required=True,
        locator="copybooks/wssystem.cob:L143",
    ),
    _ParamSpec(
        keyword="DBUSER",
        variable="ACAS_DB_USER",
        attribute="rdbms_user",
        # `RDBMS-User pic x(12)` [copybooks/wssystem.cob:L138] narrowing from
        # `LK-Implementation pic x(64)` [common/acas-get-params.cbl:L154-L155].
        carrier_width=12,
        stored_width=12,
        required=True,
        locator="copybooks/wssystem.cob:L138",
    ),
    _ParamSpec(
        keyword="DBPASS",
        variable="ACAS_DB_PASSWORD",
        attribute="rdbms_passwd",
        # `RDBMS-Passwd pic x(12)` [copybooks/wssystem.cob:L139] narrowing from
        # `LK-Password pic x(64)` [common/acas-get-params.cbl:L156].
        carrier_width=12,
        stored_width=12,
        required=True,
        locator="copybooks/wssystem.cob:L139",
    ),
    _ParamSpec(
        keyword="DBNAME",
        variable="ACAS_DB_NAME",
        attribute="rdbms_db_name",
        # `RDBMS-DB-Name pic x(12)` [copybooks/wssystem.cob:L137] narrowing
        # from `LK-Base-Name pic x(64)` [common/acas-get-params.cbl:L157].
        carrier_width=12,
        stored_width=12,
        required=True,
        locator="copybooks/wssystem.cob:L137",
    ),
    _ParamSpec(
        keyword="DBPORT",
        variable="ACAS_DB_PORT",
        attribute="rdbms_port",
        # FOUR, not five. `LK-Port-Number pic x(4)`
        # [common/acas-get-params.cbl:L158] on the fallback path, and
        # `01 Ws-Mysql-Port-Number pic x(4)`
        # [copybooks/mysql-variables.cpy:L91] on every bridge path
        # [common/glpostingMT.cbl:L410-L413]. The receiving `RDBMS-Port` is
        # x(5) [copybooks/wssystem.cob:L142], so the value is STORED at five
        # and CARRIED at four - which is the narrowing
        # `acas_posting/dal/connection.py` reproduces.
        carrier_width=4,
        stored_width=5,
        required=True,
        locator="copybooks/wssystem.cob:L142",
    ),
    _ParamSpec(
        keyword="DBSOCK",
        variable="ACAS_DB_SOCKET",
        attribute="rdbms_socket",
        # `RDBMS-Socket pic x(64)` [copybooks/wssystem.cob:L144] and
        # `DB-Socket pic x(64)` [copybooks/wsfnctn.cob:L61] agree at 64, as
        # does `LK-Socket` [common/acas-get-params.cbl:L159].
        carrier_width=64,
        stored_width=64,
        required=False,
        locator="copybooks/wssystem.cob:L144",
    ),
)


# =============================================================================
#  THE ONE FAILURE THIS MODULE CAN PRODUCE
# =============================================================================


class RdbmsParamError(ValueError):
    """The connection contract is absent or unusable, so the run cannot start.

    Subclasses `ValueError` because a caller naturally expects one when a
    supplied value is wrong - the convention `acas_posting/dictionary/loader.py`
    and `harness/dump_tables.py` both follow.

    FAIL FAST, AND BEFORE ANYTHING IS TOUCHED. Raised while the linkage is
    still being bound: no database has been contacted, no file opened and no
    program module entered, so a run that raises this has changed nothing.

    NO VALUE IS EVER CARRIED IN THE MESSAGE. A length and a limit are named;
    the offending value is not, so a traceback cannot leak a credential.

    Attributes:
        return_code: The frozen counterpart from
            [common/acas-get-params.cbl:L37-L42] - `RDB_RETURN_NO_SOURCE` (8)
            when the contract is absent entirely, `RDB_RETURN_MALFORMED` (1)
            when it is present but cannot work. A caller that wants to tell
            "not configured" from "misconfigured" reads this rather than
            parsing the message.
    """

    def __init__(self, return_code: int, message: str) -> None:
        """Build the error with its frozen return code.

        Args:
            return_code: `RDB_RETURN_NO_SOURCE` or `RDB_RETURN_MALFORMED`.
            message: What is wrong and what to do about it. Must not contain a
                parameter value.
        """
        super().__init__(message)
        self.return_code: int = return_code


# =============================================================================
#  THE RESOLVED VALUES  -  `01 LK-RDB-Vars` [common/acas-get-params.cbl:L152]
# =============================================================================


@dataclass(frozen=True, slots=True, repr=False)
class RdbmsParams:
    """The six resolved values, as `LK-RDB-Vars` holds them.

    Mirrors the frozen linkage group at
    [common/acas-get-params.cbl:L152-L159], member for member and in its
    declaration order::

        01  LK-RDB-Vars                      value spaces.
            03  LK-Host-Name    pic x(64).
            03  LK-Implementation
                                pic x(64).
            03  LK-Password     pic x(64).
            03  LK-Base-Name    pic x(64).
            03  LK-Port-Number  pic x(4).
            03  LK-Socket       pic x(64).

    Frozen, because a resolved contract is a fact about the environment as it
    was read; slotted, because there is exactly one instance per run and it
    needs no per-object dictionary.

    THE VALUES HERE ARE UNPADDED. Padding to each receiving item's own
    `pic x(n)` width is a `MOVE` property and happens in
    `bind_rdbms_connection`, so this class holds what the environment supplied
    and nothing else.

    `repr` IS OVERRIDDEN so that the password cannot leak into a traceback, a
    log line or a debugger session.

    Attributes:
        host: `DBHOST` -> `LK-Host-Name` -> `RDBMS-Host`.
        user: `DBUSER` -> `LK-Implementation` -> `RDBMS-User`.
        password: `DBPASS` -> `LK-Password` -> `RDBMS-Passwd`. NEVER logged.
        database: `DBNAME` -> `LK-Base-Name` -> `RDBMS-DB-Name`.
        port: `DBPORT` -> `LK-Port-Number` -> `RDBMS-Port`. Text, not an
            `int`: the data-access layer converts it the way the C interface
            does, and converting it here would discard the frozen narrowing.
        socket: `DBSOCK` -> `LK-Socket` -> `RDBMS-Socket`. Blank means
            "connect over TCP".
    """

    host: str
    user: str
    password: str
    database: str
    port: str
    socket: str

    def __repr__(self) -> str:
        """Describe the parameters WITHOUT the password.

        The password is replaced by a fixed marker rather than by its length,
        because a length is itself information about a credential.

        Returns:
            A representation safe to write to a log or a traceback.
        """
        return (
            f"{type(self).__name__}(host={self.host!r}, user={self.user!r}, "
            f"password=<redacted>, database={self.database!r}, "
            f"port={self.port!r}, socket={self.socket!r})"
        )


# =============================================================================
#  `MOVE` INTO AN ALPHANUMERIC ITEM
# =============================================================================


def _pic_x(text: str, width: int) -> str:
    """Fit a value to an alphanumeric picture of `width` characters.

    COBOL `MOVE` into a `pic x(n)` item truncates on the right and pads on the
    right with spaces. Reproduced locally, mirroring the same private helper in
    `acas_posting/dal/connection.py` and `acas_posting/dal/status.py`, because
    this layer may not import `acas_posting/cobol/move.py`: the Agent Action
    Plan's import table (section 0.4.3) does not permit a `cli` module to reach
    the `cobol` package.

    Truncation is unreachable for every value that gets this far - the caller
    has already refused anything longer than its carrier - so in practice this
    only ever pads. It is written as the full `MOVE` rule anyway, because a
    helper that implemented half of a COBOL verb would be a trap for the next
    reader.

    Args:
        text: The sending value.
        width: The receiving item's declared character count.

    Returns:
        Exactly `width` characters.
    """
    return text[:width].ljust(width)


# =============================================================================
#  THE READER  -  `acas-get-params` over the environment
# =============================================================================


def resolve_rdbms_params(
    env: Mapping[str, str] | None = None,
) -> RdbmsParams:
    """Read the six connection parameters, as `acas-get-params` reads them.

    Reproduces `common/acas-get-params.cbl` over the environment transport:
    the same six keywords, the same closed set, the same return codes, and the
    same "absent source" versus "malformed source" distinction. Nothing is
    defaulted, guessed or repaired - a contract that cannot work is refused so
    that the run stops before it can write a row against the wrong database.

    THE ENVIRONMENT IS READ ONCE, HERE. Every value is taken from `env` in one
    pass, in the frozen `MOVE` order, so two calls given the same mapping
    resolve identically (rule R-6). Nothing else in the shipped package reads
    the environment.

    Args:
        env: The mapping to resolve from. `os.environ` when omitted, which is
            the case in a real run; a test or an orchestrator passes an
            explicit mapping and touches the real environment not at all.

    Returns:
        The six resolved values, unpadded.

    Raises:
        RdbmsParamError: With `return_code` `RDB_RETURN_NO_SOURCE` (8) when not
            one of the six variables is present - this transport's "No file
            found" [common/acas-get-params.cbl:L39]. With
            `RDB_RETURN_MALFORMED` (1) when the contract is present but a
            required value is blank, a value is longer than its frozen carrier,
            or a value contains whitespace the frozen readers would drop.
    """
    source: Mapping[str, str] = os.environ if env is None else env

    # `call "CBL_CHECK_FILE_EXIST" using "acas.param"` / `if Return-Code not =
    # zero / move 8 to LK-Return / goback` [common/acas-get-params.cbl:L174-L178]
    # is "is there a source at all?". Its counterpart is "is any of the six
    # variables present?" - absence of the WHOLE contract, not of one member,
    # because one missing member is a malformed source and gets code 1 below.
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

    resolved: dict[str, str] = {}
    for spec in ACAS_PARAM_CONTRACT:
        value = source.get(spec.variable, "")

        # A required parameter must be present AND non-blank. The frozen reader
        # cannot express this - a missing line simply leaves `LK-RDB-Vars` at
        # its `value spaces` [common/acas-get-params.cbl:L152] - and the
        # consequence there is the same silent misconnection this module exists
        # to prevent, so an incomplete source is malformed rather than usable.
        if spec.required and not value:
            raise RdbmsParamError(
                RDB_RETURN_MALFORMED,
                f"{spec.variable} is not set, or is empty, but it carries the "
                f"{spec.keyword} parameter that the frozen reader moves into "
                f"{spec.attribute} [{spec.locator}]. Five of the six are "
                f"required; only ACAS_DB_SOCKET may be empty, which means "
                f"connect over TCP. harness/docker-compose.yml sets all six "
                f"for the gnucobol service.",
            )

        # Whitespace ends the value TWICE on the COBOL side: at
        # [common/acas-get-params.cbl:L193-L199], where the UNSTRING is
        # `delimited by "=" or ":" or space`; and again in every bridge, where
        # each item is extracted with `delimited by space`
        # [common/glpostingMT.cbl:L394-L417]. So a value with a space in it,
        # or with padding around it, is silently shortened rather than used.
        if any(character.isspace() for character in value):
            raise RdbmsParamError(
                RDB_RETURN_MALFORMED,
                f"{spec.variable} contains whitespace, which the COBOL side "
                f"silently drops: the frozen reader UNSTRINGs its value "
                f"'delimited by \"=\" or \":\" or space' "
                f"[common/acas-get-params.cbl:L193-L199], and every bridge "
                f"then extracts the item 'delimited by space' "
                f"[common/glpostingMT.cbl:L394-L417]. The compiled oracle "
                f"would therefore use a shorter value than this run does. Use "
                f"a value with no space, tab or newline in it. (The value "
                f"itself is deliberately not shown.)",
            )

        # The width gate. `MOVE` truncates on the right without complaint, so
        # a longer value would make the compiled oracle authenticate as a
        # different user, or against a different database or port, than this
        # run - and a diff between two differently-connected runs says nothing
        # about the migration. Only the LENGTH and the LIMIT are reported.
        if len(value) > spec.carrier_width:
            raise RdbmsParamError(
                RDB_RETURN_MALFORMED,
                f"{spec.variable} is {len(value)} characters long but the "
                f"COBOL side can carry at most {spec.carrier_width}: the "
                f"value has to reach the client library through "
                f"{spec.attribute} [{spec.locator}] and the RDB-Data group "
                f"[copybooks/wsfnctn.cob:L56-L62]"
                + (
                    ", narrowing again into "
                    "`01 Ws-Mysql-Port-Number pic x(4)` "
                    "[copybooks/mysql-variables.cpy:L91] before the connect"
                    if spec.keyword == "DBPORT"
                    else ""
                )
                + f". MOVE would truncate it silently, so it is refused "
                f"instead. Both sides of the comparison must use the same "
                f"credentials, so choose a value the frozen carriers can "
                f"hold. (The value itself is deliberately not shown.)",
            )

        resolved[spec.keyword] = value

    return RdbmsParams(
        host=resolved["DBHOST"],
        user=resolved["DBUSER"],
        password=resolved["DBPASS"],
        database=resolved["DBNAME"],
        port=resolved["DBPORT"],
        socket=resolved["DBSOCK"],
    )


# =============================================================================
#  THE ADAPTER  -  the six `MOVE` statements [common/glbatchLD.cbl:L262-L267]
# =============================================================================


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
    not: the CLI builds `SYSTEM-REC` at the record layer's declared defaults
    and never loads it from the store (see `Q-CLI-SYSREC-LOAD` in
    `acas_posting/cli/args.py`), so `RDBMS-DB-Name` is never spaces - it is the
    literal "ACASDB" [copybooks/wssystem.cob:L137] - and a literal
    reproduction of the guard would skip the load on every single run and leave
    the placeholder password in place. The guard's INTENT is "load them if they
    are not already set", and under the declared defaults they are never set,
    so the load always runs. Recorded as a documented divergence in this
    module's footer.

    Args:
        system_record: The record to fill. MUTATED IN PLACE, which is what the
            frozen `MOVE` statements do to their own copy, and which keeps the
            caller holding the one record the linkage will carry.
        env: The mapping to resolve from, passed through to
            `resolve_rdbms_params`. `os.environ` when omitted.

    Returns:
        The resolved parameters, so a caller can record WHICH endpoint a run
        used without re-reading the environment. Its representation redacts the
        password.

    Raises:
        RdbmsParamError: The contract is absent or unusable. Raised by
            `resolve_rdbms_params` BEFORE any field is written, so a failed
            call leaves `system_record` exactly as it found it.
    """
    parameters = resolve_rdbms_params(env)

    # Resolve fully before writing anything, so the record is never left half
    # filled: the reader above raises before this point or not at all.
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
    # `SystemRecord.system_data_block`. The frozen MOVEs name them unqualified
    # because they are unique within the program; Python needs the group path.
    system_data_block = system_record.system_data_block

    # The six statements, in the frozen source's own order. One iteration per
    # COBOL statement, so this block diffs against
    # [common/glbatchLD.cbl:L262-L267] entry for entry.
    for spec in ACAS_PARAM_CONTRACT:
        setattr(
            system_data_block,
            spec.attribute,
            _pic_x(values[spec.keyword], spec.stored_width),
        )

    return parameters


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
