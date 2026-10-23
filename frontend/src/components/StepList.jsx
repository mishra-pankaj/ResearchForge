// src/components/StepList.jsx
const STEPS = [
  { key: "search", label: "Searching the web" },
  { key: "scrape", label: "Reading sources" },
  { key: "write", label: "Writing the report" },
  { key: "critique", label: "Reviewing the report" },
];

export default function StepList({ currentStep, status }) {
  const currentIndex = STEPS.findIndex((step) => step.key === currentStep);

  return (
    <ol className="space-y-3">
      {STEPS.map((step, index) => {
        let state = "waiting";
        if (status === "done") {
          state = "complete";
        } else if (index < currentIndex) {
          state = "complete";
        } else if (index === currentIndex) {
          state = "active";
        }

        return (
          <li key={step.key} className="flex items-center gap-3">
            <StepDot state={state} />
            <span
              className={
                state === "active"
                  ? "font-medium text-blue-700"
                  : state === "complete"
                    ? "text-slate-700"
                    : "text-slate-400"
              }
            >
              {step.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function StepDot({ state }) {
  if (state === "complete") {
    return (
      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-green-500 text-xs font-bold text-white">
        ✓
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className="flex h-6 w-6 items-center justify-center">
        <span className="h-4 w-4 animate-pulse rounded-full bg-blue-600" />
      </span>
    );
  }
  return <span className="h-6 w-6 rounded-full border-2 border-slate-300" />;
}