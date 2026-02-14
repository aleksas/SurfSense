// Streaming proxy for the backend SSE chat endpoint.
//
// Next.js rewrites can buffer Server-Sent Events, which makes the UI appear
// "stuck" until the LLM finishes. This route proxies /api/v1/new_chat to the
// internal FastAPI service while preserving streaming.

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function backendBaseUrl(): string {
	return (process.env.INTERNAL_FASTAPI_BACKEND_URL || "http://backend:8000").replace(/\/+$/, "");
}

function pickHeaders(req: Request): Headers {
	const out = new Headers();
	const auth = req.headers.get("authorization");
	if (auth) out.set("authorization", auth);
	const contentType = req.headers.get("content-type");
	if (contentType) out.set("content-type", contentType);
	const accept = req.headers.get("accept");
	if (accept) out.set("accept", accept);
	return out;
}

export async function POST(req: Request): Promise<Response> {
	const upstream = await fetch(`${backendBaseUrl()}/api/v1/new_chat`, {
		method: "POST",
		headers: pickHeaders(req),
		// Buffer request body to avoid Node fetch duplex issues.
		body: await req.text(),
	});

	// Preserve streaming body; override headers to discourage buffering/transforms.
	const headers = new Headers(upstream.headers);
	headers.set("cache-control", "no-cache, no-transform");
	headers.set("x-accel-buffering", "no");
	headers.set("connection", "keep-alive");

	return new Response(upstream.body, {
		status: upstream.status,
		statusText: upstream.statusText,
		headers,
	});
}

