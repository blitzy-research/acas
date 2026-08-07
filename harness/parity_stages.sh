# shellcheck shell=bash
#
# harness/parity_stages.sh -- THE canonical parity-protocol stage registry.
#
# WHY THIS FILE EXISTS (finding F-16)
# ==================================
# The oracle-comparison protocol has TEN stages, in one order, and that order is what
# makes an empty diff mean anything at all (Agent Action Plan section 0.8.5). Before this
# file the count and the names were restated independently in six places -- the driver's
# own stage table, both runners' stage banners, the reset script's banner, the composed
# recipes' service comments, the scenario definitions' prose and the test suite's
# docstrings -- and they had drifted apart: several said EIGHT stages and one said NINE,
# describing a protocol that no longer matched the one being executed. A reader
# reconciling a transcript against the documentation would have concluded the driver had
# skipped work it had in fact done, or that a stage they could see in the log did not
# exist.
#
# Stage numbering is not cosmetic here. It is how `--from`/`--to` name a range, how a
# resumed run identifies which artifacts it may trust, and how the diff evidence cites
# the step that produced a capture. So the registry is DEFINED ONCE, here, and every
# consumer reads it:
#
#   harness/run_parity.sh          sources this file and drives exactly these rows
#   harness/run_cobol_scenario.sh  sources it for its stage banner
#   harness/run_python_scenario.sh sources it for its stage banner
#   harness/reset_db.sh            sources it for its stage banner
#   harness/docker-compose.yml     quotes `run_parity.sh --print-stages`
#   tests/conftest.py              reads it through the same `--print-stages` output
#
# Sourcing rather than duplicating means a stage cannot be renamed in one place and left
# stale in another: there is only one place.
#
# THE STAGES, AND WHY EACH IS WHERE IT IS
# =======================================
#  1  reset + seed        the COBOL cycle must start from a known state
#  2  run COBOL           the oracle; the behavioural specification (rule R-6)
#  3  dump COBOL          raw state capture, ordered by primary key
#  4  normalise COBOL     removes representation artefacts -- character padding above
#                         all, because the bridge widens and trims names
#                         (section 0.6.2)
#  5  reset + RE-SEED     the SAME fixture bytes, so the Python cycle starts from the
#                         state the COBOL cycle started from and not the state it
#                         LEFT. Seeding identical bytes is proven by the fixture marker
#                         digest, not assumed (finding F-22)
#  6  run Python          the migrated cycle
#  7  dump Python         raw state capture
#  8  normalise Python    the same normalisation, so the comparison is like-for-like
#  9  verify published    both trees declare themselves complete before a single row is
#                         compared; two partial captures can produce an EMPTY diff
# 10  diff                the verdict. An empty diff is the pass condition
#
# This file is SOURCED, never executed. It defines variables and functions and runs no
# work of its own, so sourcing it has no side effect beyond the definitions.

# The definitions are guarded so the file may be sourced more than once in one shell --
# the driver sources it, and a script it invokes in the same process would source it
# again -- without the second source failing on a readonly reassignment. `readonly`
# itself is what protects the registry from a consumer redefining a row locally: an
# attempt to reassign fails loudly rather than silently driving a different protocol.
if [[ -z "${ACAS_PARITY_STAGES_DEFINED:-}" ]]; then
  # The number of stages. Any consumer printing "stage N of M" reads M from here.
  ACAS_PARITY_STAGE_COUNT=10
  readonly ACAS_PARITY_STAGE_COUNT

  # One row per stage, `<number>:<label>'. The number is the stage's identity in
  # `--from`/`--to`, in every banner and in every artifact that cites a stage.
  readonly -a ACAS_PARITY_STAGES=(
      '1:reset the schema and seed the scenario'
      '2:run the compiled COBOL cycle'
      '3:dump the COBOL state'
      '4:normalise the COBOL dump'
      '5:reset the schema and re-seed the SAME scenario'
      '6:run the migrated Python cycle'
      '7:dump the Python state'
      '8:normalise the Python dump'
      '9:verify both captures are published'
      '10:diff the two normalised trees -- an EMPTY diff is the pass'
  )

  ACAS_PARITY_STAGES_DEFINED=1
  readonly ACAS_PARITY_STAGES_DEFINED
fi

# Return the label for one stage number, on stdout.
#
# Args:
#   $1  the stage number, 1..ACAS_PARITY_STAGE_COUNT
#
# Exits 1 with a message on stderr when the number names no stage, rather than printing
# an empty label -- a banner reading "stage 11/10: " would say a protocol ran that does
# not exist.
acas_parity_stage_label() {
  local wanted="$1" entry
  for entry in "${ACAS_PARITY_STAGES[@]}"; do
    if [[ "${entry%%:*}" == "$wanted" ]]; then
      printf '%s' "${entry#*:}"
      return 0
    fi
  done
  printf 'harness/parity_stages.sh: %s names no stage; the protocol has %s.\n' \
    "$wanted" "$ACAS_PARITY_STAGE_COUNT" >&2
  return 1
}

# Print `stage <n>/<count>: <label>' for one stage, the exact phrasing every banner in
# the protocol uses so a reader grepping a transcript finds them all with one pattern.
#
# Args:
#   $1  the stage number
#   $2  an OPTIONAL sub-label, appended in parentheses, for a script that performs one
#       stage in several parts (the COBOL runner drives one operation at a time).
acas_parity_stage_headline() {
  local number="$1" suffix="${2:-}" label
  label="$(acas_parity_stage_label "$number")" || return 1
  if [[ -n "$suffix" ]]; then
    printf 'stage %s/%s: %s (%s)' \
      "$number" "$ACAS_PARITY_STAGE_COUNT" "$label" "$suffix"
  else
    printf 'stage %s/%s: %s' "$number" "$ACAS_PARITY_STAGE_COUNT" "$label"
  fi
}

# Print the whole registry, one `<number><TAB><label>' row per line.
#
# This is the machine-readable form the composed recipes and tests/conftest.py consume,
# reached through `harness/run_parity.sh --print-stages` so a consumer needs to know one
# entry point rather than this file's path. Tab-separated because a label contains
# spaces and may contain a colon.
acas_parity_stage_registry() {
  local entry
  for entry in "${ACAS_PARITY_STAGES[@]}"; do
    printf '%s\t%s\n' "${entry%%:*}" "${entry#*:}"
  done
}
