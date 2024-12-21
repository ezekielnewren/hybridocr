
export namespace util {
    const ptr_size: number = 4;

    let g_wasm: WebAssembly.WebAssemblyInstantiatedSource | null = null;
    let g_wasm_init: Promise<void> | null = null;
    let g_wasm_path: string | null = null;

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


    class WasmMemory {
        public wasm: any;
        public ptr: number | bigint;
        public len: number | bigint;

        private constructor(wasm: any, ptr: number | bigint, len: number | bigint) {
            this.wasm = wasm;
            this.ptr = ptr;
            this.len = len;
        }

        static new(wasm: any, len: number) {
            return this.from_pointer(wasm, wasm.allocate(len));
        }

        static from_pointer(wasm: any, ptr: number) {
            let memory = new DataView(wasm.memory.buffer);
            const len = ptr_size == 4 ? memory.getUint32(ptr, true) : memory.getBigUint64(ptr, true);
            return new WasmMemory(wasm, ptr, len);
        }

        as_Uint8Array(): Uint8Array {
            return new Uint8Array(this.wasm.memory.buffer, this.ptr as number+ptr_size, this.len as number);
        }

        free() {
            if (typeof this.ptr === "number" && typeof this.len === "number") {
                this.wasm.deallocate(this.ptr as number-ptr_size, this.len as number+ptr_size);
            } else {
                this.wasm.deallocate(this.ptr as bigint-BigInt(ptr_size), this.len as bigint+BigInt(ptr_size));
            }
        }


    }


    async function argon2(_password: Uint8Array, _salt: Uint8Array, m: number, t: number, p: number, length: number, str_type: string, lambda: any) {
        const wasm = (await get_wasm()).instance.exports as any;
        let password = WasmMemory.new(wasm, _password.length);
        password.as_Uint8Array().set(_password);
        let salt = WasmMemory.new(wasm, _salt.length);
        salt.as_Uint8Array().set(_salt);

        const result = WasmMemory.from_pointer(wasm, lambda(password.ptr, password.len, salt.ptr, salt.len, m, t, p, length));
        let hash = new Uint8Array(result.len as number);
        hash.set(result.as_Uint8Array());
        result.free();
        salt.free();
        password.free();

        return new Argon2Result(str_type, 19, m, t, p, _salt, hash);
    }

    export async function argon2id(_password: Uint8Array, _salt: Uint8Array, m: number, t: number, p: number, length: number) {
        const wasm = (await get_wasm()).instance.exports as any;
        return argon2(_password, _salt, m, t, p, length, "argon2id", wasm._argon2id);
    }

    export async function argon2i(_password: Uint8Array, _salt: Uint8Array, m: number, t: number, p: number, length: number) {
        const wasm = (await get_wasm()).instance.exports as any;
        return argon2(_password, _salt, m, t, p, length, "argon2i", wasm._argon2i);
    }

    export async function argon2d(_password: Uint8Array, _salt: Uint8Array, m: number, t: number, p: number, length: number) {
        const wasm = (await get_wasm()).instance.exports as any;
        return argon2(_password, _salt, m, t, p, length, "argon2d", wasm._argon2d);
    }

    export function is_nodejs() {
        return process.env.NODE_ENV !== "production";
    }


    export function toHex(data: Uint8Array): string {
        return Array.from(data)
            .map(byte => byte.toString(16).padStart(2, "0"))
            .join("");
    }


    export class Point {
        x: number;
        y: number;

        constructor(x: number, y: number) {
            this.x = x;
            this.y = y;
        }
    }

    export class Quadrilateral {
        tl: Point;
        tr: Point;
        br: Point;
        bl: Point;

        constructor(tl: Point, tr: Point, br: Point, bl: Point) {
            this.tl = tl;
            this.tr = tr;
            this.br = br;
            this.bl = bl;
        }
    }

    export class PixelBuffer {
        width: number;
        height: number;
        channels: number;
        interleaved: boolean;
        data: Uint8Array;

        constructor(width: number, height: number, channels: number, interleaved: boolean, data: Uint8Array) {
            this.width = width;
            this.height = height;
            this.channels = channels;
            this.interleaved = interleaved;
            this.data = data;
        }
    }

    export async function perspectiveTransform(img: PixelBuffer, quad: Quadrilateral): Promise<PixelBuffer> {
        let x = perspective_transform(
            img.width,
            img.height,
            img.channels,
            img.interleaved,
            img.data,
            Float32Array.from([
                quad.tl.x,
                quad.tl.y,
                quad.tr.x,
                quad.tr.y,
                quad.br.x,
                quad.br.y,
                quad.bl.x,
                quad.bl.y,
            ])
        );
        const dv = new DataView(x.buffer);
        const w = dv.getUint32(0, true);
        const h = dv.getUint32(4, true);
        const c = dv.getUint8(8);
        const interleaved = dv.getUint8(9) > 0;
        const data = x.subarray(10);
        return new PixelBuffer(w, h, c, interleaved, data);
    }

    async function setup_wasm() {
        try {
            let wasmBuffer;
            if (process.env.NODE_ENV !== "production") {
                    let path = await import('path');
                    let fs = await import('fs');
                    const wasmPath = path.resolve(__dirname, g_wasm_path ?? "../../static/wasm/hybridocr.wasm");
                    wasmBuffer = fs.readFileSync(wasmPath);
            } else {
                const r = await fetch(g_wasm_path ?? "/static/wasm/hybridocr.wasm");
                if (!r.ok) {
                    throw new Error(r.statusText);
                }

                wasmBuffer = await r.arrayBuffer();
            }
            let imports = {};
            g_wasm = await WebAssembly.instantiate(wasmBuffer, imports);
        } catch (e) {
            g_wasm = null;
            throw e;
        }
    }

    export async function get_wasm(): Promise<WebAssembly.WebAssemblyInstantiatedSource> {
        if (g_wasm_init == null) {
            g_wasm_init = (async () => {
                await setup_wasm();
            })();
        }
        try {
            await g_wasm_init;
        } catch (e) {
            g_wasm_init = null;
            throw e;
        }
        if (!g_wasm) {
            throw new Error("Failed to initialize wasm");
        }
        return g_wasm;
    }
}



(async () => {
    await util.get_wasm();
})();
