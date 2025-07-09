
from flask import Flask, render_template, request, jsonify
import requests
import json
import re

app = Flask(__name__)

def parse_cash_value(value_str):
    """Parse cash values like '3m', '500k', '1.5m' into actual numbers"""
    if not value_str or value_str == "0" or value_str == 0:
        return 0
    
    # Convert to string and remove any extra spaces/symbols
    value_str = str(value_str).strip().lower()
    
    # Extract number and suffix
    match = re.match(r'([\d.]+)([km]?)', value_str)
    if not match:
        try:
            return int(float(value_str))
        except:
            return 0
    
    number, suffix = match.groups()
    number = float(number)
    
    if suffix == 'k':
        return int(number * 1000)
    elif suffix == 'm':
        return int(number * 1000000)
    else:
        return int(number)

# Base API URL
API_BASE_URL = "https://api.jailbreakchangelogs.xyz/items/list"

@app.route('/')
def home():
    """Main page displaying all items from the API"""
    try:
        response = requests.get(API_BASE_URL)
        response.raise_for_status()
        all_items = response.json()
        
        # Get search parameter only
        search_query = request.args.get('search', '').strip()
        
        # Filter for only vehicles and add parsed cash values
        vehicles = []
        for item in all_items:
            if item.get('type', '').lower() == 'vehicle':
                # Parse the cash_value field
                item['parsed_cash_value'] = parse_cash_value(item.get('cash_value', 0))
                
                # Skip items that are not tradable
                if item.get('tradable', 1) == 0:
                    continue
                
                # Apply search filter if there's a search query
                if search_query:
                    if search_query.lower() in item.get('name', '').lower():
                        vehicles.append(item)
                else:
                    # Show all tradable vehicles when not searching
                    vehicles.append(item)
        
        # Always sort by price (most expensive first)
        vehicles.sort(key=lambda x: x['parsed_cash_value'], reverse=True)
        
        return render_template('index.html', items=vehicles, search_query=search_query)
    except requests.RequestException as e:
        return render_template('index.html', items=[], error=f"Error fetching data: {str(e)}")

@app.route('/api/items')
def api_items():
    """JSON endpoint for items data"""
    try:
        response = requests.get(API_BASE_URL)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/item/<item_name>')
def item_detail(item_name):
    """Show details for a specific item"""
    try:
        response = requests.get(API_BASE_URL)
        response.raise_for_status()
        all_items = response.json()
        # Filter for only vehicles
        vehicles = [item for item in all_items if item.get('type', '').lower() == 'vehicle']
        
        # Find the specific item
        item = None
        for i in vehicles:
            if i.get('name', '').lower() == item_name.lower():
                item = i
                break
        
        if item:
            return render_template('item_detail.html', item=item)
        else:
            return render_template('item_detail.html', item=None, error="Vehicle not found")
    except requests.RequestException as e:
        return render_template('item_detail.html', item=None, error=f"Error fetching data: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
