import { useState } from "react";
import { api } from "../api/client";
import { formatBrowserDateTime, formatExpectedFillEnd } from "../hooks/runsUtils";

const DEFAULT_DAG_ID = import.meta.env.VITE_DEFAULT_DAG_ID ?? "form_filler_plan";

const PACE_OPTIONS = {
  slow: { label: "Slow", intervalMinutes: 60, description: "1/hour" },
  intermediate: { label: "Intermediate", intervalMinutes: 10, description: "6/hour" },
  fast: { label: "Fast", intervalMinutes: 5, description: "12/hour" },
};

const AXES = [
  {
    id: "age_profile",
    label: "Age profile",
    left: { value: "young_adult", label: "Young adult" },
    right: { value: "senior", label: "Senior" },
    hint: "Shapes vocabulary, tech-familiarity and cultural references in answers.",
    steps: [
      { value: "young_adult",  label: "Young adult",  traits: ["Informal phrasing", "Tech-native", "Current slang", "Short sentences"] },
      { value: "early_career", label: "Early career", traits: ["Motivated tone", "Learning-oriented", "Eager", "Direct"] },
      { value: "mid_career",   label: "Mid-career",   traits: ["Balanced register", "Experience-aware", "Measured", "Professional"] },
      { value: "experienced",  label: "Experienced",  traits: ["Authoritative", "Detail-conscious", "Structured", "Deliberate"] },
      { value: "senior",       label: "Senior",       traits: ["Formal phrasing", "Traditional", "Methodical", "Long-form"] },
    ],
  },
  {
    id: "political_leaning",
    label: "Political leaning",
    left: { value: "progressive", label: "Progressive" },
    right: { value: "conservative", label: "Conservative" },
    hint: "Influences framing on values-adjacent and societal questions.",
    steps: [
      { value: "progressive",  label: "Progressive",  traits: ["Inclusive language", "Reform-oriented", "Equity-focused", "Optimistic about change"] },
      { value: "centre_left",  label: "Centre-left",  traits: ["Pragmatic reform", "Evidence-based", "Collaborative", "Moderate"] },
      { value: "centrist",     label: "Centrist",     traits: ["Balanced framing", "Neutral tone", "Compromise-seeking", "Non-partisan"] },
      { value: "centre_right", label: "Centre-right", traits: ["Stability-oriented", "Institutional trust", "Merit-based", "Cautious change"] },
      { value: "conservative", label: "Conservative", traits: ["Traditional values", "Continuity-focused", "Formal register", "Sceptical of novelty"] },
    ],
  },
  {
    id: "risk_tolerance",
    label: "Risk tolerance",
    left: { value: "risk_averse", label: "Risk-averse" },
    right: { value: "risk_seeking", label: "Risk-seeking" },
    hint: "Affects self-presentation: safe and qualified vs. bold and ambitious.",
    steps: [
      { value: "risk_averse",  label: "Risk-averse",  traits: ["Hedged claims", "Caveats added", "Understatement", "Avoids bold promises"] },
      { value: "cautious",     label: "Cautious",     traits: ["Measured confidence", "Realistic scope", "Accountable tone", "Careful phrasing"] },
      { value: "moderate",     label: "Moderate",     traits: ["Confident but grounded", "Clear claims", "Balanced ambition", "Achievable goals"] },
      { value: "confident",    label: "Confident",    traits: ["Strong assertions", "Ambitious framing", "Proactive stance", "Results-oriented"] },
      { value: "risk_seeking", label: "Risk-seeking", traits: ["Bold claims", "Entrepreneurial tone", "Visionary", "High-impact language"] },
    ],
  },
  {
    id: "verbosity",
    label: "Communication style",
    left: { value: "terse", label: "Terse" },
    right: { value: "verbose", label: "Verbose" },
    hint: "Controls answer length and elaboration depth.",
    steps: [
      { value: "terse",    label: "Terse",    traits: ["1–2 sentences", "No elaboration", "Bullet-like", "Minimal context"] },
      { value: "concise",  label: "Concise",  traits: ["3–4 sentences", "Key points only", "Tight paragraphs", "No filler"] },
      { value: "balanced", label: "Balanced", traits: ["Full paragraph", "Context included", "Examples where useful", "Readable"] },
      { value: "detailed", label: "Detailed", traits: ["Multi-paragraph", "Thorough coverage", "Anticipates questions", "Rich context"] },
      { value: "verbose",  label: "Verbose",  traits: ["Extended prose", "All angles covered", "Heavy elaboration", "Academic density"] },
    ],
  },
  {
    id: "formality",
    label: "Formality",
    left: { value: "casual", label: "Casual" },
    right: { value: "formal", label: "Formal" },
    hint: "Sets register and tone across all written fields.",
    steps: [
      { value: "casual",       label: "Casual",       traits: ["Conversational", "Contractions used", "First-name feel", "Relaxed flow"] },
      { value: "semi_casual",  label: "Semi-casual",  traits: ["Friendly but clear", "Light professionalism", "Approachable", "Warm"] },
      { value: "professional", label: "Professional", traits: ["Polished phrasing", "No contractions", "Business-appropriate", "Confident"] },
      { value: "semi_formal",  label: "Semi-formal",  traits: ["Structured sentences", "Precise vocabulary", "Reserved tone", "Document-ready"] },
      { value: "formal",       label: "Formal",       traits: ["Academic register", "Third-person capable", "Institutional tone", "Zero informality"] },
    ],
  },
];

function PersonalityAxis({ axis, value, onChange }) {
  const currentStep = axis.steps[value];
  return (
    <div className="axis">
      <div className="axis__header">
        <span className="axis__label">{axis.label}</span>
        <span className="axis__hint">{axis.hint}</span>
      </div>
      <div className="axis__scale">
        <div className="axis__track">
          <div className="axis__fill" style={{ width: `${(value / (axis.steps.length - 1)) * 100}%` }} />
          {axis.steps.map((step, i) => (
            <button
              key={step.value}
              type="button"
              className={`axis__dot${value === i ? " axis__dot--active" : ""}`}
              onClick={() => onChange(i)}
              aria-label={step.label}
              title={step.label}
            />
          ))}
        </div>
        <div className="axis__end-labels">
          <span>{axis.left.label}</span>
          <span>{axis.right.label}</span>
        </div>
      </div>
      <div className="axis__card">
        <span className="axis__card-name">{currentStep.label}</span>
        <div className="axis__traits">
          {currentStep.traits.map((t) => (
            <span key={t} className="trait-tag">{t}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function randomRunId(name) {
  const slug = name.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").slice(0, 24);
  return `${slug}__${Date.now().toString(36)}`;
}

export default function TriggerForm({ onSuccess, fillsRemaining, onTopUp }) {
  const [runName, setRunName]             = useState("");
  const [formUrl, setFormUrl]             = useState("");
  const [numExecutions, setNumExecutions] = useState(1);
  const [pace, setPace]                   = useState("intermediate");
  const [loading, setLoading]             = useState(false);
  const [error, setError]                 = useState(null);
  const [axisValues, setAxisValues]       = useState(AXES.map(() => 2));

  const hasUrl  = formUrl.trim().length > 0;
  const after   = fillsRemaining !== null ? fillsRemaining - numExecutions : null;
  const isLow   = after !== null && after < 10 && after >= 0;
  const isEmpty = after !== null && after < 0;
  const baseInterval = PACE_OPTIONS[pace].intervalMinutes;
  const scheduleStart = Date.now();
  const expectedFillStart = formatBrowserDateTime(scheduleStart);
  const expectedFillEnd = formatExpectedFillEnd(scheduleStart, numExecutions, baseInterval);

  function setAxis(axisIdx, stepIdx) {
    setAxisValues((prev) => prev.map((v, i) => (i === axisIdx ? stepIdx : v)));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!runName.trim()) return;
    setError(null);
    setLoading(true);
    try {
      const personality = Object.fromEntries(
        AXES.map((axis, i) => [axis.id, axis.steps[axisValues[i]].value])
      );
      const payload = {
        form_url: formUrl,
        dag_id: DEFAULT_DAG_ID,
        run_id: randomRunId(runName),
        num_executions: numExecutions,
        base_interval_minutes: Number(baseInterval.toFixed(4)),
        conf_run_name: runName.trim(),
        run_name: runName.trim(),
        conf_personality: personality,
      };
      const data = await api.trigger(payload);
      setRunName("");
      setFormUrl("");
      onSuccess?.(data, runName.trim());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="trigger-form" onSubmit={handleSubmit} noValidate>

      {/* Row 1: name + URL */}
      <div className="trigger-form__section">
        <div className="trigger-form__inline">
          <div className="field field--run-name">
          <label htmlFor="run_name">
            Run name <span className="required-mark">*</span>
          </label>
          <input
            id="run_name"
            type="text"
            placeholder="Q3 application form"
            value={runName}
            onChange={(e) => setRunName(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div className="field field--grow field--form-url">
          <label htmlFor="form_url">
            Form URL <span className="required-mark">*</span>
          </label>
          <input
            id="form_url"
            type="url"
            placeholder="https://forms.example.edu/apply"
            value={formUrl}
            onChange={(e) => setFormUrl(e.target.value)}
            required
          />
        </div>

        <div className="field field--runs">
          <label htmlFor="num_executions">Runs</label>
          <input
            id="num_executions"
            type="number"
            min={1}
            value={numExecutions}
            onChange={(e) => setNumExecutions(Math.max(1, Number(e.target.value) || 1))}
            className="input--narrow"
          />
        </div>

        <div className="field field--pace">
          <span className="field__label" id="pace-label">Pace</span>
          <div className="pace-options" role="group" aria-labelledby="pace-label">
            {Object.entries(PACE_OPTIONS).map(([value, option]) => (
              <button
                key={value}
                type="button"
                className={`pace-option${pace === value ? " pace-option--active" : ""}`}
                onClick={() => setPace(value)}
                aria-pressed={pace === value}
                title={option.description}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <button
          className="submit-btn"
          type="submit"
          disabled={loading || !runName.trim() || !formUrl.trim() || isEmpty}
        >
          {loading
            ? <span className="spinner" />
            : numExecutions > 1
            ? `Trigger ${numExecutions}`
            : "Trigger"}
        </button>
        </div>
      </div>

      {/* Planned schedule in the browser's local timezone */}
      <div className="schedule-preview" aria-live="polite">
        <div className="schedule-preview__item">
          <span className="schedule-preview__label">Starts</span>
          <strong>{expectedFillStart}</strong>
        </div>
        <span className="schedule-preview__arrow" aria-hidden="true">→</span>
        <div className="schedule-preview__item">
          <span className="schedule-preview__label">Planned end</span>
          <strong>{expectedFillEnd}</strong>
        </div>
        <span className="schedule-preview__hint">browser local time</span>
      </div>

      {/* Fills preview — always shown when billing is available */}
      {fillsRemaining !== null && (
        <div className={`fills-preview${isLow ? " fills-preview--low" : ""}${isEmpty ? " fills-preview--empty" : ""}`}>
          {isEmpty ? (
            <>
              <span className="fills-preview__text">Not enough fills.</span>
              <button type="button" className="fills-preview__topup" onClick={onTopUp}>
                Top up →
              </button>
            </>
          ) : (
            <>
              <span className="fills-preview__text">
                {fillsRemaining} fills remaining
                {numExecutions > 1 && (
                  <> → <strong>{after}</strong> after trigger</>
                )}
              </span>
              {isLow && (
                <button type="button" className="fills-preview__topup" onClick={onTopUp}>
                  Top up →
                </button>
              )}
            </>
          )}
        </div>
      )}

      {/* Personality — appears when URL is entered */}
      {hasUrl && (
        <div className="personality-panel">
          <div className="personality-panel__header">
            <span className="personality-panel__title">Agent personality</span>
            <span className="personality-panel__sub">
              Tune how the agent sounds when filling this form.
            </span>
          </div>
          <div className="advanced-fields advanced-fields--personality">
            {AXES.map((axis, i) => (
              <PersonalityAxis
                key={axis.id}
                axis={axis}
                value={axisValues[i]}
                onChange={(stepIdx) => setAxis(i, stepIdx)}
              />
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="banner banner--error">
          <span className="banner__label">Error</span>
          <span>{error}</span>
        </div>
      )}
    </form>
  );
}
