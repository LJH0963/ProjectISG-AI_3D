from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
from urllib import request as urlrequest
import time

# 환경 변수 로딩
from dotenv import load_dotenv
load_dotenv()

import os
os.environ["CUDA_VISIBLE_DEVICES"] = os.getenv("CUDA_DEVICE", "0")

app = FastAPI()
app.mount("/images", StaticFiles(directory="output"), name="images")

comfy_ip = "0.0.0.0:8190"  # ComfyUI 서버 주소
host_ip = os.getenv("MVADAPTER_SERVER")  # 일반 이미지 생성 및 MV_Adapter 서버 주소

class PromptInput(BaseModel):
    user_prompt: str
    user_negative: str

class MVAdapterInput(BaseModel):
    reference_filename: str  # generate()에서 생성된 이미지 파일명
    user_prompt: str

# 텍스트 기반 프롬프트 워크플로우 생성

def generate_prompt_text(user_prompt, user_negative: str) -> dict:
    return {
        "3": {
            "inputs": {
                "seed": 337089376345,
                "steps": 20,
                "cfg": 7,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": 1,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler",
            "_meta": {
                "title": "KSampler"
            }
        },
        "4": {
            "inputs": {
                "ckpt_name": "AnythingXL_xl.safetensors"
            },
            "class_type": "CheckpointLoaderSimple",
            "_meta": {
                "title": "Load Checkpoint"
            }
        },
        "5": {
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage",
            "_meta": {
                "title": "Empty Latent Image"
            }
        },
        "6": {
            "inputs": {
                "text": f"{user_prompt}, ctv, no humans, stylized, shiny surface, masterpiece, best quality, ultra-detailed, genshin impact style, fantasy style illustration, still life, solo, simple background, cel shading, anime rendering\n",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "7": {
            "inputs": {
                "text": f"{user_negative}, low quality, distorted tip, melted shape, blurry, broken parts, watercolor, extra leaf, human, text, doll, face, jack-o-lantern, carved, halloween, face, glowing from inside, spooky, scary\n",
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {
                "title": "CLIP Text Encode (Prompt)"
            }
        },
        "8": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            },
            "class_type": "VAEDecode",
            "_meta": {
                "title": "VAE Decode"
            }
        },
        "12": {
            "inputs": {
                "image": ["13", 0]
            },
            "class_type": "Image Remove Background (rembg)",
            "_meta": {
                "title": "Image Remove Background (rembg)"
            }
        },
        "13": {
            "inputs": {
                "image": ["8", 0]
            },
            "class_type": "AILab_ImagePreview",
            "_meta": {
                "title": "이미지 미리보기 (RMBG)"
            }
        },
        "9": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["12", 0]
            },
            "class_type": "SaveImage",
            "_meta": {
                "title": "Save Image"
            }
        }
    }

# MVAdapter 워크플로우 정적 정의 및 입력 이미지만 반영

def generate_mv_adapter_workflow(reference_image_filename, user_prompt : str) -> dict:
    workflow = {
      "1": {
        "inputs": {
          "ckpt_name": "sdXL_v10VAEFix.safetensors",
          "pipeline_name": "MVAdapterI2MVSDXLPipeline"
        },
        "class_type": "LdmPipelineLoader",
        "_meta": {
          "title": "LDM Pipeline Loader"
        }
      },
      "2": {
        "inputs": {
          "scheduler_name": "DDPM",
          "shift_snr": True,
          "shift_mode": "interpolated",
          "shift_scale": 8,
          "pipeline": ["1", 0]
        },
        "class_type": "DiffusersMVSchedulerLoader",
        "_meta": {
          "title": "Diffusers MV Scheduler Loader"
        }
      },
      "3": {
        "inputs": {
          "vae_name": "sdxl_vae.safetensors",
          "upcast_fp32": True
        },
        "class_type": "LdmVaeLoader",
        "_meta": {
          "title": "LDM Vae Loader"
        }
      },
      "4": {
        "inputs": {
          "load_mvadapter": True,
          "adapter_path": "huanngzh/mv-adapter",
          "adapter_name": "mvadapter_i2mv_sdxl_beta.safetensors",
          "num_views": 6,
          "enable_vae_slicing": True,
          "enable_vae_tiling": False,
          "pipeline": ["1", 0],
          "scheduler": ["2", 0],
          "autoencoder": ["3", 0]
        },
        "class_type": "DiffusersMVModelMakeup",
        "_meta": {
          "title": "Diffusers MV Model Makeup"
        }
      },
      "6": {
        "inputs": {
          "num_views": 6,
          "prompt": f"{user_prompt}, high quality",
          "negative_prompt": "watermark, ugly, deformed, noisy, blurry, low contrast",
          "width": 1024,
          "height": 1024,
          "steps": 50,
          "cfg": 3,
          "seed": 21,
          "controlnet_conditioning_scale": 1,
          "pipeline": ["4", 0],
          "reference_image": ["8", 0],
          "azimuth_degrees": ["13", 0]
        },
        "class_type": "DiffusersMVSampler",
        "_meta": {
          "title": "Diffusers MV Sampler"
        }
      },
      "7": {
        "inputs": {
          "image": f"/home/wanted-1/ComfyUI/output/{reference_image_filename}"
        },
        "class_type": "LoadImage",
        "_meta": {
          "title": "이미지 로드"
        }
      },
      "8": {
        "inputs": {
          "height": 1024,
          "width": 1024,
          "remove_bg_fn": ["9", 0],
          "image": ["7", 0]
        },
        "class_type": "ImagePreprocessor",
        "_meta": {
          "title": "Image Preprocessor"
        }
      },
      "9": {
        "inputs": {
          "ckpt_name": "ZhengPeng7/BiRefNet"
        },
        "class_type": "BiRefNet",
        "_meta": {
          "title": "BiRefNet"
        }
      },
      "10": {
        "inputs": {
          "images": ["8", 0]
        },
        "class_type": "PreviewImage",
        "_meta": {
          "title": "이미지 미리보기"
        }
      },
      "11": {
        "inputs": {
          "images": ["6", 0]
        },
        "class_type": "PreviewImage",
        "_meta": {
          "title": "이미지 미리보기"
        }
      },
      "12": {
        "inputs": {
          "filename_prefix": "ComfyUI",
          "images": ["6", 0]
        },
        "class_type": "SaveImage",
        "_meta": {
          "title": "이미지 저장"
        }
      },
      "13": {
        "inputs": {
          "front_view": True,
          "front_right_view": False,
          "right_view": False,
          "back_view": True,
          "left_view": True,
          "front_left_view": False
        },
        "class_type": "ViewSelector",
        "_meta": {
          "title": "View Selector"
        }
      }
    }
    return workflow

# ComfyUI 서버와 통신

def queue_prompt(prompt_workflow: dict, ip: str) -> str:
    data = json.dumps({"prompt": prompt_workflow}).encode("utf-8")
    req = urlrequest.Request(f"http://{ip}/prompt", data=data)
    try:
        res = urlrequest.urlopen(req)
        return json.loads(res.read().decode("utf-8"))['prompt_id']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def check_progress(prompt_id: str, ip: str) -> dict:
    while True:
        try:
            req = urlrequest.Request(f"http://{ip}/history/{prompt_id}")
            res = urlrequest.urlopen(req)
            history = json.loads(res.read().decode("utf-8"))
            if prompt_id in history:
                return history[prompt_id]
        except Exception:
            pass
        time.sleep(3)

# 텍스트 이미지 생성 요청

@app.post("/generate")
def generate_image(input_data: PromptInput):
    try:
        prompt_workflow = generate_prompt_text(input_data.user_prompt, input_data.user_negative)
        prompt_id = queue_prompt(prompt_workflow, comfy_ip)
        result = check_progress(prompt_id, comfy_ip)

        file_image_url = None
        image_filename = None
        for node_output in result["outputs"].values():
            if "images" in node_output:
                for image in node_output["images"]:
                    image_filename = image["filename"]
                    file_image_url = f"{host_ip}/images/{image_filename}"

        return {
            "status": "completed" if file_image_url else "fail",
            "image": file_image_url,
            "filename": image_filename
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MVAdapter 기반 이미지 생성 요청

@app.post("/generate_mv_adapter")
def generate_mv_adapter(input_data: MVAdapterInput):
    try:
        prompt_workflow = generate_mv_adapter_workflow(input_data.reference_filename, input_data.user_prompt)
        prompt_id = queue_prompt(prompt_workflow, comfy_ip)
        result = check_progress(prompt_id, comfy_ip)

        file_image_url = None
        output_dir = "output"
        for node_output in result["outputs"].values():
            if "images" in node_output:
                # 기존 결과 중 하나만 대표로 반환
                for image in node_output["images"]:
                    if "filename" in image:
                        file_image_url = f"{host_ip}/images/{image['filename']}"
                break  # 첫 번째 출력만 사용

        # 마지막 3개 파일 이름 변경
        view_names = ["front", "back", "left"]
        files = sorted(
            [f for f in os.listdir(output_dir) if f.endswith(".png") and f.startswith("ComfyUI_")]
        )
        last_three = files[-3:]
        for old_name, view in zip(last_three, view_names):
            old_path = os.path.join(output_dir, old_name)
            new_name = old_name.replace("_.png", f"_{view}.png")
            new_path = os.path.join(output_dir, new_name)
            os.rename(old_path, new_path)

        return {"status": "completed" if file_image_url else "fail", "image": file_image_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
