import React, { useEffect, useState } from 'react';
import API from '../lib/api';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Quick Expense State
  const [desc, setDesc] = useState('');
  const [amount, setAmount] = useState('');
  const [adding, setAdding] = useState(false);

  const fetchDashboard = () => {
    setLoading(true);
    API.get('/dashboard/summary')
      .then((res) => setData(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const handleAddQuickExpense = async (e) => {
    e.preventDefault();
    if (!desc || !amount) return;

    setAdding(true);
    try {
      await API.post('/transactions/add', {
        date: new Date().toISOString().split('T')[0],
        description: desc,
        amount: parseFloat(amount)
      });
      setDesc('');
      setAmount('');
      fetchDashboard();
    } catch (err) {
      console.error('Failed to add expense:', err);
    } finally {
      setAdding(false);
    }
  };

  if (loading && !data) return <div className="p-8 text-center text-slate-400">Loading Dashboard...</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Financial Dashboard</h1>
        <button 
          onClick={fetchDashboard}
          className="bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700 px-3 py-1.5 rounded-lg"
        >
          🔄 Refresh
        </button>
      </div>

      {/* Quick Add Expense Bar */}
      <form onSubmit={handleAddQuickExpense} className="bg-slate-800 p-4 rounded-xl border border-slate-700 flex flex-col md:flex-row gap-3 items-center">
        <span className="text-sm font-semibold text-slate-300 whitespace-nowrap">⚡ Add Quick Expense:</span>
        <input
          type="text"
          placeholder="Description (e.g., Swiggy, Uber, Electricity)"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        />
        <input
          type="number"
          placeholder="Amount (₹)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-32 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={adding || !desc || !amount}
          className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded-lg text-sm disabled:opacity-50 whitespace-nowrap"
        >
          {adding ? 'Classifying...' : '+ Add Expense'}
        </button>
      </form>

      {/* Summary Cards */}
      {data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <p className="text-slate-400 text-sm">Total Spend</p>
              <p className="text-3xl font-extrabold text-white mt-1">₹{data.total_spend}</p>
            </div>
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <p className="text-slate-400 text-sm">Potential Monthly Savings</p>
              <p className="text-3xl font-extrabold text-emerald-400 mt-1">₹{data.potential_savings}</p>
              <p className="text-xs text-slate-400 mt-1">{data.avoidable_percentage}% of total spend is avoidable</p>
            </div>
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <p className="text-slate-400 text-sm">Total Transactions</p>
              <p className="text-3xl font-extrabold text-blue-400 mt-1">{data.total_transactions}</p>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 h-80">
              <h2 className="text-lg font-semibold mb-4">Category Breakdown</h2>
              <ResponsiveContainer width="100%" height="80%">
                <PieChart>
                  <Pie data={data.category_breakdown} dataKey="amount" nameKey="category" cx="50%" cy="50%" outerRadius={80} label>
                    {data.category_breakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 h-80">
              <h2 className="text-lg font-semibold mb-4">Monthly Spending Trend</h2>
              <ResponsiveContainer width="100%" height="80%">
                <BarChart data={data.monthly_trend}>
                  <XAxis dataKey="month" stroke="#94A3B8" />
                  <YAxis stroke="#94A3B8" />
                  <Tooltip />
                  <Bar dataKey="amount" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Expenses History Table */}
          <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
            <h2 className="text-lg font-semibold mb-4">Recent Expense History</h2>
            {data.recent_transactions && data.recent_transactions.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="text-xs uppercase bg-slate-900/50 text-slate-400 border-b border-slate-700">
                    <tr>
                      <th className="p-3">Date</th>
                      <th className="p-3">Description</th>
                      <th className="p-3">Category</th>
                      <th className="p-3">Type</th>
                      <th className="p-3 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {data.recent_transactions.map((tx) => (
                      <tr key={tx.id} className="hover:bg-slate-700/30 transition">
                        <td className="p-3 text-slate-400 font-mono text-xs">{tx.date}</td>
                        <td className="p-3 font-medium text-white">{tx.description}</td>
                        <td className="p-3">
                          <span className="bg-slate-700 text-slate-200 px-2 py-1 rounded text-xs">
                            {tx.category}
                          </span>
                        </td>
                        <td className="p-3">
                          {tx.is_avoidable ? (
                            <span className="bg-amber-900/40 text-amber-300 border border-amber-700/50 px-2 py-0.5 rounded text-xs">
                              Avoidable
                            </span>
                          ) : (
                            <span className="bg-emerald-900/40 text-emerald-300 border border-emerald-700/50 px-2 py-0.5 rounded text-xs">
                              Essential
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-right font-bold text-white">₹{tx.amount}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-slate-500 text-xs italic">No transactions added yet.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}