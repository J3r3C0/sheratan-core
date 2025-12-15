import express from "express";
import cors from "cors";
import fetch from "node-fetch";
import pLimit from "p-limit";

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(express.json({ limit: "2mb" }));

const PORT = process.env.PORT ? Number(process.env.PORT) : 3000;
const UPSTREAM = process.env.SHERATAN_UPSTREAM_LLM_URL || "";
const TOKEN = process.env.LLM_BRIDGE_TOKEN || "";
const TIMEOUT_MS = process.env.LLM_BRIDGE_TIMEOUT_MS ? Number(process.env.LLM_BRIDGE_TIMEOUT_MS) : 120000;
const CONCURRENCY = process.env.LLM_BRIDGE_CONCURRENCY ? Number(process.env.LLM_BRIDGE_CONCURRENCY) : 2;

const limit = pLimit(Math.max(1, CONCURRENCY));

function requireToken(req, res, next) {
  if (!TOKEN) return next();
  const got = req.headers["x-sheratan-token"];
  if (got !== TOKEN) return res.status(401).json({ ok: false, error: "unauthorized" });
  next();
}

app.get("/health", (_req, res) => res.json({ ok: true, service: "llm-bridge", upstream: UPSTREAM || null, concurrency: CONCURRENCY }));

app.post("/api/llm/call", requireToken, async (req, res) => {
  if (!UPSTREAM) return res.status(500).json({ ok: false, error: "SHERATAN_UPSTREAM_LLM_URL not set" });

  try {
    const out = await limit(async () => {
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), TIMEOUT_MS);

      const r = await fetch(UPSTREAM, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(TOKEN ? { "x-sheratan-token": TOKEN } : {}),
        },
        body: JSON.stringify(req.body ?? {}),
        signal: ctrl.signal,
      });

      clearTimeout(t);

      const txt = await r.text();
      let data;
      try { data = JSON.parse(txt); } catch { data = { raw: txt }; }
      return { status: r.status, data };
    });

    return res.status(out.status).json(out.data);
  } catch (e) {
    const msg = (e && e.name === "AbortError") ? "upstream_timeout" : (e?.message || String(e));
    return res.status(502).json({ ok: false, error: msg });
  }
});

app.listen(PORT, "0.0.0.0", () => console.log(`[llm-bridge] :${PORT} upstream=${UPSTREAM||"(unset)"}`));
