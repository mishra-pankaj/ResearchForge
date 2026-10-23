// src/pages/ResearchPage.jsx
import ReportView from "../components/ReportView";
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getResearch } from "../api";
import StepList from "../components/StepList";
import ErrorMessage from "../components/ErrorMessage";

const POLL_MS = 10000;

export default function ResearchPage() {
  const { id } = useParams();
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let timer;
    let cancelled = false;

    async function load() {
      try {
        const data = await getResearch(id);
        if (cancelled) return;
        setJob(data);
        setError("");

        // Keep polling only while the job is still in progress.
        if (data.status === "queued" || data.status === "running") {
          timer = setTimeout(load, POLL_MS);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err.message);
        // Stop polling on a 404; retry on other errors.
        if (err.status !== 404) {
          timer = setTimeout(load, POLL_MS);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id]);

  if (error && !job) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-12">
        <ErrorMessage message={error} />
        <Link to="/" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Back to home
        </Link>
      </div>
    );
  }

  if (!job) {
    return <p className="p-8 text-slate-500">Loading...</p>;
  }

  if (job.status === "failed") {
    return <FailedView job={job} />;
  }

    if (job.status === "done") {
    return <ReportPage job={job} />;
  }

  return <ProgressView job={job} error={error} />;
}

function ProgressView({ job, error }) {
  const waitingInQueue = job.status === "queued";

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← New research
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-slate-800">{job.topic}</h1>

      <div className="mt-8 rounded-lg border border-slate-200 bg-white p-6">
        <p className="mb-6 text-sm text-slate-500">
          {waitingInQueue
            ? "Waiting for the worker. Jobs run one at a time, so this can take a while."
            : "Research is running. This usually takes several minutes."}
        </p>

        <StepList currentStep={job.current_step} status={job.status} />
      </div>

      <p className="mt-4 text-xs text-slate-400">Checking progress every 10 seconds.</p>

      <div className="mt-4">
        <ErrorMessage message={error} />
      </div>
    </div>
  );
}

function FailedView({ job }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← New research
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-slate-800">{job.topic}</h1>

      <div className="mt-8">
        <ErrorMessage message={`This research failed: ${job.error}`} />
      </div>

      <Link
        to="/"
        className="mt-6 inline-block rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700"
      >
        Start a new research
      </Link>
    </div>
  );
}

function ReportPage({ job }) {
  return (
    <div className="mx-auto max-w-3xl px-4 py-12">
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        ← New research
      </Link>

      <h1 className="mb-6 mt-4 text-3xl font-bold text-slate-800">{job.topic}</h1>

      <ReportView result={job} />
    </div>
  );
}