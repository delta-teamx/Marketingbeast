import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 px-6">
      <h1 className="text-3xl font-semibold">Welcome to Presence</h1>
      <p className="text-white/70">
        Signed in as <span className="font-medium">{user.email}</span>.
      </p>
      <p className="text-sm text-white/50">
        This is the Phase 0 skeleton. Connecting Facebook &amp; Instagram and the
        AI presence audit land in the next phases.
      </p>
    </main>
  );
}
