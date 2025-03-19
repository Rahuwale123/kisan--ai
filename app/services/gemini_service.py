import google.generativeai as genai
from config import Config
from app import cache
import logging
from app.services.db_manage import DatabaseManager
import json

class GeminiService:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.db_manager = DatabaseManager()
    
    def get_response(self, user_input, history=None, language='hi-IN', call_sid=None):
        """Get AI response with full conversation context"""
        try:
            conversation_context = ""
            is_first_call = False
            
            # Get farmer data if available
            farmer_data = None
            if call_sid:
                phone_number = cache.get(f'phone_{call_sid}')
                if phone_number:
                    farmer_data = self.db_manager.get_farmer_data(phone_number)
                    if farmer_data:
                        # Format farmer data for context
                        conversation_context = "Previous farmer information:\n"
                        if farmer_data['name']:
                            conversation_context += f"Name: {farmer_data['name']}\n"
                        if farmer_data['taluka']:
                            conversation_context += f"Location: {farmer_data['taluka']}\n"
                        if farmer_data['total_land']:
                            conversation_context += f"Total Land: {farmer_data['total_land']}\n"
                        if farmer_data['crops']:
                            crops = [f"{c['crop']} ({c['land_size']})" for c in farmer_data['crops']]
                            conversation_context += f"Crops: {', '.join(crops)}\n"
                        if farmer_data['animals']:
                            animals = [f"{a['name']} ({a['count']})" for a in farmer_data['animals']]
                            conversation_context += f"Animals: {', '.join(animals)}\n"
                        if farmer_data['milk_prod']:
                            conversation_context += f"Milk Production: {farmer_data['milk_prod']}\n"
                        if farmer_data['water_resource']:
                            conversation_context += f"Water Resources: {', '.join(farmer_data['water_resource'])}\n"
                        conversation_context += "\n"
                    else:
                        is_first_call = True
            
            # Add conversation history
            if history:
                # Only include last 2 exchanges for context
                recent_history = history[-2:]
                for exchange in recent_history:
                    conversation_context += f"User: {exchange['user']}\nDiksha: {exchange['ai']}\n"
            
            prompt = f"""
            You are Diksha (दीक्षा), a female farming expert from BAP Company's farmer division. Remember:
            1. When user responds to "कैसे हैं आप?", ALWAYS reply with:
               - For new farmers (no data): "नमस्ते! मैं दीक्षा बीएपी कंपनी के किसान विभाग से बात कर रही हूं। मैं आपको बेहतर मदद के लिए थोड़ी सी जानकारी चाहिए।"
               - For existing farmers: "नमस्ते [farmer_name] जी! क्या हाल चाल हैं? मैं दीक्षा बीएपी कंपनी के किसान विभाग से बात कर रही हूं।"
            2. After this introduction:
               - For new farmers: Ask their name naturally
               - For existing farmers: Focus on their current query
            3. Keep responses short and friendly
            4. Use farmer's name occasionally (not in every message)
            5. Give practical farming advice based on their data
            6. Make conversation feel natural like talking to a local farming expert
            7. IMPORTANT: Never repeat previous conversation details unless specifically asked
            8. Keep responses focused on the current question
            9. Use natural transitions between topics
            10. Avoid long explanations - be concise and clear

            IMPORTANT CONVERSATION RULES:
            For first-time callers (when no previous data exists):
            1. After they share their name, collect information naturally:
               - Village/area
               - Farming land size
               - Crops and land used
               - Water resources
               - Animals and milk production (if relevant)
               - Loans (if mentioned)
            2. Only ask one question at a time
            3. Don't force all questions - only ask what's relevant

            For returning callers (when we have previous data):
            1. Don't ask for information we already have
            2. Focus on their current query
            3. Reference their existing information when relevant
            4. Keep responses direct and to the point
            5. Don't summarize previous conversation unless asked
            
            Complete conversation context:
            {conversation_context}
            
            Current user message: {user_input}

            Example of natural conversation flow:
            User: मेरी फसल में कीड़े लग गए हैं
            Diksha: आपकी फसल में कीड़ों की समस्या के लिए मैं कुछ उपाय बताती हूं। क्या आप बता सकते हैं कि कौन से कीड़े दिख रहे हैं?

            User: सफेद कीड़े हैं
            Diksha: अच्छा, व्हाइट फ्लाई की समस्या लग रही है। इसके लिए नीम का तेल और पानी का घोल छिड़क सकते हैं।

            Respond naturally as Diksha, using conversation history and farmer data for context:"""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    'temperature': 0.7,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 200
                }
            )
            
            if response and hasattr(response, 'text'):
                return response.text
            else:
                logging.error("Invalid response from Gemini")
                return "मैं समझ नहीं पाई। फिर से बताओ क्या पूछना है?"

        except Exception as e:
            logging.error(f"Gemini error: {str(e)}")
            return "मैं समझ नहीं पाई। फिर से बताओ क्या पूछना है?"