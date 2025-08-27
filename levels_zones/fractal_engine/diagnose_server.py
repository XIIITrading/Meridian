"""
diagnose_server.py - Check which endpoints your Polygon server supports
"""

import requests
import json
from datetime import datetime, timedelta

def diagnose_server():
    server_url = "http://localhost:8200"
    api_key = "your_api_key_here"  # Replace with your actual API key
    
    print("Polygon Server Endpoint Diagnostics")
    print("=" * 60)
    
    # Test date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    from_str = start_date.strftime("%Y-%m-%d")
    to_str = end_date.strftime("%Y-%m-%d")
    
    # Test various endpoint formats
    test_endpoints = [
        {
            "name": "Standard Polygon v2 Aggregates",
            "url": f"{server_url}/v2/aggs/ticker/SPY/range/15/minute/{from_str}/{to_str}",
            "params": {"apiKey": api_key, "adjusted": "true", "sort": "asc", "limit": 10}
        },
        {
            "name": "Alternative bars endpoint",
            "url": f"{server_url}/bars",
            "params": {"ticker": "SPY", "from": from_str, "to": to_str, "timeframe": "15minute", "apiKey": api_key}
        },
        {
            "name": "OpenAPI Specification",
            "url": f"{server_url}/openapi.json",
            "params": {}
        },
        {
            "name": "Root endpoint",
            "url": f"{server_url}/",
            "params": {}
        }
    ]
    
    for test in test_endpoints:
        print(f"\nTesting: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            response = requests.get(test['url'], params=test['params'], timeout=10)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Endpoint works!")
                
                # Try to parse response
                try:
                    data = response.json()
                    if 'results' in data:
                        print(f"  Found {len(data['results'])} results")
                    elif 'paths' in data:
                        print(f"  Found {len(data['paths'])} API paths")
                        # List first few paths
                        for i, path in enumerate(list(data['paths'].keys())[:5]):
                            print(f"    - {path}")
                        if len(data['paths']) > 5:
                            print(f"    ... and {len(data['paths']) - 5} more")
                except:
                    print(f"  Response preview: {response.text[:200]}...")
            else:
                print(f"✗ Failed with status {response.status_code}")
                if response.text:
                    print(f"  Error: {response.text[:200]}")
                    
        except Exception as e:
            print(f"✗ Connection error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Diagnostics complete")

if __name__ == "__main__":
    diagnose_server()