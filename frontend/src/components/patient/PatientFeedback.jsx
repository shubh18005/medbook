import React from "react";
import StatCard from "../common/StatCard";
import StarRating from "../common/StarRating";

const cardStyle = {
  background: "#ffffff",
  borderRadius: 16,
  padding: 20,
  border: "1px solid #e2e8f0",
  boxShadow: "0 4px 16px rgba(0,0,0,0.03)",
};

function rewardChip(item) {
  if (item.rewardStatus === "granted") {
    return item.rewardType === "discount"
      ? { text: `${item.rewardDiscountPercent}% off · ${item.rewardCode}`, bg: "#ecfdf5", color: "#047857", border: "#a7f3d0" }
      : { text: `+${item.rewardPoints} points`, bg: "#ecfdf5", color: "#047857", border: "#a7f3d0" };
  }
  if (item.rewardStatus === "withheld") {
    return { text: "Quality check not met", bg: "#fff7ed", color: "#c2410c", border: "#fed7aa" };
  }
  return null;
}

/** "Feedback" tab: visits waiting for feedback, past submissions, and (if on offer) rewards earned. */
export default function PatientFeedback({ status, onGiveFeedback }) {
  if (!status) {
    return <div style={{ ...cardStyle, color: "#64748b", textAlign: "center" }}>Feedback is not available right now.</div>;
  }

  const hasOffer = status.offer && status.offer !== "none";
  const showPoints = status.offer === "points" || status.offer === "gated" || status.totalPoints > 0;
  const showDiscounts = status.offer === "discount" || status.offer === "gated" || status.discounts.length > 0;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontWeight: 800, color: "#0f172a", fontSize: 24 }}>Your Feedback</h2>
        <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b" }}>
          Your feedback helps the clinic improve. Share it right after a visit while it is fresh.
        </p>
      </div>

      {hasOffer && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 24 }}>
          {showPoints && <StatCard icon="★" label="Points earned" value={status.totalPoints} color="#f59e0b" />}
          {showDiscounts && <StatCard icon="%" label="Discount codes" value={status.discounts.length} color="#0f766e" />}
          <StatCard icon="✎" label="Feedback given" value={status.history.length} color="#3b82f6" />
        </div>
      )}

      <h3 style={{ margin: "0 0 10px", fontSize: 16, fontWeight: 800, color: "#0f172a" }}>Waiting for your feedback</h3>
      {status.pending.length === 0 ? (
        <div style={{ ...cardStyle, color: "#64748b", fontSize: 14 }}>You're all caught up. Nothing is waiting.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {status.pending.map((p) => (
            <div key={p.appointmentId} style={{ ...cardStyle, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
              <div>
                <div style={{ fontWeight: 700, color: "#0f172a" }}>{p.doctorName}</div>
                <div style={{ fontSize: 13, color: "#64748b" }}>{p.specialty} · {p.date}</div>
              </div>
              <button
                onClick={() => onGiveFeedback(p)}
                style={{ background: "#0f766e", color: "#ffffff", border: "none", padding: "8px 16px", borderRadius: 10, fontWeight: 700, fontSize: 13, cursor: "pointer", fontFamily: "inherit" }}
              >
                Give feedback
              </button>
            </div>
          ))}
        </div>
      )}

      <h3 style={{ margin: "26px 0 10px", fontSize: 16, fontWeight: 800, color: "#0f172a" }}>Past feedback</h3>
      {status.history.length === 0 ? (
        <div style={{ ...cardStyle, color: "#64748b", fontSize: 14 }}>You haven't submitted any feedback yet.</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {status.history.map((h) => {
            const chip = rewardChip(h);
            return (
              <div key={h.appointmentId} style={{ ...cardStyle, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <div>
                  <div style={{ fontWeight: 700, color: "#0f172a" }}>{h.doctorName || "Consultation"}</div>
                  <div style={{ fontSize: 13, color: "#64748b" }}>
                    {h.visitDate} · submitted {h.submittedAt ? new Date(h.submittedAt).toLocaleDateString() : ""}
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                  <StarRating value={h.overallRating} readOnly label={`Rated ${h.overallRating} out of 5`} size={18} onChange={() => {}} />
                  {chip && (
                    <span style={{ fontSize: 12, fontWeight: 700, padding: "4px 12px", borderRadius: 20, background: chip.bg, color: chip.color, border: `1px solid ${chip.border}` }}>
                      {chip.text}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
