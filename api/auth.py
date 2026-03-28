import json
import hashlib
import uuid
from datetime import datetime

# In-memory user storage for testing
users_db = {}

def handler(event, context):
    try:
        # Parse request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '')
        body = event.get('body', '{}')
        
        if body and isinstance(body, str):
                try:
                        body_data = json.loads(body)
                except:
                        body_data = {}
        else:
                body_data = {}
        
        # Health check
        if path == '/api/health':
                return {
                        'statusCode': 200,
                        'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                        },
                        'body': json.dumps({'status': 'healthy'})
                }
        
        # Simple signup
        if http_method == 'POST' and path == '/api/auth/simple-signup':
                username = body_data.get('username')
                password = body_data.get('password')
                email = body_data.get('email')
                
                if not username or not password:
                        return {
                                'statusCode': 400,
                                'body': json.dumps({'detail': 'Username and password required'})
                        }
                
                if username in users_db:
                        return {
                                'statusCode': 400,
                                'body': json.dumps({'detail': 'Username already exists'})
                        }
                
                user_id = f"user_{uuid.uuid4().hex[:12]}"
                users_db[username] = {
                        'user_id': user_id,
                        'username': username,
                        'password_hash': hashlib.sha256(password.encode()).hexdigest(),
                        'email': email,
                        'created_at': datetime.now().isoformat()
                }
                
                return {
                        'statusCode': 200,
                        'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                        },
                        'body': json.dumps({'message': 'User created successfully', 'user_id': user_id})
                }
        
        # Simple login
        if http_method == 'POST' and path == '/api/auth/simple-login':
                username = body_data.get('username')
                password = body_data.get('password')
                
                if not username or not password:
                        return {
                                'statusCode': 401,
                                'body': json.dumps({'detail': 'Username and password required'})
                        }
                
                user = users_db.get(username)
                if not user or user['password_hash'] != hashlib.sha256(password.encode()).hexdigest():
                        return {
                                'statusCode': 401,
                                'body': json.dumps({'detail': 'Invalid username or password'})
                        }
                
                return {
                        'statusCode': 200,
                        'headers': {
                                'Content-Type': 'application/json',
                                'Access-Control-Allow-Origin': '*',
                        },
                        'body': json.dumps({
                                'user_id': user['user_id'],
                                'username': user['username'],
                                'email': user.get('email'),
                                'message': 'Login successful'
                        })
                }
        
        # Default response
        return {
                'statusCode': 404,
                'body': json.dumps({'detail': 'Endpoint not found'})
        }
        
    except Exception as e:
        return {
                'statusCode': 500,
                'body': json.dumps({'detail': f'Internal server error: {str(e)}'})
        }
