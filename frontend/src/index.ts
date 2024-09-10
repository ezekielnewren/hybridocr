import * as readline from 'readline';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

async function prompt(prompt: string): Promise<string> {
    return new Promise((resolve) => {
        rl.question(prompt, (answer: string) => { resolve(answer) });
    });
}

function sqrt(n: bigint): bigint {
    if (n < 0n) {
        throw new Error("Negative numbers don't have real square roots.");
    }

    if (n === 0n || n === 1n) {
        return n;
    }

    let x = n;
    let y = (x + 1n) / 2n;
    while (y < x) {
        x = y;
        y = (x + n / x) / 2n;
    }
    return x;
}

function isPrime(number: bigint): boolean {
    if (number < 2n) {
        return false;
    }

    if (number == 2n || number == 3n) {
        return true;
    }

    if (number%2n == 0n || number%3n == 0n) {
        return false;
    }

    const max = sqrt(number);

    for (let d=5n; d<max; d+=2n) {
        if (number%d == 0n) {
            return false;
        }
    }

    return true;
}

async function main() {

    while (true) {
        const input = await prompt("integer: ");
        if (input == "exit") {
            break;
        }

        const number = BigInt(input);

        const prime = isPrime(number);

        if (prime) {
            console.log(number+" is prime");
        } else {
            console.log(number+" is composite");
        }
    }

    rl.close();
}

main().finally();

