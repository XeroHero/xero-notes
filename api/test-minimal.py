def handler(request):
    """
    Minimal test function for Vercel debugging
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': '{"message": "Vercel serverless function is working!", "timestamp": "' + str(__import__('datetime').datetime.now().isoformat()) + '"}'
    }
