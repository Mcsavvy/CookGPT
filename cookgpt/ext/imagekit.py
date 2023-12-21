from io import BufferedReader

from imagekitio.client import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from werkzeug.datastructures import FileStorage

from cookgpt.chatbot.models import Chat, ChatMedia, MediaType
from cookgpt.globals import setvar

imagekit: ImageKit = None  # type: ignore


def init_app(app):  # pragma: no cover
    """Initializes extension"""
    global imagekit
    instance = ImageKit(
        private_key=app.config.IMAGEKIT_PRIVATE_KEY,
        public_key=app.config.IMAGEKIT_PUBLIC_KEY,
        url_endpoint=app.config.IMAGEKIT_ENDPOINT,
    )
    imagekit = instance
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


def upload_image(chat: Chat, file: FileStorage):
    """Utility function to upload the file"""
    buffer = BufferedReader(file)  # type: ignore

    val = imagekit.upload_file(
        file=buffer,
        file_name=file.filename,
        options=UploadFileRequestOptions(use_unique_file_name=False),
    )
    print(val.response_metadata.raw)
    val.response_metadata.raw["thumbnailUrl"]
    secret = val.response_metadata.raw["fileId"]
    # The next two lines are for creating a file object or anything
    chatmedia = ChatMedia.create(
        chat_id=chat.id,
        secret=secret,
        url=val.response_metadata.raw["thumbnailUrl"],
        type=MediaType.IMAGE,
        description="",
    )
    print(chatmedia.url)
    return chatmedia
