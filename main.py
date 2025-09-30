import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Configure the Gemini client
model = None
try:
    # Correctly load the API key by its variable name
    gemini_api_key = os.getenv("GEMINI_API_KEY") 
    
    if not gemini_api_key:
        logging.error("GEMINI_API_KEY environment variable not found in .env file.")
    else:
        genai.configure(api_key=gemini_api_key)
        # Try different model names that might work
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        logging.info("Google Gemini model initialized successfully.")
except Exception as e:
    logging.error(f"Error configuring Gemini client: {e}")

# Initialize FastAPI app and CORS
app = FastAPI()
origins = ["http://localhost", "http://localhost:8080", "http://127.0.0.1:5500"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Define request model
class IngredientsRequest(BaseModel):
    ingredients: str

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "AI Chef Backend (Google Gemini) is running!"}

# Test endpoint to list available models
@app.get("/list-models")
def list_models():
    try:
        models = genai.list_models()
        available_models = [model.name for model in models if 'generateContent' in model.supported_generation_methods]
        return {"available_models": available_models}
    except Exception as e:
        return {"error": str(e)}

# Main endpoint for generating recipes
@app.post("/generate-recipe")
async def generate_recipe(request: IngredientsRequest):
    if not model:
        raise HTTPException(status_code=500, detail="Gemini model not initialized. Check server logs.")

    try:
        prompt = f"""
        You are a world-class chef. Create a unique dinner recipe based on the following ingredients: {request.ingredients}.
        IMPORTANT: Your entire response must be ONLY a single, valid JSON object. Do not include any text, backticks, or explanations.
        The JSON object must have these exact keys: "recipe_name", "description", "ingredients", "instructions".
        """
        response = model.generate_content(prompt)

        # The frontend expects a string to parse, so we send the raw text
        # We also include cleaning logic as a safeguard against markdown
        raw_content = response.text
        start_index = raw_content.find('{')
        end_index = raw_content.rfind('}')

        image_url = None

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

                # No image functionality

                return {"recipe": json.dumps(recipe_obj)}
            except Exception as parse_err:
                logging.error(f"Error parsing/cleaning recipe JSON: {parse_err}")
                return {"recipe": clean_json_str}
        else:
            # If no JSON is found, return the raw text for debugging
            return {"recipe": raw_content}

    except Exception as e:
        logging.error(f"An unexpected error occurred with the Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"An error with the Gemini API occurred: {str(e)}")