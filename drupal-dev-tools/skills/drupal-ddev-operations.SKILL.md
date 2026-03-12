# Drupal DDEV Operations Skill

## Purpose
Use this skill for safe day-to-day Drupal 11 environment operations in DDEV projects.

## When to apply
- Running updates (core or contrib).
- Importing/exporting databases and configuration.
- Diagnosing local environment issues.

## Standard operating procedure
1. Verify project status with `ddev list` and `ddev describe`.
2. Create a backup before destructive changes.
3. Apply Composer updates and then Drush database updates.
4. Rebuild caches and confirm site health.
5. Export and commit configuration updates when needed.

## Safe update flow
```bash
ddev export-db --file=pre-update-backup.sql
ddev composer update drupal/core* --with-dependencies
ddev drush updb -y
ddev drush cr
ddev drush config:status
```

## Troubleshooting shortcuts
```bash
ddev logs web
ddev logs db
ddev drush status
ddev drush watchdog:show
```
