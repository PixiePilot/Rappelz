from logging import currentframe
import threading
import os
import discord
from discord.client import Client
from discord.ext import commands
import time
from dotenv import load_dotenv
import pyodbc
import asyncio
giveawaylist = []

connah = None # will later represent the connection to the Auth DB
conn = None # will later represent the connection to the Telecaster DB
connectionstring = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Telecaster;'
                    'Trusted_Connection=yes;')
connectionstringah = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Auth;'
                    'Trusted_Connection=yes;')
#^ The connection strings ^


#loads the discord token.
with open("Token.txt") as read:
    DISCORD_TOKEN = (read.readline())

bot = commands.Bot(command_prefix="!")

#On_ready is code that's executed whenever the bot starts, In this case it will attempt to connect to the sql server.
print("Attempting to connect to the SQL server...")
@bot.event
async def on_ready():
    global conn,connah,connectionstring

    try:
        conn = pyodbc.connect(connectionstring)
        connah = pyodbc.connect(connectionstringah)
    except ConnectionRefusedError:
        print('Connection refused by SQL server\nThis bot only works with Myssql make sure you\'re not using Mysql')
        quit()
    except ConnectionError:
        print('Unable to connect to SQL server\nThis could be caused by :\nIncorrect password or user or invalid permissions to see the error')
        quit()

    print(f'successfully connected to SQL server.\nLogged in as user {bot.user} on discord')


#list of functions
def functionlvl(msg):
        cursor = conn.cursor()
        cursor.execute('SELECT TOP(3) name , lv from dbo.Character order by lv DESC')
        data    = cursor.fetchall()
        name    = []
        level   = []
        message = str()

        for row in data:
            name.append(row.name)
            level.append(row.lv)


        for rank, (namestring, levelstring) in enumerate(zip(name,level)):

            message = (f'{message}\nRank {rank+1}\nname : {namestring:10} level: {levelstring}')
        message = (f'```{message}```')
        return message
#Funciton level is simply the function that shows the top 3 highest level players in the game and returns the value

def functiongold(msg):
    cursor = conn.cursor()
    cursor.execute('SELECT TOP(3) name , gold from dbo.Character order by gold DESC')
    data = cursor.fetchall()
    name = []
    gold = []
    message = str()

    for row in data:
        name.append(row.name)
        gold.append(row.gold)

    for rank, (namestring, goldstring) in enumerate(zip(name, gold)):

        message = (f'{message}\nRank{rank+1:3}\n name: {namestring:10} ruppee: {goldstring:3}')

    message = f'```{message}```'
        
    return message
#Funciton gold is simply the function that shows the top 3 richest players in the game and returns the value

def discordidtoname(msg):
        cursor = connah.cursor()
        user = msg.author.id
        cursor.execute(f"SELECT account,DiscordID FROM [Account] WHERE DiscordID ={user}")
        result = cursor.fetchall()
        username = []
        count = 0
        for row in result:
            username.append(row.account)
            count += 1
            if count >= 2:
                msg.channel.send("You can only have one discord ID per account.")
                return False
        username = username.pop()
        return username
#Function to resolves the users account based on their discord ID ( Needs the ID to already be added to the AUTH db table design in varchar ( it's used as an int ) )

def threadingwait(waittime,msg,giveawaylist):
    time.sleep(waittime)
    print(giveawaylist)
    return
#Timer for giveaway after deletion, Since it's a multithread the sleep will not stop the rest of the code

@bot.command()
async def lvl(msg):
    message = functionlvl(msg)
    await msg.channel.send(message)
#functionlvl

@bot.command()
async def gold(msg):
    message = functiongold(msg)
    await msg.channel.send(message)
#functiongold

@bot.command()
async def test(msg):
    resolved_name = discordidtoname(msg)
    await msg.channel.send(resolved_name)
#function discordidtoname

@bot.command()
async def giveaway(msg,itemname: str,timer: int,id: int):
        global giveawaymessage,giveawaylist
        giveawaymessage = await msg.channel.send((f'There\'s a give away where {itemname} will be given away in {timer} seconds'))
        emoji = '\N{THUMBS UP SIGN}'
        await giveawaymessage.add_reaction(emoji)
        print(giveawaymessage)
        
        #the await is ignored for the first one, When it's ran again after the timer it will run the code below it aswell.
        await giveawaymessage.delete(delay=timer)
        thread = threading.Thread(target=threadingwait,args=[timer,msg,giveawaylist])
        thread.start()
        print('test')

    



@bot.event
async def on_reaction_add(reaction,user):
    global giveawaymessage,giveawaylist
    if reaction.message == giveawaymessage:
        for check in giveawaylist:
            if check == user.id:
                return
        giveawaylist.append(user.id)
        print(giveawaylist)
    return
#Checks the current give away message for newly added ( does not save if bot shuts down)
bot.run(DISCORD_TOKEN)
