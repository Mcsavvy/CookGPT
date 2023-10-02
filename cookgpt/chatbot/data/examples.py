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


class Chat:
    class Get:
        Response = ChatExample
        NotFound = {"message": "chat not found"}

    class Post:
        Body = {
            "query": Query,
        }
        Response = {
            "chat": ChatExample,
            "streaming": True,
        }
        QueryParams = {"stream": True}

    class Delete:
        Response = {"message": "chat deleted"}


class Chats:
    class Get:
        Response = {"chats": [ChatExample]}
        NotFound = {"message": "thread not found"}

    class Delete:
        Response = {"message": "all messages deleted"}
        NotFound = {"message": "thread not found"}
