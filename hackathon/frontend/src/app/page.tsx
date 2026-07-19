'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiRequest } from './api';
import { Shield, Sparkles, GraduationCap, Lock, Mail, User } from 'lucide-react';

export default function AuthPage() {
    const router = useRouter();
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [role, setRole] = useState('student');
    const [semester, setSemester] = useState(1);
    const [branch, setBranch] = useState('Computer Science');
    const [bioShort, setBioShort] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Check if already authenticated
        const token = localStorage.getItem('token');
        if (token) {
            router.push('/dashboard');
        }
    }, [router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        // Validate email domain
        if (!email.toLowerCase().endsWith('@college.edu')) {
            setError('Access restricted to institutional email domains (@college.edu).');
            setLoading(false);
            return;
        }

        try {
            if (isLogin) {
                const data = await apiRequest('/api/auth/login', {
                    method: 'POST',
                    body: { email, password }
                });
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                localStorage.setItem('userId', data.user_id.toString());
                router.push('/dashboard');
            } else {
                const body: Record<string, any> = {
                    email,
                    password,
                    name,
                    role,
                    bio_short: bioShort || 'Determined Learner'
                };
                if (role === 'student') {
                    body.semester = Number(semester);
                    body.branch = branch;
                }

                const data = await apiRequest('/api/auth/signup', {
                    method: 'POST',
                    body
                });
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                localStorage.setItem('userId', data.user_id.toString());
                router.push('/dashboard');
            }
        } catch (err: any) {
            setError(err.message || 'Authentication failed. Please verify credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen grid lg:grid-cols-2 relative bg-[#060814] select-none text-gray-200">
            {/* Background glow effects */}
            <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-900/20 blur-[150px] pointer-events-none" />
            <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-900/10 blur-[150px] pointer-events-none" />

            {/* Left Column - Branding (Visual Wow) */}
            <div className="hidden lg:flex flex-col justify-between p-12 border-r border-white/5 bg-gradient-to-br from-[#0c1024] to-[#060814] relative overflow-hidden">
                <div className="flex items-center space-x-2">
                    <div className="p-2.5 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-cyan-300">
                        <Shield className="w-6 h-6 animate-pulse" />
                    </div>
                    <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent stats-number">
                        TechSeek
                    </span>
                </div>

                <div className="my-auto space-y-6 max-w-md">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium text-cyan-400 bg-cyan-400/5 border border-cyan-400/10">
                        <Sparkles className="w-3.5 h-3.5 mr-1" /> Checked Accomplishment Graph
                    </span>
                    <h1 className="text-4xl font-extrabold tracking-tight leading-tight text-white">
                        Unifying college Achievements and verified talent profiles.
                    </h1>
                    <p className="text-sm text-gray-400 leading-relaxed">
                        Build your professional identity from semester one. Standardise portfolio records verified by AI OCR detection and institution faculty checks, while exploring exclusive matches.
                    </p>

                    {/* Stats layout */}
                    <div className="grid grid-cols-3 gap-6 pt-4 border-t border-white/5">
                        <div>
                            <div className="stats-number text-2xl font-bold text-white">100%</div>
                            <div className="text-xs text-gray-400 uppercase mt-0.5">Faculty Checked</div>
                        </div>
                        <div>
                            <div className="stats-number text-2xl font-bold text-white">1.2k+</div>
                            <div className="text-xs text-gray-400 uppercase mt-0.5">Students</div>
                        </div>
                        <div>
                            <div className="stats-number text-2xl font-bold text-white">8+</div>
                            <div className="text-xs text-gray-400 uppercase mt-0.5">Badges</div>
                        </div>
                    </div>
                </div>

                <div className="text-xs text-gray-500">
                    &copy; {new Date().getFullYear()} College TechSeek Administration System.
                </div>
            </div>

            {/* Right Column - Auth Forms */}
            <div className="flex flex-col justify-center items-center p-6 lg:p-12">
                <div className="w-full max-w-sm glass-panel p-8 shadow-2xl relative">
                    <div className="absolute top-3 right-3 text-[10px] text-cyan-400/60 font-mono tracking-widest uppercase">
                        SECURE ACCESS
                    </div>

                    <div className="text-center mb-6">
                        <h2 className="text-2xl font-bold text-white tracking-tight">
                            {isLogin ? 'Welcome Back' : 'Create Identity'}
                        </h2>
                        <p className="text-xs text-gray-400 mt-1.5">
                            {isLogin ? 'Access your dashboard with credentials' : 'Register your institutional record'}
                        </p>
                    </div>

                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-xs px-3.5 py-2.5 rounded-lg mb-4 text-center">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!isLogin && (
                            <div className="space-y-1">
                                <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3.5 w-4 h-4 text-gray-500" />
                                    <input
                                        type="text"
                                        required
                                        placeholder="Jane Doe"
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="w-full pl-9 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                    />
                                </div>
                            </div>
                        )}

                        <div className="space-y-1">
                            <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Institution Email</label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-3.5 w-4 h-4 text-gray-500" />
                                <input
                                    type="email"
                                    required
                                    placeholder="jane.doe@college.edu"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    className="w-full pl-9 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                />
                            </div>
                        </div>

                        <div className="space-y-1">
                            <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Password</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-3.5 w-4 h-4 text-gray-500" />
                                <input
                                    type="password"
                                    required
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full pl-9 pr-4 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                />
                            </div>
                        </div>

                        {!isLogin && (
                            <>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-1">
                                        <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Accreditation Identity</label>
                                        <select
                                            value={role}
                                            onChange={(e) => setRole(e.target.value)}
                                            className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                        >
                                            <option className="bg-[#0b0f1d]" value="student">Student</option>
                                            <option className="bg-[#0b0f1d]" value="faculty">Faculty</option>
                                        </select>
                                    </div>

                                    {role === 'student' ? (
                                        <div className="space-y-1">
                                            <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Semester</label>
                                            <select
                                                value={semester}
                                                onChange={(e) => setSemester(Number(e.target.value))}
                                                className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                            >
                                                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                                                    <option key={s} className="bg-[#0b0f1d]" value={s}>Semester {s}</option>
                                                ))}
                                            </select>
                                        </div>
                                    ) : null}
                                </div>

                                {role === 'student' ? (
                                    <div className="space-y-1">
                                        <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Academic Department</label>
                                        <input
                                            type="text"
                                            required
                                            placeholder="Computer Science, ECE, BioTech"
                                            value={branch}
                                            onChange={(e) => setBranch(e.target.value)}
                                            className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                        />
                                    </div>
                                ) : null}

                                <div className="space-y-1">
                                    <label className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Tagline / Short Bio</label>
                                    <input
                                        type="text"
                                        required
                                        placeholder="Full stack hacker / ML researcher"
                                        value={bioShort}
                                        onChange={(e) => setBioShort(e.target.value)}
                                        className="w-full px-3 py-2.5 bg-black/40 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-indigo-500 text-white transition-colors"
                                    />
                                </div>
                            </>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 mt-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800/50 rounded-lg text-sm font-semibold tracking-wider transition-colors shadow-lg hover:shadow-indigo-500/20 active:scale-[0.98] transform duration-100 flex justify-center items-center"
                        >
                            {loading ? (
                                <div className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin" />
                            ) : isLogin ? (
                                'SIGN IN INSTANTLY'
                            ) : (
                                'REGISTER ACCOUNT'
                            )}
                        </button>
                    </form>

                    <div className="mt-6 pt-4 border-t border-white/5 text-center text-xs">
                        <span className="text-gray-400">
                            {isLogin ? "New to the system?" : "Already registered?"}
                        </span>{' '}
                        <button
                            onClick={() => {
                                setError('');
                                setIsLogin(!isLogin);
                            }}
                            className="text-cyan-400 hover:underline font-medium"
                        >
                            {isLogin ? 'Register now' : 'Log in here'}
                        </button>
                    </div>
                </div>
            </div>
        </main>
    );
}
