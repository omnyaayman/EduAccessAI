import { NextResponse } from "next/server";

export async function GET() {
  const backendUrl =
    process.env.API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "https://eduaccess-ai-backend.onrender.com";

  try {
    const res = await fetch(`${backendUrl}/health`, { cache: "no-store" });
    if (res.ok) {
      const data = await res.json();
      return NextResponse.json({
        status: "ok",
        frontend: "ok",
        backend: data,
        service: "EduAccess AI",
        version: "2.0.0",
      });
    }
    return NextResponse.json(
      {
        status: "degraded",
        frontend: "ok",
        backend_status: res.status,
        service: "EduAccess AI",
        version: "2.0.0",
      },
      { status: 200 }
    );
  } catch (e: any) {
    return NextResponse.json(
      {
        status: "degraded",
        frontend: "ok",
        backend_error: e.message || "Backend starting up on Render",
        service: "EduAccess AI",
        version: "2.0.0",
      },
      { status: 200 }
    );
  }
}
