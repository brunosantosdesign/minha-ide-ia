from pathlib import Path
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do ficheiro .env
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Tenta ler a chave secreta do ambiente, ou usa uma padrão (NÃO FAÇA ISTO EM PRODUÇÃO)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-fallback-key-for-dev-CHANGE-ME')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True' # Lê do .env, padrão é True

ALLOWED_HOSTS = [] # Pode adicionar 'localhost', '127.0.0.1' se necessário


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Nossas apps
    'chat',
    # CORREÇÃO: Especificar o caminho completo para a app core
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', # CSRF é importante para segurança
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Diz ao Django para procurar templates dentro das apps
        'DIRS': [], # Não precisa de diretórios globais se os templates estiverem nas apps
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# A base de dados principal do Django continua a ser SQLite por simplicidade
# O MongoDB será acedido diretamente pelo PyMongo
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
     {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
# Informa ao Django onde encontrar os ficheiros estáticos globais na raiz do projeto
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configurações Específicas da Aplicação ---

# String de conexão do MongoDB lida do ficheiro .env
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'nostalgic_elbakyan') # Nome da DB usada no main.py original

