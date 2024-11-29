import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from fastapi import Depends
from passlib.context import CryptContext
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseSettings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
class Settings(BaseSettings):
    authjwt_secret_key: str = os.getenv("AUTHJWT_SECRET_KEY", "fallback_secret_key")  

@AuthJWT.load_config
def get_config():
    return Settings()
# Load environment variables
load_dotenv()
latest_challenge: Optional[str] = None
# Initialize FastAPI app
app = FastAPI()
DATABASE_URL = "postgresql://postgres:Montu#2799@localhost/adaptive_coding_challenge"

engine = create_engine(DATABASE_URL)
metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("email", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("created_at", TIMESTAMP, server_default=func.now())
)

solved_challenges = Table(
    "solved_challenges", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
    Column("challenge_id", String, server_default=func.uuid_generate_v4()),
    Column("topic", String),
    Column("difficulty", String),
    Column("language", String),
    Column("status", String),
    Column("submitted_at", TIMESTAMP, server_default=func.now())
)

metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    print("Error: OPENAI_API_KEY is not set.")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# Define models
class ChallengeRequest(BaseModel):
    topic: str
    difficulty: str

class SolutionSubmission(BaseModel):
    solution: str
    language: str 

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

@app.on_event("startup")
async def startup_event():
    from fastapi.routing import APIRoute
    print("Registered Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"Path: {route.path}, Methods: {route.methods}")

# Endpoint to generate a coding challenge
@app.post("/api/generate-challenge")
async def generate_challenge(request: ChallengeRequest):
    global latest_challenge  # Reference the global variable
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a coding challenge generator."},
                {"role": "user", "content": f"Generate a {request.difficulty} coding challenge about {request.topic}."}
            ]
        )
        challenge = response['choices'][0]['message']['content'].strip()
        latest_challenge = challenge  # Store the latest challenge
        return {"challenge": challenge}
    except Exception as e:
        print(f"Detailed Error: {e}")
        raise HTTPException(status_code=500, detail="Error generating challenge.")

@app.post("/api/submit-solution")
async def submit_solution(request: SolutionSubmission):
    global latest_challenge  # Reference the global variable
    if not latest_challenge:
        raise HTTPException(status_code=400, detail="No challenge has been generated yet.")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are a solution validator for {request.language} code."},
                {"role": "user", "content": f"Here is the challenge:\n{latest_challenge}\n\nHere is the user's solution in {request.language}:\n{request.solution}\n\nDoes this solution solve the challenge correctly? Provide feedback."}
            ]
        )
        feedback = response['choices'][0]['message']['content'].strip()
        return {"feedback": feedback}
    except openai.error.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        raise HTTPException(status_code=500, detail="OpenAI API Error")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected Error: {e}")

@app.post("/api/register")
async def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(request.password)
    db.execute(users.insert().values(
        username=request.username,
        email=request.email,
        password_hash=hashed_password
    ))
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/api/login")
async def login_user(request: LoginRequest, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = db.execute(users.select().where(users.c.username == request.username)).fetchone()
    if not user or not pwd_context.verify(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = Authorize.create_access_token(subject=str(user.id))
    return {"access_token": access_token}

# Serve React app for non-API routes
# @app.get("/{full_path:path}")
# async def serve_react_app(full_path: str):
#     if full_path.startswith("api/"):
#         raise HTTPException(status_code=404, detail="API route not found.")
    
#     file_path = Path(__file__).parent / "coding-challenge-ui/build" / "index.html"
#     if file_path.exists():
#         return FileResponse(file_path)
#     raise HTTPException(status_code=404, detail="React app not found.")

@app.get("/")
async def root():
    file_path = Path(__file__).parent / "coding-challenge-ui/build/index.html"
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="React build file not found")

# Serve React static files
app.mount(
    "/",
    StaticFiles(directory=Path(__file__).parent / "coding-challenge-ui/build", html=True),
    name="static",
)

# Healthcheck endpoint
@app.get("/api/healthcheck")
async def healthcheck():
    return {"status": "ok"}
