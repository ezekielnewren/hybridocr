// Import the Google Cloud Vision library
import vision from '@google-cloud/vision';

// Import the fs module if needed to load local images
import * as fs from 'fs';

// Function to detect text in an image
async function detectText(imagePath: string) {
  // Initialize the Vision client with the credentials
  const client = new vision.ImageAnnotatorClient({
    keyFilename: 'path-to-your-service-account-file.json',  // Update with the path to your JSON credentials file
  });

  // Make an API request for text detection
  const [result] = await client.textDetection(imagePath);

  // Extract text annotations (recognized text)
  const detections = result.textAnnotations;
  if (detections && detections.length > 0) {
    console.log('Text found:');
    detections.forEach(text => console.log(text.description));
  } else {
    console.log('No text found in the image.');
  }
}

// Call the function with the image path
detectText('path-to-your-image-file.jpg'); // Replace with your image path
