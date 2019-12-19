from abc import ABCMeta, abstractmethod
from pathlib import Path


class Pathnamed(metaclass=ABCMeta):
    @abstractmethod
    def resource_path(self) -> str:
        pass


class Visualizeable(metaclass=ABCMeta):
    @abstractmethod
    def visualize(self, root_path: Path):
        pass

