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
  const m = /^Basic\s+(\S+)$/i.exec(header);
  if (!m) return false;

  // Decode base64 to RAW BYTES (atob yields a Latin-1 string — one char per byte).
  let provided;
  try {
    provided = Uint8Array.from(atob(m[1]), (c) => c.charCodeAt(0));
  } catch {
    return false; // malformed base64
  }
  // Compare the WHOLE "user:pass" credential as UTF-8 bytes. Comparing the full string
  // (rather than splitting on ':' and re-encoding each half) is correct for non-ASCII
  // credentials AND for passwords containing ':' (only the username may not contain one,
  // per the Basic Auth spec). Constant-time; both length and content folded in.
  const expected = new TextEncoder().encode(`${user}:${pass}`);
  return timingSafeEqual(provided, expected);
}

// Constant-time byte-array comparison. The length difference is folded in but the loop
// still runs the full length, so neither equality nor length leaks early.
function timingSafeEqual(a, b) {
  const len = Math.max(a.length, b.length);
  let diff = a.length ^ b.length;
  for (let i = 0; i < len; i++) {
    diff |= (a[i] || 0) ^ (b[i] || 0);
  }
  return diff === 0;
}
