// import * as Comlink from "comlink";
import init, { _perspective_transform, _argon2 } from "hybridocr"

self.onmessage = function(event) {
    console.log('Worker received:', event.data);

    // Perform some computation (e.g., calculate factorial)
    const result = factorial(event.data);

    // Send the result back to the main thread
    self.postMessage(result);
};

// Example function: Calculate factorial
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}


async function setup_wasm() {
    try {
        if (typeof window === "undefined") {
            let path = await import('path');
            let fs = await import('fs');
            const wasmPath = path.resolve(__dirname, "../../../wasm/pkg/hybridocr_bg.wasm");
            const wasmBuffer = fs.readFileSync(wasmPath);
            // @ts-ignore
            await init({module_or_path: wasmBuffer});
        } else {
            // @ts-ignore
            await init({module_or_path: window.static_prefix+"wasm/hybridocr_bg.wasm"});
        }
    } catch (e) {
        console.log(e);
    }
}

expose({
    _argon2: _argon2,
    setup_wasm: setup_wasm,
})

// Comlink.expose({ _perspective_transform, _argon2 })
