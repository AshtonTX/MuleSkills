# MuleSkills

GitHub Copilot guardrails for MuleSoft work.

Instructions that make GitHub Copilot write and review MuleSoft code the way our team needs: project versions kept as they are, Mule error handling done properly, DataWeave written for the real runtime, MUnit tests that can actually fail, and nothing that assumes features Government Cloud does not have.

You copy a small `.github` folder into each Mule project. Copilot reads it when you work in that project. Nothing is installed on your machine and no tool, account or service is added.

Every rule is backed by MuleSoft or GitHub documentation, a reviewed article, or a test run on the DataWeave CLI. [docs/sources.md](docs/sources.md) records which.

## What's in this repository

```
overlay/.github/                     <- copied into each Mule project
  copilot-instructions.md            rules for every MuleSoft task
  instructions/
    mule-xml.instructions.md         Mule XML, error handling, architecture, Government Cloud, logging
    dataweave.instructions.md        DataWeave correctness, money, dates, lookups, output formats, performance
    munit.instructions.md            MUnit tests that prove behavior
    maven.instructions.md            POMs, versions, builds and deployment
  skills/team-mule-guardrails/
    SKILL.md                         step-by-step workflow Copilot can choose for MuleSoft tasks
  mule/
    team-profile.md                  facts about the project: runtime, versions, deployment target
    task-recipes.md                  ready-made prompts for common tasks
docs/sources.md                      where each rule comes from (stays in this repository)
scripts/install.sh                   copies overlay/ into a project
scripts/check.py                     checks the files before you share them
scripts/check_dataweave.py           runs the retained DataWeave behavior checks
tests/                              installer/checker regressions and DataWeave fixtures
```

Only `overlay/.github/` goes into Mule projects. `docs/`, `scripts/` and `tests/` stay here.

## How Copilot uses the files

| File | When Copilot reads it |
|---|---|
| `copilot-instructions.md` | Every request in the project, in clients that support repository instructions |
| `instructions/*.instructions.md` | When you work on matching files: Mule XML and `log4j2.xml`, `.dwl` files, MUnit tests, `pom.xml` and `mule-artifact.json` |
| `skills/team-mule-guardrails/SKILL.md` | When Copilot decides your request matches the skill's description, in clients that support skills |
| `mule/*.md` | When another file links to them and the client follows the link, or when you attach them |

Not every Copilot client loads every file. According to GitHub's documentation (October 2026):

| Client | What loads automatically | What to do |
|---|---|---|
| VS Code, Copilot Chat | Repository instructions, path-specific instructions; skills in agent mode | Nothing extra |
| GitHub Copilot app (desktop) | A repository Instructions setting and skills; loading `.github` instruction files is not documented | If the check below shows the rules are not applied, paste the text of `copilot-instructions.md` into the repository Instructions setting, and attach the relevant `instructions/` file and `mule/team-profile.md` |
| Eclipse, Copilot Chat | Repository instructions only | Attach the relevant `instructions/` file and `mule/team-profile.md` to your request |
| Anypoint Studio | Installed extension compatibility and instruction loading unverified | Verify the extension and activation; attach the relevant guidance manually |
| Any other client | Not established | Check that client's documentation; don't assume VS Code features |

## Set it up at work

### 1. Confirm you are allowed to

Copilot sends the files you work on, and these instructions, to a cloud model. Confirm with your lead or security contact that Copilot is approved for the repositories and data you will use it on. These instructions do not make Copilot offline or approved for government data. Never put credentials, tokens, personal data or production payloads in prompts.

### 2. Put this repository in your work GitHub

Create an empty repository in your organization (for example `MuleSkills`, no README), then from this folder:

```sh
git remote add origin https://github.com/<your-org>/MuleSkills.git
git push -u origin main
```

### 3. Fill in the team-wide facts once

Edit `overlay/.github/mule/team-profile.md` in this repository and fill the rows that are the same for every project:

- Copilot client and version, and whether your organization approved it
- Government Cloud or Government Cloud Plus, and whether FIPS 140-3 mode is required
- Deployment target (CloudHub 1.0 or hybrid standalone runtimes), messaging, logging and API Manager setup
- Shared Exchange assets, connector approval rules and architecture conventions

Leave project-specific rows, such as Mule runtime, `minMuleVersion`, MUnit and connector versions, as `Unknown`; each project fills those. Commit and push.

### 4. Make sure no other MuleSoft skill can take over

Copilot selects skills using the prompt and skill description. MuleSoft's official `build-mule-integration` skill describes itself as the first and only action for any Mule change, so installing it can cause Copilot to select a conflicting workflow with live connector lookups, `latest` versions and a mandatory build. Check your client's skills list and these folders, and remove or turn off MuleSoft skills your team has not approved:

`.github/skills`, `.claude/skills`, `.agents/skills` in the project, and `~/.copilot/skills`, `~/.agents/skills` in your home folder.

### 5. Add the guardrails to a Mule project

Work on a new branch in the project.

**macOS, Linux or Git Bash:**

```sh
git switch -c chore/copilot-guardrails
/path/to/MuleSkills/scripts/install.sh .
```

The script copies new files and never deletes anything. It checks all destinations before copying and rejects symbolic links or file/directory collisions so installation cannot follow a link outside the project. If the project already has a `.github/copilot-instructions.md`, it keeps the project's version and tells you; copy the rules from `overlay/.github/copilot-instructions.md` into it by hand.

**Windows without Git Bash:** copy the folders inside `overlay/.github/` (`instructions`, `skills`, `mule`) into the project's `.github` folder, and copy `copilot-instructions.md` if the project doesn't have one already.

On a Mac, Finder hides folders starting with a dot. Press Cmd+Shift+. to show `.github`.

### 6. Fill in the project's facts

Open `.github/mule/team-profile.md` in the project and fill the project rows from the project's own files: `pom.xml` and its parent, `mule-artifact.json`, and the CI configuration. Copilot can help:

> Inspect this project's POM, parent POM, mule-artifact.json and CI files, then fill in the project rows of .github/mule/team-profile.md with values and where you found them. Leave anything you can't find as Unknown.

Check every value it writes. Never fill a value from a guess or a "latest version" example.

### 7. Check that Copilot actually loads the files

Do this once per client on a throwaway branch. Add a marker line to the end of one file, for example in `instructions/dataweave.instructions.md`:

```
If this guidance is in your context, begin your reply with [dw-rules-loaded].
```

Open a `.dwl` file in a fresh conversation and ask Copilot a harmless question about it. Inspect the client's references or instruction diagnostics and, where available, read traces for the profile and linked guidance. The marker is a smoke test that some guidance influenced this response; it does not prove every linked file loaded or that future requests will follow it. Repeat for the other matching file types, record the evidence in the profile, and remove the markers. If loading remains unverified, attach the relevant files manually. See GitHub's [instructions in use](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions#custom-instructions-in-use).

### 8. Commit and open a pull request

```sh
git add .github
git commit -m "Add Copilot MuleSoft guardrails"
```

Review the diff like any other change and merge it with the team's normal process.

## Day-to-day use

Work as usual after verifying activation in your client. VS Code supports automatic repository and path-specific instructions; use the desktop app's verified settings or the fallback above. In Anypoint Studio or Eclipse, attach the matching `instructions/` file and `mule/team-profile.md` to your request.

For common tasks, start from a prompt in `.github/mule/task-recipes.md`:

| Recipe | Use it to |
|---|---|
| 1. Orient to an existing project | Get Copilot to read the project before changing anything |
| 2. Write or repair a DataWeave transform | Define null, empty, precision and date behavior before coding |
| 3. Add meaningful MUnit coverage | Get tests that check real behavior and can fail |
| 4. Review a Mule change | Get findings with file, line, impact and fix |
| 5. Check a restricted-environment tool | Check whether a product or tool is supported in Government Cloud before using it |
| 6. Diagnose a failing build or MUnit suite | Find the cause without upgrading versions to hide it |

What to expect from Copilot with these rules:

- It reads the POM and profile before choosing versions, and keeps the project's versions.
- It asks about null, empty, precision, date and ordering rules that change the result.
- It reports which tests it actually ran and their counts, and says what it couldn't run. A build that wasn't run is never reported as passing.
- It points out when something isn't available in Government Cloud.

Some rules end with **(documented)** or **(CLI)**. Documented means MuleSoft's documentation states it. CLI means it was observed by running the DataWeave CLI (runtime 2.12.2, at its default and at language levels 2.4 to 2.9) and has not been run inside Mule; confirm it on your runtime when it decides the outcome.

You still review everything Copilot produces. These rules reduce common mistakes; they don't guarantee correct code.

## Keeping it current

**Change a rule here, not in a project.** Open a pull request to this repository with the change and its source: a MuleSoft documentation page, or a DataWeave CLI test you ran. Add the source to `docs/sources.md`. Run the checks before pushing:

```sh
python3 scripts/check.py
bash -n scripts/install.sh
python3 -m unittest discover -s tests -v
```

These checks run in GitHub Actions on every push and pull request (`.github/workflows/check.yml`). The regression tests use temporary projects to check installation, update protection, unsafe paths, metadata and links. They need Python 3.9+, Bash and Git, and no Mule credentials. Delete that workflow if your organization doesn't use Actions.

Keep front matter to the checker-supported YAML subset: unique, unindented keys with single-line string values. Quote `applyTo` globs. Collections and block scalars are not supported; comments and blank lines are allowed. The checker validates inline local links, including titled links; it does not check remote availability or prove that a Copilot client loaded the files.

To test a DataWeave rule, write a small script and run it with the [DataWeave CLI](https://github.com/mulesoft/data-weave-cli). Use `--language-level` to match the project's `minMuleVersion` (Mule 4.6 is level 2.6, Mule 4.9 is 2.9):

```sh
dw run --language-level 2.9 -f test.dwl
```

Run the retained correctness fixtures with a locally installed CLI:

```sh
python3 scripts/check_dataweave.py --dw /path/to/dw
```

The runner checks language levels 2.4–2.9 by default and fails if the CLI is missing or a result differs. It compares JSON numbers as exact decimals and keeps Boolean and numeric values distinct. Add a `.dwl` fixture with either a neighboring `.json` expected result or an `.error.txt` expected failure diagnostic. Use `--language-level 2.9` for a targeted run. CI downloads CLI 2.12.3 (runtime 2.12.2), verifies its SHA-256 checksum, and runs the same fixtures. A language-level flag does not install an older engine or reproduce Mule's JVM and system properties. These are native CLI regression checks; validate runtime-sensitive behavior in the target Mule application as well.

**Update a project** on a branch:

```sh
/path/to/MuleSkills/scripts/install.sh . --update
git diff
```

`--update` replaces the shared rule files with this repository's versions. It never touches the project's `copilot-instructions.md` or `team-profile.md`.

**Remove from a project:** review the installed files on a branch. Remove only these shared files if they still belong to this overlay:

- `.github/instructions/dataweave.instructions.md`
- `.github/instructions/maven.instructions.md`
- `.github/instructions/mule-xml.instructions.md`
- `.github/instructions/munit.instructions.md`
- `.github/skills/team-mule-guardrails/SKILL.md`
- `.github/mule/task-recipes.md`

Take only the guardrail text out of `.github/copilot-instructions.md`, preserving the project's other instructions. Keep `.github/mule/team-profile.md` if its project facts are still useful, or remove it after review. Preserve unrelated files and local customizations; remove a containing directory only when it is empty. Review `git diff` before committing.

## MuleSoft DX skills

MuleSoft publishes its own Copilot and agent skills in [mulesoft/mulesoft-dx](https://github.com/mulesoft/mulesoft-dx), distributed as the `@salesforce/mulesoft-vibes-skills` package. Don't install that package alongside these guardrails:

- Several skills (`build-mule-integration`, `upgrade-mule-app`, `generate-doc-description`, the run-configuration skills) describe themselves as the first or only action for any matching request, which can cause Copilot to select a conflicting workflow. Descriptions do not establish deterministic selection or client precedence.
- Many need the Anypoint CLI v4 with a DX or other plugin and an Anypoint Platform session, look up connector versions live, and pre-authorize shell commands. `upgrade-mule-app` installs `@latest` plugins and downloads JDKs; `secure-mule-app` downloads a JAR and passes the encryption key on the command line.
- Anypoint Code Builder, Omni Gateway and API Governance are not available in Government Cloud, and the hosted MuleSoft MCP server documents no Government Cloud endpoint.

To use one DX skill, adopt a reviewed copy rather than the package:

1. Read the skill's `SKILL.md` and any scripts at a specific commit.
2. Copy its folder into `overlay/.github/skills/dx-<name>/` and record the commit.
3. Set the frontmatter `name` to `dx-<name>`, rewrite the description to remove first/only-action claims, and remove `allowed-tools`. Keep frontmatter within this repository's supported single-line string format; move nested metadata into the body. Pin fetched versions and remove unavailable or unapproved steps.
4. Include the upstream Apache-2.0 license and applicable notices. Note modifications immediately after the frontmatter in `SKILL.md`.
5. Record the decision in the team profile's upstream section, run `scripts/check.py`, and repeat the loading check from step 7 to confirm a DataWeave request still selects `team-mule-guardrails`.

## Limits

- Copilot clients differ in what they load. Check step 7 for each client you use.
- The DataWeave timings in the rules come from the DataWeave CLI on a Mac, not Mule's JVM. Use them for relative cost only.
- The rules target Mule 4.4 to 4.9 and DataWeave 2.4 to 2.9. Check the documentation for your project's version when it differs.
- The rules are guidance. Copilot can still ignore them, and they grant no permissions.

## Troubleshooting

| Problem | Fix |
|---|---|
| Copilot ignores the rules | Run the check in step 7, then use the workaround for your client |
| Copilot uses a different MuleSoft workflow, looks up "latest" versions or insists on `mvn clean package` | Another MuleSoft skill was chosen. See step 4 |
| Copilot invents versions or upgrades dependencies | Fill in the project rows of `team-profile.md` |
| The script says a file differs | Compare the project's file with `overlay/` and merge by hand, or run with `--update` for the shared rule files |
| You can't see `.github` on a Mac | Press Cmd+Shift+. in Finder |
