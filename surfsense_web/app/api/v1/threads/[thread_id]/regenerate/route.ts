// Streaming proxy for the backend regenerate SSE endpoint.
//
// Keeps the browser on same-origin while preserving streaming semantics.

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

export async function POST(
	req: Request,
	{ params }: { params: Promise<{ thread_id: string }> }
): Promise<Response> {
	const { thread_id } = await params;

	const upstream = await fetch(`${backendBaseUrl()}/api/v1/threads/${thread_id}/regenerate`, {
		method: "POST",
		headers: pickHeaders(req),
		body: await req.text(),
	});

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

