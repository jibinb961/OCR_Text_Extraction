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

# Initialize OCR processor, image preprocessor, and data parser
ocr_processor = OCRProcessor()
image_preprocessor = ImagePreprocessor()
data_parser = DataParser()

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Render the home page."""
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
        
        # Secure the filename and generate a unique ID
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        base_filename, ext = os.path.splitext(filename)
        unique_filename = f"{base_filename}_{file_id}{ext}"
        
        # Save the original file
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
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
            processed_path = os.path.join(app.config['PROCESSED_FOLDER'], f"processed_{unique_filename}")
            image_preprocessor.save_image(processed_image, processed_path)
            
            # Extract structured data from processed image
            structured_data = ocr_processor.extract_structured_data(processed_image)
            
            # Extract plain text for basic parsing
            extracted_text = ocr_processor.extract_text_from_image(processed_image)
            
            # Parse the text to extract structured data
            parsed_data = data_parser.parse_text(extracted_text)
            
            # Add structured data to parsed results
            parsed_data['tables'] = structured_data.get('tables', [])
            parsed_data['lines'] = structured_data.get('lines', [])
            
            # Save the data in session for the result page
            session['file_id'] = file_id
            session['original_path'] = os.path.join('uploads', unique_filename)
            session['processed_path'] = os.path.join('processed', f"processed_{unique_filename}")
            session['extracted_text'] = extracted_text
            session['parsed_data'] = parsed_data
            session['deskew_enabled'] = enable_deskew
            
            # Redirect to result page
            return redirect(url_for('result', file_id=file_id))
        else:
            flash('Error processing image')
            return redirect(request.url)
    except Exception as e:
        logger.error(f"Error processing upload: {e}")
        flash('Error processing file')
        return redirect(request.url)

@app.route('/result/<file_id>')
def result(file_id):
    """
    Display OCR results for a processed file.
    
    Args:
        file_id (str): Unique ID for the file.
        
    Returns:
        Rendered result template.
    """
    try:
        # Retrieve data from session
        if session.get('file_id') != file_id:
            flash('Session expired or invalid file ID')
            return redirect(url_for('index'))
        
        original_path = session.get('original_path')
        processed_path = session.get('processed_path')
        extracted_text = session.get('extracted_text')
        parsed_data = session.get('parsed_data')
        deskew_enabled = session.get('deskew_enabled', True)
        
        return render_template(
            'result.html',
            original_path=original_path,
            processed_path=processed_path,
            extracted_text=extracted_text,
            parsed_data=parsed_data,
            deskew_enabled=deskew_enabled
        )
    except Exception as e:
        logger.error(f"Error displaying result: {e}")
        flash('Error displaying result')
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
def internal_server_error(error):
    """Handle internal server error."""
    flash('Server error')
    return redirect(url_for('index')), 500

if __name__ == '__main__':
    app.run(debug=True) 