from pathlib import Path

from invoke import task

import config


@task
def copy(ctx):
    """Copy files on the server"""
    print("copy files to the server")
    for source, dest in config.content:
        print(f"{source} -> {dest}")
        recursive = ""
        source = Path(source).expanduser()
        if source.exists() and source.is_dir():
            source = f"{source}/*"
        command = " ".join(["scp", recursive, source, f"{config.server}:{dest}"])
        ctx.run(command, echo=True)
