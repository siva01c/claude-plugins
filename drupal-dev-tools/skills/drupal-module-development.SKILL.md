# Drupal Module Development Skill

## Purpose
Use this skill when creating or extending custom Drupal 11 modules with modern architecture and maintainable code.

## When to apply
- Building a new custom module in `web/modules/custom`.
- Adding services, event subscribers, forms, or controllers.
- Refactoring procedural logic to service-based design.

## Workflow
1. Scaffold the module structure (`.info.yml`, `.services.yml`, routing, permissions).
2. Register dependencies through service definitions and constructor injection.
3. Build controllers/forms/plugins using Drupal 11 APIs and strict typing.
4. Add config schema for any custom configuration.
5. Validate with Drush cache rebuild and config export.

## Guardrails
- Avoid direct use of superglobals in business logic.
- Prefer dependency injection over static service locators.
- Keep schema, permissions, routes, and services documented and versioned.
- Do not modify Drupal core or contrib module code directly.

## Quick command checklist
```bash
ddev drush en <module_name> -y
ddev drush cr
ddev drush config:export -y
```
