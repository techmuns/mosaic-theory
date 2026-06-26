// ============================================================================
// FAIL-CLOSED AUTHED GATE  —  Cloudflare Pages middleware (defense-in-depth)
// ----------------------------------------------------------------------------
// frontend/dossiers/*.json and frontend/snapshots/*.jsonl are DERIVED from
// licensed CIQ data. Per CLAUDE.md / STATE.md §4 they may be served ONLY from an
// AUTHED origin — serving them unauthenticated is the one IRREVERSIBLE leak this
// project guards against (once a reachable URL has served them, it can't be
// retracted).
//
// This middleware is the belt-and-suspenders BEHIND the account-side Cloudflare
// Access (Zero Trust) policy. The primary gate is still Access in front of the
// Pages project (Google IdP + an allow-policy on your emails/domain). This
// Function independently validates the IDENTITY-LEVEL JWT that Access mints on a
// successful Google login, so the ORIGIN itself fails closed even if that policy
// is ever disabled, removed, or misconfigured.
//
// FAIL CLOSED, ALWAYS. If the Access env config is missing, the team signing keys
// can't be fetched, or the JWT is absent / invalid / expired / wrong-audience, the
// response is 403 — never the asset. A bug in here can only DENY (no leak), never
// expose. That asymmetry is why this is safe to ship even though it cannot be
// exercised end-to-end without a live Cloudflare Access deployment.
//
// Required Pages environment variables (set in the dashboard — NEVER committed):
//   CF_ACCESS_TEAM_DOMAIN   e.g. "yourteam.cloudflareaccess.com" (or just "yourteam")
//   CF_ACCESS_AUD           the Access application Audience (AUD) tag
// Optional (prefer enforcing identity in the Access POLICY itself):
//   CF_ACCESS_ALLOWED_EMAILS   comma-separated allowlist; an extra origin-side check
// ============================================================================

const CERTS_TTL_MS = 3600_000; // re-fetch the team signing keys hourly (best-effort isolate cache)
let _certs = null; // { byKid: Map<string, CryptoKey>, fetchedAt: number, issuer: string }

export async function onRequest(ctx) {
  try {
    if (await authorized(ctx.request, ctx.env)) return await ctx.next();
  } catch {
    // any unexpected failure falls through to deny — fail closed
  }
  return deny();
}

function deny() {
  return new Response("Forbidden — this origin serves authenticated users only.", {
    status: 403,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}

async function authorized(request, env) {
  const teamRaw = (env && env.CF_ACCESS_TEAM_DOMAIN) || "";
  const aud = (env && env.CF_ACCESS_AUD) || "";
  if (!teamRaw || !aud) return false; // UNCONFIGURED ⇒ deny everything (the safe default)

  const team = teamRaw.includes(".") ? teamRaw : `${teamRaw}.cloudflareaccess.com`;
  const issuer = `https://${team}`;

  const token = readToken(request);
  if (!token) return false;

  const claims = await verifyJwt(token, issuer, aud);
  if (!claims) return false;

  const allow = String(env.CF_ACCESS_ALLOWED_EMAILS || "")
    .split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
  if (allow.length) {
    const email = String(claims.email || "").toLowerCase();
    if (!email || !allow.includes(email)) return false;
  }
  return true;
}

// Access injects the JWT on the header for every authenticated request; the cookie
// is the fallback for a top-level navigation that hasn't re-issued the header yet.
function readToken(request) {
  const h = request.headers.get("Cf-Access-Jwt-Assertion");
  if (h) return h.trim();
  const cookie = request.headers.get("Cookie") || "";
  const m = cookie.match(/(?:^|;\s*)CF_Authorization=([^;]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

async function verifyJwt(token, issuer, aud) {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  const [h64, p64, s64] = parts;

  let header, payload;
  try {
    header = JSON.parse(b64urlToStr(h64));
    payload = JSON.parse(b64urlToStr(p64));
  } catch {
    return null;
  }
  if (header.alg !== "RS256" || !header.kid) return null;

  const now = Math.floor(Date.now() / 1000);
  if (payload.iss !== issuer) return null;
  const auds = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!auds.includes(aud)) return null;
  if (typeof payload.exp !== "number" || payload.exp <= now) return null;
  if (typeof payload.nbf === "number" && payload.nbf > now + 60) return null;
  if (typeof payload.iat === "number" && payload.iat > now + 60) return null;

  const key = await keyForKid(issuer, header.kid);
  if (!key) return null;

  const data = new TextEncoder().encode(`${h64}.${p64}`);
  const sig = b64urlToBytes(s64);
  const ok = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, sig, data);
  return ok ? payload : null;
}

async function keyForKid(issuer, kid) {
  const fresh =
    _certs && _certs.issuer === issuer && Date.now() - _certs.fetchedAt < CERTS_TTL_MS;
  if (!fresh) {
    const res = await fetch(`${issuer}/cdn-cgi/access/certs`, { cf: { cacheTtl: 3600 } });
    if (!res.ok) return null; // can't fetch keys ⇒ can't verify ⇒ deny
    const { keys } = await res.json();
    const byKid = new Map();
    for (const jwk of keys || []) {
      try {
        const k = await crypto.subtle.importKey(
          "jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]
        );
        if (jwk.kid) byKid.set(jwk.kid, k);
      } catch {
        // skip a malformed key, keep the rest
      }
    }
    _certs = { byKid, fetchedAt: Date.now(), issuer };
  }
  return _certs.byKid.get(kid) || null;
}

function b64urlToBytes(s) {
  const b64 = s.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(s.length / 4) * 4, "=");
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function b64urlToStr(s) {
  return new TextDecoder().decode(b64urlToBytes(s));
}
