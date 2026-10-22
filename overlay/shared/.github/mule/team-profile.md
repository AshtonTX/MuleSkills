# Team profile

Facts about this project. Use them when choosing versions, syntax, tests and deployment settings. `Unknown` means find the evidence in the project or ask; never guess a value or use "latest". Keep credentials, sensitive payloads, private endpoints and access grants out of this file.

To fill in or update this file, follow [the guide](team-profile-guide.md). Other tasks don't need the guide.

## Team

- **AI assistant clients:** GitHub Copilot CLI, the GitHub Copilot desktop app and Claude Code; each developer's versions and models unknown
- **Deployment/control plane:** Government Cloud present; Government Cloud or Government Cloud Plus unknown; exact target (CloudHub 1.0 or hybrid standalone) unknown
- **FIPS 140-3 mode required:** Unknown
- **Messaging, logging and API management:** Unknown
- **Shared assets:** Unknown
- **Connector approval:** Unknown
- **Architecture conventions:** Unknown
- **Approved data and external access:** Unknown
- **Upstream MuleSoft skill:** None selected or enabled by these guardrails
- **Loading check:** Not run

## Project

- **Repository, module, commit:** Unknown
- **Mule runtime patch and release channel:** Unknown
- **`minMuleVersion`:** Unknown
- **DataWeave engine and effective language level:** Unknown
- **Runtime JVM:** Unknown
- **Maven version and Maven's actual JVM:** Unknown
- **MUnit version, runtime and JVM:** Unknown
- **Compiled Java bytecode target:** Unknown
- **Mule Maven Plugin version/execution:** Unknown
- **MUnit runner, tools and Maven plugin versions:** Unknown
- **Connector and JDBC driver coordinates:** Unknown
- **Unresolved parent/property versions:** Unknown
- **Runtime topology:** Unknown
- **API/error contract and shared conventions:** Unknown; follow reviewed existing code
- **Configuration property resolution:** Unknown
- **Null/empty/type/precision/date/ordering rules:** Per operation; unknown until contract supplied
- **Targeted and aggregate local checks:** Unknown
- **Reviewed local examples:** Not supplied

## Government Cloud limits

As of October 2026 (recheck before planning), MuleSoft lists CloudHub 2.0, Runtime Fabric, Anypoint Security (including tokenization), Anypoint Code Builder, Omni Gateway, API Governance, Anypoint Analytics and API Data Gateway as unavailable in Government Cloud. Government Cloud and Government Cloud Plus are distinct platforms with different authorization boundaries. In Government Cloud, Anypoint MQ requires encrypted queues, connected apps and connector 4.x, and has no cross-region failover. Mule does not run in FIPS mode by default.
