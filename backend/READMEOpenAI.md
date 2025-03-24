🌿 Branch Information
To run the OpenAI API, please use the test-akira branch.

📥 Setup Instructions
After cloning the repository, switch to the correct branch:
```bash
git checkout test-akira
```

Ensure you have Python and pip installed.
then you need to go to folder `./bash` and run : 
```bash
uv sync
```

Activate the Python virtual environment:
```bash
source .venv/bin/activate
```

Now, start the application using:
```bash
docker compose watch
```
🔧 Environment Configuration
Don't forget to set up your database credentials and OpenAI API key in the `.env` file.

if you want to make it changes with reload. you can use `command: sleep infinity` in file `docker-compose.override.yml` and in another terminal and do : 
```bash
docker compose exec backend bash
```
and run :
```bash
fastapi run --reload main/app.py
```

In case you don't have the table if `QueryLog`

🛠 Database Migration
There have been changes in the database schema. Before running the application, you must generate and apply migrations from app/models.py.

🔹 Steps to Apply Database Migrations
1️⃣ Enter the backend container (if using Docker Compose):

```bash
docker-compose exec backend bash
```
2️⃣ Navigate to the application directory (/app)

3️⃣ Run the migration commands:

```bash
alembic revision --autogenerate -m "Schema update"
```
```bash
alembic upgrade head
```
After completing these steps, a new table will be created in your local database.


📡 API Endpoint
Once everything is set up, the OpenAI API will be available at:
🔗 http://localhost:8000/api/v1/openai/query

📝 Example Payload (JSON Format) for POST
```bash
{
  "query": "где находится россия ?", 
  "context": "я студент хочу учться географию"
}
```
🔗 http://localhost:8000/api/v1/openai/history
📝 Example Payload (JSON Format)  for GET
```bash
{
    "id": "d2358acd-6cec-4f4b-bd96-faf3abd63aa2",
    "query": "who is president of Russia?",
    "response": "As of my last knowledge update in October 2023, the President of Russia is Vladimir Putin. Please verify with up-to-date sources to confirm if this information is still current.",
    "created_at": "2025-03-22T16:45:04.159944"
}
```

✅ Everything should work smoothly after setup! 🚀

For running the test please in folder `/app` use

```bash
pytest app/tests/api/routes/test_openai.py 
```
