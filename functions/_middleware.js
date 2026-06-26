// ============================================================================
// FAIL-CLOSED BASIC-AUTH GATE  —  Cloudflare Pages middleware
// ----------------------------------------------------------------------------
// frontend/dossiers/*.json and frontend/snapshots/*.{jsonl,json} are DERIVED from
// licensed CIQ data. Per CLAUDE.md / STATE.md §4 they may be served ONLY from an
// AUTHED origin — serving them unauthenticated is the one IRREVERSIBLE leak this
// project guards against. This Function gates the ENTIRE site (every path,
// including the data files) behind HTTP Basic Auth.
//
// NO Cloudflare Zero Trust / Access required — credentials are plain Pages env
// vars, so the deploy needs no extra Cloudflare product, no payment method.
//
// Required Pages environment variables (set in the dashboard — NEVER committed;
// store BASIC_AUTH_PASS as an encrypted secret):
//   BASIC_AUTH_USER   the dashboard username
//   BASIC_AUTH_PASS   the dashboard password
//
// FAIL CLOSED, ALWAYS. If either env var is unset, or the credentials are missing
// or wrong, the response is 401 — never the asset. A bug here can only DENY (no
// leak), never expose. That asymmetry is why this is safe even though it can't be
// exercised end-to-end without a live deployment.
// ============================================================================

const REALM = "Nostra Vinci - authorized users only"; // ASCII only: HTTP header values are Latin-1

export async function onRequest(ctx) {
  try {
    if (authorized(ctx.request, ctx.env)) return await ctx.next();
  } catch {
    // any unexpected failure falls through to the challenge — fail closed
  }
  return challenge();
}

function challenge() {
  return new Response("Authentication required.", {
    status: 401,
    headers: {
      "WWW-Authenticate": `Basic realm="${REALM}", charset="UTF-8"`,
      "content-type": "text/plain; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function authorized(request, env) {
  const user = env && env.BASIC_AUTH_USER;
  const pass = env && env.BASIC_AUTH_PASS;
  if (!user || !pass) return false; // UNCONFIGURED ⇒ deny everything (the safe default)

  const header = (request.headers.get("Authorization") || "").trim();
  const m = /^Basic\s+(.+)$/i.exec(header);
  if (!m) return false;

  let decoded;
  try {
    decoded = atob(m[1]);
  } catch {
    return false; // malformed base64
  }
  const sep = decoded.indexOf(":");
  if (sep < 0) return false;
  const u = decoded.slice(0, sep);
  const p = decoded.slice(sep + 1);

  // Evaluate BOTH legs (no && short-circuit) so a correct username can't be
  // distinguished from a wrong one by timing.
  return Boolean(timingSafeEqual(u, user) & timingSafeEqual(p, pass));
}

// Constant-time string comparison over UTF-8 bytes. Length difference is folded in
// but the loop still runs the full length, so neither equality nor length leaks early.
function timingSafeEqual(a, b) {
  const enc = new TextEncoder();
  const ab = enc.encode(a);
  const bb = enc.encode(b);
  const len = Math.max(ab.length, bb.length);
  let diff = ab.length ^ bb.length;
  for (let i = 0; i < len; i++) {
    diff |= (ab[i] || 0) ^ (bb[i] || 0);
  }
  return diff === 0;
}
