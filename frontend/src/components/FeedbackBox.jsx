// src/components/FeedbackBox.jsx
import { useEffect, useState } from "react";
import { getFeedback, submitFeedback } from "../api";
import FeedbackModal from "./FeedbackModal";

export default function FeedbackBox({ jobId }) {
  const [saved, setSaved] = useState(null);
  const [loading, setLoading] = useState(true);
  const [openKind, setOpenKind] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [modalError, setModalError] = useState("");
  const [boxError, setBoxError] = useState("");

  // Load the saved reply when the box appears.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getFeedback(jobId)
      .then((reply) => {
        if (!cancelled) setSaved(reply);
      })
      .catch((err) => {
        if (!cancelled) setBoxError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  function openPopup(kind) {
    if (saved || loading) return;
    setModalError("");
    setOpenKind(kind);
  }

  function closePopup() {
    if (submitting) return;
    setOpenKind(null);
    setModalError("");
  }

  async function handleSubmit(message) {
    setSubmitting(true);
    setModalError("");
    try {
      const reply = await submitFeedback(jobId, openKind, message);
      setSaved(reply);
      setBoxError("");
      setOpenKind(null);
    } catch (err) {
      if (err.status === 409) {
        // The server already has a reply, or the report is not finished.
        // Re-read the server, so the box shows what is actually saved.
        const reply = await getFeedback(jobId).catch(() => null);
        setSaved(reply);
        setOpenKind(null);
        setBoxError(
          reply ? "This report already has your feedback." : err.message
        );
      } else {
        // Keep the pop-up open so the user can retry.
        setModalError(err.message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  const chosen = saved?.kind;

  return (
    <section className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-5">
      <p className="mb-3 text-sm font-medium text-slate-700">
        Was this report helpful?
      </p>

      {loading ? (
        <p className="text-sm text-slate-500">Loading...</p>
      ) : (
        <div className="flex gap-3">
          <FeedbackPart
            icon="👍"
            label="Thumbs up"
            kind="up"
            chosen={chosen === "up"}
            locked={Boolean(saved)}
            onClick={openPopup}
          />
          <FeedbackPart
            icon="👎"
            label="Thumbs down"
            kind="down"
            chosen={chosen === "down"}
            locked={Boolean(saved)}
            onClick={openPopup}
          />
        </div>
      )}

      {/* {saved && (
        <p className="mt-3 whitespace-pre-line text-sm text-slate-700">
          <span className="font-medium">Your reply:</span> {saved.message}
        </p>
      )} */}

      {boxError && <p className="mt-3 text-sm text-red-600">{boxError}</p>}

      {openKind && (
        <FeedbackModal
          kind={openKind}
          onSubmit={handleSubmit}
          onCancel={closePopup}
          submitting={submitting}
          error={modalError}
        />
      )}
    </section>
  );
}

function FeedbackPart({ icon, label, kind, chosen, locked, onClick }) {
  let tone = "border-slate-300 bg-white text-slate-700 hover:bg-slate-100";
  if (chosen) {
    tone = "border-blue-600 bg-blue-600 text-white";
  } else if (locked) {
    tone = "border-slate-200 bg-slate-100 text-slate-400";
  }

  return (
    <button
      type="button"
      onClick={() => onClick(kind)}
      disabled={locked}
      className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-4 py-3 text-sm font-medium transition disabled:cursor-not-allowed ${tone}`}
    >
      <span aria-hidden="true">{icon}</span>
      {label}
    </button>
  );
}