import configparser
import csv
import logging
import os
import re
import sys


class Note:
    # [P2]
    # type = 1649545214
    # distance = 0.00001
    # flag = 0
    def __init__(self, type, distance, flag):
        self.type = type
        self.distance = distance
        self.flag = flag

class Roadbook:
    def __init__(self, filename):
        self.notes = {}
        self.read_ini(filename)

    def read_ini(self, filename):
        config = configparser.ConfigParser(strict=False)
        encoding = 'utf-8'
        encoding = 'cp1252'
        logging.info(f"Reading {filename}")
        try:
            config.read(filename, encoding=encoding)
        except Exception as e:
            logging.error(f'Error reading {filename}: {e}')
            # work around for configparser not handling utf-8
            with open(filename, 'r', encoding=encoding) as f:
                content = f.read()
            # remove the BOM
            content = content.replace('\ufeff', '')
            config.read_string(content)

        for section in config.sections():
            if section == 'PACENOTES':
                self.num_notes = config.getint(section, 'count')
                continue

            if section.startswith('P'):
                note = Note(config.getint(section, 'type'),
                            config.getfloat(section, 'distance'),
                            config.getint(section, 'flag'))

                # the high notes are not interesting
                if note.type > 6_000_000:
                    continue

                if note.flag > 65_000:
                    note.flag = 0

                note_id = int(section[1:])
                self.notes[note_id] = note

    def get_notes(self, note_type):
        notes = []
        for note_id, note in self.notes.items():
            if note.type == note_type:
                notes.append(note)
        return notes

    def get_notes_flag(self, note_flag):
        notes = []
        for note_id, note in self.notes.items():
            if note.flag == note_flag:
                notes.append(note)
        return notes

    def note_types(self):
        types = set()
        for note in self.notes.values():
            types.add(note.type)
        return types

    def note_flags(self):
        flags = set()
        for note in self.notes.values():
            flags.add(note.flag)
        return flags

class Roadbooks:
    def __init__(self, path):
        self.base_path = path
        self.books = {}

    def read_roadbooks(self, name):
        # recurse into self.base_path
        logging.info(f"Analyzing {name}")
        if name.startswith('/'):
            # name is a regex
            regex = name.lstrip('/')
            regex = regex.rstrip('/')
            name = re.compile(regex)
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if name == file or (isinstance(name, re.Pattern) and name.match(file)):
                    if file.endswith('.ini'):
                        self.read_roadbook(file, os.path.join(root, file))

    def read_roadbook(self, name, filename):
        book = Roadbook(filename)
        self.books[name] = book

    def analyze_books(self):
        # get all note types
        note_types = set()
        note_flags = set()
        for book in self.books.values():
            note_types |= book.note_types()
            note_flags |= book.note_flags()

        row = ['name']
        note_types_list = sorted(list(note_types))
        note_flags_list = sorted(list(note_flags))
        row.extend(note_types_list)
        # prepend 'flag_' to note_flags
        note_flags_list = [f'flag_{x}' for x in note_flags_list]
        row.extend(note_flags_list)

        csv_writer = csv.writer(sys.stdout)
        csv_writer.writerow(row)

        books = self.books.items()
        # sort by name
        books = sorted(books, key=lambda x: x[0])
        for name, book in books:
            row = []
            row.append(name)
            for note_type in note_types_list:
                book_note_types = book.get_notes(note_type)
                row.append(len(book_note_types))
            for note_flag in note_flags_list:
                book_note_flags = book.get_notes_flag(note_flag)
                row.append(len(book_note_flags))
            csv_writer.writerow(row)


    def csv_output(self, name, notes):
        note_types = sorted(notes.keys())
        for note_type in note_types:
            note_list = notes[note_type]
            print(f"{note_type}: {len(note_list)}")



if __name__ == "__main__":
    book = Roadbook("Luppis Pacenote Pack V2 [26.1.2024]/ALL PACENOTES/PACENOTE WITH FOLDER STRUCTURE/Plugins/NGPCarMenu/MyPacenotes/Ahvenus I BTB/Ahvenus I_default.ini")

    print(book.num_notes)
    print(book.note_types())
