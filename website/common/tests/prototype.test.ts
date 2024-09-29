// https://github.com/ldclabs/cose-ts

// import * as utils from "@ldclabs/cose-ts/utils";
import { bytesToHex, utf8ToBytes, randomBytes, compareBytes } from '@ldclabs/cose-ts/utils';

test('test salt', () => {
  const salt = randomBytes(16);
  console.log(bytesToHex(salt));
});
