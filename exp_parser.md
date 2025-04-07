# Data Parser Module (parser.py) - Explanation

## Overview
The `DataParser` class in `utils/parser.py` is responsible for extracting structured information from OCR text. It parses raw text to identify and extract key data points like dates, monetary amounts, addresses, contact information, and invoice details.

## Functionality
This module provides the following core functionality:
- Extracting dates in various formats
- Identifying monetary amounts and currencies
- Detecting postal addresses
- Finding email addresses
- Extracting phone numbers in different formats
- Identifying invoice numbers
- Parsing item descriptions and prices
- Converting parsed data to JSON format

## Dependencies
- **re**: Standard library module for regular expressions
- **dateutil.parser**: For parsing dates in different formats
- **json**: For JSON serialization
- **logging**: Standard library module for logging

## Workflow

### 1. Initialization
When a `DataParser` object is created, it initializes logging and prepares for parsing operations.

### 2. Main Parsing Pipeline
The central method `parse_text` coordinates the entire parsing process:
1. Takes raw OCR text as input
2. Validates the input
3. Calls specialized extractors for each data type
4. Collects results into a structured dictionary
5. Returns the comprehensive parsing results

```python
def parse_text(self, text):
    if not text or not isinstance(text, str):
        logger.error("Invalid text input for parsing")
        return {}
    
    # Create result dictionary
    result = {
        'dates': self.extract_dates(text),
        'amounts': self.extract_amounts(text),
        'addresses': self.extract_addresses(text),
        'emails': self.extract_emails(text),
        'phone_numbers': self.extract_phone_numbers(text),
        'invoice_numbers': self.extract_invoice_numbers(text),
        'item_descriptions': self.extract_item_descriptions(text)
    }
    
    logger.info(f"Parsed text and extracted {sum(len(v) for v in result.values())} data points")
    return result
```

### 3. Date Extraction
The `extract_dates` method:
1. Uses multiple regular expression patterns to match different date formats
2. Extracts matched dates from the text
3. Uses `dateutil.parser` to convert string dates to standardized date objects
4. Returns a list of date information including original string, parsed date, and position

Date patterns include:
- Numeric formats (DD/MM/YYYY, MM/DD/YYYY)
- Written formats (01 January 2023)
- Month-first formats (January 01, 2023)

### 4. Amount Extraction
The `extract_amounts` method:
1. Uses multiple regex patterns to match monetary amounts
2. Handles different currency symbols and formats
3. Extracts both the numeric value and currency information
4. Returns a list of amount information including original string, numeric value, currency, and position

Currency patterns include:
- Symbol before amount ($1,234.56)
- Symbol after amount (1,234.56$)
- Currency code before/after amount (USD 1,234.56 or 1,234.56 USD)

### 5. Address Extraction
The `extract_addresses` method:
1. Uses regex patterns to match common address formats
2. Identifies addresses based on street designations, postal codes, etc.
3. Returns a list of addresses with their positions in the text

Address patterns include:
- Street addresses with postal codes
- PO Box addresses

### 6. Email Extraction
The `extract_emails` method:
1. Uses a regex pattern to identify email addresses
2. Returns a list of email addresses with their positions

The email pattern validates the standard format of local-part@domain.extension.

### 7. Phone Number Extraction
The `extract_phone_numbers` method:
1. Uses multiple regex patterns to match different phone number formats
2. Handles various separators and formats (parentheses, dashes, dots)
3. Extracts the actual phone number from text that may contain prefixes like "Call us:"
4. Returns a list of phone numbers with their positions

Phone number patterns include:
- International format (+1 (123) 456-7890)
- National format ((123) 456-7890)
- Basic format (123-456-7890)
- Contextual format (Call us: (123) 456-7890)

### 8. Invoice Number Extraction
The `extract_invoice_numbers` method:
1. Uses regex patterns to match invoice number formats
2. Identifies invoice numbers by prefixes like "Invoice:" or "INV"
3. Returns a list of invoice numbers with their positions

Invoice patterns include:
- Basic numeric (Invoice: 12345)
- Alphanumeric with separators (Invoice: ABC-12345)

### 9. Item Description Extraction
The `extract_item_descriptions` method:
1. Splits text into lines
2. Looks for lines containing price patterns
3. Extracts item descriptions (text before the price)
4. Returns a list of items with descriptions and prices

This is particularly useful for extracting line items from invoices or receipts.

### 10. JSON Conversion
The `to_json` method:
1. Takes the parsed data dictionary
2. Handles any special data types that need conversion for JSON serialization
3. Returns a JSON string representation of the data

## Implementation Details

### Regular Expressions
The parser uses carefully crafted regular expressions to match data patterns:
- Patterns are designed to balance precision and recall
- Multiple patterns are used for each data type to handle variations
- Patterns are optimized for performance

### Error Handling
The module implements comprehensive error handling:
- Each method catches exceptions to prevent crashes
- Failed extractions return empty lists rather than throwing exceptions
- Detailed error logging helps with troubleshooting

### Data Enrichment
Beyond simple extraction, the parser enhances data with:
- Position information (start and end indices in the original text)
- Parsed date objects for standardized date handling
- Extracted numeric values from amounts
- Currency identification

## Usage Examples

### Basic Text Parsing
```python
parser = DataParser()
results = parser.parse_text("Invoice #12345 dated January 15, 2023. Total: $125.99")
print(results)
```

### Integration with OCR
```python
from utils.ocr import OCRProcessor
from utils.preprocessing import ImagePreprocessor

preprocessor = ImagePreprocessor()
ocr = OCRProcessor()
parser = DataParser()

# Process image, extract text, and parse data
processed_image = preprocessor.process_image("path/to/invoice.jpg")
extracted_text = ocr.extract_text_from_image(processed_image)
parsed_data = parser.parse_text(extracted_text)

# Access specific data
dates = parsed_data['dates']
amounts = parsed_data['amounts']
invoice_numbers = parsed_data['invoice_numbers']
```

### Converting Results to JSON
```python
parser = DataParser()
parsed_data = parser.parse_text("Invoice #12345 dated January 15, 2023. Total: $125.99")
json_data = parser.to_json(parsed_data)
print(json_data)
``` 