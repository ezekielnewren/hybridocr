import init, { _perspective_transform, _argon2id } from "hybridocr"


async function setup_wasm() {
    if (typeof window === "undefined") {
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
        let hash = _argon2id(password, salt, m, t, p, length);
        return new Argon2Result("argon2id", 19, m, t, p, salt, hash);
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

        to_array() {
            return new Float32Array([
                this.tl.x,
                this.tl.y,
                this.tr.x,
                this.tr.y,
                this.br.x,
                this.br.y,
                this.bl.x,
                this.bl.y,
            ]);
        }
    }

    export class PixelBuffer {
        width: number;
        height: number;
        channels: number;
        data: Uint8Array;

        constructor(width: number, height: number, channels: number, data: Uint8Array) {
            this.width = width;
            this.height = height;
            this.channels = channels;
            this.data = data;
        }
    }

    export async function perspective_transform(img: PixelBuffer, quad: Quadrilateral) {
        return _perspective_transform(img, quad);
    }

    export async function setup_wasm() {

    }

    export function get_util() {
        return util;
    }
}



(async () => {
    await util.setup_wasm();
})();
