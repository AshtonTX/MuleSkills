---
paths: "**/src/main/resources/**/*.yaml,**/src/main/resources/**/*.properties,**/src/test/resources/**/*.yaml,**/src/test/resources/**/*.properties"
description: "Rules for Mule configuration and secure property files: value types, precedence, environment selection and encryption."
---

# Mule configuration properties

Apply these rules only to files loaded as Mule configuration or secure configuration properties, not API definitions, payload fixtures or unrelated YAML. Read the provider declarations, consumers and environment-selection evidence in [the profile](../../.github/mule/team-profile.md); keep project facts there, not in these rules.

- Trace each changed key to its provider and consumers. Mule configuration files support String values; quote YAML numbers and booleans used as configuration values. See [supported property files](https://docs.mulesoft.com/mule-runtime/4.9/configuring-properties#supported_files).
- Do not assume a later file overrides an earlier one: across files loaded by `configuration-properties`, the first definition is preserved. Deployment properties override system properties, then environment properties, application properties and global properties. Check the effective source before changing a bundled value. See [property loading and hierarchy](https://docs.mulesoft.com/mule-runtime/4.9/configuring-properties).
- A selector such as `${env}` in a properties filename cannot come from another application properties file. Use the project's existing global, system, environment or deployment source. References within one file are allowed; a dependency on another application property provider, including a secure provider, is not equivalent. See [dynamic property files](https://docs.mulesoft.com/mule-runtime/4.9/configuring-properties#setting-the-properties-file-dynamically).
- For secure files, preserve the encryption format and keep the runtime key out of the repository. Consumers use `secure::` even for unencrypted values loaded by the secure provider. Its required `secure-properties:encrypt` child and key, algorithm, mode and `useRandomIVs` must match the encryption settings; do not change those settings while retaining incompatible ciphertext. See [Secure Configuration Properties](https://docs.mulesoft.com/mule-runtime/4.9/secure-configuration-properties). Keep [Mule XML secret/TLS rules](mule-xml.md) when editing the loader.
