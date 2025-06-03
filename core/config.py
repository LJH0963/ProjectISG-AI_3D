import os
from dotenv import load_dotenv

# ✅ .env 파일 로드
load_dotenv()

# ✅ DISCORD 설정
DISCORD_TOKEN = os.getenv("DISCORD_API_KEY")

# ✅ 3D 경로 설정
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
OUTPUT_3D_DIR = os.path.join(OUTPUT_DIR, "3D")
MVADAPTER_SERVER = os.getenv("MVADAPTER_SERVER")
HY3D_SERVER = os.getenv("HY3D_SERVER")
PROMPT_CONVERT_API = os.getenv("PROMPT_CONVERT_API")