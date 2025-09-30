import os
import json
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure Gemini
gemini_api_key = os.getenv("GEMINI_API_KEY")
model = None

if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("models/gemini-2.0-flash-exp")
        logging.info("Gemini model initialized")
    except Exception as e:
        logging.error(f"Error initializing Gemini: {e}")

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"message": "RAGPT API is running!", "status": "ok"}
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        if self.path == '/api/generate-recipe' or self.path == '/generate-recipe':
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                ingredients = data.get('ingredients', '')
                
                if not ingredients:
                    self.send_response(400)
                    self._set_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Ingredients required"}).encode())
                    return
                
                if not model:
                    self.send_response(500)
                    self._set_cors_headers()
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Gemini not configured"}).encode())
                    return
                
                # Generate recipe
                prompt = f"""
                You are a world-class chef. Create a unique dinner recipe based on the following ingredients: {ingredients}.
                IMPORTANT: Your entire response must be ONLY a single, valid JSON object. Do not include any text, backticks, or explanations.
                The JSON object must have these exact keys: "recipe_name", "description", "ingredients", "instructions".
                """
                
                response = model.generate_content(prompt)
                raw_content = response.text
                
                # Extract JSON
                start_index = raw_content.find('{')
                end_index = raw_content.rfind('}')
                
                if start_index != -1 and end_index != -1:
                    clean_json_str = raw_content[start_index : end_index + 1]
                    try:
                        recipe_obj = json.loads(clean_json_str)
                        
                        # Ensure ingredients is a list
                        if isinstance(recipe_obj.get("ingredients"), str):
                            recipe_obj["ingredients"] = [i.strip() for i in recipe_obj["ingredients"].split(',') if i.strip()]
                        
                        # Ensure instructions is a list
                        if isinstance(recipe_obj.get("instructions"), str):
                            recipe_obj["instructions"] = [i.strip() for i in recipe_obj["instructions"].split('.') if i.strip()]
                        
                        self.send_response(200)
                        self._set_cors_headers()
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"recipe": json.dumps(recipe_obj)}).encode())
                        return
                    except Exception as e:
                        logging.error(f"JSON parse error: {e}")
                
                # Fallback
                self.send_response(200)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"recipe": raw_content}).encode())
                
            except Exception as e:
                logging.error(f"Error: {e}")
                self.send_response(500)
                self._set_cors_headers()
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self._set_cors_headers()
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
