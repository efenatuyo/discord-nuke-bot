from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def main():

  return "hi" #Change this if you want

def run():
    app.run(host="0.0.0.0", port=8080) #don't touch this

def keep_alive():
    server = Thread(target=run)
    server.start()
