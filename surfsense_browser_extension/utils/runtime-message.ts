export function sendRuntimeMessage<TResponse = unknown>(
	name: string,
	body?: unknown
): Promise<TResponse> {
	return new Promise((resolve, reject) => {
		chrome.runtime.sendMessage({ name, body }, (response) => {
			const runtimeError = chrome.runtime.lastError;

			if (runtimeError) {
				reject(new Error(runtimeError.message));
				return;
			}

			if (response?.error) {
				reject(new Error(String(response.error)));
				return;
			}

			resolve(response as TResponse);
		});
	});
}
