import { describe, expect, test } from 'vitest'
import * as util from "../src/util.js"

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
});
