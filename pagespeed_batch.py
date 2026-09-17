#!/usr/bin/env python3
"""
PageSpeed Insights Batch Scraper – Appends results to existing CSV
Usage: python3 pagespeed_batch.py leads.csv
"""

import csv
import requests
import time
import sys
import re
from datetime import datetime

API_KEY =   # Replace with your actual key

# List of possible column names for website URLs
URL_COLUMN_CANDIDATES = ['website', 'url', 'Website', 'URL', 'site', 'domain', 'web', 'link']

def detect_url_column(headers):
    """Find the column name that contains URLs."""
    for candidate in URL_COLUMN_CANDIDATES:
        if candidate in headers:
            return candidate
    # If none found, ask the user
    print("Could not detect a URL column. Please enter the exact column name containing the URLs:")
    return input().strip()

def run_pagespeed(url):
    """Run PageSpeed Insights API on a URL and return a dict of scores."""
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        'url': url,
        'key': API_KEY,
        'category': ['performance', 'accessibility', 'best-practices', 'seo'],
        'strategy': 'mobile'
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=60)
        data = response.json()
        
        if 'error' in data:
            print(f"  ❌ API Error: {data['error']['message']}")
            return None
        
        # Extract metrics
        scores = {
            'performance': data['lighthouseResult']['categories']['performance']['score'] * 100,
            'accessibility': data['lighthouseResult']['categories']['accessibility']['score'] * 100,
            'best_practices': data['lighthouseResult']['categories']['best-practices']['score'] * 100,
            'seo': data['lighthouseResult']['categories']['seo']['score'] * 100,
            'fcp': data['lighthouseResult']['audits']['first-contentful-paint']['numericValue'],
            'lcp': data['lighthouseResult']['audits']['largest-contentful-paint']['numericValue'],
            'tbt': data['lighthouseResult']['audits']['total-blocking-time']['numericValue'],
            'cls': data['lighthouseResult']['audits']['cumulative-layout-shift']['numericValue']
        }
        return scores
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 pagespeed_batch.py your_file.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = input_file  # Overwrite the same file
    
    # Read the CSV
    rows = []
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    
    if not rows:
        print("❌ The CSV file is empty.")
        return
    
    # Detect URL column
    url_col = detect_url_column(fieldnames)
    if url_col not in fieldnames:
        print(f"❌ Column '{url_col}' not found. Available columns: {', '.join(fieldnames)}")
        return
    
    # Prepare new columns
    new_columns = ['performance', 'accessibility', 'best_practices', 'seo', 'fcp', 'lcp', 'tbt', 'cls']
    # Add them to fieldnames if not already present (won't duplicate)
    for col in new_columns:
        if col not in fieldnames:
            fieldnames.append(col)
    
    print(f"🔍 Processing {len(rows)} URLs from column '{url_col}'...")
    
    # Process each row
    for i, row in enumerate(rows, 1):
        url = row.get(url_col, '').strip()
        if not url or url == '#':
            print(f"[{i}/{len(rows)}] ⏭️ Skipping empty/invalid URL")
            # Fill with N/A
            for col in new_columns:
                row[col] = 'N/A'
            continue
        
        # Validate URL
        if not url.startswith('http'):
            url = 'https://' + url
        
        print(f"[{i}/{len(rows)}] Testing: {url}")
        result = run_pagespeed(url)
        
        if result:
            for key, value in result.items():
                # Round floating numbers to 2 decimals
                if isinstance(value, float):
                    value = round(value, 2)
                row[key] = value
            print(f"  ✅ Performance: {result['performance']:.1f}")
        else:
            # Fill with N/A on failure
            for col in new_columns:
                row[col] = 'N/A'
            print(f"  ❌ Failed – marked as N/A")
        
        # Add a small delay to avoid rate limiting
        time.sleep(2)
    
    # Write the updated rows back to the same file
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✅ Results appended to {output_file}")

if __name__ == "__main__":
    main()
