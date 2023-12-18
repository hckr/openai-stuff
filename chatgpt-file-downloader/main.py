import os
import re
from pathlib import Path

import click
import requests
import undetected_chromedriver as uc

TOKEN = os.environ.get('TOKEN')

CONVERSATION_ENDPOINT = 'https://chat.openai.com/backend-api/conversation/{}'
FILE_DOWNLOAD_ENDPOINT = 'https://chat.openai.com/backend-api/files/{}/download'

# Using Selenium because Cloudflare bot detection doesn't work well with requests

options = uc.ChromeOptions()
options.add_argument("--disable-gpu")
driver = uc.Chrome(options=options)
driver.set_window_size(50, 50)
driver.minimize_window()
driver.get('https://chat.openai.com/')


def fetch_conversation_raw_json(conversation_id: str) -> str:
    script = """
    var callback = arguments[0];
    fetch('""" + CONVERSATION_ENDPOINT.format(conversation_id) + """', {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer """ + TOKEN + """',
        }
    })
    .then(response => response.text())
    .then(data => callback(data))
    .catch(error => callback({ error: error.message }));
    """

    # Execute the script
    data = driver.execute_async_script(script)

    return data


def get_file_ids_from_conversation(conversation_raw_json: str) -> list[str]:
    return re.findall(r'file-service://(file-[A-Za-z0-9]+)',
                      conversation_raw_json)


def download_file(file_id: str, out_dir: Path) -> Path:
    script = """
    var callback = arguments[0];
    fetch('""" + FILE_DOWNLOAD_ENDPOINT.format(file_id) + """', {
        method: 'GET',
        headers: {
            'Authorization': 'Bearer """ + TOKEN + """',
        }
    })
    .then(response => response.json())
    .then(data => callback(data))
    .catch(error => callback({ error: error.message }));
    """

    file_info = driver.execute_async_script(script)
    assert file_info['status'] == 'success'
    file_name = file_info['file_name']
    download_url = file_info['download_url']
    out_path = out_dir / file_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(download_url, stream=True) as r:
        r.raise_for_status()
        with open(out_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return out_path


@click.command()
@click.argument('conversation_id', type=str)
@click.argument(
    'out_dir',
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
def fetch_conversation(conversation_id: str, out_dir: Path):

    if not TOKEN:
        raise click.ClickException('Environment variable TOKEN is not set. '
                                   'Please set it to your OpenAI API token.')

    conversation_raw_json = fetch_conversation_raw_json(conversation_id)
    file_ids = get_file_ids_from_conversation(conversation_raw_json)
    for file_id in file_ids:
        path = download_file(file_id, out_dir)
        click.echo(f'Downloaded {file_id} into {path}')


if __name__ == '__main__':
    fetch_conversation()
