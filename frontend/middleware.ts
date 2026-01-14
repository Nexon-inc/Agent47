import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  
  // Protect admin routes - only admins can access
  if (pathname.startsWith('/admin')) {
    // Check for admin token in localStorage (we'll check this on the client side)
    // For server-side, we check if there's an admin token cookie
    const adminToken = request.cookies.get('admin_token')?.value
    
    // If no admin token, redirect to admin login
    // Note: We can't access localStorage in middleware, so we check cookies
    // The admin login page will set the admin_token cookie
    if (!adminToken || adminToken === 'null' || adminToken === 'undefined') {
      // Allow access to admin login page
      if (pathname === '/admin/login' || pathname === '/admin') {
        return NextResponse.next()
      }
      // Redirect all other admin pages to login
      const url = request.nextUrl.clone()
      url.pathname = '/admin/login'
      url.searchParams.set('redirect', pathname)
      return NextResponse.redirect(url)
    }
  }
  
  // Check if user is accessing dashboard or protected routes
  // Note: We allow access here and let the backend middleware handle tier checks
  // The backend will redirect to pricing if tier is not set or insufficient
  // This is because tier information may not be in cookies immediately after login
  if (pathname.startsWith('/dashboard')) {
    // Just check if user has an access token (basic auth check)
    // Backend will handle tier validation and redirects
    const accessToken = request.cookies.get('access_token')?.value
    // If no token at all, they're not authenticated - but let the backend handle this
    // We don't redirect here because the backend middleware handles auth
  }
  
  // Check if user is accessing onboarding but has already completed it
  if (pathname.startsWith('/onboarding')) {
    const onboardingCompleted = request.cookies.get('onboarding_completed')?.value
    
    if (onboardingCompleted === 'true') {
      const url = request.nextUrl.clone()
      url.pathname = '/dashboard'
      return NextResponse.redirect(url)
    }
  }
  
  const response = NextResponse.next()
  
  // Add performance headers for faster navigation
  response.headers.set('X-DNS-Prefetch-Control', 'on')
  response.headers.set('X-Frame-Options', 'SAMEORIGIN')
  
  // Enable prefetching for common routes
  if (pathname === '/') {
    const linkHeader = [
      '</dashboard>; rel=prefetch',
      '</auth>; rel=prefetch',
      '</pricing>; rel=prefetch',
    ].join(', ')
    response.headers.set('Link', linkHeader)
  }
  
  return response
}

export const config = {
  matcher: [
    '/dashboard/:path*',
    '/admin/:path*',
    '/onboarding/:path*'
  ]
}