import os
import sys
from django.conf import settings

BASE_DIR = os.path.dirname(__file__)
# BASE_DIR = os.path.normpath(os.path.dirname(__file__))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'sitebuilder/templates')],
    }
]

settings.configure(
    DEBUG = True,
    SECRET_KEY = 'b0mqvak1p2sqm6p#+8o8fyxf+ox(le)8&jh_5^sxa!=7!+wxj0',
    ROOT_URLCONF = 'sitebuilder.urls',
    MIDDLEWARE_CLASSES = (),
    INSTALLED_APPS = (
        'django.contrib.staticfiles',
        # 'django.contrib.webdesign', # This is deprecated for < Django 3.x 
        'sitebuilder',
        'compressor', # Compressor for static files
    ),
    STATIC_URL = '/static/',
    SITE_PAGES_DIRECTORY = os.path.join(BASE_DIR, 'pages'),
    SITE_OUTPUT_DIRECTORY = os.path.join(BASE_DIR, '_build'),
    STATIC_ROOT = os.path.join(BASE_DIR, '_build', 'static'),
    TEMPLATES = TEMPLATES,
        # This field makes hash name for each static file in the _build/static folder
    # STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.CachedStaticFilesStorage', 
    STATIC_FINDERS = (
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        'compressor.finders.CompressorFinder' # 
    )
)

if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)