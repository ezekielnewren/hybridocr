import init, { _argon2id, _argon2i, _argon2d } from "hybridocr"
import path from "path";
import fs from "fs";

export function is_nodejs() {
    return typeof process !== 'undefined';
}

async function setup_wasm() {
    const rel_path = "/static/wasm/hybridocr_bg.wasm";
    if (is_nodejs()) {
        const wasmPath = path.resolve(__dirname, "../.."+rel_path);
        const wasmBuffer = fs.readFileSync(wasmPath);
        await init({module_or_path: wasmBuffer});
    } else {
        await init({module_or_path: rel_path});
    }
}
await setup_wasm();


export function toHex(data: Uint8Array): string {
    return Array.from(data)
        .map(byte => byte.toString(16).padStart(2, "0"))
        .join("");
}

export function toB64(data: Uint8Array, padding: boolean = true, urlSafe: boolean = false) {
    const binaryString = Array.from(data)
    .map(byte => String.fromCharCode(byte))
    .join('');
    let r = btoa(binaryString);
    if (!padding) {
        r = r.replaceAll("=", "");
    }
    if (urlSafe) {
        r = r.replaceAll("+", "-");
        r = r.replaceAll("/", "_");
    }
    return r;
}

class Argon2Result {
    readonly algorithm: string;
    readonly version: number;
    readonly m: number;
    readonly t: number;
    readonly p: number;
    readonly salt: Uint8Array;
    readonly hash: Uint8Array;

    constructor(algorithm: string, version: number, m: number, t: number, p: number, salt: Uint8Array, hash: Uint8Array) {
        this.algorithm = algorithm;
        this.version = version;
        this.m = m;
        this.t = t;
        this.p = p;
        this.salt = salt;
        this.hash = hash;
    }

    public encoded() {
        let out = "";
        out += "$"+this.algorithm;
        out += "$"+this.version
        out += "$m="+this.m+",t="+this.t+",p="+this.p;
        out += "$"+toB64(this.salt, false);
        out += "$"+toB64(this.hash, false);
        return out;
    }

}


export async function argon2id(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
    const hash = _argon2id(password, salt, m, t, p, length);
    return new Argon2Result("argon2id", 19, m, t, p, salt, hash);
}

export async function argon2i(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
    const hash = _argon2i(password, salt, m, t, p, length);
    return new Argon2Result("argon2i", 19, m, t, p, salt, hash);
}

export async function argon2d(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
    const hash = _argon2d(password, salt, m, t, p, length);
    return new Argon2Result("argon2d", 19, m, t, p, salt, hash);
}
