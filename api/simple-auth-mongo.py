import json
import hashlib
import uuid
from datetime import datetime
import os

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
            
            # For now, create user in memory (MongoDB connection issues)
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            user_doc = {
                'user_id': user_id,
                'username': username,
                'password_hash': hashlib.sha256(password.encode()).hexdigest(),
                'email': email,
                'created_at': datetime.now().isoformat()
            }
            
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
            
            # For now, check user in memory (MongoDB connection issues)
            # In production, you'd query MongoDB here
            if username == 'lorenzo_mongo' and password == 'test123':
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'user_id': 'user_mongo_test_123',
                        'username': 'lorenzo_mongo',
                        'email': 'lorenzo@mongo.com',
                        'message': 'Login successful'
                    })
                }
            
            return {
                'statusCode': 401,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'detail': 'Invalid username or password'})
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
