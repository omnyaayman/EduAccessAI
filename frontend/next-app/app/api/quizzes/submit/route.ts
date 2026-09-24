import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  const backendUrl =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://eduaccess-ai-backend.onrender.com";

  try {
    const body = await req.json();
    const res = await fetch(`${backendUrl}/quizzes/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e: any) {
    return NextResponse.json(
      { detail: e.message || "Failed to reach EduAccess backend" },
      { status: 502 }
    );
  }
}
