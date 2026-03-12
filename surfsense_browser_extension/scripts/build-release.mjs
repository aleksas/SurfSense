import { build } from "esbuild";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const outDir = path.join(projectRoot, "build", "chrome-mv3-prod");

const packageJson = JSON.parse(
	await fs.readFile(path.join(projectRoot, "package.json"), "utf8")
);

const mimeTypes = {
	".png": "image/png",
	".jpg": "image/jpeg",
	".jpeg": "image/jpeg",
	".svg": "image/svg+xml",
};
const moduleExtensions = [".ts", ".tsx", ".js", ".jsx", ".css", ".json"];

function resolveProjectPath(specifier) {
	if (specifier.startsWith("~/")) {
		return path.join(projectRoot, specifier.slice(2));
	}

	if (specifier.startsWith("~")) {
		return path.join(projectRoot, specifier.slice(1));
	}

	if (specifier.startsWith("@/")) {
		return path.join(projectRoot, specifier.slice(2));
	}

	return specifier;
}

async function pathStat(targetPath) {
	try {
		return await fs.stat(targetPath);
	} catch {
		return null;
	}
}

async function resolveModulePath(targetPath) {
	const directStat = await pathStat(targetPath);
	if (directStat?.isFile()) {
		return targetPath;
	}

	for (const extension of moduleExtensions) {
		if (await pathStat(`${targetPath}${extension}`)) {
			return `${targetPath}${extension}`;
		}
	}

	for (const extension of moduleExtensions) {
		const indexPath = path.join(targetPath, `index${extension}`);
		if (await pathStat(indexPath)) {
			return indexPath;
		}
	}

	return targetPath;
}

const aliasPlugin = {
	name: "alias-plugin",
	setup(buildContext) {
		buildContext.onResolve({ filter: /^data-base64:/ }, (args) => {
			const resolved = resolveProjectPath(args.path.slice("data-base64:".length));
			return {
				path: path.isAbsolute(resolved)
					? resolved
					: path.resolve(args.resolveDir, resolved),
				namespace: "data-base64",
			};
		});

		buildContext.onResolve({ filter: /^(~|@\/)/ }, async (args) => {
			const resolved = resolveProjectPath(args.path);
			return {
				path: await resolveModulePath(resolved),
			};
		});

		buildContext.onLoad({ filter: /.*/, namespace: "data-base64" }, async (args) => {
			const buffer = await fs.readFile(args.path);
			const extension = path.extname(args.path).toLowerCase();
			const mimeType = mimeTypes[extension] || "application/octet-stream";
			const dataUrl = `data:${mimeType};base64,${buffer.toString("base64")}`;

			return {
				contents: `export default ${JSON.stringify(dataUrl)};`,
				loader: "js",
			};
		});
	},
};

async function ensureCleanOutput() {
	await fs.rm(outDir, { recursive: true, force: true });
	await fs.mkdir(path.join(outDir, "assets"), { recursive: true });
}

async function buildEntries() {
	const commonOptions = {
		absWorkingDir: projectRoot,
		bundle: true,
		jsx: "automatic",
		plugins: [aliasPlugin],
		sourcemap: false,
		target: "chrome114",
		logLevel: "info",
		define: {
			"process.env.PLASMO_PUBLIC_BACKEND_URL": JSON.stringify(
				process.env.PLASMO_PUBLIC_BACKEND_URL || ""
			),
		},
	};

	await build({
		...commonOptions,
		entryPoints: [path.join(projectRoot, "popup-main.tsx")],
		outfile: path.join(outDir, "popup.js"),
		format: "esm",
		loader: {
			".png": "file",
			".css": "css",
		},
	});

	await build({
		...commonOptions,
		entryPoints: [path.join(projectRoot, "background", "runtime.ts")],
		outfile: path.join(outDir, "background.js"),
		format: "esm",
		loader: {
			".png": "file",
		},
	});

	await build({
		...commonOptions,
		entryPoints: [path.join(projectRoot, "content.ts")],
		outfile: path.join(outDir, "content.js"),
		format: "iife",
		loader: {
			".png": "file",
		},
	});
}

async function writeManifest() {
	const manifest = {
		manifest_version: 3,
		name: packageJson.manifest.name,
		version: packageJson.manifest.version,
		description: packageJson.manifest.description,
		action: {
			default_popup: "popup.html",
		},
		background: {
			service_worker: "background.js",
			type: "module",
		},
		content_scripts: [
			{
				matches: ["<all_urls>"],
				js: ["content.js"],
			},
		],
		permissions: ["storage", "activeTab", "scripting", "tabs"],
		host_permissions: ["<all_urls>"],
		icons: {
			128: "assets/icon.png",
		},
	};

	await fs.writeFile(
		path.join(outDir, "manifest.json"),
		JSON.stringify(manifest, null, 2)
	);
}

async function writePopupHtml() {
	const popupCssExists = await fs
		.access(path.join(outDir, "popup.css"))
		.then(() => true)
		.catch(() => false);

	const html = `<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8">
    <title>SurfSense</title>${popupCssExists ? '\n    <link rel="stylesheet" href="/popup.css">' : ""}
    <script type="module" crossorigin src="/popup.js"></script>
  </head>
  <body class="bg-gray-900 w-[400px] min-h-[500px] overflow-hidden">
    <div id="root"></div>
  </body>
</html>
`;

	await fs.writeFile(path.join(outDir, "popup.html"), html);
}

async function copyAssets() {
	await fs.copyFile(
		path.join(projectRoot, "assets", "icon.png"),
		path.join(outDir, "assets", "icon.png")
	);
	await fs.copyFile(
		path.join(projectRoot, "assets", "brain.png"),
		path.join(outDir, "assets", "brain.png")
	);
}

await ensureCleanOutput();
await buildEntries();
await writeManifest();
await writePopupHtml();
await copyAssets();
