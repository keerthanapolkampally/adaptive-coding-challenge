# Adaptive Coding Challenge

https://drive.google.com/file/d/1o_Da4bwaVOkRkt2CtWT8qWCL5X_T-J7R/view?usp=drive_link

Adaptive Coding Challenge is a platform for generating, solving, and validating coding challenges. It leverages OpenAI APIs for solution validation and provides recommendations for new challenges based on user activity.

---

## Features
- **Challenge Generator**: Create customized coding challenges based on topic and difficulty.
- **Solution Submission**: Submit solutions and get instant feedback.
- **Challenge Recommendations**: Get recommended challenges based on solved ones.
- **Validation**: Uses OpenAI APIs to validate solutions.

---

## Prerequisites

Before running the project, ensure you have the following installed:
- Python 3.8 or higher
- Node.js 14 or higher
- PostgreSQL 12 or higher
- Git
- OpenAI API key

---

## Installation

### **1. Clone the Repository**
```bash
git clone https://github.com/keerthanapolkampally/adaptive-coding-challenge.git
cd adaptive-coding-challenge

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

Create a .env file in the root directory:

OPENAI_API_KEY=<your-openai-api-key>
DATABASE_URL=postgresql://<username>:<password>@localhost/<database_name>
AUTHJWT_SECRET_KEY=<your-secret-key>

psql -U <username> -d <database_name> -f create_tables.sql

cd coding-challenge-ui
npm install
npm start
npm run build

uvicorn main:app --reload
