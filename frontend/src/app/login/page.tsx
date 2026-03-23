'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginPage() {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [err, setErr] = useState('');
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr('');
    try {
      const res = await login(user, pass);
      localStorage.setItem('netscope_token', res.access_token);
      router.push('/dashboard');
    } catch {
      setErr('Invalid credentials. Try admin/admin for demo.');
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={handleSubmit} className="card w-full max-w-sm space-y-4">
        <h1 className="text-xl font-display font-bold text-net-400">NetScope Login</h1>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Username</label>
          <input
            type="text"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            className="w-full px-3 py-2 rounded bg-dark-700 border border-dark-500 focus:border-net-500 outline-none"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Password</label>
          <input
            type="password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            className="w-full px-3 py-2 rounded bg-dark-700 border border-dark-500 focus:border-net-500 outline-none"
            required
          />
        </div>
        {err && <p className="text-red-400 text-sm">{err}</p>}
        <button type="submit" className="w-full py-2 rounded bg-net-600 hover:bg-net-500 transition">
          Sign in
        </button>
      </form>
    </main>
  );
}
