#!/usr/bin/env python3
"""
Inspect Excel Sheets
-------------------
This script inspects Excel files to determine their structure before processing.

Usage:
python inspect_sheets.py <excel_file_path>

Where:
    excel_file_path is the path to the Excel file to inspect
    
Options:
    --all, -a    Inspect all available Excel files in the current directory
"""

import sys
import pandas as pd
import os
import logging
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def inspect_excel_file(excel_path):
    """
    Inspect an Excel file and print information about its structure
    
    Args:
        excel_path: Path to the Excel file
    """
    if not os.path.exists(excel_path):
        logger.error(f"File not found: {excel_path}")
        return
        
    logger.info(f"Inspecting Excel file: {excel_path}")
    
    try:
        # Get sheet names
        xl = pd.ExcelFile(excel_path)
        sheet_names = xl.sheet_names
        logger.info(f"Available sheets: {sheet_names}")
        
        # Look for specific sheet name - "City of Vancouver Bike Data"
        target_sheet = "City of Vancouver Bike Data"
        if target_sheet in sheet_names:
            logger.info(f"Found target sheet: {target_sheet}")
            inspect_specific_sheet(excel_path, target_sheet)
        else:
            # Inspect each sheet if target sheet not found
            for sheet_name in sheet_names:
                logger.info(f"\nReading sheet: {sheet_name}")
                inspect_sheet(excel_path, sheet_name)
                
    except Exception as e:
        logger.error(f"Error opening Excel file: {e}")

def inspect_specific_sheet(excel_path, sheet_name):
    """
    Inspect the specific sheet with more detailed analysis
    
    Args:
        excel_path: Path to the Excel file
        sheet_name: Name of the sheet to inspect
    """
    try:
        logger.info(f"Performing detailed inspection of sheet: {sheet_name}")
        
        # Read a small sample (first 10 rows) to get a glimpse
        df_sample = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=10)
        
        # Sheet dimensions and columns
        logger.info(f"Sheet dimensions: {df_sample.shape}")
        logger.info(f"Column names: {list(df_sample.columns)}")
        
        # Show the first few rows
        logger.info(f"First 5 rows preview:")
        logger.info(df_sample.head(5))
        
        # Check column types
        logger.info(f"Column data types:")
        logger.info(df_sample.dtypes)
        
        # Show information about missing values
        missing_values = df_sample.isna().sum()
        logger.info(f"Missing values per column:")
        logger.info(missing_values)
        
        # Check column letters and ranges
        num_columns = df_sample.shape[1]
        column_letters = [chr(65 + i) for i in range(min(num_columns, 26))]
        if num_columns > 26:
            column_letters += [f'A{chr(65 + i)}' for i in range(num_columns - 26)]
        
        logger.info(f"Column range: {column_letters[0]} through {column_letters[-1]}")
        
        # Try to identify date, route, and count columns
        potential_date_cols = [col for col in df_sample.columns if any(date_term in str(col).lower() for 
                                                              date_term in ['date', 'time', 'year', 'month'])]
        
        potential_route_cols = [col for col in df_sample.columns if any(route_term in str(col).lower() for 
                                                                route_term in ['route', 'path', 'bridge', 'street', 'lane'])]
        
        # Check for numeric columns (potential count columns)
        numeric_cols = df_sample.select_dtypes(include=['number']).columns.tolist()
        
        logger.info(f"Potential date columns: {potential_date_cols}")
        logger.info(f"Potential route columns: {potential_route_cols}")
        logger.info(f"Numeric columns (potential counts): {numeric_cols}")
        
        # Determine the data format based on column structure
        if len(potential_route_cols) > 1:
            logger.info("Data appears to be in WIDE format (routes as columns)")
            # Sample values from potential route columns
            for col in potential_route_cols[:3]:  # Show just first 3 for brevity
                logger.info(f"Sample values from route column '{col}':")
                logger.info(df_sample[col].head(3))
        else:
            logger.info("Data may be in LONG format (routes as rows)")
            # Look for a column that might contain route names
            for col in df_sample.columns:
                if df_sample[col].dtype == 'object' and df_sample[col].nunique() > 3:
                    logger.info(f"Column '{col}' may contain route names. Unique values:")
                    logger.info(df_sample[col].unique()[:5])  # Show first 5 unique values
        
        # Provide specific recommendation based on file analysis
        file_name = os.path.basename(excel_path)
        if file_name == "bikevolume20212024.xlsx":
            logger.info("This is the recent data file (2021-2024)")
            # Any specific recommendations for this file
        elif file_name == "bikevolumedata.xlsx":
            logger.info("This is the historical data file")
            # Any specific recommendations for this file
            
    except Exception as e:
        logger.error(f"Error inspecting sheet {sheet_name}: {e}")

def inspect_sheet(excel_path, sheet_name):
    """
    Basic inspection of a sheet
    
    Args:
        excel_path: Path to the Excel file
        sheet_name: Name of the sheet to inspect
    """
    try:
        # Read a small sample
        df_sample = pd.read_excel(excel_path, sheet_name=sheet_name, nrows=5)
        
        logger.info(f"Sheet dimensions: {df_sample.shape}")
        logger.info(f"Column names: {list(df_sample.columns)}")
        
        # Check column letters and ranges
        num_columns = df_sample.shape[1]
        column_letters = [chr(65 + i) for i in range(min(num_columns, 26))]
        if num_columns > 26:
            column_letters += [f'A{chr(65 + i)}' for i in range(num_columns - 26)]
        
        logger.info(f"Column range: {column_letters[0]} through {column_letters[-1]}")
        
    except Exception as e:
        logger.error(f"Error inspecting sheet {sheet_name}: {e}")

def main():
    """
    Main function to process command line arguments
    """
    parser = argparse.ArgumentParser(description='Inspect Excel file structure.')
    parser.add_argument('excel_path', nargs='?', help='Path to the Excel file to inspect')
    parser.add_argument('--all', '-a', action='store_true', help='Inspect all available Excel files')
    
    args = parser.parse_args()
    
    if args.all:
        # Look for both Excel files
        logger.info("Inspecting all bike data Excel files in the current directory")
        files_to_inspect = ['bikevolume20212024.xlsx', 'bikevolumedata.xlsx']
        
        for file_path in files_to_inspect:
            if os.path.exists(file_path):
                logger.info(f"\n{'='*50}")
                logger.info(f"INSPECTING FILE: {file_path}")
                logger.info(f"{'='*50}")
                inspect_excel_file(file_path)
            else:
                logger.warning(f"File not found: {file_path}")
        
        return 0
        
    if not args.excel_path:
        logger.error("Please provide an Excel file path")
        logger.info(f"Usage: python {sys.argv[0]} <excel_file_path>")
        logger.info(f"Or use --all to inspect all bike data files")
        return 1
        
    excel_path = args.excel_path
    inspect_excel_file(excel_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())