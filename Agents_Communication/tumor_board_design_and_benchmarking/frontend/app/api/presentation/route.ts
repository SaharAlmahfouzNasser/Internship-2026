const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";
const DEFAULT_CASE = "nsclc_egfr_l858r_advanced";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const caseId: string = (body as { case_id?: string }).case_id ?? DEFAULT_CASE;

  const upstream = await fetch(`${FASTAPI_URL}/stream/${caseId}`, {
    method: "POST",
    signal: req.signal
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(
      `data: ${JSON.stringify({ type: "error", content: "Backend unavailable." })}\n\n`,
      {
        status: 502,
        headers: { "Content-Type": "text/event-stream" }
      }
    );
  }

  return new Response(upstream.body, {
    headers: {
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "Content-Type": "text/event-stream; charset=utf-8"
    }
  });
}
