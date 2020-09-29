import os

path = os.path.dirname(__file__)
BASE_DIR = os.path.normpath(os.path.dirname(__file__))

templates = os.path.join(BASE_DIR, 'templates/home.html')

# print(path)

# print(BASE_DIR)

# print(templates)

with open(templates) as html:
    for line in html:
        print(line)