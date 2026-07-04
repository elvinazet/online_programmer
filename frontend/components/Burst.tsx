import type { CSSProperties } from "react";

export default function Burst({
  points = 12,
  inner = 0.42,
  className = "",
  style,
}: {
  points?: number;
  inner?: number;
  className?: string;
  style?: CSSProperties;
}) {
  const step = Math.PI / points;
  let d = "";
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 ? inner : 1;
    const a = i * step - Math.PI / 2;
    const x = 50 + Math.cos(a) * 49 * r;
    const y = 50 + Math.sin(a) * 49 * r;
    d += (i ? "L" : "M") + x.toFixed(2) + " " + y.toFixed(2);
  }
  d += "Z";
  return (
    <svg viewBox="0 0 100 100" className={className} style={style} aria-hidden="true">
      <path d={d} fill="currentColor" />
    </svg>
  );
}
