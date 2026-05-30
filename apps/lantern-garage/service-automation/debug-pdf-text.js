const pdfParse = require('pdf-parse');
const fs = require('fs');

async function debugPDF(pdfPath) {
  try {
    const dataBuffer = fs.readFileSync(pdfPath);
    const data = await pdfParse(dataBuffer);
    
    console.log('=== PDF TEXT CONTENT ===\n');
    console.log(data.text);
    console.log('\n=== END PDF TEXT ===\n');
    
    console.log('Number of pages:', data.numpages);
    console.log('Text length:', data.text.length);
    
    // Save raw text to file
    fs.writeFileSync('raw-pdf-text.txt', data.text);
    console.log('Raw text saved to raw-pdf-text.txt');
    
  } catch (error) {
    console.error('Error:', error.message);
  }
}

const pdfPath = process.argv[2];
if (!pdfPath) {
  console.log('Usage: node debug-pdf-text.js <path-to-pdf>');
  process.exit(1);
}

debugPDF(pdfPath);
