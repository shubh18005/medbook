import React, { useState, useEffect } from "react";
import { fetchFeedbackStats, downloadFeedbackCsv } from "../../utils/api";

const GROUP_COLORS = { A: "#64748b", B: "#3b82f6", C: "#8b5cf6", D: "#0f766e" };

const cardStyle = {
  background: "#ffffff",
  borderRadius: 16,
  padding: 20,
  border: "1px solid #e2e8f0",
  boxShadow: "0 4px 16px rgba(0,0,0,0.03)",
};

const num = (v, digits = 1, suffix = "") => `${Number(v).toFixed(digits)}${suffix}`;

/**
 * Study dashboard: the measures behind RQ1-RQ3, per group, plus an anonymised
 * CSV export for the Python analysis pipeline.
 */
export default function AdminStudy({ onToast }) {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchFeedbackStats()
      .then(setStats)
      .catch((err) => setError(err.message));
  }, []);

  const handleExport = async () => {
    setExporting(true);
    try {
      await downloadFeedbackCsv();
      onToast?.("Anonymised feedback CSV downloaded.");
    } catch (err) {
      onToast?.(err.message, "error");
    } finally {
      setExporting(false);
    }
  };

  if (error) return <div style={{ ...cardStyle, color: "#b91c1c" }}>{error}</div>;
  if (!stats) return <div style={{ textAlign: "center", padding: 60, color: "#64748b" }}>Loading study data…</div>;

  const { groups, config, qualityHistogram, totalFeedback } = stats;

  // metric rows: [label, hint, render(groupStats), isBar]
  const rows = [
    ["Participants enrolled", "Patients assigned to the group", (g) => g.enrolled],
    ["Shown the checkpoint", "...with at least one completed visit", (g) => g.shown],
    ["Responded", "...who gave feedback at least once", (g) => g.responded],
    ["Response rate", "Responded ÷ shown (RQ1)", (g) => (g.shown ? num(g.responseRate, 1, "%") : "—"), true],
    ["Feedback submitted", "Total submissions", (g) => g.feedbackCount],
    ["Mean overall rating", "Out of 5 (RQ2)", (g) => (g.feedbackCount ? num(g.meanRating, 2) : "—")],
    ["Neutral share", "Submissions rated 3 stars (RQ2)", (g) => (g.feedbackCount ? num(g.neutralShare, 1, "%") : "—")],
    ["Mean words", "Length of the free text", (g) => (g.feedbackCount ? num(g.meanWords, 1) : "—")],
    ["Mean quality score Q", "0 to 1 (RQ3)", (g) => (g.feedbackCount ? num(g.meanQuality, 2) : "—")],
    ["Low-effort share", `Q below ${config.threshold} (RQ3)`, (g) => (g.feedbackCount ? num(g.lowEffortShare, 1, "%") : "—")],
    ["Rewards granted", "", (g) => (g.group === "A" ? "—" : g.rewardsGranted)],
    ["Rewards withheld", "Failed the quality gate", (g) => (g.group === "D" ? g.rewardsWithheld : "—")],
  ];
  const aspectRows = [
    ["doctor", "Doctor"], ["staff", "Staff"], ["waiting", "Waiting time"], ["cleanliness", "Cleanliness"], ["billing", "Billing"],
  ];
  const maxHist = Math.max(1, ...qualityHistogram);
  const histLabels = ["0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1"];

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontWeight: 800, color: "#0f172a", fontSize: 24 }}>Feedback Study Dashboard</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#64748b", maxWidth: 640 }}>
            Group-wise measures for the reward study. {totalFeedback} submission{totalFeedback === 1 ? "" : "s"} so far. Group
            letters are assigned randomly at registration and are never shown to patients.
          </p>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          style={{ background: "#0f172a", color: "#ffffff", border: "none", padding: "10px 18px", borderRadius: 10, fontWeight: 700, fontSize: 13, cursor: exporting ? "wait" : "pointer", fontFamily: "inherit" }}
        >
          {exporting ? "Preparing…" : "Export anonymised CSV"}
        </button>
      </div>

      <div style={{ ...cardStyle, padding: 0, overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14, minWidth: 640 }}>
          <thead>
            <tr>
              <th style={{ ...th, textAlign: "left" }}>Measure</th>
              {groups.map((g) => (
                <th key={g.group} style={th} scope="col">
                  <span style={{ display: "inline-block", width: 9, height: 9, borderRadius: "50%", background: GROUP_COLORS[g.group], marginRight: 6 }} />
                  {g.group} · {g.name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(([label, hint, render, isBar]) => (
              <tr key={label}>
                <th scope="row" style={{ ...td, textAlign: "left", fontWeight: 600, color: "#0f172a" }}>
                  {label}
                  {hint && <div style={{ fontSize: 11, fontWeight: 400, color: "#94a3b8" }}>{hint}</div>}
                </th>
                {groups.map((g) => (
                  <td key={g.group} style={{ ...td, fontWeight: isBar ? 800 : 500 }}>
                    {render(g)}
                    {isBar && g.shown > 0 && (
                      <div style={{ height: 5, background: "#f1f5f9", borderRadius: 3, marginTop: 5 }}>
                        <div style={{ width: `${Math.min(100, g.responseRate)}%`, height: "100%", background: GROUP_COLORS[g.group], borderRadius: 3 }} />
                      </div>
                    )}
                  </td>
                ))}
              </tr>
            ))}
            <tr><td colSpan={groups.length + 1} style={{ ...td, textAlign: "left", background: "#f8fafc", fontWeight: 700, color: "#475569", fontSize: 12 }}>Mean aspect ratings (out of 5)</td></tr>
            {aspectRows.map(([key, label]) => (
              <tr key={key}>
                <th scope="row" style={{ ...td, textAlign: "left", fontWeight: 600, color: "#0f172a" }}>{label}</th>
                {groups.map((g) => (
                  <td key={g.group} style={td}>{g.meanAspect?.[key] ? num(g.meanAspect[key], 2) : "—"}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16, marginTop: 20 }}>
        <div style={cardStyle}>
          <h3 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 800, color: "#0f172a" }}>Quality score distribution</h3>
          <p style={{ margin: "0 0 14px", fontSize: 12, color: "#64748b" }}>
            All groups. Use this on the pilot to choose the threshold (currently {config.threshold}).
          </p>
          {qualityHistogram.map((count, i) => (
            <div key={histLabels[i]} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, fontSize: 12 }}>
              <span style={{ width: 56, color: "#64748b" }}>{histLabels[i]}</span>
              <div style={{ flex: 1, background: "#f1f5f9", height: 14, borderRadius: 4 }}>
                <div style={{ width: `${(count / maxHist) * 100}%`, height: "100%", background: i >= 3 ? "#0f766e" : "#cbd5e1", borderRadius: 4 }} />
              </div>
              <span style={{ width: 28, textAlign: "right", fontWeight: 700, color: "#0f172a" }}>{count}</span>
            </div>
          ))}
        </div>

        <div style={cardStyle}>
          <h3 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 800, color: "#0f172a" }}>Current study settings</h3>
          <p style={{ margin: "0 0 14px", fontSize: 12, color: "#64748b" }}>
            Set in the backend's application.properties. Freeze them after the pilot and report them with the results.
          </p>
          <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
            <tbody>
              {[
                ["Weight on detail (D)", config.wDetail],
                ["Weight on uniqueness (U)", config.wUnique],
                ["Weight on consistency (C)", config.wConsistency],
                ["Threshold (θ)", config.threshold],
                ["Points reward", config.rewardPoints],
                ["Discount reward", `${config.rewardDiscountPercent}%`],
                ["Group D receives", config.groupDRewardType],
              ].map(([k, v]) => (
                <tr key={k}>
                  <td style={{ padding: "5px 0", color: "#475569" }}>{k}</td>
                  <td style={{ padding: "5px 0", textAlign: "right", fontWeight: 700, color: "#0f172a" }}>{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const th = { padding: "12px 14px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0", fontSize: 13, fontWeight: 700, color: "#0f172a", textAlign: "center", whiteSpace: "nowrap" };
const td = { padding: "10px 14px", borderBottom: "1px solid #f1f5f9", textAlign: "center", color: "#334155", verticalAlign: "top" };
