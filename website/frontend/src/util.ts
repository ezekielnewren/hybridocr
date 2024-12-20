export namespace util {
    type Pointer = number;
    type usize = number;

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
        public ptr: Pointer;
        public len: usize;

        constructor(ptr: Pointer, len: usize) {
            this.ptr = Number(ptr);
            this.len = Number(len);
        }

        static from_u64(packed: bigint): WasmMemory {
            let ptr: Pointer = Number(packed >> 32n);
            let len: usize = Number(packed & 0xffffffffn);
            return new WasmMemory(ptr, len);
        }

        static from_Uint8Array(wasm: any, src: Uint8Array): WasmMemory {
            let dst: WasmMemory = new WasmMemory(wasm.allocate(src.length), src.length);
            dst.copy_from(wasm, src);
            return dst;
        }

        copy_from(wasm: any, src: Uint8Array) {
            let memory = new Uint8Array(wasm.memory.buffer);
            for (let i=0; i<this.len; i++) {
                memory[Number(this.ptr)+i] = src[i];
            }
        }

        copy_to(wasm: any): Uint8Array {
            let dst = new Uint8Array(Number(this.len));
            let memory = new Uint8Array(wasm.memory.buffer);
            for (let i=0; i<this.len; i++) {
                dst[i] = memory[Number(this.ptr)+i];
            }
            return dst;
        }

        free(wasm: any) {
            wasm.deallocate(this.ptr, this.len);
        }

    }


    export async function argon2id(_password: Uint8Array, _salt: Uint8Array, m: number, t: number, p: number, length: number) {
        const wasm = (await get_wasm()).instance.exports as any;

        let password = WasmMemory.from_Uint8Array(wasm, _password);
        let salt = WasmMemory.from_Uint8Array(wasm, _salt);

        const result = WasmMemory.from_u64(wasm._argon2id(password.ptr, password.len, salt.ptr, salt.len, m, t, p, length));

        let hash = result.copy_to(wasm);
        result.free(wasm);
        salt.free(wasm);
        password.free(wasm);

        return new Argon2Result("argon2id", 19, m, t, p, _salt, hash);
    }

    export async function argon2i(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
        const hash = _argon2i(password, salt, m, t, p, length);
        return new Argon2Result("argon2i", 19, m, t, p, salt, hash);
    }

    export async function argon2d(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
        const hash = _argon2d(password, salt, m, t, p, length);
        return new Argon2Result("argon2d", 19, m, t, p, salt, hash);
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
