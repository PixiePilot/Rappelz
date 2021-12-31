import os
import discord
from dotenv import load_dotenv
import pyodbc

# loading constants from environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
DISCORD_TOKEN = ''



conn = None # will later represent the connection to the database


# define discord bot
client = discord.Client()

@client.event
async def on_ready():
    '''
    this method is called when the bot is ready to do bot stuff
    sets up a connection to the player database and logs status to console
    '''
    print('Connecting to SQL server.')
    try:
        global conn
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=localhost;'
                              'Database=Telecaster;'
                              'Trusted_Connection=yes;')
    except:
        print('Couldn\'t connect to the SQL server.')
        quit()

    print(f'Loaded successfully as {client.user}')



@client.event
async def on_message(msg):
    '''
    on message recieve, process message.
    this is the bulk of the bot's functionality
    '''

    if msg.content == '!help':
        await msg.channel.send('The current commands are:\n!gold\n!lvl')
#------------------------------------------<lvl>----------------------------------
    if msg.content == '!lvl':
        cursor = conn.cursor()
        cursor.execute('SELECT name , lv from dbo.Character order by lv DESC')
        data    = cursor.fetchall()
        name    = []
        level   = []
        message = ''

        for row in data:
            name.append(row.name)
            level.append(row.lv)


        for i, (x, y) in enumerate(zip(name,level)):
            if i == 3:
                break
            message = (f'{message}\nRank{i+1}\nname : {x:10} level: {y}')
        message = (f'```{message}```')
        await msg.channel.send(message)
#------------------------------------------</lvl>---------------------------------


#------------------------------------------<Gold>---------------------------------
    if msg.content == '!gold':
        cursor = conn.cursor()
        cursor.execute('SELECT name , gold from dbo.Character order by gold DESC')
        data = cursor.fetchall()
        name = []
        gold = []
        message = str()

        for row in data:
            name.append(row.name)
            gold.append(row.gold)

        for i, (x, y) in enumerate(zip(name, gold)):
            if i == 3:
                break
            message = (f'{message}\nRank{i+1:3}\n name: {x:10} ruppee: {y:3}')

        message = f'```{message}```'
        await msg.channel.send(message)
#------------------------------------------</Gold>---------------------------------

#run discord bot
client.run(DISCORD_TOKEN)