import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;
  
  // If accessing a specific conversation page, allow through and let client handle auth
  if (pathname.match(/\/conversations\/[\w-]+/)) {
    return NextResponse.next();
  }

  // Add routes that should be protected
  const protectedRoutes = ['/conversations'];
  // Add routes that logged-in users shouldn't access
  const authRoutes = ['/login', '/register'];

  // Redirect logged-in users trying to access auth routes
  if (token && authRoutes.includes(pathname)) {
    return NextResponse.redirect(new URL('/conversations', request.url));
  }
  
  // Redirect non-logged-in users trying to access protected routes
  if (!token && protectedRoutes.some(route => pathname === route)) {
    const redirectUrl = new URL('/login', request.url);
    redirectUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // Handle root route - MODIFIED THIS SECTION
  if (pathname === '/') {
    return NextResponse.next(); // Allow access to landing page
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)']
}
