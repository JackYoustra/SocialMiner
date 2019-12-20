from abc import ABCMeta, abstractmethod
from math import atan, degrees
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


class Pathnamed(metaclass=ABCMeta):
    @abstractmethod
    def resource_path(self) -> str:
        pass


class Visualizeable(metaclass=ABCMeta):
    @abstractmethod
    def visualize(self, root_path: Path):
        pass


def top_pie_visualization(title: str, output_dir: Path, pie_sources: list, pie_labels: list, slice_count: int,
                          total=None):
    if total is None:
        total = sum(pie_sources)
    piefig, pie = plt.subplots()
    slices = pie_sources[:slice_count - 1] / total
    other = 1 - sum(slices)
    slices = np.append(slices, other)
    labels = pie_labels[:slice_count - 1]
    labels = np.append(labels, "Other")
    plot, text, auto_pct_txt = pie.pie(slices, labels=labels, autopct='%1.1f%%', rotatelabels=True)
    for i, a in enumerate(auto_pct_txt):
        amount = pie_sources[i]
        a.set_text("{}: {}".format(a.get_text(), amount))
        x, y = a.get_position()
        angle = degrees(atan(y / x))
        a.set_rotation(angle)
    piefig.savefig(output_dir / "{}.png".format(title))
