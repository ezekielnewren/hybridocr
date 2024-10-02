import { describe, expect, test } from 'vitest'

import * as vision from '@google-cloud/vision';
import * as backend from "../src/backend";
import * as assert from "node:assert";
// import assert from "assert";

describe('Google Vision', () => {
    const client = new vision.ImageAnnotatorClient();



    test('run ocr', async () => {

    });
});


describe("backend", () => {

    test("get config", async () => {
        const x: backend.HybridocrConfig = await backend.getConfig();
        assert.ok(x);
    })

    test("open database", async () => {
        const db = await backend.openDatabase();
        await db.close();
    })
})


