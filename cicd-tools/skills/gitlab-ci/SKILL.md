---
name: gitlab-ci
description: >
  Use this skill when authoring or debugging GitLab CI/CD pipelines
  (.gitlab-ci.yml) — e.g. "add a CI pipeline for this Drupal project", "run
  phpcs/phpstan/phpunit in GitLab CI", "deploy with drush from a pipeline",
  "why is my job not running", "cache composer dependencies", or anything
  involving stages, rules, artifacts, environments, or GitLab runners.
---

# GitLab CI/CD Skill

GitLab CI runs pipelines defined in `.gitlab-ci.yml` at the repository root.
This skill covers pipeline authoring with a Drupal project as the working
example: validate → test → build → deploy, with composer caching and
drush-based deployment.

---

## Pipeline anatomy

```yaml
stages:
  - validate
  - test
  - deploy

default:
  image: php:8.3-cli
  before_script:
    - curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

variables:
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"

cache:
  key:
    files:
      - composer.lock        # cache invalidates when the lock file changes
  paths:
    - .composer-cache/
    - vendor/
```

- **`stages`** run sequentially; jobs within a stage run in parallel.
- **`default`** holds settings shared by all jobs.
- **Cache vs artifacts:** cache is best-effort storage between pipelines
  (composer/npm caches); artifacts pass build results between jobs of the
  same pipeline and can be downloaded from the UI.

---

## Controlling when jobs run — `rules:`

`rules:` replaces the deprecated `only/except`:

```yaml
phpcs:
  stage: validate
  script:
    - composer install --no-progress
    - vendor/bin/phpcs --standard=Drupal,DrupalPractice web/modules/custom
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

First matching rule wins. Common conditions:

| Goal | Rule |
|---|---|
| MR pipelines only | `if: $CI_PIPELINE_SOURCE == "merge_request_event"` |
| Default branch only | `if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` |
| Tags only | `if: $CI_COMMIT_TAG` |
| Skip on draft MRs | `if: $CI_MERGE_REQUEST_TITLE =~ /^Draft:/` + `when: never` |
| Manual gate | `when: manual` (e.g. production deploy) |

---

## Drupal test jobs

```yaml
phpstan:
  stage: test
  script:
    - composer install --no-progress
    - vendor/bin/phpstan analyse web/modules/custom

phpunit:
  stage: test
  services:
    - name: mariadb:11.4
      alias: db
  variables:
    MARIADB_DATABASE: drupal_test
    MARIADB_ROOT_PASSWORD: root
    SIMPLETEST_DB: mysql://root:root@db/drupal_test
    SIMPLETEST_BASE_URL: http://localhost
  script:
    - composer install --no-progress
    - vendor/bin/phpunit -c web/core/phpunit.xml.dist web/modules/custom
  artifacts:
    when: always
    reports:
      junit: junit.xml          # test results shown in MR widget
```

`services:` starts sidecar containers (database, redis) reachable by alias.

### Semgrep SAST with SARIF

```yaml
semgrep:
  stage: test
  image: semgrep/semgrep
  variables:
    SEMGREP_CONFIGS: >-
      --config p/php --config p/owasp-top-ten --config p/secrets
      --config .semgrep/drupal.yml --config .semgrep/drupal-routing.yml
  script:
    - semgrep scan --metrics=off $SEMGREP_CONFIGS
        --sarif-output=semgrep.sarif
        --gitlab-sast-output=gl-sast-report.json
        web/modules/custom web/themes/custom
  artifacts:
    when: always
    paths: [semgrep.sarif]       # SARIF for other tools and for download
    reports:
      sast: gl-sast-report.json  # findings in the MR security widget
```

- GitLab's MR widget reads its own SAST format, not SARIF:
  `--gitlab-sast-output` writes it next to the SARIF file in the same run.
  Older Semgrep versions without the `--<format>-output` options take one
  format per run (`--sarif --output …`) — run the scan twice there.
- Copy the custom Drupal rules (the `security-tools` `semgrep` skill's
  `rules/drupal.yml` and `rules/drupal-routing.yml`) into the project, here
  `.semgrep/`.
- Add `--error` to fail the job on findings.

---

## Deploying with drush

```yaml
deploy_prod:
  stage: deploy
  environment:
    name: production
    url: https://www.example.com
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual              # require a human click for prod
  script:
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - ssh deploy@prod.example.com "cd /var/www/site && git pull --ff-only
        && composer install --no-dev --optimize-autoloader
        && vendor/bin/drush deploy -y"
```

`drush deploy` runs `updb → config:import → cache:rebuild` in the right
order. Store `SSH_PRIVATE_KEY` as a **masked, protected** CI/CD variable
(Settings → CI/CD → Variables) — never in the repository.

`environment:` makes deployments visible under Operations → Environments and
enables rollback tracking.

---

## Reuse — include and needs

```yaml
include:
  - local: .gitlab/ci/common.yml                  # split big configs
  - component: gitlab.com/components/sast/sast@main   # CI/CD component

phpunit:
  needs: ["phpcs"]      # DAG: start as soon as phpcs passes, skip stage wait
```

`needs:` builds a directed acyclic graph so independent jobs don't wait for
their whole previous stage.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Job never appears in pipeline | A `rules:` entry filtered it out — check `$CI_PIPELINE_SOURCE` for the trigger type |
| "This job is stuck" | No runner with matching `tags:`; check runner availability |
| Composer re-downloads everything each run | Cache key/path mismatch — cache `vendor/` and `$COMPOSER_CACHE_DIR`, key on `composer.lock` |
| PHPUnit cannot connect to DB | Service alias must match host in `SIMPLETEST_DB`; wait for DB startup or use healthcheck-aware images |
| Masked variable prints as `[MASKED]` but auth fails | Variable contains newline/CR — for SSH keys use `tr -d '\r'` and file-type variables |
| Pipeline runs twice per MR push | Branch + MR pipelines both enabled — use `workflow: rules:` to keep one |
