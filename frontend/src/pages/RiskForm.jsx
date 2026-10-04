import React, { useState } from 'react';
import API from '../lib/api';

export default function RiskForm() {
  const [formData, setFormData] = useState({
    age: 25,
    monthly_income: 75000,
    emi_amount: 12000,
    dependents: 1,
    savings: 250000,
    horizon_years: 5,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await API.post('/risk/evaluate', formData);
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Risk Assessment Profile</h1>

      <form onSubmit={handleSubmit} className="bg-slate-800 p-6 rounded-xl border border-slate-700 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-slate-400">Age</label>
          <input
            type="number"
            value={formData.age}
            onChange={(e) => setFormData({ ...formData, age: Number(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white mt-1"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400">Monthly Income (₹)</label>
          <input
            type="number"
            value={formData.monthly_income}
            onChange={(e) => setFormData({ ...formData, monthly_income: Number(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white mt-1"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400">Monthly EMI Obligations (₹)</label>
          <input
            type="number"
            value={formData.emi_amount}
            onChange={(e) => setFormData({ ...formData, emi_amount: Number(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white mt-1"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400">Dependents</label>
          <input
            type="number"
            value={formData.dependents}
            onChange={(e) => setFormData({ ...formData, dependents: Number(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white mt-1"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400">Total Savings (₹)</label>
          <input
            type="number"
            value={formData.savings}
            onChange={(e) => setFormData({ ...formData, savings: Number(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white mt-1"
          />
        </div>

        <div>
          <label className="text-xs text-slate-400">Investment Horizon (Years)</label>
          <input
            type="number"
            value={formData.horizon_years}
            onChange={(e) => setFormData({ ...formData, horizon_years: Number(e.target.value) })}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white mt-1"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="md:col-span-2 bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg mt-2"
        >
          {loading ? 'Evaluating Risk Profile...' : 'Calculate Risk Profile'}
        </button>
      </form>

      {result && (
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold text-emerald-400">{result.category} Profile</h2>
            <span className="bg-blue-600/30 text-blue-400 text-sm px-3 py-1 rounded-full font-semibold">
              Score: {result.risk_score}/100
            </span>
          </div>
          <ul className="list-disc pl-5 text-sm text-slate-300 space-y-1">
            {result.factors.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}