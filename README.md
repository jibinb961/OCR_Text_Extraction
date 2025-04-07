# Document Scanning and OCR System

A Python-based application for scanning and extracting text and key data points from documents including invoices, receipts, and handwritten notes.

## Features

- Document scanning and image processing
- Text extraction using Tesseract OCR
- Data parsing to extract key information (dates, totals, addresses, phone numbers, emails, etc.)
- User-friendly web interface built with Flask
- Image preprocessing for improved OCR accuracy

## Requirements

- Python 3.8+
- Tesseract OCR engine
- Flask
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository
   ```
   git clone <repository-url>
   cd OCR
   ```

2. Create and activate a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install the required packages
   ```
   pip install -r requirements.txt
   ```

4. Install Tesseract OCR engine:
   - On macOS: `brew install tesseract`
   - On Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - On Windows: Download the installer from [here](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

1. Start the Flask application:
   ```
   python app.py
   ```

2. Open a web browser and navigate to `http://localhost:5000`

3. Upload a document image to extract text and data

4. View and edit the extracted data

## Project Structure

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
│   ├── uploads/         # User uploaded documents (not tracked by Git)
│   └── processed/       # Processed images (not tracked by Git)
│
├── templates/           # HTML templates
│
├── utils/
│   ├── ocr.py           # OCR functionality
│   ├── preprocessing.py # Image preprocessing
│   └── parser.py        # Data parsing
│
└── tests/               # Testing suite
```

## Development

The project follows a structured development approach with stages tracked in `progress_tracker.md`. 

## Testing

Run the tests using:
```
python -m unittest tests/test_ocr.py
```

## License

MIT License 