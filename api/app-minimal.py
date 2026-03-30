from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Xero Notes API running", "version": "1.0.0"}

@app.get("/api/health")
def health():
    return {"status": "healthy", "message": "FastAPI working on Vercel!"}

@app.post("/api/auth/simple-login")
async def simple_login(request):
    try:
        data = await request.json()
        username = data.get('username')
        password = data.get('password')
        
        if username == 'lorenzo_mongo' and password == 'test123':
            return {
                "user_id": "user_test_123",
                "username": "lorenzo_mongo",
                "email": "lorenzo@test.com",
                "message": "Login successful"
            }
        else:
            return {"detail": "Invalid username or password"}
    except:
        return {"detail": "Internal server error"}

handler = app
