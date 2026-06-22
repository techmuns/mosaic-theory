// Pure presentation helpers — formatting only, no data access, no DOM.
// (Kept tiny and dependency-free; the dashboard is static and lightweight by design.)

export const DASH = "—"; // the honest "no value" glyph used across the UI

export function fmtInt(n) {
  return typeof n === "number" && isFinite(n) ? n.toLocaleString("en-US") : DASH;
}

export function fmtMoney(n, { compact = true } = {}) {
  if (typeof n !== "number" || !isFinite(n)) return DASH;
  if (!compact) return "$" + n.toLocaleString("en-US", { maximumFractionDigits: 0 });
  const a = Math.abs(n);
  // unary + drops trailing zeros: 10.00→10, 3.05→3.05, 300.0→300 ($10B / $3.05B / $300M)
  if (a >= 1e9) return "$" + +(n / 1e9).toFixed(2) + "B";
  if (a >= 1e6) return "$" + +(n / 1e6).toFixed(1) + "M";
  if (a >= 1e3) return "$" + (n / 1e3).toFixed(0) + "K";
  return "$" + n.toFixed(2);
}

export function fmtPrice(n) {
  return typeof n === "number" && isFinite(n) ? "$" + n.toFixed(2) : DASH;
}

export function fmtPct(frac, { digits = 0, signed = false } = {}) {
  if (typeof frac !== "number" || !isFinite(frac)) return DASH;
  const v = (frac * 100).toFixed(digits);
  return (signed && frac > 0 ? "+" : "") + v + "%";
}

export function fmtScore(n) {
  return typeof n === "number" && isFinite(n) ? n.toFixed(3) : DASH;
}

// ISO date/datetime string -> "Jun 17, 2026" (date-only, UTC-safe, no time drift).
export function fmtDate(iso) {
  if (!iso) return DASH;
  const d = new Date(String(iso).slice(0, 10) + "T00:00:00Z");
  if (isNaN(d)) return DASH;
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
}

// Whole days between two ISO dates (b - a). Positive => b is later.
export function daysBetween(aIso, bIso) {
  const a = new Date(String(aIso).slice(0, 10) + "T00:00:00Z");
  const b = new Date(String(bIso).slice(0, 10) + "T00:00:00Z");
  if (isNaN(a) || isNaN(b)) return null;
  return Math.round((b - a) / 86400000);
}

export function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}
