"use client";

import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function SignOutButton() {
  const router = useRouter();
  return (
    <button
      onClick={async () => {
        if (process.env.NEXT_PUBLIC_DEMO !== "1") {
          await createClient().auth.signOut();
        }
        router.push(process.env.NEXT_PUBLIC_DEMO === "1" ? "/" : "/login");
      }}
      className="btn-ghost rounded-lg px-3 py-1.5 text-sm"
    >
      Sign out
    </button>
  );
}
