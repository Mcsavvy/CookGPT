import json
from io import BufferedReader, RawIOBase

from apiflask import Schema
from apiflask.fields import File
from imagekitio.client import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from marshmallow import ValidationError

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


def validate_file_size(file):
    """Validates the file size making sure it's at most 8mb"""
    max_size_in_bytes = 8 * 1024 * 1024  # 8MB in bytes
    if file and len(file.read()) > max_size_in_bytes:
        raise ValidationError("File size must be at most 8MB.")
    file.seek(0)


def validate_file_type(file):
    """Validates the file type"""
    if file and file.mimetype not in ["image/jpeg", "image/png", "image/gif"]:
        raise ValidationError("File must either be a jpeg, gif or png")


class UploadImage(Schema):
    profile_picture = File(
        required=True,
        metadata={
            "description": "The file you want to use. It must be a picture below 8mb"
        },
        validate=[validate_file_type, validate_file_size],
    )


def delete_image(chat: Chat):
    """Utility function to delete the user's profile picture from ImageKit"""
    val = chat.file.copy()
    if len(val) == 2:
        fId = val[-1]
        try:
            val = imagekit.delete_file(fId)
            # These next two lines are for deleting the image
            chat_media = ChatMedia(
                chat_id=chat.id,
                secret=secret,
            )
            chat_media.delete()  # ? Not sure if this is how it works
            print(val.response_metadata.raw)
            return True
        except Exception as e:
            print(e)
            return False


def upload_image(chat: Chat, file: RawIOBase):
    """Utility function to upload the file"""
    buffer = BufferedReader(file)
    try:
        delete_image(chat)
        val = imagekit.upload_file(
            file=buffer,
            file_name=str(chat.id[0:6]),
            options=UploadFileRequestOptions(use_unique_file_name=True),
        )
        print(val.response_metadata.raw)
        url = val.response_metadata.raw["url"]
        secret = val.response_metadata.raw["fileId"]
        json.dumps([url, secret])

        # The next two lines are for creating a file object or anything
        ChatMedia.create(
            chat=chat, secret=secret, url=url, type=MediaType.IMAGE
        )
        return True
    except Exception as e:
        print(e)
        return False
