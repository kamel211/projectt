from fastapi import APIRouter, UploadFile, File, Depends, Body
from fastapi.responses import JSONResponse
from Controller.chat_controller import handle_file_upload, verify_token, get_chats, fetch_messages, send_text_message
from pydantic import BaseModel



router = APIRouter(prefix="/chat")

# ===== Pydantic model للرسالة =====

class MessagePayload(BaseModel):
    receiver_id: str
    message: str
    type: str = "text"  # افتراضي نص

# ===== Upload file =====
@router.post("/upload_file/{other_id}")
async def upload_file(other_id: str, file: UploadFile = File(...), token: str = Depends(verify_token)):
    user_id = token["id"]
    file_data = await file.read()
    result = await handle_file_upload(user_id, other_id, file_data, file.filename)
    return JSONResponse(result)

# ===== Send text message =====

# ===== Send text message =====
@router.post("/send")
async def send_message(payload: MessagePayload = Body(...), token: str = Depends(verify_token)):
    user_id = token["id"]
    receiver_id = payload.receiver_id
    message = payload.message
    result = send_text_message(user_id, receiver_id, message)
    return JSONResponse(result)

@router.get("/list")
async def list_chats(token: dict = Depends(verify_token)):
    user_id = token["id"]
    return JSONResponse(get_chats(user_id))



@router.get("/messages/{other_id}")
async def messages(other_id: str, token: str = Depends(verify_token)):
    user_id = token["id"]
    return JSONResponse(fetch_messages(user_id, other_id))
