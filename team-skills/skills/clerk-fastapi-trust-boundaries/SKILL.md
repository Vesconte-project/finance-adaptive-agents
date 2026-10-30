---
name: clerk-fastapi-trust-boundaries
description: Use when designing or reviewing user authentication across Clerk, Next.js BFF, FastAPI, Cloudflare, and Vercel previews; distinguish user identity, service identity, resource authorization, and origin protection.
---

# Identity at the API trust boundary

**Scope:** authentication and admission of frontend-originated requests to a Python/FastAPI backend, especially with Clerk, Vercel and Cloudflare. This is architecture guidance, **not evidence that a target deployment already implements it**. Installing keys or repairing a sign-in form on one deployment is outside this architectural scope: that diagnosis needs the affected deployment's effective environment, configured authentication routes, and browser evidence. These architecture checks alone do not establish why a particular form failed.

## Non-interchangeable proofs

- **User:** FastAPI authenticates a Clerk session token cryptographically (or a deliberately specified delegation assertion). Use the official Python SDK where compatible; pin token type, issuer/instance, signature, expiry, audience if applicable, authorized party (`azp`) policy, and expected environment. Resolve an internal principal from `(issuer, subject)`; never grant rights based on client-supplied `user_id`.
- **Calling service:** Vercel OIDC, Cloudflare Access service authentication, or another explicit service credential may establish workload identity. It does **not** prove the end user's identity or ownership of an object. Restrict service identity by environment and permissions; Preview identity must not authorize Production.
- **Origin:** Tunnel establishes transport, **not** an Access policy or app authorization. Verify ingress, origin listeners/firewalls (including IPv6), hostnames, route policies, bypasses and origin certificate verification. Do not trust client-injectable headers claiming upstream identity.
- **Authorization:** FastAPI enforces tenant/account/owner, operation, entitlements and quotas at the resource boundary even if the BFF already hid a UI element or checked a plan.

## How to decide direct vs BFF

Direct browser -> Cloudflare -> FastAPI with an HTTP bearer authorization header carrying the Clerk session token is an appropriate target when an HTTPS API reachable by browsers is acceptable. Implement explicit CORS origins and rate limiting; CORS does not authenticate callers. A BFF can remain for same-origin cookies, response shaping, restricted service ingress, or special streaming behavior, but should forward verifiable user identity rather than `user_id` plus a universal shared secret.

Do not use Access human login as a drop-in replacement for Clerk on browser-facing APIs; test `OPTIONS` preflight and authentication. For cookie-authenticated BFF mutations, test CSRF; for bearer APIs, test XSS/token exposure and CORS. SSE with native `EventSource` has different header capabilities from authenticated `fetch` streaming.

## BFF-asserted visitor IP behind Cloudflare Access

When a BFF forwards the end visitor's IP (for rate limiting or abuse controls) and the
backend accepts it only together with a valid Cloudflare Access JWT, the acceptance path
usually **falls back silently** to the connection address on any failure. Behind a
serverless BFF that address is the platform's egress IP, so every anonymous visitor
shares one bucket and the public site degrades into `429` responses without any
authentication error being logged.

- Compare the Access JWT `iss` exactly with the configured issuer. A trailing slash
  (`https://<team>.cloudflareaccess.com/` versus `https://<team>.cloudflareaccess.com`)
  is enough to reject every assertion. Normalize or validate the configured value at
  the point where configuration is rendered, not only in the verifier.
- Provision the Access signing keys from the team's fixed certificate endpoint and
  refresh them outside the request path. Cloudflare rotates them periodically with an
  overlap window; a static JWKS eventually rejects every assertion.
- Check the audience against the specific Access application's AUD tag.
- Count rejection reasons in aggregate (missing headers, format, timestamp, HMAC, JWT
  issuer/audience/kid), without values, so the failing stage is visible.
- In functional proofs, use the IP family the browser actually uses. If the public site
  has only an A record, a visitor's IPv6 address from a "what is my IP" page will never
  match the proof the BFF sends. Mobile carrier-grade NAT may also present a different
  public IPv4 per connection; prefer a second fixed network for two-visitor proofs.

## Verification and stop conditions

1. Trace one request end-to-end, collecting sanitized routing, token type, instance ID, service identity, and final authorization decision; never record bearer tokens.
2. Test wrong issuer, wrong Preview/Production environment, expired token, forged `user_id`, wrong account, wrong `azp`, stale membership, and direct origin/hostname bypass.
3. Test key rotation/JWKS cache and clearly document revocation latency; local JWT verification alone cannot establish immediate session revocation.
4. If issuer, token acceptance, Cloudflare Access policy or firewall status cannot be confirmed, mark it **unknown** and do not assert the origin or resource is protected.
5. Do not change credentials, Access policies, deployments or production admission without explicit environment-owner approval.

## Sources to re-check when SDK/provider changes

- Clerk cross-origin requests: https://clerk.com/docs/guides/development/making-requests
- Clerk session claims: https://clerk.com/docs/guides/sessions/session-tokens
- Clerk backend authentication: https://clerk.com/docs/reference/backend/authenticate-request
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- JWT best practices: https://www.rfc-editor.org/rfc/rfc8725

Provider references last reviewed 2026-10-10.
