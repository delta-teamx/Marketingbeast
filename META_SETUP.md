# Connecting Meta (Facebook + Instagram) — step-by-step

This is the practical guide to take Presence from **mock** Facebook/Instagram to
**live**. You create **one** Meta app; your customers never give you a key — they
click "Connect Facebook" and authorize *your* app via OAuth.

> ⏱ The long pole is **App Review** (1–4 weeks). Start it first; do everything
> else in parallel. Until review is approved you can still test with your own
> Page in *development mode* (see §7).

---

## What you need before you start
- A **Facebook account** that is an admin of your Facebook **Page**.
- Your Instagram account converted to a **Business/Creator** account and **linked
  to that Facebook Page** (Instagram → Settings → Account → linked Page).
- Your business details (legal name, address, website) for **Business
  Verification**.
- Your live URLs:
  - Web app: `https://presence-marketing-app.netlify.app` (your Netlify site)
  - API: your Render URL, e.g. `https://presence-api.onrender.com`

---

## 1. Create the Meta app
1. Go to <https://developers.facebook.com/apps> → **Create App**.
2. Choose app type **Business**.
3. Name it (e.g. "Presence"), pick your **Business Portfolio** (create one if
   prompted).
4. After it's created, open **App settings → Basic** and copy:
   - **App ID** → this becomes `META_APP_ID`
   - **App Secret** (click *Show*) → this becomes `META_APP_SECRET`
5. On the same page set:
   - **App Domains:** `presence-marketing-app.netlify.app` and your Render domain
   - **Privacy Policy URL:** `https://presence-marketing-app.netlify.app/privacy`
   - **Terms of Service URL:** `https://presence-marketing-app.netlify.app/terms`
   - **User data deletion:** `https://presence-marketing-app.netlify.app/data-deletion`

   (These three pages already exist in the app.)

---

## 2. Add the products
In the app's left nav → **Add product**, add:
- **Facebook Login** (for OAuth)
- **Instagram Graph API** (publishing + insights)
- **Messenger** (the inbox — optional for v1; needed for DM features)
- **Marketing API** (ads — optional, only if you launch the Ads Manager feature)

### Configure Facebook Login → Settings
- **Valid OAuth Redirect URIs** — add exactly:
  ```
  https://<your-render-domain>/api/integrations/meta/oauth/callback
  ```
  e.g. `https://presence-api.onrender.com/api/integrations/meta/oauth/callback`
- **Client OAuth Login:** ON · **Web OAuth Login:** ON.

> This redirect URI **must match** `META_REDIRECT_URI` exactly (below) or login
> fails with "URL blocked".

---

## 3. Business Verification
**App settings → Business verification** (or Business Portfolio → Security
Center). Submit your legal business documents. Advanced access to the
permissions below is only granted after this passes.

---

## 4. The permissions (scopes) to request
Presence requests these (already coded in `apps/api/app/services/meta/live.py`):

**Pages:** `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`,
`pages_manage_metadata`
**Instagram:** `instagram_basic`, `instagram_content_publish`
**Business:** `business_management`

For the **inbox** (later) add: `pages_messaging`, `instagram_manage_comments`,
`instagram_manage_messages`, `pages_read_user_content`.
For **ads** (later) add: `ads_management`, `ads_read`.

---

## 5. App Review
**App Review → Permissions and Features.** For each non-default permission click
**Request advanced access** and provide:
- A **screencast** showing the feature using that permission (e.g. connecting a
  Page and publishing a post).
- A written **use-case** description.
- The published **privacy policy URL** and **data-deletion** method (from §1).

Submit and wait. This is the 1–4 week step.

---

## 6. Flip Presence to live
Once you have the App ID/Secret (you can do this before review approval to test
in development mode), set these on Render — in the **`presence-shared`** env-var
group (so the web service *and* the worker/beat all get them):

```
META_MODE=live
META_APP_ID=<your app id>
META_APP_SECRET=<your app secret>
META_REDIRECT_URI=https://<your-render-domain>/api/integrations/meta/oauth/callback
META_GRAPH_VERSION=v21.0
WEB_APP_URL=https://presence-marketing-app.netlify.app
```

No code change is needed — the live adapter is already implemented. Save; Render
redeploys.

---

## 7. Test before launch (works during development mode too)
1. In the Meta app → **App roles → Roles**, add yourself/testers. In development
   mode only people with a role can authorize — perfect for a pre-review test.
2. In Presence: open a brand → **Connect Facebook & Instagram** → authorize with
   your test account → you should land back on the dashboard with your Page +
   IG account connected.
3. Compose a post → **Publish now** → confirm it appears on your real Page.
4. Run **Analytics → Sync** and **Inbox → Sync** to confirm insights/DMs pull.
5. When App Review is approved, switch the app to **Live** (top toggle) and any
   customer can connect their own Page.

---

## Quick reference — env vars
| Var | Where it comes from |
|-----|---------------------|
| `META_APP_ID` | App settings → Basic → App ID |
| `META_APP_SECRET` | App settings → Basic → App Secret |
| `META_REDIRECT_URI` | `https://<render-domain>/api/integrations/meta/oauth/callback` (must also be whitelisted in Facebook Login settings) |
| `META_MODE` | `live` |
| `META_GRAPH_VERSION` | `v21.0` |
| `WEB_APP_URL` | your Netlify site URL |

If OAuth fails: 99% of the time it's a **redirect URI mismatch** — the value in
Facebook Login → Valid OAuth Redirect URIs must be byte-for-byte equal to
`META_REDIRECT_URI`.
