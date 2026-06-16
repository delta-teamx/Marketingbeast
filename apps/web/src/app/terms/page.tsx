import { LegalH2, LegalPage } from "@/components/legal-page";

export const metadata = { title: "Terms of Service — Presence" };

export default function TermsPage() {
  return (
    <LegalPage title="Terms of Service" updated="June 2026">
      <p>
        By using Presence you agree to these terms. If you use Presence on behalf
        of an organization, you agree on its behalf.
      </p>

      <LegalH2>The service</LegalH2>
      <p>
        Presence helps you audit, create, schedule, publish, advertise, and report
        on social content via Meta’s official APIs. Features depend on the accounts
        you connect and the plan you choose.
      </p>

      <LegalH2>Your responsibilities</LegalH2>
      <p>
        You’re responsible for the accounts you connect, the content you publish,
        and complying with Meta’s terms and applicable law. You must own or have
        permission to manage any account or brand you add.
      </p>

      <LegalH2>Optional group posting (Tier B)</LegalH2>
      <p>
        The optional browser extension that helps you post to Facebook groups runs
        in your own browser, under your control, with pacing safeguards. It is
        higher-risk and used at your own risk; automating activity can lead Meta to
        restrict or ban accounts. You accept that risk if you use it.
      </p>

      <LegalH2>Billing</LegalH2>
      <p>
        Paid plans renew until cancelled. Credits for AI media generation are
        consumed as you use them. Prices may change with notice.
      </p>

      <LegalH2>Liability</LegalH2>
      <p>
        The service is provided “as is.” To the extent permitted by law, we are not
        liable for indirect or consequential damages, or for actions taken by Meta
        against connected accounts.
      </p>

      <LegalH2>Contact</LegalH2>
      <p>Email support@presence.app.</p>
    </LegalPage>
  );
}
