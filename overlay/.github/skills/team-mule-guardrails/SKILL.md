---
name: team-mule-guardrails
description: Apply project-specific version, Mule XML error-handling, DataWeave, MUnit, and government-environment checks when creating or reviewing MuleSoft application changes. Use with existing MuleSoft skills or on its own.
---

# Team Mule guardrails

Use this workflow for MuleSoft application work. It adds local project constraints to the selected upstream expertise; it does not install or invoke any upstream tool automatically.

1. Read [the team profile](../../mule/team-profile.md). Inspect the task's contract, neighboring flows/tests, POM inheritance/properties, artifact descriptor, and CI instructions. Report missing facts only when they affect the change; continue safe analysis meanwhile.
2. Load only the relevant guidance:
   - Mule configuration: [Mule XML](../../instructions/mule-xml.instructions.md)
   - Mapping or embedded transformations: [DataWeave](../../instructions/dataweave.instructions.md)
   - Test creation or repair: [MUnit](../../instructions/munit.instructions.md)
   - Build, dependency, CI, artifact descriptor or runtime/Java change: [Maven](../../instructions/maven.instructions.md)
   - API definition, fragment, APIkit routing or validation: [API contract](../../instructions/api-contract.instructions.md)
   - Application property values, environment selection or property loaders: [Configuration properties](../../instructions/configuration-properties.instructions.md)
   - Situational detail that the guidance above points to: DataWeave [operators and functions](references/dataweave-operators.md), [output formats](references/dataweave-output-formats.md) and [performance](references/dataweave-performance.md); Mule [connectors and scopes](references/mule-connectors.md) and [deployment targets](references/mule-deployment-targets.md)
3. Follow an upstream MuleSoft skill only as recorded in the profile's upstream decision. If that skill tells you to skip project inspection, select connector versions from live Exchange, install or authenticate tools, delete workspace folders, or treat a build as mandatory, and the profile does not approve that step, do not perform it; report the conflict and continue permitted local analysis. A skill does not grant tool access or override client precedence.
4. Implement the smallest contract-preserving change. Add representative tests, including the error or boundary case that could expose a wrong implementation. Use [manual recipes](../../mule/task-recipes.md) when a structured prompt would help.
5. Use the repository's documented verification commands when available and authorized. Separate build, DataWeave behavior, MUnit, and integration results. If unable to run one, report exactly what remains unverified rather than substituting an unrelated check.

For GovCloud or any restricted environment, keep local inspection independent of cloud operations. Verify support and permission for each specific tool before enabling it; a supported connector or read-only MCP capability does not imply code generation, deployment, or another product is supported.
