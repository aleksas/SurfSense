import React from "react";
import { createRoot } from "react-dom/client";
import Popup from "~popup.tsx";

const rootElement = document.getElementById("root");

if (!rootElement) {
	throw new Error("Popup root element not found");
}

createRoot(rootElement).render(
	<React.StrictMode>
		<Popup />
	</React.StrictMode>
);
