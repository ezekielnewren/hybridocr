import { bytesToHex, utf8ToBytes, randomBytes, compareBytes } from '@ldclabs/cose-ts/utils';


export function getRandomIV() {
    return bytesToHex(randomBytes(16));
}

