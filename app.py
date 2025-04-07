"""
Document Scanning and OCR System

Flask application for scanning documents and extracting text and structured data.
"""

import os
import uuid
from flask import Flask, request, render_template, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import logging
import json
from utils.ocr import OCRProcessor
from utils.preprocessing import ImagePreprocessor
from utils.parser import DataParser
from datetime import timedelta
import time
import cv2

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-for-testing')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'processed')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif', 'pdf'}

# Create upload directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max file size

# Configure session settings
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Session lasts for 1 day
app.config['SESSION_COOKIE_NAME'] = 'ocr_scanner_session'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize OCR processor, image preprocessor, and data parser
ocr_processor = OCRProcessor()
image_preprocessor = ImagePreprocessor()
data_parser = DataParser()

def allowed_file(filename):
    """
    Check if the file extension is allowed.
    
    Args:
        filename (str): Name of the file to check.
        
    Returns:
        bool: True if the file extension is allowed, False otherwise.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """
    Render the upload form.
    
    Returns:
        Rendered template with the upload form.
    """
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle file upload and start OCR processing.
    
    Returns:
        Redirect to the result page if successful, or back to the index if not.
    """
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    # Check if file was selected
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    # Check if file is allowed
    if not file or not allowed_file(file.filename):
        flash('File type not allowed')
        return redirect(request.url)
    
    try:
        # Get processing options from form
        enable_deskew = request.form.get('enable_deskew', 'off') == 'on'
        
        # Generate unique ID for this processing session
        process_id = str(uuid.uuid4())
        
        # Secure the filename and generate unique filenames
        filename = secure_filename(file.filename)
        base_filename, ext = os.path.splitext(filename)
        original_filename = f"{base_filename}_{process_id}{ext}"
        processed_filename = f"processed_{base_filename}_{process_id}{ext}"
        
        # Save the original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
        file.save(original_path)
        logger.info(f"Saved uploaded file to {original_path}")
        
        # Process the image and save the processed version
        processed_image = image_preprocessor.process_image(
            original_path, 
            resize=True, 
            denoise=True, 
            deskew_image=enable_deskew,
            threshold_method='adaptive'
        )
        
        if processed_image is not None:
            processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
            image_preprocessor.save_image(processed_image, processed_path)
            
            # Extract text from processed image
            extracted_text = ocr_processor.extract_text_from_image(processed_image)
            
            # Parse the text
            parsed_data = data_parser.parse_text(extracted_text)
            
            # Redirect to result page with process ID
            return redirect(url_for('result', process_id=process_id))
        else:
            flash('Error processing image')
            return redirect(request.url)
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        flash('Error processing file')
        return redirect(request.url)

@app.route('/result/<process_id>')
def result(process_id):
    """
    Display the OCR processing results.
    
    Args:
        process_id (str): The unique ID of the processing session.
        
    Returns:
        Rendered template with the results.
    """
    try:
        # Find the files for this process ID
        original_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if process_id in f]
        processed_files = [f for f in os.listdir(app.config['PROCESSED_FOLDER']) if process_id in f]
        
        if not original_files or not processed_files:
            flash('Files not found. Please upload the file again.')
            return redirect(url_for('index'))
        
        # Get the first matching file (should be only one)
        original_filename = original_files[0]
        processed_filename = processed_files[0]
        
        # Construct paths
        original_path = os.path.join('uploads', original_filename)
        processed_path = os.path.join('processed', processed_filename)
        
        # Read the processed image and extract text
        processed_image = cv2.imread(os.path.join(app.config['PROCESSED_FOLDER'], processed_filename))
        extracted_text = ocr_processor.extract_text_from_image(processed_image)
        
        # Parse the text
        parsed_data = data_parser.parse_text(extracted_text)
        
        return render_template(
            'result.html',
            original_path=original_path,
            processed_path=processed_path,
            extracted_text=extracted_text,
            deskew_enabled=True  # We'll determine this from the filename if needed
        )
    except Exception as e:
        logger.error(f"Error displaying results: {e}")
        flash('Error displaying results. Please try again.')
        return redirect(url_for('index'))

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """
    API endpoint for extracting text and data from an uploaded image.
    
    Returns:
        JSON with extracted text and parsed data.
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        
        # Check if file was selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check if file is allowed
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get processing options
        enable_deskew = request.form.get('enable_deskew', 'true').lower() == 'true'
        
        # Secure the filename and generate a unique ID
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        base_filename, ext = os.path.splitext(filename)
        unique_filename = f"{base_filename}_{file_id}{ext}"
        
        # Save the original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(original_path)
        
        # Process the image
        processed_image = image_preprocessor.process_image(
            original_path,
            resize=True,
            denoise=True,
            deskew_image=enable_deskew,
            threshold_method='adaptive'
        )
        
        if processed_image is not None:
            # Extract text from processed image
            extracted_text = ocr_processor.extract_text_from_image(processed_image)
            
            # Parse the text to extract structured data
            parsed_data = data_parser.parse_text(extracted_text)
            
            return jsonify({
                'file_id': file_id,
                'extracted_text': extracted_text,
                'parsed_data': parsed_data,
                'deskew_enabled': enable_deskew
            })
        else:
            return jsonify({'error': 'Error processing image'}), 500
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file too large error."""
    flash('File too large')
    return redirect(url_for('index')), 413

@app.errorhandler(500)
def internal_error(error):
    """
    Handle internal server errors.
    
    Args:
        error: The error that occurred.
        
    Returns:
        Redirect to the index page with an error message.
    """
    logger.error(f"Internal server error: {error}")
    flash('An internal error occurred. Please try again.')
    return redirect(url_for('index'))

# Add cleanup task to remove old files
def cleanup_old_files():
    """
    Remove files older than 24 hours.
    """
    try:
        current_time = time.time()
        for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                # Check if file is older than 24 hours
                if current_time - os.path.getmtime(file_path) > 86400:  # 24 hours in seconds
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")

# Schedule cleanup task
@app.before_request
def before_request():
    cleanup_old_files()

if __name__ == '__main__':
    app.run(debug=True) 