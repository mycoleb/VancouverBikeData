import pandas as pd
import numpy as np
import re
import io
import sys
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from datetime import datetime
import calendar
from matplotlib.colors import LinearSegmentedColormap
import os

# For PDF extraction
import PyPDF2
try:
    import tabula
except ImportError:
    print("tabula-py not installed. Install with: pip install tabula-py")
    print("Note: tabula-py requires Java to be installed")

def extract_data_from_pdf(pdf_path):
    """
    Extract bike count data from Vancouver's PDF format
    """
    print(f"Extracting data from {pdf_path}...")
    
    # Try using tabula-py first (better for structured tables)
    try:
        # Read all tables from the PDF
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        
        if tables and len(tables) > 0:
            print(f"Successfully extracted {len(tables)} tables with tabula")
            
            # Process the tables
            # The main table should be the largest one
            main_table = max(tables, key=lambda x: x.size)
            
            # Clean up the table
            # Drop completely empty rows and columns
            main_table = main_table.dropna(how='all').dropna(axis=1, how='all')
            
            return main_table
    except Exception as e:
        print(f"Error using tabula: {e}")
    
    # Fallback to PyPDF2 if tabula fails
    print("Falling back to PyPDF2 extraction method...")
    
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text()
        
        # Parse the text to extract the data
        # This requires custom parsing logic based on the PDF structure
        
        # Split the text by lines
        lines = text.split('\n')
        
        # Look for the section with the data table
        data_lines = []
        capture = False
        
        for line in lines:
            # Try to identify the start of the table (modify based on actual PDF content)
            if re.match(r'^\d{1,2}-[A-Za-z]{3}', line):  # Matches patterns like "9-Aug"
                capture = True
            
            if capture:
                data_lines.append(line)
        
        # Process the captured lines to create a table structure
        data = []
        headers = []
        
        # Extract headers (this will depend on the actual PDF structure)
        # For example, looking for the line before the data starts
        for i, line in enumerate(lines):
            if "Burrard Bridge" in line and "Hornby Street" in line:
                headers = line.split()
                break
        
        # Process each data line
        for line in data_lines:
            # Split the line into values
            values = re.findall(r'\d+,\d+|\d+|[A-Za-z]{3}', line)
            
            if len(values) > 3:  # Ensure we have enough data
                # First value should be the date
                date_match = re.match(r'(\d{1,2})-([A-Za-z]{3})', values[0])
                if date_match:
                    year = date_match.group(1)
                    month = date_match.group(2)
                    row = {'Year': f"20{year}", 'Month': month}
                    
                    # Add the count values
                    for i, value in enumerate(values[1:]):
                        if i < len(headers):
                            col_name = headers[i]
                            # Convert values like "139,000" to integers
                            count = int(value.replace(',', '')) if ',' in value else int(value)
                            row[col_name] = count
                    
                    data.append(row)
        
        # Create DataFrame
        if data:
            df = pd.DataFrame(data)
            return df
        else:
            print("Failed to extract data using PyPDF2")
            return None
            
    except Exception as e:
        print(f"Error using PyPDF2: {e}")
        return None

def process_bike_data(df):
    """
    Process and clean the extracted data
    """
    if df is None:
        print("No data to process")
        return None
    
    # Display the first few rows to see the structure
    print("Data preview:")
    print(df.head())
    
    # Ensure we have proper column names
    if 'Year' not in df.columns and 'Month' not in df.columns:
        # Try to identify date columns based on patterns
        date_col = None
        for col in df.columns:
            if df[col].astype(str).str.match(r'^\d{1,2}-[A-Za-z]{3}').any():
                date_col = col
                break
        
        if date_col:
            # Extract year and month from the date column
            df['temp'] = df[date_col]
            df['Year'] = df['temp'].str.extract(r'(\d{1,2})')[0].apply(lambda x: f'20{x}')
            df['Month'] = df['temp'].str.extract(r'-([A-Za-z]{3})')[0]
            df = df.drop('temp', axis=1)
        else:
            print("Could not identify date column")
    
    # Convert count columns to numeric
    for col in df.columns:
        if col not in ['Year', 'Month']:
            try:
                # Handle values like "139,000" or "*"
                df[col] = df[col].astype(str).str.replace(',', '').replace('*', np.nan).astype(float)
            except:
                print(f"Could not convert column {col} to numeric")
    
    # Create a proper date column
    if 'Year' in df.columns and 'Month' in df.columns:
        # Convert month abbreviations to numbers
        month_map = {month[:3]: i+1 for i, month in enumerate(calendar.month_name) if month}
        df['MonthNum'] = df['Month'].map(month_map)
        
        # Create date column (use day 15 as mid-month reference)
        df['Date'] = pd.to_datetime(df['Year'] + '-' + df['MonthNum'].astype(str) + '-15')
        
        # Sort by date
        df = df.sort_values('Date')
    
    return df

def create_long_format_data(df):
    """
    Convert data from wide format to long format
    """
    if df is None:
        return None
    
    # Identify route columns (all except Year, Month, MonthNum, Date)
    route_cols = [col for col in df.columns if col not in ['Year', 'Month', 'MonthNum', 'Date']]
    
    # Create long format data
    long_data = []
    
    for _, row in df.iterrows():
        for route in route_cols:
            if pd.notna(row[route]):
                long_data.append({
                    'Date': row['Date'],
                    'Year': row['Year'],
                    'Month': row['Month'],
                    'Route': route,
                    'Count': row[route]
                })
    
    return pd.DataFrame(long_data)

def save_to_csv(df, output_path):
    """
    Save processed data to CSV
    """
    if df is not None:
        df.to_csv(output_path, index=False)
        print(f"Data saved to {output_path}")
    else:
        print("No data to save")

def main(pdf_path, output_path='vancouver_bike_data.csv'):
    # Extract data from PDF
    raw_data = extract_data_from_pdf(pdf_path)
    
    # Process and clean the data
    processed_data = process_bike_data(raw_data)
    
    # Convert to long format
    long_data = create_long_format_data(processed_data)
    
    # Save to CSV
    save_to_csv(long_data, output_path)
    
    return long_data

if __name__ == "__main__":
    # Get PDF path from command line or use default
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "vancouver_bike_data.pdf"
    
    # Get output path from command line or use default
    output_path = sys.argv[2] if len(sys.argv) > 2 else "vancouver_bike_data.csv"
    
    main(pdf_path, output_path)