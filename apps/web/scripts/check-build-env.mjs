// Prebuild guard: NEXT_PUBLIC_API_BASE_URL is inlined into the bundle at build
// time. If it's missing, the shipped app silently calls http://localhost:8000
// and every request fails for real users — so fail the build loudly instead.
// Demo builds (NEXT_PUBLIC_DEMO=1) talk to a local API on purpose and are exempt.
if (process.env.NEXT_PUBLIC_DEMO !== "1" && !process.env.NEXT_PUBLIC_API_BASE_URL) {
  console.error(
    "\n✖ Build aborted: NEXT_PUBLIC_API_BASE_URL is not set.\n" +
      "  Set it to your API's URL (e.g. https://presence-api.onrender.com) in the\n" +
      "  build environment before building, or set NEXT_PUBLIC_DEMO=1 for a demo build.\n",
  );
  process.exit(1);
}
