from setuptools import setup, find_packages

setup(
    name="ocr-document-scanner",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "Flask>=2.3.3",
        "Werkzeug>=2.3.7",
        "Pillow>=10.0.0",
        "pytesseract>=0.3.10",
        "regex>=2023.8.8",
        "python-dateutil>=2.8.2",
        "numpy>=1.25.2",
    ],
    author="Jibin Baby",
    author_email="example@example.com",
    description="A document scanning and OCR system for extracting text and data from images",
    keywords="ocr, document scanning, text extraction",
    url="https://github.com/yourusername/OCR",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 