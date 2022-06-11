
import tweepy
import requests
from time import sleep
from os import environ, remove
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv()


def auth_twitter():

    CONSUMER_KEY = environ['CONSUMER_KEY']
    CONSUMER_SECRET = environ['CONSUMER_SECRET']
    ACCESS_TOKEN = environ['ACCESS_TOKEN']
    ACCESS_SECRET = environ['ACCESS_SECRET']

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    return api


def get_replies(api, screen_name, tweet_id):

    replies = []
    replies_clean = []
    for tweet in tweepy.Cursor(api.search_tweets, q='to:'+screen_name, result_type='recent', timeout=999999).items(1000):
        if hasattr(tweet, 'in_reply_to_status_id_str'):
            if (tweet.in_reply_to_status_id_str == tweet_id):
                replies.append(tweet)

    for tweet in replies:
        row = {'user': tweet.user.screen_name,
               'text': tweet.text.replace('\n', ' '),
               'id': tweet.id_str}
        replies_clean.append(row)

    return replies_clean


def getLastId():
    with open('lastId.txt') as f:
        lines = f.readlines()
    return str(lines[0])


def setLastId(id):
    with open('lastId.txt', 'w') as f:
        f.write(str(id))


def getInfo(api):

    data = []
    last_id = getLastId()

    mentions = api.mentions_timeline(
        since_id=last_id,
        tweet_mode='extended')

    for mention in mentions:
        data.append({'id': mention.id,
                     'user_id': mention.user.id,
                     'text': mention.full_text,
                     'user_name': mention.user.name,
                     'user_screen_name': mention.user.screen_name,
                     'img_url': mention.user.profile_image_url.replace('_normal', '')})

    return data


def textWrap(text, font, max_width):
    lines = []
    # If the width of the text is smaller than image width
    # we don't need to split it, just add it to the lines array
    # and return
    max_width -= 190
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            # when the line gets longer than the max width do not append the word,
            # add the line to the lines array
            lines.append(line)
    return lines


def getLines(text):
    # open the background file
    img = Image.open('imgs\\template2.jpg')

    # size() returns a tuple of (width, height)
    image_size = img.size

    # create the ImageFont instance
    font_file_path = 'arial.ttf'
    font = ImageFont.truetype(font_file_path, size=50, encoding="unic")

    # get shorter lines
    lines = textWrap(text, font, image_size[0])
    # ['This could be a single line text ', 'but its too long to fit in one. ']
    print(lines)
    return lines


def drawImage(mention):

    # download profile picture
    ppimg = requests.get(url=mention['img_url'])
    with open(f"imgs\{mention['user_id']}.jpg", "wb") as f:
        f.write(ppimg.content)

    # write text
    # width = 1080
    # height = 1080

    font_main = ImageFont.truetype("fonts\TT Firs Regular.ttf", size=50)
    font_name = ImageFont.truetype("fonts\TT Firs Medium.ttf", size=40)
    font_user_name = ImageFont.truetype("fonts\TT Firs Italic.ttf", size=30)

    # img = Image.new('RGB', (width, height), color='black')
    bg = Image.open('imgs\\template2.jpg')

    imgDraw = ImageDraw.Draw(bg)

    # prepare quote
    mention['text'] = mention['text'].replace('#comment2Quote', '')
    mention['text'] = mention['text'].replace('@elcanmhmmdl', '')
    quote = f'{mention["text"]}'
    quote = quote.strip()

    # split lines
    h = -60
    quote_f = ''
    lines = getLines(quote)
    for l in lines:
        quote_f += f'{l}\n'
        h += 60
    quote_f = quote_f.strip()

    # textWidth, textHeight = imgDraw.textsize(
    #     quote_f, font=font)
    # xText = (width - textWidth) / 2
    # yText = (height - textHeight) / 2

    imgDraw.text((110, 420), quote_f,
                 font=font_main, fill=(255, 255, 255), spacing=12)

    imgDraw.text((223, 562+h), mention['user_name'],
                 font=font_name, fill=(255, 255, 255))

    imgDraw.text((223, 603+h), f"@{mention['user_screen_name']}",
                 font=font_user_name, fill=(255, 255, 255))

    pp = Image.open(f"imgs\{mention['user_id']}.jpg")
    pp = pp.resize((110, 110))

    # mask circle
    mask_im = Image.new("L", pp.size, 0)
    draw = ImageDraw.Draw(mask_im)
    draw.ellipse((5, 5, 105, 105), fill=255)
    # mask_im.save('mask_circle.jpg', quality=95)

    mask_im_blur = mask_im.filter(ImageFilter.GaussianBlur(2))
    # mask_im_blur.save('mask_circle_blur.jpg', quality=95)

    back_im = bg.copy()
    back_im.paste(pp, (99, 550+h), mask_im_blur)
    back_im.save(f'imgs\{mention["id"]}.jpg', quality=95)


def main():

    api = auth_twitter()

    while True:

        mentiones = getInfo(api)

        for mention in mentiones:

            if '#comment2quote' in mention['text'].lower():

                drawImage(mention)

                api.update_status_with_media(
                    status=f'@{mention["user_screen_name"]} Here is your quote!',
                    in_reply_to_status_id=mention['id'],
                    filename=f'imgs\{mention["id"]}.jpg',
                )

                setLastId(id=mention['id'])

                print(mention)

                # delete imgs
                remove(f'imgs\{mention["user_id"]}.jpg')
                # remove(f'imgs\{mention["id"]}.jpg')

        print("Sleeping for a minute...")
        sleep(60)


def test():
    # Courage isn't having the strength to go
    mention = {'id': 1534181445299740674, 'user_id': 2401290224, 'text': "Courage isn't having the strength Courage isn't having the strength Courage isn't having the strength to go on - it is going on when you don't have strength.",
               'user_name': 'Elcan Məhəmmədli', 'user_screen_name': 'eljanmahammadli', 'img_url': 'http://pbs.twimg.com/profile_images/1533503948719628288/tkxiJ5F3.jpg'}

    drawImage(mention)


if __name__ == '__main__':
    main()
    # test()
