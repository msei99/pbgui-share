# PBGui Dashboard Share

## Contact/Support on Telegram: https://t.me/+kwyeyrmjQ-lkYTJk

v 0.97

## Overview
A tool to share a part of your [PBGui](https://github.com/msei99/pbgui) Dashboard in the streamlit Community Cloud

## Installation
Go to https://manicpt.streamlit.app/ and fork my app
Follow the streamlit documentation https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/fork-and-edit-a-public-app
Clone your new fork to your local system using "git clone https://your_url.git"

## Configure
- Edit api-keys.json
- Push your api-keys.json to your github
- Copy pbgui-share.ini.example to pbgui-share.ini
- Edit pbgui-share.ini and configure yout path to pbgui
- Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml
- Edit .streamlit/secrets.toml and configure your database connection ()
- In your App in the Community Cloud go to Settings/Secrets and copy/paste the same settings as you configured in secrets.toml

## Running
```
python PBGShare.py

```