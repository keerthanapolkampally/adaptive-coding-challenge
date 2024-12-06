from openai.embeddings_utils import get_embedding
from sqlalchemy import update
from main import SessionLocal, challenges_table
from sqlalchemy.sql import text


def generate_embeddings():
    with SessionLocal() as db:
        challenges = db.execute(text("SELECT id, description FROM challenges")).mappings().all()
        for challenge in challenges:
            try:
                print(f"Generating embedding for Challenge ID: {challenge['id']}")
                embedding = get_embedding(challenge["description"], engine="text-embedding-ada-002")

                # Update the table with the generated embedding
                db.execute(
                    update(challenges_table)
                    .where(challenges_table.c.id == challenge["id"])
                    .values(embedding=embedding)
                )
                db.commit()
            except Exception as e:
                print(f"Error generating embedding for Challenge ID: {challenge['id']}. Error: {e}")


if __name__ == "__main__":
    generate_embeddings()

