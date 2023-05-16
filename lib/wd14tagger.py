import os
import cv2
import huggingface_hub
import numpy as np
import onnxruntime as rt
import pandas as pd
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.environ["HF_TOKEN"]
VIT_MODEL_REPO = "SmilingWolf/wd-v1-4-vit-tagger"
CONV_MODEL_REPO = "SmilingWolf/wd-v1-4-convnext-tagger"
SWIN_MODEL_REPO = "SmilingWolf/wd-v1-4-swinv2-tagger-v2"
MODEL_FILENAME = "model.onnx"
LABEL_FILENAME = "selected_tags.csv"


model = None
labels = None


def fix_tags(tag: str):
    return tag.replace("_", " ").replace("(", "\\(").replace(")", "\\)")


def make_square(img, target_size):
    old_size = img.shape[:2]
    desired_size = max(old_size)
    desired_size = max(desired_size, target_size)

    delta_w = desired_size - old_size[1]
    delta_h = desired_size - old_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [255, 255, 255]
    new_im = cv2.copyMakeBorder(
        img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return new_im


def smart_resize(img, size):
    if img.shape[0] > size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    elif img.shape[0] < size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
    return img


def load_model(model_repo: str) -> rt.InferenceSession:
    global model
    global labels
    path = huggingface_hub.hf_hub_download(
        model_repo, MODEL_FILENAME, use_auth_token=HF_TOKEN
    )
    model = rt.InferenceSession(
        path, providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
    )
    path = huggingface_hub.hf_hub_download(
        model_repo, LABEL_FILENAME, use_auth_token=HF_TOKEN
    )
    labels = pd.read_csv(path)["name"].tolist()


def unload_model():
    global model
    global labels
    del model
    del labels
    model = None
    labels = None


def interrogation(
    image: Image.Image,
    score_threshold: float,
):
    height = model.get_inputs()[0].shape[1]

    image = image.convert("RGBA")
    new_image = Image.new("RGBA", image.size, "WHITE")
    new_image.paste(image, mask=image)
    image = new_image.convert("RGB")
    image = np.asarray(image)

    image = image[:, :, ::-1]

    image = make_square(image, height)
    image = smart_resize(image, height)
    image = image.astype(np.float32)
    image = np.expand_dims(image, 0)

    input_name = model.get_inputs()[0].name
    label_name = model.get_outputs()[0].name
    probs = model.run([label_name], {input_name: image})[0]

    l = list(zip(labels, probs[0].astype(float)))

    ratings_names = l[:4]

    tags_names = l[4:]
    res = [x for x in tags_names if x[1] > score_threshold]
    res = dict(res)

    b = dict(sorted(res.items(), key=lambda item: item[1], reverse=True))

    return {
        "tag": fix_tags(", ".join(list(b.keys()))),
        "raw": ", ".join(list(b.keys())),
        "dict": res,
        "rating": dict(ratings_names),
    }
