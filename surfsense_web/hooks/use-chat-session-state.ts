"use client";

import { useShape } from "@electric-sql/react";
import { useSetAtom } from "jotai";
import { useEffect } from "react";
import { chatSessionStateAtom } from "@/atoms/chat/chat-session-state.atom";
import type { ChatSessionState } from "@/contracts/types/chat-session-state.types";

// Always use same-origin for the browser. Next.js rewrites proxy /electric to
// the Electric container so tunnels work.
const ELECTRIC_URL = typeof window !== "undefined" ? `${window.location.origin}/electric` : "";

/**
 * Syncs chat session state for a thread via Electric SQL.
 * Call once per thread (in page.tsx). Updates global atom.
 */
export function useChatSessionStateSync(threadId: number | null) {
	const setSessionState = useSetAtom(chatSessionStateAtom);

	const { data } = useShape<ChatSessionState>({
		url: `${ELECTRIC_URL}/v1/shape`,
		params: {
			table: "chat_session_state",
			where: `thread_id = ${threadId ?? -1}`,
		},
	});

	useEffect(() => {
		if (!threadId) {
			setSessionState(null);
			return;
		}

		const row = data?.[0];
		setSessionState({
			threadId,
			isAiResponding: !!row?.ai_responding_to_user_id,
			respondingToUserId: row?.ai_responding_to_user_id ?? null,
		});
	}, [threadId, data, setSessionState]);
}
