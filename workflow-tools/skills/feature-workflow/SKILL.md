---
name: feature-workflow
description: >
  Phased workflow for delivering a Drupal feature or non-trivial change:
  plan, implement, review, test, finalize. Use when building a new custom
  module, adding a route/form/plugin, changing entity structure or schema,
  or any task touching more than a couple of files. Do NOT use for typo
  fixes, CSS tweaks, or single-line changes — use the tiny-fix skill
  instead. Each phase has an exit condition; do not move to the next phase
  until it is met.
---

# Feature Workflow

A gated, phased procedure for non-trivial Drupal development tasks. The goal
is that no step is skipped and no task is declared done without evidence
(passing checks, exported config, green tests).

## When this activates

- Building or extending a custom module or theme
- Adding routes, forms, controllers, services, or plugins
- Changing entity structure, fields, or database schema
- Any change spanning multiple files or subsystems

## Task classification (do this first)

Before starting, classify the task and adjust rigor:

| Class | Signal | Rigor |
|-------|--------|-------|
| **tiny-fix** | Typo, comment, CSS tweak, single-line change | Stop — use the `tiny-fix` skill instead |
| **standard** | New feature, refactor, multi-file change | All phases below |
| **security-sensitive** | Touches routing, forms, user input, DB queries, permissions, file handling | All phases below + mandatory security pass in Phase 3 |
| **schema-touching** | Changes entity definitions, fields, or DB schema | All phases below + update hook requirement in Phase 2 |

## Phase 1 — Plan

1. Restate the requirement in one or two sentences. If ambiguous, ask before coding.
2. List the files and Drupal subsystems that will change (routing, services, config schema, hooks, plugins).
3. Identify config entities the change will create or modify — these must be exported before the task is done.
4. For multisite codebases: list every site that shares the affected module and note the impact.

**Exit condition:** a short written plan exists in the conversation. No code yet.

## Phase 2 — Implement

1. Follow Drupal 11 coding standards. If the `drupal-module-development` skill (drupal-dev-tools plugin) is available, apply it; otherwise follow core conventions: dependency injection over `\Drupal::` static calls in OOP code, typed config schema for new config, `declare(strict_types=1)` where the codebase uses it.
2. **Schema-touching tasks:** every entity/field/schema change ships with a matching `hook_update_N()` or `hook_post_update_NAME()` in the same changeset. An update hook must be idempotent.
3. New config objects get a `config/schema/*.schema.yml` entry.
4. Keep scope: do not refactor code the task did not ask for. Note improvement opportunities instead of applying them.

**Exit condition:** the change is complete, `drush cr` succeeds, and the site loads without new PHP errors in the log (`drush watchdog:show --severity=Error`).

## Phase 3 — Review

1. Run coding standards and static analysis if available in the project:
   ```bash
   phpcs --standard=Drupal,DrupalPractice web/modules/custom/MODULE
   phpstan analyse web/modules/custom/MODULE
   ```
2. If the `/drupal-dev-tools:drupal` audit command is installed, run it on the changed module.
3. **Optional SAST scan:** if the `semgrep` skill (security-tools plugin) is available and Semgrep can run (local `semgrep` or `docker run semgrep/semgrep`), scan the changed module with it and triage every finding (true positive / false positive / needs context, with its ASVS ID). True positives are fixed before Phase 4. Recommended for security-sensitive tasks; if it cannot run, note that.
4. **Security-sensitive tasks:** if the `owasp-asvs` skill (security-tools plugin) is available, walk the relevant checklist sections (V1 encoding/sanitization at minimum), starting from the Semgrep findings when the scan ran. If it is not installed, verify manually: parameterized queries only, `Xss::filter()` on user-supplied markup, access checks on every new route, CSRF protection on state-changing GET routes.

**Exit condition:** phpcs and phpstan pass (or their absence is noted), the Semgrep findings are triaged with no open true positive (or the scan's absence is noted), and for security-sensitive tasks the security pass is documented in the conversation.

## Phase 4 — Test

1. Run existing tests for the affected module: `phpunit` (via DDEV: `ddev exec phpunit ...`).
2. New behavior gets at least one kernel or functional test when the project has a test suite. If the project has no test infrastructure, state this explicitly instead of silently skipping.
3. Manually verify the acceptance criteria from Phase 1.

**Exit condition:** tests pass, or the absence of a test suite is explicitly recorded.

## Phase 5 — Finalize

1. Export configuration: `drush cex` — review the diff; only intended changes may be present.
2. Stage the complete changeset: code + update hooks + exported config + tests together.
3. Write a commit message describing what and why. Follow the project's convention (e.g. conventional commits).
4. Summarize: what changed, what evidence exists (checks run, tests passed), and any follow-ups noted in Phase 2.

**Exit condition:** config export is clean, changeset is coherent, summary delivered.

## Hard rules

- Never claim a phase is complete without the evidence its exit condition requires.
- Never skip Phase 3 for security-sensitive tasks.
- Never modify production databases or run destructive drush commands (`sql-drop`, `pmu`, `entity:delete`) as part of this workflow without explicit user confirmation.
