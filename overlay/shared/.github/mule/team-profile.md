# Team profile: fill from project evidence

This template records facts, not proposed version upgrades. Government Cloud is confirmed for our team; other unknowns need evidence before a pilot. Use approved names/references only; never put credentials, sensitive payloads, private endpoints, or access grants here.

| Fact | Current value | Evidence to record |
|---|---|---|
| Copilot product/version, mode, model/account | Unknown; desktop workflow confirmed | Client About/settings and organization approval |
| Repository, module, commit | Unknown | Working checkout and module POM |
| Mule runtime patch and release channel | Unknown | Deployment configuration, CI and resolved POM |
| `minMuleVersion` | Unknown | `mule-artifact.json`; distinguish declared minimum from deployed runtime |
| DataWeave engine and effective language level | Unknown | Runtime mapping and `minMuleVersion`; `%dw 2.0` is not an engine pin |
| Runtime JVM | Unknown | Approved runtime and Java compatibility evidence |
| Maven version and Maven's actual JVM | Unknown | Approved wrapper/CI configuration and `mvn -version` when permitted |
| MUnit version, runtime and JVM | Unknown | Plugin configuration (`munit.runtimeversion` in MUnit 3.7 docs; `runtimeVersion` is the deprecated alias), toolchain and actual execution output. 3.6 versus 3.7 changes assertion-error handling and supported Maven range |
| Compiled Java bytecode target | Unknown | Compiler configuration and effective properties |
| Mule Maven Plugin version/execution | Unknown | Resolved plugin version, binding and profile effects |
| MUnit runner, tools and Maven plugin versions | Unknown | Exact coordinates and resolved effective POM |
| Connector and JDBC driver coordinates | Unknown | Group/artifact/version/classifier; inherited resolution and compatibility. If a driver was added through Studio's Required Libraries instead of a declared dependency, record the exact jar and where it is configured |
| Unresolved parent/property versions | Unknown | Name missing evidence; do not infer a value |
| Deployment/control plane | Government Cloud present; Government Cloud or Government Cloud Plus unknown; exact target (CloudHub 1.0 or hybrid standalone) unknown | Approved platform/team evidence, region and feature support. MuleSoft describes the two as distinct platforms with different authorization boundaries. As of October 2026 MuleSoft lists CloudHub 2.0, Runtime Fabric, Anypoint Security (including tokenization), Anypoint Code Builder, Omni Gateway, API Governance, Anypoint Analytics and API Data Gateway as unavailable in Government Cloud; recheck before planning. Record whether FIPS 140-3 mode is required (Mule does not run in FIPS mode by default) |
| Runtime topology | Unknown | CloudHub 1.0: worker count and size (two or more workers for high availability), VPC and dedicated load balancer use (private ports 8091/8092), Persistent Queues, Object Store v2. Standalone: cluster or server group, Mule domain projects, how organization credentials and properties are supplied |
| Messaging, logging and API management | Unknown | Anypoint MQ, JMS broker or VM only (in Government Cloud, Anypoint MQ requires encrypted queues, connected apps and connector 4.x, and has no cross-region failover); log destination (CloudHub logs or forwarded through `log4j2.xml`) and logger used; API Manager instances and per-environment autodiscovery IDs |
| Shared assets | Unknown | Exchange templates, fragments and libraries the team reuses (for example a common error handler or logging framework); use these instead of writing new ones |
| Connector approval | Unknown | Connectors approved for use and their support category (Select, Premium, Certified partner-supported, or unsupported community); adding a connector needs approval |
| Architecture conventions | Unknown | Whether API-led layers (system/process/experience) are used and how projects are named per layer (for example `-sapi`, `-papi`, `-eapi` suffixes); health-check endpoint convention; file layout (for example a common flows file and per-resource folders under `src/main/resources`); where shared configuration and the default error handler live; per-environment property file pattern; error response shape and code list |
| API/error contract and shared conventions | Unknown; follow reviewed existing code | Root RAML/OAS path and version, referenced fragments/assets, pinned APIkit coordinates, parser/validation settings, authentication enforcement reference, tests, flow boundaries, naming and redacted logging |
| Configuration property resolution | Unknown | Provider files and loading order, environment-selector source, deployment override names, secure-properties module and encryption-setting references; never record secret values or encryption keys |
| Null/empty/type/precision/date/ordering rules | Per operation; unknown until contract supplied | Contract plus positive and negative fixtures |
| Targeted and aggregate local checks | Unknown | Reviewed README/CI commands, selected counts, plugin side effects |
| Approved data and external access | Unknown | Allowed code/API-spec/metadata classes, public searches/docs, tools, model/service and network rules; GitHub enterprise policies or managed settings that restrict MCP servers and plugins |
| Reviewed local examples | Not supplied | Paths to one transform, flow/error handler and MUnit suite |
| Upstream skill, revision and decision owner | None selected or enabled | Reviewed file/SHA, license, scripts and tool prerequisites; skills already present in project/personal skill folders or the client's skills list |

## Upstream exceptions: complete before enabling

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

Current decision: **not selected; no upstream workflow enabled by these guardrails**. Do not silently treat the proposed exceptions above as organizational approval.

## Activation evidence: complete on the actual client

| Probe | Expected candidate context | Observed evidence / outcome |
|---|---|---|
| Main Mule XML | Repository, Mule XML and embedded DataWeave rules | Not run |
| `.dwl` | Repository and DataWeave rules | Not run |
| MUnit XML with expressions | Repository, MUnit and DataWeave rules | Not run |
| POM / artifact descriptor / `.mvn/` / GitHub Actions workflow | Repository and Maven rules | Not run |
| `src/main/resources/log4j2.xml` | Repository and Mule XML rules | Not run |
| RAML / `src/main/resources/api/` definition or fragment | Repository and API contract rules; explicitly open guidance for other OAS locations | Not run |
| Resource `.yaml` / `.properties` loaded by Mule | Repository and configuration-property rules; MUnit also matches test resources | Not run |
| Skill invocation and linked files | Selected skill, profile and relevant scoped guidance opened | Not run |
| Unapproved upstream skill (negative) | Not selected for a DataWeave change | Not run |

Record file paths, client settings, references/read traces/diagnostics, and whether context was automatic or manually attached. Record inaccessible files and conflicts. A self-reported claim that files were read is not sufficient evidence.

## After the pilot

Record recurring mistakes, actual build and test counts, remaining blockers, and narrowly justified rule changes. Propose rule changes to the MuleSkills repository rather than editing a project's copy.
