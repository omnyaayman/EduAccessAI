import { NextRequest, NextResponse } from "next/server";

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;
  const backendUrl =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://eduaccess-ai-backend.onrender.com";

  try {
    const res = await fetch(`${backendUrl}/result/${encodeURIComponent(jobId)}`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json(
        { detail: `Job ${jobId} not found or backend returned status ${res.status}` },
        { status: res.status }
      );
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (e: any) {
    return NextResponse.json(
      { detail: e.message || "Failed to reach EduAccess backend" },
      { status: 502 }
    );
  }
}
