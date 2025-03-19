import google.generativeai as genai
from config import Config
import json
import logging
import re
from app.schemas.farmer_schema import DEFAULT_FARMER_DATA
from app.services.db_manage import DatabaseManager

class GeminiDB:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.db_manager = DatabaseManager()
        
    def clean_response(self, text):
        """Remove markdown formatting from response"""
        # Remove ```json from start and ``` from end
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return text.strip()
        
    def analyze_conversation(self, conversation_history, phone_number=None):
        """Analyze conversation and extract farmer information"""
        try:
            # Get existing farmer data if available
            existing_data = None
            if phone_number:
                existing_data = self.db_manager.get_farmer_data(phone_number)
            
            # Format existing data for prompt
            existing_data_text = ""
            if existing_data:
                existing_data_text = "Previous farmer data:\n"
                if existing_data['name']:
                    existing_data_text += f"Name: {existing_data['name']}\n"
                if existing_data['taluka']:
                    existing_data_text += f"Location: {existing_data['taluka']}\n"
                if existing_data['total_land']:
                    existing_data_text += f"Total Land: {existing_data['total_land']}\n"
                if existing_data['crops']:
                    crops = [f"{c['crop']} ({c['land_size']})" for c in existing_data['crops']]
                    existing_data_text += f"Crops: {', '.join(crops)}\n"
                if existing_data['animals']:
                    animals = [f"{a['name']} ({a['count']})" for a in existing_data['animals']]
                    existing_data_text += f"Animals: {', '.join(animals)}\n"
                if existing_data['milk_prod']:
                    existing_data_text += f"Milk Production: {existing_data['milk_prod']}\n"
                if existing_data['water_resource']:
                    existing_data_text += f"Water Resources: {', '.join(existing_data['water_resource'])}\n"
            
            # Prepare conversation text
            conversation_text = "\n".join([
                f"User: {exchange['user']}\nDiksha: {exchange['ai']}"
                for exchange in conversation_history
            ])
            
            prompt = f"""
            Analyze this conversation between a farmer and Diksha (an agricultural assistant) and extract structured information.
            Return ONLY a JSON object matching this exact structure (do not include any other text).
            IMPORTANT: All data in the JSON must be in English, even if the conversation is in another language.

            {existing_data_text}

            JSON Structure:
            {{
                "phone_number": string or null,
                "name": string or null (translate to English if in another language),
                "taluka": string or null (keep original name but in English script),
                "village": null,
                "total_land": string or null,
                "crops": [
                    {{"crop": string (in English), "land_size": string}}
                ],
                "animals": [
                    {{"name": string (in English), "count": number}}
                ],
                "milk_prod": string or null,
                "loan": string or null,
                "water_resource": [string (in English)]
            }}

            Rules:
            1. Use existing farmer data as context and only update fields that have new information
            2. Keep unchanged fields from existing data
            3. Only include new information explicitly mentioned in the conversation
            4. Use null for any fields not mentioned and not in existing data
            5. Keep original units (acres, bigha, etc.) as mentioned
            6. For partial information, include what's available
            7. Infer location details (taluka/village) from context if mentioned
            8. Include all mentioned crops and animals
            9. Water resources can be: Well, Borewell, Canal, Rain, River, etc.
            10. TRANSLATE ALL TEXT TO ENGLISH, except for proper nouns like place names
            11. For place names (taluka/village), keep the original name but write it in English script

            Conversation:
            {conversation_text}
            """

            response = self.model.generate_content(prompt)
            
            # Clean and parse response
            if response and hasattr(response, 'text'):
                cleaned_response = self.clean_response(response.text)
                try:
                    farmer_data = json.loads(cleaned_response)
                    
                    # Merge with existing data if available
                    if existing_data:
                        for key in farmer_data:
                            if farmer_data[key] is None and key in existing_data:
                                farmer_data[key] = existing_data[key]
                    
                    # Ensure arrays are initialized
                    if 'crops' not in farmer_data or farmer_data['crops'] is None:
                        farmer_data['crops'] = []
                    if 'animals' not in farmer_data or farmer_data['animals'] is None:
                        farmer_data['animals'] = []
                    if 'water_resource' not in farmer_data or farmer_data['water_resource'] is None:
                        farmer_data['water_resource'] = []
                    
                    complete_data = DEFAULT_FARMER_DATA.copy()
                    complete_data.update(farmer_data)
                    
                    # Ensure phone number is set
                    if phone_number:
                        complete_data['phone_number'] = phone_number
                    
                    return complete_data
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing Gemini response: {str(e)}")
                    return DEFAULT_FARMER_DATA
            else:
                logging.error("Invalid response from Gemini")
                return DEFAULT_FARMER_DATA
                
        except Exception as e:
            logging.error(f"Error analyzing conversation: {str(e)}")
            return DEFAULT_FARMER_DATA
