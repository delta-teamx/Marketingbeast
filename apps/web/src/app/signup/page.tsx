import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { ApiPrewarm } from "@/components/api-prewarm";

export default function SignupPage() {
  return (
    <AuthShell>
      <ApiPrewarm />
      <AuthForm mode="signup" />
    </AuthShell>
  );
}
