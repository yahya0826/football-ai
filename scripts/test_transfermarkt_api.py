#!/usr/bin/env python3
"""Test Transfermarkt API access"""
import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.transfermarkt.com/',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Son stats page
stats_url = 'https://www.transfermarkt.com/heung-min-son/profil/spieler/91845/statistik'
resp = requests.get(stats_url, headers=headers, timeout=15)
print(f'Stats page status: {resp.status_code}')
print(f'Response length: {len(resp.text)}')

if resp.status_code == 200:
    # Look for JSON data
    json_pattern = re.findall(r'\{[^{}]*\}', resp.text)
    print(f'JSON-like fragments: {len(json_pattern)}')

    # Try to find stats data
    data_patterns = re.findall(r'"season":"[^"]+".*?"goals":\d+', resp.text)
    print(f'Season stats found: {len(data_patterns)}')

    # Check for table
    tables = re.findall(r'<table[^>]*class="[^"]*stats[^"]*"[^>]*>', resp.text)
    print(f'Stats tables found: {len(tables)}')

    # Check for script with data
    script_data = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    for s in script_data:
        if 'player' in s.lower() and ('stats' in s.lower() or 'market' in s.lower()):
            print(f'Found relevant script, length: {len(s)}')
            break