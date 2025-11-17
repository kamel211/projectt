from fastapi import HTTPException, Header
from database import messages_collection
from datetime import datetime
import os
from cryptography.fernet import Fernet
from io import BytesIO
from PIL import Image
import jwt
from fastapi import Header, HTTPException
from jwt import PyJWTError

# إعداد التشفير
SECRET_KEY_FILE = "fernet.key"
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "rb") as f:
        SECRET_KEY = f.read()
else:
    from cryptography.fernet import Fernet
    SECRET_KEY = Fernet.generate_key()
    with open(SECRET_KEY_FILE, "wb") as f:
        f.write(SECRET_KEY)
cipher = Fernet(SECRET_KEY)

UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ================== Token Verification ==================

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"

def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token_value = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalid")
        return {"id": user_id}
    except PyJWTError:
        raise HTTPException(status_code=401, detail="Token invalid")


# ================== Encryption Helpers ==================
def encrypt_text(text: str) -> bytes:
    return cipher.encrypt(text.encode())

def encrypt_bytes(data: bytes) -> bytes:
    return cipher.encrypt(data)

def decrypt_bytes(data: bytes) -> bytes:
    return cipher.decrypt(data)

def is_image_file(file_data: bytes) -> bool:
    try:
        Image.open(BytesIO(file_data))
        return True
    except:
        return False

# ================== رفع الملفات ==================
async def handle_file_upload(user_id: str, other_id: str, file_data: bytes, filename: str):
    timestamp = datetime.utcnow()
    is_image = is_image_file(file_data)

    user_folder = os.path.join(UPLOAD_FOLDER, user_id, other_id)
    os.makedirs(user_folder, exist_ok=True)

    unique_filename = f"{filename}"
    file_path = os.path.join(user_folder, unique_filename)
    with open(file_path, "wb") as f:
        f.write(encrypt_bytes(file_data))

    messages_collection.insert_one({
        "sender_id": user_id,
        "receiver_id": other_id,
        "message_text": file_path if not is_image else "",  # نص أو مسار
        "type": "image" if is_image else "file",
        "filename": unique_filename,
        "timestamp": timestamp,
        "delivered": False
    })

    return {
        "status": "success",
        "filename": unique_filename,
        "type": "image" if is_image else "file",
        "preview": f"/chat/preview/{user_id}/{other_id}/{unique_filename}" if is_image else None,
        "timestamp": str(timestamp)
    }

# ================== Send Text Message ==================
def send_text_message(sender_id: str, receiver_id: str, text: str):
    timestamp = datetime.utcnow()
    messages_collection.insert_one({
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "message_text": text,
        "type": "text",
        "filename": None,
        "timestamp": timestamp,
        "delivered": False
    })
    return {
        "status": "success",
        "message_text": text,
        "type": "text",
        "timestamp": str(timestamp)
    }

# ================== Fetch Messages ==================
def fetch_messages(user_id: str, other_id: str):
    msgs = list(messages_collection.find(
        {"$or": [
            {"sender_id": user_id, "receiver_id": other_id},
            {"sender_id": other_id, "receiver_id": user_id}
        ]}
    ).sort("timestamp", 1))  # ترتيب حسب الوقت
    result = []
    for m in msgs:
        preview = f"/chat/preview/{m['sender_id']}/{m['receiver_id']}/{m['filename']}" if m['type'] == 'image' else None
        result.append({
            "sender_id": m["sender_id"],
            "receiver_id": m["receiver_id"],
            "message_text": m["message_text"],
            "type": m["type"],
            "filename": m["filename"],
            "preview": preview,
            "timestamp": str(m["timestamp"])
        })
    return result

# ================== List Chats ==================
def get_chats(user_id: str):
    pipeline = [
        {"$match": {"$or": [{"sender_id": user_id}, {"receiver_id": user_id}]}},
        {"$sort": {"timestamp": -1}},
        {"$group": {
            "_id": {"chat_with": {"$cond": [{"$eq": ["$sender_id", user_id]}, "$receiver_id", "$sender_id"]}},
            "lastMessage": {"$first": "$message_text"},
            "type": {"$first": "$type"},
            "filename": {"$first": "$filename"},
            "chat_with_id": {"$first": {"$cond": [{"$eq": ["$sender_id", user_id]}, "$receiver_id", "$sender_id"]}},
            "timestamp": {"$first": "$timestamp"}
        }},
        {"$sort": {"timestamp": -1}}
    ]
    chats = list(messages_collection.aggregate(pipeline))
    return [
        {
            "chat_with": c["_id"]["chat_with"],
            "chat_with_id": c["chat_with_id"],
            "lastMessage": c["lastMessage"],
            "type": c["type"],
            "filename": c["filename"],
            "timestamp": str(c["timestamp"])
        }
        for c in chats
    ]
