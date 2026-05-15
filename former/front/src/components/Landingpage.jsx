import { useState, useEffect, useRef } from "react";
import "./LandingPage.css";

const STEPS = [
  {
    num: "01",
    title: "Paste a form URL",
    body: "Any university portal, enrollment page, or application form. If it loads in a browser, former can fill it.",
  },
  {
    num: "02",
    title: "Set the persona",
    body: "Tune age profile, tone, formality, risk appetite. The LLM writes like a real applicant — not a robot.",
  },
  {
    num: "03",
    title: "Trigger and forget",
    body: "former fills and submits the form on your behalf. Track progress in real-time. Go touch grass.",
  },
];

const FEATURES = [
  { icon: "⚡", title: "Fast", body: "What takes you 40 minutes takes former 90 seconds." },
  { icon: "🎭", title: "Realistic", body: "Multi-axis personality tuning makes outputs indistinguishable from human answers." },
  { icon: "🔁", title: "Repeatable", body: "Trigger dozens of runs with randomised intervals — no spam patterns." },
  { icon: "🔒", title: "Private", body: "Runs in your own infrastructure. No third party ever sees your data." },
];

const FAQS = [
  { q: "Does it work on any form?", a: "Most standard HTML forms — university portals, Google Forms, Typeform, custom enrollment pages. Highly exotic single-page apps may need a heads-up." },
  { q: "Will my answers look human?", a: "That's the whole point. The personality system controls vocabulary, tone, verbosity and political framing so every run reads differently." },
  { q: "Can I run the same form multiple times?", a: "Yes. Set executions to however many you need, add an interval and jitter, and former spreads them out naturally." },
  { q: "Do I need to set up anything?", a: "Just create a free account. former runs on our hosted infrastructure — no local setup, no CLI, no config files." },
];


function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`lp-faq__item${open ? " lp-faq__item--open" : ""}`}>
      <button className="lp-faq__q" onClick={() => setOpen((v) => !v)}>
        <span>{q}</span>
        <span className="lp-faq__arrow">{open ? "−" : "+"}</span>
      </button>
      {open && <p className="lp-faq__a">{a}</p>}
    </div>
  );
}

export default function LandingPage({ onGoToApp }) {
  const heroRef = useRef(null);

  useEffect(() => {
    const els = document.querySelectorAll(".lp-reveal");
    const obs = new IntersectionObserver(
      (entries) => entries.forEach((e) => { if (e.isIntersecting) e.target.classList.add("lp-reveal--in"); }),
      { threshold: 0.12 }
    );
    els.forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  return (
    <div className="lp">

      {/* Nav */}
      <nav className="lp-nav">
        <span className="lp-nav__logo">former</span>
        <div className="lp-nav__right">
          <button className="lp-nav__login" onClick={onGoToApp}>Sign in</button>
          <button className="lp-nav__cta" onClick={onGoToApp}>
            Sign up free
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="lp-hero" ref={heroRef}>
        <div className="lp-hero__eyebrow">LLM-powered form filling</div>
        <h1 className="lp-hero__h1">
          Stop filling<br />
          forms<br />
          <em>manually.</em>
        </h1>
        <p className="lp-hero__sub">
          former fills university application and enrollment forms for you —
          fast, realistic, and tuned to sound like an actual human.
          Not a bot. Not obviously AI. Just done.
        </p>
        <div className="lp-hero__actions">
          <button
            className="lp-btn lp-btn--primary"
            onClick={onGoToApp}
          >
            Get started free
          </button>
          <button className="lp-btn lp-btn--ghost" onClick={onGoToApp}>
            Sign in →
          </button>
        </div>

        {/* Floating stat pills */}
        <div className="lp-hero__pills">
          <span className="lp-pill">40 min → 90 sec</span>
          <span className="lp-pill">5 personality axes</span>
          <span className="lp-pill">Any HTML form</span>
        </div>
      </section>

      {/* Problem strip */}
      <section className="lp-problem lp-reveal">
        <div className="lp-problem__inner">
          <p className="lp-problem__line lp-problem__line--cross">Spending Sunday afternoon on an enrollment form that asks for the same info for the 12th time.</p>
          <p className="lp-problem__line lp-problem__line--check">Pasting a URL, hitting trigger, and closing your laptop.</p>
        </div>
      </section>

      {/* How it works */}
      <section className="lp-section lp-reveal">
        <div className="lp-section__inner">
          <div className="lp-section__header">
            <span className="lp-label">How it works</span>
            <h2 className="lp-section__h2">Three steps.<br />Zero Sunday afternoons lost.</h2>
          </div>
          <div className="lp-steps">
            {STEPS.map((s) => (
              <div className="lp-step" key={s.num}>
                <span className="lp-step__num">{s.num}</span>
                <h3 className="lp-step__title">{s.title}</h3>
                <p className="lp-step__body">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="lp-section lp-section--alt lp-reveal">
        <div className="lp-section__inner">
          <div className="lp-section__header">
            <span className="lp-label">Why former</span>
            <h2 className="lp-section__h2">Built to actually work.</h2>
          </div>
          <div className="lp-features">
            {FEATURES.map((f) => (
              <div className="lp-feature" key={f.title}>
                <span className="lp-feature__icon">{f.icon}</span>
                <h3 className="lp-feature__title">{f.title}</h3>
                <p className="lp-feature__body">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Personality callout */}
      <section className="lp-section lp-reveal">
        <div className="lp-section__inner lp-personality-callout">
          <div className="lp-personality-callout__text">
            <span className="lp-label">Personality system</span>
            <h2 className="lp-section__h2">Sounds like you.<br />Or whoever you need.</h2>
            <p className="lp-personality-callout__body">
              Tune five independent axes — age profile, political leaning, risk tolerance,
              communication style, and formality — and the LLM writes answers
              that match. Same form, ten different personas, ten different outputs.
            </p>
          </div>
          <div className="lp-personality-callout__axes">
            {[
              { label: "Age profile", left: "Young", right: "Senior", pct: 30 },
              { label: "Tone", left: "Progressive", right: "Conservative", pct: 50 },
              { label: "Risk", left: "Cautious", right: "Bold", pct: 70 },
              { label: "Verbosity", left: "Terse", right: "Verbose", pct: 40 },
              { label: "Formality", left: "Casual", right: "Formal", pct: 65 },
            ].map((ax) => (
              <div className="lp-axis-preview" key={ax.label}>
                <div className="lp-axis-preview__header">
                  <span className="lp-axis-preview__label">{ax.label}</span>
                  <div className="lp-axis-preview__ends">
                    <span>{ax.left}</span>
                    <span>{ax.right}</span>
                  </div>
                </div>
                <div className="lp-axis-preview__track">
                  <div className="lp-axis-preview__fill" style={{ width: `${ax.pct}%` }} />
                  <div className="lp-axis-preview__dot" style={{ left: `calc(${ax.pct}% - 6px)` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="lp-section lp-section--alt lp-reveal">
        <div className="lp-section__inner lp-section__inner--narrow">
          <div className="lp-section__header">
            <span className="lp-label">FAQ</span>
            <h2 className="lp-section__h2">Good questions.</h2>
          </div>
          <div className="lp-faq">
            {FAQS.map((f) => <FaqItem key={f.q} {...f} />)}
          </div>
        </div>
      </section>

      {/* Signup CTA */}
      <section className="lp-waitlist lp-reveal" id="signup">
        <div className="lp-waitlist__inner">
          <span className="lp-label lp-label--light">Free to use</span>
          <h2 className="lp-waitlist__h2">Ready to reclaim your Sundays?</h2>
          <p className="lp-waitlist__sub">
            Create an account and start filling forms in under two minutes.
          </p>
          <button className="lp-waitlist__btn lp-waitlist__btn--large" onClick={onGoToApp}>
            Create free account →
          </button>
          <p className="lp-waitlist__fine">Already have an account? <button className="lp-waitlist__signin" onClick={onGoToApp}>Sign in</button></p>
        </div>
      </section>

      {/* Footer */}
      <footer className="lp-footer">
        <span className="lp-nav__logo">former</span>
        <span className="lp-footer__copy">LLM-powered form filling for students</span>
      </footer>
    </div>
  );
}