export const greet = (name: string) => `Hello, ${name}!`;

import {PDFDict, PDFDocument, PDFName, PDFRawStream, PDFStream} from 'pdf-lib';
import { Jimp } from 'jimp';

export async function extractImagesFromPDF(pdfBuffer: Uint8Array): Promise<object[]> {
  let result: object[] = [];

  const pdfDoc = await PDFDocument.load(pdfBuffer);

  for (let pageIndex = 0; pageIndex < pdfDoc.getPageCount(); pageIndex++) {
    const page = pdfDoc.getPage(pageIndex);
    const res = page.node.Resources();
    if (!res) continue;
    const xObjects = res.entries();

    for (const [_, obj] of xObjects) {
      const objdict = obj as PDFDict;
      for (const [_, v] of objdict.entries()) {
        const stream = pdfDoc.context.lookup(v) as PDFRawStream;
        const blob = stream?.getContents();
        const image = await Jimp.fromBuffer(blob);
        result.push(image);
      }
    }
  }

  return result;
}

