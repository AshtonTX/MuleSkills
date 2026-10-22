# MuleSkills

Rules that make Claude Code and GitHub Copilot write MuleSoft code the way our team does.

Add a few files to a Mule project and your AI assistant will:

- keep the project's Mule, Java and connector versions instead of upgrading them
- handle Mule errors properly and write DataWeave for the runtime you actually run
- write MUnit tests that can fail, and report which tests it really ran
- point out anything Government Cloud doesn't support

Nothing is installed on your machine and no tool, account or service is added. Claude Code, GitHub Copilot CLI and the GitHub Copilot desktop app read the files when you work in the project. Every rule is backed by MuleSoft or GitHub documentation, a reviewed article or a DataWeave CLI test; [docs/sources.md](docs/sources.md) records which.

## Quick start

You need Git, and Copilot CLI 1.0.89 or later, the Copilot desktop app, or Claude Code. On Windows, run the commands in Git Bash, which comes with Git for Windows. These steps assume MuleSkills is already in your organization's GitHub; if it isn't, do the [team setup](docs/setup.md#once-for-the-team) first.

1. Clone this repository once:

   ```sh
   git clone https://github.com/<your-org>/MuleSkills.git ~/MuleSkills
   ```

2. In the Mule project, on a new branch, install the rules:

   ```sh
   git switch -c chore/mule-guardrails
   ~/MuleSkills/scripts/install.sh .
   ```

3. Fill in the Project section of `.github/mule/team-profile.md`: runtime, versions, deployment target. The assistant can do a first pass:

   > Fill in the Project section of .github/mule/team-profile.md from this project's POM, parent POM, mule-artifact.json and CI files, following .github/mule/team-profile-guide.md. Say where you found each value and leave anything you can't find as Unknown.

   Check every value it writes.

4. Check that your assistant sees the rules. In Copilot CLI, `copilot instruction list` should show `CLAUDE.md` and six `.claude/rules` files. In Claude Code, run `/memory`.

5. Commit, then open a pull request in the project:

   ```sh
   git add CLAUDE.md .claude .github/mule
   git commit -m "Add MuleSoft guardrails"
   ```

Then work as usual. [Setup](docs/setup.md) covers Windows without Git Bash, older Copilot versions and a more thorough loading check.

## What gets added to the project

| Path | What it does |
|---|---|
| `CLAUDE.md` | Rules for every MuleSoft task; always loaded |
| `.claude/rules/` | Rules for one kind of file each: Mule XML, DataWeave, MUnit, Maven, API contracts, configuration properties |
| `.claude/skills/team-mule-guardrails/` | A step-by-step workflow for MuleSoft tasks, and reference files the rules open when a change needs them |
| `.github/mule/team-profile.md` | This project's facts: runtime, versions, deployment target |
| `.github/mule/team-profile-guide.md` | How to fill in the profile; opened only when you do |
| `.github/mule/task-recipes.md` | Ready-made prompts for common tasks |

## Everyday use

- Start common tasks from a prompt in [task-recipes.md](overlay/shared/.github/mule/task-recipes.md): orient to a project, write DataWeave, add MUnit tests, review a change, fix a failing build, upgrade a runtime.
- Choose a capable model. In testing, a small, fast model (the kind Copilot's Auto mode sometimes picks) skipped the rule files.
- In Anypoint Studio or Eclipse the rule files don't load on their own: attach the matching ones and `team-profile.md` to your request.
- Don't install MuleSoft's `@salesforce/mulesoft-vibes-skills` package as well; its skills can take over from these rules ([why](docs/maintaining.md#mulesoft-dx-skills)).
- Your assistant sends your code to a cloud model. Use it only where your organization has approved it, and never put credentials, tokens, personal data or production payloads in a prompt.
- Review everything the assistant writes. The rules reduce common mistakes; they don't guarantee correct code.

## Update a project

On a branch in the project:

```sh
git -C ~/MuleSkills pull
~/MuleSkills/scripts/install.sh . --update
git diff
```

`--update` replaces the shared rule files and never touches the project's `CLAUDE.md` or `team-profile.md`.

## More documentation

| Read | When you want to |
|---|---|
| [Setup](docs/setup.md) | Set this repository up for the team, install in detail, check loading thoroughly, or remove the rules from a project |
| [How it works](docs/how-it-works.md) | Learn how each assistant loads the files, which layout to use, which other clients work, and the limits |
| [Changing the rules](docs/maintaining.md) | Edit a rule, run the checks, test DataWeave, or adopt a MuleSoft DX skill |
| [Troubleshooting](docs/troubleshooting.md) | Fix an assistant that ignores the rules, or an installer or build error |
| [Sources](docs/sources.md) | See the evidence behind each rule |

Found a rule that looks wrong? Open a pull request with the fix and its source; [Changing the rules](docs/maintaining.md) shows how.
