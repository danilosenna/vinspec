@echo off
echo Ativando ambiente virtual...
call venv310\Scripts\activate

echo Instalando dependências...
pip install -r requirements.txt

echo Migrações do banco de dados...
python manage.py makemigrations
python manage.py migrate

echo.
echo ✅ Instalação concluída com sucesso!
pause
