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
import random
import hashlib
giveawaylist = []

connah = None # will later represent the connection to the Auth DB
conn = None # will later represent the connection to the Telecaster DB
connbil = None # Will later represent the connection to the Billing DB (Mainly used for paid item ( Cs box ) )
connectionstring = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Telecaster;'
                    'Trusted_Connection=yes;')

connectionstringah = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Auth;'
                    'Trusted_Connection=yes;')

connectionstringbil = ('Driver={SQL Server};'
                    'Server=localhost;'
                    'DataBase=Telecaster;'
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
    global conn,connah,connbil,connectionstring

    try:
        conn = pyodbc.connect(connectionstring)
        connah = pyodbc.connect(connectionstringah)
        connbil = pyodbc.connect(connectionstringbil)
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

def discordidtonamegiveaway(msg,id):
        cursor = connah.cursor()
        user = id
        cursor.execute(f"SELECT account_id,DiscordID FROM [Account] WHERE DiscordID ={user}")
        result = cursor.fetchall()
        accountid = []
        count = 0 
        for row in result:
            count +=1
            if count >= 2:
                return
            accountid.append(row.account_id)


        accountid = accountid.pop()
        return accountid
#Function to resolves the users account based on their discord ID ( Needs the ID to already be added to the AUTH db table design in varchar ( it's used as an int ) )

async def taskwinner(waittime,msg,giveawaylist,id):
    global connbil
    connbil = connbil.cursor()
    await asyncio.sleep(waittime)
    print(giveawaylist)
    amount = len(giveawaylist)
    randomnumber = random.randint(0,amount)
    randomnumber -= 1
    winner = giveawaylist[randomnumber]
    winner = discordidtonamegiveaway(msg,winner)
    print(winner)
    # After learning billing insert query here 
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
        taskdelmsg = asyncio.create_task(taskwinner(timer,msg,giveawaylist,id))        
        await giveawaymessage.delete(delay=timer)
        #thread = threading.Thread(target=threadingwait,args=[timer,msg,giveawaylist,id])
        #thread.start()
        await taskdelmsg

@bot.command()
async def register(msg):
    
    await msg.channel.send(f"Please check your DM, {msg.author.name}")
    message = (f"Hello, {msg.author.name}.\nusing the DM's you will be able to savely link your discord to your Ingame account, Be wary though you can only have 1 ingame account connected to 1 discord account.\n By typing !link you will be able to link your discord account to Rappelz however you need to login first\nwhich can be done by typing !link in the following manner: !link loginname password")
    await msg.author.send(message)

@bot.command()
@commands.dm_only()
async def link(msg,user:str,login:str):
    global connah
    cursor = connah.cursor()
    user = "'"+user+"'"
    md5key = str(2020)
    loginstr = (md5key+login)
    result = hashlib.md5(loginstr.encode())
    hashedlogin = (result.hexdigest())
    hashedlogin = "'"+hashedlogin+"'"
    print(f"{user},{hashedlogin} has been called to verify by user {msg.author} their discord id is: {msg.author.id}")

    cursor.execute(f"SELECT account , password , DiscordID, account_id FROM [Account] WHERE (account = {user} AND password = {hashedlogin})")

    logininfo = cursor.fetchall()

    for row in logininfo:

        print("Account name: "+(row.account) +" Password: "+ (row.password)+" DiscordID: " +(row.DiscordID)+" accountid: "+(row.account_id) )



@bot.event
async def on_reaction_add(reaction,user):
    global giveawaymessage,giveawaylist
    if user.id == 921459290273898507:
        return
    if reaction.message == giveawaymessage:
        for check in giveawaylist:
            if check == user.id:
                return
        giveawaylist.append(user.id)
        print(giveawaylist)
    return
#Checks the current give away message for newly added ( does not save if bot shuts down)
bot.run(DISCORD_TOKEN)
