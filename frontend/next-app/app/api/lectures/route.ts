import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://eduaccess-ai-backend.onrender.com";

  try {
    const res = await fetch(`${backendUrl}/lectures`, {
      cache: "no-store",
    });
    if (!res.ok) {
      return NextResponse.json(
        { detail: `Backend returned status ${res.status}` },
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
