import React, { useState } from "react";

/**
 * 1-5 star input. Each star is a real <button>, so it is keyboard-focusable
 * (Tab, then Enter/Space) and announced by screen readers as part of a
 * radio group. With `clearable`, clicking the selected star again clears it
 * (used for the optional per-aspect ratings).
 */
export default function StarRating({ value = 0, onChange, label, size = 28, clearable = false, readOnly = false }) {
  const [hover, setHover] = useState(0);
  const shown = hover || value;

  const select = (n) => {
    if (readOnly) return;
    onChange(clearable && n === value ? 0 : n);
  };

  return (
    <div
      role="radiogroup"
      aria-label={label}
      onMouseLeave={() => setHover(0)}
      style={{ display: "inline-flex", gap: 2 }}
    >
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={value === n}
          aria-label={`${n} ${n === 1 ? "star" : "stars"}`}
          disabled={readOnly}
          onClick={() => select(n)}
          onMouseEnter={() => !readOnly && setHover(n)}
          style={{
            background: "transparent",
            border: "none",
            padding: 2,
            cursor: readOnly ? "default" : "pointer",
            fontSize: size,
            lineHeight: 1,
            color: n <= shown ? "#f59e0b" : "#cbd5e1",
            transition: "color 0.1s",
          }}
        >
          ★
        </button>
      ))}
    </div>
  );
}
