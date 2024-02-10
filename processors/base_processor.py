import sys

import esper


class BaseProcessor(esper.Processor):
    def process(self, dt):
        """
        This method, called by world.process(), is just a wrapper that
        catches exceptions before they are propagated to a container
        layer, thus we can see the actual error instead of a 'GLException'.
        Do NOT override this method in your subclasses, override _process()
        instead
        """
        try:
            self._process(dt)
        except Exception as ex:
            print(ex)
            raise ex
            sys.exit(-1)

    def _process(self, dt):
        """
        This method will be called by the real process function, override
        this method with your processor specific code
        """
        raise NotImplementedError()
