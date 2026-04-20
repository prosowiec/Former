const STAGES = ["pending", "running", "done"];

const STATE_MAP = {
  queued: { stage: "pending", failed: false },
  running: { stage: "running", failed: false },
  success: { stage: "done", failed: false },
  failed: { stage: "running", failed: true },
  unknown: { stage: "pending", failed: false },
};

const STAGE_LABELS = {
  pending: "Pending",
  running: "Filling form",
  done: "Done",
};

export default function RunStageIndicator({ state = "unknown" }) {
  const { stage, failed } = STATE_MAP[state] ?? STATE_MAP.unknown;
  const currentIndex = STAGES.indexOf(stage);

  return (
    <div className="stage-indicator">
      {STAGES.map((s, i) => {
        const isActive = i === currentIndex;
        const isDone = i < currentIndex || (s === "done" && stage === "done");
        const isFailed = failed && isActive;

        let cls = "stage-step";
        if (isFailed) cls += " stage-step--failed";
        else if (isDone) cls += " stage-step--done";
        else if (isActive) cls += " stage-step--active";

        return (
          <div className="stage-step-wrapper" key={s}>
            <div className={cls}>
              {isDone && !isFailed ? <CheckIcon /> : null}
              {isFailed ? <XIcon /> : null}
            </div>
            <span className="stage-step-label">{STAGE_LABELS[s]}</span>
            {i < STAGES.length - 1 && (
              <div className={`stage-connector${isDone ? " stage-connector--done" : ""}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function CheckIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <path d="M1.5 5l2.5 2.5 4.5-4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
      <path d="M2 2l6 6M8 2l-6 6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}