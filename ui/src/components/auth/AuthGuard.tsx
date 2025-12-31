'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
    children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [isChecking, setIsChecking] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    const publicRoutes = ['/', '/login', '/register', '/privacy', '/terms'];
    const isPublicRoute = publicRoutes.includes(pathname) || pathname?.startsWith('/blog');

    useEffect(() => {
        const checkAuth = () => {
            if (typeof window === 'undefined') {
                return;
            }

            const apiKey = localStorage.getItem('sentinel_api_key');
            const hasAuth = !!apiKey;

            setIsAuthenticated(hasAuth);
            setIsChecking(false);

            // If not authenticated and trying to access protected route, redirect to login
            if (!hasAuth && !isPublicRoute) {
                router.push('/login');
            }

            // If authenticated and trying to access login/register, redirect to dashboard
            if (hasAuth && (pathname === '/login' || pathname === '/register')) {
                router.push('/dashboard');
            }
        };

        checkAuth();
    }, [pathname, isPublicRoute, router]);

    // Show loading state while checking authentication
    if (isChecking) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <p className="text-sm text-muted-foreground">Loading...</p>
                </div>
            </div>
        );
    }

    // For public routes, always show content
    if (isPublicRoute) {
        return <>{children}</>;
    }

    // For protected routes, only show if authenticated
    if (isAuthenticated) {
        return <>{children}</>;
    }

    // Return null while redirecting
    return null;
}
