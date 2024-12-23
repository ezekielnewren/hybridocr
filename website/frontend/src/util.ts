
export namespace util {
    // const ptr_size: number = 4;

    let g_wasm: WebAssembly.WebAssemblyInstantiatedSource | null = null;
    let g_wasm_init: Promise<void> | null = null;
    let g_wasm_path: string | null = null;


    function check_type(value: any, type: any) {
        if (typeof type === "function") {
            if (value instanceof type || typeof value === type.name.toLowerCase()) {
                return;
            }
            throw new TypeError(`Type mismatch: Expected ${type.name}, but received ${typeof value}`);
        }

        if (typeof type === "string") {
            if (typeof value === type.toLowerCase()) {
                return;
            }
            throw new TypeError(`Type mismatch: Expected ${type}, but received ${typeof value}`);
        }

        throw new Error("Invalid type passed to check_type");
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


    export class Data {
        public wasm: any;
        _ptr: bigint;
        _len: bigint;

        private constructor(wasm: any, ptr: bigint, len: bigint) {
            check_type(ptr, BigInt);
            check_type(len, BigInt);
            this.wasm = wasm;
            this._ptr = ptr;
            this._len = len;
        }

        static new(wasm: any, len: bigint) {
            check_type(len, BigInt);
            return this.from_pointer(wasm, wasm.malloc(Number(len)));
        }

        static from_pointer(wasm: any, ptr: any) {
            let len = wasm.memory_length(ptr);
            return new Data(wasm, BigInt(ptr), BigInt(len));
        }

        static from(wasm: any, src: Uint8Array) {
            let t = this.new(wasm, BigInt(src.length));
            t.as_Uint8Array().set(src);
            return t;
        }

        to(off?: number, len?: number) {
            off = off || 0;
            len = len || this.len();
            let t = new Uint8Array(this.len());
            t.set(this.as_Uint8Array().subarray(off, off+len));
            return t;
        }

        ptr() {
            return Number(this._ptr);
        }

        len() {
            return Number(this._len)
        }

        as_Uint8Array(): Uint8Array {
            return new Uint8Array(this.wasm.memory.buffer, Number(this._ptr), Number(this._len));
        }

        as_DataView(): DataView {
            return new DataView(this.wasm.memory.buffer, Number(this._ptr), Number(this._len));
        }

        free() {
            this.wasm.free(Number(this._ptr));
        }


    }


    async function argon2(_password: Uint8Array, _salt: Uint8Array, m: number, t: number, p: number, length: number, str_type: string, lambda: any) {
        const wasm = (await get_wasm()).instance.exports as any;
        let password = Data.from(wasm, _password);
        let salt = Data.from(wasm, _salt);

        const result = Data.from_pointer(wasm, lambda(password.ptr(), salt.ptr(), m, t, p, length));
        let hash = result.to();
        result.free();

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
        const wasm = (await get_wasm()).instance.exports as any;

        let _data = Data.from(wasm, img.data);
        // let t = Float32Array.from([
        //         quad.tl.x,
        //         quad.tl.y,
        //         quad.tr.x,
        //         quad.tr.y,
        //         quad.br.x,
        //         quad.br.y,
        //         quad.bl.x,
        //         quad.bl.y,
        //     ]);
        let _quad = Data.new(wasm, BigInt(4*8));
        let _dv = _quad.as_DataView();
        let off = 0;
        _dv.setFloat32(off, quad.tl.x, true); off += 4;
        _dv.setFloat32(off, quad.tl.y, true); off += 4;
        _dv.setFloat32(off, quad.tr.x, true); off += 4;
        _dv.setFloat32(off, quad.tr.y, true); off += 4;
        _dv.setFloat32(off, quad.br.x, true); off += 4;
        _dv.setFloat32(off, quad.br.y, true); off += 4;
        _dv.setFloat32(off, quad.bl.x, true); off += 4;
        _dv.setFloat32(off, quad.bl.y, true);

        let raw = wasm.perspective_transform(
            img.width,
            img.height,
            img.channels,
            img.interleaved ? 1 : 0,
            _data.ptr(),
            _quad.ptr()
        );
        let result = Data.from_pointer(wasm, raw);

        const dv = result.as_DataView();
        const w = dv.getUint32(0, true);
        const h = dv.getUint32(4, true);
        const c = dv.getUint8(8);
        const interleaved = dv.getUint8(9) > 0;
        const data = result.to(10);
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
