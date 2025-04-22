import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
import calendar

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
# In excel_reader.py, modify the extract_data_from_excel function:

def extract_data_from_excel(excel_path):
    """
    Extract bike count data from Vancouver's Excel files
    
    Args:
        excel_path: Path to the Excel file
        
    Returns:
        DataFrame with processed data
    """
    logger.info(f"Extracting data from {excel_path}...")
    
    try:
        # Determine the engine based on file extension
        engine = 'openpyxl' if excel_path.endswith('.xlsx') else 'xlrd'
        
        # List all sheets
        xl = pd.ExcelFile(excel_path)
        logger.info(f"Available sheets: {xl.sheet_names}")
        
        # Try each sheet until we find one with bike data
        for sheet_name in xl.sheet_names:
            try:
                df = pd.read_excel(excel_path, engine=engine, sheet_name=sheet_name)
                logger.info(f"Reading sheet: {sheet_name}, shape: {df.shape}")
                
                # Check if this sheet has potential bike data
                if df.shape[1] > 5:  # If it has several columns, might be the data
                    return df
            except Exception as e:
                logger.warning(f"Error reading sheet {sheet_name}: {e}")
        
        # If we get here, use the first sheet as fallback
        return pd.read_excel(excel_path, engine=engine)
        
    except Exception as e:
        logger.error(f"Error reading Excel file: {e}")
        return None    
    
def process_bike_data(df):
    """
    Process and clean the extracted data from Excel
    
    Args:
        df: DataFrame from extract_data_from_excel
        
    Returns:
        Cleaned DataFrame ready for visualization
    """
    if df is None:
        logger.error("No data to process")
        return None
    
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    logger.info("Processing Excel bike data...")
    
    # Display the first few rows to see the structure
    logger.info("Data preview:")
    logger.info(df.head())
    
    # Try to identify date and route columns
    # This section needs to be customized based on actual Excel file structure
    
    # Strategy 1: Look for columns with date-like names
    date_cols = [col for col in df.columns if any(date_word in str(col).lower() 
                                              for date_word in ['date', 'year', 'month', 'time'])]
    
    # Strategy 2: Look for route-like names
    route_keywords = ['bridge', 'street', 'road', 'path', 'lane', 'route', 'burrard', 'hornby', 'dunsmuir']
    route_cols = [col for col in df.columns if any(route_word in str(col).lower() 
                                               for route_word in route_keywords)]
    
    logger.info(f"Potential date columns found: {date_cols}")
    logger.info(f"Potential route columns found: {route_cols}")
    
    # If we have potential date columns, we might have a "wide" format
    # If we have potential route columns, we might have a "long" format
    # We need to handle both cases
    
    # Check if our data is in "wide" format (routes as columns)
    is_wide_format = len(route_cols) > 1
    
    # Process based on identified format
    if is_wide_format:
        logger.info("Processing wide format data (routes as columns)")
        return process_wide_format(df, date_cols, route_cols)
    else:
        logger.info("Processing long/unknown format data")
        return process_unknown_format(df)
    
def process_wide_format(df, date_cols, route_cols):
    """
    Process data in wide format (routes as columns)
    """
    # Try to extract year and month from date columns
    year_col = next((col for col in date_cols if 'year' in str(col).lower()), None)
    month_col = next((col for col in date_cols if 'month' in str(col).lower()), None)
    
    # If we have separate year and month columns
    if year_col and month_col:
        # Create a Date column
        logger.info(f"Creating Date column from {year_col} and {month_col}")
        
        # Convert to string first to handle various formats
        df['Year'] = df[year_col].astype(str)
        df['Month'] = df[month_col].astype(str)
        
        # Try to convert month names/abbreviations to numbers if needed
        try:
            # If months are already numbers
            df['MonthNum'] = pd.to_numeric(df['Month'], errors='coerce')
        except:
            # If months are names or abbreviations
            month_map = {month[:3].lower(): i+1 for i, month in enumerate(calendar.month_name) if month}
            df['MonthNum'] = df['Month'].str.lower().str[:3].map(month_map)
        
        # Create date column (use day 15 as mid-month reference)
        df['Date'] = pd.to_datetime(df['Year'] + '-' + df['MonthNum'].astype(str) + '-15', errors='coerce')
    
    # Check if we have a date column already
    elif any('date' in str(col).lower() for col in date_cols):
        date_col = next(col for col in date_cols if 'date' in str(col).lower())
        df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Extract year and month
        df['Year'] = df['Date'].dt.year.astype(str)
        df['Month'] = df['Date'].dt.month_name().str[:3]
    
    # Drop rows where Date couldn't be parsed
    if 'Date' in df.columns:
        df = df.dropna(subset=['Date'])
        logger.info(f"Created Date column, data shape: {df.shape}")
    else:
        logger.warning("Could not create Date column")
        return None
    
    # Select route columns for our long-format conversion
    # If we have identified route columns, use those
    # Otherwise, try to use all numeric columns except date-related ones
    if not route_cols:
        # Try to identify count columns (numeric columns that aren't dates)
        numeric_cols = df.select_dtypes(include=['number']).columns
        route_cols = [col for col in numeric_cols if col not in date_cols + ['Date', 'Year', 'MonthNum']]
    
    # Create long format data
    logger.info(f"Converting wide format to long format using route columns: {route_cols}")
    
    long_data = []
    for _, row in df.iterrows():
        for route in route_cols:
            if pd.notna(row[route]):
                try:
                    count_value = float(row[route])
                    # Only add non-zero, valid counts
                    if not pd.isna(count_value) and count_value > 0:
                        long_data.append({
                            'Date': row['Date'],
                            'Year': row['Year'] if 'Year' in row else row['Date'].year,
                            'Month': row['Month'] if 'Month' in row else row['Date'].strftime('%b'),
                            'Route': route,
                            'Count': count_value
                        })
                except:
                    # Skip non-numeric values
                    pass
    
    long_df = pd.DataFrame(long_data)
    logger.info(f"Created long format data with shape: {long_df.shape}")
    
    return long_df

def process_unknown_format(df):
    """
    Process data in unknown format, using heuristics to identify structure
    """
    logger.info("Attempting to identify data structure using heuristics")
    
    # First, clean column names
    df.columns = [str(col).strip() for col in df.columns]
    
    # Try to identify date, route, and count columns using heuristics
    # This is a generic approach and might need adjustment for specific files
    
    # Look for numeric columns as potential count columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    logger.info(f"Potential numeric columns: {list(numeric_cols)}")
    
    # Look for columns with many unique values as potential route columns
    high_cardinality_cols = [col for col in df.columns 
                            if col not in numeric_cols and df[col].nunique() > 5]
    logger.info(f"Potential categorical columns: {list(high_cardinality_cols)}")
    
    # Try different approaches based on what we found
    
    # Approach 1: If we have months/dates and routes clearly identified
    date_cols = [col for col in df.columns if any(word in str(col).lower() 
                                               for word in ['date', 'month', 'year'])]
    route_cols = [col for col in df.columns if any(word in str(col).lower() 
                                                for word in ['route', 'location', 'path'])]
    count_cols = [col for col in numeric_cols if any(word in str(col).lower() 
                                                  for word in ['count', 'volume', 'trips'])]
    
    if date_cols and route_cols and count_cols:
        logger.info(f"Found date columns: {date_cols}, route columns: {route_cols}, "
                   f"count columns: {count_cols}")
        
        # In this case, we might already have a long format
        result_df = df[date_cols + route_cols + count_cols].copy()
        
        # Rename columns for consistency
        rename_map = {}
        for col in date_cols:
            if 'year' in str(col).lower():
                rename_map[col] = 'Year'
            elif 'month' in str(col).lower():
                rename_map[col] = 'Month'
            elif 'date' in str(col).lower():
                rename_map[col] = 'Date'
                
        for col in route_cols:
            rename_map[col] = 'Route'
            
        for col in count_cols:
            rename_map[col] = 'Count'
            
        result_df = result_df.rename(columns=rename_map)
        
        # Create Date column if needed
        if 'Date' not in result_df.columns and 'Year' in result_df.columns and 'Month' in result_df.columns:
            # Try to create a proper date column
            try:
                # Convert year to string
                result_df['Year'] = result_df['Year'].astype(str)
                
                # Handle month
                if result_df['Month'].dtype == 'O':  # If month is object/string
                    # Try to convert month names to numbers
                    month_map = {month[:3].lower(): i+1 for i, month in enumerate(calendar.month_name) if month}
                    result_df['MonthNum'] = result_df['Month'].str.lower().str[:3].map(month_map)
                else:
                    # If month is already numeric
                    result_df['MonthNum'] = result_df['Month']
                
                # Create date
                result_df['Date'] = pd.to_datetime(
                    result_df['Year'] + '-' + result_df['MonthNum'].astype(str) + '-15', 
                    errors='coerce'
                )
            except Exception as e:
                logger.warning(f"Error creating Date column: {e}")
                
        logger.info(f"Processed dataframe shape: {result_df.shape}")
        return result_df
        
    # If we couldn't identify columns properly, fall back to best guess
    logger.warning("Could not clearly identify columns, using best guess approach")
    
    # If we have at least one likely date column and one numeric column
    if len(date_cols) > 0 and len(numeric_cols) > 0:
        # Try to create a proper date and convert to long format
        try:
            # Use the first date column
            date_col = date_cols[0]
            df['temp_date'] = pd.to_datetime(df[date_col], errors='coerce')
            
            # Get route data from all numeric columns
            route_data = []
            for col in numeric_cols:
                for idx, row in df.iterrows():
                    if pd.notna(row[col]) and row[col] > 0:
                        route_data.append({
                            'Date': row['temp_date'],
                            'Year': row['temp_date'].dt.year,
                            'Month': row['temp_date'].dt.strftime('%b'),
                            'Route': col,
                            'Count': row[col]
                        })
            
            result_df = pd.DataFrame(route_data)
            logger.info(f"Created long format with best guess, shape: {result_df.shape}")
            return result_df
        except Exception as e:
            logger.error(f"Error in best guess approach: {e}")
    
    # If all else fails, return the original with a warning
    logger.warning("Could not process the data in any recognized format. "
                  "Manual intervention may be required.")
    return df

def main(excel_path, output_path='vancouver_bike_data.csv'):
    """
    Main function to extract and process Excel data
    
    Args:
        excel_path: Path to the Excel file
        output_path: Path to save the processed CSV
        
    Returns:
        DataFrame with processed data
    """
    # Extract data from Excel
    raw_data = extract_data_from_excel(excel_path)
    
    # Process and clean the data
    processed_data = process_bike_data(raw_data)
    
    # Save to CSV
    if processed_data is not None:
        processed_data.to_csv(output_path, index=False)
        logger.info(f"Data saved to {output_path}")
    else:
        logger.error("No processed data to save")
    
    return processed_data

if __name__ == "__main__":
    import sys
    
    # Get Excel path from command line or use default
    excel_path = sys.argv[1] if len(sys.argv) > 1 else "bike-volume-data.xlsx"
    
    # Get output path from command line or use default
    output_path = sys.argv[2] if len(sys.argv) > 2 else "vancouver_bike_data.csv"
    
    main(excel_path, output_path)