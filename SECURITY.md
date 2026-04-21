# Security policy

## Reporting a vulnerability

Email **security@qortara.com** with the details of the issue. Please **do not** file public GitHub issues, pull requests, or discussion posts for security reports.

A useful report includes:

- Affected version(s) of `qortara-governance-langchain`
- Reproduction steps or a proof-of-concept
- Your assessment of impact (e.g., patch bypass, policy evasion, information disclosure, denial of service)
- Whether the finding has been disclosed elsewhere

We aim to acknowledge receipt within **5 business days** and to provide an initial assessment within **15 business days**. If the issue is confirmed, we will agree on a coordinated disclosure timeline — typically 60 to 90 days, adjusted for severity and mitigation complexity. Credit is offered in advisory text at the reporter's discretion.

If you do not receive an acknowledgement within 5 business days, please follow up on the same thread.

## Scope

In scope:

- The `qortara-governance-langchain` SDK (this repository): patch correctness, circuit-breaker behavior, error-handling, dependency vulnerabilities, information disclosure through exception content or logs.
- The sidecar wire protocol *as consumed by this SDK*: request construction, response handling, authentication header handling.

Out of scope for this repository's advisory process:

- Vulnerabilities in LangChain, LangGraph, or other upstream dependencies — report those upstream. We'll track and pin as needed once an upstream advisory lands.
- Issues in applications built *using* this SDK that do not involve the SDK itself.
- Social-engineering, physical access, or third-party service outage scenarios.

Findings in the hosted decision plane should be reported to the same address; routing inside MythologIQ Labs is handled on our end.

## Supported versions

During the `0.x` series, only the latest `0.x` release receives security fixes. Once a `1.0` release ships, the supported-version window will be documented here.

## Safe-harbor

Good-faith security research conducted under this policy will not result in legal action from MythologIQ Labs, LLC. "Good faith" means: avoid privacy violations and service degradation, only interact with accounts you own or have explicit permission to test, and give us reasonable time to remediate before any public disclosure.
