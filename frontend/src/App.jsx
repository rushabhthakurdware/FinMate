import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { supabase } from './lib/supabase';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import RiskForm from './pages/RiskForm';
import Advisory from './pages/Advisory';
import Knowledge from './pages/Knowledge';

export default function App() {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-400">Initializing FINMATE...</div>;

  return (
    <Router>
      <div className="min-h-screen bg-slate-900 text-slate-100">
        <Navbar session={session || { user: { email: 'dev@finmate.local' } }} />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/risk" element={<RiskForm />} />
          <Route path="/advisory" element={<Advisory />} />
          <Route path="/knowledge" element={<Knowledge />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
}