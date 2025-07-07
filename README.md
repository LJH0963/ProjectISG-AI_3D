# 🎮 ProjectISG-AI_3D

**ProjectISG-AI_3D**는 게임 제작 시 높은 시간과 비용이 요구되는 **게임 아이콘 이미지 및 3D Textured Mesh 생성** 작업을 자동화하는 것을 목표로 합니다. 사용자는 텍스트 기반의 간단한 입력만으로 고퀄리티의 2D 이미지와 이를 기반으로 한 GLB 3D 모델까지 획득할 수 있으며, 이 과정은 Streamlit 웹페이지 또는 Discord Bot의 형태로 쉽게 이루어집니다.

📎 **[최종 발표 자료 보기(Canva)](https://www.canva.com/design/DAGpFri1Psc/8Qdu-G4EM12JpsM9bEOmXg/view?utm_content=DAGpFri1Psc&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h09cc5a9eb8)**

📎 **[시연 영상 보기](https://drive.google.com/file/d/16N3IIfTrkOFcfqBd9p5oeqGPh-f5a1jY/view?usp=drive_link)**

---

## 🚀 목표

- 게임 아이콘 제작 및 3D Mesh 생성 과정을 **자동화**하여 인력 비용 및 제작 시간을 절감
- LLM과 ComfyUI 기반 생성 모델을 연계하여 **간편한 프론트엔드 UX 제공**
- Web UI(Streamlit) 또는 Discord Bot을 통한 **멀티 채널 접근성 제공**

---

## 🤖 Discord Bot 동작 예시

아래는 **Discord**를 통해 프롬프트를 입력하고, **3D 에셋**이 자동으로 생성되는 모습입니다.

![Discord Demo](asset/Demo.gif)

---

## 📌 선행 조건

- ✅ **ComfyUI Portable** 설치 필요 (Windows, Linux 모두 가능)
- ✅ **MVAdapter** 설치(Linux 기준 빌드):
  - GitHub: [https://github.com/huanngzh/ComfyUI-MVAdapter](https://github.com/huanngzh/ComfyUI-MVAdapter)
  - 제공된 **노드 워크플로우 예시**를 기준으로 실행
  - **CUDA 11.8** 환경에서 빌드됨
- ✅ **Hunyuan 3D v2.0 ComfyUI** 설치(Windows 기준 빌드):
  - GitHub: [https://github.com/niknah/ComfyUI-Hunyuan-3D-2](https://github.com/niknah/ComfyUI-Hunyuan-3D-2)
  - 제공된 **노드 워크플로우 예시**를 기준으로 실행
  - **CUDA 12.6** 환경에서 빌드됨

---

## 🤩 주요 기능

- 프롬프트 기반 이미지 생성 (ComfyUI + FastAPI)
- 생성된 2D 바탕의 Multiview 텍스처 이미지 생성 (MVAdapter)
- 생성된 front/back/left 이미지를 GLB 3D 모델 생성 (Hunyuan 3D v2.0)
- Streamlit을 통한 전체 파이프라인 실행 (GUI 기반, ComfyUI Prompt 형태)
- Discord Bot을 통한 채팅 기반 2D → 3D 생성 흐름 제공(LLM 결합)

---

## 🛠 사용 기술 스택

| 분야       | 사용 기술                                           |
| -------- | ----------------------------------------------- |
| Frontend | Streamlit, Discord Bot                          |
| Backend  | FastAPI, Python                                 |
| AI 모델    | ComfyUI (Portable), Hunyuan 3D v2.0, MV-Adapter |
| 환경 설정    | `core/config.py` 기반 설정 파일 관리                    |

---

## 🏠 프로젝트 구조

```
📁 ProjectISG-AI_3D
├── core/
│   └── config.py         # 환경 변수 설정 모듈
├── asset/
│   └── Demo.gif          # Discord 실행 Demo 영상
├── output/               # 생성 이미지 저장 경로
├── tmp/                  # 업로드 파일 임시 저장 경로
├── comfy_mv_api.py       # ComfyUI 프롬프트 이미지 + 텍스처 생성 서버
├── hy3d_api.py           # 3면 이미지 → GLB 생성 FastAPI 서버
├── stream2.py            # 전체 파이프라인을 실행하는 Streamlit 앱
├── discord_bot.py        # Discord 봇 명령어로 자동 생성
├── LICENSE
├── README.md
└── requirements.txt      # 의존성 리스트
```

---

## 🧬 세부 프로세스 설명

### 1. comfy_mv_api.py

- `POST /generate`: 프롬프트 기반 이미지 생성 (ComfyUI 워크플로우 트리거)
- `POST /generate_mv_adapter`: 생성된 이미지 기반 텍스처 생성 (MVAdapter 실행)

### 2. hy3d_api.py

- `POST /generate_hy3d`: front/back/left 이미지를 업로드하면 GLB 3D 모델 생성

### 3. stream2.py

- Streamlit 기반 웹 UI 구성
- 프롬프트 입력 → 2) 텍스처 생성 → 3) 3면 이미지 업로드 → 4) GLB 다운로드 순차 실행

### 4. discord_bot.py

- Discord 명령어: `!3d <프롬프트>` 실행 시 전체 파이프라인 자동 수행
- 프롬프트 변환 → 이미지 생성 → 텍스처 생성 → GLB 생성 → 결과 파일 첨부 응답

---

## 📡 API 명세 요약

| Method | Endpoint               | 설명                       |
| ------ | ---------------------- | ------------------------ |
| POST   | `/generate`            | 프롬프트 기반 이미지 생성 (MV)      |
| POST   | `/generate_mv_adapter` | 텍스처용 이미지 생성              |
| POST   | `/generate_hy3d`       | front/back/left → GLB 생성 |

---

## ⚙ 실행 방법

```bash
# 환경 설정 파일 열기 및 수정
# [core/config.py] 파일을 텍스트 에디터(VSCode 등)로 열어 환경값을 입력/수정합니다.

# 가상환경 설치 및 의존성 설치
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 서버 실행 (포트를 자유롭게 지정 가능)
uvicorn comfy_mv_api:app --host 0.0.0.0 --port {yourport} --reload
uvicorn hy3d_api:app --host 0.0.0.0 --port {yourport} --reload

# Streamlit 앱 실행
streamlit run stream2.py --server.address 0.0.0.0 --server.port {yourport}

# Discord 봇 실행
python discord_bot.py
```

---

## 💭 프로젝트 회고 및 느낀 점

- Streamlit / Discord 멀티 채널 연동을 통한 UX 확장이 매우 효과적이었음
- 기존 수작업 대비 자동화 파이프라인 도입으로 효율성과 생산성 향상 체감
- 프롬프트 기반의 UX를 통해 디자이너/비개발자와 협업 접근성 높임

---

## 🔮 향후 발전 및 확장 방안

- WebSocket 기반 실시간 생성 상태 모니터링 추가
- FBX 등 다양한 모델 포맷으로의 변환 지원
- 캐릭터 애니메이션 자동 생성 기능 연동 - Business Model로의 확장 가능성
- 프롬프트 추천 및 세분화 기능 추가

---

## 🤝 협업 및 기여 전략

- 설정은 `core/config.py` 모듈로 통일되며, 모든 경로 및 서버 포트는 해당 파일에서 일관되게 관리됩니다.
- 비개발자나 디자이너도 접근 가능하도록 **Streamlit 웹 UI**와 **Discord 봇 명령어**를 모두 제공하여 편의성과 진입 장벽을 낮추고자 했습니다.
- 프론트엔드 없이도 텍스트 프롬프트만으로 3D 에셋을 생성할 수 있도록, UX 단에서의 **직관성과 간편함**을 우선시하여 구성되었습니다.
