from concurrent.futures import ThreadPoolExecutor
import math
import os
from tqdm import tqdm
from typing import *
import requests

from booruer.commands import command
from booruer.utils import retry, write_meta, tag_filter, check_dir
from booruer.utils import create_url
from booruer.danbooru.model import DanBooruPost


DANBOORU_API_KEY = os.environ.get("DANBOORU_API_KEY", "")
DANBOORU_USER_ID = os.environ.get("DANBOORU_USER_ID", "")

ALLOWED_EXTS = ["jpg", "jpeg", "png", "webp", "tiff"]


def download(
    post: DanBooruPost,
    outdir: str,
    original: bool = False,
    filter: str = "",
):
    if post.is_banned or post.file_ext not in ALLOWED_EXTS:
        return

    url = (
        post.file_url
        if original or not hasattr(post, "large_file_url")
        else post.large_file_url
    )
    if not url.startswith("http"):
        url = create_url(url)

    filename = f"{post.id}.png"

    if filter and not tag_filter(post.tag_string, filter):
        return False

    write_meta(
        os.path.join(outdir, f"{post.id}.json"),
        {
            "score": post.score,
            "tags": post.tag_string.split(" "),
            "tag_string": post.tag_string,
            "tag_general": post.tag_string_general.split(" "),
            "characters": post.tag_string_character.split(" "),
            "copyrights": post.tag_string_copyright.split(" "),
            "artists": post.tag_string_artist.split(" "),
            "meta": post.tag_string_meta.split(" "),
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
        posts = [DanBooruPost(**x) for x in data]

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
                ps.add_done_callback(lambda _: bar.update(1))


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
        url = create_url("/posts.json")
        params = {
            "login": DANBOORU_USER_ID,
            "api_key": DANBOORU_API_KEY,
            "tags": tags,
            "page": i,
            "limit": lim,
        }

        process(url, params, outdir, original=original, filter=filter)
