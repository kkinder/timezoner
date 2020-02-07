from datetime import datetime

from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent, PreferencesEvent, PreferencesUpdateEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem

import pytz_local as pytz


class DemoExtension(Extension, EventListener):
    timezones = [(tz.lower(), tz) for tz in pytz.all_timezones]

    def __init__(self):
        super(DemoExtension, self).__init__()

        self.faves = [None]*5
        self.globalist_format = '12h'

        self.subscribe(KeywordQueryEvent, self)
        self.subscribe(PreferencesEvent, self)
        self.subscribe(PreferencesUpdateEvent, self)

    def on_event(self, event, extension):
        if isinstance(event, PreferencesEvent):
            return self.on_preferences_event(event, extension)
        elif isinstance(event, PreferencesUpdateEvent):
            return self.on_preferences_update_event(event, extension)
        elif isinstance(event, KeywordQueryEvent):
            return self.on_keyword_event(event, extension)
        else:
            raise Exception(f'Unexpected event: {event!r}')

    def _set_fav(self, index, value):
        self.faves[index] = value

    def on_preferences_event(self, event: PreferencesEvent, extension):
        for i in range(5):
            self._set_fav(i, event.preferences.get(f'globalist_fav{i + 1}'))
        self.globalist_format = event.preferences.get('globalist_format', '12h')

    def on_preferences_update_event(self, event: PreferencesUpdateEvent, extension):
        if event.id.startswith('globalist_fav'):
            self._set_fav(int(event.id[-1])-1, event.new_value)
        elif event.id == 'globalist_format':
            self.globalist_format = event.new_value

    def on_keyword_event(self, event: KeywordQueryEvent, extension):
        if self.globalist_format == '24h':
            print_format = '%H:%M'
            copy_format = '%H:%M (%Z)'
        else:
            print_format = '%I:%M %p'
            copy_format = '%I:%M %p (%Z)'

        local_day = datetime.now().strftime('%A')

        argument = event.get_argument()

        zones_to_show = []

        if argument:
            loose_query = argument.lower()

            for tz_comp, tz in self.timezones:
                if loose_query in tz_comp:
                    zones_to_show.append(tz)
        else:
            zones_to_show = self.faves

        items = []
        for tz in zones_to_show:
            other_time = datetime.now(pytz.timezone(tz))
            remote_day = other_time.strftime('%A')
            if remote_day != local_day:
                print_value = other_time.strftime(f'{print_format} [%A]')
                copy_value = other_time.strftime(f'%A @ {copy_format}')
            else:
                print_value = other_time.strftime(print_format)
                copy_value = other_time.strftime(copy_format)
            items.append(ExtensionResultItem(icon='images/icon.png',
                                             name=f'{tz}',
                                             description=print_value,
                                             on_enter=CopyToClipboardAction(copy_value)))

        return RenderResultListAction(items)


if __name__ == '__main__':
    DemoExtension().run()
