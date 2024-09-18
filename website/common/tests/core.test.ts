import * as fs from 'fs';
import * as path from 'path';

// import * from '../src/core';
import * as CoreModule from '../src/core';

test('test greeter', () => {
  expect(CoreModule.greet("alice")).toBe("Hello, alice!");
});


test('extract images from pdf', async () => {
  const pdfFilePath = path.join(__dirname, 'test-assets', 'JWST generated.pdf');
  const buffer: Uint8Array = new Uint8Array(fs.readFileSync(pdfFilePath));

  const arr = await CoreModule.extractImagesFromPDF(buffer);

  expect(arr.length).toBe(3);
  expect(arr).toBeDefined()
})

test('run google ocr', async () => {

})



