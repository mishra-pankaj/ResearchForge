// src/pages/History.jsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listResearch, deleteResearch } from "../api";
import ErrorMessage from "../components/ErrorMessage";

const PAGE_SIZE = 20;

export default function History() {
  const [jobs, setJobs] = useState([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        // Ask for one extra row to know whether another page exists.
        const rows = await listResearch({ limit: PAGE_SIZE + 1, offset });
        if (cancelled) return;
        setHasMore(rows.length > PAGE_SIZE);
        setJobs(rows.slice(0, PAGE_SIZE));
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [offset]);

  async function handleDelete(job) {
    const confirmed = window.confirm(
      `Delete this research?\n\n"${job.topic}"\n\nThis cannot be undone.`
    );
    if (!confirmed) return;

    setError("");
    setNotice("");
    try {
      await deleteResearch(job.id);
      setJobs((current) => current.filter((item) => item.id !== job.id));
      setNotice("Research deleted.");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <header className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">History</h1>
        <Link to="/" className="text-sm font-medium text-blue-600 hover:underline">
          New research
        </Link>
      </header>

      <div className="space-y-3">
        <ErrorMessage message={error} />
        {notice && (
          <div className="rounded-lg border border-green-300 bg-green-50 px-4 py-3 text-sm text-green-700">
            {notice}
          </div>
        )}
      </div>

      {loading && <p className="mt-6 text-slate-500">Loading...</p>}

      {!loading && jobs.length === 0 && !error && (
        <p className="mt-6 text-slate-500">
          No finished research yet. Start one from the home page.
        </p>
      )}

      {!loading && jobs.length > 0 && (
        <ul className="mt-6 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white">
          {jobs.map((job) => (
            <HistoryRow key={job.id} job={job} onDelete={handleDelete} />
          ))}
        </ul>
      )}

      {!loading && (offset > 0 || hasMore) && (
        <div className="mt-6 flex items-center justify-between">
          <button
            type="button"
            onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
            disabled={offset === 0}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-slate-500">
            Showing {offset + 1}–{offset + jobs.length}
          </span>
          <button
            type="button"
            onClick={() => setOffset((value) => value + PAGE_SIZE)}
            disabled={!hasMore}
            className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function HistoryRow({ job, onDelete }) {
  const created = new Date(job.created_at).toLocaleString();
  const isFailed = job.status === "failed";

  return (
    <li className="flex items-center justify-between gap-4 px-4 py-4">
      <div className="min-w-0">
        <Link
          to={`/research/${job.id}`}
          className="block truncate font-medium text-slate-800 hover:text-blue-600"
        >
          {job.topic}
        </Link>
        <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
          <span
            className={
              isFailed
                ? "rounded-full bg-red-100 px-2 py-0.5 font-medium text-red-700"
                : "rounded-full bg-green-100 px-2 py-0.5 font-medium text-green-700"
            }
          >
            {isFailed ? "Failed" : "Done"}
          </span>
          <span>{created}</span>
        </div>
      </div>

      <button
        type="button"
        onClick={() => onDelete(job)}
        className="shrink-0 rounded-lg border border-red-200 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50"
      >
        Delete
      </button>
    </li>
  );
}