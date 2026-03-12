# Claude Code Plugin Marketplace

A curated collection of developer tools and plugins for [Claude Code](https://claude.com/claude-code), designed to enhance your development workflow with specialized agents and commands.

## Repository

[https://github.com/siva01c/claude-plugins](https://github.com/siva01c/claude-plugins)

## Available Plugins

### Drupal Dev Tools

**Version:** 2.2.0
**Description:** Comprehensive Drupal 11 development toolkit with DDEV integration

#### Features:
- **Slash Command: `/drupal-dev-tools:drupal`** - Performs comprehensive Drupal 11 code audit and security analysis
  - Verifies Drupal 11 coding standards compliance
  - Checks for security vulnerabilities (SQL injection, XSS, unsafe input handling)
  - Reviews code quality and design patterns (SOLID, DRY principles)
  - Identifies code duplication and deprecated APIs
  - Provides actionable recommendations with Drupal documentation references

- **Agent: `drupal-ddev`** - Specialized agent for managing DDEV-based Drupal 11 projects
  - Module management (install, update, remove)
  - Configuration management (export, import, status)
  - Database operations (import, export, updates)
  - Cache management and performance optimization
  - Development workflows and best practices

- **Skills bundle (`drupal-dev-tools/skills/*/SKILL.md`)** - Reusable Drupal 11 workflows
  - Module development skill
  - Security review skill
  - DDEV operations skill

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

### Step 3: Install a Plugin

Install the Drupal Dev Tools plugin:

```
/plugin install drupal-dev-tools@dev-tools
```

The format is: `/plugin install <plugin-name>@<marketplace-name>`

### Step 4: Verify Installation

Check that the plugin is installed:

```
/plugin list
```

## Using the Plugins

### Drupal Dev Tools

#### Using the `/drupal-dev-tools:drupal-ddev` Command

Once installed, you can run comprehensive Drupal code audits:

```
/drupal-dev-tools:drupal
```

This will analyze your Drupal project and provide a structured report covering:
- Drupal 11 best practices compliance
- Security vulnerabilities
- Code quality and design issues
- Code duplication
- Refactoring recommendations

#### Using the `drupal-ddev` Agent

The drupal-ddev agent is automatically available when working with DDEV-based Drupal projects. Simply interact with Claude Code naturally, and it will use the agent when appropriate for tasks like:

- "Install the webform module"
- "Export the current configuration"
- "Clear all caches"
- "Create a backup of the database"
- "Update Drupal core"

The agent knows common DDEV and Drush commands and follows Drupal best practices.

## Plugin Structure

This repository follows the Claude Code plugin marketplace structure:

```
claude-plugins/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace definition
└── drupal-dev-tools/         # Plugin directory
    ├── .claude-plugin/
    │   └── plugin.json       # Plugin metadata
    ├── commands/
    │   └── drupal.md         # Slash command definition
    ├── agents/
    │   └── drupal-ddev.md    # Agent definition
    └── skills/
        ├── drupal-module-development/
        │   └── SKILL.md
        ├── drupal-security-review/
        │   └── SKILL.md
        └── drupal-ddev-operations/
            └── SKILL.md

```

## Contributing

Contributions are welcome! To add a new plugin:

1. Fork this repository
2. Create a new plugin directory with the required structure:
   - `.claude-plugin/plugin.json` - Plugin metadata
   - `commands/` - Slash command definitions (optional)
   - `agents/` - Agent definitions (optional)
3. Update `.claude-plugin/marketplace.json` to include your plugin
4. Submit a pull request

### Plugin Requirements

Each plugin must have:
- A unique name (kebab-case)
- A `.claude-plugin/plugin.json` file with metadata
- At least one command or agent
- Clear documentation

## Documentation

For more information about Claude Code plugins:
- [Plugin Marketplaces Documentation](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces)
- [Creating Custom Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)

## License

This project is open source. Please check individual plugin directories for specific licenses.


## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/siva01c/claude-plugins/issues)
- Check the [Claude Code documentation](https://docs.claude.com/en/docs/claude-code)

## Changelog

### Version 2.2.0 (Latest)
- Added Drupal-focused reusable skills bundle (`*.SKILL.md`)
- Updated plugin metadata and marketplace entry
- Kept existing audit command and DDEV agent workflows

### Version 2.1.0
- Enhanced Drupal 11 development tools
- Added comprehensive code audit command
- Improved DDEV agent with detailed workflows
- Updated security analysis patterns

---

Made with Claude Code
