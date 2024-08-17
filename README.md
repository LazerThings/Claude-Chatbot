# Claude Chatbot
This is a self hosted Claude chatbot made (mostly) by Claude 3.5 Sonnet itself. It runs Claude 3 Haiku, but you can change this in the code. It is easy to setup and is made with [Python](https://python.org) and [Bottle](https://bottlepy.org).
## Setup
1. Make sure you set the enviroment variable `ANTHROPIC_API_KEY` on the computer running the server to the API key to use.
2. Download this repository and make sure you are extracting it into an empty folder.
3. Go into a terminal and navigate into this empty folder, then run `pip install -r requirements.txt` to install the requirements (`bottle`, `anthropic`, and `markdown2`).
4. Then, in the terminal, run `py claude_chatbot.py`.
## Using
Connect to the computer in a web browser, at port 6705. This will open the computer's Claude Chatbot server.
## Saving
Claude Chatbot auto-saves whenever you do anything in the app. It saves between client-side reloads and even the server restarting, because all the storage is in the `conversations.json` file. Deleting this file will wipe all data.