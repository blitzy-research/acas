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

# Nothing this script writes is group- or world-readable, and the builder sets the
# same mask for itself so the files the generated writers create match.
umask 077

readonly EX_OK=0
readonly EX_USAGE=70          # bad command line
readonly EX_PRECONDITION=71   # environment, directory or toolchain assertion
readonly EX_BUILD=72          # at least one scenario's fixtures could not be built

readonly ACAS_BF_SELF='harness/build_fixtures.sh'
readonly ACAS_BF_BUILDER='make_fixtures.py'

ACAS_BF_REPO="${ACAS_REPO:-/repo}"
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
                      Default: removed once the fixtures are proved readable.
  -h, --help          This text.

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
  $EX_OK   every requested scenario built and read back.
  $EX_USAGE  bad command line.
  $EX_PRECONDITION  environment, directory or toolchain assertion failed.
  $EX_BUILD  at least one scenario could not be built; each failure is reported with
      the builder's own diagnostic and its own exit code.
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

  local file stem target rc failures=0 built=0
  local -a failed=()
  for file in "${scenarios[@]}"; do
    stem="${file%.yaml}"
    target="$ACAS_BF_OUT/$stem"

    # A stale fixture from an earlier build must not survive into a seed: an INDEXED
    # file of a different shape alongside a new one is a confusing failure, and a
    # file the current declaration no longer mentions would be staged anyway if the
    # declaration were later narrowed. The builder clears what it will write; this
    # clears the whole scenario directory, which is stronger and is what an operator
    # means by "build the fixtures".
    rm -rf -- "$target" || acas_bf_die "$EX_PRECONDITION" \
      "the previous fixture directory could not be removed: $target"

    printf -- '--- %s\n' "$stem"
    rc=0
    python3 "$ACAS_BF_REPO/harness/$ACAS_BF_BUILDER" \
      "$ACAS_BF_REPO/harness/scenarios/$file" \
      --out "$target" \
      --repo "$ACAS_BF_REPO" \
      --modules "$ACAS_BF_MODULES" </dev/null || rc=$?

    if (( rc == 0 )); then
      built=$(( built + 1 ))
      if (( ! ACAS_BF_KEEP )) && [[ -d "$target/.build" ]]; then
        rm -rf -- "$target/.build" || acas_bf_warn \
          "the generated-source directory could not be removed: $target/.build"
      fi
      acas_bf_log "$stem: ready at $target"
    else
      failures=$(( failures + 1 ))
      failed+=("$stem (exit $rc)")
      acas_bf_warn "$stem: FAILED, builder exit $rc"
      acas_bf_warn "  the generated source is kept at $target/.build for diagnosis"
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
