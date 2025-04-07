"""
Data Parser Module

This module handles parsing and extracting structured information from OCR text.
"""

import re
import logging
from typing import Dict, List, Any, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataParser:
    def __init__(self):
        """Initialize the data parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse the extracted text to identify invoice structure.
        
        Args:
            text (str): The extracted text from OCR.
            
        Returns:
            Dict[str, Any]: Dictionary containing parsed data.
        """
        try:
            # Split text into lines
            lines = text.split('\n')
            
            # Initialize result dictionary
            result = {
                'extracted_text': text,
                'invoice_data': {},
                'table_data': None,
                'summary_data': []
            }
            
            # Extract invoice table and metadata
            invoice_data, table_data, summary_data = self._extract_invoice_structure(lines)
            
            result['invoice_data'] = invoice_data
            result['table_data'] = table_data
            result['summary_data'] = summary_data
            
            return result
        except Exception as e:
            logger.error(f"Error parsing text: {e}")
            return {'extracted_text': text}
    
    def _extract_invoice_structure(self, lines: List[str]) -> Tuple[Dict[str, str], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Extract invoice structure including header info, table data, and summary.
        
        Args:
            lines (List[str]): List of text lines from OCR.
            
        Returns:
            Tuple containing invoice metadata, table data, and summary data.
        """
        invoice_data = {}
        table_data = {
            'headers': [],
            'rows': []
        }
        summary_data = []
        
        # Search for invoice number
        invoice_number = None
        for line in lines:
            invoice_match = re.search(r'INVOICE\s*(?:NUMBER|NO|#)?\s*[:#]?\s*([A-Z0-9\-]+)', line, re.IGNORECASE)
            if invoice_match:
                invoice_number = invoice_match.group(1).strip()
                invoice_data['invoice_number'] = invoice_number
                break
        
        # Search for date information
        for line in lines:
            date_match = re.search(r'Date\s*[:]\s*(.*)', line)
            if date_match:
                invoice_data['date'] = date_match.group(1).strip()
            
            due_date_match = re.search(r'Due\s*Date\s*[:]\s*(.*)', line)
            if due_date_match:
                invoice_data['due_date'] = due_date_match.group(1).strip()
        
        # Search for customer information
        to_section_start = None
        to_section_end = None
        
        for i, line in enumerate(lines):
            if re.search(r'^To\s*$', line, re.IGNORECASE):
                to_section_start = i + 1
            elif to_section_start and not line.strip():
                to_section_end = i
                break
        
        if to_section_start and to_section_end:
            customer_info = ' '.join([lines[i].strip() for i in range(to_section_start, to_section_end)])
            invoice_data['customer'] = customer_info
        
        # Find table headers and data rows
        table_start = None
        table_end = None
        headers = []
        
        # Look for common invoice table headers
        header_patterns = [
            r'(Date|Time)\s+(Description|Item|Service)\s+(Quantity|Qty)?\s*(Rate|Price|Cost)?\s*(Amount|Charges|Total)',
            r'(Description|Item|Service)\s+(Date|Time)?\s+(Quantity|Qty)?\s*(Rate|Price|Cost)?\s*(Amount|Charges|Total)',
            r'(Date)\s+(Description)\s+(Charges)'  # Specifically for your example
        ]
        
        for i, line in enumerate(lines):
            for pattern in header_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Found the header row
                    table_start = i
                    headers = self._extract_headers(line)
                    table_data['headers'] = headers
                    break
            if table_start is not None:
                break
        
        # If we found headers, look for the data rows
        if table_start is not None:
            # Start looking for rows after header line
            current_line = table_start + 1
            data_rows = []
            
            while current_line < len(lines):
                line = lines[current_line].strip()
                
                # Skip empty lines
                if not line:
                    current_line += 1
                    continue
                
                # Check if we've reached summary section (Subtotal, Total, etc.)
                if any(summary_term in line.lower() for summary_term in ['subtotal', 'total', 'vat', 'tax', 'balance']):
                    table_end = current_line
                    break
                
                # Try to parse this as a data row
                row_data = self._parse_table_row(line, headers)
                if row_data:
                    data_rows.append(row_data)
                
                current_line += 1
            
            table_data['rows'] = data_rows
        
        # Extract summary section (after table)
        if table_end is not None:
            current_line = table_end
            
            while current_line < len(lines):
                line = lines[current_line].strip()
                
                # Try to extract summary item (like "Subtotal $366")
                summary_match = re.search(r'(Subtotal|VAT|Tax|Balance|Total|Grand Total|Due)[\s\(]?[^$]*[\)\s:]*\s*[$]?(\d+(?:,\d{3})*(?:\.\d{2})?)', line, re.IGNORECASE)
                
                if summary_match:
                    item = summary_match.group(1).strip()
                    amount = summary_match.group(2).strip()
                    
                    # Handle VAT percentage if present
                    vat_match = re.search(r'VAT\s*\(\s*(\d+(?:\.\d+)?)\s*%\s*\)', line, re.IGNORECASE)
                    if vat_match:
                        item = f"VAT ({vat_match.group(1)}%)"
                    
                    summary_data.append({
                        'item': item,
                        'amount': amount
                    })
                
                current_line += 1
        
        return invoice_data, table_data, summary_data
    
    def _extract_headers(self, header_line: str) -> List[str]:
        """
        Extract headers from the header line of a table.
        
        Args:
            header_line (str): Line containing the headers.
            
        Returns:
            List[str]: List of header names.
        """
        # Common header patterns
        patterns = [
            (r'Date', 'Date'),
            (r'Description|Item|Service', 'Description'),
            (r'Quantity|Qty', 'Quantity'),
            (r'Rate|Price|Cost', 'Rate'),
            (r'Amount|Charges|Total', 'Amount')
        ]
        
        headers = []
        remaining_line = header_line
        
        for pattern, header_name in patterns:
            match = re.search(pattern, remaining_line, re.IGNORECASE)
            if match:
                headers.append(header_name)
                # Remove the matched part to avoid re-matching
                start, end = match.span()
                remaining_line = remaining_line[:start] + ' ' * (end - start) + remaining_line[end:]
        
        # If no patterns matched, just split by whitespace
        if not headers:
            headers = [h for h in header_line.split() if h.strip()]
        
        return headers
    
    def _parse_table_row(self, line: str, headers: List[str]) -> Dict[str, str]:
        """
        Parse a table row into structured data based on headers.
        
        Args:
            line (str): Line to parse as a table row.
            headers (List[str]): Table headers.
            
        Returns:
            Dict[str, str]: Dictionary of column values, or None if not a valid row.
        """
        # If we have a date column, look for a date pattern at the start
        if 'Date' in headers and not re.match(r'\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4}|\d{1,2}[-/\.]\d{2,4}', line):
            # Special case for MM-DD-YY format in your example
            if not re.match(r'\d{2}[-/\.]\d{2}[-/\.]\d{2}', line):
                return None
        
        # Try to find a price/amount at the end
        amount_match = re.search(r'[$](\d+(?:,\d{3})*(?:\.\d{2})?)$', line)
        if not amount_match:
            return None
        
        # If we got here, this likely is a data row
        row_data = {}
        
        if len(headers) >= 3 and 'Date' in headers and 'Description' in headers and ('Amount' in headers or 'Charges' in headers):
            # For format like: "12-08-29 Cleaning $30"
            date_match = re.match(r'(\d{2}[-/\.]\d{2}[-/\.]\d{2})\s+(.+?)\s+[$](\d+(?:,\d{3})*(?:\.\d{2})?)$', line)
            
            if date_match:
                date = date_match.group(1)
                description = date_match.group(2).strip()
                amount = date_match.group(3)
                
                row_data = {
                    'Date': date,
                    'Description': description,
                    'Amount': amount
                }
            else:
                # Try more general approach
                parts = line.split('$')
                if len(parts) >= 2:
                    before_amount = parts[0].strip()
                    amount = parts[1].strip()
                    
                    # Try to split the before_amount part into date and description
                    before_parts = before_amount.split(' ', 1)
                    if len(before_parts) >= 2:
                        date_part = before_parts[0].strip()
                        description_part = before_parts[1].strip()
                        
                        row_data = {
                            'Date': date_part,
                            'Description': description_part,
                            'Amount': amount
                        }
        
        return row_data 