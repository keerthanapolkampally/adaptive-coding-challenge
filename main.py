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
from sqlalchemy import create_engine, MetaData, Table, Text, Column, Integer, String, ForeignKey, Float, TIMESTAMP
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
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import text
from sqlalchemy.engine import Row
from sqlalchemy.ext.declarative import declarative_base
import time

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

from sqlalchemy import Table, Column, Integer, String, MetaData

challenges_table = Table(
    "challenges", metadata,
    Column("id", Integer, primary_key=True),
    Column("description", Text, nullable=False),
    Column("embedding", ARRAY(Float)),  # Assuming PostgreSQL ARRAY for embeddings
)
metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
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
    challenge_id: str
    solution: str
    language: str
    is_llm_generated: bool = False  # Default to False

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class SelectChallengeRequest(BaseModel):
    challenge_id: str

@app.on_event("startup")
async def startup_event():
    from fastapi.routing import APIRoute
    print("Registered Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"Path: {route.path}, Methods: {route.methods}")

latest_challenge_id: Optional[str] = None  # Global variable to track latest generated challenge ID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
import openai

router = APIRouter()

@app.post("/api/generate-challenge")
async def generate_challenge(
    request: ChallengeRequest,
    db: Session = Depends(get_db),
    Authorize: AuthJWT = Depends(),
):
    try:
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()  # Get the user ID from JWT token

        # Generate challenge via LLM
        topic = request.topic or "general"
        difficulty = request.difficulty or "medium"
        prompt = f"""
        Create a coding challenge with the following specifications:
        - **Topic**: {topic}
        - **Difficulty**: {difficulty}
        Provide the challenge in this format:
        - Title:
        - Description:
        - Examples:
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a coding challenge generator."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
        )

        generated_challenge = response['choices'][0]['message']['content'].strip()

        if not generated_challenge:
            raise HTTPException(status_code=500, detail="Failed to generate challenge")

        # Extract the title from the challenge
        title_line = next((line for line in generated_challenge.splitlines() if line.startswith("- **Title**:")), None)
        title = title_line.replace("- **Title**:", "").strip() if title_line else "Untitled Challenge"

        # Save the challenge in the `challenges` table
        new_challenge_id = str(uuid4())
        db.execute(
            text("""
                INSERT INTO challenges (id, title, description, topic, difficulty)
                VALUES (:id, :title, :description, :topic, :difficulty)
            """),
            {
                "id": new_challenge_id,
                "title": title,
                "description": generated_challenge,
                "topic": topic,
                "difficulty": difficulty,
            },
        )

        # Associate the challenge with the user in `solved_challenges`
        db.execute(
            text("""
                INSERT INTO solved_challenges (id, user_id, challenge_id, status, submitted_at)
                VALUES (:id, :user_id, :challenge_id, 'Generated', NOW())
            """),
            {
                "id": str(uuid4()),
                "user_id": user_id,
                "challenge_id": new_challenge_id,
            },
        )

        db.commit()

        return {"id": new_challenge_id, "title": title, "description": generated_challenge}

    except Exception as e:
        print(f"Error generating challenge: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate challenge")

@app.post("/api/enrich-challenge-metadata")
async def enrich_challenge_metadata(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        Authorize.jwt_required()

        # Fetch challenges with missing metadata
        challenges_to_enrich = db.execute(
            text("SELECT id, title, description FROM challenges WHERE topic IS NULL OR difficulty IS NULL")
        ).fetchall()

        enriched_challenges = []
        for challenge in challenges_to_enrich:
            # Prepare prompt for LLM
            prompt = f"""
You are an assistant who categorizes programming challenges.
Here is a challenge description:
Title: {challenge['title']}
Description: {challenge['description']}

Determine the following:
1. Topic of the challenge (e.g., Arrays, Graphs, DP, etc.)
2. Difficulty level (Easy, Medium, Hard)
Provide the output in JSON format with keys 'topic' and 'difficulty'.
            """

            # Call OpenAI Chat API
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a challenge metadata assistant."},
                    {"role": "user", "content": prompt},
                ],
            )

            # Parse LLM response
            metadata = eval(response['choices'][0]['message']['content'])
            topic = metadata.get("topic")
            difficulty = metadata.get("difficulty")

            if topic and difficulty:
                # Update the database
                db.execute(
                    text("UPDATE challenges SET topic = :topic, difficulty = :difficulty WHERE id = :id"),
                    {"topic": topic, "difficulty": difficulty, "id": challenge['id']},
                )
                enriched_challenges.append(
                    {"id": challenge['id'], "topic": topic, "difficulty": difficulty}
                )

        db.commit()

        return {"message": "Metadata enrichment complete", "enriched_challenges": enriched_challenges}
    except Exception as e:
        print(f"Error enriching metadata: {e}")
        raise HTTPException(status_code=500, detail="Failed to enrich metadata")

@app.post("/api/submit-solution")
async def submit_solution(
    request: SolutionSubmission,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    try:
        # Ensure user is authenticated
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()

        # Retrieve the challenge description and validate challenge association
        challenge = db.execute(
            text("""
                SELECT c.description
                FROM solved_challenges sc
                JOIN challenges c ON sc.challenge_id = c.id
                WHERE sc.challenge_id = :challenge_id AND sc.user_id = :user_id
            """),
            {"challenge_id": request.challenge_id, "user_id": user_id},
        ).fetchone()

        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found or not associated with this user.")

        challenge_description = challenge[0]

        # Validate the solution using the LLM
        prompt = f"""
Here is the challenge:
{challenge_description}

Here is the user's solution in {request.language}:
{request.solution}

Does this solution solve the challenge correctly? Provide feedback.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a solution validator for coding challenges."},
                {"role": "user", "content": prompt},
            ],
        )
        feedback = response['choices'][0]['message']['content'].strip()

        # Determine the status based on feedback
        status = "Solved" if "correct" in feedback.lower() else "Failed"

        # Update or insert the solution submission into `solved_challenges`
        db.execute(
            text("""
                UPDATE solved_challenges
                SET language = :language, status = :status, submitted_at = NOW()
                WHERE challenge_id = :challenge_id AND user_id = :user_id
            """),
            {
                "language": request.language,
                "status": status,
                "challenge_id": request.challenge_id,
                "user_id": user_id,
            },
        )
        db.commit()

        return {"feedback": feedback, "status": status}

    except Exception as e:
        print(f"Error submitting solution: {e}")
        raise HTTPException(status_code=500, detail="Error submitting solution.")

from sqlalchemy.sql import text
import numpy as np
from fastapi import HTTPException

import json

@app.get("/api/recommend-challenges")
async def recommend_challenges(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    try:
        start_time = time.time()
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()
        # Fetch solved challenges
        solved_challenges_data = db.execute(
            text("SELECT challenge_id FROM solved_challenges WHERE user_id = :user_id"),
            {"user_id": user_id},
        ).fetchall()
        
        if solved_challenges_data:
            solved_ids = [row[0] for row in solved_challenges_data]
            solved_descriptions = db.execute(
                text("SELECT description FROM challenges WHERE id = ANY(:ids)"),
                {"ids": list(solved_ids)},  # Use list to avoid tuple-related issues
            ).fetchall()
            solved_descriptions = [row[0] for row in solved_descriptions]

            # Prepare prompt for LLM
            prompt = f"""
            You are a coding challenge recommendation assistant.

            The user has solved the following challenges:
            Descriptions: {', '.join(solved_descriptions[:5])}

            Recommend 3 new unsolved coding challenges similar to the descriptions that user has solved for the user to learn. Provide the recommendations in the following JSON format:
            [
                {{
                    "id": str(uuid.uuid4()),
                    "title": "Challenge Title",
                    "description": "Challenge Description",
                    "examples": ["Example 1", "Example 2"],
                    "topic": "Topic",
                    "difficulty": "Easy/Medium/Hard",
                    "why_recommended": "Reason"
                }}
            ]
            Ensure the output is valid JSON and uses double quotes for all keys and string values. Make sure the formatting of JSON is correct. 
            Also, do not have anything unfinished. Please make sure everything is in place and in correct format. Please do not have any unterminated strings. 
            Let the examples be simple if it is taking up more time or processing. Let the description of the challenge be as clear as possible and also examples should be like input, output.
            """
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a coding challenge recommendation assistant."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
            )
            print(f"Raw LLM response: {response['choices'][0]['message']['content']}")
            try:
                recommendations = json.loads(response['choices'][0]['message']['content'])
            except json.JSONDecodeError as e:
                print(f"Error parsing LLM response: {e}")
                raise HTTPException(status_code=500, detail="Failed to parse LLM response")
        else:
            # Fallback if no solved challenges
            recommendations = db.execute(
                text("SELECT id, description FROM challenges LIMIT 5")
            ).fetchall()
            recommendations = [
                {
                    "id": str(uuid.uuid4()),
                    "title": f"Challenge {row[0]}",
                    "description": row[1],
                    "examples": [],
                    "topic": "General",
                    "difficulty": "Medium",
                    "why_recommended": "Fallback recommendation.",
                }
                for row in recommendations
            ]
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        print(f"Time taken for recommended challenges: {elapsed_time:.2f} seconds")  # Debugging
        return {"recommendations": recommendations}

    except Exception as e:
        print(f"Error during recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")
from uuid import UUID

@app.post("/api/select-recommended-challenge")
async def select_recommended_challenge(
    request: SelectChallengeRequest,
    Authorize: AuthJWT = Depends(),
    db: Session = Depends(get_db),
):
    try:
        Authorize.jwt_required()
        user_id = Authorize.get_jwt_subject()

        # Check if the challenge exists in the `challenges` table
        result = db.execute(
            text("SELECT id FROM challenges WHERE id = :id"),
            {"id": request.challenge_id},
        ).fetchone()

        if not result:
            # If the challenge doesn't exist, create a placeholder entry in `challenges`
            db.execute(
                text("""
                    INSERT INTO challenges (id, title, description, topic, difficulty)
                    VALUES (:id, 'Recommended Challenge', 'Description unavailable', 'General', 'Medium')
                """),
                {"id": request.challenge_id},
            )
            db.commit()

        # Check if the challenge is already associated with the user
        existing_association = db.execute(
            text("""
                SELECT id FROM solved_challenges
                WHERE challenge_id = :challenge_id AND user_id = :user_id
            """),
            {"challenge_id": request.challenge_id, "user_id": user_id},
        ).fetchone()

        if not existing_association:
            # Associate the challenge with the user
            db.execute(
                text("""
                    INSERT INTO solved_challenges (id, user_id, challenge_id, status, submitted_at)
                    VALUES (:id, :user_id, :challenge_id, 'Selected', NOW())
                """),
                {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "challenge_id": request.challenge_id,
                },
            )
            db.commit()

        # Fetch the challenge details to return to the frontend
        challenge_details = db.execute(
            text("""
                SELECT id, title, description, topic, difficulty
                FROM challenges WHERE id = :id
            """),
            {"id": request.challenge_id},
        ).fetchone()

        return {
            "message": "Challenge selected successfully.",
            "challenge": {
                "id": challenge_details[0],
                "title": challenge_details[1],
                "description": challenge_details[2],
                "topic": challenge_details[3],
                "difficulty": challenge_details[4],
            },
        }

    except Exception as e:
        print(f"Error in select_recommended_challenge: {e}")
        raise HTTPException(status_code=500, detail="Failed to select challenge")

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
