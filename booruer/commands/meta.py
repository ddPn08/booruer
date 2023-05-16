from glob import glob
import os
from lib import wd14tagger
from PIL import Image
from tqdm import tqdm

from booruer.commands import command
from booruer.danbooru import utils as danbooru
from booruer.utils import create_meta, write_meta, open_meta


@command
def __run__(
    dir: str,
    skip_tag: bool = False,
    force_tag: bool = False,
    force_categorize: bool = False,
    tagger_threshold: float = 0.5,
    tagger_model: str = "swinv2",
    refetch: bool = False,
):
    images: list[str] = [
        x
        for x in glob(os.path.join(dir, "**", "*"), recursive=True)
        if x.endswith(".png") or x.endswith(".jpg")
    ]

    if refetch:
        for filepath in tqdm(images):
            meta_filepath = os.path.splitext(filepath)[0] + ".json"
            if not os.path.exists(meta_filepath):
                default = danbooru.get_post_meta(
                    os.path.splitext(os.path.basename(filepath))[0]
                )
                if default is not None:
                    write_meta(meta_filepath, create_meta(default))
                else:
                    print(f"Failed to research {filepath}")

    if not skip_tag:
        wd14tagger.load_model(wd14tagger.SWIN_MODEL_REPO)

        for filepath in tqdm(images):
            meta_filepath = os.path.splitext(filepath)[0] + ".json"
            if not os.path.exists(meta_filepath):
                write_meta(meta_filepath, {})
            meta = open_meta(meta_filepath)
            if "tags" not in meta or force_tag:
                image = Image.open(filepath)
                data = wd14tagger.interrogation(image, tagger_threshold)
                tags: list[str] = list(data["dict"].keys())
                data = danbooru.categorize_tags(tags)
                meta["tags"] = tags
                meta["tag_string"] = " ".join(tags)
                meta["tag_general"] = [x for x in tags if x in data["general"]]
                meta["artists"] = data["artists"]
                meta["copyrights"] = data["copyrights"]
                meta["characters"] = data["characters"]
                meta["meta"] = data["meta"]
                write_meta(meta_filepath, meta)
        wd14tagger.unload_model()
