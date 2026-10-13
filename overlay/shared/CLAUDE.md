# MuleSoft project context

For MuleSoft work, read [the team profile](.github/mule/team-profile.md) and use the `team-mule-guardrails` skill when available. Otherwise open [the task recipes](.github/mule/task-recipes.md).

- Rules for each file type are in [the rule files](.claude/rules/). If the ones that match the file you are about to read or change are not already in your context, open them first. A Mule or MUnit XML file matches its own rules and the DataWeave rules.
- Inspect the existing `pom.xml`, parent POM/property definitions, `mule-artifact.json`, and CI commands before choosing syntax, versions, dependencies, or tests. Unknown values stay unknown; do not replace project pins with "latest".
- Reconcile conflicting instructions with project evidence and approved restrictions before dependent changes. Ask for the unresolved decision while continuing independent inspection. This guidance does not change the client's instruction precedence or grant tool permissions; linked files must actually be opened or supplied.
- Follow the existing API contract and shared project conventions. Keep changes limited to the requested behavior. State assumptions that affect error, null, ordering, or retry semantics.
- Use only repository content and fixtures approved for the configured AI assistant and model. Local files and manual prompts may still be sent to a cloud model; this pack does not make the assistant offline or government-approved. Use sanitized fixtures. Do not put credentials, tokens, personal data, full production payloads, or private endpoints in prompts, examples, logs, or remote tools.
- Installation, authentication, cloud actions, and external tool use require the team's approved workflow. A skill is guidance, not permission. For government environments, verify the specific product and tool are supported before use.
- Return changed files, tests actually run and their results, and any checks blocked by the environment. Never label static checks as a Mule/MUnit pass. A MUnit run that skipped required validation, swallowed an expected error, or selected zero tests is not a pass.

These team guardrails are original guidance. They do not replace MuleSoft product documentation or organization policy.
