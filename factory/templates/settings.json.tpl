{
  "permissions": {
    "allow": [
      "Bash(dev-browser *)",
      "Bash(ls briefs/*)",
      "Bash(mv briefs/*)",
      "Bash(mkdir -p session/*)"
    ]
  },
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "mkdir -p \"$CLAUDE_PROJECT_DIR\"/.claude && touch \"$CLAUDE_PROJECT_DIR\"/.claude/.turn-marker"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/brief-progress-guard.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Task|Agent",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/trajectory-log.sh"
          }
        ]
      }
    ]
  }
}
