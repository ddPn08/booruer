import utils
import glob
import os
from tqdm import tqdm

from booruer.commands import command


@command
def __run__(
    dir: str,
    prefix: str = "",
    ignore: str = "",
    copyrights: bool = False,
    artists: bool = False,
    characters: bool = False,
    meta: bool = False,
    rating: bool = False,
    use_underline: bool = False,
    escape_bracket: bool = False,
):
    for meta_filepath in tqdm(glob.glob(os.path.join(dir, "*.json"))):
        meta_data = utils.open_meta(meta_filepath)

        tag_string = f"{prefix}, " if prefix else ""

        if artists and len(meta_data["artists"]) > 0:
            tag_string += f"{', '.join(meta_data['artists'])}, "
        if copyrights and len(meta_data["copyrights"]) > 0:
            tag_string += f"{', '.join(meta_data['copyrights'])}, "
        if characters and len(meta_data["characters"]) > 0:
            tag_string += f"{', '.join(meta_data['characters'])}, "
        if meta and len(meta_data["meta"]) > 0:
            tag_string += f"{', '.join(meta_data['meta'])}, "
        if (
            rating
            and "rating" in meta_data
            and (
                meta_data["rating"] == "questionable"
                or meta_data["rating"] == "explicit"
                or meta_data["rating"] == "q"
                or meta_data["rating"] == "e"
            )
        ):
            tag_string += "nsfw, "

        for tag in meta_data["tag_general"]:
            if ignore and tag in ignore.split(" "):
                continue
            tag_string += tag + ", "

        if not use_underline:
            tag_string = tag_string.replace("_", " ")
        if escape_bracket:
            tag_string = tag_string.replace("(", "\\(").replace(")", "\\)")

        tag_string = tag_string[: len(tag_string) - 2]

        with open(meta_filepath.replace(".json", ".txt"), mode="w") as f:
            f.write(tag_string)
