import Link from "next/link";

/** Landing hero. Kept as a standalone component so it's unit-testable. */
export function Hero() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-8 px-6 text-center">
      <span className="rounded-full border border-white/15 px-3 py-1 text-xs uppercase tracking-widest text-white/60">
        Presence
      </span>
      <h1 className="text-4xl font-semibold leading-tight sm:text-6xl">
        Be everywhere. Lift no finger.
      </h1>
      <p className="max-w-xl text-lg text-white/70">
        Your AI marketing employee. Enter your business URL and Presence audits
        your social presence, then generates, schedules, and publishes content
        across Facebook and Instagram.
      </p>
      <div className="flex flex-wrap items-center justify-center gap-4">
        <Link
          href="/signup"
          className="rounded-md bg-white px-6 py-3 font-medium text-black transition hover:bg-white/90"
        >
          Get started
        </Link>
        <Link
          href="/login"
          className="rounded-md border border-white/20 px-6 py-3 font-medium transition hover:bg-white/5"
        >
          Sign in
        </Link>
      </div>
    </main>
  );
}
