// src/pages/Home.jsx
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createResearch } from "../api";
import ErrorMessage from "../components/ErrorMessage";

const MIN_LENGTH = 3;
const MAX_LENGTH = 300;

export default function Home() {
  const [topic, setTopic] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const trimmed = topic.trim();
  const tooShort = trimmed.length < MIN_LENGTH;
  const tooLong = trimmed.length > MAX_LENGTH;

  async function handleSubmit(event) {
    event.preventDefault();
    if (tooShort || tooLong) return;

    setError("");
    setSubmitting(true);
    try {
      const job = await createResearch(trimmed);
      navigate(`/research/${job.id}`);
    } catch (err) {
      setError(err.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">Research Assistant</h1>
        <Link to="/history" className="text-sm font-medium text-blue-600 hover:underline">
          History
        </Link>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4">
        <label htmlFor="topic" className="block text-sm font-medium text-slate-700">
          What should we research?
        </label>
        <textarea
          id="topic"
          rows={3}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. impact of war on stock market"
          className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
        />

        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>
            {trimmed.length < MIN_LENGTH
              ? `At least ${MIN_LENGTH} characters`
              : tooLong
                ? `Maximum ${MAX_LENGTH} characters`
                : "Ready"}
          </span>
          <span>{trimmed.length} / {MAX_LENGTH}</span>
        </div>

        <button
          type="submit"
          disabled={tooShort || tooLong || submitting}
          className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {submitting ? "Starting research..." : "Start research"}
        </button>

        <ErrorMessage message={error} />
      </form>

      <p className="mt-6 text-sm text-slate-500">
        Research runs in the background and takes several minutes. Jobs run one at a time,
        so a new job may wait in the queue.
      </p>
    </div>
  );
}