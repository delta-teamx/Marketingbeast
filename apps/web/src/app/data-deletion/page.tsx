import { LegalH2, LegalPage } from "@/components/legal-page";

export const metadata = { title: "Data Deletion — Presence" };

export default function DataDeletionPage() {
  return (
    <LegalPage title="Data Deletion" updated="June 2026">
      <p>
        You can delete your data from Presence at any time. This page describes how,
        and serves as our data-deletion instructions for Meta Platform compliance.
      </p>

      <LegalH2>Disconnect an account</LegalH2>
      <p>
        In your dashboard, disconnect any Facebook Page or Instagram account. This
        immediately revokes and deletes the stored access token and stops all
        activity for that account.
      </p>

      <LegalH2>Delete your account</LegalH2>
      <p>
        To delete your entire account and all associated data (brands, content,
        analytics, conversations, tokens), email{" "}
        <a className="underline" href="mailto:privacy@presence.app">privacy@presence.app</a>{" "}
        from your account email with the subject “Delete my data”. We process
        deletion within 30 days and confirm by email.
      </p>

      <LegalH2>What is deleted</LegalH2>
      <p>
        All personal data, Meta access tokens, connected-account data we cached
        (posts, comments, DMs, insights), and AI-generated assets tied to your
        account. Aggregated, anonymized statistics that cannot identify you may be
        retained.
      </p>
    </LegalPage>
  );
}
