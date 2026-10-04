import React, { useState } from 'react';
import API from '../lib/api';

export default function Knowledge() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    try {
      const res = await API.post('/knowledge/ask', { question });
      setAnswer(res.data.answer);
      setSources(res.data.sources);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Knowledge Center & AI Assistant</h1>

      <form onSubmit={handleAsk} className="flex gap-3">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask FINMATE about FDs, SIPs, Capital Gains, or Crypto..."
          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-6 py-3 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Asking...' : 'Ask'}
        </button>
      </form>

      {answer && (
        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
          <h2 className="text-xl font-semibold text-blue-400">FINMATE Recommendation</h2>
          <div className="whitespace-pre-wrap text-slate-200 leading-relaxed">{answer}</div>

          {sources.length > 0 && (
            <div className="border-t border-slate-700 pt-3 text-xs text-slate-400">
              <p className="font-semibold mb-1">Grounded Knowledge Sources:</p>
              <ul className="list-disc pl-4 space-y-0.5">
                {sources.map((s, idx) => (
                  <li key={idx}>{s.title} ({s.category})</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}