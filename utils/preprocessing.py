"""
Image Preprocessing Module

This module handles preprocessing of document images before OCR.
It includes functions for resizing, denoising, deskewing, and thresholding.
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
    
    def resize_image(self, image, max_width=1800):
        """
        Resize an image while maintaining aspect ratio.
        
        Args:
            image (numpy.ndarray): Input image.
            max_width (int, optional): Maximum width of the output image. Defaults to 1800.
        
        Returns:
            numpy.ndarray: Resized image.
        """
        height, width = image.shape[:2]
        if width > max_width:
            ratio = max_width / width
            new_height = int(height * ratio)
            resized = cv2.resize(image, (max_width, new_height), interpolation=cv2.INTER_AREA)
            return resized
        return image
    
    def denoise_image(self, image):
        """
        Remove noise from an image.
        
        Args:
            image (numpy.ndarray): Input grayscale image.
        
        Returns:
            numpy.ndarray: Denoised image.
        """
        # Use fastNlMeansDenoising to preserve edges better than median blur
        denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        return denoised
    
    def enhance_thin_characters(self, image):
        """
        Apply morphological operations to enhance thin characters like digit "1".
        
        Args:
            image (numpy.ndarray): Binary image after thresholding.
            
        Returns:
            numpy.ndarray: Enhanced image.
        """
        # Create a small structuring element for morphological operations
        kernel = np.ones((2, 2), np.uint8)
        
        # Apply a slight dilation to thicken thin strokes
        dilated = cv2.dilate(image, kernel, iterations=1)
        
        # Apply opening to remove small noise while preserving character shapes
        opened = cv2.morphologyEx(dilated, cv2.MORPH_OPEN, kernel)
        
        return opened
    
    def deskew(self, image):
        """
        Deskew (straighten) a document image.
        
        Args:
            image (numpy.ndarray): Input grayscale image.
        
        Returns:
            numpy.ndarray: Deskewed image.
        """
        try:
            # Find all contours
            contours, _ = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            
            # If no contours found, return original image
            if not contours:
                logger.warning("No contours found for deskewing, returning original image")
                return image
            
            # Find the largest contour by area (assumed to be the document)
            areas = [cv2.contourArea(c) for c in contours]
            max_contour = contours[np.argmax(areas)]
            
            # Get the minimum area rectangle
            rect = cv2.minAreaRect(max_contour)
            angle = rect[2]
            
            # Determine if image is landscape or portrait
            is_portrait = rect[1][0] < rect[1][1]  # width < height
            
            # Adjust angle based on orientation
            # Only deskew if the angle is significantly off
            if is_portrait:
                # For portrait, adjust angles near 0, 90, 180, 270
                if -5 < angle < 5:
                    return image  # Close to horizontal, no deskew needed
                elif 85 < angle < 95:
                    angle = angle - 90
                elif -95 < angle < -85:
                    angle = angle + 90
                else:
                    # Adjust angle to get closer to horizontal/vertical
                    if angle > 45:
                        angle = angle - 90
                    elif angle < -45:
                        angle = angle + 90
            else:
                # For landscape, adjust angles near 0, 90, 180, 270
                if -5 < angle < 5:
                    return image  # Close to horizontal, no deskew needed
                elif 85 < angle < 95:
                    angle = angle - 90
                elif -95 < angle < -85:
                    angle = angle + 90
                else:
                    # For landscape orientation, no need for extra adjustments
                    pass
            
            # If angle is very small, don't rotate to avoid unnecessary distortion
            if -1 < angle < 1:
                return image
            
            # Get the rotation matrix
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            
            # Perform the rotation
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=255
            )
            
            logger.info(f"Deskewed image by {angle:.2f} degrees")
            return rotated
        except Exception as e:
            logger.error(f"Error during deskewing: {e}")
            return image
    
    def process_image(self, image_path, resize=True, denoise=True, deskew_image=True, threshold_method='adaptive'):
        """
        Process an image for better OCR results.
        
        Args:
            image_path (str): Path to the image file.
            resize (bool, optional): Whether to resize the image. Defaults to True.
            denoise (bool, optional): Whether to denoise the image. Defaults to True.
            deskew_image (bool, optional): Whether to deskew the image. Defaults to True.
            threshold_method (str, optional): Thresholding method ('adaptive', 'otsu', or None). 
                                            Defaults to 'adaptive'.
        
        Returns:
            numpy.ndarray: Processed image.
        """
        try:
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not read image from {image_path}")
                return None
            
            # Convert to grayscale if not already
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Resize image if needed
            if resize:
                gray = self.resize_image(gray)
            
            # Denoise the image (remove noise)
            if denoise:
                gray = self.denoise_image(gray)
            
            # Deskew the image (straighten)
            if deskew_image:
                gray = self.deskew(gray)
            
            # Apply thresholding based on the specified method
            if threshold_method == 'adaptive':
                # Use a gentler adaptive threshold to preserve thin strokes like digit "1"
                processed = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2  # Smaller block size (11) and constant (2) for better detail
                )
            elif threshold_method == 'otsu':
                # Apply Gaussian blur before Otsu's method to reduce noise while preserving details
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                _, processed = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            else:
                processed = gray
            
            # Apply additional processing to enhance thin characters
            processed = self.enhance_thin_characters(processed)
            
            logger.info(f"Successfully processed image from {image_path}")
            return processed
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return None
    
    def save_image(self, image, output_path):
        """
        Save a processed image to disk.
        
        Args:
            image (numpy.ndarray): Image to save.
            output_path (str): Path to save the image to.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            cv2.imwrite(output_path, image)
            logger.info(f"Saved processed image to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image to {output_path}: {e}")
            return False 