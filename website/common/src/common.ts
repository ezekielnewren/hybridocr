import { bytesToHex, utf8ToBytes, randomBytes, compareBytes } from '@ldclabs/cose-ts/utils';


export function getRandomIV() {
    return bytesToHex(randomBytes(16));
}


export function bytes2string(data: Uint8Array): string {
    return new TextDecoder().decode(data);
}


export function string2bytes(data: string): Uint8Array {
    return new TextEncoder().encode(data);
}


const b64forward = Uint8Array.from(Array.from("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_").map(letter => letter.charCodeAt(0)));
const b64reverse = Uint8Array.from({length: 127}, () => 0xff);
b64forward.forEach((v, i) => b64reverse[v] = i);

export function b64encode(data: Uint8Array): Uint8Array {
    let result = new Uint8Array(Math.ceil(data.length*4/3));

    let i = 0, j = 0;
    while (i < data.length) {
        const b0 = data[i++];
        const b1 = i<data.length ? data[i++] : 0;
        const b2 = i<data.length ? data[i++] : 0;

        // Combine the three bytes into a 24-bit number
        const combined = (b0 << 16) | (b1 << 8) | b2;

        // Break the 24-bit number into four 6-bit segments and map to Base64 chars
        result[j++] = b64forward[(combined >> 18) & 0x3f];
        result[j++] = b64forward[(combined >> 12) & 0x3f];
        if (j < result.length) result[j++] = b64forward[(combined >> 6) & 0x3f];
        if (j < result.length) result[j++] = b64forward[(combined >> 0) & 0x3f];
    }

    return result;
}

export function b64decode(data: Uint8Array): Uint8Array {
    let in_length = data.length;
    if (data[in_length-1] === '='.charCodeAt(0)) in_length--;
    if (data[in_length-1] === '='.charCodeAt(0)) in_length--;

    let result = new Uint8Array(Math.floor(in_length*3/4));

    let i = 0, j = 0;
    while (i < in_length) {
        const c0 = b64reverse[data[i++]];
        const c1 = b64reverse[data[i++]];
        const c2 = i < in_length ? b64reverse[data[i++]] : 0;
        const c3 = i < in_length ? b64reverse[data[i++]] : 0;

        const combined = (c0 << 18) | (c1 << 12) | (c2 << 6) | c3;

        result[j++] = (combined >> 16) & 0xff;
        if (j<result.length) result[j++] = (combined >> 8) & 0xff;
        if (j<result.length) result[j++] = (combined >> 0) & 0xff;
    }

    return result;
}
