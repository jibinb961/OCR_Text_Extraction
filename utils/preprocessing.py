"""
Image Preprocessing Module

This module handles various image preprocessing techniques to improve OCR accuracy,
including resizing, thresholding, noise reduction, and deskewing.
"""

import cv2
import numpy as np
import logging
from PIL import Image
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePreprocessor:
    def __init__(self):
        """Initialize the image preprocessor."""
        logger.info("Image preprocessor initialized")
    
    def load_image(self, image_path):
        """
        Load an image from a file path.
        
        Args:
            image_path (str): Path to the image file.
            
        Returns:
            numpy.ndarray: The loaded image or None if loading fails.
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Failed to load image from {image_path}")
                return None
            
            logger.info(f"Successfully loaded image from {image_path}")
            return image
        except Exception as e:
            logger.error(f"Error loading image from {image_path}: {e}")
            return None
    
    def resize_image(self, image, target_width=None, scale_factor=None):
        """
        Resize an image to improve OCR processing.
        
        Args:
            image: The image to resize (numpy.ndarray).
            target_width (int, optional): The target width to resize to.
            scale_factor (float, optional): Scale factor for resizing.
            
        Returns:
            numpy.ndarray: Resized image.
        """
        try:
            # Get original dimensions
            height, width = image.shape[:2]
            
            # Determine new dimensions
            if target_width:
                ratio = target_width / width
                new_width = target_width
                new_height = int(height * ratio)
            elif scale_factor:
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
            else:
                # Default scale factor if none provided
                scale_factor = 1.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
            
            # Resize image
            resized_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized_image
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return image
    
    def convert_to_grayscale(self, image):
        """
        Convert an image to grayscale.
        
        Args:
            image: The image to convert (numpy.ndarray).
            
        Returns:
            numpy.ndarray: Grayscale image.
        """
        try:
            # Check if image is already grayscale
            if len(image.shape) == 2:
                return image
            
            # Convert to grayscale
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            logger.info("Converted image to grayscale")
            return gray_image
        except Exception as e:
            logger.error(f"Error converting image to grayscale: {e}")
            return image
    
    def apply_thresholding(self, image, method='adaptive'):
        """
        Apply thresholding to an image to improve text contrast.
        
        Args:
            image: The grayscale image (numpy.ndarray).
            method (str): Thresholding method ('simple', 'otsu', or 'adaptive').
            
        Returns:
            numpy.ndarray: Thresholded image.
        """
        try:
            # Ensure image is grayscale
            if len(image.shape) > 2:
                image = self.convert_to_grayscale(image)
            
            # Apply thresholding based on method
            if method == 'simple':
                _, thresholded = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)
            elif method == 'otsu':
                _, thresholded = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            elif method == 'adaptive':
                thresholded = cv2.adaptiveThreshold(
                    image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
            else:
                # Default to adaptive thresholding
                thresholded = cv2.adaptiveThreshold(
                    image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
            
            logger.info(f"Applied {method} thresholding")
            return thresholded
        except Exception as e:
            logger.error(f"Error applying thresholding: {e}")
            return image
    
    def remove_noise(self, image):
        """
        Remove noise from an image.
        
        Args:
            image: The image (numpy.ndarray).
            
        Returns:
            numpy.ndarray: Noise-reduced image.
        """
        try:
            # Ensure image is grayscale
            if len(image.shape) > 2:
                image = self.convert_to_grayscale(image)
            
            # Apply noise reduction
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
            
            logger.info("Applied noise reduction")
            return denoised
        except Exception as e:
            logger.error(f"Error removing noise: {e}")
            return image
    
    def deskew(self, image):
        """
        Deskew (straighten) an image.
        
        Args:
            image: The image (numpy.ndarray).
            
        Returns:
            numpy.ndarray: Deskewed image.
        """
        try:
            # Ensure image is grayscale
            if len(image.shape) > 2:
                gray = self.convert_to_grayscale(image)
            else:
                gray = image.copy()
            
            # Apply threshold
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find all contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # Find largest contour
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            if not contours:
                logger.info("No contours found for deskewing, returning original image")
                return image
            
            # Get rotated rectangle of largest contour
            rect = cv2.minAreaRect(contours[0])
            angle = rect[2]
            
            # Improved angle adjustment logic
            # OpenCV's minAreaRect returns angles in the range [-90, 0)
            # We need to determine if we need to correct the orientation
            
            # First check if the angle is significant enough to warrant correction
            # Only rotate if the angle is more than 5 degrees off horizontal/vertical
            if abs(angle) < 5 or abs(angle + 90) < 5:
                logger.info(f"Image is already well-aligned (angle: {angle:.2f}), skipping deskew")
                return image
                
            # Correct the angle based on aspect ratio to avoid incorrect 90 degree rotations
            width, height = rect[1]
            if width < height:
                # If width < height, we're looking at a rectangle in portrait orientation
                if angle < -45:
                    angle = 90 + angle
            else:
                # Width >= height, we're looking at a rectangle in landscape orientation
                # Adjust angle to preserve the correct orientation
                if angle >= -45:
                    angle = angle
                else:
                    angle = 90 + angle
            
            # Rotate image
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            logger.info(f"Deskewed image by {angle:.2f} degrees")
            return rotated
        except Exception as e:
            logger.error(f"Error deskewing image: {e}")
            return image
    
    def process_image(self, image_path, resize=True, denoise=True, deskew_image=True, threshold_method='adaptive'):
        """
        Apply a full preprocessing pipeline to an image.
        
        Args:
            image_path (str): Path to the image file.
            resize (bool): Whether to resize the image.
            denoise (bool): Whether to remove noise.
            deskew_image (bool): Whether to deskew the image.
            threshold_method (str): Thresholding method.
            
        Returns:
            numpy.ndarray: Processed image.
        """
        try:
            # Load image
            image = self.load_image(image_path)
            if image is None:
                return None
            
            # Make a copy to avoid modifying the original
            processed = image.copy()
            
            # Convert to grayscale
            processed = self.convert_to_grayscale(processed)
            
            # Apply preprocessing steps
            if resize:
                processed = self.resize_image(processed)
            
            if denoise:
                processed = self.remove_noise(processed)
            
            if deskew_image:
                processed = self.deskew(processed)
            
            # Apply thresholding
            processed = self.apply_thresholding(processed, method=threshold_method)
            
            logger.info(f"Completed image preprocessing for {image_path}")
            return processed
        except Exception as e:
            logger.error(f"Error during image preprocessing: {e}")
            return None
    
    def save_image(self, image, output_path):
        """
        Save an image to a file.
        
        Args:
            image: The image to save (numpy.ndarray).
            output_path (str): Path to save the image to.
            
        Returns:
            bool: True if saving was successful, False otherwise.
        """
        try:
            cv2.imwrite(output_path, image)
            logger.info(f"Saved image to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image to {output_path}: {e}")
            return False 