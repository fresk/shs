from kivy.config import Config

class DualScreenTouchTransform(object):

    def process(self, events):
        processed = []
        for etype, touch in events:
            touch.sy = touch.sy/2.0
            processed.append((etype, touch))
        return processed
