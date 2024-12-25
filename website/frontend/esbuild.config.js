import { build } from "esbuild";

await build({
    entryPoints: [
        "src/util.ts"
    ],
    bundle: true,
    outfile: "../static/js/util.js",
    platform: "browser",
    format: "esm",
    globalName: "hybridocr",
    minify: false,
    external: ["path", "fs"],
});
