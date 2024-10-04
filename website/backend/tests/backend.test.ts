import { describe, expect, test } from 'vitest'

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
        const db = await backend.openDatabase();
        await db.close();
    })

    test("open redis", async () => {
        const client = await backend.openRedis();
        let vector = ["key", "value"];

        await client.set(vector[0], vector[1]);
        expect(await client.get(vector[0])).toBe(vector[1]);

        await client.disconnect();
    })

})


