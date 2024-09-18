import * as vision from '@google-cloud/vision';

async function performOcr(client: vision.ImageAnnotatorClient, base64Image: string): Promise<any> {
    const [result] = await client.textDetection({ image: { content: base64Image } });
    return result;
}

