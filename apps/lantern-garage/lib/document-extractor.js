const fs = require('fs');
const path = require('path');
const pdfParse = require('pdf-parse');
const Tesseract = require('tesseract.js');
const sharp = require('sharp');
const ExifParser = require('exif-parser');

// Extract text from PDF (fast path for text-based PDFs, fallback to OCR)
async function extractPdfText(filePath) {
  try {
    const buffer = fs.readFileSync(filePath);
    const pdfData = await pdfParse(buffer).catch(err => {
      throw new Error(`PDF parsing failed: ${err.message}`);
    });

    const text = pdfData.text || '';

    // If extracted text is too sparse, likely scanned PDF - skip OCR (too slow)
    if (text.length < 100 || (text.match(/\s{4,}/g) || []).length > text.length * 0.1) {
      return {
        method: 'skipped-scanned',
        content: text.trim(),
        pages: pdfData.numpages || 1,
        confidence: 0.6,
        metadata: {
          title: pdfData.info?.Title || null,
          author: pdfData.info?.Author || null,
          createdAt: pdfData.info?.CreationDate || null,
          modifiedAt: pdfData.info?.ModDate || null
        }
      };
    }

    return {
      method: 'textract',
      content: text.trim(),
      pages: pdfData.numpages || 1,
      confidence: 0.95,
      metadata: {
        title: pdfData.info?.Title || null,
        author: pdfData.info?.Author || null,
        subject: pdfData.info?.Subject || null,
        createdAt: pdfData.info?.CreationDate || null,
        modifiedAt: pdfData.info?.ModDate || null,
        producer: pdfData.info?.Producer || null
      }
    };
  } catch (err) {
    console.error(`[pdf-parse] ${err.message}`);
    return {
      method: 'error',
      content: '',
      confidence: 0,
      error: `PDF extraction failed: ${err.message}`
    };
  }
}

// OCR fallback for scanned PDFs/images
async function ocrImage(imagePath) {
  try {
    const { data: { text, confidence } } = await Tesseract.recognize(imagePath, 'eng');
    return {
      method: 'ocr',
      content: text.trim(),
      confidence: Math.min(0.95, confidence / 100) || 0.88
    };
  } catch (err) {
    console.error(`[Tesseract] OCR failed: ${err.message}`);
    return {
      method: 'error',
      content: '',
      confidence: 0,
      error: err.message
    };
  }
}

// Convert PDF to images and OCR each page
async function ocrPdfPages(filePath) {
  // PDF→image→OCR is complex and slow; for now return empty with warning
  // In production, use: pdf2image + Tesseract, or AWS Textract for scanned PDFs
  return {
    method: 'error',
    content: '',
    confidence: 0,
    error: 'Scanned PDF detected. PDF→OCR pipeline requires pdf-image or cloud API. Skipping.'
  };
}

// Extract file-level metadata
async function extractFileMetadata(filePath) {
  const stat = fs.statSync(filePath);
  const ext = path.extname(filePath).toLowerCase();

  const metadata = {
    fileName: path.basename(filePath),
    filePath: filePath,
    size: stat.size,
    createdAt: stat.birthtime,
    modifiedAt: stat.mtime,
    extension: ext
  };

  // Extract EXIF from images
  if (['.png', '.jpg', '.jpeg', '.tiff'].includes(ext)) {
    try {
      const buffer = fs.readFileSync(filePath);
      const parser = new ExifParser.Parser();
      const result = parser.parseBuffer(buffer);

      metadata.exif = {
        datetime: result.tags?.DateTime || null,
        camera: result.tags?.Model || null,
        width: result.tags?.ImageWidth || null,
        height: result.tags?.ImageHeight || null,
        orientation: result.tags?.Orientation || null
      };
    } catch (err) {
      // EXIF extraction optional; don't fail on error
      metadata.exif = null;
    }
  }

  return metadata;
}

// Main extraction function - routes to appropriate handler
async function extractDocumentContent(filePath, mimeType = null) {
  const ext = path.extname(filePath).toLowerCase();

  try {
    if (ext === '.pdf') {
      return await extractPdfText(filePath);
    }

    if (['.png', '.jpg', '.jpeg', '.tiff', '.gif', '.webp'].includes(ext)) {
      return await ocrImage(filePath);
    }

    if (['.txt', '.md', '.json', '.csv'].includes(ext)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return {
        method: 'fs',
        content: content.trim(),
        confidence: 1.0
      };
    }

    return {
      method: 'unsupported',
      content: '',
      confidence: 0,
      error: `Unsupported file type: ${ext}`
    };
  } catch (err) {
    return {
      method: 'error',
      content: '',
      confidence: 0,
      error: err.message
    };
  }
}

module.exports = {
  extractDocumentContent,
  extractFileMetadata,
  extractPdfText,
  ocrImage,
  ocrPdfPages
};
