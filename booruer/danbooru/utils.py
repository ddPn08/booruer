import requests

from booruer.utils import create_url


def get_post_meta(id: str):
    url = create_url(f"/posts/{id}.json")
    with requests.get(
        url,
        headers={
            "Accept": "application/json",
        },
    ) as r:
        return r.json()


def categorize_tags(tags: list[str]):
    url = create_url("/tags.json")
    params = {
        "search[name_comma]": ",".join(tags),
        "limit": len(tags),
    }
    headers = {
        "Accept": "application/json",
    }

    with requests.get(url, params=params, headers=headers) as r:
        tags = r.json()

    def extract(cate):
        return [
            tag["name"]
            for tag in sorted(
                [tag for tag in tags if tag["category"] == cate],
                key=lambda x: x["name"],
            )
        ]

    general = extract(0)
    artists = extract(1)
    copyrights = extract(3)
    characters = extract(4)
    meta = extract(5)

    return {
        "general": general,
        "artists": artists,
        "copyrights": copyrights,
        "characters": characters,
        "meta": meta,
    }
