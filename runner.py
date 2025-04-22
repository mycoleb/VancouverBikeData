#!/usr/bin/env python3
"""
Vancouver Bike Data Visualization
---------------------------------
This script creates an MP4 visualization of Vancouver bike data from a PDF file.

Requirements:
- pandas
- numpy
- matplotlib
- PyPDF2
- tabula-py (and Java)
- FFmpeg (for creating the MP4)

Usage:
python create_vancouver_bike_viz.py [pdf_path] [output_file]

If pdf_path is not provided, sample data will be used.
If output_file is not provided, the default 'vancouver_bike_viz.mp4' will be used.
"""

import os
import sys
from pdfex import main as extract_pdf_data
from p import create_bike_data_animation, create_sample_data

import subprocess
import os
import platform

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
            print("✅ FFmpeg is installed and available.")
            return True
        else:
            print("❌ FFmpeg is installed but returned an error.")
            return False
    except FileNotFoundError:
        print("❌ FFmpeg is not installed or not in the system PATH.")
        print("Please install FFmpeg:")
        if platform.system() == "Windows":
            print("  - Download from: https://www.gyan.dev/ffmpeg/builds/")
            print("  - Or use Chocolatey (as admin): choco install ffmpeg")
        elif platform.system() == "Darwin":  # macOS
            print("  - Using Homebrew: brew install ffmpeg")
        else:  # Linux
            print("  - Using apt: sudo apt install ffmpeg")
            print("  - Using yum: sudo yum install ffmpeg")
        return False


def main():
    # Get PDF path from command line or use None
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Get output path from command line or use default
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'vancouver_bike_viz.mp4'
    
    # Extract data from PDF if provided, otherwise use sample data
    if pdf_path and os.path.exists(pdf_path):
        print(f"Extracting data from {pdf_path}...")
        bike_data = extract_pdf_data(pdf_path)
        
        # Save extracted data to CSV for reference
        csv_path = os.path.splitext(output_file)[0] + '_data.csv'
        if bike_data is not None:
            bike_data.to_csv(csv_path, index=False)
            print(f"Extracted data saved to {csv_path}")
    else:
        if pdf_path:
            print(f"PDF file {pdf_path} not found.")
        print("Using sample data...")
        bike_data = create_sample_data()
    
    # Create visualization
    if bike_data is not None:
        print(f"Creating visualization...")
        create_bike_data_animation(bike_data, output_file)
        print(f"Visualization saved to {output_file}")
    else:
        print("Error: Could not create bike data. Visualization failed.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())