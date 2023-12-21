import json
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from api import app
from cookgpt.auth.models import ChatMedia

# import os
from io import BufferedReader
# from models import store
def init_app(app): # pragma: no cover
    """Initializes extension"""
    instance = ImageKit(
        private_key=app.config["IMAGE_KIT"]["PRIVATE_KEY"],
        public_key=app.config["IMAGE_KIT"]["PUBLIC_KEY"],
        url_endpoint=app.config["IMAGE_KIT"]["URL_ENDPOINT"],
    )
    return instance
imagekit = init_app(app) # All I needed was to access the app and nothing more




def delete_image(chat):
    """Utility function to delete the user's profile picture from ImageKit"""
    fId = chat.media.secret or ""
    if fId != ""
        try:
            val = imagekit.delete_file(fId)
            chat.media.delete() # ? Not sure if this is how it works
            print(val.response_metadata.raw)
            return True
        except Exception as e:
            print(e)
            return False


def upload_image(chat, file):
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
        file_data = json.dumps([url, secret])
        # The next two lines are for creating a file object or anything
        chat_media = ChatMedia(chat=chat, chat_id=chat.id, secret=secret, url=url type="image")
        chat_media.save() # ? Not sure if this is how it works
        # store.save()
        return True
    except Exception as e:
        print(e)
        return False
