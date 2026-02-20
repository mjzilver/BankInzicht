setlocal

git fetch
git pull

IF NOT EXIST venv (
    python -m venv venv
)
call venv\Scripts\activate

pip install .

python src\app.py
