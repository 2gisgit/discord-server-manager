#Made by 2gis#8389, https://discordapp.com/users/797308789673033748

import nextcord
from nextcord.ext import commands, tasks
import logging
import atexit
import sys
import inspect
import json
import re
import threading
import schedule
import time
import requests
import os
import subprocess


setting_jf = json.loads(open("settings.json", "r", encoding="utf8").read())

token = setting_jf["token"]

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix=setting_jf["prefix"], intents=intents)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s'))
logger.addHandler(file_handler)


def scheduler():
	def refresh():
		with open("data.json", "w") as f:
			f.write("{}")

	schedule.every(1).hours.do(refresh)

	while True:
		schedule.run_pending()
		time.sleep(1)

t = threading.Thread(target=scheduler)
t.daemon = True
t.start()


def before_exit():
	data = inspect.getinnerframes(sys.last_traceback, 3)[0]
	logger.info(f"ERROR CODE {{{data.code_context}}}, ERROR LINENO {{{data.lineno}}}, ERROR INDEX {{{data.index}}}")
	logger.info(f"RAW DATA\n\n{[data]}")

atexit.register(before_exit)


@bot.event
async def on_ready():
	await bot.change_presence(status=nextcord.Status.online, activity=nextcord.Game('Commands: !help'))
	logger.info(f'logged in {bot.user}')


@bot.event
async def on_message(message):
	try:
		if message.guild is None and message.author != bot.user:
			if not message.author.bot:
				channel = nextcord.utils.get(bot.get_all_channels(), name=setting_jf["report_channel"])
				title = (re.compile('{}(.*){}'.format(re.escape('<'), re.escape('>')))).findall(message.content)
				embed = nextcord.Embed(title=title[0], description=re.sub(r'<(.*)>\n?', '', message.content), color=nextcord.Color.red())

				user_id = message.author.id
				user = await bot.fetch_user(str(user_id))
				
				logger.info(f"{user} writed post '{message.content}'")
				with open('data.json') as f:
					curr_data = json.load(f)
					
				
				if str(user_id) in curr_data.values():
					await user.send("You can only write post once per hour. Pls try again later.")
					
				else:
					await user.send("The post has been completed. Thx.")
					tag = len(curr_data) + 1
					curr_data[str(tag)] = str(user_id)
					with open("data.json", "w") as f:
						json.dump(curr_data, f)
					await channel.send(embed=embed)
		#clear messages
		if message.content.startswith(f'{setting_jf["prefix"]}cls'):
			if message.author.guild_permissions.manage_messages:
				await message.delete()
				_, limit = message.content.split()
				await message.channel.purge(limit=int(limit))
			else:
				logger.info(f'{message.author.name} has used "cls" command.')
				await message.channel.send("PermissionError (You can't use this command)")
		#make a thread if server has question channel
		elif str(message.channel.id) in setting_jf["question_channel_id"]:
			if message.author != bot.user:
				logger.info(f'{message.author.name} made a thread in help channel.')
				embed = nextcord.Embed(description=f"""This is a place to answer {message.author.mention} questions.
		
{message.author.mention} has a question...
It says {message.content}!""", color=int(setting_jf["embed_color"], 16))
				embed.set_footer(text="If you open the thread as a joke, be careful as you may be punished.")
				thread = await message.channel.create_thread(name=f"Q of {message.author.name}", type=nextcord.ChannelType.public_thread)
				await thread.send(embed=embed)
		else:
			pass
	except AttributeError:
		logger.info(f'{message.author.name} has failed to make a thread in help channel.')
		try:
			if message.author.dm_channel:
				await message.author.dm_channel.send("ThreadError (Something wrong while making thread)")
			elif message.author.dm_channel is None:
				channel = await message.author.create_dm()
				await channel.send("ThreadError (Something wrong while making thread)")
		except nextcord.errors.Forbidden:
			logger.info(f"failed to send dm to {message.author.id}.")
			await message.channel.send(f"{message.author.mention}pls allow dm from server members.")
	await bot.process_commands(message)


@bot.command(name="user")
async def userinfo(ctx, member: nextcord.Member = None):
	if not member:
		member = ctx.message.author
	embed = nextcord.Embed(color=int(setting_jf["embed_color"], 16), title=f"Info of {member}")
	roles = [role.mention for role in member.roles]
	embed.set_thumbnail(url=member.avatar.url)
	embed.set_footer(text=f"{ctx.author} used the command")
	embed.add_field(name="Name:", value=member.mention)
	embed.add_field(name="ID:", value=member.id)
	embed.add_field(name="NickName:", value=member.display_name)
	embed.add_field(name="Account Creation Time:", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
	embed.add_field(name="Server Entry Time:", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
	embed.add_field(name="Roles:", value="".join(roles))
	embed.add_field(name="Top-Level Role:", value=member.top_role.mention)
	embed.add_field(name="Is Bot:", value=member.bot)
	logger.info(f'{ctx.author.name} has used "user" command.')
	await ctx.send(embed=embed)


@bot.command(name="ping")
async def ping(ctx):
	embed = nextcord.Embed(title=f'''Pong! {round (bot.latency * 1000)} ms''', color=int(setting_jf["embed_color"], 16))
	logger.info(f'{ctx.author.name} has used "ping" command.')
	await ctx.send(embed=embed)


@bot.command(name="kick")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: nextcord.Member, reason=''):
	await member.kick(reason=reason)


@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: nextcord.Member, reason=''):
	await member.ban(reason=reason)


@bot.command(name="upd")
@commands.has_permissions(administrator=True)
async def remote(ctx, file: str):
	url = ctx.message.attachments[0].url
	code = requests.get(url).content.decode().replace("\r\n", "\n")
	if (file == "main") or (file == "bot.py"):
		await ctx.send("running subprogram...")
		subprocess.Popen(['python', "bot.py", code])
		await ctx.send("quiting main program...")
		sys.exit(0)
	else:
		await ctx.send(f"updating {file}...")
		f = open(file, 'w')
		f.write(code)
		f.close()
		await ctx.send("done!")


@bot.command(name="show")
@commands.has_permissions(administrator=True)
async def show(ctx, file: str):
	f = open(file, 'r')
	read = f.readlines()
	if len(read) > 21:
		read = read[len(read)-3:]
	await ctx.send(f"```{''.join(read)}```")
	f.close()


@bot.command(name="mkfile")
@commands.has_permissions(administrator=True)
async def mkfile(ctx, filename: str):
	open(filename, 'w').close()


@bot.command(name="ls")
@commands.has_permissions(administrator=True)
async def ls(ctx):
	await ctx.send("```"+'\n'.join(os.listdir("./"))+"```")


bot.run(token)
