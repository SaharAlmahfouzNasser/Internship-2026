import { NextResponse } from "next/server";
import { readFile } from "node:fs/promises";
import path from "node:path";

// Resolve the repo logs/ directory. Defaults to ../logs relative to the
// frontend working directory; override with LOGS_DIR if running elsewhere.
const LOGS_DIR = process.env.LOGS_DIR ?? path.join(process.cwd(), "..", "logs");

// Whitelist of case ids we serve (prevents path traversal via case_id).
const ALLOWED_CASES = new Set([
  "nsclc_egfr_l858r_advanced",
  "breast_her2_equivocal_then_fish_positive",
  "synchronous_sclc_nsclc"
]);

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const caseId = searchParams.get("case_id") ?? "";

  if (!ALLOWED_CASES.has(caseId)) {
    return NextResponse.json(
      { error: `Unknown case_id: ${caseId}` },
      { status: 400 }
    );
  }

  const latestPath = path.join(LOGS_DIR, "latest", `${caseId}.json`);

  try {
    const raw = await readFile(latestPath, "utf-8");
    const data = JSON.parse(raw);
    return NextResponse.json(data, {
      headers: { "Cache-Control": "no-store" }
    });
  } catch {
    return NextResponse.json(
      {
        error: `No saved run found for ${caseId}. Run the case once (tb-run / live Stream) to create logs/latest/${caseId}.json.`
      },
      { status: 404 }
    );
  }
}
