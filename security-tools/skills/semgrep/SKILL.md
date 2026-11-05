---
name: semgrep
description: >-
  Semgrep as the deterministic SAST layer under a Drupal security review: run it
  on custom modules and themes (local semgrep or `docker run semgrep/semgrep`,
  no global install), with the registry packs p/php, p/owasp-top-ten and
  p/secrets plus custom Drupal rules (SQL injection in query()/db_query(), XSS
  through #markup and Markup::create(), superglobals, static \Drupal:: calls in
  DI classes, debug leftovers, routes without access checks), read the JSON
  output and triage every finding to true positive / false positive / needs
  context with its OWASP ASVS requirement. Use on "run semgrep", "SAST scan",
  "static security scan of custom code", before or during a Drupal security
  review, or when a workflow asks for the optional Semgrep step.
---

# Semgrep SAST for Drupal

A security review that rests only on reading code misses what nobody read.
Semgrep gives it a deterministic floor: the same code always gives the same
findings, each with a rule id and a line. The review then judges those
findings and goes on to what a pattern cannot see (business logic, object-level
access, data flow across services).

Use it together with:

- `owasp-asvs` (this plugin) — the requirement each finding maps to;
- `drupal-dev-tools:drupal-security-review` — the manual checklist the scan
  feeds.

## What is scanned

Only custom code — contrib and core have their own security process:

```
web/modules/custom
web/themes/custom
```

Adjust to the project's docroot (`docroot/`, `html/`). Skip paths that do not
exist; a scan of a missing path is an error, not an empty result.

## Rule sets

| Config | What it covers |
|---|---|
| `p/php` | General PHP security rules (exec, eval, unserialize, weak crypto…) |
| `p/owasp-top-ten` | OWASP Top 10 rules across languages, incl. JavaScript in themes |
| `p/secrets` | Hard-coded keys, tokens and passwords |
| `rules/drupal.yml` | Custom Drupal PHP rules, below |
| `rules/drupal-routing.yml` | Routes in `*.routing.yml` without an access requirement |

`rules/` is the directory next to this file. Pass the two rule files
explicitly — the directory also holds the test fixtures, which are not rules.

The registry packs (`p/…`) are downloaded at scan time, so they need network
access. Offline, run only the two local files and say in the report that the
registry packs were not run.

### Custom Drupal rules

| Rule id | Finds | ASVS | Severity |
|---|---|---|---|
| `drupal-sqli-concatenated-query` | `->query()` / `db_query()` with concatenated, interpolated or `sprintf()`-built SQL | V1.1.4 | ERROR |
| `drupal-xss-markup-unescaped` | A variable in `#markup` without `t()`, `Xss::filter()` or `Html::escape()` | V1.1.1, V1.2.1 | WARNING |
| `drupal-xss-markup-create` | `Markup::create()` with a variable that was not filtered | V1.1.1, V1.2.1 | WARNING |
| `drupal-superglobal-access` | `$_GET`, `$_POST`, `$_REQUEST`, `$_COOKIE`, `$_FILES` | V2.1.1 | WARNING |
| `drupal-static-call-in-di-class` | `\Drupal::…()` in a class with a constructor or `create()` | — (design) | INFO |
| `drupal-debug-output` | `var_dump`, `print_r`, `dpm`, `kint`, `dump`, `dd` … | V12.1.1, V12.1.2 | WARNING |
| `drupal-route-without-access-check` | A route with no `_permission`, `_access`, `_custom_access`, `_entity_access`, `_role` or `_user_is_logged_in` | V8.1.3, V4.2.1 | WARNING |

The ASVS IDs are the ones used in the `owasp-asvs` skill. Each rule also holds
them in `metadata.asvs`, with a `metadata.triage` hint. The DI rule is a design
finding (dependency inversion, see `quality-tools:solid`), not an ASVS
requirement; it is reported because a hidden `\Drupal::currentUser()` or
`\Drupal::request()` is where access and input handling hide.

## Running it

From the project root. `RULES` is the absolute path of this skill's `rules/`
directory.

**Semgrep installed locally** (or without installing it: `pipx run semgrep …`,
`uvx semgrep …`):

```bash
semgrep scan --metrics=off --json --output semgrep.json \
  --config p/php --config p/owasp-top-ten --config p/secrets \
  --config "$RULES/drupal.yml" --config "$RULES/drupal-routing.yml" \
  web/modules/custom web/themes/custom
```

**Docker, nothing installed:**

```bash
docker run --rm \
  -v "$PWD:/src" -v "$RULES:/rules:ro" -w /src \
  semgrep/semgrep semgrep scan --metrics=off --json --output semgrep.json \
  --config p/php --config p/owasp-top-ten --config p/secrets \
  --config /rules/drupal.yml --config /rules/drupal-routing.yml \
  web/modules/custom web/themes/custom
```

In a DDEV project run the same `docker run` from the host, not inside the web
container. Exit code 0 means the scan ran, whether or not it found anything;
1 with `--error` means findings; anything else is a failed scan — read
`.errors` in the JSON before reporting "no findings".

Write `semgrep.json` outside the repository or add it to `.gitignore`; scan
output is not committed.

## Reading the JSON

```bash
jq -r '.results[] | [.check_id, "\(.path):\(.start.line)", .extra.severity,
  ((.extra.metadata.asvs // []) | join(",")),
  ((.extra.metadata.cwe // []) | join("; "))] | @tsv' semgrep.json
jq '.errors' semgrep.json        # parse errors, timeouts, skipped files
```

- `check_id` of a local rule is prefixed with its path
  (`rules.drupal-sqli-concatenated-query`); report the part after the last dot.
- `extra.lines` is the matched source, `extra.message` the rule's advice.
- `.errors` with a parse error means that file was **not** scanned: list it in
  the report.

## Triage

Every finding gets one verdict, decided by reading the code around it:

| Verdict | When |
|---|---|
| **true positive** | The flagged value can be influenced by a user (request, entity field, user-editable config, external API) and reaches the sink unprotected, or the pattern is wrong in itself (debug output, a route without access) |
| **false positive** | The value is constant or already sanitised on the way, or the code never runs in production (tests, a `settings.php` guard) — say which |
| **needs context** | The value comes from another method, service or module that you did not read; name what has to be checked |

Rules for triage:

1. Read the whole method, not only `extra.lines`. Follow the variable back to
   where it is set.
2. Use the rule's `metadata.triage` hint; it lists the common false positives.
3. Do not drop a finding because "it is only admin": admin input is still
   input (V1.1.1), unless the value is filtered with `Xss::filterAdmin()` on
   purpose.
4. A false positive that recurs can be silenced in code with
   `// nosemgrep: <rule-id>` **and a reason on the same line**. Never silence
   a true positive.
5. Semgrep is syntactic. SQL concatenated into a variable and passed to
   `query()` later, input that reaches a sink through another service, and
   missing object-level access are not found — they stay on the manual
   checklist.

### ASVS for registry findings

Registry rules carry CWE and OWASP Top 10 metadata, not ASVS. Map them by CWE
to the `owasp-asvs` checklist:

| CWE | ASVS |
|---|---|
| CWE-89 SQL injection | V1.1.4 |
| CWE-79 XSS | V1.1.1, V1.2.1 |
| CWE-78 OS command injection | V1.1.5 |
| CWE-95 / CWE-94 eval, code injection | V1.2.2 |
| CWE-918 SSRF | V1.2.3 |
| CWE-22 path traversal | V5.2.2 |
| CWE-434 unrestricted upload | V5.1.2 |
| CWE-352 CSRF | V3.3.1 |
| CWE-798 / CWE-259 hard-coded secret | V6.3.1, V14.4.1 |
| CWE-327 / CWE-328 weak crypto or hash | V14.1.1 |
| CWE-330 weak randomness | V14.2.1 |
| CWE-862 / CWE-285 missing authorization | V8.1.3 |
| CWE-489 debug code | V12.1.1 |

A CWE that is not in the table: name the CWE and pick the closest ASVS chapter
from `owasp-asvs`, marked "(nearest)".

## Report

One row per finding, true positives first, then needs context, then false
positives:

```markdown
| Rule | Location | ASVS | Severity | Verdict | Reason |
|---|---|---|---|---|---|
| drupal-sqli-concatenated-query | web/modules/custom/foo/src/Repo.php:42 | V1.1.4 | ERROR | true positive | `$title` comes from the route parameter |
| drupal-xss-markup-unescaped | web/modules/custom/foo/src/Controller/Bar.php:18 | V1.1.1 | WARNING | needs context | value built in `BarBuilder::build()`, not read |
| drupal-debug-output | web/modules/custom/foo/foo.module:77 | V12.1.1 | WARNING | false positive | inside `if (getenv('FOO_DEBUG'))`, never set in production |
```

Below the table: the configs that ran (and which did not, e.g. offline), the
paths scanned, files listed in `.errors`, and the Semgrep version
(`semgrep --version`).

## Testing the custom rules

Each rule file has a fixture with `// ruleid: <id>` (the next line must be
reported) and `// ok: <id>` (the next line must not):

| Rules | Fixture |
|---|---|
| `rules/drupal.yml` | `rules/drupal.php` |
| `rules/drupal-routing.yml` | `rules/drupal-routing.test.yaml` |

```bash
semgrep --test rules/
# or
docker run --rm -v "$PWD/rules:/rules:ro" semgrep/semgrep semgrep --test /rules
```

A changed rule ships with a fixture line that proves it — one `ruleid:` for
what it now finds and one `ok:` for what it must leave alone.
