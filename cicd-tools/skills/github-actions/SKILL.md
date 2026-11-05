---
name: github-actions
description: >
  Use this skill when authoring or debugging GitHub Actions workflows
  (.github/workflows/*.yml) — e.g. "add CI for this Drupal project on
  GitHub", "run phpcs/phpstan/phpunit on pull requests", "cache composer
  dependencies", "deploy over SSH when main is pushed", "why didn't my
  workflow trigger", or anything involving jobs, matrices, runners, secrets,
  or reusable workflows.
---

# GitHub Actions Skill

GitHub Actions runs workflows from `.github/workflows/*.yml`. This skill
covers workflow authoring with a Drupal project as the working example:
linting, static analysis, PHPUnit with a database service, and SSH/drush
deployment.

---

## Workflow anatomy

```yaml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read            # least privilege — grant more only per job

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true  # newer push cancels the outdated run

jobs:
  phpcs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          tools: composer:v2
      - uses: actions/cache@v4
        with:
          path: ~/.composer/cache
          key: composer-${{ hashFiles('composer.lock') }}
          restore-keys: composer-
      - run: composer install --no-progress
      - run: vendor/bin/phpcs --standard=Drupal,DrupalPractice web/modules/custom
```

Key defaults to always set:

- **`permissions:`** — the implicit token is powerful; start from
  `contents: read` and widen per job only when needed.
- **`concurrency:`** — avoids burning runner minutes on superseded pushes.

---

## PHPUnit with a database service

```yaml
  phpunit:
    runs-on: ubuntu-latest
    services:
      db:
        image: mariadb:11.4
        env:
          MARIADB_DATABASE: drupal_test
          MARIADB_ROOT_PASSWORD: root
        ports: ['3306:3306']
        options: >-
          --health-cmd="healthcheck.sh --connect --innodb_initialized"
          --health-interval=10s --health-timeout=5s --health-retries=5
    env:
      SIMPLETEST_DB: mysql://root:root@127.0.0.1:3306/drupal_test
      SIMPLETEST_BASE_URL: http://localhost
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          extensions: gd, pdo_mysql
      - run: composer install --no-progress
      - run: vendor/bin/phpunit -c web/core/phpunit.xml.dist web/modules/custom
```

`services:` containers get health-checked before steps run — no manual
wait loops. From the runner they are reachable on `127.0.0.1:<mapped port>`.

### Matrix builds

```yaml
    strategy:
      matrix:
        php: ['8.3', '8.4']
    steps:
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
```

---

## Semgrep SAST with SARIF

Semgrep runs in its own container image, so no PHP or Composer setup is
needed. SARIF uploaded to code scanning shows each finding on the PR diff and
under Security → Code scanning (public repos, or private ones with GitHub
Advanced Security).

```yaml
  semgrep:
    runs-on: ubuntu-latest
    container: semgrep/semgrep
    permissions:
      contents: read
      security-events: write   # upload-sarif needs it; keep it on this job only
    steps:
      - uses: actions/checkout@v4
      - run: >-
          semgrep scan --metrics=off --sarif --output semgrep.sarif
          --config p/php --config p/owasp-top-ten --config p/secrets
          --config .semgrep/drupal.yml --config .semgrep/drupal-routing.yml
          web/modules/custom web/themes/custom
      - uses: github/codeql-action/upload-sarif@v3
        if: always()            # upload even when the scan step failed on findings
        with:
          sarif_file: semgrep.sarif
          category: semgrep
```

- Copy the custom Drupal rules (the `security-tools` `semgrep` skill's
  `rules/drupal.yml` and `rules/drupal-routing.yml`) into the project, here
  `.semgrep/`, so CI does not depend on a local plugin path.
- Add `--error` to fail the job on any finding; without it the job stays green
  and code scanning carries the findings.
- Fork PRs get a read-only token, so the upload step fails there — guard it
  with `if: github.event.pull_request.head.repo.full_name == github.repository`
  when the project takes outside contributions.

---

## Deployment job

```yaml
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    needs: [phpcs, phpunit]
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://www.example.com
    steps:
      - uses: webfactory/ssh-agent@v0.9.0
        with:
          ssh-private-key: ${{ secrets.SSH_PRIVATE_KEY }}
      - run: |
          ssh -o StrictHostKeyChecking=accept-new deploy@prod.example.com \
            "cd /var/www/site && git pull --ff-only \
             && composer install --no-dev --optimize-autoloader \
             && vendor/bin/drush deploy -y"
```

- `needs:` gates deployment on green checks.
- `environment:` enables required reviewers and deployment history
  (Settings → Environments) — use it for production approval gates.
- Secrets live in repo/environment settings, referenced via
  `${{ secrets.NAME }}`. For cloud providers prefer **OIDC**
  (`permissions: id-token: write` + the provider's auth action) over
  long-lived keys.

---

## Reuse

- **Reusable workflow** — a whole workflow callable from others:

  ```yaml
  # .github/workflows/drupal-tests.yml
  on:
    workflow_call:
      inputs:
        php-version: { type: string, default: '8.3' }
  ```

  ```yaml
  # caller
  jobs:
    tests:
      uses: ./.github/workflows/drupal-tests.yml
      with:
        php-version: '8.4'
  ```

- **Composite action** — a reusable step sequence in
  `.github/actions/<name>/action.yml` (e.g. "setup PHP + composer install
  with cache") to deduplicate job boilerplate.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Workflow doesn't trigger | Check `on:` filters — `branches:`/`paths:` excluded the ref, or push was from a workflow using the default token (no recursive triggers) |
| `Permission denied` on push/comment from job | Widen `permissions:` for that job (e.g. `pull-requests: write`) |
| Composer cache never hits | Key on `hashFiles('composer.lock')` and add a `restore-keys:` prefix fallback |
| PHPUnit can't reach DB | Use `127.0.0.1` with the mapped port, not the service name (service names only resolve in container jobs) |
| Deploy ran before tests finished | Add the test jobs to `needs:` of the deploy job |
| Two runs per PR push | `push:` + `pull_request:` both trigger — restrict `push:` to `branches: [main]` |
