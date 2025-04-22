#!/usr/bin/env python3
"""
Process Vancouver Bike Data CSV Files
--------------------------------------
This script processes both CSV files and combines them for visualization.

Usage:
python process_csv.py [--recent RECENT_FILE] [--historical HISTORICAL_FILE] [--output OUTPUT_FILE]

Where:
    RECENT_FILE is the path to the recent bike data CSV file
    HISTORICAL_FILE is the path to the historical bike data CSV file
    OUTPUT_FILE is the path to save the combined CSV file
"""

import pandas as pd
import numpy as np
import os
import sys
import argparse
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        # Read the CSV file
        df = pd.read_csv(csv_path)
        logger.info(f"Successfully read CSV file, shape: {df.shape}")
        return df
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        return None

def process_recent_csv_data(df):
    """
    Process the recent bike count data (2021-2024)
    
    Args:
        df: DataFrame from read_csv_data
        
    Returns:
        Processed DataFrame in standardized format
    """
    if df is None:
        logger.error("No recent data to process")
        return None
    
    logger.info("Processing recent bike data...")
    logger.info(f"Original columns: {list(df.columns)}")
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    try:
        # Expected columns for recent data: Location, Direction, CorrectionFactor, 
        # PercentPassing20%, PercentPassing10%, date, Volume
        
        # Check if we have the expected columns
        expected_columns = ['Location', 'Direction', 'date', 'Volume']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"Missing expected columns: {missing_columns}")
            
            # Try to map available columns to expected ones
            col_mapping = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'location' in col_lower or 'route' in col_lower:
                    col_mapping[col] = 'Location'
                elif 'direct' in col_lower:
                    col_mapping[col] = 'Direction'
                elif 'date' in col_lower or 'time' in col_lower:
                    col_mapping[col] = 'date'
                elif 'volume' in col_lower or 'count' in col_lower:
                    col_mapping[col] = 'Volume'
            
            # Rename columns based on mapping
            df = df.rename(columns=col_mapping)
            logger.info(f"Mapped columns: {col_mapping}")
            logger.info(f"New columns: {list(df.columns)}")
        
        # Process the date column
        if 'date' in df.columns:
            # Convert to datetime
            df['Date'] = pd.to_datetime(df['date'], errors='coerce')
            
            # Extract year and month
            df['Year'] = df['Date'].dt.year
            df['Month'] = df['Date'].dt.strftime('%b')  # Month abbreviation
            
            # Drop rows with invalid dates
            invalid_dates = df['Date'].isna().sum()
            if invalid_dates > 0:
                logger.warning(f"Dropping {invalid_dates} rows with invalid dates")
                df = df.dropna(subset=['Date'])
        else:
            logger.error("No date column found in recent data")
            return None
        
        # Create standardized format
        if 'Location' in df.columns and 'Volume' in df.columns:
            # Create a new dataframe in the desired format
            result_df = pd.DataFrame({
                'Date': df['Date'],
                'Year': df['Year'],
                'Month': df['Month'],
                'Route': df['Location'],
                'Count': df['Volume']
            })
            
            # Drop any rows with missing values
            result_df = result_df.dropna()
            
            logger.info(f"Processed recent data, shape: {result_df.shape}")
            return result_df
        else:
            logger.error("Could not create standardized format - missing location or volume data")
            return None
        
    except Exception as e:
        logger.error(f"Error processing recent data: {e}")
        return None

def process_historical_csv_data(df):
    """
    Process the historical bike count data
    
    Args:
        df: DataFrame from read_csv_data
        
    Returns:
        Processed DataFrame in standardized format
    """
    if df is None:
        logger.error("No historical data to process")
        return None
    
    logger.info("Processing historical bike data...")
    logger.info(f"Original columns: {list(df.columns)}")
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    try:
        # Historical data is likely in wide format with routes as columns
        # And a Date column for the time period
        
        # Check if we have a Date column
        if 'Date' not in df.columns:
            # Try to find a date-like column
            date_col = None
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    date_col = col
                    break
            
            if date_col:
                df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            else:
                logger.error("No date column found in historical data")
                return None
        else:
            # Convert Date to datetime
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Extract year and month
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.strftime('%b')  # Month abbreviation
        
        # Identify route columns (all columns except Date, Year, Month)
        route_cols = [col for col in df.columns if col not in ['Date', 'Year', 'Month']]
        
        # Convert to long format
        long_data = []
        
        for _, row in df.iterrows():
            for route in route_cols:
                if pd.notna(row[route]) and row[route] != 0:  # Skip missing or zero values
                    long_data.append({
                        'Date': row['Date'],
                        'Year': row['Year'],
                        'Month': row['Month'],
                        'Route': route,
                        'Count': float(row[route])  # Ensure numeric
                    })
        
        result_df = pd.DataFrame(long_data)
        
        # Drop any rows with missing values
        result_df = result_df.dropna()
        
        logger.info(f"Processed historical data, shape: {result_df.shape}")
        return result_df
        
    except Exception as e:
        logger.error(f"Error processing historical data: {e}")
        return None

def combine_bike_data(recent_data, historical_data):
    """
    Combine data from two dataframes, ensuring consistent format
    
    Args:
        recent_data: DataFrame with recent bike count data
        historical_data: DataFrame with historical bike count data
        
    Returns:
        Combined DataFrame
    """
    if recent_data is None and historical_data is None:
        logger.error("Both datasets are empty or could not be processed")
        return None
    
    # If one dataset is missing, return the other
    if recent_data is None:
        logger.warning("Recent data is missing, using only historical data")
        return historical_data
    
    if historical_data is None:
        logger.warning("Historical data is missing, using only recent data")
        return recent_data
    
    # Make sure both dataframes have the same columns
    required_columns = ['Date', 'Year', 'Month', 'Route', 'Count']
    
    for df, name in [(recent_data, 'recent_data'), (historical_data, 'historical_data')]:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"Missing columns in {name}: {missing_cols}")
            return None
    
    # Combine the data
    logger.info(f"Combining datasets: recent ({recent_data.shape[0]} rows) and "
               f"historical ({historical_data.shape[0]} rows)")
    
    combined_data = pd.concat([historical_data, recent_data], ignore_index=True)
    
    # Remove duplicates if any
    combined_data = combined_data.drop_duplicates(subset=['Date', 'Route'])
    
    # Sort by date and route
    combined_data = combined_data.sort_values(['Date', 'Route'])
    
    logger.info(f"Combined data has {combined_data.shape[0]} rows")
    
    return combined_data

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Process Vancouver bike data CSV files.')
    parser.add_argument('--recent', default=None, 
                        help='Path to recent bike data CSV file')
    parser.add_argument('--historical', default=None, 
                        help='Path to historical bike data CSV file')
    parser.add_argument('--output', default='combined_bike_data.csv', 
                        help='Path to save the combined CSV file')
    
    args = parser.parse_args()
    
    # Get file paths
    recent_file = args.recent
    historical_file = args.historical
    output_file = args.output
    
    # Check if files exist
    if recent_file and not os.path.exists(recent_file):
        logger.warning(f"Recent data file {recent_file} not found")
        recent_file = None
    
    if historical_file and not os.path.exists(historical_file):
        logger.warning(f"Historical data file {historical_file} not found")
        historical_file = None
    
    if not recent_file and not historical_file:
        logger.error("No input files found. Exiting.")
        return 1
    
    # Process recent data
    recent_data = None
    if recent_file:
        logger.info(f"Processing recent data from {recent_file}")
        raw_recent = read_csv_data(recent_file)
        recent_data = process_recent_csv_data(raw_recent)
    
    # Process historical data
    historical_data = None
    if historical_file:
        logger.info(f"Processing historical data from {historical_file}")
        raw_historical = read_csv_data(historical_file)
        historical_data = process_historical_csv_data(raw_historical)
    
    # Combine the data
    combined_data = combine_bike_data(recent_data, historical_data)
    
    # Save combined data
    if combined_data is not None:
        combined_data.to_csv(output_file, index=False)
        logger.info(f"Combined data saved to {output_file}")
        
        # Print summary statistics
        logger.info(f"Data summary:")
        logger.info(f"  - Total records: {combined_data.shape[0]}")
        logger.info(f"  - Date range: {combined_data['Date'].min()} to {combined_data['Date'].max()}")
        logger.info(f"  - Routes: {combined_data['Route'].nunique()}")
        logger.info(f"  - Total bike count: {combined_data['Count'].sum():,}")
        
        return 0
    else:
        logger.error("Failed to create combined dataset")
        return 1

if __name__ == "__main__":
    sys.exit(main())