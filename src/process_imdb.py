#!/usr/bin/env python3
"""
Standalone script to process IMDB data files and convert them to JSON.
Run this once before starting the Flask app.

Usage: python process_imdb.py
"""

from movies import Movies
import sys

def main():
    print("Starting IMDB data processing...")
    print("This may take a few minutes depending on file size...")
    
    try:
        movies_handler = Movies()
        result = movies_handler._process_imdb_data()
        
        if result:
            print("\n✓ IMDB data processing completed successfully!")
            print(f"  Movies saved to: data/movies.json")
        else:
            print("\n✗ No movies were processed. Check file paths and permissions.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Error processing IMDB data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
