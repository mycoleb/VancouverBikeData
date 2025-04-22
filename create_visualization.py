#!/usr/bin/env python3
"""
Vancouver Bike Data Visualization Runner
---------------------------------------
This script runs the full pipeline to process CSV files and create visualizations.

Usage:
python create_visualization.py [--recent RECENT_FILE] [--historical HISTORICAL_FILE] [--output OUTPUT_FILE]

Where:
    RECENT_FILE is the path to the recent bike data CSV file (default: bikevolume20212024.csv)
    HISTORICAL_FILE is the path to the historical bike data CSV file (default: bikevolumedata.csv)
    OUTPUT_FILE is the path to save the MP4 visualization (default: vancouver_bike_viz.mp4)
"""

import os
import sys
import argparse
import logging
import subprocess
import time

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_files(recent_file, historical_file):
    """
    Check if the input files exist and return the status
    """
    # Try alternative filenames without spaces if the original files aren't found
    recent_alternatives = [
        recent_file,
        recent_file.replace(" ", ""),
        "bikevolume20212024.csv",
        "bikevolume20212024Sheet1.csv"
    ]
    
    historical_alternatives = [
        historical_file,
        historical_file.replace(" ", ""),
        "bikevolumedata.csv",
        "bikedatavolume.csv",
        "bikevolumedataSheet1.csv"
    ]
    
    # Check for recent file
    recent_exists = False
    recent_file_path = None
    for file_path in recent_alternatives:
        if os.path.exists(file_path):
            recent_exists = True
            recent_file_path = file_path
            logger.info(f"Found recent data file: {file_path}")
            break
    
    if not recent_exists:
        logger.warning(f"Recent data file not found. Tried these paths: {', '.join(recent_alternatives)}")
    
    # Check for historical file
    historical_exists = False
    historical_file_path = None
    for file_path in historical_alternatives:
        if os.path.exists(file_path):
            historical_exists = True
            historical_file_path = file_path
            logger.info(f"Found historical data file: {file_path}")
            break
    
    if not historical_exists:
        logger.warning(f"Historical data file not found. Tried these paths: {', '.join(historical_alternatives)}")
    
    return recent_exists, historical_exists, recent_file_path, historical_file_path

def read_csv_data(csv_path):
    """
    Read bike count data from CSV files
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        DataFrame with the CSV data
    """
    logger.info(f"Reading CSV data from {csv_path}...")
    
    try:
        # Import pandas here to avoid importing it if not needed
        import pandas as pd
        
        # Read the CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Successfully read CSV file, shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return None

def process_csv_files(recent_file, historical_file, output_file):
    """
    Process the CSV files using our process_csv.py script
    """
    logger.info("Processing CSV files...")
    
    try:
        # First try using the process_csv.py script
        try:
            # Using subprocess to run the process_csv.py script
            cmd = [
                sys.executable, 
                "process_csv.py",
                "--recent", recent_file,
                "--historical", historical_file,
                "--output", output_file
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("CSV processing completed successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.warning(f"process_csv.py failed: {result.stderr}")
                # Fall back to process_excel.py
                logger.info("Falling back to process_excel.py...")
                
                cmd = [
                    sys.executable, 
                    "process_excel.py",
                    "--recent", recent_file,
                    "--historical", historical_file,
                    "--output", output_file
                ]
                
                logger.info(f"Running command: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("CSV processing completed successfully with process_excel.py")
                    logger.info(result.stdout)
                    return True
                else:
                    logger.error(f"CSV processing failed with return code {result.returncode}")
                    logger.error(f"Error: {result.stderr}")
                    return False
        
        except FileNotFoundError:
            logger.warning("process_csv.py not found, trying direct processing...")
            
            # If process_csv.py is not found, try to process the CSV files directly
            import pandas as pd
            
            # Read the CSV files
            recent_data = None
            historical_data = None
            
            if recent_file and os.path.exists(recent_file):
                recent_data = read_csv_data(recent_file)
            
            if historical_data and os.path.exists(historical_file):
                historical_data = read_csv_data(historical_file)
            
            if recent_data is None and historical_data is None:
                logger.error("No data could be read from CSV files")
                return False
            
            # Save the data to the output file
            if recent_data is not None:
                recent_data.to_csv(output_file, index=False)
                logger.info(f"Saved recent data to {output_file}")
                return True
            else:
                historical_data.to_csv(output_file, index=False)
                logger.info(f"Saved historical data to {output_file}")
                return True
    
    except Exception as e:
        logger.error(f"Error processing CSV files: {e}")
        return False

def create_visualization(combined_csv, output_file):
    """
    Create the visualization using our p.py script
    """
    logger.info("Creating visualization...")
    
    try:
        # First, check if the combined CSV file exists
        if not os.path.exists(combined_csv):
            logger.error(f"Combined CSV file {combined_csv} not found")
            return False
        
        # Import the create_bike_data_animation function from p.py
        try:
            from p import create_bike_data_animation
            import pandas as pd
            
            # Read the combined CSV file
            bike_data = pd.read_csv(combined_csv)
            
            # Check if we have a Date column
            if 'Date' in bike_data.columns:
                # Convert Date column to datetime
                bike_data['Date'] = pd.to_datetime(bike_data['Date'])
            else:
                logger.warning("Date column not found in the CSV. Checking alternatives...")
                
                # Try to create a Date column from other columns
                if 'date' in bike_data.columns:
                    bike_data['Date'] = pd.to_datetime(bike_data['date'])
                elif 'Year' in bike_data.columns and 'Month' in bike_data.columns:
                    bike_data['Date'] = pd.to_datetime(bike_data['Year'].astype(str) + '-' + 
                                                     bike_data['Month'].astype(str) + '-15')
                else:
                    logger.error("Could not create Date column from available data")
                    return False
            
            # Create the visualization
            create_bike_data_animation(bike_data, output_file)
            
            logger.info(f"Visualization created successfully: {output_file}")
            return True
        
        except ImportError as e:
            logger.error(f"Could not import create_bike_data_animation from p.py: {e}")
            logger.info("Attempting to use subprocess method instead...")
            
            # Using subprocess to run the p.py script directly
            cmd = [
                sys.executable,
                "p.py",
                combined_csv,
                output_file
            ]
            
            logger.info(f"Running command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("Visualization created successfully")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"Visualization creation failed with return code {result.returncode}")
                logger.error(f"Error: {result.stderr}")
                return False
    
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        return False

def main():
    """
    Main function to run the full pipeline
    """
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Run Vancouver bike data visualization pipeline.')
    parser.add_argument('--recent', default='bikevolume20212024 Sheet1.csv', 
                        help='Path to recent bike data CSV file')
    parser.add_argument('--historical', default='bikevolumedata Sheet1.csv', 
                        help='Path to historical bike data CSV file')
    parser.add_argument('--output', default='vancouver_bike_viz.mp4', 
                        help='Path to save the MP4 visualization')
    parser.add_argument('--csv_output', default='combined_bike_data.csv',
                        help='Path to save the combined CSV data')
    parser.add_argument('--skip_processing', action='store_true',
                        help='Skip the CSV processing step and use an existing combined CSV file')
    
    args = parser.parse_args()
    
    # File paths
    recent_file = args.recent
    historical_file = args.historical
    output_file = args.output
    csv_output = args.csv_output
    
    # Check if files exist and get alternative paths if needed
    recent_exists, historical_exists, recent_file_path, historical_file_path = check_files(recent_file, historical_file)
    
    # Update the file paths if alternatives were found
    if recent_exists:
        recent_file = recent_file_path
    else:
        recent_file = None
        
    if historical_exists:
        historical_file = historical_file_path
    else:
        historical_file = None
    
    if not recent_file and not historical_file:
        logger.error("No input files found. Exiting.")
        return 1
    
    # Process CSV files if not skipping
    if not args.skip_processing:
        logger.info("Starting CSV processing...")
        
        success = process_csv_files(recent_file, historical_file, csv_output)
        
        if not success:
            logger.error("CSV processing failed. Exiting.")
            return 1
        
        logger.info(f"CSV processing completed. Output saved to {csv_output}")
    else:
        logger.info("Skipping CSV processing as requested")
        
        # Check if the combined CSV file exists
        if not os.path.exists(csv_output):
            logger.error(f"Combined CSV file {csv_output} not found, but --skip_processing was specified")
            return 1
    
    # Create visualization
    logger.info("Starting visualization creation...")
    
    success = create_visualization(csv_output, output_file)
    
    if not success:
        logger.error("Visualization creation failed. Exiting.")
        return 1
    
    logger.info(f"Visualization successfully created: {output_file}")
    logger.info("Pipeline completed successfully!")
    
    return 0

if __name__ == "__main__":
    start_time = time.time()
    
    # Run the main function
    exit_code = main()
    
    # Report execution time
    elapsed_time = time.time() - start_time
    logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
    
    sys.exit(exit_code)