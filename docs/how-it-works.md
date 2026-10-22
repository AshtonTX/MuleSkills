# How it works

What the files are, how each assistant loads them, and where that falls short.

- [What's in this repository](#whats-in-this-repository)
- [Two layouts](#two-layouts)
- [How the assistants load the files](#how-the-assistants-load-the-files)
- [Other clients](#other-clients)
- [Working with the rules](#working-with-the-rules)
- [Limits](#limits)

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
docs/                                these pages and the sources behind each rule (stay in this repository)
scripts/install.sh                   copies one layout into a project
scripts/build.py                     regenerates overlay/github from overlay/shared
scripts/check.py                     checks the files before you share them
scripts/check_dataweave.py           runs the retained DataWeave behavior checks
tests/                               installer, checker and generator regressions, and DataWeave fixtures
```

Only one layout goes into a Mule project. `docs/`, `scripts/` and `tests/` stay here.

## Two layouts

| Layout | What it installs | Who reads it |
|---|---|---|
| `shared` (default) | `CLAUDE.md`, `.claude/rules/`, `.claude/skills/`, `.github/mule/` | Claude Code, GitHub Copilot CLI 1.0.89 or later, and the GitHub Copilot desktop app |
| `github` | `.github/copilot-instructions.md`, `.github/instructions/`, `.github/skills/`, `.github/mule/` | GitHub Copilot only, including Copilot CLI before 1.0.89 and Copilot code review. Claude Code reads none of it |

Install one layout per project. Copilot reads both sets when both are present, so every rule would load twice; the installer refuses to add one beside the other. The rules are identical in both: `overlay/github` is generated from `overlay/shared`.

Use `shared` unless someone on the project needs a Copilot client that does not read `.claude/rules`. Copilot CLI gained that in version 1.0.89 (28 September 2026); check with `copilot --version`.

## How the assistants load the files

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

## Other clients

According to their documentation (October 2026, not tested here):

| Client | What loads automatically | What to do |
|---|---|---|
| VS Code, Copilot Chat | Repository instructions and path-specific instructions; its settings reference lists `.claude/rules` among the default locations. Files a rule links to are not added unless `chat.includeReferencedInstructions` is on (it is off by default) | In agent mode, nothing extra: the agent can open the reference files. In other chat modes, turn that setting on or attach the reference files your change needs |
| Copilot code review, Copilot cloud agent | `.github/copilot-instructions.md`, `.github/instructions/` and `CLAUDE.md`; `.claude/rules` is not listed | They get `CLAUDE.md` from the `shared` layout but not the scoped rules. Install the `github` layout in projects that rely on them |
| Eclipse, Copilot Chat | Repository instructions only | Attach every rule file that matches the file you are working on (a Mule or MUnit XML file also matches the DataWeave rules), the reference files they name for your change, and `.github/mule/team-profile.md` |
| Anypoint Studio | Installed extension compatibility and instruction loading unverified | Verify the extension and activation; attach the guidance manually: every matching rule file, including the DataWeave rules for Mule or MUnit XML, and the reference files they name for your change |
| Any other client | Not established | Check that client's documentation; don't assume VS Code features |

API guidance matches `.raml` files and `src/main/resources/api/`; open it explicitly for OAS files elsewhere. Configuration-property guidance matches `.yaml` and `.properties` under main/test resources and applies only when Mule loads them as properties. API examples and ordinary test fixtures are not property files. The skill links to both files for related XML changes. Nonstandard layouts and other CI vendors need explicit guidance loading or project-reviewed globs.

## Working with the rules

Work as usual after verifying activation in your client. In Anypoint Studio or Eclipse, attach every matching rule file and `.github/mule/team-profile.md` to your request. A Mule or MUnit XML file matches two: its own rules and the DataWeave rules.

The rule files point to reference files for situational detail: operators, output formats and performance for DataWeave; connectors and deployment targets for Mule XML. A client that can open files reads them when needed. Where you attach files by hand, attach the references your change touches too, or the rules in them will not apply.

DataWeave written inside a Transform Message or an inline `#[...]` expression is covered the same way as a `.dwl` file: the DataWeave rules match Mule and MUnit XML, and include rules for editing a script inside XML.

For common tasks, start from a prompt in [`task-recipes.md`](../overlay/shared/.github/mule/task-recipes.md):

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

## Limits

- Clients differ in what they load. Run the [loading check](setup.md#3-check-that-your-assistant-actually-loads-the-files) for each client you use.
- Copilot CLI and the desktop app rely on the model to open the rule files. A capable model did so in every test session; a small one did not. Claude Code adds them itself.
- The loading tests ran on macOS. Windows was not tested.
- The DataWeave timings in the rules come from the DataWeave CLI on a Mac, not Mule's JVM. Use them for relative cost only.
- The rules target Mule 4.4 to 4.9 and DataWeave 2.4 to 2.9. Check the documentation for your project's version when it differs.
- The rules are guidance. An assistant can still ignore them, and they grant no permissions.
