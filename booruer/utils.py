import traceback
import json
import os
import shutil


def create_url(path: str, origin: str = "https://danbooru.donmai.us"):
    return os.environ.get("BOORU_ORIGIN", origin) + path


def retry(max: int = 3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(max):
                try:
                    return func(*args, **kwargs)
                except:
                    print(f"Retry {i + 1} times.")
                    if i + 1 == max:
                        traceback.print_exc()
                    continue
            raise Exception("Retry failed.")

        return wrapper

    return decorator


def create_meta(post):
    return {
        "score": post["score"],
        "tags": post["tag_string"].split(" "),
        "tag_string": post["tag_string"],
        "tag_general": post["tag_string_general"].split(" "),
        "characters": post["tag_string_character"].split(" "),
        "copyrights": post["tag_string_copyright"].split(" "),
        "artists": post["tag_string_artist"].split(" "),
        "meta": post["tag_string_meta"].split(" "),
        "rating": post["rating"],
    }


def open_meta(filepath: str):
    with open(filepath, mode="r") as f:
        buf = f.read()
        return json.loads(buf)


def write_meta(filepath: str, obj: dict):
    j = json.dumps(obj, indent=2)
    with open(filepath, mode="w") as f:
        f.write(j)


def check_dir(dir: str, force: bool = False):
    if os.path.isfile(dir):
        if force:
            os.remove(dir)
        else:
            raise Exception(
                "A file already exists in the location specified in outdir."
            )
    os.makedirs(dir, exist_ok=True)
    if len(os.listdir(dir)) > 0:
        if force:
            shutil.rmtree(dir)
            os.makedirs(dir, exist_ok=True)
        else:
            raise Exception("Directory is not empty.")


def tag_filter(tag: str, filter: str):
    filter = filter.split(" ")
    for v in filter:
        if v.startswith("-") and v[1:] in tag:
            return False
        if not v.startswith("-") and v not in tag:
            return False

    return True
