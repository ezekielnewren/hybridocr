import { describe, expect, test } from 'vitest'
// import * as util from "../src/util.js"
import * as util from "../src/util.js"
import sharp, { Metadata } from "sharp";
// import {perspectiveTransform} from "../src/util.js";
import crypto from "crypto";

describe("util", () => {

    test("rustargon2", async () => {
        const test_vector: [string, string, number, number, number, number, string][] = [
            // ["abc123", "saltsaltsaltsalt", 8, 100000, 1, 8, "805ef5742dad2e5d"],
            // ["abc123", "saltsaltsaltsalt", 65536, 100, 1, 8, "4ac02cad101aef49"],
            ["password", "saltsaltsaltsalt", 8192, 10, 1, 8, "60d5d3728e906b8e"],
            ["abc", "saltsaltsaltsalt", 8, 1, 1, 16, "3c71ee188cea4be3ba175abaaa42325f"],
            ["abc", "saltsaltsaltsalt", 16, 1, 2, 16, "459b0fe92c28b3144d7c35565b0a0273"],
            ["abc", "saltsaltsaltsalt", 16, 1, 1, 16, "072b33b2b051a76df8380e9ed94dc4c5"],
            ["123456", "wdvnasldkfarealdfg", 32, 100, 4, 8, "fd809746448b8335"],
        ]


        const e = new TextEncoder();
        try {
            await util.argon2id(e.encode("a"), e.encode("asdf"), 1, 1, 1, 1);
            expect.fail("These parameters are invalid and this should throw an error");
        } catch (e) {
            expect(e).not.toBeNull();
        }

        for (const v of test_vector) {
            const password = e.encode(v[0]);
            let salt = e.encode(v[1]);

            const start = performance.now();
            let result = await util.argon2id(password, salt, v[2], v[3], v[4], v[5]);
            const time = (performance.now()-start)/1000;

            const view = result.encoded();
            const actual = util.toHex(result.hash, true);
            expect(actual).toBe(v[6]);
        }
    })

    test("testPerspectiveTransform", async () => {
        let path = "../../tests/file/ocr_sample_from_smartphone_rgb.avif";
        let img = sharp(path);
        let meta = await img.metadata();
        let raw = Uint8Array.from(await img.raw().toBuffer());

        let apb = new util.PixelBuffer(
            meta.width as number,
            meta.height as number,
            meta.channels as number,
            raw
        );

        let aq = new util.Quadrilateral(
            new util.Point(50.0,   335.0),
            new util.Point(1076.0, 305.0),
            new util.Point(1130.0, 1688.0),
            new util.Point(29.0,   1690.0)
        );

        const start = performance.now();
        let out = await util.perspective_transform(apb, aq);
        const time = (performance.now()-start)/1000;
        expect(out).not.toBeNull();
        let xxx = Buffer.from(out.data);
        let xx = sharp(xxx, {
            raw: {
                width: out.width,
                height: out.height,
                channels: out.channels as 1 | 3 | 4 | 2,
            }
        });
        await xx.avif().toFile("/tmp/output.avif");
    })
    
    test("hkdf", async () => {
        // okm, hash, ikm, salt, info, length
        let tv: [string, string, string, string, string, number][] = [
            [
                "e00f9e18a24f2ae769846de7e5c65380981a0fd324c7e371340cb9a5454b01e4",
                "SHA-512",
                "048458114dafd3d7b3de4aef7a2cf7ba",
                util.toHex("salt", true) as string,
                util.toHex("info", true) as string,
                32
            ],
            [
                "b4c206dd9156c18d29598ffccbf0a64c0325c0b131144d7d1a09fa84ccbfdd20",
                "SHA-384",
                "bd8857d2500f6a136b4d02aad3a5dfca",
                util.toHex("salt", true) as string,
                util.toHex("info", true) as string,
                32
            ],
            // https://datatracker.ietf.org/doc/html/rfc5869#appendix-A
            [
                "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865",
                "SHA-256",
                "0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b",
                "000102030405060708090a0b0c",
                "f0f1f2f3f4f5f6f7f8f9",
                42
            ],
            [
                "b11e398dc80327a1c8e7f78c596a49344f012eda2d4efad8a050cc4c19afa97c59045a99cac7827271cb41c65e590e09da3275600c2f09b8367793a9aca3db71cc30c58179ec3e87c14c01d5c1f3434f1d87",
                "SHA-256",
                "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f404142434445464748494a4b4c4d4e4f",
                "606162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeaf",
                "b0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedfe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff",
                82
            ],
            [
                "8da4e775a563c18f715f802a063c5a31b8a11f5c5ee1879ec3454e5f3c738d2d9d201395faa4b61a96c8",
                "SHA-256",
                "0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b",
                "",
                "",
                42
            ],
            [
                "085a01ea1b10f36933068b56efa5ad81a4f14b822f5b091568a9cdd4f155fda2c22e422478d305f3f896",
                "SHA-1",
                "0b0b0b0b0b0b0b0b0b0b0b",
                "000102030405060708090a0b0c",
                "f0f1f2f3f4f5f6f7f8f9",
                42
            ],
            [
                "0bd770a74d1160f7c9f12cd5912a06ebff6adcae899d92191fe4305673ba2ffe8fa3f1a4e5ad79f3f334b3b202b2173c486ea37ce3d397ed034c7f9dfeb15c5e927336d0441f4c4300e2cff0d0900b52d3b4",
                "SHA-1",
                "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f404142434445464748494a4b4c4d4e4f",
                "606162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeaf",
                "b0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedfe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff",
                82
            ],
            [
                "0ac1af7002b3d761d1e55298da9d0506b9ae52057220a306e07b6b87e8df21d0ea00033de03984d34918",
                "SHA-1",
                "0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b",
                "",
                "",
                42
            ],
            [
                "2c91117204d745f3500d636a62f64f0ab3bae548aa53d423b0d1f27ebba6f5e5673a081d70cce7acfc48",
                "SHA-1",
                "0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c",
                "",
                "",
                42
            ]
        ];


        for (const [answer, hash_algorithm, input_keying_material, hkdf_salt, hkdf_info, okm_length] of tv) {
            let params: HkdfParams = {
                name: "HKDF",
                hash: hash_algorithm,
                info: util.fromHex(hkdf_info),
                salt: util.fromHex(hkdf_salt),
            };

            let t0 = util.fromHex(input_keying_material);
            let t1 = await crypto.subtle.importKey("raw", t0, "HKDF", false, ["deriveKey", "deriveBits"]);
            let okm = await crypto.subtle.deriveBits(params, t1, okm_length*8);
            let actual = util.toHex(new Uint8Array(okm), true) as string;

            expect(actual).toBe(answer);
        }
    });
    

});
