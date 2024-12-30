
const worker = new Worker("worker.js");

worker.postMessage({a: 2, b: 3});

worker.onmessage = function(e) {
    console.log("Result from worker:", e.data);
}

worker.onerror = function(e) {
    console.error("Worker error:", e);
}
