import os
import time
import glob
import streamlit as st
import requests
import zipfile
import io
import shutil
from dotenv import load_dotenv
load_dotenv()

# 환경 변수 설정 및 불러오기
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
OUTPUT_IMAGE_FOLDER = OUTPUT_DIR
FASTAPI_STATIC_DIR = os.path.join(OUTPUT_IMAGE_FOLDER, "3D")  # FastAPI static 서빙 디렉토리
MVADAPTER_SERVER = os.getenv("MVADAPTER_SERVER")
HY3D_SERVER = os.getenv("HY3D_SERVER")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(FASTAPI_STATIC_DIR, exist_ok=True)

# Streamlit 시작
st.set_page_config(page_title="ComfyUI + MVAdapter REST", layout="centered")
st.title("🧊 이미지 기반 3D 생성기 (REST 연동 버전)")

# 세션 상태
if "image_path" not in st.session_state:
    st.session_state.image_path = None
if "glb_path" not in st.session_state:
    st.session_state.glb_path = None

# 유틸 함수
def find_latest_png(folder_path):
    png_files = glob.glob(os.path.join(folder_path, '*.png'))
    return max(png_files, key=os.path.getctime) if png_files else None

def find_latest_named_images(folder, name_keys):
    result = {}
    for key in name_keys:
        files = glob.glob(os.path.join(folder, f"*{key}*.png"))
        result[key] = max(files, key=os.path.getmtime) if files else None
    return result

def find_latest_glb(directory):
    glb_files = glob.glob(os.path.join(directory, "Hy3D_textured*.glb"))
    return os.path.basename(max(glb_files, key=os.path.getmtime)) if glb_files else None

def get_random_hex():
    return os.urandom(8).hex()

# Step 1. 프롬프트로 이미지 생성
st.header("1️⃣ 프롬프트로 이미지 생성")
prompt = st.text_input("✨ 프롬프트 입력", "a single pepper, vibrant red hot chili pepper")
negative = st.text_input("🚫 네거티브 프롬프트", "shadow")

if st.button("🚀 이미지 생성 요청"):
    with st.spinner("ComfyUI 서버 호출 중..."):
        try:
            res = requests.post(
                f"{MVADAPTER_SERVER}/generate",
                json={"user_prompt": prompt, "user_negative": negative}
            )
            if res.status_code == 200 and res.json().get("status") == "completed":
                time.sleep(2)
                st.session_state.image_path = find_latest_png(OUTPUT_IMAGE_FOLDER)
                st.success("✅ 이미지 생성 완료!")
            else:
                st.error("❌ 이미지 생성 실패 또는 서버 오류!")
        except Exception as e:
            st.error(f"예외 발생: {e}")

if st.session_state.image_path:
    st.image(st.session_state.image_path, caption="🖼 생성된 이미지", use_container_width=True)
    with open(st.session_state.image_path, "rb") as f:
        st.download_button("⬇️ 이미지 다운로드", f, file_name=os.path.basename(st.session_state.image_path), mime="image/png")

# Step 2. MVAdapter로 텍스처 이미지 생성
st.header("2️⃣ 텍스처 이미지 생성")
if st.session_state.image_path and st.button("🎨 텍스처 이미지 생성"):
    with st.spinner("MVAdapter 서버에 요청 중..."):
        try:
            image_filename = os.path.basename(st.session_state.image_path)
            res = requests.post(
                f"{MVADAPTER_SERVER}/generate_mv_adapter",
                json={"reference_filename": image_filename, "user_prompt": prompt}
            )

            if res.status_code == 200 and res.json().get("status") == "completed":
                st.success("✅ 텍스처 이미지 생성 완료!")
                named_imgs = find_latest_named_images(OUTPUT_IMAGE_FOLDER, ["front", "back", "left"])
                if all(named_imgs.values()):
                    cols = st.columns(3)
                    for idx, (name, path) in enumerate(named_imgs.items()):
                        with cols[idx]:
                            st.image(path, caption=name, use_container_width=True)

                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w") as zipf:
                        for name, path in named_imgs.items():
                            zipf.write(path, arcname=os.path.basename(path))
                    zip_buffer.seek(0)

                    st.download_button("⬇️ 텍스처 ZIP 다운로드", zip_buffer, file_name="texture_images.zip", mime="application/zip")
                else:
                    st.warning("⚠️ front/back/left 이미지 중 일부 누락")
            else:
                st.error("❌ 텍스처 생성 실패")
        except Exception as e:
            st.error(f"예외 발생: {e}")

# Step 3. 업로드한 이미지로 Hy3D GLB 생성 요청
st.header("3️⃣ 업로드 이미지로 GLB 생성")

uploaded_front = st.file_uploader("📤 Front 이미지", type=["png"], key="front")
uploaded_back = st.file_uploader("📤 Back 이미지", type=["png"], key="back")
uploaded_left = st.file_uploader("📤 Left 이미지", type=["png"], key="left")

if st.button("🧊 GLB 생성 요청"):
    if not (uploaded_front and uploaded_back and uploaded_left):
        st.error("❌❌❌ 모든 이미지(front/back/left)를 업로드해야 합니다. ❌❌❌")
    else:
        with st.spinner("Hy3D 서버 요청 중..."):
            try:
                files = {
                    "front": ("front.png", uploaded_front, "image/png"),
                    "back": ("back.png", uploaded_back, "image/png"),
                    "left": ("left.png", uploaded_left, "image/png")
                }

                res = requests.post(f"{HY3D_SERVER}/generate_hy3d", files=files)
                if res.status_code == 200:
                    # ▶️ GLB 파일명을 유니크하게 설정
                    unique_filename = f"Hy3D_textured_{get_random_hex()}.glb"
                    glb_path = os.path.join(FASTAPI_STATIC_DIR, unique_filename)

                    # ▶️ GLB 파일을 리눅스 서버 output/3D 경로에 저장
                    with open(glb_path, "wb") as f:
                        f.write(res.content)

                    st.session_state.glb_path = glb_path
                    st.success("✅ GLB 생성이 완료되었습니다!")

                    with open(glb_path, "rb") as f:
                        st.download_button("⬇️ GLB 다운로드", f, file_name=unique_filename, mime="application/octet-stream")
                else:
                    st.error(f"❌ GLB 생성 실패 (status code: {res.status_code})")
            except Exception as e:
                st.error(f"예외 발생: {e}")

# Step 4. 세션 초기화
if st.button("🔄 초기화"):
    st.session_state.clear()
    st.rerun()
