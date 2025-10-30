from pathlib import Path

from invoke import task
from rich import print

import config
from commands import (
    CopyDirContent,
    CopyDirContentToRemote,
    CopyFile,
    CopyFileToRemote,
    EnsureDirectoryExists,
    ExecuteOnHost,
    NginxReload,
    Sudo,
)


def run_command(ctx, command):
    print(command.describe)
    ctx.run(str(command), echo=True)


@task
def update_content(ctx):
    """Copy files on the server"""
    commands = [
        ExecuteOnHost(
            config.REMOTE, EnsureDirectoryExists(config.CONTENT_REMOTE_TEMP_DIR)
        ),
        CopyDirContentToRemote(
            config.CONTENT_LOCAL_DIR, config.REMOTE, config.CONTENT_REMOTE_TEMP_DIR
        ),
        ExecuteOnHost(
            config.REMOTE, Sudo(EnsureDirectoryExists(config.CONTENT_REMOTE_FINAL_DIR))
        ),
        ExecuteOnHost(
            config.REMOTE,
            Sudo(
                CopyDirContent(
                    config.CONTENT_REMOTE_TEMP_DIR, config.CONTENT_REMOTE_FINAL_DIR
                )
            ),
        ),
    ]
    for command in commands:
        run_command(ctx, command)


@task
def update_config(ctx):
    """Copy files on the server"""
    commands = [
        ExecuteOnHost(
            config.REMOTE,
            EnsureDirectoryExists(Path(config.SERVER_CONFIG_FILE_REMOTE_TEMP).parent),
        ),
        CopyFileToRemote(
            config.SERVER_CONFIG_FILE_LOCAL,
            config.REMOTE,
            config.SERVER_CONFIG_FILE_REMOTE_TEMP,
        ),
        ExecuteOnHost(
            config.REMOTE,
            Sudo(
                CopyFile(
                    config.SERVER_CONFIG_FILE_REMOTE_TEMP,
                    config.SERVER_CONFIG_FILE_REMOTE_FINAL,
                )
            ),
        ),
        ExecuteOnHost(config.REMOTE, Sudo(NginxReload())),
    ]

    for command in commands:
        run_command(ctx, command)
