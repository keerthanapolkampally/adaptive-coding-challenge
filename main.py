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
from uuid import uuid4
from datetime import timedelta 

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
        latest_challenge = {
            "challenge": challenge,
            "topic": request.topic,
            "difficulty": request.difficulty
        }
        return {"challenge": challenge}
    except Exception as e:
        print(f"Detailed Error: {e}")
        raise HTTPException(status_code=500, detail="Error generating challenge.")

@app.post("/api/submit-solution")
async def submit_solution(
    request: SolutionSubmission, 
    Authorize: AuthJWT = Depends(), 
    db: Session = Depends(get_db)
):
    global latest_challenge

    # Validate that a challenge exists
    if not latest_challenge:
        raise HTTPException(status_code=400, detail="No challenge has been generated yet.")

    try:
        # Ensure user is authenticated
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()
        topic = latest_challenge.get("topic", "unknown")
        difficulty = latest_challenge.get("difficulty", "unknown")
        # Process the OpenAI validation
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"You are a solution validator for {request.language} code."},
                {"role": "user", "content": f"Here is the challenge:\n{latest_challenge}\n\nHere is the user's solution in {request.language}:\n{request.solution}\n\nDoes this solution solve the challenge correctly? Provide feedback."}
            ]
        )
        feedback = response['choices'][0]['message']['content'].strip()

        # Determine status
        status = "Solved" if "correct" in feedback.lower() else "Failed"

        # Store the result in the database
        db.execute(solved_challenges.insert().values(
            user_id=user_id,  # Use user_id from JWT token
            challenge_id=str(uuid4()),
            topic=topic,  # Replace with actual topic
            difficulty=difficulty,  # Replace with actual difficulty
            language=request.language,
            status=status,
            submitted_at=func.now(),
        ))
        db.commit()

        return {"feedback": feedback}
    except Exception as e:
        import traceback
        print(f"Unexpected Error: {e}")
        print(traceback.format_exc())
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
    expires = timedelta(hours=2)  # Adjust the expiration time as needed
    access_token = Authorize.create_access_token(subject=str(user.id), expires_time=expires)
    return {"access_token": access_token}    

@app.get("/api/user-history")
async def get_user_history(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        # Ensure the user is authenticated
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()
        
        # Fetch the user's challenge history
        result = db.execute(solved_challenges.select().where(solved_challenges.c.user_id == user_id)).fetchall()
        history = [
            {
                "challenge_id": row.challenge_id,
                "topic": row.topic,
                "difficulty": row.difficulty,
                "language": row.language,
                "status": row.status,
                "submitted_at": row.submitted_at,
            }
            for row in result
        ]
        return {"history": history}
    except Exception as e:
        print(f"Error fetching user history: {e}")
        raise HTTPException(status_code=500, detail="Unable to fetch user history")


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
