---
name: clerk-vercel-auth-environments
description: Diagnose Clerk sign-in or sign-up missing or broken on a Vercel deployment by tracing instance keys, environment targets, redeploys, and browser behavior. Use for existing authentication failures on Vercel Preview or Production deployments, comparing local behavior when relevant; not for unrelated build failures or general authentication implementation.
---

# Clerk authentication across Vercel environments

The decisive question is which Clerk instance the **specific deployment** received.
Do not infer it from a successful Vercel build, a key stored elsewhere in the project,
or a screenshot of an earlier deployment.

## Trace the affected deployment

1. Identify the project, deployment ID, commit, branch, target environment, and URL.
   Check whether Vercel Deployment Protection is returning its own login page.
2. Inspect environment-variable **metadata** for that project and target, including
   branch-specific Preview entries. Do not decrypt values just to check existence.
   `Development` is the local development target; a PR deployment needs `Preview`.
3. Identify the framework, installed Clerk SDK, and how it receives configuration.
   For Next.js, check `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY`;
   Vite-based clients commonly use `VITE_CLERK_PUBLISHABLE_KEY`. Other SDKs or
   explicit provider props may differ. Confirm that the effective public and
   server keys, where a server key is used, belong to the same Clerk instance.
   Matching prefixes establish environment type, not instance identity; use
   approved instance metadata without displaying secret values.
   The public key prefixes are `pk_test_` and `pk_live_`;
   the corresponding server-only prefixes are `sk_test_` and `sk_live_`. Preserve
   the publishable key exactly, including any base64 padding. Never expose the
   secret key in client code, logs, command arguments, or a Skill.
4. Match keys to the domain. For ordinary `*.vercel.app` Preview deployments, use
   a Clerk Development instance. Production uses its Production instance and
   configured custom domain. If a team uses a custom Preview domain or separate
   staging application, inspect that setup rather than applying the ordinary case.

## Repair and verify

When authorized to change Vercel configuration, use the narrowest appropriate
environment and optional branch scope. Keep the secret as a secret, and keep the
publishable key public. Read the metadata back. Changing variables affects **new**
deployments; rebuild or redeploy the affected Preview and identify the new deployment.
Branch-specific variables will not cover future PR branches; choose project-wide
Preview scope only when that is the intended policy. Avoid production changes as a
side effect of a Preview repair.

Check the served HTML or runtime configuration for the *public key prefix* only.
That identifies the environment type of an exposed key, not the complete instance
identity or whether Clerk loaded in the browser. Resolve the application’s actual
authentication routes from its router, SDK configuration, and provider props.
`/sign-up` and `/sign-in` are examples, not required paths; hosted redirects or
embedded forms may apply instead. Open the configured flow in a browser, wait
for the actual Clerk form, and check console/network errors. Complete any
authentication flow only within the task’s authorized test account and scope. If the
Preview is protected, distinguish Vercel's login page from the app's Clerk page.
Report separately: deployment readiness, effective key, rendered form, and any
completed authentication flow. A green deployment is not functional evidence.

## Automatic Frontend API proxy (`/__clerk`) on Vercel

Some Clerk Next.js SDK versions enable a Frontend API proxy automatically during a
Vercel Production build, deriving it from Vercel system variables (for example when
the project's production URL is a `*.vercel.app` domain). The served page then
announces a proxy path such as `/__clerk`, but the application only serves it if its
middleware explicitly enables the proxy and its matcher covers that path.

Recognizable signals, without reading any secret:

- the served HTML contains `proxyUrl` with `/__clerk`, and `clerk-js` is loaded from
  `/<site>/__clerk/npm/...`;
- `/__clerk/npm/@clerk/clerk-js@…/dist/clerk.browser.js` and `/__clerk/v1/client`
  return 404 from the site, while the instance's own Frontend API host (the custom
  `clerk.<domain>` CNAME) answers `/v1/environment` with 200;
- a browser with an older Clerk cookie is redirected to
  `/__clerk/v1/client/handshake?...` and gets 404; a fresh private window renders the
  page but sign-in cannot load.

Decide explicitly: either serve the proxy deliberately (middleware option plus matcher
plus any CSP changes), or disable automatic proxying and use the instance's Frontend API
host directly. With a working Frontend API CNAME, disabling is the simpler fix: set the
SDK's documented opt-out (for example `CLERK_DISABLE_AUTO_PROXY=true`) in the affected
target, confirm no explicit proxy variables exist, and **rebuild without the build
cache**, because the proxy URL is baked into already generated HTML. If the project uses
manual promotion, promote the new deployment. Verify that the HTML no longer contains
the proxy path and that `clerk-js` loads from the Frontend API host. Check every Next.js
project that shares the SDK behavior before opening it on a custom domain.

Observed in October 2026 with `@clerk/nextjs` 7.5.x and 7.9.x on Vercel; confirm the
detection rules and the opt-out name in the installed SDK version.

The “Secured by Clerk” badge is controlled by Clerk's plan and dashboard setting.
Check the current plan and official docs before promising removal; appearance CSS
is not the source of that setting.

This Skill does not grant permission to alter credentials, billing, production,
or release state. Follow the target repository's authority and deployment rules.

## Evidence to refresh at use time

The key pairing and ordinary Preview approach are documented by
[Clerk environment variables](https://clerk.com/docs/guides/development/clerk-environment-variables),
[Clerk environments](https://clerk.com/docs/guides/development/managing-environments),
and [Clerk on Vercel](https://clerk.com/docs/guides/development/deployment/vercel).
The distinction among Vercel targets, branch-specific Preview variables, and
new-deployment application is documented by
[Vercel environment variables](https://vercel.com/docs/environment-variables).
Framework-specific key and route configuration was rechecked on 19 October 2026;
the earlier provider review was in September 2026. Verify relevant behavior again if
the installed SDK, CLI, integration, or provider settings have changed.
