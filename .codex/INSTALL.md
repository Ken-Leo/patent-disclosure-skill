# Installing Patent Disclosure Skill for Codex

Enable this skill in Codex via native skill discovery.

## Prerequisites

- Git

## Installation

### macOS / Linux

```bash
git clone https://github.com/handsomestWei/patent-disclosure-skill.git ~/.patent-disclosure-skill

mkdir -p ~/.agents/skills
ln -s ~/.patent-disclosure-skill ~/.agents/skills/patent-disclosure-skill
```

### Windows (PowerShell)

```powershell
git clone https://github.com/handsomestWei/patent-disclosure-skill.git "$env:USERPROFILE\.patent-disclosure-skill"

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\patent-disclosure-skill" "$env:USERPROFILE\.patent-disclosure-skill"
```

## Verification

Restart Codex and ask: "列出可用技能" — the skill should appear as `patent-disclosure-skill`.

## Environment Variable

Codex sets `$CODEX_SKILL_DIR` to the skill root directory. The skill uses this variable for path resolution; if unavailable, it falls back to the skill's own directory.
