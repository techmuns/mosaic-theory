// THEME EDGE — sub-router. Two stage tabs (the themes landing + the radar intake); theme pages
// and tier tables are DRILL-DOWNS reached top-down by MAGNITUDE, framed with the same tabs:
//   #/themes                → landing (theme table + cross-theme watchlist + radar intake strip)
//   #/themes/radar[/tab]    → radar intake (map · inbox · log — one view, chip sub-tabs)
//   #/themes/<theme>        → theme altitude (brief + who's in play + flags + underwrite cards)
//   #/themes/<theme>/<tier> → tier altitude (one theme's one-tier names table)
// Legacy #/radar, #/themes/watchlist, #/themes/scan|forward are normalized in app.js parseHash.
// NOTE: first-segment names here are RESERVED against theme slugs — build.py refuses a collision.
export async function render(root, params, ctx) {
  const [a, b] = params || [];
  if (!a) return (await import("./portfolio.js")).render(root, ctx);
  if (a === "radar") return (await import("./radar.js")).render(root, [b].filter(Boolean), ctx);
  if (b) return (await import("./tier.js")).render(root, ctx, a, b);
  return (await import("./theme.js")).render(root, ctx, a);
}
