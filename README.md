# PBGui Dashboard Share

## Contact/Support on Telegram: https://t.me/+kwyeyrmjQ-lkYTJk

v 0.95

## Overview
A tool to share a part of your PBGUi Dashboard in the streamlit Community Cloud

## Installation
Go to https://manicpt.streamlit.app/ and fork my app
Follow the streamlit documentation https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/fork-and-edit-a-public-app
Clone your new fork to your local system using "git clone https://your_url.git"

## Configure
- Delete pbgui-share.db
- Edit api-keys.json
- Copy pbgui-share.ini.example to pbgui-share.ini
- Edit pbgui-share.ini and configure your github account
- Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml
- Edit .streamlit/secrets.toml and set your password in db_key
- In your App in the Community Cloud go to Settings/Secrets and add your password as db_key = "password"

## Running
```
python PBGShare.py

```