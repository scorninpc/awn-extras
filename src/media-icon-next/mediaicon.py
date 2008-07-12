# !/usr/bin/python

# Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk

import awn
import dbus

import awn.extras.awnmediaplayers as mediaplayers


FILENAME = "mediaicon.py"


def error_decorator(fn):
    """Handles errors caused by dbus"""
    def errors(cls, *args, **kwargs):
        try:
            fn(cls, *args)
        except (dbus.exceptions.DBusException, AttributeError, RuntimeError):
            cls.what_app()
    return errors


class App (awn.AppletSimple):
    """
    """
    def __init__ (self, uid, orient, height, media_button_type):
        """
        Creating the applets core
        """
        awn.AppletSimple.__init__(self, uid, orient, height)
        
        self.media_button_type = media_button_type
        if not hasattr(self, 'set_awn_icon'):
            if self.media_button_type == "-next": # -next -previous -pp
                self.media_icon_name = "forward.svg"
            elif self.media_button_type == "-previous":
                self.media_icon_name = "backward.svg"
            elif self.media_button_type == "-pp":
                self.media_icon_name = "play.svg"
            location =  __file__
            self.location = location.replace(FILENAME,'')
            self.location_icon = self.location + 'icons/' + self.media_icon_name
            icon = gdk.pixbuf_new_from_file (self.location_icon)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
            self.set_icon(icon)
        else:
            print 'set_awn_icon is supported'
            if self.media_button_type == "-next": # -next -previous -pp
                self.media_icon_name = "media-skip-forward"
            elif self.media_button_type == "-previous":
                self.media_icon_name = "media-skip-backward"
            elif self.media_button_type == "-pp":
                self.media_icon_name = "media-playback-start"
            self.set_awn_icon('media-icon' + self.media_button_type, uid, \
                self.media_icon_name)
        
        self.what_app()
        self.height = height
        self.title = awn.awn_title_get_default()
        self.popup_menu = self.create_default_menu()
        self.connect("button-press-event", self.button_press)

    def button_press(self, widget, event):
        if event.button == 1:
            if self.media_button_type == "-next": # -next -previous -pp
                self.button_next_press()
            elif self.media_button_type == "-previous":
                self.button_previous_press()
            elif self.media_button_type == "-pp":
                self.button_pp_press()
        elif event.button == 3:
            self.popup_menu.popup(None, None, None, event.button, event.time)

    def what_app(self):
        self.player_name = mediaplayers.what_app()
        if self.player_name == None:pass
        else:
            self.MediaPlayer = mediaplayers.__dict__[self.player_name]()

    @error_decorator
    def button_previous_press(self):
        self.MediaPlayer.button_previous_press()

    @error_decorator
    def button_pp_press(self):
        self.MediaPlayer.button_pp_press()

    @error_decorator
    def button_next_press(self):
        self.MediaPlayer.button_next_press()


if __name__ == "__main__":
    awn.init(sys.argv[1:])
    applet = App(awn.uid, awn.orient, awn.height, "-next")
    awn.init_applet(applet)
    applet.show_all()
    gtk.main()
