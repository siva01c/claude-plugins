---
name: git-worktree
description: >
  Use this skill whenever a task involves running parallel work on a git
  repository without conflicts — e.g. "fix this bug while I keep working on
  my feature", "run Claude on two branches at once", "work on this task in
  isolation", "create a throwaway branch for this experiment", or anything
  where two agents or sessions might edit the same files. Also trigger when
  the user asks to use worktrees directly, or when an agent needs its own
  isolated checkout so it can work without disturbing the main branch. Even
  if the user just says "do this in parallel" or "don't mess up my current
  work", consider worktrees.
---

# Git Worktree Skill

Git worktrees let you check out multiple branches of the same repository into
separate directories simultaneously. Each directory is a fully independent
working tree — its own HEAD, index, and files — but all share the same `.git`
history and objects, so they stay lightweight.

Use this skill to give each agent or parallel task its own isolated workspace.

---

## When to reach for worktrees

- Two or more agents might edit the same files simultaneously
- A task should not disturb the current branch's working state
- You need a throwaway sandbox that can be discarded cleanly if things go wrong
- The user asks to work on multiple features or fixes in parallel
- You want to run tests on one branch while editing another

---

## Core commands

### Create a worktree

```bash
# New branch from current HEAD
git worktree add ../my-task -b my-task-branch

# From a specific commit or existing branch
git worktree add ../hotfix -b hotfix origin/main

# Detached HEAD (no branch)
git worktree add --detach ../scratch HEAD

# Empty worktree on an unborn branch (blank slate)
git worktree add --orphan ../experiment -b experiment
```

The new directory is ready to use immediately. `cd` into it and work normally.

### List all worktrees

```bash
git worktree list
# /path/to/main        abc1234 [main]
# /path/to/my-task     def5678 [my-task-branch]
```

### Remove a worktree when done

```bash
# Clean remove (fails if the worktree has uncommitted changes)
git worktree remove ../my-task

# Force remove (discard dirty worktree)
git worktree remove --force ../my-task

# If you deleted the directory manually, clean up the metadata
git worktree prune
```

### Move a worktree

```bash
git worktree move ../my-task ../new-location
```

### Lock / unlock (for portable drives or network shares)

```bash
git worktree lock ../my-task --reason "on external drive"
git worktree unlock ../my-task
```

### Repair after a manual move

```bash
# Run inside the moved worktree
git worktree repair

# Or from main, pointing at each moved worktree
git worktree repair ../new-location-1 ../new-location-2
```

---

## Recommended layout for agents

Place worktrees as siblings of the main repo directory so paths stay
predictable and `.gitignore` patterns do not need updating:

```
projects/
  my-app/           ← main repo  (agents work here by default)
  my-app-task-a/    ← worktree for task A
  my-app-task-b/    ← worktree for task B
```

Create them from the main repo root:

```bash
git worktree add ../my-app-task-a -b task-a
git worktree add ../my-app-task-b -b task-b
```

---

## Agent workflow

1. **Create** a worktree on a fresh branch before starting work.
2. **Work** entirely inside that directory — treat it like a normal repo.
3. **Commit** as usual; history is shared with the main repo.
4. **Verify** the result (tests, review, etc.).
5. **Merge or PR** the branch back via standard git workflow.
6. **Remove** the worktree once done.

```bash
# Step 1 — set up
git worktree add ../my-app-fix-login -b fix-login

# Step 2 — work
cd ../my-app-fix-login
# ... make changes ...

# Step 3 — commit
git add -A && git commit -m "fix: resolve login redirect loop"

# Step 4 — back in main repo, merge
cd ../my-app
git merge fix-login

# Step 5 — clean up
git worktree remove ../my-app-fix-login
git branch -d fix-login
```

---

## Safety rules

- **One branch per worktree.** Git prevents the same branch from being checked
  out in two worktrees at once. Use separate branch names for each worktree.
- **Do not share an index.** Never point two worktrees at the same directory.
- **Avoid submodules in moved worktrees.** `git worktree move` cannot move a
  worktree that contains submodules; handle those manually.
- **Discard freely.** If a worktree session goes wrong, `git worktree remove
  --force` discards it entirely with no impact on other branches.
- **Prune stale metadata.** After manually deleting a worktree directory, run
  `git worktree prune` in the main repo to remove orphaned administrative
  files.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `fatal: '<branch>' is already checked out` | Use a different branch name, or check `git worktree list` |
| Worktree directory deleted but `git worktree list` still shows it | Run `git worktree prune` |
| Moved worktree can no longer find the repo | Run `git worktree repair` inside the moved directory |
| Locked worktree blocks removal | `git worktree unlock <path>` then remove |
| Changes in worktree not visible in main | Changes are per-worktree until committed and merged |