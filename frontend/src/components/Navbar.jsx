import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { LayoutDashboard, Upload, ShieldAlert, TrendingUp, BookOpen, LogOut } from 'lucide-react';

export default function Navbar({ session }) {
  const navigate = useNavigate();

  const handleLogout = async () => {
    await supabase.auth.signOut();
    navigate('/login');
  };

  return (
    <nav className="bg-slate-800 border-b border-slate-700 px-6 py-4 flex justify-between items-center">
      <div className="flex items-center gap-2">
        <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent">
          FINMATE
        </span>
      </div>

      {session && (
        <div className="flex items-center gap-6 text-sm font-medium text-slate-300">
          <Link to="/" className="flex items-center gap-1.5 hover:text-white transition">
            <LayoutDashboard size={16} /> Dashboard
          </Link>
          <Link to="/upload" className="flex items-center gap-1.5 hover:text-white transition">
            <Upload size={16} /> Upload PDF/CSV
          </Link>
          <Link to="/risk" className="flex items-center gap-1.5 hover:text-white transition">
            <ShieldAlert size={16} /> Risk Profile
          </Link>
          <Link to="/advisory" className="flex items-center gap-1.5 hover:text-white transition">
            <TrendingUp size={16} /> Advisory
          </Link>
          <Link to="/knowledge" className="flex items-center gap-1.5 hover:text-white transition">
            <BookOpen size={16} /> Knowledge Base
          </Link>

          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-red-400 hover:text-red-300 transition ml-4"
          >
            <LogOut size={16} /> Logout
          </button>
        </div>
      )}
    </nav>
  );
}