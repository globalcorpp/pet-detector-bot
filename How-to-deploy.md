python-telegram-bot==21.10

python3 -m venv .venv
source .venv/bin/activate
pip install python-telegram-bot python-dotenv
pip install aiohttp
pip freeze > requirements.txt

pip install -r requirements.txt

I used render.com


python3.11 -m venv pet_env
source pet_env/bin/activate

pip install "numpy<2"

uvicorn bot-api:app --host 0.0.0.0 --port 8080 --reload

python bot-plus.py
