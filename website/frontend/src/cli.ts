import loadArgon2idWasm from "argon2id";

const password = "abc123"
const start = performance.now();
const argon2id = await loadArgon2idWasm();
const result = argon2id({
    password,
    salt: "somesalt",
    parallelism: 1,
    passes: 10,
    memorySize: 8192,
    hashLen: 32,
});
const time = performance.now()-start;
console.log(time);

