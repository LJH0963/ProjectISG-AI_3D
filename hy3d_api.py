from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import tempfile
import os
import json
import time
import glob
from urllib import request as urlrequest
from dotenv import load_dotenv
load_dotenv()

# =========================
# 설정
# =========================

# ComfyUI 프롬프트 서버 주소
comfy_ip = "127.0.0.1:8188"

# GLB 저장 위치
output_dir = os.getenv("OUTPUT_3D_DIR", "output")
os.makedirs(output_dir, exist_ok=True)

TMP_DIR = "tmp"
os.makedirs(TMP_DIR, exist_ok=True)

# =========================
# FastAPI 앱 설정
# =========================

app = FastAPI()
app.mount("/files", StaticFiles(directory=os.path.join(output_dir, "3D")), name="files")

# =========================
# 유틸 함수
# =========================

def save_upload_file(upload_file: UploadFile, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix, dir=TMP_DIR)
    with os.fdopen(fd, "wb") as f:
        f.write(upload_file.file.read())
    return path

def queue_prompt(prompt_workflow: dict, ip: str) -> str:
    data = json.dumps({"prompt": prompt_workflow}).encode("utf-8")
    req = urlrequest.Request(f"http://{ip}/prompt", data=data)
    res = urlrequest.urlopen(req)
    return json.loads(res.read().decode("utf-8"))['prompt_id']

def check_progress(prompt_id: str, ip: str) -> dict:
    while True:
        req = urlrequest.Request(f"http://{ip}/history/{prompt_id}")
        res = urlrequest.urlopen(req)
        history = json.loads(res.read().decode("utf-8"))
        if prompt_id in history:
            return history[prompt_id]
        time.sleep(3)

# ---------------------------
# Hy3D 워크플로우 생성 함수
# ---------------------------

def generate_hy3d_workflow(front_img: str, back_img: str, left_img: str) -> dict:
    return {
        "10": {
            "inputs": {
                "model": "hunyuan3d-dit-v2-0-fp16.safetensors",
                "attention_mode": "sdpa",
                "cublas_ops": False
            },
            "class_type": "Hy3DModelLoader",
            "_meta": {
                "title": "Hy3DModelLoader"
            }
        },
        "17": {
            "inputs": {
                "filename_prefix": "3D/Hy3D",
                "file_format": "glb",
                "save_file": True,
                "trimesh": [
                    "203",
                    0
            ]
            },
            "class_type": "Hy3DExportMesh",
            "_meta": {
                "title": "Hy3DExportMesh"
            }
        },
        "28": {
            "inputs": {
            "model": "hunyuan3d-delight-v2-0"
            },
            "class_type": "DownloadAndLoadHy3DDelightModel",
            "_meta": {
            "title": "(Down)Load Hy3D DelightModel"
            }
        },
        "35": {
            "inputs": {
            "steps": 50,
            "width": 512,
            "height": 512,
            "cfg_image": 1,
            "seed": 0,
            "delight_pipe": [
                "28",
                0
            ],
            "image": [
                "64",
                0
            ],
            "scheduler": [
                "148",
                0
            ]
            },
            "class_type": "Hy3DDelightImage",
            "_meta": {
            "title": "Hy3DDelightImage"
            }
        },
        "45": {
            "inputs": {
            "images": [
                "35",
                0
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "이미지 미리보기"
            }
        },
        "52": {
            "inputs": {
            "width": 518,
            "height": 518,
            "interpolation": "lanczos",
            "method": "pad",
            "condition": "always",
            "multiple_of": 2,
            "image": [
                "157",
                0
            ]
            },
            "class_type": "ImageResize+",
            "_meta": {
            "title": "🔧 Image Resize"
            }
        },
        "55": {
            "inputs": {
            "mode": "base",
            "use_jit": True
            },
            "class_type": "TransparentBGSession+",
            "_meta": {
            "title": "🔧 InSPyReNet TransparentBG"
            }
        },
        "56": {
            "inputs": {
            "rembg_session": [
                "55",
                0
            ],
            "image": [
                "52",
                0
            ]
            },
            "class_type": "ImageRemoveBackground+",
            "_meta": {
            "title": "🔧 Image Remove Background"
            }
        },
        "61": {
            "inputs": {
            "camera_azimuths": "0, 90, 180, 270, 0, 180",
            "camera_elevations": "0, 0, 0, 0, 90, -90",
            "view_weights": "1, 0.1, 0.5, 0.1, 0.05, 0.05",
            "camera_distance": 1.45,
            "ortho_scale": 1.2
            },
            "class_type": "Hy3DCameraConfig",
            "_meta": {
            "title": "Hy3D Camera Config"
            }
        },
        "64": {
            "inputs": {
            "x": 0,
            "y": 0,
            "resize_source": False,
            "destination": [
                "184",
                0
            ],
            "source": [
                "166",
                1
            ],
            "mask": [
                "166",
                2
            ]
            },
            "class_type": "ImageCompositeMasked",
            "_meta": {
            "title": "마스크된 이미지 합성"
            }
        },
        "79": {
            "inputs": {
            "render_size": 1024,
            "texture_size": 2048,
            "normal_space": "world",
            "trimesh": [
                "83",
                0
            ],
            "camera_config": [
                "61",
                0
            ]
            },
            "class_type": "Hy3DRenderMultiView",
            "_meta": {
            "title": "Hy3D Render MultiView"
            }
        },
        "83": {
            "inputs": {
            "trimesh": [
                "203",
                0
            ]
            },
            "class_type": "Hy3DMeshUVWrap",
            "_meta": {
            "title": "Hy3D Mesh UV Wrap"
            }
        },
        "85": {
            "inputs": {
            "model": "hunyuan3d-paint-v2-0"
            },
            "class_type": "DownloadAndLoadHy3DPaintModel",
            "_meta": {
            "title": "(Down)Load Hy3D PaintModel"
            }
        },
        "88": {
            "inputs": {
            "view_size": 512,
            "steps": 25,
            "seed": 1024,
            "denoise_strength": 1,
            "pipeline": [
                "85",
                0
            ],
            "ref_image": [
                "35",
                0
            ],
            "normal_maps": [
                "79",
                0
            ],
            "position_maps": [
                "79",
                1
            ],
            "camera_config": [
                "61",
                0
            ],
            "scheduler": [
                "149",
                0
            ]
            },
            "class_type": "Hy3DSampleMultiView",
            "_meta": {
            "title": "Hy3D Sample MultiView"
            }
        },
        "90": {
            "inputs": {
            "images": [
                "79",
                0
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "이미지 미리보기"
            }
        },
        "92": {
            "inputs": {
            "images": [
                "117",
                0
            ],
            "renderer": [
                "79",
                2
            ],
            "camera_config": [
                "61",
                0
            ]
            },
            "class_type": "Hy3DBakeFromMultiview",
            "_meta": {
            "title": "Hy3D Bake From Multiview"
            }
        },
        "98": {
            "inputs": {
            "texture": [
                "104",
                0
            ],
            "renderer": [
                "129",
                2
            ]
            },
            "class_type": "Hy3DApplyTexture",
            "_meta": {
            "title": "Hy3D Apply Texture"
            }
        },
        "99": {
            "inputs": {
            "filename_prefix": "3D/Hy3D_textured",
            "file_format": "glb",
            "save_file": True,
            "trimesh": [
                "98",
                0
            ]
            },
            "class_type": "Hy3DExportMesh",
            "_meta": {
            "title": "Hy3DExportMesh"
            }
        },
        "104": {
            "inputs": {
            "inpaint_radius": 3,
            "inpaint_method": "ns",
            "texture": [
                "129",
                0
            ],
            "mask": [
                "129",
                1
            ]
            },
            "class_type": "CV2InpaintTexture",
            "_meta": {
            "title": "CV2 Inpaint Texture"
            }
        },
        "111": {
            "inputs": {
            "images": [
                "88",
                0
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "Preview Image: Multiview results"
            }
        },
        "116": {
            "inputs": {
            "images": [
                "79",
                1
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "이미지 미리보기"
            }
        },
        "117": {
            "inputs": {
            "width": 2048,
            "height": 2048,
            "interpolation": "lanczos",
            "method": "stretch",
            "condition": "always",
            "multiple_of": 0,
            "image": [
                "88",
                0
            ]
            },
            "class_type": "ImageResize+",
            "_meta": {
            "title": "🔧 Image Resize"
            }
        },
        "125": {
            "inputs": {
            "images": [
                "92",
                0
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "Preview Image: Initial baked texture"
            }
        },
        "126": {
            "inputs": {
            "images": [
                "129",
                0
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "Preview Image: vertex inpainted texture"
            }
        },
        "127": {
            "inputs": {
            "images": [
                "104",
                0
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "Preview Image: fully inpainted texture"
            }
        },
        "129": {
            "inputs": {
            "texture": [
                "92",
                0
            ],
            "mask": [
                "92",
                1
            ],
            "renderer": [
                "92",
                2
            ]
            },
            "class_type": "Hy3DMeshVerticeInpaintTexture",
            "_meta": {
            "title": "Hy3D Mesh Vertice Inpaint Texture"
            }
        },
        "132": {
            "inputs": {
            "value": 0.8,
            "width": 512,
            "height": 512
            },
            "class_type": "SolidMask",
            "_meta": {
            "title": "단색 마스크"
            }
        },
        "133": {
            "inputs": {
            "mask": [
                "132",
                0
            ]
            },
            "class_type": "MaskToImage",
            "_meta": {
            "title": "마스크를 이미지로 변환"
            }
        },
        "138": {
            "inputs": {
            "mask": [
                "56",
                1
            ]
            },
            "class_type": "MaskPreview+",
            "_meta": {
            "title": "🔧 Mask Preview"
            }
        },
        "140": {
            "inputs": {
            "box_v": 1.01,
            "octree_resolution": 256,
            "num_chunks": 32000,
            "mc_level": 0,
            "mc_algo": "mc",
            "enable_flash_vdm": True,
            "force_offload": True,
            "vae": [
                "10",
                1
            ],
            "latents": [
                "166",
                0
            ]
            },
            "class_type": "Hy3DVAEDecode",
            "_meta": {
            "title": "Hy3D VAE Decode"
            }
        },
        "148": {
            "inputs": {
            "scheduler": "Euler A",
            "sigmas": "default",
            "pipeline": [
                "28",
                0
            ]
            },
            "class_type": "Hy3DDiffusersSchedulerConfig",
            "_meta": {
            "title": "Hy3D Diffusers Scheduler Config"
            }
        },
        "149": {
            "inputs": {
            "scheduler": "DPM++",
            "sigmas": "default",
            "pipeline": [
                "85",
                0
            ]
            },
            "class_type": "Hy3DDiffusersSchedulerConfig",
            "_meta": {
            "title": "Hy3D Diffusers Scheduler Config"
            }
        },
        "154": {
            "inputs": {
            "model_file": [
                "99",
                0
            ],
            "image": ""
            },
            "class_type": "Preview3D",
            "_meta": {
            "title": "3D 미리보기"
            }
        },
        "157": {
            "inputs": {
            "image": front_img
            },
            "class_type": "LoadImage",
            "_meta": {
            "title": "Load Image: Front"
            }
        },
        "159": {
            "inputs": {
            "image": back_img
            },
            "class_type": "LoadImage",
            "_meta": {
            "title": "Load Image: Back"
            }
        },
        "160": {
            "inputs": {
            "image": left_img
            },
            "class_type": "LoadImage",
            "_meta": {
            "title": "Load Image: Left"
            }
        },
        "162": {
            "inputs": {
            "model_file": [
                "17",
                0
            ],
            "image": ""
            },
            "class_type": "Preview3D",
            "_meta": {
            "title": "3D 미리보기"
            }
        },
        "163": {
            "inputs": {
            "render_type": "normal",
            "render_size": 1024,
            "camera_type": "orth",
            "camera_distance": 1.45,
            "pan_x": 0,
            "pan_y": 0,
            "ortho_scale": 1.2,
            "azimuth": 146.666748046875,
            "elevation": 0,
            "bg_color": "128, 128, 255",
            "trimesh": [
                "203",
                0
            ]
            },
            "class_type": "Hy3DRenderSingleView",
            "_meta": {
            "title": "Hy3D Render SingleView"
            }
        },
        "166": {
            "inputs": {
            "guidance_scale": 5.5,
            "steps": 30,
            "seed": 416935455784444,
            "scheduler": "FlowMatchEulerDiscreteScheduler",
            "pipeline": [
                "10",
                0
            ],
            "front": [
                "195",
                0
            ],
            "left": [
                "196",
                0
            ],
            "back": [
                "198",
                0
            ]
            },
            "class_type": "Hy3DGenerateMeshMultiView",
            "_meta": {
            "title": "Hy3DGenerateMeshMultiView"
            }
        },
        "170": {
            "inputs": {
            "rembg_session": [
                "55",
                0
            ],
            "image": [
                "171",
                0
            ]
            },
            "class_type": "ImageRemoveBackground+",
            "_meta": {
            "title": "🔧 Image Remove Background"
            }
        },
        "171": {
            "inputs": {
            "width": 518,
            "height": 518,
            "interpolation": "lanczos",
            "method": "pad",
            "condition": "always",
            "multiple_of": 2,
            "image": [
                "160",
                0
            ]
            },
            "class_type": "ImageResize+",
            "_meta": {
            "title": "🔧 Image Resize"
            }
        },
        "174": {
            "inputs": {
            "mask": [
                "170",
                1
            ]
            },
            "class_type": "MaskPreview+",
            "_meta": {
            "title": "🔧 Mask Preview"
            }
        },
        "176": {
            "inputs": {
            "width": 518,
            "height": 518,
            "interpolation": "lanczos",
            "method": "pad",
            "condition": "always",
            "multiple_of": 2,
            "image": [
                "159",
                0
            ]
            },
            "class_type": "ImageResize+",
            "_meta": {
            "title": "🔧 Image Resize"
            }
        },
        "177": {
            "inputs": {
            "rembg_session": [
                "55",
                0
            ],
            "image": [
                "176",
                0
            ]
            },
            "class_type": "ImageRemoveBackground+",
            "_meta": {
            "title": "🔧 Image Remove Background"
            }
        },
        "178": {
            "inputs": {
            "mask": [
                "177",
                1
            ]
            },
            "class_type": "MaskPreview+",
            "_meta": {
            "title": "🔧 Mask Preview"
            }
        },
        "182": {
            "inputs": {
            "images": [
                "166",
                1
            ]
            },
            "class_type": "PreviewImage",
            "_meta": {
            "title": "이미지 미리보기"
            }
        },
        "183": {
            "inputs": {
            "mask": [
                "166",
                2
            ]
            },
            "class_type": "MaskPreview+",
            "_meta": {
            "title": "🔧 Mask Preview"
            }
        },
        "184": {
            "inputs": {
            "amount": [
                "185",
                0
            ],
            "image": [
                "133",
                0
            ]
            },
            "class_type": "RepeatImageBatch",
            "_meta": {
            "title": "이미지 반복 배치 생성"
            }
        },
        "185": {
            "inputs": {
            "batch": [
                "166",
                1
            ]
            },
            "class_type": "BatchCount+",
            "_meta": {
            "title": "🔧 Batch Count"
            }
        },
        "195": {
            "inputs": {
            "image": [
                "52",
                0
            ],
            "alpha": [
                "202",
                0
            ]
            },
            "class_type": "JoinImageWithAlpha",
            "_meta": {
            "title": "알파와 함께 이미지 결합"
            }
        },
        "196": {
            "inputs": {
            "image": [
                "171",
                0
            ],
            "alpha": [
                "199",
                0
            ]
            },
            "class_type": "JoinImageWithAlpha",
            "_meta": {
            "title": "알파와 함께 이미지 결합"
            }
        },
        "198": {
            "inputs": {
            "image": [
                "176",
                0
            ],
            "alpha": [
                "201",
                0
            ]
            },
            "class_type": "JoinImageWithAlpha",
            "_meta": {
            "title": "알파와 함께 이미지 결합"
            }
        },
        "199": {
            "inputs": {
            "mask": [
                "170",
                1
            ]
            },
            "class_type": "InvertMask",
            "_meta": {
            "title": "마스크 반전"
            }
        },
        "201": {
            "inputs": {
            "mask": [
                "177",
                1
            ]
            },
            "class_type": "InvertMask",
            "_meta": {
            "title": "마스크 반전"
            }
        },
        "202": {
            "inputs": {
            "mask": [
                "56",
                1
            ]
            },
            "class_type": "InvertMask",
            "_meta": {
            "title": "마스크 반전"
            }
        },
        "203": {
            "inputs": {
            "remove_floaters": True,
            "remove_degenerate_faces": True,
            "reduce_faces": True,
            "max_facenum": 50000,
            "smooth_normals": False,
            "trimesh": [
                "140",
                0
            ]
            },
            "class_type": "Hy3DPostprocessMesh",
            "_meta": {
            "title": "Hy3D Postprocess Mesh"
            }
        },
        "204": {
            "inputs": {
            "INPUT_mesh_key": [
                "99",
                0
            ],
            "filename_prefix": "mesh/ComfyUI"
            },
            "class_type": "SaveGLB_motorway_edition",
            "_meta": {
            "title": "SaveGLB_motorway_edition"
            }
        }
        }

# ---------------------------
# Hy3D 실행 API
# ---------------------------

@app.post("/generate_hy3d")
async def generate_hy3d(
    front: UploadFile = File(...),
    back: UploadFile = File(...),
    left: UploadFile = File(...)
):
    try:
        # 업로드된 파일 저장
        front_img = save_upload_file(front, ".png")
        back_img = save_upload_file(back, ".png")
        left_img = save_upload_file(left, ".png")

        # 워크플로우 생성 및 실행
        prompt_workflow = generate_hy3d_workflow(front_img, back_img, left_img)
        prompt_id = queue_prompt(prompt_workflow, comfy_ip)
        _ = check_progress(prompt_id, comfy_ip)

        # 최신 GLB 파일 반환
        glb_files = glob.glob(os.path.join(output_dir, "3D", "Hy3D_textured*.glb"))
        glb_files.sort(key=os.path.getmtime, reverse=True)
        if not glb_files:
            raise HTTPException(status_code=404, detail="Hy3D GLB 파일을 찾을 수 없습니다.")

        return FileResponse(
            glb_files[0],
            filename=os.path.basename(glb_files[0]),
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for f in [front_img, back_img, left_img]:
            if os.path.exists(f):
                os.remove(f)