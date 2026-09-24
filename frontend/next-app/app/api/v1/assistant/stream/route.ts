import { NextRequest } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const backendUrl =
      process.env.API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      "https://eduaccess-ai-backend.onrender.com";

    const res = await fetch(`${backendUrl}/api/v1/assistant/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    return new Response(res.body, {
      status: res.status,
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (e: any) {
    return new Response(
      `data: {"token": "Failed to connect to assistant stream: ${e.message}", "done": true}\n\n`,
      {
        headers: { "Content-Type": "text/event-stream" },
      }
    );
  }
}
