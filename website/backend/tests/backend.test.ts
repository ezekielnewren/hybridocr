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

})


