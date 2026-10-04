import React, { useState } from 'react';
import API from '../lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444'];

export default function Advisory() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchAdvice = async () => {
    setLoading(true);
    try {
      const res = await API.post('/advisory/recommend', {
        age: 26,
        monthly_income: 75000,
        emi_amount: 12000,
        dependents: 1,
        savings: 250000,
        horizon_years: 5,
      });
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Personalized Investment Advisory</h1>
        <button
          onClick={fetchAdvice}
          disabled={loading}
          className="bg-emerald-600 hover:bg-emerald-500 text-white font-medium px-5 py-2.5 rounded-lg"
        >
          {loading ? 'Generating AI Plan...' : 'Generate Plan'}
        </button>
      </div>

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Allocation Chart */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 h-80">
              <h2 className="text-lg font-semibold mb-2">Recommended Allocation</h2>
              <ResponsiveContainer width="100%" height="80%">
                <PieChart>
                  <Pie data={data.allocation} dataKey="percentage" nameKey="instrument" cx="50%" cy="50%" outerRadius={80} label>
                    {data.allocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Projections Chart */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 h-80">
              <h2 className="text-lg font-semibold mb-2">12-Month Projected Growth</h2>
              <ResponsiveContainer width="100%" height="80%">
                <LineChart data={data.projections}>
                  <XAxis dataKey="month" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip />
                  <Line type="monotone" dataKey="expected" stroke="#10B981" strokeWidth={2} name="Expected" />
                  <Line type="monotone" dataKey="optimistic" stroke="#3B82F6" strokeWidth={1} strokeDasharray="3 3" name="Optimistic" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* AI Explanation Card */}
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-3">
            <h3 className="text-lg font-bold text-blue-400">Why This Allocation?</h3>
            <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">{data.explanation}</p>
            {data.crypto_warning && <p className="text-amber-400 text-xs font-semibold">{data.crypto_warning}</p>}
            <p className="text-slate-500 text-xs italic">{data.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
}