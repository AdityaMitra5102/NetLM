#NetLM allows you to remotely configure Cisco Ios devices over a telegram bot
#Ideal for remote trouble shooting and incident response
#NetLM allows you to give commands in plain English and uses AI to convert it to ios commands.


ip='192.168.56.2' #Telnet. (Can be configured for serial or SSH too)
port=5003 #Telnet port

TOKEN="[REDACTED]" #Telegram token

import requests
import json
import socket
import time

def extract_normal_text(bytes_buffer):
	normal_text = b''
	for byte in bytes_buffer:
		try:
			char = bytes([byte]).decode('utf-8')
			normal_text += bytes([byte])
		except UnicodeDecodeError:
			pass
	return normal_text.decode('utf-8', errors='replace')

def call(msg):
	url = "http://localhost:11434/api/chat" #Ollama api
	data = {"model": "llama3","stream": False,"messages": [{ "role": "user", "content": "You are supposed to give commands for a Cisco ios."}, {"role": "user", "content": "You are now in user exec mode."},{ "role": "user", "content":  "Give the commands to perform each task as a json list format, each command as an element in the list. Dont say any thing else. No explanation needed. The commands have to correct."}, {"role": "user", "content": "The task is "+msg }]}
	response = requests.post(url, json=data)
	resp=response.json()
	commandlist=resp['message']['content']
	return json.loads(commandlist)

def make_commandlist(msg):
	list=[]
	list=list+call(msg)
	for i in range(3):
		list.append('exit')
	for i in range(len(list)):
		list[i]='    '+list[i]

	print(list)
	return list

def runtask(msg):
	try:
		commands=make_commandlist(msg)
		output=''
		for x in commands:
			s=socket.socket()
			s.connect((ip,port))
			#print(x)
			output=output+x+'\n'
			s.send((x+"\n\r").encode())
			time.sleep(3)
			recv=s.recv(2048)
			rec=extract_normal_text(recv)
			#print(rec)
			output=output+rec+'\n\n'
			time.sleep(1)
			s.close()
		return output
	except:
		return runtask(msg)
	


from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Give instruction for switch")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    txt=update.message.text
    print(txt)
    op=runtask(txt)
    await update.message.reply_text(op)


def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("Bot started")


if __name__ == "__main__":
    main()
