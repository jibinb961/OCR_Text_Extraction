"""
OCR Utility Module

This module handles the OCR (Optical Character Recognition) functionality using Tesseract.
It extracts text from preprocessed images.
"""

import pytesseract
import os
from PIL import Image
import logging

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
            hocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Log success
            logger.info("Successfully extracted structured data from image")
            
            return hocr_data
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {} 