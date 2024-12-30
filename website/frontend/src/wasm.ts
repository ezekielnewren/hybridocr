import * as Comlink from "comlink";
import init, { _perspective_transform, _argon2 } from "hybridocr"

const workerAPI = {
    async setup(url: string) {
        try {
            await init({module_or_path: url});
            console.log("finished wasm initialization");
        } catch (e) {
            console.log(e);
        }
    },
    // _perspective_transform,
    a2(alg: number, password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number): Uint8Array {
        console.log("_argon2 called");
        return _argon2(alg, password, salt, m, t, p, length);
    },
}

Comlink.expose(workerAPI);
