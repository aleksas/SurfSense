import "./index";
import savedata from "./messages/savedata";
import savesnapshot from "./messages/savesnapshot";

type RuntimeMessage = {
	name?: string;
	body?: unknown;
};

type RuntimeResponse = {
	send: (payload: unknown) => void;
};

async function invokeHandler(
	handler: (req: RuntimeMessage, res: RuntimeResponse) => Promise<void> | void,
	request: RuntimeMessage
) {
	return await new Promise<unknown>((resolve, reject) => {
		let responded = false;

		const response: RuntimeResponse = {
			send(payload) {
				responded = true;
				resolve(payload);
			},
		};

		Promise.resolve(handler(request, response))
			.then(() => {
				if (!responded) {
					resolve(undefined);
				}
			})
			.catch(reject);
	});
}

const handlers = {
	savedata,
	savesnapshot,
} as const;

chrome.runtime.onMessage.addListener((message: RuntimeMessage, _sender, sendResponse) => {
	if (!message?.name) {
		return;
	}

	const handler = handlers[message.name as keyof typeof handlers];

	if (!handler) {
		return;
	}

	invokeHandler(handler, message)
		.then((payload) => {
			sendResponse(payload);
		})
		.catch((error) => {
			console.error("Runtime message failed", error);
			sendResponse({
				error: String(error instanceof Error ? error.message : error),
			});
		});

	return true;
});
