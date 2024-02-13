#!/usr/bin/env python3

import argparse
import csv
import os
import logging
import sys
from rbr_pacenote_plugin import RbrPacenotePlugin


class PacenoteType:
    def __init__(self, name, id):
        self.name = name
        self.id = id

    def rbr_name(self):
        translation_table = {
            'corner_1' : 'one',
            'corner_2' : 'two',
            'corner_3' : 'three',
            'corner_4' : 'four',
            'corner_5' : 'five',
            'corner_6' : 'six',
        }

        _rbr_name = self.name
        for key, value in translation_table.items():
            _rbr_name = _rbr_name.replace(key, value)

        print(f'{self.name} -> {_rbr_name}')
        return _rbr_name

    def __str__(self):
        return f'{self.name} - {self.id}'

class CrewChiefNote:
    def __init__(self, name):
        self.name = name
        self.sounds = {} # soundfile: subtitle

    def create(self):
        print(f'{self.name}')

    def add_sound(self, file, subtitle):
        self.sounds[file] = subtitle

    def __str__(self):
        return f'{self.name} - {self.sounds}'

class CoDriver:
    def __init__(self, rbr_pacenote_plugin = None):
        self.cc_pacenotes_types = {}
        self.cc_sounds = {}
        self.rbr_sounds = {}
        self.mapped_cc_notes = {}
        self.rbr_pacenote_plugin = rbr_pacenote_plugin
        self.rbr_pacenotes = rbr_pacenote_plugin.pacenotes

    # 2. Get the mapping from CC CoDriver.cs
    # public enum PacenoteType
    # {
    #     // Weird naming is used to simplify sound reading.
    #     corner_1_left = 0,
    #     corner_square_left = 1,
    #     detail_finish = 22,
    def init_cc_pacenotes_types(self, file = "pacenote_type.txt"):
        # // Weird naming is used to simplify sound reading.
        # corner_1_left = 0,
        # iterate through the lines

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
                self.cc_pacenotes_types[id] = PacenoteType(name, id)

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

    def get_rbr_pacenote_by_name(self, name):
        for id, note in self.rbr_pacenotes.items():
            if note.name.lower() == name.lower():
                return note
        return None

    def get_rbr_pacenote_by_id(self, id):
        for note in self.rbr_pacenotes.values():
            if note.id == id:
                return note
        return None

    def get_pacenote_type_for_cc_sound(self, sound):
        for id, type in self.cc_pacenotes_types.items():
            if type.name.lower() == sound.lower():
                return type
        return None

    def map_notes(self):
        # iterate through the pacenotes
        for id, note in self.rbr_pacenotes.items():
            logging.debug(f'{note}')
            if note.id:
                type = self.get_pacenote_type_for_id(note.id)
                name = type.name
            else:
                logging.debug(f'no id')

            cc_note = CrewChiefNote(name)

            for sound in note.sounds:
                # get the path to the rbr sound file
                file = self.rbr_pacenote_plugin.sound_file(sound)
                if os.path.exists(file):
                    logging.debug(f'Found sound: {sound}')
                    cc_note.add_sound(file, "")
                else:
                    logging.error(f'Not found: {sound} - {file}')
                    return
    def map_notes_from_cc(self):
        ignore = [
            'acknowledge_end_recce',
            'acknowledge_start_recce'
        ]
        for sound in sorted(self.cc_sounds.keys()):
            if sound in ignore:
                logging.debug(f'ignoring {sound}')
                continue
            if sound.startswith('cmp_'):
                # remove the cmp_ prefix
                remainder = sound[4:]
                if remainder.startswith('into_'):
                    into = self.get_rbr_pacenote_by_name('into')
                    remainder = remainder[5:]
                # get the pacenote type
                type = self.get_pacenote_type_for_cc_sound(remainder)
                if not type:
                    logging.error(f'Unknown pacenote type: {remainder}')
                    exit(1)
                # get the rbr pacenote

                note = self.get_rbr_pacenote_by_name(type.rbr_name())
                if not note:
                    logging.error(f'Unknown pacenote: {type.id}')
                    exit(1)
                logging.debug(f'{sound}: - type: {type} - note: {note}')

                # create a new CrewChiefNote
                cc_note = CrewChiefNote(sound)
                for file in note.sounds:
                    subtitle = note.translation
                    cc_note.add_sound(file, subtitle)
                print(cc_note)

                print(sound)
                exit(1)
                continue
            print(f'{sound}')

    def write_cc_notes(self):
        logging.debug(f'writing {len(self.mapped_cc_notes)} notes')
        # iterate through the pacenotes
        for id, note in self.mapped_cc_notes.items():
            note.create()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    pacenote_dir = "Janne's Note Pack v2.0/English Numeric - Number First/Plugins/Pacenote"
    pacenote_ini = ["Rbr.ini", "Rbr-Enhanced.ini"]

    # pacenote_dir = "Pacenote"
    # pacenote_ini = ["Rbr.ini", "Rbr-Enhanced.ini"]

    # pacenote_dir = "RBR-German-tts-Codriver-main/Plugins/Pacenote"
    # pacenote_ini = ["Smo-Nummern_und_90.ini"]
    # pacenote_ini = ["Smo-Mix.ini"]

    # pacenote_dir = "Co_Driver_RBR_Deutsch_Bollinger_V1.1_22-12-03/David_Bollinger_(CH)/Deutsch Numerisch - Deskriptiv/Plugins/Pacenote"
    # pacenote_dir = "Co_Driver_RBR_Deutsch_Bollinger_V1.1_22-12-03/David_Bollinger_(CH)/Deutsch Numerisch - Nummer zuerst/Plugins/Pacenote"
    # pacenote_dir = "Co_Driver_RBR_Deutsch_Bollinger_V1.1_22-12-03/David_Bollinger_(CH)/Deutsch Numerisch - Kurve zuerst/Plugins/Pacenote"
    pacenote_ini = ["Rbr.ini"]

    pacenote_dir_absolute = os.path.join(base_dir, pacenote_dir)
    rbr_pacenote_plugin = RbrPacenotePlugin(pacenote_dir_absolute, pacenote_ini=pacenote_ini)

    codriver = CoDriver(rbr_pacenote_plugin=rbr_pacenote_plugin)
    codriver.init_cc_pacenotes_types("pacenote_type.txt")
    codriver.init_cc_sounds("codriver")
    # codriver.init_rbr_sounds("Pacenote/sounds/DavidBollinger")

    sounds = set(codriver.cc_sounds.keys())
    pacenotes = set(codriver.cc_pacenotes_types.keys())
    rbr_pacenotes = set(codriver.rbr_pacenotes.keys())
    # print(rbr_pacenotes)
    # print(len(rbr_pacenotes))
    rbr_sounds = set(codriver.rbr_sounds.keys())
    # print(rbr_sounds)

    # print(pacenotes - sounds)
    # print(sounds - pacenotes)

    # get commandline arguments and parse them
    parser = argparse.ArgumentParser(description='CoDriver')
    parser.add_argument('--rbr-list', action='store_true', help='List RBR pacenotes')
    parser.add_argument('--rbr-list-csv', action='store_true', help='List RBR pacenotes as CSV')
    parser.add_argument('--rbr-find-note-by-name', help='Find a note by name')
    parser.add_argument('--map-to-cc', action='store_true', help='Map RBR pacenotes to CC pacenotes')

    args = parser.parse_args()
    if args.rbr_list:
        notes = rbr_pacenote_plugin.pacenotes.values()
        # sort notes by id
        notes = sorted(notes, key=lambda x: x.id)

        for note in notes:
            print(f'{note}')

    if args.rbr_list_csv:
        notes = rbr_pacenote_plugin.pacenotes.values()
        # sort notes by id
        notes = sorted(notes, key=lambda x: x.id)

        csv_writer = csv.writer(sys.stdout)
        csv_writer.writerow(['id', 'name', 'type', 'category', 'package', 'ini', 'sound_count', 'sounds'])
        for note in notes:
            for sound in note.sounds:
                csv_writer.writerow([note.id, note.name, note.type, note.category, note.package, note.ini, note.sound_count, sound])

    if args.rbr_find_note_by_name:
        note = codriver.get_rbr_pacenote_by_name(args.rbr_find_note_by_name)
        if note:
            print(note)
        else:
            print(f'Not found: {args.rbr_find_note_by_name}')

    if args.map_to_cc:
        codriver.map_notes_from_cc()


# Links
#  https://thecrewchief.org/showthread.php?1851-Richard-Burns-Rally-Crew-Chief-setup-and-known-issues
#  https://thecrewchief.org/showthread.php?825-Authoring-alternative-Crew-Chief-voice-packs
#  https://gitlab.com/mr_belowski/CrewChiefV4/-/blob/master/complete-radioerize-from-raw.txt
#  https://nerdynav.com/best-ai-voice-generators/
#  https://github.com/Smo-RBR/RBR-German-tts-Codriver

