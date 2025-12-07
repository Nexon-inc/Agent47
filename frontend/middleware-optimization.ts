/**
 * Middleware optimizations for faster navigation
 * This file contains utilities to optimize Next.js navigation performance
 */

import { NextRequest, NextResponse } from "next/server"

/**
 * Add performance headers for faster page loads
 */
export function addPerformanceHeaders(response: NextResponse) {
  // Enable HTTP/2 Server Push hints
  response.headers.set("Link", "</fonts>; rel=preload; as=font; crossorigin")
  
  // Cache static assets
  response.headers.set("Cache-Control", "public, max-age=31536000, immutable")
  
  return response
}

/**
 * Prefetch routes for faster navigation
 */
export const prefetchRoutes = [
  "/dashboard",
  "/dashboard?tab=home",
  "/dashboard?tab=agents-overview",
  "/dashboard?tab=platforms-overview",
  "/auth",
  "/pricing",
  "/features",
]

