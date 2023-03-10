## Discord Nuke Bot
Welcome to the Discord Nuke Bot project! This bot was created specifically for the Community Nuker Server, a fun and lighthearted Discord server where users can nuke their own servers for entertainment purposes. Everything in this project is made with love, so if you enjoy using it, we would appreciate a star on GitHub!

This bot allows users to "nuke" their Discord servers, which essentially means to delete all channels and roles, ban all users, and then restore the server to its previous state. Please note that this bot is for entertainment purposes only and should not be used to actually harm any Discord servers. Use at your own risk.

Before getting started, we recommend that you take a moment to review the introductions provided in the [setup.md](https://github.com/efenatuyo/discord-nuke-bot/blob/main/setup.md) file. This will give you a good overview of the steps involved in setting up and using the bot, as well as any important considerations to keep in mind. Once you have familiarized yourself with the introductions, you can begin using the bot. Thank you for choosing to work with us, and we hope you find our project helpful and enjoyable.

### Antiratelimit

This bot uses a token bucket system to bypass Discord rate limits. When a command is received, the bot checks to see if there are enough tokens available in the bucket to process the request. If there are, it removes a token and processes the command. If there are not enough tokens available, the request is denied until more tokens are added to the bucket. This helps to prevent the bot from overloading the Discord server and ensures that all users have a fair chance to use the bot.

### Commands
The Discord Nuke Bot comes with a variety of commands that allow you to control and customize your nuking experience. Here is a list of all the available commands:

`ban`: This command bans every user from the server. This is typically used as a part of the nuke process, but can also be used on its own if you want to temporarily remove all users from the server.

`help`: The help command displays a list of all the available commands and a brief description of what each one does.

`leaderboard`: The leaderboard command displays a list of the top users on the server based on their nuke count. This can be a fun way to see who is the most active nuker on the server.

`login`: The login command saves your Discord bot token, which is required for the bot to function. You can obtain your bot token by creating a Discord bot and getting the token from the Discord Developer Portal.

`nuke`: The nuke command initiates the nuke process on the server. This will delete all channels and roles, ban all users, and then restore the server to its previous state.

`restore`: The restore command restores the server to its previous state after a nuke. This can be useful if you want to cancel a nuke before it is completed or if something goes wrong during the nuke process.

`stats`: The stats command displays some basic statistics about your nuking activity on the server, including your nuke count and the time of your last nuke.

`token_nuke`: The token_nuke command is similar to the regular nuke command, but it allows you to specify a Discord bot token to use for the nuke. This can be useful if you want to use multiple bot accounts to nuke a server.

`unban`: The unban command unbanishes all users from the server. This is typically used as a part of the restore process, but can also be used on its own if you want to allow all users to join the server again.

`type`: The type command allows you to turn the auto_nuke feature on or off. When auto_nuke is on, the bot will automatically nuke the server at a specified interval. This can be useful if you want to have a constantly nuking server for fun, but be warned that it can also be very disruptive.

### Owner Commands

`fix`: Leaves every guild the bot is in

### Screenshots

Leaderboard:

![Screenshot of the leaderboard command](https://media.discordapp.net/attachments/1058161953257824346/1059543612179873893/image.png)

Tracker:

![Screenshot of the Tracker event](https://media.discordapp.net/attachments/1058161953257824346/1059543983124131871/image.png)

Stats:

![Screenshot of the Stats command](https://media.discordapp.net/attachments/1058161953257824346/1059544207544565881/image.png)


### Support
If you need help using this bot or have any questions, you can join the [server](https://discord.gg/n2xfSuf7p8) and ask for assistance. You can also create an issue on this GitHub repository and we will do our best to help you out.

### License
This project is licensed under the terms of the CC-BY-SA-4.0 license. This means that you are free to use, modify, and distribute the code as long as you give proper credit to the original creators. If you use this project in your own work, please make sure to include a link back to this repository and mention the original authors. Failure to do so may result in the project being taken down. We want to make sure that everyone who uses this project is able to do so legally and ethically.
