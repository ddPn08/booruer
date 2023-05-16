commands = {}


def command(func):
    module = func.__module__.split(".")
    if module[0] != "booruer":
        raise Exception(f"Invalid module: {module[0]}")
    if module[1] != "commands":
        raise Exception(f"Invalid module: {module[1]}")

    module = module[2:]
    if func.__name__ != "__run__":
        module.append(func.__name__)

    current = commands

    for i, name in enumerate(module):
        if i == len(module) - 1:
            current[name] = func
        else:
            if name not in current:
                current[name] = {}
            current = current[name]

def load_all():
    from . import meta, tag
    from .danbooru import download
    from .booru import download