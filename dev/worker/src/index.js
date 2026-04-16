/**
 * Hardin Local — Newsletter email collection worker
 * Cloudflare Worker + D1 (SQLite)
 */

export default {
  async fetch(request, env) {
    // CORS headers for all responses
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    // Handle preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    const url = new URL(request.url);

    if (url.pathname === "/subscribe" && request.method === "POST") {
      return handleSubscribe(request, env, corsHeaders);
    }

    if (url.pathname === "/subscribers" && request.method === "GET") {
      return handleList(env, corsHeaders);
    }

    return json(404, { error: "Not found" }, corsHeaders);
  },
};

async function handleSubscribe(request, env, cors) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { error: "Invalid JSON" }, cors);
  }

  const email = (body.email || "").trim().toLowerCase();
  const source = (body.source || "unknown").trim();

  if (!email || !/^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(email)) {
    return json(400, { error: "Invalid email address" }, cors);
  }

  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const now = new Date().toISOString();

  try {
    await env.DB.prepare(
      "INSERT INTO subscribers (email, source_page, subscribed_at, ip_address) VALUES (?, ?, ?, ?)"
    ).bind(email, source, now, ip).run();
    return json(200, { ok: true, message: "Subscribed" }, cors);
  } catch (e) {
    if (e.message && e.message.includes("UNIQUE")) {
      return json(200, { ok: true, message: "Already subscribed" }, cors);
    }
    return json(500, { error: "Server error" }, cors);
  }
}

async function handleList(env, cors) {
  const { results } = await env.DB.prepare(
    "SELECT email, source_page, subscribed_at FROM subscribers ORDER BY subscribed_at DESC"
  ).all();

  return json(200, {
    count: results.length,
    subscribers: results.map((r) => ({
      email: r.email,
      source: r.source_page,
      date: r.subscribed_at,
    })),
  }, cors);
}

function json(status, data, headers = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}
