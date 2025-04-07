# OCR Document Scanner - Project Documentation

## Project Overview
The OCR Document Scanner is a Python-based application designed to extract text and structured data from document images. It provides a complete solution for scanning, processing, and extracting information from various document types like invoices, receipts, and handwritten notes.

## Key Features
- Upload and process document images through a user-friendly web interface
- Apply advanced image preprocessing to enhance OCR accuracy
- Extract text from documents using Tesseract OCR
- Parse extracted text to identify key data points (dates, amounts, contact information, etc.)
- Display results in a structured, easy-to-understand format
- RESTful API for integration with other systems

## Technical Architecture
The application follows a modular architecture with clearly separated components:

![System Architecture](https://i.imgur.com/4AJG2Xg.png)

### Components
1. **Web Application (app.py)**
   - Flask-based web server
   - User interface for document upload and results display
   - Orchestrates the document processing workflow
   - [Detailed Documentation](exp_app.md)

2. **Image Preprocessor (utils/preprocessing.py)**
   - Enhances image quality for better OCR results
   - Implements algorithms for resizing, grayscale conversion, thresholding, noise removal, and deskewing
   - [Detailed Documentation](exp_preprocessing.md)

3. **OCR Processor (utils/ocr.py)**
   - Extracts text from processed images
   - Interfaces with Tesseract OCR engine
   - [Detailed Documentation](exp_ocr.md)

4. **Data Parser (utils/parser.py)**
   - Analyzes extracted text to identify structured data
   - Uses pattern matching for dates, amounts, addresses, emails, etc.
   - [Detailed Documentation](exp_parser.md)

5. **Testing Framework (tests/test_ocr.py)**
   - Validates component functionality
   - Ensures correct data extraction
   - [Detailed Documentation](exp_tests.md)

## Data Flow
The system processes documents through the following steps:

1. **Document Upload**: User uploads a document image through the web interface
2. **Image Preprocessing**: The image is enhanced to improve OCR accuracy
3. **Text Extraction**: Tesseract OCR extracts text from the processed image
4. **Data Parsing**: The extracted text is analyzed to identify structured data
5. **Results Display**: The original image, processed image, extracted text, and parsed data are presented to the user

## User Interface
The web interface consists of two main pages:

1. **Upload Page (index.html)**
   - Simple form for document upload
   - Supported file types information
   - How-it-works overview

2. **Results Page (result.html)**
   - Side-by-side display of original and processed images
   - Complete extracted text
   - Categorized data cards for different types of extracted information

## Installation and Setup

### Requirements
- Python 3.8 or higher
- Tesseract OCR engine
- Dependencies listed in requirements.txt

### Installation Steps
1. Clone the repository
2. Create and activate a virtual environment
3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Install Tesseract OCR engine (platform-specific)
5. Run the application:
   ```
   python app.py
   ```

## API Reference

### Document Processing Endpoint
- **URL**: `/api/extract`
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Request Body**:
  - `file`: The document image file
- **Response**:
  ```json
  {
    "file_id": "unique-id",
    "extracted_text": "Raw OCR text...",
    "parsed_data": {
      "dates": [...],
      "amounts": [...],
      "addresses": [...],
      "emails": [...],
      "phone_numbers": [...],
      "invoice_numbers": [...],
      "item_descriptions": [...]
    }
  }
  ```

## Development Information

### Project Structure
```
OCR/
│
├── app.py               # Main Flask application
├── requirements.txt     # Project dependencies
├── progress_tracker.md  # Development progress tracking
├── .gitignore           # Git ignore file
│
├── static/              # Static files (CSS, JS, images)
│   ├── css/             # CSS stylesheets
│   ├── uploads/         # User uploaded documents
│   └── processed/       # Processed images
│
├── templates/           # HTML templates
│   ├── base.html        # Base template with common elements
│   ├── index.html       # Upload page
│   └── result.html      # Results display page
│
├── utils/
│   ├── __init__.py      # Package initialization
│   ├── ocr.py           # OCR functionality
│   ├── preprocessing.py # Image preprocessing
│   └── parser.py        # Data parsing
│
└── tests/               # Testing suite
    ├── __init__.py      # Test package initialization
    ├── test_ocr.py      # OCR system tests
    └── test_data/       # Test data directory
```

### Component Documentation
- [Web Application (app.py)](exp_app.md)
- [Image Preprocessor (preprocessing.py)](exp_preprocessing.md)
- [OCR Processor (ocr.py)](exp_ocr.md)
- [Data Parser (parser.py)](exp_parser.md)
- [Testing Framework (test_ocr.py)](exp_tests.md)

## Testing
Run the tests using:
```
python -m unittest tests/test_ocr.py
```

The test suite verifies:
- Correct initialization of components
- Date extraction functionality
- Amount extraction functionality
- Email extraction functionality
- Phone number extraction functionality

## Future Enhancements
- Machine learning-based document classification
- Template matching for specific document types
- Improved handwriting recognition
- Client-side image preprocessing using JavaScript
- User accounts and document history
- Export functionality (PDF, CSV, JSON)

## Troubleshooting

### Common Issues
1. **Tesseract Not Found**: Ensure Tesseract is installed and the path is correct
2. **Poor OCR Results**: Try adjusting preprocessing parameters for specific document types
3. **Large File Upload Issues**: Check MAX_CONTENT_LENGTH in app configuration
4. **Permission Errors**: Ensure upload and processed directories are writable

### Logging
The application uses Python's logging module to record operations. Check logs for:
- Component initialization
- Processing steps
- Error information

## License
This project is licensed under the MIT License - see the LICENSE file for details. 