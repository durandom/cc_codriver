import configparser


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
        config = configparser.ConfigParser()
        config.read(filename)

        for section in config.sections():
            if section == 'PACENOTES':
                self.num_notes = config.getint(section, 'count')
                continue

            if section.startswith('P'):
                note = Note(config.get(section, 'type'),
                            config.get(section, 'distance'),
                            config.get(section, 'flag'))

                note_id = int(section[1:])
                self.notes[note_id] = note


    def note_types(self):
        types = set()
        for note in self.notes.values():
            types.add(note.type)
        return types


if __name__ == "__main__":
    book = Roadbook("Luppis Pacenote Pack V2 [26.1.2024]/ALL PACENOTES/PACENOTE WITH FOLDER STRUCTURE/Plugins/NGPCarMenu/MyPacenotes/Ahvenus I BTB/Ahvenus I_default.ini")

    print(book.num_notes)
    print(book.note_types())
