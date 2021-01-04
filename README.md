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
## Demo
<img src="/demo/demo.gif" width="300" height="533"/>

## How to run?
The easiest way is to run docker container with docker-compose\
Just fill in bot.env file and run <code>docker-compose up -d</code>

To run without docker run:\
* <code>pip3 install -r requirements.txt</code>
* <code>python3 -m transmision-telegram-bot</code>

## TO DO list:
* Status notifications
