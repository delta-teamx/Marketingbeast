import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import { ApiPrewarm } from "@/components/api-prewarm";

export default function LoginPage() {
  return (
    <AuthShell>
      <ApiPrewarm />
      <AuthForm mode="login" />
    </AuthShell>
  );
}
