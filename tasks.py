from abc import abstractmethod, abstractproperty
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from invoke import task

import config


class Command:
    @abstractmethod
    def elements(self) -> Iterable[str | None | Path]: ...

    @property
    @abstractmethod
    def describe(self) -> str: ...

    def __str__(self):
        return " ".join(map(str, filter(None, self.elements())))


@dataclass
class EnsureDirectoryExists(Command):
    directory: str

    @property
    def describe(self):
        return f"ensure directory {self.directory} exists"

    def elements(self):
        return ["mkdir", "-p", self.directory]


@dataclass
class ExecuteOnHost(Command):
    host: str
    command: Command

    @property
    def describe(self):
        return f"run on host {self.host}: {self.command.describe}"

    def elements(self):
        return ["ssh", self.host, f'"{self.command}"']


@dataclass
class CopyDirectoryAs(Command):
    source: str
    host: str
    dest: str

    @property
    def describe(self):
        return f"copy directory {self.source} on {self.host} as {self.dest}"

    def elements(self):
        source_dir = Path(self.source).expanduser()
        return ["scp", "-r", source_dir, f"{self.host}:{self.dest}"]


@dataclass
class CopyFileIn(Command):
    source: str
    host: str
    dest: str

    @property
    def describe(self):
        return f"copy file {self.source} on {self.host} in {self.dest}"

    def elements(self):
        source = Path(self.source).expanduser()
        return ["scp", source, f"{self.host}:{self.dest}"]


@dataclass
class DockerComposeUp(Command):
    file: str

    @property
    def describe(self):
        return f"start docker composition from file {self.file}"

    def elements(self):
        file = Path(self.file).expanduser()
        return ["docker", "compose", "--file", file, "up", "--detach"]


@dataclass
class DockerComposeDown(Command):
    file: str

    @property
    def describe(self):
        return f"terminate docker composition from file {self.file}"

    def elements(self):
        file = Path(self.file).expanduser()
        return ["docker", "compose", "--file", file, "down"]


@task
def copy(ctx):
    """Copy files on the server"""
    for source, mode, dest in config.content:
        match mode:
            case "in":
                commands = [
                    ExecuteOnHost(config.server, EnsureDirectoryExists(dest)),
                    CopyFileIn(source, config.server, dest),
                ]
            case "as":
                commands = [CopyDirectoryAs(source, config.server, dest)]
            case _:
                raise RuntimeError(f"unknown mode: {mode}")
        for command in commands:
            print(command.describe)
            ctx.run(str(command), echo=True)


@task
def terminate(ctx):
    """Terminate server"""
    command = ExecuteOnHost(config.server, DockerComposeDown(config.compose))
    ctx.run(str(command))


@task
def start(ctx):
    """Start server"""
    command = ExecuteOnHost(config.server, DockerComposeUp(config.compose))
    ctx.run(str(command))
