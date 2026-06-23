// Shared read-only UI snippets.

// The "how to update" block is COPYABLE TEXT, never a button. The dashboard is a static mirror and
// never runs the pipeline — the human copies these commands into their own terminal, then pushes.
// This preserves the read-only discipline: nothing here triggers a write, compute, or fetch.
export function refreshBlock() {
  return `
    <details class="card" style="margin-top:20px; background:var(--surface-2);">
      <summary style="cursor:pointer; font-size:12.5px; font-weight:600; color:var(--ink-2);">How to update this dashboard <span class="muted" style="font-weight:400;">(read-only — copy &amp; run locally, then push)</span></summary>
      <div class="subtitle muted" style="margin:10px 0 8px;">A static mirror of the last pushed snapshots. To refresh it, run the pipeline locally and push — the dashboard runs nothing.</div>
      <pre style="background:var(--nav-bg); color:#c3cad6; padding:12px 14px; border-radius:8px; font-size:12px; overflow-x:auto; margin:0; line-height:1.6;"><code>vinci run-weekly            # refresh EOD + rebuild universe + screen
vinci rank --structural     # re-rank with the structural-demote channel
git add data/snapshots &amp;&amp; git commit -m "refresh snapshots" &amp;&amp; git push</code></pre>
    </details>`;
}
