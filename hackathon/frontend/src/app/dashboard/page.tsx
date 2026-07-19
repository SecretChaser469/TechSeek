'use client';

import { useState, useEffect } from 'react';
import Link from 'next/navigation';
import { apiRequest } from '../api';
import {
    Award,
    Flame,
    Users,
    BookOpen,
    ArrowRight,
    ShieldCheck,
    AlertTriangle,
    Upload,
    Search,
    CheckCircle,
    HelpCircle
} from 'lucide-react';

export default function DashboardOverview() {
    const [user, setUser] = useState<any>(null);
    const [badges, setBadges] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState({
        achievements: 0,
        applications: 0,
        connections: 0,
        flagged: 0
    });

    useEffect(() => {
        async function loadDashboardData() {
            try {
                const u = await apiRequest('/api/users/me');
                setUser(u);

                // Calculate metrics
                const achs = u.achievements || [];
                const verified = achs.filter((a: any) => a.verification_status === 'faculty_verified').length;
                const flagged = achs.filter((a: any) => a.verification_status === 'ai_flagged').length;

                // Fetch user badges
                const b = await apiRequest('/api/gamification/badges');
                const earned = b.filter((badge: any) => badge.earned_at || badge.users?.length > 0);
                setBadges(earned);

                // Fetch team request count
                let appsCount = 0;
                try {
                    const reqs = await apiRequest('/api/teams/requests');
                    appsCount = reqs.length;
                } catch (e) { }

                setMetrics({
                    achievements: verified,
                    applications: appsCount,
                    connections: u.streak_count || 1, // fallback mock representation
                    flagged
                });
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        }
        loadDashboardData();
    }, []);

    if (loading) {
        return (
            <div className="space-y-6 animate-pulse">
                <div className="h-10 bg-white/5 rounded-lg w-1/4" />
                <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
                    {[1, 2, 3, 4].map(n => (
                        <div key={n} className="h-28 bg-white/5 rounded-xl border border-white/5" />
                    ))}
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 h-64 bg-white/5 rounded-xl" />
                    <div className="h-64 bg-white/5 rounded-xl" />
                </div>
            </div>
        );
    }

    const isFaculty = user?.role === 'faculty';

    return (
        <div className="space-y-8">
            {/* Welcome Banner */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                <div>
                    <h1 className="text-3xl font-extrabold tracking-tight text-white">
                        Honor Room overview
                    </h1>
                    <p className="text-gray-400 text-sm mt-1">
                        Hello, <span className="text-indigo-400 font-semibold">{user?.name}</span> ({user?.role}). Below are your verified credentials as of today.
                    </p>
                </div>

                <div className="flex items-center space-x-3">
                    <Link
                        href={isFaculty ? "/dashboard/verification-center" : "/dashboard/achievements"}
                        className="flex items-center space-x-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-all shadow-md active:scale-95"
                    >
                        {isFaculty ? (
                            <>
                                <CheckSquare className="w-4 h-4" />
                                <span>Verify Upload Queue</span>
                            </>
                        ) : (
                            <>
                                <Upload className="w-4 h-4" />
                                <span>Log New Achievement</span>
                            </>
                        )}
                    </Link>
                </div>
            </div>

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {/* Stat 1 */}
                <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between h-28">
                    <div className="flex justify-between items-start">
                        <span className="text-xs uppercase tracking-wider text-mutedGray font-semibold">Active Streak</span>
                        <Flame className="w-5 h-5 text-amber-500" />
                    </div>
                    <div className="flex items-baseline space-x-1.5 mt-2">
                        <span className="text-3xl stats-number font-bold text-white">{user?.streak_count || 0}</span>
                        <span className="text-xs text-amber-500">Days Active</span>
                    </div>
                </div>

                {/* Stat 2 */}
                <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between h-28">
                    <div className="flex justify-between items-start">
                        <span className="text-xs uppercase tracking-wider text-mutedGray font-semibold">Verified Records</span>
                        <Award className="w-5 h-5 text-emerald-500" />
                    </div>
                    <div className="flex items-baseline space-x-1.5 mt-2">
                        <span className="text-3xl stats-number font-bold text-white">{metrics.achievements}</span>
                        <span className="text-xs text-emerald-500">Accredited</span>
                    </div>
                </div>

                {/* Stat 3 */}
                <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between h-28">
                    <div className="flex justify-between items-start">
                        <span className="text-xs uppercase tracking-wider text-mutedGray font-semibold">Flagged Uploads</span>
                        <AlertTriangle className="w-5 h-5 text-rose-500" />
                    </div>
                    <div className="flex items-baseline space-x-1.5 mt-2">
                        <span className="text-3xl stats-number font-bold text-white">{metrics.flagged}</span>
                        <span className="text-xs text-rose-500">Requires Review</span>
                    </div>
                </div>

                {/* Stat 4 */}
                <div className="glass-panel p-5 relative overflow-hidden flex flex-col justify-between h-28">
                    <div className="flex justify-between items-start">
                        <span className="text-xs uppercase tracking-wider text-mutedGray font-semibold">Team Opportunities</span>
                        <Users className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div className="flex items-baseline space-x-1.5 mt-2">
                        <span className="text-3xl stats-number font-bold text-white">{metrics.applications}</span>
                        <span className="text-xs text-cyan-400">Open Boards</span>
                    </div>
                </div>
            </div>

            {/* Main Grid: Detail Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Side: Recent Achievements */}
                <div className="lg:col-span-2 space-y-5">
                    <div className="flex justify-between items-center">
                        <h3 className="text-lg font-bold text-white tracking-tight">Recent Portfolio Uploads</h3>
                        <Link href="/dashboard/achievements" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center space-x-0.5">
                            <span>View Full list</span>
                            <ArrowRight className="w-3 h-3" />
                        </Link>
                    </div>

                    <div className="glass-panel divide-y divide-white/5">
                        {user?.achievements && user.achievements.length > 0 ? (
                            user.achievements.slice(0, 4).map((ach: any) => (
                                <div key={ach.id} className="p-4 flex items-center justify-between">
                                    <div className="space-y-1">
                                        <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono tracking-wider bg-white/5 border border-white/5 uppercase text-gray-400">
                                            {ach.type}
                                        </span>
                                        <h4 className="text-sm font-semibold text-white mt-1">{ach.title}</h4>
                                        <p className="text-xs text-gray-400 line-clamp-1">{ach.description}</p>
                                    </div>
                                    <div>
                                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono tracking-widest uppercase border ${ach.verification_status === 'faculty_verified'
                                                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                                                : ach.verification_status === 'ai_flagged'
                                                    ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
                                                    : ach.verification_status === 'rejected'
                                                        ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                                                        : 'bg-gray-500/10 border-gray-500/20 text-gray-400'
                                            }`}>
                                            {ach.verification_status.replace('_', ' ')}
                                        </span>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="p-8 text-center text-xs text-gray-500">
                                No achievements recorded yet. Add your certificates, projects, or hackathons to get began.
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Side: Badges & Gamification Overview */}
                <div className="space-y-5">
                    <h3 className="text-lg font-bold text-white tracking-tight">Earned Badges</h3>
                    <div className="glass-panel p-5 space-y-4">
                        {badges.length > 0 ? (
                            <div className="grid grid-cols-4 gap-4">
                                {badges.map((b: any) => {
                                    const bd = b.badge || b;
                                    return (
                                        <div key={bd.id} className="flex flex-col items-center justify-center p-2 rounded-lg bg-white/5 border border-white/5 group relative" title={bd.description}>
                                            <span className="text-2xl mb-1 filter drop-shadow-[0_0_5px_rgba(99,102,241,0.5)]">
                                                {bd.icon_url || '🏆'}
                                            </span>
                                            <span className="text-[9px] font-semibold text-center text-gray-300 truncate w-full">
                                                {bd.name}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="text-center py-6 text-xs text-gray-500 space-y-2">
                                <HelpCircle className="w-8 h-8 text-mutedGray mx-auto" />
                                <p>No badges earned yet.</p>
                                <p className="text-[10px] text-indigo-400">Unlock your first badge by uploading a hackathon achievement!</p>
                            </div>
                        )}
                    </div>

                    {/* Quick Info Box */}
                    <div className="glass-panel p-5 bg-gradient-to-br from-indigo-900/15 via-[#0b0e1e]/60 to-[#060814] relative overflow-hidden">
                        <h4 className="text-sm font-bold text-white mb-2 flex items-center space-x-1.5">
                            <ShieldCheck className="w-4 h-4 text-cyan-400" />
                            <span>AI Assisted Verification</span>
                        </h4>
                        <p className="text-xs text-gray-400 leading-relaxed">
                            When uploading proof documents, our OCR system scans contents to estimate confidence scores. Faculty checks all documents for accreditation.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
