// THEME EDGE — sub-router / drill-down. Two top tabs (portfolio landing + watchlist); surfaced-names
// and forward-performance are now DRILL-DOWNS reached top-down by MAGNITUDE, never landing on
// all-names-across-all-themes at once:
//   #/themes                → portfolio landing (theme rows + pooled forward + power floor)
//   #/themes/watchlist      → flat cross-theme watchlist (collapsed, trigger-led)
//   #/themes/<theme>        → theme altitude (one theme's detail)
//   #/themes/<theme>/<tier> → tier altitude (one theme's one-tier names table)
// Legacy #/themes/scan and #/themes/forward redirect to the portfolio landing.
export async function render(root, params, ctx) {
  const [a, b] = params || [];
  if (!a) return (await import("./portfolio.js")).render(root, ctx);
  if (a === "watchlist") return (await import("./watchlist.js")).render(root, ctx);
  if (a === "scan" || a === "forward") { location.hash = "#/themes"; return; }
  if (b) return (await import("./tier.js")).render(root, ctx, a, b);
  return (await import("./theme.js")).render(root, ctx, a);
}
