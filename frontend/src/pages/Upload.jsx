import React, { useState } from 'react';
import API from '../lib/api';

export default function Upload() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setMessage(null);

    try {
      const res = await API.post('/transactions/upload-statement', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setMessage({ type: 'success', text: `Success: ${res.data.message}` });
    } catch (err) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Upload failed' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Upload Bank Statement (CSV)</h1>
      <form onSubmit={handleUpload} className="bg-slate-800 p-6 rounded-xl border border-slate-700 space-y-4">
        <input
          type="file"
          accept=".csv,.pdf"
          onChange={(e) => setFile(e.target.files[0])}
          className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer"
        />
        <button
          type="submit"
          disabled={loading || !file}
          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 rounded-lg disabled:opacity-50"
        >
          {loading ? 'Processing & Categorizing...' : 'Upload & Categorize'}
        </button>
      </form>

      {message && (
        <div className={`p-4 rounded-lg text-sm ${message.type === 'success' ? 'bg-emerald-900/50 text-emerald-300 border border-emerald-700' : 'bg-red-900/50 text-red-300 border border-red-700'}`}>
          {message.text}
        </div>
      )}
    </div>
  );
}