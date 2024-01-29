"""chatbot schema data examples."""


Response = "Okay, tell me what type of rice so I can suggest recipes"
Query = "Hi, I need a recipe for rice"
DateTime = "2021-01-01 00:00:00"
Uuid = "36b51f8a-c9fa-43f8-92fa-ff6927736c10"

ChatExample = {
    "id": Uuid,
    "content": Response,
    "chat_type": "RESPONSE",
    "cost": 0,
    "previous_chat_id": Uuid,
    "next_chat_id": Uuid,
    "sent_time": DateTime,
    "thread_id": Uuid,
}

ThreadExample = {"id": Uuid, "chat_count": 2, "cost": 220}


class Chat:
    """Represents a chat object with various operations."""

    class Get:
        """Represents the GET operation for retrieving a chat."""

        Response = ChatExample
        NotFound = {"message": "chat not found"}

    class Post:
        """Represents the POST operation for creating a chat."""

        Body = {"query": Query, "thread_id": Uuid}
        Response = {
            "chat": ChatExample,
            "streaming": True,
        }
        QueryParams = {"stream": True}

    class Delete:
        """Represents the DELETE operation for deleting a chat."""

        Response = {"message": "chat deleted"}


class Chats:
    """Represents a collection of chats with various operations."""

    class Get:
        """Represents the GET operation for retrieving chats."""

        QueryParams = {"thread_id": Uuid}
        Response = {"chats": [ChatExample]}
        NotFound = {"message": "thread not found"}

    class Delete:
        """Represents the DELETE operation for deleting chats."""

        Body = {"thread_id": Uuid}
        Response = {"message": "all messages deleted"}
        NotFound = {"message": "chat not found"}


class Thread:
    """Represents a thread object with various operations."""

    class Delete:
        """Represents the DELETE operation for deleting a thread."""

        Response = {"message": "thread deleted"}

    class Get:
        """Represents the GET operation for retrieving a thread."""

        Response = ThreadExample

    class Post:
        """Represents the POST operation for creating a thread."""

        Body = {"title": "Jollof Rice Recipe"}
        Response = {"message": "thread created", "thread": ThreadExample}

    class Patch:
        """Represents the PATCH operation for updating a thread."""

        Body = {"title": "Jollof Rice Recipe"}
        Response = {"message": "thread updated", "thread": ThreadExample}

    NotFound = {"message": "thread not found"}


class Threads:
    """Represents a collection of threads with various operations."""

    class Get:
        """Represents the GET operation for retrieving threads."""

        Response = {"threads": [ThreadExample, ThreadExample]}

    class Delete:
        """Represents the DELETE operation for deleting threads."""

        Response = {"message": "all threads deleted"}
