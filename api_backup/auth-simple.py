def handler(request):
    """
    Simple Vercel serverless function for auth
    """
    try:
        # Parse request data
        method = request.method
        url = request.url
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                },
                'body': ''
            }
        
        # Handle POST requests
        if method == 'POST':
            import json
            
            # Get request body
            if hasattr(request, 'body'):
                body = request.body
            else:
                # For Vercel, body might be in request.get_data()
                body_data = request.get_data()
                if body_data:
                    body = body_data.decode('utf-8')
                else:
                    body = '{}'
            
            try:
                data = json.loads(body) if body else {}
            except:
                data = {}
            
            # Simple login endpoint
            if '/api/auth/simple-login' in url:
                username = data.get('username')
                password = data.get('password')
                
                # Hardcoded test user for now
                if username == 'lorenzo_mongo' and password == 'test123':
                    return {
                        'statusCode': 200,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*',
                        },
                        'body': json.dumps({
                            'user_id': 'user_test_123',
                            'username': 'lorenzo_mongo',
                            'email': 'lorenzo@test.com',
                            'message': 'Login successful'
                        })
                    }
                else:
                    return {
                        'statusCode': 401,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*',
                        },
                        'body': json.dumps({'detail': 'Invalid username or password'})
                    }
            
            # Simple signup endpoint  
            if '/api/auth/simple-signup' in url:
                username = data.get('username')
                password = data.get('password')
                email = data.get('email')
                
                if not username or not password:
                    return {
                        'statusCode': 400,
                        'headers': {
                            'Content-Type': 'application/json',
                            'Access-Control-Allow-Origin': '*',
                        },
                        'body': json.dumps({'detail': 'Username and password required'})
                    }
                
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                    },
                    'body': json.dumps({
                        'message': 'User created successfully', 
                        'user_id': f'user_{username}_{hash(password)[:8]}'
                    })
                }
        
        # Default response
        return {
            'statusCode': 404,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'detail': 'Endpoint not found'})
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'detail': f'Internal server error: {str(e)}'})
        }
