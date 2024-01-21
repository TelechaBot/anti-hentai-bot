# Lolicon correction

![Ruff](https://github.com/TelechaBot/anime-tag-bot/actions/workflows/ruff.yml/badge.svg)

> [!IMPORTANT]
> Deploy With [wd14-tagger-server](https://github.com/LlmKira/wd14-tagger-server)

## Project Description

Identify child pornography and Ban them on Telegram Group.

## Usage

```shell
git clone https://github.com/TelechaBot/anti-hentai-bot
cd anti-hentai-bot
cp .env.exp .env
nano .env
```

```shell
pip install pdm
pdm install
pdm run main.py
```

### Run In BackGround

```shell
pm2 start pm2.json
pm2 status
pm2 stop pm2.json

```
