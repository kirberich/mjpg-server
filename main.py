from server import Api
from recorder import Recorder
import settings

if __name__ == '__main__':
    recorder = Recorder()
    api = Api(recorder=recorder)
    api.demonize(port=settings.PORT)

    while True:
        recorder.update_frame_rate()
        recorder.handle_frame()
