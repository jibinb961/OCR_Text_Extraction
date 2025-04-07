# app.py - Flask Application Explanation

## Overview
`app.py` is the main entry point of the OCR Document Scanner application. It's a Flask web application that provides a user interface for uploading documents, processing them, and displaying the extracted information.

## Functionality
The script provides the following core functionality:
- Web interface for document upload
- Image processing pipeline coordination
- OCR text extraction
- Data parsing from extracted text
- Results display and visualization
- REST API endpoint for programmatic access

## Dependencies
- **Flask**: Web framework
- **Werkzeug**: Utilities for WSGI applications
- **utils.ocr.OCRProcessor**: OCR text extraction
- **utils.preprocessing.ImagePreprocessor**: Image preprocessing
- **utils.parser.DataParser**: Data parsing from text

## Configuration
The application configures:
- File upload settings (allowed file types, maximum size)
- Upload and processed file storage directories
- Logging level and format
- Secret key for session management

## Workflow

### 1. User Interface (routes)
- **/** (index): Displays the upload form
- **/upload**: Processes uploaded files
- **/result/<file_id>**: Displays processing results
- **/api/extract**: REST API endpoint

### 2. File Upload Process
1. User uploads a document through the web interface
2. System validates the file (type, size)
3. A unique ID is generated for the file
4. The file is saved to the upload directory

### 3. Image Processing
1. The uploaded image is loaded
2. The image is preprocessed using `ImagePreprocessor`
   - Converted to grayscale
   - Resized for optimal OCR
   - Noise removal
   - Deskewing (straightening)
   - Thresholding for better contrast
3. The processed image is saved to the processed directory

### 4. OCR Processing
1. The processed image is passed to `OCRProcessor`
2. Tesseract OCR extracts text from the image
3. The extracted text is stored for further processing

### 5. Data Parsing
1. The extracted text is passed to `DataParser`
2. The parser identifies and extracts:
   - Dates
   - Monetary amounts
   - Addresses
   - Email addresses
   - Phone numbers
   - Invoice numbers
   - Item descriptions

### 6. Results Display
1. The original image, processed image, extracted text, and parsed data are passed to the result template
2. The user can view the results in a structured format

### 7. API Endpoint
The application also provides a REST API endpoint (`/api/extract`) that follows the same processing workflow but returns JSON data instead of HTML.

## Error Handling
The application includes error handling for:
- Missing files
- Invalid file types
- File size limitations
- Processing errors
- Server errors

## Security Considerations
- Secure file names using `secure_filename`
- File size limitations to prevent DOS attacks
- File type validation to prevent malicious uploads
- Error handling to prevent information disclosure 