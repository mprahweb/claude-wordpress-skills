# Installation Guide

This guide walks you through every way to install **claude-wordpress-skills** into Claude Code.

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed and authenticated
- Git installed on your system (required for Options 2 and 3)

---

## Option 1: Marketplace Install (Recommended)

The marketplace method gives you all skills and keeps them up to date automatically.

**Step 1 — Open Claude Code** in your terminal:

```bash
claude
```

**Step 2 — Add the marketplace source:**

```bash
/plugin marketplace add elvismdev/claude-wordpress-skills
```

**Step 3 — Install the skill pack:**

```bash
/plugin install claude-wordpress-skills@claude-wordpress-skills
```

**Step 4 — Verify the installation** by checking that commands are available:

```bash
/claude-wordpress-skills:wp-perf-review --help
```

**Step 5 — Run your first review:**

```bash
/claude-wordpress-skills:wp-perf-review wp-content/plugins/my-plugin
```

> **Note:** Commands installed via marketplace are namespaced with the plugin name prefix
> (e.g., `/claude-wordpress-skills:wp-perf-review`).

---

## Option 2: Clone Locally

Install once for all projects on your machine.

**Step 1 — Clone the repository** into Claude's plugin directory:

```bash
git clone https://github.com/elvismdev/claude-wordpress-skills.git ~/.claude/plugins/wordpress
```

**Step 2 — Restart Claude Code** to pick up the new plugin:

```bash
# Exit Claude Code and reopen it
claude
```

**Step 3 — Verify** that the slash commands are available:

```bash
/wp-perf-review --help
```

**Step 4 — Update the plugin** at any time by pulling the latest changes:

```bash
git -C ~/.claude/plugins/wordpress pull origin master
```

> **Tip:** Commands are available without a namespace prefix when installed this way
> (e.g., `/wp-perf-review` instead of `/claude-wordpress-skills:wp-perf-review`).

---

## Option 3: Git Submodule (Team Projects)

Add the skills to a project repository so every team member gets them automatically.

**Step 1 — Navigate** to your project root:

```bash
cd /path/to/your-wordpress-project
```

**Step 2 — Add the submodule:**

```bash
git submodule add https://github.com/elvismdev/claude-wordpress-skills.git .claude/plugins/wordpress
```

**Step 3 — Commit the submodule** to your project:

```bash
git add .gitmodules .claude/plugins/wordpress
git commit -m "Add WordPress Claude skills"
```

**Step 4 — Push** so teammates receive the submodule reference:

```bash
git push origin main
```

**Step 5 — Teammates initialize** the submodule after cloning or pulling:

```bash
git submodule update --init --recursive
```

**Step 6 — Restart Claude Code** in the project directory:

```bash
claude
```

**Step 7 — Update the submodule** when new skill versions are released:

```bash
git submodule update --remote .claude/plugins/wordpress
git add .claude/plugins/wordpress
git commit -m "Update WordPress Claude skills"
```

---

## Option 4: Copy Individual Skills

Use this when you only need a single skill and want the smallest footprint.

**Step 1 — Clone or download** this repository somewhere temporary:

```bash
git clone https://github.com/elvismdev/claude-wordpress-skills.git /tmp/claude-wordpress-skills
```

**Step 2 — Create the Claude skills directory** if it does not exist:

```bash
mkdir -p ~/.claude/skills
```

**Step 3 — Copy the skill(s) you need:**

```bash
# Copy the performance review skill
cp -r /tmp/claude-wordpress-skills/skills/wp-performance-review ~/.claude/skills/
```

**Step 4 — Optionally remove the temporary clone:**

```bash
rm -rf /tmp/claude-wordpress-skills
```

**Step 5 — Restart Claude Code:**

```bash
claude
```

**Step 6 — Verify** the skill is loaded:

```bash
/wp-perf-review .
```

**Step 7 — Update a skill manually** by repeating Steps 1–5 and overwriting the old directory:

```bash
cp -r /tmp/claude-wordpress-skills/skills/wp-performance-review ~/.claude/skills/
```

---

## Verify Your Installation

After any installation method, confirm everything is working:

```bash
# Quick scan of your WordPress project
/wp-perf .

# Full review of a plugin
/wp-perf-review wp-content/plugins/my-plugin

# Full review of a theme
/wp-perf-review wp-content/themes/my-theme
```

You can also trigger skills with natural language:

```
Review this plugin for performance issues
Check this theme for slow database queries
Find anti-patterns before launch
```

---

## Comparison of Installation Methods

| Method | Scope | Auto-updates | Namespace prefix | Best for |
|--------|-------|-------------|-----------------|----------|
| Marketplace | Global | Yes | Yes | Individual developers |
| Clone locally | Global | Manual (`git pull`) | No | Individual developers |
| Git submodule | Per project | Manual (`git submodule update`) | No | Teams sharing a codebase |
| Copy individual skill | Global | Manual (re-copy) | No | Minimal installs |

---

## Uninstalling

**Marketplace install:**

```bash
/plugin uninstall claude-wordpress-skills
```

**Local clone:**

```bash
rm -rf ~/.claude/plugins/wordpress
```

**Git submodule:**

```bash
git submodule deinit -f .claude/plugins/wordpress
git rm -f .claude/plugins/wordpress
rm -rf .git/modules/.claude/plugins/wordpress
git commit -m "Remove WordPress Claude skills"
```

**Copied individual skill:**

```bash
rm -rf ~/.claude/skills/wp-performance-review
```

---

## Troubleshooting

**Commands not appearing after install**

Restart Claude Code. Skills are loaded at startup and do not hot-reload.

**`/plugin` command not found**

Ensure you are running Claude Code version 1.x or later. Update with:

```bash
npm update -g @anthropic-ai/claude-code
```

**Permission denied when copying to `~/.claude/`**

```bash
mkdir -p ~/.claude/skills
chmod 755 ~/.claude/skills
```

**Submodule shows as empty directory**

```bash
git submodule update --init --recursive
```

---

For further help, open an issue at https://github.com/elvismdev/claude-wordpress-skills/issues.
