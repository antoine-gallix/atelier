from pathlib import Path

from invoke import task

import config


@task
def copy(ctx):
    print("copy files to the server")
    for source, dest in config.content:
        print(f"{source} -> {dest}")
        recursive = None
        source = Path(source).expanduser()
        if source.exists() and source.is_dir():
            source = f"{source}/*"
        command_elements = ["scp", recursive, source, f"{config.server}:{dest}"]
        command = " ".join(
            map(
                str,
                filter(None, command_elements),
            )
        )
        ctx.run(command, echo=True)
