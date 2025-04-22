#!/usr/bin/env python3
"""
Vancouver Bike Data Visualization
---------------------------------
This script creates an MP4 visualization of Vancouver bike data from PDF or Excel files.

Requirements:
- pandas
- numpy
- matplotlib
- PyPDF2
- tabula-py (for PDF)
- openpyxl (for Excel .xlsx)
- xlrd (for Excel .xls)
- FFmpeg (for creating the MP4)

Usage:
python runner.py [data_path] [output_file] [--format {pdf,excel}]

If data_path is not provided, sample data will be used.
If output_file is not provided, the default 'vancouver_bike_viz.mp4' will be used.
The format parameter is optional and will be inferred from the file extension if not provided.
"""

import os
import sys
import argparse
import pandas as pd
from pdfex import main as extract_pdf_data
from p import create_bike_data_animation
from excel_reader import main as extract_excel_data

import subprocess
import platform
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_ffmpeg():
    """
    Check if FFmpeg is installed and available in the system path.
    Returns True if FFmpeg is found, False otherwise.
    """
    try:
        # Hide the console window on Windows
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        # Run ffmpeg command to check its version
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True,
            startupinfo=startupinfo
        )
        
        # If the command ran successfully, ffmpeg is installed
        if result.returncode == 0:
            logger.info("✅ FFmpeg is installed and available.")
            return True
        else:
            logger.warning("❌ FFmpeg is installed but returned an error.")
            return False
    except FileNotFoundError:
        logger.error("❌ FFmpeg is not installed or not in the system PATH.")
        logger.info("Please install FFmpeg:")
        if platform.system() == "Windows":
            logger.info("  - Download from: https://www.gyan.dev/ffmpeg/builds/")
            logger.info("  - Or use Chocolatey (as admin): choco install ffmpeg")
        elif platform.system() == "Darwin":  # macOS
            logger.info("  - Using Homebrew: brew install ffmpeg")
        else:  # Linux
            logger.info("  - Using apt: sudo apt install ffmpeg")
            logger.info("  - Using yum: sudo yum install ffmpeg")
        return False

def determine_file_type(file_path):
    """
    Determine if the file is a PDF or Excel file based on its extension.
    
    Args:
        file_path: Path to the data file
        
    Returns:
        String: 'pdf', 'excel', or None if the file type is not supported
    """
    if not file_path:
        return None
        
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return 'pdf'
    elif file_ext in ['.xlsx', '.xls', '.xlsm']:
        return 'excel'
    else:
        logger.warning(f"Unsupported file extension: {file_ext}")
        return None

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Create bike data visualization from PDF or Excel.')
    parser.add_argument('data_path', nargs='?', default=None, help='Path to the PDF or Excel file')
    parser.add_argument('output_file', nargs='?', default='vancouver_bike_viz.mp4', 
                       help='Output MP4 file path')
    parser.add_argument('--format', choices=['pdf', 'excel'], 
                       help='Force interpretation as PDF or Excel (optional)')
    
    args = parser.parse_args()
    
    # Get data path and output path
    data_path = args.data_path
    output_file = args.output_file
    
    # Check FFmpeg availability
    if not check_ffmpeg():
        logger.warning("FFmpeg is required for creating MP4 visualizations.")
        logger.info("Continuing anyway, but visualization may fail at the final stage.")
    
    # Determine file type
    file_type = args.format if args.format else determine_file_type(data_path)
    
    # Extract data based on file type or use sample data
    if data_path and os.path.exists(data_path):
        logger.info(f"Using data from {data_path}")
        
        if file_type == 'pdf':
            logger.info("Processing PDF file...")
            bike_data = extract_pdf_data(data_path)
        elif file_type == 'excel':
            logger.info("Processing Excel file...")
            bike_data = extract_excel_data(data_path)
        else:
            logger.warning(f"Could not determine file type for {data_path}. Using sample data.")
            
        
        # Save extracted data to CSV for reference
        csv_path = os.path.splitext(output_file)[0] + '_data.csv'
        if bike_data is not None:
            bike_data.to_csv(csv_path, index=False)
            logger.info(f"Extracted data saved to {csv_path}")
    else:
        if data_path:
            logger.warning(f"Data file {data_path} not found.")
        logger.info("Using sample data...")
        
    
    # Create visualization
    if bike_data is not None:
        logger.info(f"Creating visualization...")
        create_bike_data_animation(bike_data, output_file)
        logger.info(f"Visualization saved to {output_file}")
    else:
        logger.error("Error: Could not create bike data. Visualization failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())