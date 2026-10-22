# MuleSkills

Guardrails for AI coding assistants on MuleSoft work.

Rules that make Claude Code and GitHub Copilot write and review MuleSoft code the way our team needs: project versions kept as they are, Mule error handling done properly, DataWeave written for the real runtime, MUnit tests that can actually fail, and nothing that assumes features Government Cloud does not have.

You copy a few files into each Mule project: `CLAUDE.md`, a `.claude` folder and a `.github/mule` folder. Claude Code, GitHub Copilot CLI and the GitHub Copilot desktop app read them when you work in that project. Nothing is installed on your machine and no tool, account or service is added.

Every rule is backed by MuleSoft or GitHub documentation, a reviewed article, or a test run on the DataWeave CLI. [docs/sources.md](docs/sources.md) records which.

## Quick start

For a teammate adding the rules to a Mule project, once this repository is in your work GitHub ([one-time team setup](#one-time-team-setup)). You need Git; on Windows, run the commands in Git Bash, which comes with Git for Windows. You also need Copilot CLI 1.0.89 or later, or Claude Code.

1. Clone this repository once:

   ```sh
   git clone https://github.com/<your-org>/MuleSkills.git ~/MuleSkills
   ```

2. In the Mule project, on a new branch, install the rules:

   ```sh
   git switch -c chore/mule-guardrails
   ~/MuleSkills/scripts/install.sh .
   ```

3. Fill in the project rows of `.github/mule/team-profile.md` ([details](#2-fill-in-the-projects-facts)).
4. Check that your assistant sees the rules: `copilot instruction list` should list `CLAUDE.md` and six `.claude/rules` files; in Claude Code, run `/memory`.
5. Commit and open a pull request in the project:

   ```sh
   git add CLAUDE.md .claude .github/mule
   git commit -m "Add MuleSoft guardrails"
   ```

The rest of this README explains each step and the choices behind it.

## What's in this repository

```
overlay/shared/                      <- copied into each Mule project (the default layout); edit rules here
  CLAUDE.md                          rules for every MuleSoft task
  .claude/rules/
    mule-xml.md                      Mule XML, error handling, architecture, logging
    dataweave.md                     DataWeave in .dwl files and inside Mule XML: correctness, money, dates, lookups
    munit.md                         MUnit tests that prove behavior
    maven.md                         POMs, artifact descriptors, Maven/CI configuration and deployment
    api-contract.md                  APIkit authentication, validation and contract-to-flow routing
    configuration-properties.md      property types, precedence, selection and encryption
  .claude/skills/team-mule-guardrails/
    SKILL.md                         step-by-step workflow the assistant can choose for MuleSoft tasks
    references/                      situational detail the rule files point to, opened on demand
      dataweave-operators.md         operator and function edge cases
      dataweave-output-formats.md    CSV and XML writer behavior
      dataweave-performance.md       performance, streaming and large payloads
      mule-connectors.md             SFTP, Anypoint MQ, Batch, Salesforce, VM queues, Cache scope
      mule-deployment-targets.md     CloudHub 1.0, clusters, API Manager, domains
  .github/mule/
    team-profile.md                  facts about the project: runtime, versions, deployment target
    task-recipes.md                  ready-made prompts for common tasks
overlay/github/                      the same rules in Copilot's own locations; generated, do not edit
docs/sources.md                      where each rule comes from (stays in this repository)
scripts/install.sh                   copies one layout into a project
scripts/build.py                     regenerates overlay/github from overlay/shared
scripts/check.py                     checks the files before you share them
scripts/check_dataweave.py           runs the retained DataWeave behavior checks
tests/                              installer, checker and generator regressions, and DataWeave fixtures
```

Only one layout goes into a Mule project. `docs/`, `scripts/` and `tests/` stay here.

## Which layout to install

| Layout | What it installs | Who reads it |
|---|---|---|
| `shared` (default) | `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.github/mule/` | Claude Code, GitHub Copilot CLI 1.0.89 or later, and the GitHub Copilot desktop app |
| `github` | `.github/copilot-instructions.md`, `.github/instructions/`, `.github/skills/`, `.github/mule/` | GitHub Copilot only, including Copilot CLI before 1.0.89 and Copilot code review. Claude Code reads none of it |

Install one layout per project. Copilot reads both sets when both are present, so every rule would load twice; the installer refuses to add one beside the other. The rules are identical in both: `overlay/github` is generated from `overlay/shared`.

Use `shared` unless someone on the project needs a Copilot client that does not read `.claude/rules`. Copilot CLI gained that in version 1.0.89 (28 September 2026); check with `copilot --version`.

## How the assistants use the files

Tested on 13 October 2026 on macOS with Claude Code 2.1.296, Copilot CLI 1.0.96 and the Copilot desktop app:

| File | Claude Code | Copilot CLI and desktop app |
|---|---|---|
| `CLAUDE.md` | Loaded at the start of every session | Added to every request |
| `.claude/rules/*.md` | Added automatically when Claude reads or edits a matching file | Listed for the model with their patterns and descriptions; the model opens the ones that match |
| `.claude/skills/team-mule-guardrails/SKILL.md` | Offered as a skill and loaded when the request matches its description | The same |
| `.claude/skills/team-mule-guardrails/references/*.md` | Opened when a rule file says to read one for the change at hand | The same |
| `.github/mule/*.md` | Opened when another file links to them, or when you attach them | The same |

The rule files match Mule XML and `log4j2.xml`, `.dwl` files, MUnit tests, `pom.xml`, `mule-artifact.json`, `.mvn/`, GitHub Actions workflows, RAML/API resources, and resource `.yaml`/`.properties` files.

**Copilot does not inject the rule files.** It gives the model a table of patterns, file paths and descriptions, and the model opens the files that match. Three things follow:

- The file-view tool returns only a "File too large" notice above about 20 KB, so every file in `overlay/` stays under 18,000 bytes and `scripts/check.py` enforces it. Rules that only matter for particular work live in `references/`, and the rule files say when to read each one.
- A Mule flow file matches both the Mule XML rules and the DataWeave rules, because DataWeave usually sits inside it in a Transform Message. Each file's `description`, a pointer at the top of the Mule XML rules, and a line in `CLAUDE.md` send the model to both.
- A small, fast model may skip the files altogether. In testing, the desktop app's Auto mode sometimes chose one that did. Pick a capable model, and keep rules that must always hold in `CLAUDE.md`, which is loaded on every request.

Other clients, according to their documentation (October 2026, not tested here):

| Client | What loads automatically | What to do |
|---|---|---|
| VS Code, Copilot Chat | Repository instructions and path-specific instructions; its settings reference lists `.claude/rules` among the default locations. Files a rule links to are not added unless `chat.includeReferencedInstructions` is on (it is off by default) | In agent mode, nothing extra: the agent can open the reference files. In other chat modes, turn that setting on or attach the reference files your change needs |
| Copilot code review, Copilot cloud agent | `.github/copilot-instructions.md`, `.github/instructions/` and `CLAUDE.md`; `.claude/rules` is not listed | They get `CLAUDE.md` from the `shared` layout but not the scoped rules. Install the `github` layout in projects that rely on them |
| Eclipse, Copilot Chat | Repository instructions only | Attach every rule file that matches the file you are working on (a Mule or MUnit XML file also matches the DataWeave rules), the reference files they name for your change, and `.github/mule/team-profile.md` |
| Anypoint Studio | Installed extension compatibility and instruction loading unverified | Verify the extension and activation; attach the guidance manually: every matching rule file, including the DataWeave rules for Mule or MUnit XML, and the reference files they name for your change |
| Any other client | Not established | Check that client's documentation; don't assume VS Code features |

API guidance matches `.raml` files and `src/main/resources/api/`; open it explicitly for OAS files elsewhere. Configuration-property guidance matches `.yaml` and `.properties` under main/test resources and applies only when Mule loads them as properties. API examples and ordinary test fixtures are not property files. The skill links to both files for related XML changes. Nonstandard layouts and other CI vendors need explicit guidance loading or project-reviewed globs.

## One-time team setup

Done once, by whoever looks after this repository for the team.

### 1. Confirm you are allowed to

Your assistant sends the files you work on, and these rules, to a cloud model. Confirm with your lead or security contact that the assistant is approved for the repositories and data you will use it on. These rules do not make an assistant offline or approved for government data. Never put credentials, tokens, personal data or production payloads in prompts.

### 2. Put this repository in your work GitHub

Create an empty repository in your organization (for example `MuleSkills`, with no README), then, from your clone of this repository, point it there and push:

```sh
git remote set-url origin https://github.com/<your-org>/MuleSkills.git
git push -u origin main
```

Teammates then clone it from there, as in the [quick start](#quick-start). If your organization allows GitHub Actions, the checks in `.github/workflows/check.yml` run on every push and pull request.

### 3. Fill in the team-wide facts once

Edit `overlay/shared/.github/mule/team-profile.md` in this repository and fill the rows that are the same for every project:

- Assistant client and version, and whether your organization approved it
- Government Cloud or Government Cloud Plus, and whether FIPS 140-3 mode is required
- Deployment target (CloudHub 1.0 or hybrid standalone runtimes), messaging, logging and API Manager setup
- Shared Exchange assets, connector approval rules and architecture conventions

Leave project-specific rows, such as Mule runtime, `minMuleVersion`, MUnit and connector versions, as `Unknown`; each project fills those. Run `python3 scripts/build.py`, then commit and push.

### 4. Make sure no other MuleSoft skill can take over

Assistants select skills using the prompt and skill description. MuleSoft's official `build-mule-integration` skill describes itself as the first and only action for any Mule change, so installing it can cause the assistant to select a conflicting workflow with live connector lookups, `latest` versions and a mandatory build. Check your client's skills list and these folders, and remove or turn off MuleSoft skills your team has not approved:

`.github/skills`, `.claude/skills`, `.agents/skills` in the project, and `~/.claude/skills`, `~/.copilot/skills`, `~/.agents/skills` in your home folder.

## Add the guardrails to a Mule project

### 1. Install the files

Work on a new branch in the project.

**macOS, Linux or Git Bash:**

```sh
git switch -c chore/mule-guardrails
~/MuleSkills/scripts/install.sh .
```

Add `--layout github` for the Copilot-only layout.

The script copies new files and never deletes anything. It checks all destinations before copying and rejects symbolic links or file/directory collisions so installation cannot follow a link outside the project. If the project already has a `CLAUDE.md`, it keeps the project's version and tells you; copy the rules from `overlay/shared/CLAUDE.md` into it by hand.

**Windows without Git Bash:** copy the contents of `overlay/shared/` into the project root, keeping the folders: `.claude/rules`, `.claude/skills/team-mule-guardrails` and `.github/mule`, plus `CLAUDE.md` if the project doesn't have one already.

**Moving a project from the `github` layout to `shared`:** the installer stops and lists the old rule files. Delete the files it lists, run it again, and commit both changes together. If `.github/copilot-instructions.md` holds only these guardrails, delete it too; if it also holds the project's own instructions, remove just the guardrail text, because Copilot loads that file alongside `CLAUDE.md`. `.github/mule/team-profile.md` stays where it is, so the project's facts are kept.

On a Mac, Finder hides folders starting with a dot. Press Cmd+Shift+. to show `.claude` and `.github`.

### 2. Fill in the project's facts

Open `.github/mule/team-profile.md` in the project and fill the project rows from the project's own files: `pom.xml` and its parent, `mule-artifact.json`, and the CI configuration. The assistant can help:

> Inspect this project's POM, parent POM, mule-artifact.json and CI files, then fill in the project rows of .github/mule/team-profile.md with values and where you found them. Leave anything you can't find as Unknown.

Check every value it writes. Never fill a value from a guess or a "latest version" example.

### 3. Check that your assistant actually loads the files

Do this once per client on a throwaway branch.

- **Copilot CLI:** run `copilot instruction list` in the project. It shows the instruction files it found, without sending a request. `CLAUDE.md` and the six `.claude/rules` files should be listed.
- **Claude Code:** run `/memory` in a session to see the files it loaded.
- **Any client:** add a marker line to the end of one file, for example `.claude/rules/dataweave.md`:

```
If this guidance is in your context, begin your reply with [dw-rules-loaded].
```

Open a `.dwl` file or a flow with a Transform Message in a fresh conversation and ask a harmless question about it. Inspect the client's references or instruction diagnostics and, where available, read traces for the profile and linked guidance. The marker is a smoke test that some guidance influenced this response; it does not prove every linked file loaded or that future requests will follow it. Repeat for the other matching file types, record the evidence in the profile, and remove the markers. If loading remains unverified, attach the relevant files manually. See GitHub's [instructions in use](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions#custom-instructions-in-use).

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

## Day-to-day use

Work as usual after verifying activation in your client. In Anypoint Studio or Eclipse, attach every matching rule file and `.github/mule/team-profile.md` to your request. A Mule or MUnit XML file matches two: its own rules and the DataWeave rules.

The rule files point to reference files for situational detail: operators, output formats and performance for DataWeave; connectors and deployment targets for Mule XML. A client that can open files reads them when needed. Where you attach files by hand, attach the references your change touches too, or the rules in them will not apply.

DataWeave written inside a Transform Message or an inline `#[...]` expression is covered the same way as a `.dwl` file: the DataWeave rules match Mule and MUnit XML, and include rules for editing a script inside XML.

For common tasks, start from a prompt in `.github/mule/task-recipes.md`:

| Recipe | Use it to |
|---|---|
| 1. Orient to an existing project | Get the assistant to read the project before changing anything |
| 2. Write or repair a DataWeave transform | Define null, empty, precision and date behavior before coding |
| 3. Add meaningful MUnit coverage | Get tests that check real behavior and can fail |
| 4. Review a Mule change | Get findings with file, line, impact and fix |
| 5. Check a restricted-environment tool | Check whether a product or tool is supported in Government Cloud before using it |
| 6. Diagnose a failing build or MUnit suite | Find the cause without upgrading versions to hide it |
| 7. Upgrade an approved Mule runtime or Java version | Check compatibility and behavior changes separately before the requested upgrade |

What to expect from an assistant with these rules:

- It reads the POM and profile before choosing versions, and keeps the project's versions.
- It asks about null, empty, precision, date and ordering rules that change the result.
- It reports which tests it actually ran and their counts, and says what it couldn't run. A build that wasn't run is never reported as passing.
- It points out when something isn't available in Government Cloud.

Some rules end with **(documented)** or **(CLI)**. Documented means MuleSoft's documentation states it. CLI means it was observed by running the DataWeave CLI (runtime 2.12.2, at its default and at language levels 2.4 to 2.9) and has not been run inside Mule; confirm it on your runtime when it decides the outcome.

You still review everything an assistant produces. These rules reduce common mistakes; they don't guarantee correct code.

## Keeping it current

**Change a rule here, not in a project.** Edit the file under `overlay/shared/`, then regenerate the Copilot-only layout:

```sh
python3 scripts/build.py
```

Never edit `overlay/github/` by hand; the next build overwrites it. When a rule refers to another installed file, write it as a Markdown link, not as plain text or a code span: the generator converts links to the other layout's paths, and stops if a path to another installed file would be left behind unconverted. For the same reason, file and folder names in `overlay/` may use only letters, digits, `.`, `_` and `-`. Open a pull request with the change and its source: a MuleSoft documentation page, or a DataWeave CLI test you ran. Add the source to `docs/sources.md`. Run the checks before pushing:

```sh
python3 scripts/check.py
python3 scripts/build.py --check
bash -n scripts/install.sh
python3 -m unittest discover -s tests -v
```

These checks run in GitHub Actions on every push and pull request (`.github/workflows/check.yml`). The regression tests use temporary projects to check installation in both layouts, update protection, unsafe paths, metadata, links and the generated layout. They need Python 3.9+, Bash and Git, and no Mule credentials. Delete that workflow if your organization doesn't use Actions.

Keep front matter to the checker-supported YAML subset: unique, unindented keys with single-line string values. Quote the `paths` globs and separate them with commas. Collections and block scalars are not supported; comments and blank lines are allowed. A rule file with no `paths` would load for every file in Claude Code, so the checker requires it. The checker validates inline local links, including titled links; it does not check remote availability or prove that a client loaded the files.

Keep every file in `overlay/` under 18,000 bytes; `scripts/check.py` fails above that. Copilot CLI and the desktop app cannot read a larger file in one call (20 KiB, measured on CLI 1.0.96), and whatever lies past that point is silently lost. When a rule file gets close, move rules that only matter for particular work into a file under `.claude/skills/team-mule-guardrails/references/` and state, in the rule file, when to read it. Every rule file needs a one-line `description`, and the checker requires it: Copilot shows it to the model next to the file's patterns, and in testing both matching files were opened in every session once each had one.

To test a DataWeave rule, write a small script and run it with the [DataWeave CLI](https://github.com/mulesoft/data-weave-cli). Use `--language-level` to match the project's `minMuleVersion` (Mule 4.6 is level 2.6, Mule 4.9 is 2.9):

```sh
dw run --language-level 2.9 -f test.dwl
```

Run the retained correctness fixtures with a locally installed CLI:

```sh
python3 scripts/check_dataweave.py --dw /path/to/dw
```

The runner checks language levels 2.4–2.9 by default and fails if the CLI is missing or a result differs. It compares JSON numbers as exact decimals and keeps Boolean and numeric values distinct. Add a `.dwl` fixture with either a neighboring `.json` expected result or an `.error.txt` expected failure diagnostic. Use `--language-level 2.9` for a targeted run. CI downloads CLI 2.12.3 (runtime 2.12.2), verifies its SHA-256 checksum, and runs the same fixtures. A language-level flag does not install an older engine or reproduce Mule's JVM and system properties. These are native CLI regression checks; validate runtime-sensitive behavior in the target Mule application as well.

**Update a project** on a branch. Pull the latest rules first, then install over the old ones:

```sh
git -C ~/MuleSkills pull
~/MuleSkills/scripts/install.sh . --update
git diff
```

`--update` replaces the shared rule files with this repository's versions. It never touches the project's `CLAUDE.md` or `team-profile.md`. Add `--layout github` for a project on that layout, where the protected file is `.github/copilot-instructions.md`.

**Remove from a project:** review the installed files on a branch. Remove only these shared files if they still belong to this overlay:

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

In the `github` layout the same files sit under `.github/instructions/` (named `*.instructions.md`) and `.github/skills/`.

Take only the guardrail text out of `CLAUDE.md`, preserving the project's other instructions. Keep `.github/mule/team-profile.md` if its project facts are still useful, or remove it after review. Preserve unrelated files and local customizations; remove a containing directory only when it is empty. Review `git diff` before committing.

## MuleSoft DX skills

MuleSoft publishes its own Copilot and agent skills in [mulesoft/mulesoft-dx](https://github.com/mulesoft/mulesoft-dx), distributed as the `@salesforce/mulesoft-vibes-skills` package. Don't install that package alongside these guardrails:

- Several skills (`build-mule-integration`, `upgrade-mule-app`, `generate-doc-description`, the run-configuration skills) describe themselves as the first or only action for any matching request, which can cause an assistant to select a conflicting workflow. Descriptions do not establish deterministic selection or client precedence.
- Many need the Anypoint CLI v4 with a DX or other plugin and an Anypoint Platform session, look up connector versions live, and pre-authorize shell commands. `upgrade-mule-app` installs `@latest` plugins and downloads JDKs; `secure-mule-app` downloads a JAR and passes the encryption key on the command line.
- Anypoint Code Builder, Omni Gateway and API Governance are not available in Government Cloud, and the hosted MuleSoft MCP server documents no Government Cloud endpoint.

To use one DX skill, adopt a reviewed copy rather than the package:

1. Read the skill's `SKILL.md` and any scripts at a specific commit.
2. Copy its folder into `overlay/shared/.claude/skills/dx-<name>/` and record the commit.
3. Set the frontmatter `name` to `dx-<name>`, rewrite the description to remove first/only-action claims, and remove `allowed-tools`. Keep frontmatter within this repository's supported single-line string format; move nested metadata into the body. Pin fetched versions and remove unavailable or unapproved steps.
4. Include the upstream Apache-2.0 license and applicable notices. Note modifications immediately after the frontmatter in `SKILL.md`.
5. Record the decision in the team profile's upstream section, run `scripts/build.py` and `scripts/check.py`, and repeat the [loading check](#3-check-that-your-assistant-actually-loads-the-files) to confirm a DataWeave request still selects `team-mule-guardrails`.

## Limits

- Clients differ in what they load. Run the [loading check](#3-check-that-your-assistant-actually-loads-the-files) for each client you use.
- Copilot CLI and the desktop app rely on the model to open the rule files. A capable model did so in every test session; a small one did not. Claude Code adds them itself.
- The loading tests ran on macOS. Windows was not tested.
- The DataWeave timings in the rules come from the DataWeave CLI on a Mac, not Mule's JVM. Use them for relative cost only.
- The rules target Mule 4.4 to 4.9 and DataWeave 2.4 to 2.9. Check the documentation for your project's version when it differs.
- The rules are guidance. An assistant can still ignore them, and they grant no permissions.

## Troubleshooting

| Problem | Fix |
|---|---|
| The assistant ignores the rules | Run the [loading check](#3-check-that-your-assistant-actually-loads-the-files), then use the workaround for your client |
| Copilot CLI does not list the `.claude/rules` files | Update it: `.claude/rules` needs version 1.0.89 or later. Or install the `github` layout |
| The installer says the project already has rule files from the other layout | Keep that layout with `--layout`, or delete the files it lists and run it again. See [installing](#1-install-the-files) |
| The assistant uses a different MuleSoft workflow, looks up "latest" versions or insists on `mvn clean package` | Another MuleSoft skill was chosen. See [one-time team setup](#4-make-sure-no-other-mulesoft-skill-can-take-over) |
| The assistant invents versions or upgrades dependencies | Fill in the project rows of `team-profile.md` |
| The script says a file differs | Compare the project's file with the one under `overlay/shared/` and merge by hand, or run with `--update` for the shared rule files |
| `scripts/build.py --check` fails | `overlay/github` is out of date. Run `python3 scripts/build.py` and commit the result |
| You can't see `.claude` or `.github` on a Mac | Press Cmd+Shift+. in Finder |
