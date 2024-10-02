import { expect, test } from 'vitest'

import * as core from "../src/core";

test('core test', async () => {

})

test('random iv', async () => {
    const iv = core.getRandomIV();
    expect(iv).not.toBeNull();
})

