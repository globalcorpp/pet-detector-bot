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
