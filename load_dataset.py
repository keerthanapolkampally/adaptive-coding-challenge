import os
import json
from sqlalchemy import create_engine, MetaData, Table, insert

# Define paths
DATASET_PATH = "APPS"  # Adjust if APPS/ is not in the root folder
DB_URL = "postgresql://polkampallykeerthana:Montu#2799@localhost/adaptive_coding_challenge"

# Connect to the database
engine = create_engine(DB_URL)
metadata = MetaData()
metadata.reflect(bind=engine)

# Reflect tables from the database
challenges_table = metadata.tables['challenges']
test_cases_table = metadata.tables['test_cases']
solutions_table = metadata.tables['solutions']

def process_folder(folder_path):
    """Process a single folder containing question, solutions, and test cases."""
    try:
        # Extract content from files
        with open(os.path.join(folder_path, 'question.txt'), 'r') as q_file:
            question = q_file.read()

        with open(os.path.join(folder_path, 'input_output.json'), 'r') as io_file:
            test_cases_raw = json.load(io_file)

        # Transform test_cases to expected format
        test_cases = []
        inputs = test_cases_raw.get("inputs", [])
        outputs = test_cases_raw.get("outputs", [])
        if len(inputs) != len(outputs):
            print(f"Warning: Mismatched inputs and outputs in {folder_path}")
        for inp, out in zip(inputs, outputs):
            test_cases.append({"input": inp, "output": out})

        # Handle missing solutions.json gracefully
        solutions = []
        solutions_file_path = os.path.join(folder_path, 'solutions.json')
        if os.path.exists(solutions_file_path):
            with open(solutions_file_path, 'r') as sol_file:
                solutions = json.load(sol_file)
        else:
            print(f"Warning: Missing solutions.json in {folder_path}")

        with open(os.path.join(folder_path, 'metadata.json'), 'r') as meta_file:
            metadata = json.load(meta_file)

        return {
            "question": question,
            "test_cases": test_cases,
            "solutions": solutions,
            "metadata": metadata
        }
    except Exception as e:
        print(f"Error processing folder {folder_path}: {e}")
        return None

def load_data(dataset_path):
    """Load data from the dataset into the database."""
    for split in ['train', 'test']:  # Iterate over train and test folders
        split_path = os.path.join(dataset_path, split)
        for folder in os.listdir(split_path):
            folder_path = os.path.join(split_path, folder)
            if os.path.isdir(folder_path):
                print(f"Processing folder: {folder_path}")
                data = process_folder(folder_path)  # Process folder
                if data:
                    try:
                        title = data['question'].split("\n")[0][:255]  # Extract title
                        with engine.connect() as conn:
                            transaction = conn.begin()  # Start a transaction
                            try:
                                # Insert challenges
                                result = conn.execute(insert(challenges_table).values(
                                    title=title,
                                    description=data['question'],
                                    metadata=data['metadata'],
                                    folder_name=folder
                                ))
                                challenge_id = result.inserted_primary_key[0]

                                # Insert test cases
                                for case in data['test_cases']:
                                    if isinstance(case, dict) and 'input' in case and 'output' in case:
                                        try:
                                            conn.execute(insert(test_cases_table).values(
                                                challenge_id=challenge_id,
                                                input=json.dumps(case['input']),
                                                output=json.dumps(case['output'])
                                            ))
                                        except Exception as e:
                                            print(f"Error inserting test case: {case}. Error: {e}")
                                    else:
                                        print(f"Skipping invalid test case format in folder {folder}: {case}")

                                # Insert solutions
                                for solution in data['solutions']:
                                    conn.execute(insert(solutions_table).values(
                                        challenge_id=challenge_id,
                                        solution=solution
                                    ))

                                transaction.commit()  # Commit the transaction
                            except Exception as e:
                                transaction.rollback()  # Rollback on error
                                print(f"Error processing folder {folder}: {e}")
                    except Exception as e:
                        print(f"Error processing data for folder {folder_path}: {e}")
                else:
                    print(f"Skipping folder {folder}: Data could not be processed")

if __name__ == "__main__":
    load_data(DATASET_PATH)
