import React from "react";

/** Banner shown on the patient portal when a completed visit is waiting for feedback. */
export default function FeedbackPrompt({ pending, offerText, onOpen }) {
  if (!pending || pending.length === 0) return null;
  const first = pending[0];
  const extra = pending.length - 1;

  return (
    <div
      style={{
        display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, flexWrap: "wrap",
        background: "#f0fdfa", border: "1px solid #99f6e4", borderRadius: 14, padding: "14px 18px", marginBottom: 20,
      }}
    >
      <div>
        <div style={{ fontWeight: 800, fontSize: 15, color: "#115e59" }}>
          How was your visit with {first.doctorName}?
        </div>
        <div style={{ fontSize: 13, color: "#0f766e", marginTop: 2 }}>
          It takes about a minute.{offerText ? ` ${offerText}` : ""}
          {extra > 0 ? ` (${extra} more visit${extra > 1 ? "s" : ""} waiting)` : ""}
        </div>
      </div>
      <button
        onClick={() => onOpen(first)}
        style={{ background: "#0f766e", color: "#ffffff", border: "none", padding: "9px 18px", borderRadius: 10, fontWeight: 700, fontSize: 13, cursor: "pointer", fontFamily: "inherit" }}
      >
        Give feedback
      </button>
    </div>
  );
}
