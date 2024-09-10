# this gets a list of available models from teh OpenAI Endpoint

import os
from openai import OpenAI
from dotenv import load_dotenv

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the .env file
env_path = os.path.join(script_dir, '.env')

# Load environment variables from the specified path
load_dotenv(env_path)

# Set up OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    organization=os.getenv("OPENAI_ORG_ID")
)

def list_available_models():
    models = client.models.list()
    for model in models:
        print(f"ID: {model.id}")
        print(f"Created: {model.created}")
        print(f"Owned By: {model.owned_by}")
        print("---")

if __name__ == "__main__":
    list_available_models()
