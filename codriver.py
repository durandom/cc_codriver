#!/usr/bin/env python3

import argparse
import csv
import json
import os
import logging
import sys
from typing import List, Optional, Union
from rbr_pacenote_plugin import RbrPacenotePlugin, RbrPacenote


class PacenoteModifier:
    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id
        self.translation_table = {
            # 'detail_' : '',
        }

    def rbr_name(self):
        _rbr_name = self.name
        for key, value in self.translation_table.items():
            _rbr_name = _rbr_name.replace(key, value)

        return _rbr_name

    def __str__(self):
        return f'{self.name} - {self.id}'

    def __repr__(self):
        return f'{self.name} - {self.id}'

class PacenoteType(PacenoteModifier):
    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id
        self.translation_table = {
            'corner_1' : 'one',
            'corner_2' : 'two',
            'corner_3' : 'three',
            'corner_4' : 'four',
            'corner_5' : 'five',
            'corner_6' : 'six',
            # 'detail_' : '',
        }

class CrewChiefNote:

    def __init__(self, name: str, notes=[], prefix: Optional['CrewChiefNote'] = None):
        self.name = name
        self.sounds = {} # soundfile: subtitle
        self.rushed = False
        self.prefix = prefix

        if notes:
            for note in notes:
                self.add_note(note)

    def add_note(self, note):
        for file in note.sounds:
            subtitle = note.translation
            self.add_sound(file, subtitle)

    def add_prefix(self, prefix: 'CrewChiefNote'):
        self.prefix = prefix

    def create(self):
        print(f'{self.name}')

    def add_sound(self, file, subtitle):
        if file in self.sounds:
            logging.error(f'Duplicate sound: {file} in {self}')
        self.sounds[file] = subtitle

    def __str__(self):
        return f'{self.name} - {self.sounds}'

    def __repr__(self):
        return f'{self.name} - {self.sounds}'

class CoDriver:
    def __init__(self,
                 cc_pacenote_types = "cc_pacenote_type.txt",
                 cc_pacenote_modifier = "cc_pacenote_modifier.txt",
                 cc_sounds = "codriver",
                 map_notes = [],
                 map_cc_types = {},
                 additional_cc_types = {},
                 skip_notes = {}):
        self.cc_pacenotes_types = {}
        self.cc_pacenotes_modifiers = {}
        self.cc_sounds = {}
        self.rbr_sounds = {}
        self.rbr_pacenote_plugins = {}
        self.skip_notes = skip_notes
        self.map_notes = map_notes
        self.map_cc_types = map_cc_types
        self.additional_cc_types = additional_cc_types

        self.init_cc_pacenotes_types(cc_pacenote_types)
        self.init_cc_pacenotes_modifier(cc_pacenote_modifier)
        self.init_cc_sounds(cc_sounds)

        self.mapped_cc_notes : List[CrewChiefNote] = []

    def add_pacenote_plugin(self, type, rbr_pacenote_plugin):
        self.rbr_pacenote_plugins[type] = rbr_pacenote_plugin

    # 2. Get the mapping from CC CoDriver.cs
    # public enum PacenoteType
    # {
    #     // Weird naming is used to simplify sound reading.
    #     corner_1_left = 0,
    #     corner_square_left = 1,
    #     detail_finish = 22,
    def init_cc_pacenotes_types(self, file = "cc_pacenote_type.txt"):
        lookup = self.parse_cc_types_files(file)
        for id, name in lookup.items():
            self.cc_pacenotes_types[id] = PacenoteType(name, id)
        for name, id in self.additional_cc_types.items():
            self.cc_pacenotes_types[id] = PacenoteType(name, id)

    def init_cc_pacenotes_modifier(self, file = "cc_pacenote_modifier.txt"):
        lookup = self.parse_cc_types_files(file)
        for id, name in lookup.items():
            self.cc_pacenotes_modifiers[id] = PacenoteModifier(name, id)

    def parse_cc_types_files(self, file):
        # // Weird naming is used to simplify sound reading.
        # corner_1_left = 0,
        # iterate through the lines

        lookup = {}
        with open(file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('//'):
                    continue
                parts = line.split('=')
                if len(parts) != 2:
                    logging.error("Invalid line: %s" % line)
                    continue
                # remove the spaces
                name = parts[0].strip()
                id = int(parts[1].strip().replace(',', ''))
                lookup[id] = name

        return lookup

    def init_cc_sounds(self, codriver_dir = "codriver"):
        # open the codriver directory and get all the subdirectories

        for root, dirs, files in os.walk(codriver_dir):
            if 'subtitles.csv' in files:
                    csv_path = os.path.join(root, 'subtitles.csv')
                    # folders_with_subtitles.append(root)

                    with open(csv_path, mode='r', encoding='utf-8') as file:
                        name = os.path.basename(root)
                        note = CrewChiefNote(name)
                        csv_reader = csv.reader(file)
                        for row in csv_reader:
                            sound = row[0]
                            subtitle = row[1]
                            note.sounds[sound] = subtitle
                        # logging.debug(f'Adding {name} - {note.sounds}')
                        self.cc_sounds[name] = note

    def init_rbr_sounds(self, sounds_dir = "sounds"):
        # open the codriver directory and get all the subdirectories

        for root, dirs, files in os.walk(sounds_dir):
            for file in files:
                if file.endswith('.ogg'):
                    sound = os.path.join(root, file)
                    # remove the sounds_dir from the path
                    sound = sound.replace(sounds_dir, '')
                    # remove leading slash
                    sound = sound[1:]
                    self.rbr_sounds[sound] = sound

    def get_pacenote_type_for_id(self, id):
        type = self.cc_pacenotes_types.get(id)
        if not type:
            logging.error(f"unknown id {id}")
            exit(1)
        return type

    def get_rbr_pacenote_by_name(self, name, package = "numeric"):
        plugin = self.rbr_pacenote_plugins[package]
        name = name.lower()
        notes = [ note for note in plugin.pacenotes if note.name.lower() == name]
        return notes

    def get_rbr_pacenotes_by_id(self, id, package = "numeric"):
        plugin = self.rbr_pacenote_plugins[package]
        notes = [ note for note in plugin.pacenotes if note.id == id]
        return notes

    def get_rbr_pacenotes(self, id=-1, name='', package = "numeric", type: Union[PacenoteType, PacenoteModifier, None] = None) -> List[RbrPacenote]:
        notes = []
        if type:
            id = type.id
            name = type.rbr_name()

        logging.debug(f'get_rbr_pacenotes: id: {id} - name: {name} - package: {package}')

        # if mapping is configured
        for mapping in self.map_notes:
            cc_id = mapping.get('cc_id')
            if id == cc_id:
                id = mapping.get('rbr_id', id)
                name = mapping.get('rbr_name', name)
            cc_name = mapping.get('cc_name', name)
            if name == cc_name:
                id = mapping.get('rbr_id', id)
                name = mapping.get('rbr_name', name)

        # check if id is a number
        if not isinstance(id, int):
            logging.error(f'Invalid id: {id}')
            exit(1)
        if id >= 0:
            notes = self.get_rbr_pacenotes_by_id(id, package=package)
            if notes:
                return notes
        if name:
            notes = self.get_rbr_pacenote_by_name(name, package=package)
            if notes:
                return notes

    def get_pacenote_type_for_cc_sound(self, sound) -> Union[PacenoteType, PacenoteModifier]:
        for src, dst in self.map_cc_types.items():
            if sound == src:
                sound = dst

        for id, type in self.cc_pacenotes_types.items():
            if type.name.lower() == sound.lower():
                return type
        for id, type in self.cc_pacenotes_modifiers.items():
            if type.name.lower() == sound.lower():
                return type
        return None

    # def map_notes(self):
    #     # iterate through the pacenotes
    #     for id, note in self.rbr_pacenotes.items():
    #         logging.debug(f'{note}')
    #         if note.id:
    #             type = self.get_pacenote_type_for_id(note.id)
    #             name = type.name
    #         else:
    #             logging.debug(f'no id')

    #         cc_note = CrewChiefNote(name)

    #         for sound in note.sounds:
    #             # get the path to the rbr sound file
    #             file = self.rbr_pacenote_plugin.sound_file(sound)
    #             if os.path.exists(file):
    #                 logging.debug(f'Found sound: {sound}')
    #                 cc_note.add_sound(file, "")
    #             else:
    #                 logging.error(f'Not found: {sound} - {file}')
    #                 return

    def map_package_and_type(self, type = '', package = 'numeric'):
        if type.endswith('_descriptive'):
            package = 'descriptive'
            type = type[:-12]

        if type.endswith('_reversed'):
            package = 'reversed'
            type = type[:-9]

        return (package, type)

    def map_notes_from_cc(self):
        cc_notes = []

        type = self.get_pacenote_type_for_cc_sound('detail_into')
        if not type:
            logging.error(f'Unknown pacenote type: detail_into')
            exit(1)
        notes = self.get_rbr_pacenotes(id=type.id, name=type.rbr_name())
        if len(notes) != 1:
            logging.error(f'Found {len(notes)} notes for type {type} - {notes}')
            exit(1)
        into = CrewChiefNote('detail_into', notes=notes)

        for sound in sorted(self.cc_sounds.keys()):
            if sound in self.skip_notes.keys():
                logging.debug(f'ignoring {sound}')
                continue

            sound_lookup = sound

            # create a new CrewChiefNote
            cc_note = CrewChiefNote(sound)

            if sound.startswith('cmp_'):
                # remove the cmp_ prefix
                sound_lookup = sound[4:]

                if sound_lookup.startswith('into_'):
                    sound_lookup = sound_lookup[5:]
                    cc_note.prefix = into

            if sound_lookup.endswith('_rushed'):
                sound_lookup = sound_lookup[:-7]
                cc_note.rushed = True

            (package, sound_lookup) = self.map_package_and_type(type=sound_lookup)

            # get the pacenote type
            type = self.get_pacenote_type_for_cc_sound(sound_lookup)
            if not type:
                logging.error(f'Unknown pacenote type: {sound_lookup}')
                exit(1)

            # get the rbr pacenote
            notes = self.get_rbr_pacenotes(type=type, package=package)

            if len(notes) != 1:
                logging.error(f'{sound}: Found {len(notes)} notes for type {type} - {notes}')

            logging.debug(f'{sound}: - type: {type} - note: {notes}')

            for note in notes:
                cc_note.add_note(note)

            cc_notes.append(cc_note)

        self.mapped_cc_notes = cc_notes

    def write_cc_notes(self):
        logging.debug(f'writing {len(self.mapped_cc_notes)} notes')
        # iterate through the pacenotes
        for id, note in self.mapped_cc_notes.items():
            note.create()

    def rbr_list_csv(self):
        csv_writer = csv.writer(sys.stdout)
        csv_writer.writerow(['style', 'id', 'name', 'type', 'category', 'package', 'ini', 'sound_count', 'translation', 'sound'])
        for name, rbr_pacenote_plugin in self.rbr_pacenote_plugins.items():
            notes = rbr_pacenote_plugin.pacenotes
            notes = sorted(notes, key=lambda x: x.id)

            for note in notes:
                for sound in note.sounds:
                    csv_writer.writerow([name, note.id, note.name, note.type, note.category, note.package, note.ini, note.sound_count, note.translation, sound])

    def cc_list_csv(self):
        csv_writer = csv.writer(sys.stdout)
        csv_writer.writerow(['type', 'file', 'subtitle'])
        notes = sorted(self.mapped_cc_notes, key=lambda x: x.name)
        for note in notes:
            for sound, subtitle in note.sounds.items():
                csv_writer.writerow([note.name, sound, subtitle])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # get commandline arguments and parse them
    parser = argparse.ArgumentParser(description='CoDriver')
    parser.add_argument('--config', help='Configuration file', default='config.json')
    parser.add_argument('--rbr-list', action='store_true', help='List RBR pacenotes')
    parser.add_argument('--rbr-list-csv', action='store_true', help='List RBR pacenotes as CSV')
    parser.add_argument('--rbr-find-note-by-name', help='Find a note by name')
    parser.add_argument('--map-to-cc-csv', action='store_true', help='Map RBR pacenotes to CC pacenotes and write to CSV')

    args = parser.parse_args()

    # read the configuration file, which is a json file
    config = json.load(open(args.config))

    codriver = CoDriver(
        cc_sounds=config['cc_sounds'],
        skip_notes=config.get('skip_notes', {}),
        map_notes=config.get('map_notes', []),
        map_cc_types=config.get('map_cc_types', {}),
        additional_cc_types=config.get('additional_cc_types', {}),
    )

    for package in config['packages']:
        pacenote_dir_absolute = os.path.join(base_dir, package['base_dir'])
        ini_files = package['ini_files']
        rbr_pacenote_plugin = RbrPacenotePlugin(pacenote_dir_absolute, ini_files=ini_files)
        codriver.add_pacenote_plugin(package['type'], rbr_pacenote_plugin)


    # if args.rbr_list:
    #     notes = rbr_pacenote_plugin.pacenotes.values()
    #     # sort notes by id
    #     notes = sorted(notes, key=lambda x: x.id)

    #     for note in notes:
    #         print(f'{note}')
    # descriptive,2109,small_crest,PACENOTE,OBSTACLES,RBR_ENHANCED,Extended.ini,2,,pikkunyppy2.ogg

    if args.rbr_list_csv:
        codriver.rbr_list_csv()

    if args.rbr_find_note_by_name:
        note = codriver.get_rbr_pacenote_by_name(args.rbr_find_note_by_name)
        if note:
            print(note)
        else:
            print(f'Not found: {args.rbr_find_note_by_name}')

    if args.map_to_cc_csv:
        codriver.map_notes_from_cc()
        codriver.cc_list_csv()


# Links
#  https://thecrewchief.org/showthread.php?1851-Richard-Burns-Rally-Crew-Chief-setup-and-known-issues
#  https://thecrewchief.org/showthread.php?825-Authoring-alternative-Crew-Chief-voice-packs
#  https://gitlab.com/mr_belowski/CrewChiefV4/-/blob/master/complete-radioerize-from-raw.txt
#  https://nerdynav.com/best-ai-voice-generators/
#  https://github.com/Smo-RBR/RBR-German-tts-Codriver

