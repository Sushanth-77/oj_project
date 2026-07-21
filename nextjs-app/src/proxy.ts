import { NextResponse } from "next/server";
import { auth } from "@/lib/auth";

export default auth((req) => {
  const isLoggedIn = !!req.auth;
  const isAuthPage = req.nextUrl.pathname.startsWith("/login") || req.nextUrl.pathname.startsWith("/register");
  const isAdminRoute = req.nextUrl.pathname.startsWith("/admin");

  if (isAuthPage) {
    if (isLoggedIn) {
      return NextResponse.redirect(new URL("/problems", req.url));
    }
    return;
  }

  if (!isLoggedIn && (req.nextUrl.pathname.startsWith("/submissions") || req.nextUrl.pathname.startsWith("/admin"))) {
    let from = req.nextUrl.pathname;
    if (req.nextUrl.search) {
      from += req.nextUrl.search;
    }
    return NextResponse.redirect(
      new URL(`/login?from=${encodeURIComponent(from)}`, req.url)
    );
  }

  if (isAdminRoute && !req.auth?.user?.isAdmin) {
    return NextResponse.redirect(new URL("/problems", req.url));
  }
});

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
