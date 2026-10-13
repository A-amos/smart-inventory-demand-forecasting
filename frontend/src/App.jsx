import { useState } from 'react';
import { api } from './api';
import Workspace from './Workspace';

export default function App() {
  const [session, setSession] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function login(event) {
    event.preventDefault(); setError(''); setBusy(true);
    const data = new FormData(event.currentTarget);
    try { setSession(await api('/auth/login', { method: 'POST', body: JSON.stringify(Object.fromEntries(data)) })); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true); setError('');
    try { await api('/auth/logout', { method: 'POST', token: session.access_token }); setSession(null); }
    catch (err) { if (err.status === 401) setSession(null); else setError(`Sign out could not be confirmed: ${err.message}`); }
    finally { setBusy(false); }
  }
  return <main className="min-h-screen bg-slate-50 text-slate-900 px-6 py-12">
    <div className="mx-auto max-w-5xl">
      <header className="mb-12"><p className="text-xs font-semibold tracking-widest text-teal-700 uppercase">Retail decision support</p><h1 className="text-3xl font-bold mt-3">Smart Inventory</h1><p className="mt-3 text-slate-600">Demand forecasting and replenishment planning</p></header>
      <section className={`bg-white border border-slate-200 rounded-2xl p-6 shadow-sm ${session ? '' : 'max-w-xl'}`}>
        {session ? <><div className="flex flex-wrap items-center justify-between gap-4 mb-8"><h2 className="text-xl font-semibold">Welcome, {session.user.name}</h2><button className="button" disabled={busy} onClick={logout}>Sign out</button></div><Workspace session={session} onUnauthorized={() => setSession(null)}/></> : <>
          <h2 className="text-xl font-semibold">Sign in to your workspace</h2><p className="mt-2 mb-6 text-sm text-slate-600">Use your authorized inventory account.</p>
          <form onSubmit={login} className="space-y-5">
            <label className="block text-sm font-medium">Email<input className="field" type="email" name="email" autoComplete="username" required maxLength={254}/></label>
            <label className="block text-sm font-medium">Password<input className="field" type="password" name="password" autoComplete="current-password" required maxLength={128}/></label>
            <button className="button w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
          </form></>}
        {error && <p role="alert" className="text-red-700 text-sm mt-4">{error}</p>}
      </section>
      <footer className="mt-10 text-sm text-slate-500">Maseno University · Computer Science research prototype</footer>
    </div>
  </main>;
}
