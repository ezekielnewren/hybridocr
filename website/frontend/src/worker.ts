import * as Comlink from "comlink";

const workerAPI = {
    add(a: number, b: number): number {
        return a + b;
    }
}

Comlink.expose(workerAPI);
