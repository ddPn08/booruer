from dotenv import load_dotenv

load_dotenv()

import fire

import booruer.commands as commands

def main():
    commands.load_all()
    fire.Fire(commands.commands)


if __name__ == "__main__":
    main()
