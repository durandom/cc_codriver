import csv
import os
import configparser
import logging

class RbrPacenotes:
    def __init__(self, ini_file = "Pacenote/config/pacenotes/Rbr.ini"):
        self.pacenotes = {}
        # self.ini_file = ini_file
        # base_dir is the directory of this file + ini_file
        self.ini_file = ini_file
        self.base_dir = os.path.dirname(self.ini_file)
        logging.debug(f'base: {self.base_dir}')


    def read_ini(self, ini_file = None, recursion = 0, category = None, package = None):
        if ini_file is None:
            ini_file = self.ini_file
        else:
            # replace backslash with slash
            ini_file = ini_file.replace('\\', '/')
            ini_file = os.path.join(self.base_dir, ini_file)

        short_file = ini_file.replace(self.base_dir, '')
        logging.debug("%sfile: %s" % (recursion * "\t", short_file))
        current_base_dir = os.path.dirname(ini_file)

        config = configparser.ConfigParser()
        config.read(ini_file)
        # check if the file is valid
        if len(config.sections()) == 0:
            logging.error("Invalid file: %s" % ini_file)
            return
        for section in config.sections():
            if section.startswith('PACKAGE') or section.startswith('CATEGORY'):
                (package_or_category, name) = section.split('::')
                if package_or_category == 'PACKAGE':
                    package = name
                if package_or_category == 'CATEGORY':
                    category = name

                for option in config.options(section):
                    if option.startswith('file'):
                        file = config.get(section, option).replace('\\', '/')
                        # prepend the base directory
                        file = os.path.join(current_base_dir, file)
                        self.read_ini(file,
                                      recursion + 1,
                                      package=package,
                                      category=category)

            note = {}
            name = ''
            if section.startswith('PACENOTE') or section.startswith('RANGE'):
                (type, name) = section.split('::')
                note['type'] = type
                note['name'] = name
                note['category'] = category
                note['package'] = package
                note['id'] = config.get(section, 'id', fallback=None)
                if not note['id']:
                    logging.debug(f'No id in {section}')
                else:
                    note['id'] = int(note['id'])
                sounds = config.get(section, 'Sounds', fallback=0)
                note['sounds'] = []
                for i in range(int(sounds)):
                    sound = config.get(section, 'Snd%d' % i)
                    note['sounds'].append(sound)
                    # sound = os.path.join(current_base_dir, sound)

            if name:
                if name not in self.pacenotes:
                    # logging.debug('New pacenote id: %s - %s' % (id, section))
                    self.pacenotes[name] = note


class PacenoteType:
    def __init__(self, name, id):
        self.name = name
        self.id = id

class CrewChiefNote:
    def __init__(self, name):
        self.name = name
        self.sounds = {} # soundfile: subtitle

    def create(self):
        print(f'{self.name}')

    def add_sound(self, file, subtitle):
        self.sounds[file] = subtitle

class CoDriver:
    def __init__(self, rbr_dir = "./"):
        self.cc_pacenotes_types = {}
        self.cc_sounds = {}
        self.rbr_pacenotes = {}
        self.rbr_sounds = {}
        self.mapped_cc_notes = {}

        # read the pacenotes.ini
        rbr_pacenote_ini = "Pacenote/PaceNote.ini"
        self.rbr_dir = rbr_dir
        ini_file = os.path.join(rbr_dir, rbr_pacenote_ini)
        config = configparser.ConfigParser()
        config.read(ini_file)
        # get the 'SETTINGS' section
        settings = config['SETTINGS']
        # get the sounds and language
        self.sounds = settings.get('sounds')
        self.language = settings.get('language')


    # 1. Read pacenotes.ini
    # [PACENOTE::FINISH]
    # id=22
    # Sounds=1
    # Snd0=finish.ogg
    # column=-1

    def init_rbr_pacenotes(self, file = "Rbr.ini"):
        # open the Rbr.ini file and get the pacenotes
        file = os.path.join(self.rbr_dir, file)
        pacenotes = RbrPacenotes(file)
        pacenotes.read_ini()
        # merge with self.rbr_pacenotes
        for id, note in pacenotes.pacenotes.items():
            self.rbr_pacenotes[id] = note

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

    def map_notes(self):
        # iterate through the pacenotes
        for id, note in self.rbr_pacenotes.items():
            logging.debug(f'{note}')
            if note['id']:
                type = self.get_pacenote_type_for_id(note['id'])
                name = type.name
            else:
                logging.debug(f'no id')

            cc_note = CrewChiefNote(name)

            for sound in note['sounds']:
                file = os.path.join(self.rbr_dir, 'Pacenote', 'sounds', self.sounds, sound)
                if os.path.exists(file):
                    logging.debug(f'Found sound: {sound}')
                    cc_note.add_sound(file, "")
                else:
                    logging.error(f'Not found: {sound} - {file}')
                    return

    def write_cc_notes(self):
        logging.debug(f'writing {len(self.mapped_cc_notes)} notes')
        # iterate through the pacenotes
        for id, note in self.mapped_cc_notes.items():
            note.create()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    codriver = CoDriver(
        # rbr_pacenote_ini = "Pacenote/PaceNote.ini"
        rbr_dir=os.path.dirname(os.path.abspath(__file__))
    )

    codriver.init_cc_pacenotes_types("pacenote_type.txt")
    codriver.init_cc_sounds("codriver")
    codriver.init_rbr_pacenotes("Pacenote/config/pacenotes/Rbr.ini")
    codriver.init_rbr_pacenotes("Pacenote/config/ranges/Rbr.ini")
    # codriver.init_rbr_strings("")
    codriver.init_rbr_sounds("Pacenote/sounds/DavidBollinger")

    sounds = set(codriver.cc_sounds.keys())
    pacenotes = set(codriver.cc_pacenotes_types.keys())
    rbr_pacenotes = set(codriver.rbr_pacenotes.keys())
    # print(rbr_pacenotes)
    # print(len(rbr_pacenotes))
    rbr_sounds = set(codriver.rbr_sounds.keys())
    # print(rbr_sounds)

    # print(pacenotes - sounds)
    # print(sounds - pacenotes)

    codriver.map_notes()
    codriver.write_cc_notes()


# Links
#  https://thecrewchief.org/showthread.php?1851-Richard-Burns-Rally-Crew-Chief-setup-and-known-issues
#  https://thecrewchief.org/showthread.php?825-Authoring-alternative-Crew-Chief-voice-packs
#  https://gitlab.com/mr_belowski/CrewChiefV4/-/blob/master/complete-radioerize-from-raw.txt
#  https://nerdynav.com/best-ai-voice-generators/
#  https://github.com/Smo-RBR/RBR-German-tts-Codriver

