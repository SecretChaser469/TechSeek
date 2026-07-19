'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
    LayoutDashboard,
    UserCircle,
    Award,
    CheckSquare,
    Users,
    Compass,
    BookOpen,
    Trophy,
    Bell,
    BarChart3,
    LogOut,
    Menu,
    X,
    Flame
} from 'lucide-react';
import { apiRequest } from '../api';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [role, setRole] = useState<string | null>(null);
    const [streak, setStreak] = useState<number>(0);
    const [unreadCount, setUnreadCount] = useState<number>(0);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [userLoaded, setUserLoaded] = useState(false);
    const [userName, setUserName] = useState('');

    useEffect(() => {
        const token = localStorage.getItem('token');
        const userRole = localStorage.getItem('role');

        if (!token) {
            router.push('/');
            return;
        }

        setRole(userRole);

        // Fetch profile to get streak & notification stats
        apiRequest('/api/users/me')
            .then(user => {
                setStreak(user.streak_count);
                setUserName(user.name);
                setUserLoaded(true);
            })
            .catch(() => {
                // Clear broken token
                localStorage.clear();
                router.push('/');
            });

        // Fetch unread notifications
        apiRequest('/api/notifications')
            .then(notifs => {
                const unread = notifs.filter((n: any) => !n.read).length;
                setUnreadCount(unread);
            })
            .catch(() => { });
    }, [router, pathname]);

    const handleLogout = () => {
        localStorage.clear();
        router.push('/');
    };

    if (role === null && !userLoaded) {
        return (
            <div className="min-h-screen bg-[#060814] flex flex-col justify-center items-center">
                <div className="w-12 h-12 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin mb-4" />
                <div className="text-sm text-indigo-400 font-mono tracking-widest animate-pulse">SECURE HANDSHAKE...</div>
            </div>
        );
    }

    const navItems = [
        { name: 'Overview', href: '/dashboard', icon: LayoutDashboard, show: true },
        { name: 'My Profile', href: '/dashboard/profile', icon: UserCircle, show: true },
        { name: 'Achievements', href: '/dashboard/achievements', icon: Award, show: true },
        { name: 'Verification Center', href: '/dashboard/verification-center', icon: CheckSquare, show: role === 'faculty' },
        { name: 'Find Team', href: '/dashboard/find-team', icon: Users, show: true },
        { name: 'Find Mentor', href: '/dashboard/find-mentor', icon: Compass, show: true },
        { name: 'Faculty Directory', href: '/dashboard/faculty-directory', icon: BookOpen, show: true },
        { name: 'Leaderboard', href: '/dashboard/leaderboard', icon: Trophy, show: true },
        { name: 'Notifications', href: '/dashboard/notifications', icon: Bell, show: true, badge: unreadCount > 0 ? unreadCount : undefined },
        { name: 'Accreditation Reports', href: '/dashboard/admin', icon: BarChart3, show: role === 'admin' }
    ];

    return (
        <div className="min-h-screen flex bg-[#060814] text-gray-200">
            {/* Background glow effects */}
            <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-cyan-900/10 blur-[150px] pointer-events-none" />
            <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-900/10 blur-[150px] pointer-events-none" />

            {/* Desktop Sidebar */}
            <aside className="hidden md:flex flex-col w-64 border-r border-white/5 bg-[#0b0e1e]/60 backdrop-blur-xl shrink-0 p-5 justify-between">
                <div className="space-y-6">
                    <div className="flex items-center justify-between pb-4 border-b border-white/5">
                        <Link href="/dashboard" className="flex items-center space-x-2.5">
                            <div className="p-2 rounded-lg bg-indigo-600/10 border border-indigo-500/20 text-cyan-400">
                                <LayoutDashboard className="w-5 h-5" />
                            </div>
                            <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent stats-number">
                                TechSeek
                            </span>
                        </Link>
                    </div>

                    {userName && (
                        <div className="py-2.5 px-3.5 rounded-lg bg-white/5 border border-white/5 flex items-center justify-between">
                            <div>
                                <p className="text-xs text-gray-400 font-medium">Logged in as</p>
                                <h4 className="text-sm font-bold text-white max-w-[120px] truncate">{userName}</h4>
                            </div>
                            <div className="flex items-center space-x-1.5 px-2 py-1 rounded bg-amber-500/10 border border-amber-500/25 text-amber-500 text-xs font-mono">
                                <Flame className="w-3.5 h-3.5 animate-pulse" />
                                <span>{streak}d</span>
                            </div>
                        </div>
                    )}

                    {/* Navigation Links */}
                    <nav className="space-y-1.5">
                        {navItems.map((item) => {
                            if (!item.show) return null;
                            const isActive = pathname === item.href;
                            const Icon = item.icon;
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm transition-all duration-150 ${isActive
                                            ? 'bg-indigo-600/20 border border-indigo-500/30 text-white font-medium shadow-inner'
                                            : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'
                                        }`}
                                >
                                    <div className="flex items-center space-x-3">
                                        <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-gray-400'}`} />
                                        <span>{item.name}</span>
                                    </div>
                                    {item.badge && (
                                        <span className="stats-number px-1.5 py-0.5 rounded text-[10px] bg-indigo-600 text-cyan-200">
                                            {item.badge}
                                        </span>
                                    )}
                                </Link>
                            );
                        })}
                    </nav>
                </div>

                <button
                    onClick={handleLogout}
                    className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-500/5 transition-all text-left"
                >
                    <LogOut className="w-4 h-4 text-gray-500" />
                    <span>Exit Session</span>
                </button>
            </aside>

            {/* Mobile Top Header */}
            <div className="flex flex-col flex-1 min-w-0">
                <header className="md:hidden flex items-center justify-between px-5 py-4 bg-[#0a0f1d] border-b border-white/5 relative z-40">
                    <Link href="/dashboard" className="flex items-center space-x-2">
                        <span className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent stats-number">
                            TechSeek
                        </span>
                    </Link>
                    <div className="flex items-center space-x-3">
                        <div className="flex items-center space-x-1 px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 text-xs font-mono">
                            <Flame className="w-3.5 h-3.5" />
                            <span>{streak}d</span>
                        </div>
                        <button
                            onClick={() => setMobileOpen(!mobileOpen)}
                            className="p-1 rounded bg-white/5 text-gray-300"
                        >
                            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>
                </header>

                {/* Mobile Navigation Drawer */}
                {mobileOpen && (
                    <div className="md:hidden fixed inset-0 top-[60px] z-30 bg-[#060814]/95 backdrop-blur-md p-6 flex flex-col justify-between border-t border-white/5">
                        <nav className="space-y-2">
                            {navItems.map((item) => {
                                if (!item.show) return null;
                                const isActive = pathname === item.href;
                                const Icon = item.icon;
                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        onClick={() => setMobileOpen(false)}
                                        className={`flex items-center justify-between px-3 py-3 rounded-lg text-sm ${isActive
                                                ? 'bg-indigo-600/20 text-white font-medium border border-indigo-500/20'
                                                : 'text-gray-400 hover:text-white'
                                            }`}
                                    >
                                        <div className="flex items-center space-x-3">
                                            <Icon className="w-4 h-4" />
                                            <span>{item.name}</span>
                                        </div>
                                        {item.badge && (
                                            <span className="stats-number px-1.5 py-0.5 rounded text-[10px] bg-indigo-600 text-cyan-200">
                                                {item.badge}
                                            </span>
                                        )}
                                    </Link>
                                );
                            })}
                        </nav>
                        <button
                            onClick={() => {
                                setMobileOpen(false);
                                handleLogout();
                            }}
                            className="flex items-center space-x-3 px-3 py-3 rounded-lg text-sm text-red-400 bg-red-500/5 hover:bg-red-500/10 text-left w-full mt-4"
                        >
                            <LogOut className="w-4 h-4" />
                            <span>Exit Session</span>
                        </button>
                    </div>
                )}

                {/* Scrollable Context Box */}
                <main className="flex-1 overflow-y-auto p-5 md:p-8 lg:p-10 relative">
                    {children}
                </main>
            </div>
        </div>
    );
}
