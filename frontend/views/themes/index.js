// THEME EDGE — sub-router. The four theme views share the `themes` route; params[0] selects the
// page (#/themes, #/themes/scan, #/themes/watchlist, #/themes/forward). Each sub-view exports
// render(root, { item, frame }). Kept read-only, like every other view.
const SUB = {
  "": () => import("./overview.js"),
  scan: () => import("./scan.js"),
  watchlist: () => import("./watchlist.js"),
  forward: () => import("./forward.js"),
};

export async function render(root, params, ctx) {
  const loader = SUB[(params && params[0]) || ""] || SUB[""];
  const mod = await loader();
  return mod.render(root, ctx);
}
