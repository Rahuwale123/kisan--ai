import requests
import logging
import json

logging.basicConfig(level=logging.INFO)

def get_api_key():
    """Get API key for making calls"""
    try:
        url = "http://localhost:5000/generate-api-key"
        response = requests.post(url)
        result = response.json()
        
        if result.get('status') == 'success':
            logging.info(f"API Key generated successfully!")
            return result.get('api_key')
        else:
            logging.error(f"Failed to get API key: {result.get('message')}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting API key: {str(e)}")
        return None

def make_call(api_key, phone_number):
    """Make call using API key"""
    try:
        url = "http://localhost:5000/initiate-call"
        headers = {'X-API-Key': api_key}
        data = {'phone_number': phone_number}
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        if result.get('status') == 'success':
            logging.info(f"Call started successfully!")
            logging.info(f"Call SID: {result.get('call_sid')}")
        else:
            logging.error(f"Call failed: {result.get('message')}")
            
        return result
        
    except Exception as e:
        logging.error(f"Error making call: {str(e)}")
        return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    # Get API key first
    api_key = get_api_key()
    if api_key:
        # Ask for phone number
        phone_number = input("Enter phone number (with country code, e.g., +91XXXXXXXXXX): ")
        # Make the call
        make_call(api_key, phone_number)
    else:
        print("Could not get API key. Please try again.")