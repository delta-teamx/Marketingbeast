import { LegalH2, LegalPage } from "@/components/legal-page";

export const metadata = { title: "Privacy Policy — Presence" };

export default function PrivacyPage() {
  return (
    <LegalPage title="Privacy Policy" updated="June 2026">
      <p>
        Presence (“we”, “us”) helps businesses and agencies manage their Facebook
        and Instagram presence. This policy explains what we collect, how we use
        it, and your choices. It is written to meet Meta Platform requirements.
      </p>

      <LegalH2>What we collect</LegalH2>
      <p>
        Account details you provide (name, email), your business and brand
        information, and — when you connect Facebook or Instagram — access tokens
        and the content/metrics those official APIs return (posts, comments, DMs,
        insights, ad performance). We never receive or store your Facebook
        password.
      </p>

      <LegalH2>How we use it</LegalH2>
      <p>
        To provide the service: audit your presence, generate and publish content,
        run and report on ads, manage your inbox, and surface analytics. AI
        features process your content to produce drafts and recommendations.
      </p>

      <LegalH2>Meta data &amp; tokens</LegalH2>
      <p>
        Connections use Meta’s official OAuth. Access tokens are encrypted at rest
        and used only to perform actions you request on accounts you connect. We do
        not sell your data or use it to train third-party models.
      </p>

      <LegalH2>Data retention &amp; deletion</LegalH2>
      <p>
        You can disconnect any account at any time, which revokes and deletes its
        tokens. You may request deletion of your account and associated data — see
        our <a className="underline" href="/data-deletion">Data Deletion</a> page.
      </p>

      <LegalH2>Contact</LegalH2>
      <p>Questions? Email privacy@presence.app.</p>
    </LegalPage>
  );
}
