import os
import signal

from geoplotlib.layers import BaseLayer
from geoplotlib.core import BatchPainter
from geoplotlib.utils import epoch_to_str
from geoplotlib.utils import BoundingBox

from environment import RunInfo


class SimulationLayer(BaseLayer):
    """Handles displaying the simulation on a map.
    It is based on geoplotlib's BaseLayer class.
    """

    def __init__(self, world, bounding_box=[0,0,0,0], max_time=None):
        """Initializes a Simulation Layer

        :param world: Esper world object
        :param bounding_box: array containing the positions of the initial view bounds in format [north, west, south, east]
        :param max_time: maximum time the simulation has to run (defaul None). If None, the simulation will never stop
        """
        self.world = world
        self.renderers = []
        self.run_info = RunInfo.get_instance()
        self.end_time = max_time
        
        self.bounding_box = BoundingBox(
            north=bounding_box[0],
            west=bounding_box[1],
            south=bounding_box[2],
            east=bounding_box[3])

    def add_renderer(self, renderer):
        """Attach a new rendering processor to the layer."""
        self.renderers.append(renderer)

    def draw(self, proj, mouse_x, mouse_y, ui_manager):
        ui_manager.info(epoch_to_str(self.run_info.timestamp()))

        painter = BatchPainter()
        painter.set_color([31, 120, 180])

        # The rendering processors must be updated with the
        # new projection and painter
        for renderer in self.renderers:
            renderer.update_drawing_context(proj, painter)
            renderer.update_mouse(mouse_x, mouse_y)

        # Update the world, aka run all processors serially
        self.world.process(self.run_info.step_size_seconds)

        painter.batch_draw()
        self.run_info.update_time()

        if self.end_time is not None and self.run_info.simulation_time() > self.end_time:
            os.kill(os.getpid(), signal.SIGINT)

    def bbox(self):
        return self.bounding_box
