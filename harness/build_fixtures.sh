#!/usr/bin/env bash
# harness/build_fixtures.sh -- build the flat seed files EVERY scenario declares, in
# one non-interactive command, by driving harness/make_fixtures.py once per scenario.
# Run `--help' for the options and the exit codes.
#
# WHY THE FIXTURES ARE BUILT RATHER THAN COMMITTED. Fifteen of the seventeen flat
# files the frozen loaders read are ORGANIZATION INDEXED or RELATIVE, and GnuCOBOL
# writes those through its own file handler: an INDEXED file on this toolchain is a
# Berkeley DB Btree whose on-disk form belongs to the library version the image
# carries, which is measurable rather than assumable (`file ledger.dat' reports it).
# A committed binary would therefore be a fixture for one build of one image, and
# would silently stop being readable when either changed. So the RECORDS are declared
# as text in each scenario file, under `seed_records', and the FILES are built from
# them here -- by generating a COBOL writer per file, compiling it against the FROZEN
# copybooks, and calling the FROZEN handler to do the writing. Nothing about the
# layout is restated anywhere; it is read out of the frozen definitions at build time.
#
# WHERE THEY GO, AND WHY NOT BESIDE THE SCENARIO. A scenario's `seed_dir' resolves
# relative to the directory holding the scenario file, which in the shipped Compose
# topology is inside the checkout -- and the checkout is mounted READ-ONLY because it
# is frozen specification (R-3). So the fixtures are built under the data volume and
# `harness/seed.sh --seed-dir' is what points the loaders at them.
#
# THIS SCRIPT MODIFIES NO FROZEN FILE and writes nothing inside the checkout.

set -Eeuo pipefail

# Word splitting on newlines and tabs only, so a path containing a space can never be
# split apart. Every expansion below is quoted regardless.
IFS=$'\n\t'

# An unmatched glob expands to nothing rather than to the pattern text.
shopt -s nullglob

# ---------------------------------------------------------------------------
#  DROP THE ADMINISTRATIVE CREDENTIAL BEFORE ANYTHING IS SPAWNED (finding SEC-04)
#
#  `harness/docker-compose.yml` puts ACAS_DB_ADMIN_USER / ACAS_DB_ADMIN_PASSWORD in
#  the `gnucobol` service environment because protocol stages 1 and 5 -- and only
#  those two, both `harness/reset_db.sh` -- drop and re-apply the frozen schema and
#  so need DDL rights. A service-wide variable is inherited by every descendant,
#  which put the database SUPERUSER password into the environment of the GnuCOBOL
#  compiler, the preSQL translator, every bridge and menu binary, the migrated
#  Python cycle and pytest itself.
#
#  THIS SCRIPT NEVER USES THAT PAIR -- it holds no reference to either name and
#  invokes neither reset_db.sh nor seed.sh -- so it removes them from its own
#  environment here, before the first child exists. Least privilege by
#  construction rather than by convention: a compile or a cycle run cannot reach
#  the credential even by accident, because it is not there to reach.
#
#  Application access is unaffected: ACAS_DB_USER / ACAS_DB_PASSWORD remain, and
#  that account holds SELECT, INSERT, UPDATE and DELETE on the one schema.
# ---------------------------------------------------------------------------
unset ACAS_DB_ADMIN_USER ACAS_DB_ADMIN_PASSWORD

# Nothing this script writes is group- or world-readable, and the builder sets the
# same mask for itself so the files the generated writers create match.
umask 077

readonly EX_OK=0
readonly EX_USAGE=70          # bad command line
readonly EX_PRECONDITION=71   # environment, directory or toolchain assertion
readonly EX_BUILD=72          # at least one scenario's fixtures could not be built
readonly EX_TIMEOUT=78        # the builder overran its deadline (finding F-29)

readonly ACAS_BF_SELF='harness/build_fixtures.sh'
readonly ACAS_BF_BUILDER='make_fixtures.py'

# THE MARKER THAT MAKES A DESTRUCTIVE ROOT A DECLARED ONE (finding F-27). This
# script removes a whole scenario directory before rebuilding it, and it used to do
# so under any root that merely resolved outside the checkout -- so `--out /root'
# or an ACAS_FIXTURES left over from another tool pointed the recursive delete at
# somebody else's data. A root is now usable only if it CARRIES this file, and the
# file is created only for a root that is empty or already a fixture root. Nothing
# is deleted under a root that could not have been built by this script.
readonly ACAS_BF_ROOT_MARKER='.acas-harness-fixture-root'

# THE COMPLETION MANIFEST (finding F-25). Written LAST, inside the staging
# directory, and therefore present only in a fixture that was published whole. Its
# absence is what tells harness/seed.sh that a directory is a partial build rather
# than a fixture -- a distinction an interrupted build could not otherwise make,
# because the files it had already written looked exactly like a finished set.
readonly ACAS_BF_MANIFEST='.acas-fixture-manifest'

# The builder's deadline, in seconds (finding F-29). It compiles and runs up to
# seventeen generated COBOL programs, so the budget is generous; what it rules out
# is an unbounded wait, which in a container looks like progress. Overridable for a
# slower host, and validated rather than trusted.
ACAS_BF_TIMEOUT="${ACAS_BF_TIMEOUT:-1800}"

ACAS_BF_REPO="${ACAS_REPO:-/repo}"

# =============================================================================
# THE CANONICAL FIXTURE ROOT -- THIS LINE IS THE SINGLE STATEMENT OF THE RULE
#
# This script WRITES the fixtures, so it owns where they go, and two other
# components have to find them again:
#
#   harness/run_parity.sh   acas_parity_resolve_fixture_root  -- the standalone driver
#   tests/conftest.py       scenario_fixture_dir()            -- the pytest protocol
#
# Both derive the root with the identical expression and cite this line. The rule:
# $ACAS_FIXTURES when set and non-empty, otherwise $ACAS_DATA/fixtures, then one
# directory per scenario named after it. The `:-/data' last resort is this script's
# alone -- it can be run outside Compose, whereas the two readers assert ACAS_DATA
# first and would rather refuse than guess.
#
# A COMMENT WOULD NOT KEEP THEM IN STEP, so it is asserted:
# tests/arithmetic/test_shared_storage_and_dispatch_boundaries.py measures all three
# derivations against one environment and fails if any pair disagrees.
# =============================================================================
ACAS_BF_OUT="${ACAS_FIXTURES:-${ACAS_DATA:-/data}/fixtures}"
ACAS_BF_MODULES="${ACAS_BUILD:-/build}"
ACAS_BF_KEEP=0
declare -a ACAS_BF_WANTED=()

acas_bf_log()  { printf '%s: %s\n' "$ACAS_BF_SELF" "$*"; }
acas_bf_warn() { printf '%s: %s\n' "$ACAS_BF_SELF" "$*" >&2; }

acas_bf_die() {
  local code="$1"; shift
  local line
  for line in "$@"; do
    printf '%s: %s\n' "$ACAS_BF_SELF" "$line" >&2
  done
  exit "$code"
}

acas_bf_secure_tree() {
  local target="$1" exposed=''
  [[ -d "$target" ]] || return 0

  # GnuCOBOL's file handler creates SYS-DISPLAY.log and fh-logger.txt itself and
  # may widen them independently of the shell's umask. The same directory also
  # holds system.dat, whose record carries the database account. Remove every
  # group/world permission after each builder run, on both success and failure,
  # so diagnostic output is never left readable beside credential-bearing data.
  chmod -R go-rwx -- "$target" || acas_bf_die "$EX_PRECONDITION" \
    "could not restrict the generated fixture tree to its owner: $target"

  exposed="$(find "$target" -perm /077 -print -quit 2>/dev/null || true)"
  [[ -z "$exposed" ]] || acas_bf_die "$EX_PRECONDITION" \
    "a generated fixture artifact is still group/world accessible: $exposed"
}

acas_bf_usage() {
  cat <<USAGE
$ACAS_BF_SELF -- build every scenario's declared flat seed files.

Usage:
  $ACAS_BF_SELF [options] [<scenario-name> ...]

Arguments:
  <scenario-name>     Build only the named scenarios, by file stem -- for example
                      clean_batch_gl. Default: every harness/scenarios/*.yaml.

Options:
  --repo PATH         The frozen checkout. Default \$ACAS_REPO, or /repo. Read only;
                      nothing is ever written inside it.
  --out PATH          Where the fixtures are built, one directory per scenario.
                      Default \$ACAS_FIXTURES, or \$ACAS_DATA/fixtures, or
                      /data/fixtures. Must be OUTSIDE the checkout.
  --modules PATH      The build tree whose common/ holds the compiled handlers.
                      Default \$ACAS_BUILD, or /build.
  --keep-work         Keep each scenario's .build directory of generated COBOL.
                      Default: removed on EVERY path, success or failure. The
                      generated source carries no credential -- the writers ACCEPT
                      the six connection values FROM ENVIRONMENT rather than
                      holding them as literals -- but it still sits beside
                      credential-bearing DATA, so it is not left behind by default.
  -h, --help          This text.

Environment:
  ACAS_BF_TIMEOUT     Seconds the builder may take per scenario. Default 1800,
                      maximum 86400. A run that reaches it exits $EX_TIMEOUT, which
                      is NOT $EX_BUILD: a deadline says nothing about the scenario.

Where the fixtures go, and what makes a directory a fixture:
  Each scenario is built in a private staging directory under the fixture root, a
  completion manifest ($ACAS_BF_MANIFEST) carrying a SHA-256 per file is written
  LAST, and only then is the directory published into place. harness/seed.sh
  REQUIRES that manifest, so an interrupted build cannot be seeded as though it were
  a finished one.

  The fixture root itself must be a directory this script owns: it carries
  $ACAS_BF_ROOT_MARKER, written when the root is empty. A root holding other content
  and no marker is refused, because each rebuild removes <root>/<scenario>
  recursively.

What it does, per scenario:
  1. Runs $ACAS_BF_BUILDER against the scenario file.
  2. That generates one COBOL writer per declared flat file, compiles it against the
     FROZEN copybooks, and calls the FROZEN handler to write the records the scenario
     declares under \`seed_records'.
  3. It then READS EVERY FILE BACK through the same frozen handler and the same frozen
     definitions, and refuses the build unless the counts agree. A file the handler
     cannot open and walk is not a fixture, whatever it looks like on disk.

Using the result:
  harness/seed.sh --seed-dir <out>/<scenario> harness/scenarios/<scenario>.yaml
  The scenario's own seed_files list still decides which files are required; the
  option only says where they live. See harness/seed.sh --help.

Requirements:
  cobc must be on the PATH, because fifteen of the seventeen flat files are INDEXED
  or RELATIVE and only GnuCOBOL can write those. Run this inside the harness image.
  ACAS_DB_NAME, ACAS_DB_USER and ACAS_DB_PASSWORD must be set: the compiled side
  takes its credentials from the SEEDED SYSTEM RECORD [copybooks/wssystem.cob:L137-L139],
  so the builder fills those three fields from the environment and refuses a scenario
  that declares them -- which is what keeps every credential out of the repository.

Exit codes:
  $EX_OK   every requested scenario built, read back and published.
  $EX_USAGE  bad command line.
  $EX_PRECONDITION  environment, directory or toolchain assertion failed, or the
      fixture root could not be claimed.
  $EX_BUILD  at least one scenario could not be built; each failure is reported with
      the builder's own diagnostic and its own exit code.
  $EX_TIMEOUT  every failure was the builder reaching ACAS_BF_TIMEOUT.
USAGE
}

acas_bf_parse() {
  while (( $# > 0 )); do
    case "$1" in
      -h|--help)     acas_bf_usage; exit "$EX_OK" ;;
      --repo)        [[ $# -ge 2 ]] || acas_bf_die "$EX_USAGE" '--repo requires a path.'
                     ACAS_BF_REPO="$2"; shift 2 ;;
      --repo=*)      ACAS_BF_REPO="${1#*=}"; shift ;;
      --out)         [[ $# -ge 2 ]] || acas_bf_die "$EX_USAGE" '--out requires a path.'
                     ACAS_BF_OUT="$2"; shift 2 ;;
      --out=*)       ACAS_BF_OUT="${1#*=}"; shift ;;
      --modules)     [[ $# -ge 2 ]] || acas_bf_die "$EX_USAGE" '--modules requires a path.'
                     ACAS_BF_MODULES="$2"; shift 2 ;;
      --modules=*)   ACAS_BF_MODULES="${1#*=}"; shift ;;
      --keep-work)   ACAS_BF_KEEP=1; shift ;;
      --)            shift; break ;;
      -*)            acas_bf_die "$EX_USAGE" "unrecognised option '$1'." \
                       'Run --help for the accepted options.' ;;
      *)             ACAS_BF_WANTED+=("$1"); shift ;;
    esac
  done
  while (( $# > 0 )); do
    ACAS_BF_WANTED+=("$1"); shift
  done
}

acas_bf_assert_environment() {
  local repo_real out_real
  repo_real="$(readlink -f -- "$ACAS_BF_REPO" 2>/dev/null || true)"
  [[ -n "$repo_real" && -d "$repo_real/copybooks" ]] || acas_bf_die "$EX_PRECONDITION" \
    "'$ACAS_BF_REPO' does not look like the checkout: no copybooks/ under it." \
    'Pass --repo, or set ACAS_REPO.'
  ACAS_BF_REPO="$repo_real"

  [[ -d "$ACAS_BF_REPO/harness/scenarios" ]] || acas_bf_die "$EX_PRECONDITION" \
    "there is no harness/scenarios directory under $ACAS_BF_REPO."

  [[ -f "$ACAS_BF_REPO/harness/$ACAS_BF_BUILDER" ]] || acas_bf_die "$EX_PRECONDITION" \
    "the builder $ACAS_BF_REPO/harness/$ACAS_BF_BUILDER is missing."

  command -v cobc >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'cobc is not on the PATH.' \
    'Fifteen of the seventeen seed files are ORGANIZATION INDEXED or RELATIVE, so' \
    'GnuCOBOL itself has to write them. Run this inside the harness image.'

  command -v python3 >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'python3 is not on the PATH; the builder is a Python program.'

  python3 -c 'import yaml' >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'PyYAML is not importable, and the scenario files are YAML.'

  # The three credential fields the builder fills from the environment. Checked here
  # rather than eight times over, so a missing one is one message and not a cascade.
  local name
  for name in ACAS_DB_NAME ACAS_DB_USER ACAS_DB_PASSWORD; do
    [[ -n "${!name-}" ]] || acas_bf_die "$EX_PRECONDITION" \
      "$name is unset or empty." \
      'The compiled side reads its database account out of the SEEDED SYSTEM RECORD' \
      '[copybooks/wssystem.cob:L137-L139], so the builder fills those three fields' \
      'from the environment and refuses a scenario that declares them. That is what' \
      'keeps every credential out of the repository.'
  done

  [[ "$ACAS_BF_TIMEOUT" =~ ^[0-9]+$ ]] && (( ACAS_BF_TIMEOUT > 0 )) \
    && (( ACAS_BF_TIMEOUT <= 86400 )) || acas_bf_die "$EX_PRECONDITION" \
    "ACAS_BF_TIMEOUT must be a whole number of seconds between 1 and 86400;" \
    "it is '$ACAS_BF_TIMEOUT'." \
    'A malformed budget is refused rather than replaced, because a builder run' \
    'with no deadline is one that can hang and look like progress.'
  command -v timeout >/dev/null 2>&1 || acas_bf_die "$EX_PRECONDITION" \
    'timeout(1) is not on the PATH, so the builder cannot be bounded.' \
    'Run this inside the harness image, which carries coreutils.'

  mkdir -p -- "$ACAS_BF_OUT" || acas_bf_die "$EX_PRECONDITION" \
    "the output directory could not be created: $ACAS_BF_OUT"
  out_real="$(readlink -f -- "$ACAS_BF_OUT" 2>/dev/null || true)"
  [[ -n "$out_real" ]] || acas_bf_die "$EX_PRECONDITION" \
    "the output directory could not be resolved: $ACAS_BF_OUT"
  if [[ "$out_real" == "$ACAS_BF_REPO" || "$out_real" == "$ACAS_BF_REPO"/* ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "the output directory $out_real is inside the frozen checkout." \
      'The checkout is read-only specification and nothing here may write to it' \
      '(R-3). Point --out at the data volume.'
  fi
  ACAS_BF_OUT="$out_real"
  acas_bf_claim_root
}

# THE DESTRUCTIVE ROOT IS DECLARED, NOT INFERRED (finding F-27).
#
# Three refusals, then one claim:
#   * a root that is `/', a filesystem root, a home directory, an ancestor of the
#     checkout or anything shallower than two path components is refused outright,
#     whatever it contains -- those are the paths a mis-set variable produces;
#   * a root that already holds this script's marker is accepted;
#   * a root that holds NOTHING ELSE is claimed by writing the marker;
#   * a root that holds other content and no marker is REFUSED, because a
#     recursive delete under it would remove data this script did not create.
# THE ONE ESCAPE FROM THE DEPTH RULE (finding F-27), the same measurement
# harness/seed.sh records at its own copy: a one-component root is a dedicated volume
# when it sits on its own filesystem, and `/data` in the shipped stack does. An
# unknown answer - either `stat` failing - is read as NO.
#
# Args:
#   $1  the absolute path to test.
# Returns:
#   0 when the path is a mount point of its own, 1 otherwise.
acas_bf_is_dedicated_mount() {
  local path="$1" here parent
  here="$(stat -c '%d' -- "$path" 2>/dev/null || true)"
  parent="$(stat -c '%d' -- "$path/.." 2>/dev/null || true)"
  [[ -n "$here" && -n "$parent" && "$here" != "$parent" ]]
}

acas_bf_claim_root() {
  local root="$ACAS_BF_OUT" depth entries

  case "$root" in
    /|/root|/home|/tmp|/var|/usr|/etc|/opt|/srv|/boot|/dev|/proc|/sys)
      acas_bf_die "$EX_PRECONDITION" \
        "refusing to use '$root' as the fixture root: it is a system directory," \
        'and this script removes a whole scenario directory under its root before' \
        'each rebuild. Point --out at a dedicated directory on the data volume,' \
        'for example \$ACAS_DATA/fixtures.' ;;
  esac
  if [[ "$root" == "$HOME" ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use the home directory '$root' as the fixture root." \
      'Point --out at a dedicated directory on the data volume.'
  fi
  if [[ "$ACAS_BF_REPO" == "$root"/* ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use '$root' as the fixture root: the frozen checkout" \
      "$ACAS_BF_REPO lives underneath it, so a delete under this root could" \
      'reach the specification itself.'
  fi
  depth="$(printf '%s' "${root#/}" | awk -F/ '{ print NF }')"
  if (( depth < 2 )) && ! acas_bf_is_dedicated_mount "$root" \
       && [[ ! -f "$root/$ACAS_BF_ROOT_MARKER" ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use '$root' as the fixture root: it is only $depth path" \
      'component(s) deep, it is not a mount point of its own, and it carries no' \
      "$ACAS_BF_ROOT_MARKER. A one-component root is admitted only when it is a" \
      'DEDICATED VOLUME - as /data is in the shipped stack - or when a previous run' \
      'already claimed it. The canonical fixture root is $ACAS_DATA/fixtures.'
  fi

  if [[ -f "$root/$ACAS_BF_ROOT_MARKER" ]]; then
    return 0
  fi

  entries="$(find "$root" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null || true)"
  if [[ -n "$entries" ]]; then
    acas_bf_die "$EX_PRECONDITION" \
      "refusing to use '$root' as the fixture root: it holds content this script" \
      'did not create and carries no harness marker.' \
      "  first entry found: $entries" \
      "  expected marker  : $root/$ACAS_BF_ROOT_MARKER" \
      'This script removes <root>/<scenario> recursively before each rebuild, so a' \
      'root it cannot prove it owns is not one it will delete under. Use an empty' \
      'directory, or create the marker deliberately if this really is a fixture' \
      'root built by an earlier version.'
  fi

  {
    printf '# harness/build_fixtures.sh fixture root.\n'
    printf '# Its presence authorises this script to remove <root>/<scenario>\n'
    printf '# recursively before each rebuild. Delete this file to revoke that.\n'
  } >"$root/$ACAS_BF_ROOT_MARKER" || acas_bf_die "$EX_PRECONDITION" \
    "could not claim the fixture root by writing $root/$ACAS_BF_ROOT_MARKER."
  chmod 600 -- "$root/$ACAS_BF_ROOT_MARKER" 2>/dev/null || true
  acas_bf_log "claimed '$root' as the fixture root (marker written)"
}

# acas_bf_assert_removable <path>
#   Re-validated IMMEDIATELY BEFORE the delete, because the root was checked when
#   the script started and a symlink or a mount can appear in between (finding
#   F-27). The path must be a real directory, must sit exactly one component below
#   the claimed root, and the root must still carry its marker.
acas_bf_assert_removable() {
  local target="$1" resolved parent

  [[ -e "$target" ]] || return 0
  [[ ! -L "$target" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$target': it is a symbolic link, which could point" \
    'anywhere, including into the frozen checkout.'
  resolved="$(readlink -f -- "$target" 2>/dev/null || true)"
  [[ -n "$resolved" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$target': its real path could not be resolved."
  parent="${resolved%/*}"
  [[ "$parent" == "$ACAS_BF_OUT" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$resolved': it is not directly inside the claimed" \
    "fixture root '$ACAS_BF_OUT'."
  [[ -f "$ACAS_BF_OUT/$ACAS_BF_ROOT_MARKER" ]] || acas_bf_die "$EX_PRECONDITION" \
    "refusing to remove '$resolved': the fixture root no longer carries its" \
    "marker $ACAS_BF_ROOT_MARKER."
}

# The scenarios to build: every *.yaml under harness/scenarios, or just the named
# ones. A name that matches no scenario is a refusal rather than a silent no-op.
acas_bf_resolve_scenarios() {
  local -a all=()
  local path stem
  for path in "$ACAS_BF_REPO"/harness/scenarios/*.yaml; do
    all+=("${path##*/}")
  done
  (( ${#all[@]} > 0 )) || acas_bf_die "$EX_PRECONDITION" \
    "no scenario files were found in $ACAS_BF_REPO/harness/scenarios."

  if (( ${#ACAS_BF_WANTED[@]} == 0 )); then
    printf '%s\n' "${all[@]}"
    return 0
  fi

  local want found
  for want in "${ACAS_BF_WANTED[@]}"; do
    stem="${want%.yaml}"
    found=0
    for path in "${all[@]}"; do
      if [[ "$path" == "$stem.yaml" ]]; then
        found=1
        printf '%s\n' "$path"
        break
      fi
    done
    (( found )) || acas_bf_die "$EX_USAGE" \
      "there is no scenario named '$stem'." \
      "Available: $(printf '%s ' "${all[@]//.yaml/}")"
  done
}

# acas_bf_write_manifest <stem> <staging>
#   THE COMPLETION MANIFEST, WRITTEN LAST (finding F-25). One `file<TAB>name<TAB>sha256'
#   row per built file, in sorted order, so the manifest is a function of the content
#   and not of the order the builder happened to write it. Its presence is what makes
#   a published directory provably whole; harness/seed.sh requires it.
acas_bf_write_manifest() {
  local stem="$1" staging="$2" name digest
  local -a produced=()

  mapfile -t produced < <(
    find "$staging" -mindepth 1 -maxdepth 1 -type f ! -name '.*' -printf '%f\n' \
      | LC_ALL=C sort
  )
  (( ${#produced[@]} > 0 )) || acas_bf_die "$EX_BUILD" \
    "$stem: the builder exited 0 but wrote no fixture file into $staging."

  {
    printf 'manifest\t1\n'
    printf 'scenario\t%s\n' "$stem"
    printf 'files\t%s\n' "${#produced[@]}"
    for name in "${produced[@]}"; do
      digest="$(sha256sum -- "$staging/$name")" || acas_bf_die "$EX_BUILD" \
        "$stem: could not digest the built fixture $name."
      printf 'file\t%s\t%s\n' "$name" "${digest%% *}"
    done
  } >"$staging/$ACAS_BF_MANIFEST" || acas_bf_die "$EX_BUILD" \
    "$stem: the completion manifest could not be written."
  chmod 600 -- "$staging/$ACAS_BF_MANIFEST" || true
  acas_bf_log "$stem: manifest lists ${#produced[@]} file(s)"
}

# acas_bf_publish <stem> <staging> <target>
#   Replace the published fixture with the staged one in as few steps as the
#   filesystem allows: move any previous directory aside, rename the staging
#   directory into place, then remove the old one. `mv' onto an existing directory
#   is not atomic, so the previous fixture is moved out of the way FIRST -- which
#   means the window in which neither exists is a rename, not a build.
acas_bf_publish() {
  local stem="$1" staging="$2" target="$3" retired

  retired="$ACAS_BF_OUT/.retired-$stem.$$"
  if [[ -e "$target" ]]; then
    acas_bf_assert_removable "$target"
    mv -- "$target" "$retired" || acas_bf_die "$EX_PRECONDITION" \
      "$stem: the previous fixture could not be moved aside: $target"
  fi
  mv -- "$staging" "$target" || acas_bf_die "$EX_PRECONDITION" \
    "$stem: the staged fixture could not be published to $target"
  if [[ -e "$retired" ]]; then
    acas_bf_assert_removable "$retired"
    rm -rf -- "$retired" || acas_bf_warn \
      "$stem: the previous fixture could not be removed: $retired"
  fi
}

acas_bf_main() {
  acas_bf_parse "$@"
  acas_bf_assert_environment

  local -a scenarios=()
  mapfile -t scenarios < <(acas_bf_resolve_scenarios)

  acas_bf_log "repo    : $ACAS_BF_REPO (read only)"
  acas_bf_log "out     : $ACAS_BF_OUT"
  acas_bf_log "modules : $ACAS_BF_MODULES"
  acas_bf_log "building ${#scenarios[@]} scenario(s)"
  printf '\n'

  local file stem target staging rc failures=0 built=0 timeouts=0
  local -a failed=()
  for file in "${scenarios[@]}"; do
    stem="${file%.yaml}"
    target="$ACAS_BF_OUT/$stem"
    # BUILT IN A PRIVATE STAGING DIRECTORY AND PUBLISHED IN ONE MOVE (F-25). The
    # build used to write straight into $target, so an interruption left a
    # directory that held some of the declared files and looked exactly like a
    # finished fixture -- and harness/seed.sh would stage it. The staging name is
    # deliberately NOT a scenario name, so it cannot be mistaken for one, and it
    # is removed on every exit path.
    staging="$ACAS_BF_OUT/.staging-$stem.$$"

    acas_bf_assert_removable "$staging"
    rm -rf -- "$staging" || acas_bf_die "$EX_PRECONDITION" \
      "a previous staging directory could not be removed: $staging"
    mkdir -p -- "$staging" || acas_bf_die "$EX_PRECONDITION" \
      "the staging directory could not be created: $staging"

    printf -- '--- %s\n' "$stem"
    rc=0
    # BOUNDED (F-29). `timeout' sends TERM at the deadline and KILL ten seconds
    # later; exit 124 is its own report that the deadline was reached, which is
    # classified separately below rather than folded into "the build failed".
    timeout --kill-after=10s "${ACAS_BF_TIMEOUT}s" \
      python3 "$ACAS_BF_REPO/harness/$ACAS_BF_BUILDER" \
        "$ACAS_BF_REPO/harness/scenarios/$file" \
        --out "$staging" \
        --repo "$ACAS_BF_REPO" \
        --modules "$ACAS_BF_MODULES" </dev/null || rc=$?

    # ⭐ THE GENERATED SOURCE IS SCRUBBED ON EVERY PATH, SUCCESS OR FAILURE (F-31).
    # It used to be kept on failure "for diagnosis", and it carried the database
    # account: the builder wrote the six connection values into MOVE literals. The
    # builder no longer emits any credential -- it emits `ACCEPT ... FROM
    # ENVIRONMENT' -- and the directory is still removed unconditionally unless
    # --keep-work asks for it, because a compiler listing beside credential-bearing
    # DATA is not something to leave lying about either way.
    if (( ! ACAS_BF_KEEP )) && [[ -d "$staging/.build" ]]; then
      rm -rf -- "$staging/.build" || acas_bf_warn \
        "the generated-source directory could not be removed: $staging/.build"
    fi
    acas_bf_secure_tree "$staging"

    if (( rc == 0 )); then
      acas_bf_write_manifest "$stem" "$staging"
      acas_bf_publish "$stem" "$staging" "$target"
      built=$(( built + 1 ))
      acas_bf_log "$stem: ready at $target"
    else
      failures=$(( failures + 1 ))
      if (( rc == 124 || rc == 137 )); then
        timeouts=$(( timeouts + 1 ))
        failed+=("$stem (TIMED OUT after ${ACAS_BF_TIMEOUT}s, exit $rc)")
        acas_bf_warn "$stem: TIMED OUT after ${ACAS_BF_TIMEOUT}s (builder exit $rc)"
        acas_bf_warn '  raise ACAS_BF_TIMEOUT for a slower host; a timeout is not a'
        acas_bf_warn '  refusal by the builder and says nothing about the scenario.'
      else
        failed+=("$stem (exit $rc)")
        acas_bf_warn "$stem: FAILED, builder exit $rc"
      fi
      if (( ACAS_BF_KEEP )); then
        acas_bf_warn "  --keep-work: the generated source is at $staging/.build"
      else
        acas_bf_assert_removable "$staging"
        rm -rf -- "$staging" || acas_bf_warn \
          "the staging directory could not be removed: $staging"
        acas_bf_warn '  nothing was published, so no partial fixture can be seeded'
      fi
    fi
    printf '\n'
  done

  acas_bf_log "built $built of ${#scenarios[@]} scenario(s)"
  if (( failures > 0 )); then
    acas_bf_warn "$failures scenario(s) FAILED:"
    local entry
    for entry in "${failed[@]}"; do
      acas_bf_warn "  $entry"
    done
    acas_bf_warn 'Each diagnostic above is the builder'"'"'s own; it names the' \
      'scenario, the file, the record and the field it refused.'
    # A TIMEOUT IS NOT A REFUSAL, AND IS NOT REPORTED AS ONE (finding F-29). The
    # builder that ran out of time said nothing about the scenario; the host or the
    # budget is what needs attention, so the status is its own.
    if (( timeouts > 0 && timeouts == failures )); then
      acas_bf_warn "every failure was a DEADLINE (${ACAS_BF_TIMEOUT}s), not a refusal;" \
        'raise ACAS_BF_TIMEOUT and re-run.'
      return "$EX_TIMEOUT"
    fi
    return "$EX_BUILD"
  fi

  printf '\n'
  acas_bf_log 'every declared flat file was written AND read back through the frozen'
  acas_bf_log 'handlers and the frozen copybooks. To seed one scenario from these:'
  acas_bf_log "  harness/seed.sh --seed-dir $ACAS_BF_OUT/<scenario> \\"
  acas_bf_log "      $ACAS_BF_REPO/harness/scenarios/<scenario>.yaml"
  return "$EX_OK"
}

acas_bf_main "$@"
