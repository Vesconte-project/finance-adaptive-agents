---
name: mcp-api-capability-triage
description: Diagnose a task where an MCP connects but lacks the needed account operation, or a service API call fails ambiguously. Choose between an exposed MCP tool, official CLI, and documented API without confusing connectivity, capability, credentials, or authorization.
---

# Choose the actual service access path

An MCP connection proves that a server answered the client, not that it can read or
change the resource the task needs. A configured credential proves neither access
nor permission for a particular operation.

## Resolve the operation before choosing a tool

1. Name the exact resource, instance or environment, and read or write operation.
   Inspect the live MCP tool inventory and schemas. A documentation or SDK-snippet
   tool is not an account-data tool. Capabilities can change; do not rely on a
   remembered list.
2. Prefer an exposed service MCP operation when it covers the task. Otherwise check
   the provider's current CLI and official API documentation for that operation.
   Use the same user-granted scope; a different transport does not widen authority.
   Do not fabricate an endpoint, infer that a secret grants dashboard access, or
   reuse a Development credential against Production.
3. Keep credentials outside repositories. Pass a secret through a protected process
   environment or supported secure input, not a command-line argument or pasted
   tool output. For a read, return only the fields needed to answer the question.
   For a write, inspect the target first and read it back afterward.

## Separate the failure layers

- **Tool absent:** the MCP server does not expose this operation; use an authorized
  documented path or report the capability gap.
- **Network/DNS/TLS failure:** the request has not reached the provider. A sandbox
  failure cannot establish that the key or API is invalid. Retry with approved
  network access only when the task authorizes that path.
- **HTTP 401/403:** check credential, instance, scope, and provider permissions;
  do not automatically rotate or broaden access.
- **HTTP success with wrong data:** confirm instance/environment and resource IDs.
  A valid Development response does not describe Production.
- **Write accepted but effect unclear:** inspect the exact resource and dependent
  deployment/runtime state. Report an unverified result if readback is unavailable.

In one observed September 2026 Clerk setup, the official Clerk MCP exposed only
documentation and SDK snippets, while the official CLI's `api` command reached the
Backend API with a Development secret. This is an example of a capability boundary,
not a permanent claim about Clerk MCP or proof of Production access. Reinspect the
available tools and keys in the target workspace.

This Skill does not authorize credential changes, external writes, or production
operations. Apply the target repository's rules and the user's granted scope.
