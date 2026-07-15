import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
import github #PyGithub
import os
import time
from pathlib import Path

RETRYABLE_403_MESSAGES = ('Timed out validating rule',)


def create_file_with_retry(repo, path, message, content, branch, attempts=4, backoff_seconds=10):
    for attempt in range(1, attempts + 1):
        try:
            repo.create_file(path, message=message, content=content, branch=branch)
            return
        except github.GithubException as e:
            data_message = (e.data or {}).get('message', '') if isinstance(e.data, dict) else ''
            is_retryable = e.status == 403 and any(m in data_message for m in RETRYABLE_403_MESSAGES)
            if not is_retryable or attempt == attempts:
                raise
            print(f"Retryable error creating {path} (attempt {attempt}/{attempts}): {data_message}")
            time.sleep(backoff_seconds * attempt)


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

    create_file_with_retry(
        repo,
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
