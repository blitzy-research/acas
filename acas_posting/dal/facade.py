r"""The single doorway between the posting programs and the file handlers.

Publishes the twelve-verb vocabulary - Open, Open-Input, Open-Output, Open-Extend,
Close, Start, Read-Next, Read-Indexed, Write, Rewrite, Delete, Delete-All - for
every entity the migrated cycle reaches, and dispatches each verb to the handler
module that owns the table.

TWO NAMING CONVENTIONS OVER ONE IMPLEMENTATION. The General, Sales and Purchase
programs name their facade paragraphs after the ENTITY
[copybooks/Proc-ACAS-FH-Calls.cob], while the IRS side names them after the
HANDLER [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]. Both alias sets are published
here so a reader following either convention finds a correspondingly named
function, and the logic exists once.

The two conventions also DIFFER IN BEHAVIOUR, and that difference is reproduced
rather than harmonised: the IRS convention wraps each handler call in a
per-handler error check that reports a handler-specific message and, on an
unrecoverable open failure, returns from the program outright
[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]. The General/Sales/Purchase
convention has no such paragraph at all - its callers test the reply inline - so
a caller's error handling depends on which alias set it used.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from types import MappingProxyType
from typing import Final, NamedTuple, NoReturn

from acas_posting.dal import acas000_system
from acas_posting.dal import acas005_gl_nominal
from acas_posting.dal import acas006_gl_posting
from acas_posting.dal import acas007_gl_batch
from acas_posting.dal import acas008_spl_posting
from acas_posting.dal import acas012_sales
from acas_posting.dal import acas013_value
from acas_posting.dal import acas015_analysis
from acas_posting.dal import acas016_invoice
from acas_posting.dal import acas019_otm3
from acas_posting.dal import acas022_purch
from acas_posting.dal import acas026_pinvoice
from acas_posting.dal import acas029_otm5
from acas_posting.dal import acasirsub1_irs_nominal
from acas_posting.dal import acasirsub3_irs_dflt
from acas_posting.dal import acasirsub4_irs_posting
from acas_posting.dal import acasirsub5_irs_final
from acas_posting.dal import connection as _connection
from acas_posting.dal import cursor_state as _cursor_state
from acas_posting.dal.status import AccessType, FileFunction, FsReply
# `redact_for_log` is deliberately NOT imported. It escapes control characters in a
# driver message rather than removing its content, so it cannot make `SQL-Msg` safe
# to log; `Open-Error-Continued` reports the typed fields instead. See the
# safe-event schema in `acas_posting/dal/status.py`.
from acas_posting.dal.status import log_handler_failure
from acas_posting.records.file_access import FileAccess
from acas_posting.records.file_defs import FileDefs

_LOG: Final[logging.Logger] = logging.getLogger(__name__)


# The vocabulary this module does NOT own The function codes and access types are
# declared once, at [copybooks/wsfnctn.cob:L88-L116], and ``dal.status`` owns their
# Python form.

#: The value the non-open verbs move into ``Access-Type``. It is NOT one of the nine
#: declared condition names, so it cannot be spelled with
#: :class:`~acas_posting.dal.status.AccessType`.
ACCESS_TYPE_LOGGING_RESET: Final[int] = 0

PRIMARY_FILE_KEY_NO: Final[int] = 1

# The three fields a verb paragraph moves into, named as the copybook names them so that
# a plan below reads as its COBOL source reads.
_FILE_FUNCTION: Final[str] = "File-Function"
_ACCESS_TYPE: Final[str] = "Access-Type"
_FILE_KEY_NO: Final[str] = "File-Key-No"

#: Published verbs whose handler refuses the function unconditionally at entry, taken
#: from the data ``dal.cursor_state`` already derives from the handlers.
ALWAYS_REFUSED_BY_HANDLER: Final[Mapping[str, object]] = (
    _cursor_state.HANDLER_REJECTED_FUNCTIONS
)


class StatusPair(NamedTuple):
    """The ``(FS-Reply, WE-Error)`` pair a facade verb yields.

    Both fields are read back out of ``File-Access`` after the handler has run, because
    that is where COBOL puts them [copybooks/wsfnctn.cob:L23-L25]. The pair is a
    convenience for the caller and never the authority.
    """

    fs_reply: int
    we_error: int


class FacadeError(Exception):
    """Base for the two conditions this module raises."""


class FacadeGoback(FacadeError):
    """Reproduces the ``goback.`` that ends the shared abort paragraph.

    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364] is a ``goback``, which returns from
    the PROGRAM rather than from the section - Agent Action Plan section 0.6.5's
    "returns from the program outright".
    """


class UnsupportedEntityError(FacadeError):
    """Raised by the eight entities whose bridges and tables are out of scope.

    This is not a stub and not a defect: it is the boundary of the migration stated in
    the one place a caller can observe it.
    """


@dataclass(frozen=True, slots=True)
class FacadeContext:
    """The linkage a ``perform`` of a facade verb needs.

    Every dispatch paragraph in both copybooks passes the same five things, e.g.
    [copybooks/Proc-ACAS-FH-Calls.cob:L51-L57]::

        call "acas007" using System-Record
                             WS-Batch-Record
                             File-Access
                             File-Defs
                             ACAS-DAL-Common-Data

    so this carries exactly those five and nothing else. It owns no connection
    and no cursor - those belong to ``dal.connection`` and ``dal.cursor_state``.

    ``record`` is the entity work area, whichever one the paragraph names. It is
    passed through opaquely and never inspected here, which is why it is typed
    ``object``: the entity record classes belong to the handler modules, and the
    layering forbids this module from importing them.

    ``dal_common`` is ``ACAS-DAL-Common-Data``. It is likewise ``object``,
    because its class lives in a records module this layer may not import.

    ``options`` has no COBOL counterpart and exists only because several handler
    modules take keyword-only parameters that COBOL had no way to express - a
    transport-security policy, a cursor-state table, a per-handler context.
    Whatever a caller puts here is forwarded verbatim to that handler's
    ``dispatch``; an empty mapping forwards nothing. It carries no accounting
    value and nothing here reads it.

    IT IS ALSO THE ONE CHANNEL BY WHICH A SECURITY POLICY REACHES A HANDLER,
    and that makes an empty mapping a decision rather than an absence. Every
    handler that opens a connection declares ``transport: TransportSecurity |
    None = None`` and forwards it to ``connection.mysql_1000_open``, whose
    ``_require_permitted_connection`` resolves ``None`` AGAINST THE INSTALLED
    PROCESS POLICY rather than against a permission of its own. Under the
    exact-parity default that policy reports an unencrypted non-local hop at
    WARNING and connects, exactly as the compiled open does (rule R-3); under an
    explicitly hardened policy it refuses unless a certificate authority is
    supplied or ``isolated_oracle=True`` is declared. So a caller that leaves
    ``options`` empty gets the SAME answer for every handler, and a caller that
    must override it for one verb states it once -
    ``options={"transport": TransportSecurity(...)}`` - and this context carries
    it to whichever handler the verb dispatches to.

    That uniformity is the point. Were ONE handler to default itself permissive
    while the other nineteen took the process policy, the policy would depend on
    which entity a program happened to touch rather than on what the operator had
    declared (CWE-319, CWE-295). Nothing here inspects or
    rewrites the mapping: the enforcement lives in ``dal/connection.py`` and the
    declaration lives with the caller, and this field is only the wire between
    them. Forwarding is by keyword, so a handler that does not accept a given key
    raises ``TypeError`` at the call rather than silently ignoring a policy the
    caller believed was in force.
    """

    system: object
    record: object
    file_access: FileAccess
    file_defs: FileDefs | None = None
    dal_common: object = None
    options: Mapping[str, object] = field(default_factory=dict)


class _Plan(NamedTuple):
    """One facade verb paragraph, transcribed as data.

    ``moves`` lists the paragraph's assignments in SOURCE ORDER, which differs between
    paragraphs and is therefore transcribed rather than normalised.
    """

    paragraph: str
    lines: str
    handler: str
    moves: tuple[tuple[str, int], ...]
    check: str | None = None
    check_first: bool = False


def _apply(file_access: FileAccess, target: str, value: int) -> None:
    """Perform one ``move``/``set`` of a verb paragraph."""
    if target is _FILE_FUNCTION:
        file_access.file_function = value
    elif target is _ACCESS_TYPE:
        file_access.access_type = value
    else:
        file_access.logging_data.file_key_no = value


def _perform(ctx: FacadeContext, plan: _Plan) -> StatusPair:
    """Run one facade verb paragraph, whichever vocabulary named it.

    The steps are the copybook's steps, in the copybook's order: apply the paragraph's
    moves, perform the dispatch paragraph, and read the status back out of the linkage.
    """
    file_access = ctx.file_access
    for target, value in plan.moves:
        _apply(file_access, target, value)

    # [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102] - ``acas000-Open-Input``
    # performs its error check BEFORE the dispatch, alone among all 42 verb paragraphs.
    if plan.check is not None and plan.check_first:
        _CHECKS[plan.check](ctx)

    _DISPATCH[plan.handler](ctx)

    if plan.check is not None and not plan.check_first:
        _CHECKS[plan.check](ctx)

    return StatusPair(file_access.fs_reply, file_access.we_error)


@lru_cache(maxsize=None)
def _keyword_extras_accepted_by(target: Callable[..., object]) -> frozenset[str]:
    """The keyword-only parameter names ``target`` declares.

    Read from the signature rather than transcribed into a table, because the
    seventeen handler modules do NOT agree on their keyword-only extras - eleven
    take ``transport``, two of those also take ``states``, three also take
    ``allow_frozen_placeholder_credentials``, ``acas022_purch`` takes
    ``purchase_file``, ``acas026_pinvoice`` takes ``context``, and six take none
    at all. A transcribed table would be a second opinion that could drift from
    the first; a signature cannot.

    Cached because the answer is fixed for the life of the process and this is
    consulted once per facade verb.

    Args:
        target: the handler's ``dispatch`` function.

    Returns:
        Its keyword-only parameter names.
    """
    return frozenset(
        name
        for name, parameter in inspect.signature(target).parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY
    )


def _forward(
    ctx: FacadeContext, target: Callable[..., object]
) -> Mapping[str, object]:
    """The keyword-only extras to forward to ``target``, projected from ``options``.

    WHY THIS PROJECTS RATHER THAN FORWARDING WHOLESALE. ``options`` is the one
    channel by which a caller's transport-security policy reaches a handler, and
    a caller states that policy ONCE for a whole run - it cannot reasonably know
    which of the seventeen handlers a given verb dispatches to, nor which of them
    declares which keyword. Forwarding the mapping wholesale made a single
    uniform declaration impossible: ``options={"transport": ...}`` reached
    ``acas006`` happily and raised ``TypeError`` from ``acas000``, so the only
    way to avoid the error was to leave ``options`` empty everywhere and let each
    handler decide its own transport policy - which is exactly how one handler
    came to default itself permissive while the other nineteen failed closed
    (CWE-319, CWE-295).

    Projecting makes the uniform declaration work: the caller says it once, every
    handler that can honour it receives it, and a handler that cannot is called
    exactly as before. NOTHING IS SILENTLY DISCARDED - a key that no handler on
    this path accepts is reported at WARNING, so a caller who believed a policy
    was in force and was wrong finds out. That report is a log record with no
    database effect and no control-flow effect, which is the whole of the test
    AAP section 0.3.4 sets for a diagnostic.

    A handler that DOES declare ``transport`` and is not given one is unaffected:
    its own default is ``None``, which ``connection.py`` resolves to the INSTALLED
    PROCESS POLICY rather than to a permission of its own. An omitted per-call
    declaration therefore cannot quietly widen what the deployment declared, and
    whatever the resolved policy permits is reported at WARNING on the open.

    Args:
        ctx: the linkage this verb was performed with.
        target: the handler ``dispatch`` about to be called.

    Returns:
        The subset of ``ctx.options`` that ``target`` accepts. An empty mapping
        when the caller supplied none, which is the ordinary case and forwards
        nothing at all.
    """
    options = ctx.options
    if not options:
        return {}

    accepted = _keyword_extras_accepted_by(target)
    unhonoured = [name for name in options if name not in accepted]
    if unhonoured:
        # `%r` on the sorted NAMES only. The values are policy objects and record
        # areas - a transport policy carries certificate paths - so the message
        # says which declarations could not be honoured and never what they held
        # (CWE-532).
        _LOG.warning(
            "facade: %s accepts no keyword extra named %r, so the caller's "
            "declaration(s) of that name are not in force for this verb; the "
            "handler's own default applies, which for a transport policy means "
            "the installed process policy governs the open",
            getattr(target, "__module__", "the handler"),
            sorted(unhonoured),
        )

    return {name: value for name, value in options.items() if name in accepted}


# ---------------------------------------------------------------------------
# THE ONE SECURITY-POLICY CONTRACT
# ---------------------------------------------------------------------------
#
# `FacadeContext.options` carries a policy to the eleven handlers that declare a
# keyword-only `transport` on their `dispatch`. Two more accept one ONLY through
# a module-level declaration function of their own - the equivalent of setting a
# sub-program's WORKING-STORAGE before the first `CALL`, which is exactly what
# their COBOL originals do with the six `RDBMS-*` values
# [common/acas008.cbl:L558-L563] - and four accept none at all, so those four
# always open under the INSTALLED PROCESS POLICY with no per-call declaration of
# their own.
#
# Three mechanisms is two too many for a caller to have to know about, and a
# caller who knows about none of them is the caller whose policy silently fails
# to apply. So this layer publishes ONE door. It is the right layer for it:
# `dal/facade.py` is already the only path from any caller to any handler, and
# the AAP's per-directory import table (section 0.4.3) names it as the DAL module
# the layer above may import.
#
# NOT GLOBAL MUTABLE STATE INVENTED BY THE MIGRATION. Each handler's declaration
# slot already exists, because each COBOL sub-program already has working storage
# that outlives one `CALL`; this function does not add a slot, it gives the
# module-level routes a single, greppable caller.


#: The handlers whose transport policy is settable ONLY through a module-level
#: declaration, each paired with the callable that sets it. Kept as data so the
#: set is greppable and so adding a handler is one line rather than a branch.
#:
#: The three spellings are the handler modules' own and are deliberately not
#: renamed: `acas000_system.configure_transport` takes the policy positionally,
#: `acas007_gl_batch.declare_connection_policy` takes it by keyword and also
#: takes the credential declaration, and
#: `acasirsub1_irs_nominal.reset_bridge_storage` takes only the transport and
#: additionally resets the rest of its working storage - which is why it is
#: called here rather than a narrower setter being invented for it.
#: `acas022_purch` publishes `reset_bridge_state()` with no policy parameter at
#: all, so it is absent from this table: it has no slot to set, and its
#: `dispatch` accepts `transport` instead, which the options channel reaches.
_MODULE_LEVEL_POLICY_SETTERS: Final[
    tuple[tuple[str, Callable[..., None]], ...]
] = (
    ("acas000_system", acas000_system.configure_transport),
    ("acas007_gl_batch", acas007_gl_batch.declare_connection_policy),
    ("acasirsub1_irs_nominal", acasirsub1_irs_nominal.reset_bridge_storage),
)


def declare_connection_policy(
    *,
    transport: _connection.TransportSecurity | None = None,
    allow_frozen_placeholder_credentials: bool = False,
) -> None:
    """Declare, once, how every handler may reach the database.

    THE COMPANION OF ``FacadeContext.options``, NOT A SUBSTITUTE FOR IT. Between
    them they cover every handler that can be told a policy at all:

    * eleven handlers declare a keyword-only ``transport`` on their ``dispatch``
      and are reached by ``options={"transport": ...}`` on the context;
    * ``acas000_system`` and ``acasirsub1_irs_nominal`` are reached only through
      a module-level declaration and are reached by this function;
    * ``acas007_gl_batch`` supports both routes for compatibility;
    * ``acas005_gl_nominal``, ``acas012_sales``, ``acas026_pinvoice`` and
      ``acasirsub4_irs_posting`` publish neither, so those four open under the
      INSTALLED PROCESS POLICY alone. That is a LIMITATION AND IT IS RECORDED AS
      ONE: a declaration meant for one of those four cannot be made per call, so
      it has to be installed process-wide - and where the installed policy is the
      hardened one, its refusal surfaces as the same ``(99, 911)`` the frozen open
      produces on any connect failure.

    A process boundary should call this once and ALSO pass the same policy on
    every context it builds; the two together are the whole contract. Calling
    this with no arguments is meaningful: it declares no TLS material and no
    isolated-oracle claim, which is the EXACT-PARITY declaration.

    Args:
        transport: the policy. ``None`` means the caller declares nothing, which
            ``connection._require_permitted_connection`` resolves against the
            INSTALLED PROCESS POLICY. Under the exact-parity default that policy
            reports an unencrypted non-local hop at WARNING and connects, exactly
            as the compiled open does (rule R-3); under an explicitly hardened
            policy it refuses unless a certificate authority is supplied or
            ``isolated_oracle=True`` is declared.
        allow_frozen_placeholder_credentials: whether the shipped placeholders of
            [copybooks/wssystem.cob:L138-L139] are declared intended. ``False``,
            the default, leaves them REPORTED at WARNING - and refused only where
            the installed policy sets
            ``require_declared_placeholder_credentials``.

    Returns:
        None. Every effect is on the named handlers' own declaration slots.
    """
    for module_name, setter in _MODULE_LEVEL_POLICY_SETTERS:
        parameters = inspect.signature(setter).parameters
        extras: dict[str, object] = {}
        if "allow_frozen_placeholder_credentials" in parameters:
            extras["allow_frozen_placeholder_credentials"] = (
                allow_frozen_placeholder_credentials
            )
        if parameters["transport"].kind is inspect.Parameter.KEYWORD_ONLY:
            setter(transport=transport, **extras)
        else:
            setter(transport, **extras)
        _LOG.debug(
            "facade: connection policy declared to %s (server verified=%s, "
            "isolated-oracle declared=%s)",
            module_name,
            bool(transport and transport.verifies_the_server()),
            bool(transport and transport.isolated_oracle),
        )


# The dispatch layer - one function per dispatch paragraph A verb paragraph sets state
# and then performs a dispatch paragraph.


def _dispatch_acas000_entity(ctx: FacadeContext) -> None:
    """``acas000`` passing ``System-Record``.

    This paragraph issues no ``move ... to File-Key-No``, so the caller's key survives
    into the handler. That is what makes the System entity a multi-key dispatcher, and
    it is the second way the two conventions disagree about ``acas000``.
    """
    acas000_system.dispatch(
        ctx.system,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas000_system.dispatch),
    )


def _dispatch_acas000_handler(ctx: FacadeContext) -> None:
    """``acas000`` passing ``WS-System-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas000_system.dispatch(
        ctx.system,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas000_system.dispatch),
    )


def _dispatch_acas004(ctx: FacadeContext) -> None:
    """``acas004`` passing ``WS-Invoice-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas004 serves the out-of-scope entity SLautogen. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas005(ctx: FacadeContext) -> None:
    """``acas005`` passing ``WS-Ledger-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas005_gl_nominal.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas005_gl_nominal.dispatch),
    )


def _dispatch_acas006(ctx: FacadeContext) -> None:
    """``acas006`` passing ``WS-Posting-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas006_gl_posting.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas006_gl_posting.dispatch),
    )


def _dispatch_acas007(ctx: FacadeContext) -> None:
    """``acas007`` passing ``WS-Batch-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas007_gl_batch.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas007_gl_batch.dispatch),
    )


def _dispatch_acas008(ctx: FacadeContext) -> None:
    """``acas008`` passing ``WS-IRS-Posting-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas008_spl_posting.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas008_spl_posting.dispatch),
    )


def _dispatch_acas010(ctx: FacadeContext) -> None:
    """``acas010`` passing ``WS-Stock-Audit-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas010 serves the out-of-scope entity Stock-Audit. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas011(ctx: FacadeContext) -> None:
    """``acas011`` passing ``WS-Stock-Record``."""
    raise UnsupportedEntityError(
        "acas011 serves the out-of-scope entity Stock. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas012(ctx: FacadeContext) -> None:
    """``acas012`` passing ``WS-Sales-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas012_sales.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas012_sales.dispatch),
    )


def _dispatch_acas013(ctx: FacadeContext) -> None:
    """``acas013`` passing ``WS-Value-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas013_value.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas013_value.dispatch),
    )


def _dispatch_acas014(ctx: FacadeContext) -> None:
    """``acas014`` passing ``WS-Delivery-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas014 serves the out-of-scope entity Delivery. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas015(ctx: FacadeContext) -> None:
    """``acas015`` passing ``WS-Analysis-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas015_analysis.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas015_analysis.dispatch),
    )


def _dispatch_acas016(ctx: FacadeContext) -> None:
    """``acas016`` passing ``WS-Invoice-Record``.

    reason is in the handler's own linkage.
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    invoice = acas016_invoice.linkage_buffer_for(ctx.record)
    acas016_invoice.dispatch(
        ctx.system,
        invoice,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas016_invoice.dispatch),
    )
    acas016_invoice.publish_linkage_buffer(invoice, ctx.record)


def _dispatch_acas017(ctx: FacadeContext) -> None:
    """``acas017`` passing ``WS-Del-Inv-Nos-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas017 serves the out-of-scope entity DelInvNos. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas019(ctx: FacadeContext) -> None:
    """``acas019`` passing ``WS-OTM3-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas019_otm3.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas019_otm3.dispatch),
    )


def _dispatch_acas022(ctx: FacadeContext) -> None:
    """``acas022`` passing ``WS-Purch-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas022_purch.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas022_purch.dispatch),
    )


def _dispatch_acas023(ctx: FacadeContext) -> None:
    """``acas023`` passing ``WS-Del-Inv-Nos-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas023 serves the out-of-scope entity DelFolio. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas026(ctx: FacadeContext) -> None:
    """``acas026`` passing ``WS-PInvoice-Record``.

    same reason as ``acas016`` and with a different pair of descriptions.
    """
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    options = _forward(ctx, acas026_pinvoice.dispatch)
    # The staged line lives in the working storage the call uses, so the same
    # `context` the caller forwarded - if any - is the one to project through, on
    # the way in AND on the way out.
    context = options.get("context")
    pinvoice = acas026_pinvoice.linkage_header_for(ctx.record, context)  # type: ignore[arg-type]
    acas026_pinvoice.dispatch(
        ctx.system,
        pinvoice,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **options,
    )
    acas026_pinvoice.publish_linkage_header(pinvoice, ctx.record, context)  # type: ignore[arg-type]


def _dispatch_acas029(ctx: FacadeContext) -> None:
    """``acas029`` passing ``WS-OTM5-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acas029_otm5.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acas029_otm5.dispatch),
    )


def _dispatch_acas030(ctx: FacadeContext) -> None:
    """``acas030`` passing ``WS-PInvoice-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas030 serves the out-of-scope entity PLautogen. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acas032(ctx: FacadeContext) -> None:
    """``acas032`` passing ``WS-Pay-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    raise UnsupportedEntityError(
        "acas032 serves the out-of-scope entity Payments. Its bridge and its"
        " tables are out of scope per Agent Action Plan section"
        " 0.2.2, so no handler module exists. The verb names are"
        " published for traceability only."
    )


def _dispatch_acasirsub1(ctx: FacadeContext) -> None:
    """``acasirsub1`` passing ``WS-IRSNL-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub1_irs_nominal.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub1_irs_nominal.dispatch),
    )


def _dispatch_acasirsub3(ctx: FacadeContext) -> None:
    """``acasirsub3`` passing ``WS-IRS-Default-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub3_irs_dflt.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub3_irs_dflt.dispatch),
    )


def _dispatch_acasirsub4(ctx: FacadeContext) -> None:
    """``acasirsub4`` passing ``Posting-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub4_irs_posting.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub4_irs_posting.dispatch),
    )


def _dispatch_acasirsub5(ctx: FacadeContext) -> None:
    """``acasirsub5`` passing ``Final-Record``."""
    _apply(ctx.file_access, _FILE_KEY_NO, PRIMARY_FILE_KEY_NO)
    acasirsub5_irs_final.dispatch(
        ctx.system,
        ctx.record,
        ctx.file_access,
        ctx.file_defs,
        ctx.dal_common,
        **_forward(ctx, acasirsub5_irs_final.dispatch),
    )


#: Dispatch paragraph to implementation. ``acas000`` has two entries because the two
#: copybooks dispatch it differently; every other handler both dispatch is textually
#: identical in both.
_DISPATCH: Final[Mapping[str, Callable[[FacadeContext], None]]] = MappingProxyType({
    "acas000-entity": _dispatch_acas000_entity,
    "acas000-handler": _dispatch_acas000_handler,
    "acas004": _dispatch_acas004,
    "acas005": _dispatch_acas005,
    "acas006": _dispatch_acas006,
    "acas007": _dispatch_acas007,
    "acas008": _dispatch_acas008,
    "acas010": _dispatch_acas010,
    "acas011": _dispatch_acas011,
    "acas012": _dispatch_acas012,
    "acas013": _dispatch_acas013,
    "acas014": _dispatch_acas014,
    "acas015": _dispatch_acas015,
    "acas016": _dispatch_acas016,
    "acas017": _dispatch_acas017,
    "acas019": _dispatch_acas019,
    "acas022": _dispatch_acas022,
    "acas023": _dispatch_acas023,
    "acas026": _dispatch_acas026,
    "acas029": _dispatch_acas029,
    "acas030": _dispatch_acas030,
    "acas032": _dispatch_acas032,
    "acasirsub1": _dispatch_acasirsub1,
    "acasirsub3": _dispatch_acasirsub3,
    "acasirsub4": _dispatch_acasirsub4,
    "acasirsub5": _dispatch_acasirsub5,
})


# Vocabulary one: the entity-named verbs of [copybooks/Proc-ACAS-FH-Calls.cob] 234
# paragraphs across 21 entities, published exactly as they exist.


_E_SYSTEM_OPEN: Final[_Plan] = _Plan(
    "System-Open",
    "L190-L195",
    "acas000-entity",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def system_open(ctx: FacadeContext) -> StatusPair:
    """``System-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L190-L195].

    Written with literal ``move n to File-Function`` and ``move n to Access-Type``
    rather than ``set fn-... to true`` - the only entity that does. Same effect,
    transcribed as written.
    """
    return _perform(ctx, _E_SYSTEM_OPEN)


_E_SYSTEM_OPEN_INPUT: Final[_Plan] = _Plan(
    "System-Open-Input",
    "L197-L202",
    "acas000-entity",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def system_open_input(ctx: FacadeContext) -> StatusPair:
    """``System-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L197-L202].

    Written with literal ``move n to File-Function`` and ``move n to Access-Type``
    rather than ``set fn-... to true`` - the only entity that does. Same effect,
    transcribed as written.
    """
    return _perform(ctx, _E_SYSTEM_OPEN_INPUT)


_E_SYSTEM_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "System-Open-Output",
    "L204-L209",
    "acas000-entity",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def system_open_output(ctx: FacadeContext) -> StatusPair:
    """``System-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L204-L209].

    Written with literal ``move n to File-Function`` and ``move n to Access-Type``
    rather than ``set fn-... to true`` - the only entity that does. Same effect,
    transcribed as written.
    """
    return _perform(ctx, _E_SYSTEM_OPEN_OUTPUT)


_E_SYSTEM_CLOSE: Final[_Plan] = _Plan(
    "System-Close",
    "L211-L215",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def system_close(ctx: FacadeContext) -> StatusPair:
    """``System-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L211-L215].

    Written with literal ``move n to File-Function`` and ``move n to Access-Type``
    rather than ``set fn-... to true`` - the only entity that does. Same effect,
    transcribed as written.
    """
    return _perform(ctx, _E_SYSTEM_CLOSE)


_E_SYSTEM_READ_INDEXED: Final[_Plan] = _Plan(
    "System-Read-Indexed",
    "L217-L220",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def system_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``System-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L217-L220]."""
    return _perform(ctx, _E_SYSTEM_READ_INDEXED)


_E_SYSTEM_WRITE: Final[_Plan] = _Plan(
    "System-Write",
    "L222-L225",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def system_write(ctx: FacadeContext) -> StatusPair:
    """``System-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L222-L225]."""
    return _perform(ctx, _E_SYSTEM_WRITE)


_E_SYSTEM_REWRITE: Final[_Plan] = _Plan(
    "System-ReWrite",
    "L227-L230",
    "acas000-entity",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def system_rewrite(ctx: FacadeContext) -> StatusPair:
    """``System-ReWrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L227-L230]."""
    return _perform(ctx, _E_SYSTEM_REWRITE)


_E_SLAUTOGEN_OPEN: Final[_Plan] = _Plan(
    "SLautogen-Open",
    "L234-L237",
    "acas004",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def slautogen_open(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L234-L237]."""
    return _perform(ctx, _E_SLAUTOGEN_OPEN)


_E_SLAUTOGEN_OPEN_INPUT: Final[_Plan] = _Plan(
    "SLautogen-Open-Input",
    "L239-L242",
    "acas004",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def slautogen_open_input(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L239-L242]."""
    return _perform(ctx, _E_SLAUTOGEN_OPEN_INPUT)


_E_SLAUTOGEN_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "SLautogen-Open-Output",
    "L244-L247",
    "acas004",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def slautogen_open_output(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L244-L247]."""
    return _perform(ctx, _E_SLAUTOGEN_OPEN_OUTPUT)


_E_SLAUTOGEN_CLOSE: Final[_Plan] = _Plan(
    "SLautogen-Close",
    "L249-L252",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def slautogen_close(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L249-L252]."""
    return _perform(ctx, _E_SLAUTOGEN_CLOSE)


_E_SLAUTOGEN_DELETE: Final[_Plan] = _Plan(
    "SLautogen-Delete",
    "L254-L258",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def slautogen_delete(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L254-L258]."""
    return _perform(ctx, _E_SLAUTOGEN_DELETE)


_E_SLAUTOGEN_DELETE_ALL: Final[_Plan] = _Plan(
    "SLautogen-Delete-All",
    "L260-L264",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def slautogen_delete_all(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L260-L264]."""
    return _perform(ctx, _E_SLAUTOGEN_DELETE_ALL)


_E_SLAUTOGEN_START: Final[_Plan] = _Plan(
    "SLautogen-Start",
    "L266-L269",
    "acas004",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def slautogen_start(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L266-L269].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_SLAUTOGEN_START)


_E_SLAUTOGEN_READ_NEXT: Final[_Plan] = _Plan(
    "SLautogen-Read-Next",
    "L271-L274",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def slautogen_read_next(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L271-L274]."""
    return _perform(ctx, _E_SLAUTOGEN_READ_NEXT)


_E_SLAUTOGEN_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "SLautogen-Read-Next-Header",
    "L276-L279",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def slautogen_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L276-L279]."""
    return _perform(ctx, _E_SLAUTOGEN_READ_NEXT_HEADER)


_E_SLAUTOGEN_READ_INDEXED: Final[_Plan] = _Plan(
    "SLautogen-Read-Indexed",
    "L281-L285",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def slautogen_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L281-L285]."""
    return _perform(ctx, _E_SLAUTOGEN_READ_INDEXED)


_E_SLAUTOGEN_WRITE: Final[_Plan] = _Plan(
    "SLautogen-Write",
    "L287-L290",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def slautogen_write(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L287-L290]."""
    return _perform(ctx, _E_SLAUTOGEN_WRITE)


_E_SLAUTOGEN_REWRITE: Final[_Plan] = _Plan(
    "SLautogen-Rewrite",
    "L292-L295",
    "acas004",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def slautogen_rewrite(ctx: FacadeContext) -> StatusPair:
    """``SLautogen-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L292-L295]."""
    return _perform(ctx, _E_SLAUTOGEN_REWRITE)


_E_GL_NOMINAL_OPEN: Final[_Plan] = _Plan(
    "GL-Nominal-Open",
    "L299-L302",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def gl_nominal_open(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L299-L302]."""
    return _perform(ctx, _E_GL_NOMINAL_OPEN)


_E_GL_NOMINAL_OPEN_INPUT: Final[_Plan] = _Plan(
    "GL-Nominal-Open-Input",
    "L304-L307",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def gl_nominal_open_input(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L304-L307]."""
    return _perform(ctx, _E_GL_NOMINAL_OPEN_INPUT)


_E_GL_NOMINAL_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "GL-Nominal-Open-Output",
    "L309-L312",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def gl_nominal_open_output(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L309-L312]."""
    return _perform(ctx, _E_GL_NOMINAL_OPEN_OUTPUT)


_E_GL_NOMINAL_OPEN_EXTEND: Final[_Plan] = _Plan(
    "GL-Nominal-Open-Extend",
    "L314-L317",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def gl_nominal_open_extend(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L314-L317].

    Sets access type 4, marked "not valid for ISAM" [copybooks/wsfnctn.cob:L111], and no
    handler dispatches an extend access type on the relational path. Published and never
    satisfied.
    """
    return _perform(ctx, _E_GL_NOMINAL_OPEN_EXTEND)


_E_GL_NOMINAL_CLOSE: Final[_Plan] = _Plan(
    "GL-Nominal-Close",
    "L319-L322",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def gl_nominal_close(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L319-L322]."""
    return _perform(ctx, _E_GL_NOMINAL_CLOSE)


_E_GL_NOMINAL_DELETE: Final[_Plan] = _Plan(
    "GL-Nominal-Delete",
    "L324-L328",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_nominal_delete(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L324-L328]."""
    return _perform(ctx, _E_GL_NOMINAL_DELETE)


_E_GL_NOMINAL_START: Final[_Plan] = _Plan(
    "GL-Nominal-Start",
    "L330-L332",
    "acas005",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def gl_nominal_start(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L330-L332].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_GL_NOMINAL_START)


_E_GL_NOMINAL_READ_NEXT: Final[_Plan] = _Plan(
    "GL-Nominal-Read-Next",
    "L334-L337",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def gl_nominal_read_next(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L334-L337]."""
    return _perform(ctx, _E_GL_NOMINAL_READ_NEXT)


_E_GL_NOMINAL_READ_INDEXED: Final[_Plan] = _Plan(
    "GL-Nominal-Read-Indexed",
    "L339-L342",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def gl_nominal_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L339-L342]."""
    return _perform(ctx, _E_GL_NOMINAL_READ_INDEXED)


_E_GL_NOMINAL_WRITE: Final[_Plan] = _Plan(
    "GL-Nominal-Write",
    "L344-L347",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def gl_nominal_write(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L344-L347]."""
    return _perform(ctx, _E_GL_NOMINAL_WRITE)


_E_GL_NOMINAL_REWRITE: Final[_Plan] = _Plan(
    "GL-Nominal-Rewrite",
    "L349-L352",
    "acas005",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def gl_nominal_rewrite(ctx: FacadeContext) -> StatusPair:
    """``GL-Nominal-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L349-L352]."""
    return _perform(ctx, _E_GL_NOMINAL_REWRITE)


_E_GL_POSTING_OPEN: Final[_Plan] = _Plan(
    "GL-Posting-Open",
    "L356-L359",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def gl_posting_open(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L356-L359]."""
    return _perform(ctx, _E_GL_POSTING_OPEN)


_E_GL_POSTING_OPEN_INPUT: Final[_Plan] = _Plan(
    "GL-Posting-Open-Input",
    "L361-L364",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def gl_posting_open_input(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L361-L364]."""
    return _perform(ctx, _E_GL_POSTING_OPEN_INPUT)


_E_GL_POSTING_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "GL-Posting-Open-Output",
    "L366-L369",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def gl_posting_open_output(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L366-L369]."""
    return _perform(ctx, _E_GL_POSTING_OPEN_OUTPUT)


_E_GL_POSTING_OPEN_EXTEND: Final[_Plan] = _Plan(
    "GL-Posting-Open-Extend",
    "L371-L374",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def gl_posting_open_extend(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L371-L374].

    Sets access type 4, marked "not valid for ISAM" [copybooks/wsfnctn.cob:L111], and no
    handler dispatches an extend access type on the relational path. Published and never
    satisfied.
    """
    return _perform(ctx, _E_GL_POSTING_OPEN_EXTEND)


_E_GL_POSTING_CLOSE: Final[_Plan] = _Plan(
    "GL-Posting-Close",
    "L376-L379",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def gl_posting_close(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L376-L379]."""
    return _perform(ctx, _E_GL_POSTING_CLOSE)


_E_GL_POSTING_DELETE: Final[_Plan] = _Plan(
    "GL-Posting-Delete",
    "L381-L385",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_posting_delete(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L381-L385]."""
    return _perform(ctx, _E_GL_POSTING_DELETE)


_E_GL_POSTING_DELETE_ALL: Final[_Plan] = _Plan(
    "GL-Posting-Delete-All",
    "L387-L391",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_posting_delete_all(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L387-L391]."""
    return _perform(ctx, _E_GL_POSTING_DELETE_ALL)


_E_GL_POSTING_START: Final[_Plan] = _Plan(
    "GL-Posting-Start",
    "L393-L395",
    "acas006",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def gl_posting_start(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L393-L395].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_GL_POSTING_START)


_E_GL_POSTING_READ_NEXT: Final[_Plan] = _Plan(
    "GL-Posting-Read-Next",
    "L397-L400",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def gl_posting_read_next(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L397-L400]."""
    return _perform(ctx, _E_GL_POSTING_READ_NEXT)


_E_GL_POSTING_READ_INDEXED: Final[_Plan] = _Plan(
    "GL-Posting-Read-Indexed",
    "L402-L405",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def gl_posting_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L402-L405]."""
    return _perform(ctx, _E_GL_POSTING_READ_INDEXED)


_E_GL_POSTING_WRITE: Final[_Plan] = _Plan(
    "GL-Posting-Write",
    "L407-L410",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def gl_posting_write(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L407-L410]."""
    return _perform(ctx, _E_GL_POSTING_WRITE)


_E_GL_POSTING_REWRITE: Final[_Plan] = _Plan(
    "GL-Posting-Rewrite",
    "L412-L415",
    "acas006",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def gl_posting_rewrite(ctx: FacadeContext) -> StatusPair:
    """``GL-Posting-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L412-L415]."""
    return _perform(ctx, _E_GL_POSTING_REWRITE)


_E_GL_BATCH_OPEN: Final[_Plan] = _Plan(
    "GL-Batch-Open",
    "L419-L422",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def gl_batch_open(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L419-L422]."""
    return _perform(ctx, _E_GL_BATCH_OPEN)


_E_GL_BATCH_OPEN_INPUT: Final[_Plan] = _Plan(
    "GL-Batch-Open-Input",
    "L424-L427",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def gl_batch_open_input(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L424-L427]."""
    return _perform(ctx, _E_GL_BATCH_OPEN_INPUT)


_E_GL_BATCH_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "GL-Batch-Open-Output",
    "L429-L432",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def gl_batch_open_output(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L429-L432]."""
    return _perform(ctx, _E_GL_BATCH_OPEN_OUTPUT)


_E_GL_BATCH_OPEN_EXTEND: Final[_Plan] = _Plan(
    "GL-Batch-Open-Extend",
    "L434-L437",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def gl_batch_open_extend(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L434-L437].

    Sets access type 4, marked "not valid for ISAM" [copybooks/wsfnctn.cob:L111], and no
    handler dispatches an extend access type on the relational path. Published and never
    satisfied.
    """
    return _perform(ctx, _E_GL_BATCH_OPEN_EXTEND)


_E_GL_BATCH_CLOSE: Final[_Plan] = _Plan(
    "GL-Batch-Close",
    "L439-L442",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def gl_batch_close(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L439-L442]."""
    return _perform(ctx, _E_GL_BATCH_CLOSE)


_E_GL_BATCH_DELETE: Final[_Plan] = _Plan(
    "GL-Batch-Delete",
    "L444-L448",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_batch_delete(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L444-L448]."""
    return _perform(ctx, _E_GL_BATCH_DELETE)


_E_GL_BATCH_DELETE_ALL: Final[_Plan] = _Plan(
    "GL-Batch-Delete-All",
    "L450-L454",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def gl_batch_delete_all(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L450-L454]."""
    return _perform(ctx, _E_GL_BATCH_DELETE_ALL)


_E_GL_BATCH_START: Final[_Plan] = _Plan(
    "GL-Batch-Start",
    "L456-L458",
    "acas007",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def gl_batch_start(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L456-L458].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_GL_BATCH_START)


_E_GL_BATCH_READ_NEXT: Final[_Plan] = _Plan(
    "GL-Batch-Read-Next",
    "L460-L463",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def gl_batch_read_next(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L460-L463]."""
    return _perform(ctx, _E_GL_BATCH_READ_NEXT)


_E_GL_BATCH_READ_INDEXED: Final[_Plan] = _Plan(
    "GL-Batch-Read-Indexed",
    "L465-L468",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def gl_batch_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L465-L468]."""
    return _perform(ctx, _E_GL_BATCH_READ_INDEXED)


_E_GL_BATCH_WRITE: Final[_Plan] = _Plan(
    "GL-Batch-Write",
    "L470-L473",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def gl_batch_write(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L470-L473]."""
    return _perform(ctx, _E_GL_BATCH_WRITE)


_E_GL_BATCH_REWRITE: Final[_Plan] = _Plan(
    "GL-Batch-Rewrite",
    "L475-L478",
    "acas007",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def gl_batch_rewrite(ctx: FacadeContext) -> StatusPair:
    """``GL-Batch-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L475-L478]."""
    return _perform(ctx, _E_GL_BATCH_REWRITE)


_E_SPL_POSTING_OPEN: Final[_Plan] = _Plan(
    "SPL-Posting-Open",
    "L482-L485",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def spl_posting_open(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L482-L485]."""
    return _perform(ctx, _E_SPL_POSTING_OPEN)


_E_SPL_POSTING_OPEN_INPUT: Final[_Plan] = _Plan(
    "SPL-Posting-Open-Input",
    "L487-L490",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def spl_posting_open_input(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L487-L490]."""
    return _perform(ctx, _E_SPL_POSTING_OPEN_INPUT)


_E_SPL_POSTING_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "SPL-Posting-Open-Output",
    "L492-L495",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def spl_posting_open_output(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L492-L495]."""
    return _perform(ctx, _E_SPL_POSTING_OPEN_OUTPUT)


_E_SPL_POSTING_OPEN_EXTEND: Final[_Plan] = _Plan(
    "SPL-Posting-Open-Extend",
    "L497-L500",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def spl_posting_open_extend(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L497-L500].

    Sets access type 4, marked "not valid for ISAM" [copybooks/wsfnctn.cob:L111], and no
    handler dispatches an extend access type on the relational path. Published and never
    satisfied.
    """
    return _perform(ctx, _E_SPL_POSTING_OPEN_EXTEND)


_E_SPL_POSTING_CLOSE: Final[_Plan] = _Plan(
    "SPL-Posting-Close",
    "L502-L505",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def spl_posting_close(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L502-L505]."""
    return _perform(ctx, _E_SPL_POSTING_CLOSE)


_E_SPL_POSTING_DELETE: Final[_Plan] = _Plan(
    "SPL-Posting-Delete",
    "L507-L511",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def spl_posting_delete(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L507-L511].

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential, and answers
    ``FS-Reply`` 99 with ``WE-Error`` 988. Published and guaranteed to fail.
    """
    return _perform(ctx, _E_SPL_POSTING_DELETE)


_E_SPL_POSTING_DELETE_ALL: Final[_Plan] = _Plan(
    "SPL-Posting-Delete-All",
    "L513-L517",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def spl_posting_delete_all(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L513-L517]."""
    return _perform(ctx, _E_SPL_POSTING_DELETE_ALL)


_E_SPL_POSTING_START: Final[_Plan] = _Plan(
    "SPL-Posting-Start",
    "L519-L521",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def spl_posting_start(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L519-L521].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_SPL_POSTING_START)


_E_SPL_POSTING_READ_NEXT: Final[_Plan] = _Plan(
    "SPL-Posting-Read-Next",
    "L523-L526",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def spl_posting_read_next(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L523-L526]."""
    return _perform(ctx, _E_SPL_POSTING_READ_NEXT)


_E_SPL_POSTING_READ_INDEXED: Final[_Plan] = _Plan(
    "SPL-Posting-Read-Indexed",
    "L528-L531",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def spl_posting_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L528-L531].

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential, and answers
    ``FS-Reply`` 99 with ``WE-Error`` 988. Published and guaranteed to fail.
    """
    return _perform(ctx, _E_SPL_POSTING_READ_INDEXED)


_E_SPL_POSTING_WRITE: Final[_Plan] = _Plan(
    "SPL-Posting-Write",
    "L533-L536",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def spl_posting_write(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L533-L536]."""
    return _perform(ctx, _E_SPL_POSTING_WRITE)


_E_SPL_POSTING_REWRITE: Final[_Plan] = _Plan(
    "SPL-Posting-Rewrite",
    "L538-L541",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def spl_posting_rewrite(ctx: FacadeContext) -> StatusPair:
    """``SPL-Posting-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L538-L541].

    ``acas008`` refuses this function unconditionally at entry
    [common/acas008.cbl:L299-L307], because the transfer file is sequential, and answers
    ``FS-Reply`` 99 with ``WE-Error`` 988. Published and guaranteed to fail.
    """
    return _perform(ctx, _E_SPL_POSTING_REWRITE)


_E_STOCK_AUDIT_OPEN: Final[_Plan] = _Plan(
    "Stock-Audit-Open",
    "L545-L548",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def stock_audit_open(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L545-L548]."""
    return _perform(ctx, _E_STOCK_AUDIT_OPEN)


_E_STOCK_AUDIT_OPEN_INPUT: Final[_Plan] = _Plan(
    "Stock-Audit-Open-Input",
    "L550-L553",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def stock_audit_open_input(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L550-L553]."""
    return _perform(ctx, _E_STOCK_AUDIT_OPEN_INPUT)


_E_STOCK_AUDIT_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Stock-Audit-Open-Output",
    "L555-L558",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def stock_audit_open_output(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L555-L558]."""
    return _perform(ctx, _E_STOCK_AUDIT_OPEN_OUTPUT)


_E_STOCK_AUDIT_OPEN_EXTEND: Final[_Plan] = _Plan(
    "Stock-Audit-Open-Extend",
    "L560-L563",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.EXTEND),
    ),
)


def stock_audit_open_extend(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Open-Extend`` [copybooks/Proc-ACAS-FH-Calls.cob:L560-L563].

    Sets access type 4, marked "not valid for ISAM" [copybooks/wsfnctn.cob:L111], and no
    handler dispatches an extend access type on the relational path. Published and never
    satisfied.
    """
    return _perform(ctx, _E_STOCK_AUDIT_OPEN_EXTEND)


_E_STOCK_AUDIT_CLOSE: Final[_Plan] = _Plan(
    "Stock-Audit-Close",
    "L565-L568",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def stock_audit_close(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L565-L568]."""
    return _perform(ctx, _E_STOCK_AUDIT_CLOSE)


_E_STOCK_AUDIT_DELETE: Final[_Plan] = _Plan(
    "Stock-Audit-Delete",
    "L570-L574",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def stock_audit_delete(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L570-L574]."""
    return _perform(ctx, _E_STOCK_AUDIT_DELETE)


_E_STOCK_AUDIT_START: Final[_Plan] = _Plan(
    "Stock-Audit-Start",
    "L576-L578",
    "acas010",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def stock_audit_start(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L576-L578].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_STOCK_AUDIT_START)


_E_STOCK_AUDIT_READ_NEXT: Final[_Plan] = _Plan(
    "Stock-Audit-Read-Next",
    "L580-L583",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def stock_audit_read_next(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L580-L583]."""
    return _perform(ctx, _E_STOCK_AUDIT_READ_NEXT)


_E_STOCK_AUDIT_READ_INDEXED: Final[_Plan] = _Plan(
    "Stock-Audit-Read-Indexed",
    "L585-L588",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def stock_audit_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L585-L588]."""
    return _perform(ctx, _E_STOCK_AUDIT_READ_INDEXED)


_E_STOCK_AUDIT_WRITE: Final[_Plan] = _Plan(
    "Stock-Audit-Write",
    "L590-L593",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def stock_audit_write(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L590-L593]."""
    return _perform(ctx, _E_STOCK_AUDIT_WRITE)


_E_STOCK_AUDIT_REWRITE: Final[_Plan] = _Plan(
    "Stock-Audit-Rewrite",
    "L595-L598",
    "acas010",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def stock_audit_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Stock-Audit-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L595-L598]."""
    return _perform(ctx, _E_STOCK_AUDIT_REWRITE)


_E_STOCK_OPEN: Final[_Plan] = _Plan(
    "Stock-Open",
    "L602-L605",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def stock_open(ctx: FacadeContext) -> StatusPair:
    """``Stock-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L602-L605]."""
    return _perform(ctx, _E_STOCK_OPEN)


_E_STOCK_OPEN_INPUT: Final[_Plan] = _Plan(
    "Stock-Open-Input",
    "L607-L610",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def stock_open_input(ctx: FacadeContext) -> StatusPair:
    """``Stock-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L607-L610]."""
    return _perform(ctx, _E_STOCK_OPEN_INPUT)


_E_STOCK_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Stock-Open-Output",
    "L612-L615",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def stock_open_output(ctx: FacadeContext) -> StatusPair:
    """``Stock-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L612-L615]."""
    return _perform(ctx, _E_STOCK_OPEN_OUTPUT)


_E_STOCK_CLOSE: Final[_Plan] = _Plan(
    "Stock-Close",
    "L617-L620",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def stock_close(ctx: FacadeContext) -> StatusPair:
    """``Stock-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L617-L620]."""
    return _perform(ctx, _E_STOCK_CLOSE)


_E_STOCK_DELETE: Final[_Plan] = _Plan(
    "Stock-Delete",
    "L622-L626",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def stock_delete(ctx: FacadeContext) -> StatusPair:
    """``Stock-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L622-L626]."""
    return _perform(ctx, _E_STOCK_DELETE)


_E_STOCK_START: Final[_Plan] = _Plan(
    "Stock-Start",
    "L628-L630",
    "acas011",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def stock_start(ctx: FacadeContext) -> StatusPair:
    """``Stock-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L628-L630].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_STOCK_START)


_E_STOCK_READ_NEXT: Final[_Plan] = _Plan(
    "Stock-Read-Next",
    "L632-L635",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def stock_read_next(ctx: FacadeContext) -> StatusPair:
    """``Stock-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L632-L635]."""
    return _perform(ctx, _E_STOCK_READ_NEXT)


_E_STOCK_READ_INDEXED: Final[_Plan] = _Plan(
    "Stock-Read-Indexed",
    "L637-L640",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def stock_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Stock-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L637-L640]."""
    return _perform(ctx, _E_STOCK_READ_INDEXED)


_E_STOCK_WRITE: Final[_Plan] = _Plan(
    "Stock-Write",
    "L642-L645",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def stock_write(ctx: FacadeContext) -> StatusPair:
    """``Stock-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L642-L645]."""
    return _perform(ctx, _E_STOCK_WRITE)


_E_STOCK_REWRITE: Final[_Plan] = _Plan(
    "Stock-Rewrite",
    "L647-L650",
    "acas011",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def stock_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Stock-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L647-L650]."""
    return _perform(ctx, _E_STOCK_REWRITE)


_E_SALES_OPEN: Final[_Plan] = _Plan(
    "Sales-Open",
    "L654-L657",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def sales_open(ctx: FacadeContext) -> StatusPair:
    """``Sales-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L654-L657]."""
    return _perform(ctx, _E_SALES_OPEN)


_E_SALES_OPEN_INPUT: Final[_Plan] = _Plan(
    "Sales-Open-Input",
    "L659-L662",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def sales_open_input(ctx: FacadeContext) -> StatusPair:
    """``Sales-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L659-L662]."""
    return _perform(ctx, _E_SALES_OPEN_INPUT)


_E_SALES_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Sales-Open-Output",
    "L664-L667",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def sales_open_output(ctx: FacadeContext) -> StatusPair:
    """``Sales-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L664-L667]."""
    return _perform(ctx, _E_SALES_OPEN_OUTPUT)


_E_SALES_CLOSE: Final[_Plan] = _Plan(
    "Sales-Close",
    "L669-L672",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def sales_close(ctx: FacadeContext) -> StatusPair:
    """``Sales-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L669-L672]."""
    return _perform(ctx, _E_SALES_CLOSE)


_E_SALES_DELETE: Final[_Plan] = _Plan(
    "Sales-Delete",
    "L674-L678",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def sales_delete(ctx: FacadeContext) -> StatusPair:
    """``Sales-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L674-L678]."""
    return _perform(ctx, _E_SALES_DELETE)


_E_SALES_START: Final[_Plan] = _Plan(
    "Sales-Start",
    "L680-L682",
    "acas012",
    (
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def sales_start(ctx: FacadeContext) -> StatusPair:
    """``Sales-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L680-L682].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_SALES_START)


_E_SALES_READ_NEXT: Final[_Plan] = _Plan(
    "Sales-Read-Next",
    "L684-L687",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def sales_read_next(ctx: FacadeContext) -> StatusPair:
    """``Sales-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L684-L687]."""
    return _perform(ctx, _E_SALES_READ_NEXT)


_E_SALES_READ_NEXT_SORTED_BY_NAME: Final[_Plan] = _Plan(
    "Sales-Read-Next-Sorted-By-Name",
    "L689-L692",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_NAME),
    ),
)


def sales_read_next_sorted_by_name(ctx: FacadeContext) -> StatusPair:
    """``Sales-Read-Next-Sorted-By-Name`` [copybooks/Proc-ACAS-FH-Calls.cob:L689-L692].
    """
    return _perform(ctx, _E_SALES_READ_NEXT_SORTED_BY_NAME)


_E_SALES_READ_INDEXED: Final[_Plan] = _Plan(
    "Sales-Read-Indexed",
    "L694-L697",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def sales_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Sales-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L694-L697]."""
    return _perform(ctx, _E_SALES_READ_INDEXED)


_E_SALES_WRITE: Final[_Plan] = _Plan(
    "Sales-Write",
    "L699-L702",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def sales_write(ctx: FacadeContext) -> StatusPair:
    """``Sales-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L699-L702]."""
    return _perform(ctx, _E_SALES_WRITE)


_E_SALES_REWRITE: Final[_Plan] = _Plan(
    "Sales-Rewrite",
    "L704-L707",
    "acas012",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def sales_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Sales-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L704-L707]."""
    return _perform(ctx, _E_SALES_REWRITE)


_E_VALUE_OPEN: Final[_Plan] = _Plan(
    "Value-Open",
    "L711-L714",
    "acas013",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def value_open(ctx: FacadeContext) -> StatusPair:
    """``Value-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L711-L714]."""
    return _perform(ctx, _E_VALUE_OPEN)


_E_VALUE_OPEN_INPUT: Final[_Plan] = _Plan(
    "Value-Open-Input",
    "L716-L719",
    "acas013",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def value_open_input(ctx: FacadeContext) -> StatusPair:
    """``Value-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L716-L719]."""
    return _perform(ctx, _E_VALUE_OPEN_INPUT)


_E_VALUE_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Value-Open-Output",
    "L721-L724",
    "acas013",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def value_open_output(ctx: FacadeContext) -> StatusPair:
    """``Value-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L721-L724]."""
    return _perform(ctx, _E_VALUE_OPEN_OUTPUT)


_E_VALUE_CLOSE: Final[_Plan] = _Plan(
    "Value-Close",
    "L726-L729",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def value_close(ctx: FacadeContext) -> StatusPair:
    """``Value-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L726-L729]."""
    return _perform(ctx, _E_VALUE_CLOSE)


_E_VALUE_DELETE: Final[_Plan] = _Plan(
    "Value-Delete",
    "L731-L735",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def value_delete(ctx: FacadeContext) -> StatusPair:
    """``Value-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L731-L735]."""
    return _perform(ctx, _E_VALUE_DELETE)


_E_VALUE_DELETE_ALL: Final[_Plan] = _Plan(
    "Value-Delete-All",
    "L737-L741",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def value_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Value-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L737-L741]."""
    return _perform(ctx, _E_VALUE_DELETE_ALL)


_E_VALUE_START: Final[_Plan] = _Plan(
    "Value-Start",
    "L743-L746",
    "acas013",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def value_start(ctx: FacadeContext) -> StatusPair:
    """``Value-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L743-L746].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_VALUE_START)


_E_VALUE_READ_NEXT: Final[_Plan] = _Plan(
    "Value-Read-Next",
    "L748-L751",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def value_read_next(ctx: FacadeContext) -> StatusPair:
    """``Value-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L748-L751]."""
    return _perform(ctx, _E_VALUE_READ_NEXT)


_E_VALUE_READ_INDEXED: Final[_Plan] = _Plan(
    "Value-Read-Indexed",
    "L753-L757",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def value_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Value-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L753-L757]."""
    return _perform(ctx, _E_VALUE_READ_INDEXED)


_E_VALUE_WRITE: Final[_Plan] = _Plan(
    "Value-Write",
    "L759-L762",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def value_write(ctx: FacadeContext) -> StatusPair:
    """``Value-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L759-L762]."""
    return _perform(ctx, _E_VALUE_WRITE)


_E_VALUE_REWRITE: Final[_Plan] = _Plan(
    "Value-Rewrite",
    "L764-L767",
    "acas013",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def value_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Value-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L764-L767]."""
    return _perform(ctx, _E_VALUE_REWRITE)


_E_DELIVERY_OPEN: Final[_Plan] = _Plan(
    "Delivery-Open",
    "L771-L774",
    "acas014",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def delivery_open(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L771-L774]."""
    return _perform(ctx, _E_DELIVERY_OPEN)


_E_DELIVERY_OPEN_INPUT: Final[_Plan] = _Plan(
    "Delivery-Open-Input",
    "L776-L779",
    "acas014",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def delivery_open_input(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L776-L779]."""
    return _perform(ctx, _E_DELIVERY_OPEN_INPUT)


_E_DELIVERY_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Delivery-Open-Output",
    "L781-L784",
    "acas014",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def delivery_open_output(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L781-L784]."""
    return _perform(ctx, _E_DELIVERY_OPEN_OUTPUT)


_E_DELIVERY_CLOSE: Final[_Plan] = _Plan(
    "Delivery-Close",
    "L786-L789",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def delivery_close(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L786-L789]."""
    return _perform(ctx, _E_DELIVERY_CLOSE)


_E_DELIVERY_DELETE: Final[_Plan] = _Plan(
    "Delivery-Delete",
    "L791-L795",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delivery_delete(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L791-L795]."""
    return _perform(ctx, _E_DELIVERY_DELETE)


_E_DELIVERY_DELETE_ALL: Final[_Plan] = _Plan(
    "Delivery-Delete-All",
    "L797-L801",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delivery_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L797-L801]."""
    return _perform(ctx, _E_DELIVERY_DELETE_ALL)


_E_DELIVERY_START: Final[_Plan] = _Plan(
    "Delivery-Start",
    "L803-L806",
    "acas014",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def delivery_start(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L803-L806].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_DELIVERY_START)


_E_DELIVERY_READ_NEXT: Final[_Plan] = _Plan(
    "Delivery-Read-Next",
    "L808-L811",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def delivery_read_next(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L808-L811]."""
    return _perform(ctx, _E_DELIVERY_READ_NEXT)


_E_DELIVERY_READ_INDEXED: Final[_Plan] = _Plan(
    "Delivery-Read-Indexed",
    "L813-L817",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def delivery_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L813-L817]."""
    return _perform(ctx, _E_DELIVERY_READ_INDEXED)


_E_DELIVERY_WRITE: Final[_Plan] = _Plan(
    "Delivery-Write",
    "L819-L822",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def delivery_write(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L819-L822]."""
    return _perform(ctx, _E_DELIVERY_WRITE)


_E_DELIVERY_REWRITE: Final[_Plan] = _Plan(
    "Delivery-Rewrite",
    "L824-L827",
    "acas014",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def delivery_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Delivery-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L824-L827]."""
    return _perform(ctx, _E_DELIVERY_REWRITE)


_E_ANALYSIS_OPEN: Final[_Plan] = _Plan(
    "Analysis-Open",
    "L831-L834",
    "acas015",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def analysis_open(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L831-L834]."""
    return _perform(ctx, _E_ANALYSIS_OPEN)


_E_ANALYSIS_OPEN_INPUT: Final[_Plan] = _Plan(
    "Analysis-Open-Input",
    "L836-L839",
    "acas015",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def analysis_open_input(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L836-L839]."""
    return _perform(ctx, _E_ANALYSIS_OPEN_INPUT)


_E_ANALYSIS_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Analysis-Open-Output",
    "L841-L844",
    "acas015",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def analysis_open_output(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L841-L844]."""
    return _perform(ctx, _E_ANALYSIS_OPEN_OUTPUT)


_E_ANALYSIS_CLOSE: Final[_Plan] = _Plan(
    "Analysis-Close",
    "L846-L849",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def analysis_close(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L846-L849]."""
    return _perform(ctx, _E_ANALYSIS_CLOSE)


_E_ANALYSIS_DELETE: Final[_Plan] = _Plan(
    "Analysis-Delete",
    "L851-L855",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def analysis_delete(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L851-L855]."""
    return _perform(ctx, _E_ANALYSIS_DELETE)


_E_ANALYSIS_START: Final[_Plan] = _Plan(
    "Analysis-Start",
    "L857-L860",
    "acas015",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def analysis_start(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L857-L860].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_ANALYSIS_START)


_E_ANALYSIS_READ_NEXT: Final[_Plan] = _Plan(
    "Analysis-Read-Next",
    "L862-L865",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def analysis_read_next(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L862-L865]."""
    return _perform(ctx, _E_ANALYSIS_READ_NEXT)


_E_ANALYSIS_READ_INDEXED: Final[_Plan] = _Plan(
    "Analysis-Read-Indexed",
    "L867-L871",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def analysis_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L867-L871]."""
    return _perform(ctx, _E_ANALYSIS_READ_INDEXED)


_E_ANALYSIS_WRITE: Final[_Plan] = _Plan(
    "Analysis-Write",
    "L873-L876",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def analysis_write(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L873-L876]."""
    return _perform(ctx, _E_ANALYSIS_WRITE)


_E_ANALYSIS_REWRITE: Final[_Plan] = _Plan(
    "Analysis-Rewrite",
    "L878-L881",
    "acas015",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def analysis_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Analysis-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L878-L881]."""
    return _perform(ctx, _E_ANALYSIS_REWRITE)


_E_INVOICE_OPEN: Final[_Plan] = _Plan(
    "Invoice-Open",
    "L885-L888",
    "acas016",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def invoice_open(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L885-L888]."""
    return _perform(ctx, _E_INVOICE_OPEN)


_E_INVOICE_OPEN_INPUT: Final[_Plan] = _Plan(
    "Invoice-Open-Input",
    "L890-L893",
    "acas016",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def invoice_open_input(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L890-L893]."""
    return _perform(ctx, _E_INVOICE_OPEN_INPUT)


_E_INVOICE_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Invoice-Open-Output",
    "L895-L898",
    "acas016",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def invoice_open_output(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L895-L898]."""
    return _perform(ctx, _E_INVOICE_OPEN_OUTPUT)


_E_INVOICE_CLOSE: Final[_Plan] = _Plan(
    "Invoice-Close",
    "L900-L903",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def invoice_close(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L900-L903]."""
    return _perform(ctx, _E_INVOICE_CLOSE)


_E_INVOICE_DELETE: Final[_Plan] = _Plan(
    "Invoice-Delete",
    "L905-L909",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def invoice_delete(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L905-L909]."""
    return _perform(ctx, _E_INVOICE_DELETE)


_E_INVOICE_DELETE_ALL: Final[_Plan] = _Plan(
    "Invoice-Delete-All",
    "L911-L915",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def invoice_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L911-L915]."""
    return _perform(ctx, _E_INVOICE_DELETE_ALL)


_E_INVOICE_START: Final[_Plan] = _Plan(
    "Invoice-Start",
    "L917-L920",
    "acas016",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def invoice_start(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L917-L920].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_INVOICE_START)


_E_INVOICE_READ_NEXT: Final[_Plan] = _Plan(
    "Invoice-Read-Next",
    "L922-L925",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def invoice_read_next(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L922-L925]."""
    return _perform(ctx, _E_INVOICE_READ_NEXT)


_E_INVOICE_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "Invoice-Read-Next-Header",
    "L927-L930",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def invoice_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L927-L930]."""
    return _perform(ctx, _E_INVOICE_READ_NEXT_HEADER)


_E_INVOICE_READ_INDEXED: Final[_Plan] = _Plan(
    "Invoice-Read-Indexed",
    "L932-L936",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def invoice_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L932-L936]."""
    return _perform(ctx, _E_INVOICE_READ_INDEXED)


_E_INVOICE_WRITE: Final[_Plan] = _Plan(
    "Invoice-Write",
    "L938-L941",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def invoice_write(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L938-L941]."""
    return _perform(ctx, _E_INVOICE_WRITE)


_E_INVOICE_REWRITE: Final[_Plan] = _Plan(
    "Invoice-Rewrite",
    "L943-L946",
    "acas016",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def invoice_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Invoice-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L943-L946]."""
    return _perform(ctx, _E_INVOICE_REWRITE)


_E_DELINVNOS_OPEN: Final[_Plan] = _Plan(
    "DelInvNos-Open",
    "L950-L953",
    "acas017",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def delinvnos_open(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L950-L953]."""
    return _perform(ctx, _E_DELINVNOS_OPEN)


_E_DELINVNOS_OPEN_INPUT: Final[_Plan] = _Plan(
    "DelInvNos-Open-Input",
    "L955-L958",
    "acas017",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def delinvnos_open_input(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L955-L958]."""
    return _perform(ctx, _E_DELINVNOS_OPEN_INPUT)


_E_DELINVNOS_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "DelInvNos-Open-Output",
    "L960-L963",
    "acas017",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def delinvnos_open_output(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L960-L963]."""
    return _perform(ctx, _E_DELINVNOS_OPEN_OUTPUT)


_E_DELINVNOS_CLOSE: Final[_Plan] = _Plan(
    "DelInvNos-Close",
    "L965-L968",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def delinvnos_close(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L965-L968]."""
    return _perform(ctx, _E_DELINVNOS_CLOSE)


_E_DELINVNOS_DELETE: Final[_Plan] = _Plan(
    "DelInvNos-Delete",
    "L970-L974",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delinvnos_delete(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L970-L974]."""
    return _perform(ctx, _E_DELINVNOS_DELETE)


_E_DELINVNOS_DELETE_ALL: Final[_Plan] = _Plan(
    "DelInvNos-Delete-All",
    "L976-L980",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delinvnos_delete_all(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L976-L980]."""
    return _perform(ctx, _E_DELINVNOS_DELETE_ALL)


_E_DELINVNOS_START: Final[_Plan] = _Plan(
    "DelInvNos-Start",
    "L982-L985",
    "acas017",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def delinvnos_start(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L982-L985].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_DELINVNOS_START)


_E_DELINVNOS_READ_NEXT: Final[_Plan] = _Plan(
    "DelInvNos-Read-Next",
    "L987-L990",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def delinvnos_read_next(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L987-L990]."""
    return _perform(ctx, _E_DELINVNOS_READ_NEXT)


_E_DELINVNOS_READ_INDEXED: Final[_Plan] = _Plan(
    "DelInvNos-Read-Indexed",
    "L992-L996",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def delinvnos_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L992-L996]."""
    return _perform(ctx, _E_DELINVNOS_READ_INDEXED)


_E_DELINVNOS_WRITE: Final[_Plan] = _Plan(
    "DelInvNos-Write",
    "L998-L1001",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def delinvnos_write(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L998-L1001]."""
    return _perform(ctx, _E_DELINVNOS_WRITE)


_E_DELINVNOS_REWRITE: Final[_Plan] = _Plan(
    "DelInvNos-Rewrite",
    "L1003-L1006",
    "acas017",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def delinvnos_rewrite(ctx: FacadeContext) -> StatusPair:
    """``DelInvNos-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1003-L1006]."""
    return _perform(ctx, _E_DELINVNOS_REWRITE)


_E_OTM3_OPEN: Final[_Plan] = _Plan(
    "OTM3-Open",
    "L1010-L1013",
    "acas019",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def otm3_open(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1010-L1013]."""
    return _perform(ctx, _E_OTM3_OPEN)


_E_OTM3_OPEN_INPUT: Final[_Plan] = _Plan(
    "OTM3-Open-Input",
    "L1015-L1018",
    "acas019",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def otm3_open_input(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1015-L1018]."""
    return _perform(ctx, _E_OTM3_OPEN_INPUT)


_E_OTM3_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "OTM3-Open-Output",
    "L1020-L1023",
    "acas019",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def otm3_open_output(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1020-L1023]."""
    return _perform(ctx, _E_OTM3_OPEN_OUTPUT)


_E_OTM3_CLOSE: Final[_Plan] = _Plan(
    "OTM3-Close",
    "L1025-L1028",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def otm3_close(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1025-L1028]."""
    return _perform(ctx, _E_OTM3_CLOSE)


_E_OTM3_DELETE: Final[_Plan] = _Plan(
    "OTM3-Delete",
    "L1030-L1034",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def otm3_delete(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1030-L1034]."""
    return _perform(ctx, _E_OTM3_DELETE)


_E_OTM3_START: Final[_Plan] = _Plan(
    "OTM3-Start",
    "L1036-L1039",
    "acas019",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def otm3_start(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1036-L1039].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_OTM3_START)


_E_OTM3_READ_NEXT: Final[_Plan] = _Plan(
    "OTM3-Read-Next",
    "L1041-L1044",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def otm3_read_next(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1041-L1044]."""
    return _perform(ctx, _E_OTM3_READ_NEXT)


_E_OTM3_READ_INDEXED: Final[_Plan] = _Plan(
    "OTM3-Read-Indexed",
    "L1046-L1050",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def otm3_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1046-L1050]."""
    return _perform(ctx, _E_OTM3_READ_INDEXED)


_E_OTM3_READ_NEXT_SORTED_BY_BATCH: Final[_Plan] = _Plan(
    "OTM3-Read-Next-Sorted-By-Batch",
    "L1052-L1055",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_BATCH),
    ),
)


def otm3_read_next_sorted_by_batch(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Next-Sorted-By-Batch`` [copybooks/Proc-ACAS-FH-Calls.cob:L1052-L1055].

    Sets function code 32, declared for OTM3 and OTM5 at
    [copybooks/wsfnctn.cob:L103-L104] and dispatched by the BRIDGE of each of the two
    handlers it was declared for - ``otm3MT`` routes it to ``ba140-Process-Read-Next``
    [common/otm3MT.cbl:L420-L423] and ``otm5MT`` likewise [common/otm5MT.cbl:L425-L426].
    """
    return _perform(ctx, _E_OTM3_READ_NEXT_SORTED_BY_BATCH)


_E_OTM3_READ_NEXT_SORTED_BY_CUST: Final[_Plan] = _Plan(
    "OTM3-Read-Next-Sorted-By-Cust",
    "L1057-L1060",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_CUST),
    ),
)


def otm3_read_next_sorted_by_cust(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Read-Next-Sorted-By-Cust`` [copybooks/Proc-ACAS-FH-Calls.cob:L1057-L1060].

    Satisfiable but never successful: the same three compounded defects yield ``(10,
    10)``. See anomaly N-sorted-order-is-a-syntax-error.
    """
    return _perform(ctx, _E_OTM3_READ_NEXT_SORTED_BY_CUST)


_E_OTM3_WRITE: Final[_Plan] = _Plan(
    "OTM3-Write",
    "L1062-L1065",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def otm3_write(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1062-L1065]."""
    return _perform(ctx, _E_OTM3_WRITE)


_E_OTM3_REWRITE: Final[_Plan] = _Plan(
    "OTM3-Rewrite",
    "L1067-L1070",
    "acas019",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def otm3_rewrite(ctx: FacadeContext) -> StatusPair:
    """``OTM3-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1067-L1070]."""
    return _perform(ctx, _E_OTM3_REWRITE)


_E_PURCH_OPEN: Final[_Plan] = _Plan(
    "Purch-Open",
    "L1074-L1077",
    "acas022",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def purch_open(ctx: FacadeContext) -> StatusPair:
    """``Purch-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1074-L1077]."""
    return _perform(ctx, _E_PURCH_OPEN)


_E_PURCH_OPEN_INPUT: Final[_Plan] = _Plan(
    "Purch-Open-Input",
    "L1079-L1082",
    "acas022",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def purch_open_input(ctx: FacadeContext) -> StatusPair:
    """``Purch-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1079-L1082]."""
    return _perform(ctx, _E_PURCH_OPEN_INPUT)


_E_PURCH_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Purch-Open-Output",
    "L1084-L1087",
    "acas022",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def purch_open_output(ctx: FacadeContext) -> StatusPair:
    """``Purch-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1084-L1087]."""
    return _perform(ctx, _E_PURCH_OPEN_OUTPUT)


_E_PURCH_CLOSE: Final[_Plan] = _Plan(
    "Purch-Close",
    "L1089-L1092",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def purch_close(ctx: FacadeContext) -> StatusPair:
    """``Purch-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1089-L1092]."""
    return _perform(ctx, _E_PURCH_CLOSE)


_E_PURCH_DELETE: Final[_Plan] = _Plan(
    "Purch-Delete",
    "L1094-L1098",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def purch_delete(ctx: FacadeContext) -> StatusPair:
    """``Purch-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1094-L1098]."""
    return _perform(ctx, _E_PURCH_DELETE)


_E_PURCH_START: Final[_Plan] = _Plan(
    "Purch-Start",
    "L1100-L1103",
    "acas022",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def purch_start(ctx: FacadeContext) -> StatusPair:
    """``Purch-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1100-L1103].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_PURCH_START)


_E_PURCH_READ_NEXT: Final[_Plan] = _Plan(
    "Purch-Read-Next",
    "L1105-L1108",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def purch_read_next(ctx: FacadeContext) -> StatusPair:
    """``Purch-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1105-L1108]."""
    return _perform(ctx, _E_PURCH_READ_NEXT)


_E_PURCH_READ_NEXT_SORTED_BYNAME: Final[_Plan] = _Plan(
    "Purch-Read-Next-Sorted-ByName",
    "L1110-L1113",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_NAME),
    ),
)


def purch_read_next_sorted_byname(ctx: FacadeContext) -> StatusPair:
    """``Purch-Read-Next-Sorted-ByName`` [copybooks/Proc-ACAS-FH-Calls.cob:L1110-L1113].

    Sets function code 31, which ``acas022`` does dispatch [common/acas022.cbl:L344].
    Note the spelling: ``ByName`` unhyphenated, where the Sales equivalent writes ``By-
    Name``. Preserved, not tidied.
    """
    return _perform(ctx, _E_PURCH_READ_NEXT_SORTED_BYNAME)


_E_PURCH_READ_INDEXED: Final[_Plan] = _Plan(
    "Purch-Read-Indexed",
    "L1115-L1119",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def purch_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Purch-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1115-L1119]."""
    return _perform(ctx, _E_PURCH_READ_INDEXED)


_E_PURCH_WRITE: Final[_Plan] = _Plan(
    "Purch-Write",
    "L1121-L1124",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def purch_write(ctx: FacadeContext) -> StatusPair:
    """``Purch-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1121-L1124]."""
    return _perform(ctx, _E_PURCH_WRITE)


_E_PURCH_REWRITE: Final[_Plan] = _Plan(
    "Purch-Rewrite",
    "L1126-L1129",
    "acas022",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def purch_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Purch-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1126-L1129]."""
    return _perform(ctx, _E_PURCH_REWRITE)


_E_DELFOLIO_OPEN: Final[_Plan] = _Plan(
    "DelFolio-Open",
    "L1133-L1136",
    "acas023",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def delfolio_open(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1133-L1136]."""
    return _perform(ctx, _E_DELFOLIO_OPEN)


_E_DELFOLIO_OPEN_INPUT: Final[_Plan] = _Plan(
    "DelFolio-Open-Input",
    "L1138-L1141",
    "acas023",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def delfolio_open_input(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1138-L1141]."""
    return _perform(ctx, _E_DELFOLIO_OPEN_INPUT)


_E_DELFOLIO_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "DelFolio-Open-Output",
    "L1143-L1146",
    "acas023",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def delfolio_open_output(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1143-L1146]."""
    return _perform(ctx, _E_DELFOLIO_OPEN_OUTPUT)


_E_DELFOLIO_CLOSE: Final[_Plan] = _Plan(
    "DelFolio-Close",
    "L1148-L1151",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def delfolio_close(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1148-L1151]."""
    return _perform(ctx, _E_DELFOLIO_CLOSE)


_E_DELFOLIO_DELETE: Final[_Plan] = _Plan(
    "DelFolio-Delete",
    "L1153-L1157",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delfolio_delete(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1153-L1157]."""
    return _perform(ctx, _E_DELFOLIO_DELETE)


_E_DELFOLIO_DELETE_ALL: Final[_Plan] = _Plan(
    "DelFolio-Delete-All",
    "L1159-L1163",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def delfolio_delete_all(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1159-L1163]."""
    return _perform(ctx, _E_DELFOLIO_DELETE_ALL)


_E_DELFOLIO_START: Final[_Plan] = _Plan(
    "DelFolio-Start",
    "L1165-L1168",
    "acas023",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def delfolio_start(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1165-L1168].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_DELFOLIO_START)


_E_DELFOLIO_READ_NEXT: Final[_Plan] = _Plan(
    "DelFolio-Read-Next",
    "L1170-L1173",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def delfolio_read_next(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1170-L1173]."""
    return _perform(ctx, _E_DELFOLIO_READ_NEXT)


_E_DELFOLIO_READ_INDEXED: Final[_Plan] = _Plan(
    "DelFolio-Read-Indexed",
    "L1175-L1179",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def delfolio_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1175-L1179]."""
    return _perform(ctx, _E_DELFOLIO_READ_INDEXED)


_E_DELFOLIO_WRITE: Final[_Plan] = _Plan(
    "DelFolio-Write",
    "L1181-L1184",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def delfolio_write(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1181-L1184]."""
    return _perform(ctx, _E_DELFOLIO_WRITE)


_E_DELFOLIO_REWRITE: Final[_Plan] = _Plan(
    "DelFolio-Rewrite",
    "L1186-L1189",
    "acas023",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def delfolio_rewrite(ctx: FacadeContext) -> StatusPair:
    """``DelFolio-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1186-L1189]."""
    return _perform(ctx, _E_DELFOLIO_REWRITE)


_E_PINVOICE_OPEN: Final[_Plan] = _Plan(
    "PInvoice-Open",
    "L1193-L1196",
    "acas026",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def pinvoice_open(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1193-L1196]."""
    return _perform(ctx, _E_PINVOICE_OPEN)


_E_PINVOICE_OPEN_INPUT: Final[_Plan] = _Plan(
    "PInvoice-Open-Input",
    "L1198-L1201",
    "acas026",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def pinvoice_open_input(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1198-L1201]."""
    return _perform(ctx, _E_PINVOICE_OPEN_INPUT)


_E_PINVOICE_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "PInvoice-Open-Output",
    "L1203-L1206",
    "acas026",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def pinvoice_open_output(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1203-L1206]."""
    return _perform(ctx, _E_PINVOICE_OPEN_OUTPUT)


_E_PINVOICE_CLOSE: Final[_Plan] = _Plan(
    "PInvoice-Close",
    "L1208-L1211",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def pinvoice_close(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1208-L1211]."""
    return _perform(ctx, _E_PINVOICE_CLOSE)


_E_PINVOICE_DELETE: Final[_Plan] = _Plan(
    "PInvoice-Delete",
    "L1213-L1217",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def pinvoice_delete(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1213-L1217]."""
    return _perform(ctx, _E_PINVOICE_DELETE)


_E_PINVOICE_DELETE_ALL: Final[_Plan] = _Plan(
    "PInvoice-Delete-All",
    "L1219-L1223",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def pinvoice_delete_all(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1219-L1223]."""
    return _perform(ctx, _E_PINVOICE_DELETE_ALL)


_E_PINVOICE_START: Final[_Plan] = _Plan(
    "PInvoice-Start",
    "L1225-L1228",
    "acas026",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def pinvoice_start(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1225-L1228].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_PINVOICE_START)


_E_PINVOICE_READ_NEXT: Final[_Plan] = _Plan(
    "PInvoice-Read-Next",
    "L1230-L1233",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def pinvoice_read_next(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1230-L1233]."""
    return _perform(ctx, _E_PINVOICE_READ_NEXT)


_E_PINVOICE_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "PInvoice-Read-Next-Header",
    "L1235-L1238",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def pinvoice_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L1235-L1238]."""
    return _perform(ctx, _E_PINVOICE_READ_NEXT_HEADER)


_E_PINVOICE_READ_INDEXED: Final[_Plan] = _Plan(
    "PInvoice-Read-Indexed",
    "L1240-L1244",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def pinvoice_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1240-L1244]."""
    return _perform(ctx, _E_PINVOICE_READ_INDEXED)


_E_PINVOICE_WRITE: Final[_Plan] = _Plan(
    "PInvoice-Write",
    "L1246-L1249",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def pinvoice_write(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1246-L1249]."""
    return _perform(ctx, _E_PINVOICE_WRITE)


_E_PINVOICE_REWRITE: Final[_Plan] = _Plan(
    "PInvoice-Rewrite",
    "L1251-L1254",
    "acas026",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def pinvoice_rewrite(ctx: FacadeContext) -> StatusPair:
    """``PInvoice-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1251-L1254]."""
    return _perform(ctx, _E_PINVOICE_REWRITE)


_E_OTM5_OPEN: Final[_Plan] = _Plan(
    "OTM5-Open",
    "L1258-L1261",
    "acas029",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def otm5_open(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1258-L1261]."""
    return _perform(ctx, _E_OTM5_OPEN)


_E_OTM5_OPEN_INPUT: Final[_Plan] = _Plan(
    "OTM5-Open-Input",
    "L1263-L1266",
    "acas029",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def otm5_open_input(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1263-L1266]."""
    return _perform(ctx, _E_OTM5_OPEN_INPUT)


_E_OTM5_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "OTM5-Open-Output",
    "L1268-L1271",
    "acas029",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def otm5_open_output(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1268-L1271]."""
    return _perform(ctx, _E_OTM5_OPEN_OUTPUT)


_E_OTM5_CLOSE: Final[_Plan] = _Plan(
    "OTM5-Close",
    "L1273-L1276",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def otm5_close(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1273-L1276]."""
    return _perform(ctx, _E_OTM5_CLOSE)


_E_OTM5_DELETE: Final[_Plan] = _Plan(
    "OTM5-Delete",
    "L1278-L1282",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def otm5_delete(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1278-L1282]."""
    return _perform(ctx, _E_OTM5_DELETE)


_E_OTM5_START: Final[_Plan] = _Plan(
    "OTM5-Start",
    "L1284-L1287",
    "acas029",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def otm5_start(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1284-L1287].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_OTM5_START)


_E_OTM5_READ_NEXT: Final[_Plan] = _Plan(
    "OTM5-Read-Next",
    "L1289-L1292",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def otm5_read_next(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1289-L1292]."""
    return _perform(ctx, _E_OTM5_READ_NEXT)


_E_OTM5_READ_INDEXED: Final[_Plan] = _Plan(
    "OTM5-Read-Indexed",
    "L1294-L1298",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def otm5_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1294-L1298]."""
    return _perform(ctx, _E_OTM5_READ_INDEXED)


_E_OTM5_READ_NEXT_SORTED_BY_BATCH: Final[_Plan] = _Plan(
    "OTM5-Read-Next-Sorted-By-Batch",
    "L1300-L1303",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_BATCH),
    ),
)


def otm5_read_next_sorted_by_batch(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Next-Sorted-By-Batch`` [copybooks/Proc-ACAS-FH-Calls.cob:L1300-L1303].

    ``otm5MT`` routes the code to ``ba140-Process-Read-Next``
    [common/otm5MT.cbl:L425-L426], which ``dal/acas029_otm5.py`` publishes as
    ``read_next_sorted_by_batch``.
    """
    return _perform(ctx, _E_OTM5_READ_NEXT_SORTED_BY_BATCH)


_E_OTM5_READ_NEXT_SORTED_BY_CUST: Final[_Plan] = _Plan(
    "OTM5-Read-Next-Sorted-By-Cust",
    "L1305-L1308",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_BY_CUST),
    ),
)


def otm5_read_next_sorted_by_cust(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Read-Next-Sorted-By-Cust`` [copybooks/Proc-ACAS-FH-Calls.cob:L1305-L1308].

    ``dal/acas029_otm5.py`` publishes it as ``read_next_sorted_by_cust``. Reached on the
    RDB path only, for the reason given on :func:`otm5_read_next_sorted_by_batch`, and
    answering ``(10, 10)`` for the same reason - anomaly N-sorted-order-is-a-syntax-
    error.
    """
    return _perform(ctx, _E_OTM5_READ_NEXT_SORTED_BY_CUST)


_E_OTM5_WRITE: Final[_Plan] = _Plan(
    "OTM5-Write",
    "L1310-L1313",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def otm5_write(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1310-L1313]."""
    return _perform(ctx, _E_OTM5_WRITE)


_E_OTM5_REWRITE: Final[_Plan] = _Plan(
    "OTM5-Rewrite",
    "L1315-L1318",
    "acas029",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def otm5_rewrite(ctx: FacadeContext) -> StatusPair:
    """``OTM5-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1315-L1318]."""
    return _perform(ctx, _E_OTM5_REWRITE)


_E_PLAUTOGEN_OPEN: Final[_Plan] = _Plan(
    "PLautogen-Open",
    "L1323-L1326",
    "acas030",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def plautogen_open(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1323-L1326]."""
    return _perform(ctx, _E_PLAUTOGEN_OPEN)


_E_PLAUTOGEN_OPEN_INPUT: Final[_Plan] = _Plan(
    "PLautogen-Open-Input",
    "L1328-L1331",
    "acas030",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def plautogen_open_input(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1328-L1331]."""
    return _perform(ctx, _E_PLAUTOGEN_OPEN_INPUT)


_E_PLAUTOGEN_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "PLautogen-Open-Output",
    "L1333-L1336",
    "acas030",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def plautogen_open_output(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1333-L1336]."""
    return _perform(ctx, _E_PLAUTOGEN_OPEN_OUTPUT)


_E_PLAUTOGEN_CLOSE: Final[_Plan] = _Plan(
    "PLautogen-Close",
    "L1338-L1341",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def plautogen_close(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1338-L1341]."""
    return _perform(ctx, _E_PLAUTOGEN_CLOSE)


_E_PLAUTOGEN_DELETE: Final[_Plan] = _Plan(
    "PLautogen-Delete",
    "L1343-L1347",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def plautogen_delete(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1343-L1347]."""
    return _perform(ctx, _E_PLAUTOGEN_DELETE)


_E_PLAUTOGEN_DELETE_ALL: Final[_Plan] = _Plan(
    "PLautogen-Delete-All",
    "L1349-L1353",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def plautogen_delete_all(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1349-L1353]."""
    return _perform(ctx, _E_PLAUTOGEN_DELETE_ALL)


_E_PLAUTOGEN_START: Final[_Plan] = _Plan(
    "PLautogen-Start",
    "L1355-L1358",
    "acas030",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def plautogen_start(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1355-L1358].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_PLAUTOGEN_START)


_E_PLAUTOGEN_READ_NEXT: Final[_Plan] = _Plan(
    "PLautogen-Read-Next",
    "L1360-L1363",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def plautogen_read_next(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1360-L1363]."""
    return _perform(ctx, _E_PLAUTOGEN_READ_NEXT)


_E_PLAUTOGEN_READ_NEXT_HEADER: Final[_Plan] = _Plan(
    "PLautogen-Read-Next-Header",
    "L1365-L1368",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT_HEADER),
    ),
)


def plautogen_read_next_header(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Read-Next-Header`` [copybooks/Proc-ACAS-FH-Calls.cob:L1365-L1368]."""
    return _perform(ctx, _E_PLAUTOGEN_READ_NEXT_HEADER)


_E_PLAUTOGEN_READ_INDEXED: Final[_Plan] = _Plan(
    "PLautogen-Read-Indexed",
    "L1370-L1374",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def plautogen_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1370-L1374]."""
    return _perform(ctx, _E_PLAUTOGEN_READ_INDEXED)


_E_PLAUTOGEN_WRITE: Final[_Plan] = _Plan(
    "PLautogen-Write",
    "L1376-L1379",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def plautogen_write(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1376-L1379]."""
    return _perform(ctx, _E_PLAUTOGEN_WRITE)


_E_PLAUTOGEN_REWRITE: Final[_Plan] = _Plan(
    "PLautogen-Rewrite",
    "L1381-L1384",
    "acas030",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def plautogen_rewrite(ctx: FacadeContext) -> StatusPair:
    """``PLautogen-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1381-L1384]."""
    return _perform(ctx, _E_PLAUTOGEN_REWRITE)


_E_PAYMENTS_OPEN: Final[_Plan] = _Plan(
    "Payments-Open",
    "L1388-L1391",
    "acas032",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def payments_open(ctx: FacadeContext) -> StatusPair:
    """``Payments-Open`` [copybooks/Proc-ACAS-FH-Calls.cob:L1388-L1391]."""
    return _perform(ctx, _E_PAYMENTS_OPEN)


_E_PAYMENTS_OPEN_INPUT: Final[_Plan] = _Plan(
    "Payments-Open-Input",
    "L1393-L1396",
    "acas032",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def payments_open_input(ctx: FacadeContext) -> StatusPair:
    """``Payments-Open-Input`` [copybooks/Proc-ACAS-FH-Calls.cob:L1393-L1396]."""
    return _perform(ctx, _E_PAYMENTS_OPEN_INPUT)


_E_PAYMENTS_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "Payments-Open-Output",
    "L1398-L1401",
    "acas032",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
)


def payments_open_output(ctx: FacadeContext) -> StatusPair:
    """``Payments-Open-Output`` [copybooks/Proc-ACAS-FH-Calls.cob:L1398-L1401]."""
    return _perform(ctx, _E_PAYMENTS_OPEN_OUTPUT)


_E_PAYMENTS_CLOSE: Final[_Plan] = _Plan(
    "Payments-Close",
    "L1403-L1406",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def payments_close(ctx: FacadeContext) -> StatusPair:
    """``Payments-Close`` [copybooks/Proc-ACAS-FH-Calls.cob:L1403-L1406]."""
    return _perform(ctx, _E_PAYMENTS_CLOSE)


_E_PAYMENTS_DELETE: Final[_Plan] = _Plan(
    "Payments-Delete",
    "L1408-L1412",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def payments_delete(ctx: FacadeContext) -> StatusPair:
    """``Payments-Delete`` [copybooks/Proc-ACAS-FH-Calls.cob:L1408-L1412]."""
    return _perform(ctx, _E_PAYMENTS_DELETE)


_E_PAYMENTS_DELETE_ALL: Final[_Plan] = _Plan(
    "Payments-Delete-All",
    "L1414-L1418",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE_ALL),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
    ),
)


def payments_delete_all(ctx: FacadeContext) -> StatusPair:
    """``Payments-Delete-All`` [copybooks/Proc-ACAS-FH-Calls.cob:L1414-L1418]."""
    return _perform(ctx, _E_PAYMENTS_DELETE_ALL)


_E_PAYMENTS_START: Final[_Plan] = _Plan(
    "Payments-Start",
    "L1420-L1423",
    "acas032",
    (
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def payments_start(ctx: FacadeContext) -> StatusPair:
    """``Payments-Start`` [copybooks/Proc-ACAS-FH-Calls.cob:L1420-L1423].

    Deliberately does NOT clear ``Access-Type``: on a START that field carries the
    relation, 5 through 9 of [copybooks/wsfnctn.cob:L112-L116], and the caller sets it.
    Clearing it would change which row is found.
    """
    return _perform(ctx, _E_PAYMENTS_START)


_E_PAYMENTS_READ_NEXT: Final[_Plan] = _Plan(
    "Payments-Read-Next",
    "L1425-L1428",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def payments_read_next(ctx: FacadeContext) -> StatusPair:
    """``Payments-Read-Next`` [copybooks/Proc-ACAS-FH-Calls.cob:L1425-L1428]."""
    return _perform(ctx, _E_PAYMENTS_READ_NEXT)


_E_PAYMENTS_READ_INDEXED: Final[_Plan] = _Plan(
    "Payments-Read-Indexed",
    "L1430-L1434",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_KEY_NO, PRIMARY_FILE_KEY_NO),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def payments_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``Payments-Read-Indexed`` [copybooks/Proc-ACAS-FH-Calls.cob:L1430-L1434]."""
    return _perform(ctx, _E_PAYMENTS_READ_INDEXED)


_E_PAYMENTS_WRITE: Final[_Plan] = _Plan(
    "Payments-Write",
    "L1436-L1439",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def payments_write(ctx: FacadeContext) -> StatusPair:
    """``Payments-Write`` [copybooks/Proc-ACAS-FH-Calls.cob:L1436-L1439]."""
    return _perform(ctx, _E_PAYMENTS_WRITE)


_E_PAYMENTS_REWRITE: Final[_Plan] = _Plan(
    "Payments-Rewrite",
    "L1441-L1444",
    "acas032",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def payments_rewrite(ctx: FacadeContext) -> StatusPair:
    """``Payments-Rewrite`` [copybooks/Proc-ACAS-FH-Calls.cob:L1441-L1444]."""
    return _perform(ctx, _E_PAYMENTS_REWRITE)


# Vocabulary two: the handler-named verbs of [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob]
# 42 paragraphs across six handlers [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob: L92-L314].


_H_ACAS000_OPEN: Final[_Plan] = _Plan(
    "acas000-Open",
    "L92-L96",
    "acas000-handler",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="acas000",
)


def acas000_open(ctx: FacadeContext) -> StatusPair:
    """``acas000-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L92-L96]."""
    return _perform(ctx, _H_ACAS000_OPEN)


_H_ACAS000_OPEN_INPUT: Final[_Plan] = _Plan(
    "acas000-Open-Input",
    "L98-L102",
    "acas000-handler",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="acas000",
    check_first=True,
)


def acas000_open_input(ctx: FacadeContext) -> StatusPair:
    """``acas000-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L98-L102].

    THE CHECK RUNS BEFORE THE DISPATCH. Alone among all 42 verb paragraphs, this one
    performs ``acas000-Check-4-Errors`` and only then performs ``acas000``.
    """
    return _perform(ctx, _H_ACAS000_OPEN_INPUT)


_H_ACAS000_CLOSE: Final[_Plan] = _Plan(
    "acas000-Close",
    "L104-L107",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acas000_close(ctx: FacadeContext) -> StatusPair:
    """``acas000-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L104-L107].

    No error check. Only the open family carries one, in all six handlers - close, read,
    write, rewrite, START and delete carry none.
    """
    return _perform(ctx, _H_ACAS000_CLOSE)


_H_ACAS000_READ_NEXT: Final[_Plan] = _Plan(
    "acas000-Read-Next",
    "L109-L112",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acas000_read_next(ctx: FacadeContext) -> StatusPair:
    """``acas000-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L109-L112]."""
    return _perform(ctx, _H_ACAS000_READ_NEXT)


_H_ACAS000_READ_INDEXED: Final[_Plan] = _Plan(
    "acas000-Read-Indexed",
    "L114-L117",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def acas000_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``acas000-Read-Indexed`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L114-L117]."""
    return _perform(ctx, _H_ACAS000_READ_INDEXED)


_H_ACAS000_WRITE: Final[_Plan] = _Plan(
    "acas000-Write",
    "L119-L122",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acas000_write(ctx: FacadeContext) -> StatusPair:
    """``acas000-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L119-L122]."""
    return _perform(ctx, _H_ACAS000_WRITE)


_H_ACAS000_REWRITE: Final[_Plan] = _Plan(
    "acas000-Rewrite",
    "L124-L127",
    "acas000-handler",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acas000_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acas000-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L124-L127]."""
    return _perform(ctx, _H_ACAS000_REWRITE)


_H_ACAS008_OPEN: Final[_Plan] = _Plan(
    "acas008-Open",
    "L130-L134",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="acas008",
)


def acas008_open(ctx: FacadeContext) -> StatusPair:
    """``acas008-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L130-L134]."""
    return _perform(ctx, _H_ACAS008_OPEN)


_H_ACAS008_OPEN_INPUT: Final[_Plan] = _Plan(
    "acas008-Open-Input",
    "L136-L140",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="acas008",
)


def acas008_open_input(ctx: FacadeContext) -> StatusPair:
    """``acas008-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L136-L140]."""
    return _perform(ctx, _H_ACAS008_OPEN_INPUT)


_H_ACAS008_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "acas008-Open-Output",
    "L142-L146",
    "acas008",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
    check="acas008",
)


def acas008_open_output(ctx: FacadeContext) -> StatusPair:
    """``acas008-Open-Output`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L142-L146]."""
    return _perform(ctx, _H_ACAS008_OPEN_OUTPUT)


_H_ACAS008_CLOSE: Final[_Plan] = _Plan(
    "acas008-Close",
    "L148-L151",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acas008_close(ctx: FacadeContext) -> StatusPair:
    """``acas008-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L148-L151]."""
    return _perform(ctx, _H_ACAS008_CLOSE)


_H_ACAS008_READ_NEXT: Final[_Plan] = _Plan(
    "acas008-Read-Next",
    "L153-L156",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acas008_read_next(ctx: FacadeContext) -> StatusPair:
    """``acas008-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L153-L156]."""
    return _perform(ctx, _H_ACAS008_READ_NEXT)


_H_ACAS008_WRITE: Final[_Plan] = _Plan(
    "acas008-Write",
    "L158-L161",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acas008_write(ctx: FacadeContext) -> StatusPair:
    """``acas008-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L158-L161]."""
    return _perform(ctx, _H_ACAS008_WRITE)


_H_ACAS008_REWRITE: Final[_Plan] = _Plan(
    "acas008-Rewrite",
    "L163-L166",
    "acas008",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acas008_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acas008-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L163-L166].

    PUBLISHED AND GUARANTEED TO FAIL - Agent Action Plan section 0.6.7 entry 6.
    ``acas008`` refuses rewrite unconditionally at entry [common/acas008.cbl:L299-L307]
    because the transfer file is sequential, answering ``FS-Reply`` 99 with ``WE-Error``
    988.
    """
    return _perform(ctx, _H_ACAS008_REWRITE)


_H_ACASIRSUB1_OPEN: Final[_Plan] = _Plan(
    "acasirsub1-Open",
    "L169-L173",
    "acasirsub1",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="irsub1",
)


def acasirsub1_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L169-L173]."""
    return _perform(ctx, _H_ACASIRSUB1_OPEN)


_H_ACASIRSUB1_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub1-Open-Input",
    "L175-L179",
    "acasirsub1",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="irsub1",
)


def acasirsub1_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L175-L179]."""
    return _perform(ctx, _H_ACASIRSUB1_OPEN_INPUT)


_H_ACASIRSUB1_OPEN_OUTPUT: Final[_Plan] = _Plan(
    "acasirsub1-Open-Output",
    "L181-L185",
    "acasirsub1",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.OUTPUT),
    ),
    check="irsub1",
)


def acasirsub1_open_output(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Open-Output`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L181-L185].
    """
    return _perform(ctx, _H_ACASIRSUB1_OPEN_OUTPUT)


_H_ACASIRSUB1_CLOSE: Final[_Plan] = _Plan(
    "acasirsub1-Close",
    "L187-L190",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub1_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L187-L190]."""
    return _perform(ctx, _H_ACASIRSUB1_CLOSE)


_H_ACASIRSUB1_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub1-Read-Next",
    "L192-L195",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub1_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L192-L195]."""
    return _perform(ctx, _H_ACASIRSUB1_READ_NEXT)


_H_ACASIRSUB1_READ_INDEXED: Final[_Plan] = _Plan(
    "acasirsub1-Read-Indexed",
    "L197-L200",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_INDEXED),
    ),
)


def acasirsub1_read_indexed(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Read-Indexed`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L197-L200].
    """
    return _perform(ctx, _H_ACASIRSUB1_READ_INDEXED)


_H_ACASIRSUB1_START: Final[_Plan] = _Plan(
    "acasirsub1-Start",
    "L202-L205",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.START),
    ),
)


def acasirsub1_start(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Start`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L202-L205].

    Clears ``Access-Type`` before setting the START function, and that destroys the
    relation. On a START that field carries 5 through 9 of
    [copybooks/wsfnctn.cob:L112-L116]; zero is none of them.
    """
    return _perform(ctx, _H_ACASIRSUB1_START)


_H_ACASIRSUB1_WRITE: Final[_Plan] = _Plan(
    "acasirsub1-Write",
    "L207-L210",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub1_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L207-L210]."""
    return _perform(ctx, _H_ACASIRSUB1_WRITE)


_H_ACASIRSUB1_DELETE: Final[_Plan] = _Plan(
    "acasirsub1-Delete",
    "L212-L215",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.DELETE),
    ),
)


def acasirsub1_delete(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Delete`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L212-L215]."""
    return _perform(ctx, _H_ACASIRSUB1_DELETE)


_H_ACASIRSUB1_REWRITE: Final[_Plan] = _Plan(
    "acasirsub1-Rewrite",
    "L217-L220",
    "acasirsub1",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub1_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub1-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L217-L220]."""
    return _perform(ctx, _H_ACASIRSUB1_REWRITE)


_H_ACASIRSUB3_OPEN: Final[_Plan] = _Plan(
    "acasirsub3-Open",
    "L223-L227",
    "acasirsub3",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="irsub3",
)


def acasirsub3_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L223-L227]."""
    return _perform(ctx, _H_ACASIRSUB3_OPEN)


_H_ACASIRSUB3_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub3-Open-Input",
    "L229-L233",
    "acasirsub3",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="irsub3",
)


def acasirsub3_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L229-L233]."""
    return _perform(ctx, _H_ACASIRSUB3_OPEN_INPUT)


_H_ACASIRSUB3_CLOSE: Final[_Plan] = _Plan(
    "acasirsub3-Close",
    "L235-L238",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub3_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L235-L238]."""
    return _perform(ctx, _H_ACASIRSUB3_CLOSE)


_H_ACASIRSUB3_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub3-Read-Next",
    "L240-L243",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub3_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L240-L243]."""
    return _perform(ctx, _H_ACASIRSUB3_READ_NEXT)


_H_ACASIRSUB3_WRITE: Final[_Plan] = _Plan(
    "acasirsub3-Write",
    "L245-L248",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub3_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L245-L248]."""
    return _perform(ctx, _H_ACASIRSUB3_WRITE)


_H_ACASIRSUB3_REWRITE: Final[_Plan] = _Plan(
    "acasirsub3-ReWrite",
    "L250-L253",
    "acasirsub3",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub3_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3-ReWrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L250-L253]."""
    return _perform(ctx, _H_ACASIRSUB3_REWRITE)


def acasirsub3(ctx: FacadeContext) -> StatusPair:
    """``acasirsub3`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L57-L64].

    The bare form is NOT the same operation as ``acasirsub3-Read-Next``, and the
    difference is load-bearing rather than cosmetic. The verb paragraph moves ``zero to
    Access-Type`` before it dispatches
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L240-L243].
    """
    _dispatch_acasirsub3(ctx)
    return StatusPair(ctx.file_access.fs_reply, ctx.file_access.we_error)


_H_ACASIRSUB4_OPEN: Final[_Plan] = _Plan(
    "acasirsub4-Open",
    "L256-L259",
    "acasirsub4",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
)


def acasirsub4_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L256-L259]."""
    return _perform(ctx, _H_ACASIRSUB4_OPEN)


_H_ACASIRSUB4_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub4-Open-Input",
    "L261-L264",
    "acasirsub4",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
)


def acasirsub4_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L261-L264]."""
    return _perform(ctx, _H_ACASIRSUB4_OPEN_INPUT)


_H_ACASIRSUB4_CLOSE: Final[_Plan] = _Plan(
    "acasirsub4-Close",
    "L266-L269",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub4_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L266-L269]."""
    return _perform(ctx, _H_ACASIRSUB4_CLOSE)


_H_ACASIRSUB4_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub4-Read-Next",
    "L271-L274",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub4_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L271-L274]."""
    return _perform(ctx, _H_ACASIRSUB4_READ_NEXT)


_H_ACASIRSUB4_WRITE: Final[_Plan] = _Plan(
    "acasirsub4-Write",
    "L276-L279",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub4_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L276-L279]."""
    return _perform(ctx, _H_ACASIRSUB4_WRITE)


_H_ACASIRSUB4_REWRITE: Final[_Plan] = _Plan(
    "acasirsub4-Rewrite",
    "L281-L284",
    "acasirsub4",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub4_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub4-Rewrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L281-L284]."""
    return _perform(ctx, _H_ACASIRSUB4_REWRITE)


_H_ACASIRSUB5_OPEN: Final[_Plan] = _Plan(
    "acasirsub5-Open",
    "L287-L291",
    "acasirsub5",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.I_O),
    ),
    check="irsub5",
)


def acasirsub5_open(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Open`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L287-L291]."""
    return _perform(ctx, _H_ACASIRSUB5_OPEN)


_H_ACASIRSUB5_OPEN_INPUT: Final[_Plan] = _Plan(
    "acasirsub5-Open-Input",
    "L293-L297",
    "acasirsub5",
    (
        (_FILE_FUNCTION, FileFunction.OPEN),
        (_ACCESS_TYPE, AccessType.INPUT),
    ),
    check="irsub5",
)


def acasirsub5_open_input(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Open-Input`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L293-L297]."""
    return _perform(ctx, _H_ACASIRSUB5_OPEN_INPUT)


_H_ACASIRSUB5_CLOSE: Final[_Plan] = _Plan(
    "acasirsub5-Close",
    "L299-L302",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.CLOSE),
    ),
)


def acasirsub5_close(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Close`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L299-L302]."""
    return _perform(ctx, _H_ACASIRSUB5_CLOSE)


_H_ACASIRSUB5_READ_NEXT: Final[_Plan] = _Plan(
    "acasirsub5-Read-Next",
    "L304-L307",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.READ_NEXT),
    ),
)


def acasirsub5_read_next(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Read-Next`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L304-L307]."""
    return _perform(ctx, _H_ACASIRSUB5_READ_NEXT)


_H_ACASIRSUB5_WRITE: Final[_Plan] = _Plan(
    "acasirsub5-Write",
    "L309-L312",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.WRITE),
    ),
)


def acasirsub5_write(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-Write`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L309-L312]."""
    return _perform(ctx, _H_ACASIRSUB5_WRITE)


_H_ACASIRSUB5_REWRITE: Final[_Plan] = _Plan(
    "acasirsub5-ReWrite",
    "L314-L317",
    "acasirsub5",
    (
        (_ACCESS_TYPE, ACCESS_TYPE_LOGGING_RESET),
        (_FILE_FUNCTION, FileFunction.RE_WRITE),
    ),
)


def acasirsub5_rewrite(ctx: FacadeContext) -> StatusPair:
    """``acasirsub5-ReWrite`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L314-L317]."""
    return _perform(ctx, _H_ACASIRSUB5_REWRITE)


# The five error-check paragraphs [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L353].
# FIVE checks for SIX dispatched handlers.


def acas000_check_4_errors(ctx: FacadeContext) -> None:
    """``acas000-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L325].
    """
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR911 at 0801`` becomes a log record: no database effect, and per
        # Agent Action Plan section 0.3.4 it must not alter control flow.
        _LOG.error(
            "IR911 acas000/systemMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acas000-Close`` - a real database effect inside an error path, so it
        # is preserved.
        acas000_close(ctx)
        open_error_continued(ctx)


def acas008_check_4_errors(ctx: FacadeContext) -> None:
    """``acas008-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L327-L332].
    """
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR916 at 0801`` becomes a log record: no database effect, and per
        # Agent Action Plan section 0.3.4 it must not alter control flow.
        _LOG.error(
            "IR916 acas008/slpostingMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acas008-Close`` - a real database effect inside an error path, so it
        # is preserved.
        acas008_close(ctx)
        open_error_continued(ctx)


def irsub1_check_4_errors(ctx: FacadeContext) -> None:
    """``irsub1-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L334-L339]."""
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR912 at 0801`` becomes a log record: no database effect, and per
        # Agent Action Plan section 0.3.4 it must not alter control flow.
        _LOG.error(
            "IR912 acasirsub1/irsnominalMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acasirsub1-Close`` - a real database effect inside an error path, so
        # it is preserved.
        acasirsub1_close(ctx)
        open_error_continued(ctx)


def irsub3_check_4_errors(ctx: FacadeContext) -> None:
    """``irsub3-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L341-L346]."""
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR913 at 0801`` becomes a log record: no database effect, and per
        # Agent Action Plan section 0.3.4 it must not alter control flow.
        _LOG.error(
            "IR913 acasirsub3/irsdfltMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acasirsub3-Close`` - a real database effect inside an error path, so
        # it is preserved.
        acasirsub3_close(ctx)
        open_error_continued(ctx)


def irsub5_check_4_errors(ctx: FacadeContext) -> None:
    """``irsub5-Check-4-Errors`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L348-L353]."""
    if ctx.file_access.fs_reply != FsReply.SUCCESS:
        # ``display IR915 at 0801`` becomes a log record: no database effect, and per
        # Agent Action Plan section 0.3.4 it must not alter control flow.
        _LOG.error(
            "IR915 acasirsub5/irsfinalMT processing: FS-Reply=%s WE-Error=%s",
            ctx.file_access.fs_reply,
            ctx.file_access.we_error,
        )
        # ``perform acasirsub5-Close`` - a real database effect inside an error path, so
        # it is preserved.
        acasirsub5_close(ctx)
        open_error_continued(ctx)


#: Error-check paragraph to implementation, keyed as ``_Plan.check`` names them.
#: ``acasirsub4`` has NO entry, by design - five checks for six dispatched handlers
#: [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L320-L348].
_CHECKS: Final[Mapping[str, Callable[[FacadeContext], None]]] = MappingProxyType({
    "acas000": acas000_check_4_errors,
    "acas008": acas008_check_4_errors,
    "irsub1": irsub1_check_4_errors,
    "irsub3": irsub3_check_4_errors,
    "irsub5": irsub5_check_4_errors,
})


def open_error_continued(ctx: FacadeContext) -> NoReturn:
    """``Open-Error-Continued`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364].

    The paragraph's own comment reads "If here we cannot continue as its a major
    failure". All five error checks ``go to`` here, so one paragraph aborts the
    caller for any of them.

    It displays five fields and waits for a keypress
    [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L356-L363] and then executes
    ``goback`` [copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]. Reproduced as:
    the five displays become log records, the wait is dropped, and the
    ``goback`` becomes :exc:`FacadeGoback`.

    Omitted: the ``display SY008`` [:L362], the ``accept Accept-Reply at 1335``
    [:L363] and the screen positions. Agent Action Plan section 0.3.4 governs all
    three - a prompt whose only effect is to block a terminal is dropped, and
    "where such a prompt sits inside an error path that then transfers control, the
    control transfer is preserved and only the pause is removed". ``SY008`` is that
    prompt's text, "Note message & Hit return" [common/ACAS.cbl:L334], and quoting
    it in a log line, or logging a notice that it was not quoted, is still putting
    an unanswerable prompt in front of an operator. The transfer - the ``goback``
    at [:L364] - is preserved.

    THE FIVE DISPLAYS BECOME ONE RECORD, not four. [:L356-L361] are six
    ``display`` statements building one diagnostic out of four fields, and emitting
    a record per field made one failure look like four, none of which carried the
    identity of the handler that failed. ``SQL-Msg`` [:L361] is dropped from the
    record entirely: it is a ``pic x(512)`` of driver free text, which for these
    tables renders the statement and its bound values, and ``redact_for_log`` was
    escaping it rather than removing it (CWE-532).

    Never raises :exc:`SystemExit` and never terminates the process. ``goback``
    returns to the COBOL program's caller, which here is a ``programs/*`` module
    that may still have end-of-job work whose partial state must survive.
    """
    file_access = ctx.file_access
    logging_data = file_access.logging_data

    # L356-L361, the six displays, as ONE record through the shared reporter, so
    # that this failure reads like every other failure in the package: the status
    # pair from [:L356-L359] and the SQLSTATE from [:L360], with the stable error
    # category derived from them. `SQL-Err` is still read the way the bridges read
    # their fixed-width fields, up to the first space.
    log_handler_failure(
        _LOG,
        program="Proc-ZZ100-ACAS-IRS-Calls",
        paragraph="Open-Error-Continued",
        locator="[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L355-L364]",
        fs_reply=int(file_access.fs_reply),
        we_error=int(file_access.we_error),
        sql_err=_connection.cobol_string_delimited_by_space(logging_data.sql_err),
        sql_state=_connection.cobol_string_delimited_by_space(
            logging_data.sql_state
        ),
        detail="unrecoverable file-handler failure; the IRS convention's error "
        "check has already named the handler, and this paragraph cannot continue",
    )
    raise FacadeGoback(
        "Open-Error-Continued: unrecoverable file-handler failure; "
        "FS-Reply=%s WE-Error=%s. Reproduces the goback at "
        "[copybooks/Proc-ZZ100-ACAS-IRS-Calls.cob:L364]."
        % (file_access.fs_reply, file_access.we_error)
    )


__all__ = (
    "ACCESS_TYPE_LOGGING_RESET",
    "ALWAYS_REFUSED_BY_HANDLER",
    #  The one security-policy door, for the handlers that publish no
    #  keyword-only `transport` on their `dispatch`. Its companion is
    #  `FacadeContext.options`; see THE ONE SECURITY-POLICY CONTRACT.
    "declare_connection_policy",
    "FacadeContext",
    "FacadeError",
    "FacadeGoback",
    "PRIMARY_FILE_KEY_NO",
    "StatusPair",
    "UnsupportedEntityError",
    "acas000_check_4_errors",
    "acas000_close",
    "acas000_open",
    "acas000_open_input",
    "acas000_read_indexed",
    "acas000_read_next",
    "acas000_rewrite",
    "acas000_write",
    "acas008_check_4_errors",
    "acas008_close",
    "acas008_open",
    "acas008_open_input",
    "acas008_open_output",
    "acas008_read_next",
    "acas008_rewrite",
    "acas008_write",
    "acasirsub1_close",
    "acasirsub1_delete",
    "acasirsub1_open",
    "acasirsub1_open_input",
    "acasirsub1_open_output",
    "acasirsub1_read_indexed",
    "acasirsub1_read_next",
    "acasirsub1_rewrite",
    "acasirsub1_start",
    "acasirsub1_write",
    "acasirsub3",
    "acasirsub3_close",
    "acasirsub3_open",
    "acasirsub3_open_input",
    "acasirsub3_read_next",
    "acasirsub3_rewrite",
    "acasirsub3_write",
    "acasirsub4_close",
    "acasirsub4_open",
    "acasirsub4_open_input",
    "acasirsub4_read_next",
    "acasirsub4_rewrite",
    "acasirsub4_write",
    "acasirsub5_close",
    "acasirsub5_open",
    "acasirsub5_open_input",
    "acasirsub5_read_next",
    "acasirsub5_rewrite",
    "acasirsub5_write",
    "analysis_close",
    "analysis_delete",
    "analysis_open",
    "analysis_open_input",
    "analysis_open_output",
    "analysis_read_indexed",
    "analysis_read_next",
    "analysis_rewrite",
    "analysis_start",
    "analysis_write",
    "delfolio_close",
    "delfolio_delete",
    "delfolio_delete_all",
    "delfolio_open",
    "delfolio_open_input",
    "delfolio_open_output",
    "delfolio_read_indexed",
    "delfolio_read_next",
    "delfolio_rewrite",
    "delfolio_start",
    "delfolio_write",
    "delinvnos_close",
    "delinvnos_delete",
    "delinvnos_delete_all",
    "delinvnos_open",
    "delinvnos_open_input",
    "delinvnos_open_output",
    "delinvnos_read_indexed",
    "delinvnos_read_next",
    "delinvnos_rewrite",
    "delinvnos_start",
    "delinvnos_write",
    "delivery_close",
    "delivery_delete",
    "delivery_delete_all",
    "delivery_open",
    "delivery_open_input",
    "delivery_open_output",
    "delivery_read_indexed",
    "delivery_read_next",
    "delivery_rewrite",
    "delivery_start",
    "delivery_write",
    "gl_batch_close",
    "gl_batch_delete",
    "gl_batch_delete_all",
    "gl_batch_open",
    "gl_batch_open_extend",
    "gl_batch_open_input",
    "gl_batch_open_output",
    "gl_batch_read_indexed",
    "gl_batch_read_next",
    "gl_batch_rewrite",
    "gl_batch_start",
    "gl_batch_write",
    "gl_nominal_close",
    "gl_nominal_delete",
    "gl_nominal_open",
    "gl_nominal_open_extend",
    "gl_nominal_open_input",
    "gl_nominal_open_output",
    "gl_nominal_read_indexed",
    "gl_nominal_read_next",
    "gl_nominal_rewrite",
    "gl_nominal_start",
    "gl_nominal_write",
    "gl_posting_close",
    "gl_posting_delete",
    "gl_posting_delete_all",
    "gl_posting_open",
    "gl_posting_open_extend",
    "gl_posting_open_input",
    "gl_posting_open_output",
    "gl_posting_read_indexed",
    "gl_posting_read_next",
    "gl_posting_rewrite",
    "gl_posting_start",
    "gl_posting_write",
    "invoice_close",
    "invoice_delete",
    "invoice_delete_all",
    "invoice_open",
    "invoice_open_input",
    "invoice_open_output",
    "invoice_read_indexed",
    "invoice_read_next",
    "invoice_read_next_header",
    "invoice_rewrite",
    "invoice_start",
    "invoice_write",
    "irsub1_check_4_errors",
    "irsub3_check_4_errors",
    "irsub5_check_4_errors",
    "open_error_continued",
    "otm3_close",
    "otm3_delete",
    "otm3_open",
    "otm3_open_input",
    "otm3_open_output",
    "otm3_read_indexed",
    "otm3_read_next",
    "otm3_read_next_sorted_by_batch",
    "otm3_read_next_sorted_by_cust",
    "otm3_rewrite",
    "otm3_start",
    "otm3_write",
    "otm5_close",
    "otm5_delete",
    "otm5_open",
    "otm5_open_input",
    "otm5_open_output",
    "otm5_read_indexed",
    "otm5_read_next",
    "otm5_read_next_sorted_by_batch",
    "otm5_read_next_sorted_by_cust",
    "otm5_rewrite",
    "otm5_start",
    "otm5_write",
    "payments_close",
    "payments_delete",
    "payments_delete_all",
    "payments_open",
    "payments_open_input",
    "payments_open_output",
    "payments_read_indexed",
    "payments_read_next",
    "payments_rewrite",
    "payments_start",
    "payments_write",
    "pinvoice_close",
    "pinvoice_delete",
    "pinvoice_delete_all",
    "pinvoice_open",
    "pinvoice_open_input",
    "pinvoice_open_output",
    "pinvoice_read_indexed",
    "pinvoice_read_next",
    "pinvoice_read_next_header",
    "pinvoice_rewrite",
    "pinvoice_start",
    "pinvoice_write",
    "plautogen_close",
    "plautogen_delete",
    "plautogen_delete_all",
    "plautogen_open",
    "plautogen_open_input",
    "plautogen_open_output",
    "plautogen_read_indexed",
    "plautogen_read_next",
    "plautogen_read_next_header",
    "plautogen_rewrite",
    "plautogen_start",
    "plautogen_write",
    "purch_close",
    "purch_delete",
    "purch_open",
    "purch_open_input",
    "purch_open_output",
    "purch_read_indexed",
    "purch_read_next",
    "purch_read_next_sorted_byname",
    "purch_rewrite",
    "purch_start",
    "purch_write",
    "sales_close",
    "sales_delete",
    "sales_open",
    "sales_open_input",
    "sales_open_output",
    "sales_read_indexed",
    "sales_read_next",
    "sales_read_next_sorted_by_name",
    "sales_rewrite",
    "sales_start",
    "sales_write",
    "slautogen_close",
    "slautogen_delete",
    "slautogen_delete_all",
    "slautogen_open",
    "slautogen_open_input",
    "slautogen_open_output",
    "slautogen_read_indexed",
    "slautogen_read_next",
    "slautogen_read_next_header",
    "slautogen_rewrite",
    "slautogen_start",
    "slautogen_write",
    "spl_posting_close",
    "spl_posting_delete",
    "spl_posting_delete_all",
    "spl_posting_open",
    "spl_posting_open_extend",
    "spl_posting_open_input",
    "spl_posting_open_output",
    "spl_posting_read_indexed",
    "spl_posting_read_next",
    "spl_posting_rewrite",
    "spl_posting_start",
    "spl_posting_write",
    "stock_audit_close",
    "stock_audit_delete",
    "stock_audit_open",
    "stock_audit_open_extend",
    "stock_audit_open_input",
    "stock_audit_open_output",
    "stock_audit_read_indexed",
    "stock_audit_read_next",
    "stock_audit_rewrite",
    "stock_audit_start",
    "stock_audit_write",
    "stock_close",
    "stock_delete",
    "stock_open",
    "stock_open_input",
    "stock_open_output",
    "stock_read_indexed",
    "stock_read_next",
    "stock_rewrite",
    "stock_start",
    "stock_write",
    "system_close",
    "system_open",
    "system_open_input",
    "system_open_output",
    "system_read_indexed",
    "system_rewrite",
    "system_write",
    "value_close",
    "value_delete",
    "value_delete_all",
    "value_open",
    "value_open_input",
    "value_open_output",
    "value_read_indexed",
    "value_read_next",
    "value_rewrite",
    "value_start",
    "value_write",
)
