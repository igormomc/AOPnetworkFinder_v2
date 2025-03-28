import os

from flask import Flask
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__, template_folder='templates')

# Set the secret key for CSRF protection and session management
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
app.config['TESTING'] = False
app.config['CACHE_TYPE'] = 'SimpleCache'

#Initialize cache
cache = Cache(app)

#THIS CATCH SHOULD BE MOVED, ITS HERE BECOUSE OF CIRCULAR IMPORTS
from app.service.convertExcelToJsonAc50 import get_excel_data
get_excel_data()

# Initialize CSRF protection
csrf = CSRFProtect(app)

from app import route
