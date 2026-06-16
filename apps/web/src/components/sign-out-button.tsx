"use client";

import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function SignOutButton() {
  const router = useRouter();
  return (
    <button
      onClick={async () => {
        await createClient().auth.signOut();
        router.push("/login");
      }}
      className="btn-ghost rounded-lg px-3 py-1.5 text-sm"
    >
      Sign out
    </button>
  );
}
