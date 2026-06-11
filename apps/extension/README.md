# Presence — Group Assistant (Tier B)

A Manifest V3 browser extension that helps you post to Facebook **groups you
belong to**, paced to look human. This is the **Tier B** layer from the product
brief: it runs **in your own browser, on your own session**, and is **assisted +
confirmed** — you review and click Post for every item. Nothing is posted
silently, and **our servers never post to groups**.

## Safety model (brief §9 — enforced in code, not optional)

Hard limits live in `src/config.ts` and **cannot be turned off by the user**:

- Randomized, jittered delays between posts (never a fixed interval).
- A daily cap with a slow **warm-up ramp** for new/quiet accounts.
- Posting only within the active hours you set (span is clamped).
- Blocks near-identical copy-paste content across groups.
- **Assisted/confirmed**: the extension opens the group and hands you the post;
  you paste and click Post.

We deliberately do **not** build proxy rotation, fingerprint spoofing, or any
ban-evasion. A consent screen (`consent.html`) names the account-ban risk in
plain language, and we never ask for or store your Facebook password.

The pacing logic is pure and unit-tested in `src/guardrails.ts` /
`tests/guardrails.test.ts`.

## How it connects

The extension only talks to the Presence backend's **queue** endpoints
(`/api/automation/group-queue`) using an access token you paste from the web app.
It fetches queued posts, claims one, opens the matching group, and — after you
confirm — reports the post as done. The backend is just a store.

## Develop

```bash
pnpm --filter @presence/extension test       # guardrail unit tests
pnpm --filter @presence/extension typecheck
pnpm --filter @presence/extension build       # outputs dist/
```

Then load `apps/extension/dist` via `chrome://extensions` → Developer mode →
**Load unpacked**.
