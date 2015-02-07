import time
import cv2, cv
import numpy
import settings

DEBUG = True

class Recorder(object):
    def __init__(self):
        self.frame = None

        self.keep_running = True
        self.frame_rate = 0
        self.last_frame = time.time()
        self.limit_fps = settings.LIMIT_FPS

        self.capture = cv.CaptureFromCAM(settings.CAMERA_INDEX)

        if settings.WIDTH:
            cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_WIDTH, settings.WIDTH)
        if settings.HEIGHT:
            cv.SetCaptureProperty(self.capture, cv.CV_CAP_PROP_FRAME_HEIGHT, settings.HEIGHT)

        if self.capture: # try to get the first frame
            frame = cv.QueryFrame(self.capture)
        else:
            raise Exception("Could not open video device")

    def update_frame_rate(self):
        # FIXME: save some kind of average for the fps
        self.frame_diff = time.time() - self.last_frame

        if self.limit_fps:
            minimum_frame_diff = 1.0/self.limit_fps
            if self.frame_diff < minimum_frame_diff:
                time.sleep(minimum_frame_diff - self.frame_diff)
            self.frame_diff = time.time() - self.last_frame

        self.frame_rate = 1.0/self.frame_diff
        self.last_frame = time.time()

        if DEBUG:
            print "FPS: %s" % round(self.frame_rate)

    def buffer_frame(self, frame):
        (retval, jpg_frame) = cv2.imencode(".jpg", frame, (cv.CV_IMWRITE_JPEG_QUALITY, settings.JPG_QUALITY))
        jpg_frame = jpg_frame.tostring()
        self.frame = jpg_frame

    def handle_frame(self):
        frame = cv.QueryFrame(self.capture)
        frame_array = numpy.asarray(frame[:,:])
        self.buffer_frame(frame_array)
