import { NextResponse } from "next/server";
import { loadCase, publicImagePath } from "@/lib/case-data";

export async function GET() {
  const caseData = await loadCase();
  return NextResponse.json({
    ...caseData,
    images: caseData.images.map((image) => ({
      ...image,
      src: publicImagePath(caseData.id, image)
    }))
  });
}
