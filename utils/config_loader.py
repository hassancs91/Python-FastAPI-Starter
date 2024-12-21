from dotenv import load_dotenv
import os


# Load environment variables from .env file at the start of the application
load_dotenv(override=True)

#configuration
ENVIRONMENT=os.getenv("ENVIRONMENT")



#API Security
API_KEY_HEADER_NAME = os.getenv("API_KEY_HEADER_NAME")
API_KEY_PASSPHRASE = os.getenv("API_KEY_PASSPHRASE")

#OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


#Database Connections
MONGO_CONNECTION_STRING = os.getenv("MONGO_CONNECTION_STRING")
MYSQL_CONNECTION_STRING = os.getenv("MYSQL_CONNECTION_STRING")






