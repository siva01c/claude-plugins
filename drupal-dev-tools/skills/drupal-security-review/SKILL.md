---
name: drupal-security-review
description: Use when auditing Drupal 11 custom modules/themes for security issues such as unsafe input handling, XSS risks, SQL injection, and access control gaps.
---

# Drupal Security Review Skill

## Purpose
Use this skill to perform focused security reviews for Drupal 11 custom modules and themes.

## When to apply
- Reviewing pull requests before merge.
- Auditing custom code for common web vulnerabilities.
- Preparing release readiness checks.

## Review checklist
1. **Input handling**: Validate and sanitize all external input.
2. **Output escaping**: Escape output in Twig and PHP render logic.
3. **Database safety**: Use query builder or placeholders in all SQL operations.
4. **Access control**: Confirm route, entity, and operation permissions are enforced.
5. **Secrets and config**: Ensure credentials are never committed and sensitive config is protected.

## Common anti-patterns to flag
- Direct SQL string concatenation with user data.
- Unescaped raw markup in render arrays.
- Trusting `$_GET`, `$_POST`, or request payloads without validation.
- Debug leftovers (`var_dump`, `kint`, `dpm`) in production paths.

## Useful validation commands
```bash
rg "(var_dump|dpm\(|kint\()" web/modules/custom web/themes/custom
rg "\$_(GET|POST|REQUEST)" web/modules/custom web/themes/custom
```
