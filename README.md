PASOS PARA DESCARGAR

1️⃣ Clonar el repositorio

Tener Git instalado. Luego abre la terminal y ejecuta:

git clone https://github.com/jowi74/Homie.git
cd Homie

2️⃣ Crear un entorno virtual

python -m venv venv

Luego activar el entorno:

Windows (PowerShell):

.\venv\Scripts\Activate.ps1

Windows (CMD):

.\venv\Scripts\activate.bat

3️⃣ Instalar dependencias

pip install -r requirements.txt

5️⃣ Migraciones

python manage.py makemigrations
python manage.py migrate

6️⃣ Crear superusuario (opcional para ver el /admin)

Para poder entrar al admin:

python manage.py createsuperuser

7️⃣ Runear el archivo

Python manage.py runserver