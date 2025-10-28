from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import chain
from pathlib import Path
from typing import Iterable

from invoke import task
from rich import print
from rich.text import Text

import config


@dataclass
class Command:
    sudo: bool = field(default=False, kw_only=True)

    @abstractmethod
    def elements(self) -> Iterable[str | None | Path]: ...

    @property
    @abstractmethod
    def describe(self) -> str | Text: ...

    def prefix(self) -> list[str]:
        if self.sudo:
            return ["sudo"]
        else:
            return []

    def __str__(self):
        return " ".join(map(str, filter(None, chain(self.prefix(), self.elements()))))


styles = defaultdict(lambda: "", {"path": "blue", "host": "green"})


@dataclass
class EnsureDirectoryExists(Command):
    directory: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "ensure directory ", (str(self.directory), styles["path"]), " exists"
        )

    def elements(self):
        return ["mkdir", "-p", self.directory]


@dataclass
class ExecuteOnHost(Command):
    host: str | Path
    command: Command

    @property
    def describe(self):
        return Text.assemble(
            "run on host ",
            (str(self.host), styles["host"]),
            ": ",
            self.command.describe,
        )

    def elements(self):
        return ["ssh", self.host, f'"{self.command}"']


@dataclass
class CopyDirectoryAs(Command):
    source: str | Path
    host: str
    dest: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "copy directory ",
            (str(self.source), styles["path"]),
            " on ",
            (self.host, styles["host"]),
            " as ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source_dir = Path(self.source).expanduser()
        return ["scp", "-r", source_dir, f"{self.host}:{self.dest}"]


@dataclass
class CopyFileIn(Command):
    source: str | Path
    host: str
    dest: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "copy file ",
            (str(self.source), styles["path"]),
            " on ",
            (self.host, styles["host"]),
            " in ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source = Path(self.source).expanduser()
        return ["scp", source, f"{self.host}:{self.dest}"]


@dataclass
class DockerComposeUp(Command):
    file: str

    @property
    def describe(self):
        return Text.assemble(
            "start docker composition from file ", (self.file, styles["path"])
        )

    def elements(self):
        file = Path(self.file).expanduser()
        return ["docker", "compose", "--file", file, "up", "--detach"]


@dataclass
class DockerComposeDown(Command):
    file: str

    @property
    def describe(self):
        return Text.assemble(
            "terminate docker composition from file ", (self.file, styles["path"])
        )

    def elements(self):
        file = Path(self.file).expanduser()
        return ["docker", "compose", "--file", file, "down"]


def run_command(ctx, command):
    print(command.describe)
    ctx.run(str(command), echo=True)


@task
def copy(ctx):
    """Copy files on the server"""
    for source, mode, dest in config.content:
        dest = Path(dest)
        match mode:
            case "in":
                commands = [
                    ExecuteOnHost(config.server, EnsureDirectoryExists(dest)),
                    CopyFileIn(source, config.server, dest),
                ]
            case "as":
                commands = [
                    ExecuteOnHost(config.server, EnsureDirectoryExists(dest.parent)),
                    CopyDirectoryAs(source, config.server, dest),
                ]
            case _:
                raise RuntimeError(f"unknown mode: {mode}")
        for command in commands:
            run_command(ctx, command)


# @task
# def terminate(ctx):
#     """Terminate server"""
#     command = ExecuteOnHost(config.server, DockerComposeDown(config.compose))
#     run_command(ctx, command)


# @task
# def start(ctx):
#     """Start server"""
#     command = ExecuteOnHost(config.server, DockerComposeUp(config.compose))
#     run_command(ctx, command)
