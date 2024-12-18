import init, { _argon2id, _argon2i, _argon2d, perspective_transform } from "hybridocr"

export async function setup_wasm() {
    if (process.env.NODE_ENV !== "production") {
        let path = await import('path');
        let fs = await import('fs');
        const wasmPath = path.resolve(__dirname, "../../../wasm/pkg/hybridocr_bg.wasm");
        const wasmBuffer = fs.readFileSync(wasmPath);
        // @ts-ignore
        await init({module_or_path: wasmBuffer});
    } else {
        // @ts-ignore
        await init({module_or_path: "/static/wasm/hybridocr_bg.wasm"});
    }
}
await setup_wasm();

export namespace util {
    export function is_nodejs() {
        return process.env.NODE_ENV !== "production";
    }

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
}
