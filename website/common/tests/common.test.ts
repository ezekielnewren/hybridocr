import { expect, test } from 'vitest'

import * as common from "../src/common";

test('core test', async () => {

})

test('random iv', async () => {
    const iv = common.getRandomIV();
    expect(iv).not.toBeNull();
})


test("base64", async () => {

    const test_vector = [
        [new Uint8Array([255, 255, 255]), common.string2bytes("____")],
        [new Uint8Array([255, 255]), common.string2bytes("__8")],
        [new Uint8Array([255]), common.string2bytes("_w")],
        [new Uint8Array([0, 0, 0]), common.string2bytes("AAAA")],
        [new Uint8Array([0, 0]), common.string2bytes("AAA")],
        [new Uint8Array([0]), common.string2bytes("AA")],
        [common.string2bytes("Ma"), common.string2bytes("TWE")],
        [common.string2bytes("Hello?"), common.string2bytes("SGVsbG8_")],
        [common.string2bytes("Hello>"), common.string2bytes("SGVsbG8-")],
        [common.string2bytes("Man"), common.string2bytes("TWFu")],
        [common.string2bytes("M"), common.string2bytes("TQ")],
        [common.string2bytes("light work."), common.string2bytes("bGlnaHQgd29yay4")],
        [common.string2bytes("apple"), common.string2bytes("YXBwbGU")],
        [common.string2bytes("banana"), common.string2bytes("YmFuYW5h")],
        [common.string2bytes("cherry"), common.string2bytes("Y2hlcnJ5")],
        [common.string2bytes("dog"), common.string2bytes("ZG9n")],
        [common.string2bytes("elephant"), common.string2bytes("ZWxlcGhhbnQ")],
        [common.string2bytes("falcon"), common.string2bytes("ZmFsY29u")],
        [common.string2bytes("grape"), common.string2bytes("Z3JhcGU")],
        [common.string2bytes("house"), common.string2bytes("aG91c2U")],
        [common.string2bytes("igloo"), common.string2bytes("aWdsb28")],
        [common.string2bytes("jungle"), common.string2bytes("anVuZ2xl")],
    ]

    // const vector = ["Man", "TWFu"];
    test_vector.forEach((v, i) => {
        const a0 = common.b64encode(v[0]);
        const e0 = v[1];
        expect(a0).toStrictEqual(e0);
        const a1 = common.b64decode(e0);
        const e1 = v[0];
        expect(a1).toStrictEqual(e1);
    });
})


