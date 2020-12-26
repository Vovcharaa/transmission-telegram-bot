<h1 align="center">
  Transmission Telegram Bot
</h1>

## Available commands
* <b>List of all features</b>;
* <b>Torrent info</b> - Get all details about a torrent;
* <b>Torrent control</b> - Start, stop, delete, verify torrents;
* <b>Add torrent</b> - From a <code>.torrent</code> file or from magnet url;
* <b>Select files to download</b>
* <b>User whitelist</b>
  
## How to run?
The easiest way is to run docker container with docker-compose\
Just fill in bot.env file and run <code>docker-compose up -d</code>

## TO DO list:
* Status notifications
* Support for different types of webhooks (Polling and webhooks without ngrok)