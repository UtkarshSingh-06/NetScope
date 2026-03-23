'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center p-8">
      <div className="text-center space-y-6">
        <h1 className="text-4xl font-display font-bold bg-gradient-to-r from-net-400 to-emerald-400 bg-clip-text text-transparent">
          NetScope
        </h1>
        <p className="text-slate-400 text-lg max-w-md mx-auto">
          AI-powered network observability and security platform
        </p>
        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 rounded-lg glass hover:bg-dark-700 transition"
          >
            Login
          </Link>
          <Link
            href="/dashboard"
            className="px-6 py-3 rounded-lg bg-net-600 hover:bg-net-500 text-white font-medium transition"
          >
            Dashboard
          </Link>
          <Link
            href="/alerts"
            className="px-6 py-3 rounded-lg glass hover:bg-dark-700 transition"
          >
            Alerts
          </Link>
        </div>
      </div>
    </main>
  );
}
