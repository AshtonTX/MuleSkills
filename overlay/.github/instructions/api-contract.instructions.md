---
applyTo: "**/*.raml,**/src/main/resources/api/**"
description: "API specification and APIkit rules: authentication enforcement, request validation and contract-to-flow routing."
---

# API contract changes

Apply these rules to API definitions and fragments, not example payloads. Read the root RAML/OAS definition, referenced assets and the project's pinned APIkit version first. For specifications outside the matched paths, open this guidance explicitly through [the team workflow](../skills/team-mule-guardrails/SKILL.md).

- For APIs served by APIkit, a security declaration in RAML/OAS does not enforce authentication. Identify the existing gateway policy or application security that enforces the requirement; a specification declaration or a direct implementation-flow test is not evidence that access is restricted. See [APIkit scaffolding and router validation](https://docs.mulesoft.com/apikit/latest/apikit-4-scaffolding-reference).
- Preserve the configured request-validation behavior. Do not disable validation to fix a rejected request or reduce latency, or tighten accepted inputs, without an explicit contract decision and tests. APIkit exposes validation controls whose spelling and placement must match the pinned module. See [APIkit XML reference](https://docs.mulesoft.com/apikit/latest/apikit-4-xml-reference).
- When changing a resource, method, request media type or APIkit configuration name, check its generated flow name or explicit `apikit:flow-mapping`. Keep routing connected to the intended implementation; a contract edit alone does not create that implementation. See [resource/action mapping](https://docs.mulesoft.com/apikit/latest/apikit-workflow-convert-existing) and the XML reference above. Preserve the [Mule XML error/response contract](mule-xml.instructions.md) and cover the change with [meaningful tests](munit.instructions.md).
