import { describe, expect, test } from 'vitest'
// import * as util from "../src/util.js"
import * as util from "../src/util.js"
import sharp, { Metadata } from "sharp";
// import {perspectiveTransform} from "../src/util.js";

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
            const actual = util.toHex(result.hash);
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


});
