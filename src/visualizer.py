from abc import ABCMeta, abstractmethod
import matplotlib.pyplot as plt
from pathlib import Path
#from typing import final


class Pathnamed(metaclass=ABCMeta):
    @abstractmethod
    def resource_path(self) -> str:
        pass


class Visualizeable(metaclass=ABCMeta):
    # watch for diamond inheritance problem! Probably a better way to write this?
    #@final
    def visualize(self, root_path: Path):
        if isinstance(self, DurationVisualizeable):
            instance_path = root_path / self.resource_path()
            instance_path.mkdir(exist_ok=True)
            self.duration_visualize(instance_path)
        pass


# Visualizes a service activity over a timeseries
class DurationVisualizeable(Visualizeable):

    @abstractmethod
    def sorted_playtimes(self):
        """ Yields a list of playtimes, from which to create visualizations.

        Returns:
            A list of floating-point playtimes, in ms, sorted

        """
        pass

    def duration_visualize(self, output_dir):
        times = self.sorted_playtimes()
        x = range(len(times))
        y = [time / 1000 for time in times]
        fig, ax = plt.subplots(tight_layout=True)
        ax.plot(x, y)
        ax.set(xlabel='Number of songs', ylabel='Song duration (secs)', title='Songs with time less than or equal to x')
        ax.grid()
        fig.savefig(output_dir / "song_playtimes.png")

        ax.set_yscale("log")
        ax.set(xlabel='Number of songs', ylabel='Log song duration (secs)',
               title='Songs with time less than or equal to x')
        fig.savefig(output_dir / "song_playtimes_log.png")
