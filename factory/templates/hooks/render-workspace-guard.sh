#!/bin/bash
# render-workspace-guard.sh — PreToolUse(Bash) hook (installed by
# software-factory onboarding)
#
# Fail-closed workspace pin: Render CLI/API commands are blocked unless the
# current Render workspace matches the pin in .claude/render-workspace.
# The pin file may hold MULTIPLE lines — any mix of the workspace name and
# its tea-... ID — and a command/workspace matching ANY line passes. Pin by
# ID as well as name where possible: Render workspace names can carry
# invisible whitespace that defeats exact-name matching.
# If the pin file is absent or empty, the guard is a no-op (project not
# pinned). Exit 2 blocks the tool call and feeds stderr back to Claude.

INPUT=$(cat)
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

PIN_FILE=".claude/render-workspace"
[ -f "$PIN_FILE" ] || exit 0
PINS=$(grep -v '^[[:space:]]*$' "$PIN_FILE")
[ -z "$PINS" ] && exit 0
PIN_LABEL=$(printf '%s\n' "$PINS" | head -1)

export HOOK_INPUT="$INPUT"
CMD=$(python3 -c 'import json, os
try:
    print(json.loads(os.environ.get("HOOK_INPUT", "{}")).get("tool_input", {}).get("command", ""))
except Exception:
    print("")' 2>/dev/null)
[ -z "$CMD" ] && exit 0

# Only guard Render CLI invocations and direct Render API calls.
if ! printf '%s' "$CMD" | grep -qE '(^|[;&|[:space:]])render[[:space:]]+(workspace|services|deploys?|logs|psql|env|jobs|custom-domains|blueprints|login|whoami)|api\.render\.com'; then
  exit 0
fi

# Workspace switching: only to the pinned workspace (by any pinned name/ID).
if printf '%s' "$CMD" | grep -qE '(^|[;&|[:space:]])render[[:space:]]+workspace[[:space:]]+set'; then
  if printf '%s' "$CMD" | grep -qF -f <(printf '%s\n' "$PINS"); then
    exit 0
  fi
  echo "BLOCKED by render-workspace-guard: this project is pinned to Render workspace '$PIN_LABEL'. 'render workspace set' may only target the pinned workspace (accepted identifiers: $(printf '%s' "$PINS" | tr '\n' ' '))." >&2
  exit 2
fi

# Everything else: verify the current workspace matches the pin. Fail closed.
CURRENT=$(render workspace current -o json 2>/dev/null)
if [ -z "$CURRENT" ]; then
  echo "BLOCKED by render-workspace-guard: could not verify the current Render workspace (render CLI missing or not logged in). Run 'render login' then 'render workspace set $PIN_LABEL'. This project only operates in '$PIN_LABEL'." >&2
  exit 2
fi
if ! printf '%s' "$CURRENT" | grep -qF -f <(printf '%s\n' "$PINS"); then
  echo "BLOCKED by render-workspace-guard: the current Render workspace does not match the pinned workspace '$PIN_LABEL'. Run 'render workspace set $PIN_LABEL' (or set by pinned ID) before any Render operation. Never operate in another workspace." >&2
  exit 2
fi
exit 0
