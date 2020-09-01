"""
Django settings for greeklink_core project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
import environ

env = environ.Env()
environ.Env.read_env()

ENV = os.environ['ENV']

SITE_ID = 1

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
if ENV == 'testing':
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'greeklink-core-env.eba-7mntraig.us-west-2.elasticbeanstalk.com', 'test.localhost']


# Application definition
SHARED_APPS = (
    'tenant_schemas',
    'organizations',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'django.contrib.sessions',
)

TENANT_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.admin',
    'core',
    'rush',
    'cal',
)

INSTALLED_APPS = [
    'tenant_schemas',
    'organizations.apps.OrganizationsConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'crispy_forms',
    'django_user_agents',
    'storages',
    'core.apps.CoreConfig',
    'rush.apps.RushConfig',
    'cal.apps.CalConfig',
]

TENANT_MODEL = 'organizations.Client'

MIDDLEWARE = [
    'tenant_schemas.middleware.TenantMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
]

ROOT_URLCONF = 'greeklink_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            'core/templates',
            'rush/templates',
        ],
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

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

WSGI_APPLICATION = 'greeklink_core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# aws postgres database in production with multitenant support
if 'RDS_DB_NAME' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'tenant_schemas.postgresql_backend',
            'NAME': os.environ['RDS_DB_NAME'],
            'USER': os.environ['RDS_USERNAME'],
            'PASSWORD': os.environ['RDS_PASSWORD'],
            'HOST': os.environ['RDS_HOSTNAME'],
            'PORT': os.environ['RDS_PORT'],
        }
    }
# django-native sqlite database in local development    
else:
    DATABASES = {
        'default': {
            'ENGINE': 'tenant_schemas.postgresql_backend',
            'NAME': 'greeklinkdb',
            'USER': 'greeklinkuser',
            'PASSWORD': 'greeklink1',
            'HOST': 'localhost',
            'PORT': '',
        }
    }

DATABASE_ROUTERS = (
    'tenant_schemas.routers.TenantSyncRouter',
)

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True




# for @login_required tag
LOGIN_URL = '/login'

# if next isn't provided, login redirects to index
LOGIN_REDIRECT_URL = '/'

# email settings
EMAIL_USE_TLS = True
EMAIL_PORT = 587

if ENV == 'testing':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    VERIFY_EMAIL_USER = os.environ['VERIFY_EMAIL']
    EMAIL_HOST_PASSWORD = os.environ['VERIFY_PASSWORD']

    #other email accounts
    ANN_EMAIL = os.environ['ANN_EMAIL']
    ANN_PASSWORD = os.environ['ANN_PASSWORD']

    SUPPORT_EMAIL_USER = os.environ['SUPPORT_EMAIL']
    SUPPORT_EMAIL_PASSWORD = os.environ['SUPPORT_PASSWORD']


# AWS SES access
else:
    EMAIL_BACKEND = 'django_ses.SESBackend'
    AWS_SES_AUTOTHROTTLE = 0.75
    VERIFY_EMAIL_USER = os.environ['VERIFY_EMAIL']
    SUPPORT_EMAIL_USER = os.environ['SUPPORT_EMAIL']
    ANN_EMAIL = os.environ['ANN_EMAIL']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

if ENV == 'testing':
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    # DEFAULT_FILE_STORAGE = 'tenant_schemas.storage.TenantFileSystemStorage'   <-- should probably be set but haven't gotten it to work yet

# AWS S3 for media upload hosting
else:
    AWS_STORAGE_BUCKET_NAME = os.environ['AWS_STORAGE_BUCKET_NAME']
    AWS_S3_REGION_NAME = os.environ['AWS_S3_REGION_NAME']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    
