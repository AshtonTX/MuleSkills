# Filling in the team profile

How to fill in [the team profile](team-profile.md). Record facts from evidence, not proposed version upgrades. Write `Unknown` when you can't find the evidence; never infer a value. Use approved names and references only; never record credentials, secret values, encryption keys, sensitive payloads, private endpoints or access grants.

The Team section is filled once in the MuleSkills repository and reaches every project on install. The Project section is filled in each project.

## Where to find each fact

| Fact | Evidence to record |
|---|---|
| AI assistant clients | `copilot --version` (the default `shared` layout needs 1.0.89 or later), `claude --version`, the model selected (a small model chosen by Copilot's Auto mode skipped rule files in testing), and organization approval |
| Deployment/control plane | Approved platform/team evidence, region and feature support. Recheck the profile's Government Cloud limits against MuleSoft's current list |
| FIPS 140-3 mode required | Approved platform/team evidence |
| Messaging, logging and API management | Anypoint MQ, JMS broker or VM only; log destination (CloudHub logs or forwarded through `log4j2.xml`) and logger used; API Manager instances and per-environment autodiscovery IDs |
| Shared assets | Exchange templates, fragments and libraries the team reuses (for example a common error handler or logging framework); use these instead of writing new ones |
| Connector approval | Connectors approved for use and their support category (Select, Premium, Certified partner-supported, or unsupported community); adding a connector needs approval |
| Architecture conventions | Whether API-led layers (system/process/experience) are used and how projects are named per layer (for example `-sapi`, `-papi`, `-eapi` suffixes); health-check endpoint convention; file layout (for example a common flows file and per-resource folders under `src/main/resources`); where shared configuration and the default error handler live; per-environment property file pattern; error response shape and code list |
| Approved data and external access | Allowed code/API-spec/metadata classes, public searches/docs, tools, model/service and network rules; GitHub enterprise policies or managed settings that restrict MCP servers and plugins |
| Upstream MuleSoft skill | Reviewed file/SHA, license, scripts and tool prerequisites, and decision owner; skills already present in project/personal skill folders or the client's skills list. See [Upstream MuleSoft skills](#upstream-mulesoft-skills-complete-before-enabling) |
| Loading check | Each client, its version, the date and the outcome. See [Loading check](#loading-check-complete-on-each-client-the-team-uses) |
| Repository, module, commit | Working checkout and module POM |
| Mule runtime patch and release channel | Deployment configuration, CI and resolved POM |
| `minMuleVersion` | `mule-artifact.json`; distinguish declared minimum from deployed runtime |
| DataWeave engine and effective language level | Runtime mapping and `minMuleVersion`; `%dw 2.0` is not an engine pin |
| Runtime JVM | Approved runtime and Java compatibility evidence |
| Maven version and Maven's actual JVM | Approved wrapper/CI configuration and `mvn -version` when permitted |
| MUnit version, runtime and JVM | Plugin configuration (`munit.runtimeversion` in MUnit 3.7 docs; `runtimeVersion` is the deprecated alias), toolchain and actual execution output. 3.6 versus 3.7 changes assertion-error handling and supported Maven range |
| Compiled Java bytecode target | Compiler configuration and effective properties |
| Mule Maven Plugin version/execution | Resolved plugin version, binding and profile effects |
| MUnit runner, tools and Maven plugin versions | Exact coordinates and resolved effective POM |
| Connector and JDBC driver coordinates | Group/artifact/version/classifier; inherited resolution and compatibility. If a driver was added through Studio's Required Libraries instead of a declared dependency, record the exact jar and where it is configured |
| Unresolved parent/property versions | Name missing evidence; do not infer a value |
| Runtime topology | CloudHub 1.0: worker count and size (two or more workers for high availability), VPC and dedicated load balancer use (private ports 8091/8092), Persistent Queues, Object Store v2. Standalone: cluster or server group, Mule domain projects, how organization credentials and properties are supplied |
| API/error contract and shared conventions | Root RAML/OAS path and version, referenced fragments/assets, pinned APIkit coordinates, parser/validation settings, authentication enforcement reference, tests, flow boundaries, naming and redacted logging |
| Configuration property resolution | Provider files and loading order, environment-selector source, deployment override names, secure-properties module and encryption-setting references; never record secret values or encryption keys |
| Null/empty/type/precision/date/ordering rules | Contract plus positive and negative fixtures |
| Targeted and aggregate local checks | Reviewed README/CI commands, selected counts, plugin side effects |
| Reviewed local examples | Paths to one transform, flow/error handler and MUnit suite |

## Upstream MuleSoft skills: complete before enabling

Record each selected/excluded/adapted section, reason, owner and date. For the official skill (reviewed in `docs/sources.md` of the MuleSkills repository), resolve these decisions explicitly:

- Preserve project-pinned versions; exclude mandatory latest-connector selection, including update mode. Use approved metadata for the exact pinned coordinates.
- Exclude live discovery, installation, authentication, or generation when unavailable/unapproved; identify the approved local evidence alternative.
- Replace unconditional `mvn clean package` completion with the project's reviewed validation commands. Record precise blocked checks without claiming completion or inventing a pass.
- Confirm actual tool names/schemas and product/environment support before use. Skill prose grants no permission and does not establish client precedence.
- Its description demands to be the first and only action before reading project files for any Mule change, including DataWeave: approve only a reviewed fork that changes this, or keep it disabled.
- Remove `allowed-tools` pre-authorization in any approved copy; client policy decides tool access.
- Exclude the step that deletes the workspace `tmp/` folder; the project may own it.
- The package bundles about twenty other MuleSoft skills (for example `upgrade-mule-app`, which installs `@latest` CLI plugins and downloads JDKs). Decide each one separately; install only reviewed copies pinned to a commit, with automatic updates off.
- Record how unapproved skills are disabled in the actual client, and the probe showing a DataWeave task did not select them.

Record the decision on the profile's **Upstream MuleSoft skill** line. Do not silently treat the proposed exceptions above as organizational approval.

## Loading check: complete on each client the team uses

First list what the client found: `copilot instruction list` for Copilot CLI, `/memory` in Claude Code. Then run the probes.

| Probe | Expected candidate context |
|---|---|
| Main Mule XML | Repository, Mule XML and embedded DataWeave rules |
| `.dwl` | Repository and DataWeave rules |
| MUnit XML with expressions | Repository, MUnit and DataWeave rules |
| POM / artifact descriptor / `.mvn/` / GitHub Actions workflow | Repository and Maven rules |
| `src/main/resources/log4j2.xml` | Repository and Mule XML rules |
| RAML / `src/main/resources/api/` definition or fragment | Repository and API contract rules; explicitly open guidance for other OAS locations |
| Resource `.yaml` / `.properties` loaded by Mule | Repository and configuration-property rules; MUnit also matches test resources |
| Skill invocation and linked files | Selected skill, profile and relevant scoped guidance opened |
| Unapproved upstream skill (negative) | Not selected for a DataWeave change |

Record file paths, client settings, references/read traces/diagnostics, and whether context was automatic or manually attached. Record inaccessible files and conflicts. A self-reported claim that files were read is not sufficient evidence. Summarize the outcome for each client on the profile's **Loading check** line.

## After the pilot

Record recurring mistakes, actual build and test counts, remaining blockers, and narrowly justified rule changes. Propose rule changes to the MuleSkills repository rather than editing a project's copy.
