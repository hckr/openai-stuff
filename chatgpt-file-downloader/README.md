# chatgpt-file-downloader

Simple script which wasn't that quick to write, because ChatGPT API is behind Cloudflare :neutral_face: That's why I had to use `undetected_chromedriver` (Selenium).

It solves the problem I had, which is to easily download all the images from the ChatGPT conversation. The script fetches all files, not only images.

## Installation

```bash
poetry install
```

## Usage

```bash
poetry run python main.py [CHATGPT_CONVERSATION_ID] [DOWNLOAD_DIR]
```
