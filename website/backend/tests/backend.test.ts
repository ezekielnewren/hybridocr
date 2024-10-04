import { describe, expect, test } from 'vitest'
import { string2bytes, bytes2string, b64encode } from "common";

import * as vision from '@google-cloud/vision';
import * as backend from "../src/backend";

describe('Google Vision', () => {
    const client = new vision.ImageAnnotatorClient();



    test('run ocr', async () => {

    });
});


describe("backend", () => {

    test("get config", async () => {
        const x: backend.HybridocrConfig = await backend.getConfig();
        expect(x).not.toBeNull();
    })

    test("open database", async () => {
        const config: backend.HybridocrConfig = await backend.getConfig();
        const db = await backend.openDatabase(config);
        await db.close();
    })

    test("open redis", async () => {
        const config: backend.HybridocrConfig = await backend.getConfig();
        const client = await backend.openRedis(config);
        let vector = ["key", "value"];

        await client.set(vector[0], vector[1]);
        expect(await client.get(vector[0])).toBe(vector[1]);

        await client.disconnect();
    })

    test("use common", async () => {
        const actual = b64encode(string2bytes("Man"));
        const expected = string2bytes("TWFu");
        expect(actual).toStrictEqual(expected);
    })

})


