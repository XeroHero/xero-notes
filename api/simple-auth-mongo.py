import json
import hashlib
import uuid
from datetime import datetime
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def handler(request):
    """
    Simple Vercel serverless function for auth with MongoDB Atlas
    """
    try:
        # Parse request
        method = request.method
        url = request.url
        body = request.body
        
        if body and isinstance(body, str):
            try:
                body_data = json.loads(body)
            except:
                body_data = {}
        else:
            body_data = {}
        
        # Simple signup
        if method == 'POST' and '/api/auth/simple-signup' in url:
            username = body_data.get('username')
            password = body_data.get('password')
            email = body_data.get('email')
            
            if not username or not password:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'detail': 'Username and password required'})
                }
            
            # Check if user already exists in MongoDB
            existing_user = await db.simple_users.find_one({'username': username})
            if existing_user:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'detail': 'Username already exists'})
                }
            
            # Create new user in MongoDB
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user_doc = {
                'user_id': user_id,
                'username': username,
                'password_hash': hashlib.sha256(password.encode()).hexdigest(),
                'email': email,
                'created_at': datetime.now().isoformat()
            }
            await db.simple_users.insert_one(user_doc)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'message': 'User created successfully', 'user_id': user_id})
            }
        
        # Simple login
        if method == 'POST' and '/api/auth/simple-login' in url:
            username = body_data.get('username')
            password = body_data.get('password')
            
            if not username or not password:
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'detail': 'Username and password required'})
                }
            
            # Find user in MongoDB
            user = await db.simple_users.find_one({'username': username})
            if not user or user['password_hash'] != hashlib.sha256(password.encode()).hexdigest():
                return {
                    'statusCode': 401,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'detail': 'Invalid username or password'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'email': user.get('email'),
                    'message': 'Login successful'
                })
            }
        
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'detail': 'Endpoint not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'detail': f'Internal server error: {str(e)}'})
        }
