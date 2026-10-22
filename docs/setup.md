# Setup

Getting MuleSkills to the team and into Mule projects. The [quick start](../README.md#quick-start) is the short version.

- [Once for the team](#once-for-the-team)
- [Add the rules to a Mule project](#add-the-rules-to-a-mule-project)
- [Update a project](#update-a-project)
- [Remove the rules from a project](#remove-the-rules-from-a-project)

## Once for the team

Done once, by whoever looks after this repository for the team.

### 1. Confirm you are allowed to

Your assistant sends the files you work on, and these rules, to a cloud model. Confirm with your lead or security contact that the assistant is approved for the repositories and data you will use it on. These rules do not make an assistant offline or approved for government data. Never put credentials, tokens, personal data or production payloads in prompts.

### 2. Put this repository in your work GitHub

Create an empty repository in your organization (for example `MuleSkills`, with no README), then, from your clone of this repository, point it there and push:

```sh
git remote set-url origin https://github.com/<your-org>/MuleSkills.git
git push -u origin main
```

Teammates then clone it from there, as in the [quick start](../README.md#quick-start). If your organization allows GitHub Actions, the [checks](maintaining.md#run-the-checks) in `.github/workflows/check.yml` run on every push and pull request.

### 3. Fill in the team-wide facts once

Edit [`overlay/shared/.github/mule/team-profile.md`](../overlay/shared/.github/mule/team-profile.md) in this repository and fill the Team section, which is the same for every project:

- Assistant client and version, and whether your organization approved it
- Government Cloud or Government Cloud Plus, and whether FIPS 140-3 mode is required
- Deployment target (CloudHub 1.0 or hybrid standalone runtimes), messaging, logging and API Manager setup
- Shared Exchange assets, connector approval rules and architecture conventions

Leave the Project section, such as Mule runtime, `minMuleVersion`, MUnit and connector versions, as `Unknown`; each project fills it. [`team-profile-guide.md`](../overlay/shared/.github/mule/team-profile-guide.md) says where to find each fact. Run `python3 scripts/build.py`, then commit and push.

### 4. Make sure no other MuleSoft skill can take over

Assistants select skills using the prompt and skill description. MuleSoft's official `build-mule-integration` skill describes itself as the first and only action for any Mule change, so installing it can cause the assistant to select a conflicting workflow with live connector lookups, `latest` versions and a mandatory build. Check your client's skills list and these folders, and remove or turn off MuleSoft skills your team has not approved:

`.github/skills`, `.claude/skills`, `.agents/skills` in the project, and `~/.claude/skills`, `~/.copilot/skills`, `~/.agents/skills` in your home folder.

[MuleSoft DX skills](maintaining.md#mulesoft-dx-skills) explains the conflict and how to adopt one of those skills safely.

## Add the rules to a Mule project

You need Git; on Windows, run the commands in Git Bash, which comes with Git for Windows.

### 1. Install the files

Work on a new branch in the project.

**macOS, Linux or Git Bash:**

```sh
git switch -c chore/mule-guardrails
~/MuleSkills/scripts/install.sh .
```

This installs the default `shared` layout. Add `--layout github` for the Copilot-only layout; [Two layouts](how-it-works.md#two-layouts) explains when a project needs it.

The script copies new files and never deletes anything. It checks all destinations before copying and rejects symbolic links or file/directory collisions so installation cannot follow a link outside the project. If the project already has a `CLAUDE.md`, it keeps the project's version and tells you; copy the rules from [`overlay/shared/CLAUDE.md`](../overlay/shared/CLAUDE.md) into it by hand.

**Windows without Git Bash:** copy the contents of `overlay/shared/` into the project root, keeping the folders: `.claude/rules`, `.claude/skills/team-mule-guardrails` and `.github/mule`, plus `CLAUDE.md` if the project doesn't have one already.

**Moving a project from the `github` layout to `shared`:** the installer stops and lists the old rule files. Delete the files it lists, run it again, and commit both changes together. If `.github/copilot-instructions.md` holds only these guardrails, delete it too; if it also holds the project's own instructions, remove just the guardrail text, because Copilot loads that file alongside `CLAUDE.md`. `.github/mule/team-profile.md` stays where it is, so the project's facts are kept.

On a Mac, Finder hides folders starting with a dot. Press Cmd+Shift+. to show `.claude` and `.github`.

### 2. Fill in the project's facts

Open `.github/mule/team-profile.md` in the project and fill the Project section from the project's own files: `pom.xml` and its parent, `mule-artifact.json`, and the CI configuration. The assistant can help:

> Inspect this project's POM, parent POM, mule-artifact.json and CI files, then fill in the Project section of .github/mule/team-profile.md following .github/mule/team-profile-guide.md. Say where you found each value. Leave anything you can't find as Unknown.

Check every value it writes. Never fill a value from a guess or a "latest version" example.

### 3. Check that your assistant actually loads the files

Do this once per client on a throwaway branch.

- **Copilot CLI:** run `copilot instruction list` in the project. It shows the instruction files it found, without sending a request. `CLAUDE.md` and the six `.claude/rules` files should be listed.
- **Claude Code:** run `/memory` in a session to see the files it loaded.
- **Any client:** add a marker line to the end of one file, for example `.claude/rules/dataweave.md`:

```
If this guidance is in your context, begin your reply with [dw-rules-loaded].
```

Open a `.dwl` file or a flow with a Transform Message in a fresh conversation and ask a harmless question about it. Inspect the client's references or instruction diagnostics and, where available, read traces for the profile and linked guidance. The marker is a smoke test that some guidance influenced this response; it does not prove every linked file loaded or that future requests will follow it. Repeat for the other matching file types, summarize the outcome on the profile's Loading check line (the guide's [loading check](../overlay/shared/.github/mule/team-profile-guide.md#loading-check-complete-on-each-client-the-team-uses) lists every probe), and remove the markers. If loading remains unverified, attach the relevant files manually. See GitHub's [instructions in use](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions#custom-instructions-in-use).

### 4. Commit and open a pull request

```sh
git add CLAUDE.md .claude .github/mule
git commit -m "Add MuleSoft guardrails"
```

After `--layout github`, the files are all under `.github`, so stage that instead:

```sh
git add .github
git commit -m "Add MuleSoft guardrails"
```

Review the diff like any other change and merge it with the team's normal process.

## Update a project

Work on a branch in the project. Pull the latest rules first, then install over the old ones:

```sh
git -C ~/MuleSkills pull
~/MuleSkills/scripts/install.sh . --update
git diff
```

`--update` replaces the shared rule files with this repository's versions. It never touches the project's `CLAUDE.md` or `team-profile.md`. Add `--layout github` for a project on that layout, where the protected file is `.github/copilot-instructions.md`.

## Remove the rules from a project

Review the installed files on a branch. Remove only these shared files if they still belong to this overlay:

- `.claude/rules/dataweave.md`
- `.claude/rules/maven.md`
- `.claude/rules/mule-xml.md`
- `.claude/rules/munit.md`
- `.claude/rules/api-contract.md`
- `.claude/rules/configuration-properties.md`
- `.claude/skills/team-mule-guardrails/SKILL.md`
- `.claude/skills/team-mule-guardrails/references/dataweave-operators.md`
- `.claude/skills/team-mule-guardrails/references/dataweave-output-formats.md`
- `.claude/skills/team-mule-guardrails/references/dataweave-performance.md`
- `.claude/skills/team-mule-guardrails/references/mule-connectors.md`
- `.claude/skills/team-mule-guardrails/references/mule-deployment-targets.md`
- `.github/mule/task-recipes.md`
- `.github/mule/team-profile-guide.md`

In the `github` layout the same files sit under `.github/instructions/` (named `*.instructions.md`) and `.github/skills/`.

Take only the guardrail text out of `CLAUDE.md`, preserving the project's other instructions. Keep `.github/mule/team-profile.md` if its project facts are still useful, or remove it after review. Preserve unrelated files and local customizations; remove a containing directory only when it is empty. Review `git diff` before committing.
