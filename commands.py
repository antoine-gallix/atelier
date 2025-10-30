from abc import abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Iterable

from rich.text import Text


@dataclass
class Command:
    @abstractmethod
    def elements(self) -> Iterable[str | None | Path]: ...

    @property
    @abstractmethod
    def describe(self) -> str | Text: ...

    def __str__(self):
        return " ".join(map(str, filter(None, self.elements())))


styles = defaultdict(lambda: "", {"path": "blue", "host": "green"})


@dataclass
class Sudo(Command):
    command: Command

    @property
    def describe(self) -> str | Text:
        return Text.assemble("Execute as Super User: ", self.command.describe)

    def elements(self) -> Iterable[str | None | Path]:
        return chain(["sudo"], self.command.elements())


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
        return ["ssh", self.host, f"'{self.command}'"]


@dataclass
class CopyFileToRemote(Command):
    source: str | Path
    host: str
    dest: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "copy file ",
            (str(self.source), styles["path"]),
            " on host ",
            (self.host, styles["host"]),
            " in ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source = Path(self.source).expanduser()
        return [
            "scp",
            source,
            f"{self.host}:{self.dest}",
        ]


@dataclass
class CopyDirToRemote(Command):
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
            " in ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source = Path(self.source).expanduser()
        return [
            "scp",
            "-r",
            source,
            f"{self.host}:{self.dest}",
        ]


@dataclass
class CopyDirContentToRemote(Command):
    source: str | Path
    host: str
    dest: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "copy content of dir ",
            (str(self.source), styles["path"]),
            " on ",
            (self.host, styles["host"]),
            " in ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source = Path(self.source).expanduser()
        return [
            "scp",
            "-r",
            str(source / "*"),
            f"{self.host}:{self.dest}",
        ]


@dataclass
class CopyDirContent(Command):
    source: str | Path
    dest: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "copy content of dir ",
            (str(self.source), styles["path"]),
            " in ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source = Path(self.source).expanduser()
        return [
            "cp",
            "-r",
            str(source / "*"),
            self.dest,
        ]


@dataclass
class CopyFile(Command):
    source: str | Path
    dest: str | Path

    @property
    def describe(self):
        return Text.assemble(
            "copy file ",
            (str(self.source), styles["path"]),
            " in ",
            (str(self.dest), styles["path"]),
        )

    def elements(self):
        source = Path(self.source).expanduser()
        return [
            "cp",
            source,
            self.dest,
        ]


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
            "Terminate docker composition from file ", (self.file, styles["path"])
        )

    def elements(self):
        file = Path(self.file).expanduser()
        return ["docker", "compose", "--file", file, "down"]


@dataclass
class NginxReload(Command):
    @property
    def describe(self):
        return Text("Reload Nginx config")

    def elements(self):
        return ["nginx", "-s", "reload"]
