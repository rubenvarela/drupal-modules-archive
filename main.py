import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import github #PyGithub
import os
from pathlib import Path


# Define files
files = [
    {'alias': 'xml-file', 'extension': 'xml', 'link': 'https://updates.drupal.org/release-history/project-list/all'},
    {'alias': 'tsv-file', 'extension': 'tsv', 'link': 'https://www.drupal.org/files/releases.tsv'},
]

# Load env, read ghtoken, load github
load_dotenv()
token = os.getenv('ghtoken')
g = github.Github(token)
repo = g.get_repo("rubenvarela/drupal-modules-archive")

# set request info
s = requests.session()
headers = s.headers
s.headers = {'User-Agent': 'rubenvarela project - https://github.com/rubenvarela/drupal-modules-archive'}

date = datetime.utcnow()
date = date.astimezone(timezone.utc)
date_format = '%Y-%m-%d %H.%M.%S %Z%z'

debug = os.getenv('DEBUG')

# Per file, load it and save it to repo
for file in files:
    data = s.get(file['link'])
    data = data.content.decode()
    path = f"data/{file['alias']}/{date.year}/{date.month}/{date.day}/{date.strftime(date_format)}.{file['extension']}"

    repo.create_file(
        path,
        message=f"New export created {date.strftime(date_format)} - {file['alias']}",
        content=data,
        branch="main"
    )

    if debug:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as fd:
            fd.write(data)
