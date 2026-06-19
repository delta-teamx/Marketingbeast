import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { SignOutButton } from "@/components/sign-out-button";
import { ProfileSettings } from "@/components/profile-settings";

export const dynamic = "force-dynamic";

const DEMO = process.env.NEXT_PUBLIC_DEMO === "1";

export default async function SettingsPage() {
  let email = "demo@presence.app";
  if (!DEMO) {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      redirect("/login");
    }
    email = user.email ?? "";
  }

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-white/5 bg-[#07070b]/70 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-[#6d5efc] to-[#22d3ee] text-sm">
              P
            </span>
            Presence
          </Link>
          <div className="flex items-center gap-3 text-sm">
            <Link href="/dashboard" className="text-white/60 hover:text-white">
              Dashboard
            </Link>
            <span className="hidden text-white/50 sm:inline">{email}</span>
            <SignOutButton />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-8">
        <ProfileSettings />
      </main>
    </div>
  );
}
