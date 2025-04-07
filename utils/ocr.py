"""
OCR Utility Module

This module handles the OCR (Optical Character Recognition) functionality using Tesseract.
It extracts text from preprocessed images.
"""

import pytesseract
import os
from PIL import Image
import logging
import numpy as np
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, tesseract_cmd=None):
        """
        Initialize the OCR processor.
        
        Args:
            tesseract_cmd (str, optional): Path to the Tesseract executable.
                If not provided, it will use the default system path.
        """
        # Configure Tesseract path if provided
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        # Verify Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR is properly configured.")
        except Exception as e:
            logger.error(f"Error initializing Tesseract OCR: {e}")
            logger.error("Please ensure Tesseract is installed and the path is correct.")
    
    def extract_text(self, image_path):
        """
        Extract text from an image using Tesseract OCR.
        
        Args:
            image_path (str): Path to the image file.
            
        Returns:
            str: Extracted text from the image.
        """
        try:
            # Open the image using PIL
            image = Image.open(image_path)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Log success
            logger.info(f"Successfully extracted text from {image_path}")
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {e}")
            return ""
    
    def extract_text_from_image(self, image):
        """
        Extract text from an already loaded image.
        
        Args:
            image: The image (PIL.Image or numpy array).
            
        Returns:
            str: Extracted text from the image.
        """
        try:
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image)
            
            # Log success
            logger.info("Successfully extracted text from image")
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def extract_structured_data(self, image):
        """
        Extract structured data like tables from an image.
        
        Args:
            image: The image (PIL.Image or numpy array).
            
        Returns:
            dict: Structured data extracted from the image.
        """
        try:
            # Extract data with hOCR format (HTML with position info)
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Process the data to identify tables and structured content
            processed_data = self._process_structured_data(data)
            
            # Log success
            logger.info("Successfully extracted structured data from image")
            
            return processed_data
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {}
    
    def _process_structured_data(self, data):
        """
        Process the raw OCR data to identify tables and structured content.
        
        Args:
            data (dict): Raw OCR data from Tesseract.
            
        Returns:
            dict: Processed structured data.
        """
        try:
            # Initialize result dictionary
            result = {
                'text_blocks': [],
                'tables': [],
                'lines': []
            }
            
            # Group words into lines based on y-coordinates
            current_line = []
            current_y = None
            line_height = None
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if not text:
                    continue
                
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = data['conf'][i]
                
                # If this is the first word or close to the current line
                if current_y is None or abs(y - current_y) < h * 0.5:
                    if current_y is None:
                        current_y = y
                        line_height = h
                    current_line.append({
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'confidence': conf
                    })
                else:
                    # Start a new line
                    if current_line:
                        result['lines'].append(current_line)
                    current_line = [{
                        'text': text,
                        'x': x,
                        'y': y,
                        'width': w,
                        'height': h,
                        'confidence': conf
                    }]
                    current_y = y
                    line_height = h
            
            # Add the last line
            if current_line:
                result['lines'].append(current_line)
            
            # Identify potential tables
            result['tables'] = self._identify_tables(result['lines'])
            
            return result
        except Exception as e:
            logger.error(f"Error processing structured data: {e}")
            return {}
    
    def _identify_tables(self, lines):
        """
        Identify potential tables in the OCR data.
        
        Args:
            lines (list): List of lines, each containing word data.
            
        Returns:
            list: Identified tables.
        """
        try:
            tables = []
            current_table = []
            
            # Sort lines by y-coordinate
            sorted_lines = sorted(lines, key=lambda line: line[0]['y'])
            
            for line in sorted_lines:
                # Check if this line has multiple columns (words with significant x-gaps)
                words = sorted(line, key=lambda word: word['x'])
                if len(words) > 1:
                    # Calculate average gap between words
                    gaps = []
                    for i in range(len(words) - 1):
                        gap = words[i + 1]['x'] - (words[i]['x'] + words[i]['width'])
                        gaps.append(gap)
                    
                    avg_gap = sum(gaps) / len(gaps) if gaps else 0
                    
                    # If gaps are significant, this might be a table row
                    if avg_gap > 20:  # Threshold for column separation
                        current_table.append(line)
                    else:
                        if current_table:
                            tables.append(current_table)
                            current_table = []
                else:
                    if current_table:
                        tables.append(current_table)
                        current_table = []
            
            # Add the last table if exists
            if current_table:
                tables.append(current_table)
            
            return tables
        except Exception as e:
            logger.error(f"Error identifying tables: {e}")
            return [] 