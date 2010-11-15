# -*- coding: utf-8 -*-

# Copyright (c) 2008 Moses Palmér
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


# Libraries used
import gobject
import gtk
import os
import re
import tempfile

# Symbols used
from awn.extras import _

# Local
from downloader import Downloader
from feed.basic import Feed, NAME, URL, PLUGIN
from feed.settings import Settings
from feed.rss import IMG_INDEX
from shared import (UI_DIR, USER_FEEDS_DIR)

UI_FILE = os.path.join(UI_DIR, 'add.ui')

URL_RE = re.compile('(?:http)|(?:https)://.*?/.*', re.IGNORECASE)


class ComicsAdder:
    """A program to add image feeds."""

    __name__ = 'Comics!'
    __version__ = '1.0'
    __author__ = 'Moses'

    ########################################################################
    # Helper methods                                                       #
    ########################################################################

    def process_error(self, result):
        label = self.ui.get_object('intro_label')
        if result == Feed.DOWNLOAD_FAILED:
            label.set_text(_('''\
Failed to download %s. Press "next" to try again.''') % self.url)
            self.assistant.set_current_page(0)
            return False

        elif result == Feed.DOWNLOAD_NOT_FEED:
            label.set_text(_('''\
The URL is not a valid comic feed. Press "next" to try again'''))
            self.assistant.set_current_page(0)
            return False

        return True

    ########################################################################
    # Standard python methods                                              #
    ########################################################################

    def __init__(self, feeds):
        """Create a new ComicsAdder instance."""
        self.feeds = feeds
        self.name = ''
        self.url = ''
        self.feed = None
        self.__update = None

        # Connect dialogue events
        self.ui = gtk.Builder()
        self.ui.add_from_file(UI_FILE)
        self.ui.connect_signals(self)
        self.assistant = self.ui.get_object('add_assistant')
        self.image_list = self.ui.get_object('image_list')

        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT, gtk.gdk.Pixbuf)
        self.image_list.set_model(self.model)

        # Show window
        self.assistant.set_page_complete(self.ui.get_object('intro_page'),
            True)
        self.assistant.set_page_complete(self.ui.get_object('last_page'),
            True)
        self.assistant.show()

    ########################################################################
    # Event hooks                                                          #
    ########################################################################

    def on_add_assistant_close(self, widget):
        if self.__update:
            self.feed.disconnect(self.__update)
        self.assistant.destroy()

    def on_add_assistant_cancel(self, widget):
        if self.__update:
            self.feed.disconnect(self.__update)
        self.assistant.destroy()

    def on_add_assistant_apply(self, widget):
        try:
            os.mkdir(USER_FEEDS_DIR)
        except Exception:
            pass
        self.name = self.ui.get_object('name_entry').get_text()
        f, filename = tempfile.mkstemp('.feed', '', USER_FEEDS_DIR, True)
        os.close(f)
        settings = Settings(filename)
        settings.description = 'Automatically generated by comics'
        settings[NAME] = self.name
        settings[URL] = self.url
        settings[IMG_INDEX] = self.image[0] + 1
        settings.comments[IMG_INDEX] = \
            'The index of the image in the HTML-code'
        try:
            settings[PLUGIN] = self.feed.get_plugin_name()
        except Exception:
            pass

        settings.save()
        self.feeds.add_feed(filename)
        self.feeds.update()

    def on_add_assistant_prepare(self, widget, page):
        if page is self.ui.get_object('url_page'):
            self.ui.get_object('wait_page').show()

        elif page is self.ui.get_object('wait_page'):
            self.assistant.set_page_complete(page, False)
            self.url = self.ui.get_object('url_entry').get_text()

            self.ui.get_object('wait_label').set_markup(
                _('Connecting to <i>%s</i>...') % self.url)

            # Download feed
            self.feed = self.feeds.get_feed_for_url(self.url)
            self.__update = self.feed.connect('updated', self.on_feed_updated)
            self.feed.update()

    def on_url_entry_changed(self, widget):
        text = widget.get_text()
        self.assistant.set_page_complete(self.ui.get_object('url_page'),
            not URL_RE.match(text) is None)

    def on_name_entry_changed(self, widget):
        text = widget.get_text()
        self.assistant.set_page_complete(self.ui.get_object('last_page'),
            not text == '')

    def on_image_list_unselect_all(self, widget):
        self.assistant.set_page_complete(self.ui.get_object('image_page'),
            False)

    def on_image_list_selection_changed(self, widget):
        selection = self.image_list.get_selected_items()
        if len(selection) == 1:
            self.assistant.set_page_complete(self.ui.get_object('image_page'),
                True)
            self.image = self.model.get_value(
                self.model.get_iter(selection[0]), 0)
        else:
            self.assistant.set_page_complete(self.ui.get_object('image_page'),
                False)

    def on_feed_updated(self, feed, result):
        if not self.process_error(result):
            return

        self.name = feed.name

        last_label = self.ui.get_object('last_label')
        last_label.set_markup(_('''\
This guide has finished.\n\
You can change the name of this comic. Press "apply" to add it.'''))
        name_entry = self.ui.get_object('name_entry')
        name_entry.set_text(self.name)

        # Can we skip the image page?
        images = feed.get_unique_images()
        if len(images) > 1:
            # Download images for the image list
            self.model.clear()
            for image in images:
                iterator = self.model.append((image, None))
                downloader = Downloader(image[1])
                downloader.connect('completed',
                    self.on_image_download_completed, iterator)
                downloader.download()
            self.ui.get_object('image_page').show()
        else:
            self.ui.get_object('image_page').hide()
            try:
                self.image = images[0]
            except IndexError:
                self.process_error(Feed.DOWNLOAD_NOT_FEED)
                return

        # Complete page
        self.assistant.set_page_complete(self.ui.get_object('wait_page'),
                                         True)
        self.ui.get_object('wait_label').set_markup(
                _('Found <b>%(name)s</b>!\n\n<i>%(description)s</i>')
                % {'name': self.name,
                    'description': self.feed.description})

    def on_image_download_completed(self, o, code, iterator):
        """Update the image list with a newly downloaded image."""
        if code != Downloader.OK:
            self.model.remove(iterator)
        else:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(o.filename)
                self.model.set_value(iterator, 1, pixbuf)
            except Exception:
                self.model.remove(iterator)
            os.remove(o.filename)
