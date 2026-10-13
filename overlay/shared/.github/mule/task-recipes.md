# Portable task recipes

These are copy/paste prompts, not client-specific slash commands. Replace the bracketed inputs with real paths and attach the relevant files if the client cannot read the repository. Do not paste secrets or production data. Use the on-demand `team-mule-guardrails` skill if visible; otherwise explicitly provide the linked guidance.

## 1. Orient to an existing Mule project

> Inspect [module path], its POM inheritance/properties, artifact descriptor, CI instructions, one flow, one transform, and one MUnit suite. Read [the team profile](team-profile.md). Summarize supported versions with their file evidence, existing conventions, and exact documented local checks. Leave unresolved values unknown. Propose the smallest instruction-profile changes that reflect this project; do not change dependencies, install tools, authenticate, or access cloud services.

## 2. Write or repair a DataWeave transform

> Read [input schema/sample], [output schema/expected sample], and [existing transform path]. Apply [DataWeave guidance](../../.claude/rules/dataweave.md). First identify missing/null/empty/wrong-type behavior, precision/date/ordering requirements, expected payload size, and any ambiguity that changes correctness. Implement [requested behavior] for the project's runtime. Add fixtures for a normal case, an applicable boundary, and invalid input. Explain the error outcome and run the available project checks. List any behavior not actually executed.

## 3. Add meaningful MUnit coverage

> Inspect [flow path] and the nearest existing suite. Apply [MUnit guidance](../../.claude/rules/munit.md). Cover [required behavior], [boundary], and [specific supported error]. Keep the business transform real; mock only [external processor/configuration]. Assert request-building values with a `before` spy and show how they bind to the connector's body/headers/parameters from its XML; an incoming-event spy alone does not prove the outbound request, and resolved-request claims need an approved local stub. Verify returned or target-variable values and required exact/minimum call counts. For propagation, ensure post-error checks execute using test-only capture of the specific expected error type, with failure if no error occurs; never wrap assertions or call checks in a handler that could catch them (MUnit 3.7+ assertion failures are catchable errors); do not change production semantics. Verify the mock matches and that tests use no live endpoint. Follow the suite's existing conventions; load fixtures from test resources; use parameterized suites for repeated scenarios. Run the documented targeted suite and regressions with current pins; report executed/ignored/failed counts and blockers.

## 4. Review a Mule change

> Review [diff/paths] against [contract] and the current project versions. Use [Mule XML](../../.claude/rules/mule-xml.md), [DataWeave](../../.claude/rules/dataweave.md), or [MUnit](../../.claude/rules/munit.md) guidance only as relevant. Prioritize actual correctness, error propagation, unsafe side effects, data exposure, and missing tests. For each finding give file/line, impact, evidence, and a minimal remedy. Separate verified findings from questions. Do not invent style defects or rewrite unrelated code.

## 5. Check a restricted-environment tool proposal

> Evaluate [specific product/tool and requested capability] for [approved environment description] using current official documentation and the team's policy. Separate local code generation from remote access, read-only discovery, deployment, and administration. Return the supported capability, source, prerequisites, and unresolved approval/support questions. Do not install, authenticate, configure MCP, transmit repository data, or call a live platform. If unavailable, suggest a local-file/manual-doc workflow.

## 6. Diagnose a failing build or MUnit suite

> Inspect [sanitized output], the invoked command or Studio run configuration, and the matching code/configuration. Follow [build guidance](../../.claude/rules/maven.md) and, for MUnit, [test guidance](../../.claude/rules/munit.md). Establish whether tests were selected and started, then distinguish dependency/runtime failure, application initialization, test setup, assertion failure and coverage failure. Inspect the current run's Surefire reports when available. Trace the failure to the contract before changing production code or expected results; check mock matching, target setup and matcher APIs. Reproduce with the documented safe local command, make the smallest in-scope fix and rerun with current pins and coverage requirements. Do not upgrade versions or add credentials to hide the failure. Report executed, ignored and failed counts, and checks not run.

## 7. Upgrade an approved Mule runtime or Java version

> Apply [build guidance](../../.claude/rules/maven.md) to the requested move from [current runtime/Java] to [target runtime/Java]. Review runtime, `minMuleVersion`, compiler target and test JVM changes separately. Check pinned connectors, JDBC libraries, custom Java and DataWeave access to POJOs for target compatibility; do not bypass Java 17 access restrictions with unsupported `--add-opens`, `--add-exports` or `--add-modules`. Identify required policy upgrades before upgrading their apps or proxies. For CloudHub 1.0, verify the pinned Mule Maven Plugin's release-channel and Java selection behavior rather than assuming a runtime string selects Java 17. Use the established standalone workflow for hybrid. Implement only the requested upgrade and required compatible changes, run approved checks on the target runtime, and report unexecuted deployment/performance checks. See [Java support](https://docs.mulesoft.com/general/java-support) and [CloudHub deployment parameters](https://docs.mulesoft.com/mule-runtime/4.9/deploy-to-cloudhub).
