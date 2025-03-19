from flask import Blueprint, request, abort, jsonify, session, current_app
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import VoiceResponse
from app.services.twilio_service import TwilioService
from app.services.gemini_service import GeminiService
from app.services.gemini_db import GeminiDB
from app.services.db_manage import DatabaseManager
from app import cache
from config import Config
import logging
import re
from datetime import datetime
import secrets
import uuid
import json

voice_bp = Blueprint('voice', __name__)
twilio_service = TwilioService()
gemini_service = GeminiService()
gemini_db = GeminiDB()
db_manager = DatabaseManager()

def validate_twilio_request():
    """Validate that the request is coming from Twilio"""
    try:
        validator = RequestValidator(Config.TWILIO_AUTH_TOKEN)
        
        url = f"{Config.BASE_URL}{request.path}"
        
        twilio_signature = request.headers.get('X-TWILIO-SIGNATURE', '')
        
        params = request.form.to_dict()
        
        logging.info(f"Validating request - URL: {url}")
        logging.info(f"Twilio signature: {twilio_signature}")
        logging.info(f"Params: {params}")
        
        is_valid = validator.validate(
            url,
            params,
            twilio_signature
        )
        
        if not is_valid:
            logging.warning(f"Validation failed for URL: {url}")
            logging.warning(f"Make sure Twilio AUTH TOKEN is correct: {Config.TWILIO_AUTH_TOKEN[:5]}...")
            
        return is_valid
        
    except Exception as e:
        logging.error(f"Validation error: {str(e)}")
        return False

def detect_language(text):
    """
    Enhanced language detection with better word recognition
    """
    # Common farming words in different languages
    hindi_words = [
        r'खेती', r'फसल', r'पानी', r'बीज', r'मौसम', r'किसान', 
        r'मैं', r'हमारे', r'कैसे', r'क्या', r'कब', r'कहाँ',
        r'बताओ', r'समस्या', r'मदद', r'धन्यवाद', r'नमस्ते'
    ]
    
    marathi_words = [
        r'शेती', r'पीक', r'पाणी', r'बी', r'हवामान', r'शेतकरी',
        r'मी', r'आमचे', r'कसे', r'काय', r'केव्हा', r'कुठे',
        r'सांगा', r'समस्या', r'मदत', r'धन्यवाद', r'नमस्कार'
    ]
    
    # Count words in each language
    hindi_matches = sum(1 for word in hindi_words if re.search(word, text))
    marathi_matches = sum(1 for word in marathi_words if re.search(word, text))
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    
    # More lenient detection logic
    if hindi_matches > marathi_matches and hindi_matches > english_words:
        return 'hi-IN'
    elif marathi_matches > hindi_matches and marathi_matches > english_words:
        return 'mr-IN'
    elif english_words > 2:  # If there are more than 2 English words
        return 'en-IN'
    else:
        # Default to Hindi if unclear
        return 'hi-IN'

def log_conversation(call_sid, role, language, text):
    """Log conversation details to terminal"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*80}")
    print(f"Time: {timestamp}")
    print(f"Call SID: {call_sid}")
    print(f"Language: {language}")
    print(f"Role: {role}")
    print(f"Message: {text}")
    print(f"{'='*80}\n")

@voice_bp.route('/voice', methods=['POST'])
def handle_call():
    """Handle incoming voice calls with better timeout"""
    try:
        call_sid = request.values.get('CallSid')
        language = cache.get(f'language_{call_sid}') or 'hi-IN'
        speech_result = request.values.get('SpeechResult', '').strip()
        
        # Store phone number in cache when call starts
        if not cache.get(f'phone_{call_sid}'):
            phone_number = request.values.get('From')  # For incoming calls
            if not phone_number:
                phone_number = request.values.get('To')  # For outgoing calls
            if phone_number:
                cache.set(f'phone_{call_sid}', phone_number)
        
        # Get complete conversation history
        history = cache.get(f'history_{call_sid}') or []
        
        if not speech_result:
            welcome_msg = 'हेलो तो कैसे हैं आप?'
            response = VoiceResponse()
            # Set 30 second timeout
            gather = response.gather(
                input='speech',
                timeout=30,  # Changed from 5 to 30 seconds
                speech_timeout='auto',
                language=language
            )
            gather.say(welcome_msg, language='hi-IN')
            
            # Add message after timeout
            response.say(
                "आप काफी देर से चुप हैं। मैं कॉल काट रही हूं। जरूरत हो तो फिर से कॉल करना।", 
                language='hi-IN'
            )
            response.hangup()
            return str(response)

        # For ongoing conversation
        ai_response = gemini_service.get_response(
            speech_result,
            history=history,
            language=language,
            call_sid=call_sid
        )
        
        # Update conversation history
        history.append({
            'user': speech_result,
            'ai': ai_response,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        cache.set(f'history_{call_sid}', history)
        
        # Create response with 30 second timeout
        response = VoiceResponse()
        gather = response.gather(
            input='speech',
            timeout=30,  # Changed from 5 to 30 seconds
            speech_timeout='auto',
            language=language
        )
        
        # Break response into natural chunks
        sentences = ai_response.split('।')
        for sentence in sentences:
            if sentence.strip():
                gather.say(
                    sentence.strip() + '।', 
                    language='hi-IN', 
                    
                    prosody={'rate': '90%', 'volume': 'loud'}
                )
                gather.pause(length=0.5)
        
        # Add timeout message and hangup
        response.say(
            "आप काफी देर से चुप हैं। मैं कॉल काट रही हूं। जरूरत हो तो फिर से कॉल करना।", 
            language='hi-IN'
        )
        response.hangup()
        
        return str(response)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        response = VoiceResponse()
        response.say(
            "मैं समझ नहीं पाई। फिर से बताओ।", 
            language='hi-IN'
        )
        return str(response)

@voice_bp.route('/voice/set-language', methods=['POST'])
def set_language():
    """Handle language selection"""
    try:
        if not Config.DEBUG and not validate_twilio_request():
            response = VoiceResponse()
            response.say("Sorry, there was an authentication error.")
            return str(response), 200
        
        digits = request.values.get('Digits', '')
        call_sid = request.values.get('CallSid')
        
        language_map = {
            '1': 'hi-IN',
            '2': 'mr-IN',
            '3': 'en-IN'
        }
        
        selected_language = language_map.get(digits, 'hi-IN')
        cache.set(f'language_{call_sid}', selected_language)
        
        return twilio_service.get_initial_response(selected_language)
        
    except Exception as e:
        logging.error(f"Error in set_language: {str(e)}")
        response = VoiceResponse()
        response.say("Sorry, an error occurred during language selection.")
        return str(response), 200

@voice_bp.route('/generate-api-key', methods=['POST'])
def generate_api_key():
    """Generate API key for call initiation"""
    try:
        # Generate a unique API key
        api_key = secrets.token_urlsafe(32)
        
        # Store API key with timestamp
        cache.set(
            f'api_key_{api_key}', 
            {
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'is_active': True
            },
            timeout=86400  # Key valid for 24 hours
        )
        
        return jsonify({
            'status': 'success',
            'api_key': api_key,
            'message': 'Use this API key to initiate calls',
            'valid_for': '24 hours'
        })
        
    except Exception as e:
        logging.error(f"Error generating API key: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate API key'
        }), 500

@voice_bp.route('/initiate-call', methods=['POST'])
def initiate_call():
    """Endpoint to initiate a call without API key requirement"""
    try:
        # Get phone number from request
        phone_number = request.json.get('phone_number')
        
        # Validate phone number
        if not phone_number:
            return jsonify({
                'status': 'error',
                'message': 'Phone number is required'
            }), 400
            
        # Log call initiation
        print(f"\n{'*'*40} INITIATING CALL {'*'*40}")
        print(f"To Number: {phone_number}")
        
        # Initiate call using Twilio service
        result = twilio_service.initiate_call(phone_number)
        print(f"Result: {result}")
        print(f"{'*'*89}\n")
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error initiating call: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@voice_bp.route('/voice/status', methods=['POST'])
def call_status():
    """Handle call status callbacks with conversation analysis"""
    try:
        call_sid = request.values.get('CallSid')
        call_status = request.values.get('CallStatus')
        
        logging.info(f"Call {call_sid} status: {call_status}")
        
        # When call completes, analyze conversation
        if call_status == 'completed':
            # Get conversation history
            history = cache.get(f'history_{call_sid}') or []
            
            if history:
                # Print complete conversation
                print(f"\n{'*'*40} COMPLETE CONVERSATION {'*'*40}")
                for exchange in history:
                    print(f"User: {exchange['user']}\nDiksha: {exchange['ai']}\n")
                print(f"{'*'*89}\n")
                
                # Get phone number
                phone_number = cache.get(f'phone_{call_sid}')
                
                # Analyze conversation and extract farmer data
                farmer_data = gemini_db.analyze_conversation(history, phone_number=phone_number)
                
                # Print farmer data
                print(f"\n{'*'*40} FARMER DATA {'*'*40}")
                print(json.dumps(farmer_data, indent=2, ensure_ascii=False))
                print(f"{'*'*89}\n")
                
                # Save to MySQL database
                if db_manager.save_farmer_data(farmer_data):
                    print(f"\nSuccessfully saved farmer data to MySQL database for {phone_number}")
                else:
                    print(f"\nFailed to save farmer data to MySQL database for {phone_number}")
                
                # Clear conversation history from cache
                cache.delete(f'history_{call_sid}')
                cache.delete(f'language_{call_sid}')
                cache.delete(f'phone_{call_sid}')
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logging.error(f"Error in call status: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})