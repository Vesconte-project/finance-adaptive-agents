---
name: clerk-vercel-auth-environments
description: Diagnose Clerk sign-in or sign-up missing or broken on a Vercel deployment by tracing instance keys, environment targets, redeploys, and browser behavior. Use for Clerk authentication across local, Preview, and Production; not for unrelated Vercel build failures.
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
3. Confirm that `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` belong to
   the same Clerk instance. The public key prefixes are `pk_test_` and `pk_live_`;
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
That proves the build received a key, but does not prove Clerk loaded in the browser.
Open `/sign-up` and `/sign-in` in a browser, wait for the actual Clerk form, and
check console/network errors and the sign-in path appropriate to the task. If the
Preview is protected, distinguish Vercel's login page from the app's Clerk page.
Report separately: deployment readiness, effective key, rendered form, and any
completed authentication flow. A green deployment is not functional evidence.

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
These provider behaviors were checked in September 2026; verify them again if
the installed SDK, CLI, integration, or provider settings have changed.
