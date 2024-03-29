
import os
import tweepy
import requests
from time import sleep
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont, ImageFilter

load_dotenv()

SLEEP = int(os.environ['SLEEP'])
SCREEN_NAME = os.environ['SCREEN_NAME']
TEMPLATE_NUM = os.environ['TEMPLATE_NUM']

curr_dir = os.path.abspath(os.getcwd())
txt_dir = os.path.join(curr_dir, 'lastId.txt')
temp_dir = os.path.join(curr_dir, 'imgs', f'template{TEMPLATE_NUM}.jpg')
fonts_dir = os.path.join(curr_dir, 'fonts')


def auth_twitter():

    CONSUMER_KEY = os.environ['CONSUMER_KEY']
    CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
    ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
    ACCESS_SECRET = os.environ['ACCESS_SECRET']

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    api.verify_credentials()

    return api


def getLastID():
    with open(txt_dir) as f:
        lines = f.readlines()
    return str(lines[0])


def setLastID(id):
    with open(txt_dir, 'w') as f:
        f.write(str(id))


def getInfo(api):

    info = []
    last_id = getLastID()

    mentions = api.mentions_timeline(
        since_id=last_id,
        tweet_mode='extended')

    for mention in mentions:
        info.append({'id': mention.id,
                     'user_id': mention.user.id,
                     'text': mention.full_text,
                     'user_name': mention.user.name,
                     'user_screen_name': mention.user.screen_name,
                     'img_url': mention.user.profile_image_url.replace('_normal', '')
                     })

    return info


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
    img = Image.open(temp_dir)

    # size() returns a tuple of (width, height)
    image_size = img.size

    # create the ImageFont instance
    font_file_path = os.path.join(fonts_dir, 'TT Firs Regular.ttf')
    font = ImageFont.truetype(font_file_path, size=50, encoding="unic")

    # get shorter lines
    lines = textWrap(text, font, image_size[0])
    # ['This could be a single line text ', 'but its too long to fit in one. ']
    # print(lines)
    return lines


def drawImage(mention):

    # download profile picture
    pp_req = requests.get(url=mention['img_url'])
    pp_dir = os.path.join(curr_dir, 'imgs', f"{mention['user_id']}.jpg")
    with open(pp_dir, "wb") as f:
        f.write(pp_req.content)


    font_main = ImageFont.truetype(os.path.join(fonts_dir, 'TT Firs Regular.ttf'), size=50)
    font_name = ImageFont.truetype(os.path.join(fonts_dir, 'TT Firs Medium.ttf'), size=40)
    font_user_name = ImageFont.truetype(os.path.join(fonts_dir, 'TT Firs Italic.ttf'), size=30)

    # write text
    # width = 1080
    # height = 1080
    # img = Image.new('RGB', (width, height), color='black')
    bg = Image.open(temp_dir)

    imgDraw = ImageDraw.Draw(bg)

    # prepare quote
    idx = mention['text'].lower().index('comment2quote')
    quote = mention['text'][:idx-1] + mention['text'][idx+14:]
    quote = quote.replace(f'@{SCREEN_NAME}', '')
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

    pp = Image.open(pp_dir)
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
    back_im_dir = os.path.join(curr_dir, 'imgs', f"{mention['id']}.jpg")
    back_im.save(back_im_dir, quality=95)


def main():

    api = auth_twitter()

    while True:

        mentiones = getInfo(api)

        for mention in mentiones:

            if '#comment2quote' in mention['text'].lower():

                drawImage(mention)
                pp_dir = os.path.join(curr_dir, 'imgs', f"{mention['user_id']}.jpg")
                back_im_dir = os.path.join(curr_dir, 'imgs', f"{mention['id']}.jpg")

                api.update_status_with_media(
                    status=f'@{mention["user_screen_name"]} Here is your quote!',
                    in_reply_to_status_id=mention['id'],
                    filename=back_im_dir,
                )

                setLastID(id=mention['id'])

                print(mention)

                # delete imgs
                os.remove(pp_dir)
                os.remove(back_im_dir)

        print("Sleeping for a minute...")
        sleep(SLEEP*60)


if __name__ == '__main__':
    main()
