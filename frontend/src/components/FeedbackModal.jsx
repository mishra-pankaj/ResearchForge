// src/components/FeedbackModal.jsx
import { useEffect, useRef, useState } from "react";

const MAX_LENGTH = 1000;

const TITLES = {
  up: "What did you like?",
  down: "What didn't you like?",
};

export default function FeedbackModal({ kind, onSubmit, onCancel, submitting = false, error = "" }) {
  const [message, setMessage] = useState("");
  const textRef = useRef(null);

  const trimmed = message.trim();
  const canSubmit = trimmed.length > 0 && !submitting;

  // Focus the text box when the pop-up opens.
  useEffect(() => {
    textRef.current?.focus();
  }, []);

  // Escape closes the pop-up without sending anything.
  useEffect(() => {
    function handleKey(event) {
      if (event.key === "Escape" && !submitting) onCancel();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [onCancel, submitting]);

  function handleSubmit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    onSubmit(trimmed);
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 px-4"
      onClick={() => {
        if (!submitting) onCancel();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="feedback-title"
        className="w-full max-w-md rounded-xl bg-white p-6 shadow-lg"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="feedback-title" className="mb-4 text-lg font-semibold text-slate-800">
          {TITLES[kind]}
        </h2>

        <form onSubmit={handleSubmit}>
          <textarea
            ref={textRef}
            rows={4}
            maxLength={MAX_LENGTH}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            disabled={submitting}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:bg-slate-50"
          />

          <div className="mt-1 text-right text-xs text-slate-500">
            {message.length} / {MAX_LENGTH}
          </div>

          {error && (
            <p className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}

          <div className="mt-5 flex justify-end gap-3">
            <button
              type="button"
              onClick={onCancel}
              disabled={submitting}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {submitting ? "Sending..." : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}