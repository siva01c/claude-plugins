#!/usr/bin/env python3
"""PostToolUse hook: run phpstan on the custom Drupal PHP file the agent just edited.

Contract (Claude Code hooks):
  - stdin: the hook payload (tool_name, tool_input.file_path, cwd, ...)
  - exit 0, no output: nothing to report (or the hook does not apply)
  - exit 2, stderr:    phpstan errors as "path:line message" - fed back to the agent
  - exit 0, stdout:    JSON with additionalContext - a one-time hint when phpstan is missing

The hook never blocks the agent because of its own environment: a missing phpstan,
a timeout, a crash or a broken configuration all end with exit 0.

Environment:
  PHPSTAN_HOOK=0           disable the hook
  PHPSTAN_HOOK_TIMEOUT=30  seconds before phpstan is given up on

This file is only the fast filter: most edits are not custom PHP and cost no more
than the interpreter start. phpstan_runner.py does the rest.
"""

import json
import os
import sys

PHP_EXTENSIONS = (".php", ".module", ".install", ".inc", ".theme", ".profile")
CUSTOM_DIRS = ("/modules/custom/", "/themes/custom/", "/profiles/custom/")


def target_file(payload):
    """Absolute path of the edited file if the hook applies to it, else None."""
    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not path.endswith(PHP_EXTENSIONS):
        return None
    if not os.path.isabs(path):
        path = os.path.join(payload.get("cwd") or os.getcwd(), path)
    path = os.path.normpath(path)
    if not any(d in path.replace(os.sep, "/") for d in CUSTOM_DIRS):
        return None
    return path


def main():
    if os.environ.get("PHPSTAN_HOOK", "1") == "0":
        return 0
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    path = target_file(payload)
    if path is None:
        return 0
    import phpstan_runner  # noqa: E402 - deferred on purpose, see the module docstring
    return phpstan_runner.run(path)


if __name__ == "__main__":
    sys.exit(main())
