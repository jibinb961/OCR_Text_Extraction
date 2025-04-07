# OCR Processor (ocr.py) - Explanation

## Overview
The `OCRProcessor` class in `utils/ocr.py` is responsible for extracting text from images using Tesseract OCR. It provides a high-level interface to interact with the Tesseract OCR engine, making it easy to extract plain text or structured data from document images.

## Functionality
This module provides the following core functionality:
- Text extraction from image files
- Text extraction from pre-loaded image data
- Structured data extraction (like tables and position data)
- Error handling for OCR operations

## Dependencies
- **pytesseract**: Python wrapper for Google's Tesseract OCR engine
- **PIL (Pillow)**: Python Imaging Library for image handling
- **logging**: Standard library module for logging

## Workflow

### 1. Initialization
When an `OCRProcessor` object is created:
1. The class checks if a custom Tesseract executable path is provided
2. It verifies that Tesseract is properly installed and accessible
3. It logs the initialization status

```python
def __init__(self, tesseract_cmd=None):
    # Configure Tesseract path if provided
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    # Verify Tesseract is installed
    try:
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR is properly configured.")
    except Exception as e:
        logger.error(f"Error initializing Tesseract OCR: {e}")
```

### 2. Text Extraction from Files
The `extract_text` method:
1. Opens an image file using PIL
2. Passes the image to Tesseract for OCR processing
3. Returns the extracted text as a string
4. Handles any errors that occur during the process

```python
def extract_text(self, image_path):
    try:
        # Open the image using PIL
        image = Image.open(image_path)
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(image)
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text: {e}")
        return ""
```

### 3. Text Extraction from Image Objects
The `extract_text_from_image` method:
1. Takes a pre-loaded image object (PIL Image or numpy array)
2. Passes it directly to Tesseract
3. Returns the extracted text
4. Handles any errors that occur

This is particularly useful when the image has already been preprocessed by another component.

### 4. Structured Data Extraction
The `extract_structured_data` method:
1. Takes an image object
2. Uses Tesseract's `image_to_data` function to extract structured data
3. Returns data in dictionary format with position information
4. This includes bounding boxes, confidence levels, and text for each detected element

## Implementation Details

### Error Handling
The OCR processor implements comprehensive error handling:
- Catches exceptions during Tesseract operations
- Logs detailed error information
- Returns empty results rather than throwing exceptions
- This makes the class robust in production environments

### Logging
Detailed logging is implemented to help with debugging and monitoring:
- Success messages for successful OCR operations
- Error messages for failed operations
- Information about the processed files

## Usage Examples

### Basic Text Extraction from File
```python
ocr = OCRProcessor()
text = ocr.extract_text("path/to/image.jpg")
print(text)
```

### Working with Preprocessed Images
```python
from preprocessing import ImagePreprocessor

preprocessor = ImagePreprocessor()
ocr = OCRProcessor()

# Preprocess and then extract text
processed_image = preprocessor.process_image("path/to/image.jpg")
text = ocr.extract_text_from_image(processed_image)
```

### Extracting Structured Data
```python
ocr = OCRProcessor()
structured_data = ocr.extract_structured_data(image)
# Access position data for each word
for i, word in enumerate(structured_data['text']):
    if word.strip():
        x = structured_data['left'][i]
        y = structured_data['top'][i]
        w = structured_data['width'][i]
        h = structured_data['height'][i]
        print(f"Word: {word}, Position: ({x}, {y}, {w}, {h})") 