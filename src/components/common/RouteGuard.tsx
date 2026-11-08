import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';

import { useAuth } from '@/contexts/AuthContext';
import { routes } from '@/routes';

interface RouteGuardProps {
  children: ReactNode;
}

// Routes that do not require authentication.
const SYSTEM_PUBLIC_ROUTES = ['/login', '/403', '/404'];

// Routes marked as public in routes.tsx.
const routePublicPaths = routes
  .filter((route) => route.public)
  .map((route) => route.path);

const PUBLIC_ROUTES = [
  ...SYSTEM_PUBLIC_ROUTES,
  ...routePublicPaths,
];

/**
 * Escapes special regex characters in a route pattern.
 */
function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Checks whether a pathname matches a public route.
 * Supports wildcard patterns such as /public/*.
 */
function matchPublicRoute(path: string, patterns: string[]): boolean {
  return patterns.some((pattern) => {
    const regexPattern = pattern
      .split('*')
      .map(escapeRegex)
      .join('.*');

    return new RegExp(`^${regexPattern}$`).test(path);
  });
}

export function RouteGuard({ children }: RouteGuardProps) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const isPublic = matchPublicRoute(
    location.pathname,
    PUBLIC_ROUTES
  );

  useEffect(() => {
    if (loading || user || isPublic) {
      return;
    }

    const destination =
      location.pathname + location.search + location.hash;

    navigate('/login', {
      state: { from: destination },
      replace: true,
    });
  }, [
    user,
    loading,
    isPublic,
    location.pathname,
    location.search,
    location.hash,
    navigate,
  ]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div
          className="h-12 w-12 animate-spin rounded-full border-b-2 border-primary"
          role="status"
          aria-label="Loading"
        />
      </div>
    );
  }

  // Prevent protected page content from flashing before redirection.
  if (!user && !isPublic) {
    return null;
  }

  return <>{children}</>;
}