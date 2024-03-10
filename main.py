import os
import sys
import logging
import json

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, BackgroundTasks


app = FastAPI(debug=True)
load_dotenv()
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)


VERIFY_TOKEN = os.environ["VERIFY_TOKEN"]
FB_APP_TOKEN = os.environ["FB_APP_TOKEN"]
TOKEN_ENDPOINT = os.environ["TOKEN_ENDPOINT"]
DIRECTLINE_URL = os.environ["DIRECTLINE_URL"]
FB_GRAPH_URL = os.environ["FB_GRAPH_URL"]


@app.get("/api/webhook")
async def verify(request: Request):
    """
    On webook verification VERIFY_TOKEN has to match the token at the
    configuration and send back "hub.challenge" as success.
    """
    if request.query_params.get("hub.mode") == "subscribe" and request.query_params.get("hub.challenge"):
        if (not request.query_params.get("hub.verify_token") == VERIFY_TOKEN):
            return Response(content="Verification token mismatch", status_code=403)
        return Response(content=request.query_params["hub.challenge"])
    return Response(content="Required arguments haven't passed.", status_code=400)


@app.post("/api/webhook")
async def spagheti(request: Request, background_task: BackgroundTasks):
    """Handle incoming webhook messages with spagheti code hehehee"""

    def _get_directline_token() -> dict:
        try:
            response = requests.get(TOKEN_ENDPOINT, timeout=30)
            response.raise_for_status()
            return {"directline_token": response.json()["token"]}
        except requests.exceptions.RequestException as e:
            logging.error(e)
            raise e

    def _start_conversation(directline_token: str) -> dict:
        try:
            headers = {"Authorization": f"Bearer {directline_token}"}
            response = requests.post(f"{DIRECTLINE_URL}/directline/conversations", headers=headers, timeout=30)
            response.raise_for_status()
            return {"conversation_id": response.json()["conversationId"], "conversation_token": response.json()["token"]}
        except requests.exceptions.RequestException as e:
            logging.error(e)
            raise e

    def _send_message(conversation_id: str, user_id: str, message: str, conversation_token: str) -> dict:
        try:
            headers = {"Authorization": f"Bearer {conversation_token}"}
            body = {
                "locale": "en-EN",
                "type": "message",
                "from": {
                        "id": user_id
                },
                "text": message
            }
            response = requests.post(f"{DIRECTLINE_URL}/directline/conversations/{conversation_id}/activities",
                                     headers=headers, json=body, timeout=30)
            response.raise_for_status()
            return {"activity_id": response.json()["id"]}
        except requests.exceptions.RequestException as e:
            logging.error(e)
            raise e

    def _get_activities(conversation_id: str, conversation_token: str) -> dict:
        try:
            headers = {"Authorization": f"Bearer {conversation_token}"}
            response = requests.get(
                f"{DIRECTLINE_URL}/directline/conversations/{conversation_id}/activities", headers=headers, timeout=30)
            response.raise_for_status()
            last_activity_type = response.json()["activities"][-1]["type"]
            try:
                role = response.json()["activities"][-1]["from"]["role"]
            except KeyError as e:
                logging.error(f"no role here, error: {e}")
                role = "user"

            bot_res = ""
            if last_activity_type == "message" and role == "bot":
                bot_res = response.json()["activities"][-1]["text"]
                bot_res = bot_res.replace("'", "")
            return {"last_activity_type": last_activity_type, "role": role, "bot_res": bot_res}
        except requests.exceptions.RequestException as e:
            logging.error(e)
            raise e

    def _send_fb_message(message: str, page_id: str, user_id: str, app_token: str) -> dict:
        try:
            headers = {"Content-Type": "application/json"}
            body = json.dumps({"recipient": {"id": user_id}, "message": {"text": message}})
            url = f"{FB_GRAPH_URL}/{page_id}/messages?messaging_type=RESPONSE&access_token={app_token}"
            response = requests.post(url, data=body, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(e)
            raise e

    def full_flow(json_req: Request) -> str:
        user_mess = json_req["entry"][0]["messaging"][0]["message"]["text"]
        user_id = json_req["entry"][0]["messaging"][0]["sender"]["id"]
        page_id = json_req["entry"][0]["messaging"][0]["recipient"]["id"]
        logging.debug({"user_mess": user_mess, "user_id": user_id, "page_id": page_id})
        directline_token = _get_directline_token()
        conversation_id = _start_conversation(directline_token["directline_token"])
        _send_message(conversation_id["conversation_id"], user_id, user_mess, conversation_id["conversation_token"])
        while True:
            last_activity = _get_activities(conversation_id["conversation_id"], conversation_id["conversation_token"])
            if last_activity["last_activity_type"] == "message" and last_activity["role"] == "bot":
                break

        if last_activity["last_activity_type"] == "message" and last_activity["role"] == "bot":
            _send_fb_message(last_activity["bot_res"], page_id, user_id, FB_APP_TOKEN)

    req = await request.json()
    background_task.add_task(full_flow, req)
    return "OK"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
