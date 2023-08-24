"""chatbot schema data examples."""


Response = "You should take some aspirin"
Query = "I have a headache"
DateTime = "2021-01-01 00:00:00"
Uuid = "36b51f8a-c9fa-43f8-92fa-ff6927736c10"


class Chat:
    In = {
        "content": Query,
        # "thread_id": Uuid,
    }
    Out = {
        "id": Uuid,
        "content": Query,
        "chat_type": "query",
        "cost": 0,
        "previous_chat_id": Uuid,
        "next_chat_id": Uuid,
        "sent_time": DateTime,
        "thread_id": Uuid,
    }


class GetChat:
    Out = {"chat": Chat.Out}
    NotFound = {"message": "chat not found"}


class DeleteChat:
    Out = {"message": "all messages deleted"}
    NotFound = {"message": "chat not found"}


class Chats:
    Out = {"chats": [Chat.Out, Chat.Out]}
