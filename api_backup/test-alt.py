import json

def handler(event, context):
    """
    Alternative Vercel serverless function format
    """
    try:
        # Log the event and context for debugging
        print(f"Event: {event}")
        print(f"Context: {context}")
        
        # Return a simple response
        response = {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'message': 'Alternative Vercel function working!',
                'event_type': type(event).__name__,
                'context_keys': list(context.keys()) if context else [],
                'timestamp': '2025-03-30T21:08:00Z'
            })
        }
        
        return response
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({'error': str(e)})
        }
