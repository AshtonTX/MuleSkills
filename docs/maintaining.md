# Changing the rules

How to change a rule, check it and share it with the team. [What's in this repository](how-it-works.md#whats-in-this-repository) shows where each file lives.

- [Change a rule](#change-a-rule)
- [Run the checks](#run-the-checks)
- [Requirements for overlay files](#requirements-for-overlay-files)
- [Test a DataWeave rule](#test-a-dataweave-rule)
- [MuleSoft DX skills](#mulesoft-dx-skills)

## Change a rule

**Change a rule here, not in a project.** Edit the file under `overlay/shared/`, then regenerate the Copilot-only layout:

```sh
python3 scripts/build.py
```

Never edit `overlay/github/` by hand; the next build overwrites it. Open a pull request with the change and its source: a MuleSoft documentation page, or a DataWeave CLI test you ran. Add the source to [sources.md](sources.md). Once it is merged, teammates pick it up when they [update their projects](setup.md#update-a-project).

## Run the checks

Run these before pushing:

```sh
python3 scripts/check.py
python3 scripts/build.py --check
bash -n scripts/install.sh
python3 -m unittest discover -s tests -v
```

These checks run in GitHub Actions on every push and pull request (`.github/workflows/check.yml`). The regression tests use temporary projects to check installation in both layouts, update protection, unsafe paths, metadata, links and the generated layout. They need Python 3.9+, Bash and Git, and no Mule credentials. Delete that workflow if your organization doesn't use Actions.

## Requirements for overlay files

- **Links.** When a rule refers to another installed file, write it as a Markdown link, not as plain text or a code span: the generator converts links to the other layout's paths, and stops if a path to another installed file would be left behind unconverted. For the same reason, file and folder names in `overlay/` may use only letters, digits, `.`, `_` and `-`.
- **Front matter.** Keep front matter to the checker-supported YAML subset: unique, unindented keys with single-line string values. Quote the `paths` globs and separate them with commas. Collections and block scalars are not supported; comments and blank lines are allowed. A rule file with no `paths` would load for every file in Claude Code, so the checker requires it. The checker validates inline local links, including titled links; it does not check remote availability or prove that a client loaded the files.
- **Description.** Every rule file needs a one-line `description`, and the checker requires it: Copilot shows it to the model next to the file's patterns, and in testing both matching files were opened in every session once each had one.
- **Size.** Keep every file in `overlay/` under 18,000 bytes; `scripts/check.py` fails above that. Copilot CLI and the desktop app cannot read a larger file in one call (20 KiB, measured on CLI 1.0.96), and whatever lies past that point is silently lost. When a rule file gets close, move rules that only matter for particular work into a file under `.claude/skills/team-mule-guardrails/references/` and state, in the rule file, when to read it.

## Test a DataWeave rule

Write a small script and run it with the [DataWeave CLI](https://github.com/mulesoft/data-weave-cli). Use `--language-level` to match the project's `minMuleVersion` (Mule 4.6 is level 2.6, Mule 4.9 is 2.9):

```sh
dw run --language-level 2.9 -f test.dwl
```

Run the retained correctness fixtures with a locally installed CLI:

```sh
python3 scripts/check_dataweave.py --dw /path/to/dw
```

The runner checks language levels 2.4–2.9 by default and fails if the CLI is missing or a result differs. It compares JSON numbers as exact decimals and keeps Boolean and numeric values distinct. Add a `.dwl` fixture with either a neighboring `.json` expected result or an `.error.txt` expected failure diagnostic. Use `--language-level 2.9` for a targeted run. CI downloads CLI 2.12.3 (runtime 2.12.2), verifies its SHA-256 checksum, and runs the same fixtures. A language-level flag does not install an older engine or reproduce Mule's JVM and system properties. These are native CLI regression checks; validate runtime-sensitive behavior in the target Mule application as well.

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
5. Work through the upstream checklist in [`team-profile-guide.md`](../overlay/shared/.github/mule/team-profile-guide.md#upstream-mulesoft-skills-complete-before-enabling) and record the decision on the team profile's Upstream MuleSoft skill line, run `scripts/build.py` and `scripts/check.py`, and repeat the [loading check](setup.md#3-check-that-your-assistant-actually-loads-the-files) to confirm a DataWeave request still selects `team-mule-guardrails`.
