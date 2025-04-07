"""
Data Parser Module

This module handles parsing and extracting structured information from OCR text using LLM inference.
"""

import json
import logging
import os
import requests
import re
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataParser:
    def __init__(self):
        """Initialize the data parser."""
        self.logger = logging.getLogger(__name__)
        
        # Get API key from environment
        self.api_key = os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set. LLM parsing will not work.")
        
        # Groq API endpoint
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        # System prompt for invoice parsing
        self.system_prompt = """
You are an invoice data extraction expert. Your task is to extract structured information from invoice text.
Carefully analyze the text and extract the following information:

1. Invoice metadata (invoice number, date, due date, etc.)
2. Customer information (name, address, contact details)
3. Vendor information (name, address, contact details)
4. Table of items/services (with headers and rows)
5. Summary information (subtotal, tax, total, etc.)

Return ONLY a JSON object with the following structure:
{
    "invoice_data": {
        "invoice_number": "",
        "date": "",
        "due_date": "",
        "customer_name": "",
        "customer_address": "",
        "vendor_name": "",
        "vendor_address": ""
    },
    "table_data": {
        "headers": ["Item", "Description", "Quantity", "Unit Price", "Amount"],
        "rows": [
            {"Item": "1", "Description": "Example Item", "Quantity": "2", "Unit Price": "10.00", "Amount": "20.00"}
        ]
    },
    "summary_data": [
        {"item": "Subtotal", "amount": "100.00"},
        {"item": "Tax", "amount": "10.00"},
        {"item": "Total", "amount": "110.00"}
    ]
}

Do not include any explanations or text outside of the JSON object. If a specific field is not found in the invoice, leave it as an empty string or exclude it. Ensure the JSON is valid and properly formatted.
"""
    
    def parse_text(self, text: str) -> Dict[str, Any]:
        """
        Parse the extracted text using LLM inference to extract structured invoice data.
        
        Args:
            text (str): The extracted text from OCR.
            
        Returns:
            Dict[str, Any]: Dictionary containing parsed invoice data.
        """
        try:
            # Check if API key is available
            if not self.api_key:
                logger.error("GROQ_API_KEY not set. Cannot perform LLM parsing.")
                return {'extracted_text': text}
            
            # Prepare result with extracted text
            result = {
                'extracted_text': text
            }
            
            # Get structured data from LLM
            parsed_data = self._query_llm(text)
            if parsed_data:
                # Update result with parsed data
                result.update(parsed_data)
            
            return result
        except Exception as e:
            logger.error(f"Error parsing text with LLM: {e}")
            return {'extracted_text': text}
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON data from text that might contain additional content.
        
        Args:
            text (str): Text that might contain JSON.
            
        Returns:
            Optional[Dict[str, Any]]: Extracted JSON object or None if not found.
        """
        # First try direct JSON parsing
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # If direct parsing fails, try to find JSON object in the text
            logger.info("Direct JSON parsing failed, trying to extract JSON from text")
            
            # Try to find JSON object using regex
            json_pattern = r'({[\s\S]*})'
            matches = re.findall(json_pattern, text)
            
            if matches:
                # Try each potential JSON match
                for potential_json in matches:
                    try:
                        # Try to parse this as JSON
                        parsed_json = json.loads(potential_json)
                        
                        # Verify this is an invoice JSON with expected structure
                        if isinstance(parsed_json, dict) and any(key in parsed_json for key in ['invoice_data', 'table_data', 'summary_data']):
                            logger.info("Successfully extracted JSON from text")
                            return parsed_json
                    except json.JSONDecodeError:
                        continue
            
            # If regex approach failed, try to find start/end of JSON
            try:
                start_idx = text.find('{')
                if start_idx != -1:
                    # Find matching closing brace
                    brace_count = 0
                    for i in range(start_idx, len(text)):
                        if text[i] == '{':
                            brace_count += 1
                        elif text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                # Found potential JSON object
                                potential_json = text[start_idx:i+1]
                                try:
                                    parsed_json = json.loads(potential_json)
                                    # Verify this is an invoice JSON
                                    if isinstance(parsed_json, dict) and any(key in parsed_json for key in ['invoice_data', 'table_data', 'summary_data']):
                                        logger.info("Successfully extracted JSON by brace matching")
                                        return parsed_json
                                except json.JSONDecodeError:
                                    pass
            except Exception as e:
                logger.error(f"Error in brace matching approach: {e}")
            
            logger.error("Failed to extract JSON from text")
            return None
    
    def _query_llm(self, text: str) -> Dict[str, Any]:
        """
        Query the LLM API to extract structured data from invoice text.
        
        Args:
            text (str): Text to analyze.
            
        Returns:
            Dict[str, Any]: Structured data extracted from the text.
        """
        try:
            # Prepare request headers
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Prepare request payload
            payload = {
                "model": "llama3-70b-8192",  # Using Llama 3 70B model
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Extract structured information from this invoice text:\n\n{text}"}
                ],
                "temperature": 0.1,  # Low temperature for deterministic results
                "max_tokens": 4000
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            # Check if request was successful
            if response.status_code == 200:
                response_data = response.json()
                
                # Extract content from response
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    content = response_data['choices'][0]['message']['content'].strip()
                    
                    # Try to extract JSON from the content
                    parsed_json = self._extract_json_from_text(content)
                    
                    if parsed_json:
                        logger.info("Successfully parsed invoice data using LLM")
                        return parsed_json
                    else:
                        logger.error("Could not extract valid JSON from LLM response")
                        logger.error(f"Raw response: {content}")
                        return {}
                else:
                    logger.error("No content found in LLM API response")
                    return {}
            else:
                logger.error(f"API request failed with status code {response.status_code}")
                logger.error(f"Response: {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error querying LLM API: {e}")
            return {} 