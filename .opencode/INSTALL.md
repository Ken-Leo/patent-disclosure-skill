# Installing Patent Disclosure Skill for OpenCode

## Prerequisites

- [OpenCode.ai](https://opencode.ai) installed

## Installation

### macOS / Linux

```bash
git clone https://github.com/handsomestWei/patent-disclosure-skill.git ~/.patent-disclosure-skill

mkdir -p ~/.config/opencode/skills
ln -s ~/.patent-disclosure-skill ~/.config/opencode/skills/patent-disclosure-skill
```

### Windows (PowerShell)

```powershell
git clone https://github.com/handsomestWei/patent-disclosure-skill.git "$env:USERPROFILE\.patent-disclosure-skill"

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills"
cmd /c mklink /J "$env:USERPROFILE\.config\opencode\skills\patent-disclosure-skill" "$env:USERPROFILE\.patent-disclosure-skill"
```

## Verification

Restart OpenCode to discover the skills. Ask: "列出可用技能"

## Notes

- OpenCode does **not** auto-detect skills from a repository on open. Skills must be installed to `~/.config/opencode/skills/` via the commands above.
- This skill uses `$SKILL_DIR` for path resolution, which defaults to the skill root directory.
