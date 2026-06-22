"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

type Mode = "login" | "signup";

export function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const isSignup = mode === "signup";

  const demo = process.env.NEXT_PUBLIC_DEMO === "1";

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Demo mode: no Supabase — go straight in.
    if (demo) {
      router.push(isSignup ? "/onboarding" : "/dashboard");
      return;
    }
    setError(null);
    setNotice(null);
    setLoading(true);
    try {
      const supabase = createClient();
      const { data, error } = isSignup
        ? await supabase.auth.signUp({ email, password })
        : await supabase.auth.signInWithPassword({ email, password });
      if (error) {
        setError(error.message);
        return;
      }
      // If email confirmation is on, signUp returns no session yet — don't push
      // into the app (it would just bounce back to login). Tell the user to
      // confirm, then sign in.
      if (isSignup && !data.session) {
        setNotice(
          "Account created! Check your email to confirm, then sign in to set up your business.",
        );
        return;
      }
      // Everyone lands on the dashboard, which walks new users through
      // onboarding (business profile + website) before showing the workspace.
      router.push("/dashboard");
    } finally {
      setLoading(false);
    }
  }

  const field =
    "rounded-lg border border-white/15 bg-white/[0.03] px-3 py-2.5 outline-none focus:border-[#6d5efc] transition";

  return (
    <div className="flex w-full max-w-sm flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">
          {isSignup ? "Create your account" : "Welcome back"}
        </h1>
        <p className="mt-1 text-sm text-white/50">
          {isSignup
            ? "Audit your business and start running your social media."
            : "Sign in to your Presence workspace."}
        </p>
      </div>
      {demo && (
        <p className="rounded-lg border border-[#6d5efc]/30 bg-[#6d5efc]/10 p-3 text-xs text-white/70">
          Demo mode — just click {isSignup ? "Sign up" : "Sign in"} (any email/password) to enter.
        </p>
      )}
      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Email
          <input
            type="email"
            name="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={field}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Password
          <input
            type="password"
            name="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={field}
          />
        </label>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {notice && (
          <p className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-300">
            {notice}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary rounded-lg px-4 py-2.5 font-semibold disabled:opacity-50"
        >
          {loading ? "…" : isSignup ? "Sign up" : "Sign in"}
        </button>
      </form>
      <p className="text-sm text-white/60">
        {isSignup ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="underline">
              Sign in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link href="/signup" className="underline">
              Create an account
            </Link>
          </>
        )}
      </p>
    </div>
  );
}
