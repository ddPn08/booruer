from concurrent.futures import ThreadPoolExecutor
import math
import os
from tqdm import tqdm
from typing import *
import requests

from booruer.commands import command
from booruer.utils import retry, write_meta, tag_filter, check_dir
from booruer.utils import create_url
from booruer.booru.model import BooruPost
from booruer.danbooru.utils import categorize_tags


DANBOORU_API_KEY = os.environ.get("GELBOORU_API_KEY", "")
DANBOORU_USER_ID = os.environ.get("GELBOORU_USER_ID", "")
GELBOORU_URL = "https://gelbooru.com/index.php"

ALLOWED_EXTS = ["jpg", "jpeg", "png", "webp", "tiff"]


def download(
    post: BooruPost,
    outdir: str,
    original: bool = False,
    filter: str = "",
):
    ext = os.path.splitext(post.file_url)[1][1:]
    if ext not in ALLOWED_EXTS:
        return

    url = post.file_url if original else post.sample_url
    if not url.startswith("http"):
        url = create_url(url)

    filename = f"{post.id}.png"

    if filter and not tag_filter(post.tags, filter):
        return False

    tags = post.tags.split(" ")
    data = categorize_tags(tags)

    write_meta(
        os.path.join(outdir, f"{post.id}.json"),
        {
            "score": post.score,
            "tags": tags,
            "tag_string": post.tags,
            "tag_general": [x for x in tags if x in data["general"]],
            "artists": data["artists"],
            "copyrights": data["copyrights"],
            "characters": data["characters"],
            "meta": data["meta"],
            "rating": post.rating,
        },
    )

    @retry(5)
    def save():
        res = requests.get(url, headers={"User-Agent": "booruer"})
        if res.status_code != 200:
            raise Exception(f"Status code: {res.status_code}")
        with open(os.path.join(outdir, filename), "wb") as f:
            f.write(res.content)
        return True

    return save()


@retry(5)
def process(
    url: str,
    params: Dict,
    outdir: str,
    original: bool = False,
    filter: str = "",
):
    with requests.get(
        url,
        params=params,
        headers={"User-Agent": "booruer", "Accept": "application/json"},
    ) as res:
        data = res.json()
        posts = [BooruPost(**x) for x in data["post"]]

        if len(posts) < 1:
            return

        bar = tqdm(
            total=len(posts),
            unit="post",
            desc="Downloading",
            leave=False,
        )

        with ThreadPoolExecutor() as executor:
            for x in posts:
                ps = executor.submit(
                    download,
                    x,
                    outdir,
                    original=original,
                    filter=filter,
                )

                def done(x):
                    if x.result():
                        bar.update(1)

                ps.add_done_callback(done)


@command
def __run__(
    tags: str,
    outdir: str,
    limit: int = 50,
    filter: str = "",
    force: bool = False,
    original: bool = False,
):
    check_dir(outdir, force=force)
    length = math.ceil(limit / 100)

    for i in tqdm(range(length)):
        last = i + 1 == length
        lim = limit - i * 100 if last else 100
        url = create_url("", GELBOORU_URL)
        params = {
            "user_id": DANBOORU_USER_ID,
            "api_key": DANBOORU_API_KEY,
            "page": "dapi",
            "q": "index",
            "json": 1,
            "s": "post",
            "tags": tags,
            "pid": i,
            "limit": lim,
        }

        process(url, params, outdir, original=original, filter=filter)
