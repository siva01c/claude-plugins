# Claude Code Plugin Marketplace

A curated collection of [Claude Code](https://claude.com/claude-code) plugins for **Drupal development, security, and deployment**. Each plugin covers one topic — Drupal itself, DDEV, Docker, CI/CD, git workflows, and security verification — so you install only what you need.

## Repository

[https://github.com/siva01c/claude-plugins](https://github.com/siva01c/claude-plugins)

## Available Plugins

| Plugin | Version | Contents |
|---|---|---|
| [drupal-dev-tools](drupal-dev-tools/) | 4.1.0 | `/drupal-dev-tools:drupal` audit command, skills: module development, security review |
| [ddev-tools](ddev-tools/) | 1.0.0 | `drupal-ddev` agent, skill: DDEV operations for Drupal projects |
| [git-tools](git-tools/) | 1.0.0 | Skill: git worktrees for parallel, conflict-free work |
| [security-tools](security-tools/) | 1.1.0 | Skills: OWASP ASVS v5.0 checklist mapped to Drupal 11 APIs, Semgrep SAST with custom Drupal rules |
| [docker-tools](docker-tools/) | 1.0.0 | Skills: Docker Compose for Drupal stacks, Docker Model Runner for local AI models |
| [cicd-tools](cicd-tools/) | 1.1.0 | Skills: GitLab CI and GitHub Actions pipelines for Drupal projects |
| [workflow-tools](workflow-tools/) | 1.1.0 | Skills: phased feature/deploy workflows and a tiny-fix path, rigor scaled to risk |
| [quality-tools](quality-tools/) | 1.1.0 | Skills: SOLID and DRY design review rules; hook: phpstan on every edited custom PHP file |

### drupal-dev-tools

Comprehensive Drupal 11 toolkit:

- **Slash command `/drupal-dev-tools:drupal`** — full code audit of custom themes and modules: Drupal 11 standards, security (SQL injection, XSS, unsafe input), SOLID/DRY design review, duplication, refactoring recommendations. Starts the security section from a Semgrep scan when `security-tools` is installed and Semgrep can run.
- **Skills** — `drupal-module-development`, `drupal-security-review`.

### ddev-tools

DDEV is a multiplatform local development environment (built on Docker), so it has its own plugin:

- **Agent `drupal-ddev`** — manages DDEV-based Drupal 11 projects: modules, configuration, database operations, caches, Composer workflows.
- **`drupal-ddev-operations`** — safe operational workflows for Drupal in DDEV: backup-first updates, database/config import-export, troubleshooting.

### git-tools

- **`git-worktree`** — check out multiple branches into separate directories so parallel tasks (or parallel Claude sessions) never conflict. Covers create/list/remove/move/repair, agent workflow, and safety rules.

### security-tools

- **`owasp-asvs`** — OWASP ASVS v5.0 verification checklist (V1–V14) with every requirement mapped to Drupal 11 APIs (`Xss::filter()`, Query Builder, Flood control, Key module…), critical security patterns in PHP, red-flags table, and recommended Drupal security modules.
- **`semgrep`** — Semgrep as the deterministic SAST layer under a security review: runs through a local `semgrep` or `docker run semgrep/semgrep` (no global install) with `p/php`, `p/owasp-top-ten`, `p/secrets` and custom Drupal rules (SQL injection in `query()`/`db_query()`, XSS through `#markup` and `Markup::create()`, superglobals, `\Drupal::` in DI classes, debug leftovers, routes without access checks). Every custom rule maps to an ASVS requirement and has a `ruleid:`/`ok:` fixture for `semgrep --test`; every finding is reported with rule id, `file:line`, ASVS and a triage verdict.

### docker-tools

- **`docker-compose`** — compose.yaml authoring and operations with a Drupal stack (php-fpm, nginx, MariaDB, Redis) as the working example: healthchecks, depends_on conditions, dev/prod override files, profiles, troubleshooting.
- **`docker-model`** — Docker Model Runner: pull/run local AI models, OpenAI-compatible endpoints, the Compose `models:` element, and using it as a local backend for the Drupal AI module.

### cicd-tools

- **`gitlab-ci`** — `.gitlab-ci.yml` authoring for Drupal: composer caching, phpcs/phpstan/phpunit jobs with a MariaDB service, `rules:`, environments, and drush-based deployment.
- **`github-actions`** — workflows for Drupal: least-privilege permissions, concurrency, matrix PHP builds, database services, reusable workflows, and SSH/drush deployment.
- Both include a Semgrep SAST job with SARIF output (code scanning upload on GitHub, SARIF artifact plus the MR security widget on GitLab).

### workflow-tools

Phased development workflows that orchestrate the other plugins' skills, with rigor scaled to the risk of the task:

- **`feature-workflow`** — gated plan → implement → review → test → finalize procedure for non-trivial Drupal changes. Classifies the task first (standard / security-sensitive / schema-touching) and adds a mandatory security pass or update-hook requirement accordingly. Uses `drupal-module-development`, the `/drupal-dev-tools:drupal` audit, an optional `semgrep` scan in Phase 3, and `owasp-asvs` when those plugins are installed, with documented manual fallbacks when they are not.
- **`deploy-workflow`** — safe deployment sequence: pre-flight config-status check, mandatory backup, `composer install` → `drush updb` → `drush cim` → `drush cr` (or `drush deploy`), post-deploy verification, and a rollback plan. Covers per-site update passes for multisite releases.
- **`tiny-fix`** — deliberately minimal path for typos, CSS tweaks, and single-line changes, with an escalation tripwire to `feature-workflow` the moment a change touches logic, config, security, or schema.

### quality-tools

Design review rules that pair with `security-tools:owasp-asvs` in a code review:

- **`solid`** — SRP, OCP, LSP, ISP and DIP as review rules: what counts as a finding (a real cost today or on the next change), what is only taste, severity scale and what each finding must cite.
- **`dry`** — duplicated *knowledge* (rules, constants, parsers, protocol details) rather than similar-looking text: what to look for, what is not a finding, severity by whether the copies have already drifted.
- **phpstan hook** — a `PostToolUse` hook (`hooks/hooks.json`, enabled by installing the plugin, no `settings.json` edit) that runs phpstan on each custom Drupal PHP file right after Claude edits it, so a made-up or outdated API call comes back to the agent at once instead of at the end of the task.

#### phpstan hook

**What it checks.** After every `Edit`, `Write` or `MultiEdit` of a `.php`, `.module`, `.install`, `.inc`, `.theme` or `.profile` file under `modules/custom/`, `themes/custom/` or `profiles/custom/` (e.g. `web/modules/custom/…`), it runs

```
vendor/bin/phpstan analyse --error-format=json <file relative to the project root>
```

from the project root. Every other edit ends at once with exit 0.

- **No errors** → exit 0, no output.
- **Errors** → exit 2 and `path:line message` lines on stderr; Claude Code shows them to the agent, which fixes them in its next step.
- **phpstan not installed** → exit 0 and a one-time hint to the agent (`composer require --dev phpstan/phpstan mglaman/phpstan-drupal phpstan/extension-installer`).
- **Timeout (30 s), crash, broken config** → exit 0; the hook never blocks the agent over its own environment.

**Project root** is the nearest directory above the file with `.ddev/`, `phpstan.neon(.dist)`, `phpstan.dist.neon`, `vendor/bin/phpstan` or `.git` — a git worktree is its own root, so paths, config and `vendor/` are the worktree's. A worktree without its own `vendor/` gets the "not installed" hint: run `composer install` in it.

**Configuration.** A project `phpstan.neon`, `phpstan.neon.dist` or `phpstan.dist.neon` is used as is (phpstan finds it in the root) — include your baseline there as usual. Without one, the hook writes its bundled default (`hooks/phpstan-default.neon`, level 5) to `vendor/phpstan-hook.neon`, adding `phpstan-baseline.neon` from the project root when it exists, and phpstan-drupal plus the deprecation rules when `phpstan/extension-installer` does not load them already. With phpstan-drupal loaded, `\Drupal::service('entity_type.manager')` resolves to the real service class, so calls on it are checked instead of reported as unknown.

**Baseline.** Errors already listed in the baseline are not reported, so the agent sees only what it introduced. Create one with `vendor/bin/phpstan analyse --generate-baseline` (in DDEV: `ddev exec vendor/bin/phpstan analyse --generate-baseline`).

**Result cache.** phpstan's own result cache stays on, so repeated edits of one file re-analyse only what changed.

**Host or DDEV.**

- *Host:* `vendor/bin/phpstan` runs directly; `php` must be on `PATH`.
- *DDEV:* when the project root (or a directory above it, for a worktree inside the project) has `.ddev/config.yaml` and `ddev` is on `PATH`, the hook runs `ddev exec --dir /var/www/html[/<worktree>] vendor/bin/phpstan …`, so phpstan uses the container's PHP. The project must be started (`ddev start`); a stopped project ends as an error of the hook, i.e. exit 0.
- *Claude Code inside the DDEV web container* (`IS_DDEV_PROJECT=true`): phpstan runs directly, as on a host.

**Latency.** The filter for edits the hook does not analyse (a `.css`, `.twig`, contrib or core file) is a Python start with three standard-library imports: measured at 37–48 ms per edit, within the noise of a bare `python3 -c pass` on the same machine (23–47 ms). A phpstan run on one file costs the phpstan start plus the Drupal autoload discovery of phpstan-drupal; the first run fills the result cache, later runs of the same file are faster. Measure it on your project with `time vendor/bin/phpstan analyse --error-format=json <file>` (`ddev exec` adds the container round-trip).

**Turning it off.** `PHPSTAN_HOOK=0` in the environment of Claude Code disables the hook; `PHPSTAN_HOOK_TIMEOUT` changes the 30 s limit.

**Requirements.** `python3` (3.8+) on the host.

## Installation

### Step 1: Add the Marketplace

In Claude Code, run the following command to add this plugin marketplace:

```
/plugin marketplace add siva01c/claude-plugins
```

### Step 2: List Available Plugins

View all plugins available in the marketplace:

```
/plugin marketplace list
```

### Step 3: Install Plugins

Install any plugin with `/plugin install <plugin-name>@<marketplace-name>`:

```
/plugin install drupal-dev-tools@dev-tools
/plugin install ddev-tools@dev-tools
/plugin install git-tools@dev-tools
/plugin install security-tools@dev-tools
/plugin install docker-tools@dev-tools
/plugin install cicd-tools@dev-tools
/plugin install workflow-tools@dev-tools
/plugin install quality-tools@dev-tools
```

### Step 4: Verify Installation

Check that the plugins are installed:

```
/plugin list
```

## Updating Plugins

Pushing new commits to this repository does **not** automatically update an already-installed plugin. Claude Code keeps a local cache of both the marketplace catalog and the installed plugin (pinned to a specific git commit), so you have to refresh them manually.

### Step 1: Refresh the Marketplace Catalog

Fetch the latest catalog from this repository:

```
/plugin marketplace update dev-tools
```

The format is: `/plugin marketplace update <marketplace-name>`. Use `--all` to refresh every marketplace at once.

### Step 2: Update the Installed Plugin

Refreshing the catalog does not change the installed copy on its own. Reinstall the plugin to pull the latest version:

```
/plugin uninstall drupal-dev-tools@dev-tools
/plugin install drupal-dev-tools@dev-tools
```

### Step 3: Reload Plugins

Activate the changes in your current session (or restart Claude Code):

```
/reload-plugins
```

### Optional: Enable Auto-Update

To have the marketplace pull the latest version automatically on startup:

1. Run `/plugin`
2. Open the **Marketplaces** tab
3. Select your marketplace
4. Toggle **Enable auto-update**

### Tip: Local Development

If you are developing this plugin locally, add the marketplace from your local working tree instead of GitHub. This avoids the push/fetch cycle — you only need `/reload-plugins` to test edits:

```
/plugin marketplace add /path/to/claude-plugins
```

## Upgrading from 1.0 to 2.0

Version 2.0 (git tag `2.0`) restructures the marketplace from a single plugin into six topic-based plugins. The `drupal-dev-tools` plugin no longer contains the multiplatform tooling — it moved to dedicated plugins:

| Item | 1.0 location | 2.0 location |
|---|---|---|
| git-worktree skill | `drupal-dev-tools:git-worktree` | `git-tools:git-worktree` |
| owasp-asvs skill | `drupal-dev-tools:owasp-asvs` | `security-tools:owasp-asvs` |
| drupal-ddev agent | `drupal-dev-tools` | `ddev-tools` |
| drupal-ddev-operations skill | `drupal-dev-tools:drupal-ddev-operations` | `ddev-tools:drupal-ddev-operations` |

Version 2.0 also adds two brand-new plugins: `docker-tools` (Docker Compose, Docker Model Runner) and `cicd-tools` (GitLab CI, GitHub Actions).

### Upgrade steps

Run these commands in Claude Code:

```
/plugin marketplace update dev-tools
/plugin uninstall drupal-dev-tools@dev-tools
/plugin install drupal-dev-tools@dev-tools
/plugin install ddev-tools@dev-tools
/plugin install git-tools@dev-tools
/plugin install security-tools@dev-tools
/plugin install docker-tools@dev-tools
/plugin install cicd-tools@dev-tools
/reload-plugins
```

Notes:

- Reinstalling `drupal-dev-tools` is **required** — it removes the relocated agent and skills from the old installed copy.
- Install `ddev-tools`, `git-tools`, and `security-tools` to keep the agent and skills you used in 1.0.
- `docker-tools` and `cicd-tools` are new in 2.0 — install only if you need them.
- If you pinned the marketplace to a local directory, replace step 1 with re-adding the marketplace from the updated checkout.

## Plugin Structure

This repository follows the Claude Code plugin marketplace structure:

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace definition (all plugins)
├── drupal-dev-tools/
│   ├── .claude-plugin/plugin.json
│   ├── commands/drupal.md
│   └── skills/
│       ├── drupal-module-development/SKILL.md
│       └── drupal-security-review/SKILL.md
├── ddev-tools/
│   ├── .claude-plugin/plugin.json
│   ├── agents/drupal-ddev.md
│   └── skills/drupal-ddev-operations/SKILL.md
├── git-tools/
│   ├── .claude-plugin/plugin.json
│   └── skills/git-worktree/SKILL.md
├── security-tools/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── owasp-asvs/SKILL.md
│       └── semgrep/
│           ├── SKILL.md
│           └── rules/            # custom Drupal rules + their test fixtures
├── docker-tools/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── docker-compose/SKILL.md
│       └── docker-model/SKILL.md
├── cicd-tools/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── gitlab-ci/SKILL.md
│       └── github-actions/SKILL.md
├── workflow-tools/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── feature-workflow/SKILL.md
│       ├── deploy-workflow/SKILL.md
│       └── tiny-fix/SKILL.md
└── quality-tools/
    ├── .claude-plugin/plugin.json
    ├── hooks/
    │   ├── hooks.json            # PostToolUse: phpstan on edited custom PHP
    │   ├── phpstan_hook.py
    │   ├── phpstan_runner.py
    │   ├── phpstan-default.neon
    │   └── tests/
    └── skills/
        ├── solid/SKILL.md
        └── dry/SKILL.md
```

## Contributing

Contributions are welcome! To add a new plugin:

1. Fork this repository
2. Create a new plugin directory with the required structure:
   - `.claude-plugin/plugin.json` - Plugin metadata
   - `commands/` - Slash command definitions (optional)
   - `agents/` - Agent definitions (optional)
   - `skills/<skill-name>/SKILL.md` - Skill definitions (optional)
3. Update `.claude-plugin/marketplace.json` to include your plugin
4. Submit a pull request

### Plugin Requirements

Each plugin must have:
- A unique name (kebab-case)
- A `.claude-plugin/plugin.json` file with metadata
- At least one command, agent, or skill
- A topic that fits the marketplace scope: Drupal development, security, or deployment
- Clear documentation

## Documentation

For more information about Claude Code plugins:
- [Plugin Marketplaces Documentation](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
- [Creating Custom Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)

## License

MIT — see [LICENSE](LICENSE).

## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/siva01c/claude-plugins/issues)
- Check the [Claude Code documentation](https://docs.claude.com/en/docs/claude-code)

## Changelog

### 2.3 (Latest)

- **New `security-tools:semgrep` skill** (security-tools 1.1.0): Semgrep SAST with `p/php`, `p/owasp-top-ten`, `p/secrets` and custom Drupal rules mapped to ASVS, triage verdicts per finding, rule fixtures for `semgrep --test`.
- Optional Semgrep step in `feature-workflow` Phase 3 (workflow-tools 1.1.0) and in the `/drupal-dev-tools:drupal` audit (drupal-dev-tools 4.1.0).
- Semgrep SAST jobs with SARIF output in `github-actions` and `gitlab-ci` (cicd-tools 1.1.0).
- **`quality-tools` 1.1.0:** phpstan `PostToolUse` hook — every edited custom Drupal PHP file is analysed right away (host or DDEV, baseline-aware, `PHPSTAN_HOOK=0` to disable). `feature-workflow` Phase 3 mentions it.

### 2.2

- **New `quality-tools` plugin:** `solid` and `dry` design review skills — the design half of a code review next to `security-tools:owasp-asvs`.

### 2.1

- **New `workflow-tools` plugin:** phased `feature-workflow` (plan/implement/review/test/finalize with task classification), `deploy-workflow` (backup-first deployment sequence with multisite support and rollback), and `tiny-fix` (low-ceremony path with escalation tripwire). Workflows reference skills from the other plugins when installed and degrade gracefully when they are not.

### 2.0
- **Restructured into topic-based plugins:** `git-worktree` moved to new `git-tools` plugin, `owasp-asvs` moved to new `security-tools` plugin, `drupal-ddev` agent + `drupal-ddev-operations` skill moved to new `ddev-tools` plugin (DDEV is multiplatform, not Drupal-specific)
- **New `docker-tools` plugin:** Docker Compose (Drupal stack) and Docker Model Runner skills
- **New `cicd-tools` plugin:** GitLab CI and GitHub Actions skills for Drupal pipelines
- `drupal-dev-tools` plugin bumped to 4.0.0 (breaking: agent and skills moved out — plugin versions are independent of repo tags)
- Marketplace metadata refocused on Drupal development, security, and deployment
- See [Upgrading from 1.0 to 2.0](#upgrading-from-10-to-20)

### 1.0 — original single-plugin marketplace
- Single `drupal-dev-tools` plugin (up to 2.2.0) containing the audit command, DDEV agent, and all skills including `git-worktree` and `owasp-asvs`
- Plugin 2.2.0: added the Drupal-focused reusable skills bundle (`skills/*/SKILL.md`)
- Plugin 2.1.0: comprehensive code audit command, improved DDEV agent workflows, updated security analysis patterns

---

Made with Claude Code
