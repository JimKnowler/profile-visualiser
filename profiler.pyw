import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo
import argparse
import json

from profilerender import ProfileRender
from profiledata import ProfileData
from profileparser import ProfileParser

# Note: Set this to true if you want to merge data for multiple threads that have the same name but
#         run at different times.  
#       This is useful when visualising a worker thread that repeatedly starts and stops
MERGE_THREADS_WITH_SAME_NAME_AND_DIFFERENT_TIME_PERIODS = False

# Note: Set this to true to report information from the parser at startup
DEBUG_PARSER = False

# Create a GTK+ widget on which we will draw using Cairo
class ProfilerWindow(gtk.DrawingArea):

    # Draw in response to an expose-event
    __gsignals__ = { "expose-event": "override",
                    "configure-event" : "override"}

    def __init__(self, args):
        super(ProfilerWindow,self).__init__()
        
        self._init_profile_data(args)

        self._init_gtk()

        self._is_mouse_over = True
        self._is_panning = False
        self._mouse_button = None
        self._last_xy = None

    def _init_gtk(self):
        self.connect("motion_notify_event", self.on_motion_notify_event)
        self.connect("button_press_event", self.on_button_press_event)
        self.connect("button_release_event", self.on_button_release_event)
        self.connect("scroll-event", self.on_scroll_event)
        self.connect("enter_notify_event", self.on_enter_notify_event)
        self.connect("leave_notify_event", self.on_leave_notify_event)

        self.set_events( gtk.gdk.EXPOSURE_MASK
                            | gtk.gdk.ENTER_NOTIFY_MASK
                            | gtk.gdk.LEAVE_NOTIFY_MASK
                            | gtk.gdk.BUTTON_PRESS_MASK
                            | gtk.gdk.BUTTON_RELEASE_MASK
                            | gtk.gdk.POINTER_MOTION_MASK
                            | gtk.gdk.POINTER_MOTION_HINT_MASK)

    def _init_profile_data(self, args):        
        filename = args.filename

        profile_data = ProfileData()
        profile_parser = ProfileParser(profile_data)
        profile_parser.load_file(filename)        

        if DEBUG_PARSER:
            profile_data.debug_tty()

        if MERGE_THREADS_WITH_SAME_NAME_AND_DIFFERENT_TIME_PERIODS:
            profile_data.merge_restarted_threads()

        self._profile_render = ProfileRender( profile_data )


    def on_motion_notify_event(self, widget, event):
        """ mouse is moved """

        x = event.x
        y = event.y

        if self._is_panning:            
            last_x, last_y = self._last_xy

            dx = x-last_x
            dy = y-last_y            

            self._profile_render.pan_by(dx,dy)
        
        self._last_xy = (x,y)

        self.queue_draw()

    def on_button_press_event(self, widget, event):
        """ mouse button is pressed """
        
        if event.button in [1,2]:
            self._mouse_button = event.button
            self._is_panning = True
            self._last_xy = (event.x, event.y)

    def on_button_release_event(self, widget, event):
        """ mouse button is released """

        if event.button == self._mouse_button:
            self._mouse_button = None
            self._is_panning = False

    def on_scroll_event(self, widget, event):
        """ scroll wheel is moved up,down,left,right """
        
        x = event.x
        y = event.y

        SCALE_FACTOR = 1.5

        if event.direction == gtk.gdk.SCROLL_DOWN:
            # zoom out
            self._profile_render.scale_at( 1.0 / SCALE_FACTOR, x, y )
        else:
            # zoom in
            self._profile_render.scale_at( SCALE_FACTOR, x, y )

        self.queue_draw()
    
    def on_enter_notify_event(self, widget, event):
        self._is_mouse_over = True
        x = event.x
        y = event.y
        self._last_xy = (x,y)

    def on_leave_notify_event(self, widget, event):
        self._is_mouse_over = False

    # Handle the expose-event by drawing
    def do_expose_event(self, event):

        # Create the cairo context
        cr = self.window.cairo_create()

        # Restrict Cairo to the exposed area; avoid extra work
        cr.rectangle(event.area.x, event.area.y,
                event.area.width, event.area.height)
        cr.clip()

        self._profile_render.render(cr)

        if self._is_mouse_over and self._last_xy:
            self._profile_render.render_pointer(cr, self._last_xy)

    # Handle the configure-event by resizing
    def do_configure_event(self, event):
        self._profile_render.resize(*self.window.get_size())


# GTK required to show the widget in a window and quit when it's closed
def run( widget ):
    window = gtk.Window()
    window.connect("delete-event", gtk.main_quit)
    widget.show()
    window.add(widget)
    window.set_title("Profiler")
    window.set_size_request(800,600)
    window.present()
    gtk.main()

def parse_args():
    parser = argparse.ArgumentParser(description="Function Profiler")
    parser.add_argument('--filename', '-f', default='profile.txt', help='file path to profile.txt file')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    profiler_window = ProfilerWindow(args)

    run(profiler_window)
