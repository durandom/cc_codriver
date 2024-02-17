import configparser
import csv
import logging
import os
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

                note_id = int(section[1:])
                self.notes[note_id] = note

    def get_notes(self, note_type):
        notes = []
        for note_id, note in self.notes.items():
            if note.type == note_type:
                notes.append(note)
        return notes

    def note_types(self):
        types = set()
        for note in self.notes.values():
            types.add(note.type)
        return types

class Roadbooks:
    def __init__(self, path):
        self.base_path = path
        self.books = {}

    def read_roadbooks(self, name):
        # recurse into self.base_path
        logging.info(f"Analyzing {name}")
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if name == file or name == 'all':
                    if file.endswith('.ini'):
                        self.read_roadbook(file, os.path.join(root, file))

    def read_roadbook(self, name, filename):
        book = Roadbook(filename)
        self.books[name] = book

    def analyze_books(self):
        # get all note types
        note_types = set()
        for book in self.books.values():
            note_types |= book.note_types()

        note_types_list = sorted(list(note_types))
        csv_writer = csv.writer(sys.stdout)
        row = note_types_list.copy()
        row.insert(0, 'name')
        csv_writer.writerow(row)

        for name, book in self.books.items():
            row = []
            row.append(name)
            for note_type in note_types_list:
                book_note_types = book.get_notes(note_type)
                row.append(len(book_note_types))
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
