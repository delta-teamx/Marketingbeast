import type { ReactNode } from "react";
import { Footer, Nav } from "@/components/marketing";

export function LegalPage({
  title,
  updated,
  children,
}: {
  title: string;
  updated: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen">
      <Nav />
      <main className="mx-auto max-w-3xl px-6 py-16">
        <h1 className="text-4xl font-bold">{title}</h1>
        <p className="mt-2 text-sm text-white/40">Last updated: {updated}</p>
        <div className="prose-invert mt-8 flex flex-col gap-5 text-sm leading-relaxed text-white/70">
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}

export function LegalH2({ children }: { children: ReactNode }) {
  return <h2 className="mt-4 text-xl font-semibold text-white">{children}</h2>;
}
