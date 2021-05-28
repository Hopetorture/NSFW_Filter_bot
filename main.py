#!/usr/bin/env python3

import logging
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
)
from telegram.update import Update

from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc, resources_pb2, service_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2

TOKEN_PATH = 'token.txt'
CLARIFAI_KEY = 'clarifai_key.txt'
NSFW_FILTER = True

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PredictionModel:
    def __init__(self):
        self.stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
        # moderation cccf390eb32cad478c7ae150069bd2c6
        # nsfw - v1.0 ccc76d86d2004ed1a38ba0cf39ecb4b1
        # nsfw-v1.0 e9576d86d2004ed1a38ba0cf39ecb4b1
        # moderation a3ab820725bb472092a2cd63b1c0035a
        # moderation d16f390eb32cad478c7ae150069bd2c6

        # self.model_id = 'aaa03c23b3724a16a56b629203edc62c'  # General
        self.model_id = 'd16f390eb32cad478c7ae150069bd2c6'  # moderation
        with open(CLARIFAI_KEY, 'r') as f:
            self.api_key = f.read()
            self.auth = (('authorization', f'Key {self.api_key}'),)

    def is_nsfw(self, img):
        request = service_pb2.PostModelOutputsRequest(
            model_id=self.model_id,
            inputs=[
                resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=img)))
            ])
        response = self.stub.PostModelOutputs(request, metadata=self.auth)

        if response.status.code != status_code_pb2.SUCCESS:
            raise Exception("Request failed, status code: " + str(response.status.code))

        total_nsfw_rating = 0.
        for concept in response.outputs[0].data.concepts:
            if concept.name in ('explicit', 'suggestive'):
                total_nsfw_rating += concept.value
        if total_nsfw_rating > 0.60:
            return True
        return False


Model = PredictionModel()


def error(update, context):
    """Log Errors caused by Updates."""
    logger.critical('Update "%s" caused error "%s"', update, context.error)


def welcome_msg(update, context):
    msg = 'Im here to chew bubble gum and see some thicc ass. As you can see, I\'m already out of gum.'
    update.message.reply_text(msg)


def send_approval(update: Update, context):
    try:
        user_id = update.message.from_user.id
    except Exception as e:
        user_id = None

    if user_id:
        if user_id == 735086534:  # Annie
            update.message.reply_text('🍓🍓🍓')
        elif user_id == 202504819:  # Yuna
            update.message.reply_text('💋💋💋')
        elif user_id == 101040948:  # me
            update.message.reply_text('🌈🌈🌈')
        elif user_id == 1255924798:  # Mary K
            update.message.reply_text('😍😍😍')

        return
    update.message.reply_text('🍑🍑🍑')


def image_reply(update: Update, context):
    if NSFW_FILTER:
        uids = set()
        for p in update.message.photo:
            if p.file_unique_id in uids:
                continue
            uids.add(p.file_unique_id)
            photo = bytes(p.get_file().download_as_bytearray())
            if Model.is_nsfw(photo):
                send_approval(update, context)
                return
        return

    update.message.reply_text('🍑🍑🍑')


def enable_nsfw(update, ctx):
    global NSFW_FILTER
    NSFW_FILTER = True


def disable_nsfw(update, ctx):
    global NSFW_FILTER
    NSFW_FILTER = False


def echo(update, ctx):
    print(update.message.text)


def run_bot():
    with open(TOKEN_PATH, 'r') as f:
        token = f.read().strip()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', welcome_msg)

    enable_nsfw_filter = CommandHandler('enable_nsfw_filter', enable_nsfw)
    disable_nsfw_filter = CommandHandler('disable_nsfw_filter', disable_nsfw)

    image_handler = MessageHandler(Filters.photo | Filters.document.image, image_reply)
    dispatcher.add_handler(image_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(enable_nsfw_filter)
    dispatcher.add_handler(disable_nsfw_filter)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    run_bot()
