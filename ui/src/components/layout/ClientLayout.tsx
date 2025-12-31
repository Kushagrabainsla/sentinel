'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { AuthGuard } from '../auth/AuthGuard';

export function ClientLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const isPublicPage = ['/', '/login', '/register', '/privacy', '/terms'].includes(pathname) || pathname?.startsWith('/blog');

    return (
        <AuthGuard>
            {isPublicPage ? (
                <>{children}</>
            ) : (
                <div className="flex h-screen overflow-hidden bg-background">
                    <Sidebar />
                    <main className="flex-1 overflow-y-auto">
                        <div className="container mx-auto p-8 max-w-7xl">
                            {children}
                        </div>
                    </main>
                </div>
            )}
        </AuthGuard>
    );
}
