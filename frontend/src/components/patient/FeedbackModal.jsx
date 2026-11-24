import React, { useState } from "react";
import Modal from "../common/Modal";
import StarRating from "../common/StarRating";
import { submitFeedback } from "../../utils/api";

const ASPECTS = [
  { key: "ratingDoctor", label: "Doctor" },
  { key: "ratingStaff", label: "Staff" },
  { key: "ratingWaiting", label: "Waiting time" },
  { key: "ratingCleanliness", label: "Cleanliness" },
  { key: "ratingBilling", label: "Billing" },
];

const inputStyle = {
  width: "100%",
  boxSizing: "border-box",
  padding: "10px 14px",
  border: "1.5px solid #cbd5e1",
  borderRadius: 10,
  fontSize: 14,
  fontFamily: "inherit",
  background: "#ffffff",
  color: "#0f172a",
  resize: "vertical",
};

/**
 * The feedback checkpoint (synopsis Fig 6.6): overall rating, five aspect
 * ratings, optional free text. Shown after the doctor marks a visit completed.
 */
export default function FeedbackModal({ appointment, status, onSubmitted, onClose }) {
  const [overall, setOverall] = useState(0);
  const [aspects, setAspects] = useState({});
  const [text, setText] = useState("");
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const needsConsent = !status.consentGiven;
  const maxLen = status.maxTextLength || 1000;
  const canSubmit = overall > 0 && (!needsConsent || consent) && !busy;

  const handleSubmit = async () => {
    setBusy(true);
    setError("");
    try {
      const res = await submitFeedback({
        appointmentId: appointment.appointmentId,
        overallRating: overall,
        ...aspects,
        freeText: text.trim(),
        consent: needsConsent ? consent : undefined,
      });
      setResult(res);
      onSubmitted(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  // ---------- Thank-you screen ----------
  if (result) {
    const granted = result.rewardStatus === "granted";
    return (
      <Modal title="Thank you" onClose={onClose} maxWidth={460}>
        <div style={{ textAlign: "center", padding: "8px 0 4px" }}>
          <div
            style={{
              width: 56, height: 56, borderRadius: "50%", margin: "0 auto 14px",
              background: granted ? "#ccfbf1" : "#f1f5f9", color: granted ? "#0f766e" : "#64748b",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, fontWeight: 800,
            }}
            aria-hidden="true"
          >
            {granted ? "✓" : "♥"}
          </div>
          <p style={{ margin: 0, fontSize: 15, color: "#0f172a", lineHeight: 1.5 }}>{result.message}</p>
          {granted && result.rewardCode && (
            <div
              style={{
                display: "inline-block", marginTop: 14, padding: "8px 16px", borderRadius: 10,
                background: "#f0fdfa", border: "1.5px dashed #0f766e", color: "#0f766e",
                fontWeight: 800, letterSpacing: 1, fontSize: 16,
              }}
            >
              {result.rewardCode}
            </div>
          )}
        </div>
        <button onClick={onClose} style={{ ...primaryBtn, width: "100%", marginTop: 22 }}>Done</button>
      </Modal>
    );
  }

  // ---------- Form ----------
  return (
    <Modal title="How was your visit?" onClose={onClose} maxWidth={560}>
      <p style={{ margin: "0 0 14px", fontSize: 13, color: "#475569" }}>
        {appointment.doctorName} · {appointment.specialty} · {appointment.date}
      </p>

      {status.offerText && (
        <div style={{ background: "#f0fdfa", border: "1px solid #99f6e4", color: "#115e59", padding: "10px 14px", borderRadius: 10, fontSize: 13, marginBottom: 18 }}>
          {status.offerText}
        </div>
      )}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 6 }}>
        <span style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>Overall</span>
        <StarRating value={overall} onChange={setOverall} label="Overall rating" size={34} />
      </div>

      <div style={{ fontWeight: 700, fontSize: 13, color: "#475569", margin: "18px 0 6px" }}>
        Rate each part of your visit (optional)
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {ASPECTS.map((a) => (
          <div key={a.key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "4px 0", borderBottom: "1px solid #f1f5f9" }}>
            <span style={{ fontSize: 14, color: "#334155" }}>{a.label}</span>
            <StarRating
              value={aspects[a.key] || 0}
              onChange={(v) => setAspects((prev) => ({ ...prev, [a.key]: v }))}
              label={`${a.label} rating`}
              size={22}
              clearable
            />
          </div>
        ))}
      </div>

      <label htmlFor="fb-text" style={{ display: "block", fontWeight: 700, fontSize: 13, color: "#475569", margin: "18px 0 6px" }}>
        Tell us more (optional)
      </label>
      <textarea
        id="fb-text"
        rows={4}
        maxLength={maxLen}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={"e.g. \u201CDoctor was great, but the waiting time was long and the clinic was dirty\u201D"}
        style={inputStyle}
      />
      <div style={{ textAlign: "right", fontSize: 11, color: "#94a3b8" }}>{text.length}/{maxLen}</div>

      {needsConsent && (
        <label style={{ display: "flex", gap: 10, alignItems: "flex-start", marginTop: 12, fontSize: 12.5, color: "#475569", lineHeight: 1.45, cursor: "pointer" }}>
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            style={{ marginTop: 3, accentColor: "#0f766e" }}
          />
          <span>
            I agree to take part in this research study on patient feedback. My answers are stored under an
            anonymous study ID (not my name) and used only for analysis. Taking part is voluntary.
          </span>
        </label>
      )}

      {error && (
        <div role="alert" style={{ marginTop: 12, background: "#fef2f2", border: "1px solid #fecaca", color: "#b91c1c", padding: "8px 12px", borderRadius: 8, fontSize: 13 }}>
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={!canSubmit}
        style={{ ...primaryBtn, width: "100%", marginTop: 18, opacity: canSubmit ? 1 : 0.5, cursor: canSubmit ? "pointer" : "not-allowed" }}
      >
        {busy ? "Submitting…" : "Submit feedback"}
      </button>
    </Modal>
  );
}

const primaryBtn = {
  background: "#0f766e",
  color: "#ffffff",
  border: "none",
  padding: "12px 20px",
  borderRadius: 10,
  fontWeight: 700,
  fontSize: 14,
  cursor: "pointer",
  fontFamily: "inherit",
};
