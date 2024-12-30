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
    _argon2,
    _perspective_transform,
}

Comlink.expose(workerAPI);
