"""Behaviour tests for the quality-tools phpstan PostToolUse hook.

Run from the repository root:
    python3 -m unittest discover -s quality-tools/hooks/tests -p 'test_*.py'

phpstan and ddev are replaced by small fake executables on PATH / in vendor/bin,
so the tests need neither PHP nor DDEV.
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
HOOK = HOOKS_DIR / "phpstan_hook.py"
HOOKS_JSON = HOOKS_DIR / "hooks.json"

FAKE_TOOL = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, os, sys, time
    with open(os.environ["FAKE_LOG"], "a") as fh:
        fh.write(json.dumps({"tool": os.path.basename(sys.argv[0]),
                             "argv": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
    time.sleep(float(os.environ.get("FAKE_SLEEP", "0")))
    sys.stdout.write(os.environ.get("FAKE_OUT", ""))
    sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
    """
)


def _executable(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def phpstan_json(files=None, errors=None):
    files = files or {}
    return json.dumps({
        "totals": {"errors": len(errors or []),
                   "file_errors": sum(len(v) for v in files.values())},
        "files": {
            path: {"errors": len(msgs),
                   "messages": [{"message": m, "line": line, "ignorable": True}
                                for line, m in msgs]}
            for path, msgs in files.items()
        },
        "errors": errors or [],
    })


class HookTestCase(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.root = base / "project"
        self.module = self.root / "web/modules/custom/foo"
        self.module.mkdir(parents=True)
        (self.root / ".git").mkdir()
        self.php_file = self.module / "foo.module"
        self.php_file.write_text("<?php\n")
        self.bin = base / "bin"
        self.bin.mkdir()
        self.tmpdir = base / "tmp"
        self.tmpdir.mkdir()
        self.log = base / "calls.log"
        self.env = {
            "PATH": f"{self.bin}{os.pathsep}{os.path.dirname(sys.executable)}{os.pathsep}/usr/bin:/bin",
            "TMPDIR": str(self.tmpdir),
            "FAKE_LOG": str(self.log),
            "HOME": str(base),
        }

    def tearDown(self):
        self._tmp.cleanup()

    # helpers -----------------------------------------------------------

    def install_phpstan(self):
        _executable(self.root / "vendor/bin/phpstan", FAKE_TOOL)

    def install_ddev(self):
        (self.root / ".ddev").mkdir(exist_ok=True)
        (self.root / ".ddev/config.yaml").write_text("name: project\n")
        _executable(self.bin / "ddev", FAKE_TOOL)

    def run_hook(self, file_path, tool="Edit", **env):
        payload = {
            "session_id": "test",
            "hook_event_name": "PostToolUse",
            "tool_name": tool,
            "tool_input": {"file_path": str(file_path)},
            "cwd": str(self.root),
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env={**self.env, **env},
            cwd=str(self.root),
            timeout=60,
        )

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]


class SkipsIrrelevantFiles(HookTestCase):

    def setUp(self):
        super().setUp()
        self.install_phpstan()

    def test_non_php_file_exits_0_silently_without_phpstan(self):
        twig = self.module / "templates/foo.html.twig"
        twig.parent.mkdir()
        twig.write_text("{{ x }}")
        r = self.run_hook(twig)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.calls(), [])

    def test_php_outside_custom_code_is_skipped(self):
        contrib = self.root / "web/modules/contrib/bar/bar.module"
        contrib.parent.mkdir(parents=True)
        contrib.write_text("<?php\n")
        r = self.run_hook(contrib)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.calls(), [])

    def test_disabled_with_env_var(self):
        r = self.run_hook(self.php_file, PHPSTAN_HOOK="0")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(self.calls(), [])

    def test_every_drupal_php_extension_is_analysed(self):
        for ext in ("php", "module", "install", "inc", "theme", "profile"):
            f = self.module / f"x.{ext}"
            f.write_text("<?php\n")
            self.run_hook(f, tool="Write")
        self.assertEqual(len(self.calls()), 6)

    def test_non_php_overhead_is_small(self):
        txt = self.root / "README.md"
        txt.write_text("x")
        start = time.monotonic()
        for _ in range(5):
            self.run_hook(txt)
        per_call = (time.monotonic() - start) / 5
        self.assertLess(per_call, 0.5)


class ReportsErrors(HookTestCase):

    def setUp(self):
        super().setUp()
        self.install_phpstan()

    def test_errors_exit_2_with_file_line_message_on_stderr(self):
        out = phpstan_json({str(self.php_file): [
            (12, "Call to an undefined method Drupal\\Core\\Entity\\EntityTypeManagerInterface::getStorageX()."),
        ]})
        r = self.run_hook(self.php_file, FAKE_OUT=out, FAKE_EXIT="1")
        self.assertEqual(r.returncode, 2)
        self.assertIn(
            "web/modules/custom/foo/foo.module:12 Call to an undefined method "
            "Drupal\\Core\\Entity\\EntityTypeManagerInterface::getStorageX().",
            r.stderr,
        )
        self.assertNotIn(str(self.root), r.stderr)

    def test_clean_file_exits_0_silently(self):
        r = self.run_hook(self.php_file, FAKE_OUT=phpstan_json(), FAKE_EXIT="0")
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))

    def test_runs_from_project_root_with_relative_path_and_json_format(self):
        self.run_hook(self.php_file, FAKE_OUT=phpstan_json())
        (call,) = self.calls()
        self.assertEqual(Path(call["cwd"]).resolve(), self.root.resolve())
        self.assertEqual(call["argv"][0], "analyse")
        self.assertIn("--error-format=json", call["argv"])
        self.assertIn("web/modules/custom/foo/foo.module", call["argv"])
        self.assertNotIn("--no-cache", call["argv"])  # result cache stays on

    def test_project_config_is_used_as_is(self):
        (self.root / "phpstan.neon").write_text("parameters:\n  level: 8\n")
        self.run_hook(self.php_file, FAKE_OUT=phpstan_json())
        (call,) = self.calls()
        self.assertFalse(any(a == "-c" or a.startswith("--configuration") for a in call["argv"]))

    def test_without_project_config_bundled_level_5_default_is_used(self):
        self.run_hook(self.php_file, FAKE_OUT=phpstan_json())
        (call,) = self.calls()
        argv = call["argv"]
        self.assertIn("-c", argv)
        config = Path(call["cwd"]) / argv[argv.index("-c") + 1]
        self.assertTrue(config.is_file(), config)
        self.assertRegex(config.read_text(), r"level:\s*5")

    def test_bundled_default_includes_project_baseline(self):
        (self.root / "phpstan-baseline.neon").write_text("parameters:\n  ignoreErrors: []\n")
        self.run_hook(self.php_file, FAKE_OUT=phpstan_json())
        (call,) = self.calls()
        argv = call["argv"]
        config = Path(call["cwd"]) / argv[argv.index("-c") + 1]
        included = (config.parent / "../phpstan-baseline.neon").resolve()
        self.assertIn("phpstan-baseline.neon", config.read_text())
        self.assertEqual(included, (self.root / "phpstan-baseline.neon").resolve())

    def test_general_errors_without_file_errors_do_not_block(self):
        out = phpstan_json(errors=["Invalid configuration"])
        r = self.run_hook(self.php_file, FAKE_OUT=out, FAKE_EXIT="1")
        self.assertEqual(r.returncode, 0)

    def test_unparseable_output_does_not_block(self):
        r = self.run_hook(self.php_file, FAKE_OUT="PHP Fatal error: oops", FAKE_EXIT="255")
        self.assertEqual(r.returncode, 0)

    def test_timeout_does_not_block(self):
        r = self.run_hook(self.php_file, FAKE_OUT=phpstan_json(), FAKE_SLEEP="3",
                          PHPSTAN_HOOK_TIMEOUT="1")
        self.assertEqual(r.returncode, 0)


class MissingPhpstan(HookTestCase):

    def test_missing_phpstan_hints_once_and_never_blocks(self):
        first = self.run_hook(self.php_file)
        self.assertEqual(first.returncode, 0)
        context = json.loads(first.stdout)["hookSpecificOutput"]
        self.assertEqual(context["hookEventName"], "PostToolUse")
        self.assertIn("phpstan", context["additionalContext"])
        second = self.run_hook(self.php_file)
        self.assertEqual((second.returncode, second.stdout), (0, ""))


class Ddev(HookTestCase):

    def setUp(self):
        super().setUp()
        self.install_phpstan()
        self.install_ddev()

    def test_ddev_project_runs_phpstan_through_ddev_exec(self):
        out = phpstan_json({"/var/www/html/web/modules/custom/foo/foo.module": [
            (3, "Undefined variable: $x"),
        ]})
        r = self.run_hook(self.php_file, FAKE_OUT=out, FAKE_EXIT="1")
        (call,) = self.calls()
        self.assertEqual(call["tool"], "ddev")
        self.assertEqual(call["argv"][0], "exec")
        self.assertIn("/var/www/html", call["argv"])
        self.assertIn("vendor/bin/phpstan", call["argv"])
        self.assertIn("web/modules/custom/foo/foo.module", call["argv"])
        self.assertEqual(r.returncode, 2)
        self.assertIn("web/modules/custom/foo/foo.module:3 Undefined variable: $x", r.stderr)
        self.assertNotIn("/var/www/html", r.stderr)

    def test_inside_the_ddev_container_phpstan_runs_directly(self):
        self.run_hook(self.php_file, FAKE_OUT=phpstan_json(), IS_DDEV_PROJECT="true")
        (call,) = self.calls()
        self.assertEqual(call["tool"], "phpstan")


class PluginWiring(unittest.TestCase):

    def test_hooks_json_registers_post_tool_use_on_edits(self):
        config = json.loads(HOOKS_JSON.read_text())
        (entry,) = config["hooks"]["PostToolUse"]
        self.assertEqual(set(entry["matcher"].split("|")), {"Edit", "Write", "MultiEdit"})
        (hook,) = entry["hooks"]
        self.assertEqual(hook["type"], "command")
        self.assertIn("${CLAUDE_PLUGIN_ROOT}/hooks/phpstan_hook.py", hook["command"])
        self.assertGreater(hook.get("timeout", 60), 30)


if __name__ == "__main__":
    unittest.main()
