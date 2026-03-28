def handler(request):
    """
    Simple Vercel serverless function for health check
    """
    try:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': '{"status": "healthy", "message": "Simple auth API working"}'
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'{{"error": "{str(e)}"}}'
        }
