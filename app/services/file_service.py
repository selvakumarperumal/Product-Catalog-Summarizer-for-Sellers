# Business logic - file handling
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from pathlib import Path
from app.exceptions.errors import (
    FileNotFoundError,
    EmptyFileError,
    CSVReadError,
    DataFrameError,
    ChunkingError,
    FileAccessError,
    FileCorruptedError
)
import logging

logger = logging.getLogger(__name__)

class FileProcessor:
    """Service class for processing uploaded files and creating chunks for LLM processing"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 500):
        """
        Initialize the file processor with configurable chunking parameters
        
        Args:
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    
    def read_csv_file(self, file_path: str, max_rows: Optional[int] = None) -> pd.DataFrame:
        """
        Read CSV file and return DataFrame
        
        Args:
            file_path: Path to the CSV file
            max_rows: Maximum number of rows to read (None for all rows)
            
        Returns:
            pandas DataFrame
            
        Raises:
            FileNotFoundError: If file doesn't exist
            CSVReadError: If there's an error reading the CSV
            EmptyFileError: If file is empty
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file permissions
        if not os.access(file_path, os.R_OK):
            logger.error(f"File access denied: {file_path}")
            raise FileAccessError(f"Permission denied to read file: {file_path}")
        
        try:
            data = pd.read_csv(file_path)
            
            # Check if file is empty
            if data.empty:
                logger.error(f"CSV file is empty: {file_path}")
                raise EmptyFileError("The CSV file is empty")
            
            if max_rows:
                data = data.head(max_rows)
            
            logger.info(f"Successfully read CSV file: {file_path} with {len(data)} rows")
            return data
            
        except pd.errors.EmptyDataError:
            logger.error(f"CSV file has no data: {file_path}")
            raise EmptyFileError("The CSV file contains no data")
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error for {file_path}: {str(e)}")
            raise FileCorruptedError(f"Unable to parse CSV file: {str(e)}")
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {file_path}: {str(e)}")
            raise FileCorruptedError(f"File encoding error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error reading CSV {file_path}: {str(e)}")
            raise CSVReadError(f"Error reading CSV file: {str(e)}")
    
    def prepare_data_for_processing(self, data: pd.DataFrame) -> Tuple[str, str]:
        """
        Prepare DataFrame data for LLM processing
        
        Args:
            data: pandas DataFrame
            
        Returns:
            Tuple of (column_names, csv_data_string)
            
        Raises:
            DataFrameError: If there's an error processing the DataFrame
            EmptyFileError: If DataFrame is empty
        """
        try:
            if data.empty:
                logger.error("DataFrame is empty during data preparation")
                raise EmptyFileError("DataFrame contains no data")
            
            # Get column names
            columns = ", ".join(data.columns.tolist())
            
            # Convert to CSV string
            data_csv = data.to_csv(index=False, header=False)
            
            if not data_csv.strip():
                logger.error("Generated CSV string is empty")
                raise DataFrameError("Failed to convert DataFrame to CSV format")
            
            logger.info(f"Successfully prepared data with {len(data)} rows and {len(data.columns)} columns")
            return columns, data_csv
            
        except EmptyFileError:
            raise  # Re-raise our custom exception
        except Exception as e:
            logger.error(f"Error preparing DataFrame for processing: {str(e)}")
            raise DataFrameError(f"Failed to prepare data for processing: {str(e)}")
    
    def create_chunks(self, text_data: str) -> List[str]:
        """
        Split text data into chunks for processing
        
        Args:
            text_data: String data to be chunked
            
        Returns:
            List of text chunks
            
        Raises:
            ChunkingError: If there's an error during text splitting
            EmptyFileError: If input data is empty
        """
        if not text_data or not text_data.strip():
            logger.error("Empty text data provided for chunking")
            raise EmptyFileError("No text data provided for chunking")
        
        try:
            chunks = self.text_splitter.split_text(text_data)
            
            if not chunks:
                logger.error("Text splitter returned no chunks")
                raise ChunkingError("Failed to create any chunks from the text data")
            
            logger.info(f"Successfully created {len(chunks)} chunks from text data")
            return chunks
            
        except Exception as e:
            logger.error(f"Error during text chunking: {str(e)}")
            raise ChunkingError(f"Failed to split text into chunks: {str(e)}")
    
    def process_file_to_chunks(self, file_path: str) -> Tuple[str, List[str]]:
        """
        Complete pipeline: read file, prepare data, and create chunks
        
        Args:
            file_path: Path to the file to process
            max_rows: Maximum number of rows to process
            
        Returns:
            Tuple of (column_names, list_of_chunks)
        """
        # Read the file
        data = self.read_csv_file(file_path)
        data = data.replace(r"[\n\r]", " ", regex=True)
        data.insert(0, "row_id", range(1, len(data) + 1))
        
        logger.info(f"Data after reading file: {data.head()}")
        # Prepare data for processing
        columns, data_csv = self.prepare_data_for_processing(data)
        
        # Create chunks
        chunks = self.create_chunks(data_csv)
        
        return columns, chunks
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about the file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_name = Path(file_path).name
        
        # For CSV files, get additional info
        if file_path.lower().endswith('.csv'):
            try:
                data = pd.read_csv(file_path)
                return {
                    "file_name": file_name,
                    "file_size": file_size,
                    "total_rows": len(data),
                    "total_columns": len(data.columns),
                    "columns": data.columns.tolist(),
                    "file_type": "csv"
                }
            except Exception as e:
                return {
                    "file_name": file_name,
                    "file_size": file_size,
                    "error": f"Could not read CSV: {str(e)}",
                    "file_type": "csv"
                }
        
        return {
            "file_name": file_name,
            "file_size": file_size,
            "file_type": Path(file_path).suffix
        }


# Convenience functions for backward compatibility and ease of use
def process_csv_to_chunks(file_path: str, chunk_size: int = 1000) -> Tuple[str, List[str]]:
    """
    Convenience function to process a CSV file and return chunks
    
    Args:
        file_path: Path to the CSV file
        max_rows: Maximum number of rows to process
        chunk_size: Size of each chunk
        
    Returns:
        Tuple of (column_names, list_of_chunks)
    """
    processor = FileProcessor(chunk_size=chunk_size)
    return processor.process_file_to_chunks(file_path)


def get_csv_info(file_path: str) -> Dict[str, Any]:
    """
    Convenience function to get CSV file information
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Dictionary with file information
    """
    processor = FileProcessor()
    return processor.get_file_info(file_path)

