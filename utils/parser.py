"""
Data Parser Module

This module extracts structured information from OCR text, including dates, amounts, 
addresses, and other key data points from documents like invoices and receipts.
"""

import re
import logging
from dateutil import parser as date_parser
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataParser:
    def __init__(self):
        """Initialize the data parser."""
        logger.info("Data parser initialized")
    
    def parse_text(self, text):
        """
        Parse OCR text to extract key information.
        
        Args:
            text (str): The OCR text to parse.
            
        Returns:
            dict: Dictionary of extracted data.
        """
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
    
    def extract_dates(self, text):
        """
        Extract dates from text.
        
        Args:
            text (str): Text to extract dates from.
            
        Returns:
            list: List of extracted dates.
        """
        try:
            # Common date patterns
            date_patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # DD/MM/YYYY, MM/DD/YYYY, etc.
                r'\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{2,4}',  # 01 January 2023
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{1,2}[,]?\s\d{2,4}'  # January 01, 2023
            ]
            
            # Find all dates in text
            dates = []
            for pattern in date_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    date_str = match.group()
                    try:
                        # Parse date string to date object
                        parsed_date = date_parser.parse(date_str, fuzzy=True)
                        dates.append({
                            'date_str': date_str,
                            'parsed': parsed_date.strftime('%Y-%m-%d'),
                            'position': match.span()
                        })
                    except Exception as e:
                        logger.debug(f"Failed to parse date '{date_str}': {e}")
            
            logger.info(f"Extracted {len(dates)} dates from text")
            return dates
        except Exception as e:
            logger.error(f"Error extracting dates: {e}")
            return []
    
    def extract_amounts(self, text):
        """
        Extract monetary amounts from text.
        
        Args:
            text (str): Text to extract amounts from.
            
        Returns:
            list: List of extracted amounts.
        """
        try:
            # Currency symbol followed by numbers or numbers followed by currency symbol
            amount_patterns = [
                r'[$€£¥]\s?\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
                r'\d+(?:,\d{3})*(?:\.\d{2})?\s?[$€£¥]',  # 1,234.56$
                r'(?:USD|EUR|GBP|JPY)\s?\d+(?:,\d{3})*(?:\.\d{2})?',  # USD 1,234.56
                r'\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|GBP|JPY)'   # 1,234.56 USD
            ]
            
            # Find all amounts in text
            amounts = []
            for pattern in amount_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    amount_str = match.group()
                    # Extract numeric value
                    numeric_value = re.search(r'\d+(?:,\d{3})*(?:\.\d{2})?', amount_str).group()
                    numeric_value = numeric_value.replace(',', '')
                    
                    # Extract currency
                    currency = None
                    if '$' in amount_str:
                        currency = 'USD'
                    elif '€' in amount_str:
                        currency = 'EUR'
                    elif '£' in amount_str:
                        currency = 'GBP'
                    elif '¥' in amount_str:
                        currency = 'JPY'
                    elif 'USD' in amount_str:
                        currency = 'USD'
                    elif 'EUR' in amount_str:
                        currency = 'EUR'
                    elif 'GBP' in amount_str:
                        currency = 'GBP'
                    elif 'JPY' in amount_str:
                        currency = 'JPY'
                    
                    amounts.append({
                        'amount_str': amount_str,
                        'numeric_value': float(numeric_value),
                        'currency': currency,
                        'position': match.span()
                    })
            
            logger.info(f"Extracted {len(amounts)} monetary amounts from text")
            return amounts
        except Exception as e:
            logger.error(f"Error extracting amounts: {e}")
            return []
    
    def extract_addresses(self, text):
        """
        Extract addresses from text.
        
        Args:
            text (str): Text to extract addresses from.
            
        Returns:
            list: List of extracted addresses.
        """
        try:
            # Match common address patterns
            address_patterns = [
                # Street, City, State ZIP
                r'\d+\s[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct)[\w\s,]+\d{5}(?:-\d{4})?',
                # PO Box
                r'P\.?O\.?\s?Box\s\d+'
            ]
            
            # Find all addresses in text
            addresses = []
            for pattern in address_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    addresses.append({
                        'address': match.group().strip(),
                        'position': match.span()
                    })
            
            logger.info(f"Extracted {len(addresses)} addresses from text")
            return addresses
        except Exception as e:
            logger.error(f"Error extracting addresses: {e}")
            return []
    
    def extract_emails(self, text):
        """
        Extract email addresses from text.
        
        Args:
            text (str): Text to extract emails from.
            
        Returns:
            list: List of extracted email addresses.
        """
        try:
            # Email pattern
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            
            # Find all emails in text
            emails = []
            matches = re.finditer(email_pattern, text)
            for match in matches:
                emails.append({
                    'email': match.group(),
                    'position': match.span()
                })
            
            logger.info(f"Extracted {len(emails)} email addresses from text")
            return emails
        except Exception as e:
            logger.error(f"Error extracting emails: {e}")
            return []
    
    def extract_phone_numbers(self, text):
        """
        Extract phone numbers from text.
        
        Args:
            text (str): Text to extract phone numbers from.
            
        Returns:
            list: List of extracted phone numbers.
        """
        try:
            # Improved phone number patterns
            phone_patterns = [
                r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 (123) 456-7890
                r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',                   # (123) 456-7890
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',                          # 123-456-7890
                r'Call us:.*?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',         # Call us: (123) 456-7890
                r'Support:.*?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'                # Support: 123-456-7891
            ]
            
            # Find all phone numbers in text
            phones = []
            for pattern in phone_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    matched_text = match.group()
                    # Extract just the phone number portion if there's additional text
                    phone_number = matched_text
                    if ':' in matched_text:
                        # Extract just the phone number after the colon
                        phone_number = re.search(r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})', matched_text)
                        if phone_number:
                            phone_number = phone_number.group(1)
                        else:
                            continue
                    
                    phones.append({
                        'phone': phone_number.strip(),
                        'position': match.span()
                    })
            
            logger.info(f"Extracted {len(phones)} phone numbers from text")
            return phones
        except Exception as e:
            logger.error(f"Error extracting phone numbers: {e}")
            return []
    
    def extract_invoice_numbers(self, text):
        """
        Extract invoice numbers from text.
        
        Args:
            text (str): Text to extract invoice numbers from.
            
        Returns:
            list: List of extracted invoice numbers.
        """
        try:
            # Invoice number patterns
            invoice_patterns = [
                r'(?:Invoice|INV)[-:#\s]*\d+',  # Invoice: 12345
                r'(?:Invoice|INV)[-:#\s]*[A-Z0-9-]+'  # Invoice: ABC-12345
            ]
            
            # Find all invoice numbers in text
            invoices = []
            for pattern in invoice_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    invoices.append({
                        'invoice_number': match.group(),
                        'position': match.span()
                    })
            
            logger.info(f"Extracted {len(invoices)} invoice numbers from text")
            return invoices
        except Exception as e:
            logger.error(f"Error extracting invoice numbers: {e}")
            return []
    
    def extract_item_descriptions(self, text):
        """
        Extract item descriptions and prices from text (for invoices/receipts).
        
        Args:
            text (str): Text to extract item descriptions from.
            
        Returns:
            list: List of extracted item descriptions.
        """
        try:
            # Split text into lines
            lines = text.split('\n')
            items = []
            
            # Pattern for price
            price_pattern = r'\d+(?:,\d{3})*(?:\.\d{2})?'
            
            for line in lines:
                # Skip short lines
                if len(line.strip()) < 5:
                    continue
                
                # Look for lines with a price
                price_match = re.search(price_pattern, line)
                if price_match:
                    price_str = price_match.group()
                    price_start, price_end = price_match.span()
                    
                    # Extract item description (text before the price)
                    description = line[:price_start].strip()
                    if description:
                        items.append({
                            'description': description,
                            'price': price_str,
                            'line': line.strip()
                        })
            
            logger.info(f"Extracted {len(items)} item descriptions from text")
            return items
        except Exception as e:
            logger.error(f"Error extracting item descriptions: {e}")
            return []
    
    def to_json(self, parsed_data):
        """
        Convert parsed data to JSON format.
        
        Args:
            parsed_data (dict): Parsed data.
            
        Returns:
            str: JSON string.
        """
        try:
            # Convert date objects to strings for JSON serialization
            clean_data = parsed_data.copy()
            
            # Convert to JSON
            json_str = json.dumps(clean_data, indent=2)
            return json_str
        except Exception as e:
            logger.error(f"Error converting to JSON: {e}")
            return "{}" 