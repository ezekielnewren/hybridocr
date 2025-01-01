import * as Comlink from "comlink";

let g_static_prefix = "/static/";
export function set_static_prefix(x: string) {
    g_static_prefix = x;
}


interface WorkerAPI {
    setup(url: string): Promise<void>;
    _argon2(alg: number, password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number): Promise<any>;
    _perspective_transform(_image: any, _quad: any): Promise<any>;
}


class WasmWorker {
    private static instance: Promise<WasmWorker>;
    worker: Worker = new Worker(g_static_prefix+"js/wasm.js", { type: "module" });
    workerAPI = Comlink.wrap<WorkerAPI>(this.worker);

    private constructor() {}

    public api() {
        return this.workerAPI;
    }

    public static async getInstance() {
        if (!WasmWorker.instance) {
            WasmWorker.instance = new Promise<WasmWorker>(async (resolve)=> {
                let t = new WasmWorker();
                await t.api().setup(g_static_prefix+"wasm/hybridocr_bg.wasm");
                resolve(t);
            });
        }
        return await WasmWorker.instance;
    }
}



export function assert(condition: boolean, message?: string) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
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

export async function argon2d(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
    let w = await WasmWorker.getInstance();
    let result = await w.api()._argon2(0, password, salt, m, t, p, length);
    if (typeof result === "string") {
        throw new Error(result);
    }
    return new Argon2Result("argon2d", 19, m, t, p, salt, result);
}

export async function argon2i(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
    let w = await WasmWorker.getInstance();
    let result = await w.api()._argon2(1, password, salt, m, t, p, length);
    if (typeof result === "string") {
        throw new Error(result);
    }
    return new Argon2Result("argon2i", 19, m, t, p, salt, result);
}

export async function argon2id(password: Uint8Array, salt: Uint8Array, m: number, t: number, p: number, length: number) {
    let w = await WasmWorker.getInstance();
    let result = await w.api()._argon2(2, password, salt, m, t, p, length);
    if (typeof result === "string") {
        throw new Error(result);
    }
    return new Argon2Result("argon2id", 19, m, t, p, salt, result);
}

const HEX_ALPHABET = [
    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
    0x61, 0x62, 0x63, 0x64, 0x65, 0x66
];
const MAP_HEX = new Map<number, number>([
    [0x30, 0], [0x31, 1], [0x32, 2], [0x33, 3], [0x34, 4],
    [0x35, 5], [0x36, 6], [0x37, 7], [0x38, 8], [0x39, 9],
    [0x61, 10], [0x62, 11], [0x63, 12], [0x64, 13], [0x65, 14], [0x66, 15],
    [0x41, 10], [0x42, 11], [0x43, 12], [0x44, 13], [0x45, 14], [0x46, 15]
]);


export function toHex(data: string | Uint8Array, as_string: boolean): string | Uint8Array {
    if (typeof data === "string") {
        data = new TextEncoder().encode(data);
    }
    const out = new Uint8Array(data.length*2);
    for (let i = 0; i < data.length; i++) {
        let v = data[i];
        out[i*2]   = HEX_ALPHABET[v>>4];
        out[i*2+1] = HEX_ALPHABET[v&0x0f];
    }
    if (as_string) {
        return new TextDecoder().decode(out);
    }
    return out;
}

export function fromHex(data: string | Uint8Array): Uint8Array {
    if (typeof data === "string") {
        data = new TextEncoder().encode(data);
    }

    const out = new Uint8Array(data.length/2);
    for (let i = 0; i < out.length; i++) {
        const a = MAP_HEX.get(data[i*2]);
        const b = MAP_HEX.get(data[i*2+1]);
        if (a === undefined || b === undefined) {
            throw new Error("Illegal character");
        }
        out[i] = (a << 4) | b;
    }
    return out;
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
    let w = await WasmWorker.getInstance();
    let result = await w.api()._perspective_transform(img, quad);
    if (typeof result === "string") {
        throw new Error(result);
    }
    return result;
}

export function escapeHtml(unsafe: string): string {
    // https://stackoverflow.com/a/6234804
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

export async function register(_id: string | null, email: string | null) {
    if (_id == null && email == null) {
        throw new Error("must supply _id or email");
    }

    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    let require_email = _id == null;
    if ((require_email || email != null) && !emailPattern.test(email as string)) {
        throw new Error("Invalid email address");
    }

    let data: Record<string, string> = {};
    if (_id != null) {
        data["_id"] = _id;
    }
    if (email != null) {
        data["email"] = email;
    }

    const response = await fetch('/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (response.ok) {
        return {success: true}
    } else {
        throw new Error(`Failed to submit email: ${response.status} ${response.statusText}`);
    }
}

export class Showcase {
    element: HTMLElement;
    image: string | File | null;
    ocr: any | null;
    isDragging: boolean;
    resizeStyle: string;

    constructor(element: HTMLElement) {
        this.element = element;
        this.image = null;
        this.ocr = null;
        this.isDragging = false;
        this.resizeStyle = "all-scroll";

        // setup ui behavior
        const tabButtonList = this.element.querySelectorAll<HTMLButtonElement>(".tab-button")!;
        for (const tabButton of tabButtonList) {
            const eTextArea = this.element.querySelector<HTMLTextAreaElement>("textarea")!;

            tabButton.addEventListener("click", () => {
                tabButtonList.forEach(btn => btn.classList.remove("active"));
                tabButton.classList.add("active");

                const type = tabButton.getAttribute("data-tab");
                if (this.ocr == null) {
                    eTextArea.value = "No data yet";
                } else if (type === "text") {
                    eTextArea.value = this.ocr.fullTextAnnotation.text;
                } else if (type === "json") {
                    eTextArea.value = JSON.stringify(this.ocr, null, 2);
                } else {
                    throw new Error("invalid tab button type");
                }
            })
        }
        tabButtonList.item(0).click();

        const eShowcaseDivider = this.element.querySelector<HTMLDivElement>(".showcase-divider")!;
        if (eShowcaseDivider != null) {
            const computedStyle = window.getComputedStyle(this.element); // Get computed styles
            const flexDirection = computedStyle.getPropertyValue('flex-direction');
            if (flexDirection === "row") {
                this.resizeStyle = "ew-resize";
            } else if (flexDirection === "column") {
                this.resizeStyle = "ns-resize";
            }

            const eImage = this.element.querySelector<HTMLDivElement>(".showcase-image")!;
            const eText = this.element.querySelector<HTMLDivElement>(".showcase-text")!;

            eShowcaseDivider.addEventListener("mousedown", (e) => {
                this.isDragging = true;
                document.body.style.cursor = this.resizeStyle;
            })

            eShowcaseDivider.addEventListener("mouseenter", () => {
                document.body.style.cursor = this.resizeStyle;
            });

            eShowcaseDivider.addEventListener("mouseleave", () => {
                if (!this.isDragging) {
                    document.body.style.cursor = 'default';
                }
            })

            document.addEventListener("mouseup", () => {
                this.isDragging = false;
                document.body.style.cursor = "default";
            })

            document.addEventListener("mousemove", (e) => {
                if (!this.isDragging) return;

                const rect = this.element.getBoundingClientRect();
                const offX = e.clientX - (rect.left + eShowcaseDivider.getBoundingClientRect().width / 2);

                const minWidth = .02;

                const imageWidth = Math.max(offX / rect.width, minWidth);
                const textWidth = Math.max((rect.width - offX) / rect.width, minWidth);

                eImage.style.flex = `0 0 ${imageWidth * 100}%`;
                eText.style.flex = `0 0 ${textWidth * 100}%`;
            });
        }
    }

    getActiveTab() {
        let t = this.element.querySelectorAll<HTMLButtonElement>(".tab-button");
        for (const tabButton of t) {
            if (tabButton.classList.contains("active")) {
                return tabButton;
            }
        }
        throw new Error("no tab buttons found");
    }

    setImage(_image: string | File | null) {
        const eImage = this.element.querySelector<HTMLImageElement>("img")!;
        this.image = _image;
        if (this.image == null) {
            eImage.src = "";
        } else if (typeof this.image === "string") {
            eImage.src = this.image;
        } else if (this.image instanceof File) {
            if (this.image.type.startsWith("image/")) {
                eImage.src = URL.createObjectURL(this.image);
            } else {
                eImage.src = "";
                const m = this.image.type;
                this.image = null;
                throw new Error(`Unsupported file type ${m}`)
            }
        } else {
            throw new Error("Invalid type for image");
        }
    }

    getImage() {
        return this.image;
    }

    setOcr(_ocr: any) {
        this.ocr = _ocr;
        this.getActiveTab().click();
    }

}

export function setErrorMessage(msg: string) {
    console.log(msg);
    const e = document.getElementById("error-message");
    if (e != null) {
        e.innerText = msg;
        e.style.display = "block";
    }
}

export function clearErrorMessage() {
    const e = document.getElementById("error-message");
    if (e != null) {
        e.innerText = "No errors";
        e.style.display = "none";
    }
}
