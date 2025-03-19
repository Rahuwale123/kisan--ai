from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from config import Config
import logging

class TwilioService:
    def __init__(self):
        self.client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)
        self.phone_number = Config.TWILIO_PHONE_NUMBER
        self.language_prompts = {
            'hi-IN': {
                'welcome': 'हेलो तो कैसे हैं आप?',
                'initial_prompt': 'नमस्ते, मैं दीक्षा बीएपी कंपनी के किसान विभाग से बात कर रही हूं।'
            },
            'mr-IN': {
                'welcome': 'नमस्कार, मी दीक्षा बीएपी कंपनी च्या शेतकरी विभागातून बोलत आहे.',
                'initial_prompt': 'नमस्कार, मी दीक्षा बीएपी कंपनी च्या शेतकरी विभागातून बोलत आहे.'
            },
            'en-IN': {
                'welcome': 'Hello, this is Diksha calling from BAP Company\'s farmer division.',
                'initial_prompt': 'Hello, this is Diksha calling from BAP Company\'s farmer division.'
            }
        }
        
    def get_gather_options(self, language='hi-IN'):
        """Get common gather options with enhanced noise suppression"""
        return Gather(
            input='speech',
            language=language,
            speech_timeout='auto',
            enhanced=True,
            speech_model='phone_call',
            profanity_filter=False,
            speech_threshold=0.8, 
            timeout=60,  
            hints='namaste,hello,namaskar,hi,hey',
            action='/voice',
            speech_contexts=['farming', 'agriculture', 'crops', 'animals'],
            background_audio_suppression=50, 
            interim_speech_results=False,
            partial_result_callback=None,
            speech_end_threshold=800,  
            speech_start_threshold=40 
        )

    def get_language_selection_response(self):
        """Initial response to detect language"""
        response = VoiceResponse()
        gather = self.get_gather_options('en-IN')
        
        for language in ['hi-IN', 'mr-IN', 'en-IN']:
            gather.say(self.language_prompts[language]['initial_prompt'], language=language)
            gather.pause(length=1)
        
        response.append(gather)
        response.redirect('/voice')
        return str(response)
    
    def get_initial_response(self, language='hi-IN'):
        """Get initial response in selected language"""
        response = VoiceResponse()
        gather = self.get_gather_options(language)
        gather.say(self.language_prompts[language]['welcome'], language=language)
        response.append(gather)
        return str(response)
    
    def convert_text_to_speech(self, text, language='hi-IN'):
        """Convert text to speech with better handling"""
        response = VoiceResponse()
        gather = response.gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            language=language
        )
        
        # Split long responses and add pauses
        sentences = text.split('।')
        for sentence in sentences:
            if sentence.strip():
                gather.say(
                    sentence.strip() + '।',
                    language='hi-IN',
                    
                    prosody={'rate': '90%', 'volume': 'loud'}
                )
                gather.pause(length=0.5)  # Small pause between sentences
            
        return str(response)

    def say_goodbye(self, language='hi-IN'):
        """Say goodbye in the selected language"""
        response = VoiceResponse()
        response.say(self.language_prompts[language]['goodbye'], language=language)
        response.hangup()
        return str(response)

    def initiate_call(self, to_number):
        """Initiate call with better timeout settings"""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=Config.TWILIO_PHONE_NUMBER,
                url=f"{Config.WEBHOOK_BASE_URL}/voice",
                timeout=30,  # Longer timeout
                status_callback=f"{Config.WEBHOOK_BASE_URL}/voice/status",
                status_callback_event=['completed', 'failed'],
                machine_detection='Enable'
            )
            return {
                'status': 'success',
                'call_sid': call.sid,
                'message': 'Call initiated successfully'
            }
        except Exception as e:
            logging.error(f"Call initiation error: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            } 