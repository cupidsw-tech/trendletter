const ENGINE_URL = process.env.ENGINE_URL || "http://localhost:8000";
const ENGINE_API_KEY = process.env.ENGINE_API_KEY || "dev-key";

export async function engineFetch(
  path: string,
  options: RequestInit = {}
): Promise<any> {
  const res = await fetch(`${ENGINE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Engine-Key": ENGINE_API_KEY,
      ...options.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Engine API error ${res.status}: ${text}`);
  }

  return res.json();
}

export async function triggerCrawl(userId: string, sources: any[]) {
  return engineFetch("/crawl/batch", {
    method: "POST",
    body: JSON.stringify({ user_id: userId, sources }),
  });
}

export async function crawlSingleSite(source: any) {
  return engineFetch("/crawl/site", {
    method: "POST",
    body: JSON.stringify(source),
  });
}
