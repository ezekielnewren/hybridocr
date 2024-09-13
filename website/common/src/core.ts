export const greet = (name: string) => `Hello, ${name}!`;


import { PDFDocument } from 'pdf-lib';
import * as fs from 'fs';

// Load and extract images from the PDF file
async function extractImagesFromPDF(pdfPath: string): Promise<Buffer[]> {
  const pdfBytes = fs.readFileSync(pdfPath);
  const pdfDoc = await PDFDocument.load(pdfBytes);

  const imageBuffers: Buffer[] = [];

  for (let i = 0; i < pdfDoc.getPageCount(); i++) {
    const page = pdfDoc.getPage(i);
    const images = page.node?.imageResources || [];

    for (const image of images) {
      // Assuming images can be extracted as JPEG or PNG
      const imageBuffer = image.toBuffer();
      imageBuffers.push(imageBuffer);
    }
  }

  return imageBuffers;
}



