"""Runs phpstan for the quality-tools PostToolUse hook (see phpstan_hook.py).

Imported only after phpstan_hook.py has decided that the edited file is custom
Drupal PHP code, so nothing here costs anything on other edits.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_MARKERS = (".ddev", "phpstan.neon", "phpstan.neon.dist", "phpstan.dist.neon",
                "vendor/bin/phpstan", ".git")
PROJECT_CONFIGS = ("phpstan.neon", "phpstan.neon.dist", "phpstan.dist.neon")
BASELINE = "phpstan-baseline.neon"
PHPSTAN = "vendor/bin/phpstan"
# Generated next to vendor/ contents so it is visible on the host and inside DDEV alike;
# includes in it are relative to vendor/.
GENERATED_CONFIG = "vendor/phpstan-hook.neon"
DRUPAL_EXTENSIONS = ("mglaman/phpstan-drupal/extension.neon",
                     "mglaman/phpstan-drupal/rules.neon",
                     "phpstan/phpstan-deprecation-rules/rules.neon")
DDEV_DOCROOT = "/var/www/html"
DEFAULT_CONFIG = Path(__file__).resolve().parent / "phpstan-default.neon"
MISSING_HINT = (
    "quality-tools phpstan hook: phpstan was not found in this project "
    f"({PHPSTAN}), so edited PHP files are not analysed. Install it with "
    "`composer require --dev phpstan/phpstan mglaman/phpstan-drupal "
    "phpstan/extension-installer` (prefix with `ddev` in a DDEV project), "
    "or set PHPSTAN_HOOK=0 to silence this hook.")


def project_root(path):
    """Nearest ancestor that looks like a project root (a git worktree counts)."""
    for parent in path.parents:
        if any((parent / marker).exists() for marker in ROOT_MARKERS):
            return parent
    return None


def ddev_container_dir(root):
    """Path of root inside the DDEV web container, or None outside a DDEV project.

    The outermost .ddev/config.yaml wins, so a git worktree inside a DDEV project
    maps to its directory under the main project's mount.
    """
    ddev = None
    for candidate in (root, *root.parents):
        if (candidate / ".ddev/config.yaml").is_file():
            ddev = candidate
    if ddev is None:
        return None
    rel = root.relative_to(ddev).as_posix()
    return DDEV_DOCROOT if rel == "." else f"{DDEV_DOCROOT}/{rel}"


def phpstan_command(root):
    """argv prefix that runs phpstan for this project, or None when it is not installed."""
    if not (root / PHPSTAN).is_file():
        return None
    container_dir = ddev_container_dir(root)
    if (container_dir and os.environ.get("IS_DDEV_PROJECT") != "true"
            and shutil.which("ddev")):
        return ["ddev", "exec", "--dir", container_dir, PHPSTAN]
    return [str(root / PHPSTAN)]


def config_args(root):
    """[] when the project has its own config (phpstan finds it), else -c <bundled default>."""
    if any((root / name).is_file() for name in PROJECT_CONFIGS):
        return []
    vendor = root / "vendor"
    includes = []
    if (root / BASELINE).is_file():
        includes.append(f"../{BASELINE}")
    if not (vendor / "phpstan/extension-installer").is_dir():
        includes.extend(rules for rules in DRUPAL_EXTENSIONS if (vendor / rules).is_file())
    text = ""
    if includes:
        text = "includes:\n" + "".join(f"\t- {inc}\n" for inc in includes) + "\n"
    text += DEFAULT_CONFIG.read_text()
    generated = root / GENERATED_CONFIG
    if not generated.is_file() or generated.read_text() != text:
        generated.write_text(text)
    return ["-c", GENERATED_CONFIG]


def display_path(path, root):
    """A path from phpstan's report (host or container) relative to the project root."""
    prefixes = {str(root), str(root.resolve())}
    container_dir = ddev_container_dir(root)
    if container_dir:
        prefixes.add(container_dir)
    for prefix in prefixes:
        prefix = prefix.rstrip("/") + "/"
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def hint_once(root, text):
    """Hand the agent a hint as additionalContext, at most once per project."""
    key = hashlib.sha1(str(root).encode()).hexdigest()[:12]
    marker = Path(tempfile.gettempdir()) / f"phpstan-hook-hint-{key}"
    if marker.exists():
        return
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": text}}))
    try:
        marker.touch()
    except OSError:
        pass


def run(file_path):
    """Analyse one file; returns the hook's exit code."""
    path = Path(file_path)
    root = project_root(path)
    if root is None:
        return 0
    command = phpstan_command(root)
    if command is None:
        hint_once(root, MISSING_HINT)
        return 0

    target = path.relative_to(root).as_posix()
    timeout = float(os.environ.get("PHPSTAN_HOOK_TIMEOUT", "30"))
    try:
        argv = command + ["analyse", "--error-format=json", "--no-progress",
                          "--no-interaction", "--memory-limit=1G",
                          *config_args(root), target]
        proc = subprocess.run(argv, cwd=root, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"phpstan hook: gave up after {timeout:g}s", file=sys.stderr)
        return 0
    except OSError as exc:
        print(f"phpstan hook: cannot run phpstan: {exc}", file=sys.stderr)
        return 0

    try:
        report = json.loads(proc.stdout)
    except ValueError:
        print("phpstan hook: phpstan did not return JSON:\n"
              + (proc.stderr or proc.stdout)[-2000:], file=sys.stderr)
        return 0

    lines = [
        f"{display_path(reported, root)}:{msg.get('line', 0)} {msg.get('message', '')}"
        for reported, result in (report.get("files") or {}).items()
        for msg in result.get("messages", [])
    ]
    if not lines:
        return 0
    print(f"phpstan found {len(lines)} error(s) in the file you just edited:", file=sys.stderr)
    print("\n".join(lines), file=sys.stderr)
    return 2
