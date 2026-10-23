// src/components/SourceText.jsx
import { useState } from "react";

export default function SourceText({ scraped }) {
  const [open, setOpen] = useState(false);

  if (!scraped || scraped.length === 0) return null;

  return (
    <section className="mt-10 border-t border-slate-200 pt-6">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="text-sm font-medium text-blue-600 hover:underline"
      >
        {open ? "Hide source text" : "Show source text"}
      </button>

      {open && (
        <div className="mt-4 space-y-4">
          {scraped.map((item) => (
            <div key={item.url} className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-2 flex items-center justify-between gap-3">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="truncate text-sm text-blue-600 hover:underline"
                >
                  {item.url}
                </a>
                <span
                  className={
                    item.ok
                      ? "shrink-0 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700"
                      : "shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500"
                  }
                >
                  {item.ok ? "Used" : "Skipped"}
                </span>
              </div>
              <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap text-xs leading-5 text-slate-600">
                {item.text}
              </pre>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}