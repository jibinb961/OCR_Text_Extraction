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
import re

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
        Extract text from an image using Tesseract OCR.
        
        Args:
            image: The image to extract text from (numpy array or PIL Image).
            
        Returns:
            str: Extracted text from the image.
        """
        try:
            # Convert to numpy array if PIL Image
            if isinstance(image, Image.Image):
                image = np.array(image)
            
            # Make a copy to avoid modifying the original
            img_for_ocr = image.copy()
            
            # Scale up the image to improve thin character recognition (especially for digit "1")
            if img_for_ocr is not None and len(img_for_ocr.shape) >= 2:
                height, width = img_for_ocr.shape[:2]
                # Scale up by 2x for better detail preservation
                img_for_ocr = cv2.resize(img_for_ocr, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
            
            # Configure Tesseract for better digit recognition
            # --oem 3: Use LSTM OCR engine
            # --psm 6: Assume a single uniform block of text
            # -c tessedit_char_whitelist: Specify allowed characters
            # -c textord_heavy_nr: Reduce noise removal to preserve thin strokes
            custom_config = r'--oem 3 --psm 6 -c textord_heavy_nr=1'
            
            # Extract text using Tesseract with improved configuration
            text = pytesseract.image_to_string(img_for_ocr, config=custom_config)
            
            # Log success
            logger.info(f"Successfully extracted text from image")
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
    def extract_structured_data(self, image):
        """
        Extract structured data from an image using Tesseract's image_to_data.
        
        Args:
            image: The image to extract data from (numpy array or PIL Image).
            
        Returns:
            dict: Dictionary containing structured data with positions and confidence levels.
        """
        try:
            # Convert to numpy array if PIL Image
            if isinstance(image, Image.Image):
                image = np.array(image)
            
            # Make a copy and scale up for better recognition
            img_for_ocr = image.copy()
            if img_for_ocr is not None and len(img_for_ocr.shape) >= 2:
                height, width = img_for_ocr.shape[:2]
                img_for_ocr = cv2.resize(img_for_ocr, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
            
            # Configure Tesseract for better structured data extraction
            custom_config = r'--oem 3 --psm 6 -c textord_heavy_nr=1'
            
            # Extract data with positions and confidence levels
            data = pytesseract.image_to_data(img_for_ocr, output_type=pytesseract.Output.DICT, config=custom_config)
            
            # Process the data to create a more usable structure
            structured_data = {
                'text': [],
                'boxes': [],
                'confidence': [],
                'lines': [],
                'tables': []
            }
            
            # Group text by line
            current_line = -1
            line_text = []
            
            for i, text in enumerate(data['text']):
                if not text.strip():
                    continue
                
                conf = int(data['conf'][i])
                if conf < 0:  # Skip entries with negative confidence
                    continue
                
                # Add text and its metadata
                structured_data['text'].append(text)
                structured_data['confidence'].append(conf)
                
                # Scale back bounding box coordinates to match original image
                x = data['left'][i] // 2
                y = data['top'][i] // 2
                w = data['width'][i] // 2
                h = data['height'][i] // 2
                structured_data['boxes'].append((x, y, w, h))
                
                # Group by line
                if data['line_num'][i] != current_line:
                    if line_text:
                        structured_data['lines'].append(' '.join(line_text))
                        line_text = []
                    current_line = data['line_num'][i]
                line_text.append(text)
            
            # Add the last line
            if line_text:
                structured_data['lines'].append(' '.join(line_text))
            
            # Try to identify table structure (rows and columns)
            # This requires more sophisticated analysis based on text positions
            # For now, we'll return the structured data without table analysis
            
            logger.info(f"Successfully extracted structured data from image")
            return structured_data
        except Exception as e:
            logger.error(f"Error extracting structured data from image: {e}")
            return {
                'text': [],
                'boxes': [],
                'confidence': [],
                'lines': [],
                'tables': []
            }
    
    def _process_ocr_data(self, data):
        """
        Process raw OCR data to group words into lines and analyze their structure.
        
        Args:
            data (dict): Raw OCR data from Tesseract
            
        Returns:
            dict: Processed data with lines and their structure
        """
        lines = []
        current_line = []
        current_y = None
        line_height = None
        
        # Process each word
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
                    lines.append(self._analyze_line_structure(current_line))
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
            lines.append(self._analyze_line_structure(current_line))
        
        return {'lines': lines}
    
    def _analyze_line_structure(self, words):
        """
        Analyze the structure of a line to identify potential columns and data types.
        
        Args:
            words (list): List of words in a line with their positions
            
        Returns:
            dict: Analyzed line structure
        """
        # Sort words by x position
        sorted_words = sorted(words, key=lambda w: w['x'])
        
        # Identify potential data types
        line_data = {
            'words': sorted_words,
            'text': ' '.join(w['text'] for w in sorted_words),
            'columns': [],
            'indentation': sorted_words[0]['x'] if sorted_words else 0
        }
        
        # Analyze each word for potential data types
        for word in sorted_words:
            text = word['text']
            
            # Check for numbers
            if re.match(r'^\d+(?:\.\d{1,2})?$', text):
                word['type'] = 'number'
                # Try to determine if it's a quantity, price, or serial number
                if '.' in text:
                    word['subtype'] = 'price'
                elif len(text) <= 2:
                    word['subtype'] = 'quantity'
                else:
                    word['subtype'] = 'serial'
            else:
                word['type'] = 'text'
                word['subtype'] = 'description'
        
        # Group words into potential columns based on spacing
        if sorted_words:
            current_column = [sorted_words[0]]
            for i in range(1, len(sorted_words)):
                prev_word = sorted_words[i-1]
                current_word = sorted_words[i]
                
                # Calculate gap between words
                gap = current_word['x'] - (prev_word['x'] + prev_word['width'])
                
                # If gap is significant, start a new column
                if gap > prev_word['width'] * 0.5:
                    line_data['columns'].append(current_column)
                    current_column = [current_word]
                else:
                    current_column.append(current_word)
            
            line_data['columns'].append(current_column)
        
        return line_data
    
    def _analyze_line_items(self, lines):
        """
        Analyze lines to identify potential line items and their relationships.
        
        Args:
            lines (list): List of analyzed lines
            
        Returns:
            list: Identified tables with line items
        """
        tables = []
        current_table = []
        current_indent = None
        
        for line in lines:
            # Check if this line is indented (potential sub-line)
            if current_indent is not None and line['indentation'] > current_indent + 20:
                # This is a sub-line of the previous line
                if current_table:
                    current_table[-1]['sub_lines'].append(line)
                continue
            
            # Check if this line looks like a line item
            if self._is_line_item(line):
                if not current_table:
                    current_table = []
                    current_indent = line['indentation']
                current_table.append({
                    'line': line,
                    'sub_lines': []
                })
            else:
                # If we have a table and this line doesn't match, end the current table
                if current_table:
                    tables.append(current_table)
                    current_table = []
                    current_indent = None
        
        # Add the last table if exists
        if current_table:
            tables.append(current_table)
        
        return tables
    
    def _is_line_item(self, line):
        """
        Determine if a line looks like a line item.
        
        Args:
            line (dict): Analyzed line structure
            
        Returns:
            bool: True if the line appears to be a line item
        """
        # A line item typically has:
        # 1. At least one number (price or quantity)
        # 2. Some descriptive text
        has_number = False
        has_text = False
        
        for word in line['words']:
            if word['type'] == 'number':
                has_number = True
            elif word['type'] == 'text':
                has_text = True
        
        return has_number and has_text 