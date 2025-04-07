"""
Tests for OCR functionality.

This module contains tests for the OCR text extraction and data parsing.
"""

import os
import sys
import unittest
import logging

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ocr import OCRProcessor
from utils.preprocessing import ImagePreprocessor
from utils.parser import DataParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestOCR(unittest.TestCase):
    """Test OCR functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.ocr_processor = OCRProcessor()
        self.image_preprocessor = ImagePreprocessor()
        self.data_parser = DataParser()
        
        # Create test directory if it doesn't exist
        self.test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
        os.makedirs(self.test_dir, exist_ok=True)
    
    def test_ocr_initialization(self):
        """Test OCR processor initialization."""
        self.assertIsNotNone(self.ocr_processor)
    
    def test_image_preprocessor_initialization(self):
        """Test image preprocessor initialization."""
        self.assertIsNotNone(self.image_preprocessor)
    
    def test_data_parser_initialization(self):
        """Test data parser initialization."""
        self.assertIsNotNone(self.data_parser)
    
    def test_date_extraction(self):
        """Test date extraction from text."""
        # Sample text with dates
        sample_text = """
        Invoice Date: 01/15/2023
        Due Date: 02/15/2023
        Order Date: January 10, 2023
        """
        
        # Parse the text
        parsed_data = self.data_parser.parse_text(sample_text)
        
        # Check if dates were extracted
        self.assertIn('dates', parsed_data)
        self.assertTrue(len(parsed_data['dates']) > 0)
        
        # Check if the correct dates were extracted
        date_strings = [date['date_str'] for date in parsed_data['dates']]
        self.assertIn('01/15/2023', date_strings)
        self.assertIn('02/15/2023', date_strings)
    
    def test_amount_extraction(self):
        """Test amount extraction from text."""
        # Sample text with amounts
        sample_text = """
        Subtotal: $100.00
        Tax: $8.50
        Total: $108.50
        """
        
        # Parse the text
        parsed_data = self.data_parser.parse_text(sample_text)
        
        # Check if amounts were extracted
        self.assertIn('amounts', parsed_data)
        self.assertTrue(len(parsed_data['amounts']) > 0)
        
        # Check if the correct amounts were extracted
        amounts = [amount['numeric_value'] for amount in parsed_data['amounts']]
        self.assertIn(100.00, amounts)
        self.assertIn(8.50, amounts)
        self.assertIn(108.50, amounts)
    
    def test_email_extraction(self):
        """Test email extraction from text."""
        # Sample text with email
        sample_text = """
        Contact us at: support@example.com
        Sales: sales@example.com
        """
        
        # Parse the text
        parsed_data = self.data_parser.parse_text(sample_text)
        
        # Check if emails were extracted
        self.assertIn('emails', parsed_data)
        self.assertTrue(len(parsed_data['emails']) > 0)
        
        # Check if the correct emails were extracted
        emails = [email['email'] for email in parsed_data['emails']]
        self.assertIn('support@example.com', emails)
        self.assertIn('sales@example.com', emails)
    
    def test_phone_extraction(self):
        """Test phone number extraction from text."""
        # Sample text with phone number
        sample_text = """
        Call us: (123) 456-7890
        Support: 123-456-7891
        """
        
        # Parse the text
        parsed_data = self.data_parser.parse_text(sample_text)
        
        # Check if phone numbers were extracted
        self.assertIn('phone_numbers', parsed_data)
        self.assertTrue(len(parsed_data['phone_numbers']) > 0)
        
        # Check if the correct phone numbers were extracted
        phones = [phone['phone'] for phone in parsed_data['phone_numbers']]
        self.assertTrue(any(p for p in phones if '123' in p and '456' in p and '7890' in p))
        self.assertTrue(any(p for p in phones if '123' in p and '456' in p and '7891' in p))

if __name__ == '__main__':
    unittest.main() 