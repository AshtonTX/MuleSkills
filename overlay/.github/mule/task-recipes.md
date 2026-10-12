# Portable task recipes

These are copy/paste prompts, not client-specific slash commands. Replace the bracketed inputs with real paths and attach the relevant files if the client cannot read the repository. Do not paste secrets or production data. Use the on-demand `team-mule-guardrails` skill if visible; otherwise explicitly provide the linked guidance.

## 1. Orient to an existing Mule project

> Inspect [module path], its POM inheritance/properties, artifact descriptor, CI instructions, one flow, one transform, and one MUnit suite. Read [the team profile](team-profile.md). Summarize supported versions with their file evidence, existing conventions, and exact documented local checks. Leave unresolved values unknown. Propose the smallest instruction-profile changes that reflect this project; do not change dependencies, install tools, authenticate, or access cloud services.

## 2. Write or repair a DataWeave transform

> Read [input schema/sample], [output schema/expected sample], and [existing transform path]. Apply [DataWeave guidance](../instructions/dataweave.instructions.md). First identify missing/null/empty/wrong-type behavior, precision/date/ordering requirements, expected payload size, and any ambiguity that changes correctness. Implement [requested behavior] for the project's runtime. Add fixtures for a normal case, an applicable boundary, and invalid input. Explain the error outcome and run the available project checks. List any behavior not actually executed.

## 3. Add meaningful MUnit coverage

> Inspect [flow path] and the nearest existing suite. Apply [MUnit guidance](../instructions/munit.instructions.md). Cover [required behavior], [boundary], and [specific supported error]. Keep the business transform real; mock only [external processor/configuration]. Assert request-building values with a `before` spy and show how they bind to the connector's body/headers/parameters from its XML; an incoming-event spy alone does not prove the outbound request, and resolved-request claims need an approved local stub. Verify returned or target-variable values and required exact/minimum call counts. For propagation, ensure post-error checks execute using test-only capture of the specific expected error type, with failure if no error occurs; never wrap assertions or call checks in a handler that could catch them (MUnit 3.7+ assertion failures are catchable errors); do not change production semantics. Verify the mock matches and that tests use no live endpoint. Follow the suite's existing conventions; load fixtures from test resources; use parameterized suites for repeated scenarios. Run the documented targeted suite and regressions with current pins; report executed/ignored/failed counts and blockers.

## 4. Review a Mule change

> Review [diff/paths] against [contract] and the current project versions. Use [Mule XML](../instructions/mule-xml.instructions.md), [DataWeave](../instructions/dataweave.instructions.md), or [MUnit](../instructions/munit.instructions.md) guidance only as relevant. Prioritize actual correctness, error propagation, unsafe side effects, data exposure, and missing tests. For each finding give file/line, impact, evidence, and a minimal remedy. Separate verified findings from questions. Do not invent style defects or rewrite unrelated code.

## 5. Check a restricted-environment tool proposal

> Evaluate [specific product/tool and requested capability] for [approved environment description] using current official documentation and the team's policy. Separate local code generation from remote access, read-only discovery, deployment, and administration. Return the supported capability, source, prerequisites, and unresolved approval/support questions. Do not install, authenticate, configure MCP, transmit repository data, or call a live platform. If unavailable, suggest a local-file/manual-doc workflow.

## 6. Diagnose a failing build or MUnit suite

> Inspect [sanitized output] and the matching code/configuration. Follow [build guidance](../instructions/maven.instructions.md). Identify whether the failure is syntax, behavior, dependency compatibility, test setup, or environment. Reproduce using the documented safe local command if possible. Make the smallest in-scope fix and rerun the affected check; do not upgrade versions or add credentials to make the error disappear. Report exact checks passed, failed, and not run.
