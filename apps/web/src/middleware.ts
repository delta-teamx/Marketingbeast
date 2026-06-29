import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

type CookieToSet = { name: string; value: string; options?: CookieOptions };

/** Refreshes the Supabase auth session on each navigation (keeps cookies fresh).
 *
 * This runs as a Netlify Edge Function. It must NEVER throw: an unhandled error
 * here renders the "edge function has crashed" page for the user (e.g. when a
 * device carries a stale/expired auth cookie, or the Supabase env wasn't inlined
 * into a build). So every failure path falls through to a normal response. */
export async function middleware(request: NextRequest) {
  // Demo mode runs without Supabase — skip session refresh entirely.
  if (process.env.NEXT_PUBLIC_DEMO === "1") {
    return NextResponse.next({ request });
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  // Without Supabase config there's nothing to refresh — don't construct a client
  // (which would crash the edge function on the first auth call).
  if (!supabaseUrl || !supabaseAnonKey) {
    return NextResponse.next({ request });
  }

  let response = NextResponse.next({ request });

  try {
    const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet: CookieToSet[]) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            response.cookies.set(name, value, options),
          );
        },
      },
    });

    // A bad/expired cookie or a transient Supabase error must not crash the page.
    await supabase.auth.getUser();
  } catch {
    // Fall through with a clean response; the app's own auth guards handle
    // redirecting unauthenticated users.
    return NextResponse.next({ request });
  }

  return response;
}

export const config = {
  // Only run on authenticated app routes that need a fresh session. Marketing and
  // auth pages render fine without the edge function — keeping them off it means a
  // shared public link can never hit an edge-function crash.
  matcher: ["/dashboard/:path*", "/onboarding/:path*", "/settings/:path*"],
};
