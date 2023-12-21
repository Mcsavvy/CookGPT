from io import BufferedReader, RawIOBase

from imagekitio.client import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions

from cookgpt.chatbot.models import Chat, ChatMedia, MediaType
from cookgpt.globals import imagekit, setvar


def init_app(app):  # pragma: no cover
    """Initializes extension"""
    instance = ImageKit(
        private_key=app.config.IMAGEKIT_PRIVATE_KEY,
        public_key=app.config.IMAGEKIT_PUBLIC_KEY,
        url_endpoint=app.config.IMAGEKIT_ENDPOINT,
    )
    setvar("imagekit", instance)


def delete_image(media: ChatMedia):
    """Utility function to delete the user's profile picture from ImageKit"""
    fId = media.secret
    if fId != "":
        try:
            val = imagekit.delete_file(fId)
            # These next two lines are for deleting the image
            print(val.response_metadata.raw)
            return True
        except Exception as e:
            print(e)
            return False


def upload_image(chat: Chat, file: RawIOBase):
    """Utility function to upload the file"""
    buffer = BufferedReader(file)
    try:
        val = imagekit.upload_file(
            file=buffer,
            file_name=str(chat.sid[0:6]),
            options=UploadFileRequestOptions(use_unique_file_name=True),
        )
        print(val.response_metadata.raw)
        url = val.response_metadata.raw["url"]
        secret = val.response_metadata.raw["fileId"]
        # The next two lines are for creating a file object or anything
        ChatMedia.create(
            chat=chat, secret=secret, url=url, type=MediaType.IMAGE
        )
        return True
    except Exception as e:
        print(e)
        return False
