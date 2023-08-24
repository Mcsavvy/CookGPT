"""Openapi Specification Docs"""

# ruff: noqa

APP = """Welcome to the Cookgpt API documentation! This documentation provides detailed information on how to integrate with the Cookgpt API, which powers an AI-powered health assistance service.

The API allows you to perform various actions such as user authentication, managing user information, and interacting with the AI chat functionality.

The API is organized around REST. Our API has predictable resource-oriented URLs, accepts JSON-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs."""


SECURITY = """The API incorporates a secure authentication mechanism using JSON Web Tokens (JWT). To access user-specific functionalities, such as managing personal information and interacting with the AI chat functionality, you need to include a JWT bearer token in the `Authorization` header of your API requests.

Include the user's authentication token in the `Authorization` header of the request. The header should be in the following format

```
Authorization: Bearer <authentication-token>
```"""


AUTH = """This section contains information about user authentication and user management."""


AUTH_LOGIN = """Use this endpoint to authenticate a user and get authentication info. This endpoint returns an access token and a refresh token. The access token is used to authenticate the user for a limited time. The refresh token is used to get a new access token when the old one expires via the `/auth/refresh` endpoint.

The expiry time of  both tokens are also returned. If the refresh token expires, the user will have to login again. Use the expiry to check and refresh the access token before it expires.

The access token should be sent in the **Authorization** header as a `Bearer` token for all requests that require authentication.

The `user_type` field is used to determine the type of user that is logged in. This can be used to determine the permissions of the user."""


AUTH_REFRESH = """Use this endpoint to refresh an access token. The access token is used to authenticate the user for a limited time. The refresh token is used to get a new access token when the old one expires. 

The refresh token should be sent in the **Authorization** header as a `Bearer` token for all requests that require authentication.

The output of this endpoint is similar to the `/auth/login` endpoint."""


AUTH_LOGOUT = """Use this endpoint to logout a user. This will invalidate the user's refresh token and access token. The user will have to login again to get a new authentication info."""


AUTH_SIGNUP = """Use this endpoint to register a new user. If an error occurs, the error message will be returned in the response body."""


CHAT = """The AI chat functionality allows users to interact with an AI-powered health assistant. The assistant can answer questions about health and wellness, and can also provide information about the user's health status.

Chats with the AI are organized into threads. Each thread has a unique ID that is used to identify the thread. The thread ID is used to get the chat messages in the thread, and to send messages to the thread.

Every user has a default thread which would be used for all interactions with the AI assistant.

> Subsequent versions of the API will allow users to create new threads and interact with the AI assistant in multiple threads.

---

Each user has a `max_chat_cost` which is the total number of tokens that he/she is allowed to spend on chats with the AI assistant. The cost of a chat is the number of tokens used in the query and the response.

> Subsequent versions of the API will allow users to purchase more tokens.

### Chat Memory Optimization
For now, the AI's memory has not been optimized and it remembers all chats that it has had with the user. This means that the AI's memory will grow linearly as the user interact with it. This will be fixed in subsequent versions of the API."""


CHAT_GET_CHATS = """Use this endpoint to get a list of all chats that the user has participated in. The chats are sorted in descending order of the last message sent in the chat."""


CHAT_DELETE_CHATS = """Use this endpoint to delete all chats in the thread. **This action cannot be undone**."""


CHAT_GET_CHAT = """Use this endpoint to get a specific chat in the thread. You need to specify the chat ID in the URL."""


CHAT_DELETE_CHAT = """Use this endpoint to delete a specific chat in the thread. **This action cannot be undone**. You need to specify the chat ID in the URL."""


CHAT_POST_CHAT = """Use this endpoint to send a message to the AI assistant. The message will be sent to the AI assistant and the response will be returned in the response body. The response will also be saved in the database.

If the user does not have enough tokens to send the message, a dummy response will be returned in the response body. Neither the query nor the dummy response will not be saved in the database.

> INFO: To identify a dummy response, check if the `cost` field is `0`."""
