import { build } from "esbuild";

await build({
    entryPoints: [
        "src/util.ts",
        "src/worker.ts",
        "src/sandbox.ts",
    ],
    bundle: true,
    // outfile: "../static/js/util.js",
    outdir: "../static/js",
    platform: "browser",
    format: "esm",
    globalName: "hybridocr",
    minify: false,
    external: ["path", "fs"],
});
