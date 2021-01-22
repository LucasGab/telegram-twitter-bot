import tweepy
import requests
import os
import sys
import logging
from telegram.ext import Updater,MessageHandler, Filters

TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
TWITTER_CONSUMER_SECRET_KEY = os.environ.get('TWITTER_CONSUMER_SECRET_KEY')
TWITTER_BEARER_TOKEN = os.environ.get('TWITTER_BEARER_TOKEN')
TWITTER_ACESS_TOKEN = os.environ.get('TWITTER_ACESS_TOKEN')
TWITTER_ACESS_TOKEN_SECRETE = os.environ.get('TWITTER_ACESS_TOKEN_SECRETE')
TOKEN_TELEGRAM = os.environ.get('TOKEN_TELEGRAM')
CHANNEL_ID = int(os.environ.get('CHANNEL_ID'))
CHANNEL_USERNAME = os.environ.get('CHANNEL_USERNAME')
APPLICATION_NAME = os.environ.get('APPLICATION_NAME')

PORT = int(os.environ.get('PORT', 5000))
DEBUG = "DEBUG"
RELEASE = "RELEASE"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET_KEY)
auth.set_access_token(TWITTER_ACESS_TOKEN, TWITTER_ACESS_TOKEN_SECRETE)
api = tweepy.API(auth)


def getTweets(text):
    text = text.strip()
    text = text.replace("@YELLOW_CRYPTO","@Yellow_crypto_")
    tweets = []
    fonts = []
    init = 0
    end = 280

    mentionIndexInit = text.find("@Yellow_crypto_")
    mentionIndexEnd = -1

    if(mentionIndexInit == -1):
        mentionIndexInit = text.find("@YELLOW_CRYPTO")
    
    if(mentionIndexInit != -1):
        mentionIndexEnd = mentionIndexInit
        while (mentionIndexEnd < len(text)) and (text[mentionIndexEnd] != '\n') and (text[mentionIndexEnd] != ' '):
            mentionIndexEnd+=1

        fonts.append(text[mentionIndexInit:mentionIndexEnd])
        text = text.replace(fonts[len(fonts)-1],"")


    fontIndexInit = text.find("Fonte:")
    fontIndexEnd  = -1

    if(fontIndexInit == -1):
        fontIndexInit = text.find("fonte:")

    if(fontIndexInit != -1):
        fontIndexEnd = fontIndexInit+7
        while (fontIndexEnd < len(text)) and (text[fontIndexEnd] != '\n') and (text[fontIndexEnd] != ' '):
            fontIndexEnd+=1
        
        fonts.append(text[fontIndexInit:fontIndexEnd])
        text = text.replace(fonts[len(fonts)-1],"")

    lines = text.split('\n')
    lines = [x for x in lines if x != '']

    actual = ''

    for line in lines:
        words = line.split(' ')
        firstLine = True
        for word in words:  

            if(len(word)+len(actual) <= 255 and firstLine):
                actual = actual + word
                firstLine = False
            elif(len(word)+1+len(actual) <= 255 and not firstLine):
                actual = actual + ' ' + word
            else:
                tweets.append(actual)
                actual = word

        if (len(actual)+2 <= 255):
            actual = actual + "\n\n"

    tweets.append(actual)

    for font in fonts:
        if(len(font) + len(tweets[len(tweets)-1]) <= 250):
            tweets[len(tweets)-1] = tweets[len(tweets)-1] + font + "\n\n"
        else:
            tweets.append(font + "\n\n")

    return tweets

def sendMessage(text):
    tweets = getTweets(text)
    api.verify_credentials()
    lastStatus = None
    for i in range(len(tweets)):
        if(i <= 0):
            lastStatus = api.update_status(status=tweets[i])
        else:
            lastStatus = api.update_status(tweets[i],lastStatus.id)
    
def sendMediaMessage(text,path):
    try:
        filename = 'temp.jpg'
        request = requests.get(path, stream=True)
        if request.status_code == 200:
            with open(filename, 'wb') as image:
                for chunk in request:
                    image.write(chunk)
            
            api.verify_credentials()

            media = api.media_upload(filename)
            tweets = getTweets(text)
            lastStatus = None
            for i in range(len(tweets)):
                if(i <= 0):
                    lastStatus = api.update_status(status=tweets[i],media_ids=[media.media_id])
                else:
                    lastStatus = api.update_status(tweets[i],lastStatus.id)

            os.remove(filename)
        else:
            sendMessage(text)

    except:
        sendMessage(text)

def echo(update, context):

    if(update.channel_post.chat.id != CHANNEL_ID 
        and (update.channel_post.chat.username == None or update.channel_post.chat.username!=CHANNEL_USERNAME)):
        return

    if(update.channel_post.text != None):
        sendMessage(update.channel_post.text)
    elif(update.channel_post.photo != None):
        size = len(update.channel_post.photo)
        photoSize = update.channel_post.photo[size-1]
        text = ""
        if(update.channel_post.caption != None):
            text = update.channel_post.caption

        sendMediaMessage(text,photoSize.get_file().file_path)

def main():
    
    mode = RELEASE
    if(len(sys.argv) > 1):
        mode = sys.argv[1]

    updater = Updater(token=TOKEN_TELEGRAM, use_context=True)

    dispatcher = updater.dispatcher
    
    echo_handler = MessageHandler((Filters.text | Filters.photo) & (~Filters.command) & Filters.chat_type.channel, echo)
    dispatcher.add_handler(echo_handler)

    if(mode==DEBUG):
        updater.start_polling()
    elif(mode==RELEASE):
        updater.start_webhook(listen="0.0.0.0",port=int(PORT),url_path=TOKEN_TELEGRAM)
        updater.bot.setWebhook( 'https://' + APPLICATION_NAME + '.herokuapp.com/' + TOKEN_TELEGRAM)

    updater.idle()

if __name__ == "__main__":
    main()    