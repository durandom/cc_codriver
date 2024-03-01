#!/usr/bin/env python3

import argparse
import csv
import json
import os
import logging
import shutil
import sys
from typing import Iterator, List, Mapping, Optional, Union
from rbr_pacenote_plugin import RbrPacenotePlugin, RbrPacenote
from roadbook import Roadbooks


class MappedNote:
    def __init__(self, note = None):
        if note:
            self.src = note.src
            self.type = note.type
            self.rbr_id = note.rbr_id
            self.popularity = note.popularity
            self.file = note.file
            self.subtitle = note.subtitle
            self.cc_note = note.cc_note
            self.rbr_note = note.rbr_note
        else:
            self.src = ''
            self.type = ''
            self.rbr_id = -1
            self.popularity = -1
            self.file = ''
            self.subtitle = ''
            self.cc_note : Optional[CrewChiefNote] = None
            self.rbr_note : Optional[RbrPacenote] = None

    def get_rbr_note(self) -> RbrPacenote:
        if not self.rbr_note:
            raise ValueError('No rbr_note set')
        return self.rbr_note

    def get_cc_note(self) -> 'CrewChiefNote':
        if not self.cc_note:
            raise ValueError('No cc_note set')
        return self.cc_note

    def set_sound_not_found(self):
        self.src = 'sound_not_found'

    def sound_not_found(self):
        return self.src == 'sound_not_found'

    def set_no_rbr_note(self):
        self.src = 'no_rbr_note'

    def no_rbr_note(self):
        return self.src == 'no_rbr_note'

    def set_no_sound_in_rbr_note(self):
        self.src = 'no_sound_in_rbr_note'

    def no_sound_in_rbr_note(self):
        return self.src == 'no_sound_in_rbr_note'

    def set_src_from_rbr(self):
        self.src = 'rbr'

    def is_rbr(self):
        return self.src == 'rbr'

    def set_src_from_rbr_base(self):
        self.src = 'rbr_base_note'

    def is_rbr_base(self):
        return self.src == 'rbr_base_note'

    def set_rbr_base_note_cc_type(self):
        self.src = 'rbr_base_note_cc_type'

    def is_rbr_base_note_cc_type(self):
        return self.src == 'rbr_base_note_cc_type'

    def set_rbr_base_note_cc_modifier(self):
        self.src = 'rbr_base_note_cc_modifier'

    def rbr_base_note_no_cc_type(self):
        self.src = 'rbr_base_note_no_cc_type'

    def as_dict(self):
        return {
            'src': self.src,
            'type': self.type,
            'rbr_id': self.rbr_id,
            'popularity': self.popularity,
            'file': self.file,
            'subtitle': self.subtitle,
        }

class PacenoteModifier:
    def __init__(self, name: str, id: int):
        self.name = name
        self.id = id
        self.translation_table = {
            'detail_' : '',
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
            'detail_' : '',
        }

class PacenoteRange(PacenoteModifier):
    def __init__(self, name: str, id: int = -1):
        # check if name is numeric
        if not name.isnumeric():
            raise ValueError(f'Invalid name: {name} for PacenoteRange')
        # just call the parent constructor
        super().__init__(name, id)

class CrewChiefNote:

    def __init__(self, name: str, prefix: Optional['CrewChiefNote'] = None):
        self.name = name
        self.sounds = {} # soundfile: subtitle
        self.notes : List[RbrPacenote] = []
        self.rushed = False
        self.prefix = prefix
        self.type : Optional[Union[PacenoteType, PacenoteModifier, PacenoteRange]] = None

    def set_type(self, type: Union[PacenoteType, PacenoteModifier, PacenoteRange]):
        self.type = type

    def add_prefix(self, prefix: 'CrewChiefNote'):
        self.prefix = prefix

    def add_notes(self, notes: List[RbrPacenote]):
        for note in notes:
            self.add_note(note)

    def add_note(self, note: RbrPacenote):
        self.notes.append(note)

    def add_file(self, file, package, sounds_dir, id = -1):
        rbr_note = RbrPacenote(file)
        rbr_note.id = id
        rbr_note.sounds.append(file)
        rbr_note.sounds_dir = sounds_dir
        rbr_note.package = package
        self.notes.append(rbr_note)

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
                 map_static = {},
                 additional_cc_types = {},
                 pacenote_stats = '',
                 fallback_to_base = False,
                 skip_notes = {}):

        self.cc_pacenotes_types = {}
        self.cc_pacenotes_modifiers = {}
        self.cc_sounds = {}
        self.cc_sounds_dir = cc_sounds
        self.rbr_sounds = {}
        self.rbr_pacenote_plugins = {}
        self.skip_notes = skip_notes
        self.map_notes = map_notes
        self.map_rbr_ids = {}
        self.map_cc_types = map_cc_types
        self.map_static = map_static
        self.additional_cc_types = additional_cc_types
        self.fallback_to_base = fallback_to_base
        self.pacenote_stats = self.init_pacenote_stats(pacenote_stats)

        self.init_cc_pacenotes_types(cc_pacenote_types)
        self.init_cc_pacenotes_modifier(cc_pacenote_modifier)
        self.init_cc_sounds(self.cc_sounds_dir)

        self.mapped_cc_notes : List[CrewChiefNote] = []

    def set_base_codriver(self, base_codriver, package):
        self.base_codriver = base_codriver
        self.base_codriver_package = package

    def add_pacenote_plugin(self, type, rbr_pacenote_plugin, map_rbr_ids = {}):
        self.rbr_pacenote_plugins[type] = rbr_pacenote_plugin
        self.map_rbr_ids[type] = map_rbr_ids

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

    def init_pacenote_stats(self, pacenote_stats):
        stats = {
            'count': {},
            'popularity': {},
            'seen_per_stage': {},
            'stages': []
        }
        if pacenote_stats:
            # open pacenote_stats as a csv file
            with open(pacenote_stats, mode='r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    stats['stages'].append(row)
                    for key, value in row.items():
                        if key.isnumeric():
                            id = int(key)
                            count = int(value)
                            if not id in stats['count']:
                                stats['count'][id] = 0
                            stats['count'][id] += count

                            if not id in stats['seen_per_stage']:
                                stats['seen_per_stage'][id] = 0
                            if count > 0:
                                stats['seen_per_stage'][id] += 1

            # calculate popularity
            # 100 means it is in every stage
            # 0 means it is in no stage
            count_stages = len(stats['stages'])
            for id, count in stats['seen_per_stage'].items():
                stats['popularity'][id] = round(count / count_stages, 2)
        return stats

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
            cc_name = mapping.get('cc_name')
            if name == cc_name:
                id = mapping.get('rbr_id', id)
                name = mapping.get('rbr_name', name)

        # if mapping for package is configured
        package_mapping = self.map_rbr_ids.get(package, {})
        for from_id, to_id in package_mapping.items():
            if id == from_id:
                if isinstance(to_id, int):
                    id = to_id
                else:
                    package = to_id[0]
                    id = to_id[1]

                if isinstance(id, str):
                    name = id
                    id = -1
                break

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

        return []

    def get_pacenote_type_for_cc_sound(self, sound) -> Union[PacenoteType, PacenoteModifier, PacenoteRange, None]:
        for id, type in self.cc_pacenotes_types.items():
            if type.name.lower() == sound.lower():
                return type
        for id, type in self.cc_pacenotes_modifiers.items():
            if type.name.lower() == sound.lower():
                return type

        if sound.isnumeric():
            return PacenoteRange(sound)

        return None

    def map_package_and_type(self, type = '', package = 'numeric'):
        for src, dst in self.map_cc_types.items():
            if type == src:
                type = dst
                break

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
        into = CrewChiefNote('detail_into')
        into.set_type(type)
        into.add_notes(notes)

        for sound in sorted(self.cc_sounds.keys()):
            if sound in self.skip_notes.keys():
                logging.debug(f'ignoring {sound}')
                continue

            sound_lookup = sound

            # create a new CrewChiefNote
            cc_note = CrewChiefNote(sound)

            if sound in self.map_static:
                rbr_id = -1
                if len(self.map_static[sound]) == 2:
                    (package, file) = self.map_static[sound]
                elif len(self.map_static[sound]) == 3:
                    (package, file, rbr_id) = self.map_static[sound]
                else:
                    raise ValueError(f'Invalid map_static: {self.map_static[sound]}')

                sound_dir = self.rbr_pacenote_plugins[package].sounds_dir()

                if isinstance(file, list):
                    prefix = file[0]
                    prefix_note = CrewChiefNote(prefix)
                    prefix_note.add_file(prefix, package, sound_dir)
                    cc_note.add_prefix(prefix_note)
                    file = file[1]

                if sound_lookup.endswith('_rushed'):
                    cc_note.rushed = True

                cc_note.add_file(file, package, sound_dir, rbr_id)
                cc_notes.append(cc_note)
                continue

            if sound.startswith('cmp_'):
                # remove the cmp_ prefix
                sound_lookup = sound[4:]

                if sound_lookup.startswith('into_'):
                    sound_lookup = sound_lookup[5:]
                    cc_note.prefix = into

            if sound_lookup.endswith('_rushed'):
                sound_lookup = sound_lookup[:-7]
                cc_note.rushed = True

            if sound_lookup.startswith('number_'):
                sound_lookup = sound_lookup[7:]

            (package, sound_lookup) = self.map_package_and_type(type=sound_lookup)

            # get the pacenote type
            type = self.get_pacenote_type_for_cc_sound(sound_lookup)
            if not type:
                logging.error(f'Unknown pacenote type: {sound_lookup}')
                continue
            if package not in self.rbr_pacenote_plugins:
                logging.error(f'Unknown package: {package}')
                continue
            cc_note.set_type(type)

            # also set the type for the not mapped note
            if sound in self.cc_sounds:
                self.cc_sounds[sound].set_type(type)

            # get the rbr pacenote
            notes = self.get_rbr_pacenotes(type=type, package=package)

            if len(notes) != 1:
                logging.error(f'{sound}: Found {len(notes)} notes for type {type} - {notes}')

            logging.debug(f'{sound}: - type: {type} - note: {notes}')

            for note in notes:
                cc_note.add_note(note)

            cc_notes.append(cc_note)

        self.mapped_cc_notes = cc_notes


    def cc_copy_original_sounds(self, type, dst_path):
        # just copy the original sound
        src = os.path.join(self.cc_sounds_dir, type)
        # copy each file from src directory to the destination directory
        for file in os.listdir(src):
            file = os.path.join(src, file)
            shutil.copy(file, dst_path)

    def cc_copy_note(self, note : MappedNote, dst_path):
        if not os.path.exists(dst_path):
            os.makedirs(dst_path)

        cc_note = note.get_cc_note()
        rbr_note = note.get_rbr_note()
        prefix = None
        if cc_note.prefix:
            prefix = cc_note.prefix.notes[0]
        sound = note.file
        wave_file = rbr_note.sound_as_wav(sound, prefix=prefix, rushed=cc_note.rushed)
        wave_file = os.path.join(rbr_note.sounds_dir, wave_file)
        shutil.copy(wave_file, dst_path)

        # create subtitles.csv
        with open(os.path.join(dst_path, 'subtitles.csv'), mode='a+', encoding='utf-8') as file:
            csv_writer = csv.writer(file)
            subtitle = rbr_note.translation
            sound_file_basename = note.file
            csv_writer.writerow([sound_file_basename, subtitle])

    def get_popularity(self, note : Union[RbrPacenote, CrewChiefNote, int]):
        popularity = 0
        rbr_id = -1
        if isinstance(note, CrewChiefNote):
            if note.type:
                rbr_id = note.type.id
        elif isinstance(note, RbrPacenote):
            rbr_id = note.id
        else:
            rbr_id = int(note)

        popularity = self.pacenote_stats['popularity'].get(rbr_id, -1)
        return popularity

    def mapped_notes(self):
        mapped_base_notes = []
        if self.fallback_to_base:
            self.base_codriver.map_notes_from_cc()
            for base_note in self.base_codriver.mapped_notes():
                mapped_base_notes.append(base_note)

        cc_sounds = sorted(self.cc_sounds.values(), key=lambda x: x.name)
        for cc_note in cc_sounds:
            yield_note = MappedNote()

            # find the mapped note
            mapped_cc_note = next((x for x in self.mapped_cc_notes if x.name == cc_note.name), None)
            yield_note.cc_note = mapped_cc_note

            mapped_base_note = None
            if self.fallback_to_base:
                for base_note in mapped_base_notes:
                    if base_note.type == cc_note.name and base_note.is_rbr():
                        base_note.set_src_from_rbr_base()
                        mapped_base_note = base_note
                        break

            if not mapped_cc_note:
                yield_note.set_no_rbr_note()
                yield_note.type = cc_note.name
                if self.fallback_to_base and mapped_base_note:
                    yield mapped_base_note
                else:
                    yield yield_note
                continue

            yield_note.type = mapped_cc_note.name

            if mapped_cc_note and len(mapped_cc_note.notes) == 0:
                logging.error(f'No sounds for {cc_note.name} in mapped note {mapped_cc_note}')
                yield_note.set_no_rbr_note()
                if mapped_cc_note.type:
                    yield_note.rbr_id = mapped_cc_note.type.id
                popularity = self.get_popularity(yield_note.rbr_id)
                yield_note.popularity = popularity
                if self.fallback_to_base and mapped_base_note:
                    yield mapped_base_note
                else:
                    yield yield_note
                continue

            if mapped_cc_note.type:
                yield_note.rbr_id = mapped_cc_note.type.id

            # process the mapped note
            rbr_notes = mapped_cc_note.notes
            rbr_notes = sorted(rbr_notes, key=lambda x: (x.id, x.name, x.category, x.translation))
            for rbr_note in rbr_notes:
                yield_note.rbr_note = rbr_note
                subtitle = rbr_note.translation
                popularity = self.get_popularity(rbr_note)
                for sound in sorted(rbr_note.sounds):
                    file = sound
                    yield_note.type = cc_note.name
                    yield_note.rbr_id = rbr_note.id
                    yield_note.popularity = popularity
                    yield_note.file = file
                    yield_note.subtitle = subtitle
                    if file in rbr_note.sounds_not_found:
                        yield_note.set_sound_not_found()
                        if self.fallback_to_base and mapped_base_note:
                            yield mapped_base_note
                        else:
                            yield yield_note
                    else:
                        yield_note.set_src_from_rbr()
                        yield yield_note

    def unmapped_base_mod_notes(self) -> Iterator[MappedNote]:
        # collect all rbr notes from all plugins
        rbr_base_mod_notes = self.base_codriver.rbr_pacenote_plugins[
            self.base_codriver_package
        ].pacenotes

        # collect all rbr notes for this codriver
        rbr_notes = set()
        for rbr_pacenote_plugin in self.rbr_pacenote_plugins.values():
            rbr_notes |= rbr_pacenote_plugin.pacenotes

        # collect all mapped notes for this codriver
        mapped_notes : List[MappedNote] = []
        for note in self.mapped_notes():
            mapped_notes.append(note)

        # iterate through all rbr notes
        rbr_base_mod_notes = list(rbr_base_mod_notes)
        rbr_base_mod_notes = sorted(rbr_base_mod_notes, key=lambda x: (x.id, x.name, x.category, x.translation))
        for rbr_note in rbr_base_mod_notes:
            yield_note = MappedNote()
            # check if the note is mapped in our codriver
            found = False
            for mapped_note in mapped_notes:
                if mapped_note.rbr_note:
                    if mapped_note.rbr_id >= 0:
                        if rbr_note.id == mapped_note.rbr_id:
                            found = True
                            break
                    else:
                        if rbr_note.name == mapped_note.rbr_note.name:
                            found = True
                            break

            if not found:
                for package in self.rbr_pacenote_plugins.keys():
                    package_mapping = self.map_rbr_ids.get(package, {})
                    for from_id, to_id in package_mapping.items():
                        if rbr_note.id == from_id:
                            found = True
                            break


            # the note is not mapped
            if not found:
                base_note = rbr_note
                # try to find the rbr_note in our rbr_notes
                for my_rbr_note in rbr_notes:
                    if rbr_note.id >= 0:
                        if my_rbr_note.id == rbr_note.id:
                            rbr_note = my_rbr_note
                            break
                    elif my_rbr_note.name == rbr_note.name:
                        rbr_note = my_rbr_note
                        break

                popularity = self.get_popularity(rbr_note)
                yield_note.popularity = popularity
                # check if id is in pacenote_types or pacenote_modifiers
                yield_note.rbr_note = rbr_note
                yield_note.rbr_id = rbr_note.id
                subtitle = rbr_note.translation
                yield_note.subtitle = subtitle
                if rbr_note.id in self.cc_pacenotes_types:
                    cc_note = CrewChiefNote('detail_' + rbr_note.name)
                    cc_note.set_type(self.cc_pacenotes_types[rbr_note.id])
                    yield_note.cc_note = cc_note
                    yield_note.type = cc_note.name
                    yield_note.set_rbr_base_note_cc_type()
                elif rbr_note.id in self.cc_pacenotes_modifiers:
                    yield_note.type = rbr_note.name
                    yield_note.set_rbr_base_note_cc_modifier()
                else:
                    yield_note.rbr_base_note_no_cc_type()
                    yield_note.type = rbr_note.name

                for sound in sorted(rbr_note.sounds):
                    file = sound
                    yield_note.file = file
                    if file in rbr_note.sounds_not_found:
                        yield_note.set_sound_not_found()
                        if self.fallback_to_base:
                            yield_note.rbr_note = base_note
                        else:
                            continue
                    yield yield_note

    def cc_list_csv(self):
        csv_writer = csv.DictWriter(sys.stdout, MappedNote().as_dict().keys())
        csv_writer.writeheader()

        for note in self.mapped_notes():
            csv_writer.writerow(note.as_dict())

        for note in self.unmapped_base_mod_notes():
            csv_writer.writerow(note.as_dict())

    def rbr_list_csv(self):
        rbr_base_mod_notes = self.base_codriver.rbr_pacenote_plugins[
            self.base_codriver_package
        ].pacenotes
        rbr_base_mod_notes = list(rbr_base_mod_notes)
        rbr_base_mod_notes = sorted(rbr_base_mod_notes, key=lambda x: (x.name, x.id, x.category, x.translation))

        csv_writer = csv.writer(sys.stdout)
        csv_writer.writerow(['style', 'id', 'name', 'type', 'category', 'package', 'ini', 'sound_count', 'translation', 'sound', 'popularity', 'error'])
        for name, rbr_pacenote_plugin in self.rbr_pacenote_plugins.items():
            notes = rbr_pacenote_plugin.pacenotes
            # sort notes by id and name
            notes = sorted(notes, key=lambda x: (x.id, x.name, x.category))

            for note in notes:
                popularity = self.get_popularity(note)
                for sound in note.sounds:
                    error = ''
                    if sound in note.sounds_mapped.values():
                        from_sound = next((k for k, v in note.sounds_mapped.items() if v == sound), None)
                        error = f'file mapped from {from_sound}'
                    if sound in note.sounds_not_found:
                        error = 'file missing'
                    csv_writer.writerow([name, note.id, note.name, note.type, note.category, note.package, note.ini, note.sound_count, note.translation, sound, popularity, error])

            name = 'base_mod'
            for base_note in rbr_base_mod_notes:
                found = False
                for note in notes:
                    if note.id >= 0:
                        if note.id == base_note.id:
                            found = True
                            break
                    elif note.name == base_note.name:
                        found = True
                        break

                if not found:
                    note = base_note
                    popularity = self.get_popularity(note)
                    for sound in note.sounds:
                        error = ''
                        if sound in note.sounds_mapped.values():
                            from_sound = next((k for k, v in note.sounds_mapped.items() if v == sound), None)
                            error = f'file mapped from {from_sound}'
                        if sound in note.sounds_not_found:
                            error = 'file missing'
                        csv_writer.writerow([name, note.id, note.name, note.type, note.category, note.package, note.ini, note.sound_count, note.translation, sound, popularity, error])

    def create_codriver(self, directory):
        # create the directory
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            logging.debug(f'Directory {directory} already exists')

        # copy terminologies.json
        src = os.path.join('terminologies.json')
        shutil.copy(src, directory)

        # create csvwriter for logging the mapping
        log_csv_file_name = os.path.join(directory, 'rbr_to_cc_mapping.csv')
        log_csv_file = open(log_csv_file_name, mode='w', encoding='utf-8')
        log_writer = csv.DictWriter(log_csv_file, MappedNote().as_dict().keys())
        log_writer.writeheader()

        for note in self.mapped_notes():
            dst_path = os.path.join(directory, note.type)
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)
            else:
                logging.debug(f'Directory {dst_path} already exists')

            if note.no_rbr_note():
                logging.error(f'No mapping for {note.type} - using original sound')
                self.cc_copy_original_sounds(note.type, dst_path)
                log_writer.writerow(note.as_dict())
                continue

            if note.no_sound_in_rbr_note():
                logging.error(f'No sounds for {note.type} in mapped note {note.rbr_note}')
                self.cc_copy_original_sounds(note.type, dst_path)
                log_writer.writerow(note.as_dict())
                continue

            if note.sound_not_found():
                logging.error(f'No sound found for {note.type} in mapped note {note.rbr_note}')
                self.cc_copy_original_sounds(note.type, dst_path)
                log_writer.writerow(note.as_dict())
                continue

            self.cc_copy_note(note, dst_path)
            log_writer.writerow(note.as_dict())

        for note in self.unmapped_base_mod_notes():
            if note.is_rbr_base_note_cc_type():
                # prepend 'detail_' to the name
                dst_path = os.path.join(directory, note.type)
                log_writer.writerow(note.as_dict())
                self.cc_copy_note(note, dst_path)

        if False:
            # find the note in our rbr_pacenote_plugins
            for rbr_note in self.rbr_pacenote_plugins['numeric'].pacenotes:
                if rbr_note.name == note.type:
                    if rbr_note.id in self.cc_pacenotes_types:
                        type = self.cc_pacenotes_types[rbr_note.id]
                        if type.name.startswith('detail_'):
                            logging.debug(f'Found {rbr_note.name} in rbr_pacenote_plugins')
                            dst_path = os.path.join(directory, type.name)

                            copied_from_package = False
                            for sound in sorted(rbr_note.sounds):
                                if sound in rbr_note.sounds_not_found:
                                    log_writer.writerow(note.as_dict())
                                    continue
                                copied_from_package = True
                                mapped_note = MappedNote(note)
                                mapped_note.cc_note = CrewChiefNote(type.name)
                                mapped_note.rbr_note = rbr_note
                                mapped_note.file = sound
                                mapped_note.subtitle = rbr_note.translation
                                if mapped_note.file in rbr_note.sounds_mapped:
                                    mapped_note.file = rbr_note.sounds_mapped[note.file]
                                log_writer.writerow(note.as_dict())
                                self.cc_copy_note(mapped_note, dst_path)

                            if not copied_from_package:
                                note.set_sound_not_found()
                                log_writer.writerow(note.as_dict())

        log_csv_file.close()

def make_codriver(name, config, config_package = 'all', fallback_to_base = False):
    config_codriver_packages = config['codrivers'][name]['packages']
    map_files = config['codrivers'][name].get('map_files', {})
    additional_sounds_dir = config['codrivers'][name].get('additional_sounds_dir', '')
    map_static = config['codrivers'][name].get('map_static', {})

    codriver = CoDriver(
        cc_sounds=config['cc_sounds'],
        skip_notes=config.get('skip_notes', {}),
        map_notes=config.get('map_notes', []),
        map_cc_types=config.get('map_cc_types', {}),
        additional_cc_types=config.get('additional_cc_types', {}),
        map_static=map_static,
        fallback_to_base=fallback_to_base,
        pacenote_stats=config.get('pacenote_stats', {}),
    )

    if config_package != 'all':
        # select only the package that is specified
        config_codriver_packages = [ package for package in config_codriver_packages if package['type'] == config_package]
    for package in config_codriver_packages:
        pacenote_dir_absolute = os.path.join(base_dir, package['base_dir'])
        ini_files = package['ini_files']
        map_rbr_ids = package.get('map_rbr_ids', {})
        # convert the keys to int
        # remove all keys that are note numeric
        map_rbr_ids = {int(k): v for k, v in map_rbr_ids.items() if k.isnumeric()}
        rbr_pacenote_plugin = RbrPacenotePlugin(pacenote_dir_absolute,
                                                ini_files=ini_files,
                                                map_files=map_files,
                                                additional_sounds_dir=additional_sounds_dir)
        codriver.add_pacenote_plugin(package['type'], rbr_pacenote_plugin, map_rbr_ids)

    return codriver

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # get commandline arguments and parse them
    parser = argparse.ArgumentParser(description='CoDriver')
    parser.add_argument('--codriver', help='Codriver in config.json', default='bollinger')
    parser.add_argument('--rbr-find-note-by-name', help='Find a note by name')
    parser.add_argument('--rbr-list-csv', action='store_true', help='List RBR pacenotes as CSV')
    parser.add_argument('--rbr-package', default='all', help='Only list pacenotes for a specific package, defaults to all')
    parser.add_argument('--roadbook-csv', action='store_true', help='Analyzes a Roabook file and creates a CSV file')
    parser.add_argument('--roadbook-csv-v3', action='store_true', help='Analyzes a Roabook file and creates a CSV file')
    parser.add_argument('--roadbook-name', default='/.*/', help='Which Roabook file to analyze, defaults to all')
    parser.add_argument('--create-codriver', help='Map RBR pacenotes to CC pacenotes and create folder structure')
    parser.add_argument('--codriver-fallback-to-base', action='store_true', help='Use sound from base codriver if not found')
    parser.add_argument('--map-to-cc-csv', action='store_true', help='Map RBR pacenotes to CC pacenotes and write to CSV')

    args = parser.parse_args()

    # read the configuration file, which is a json file
    config = json.load(open('config.json'))

    if args.roadbook_csv:
        roadbook_dir = config['roadbooks']
        roadbooks = Roadbooks(roadbook_dir)
        roadbooks.read_roadbooks(args.roadbook_name)
        roadbooks.analyze_books()
        exit(0)

    if args.roadbook_csv_v3:
        roadbook_dir = config['roadbooks_v3']
        roadbooks = Roadbooks(roadbook_dir)
        roadbooks.read_roadbooks(args.roadbook_name)
        roadbooks.analyze_books()
        exit(0)

    codriver_name = args.codriver
    codriver = make_codriver(codriver_name, config, args.rbr_package, fallback_to_base=args.codriver_fallback_to_base)

    rbr_base_mod = config['rbr_base_mod']
    rbr_base_package = config['rbr_base_package']
    codriver_base = make_codriver(rbr_base_mod, config)

    codriver.set_base_codriver(codriver_base, rbr_base_package)

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

    if args.create_codriver:
        codriver.map_notes_from_cc()
        codriver.create_codriver(args.create_codriver)
