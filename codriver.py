import csv
import os
import configparser
import logging

class RbrPacenotes:
    def __init__(self, ini_file = "Pacenote/config/pacenotes/Rbr.ini"):
        self.pacenotes = {}
        # self.ini_file = ini_file
        # base_dir is the directory of this file + ini_file
        self.ini_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ini_file)
        self.base_dir = os.path.dirname(self.ini_file)


    def read_ini(self, ini_file = None, recursion = 0):
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
            for option in config.options(section):
                if option.startswith('file'):
                    file = config.get(section, option).replace('\\', '/')
                    # prepend the base directory
                    file = os.path.join(current_base_dir, file)
                    self.read_ini(file, recursion + 1)
                elif option == 'id':
                    id = config.get(section, option)
                    sounds = config.get(section, 'Sounds')
                    for i in range(int(sounds)):
                        sound = config.get(section, 'Snd%d' % i)
                        # sound = os.path.join(current_base_dir, sound)
                        if id in self.pacenotes:
                            self.pacenotes[id][i] = sound
                        else:
                            logging.debug('New pacenote id: %s - %s' % (id, section))
                            self.pacenotes[id] = {i: sound}


class PacenoteType:
    def __init__(self, name):
        self.name = name


class CoDriver:
    def __init__(self):
        self.cc_pacenotes_types = {}
        self.cc_sounds = {}
        self.rbr_pacenotes = {}
        self.rbr_sounds = {}

    # 1. Read pacenotes.ini
    # [PACENOTE::FINISH]
    # id=22
    # Sounds=1
    # Snd0=finish.ogg
    # column=-1

    def init_rbr_pacenotes(self, file = "Rbr.ini"):
        # open the Rbr.ini file and get the pacenotes
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
                key = parts[0].strip()
                value = parts[1].strip()
                self.cc_pacenotes_types[key] = PacenoteType(value)

    def init_cc_sounds(self, codriver_dir = "codriver"):
        # open the codriver directory and get all the subdirectories

        for root, dirs, files in os.walk(codriver_dir):
            if 'subtitles.csv' in files:
                    csv_path = os.path.join(root, 'subtitles.csv')
                    # folders_with_subtitles.append(root)

                    with open(csv_path, mode='r', encoding='utf-8') as file:
                        csv_reader = csv.DictReader(file)
                        data = [row for row in csv_reader]
                        basename = os.path.basename(root)
                        self.cc_sounds[basename] = data

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


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    codriver = CoDriver()

    codriver.init_cc_pacenotes_types("pacenote_type.txt")
    codriver.init_cc_sounds("codriver")
    codriver.init_rbr_pacenotes("Pacenote/config/pacenotes/Rbr.ini")
    codriver.init_rbr_pacenotes("Pacenote/config/ranges/Rbr.ini")
    codriver.init_rbr_sounds("Pacenote/sounds/DavidBollinger")

    sounds = set(codriver.cc_sounds.keys())
    pacenotes = set(codriver.cc_pacenotes_types.keys())
    rbr_pacenotes = set(codriver.rbr_pacenotes.keys())
    print(len(rbr_pacenotes))
    rbr_sounds = set(codriver.rbr_sounds.keys())
    # print(rbr_sounds)

    # print(pacenotes - sounds)
    # print(sounds - pacenotes)

    # for all cc_sounds find the corresponding pacenote type in cc
    # for name, note in codriver.pacenotes_types.items():

# Links
#  https://thecrewchief.org/showthread.php?1851-Richard-Burns-Rally-Crew-Chief-setup-and-known-issues
#  https://thecrewchief.org/showthread.php?825-Authoring-alternative-Crew-Chief-voice-packs
#  https://gitlab.com/mr_belowski/CrewChiefV4/-/blob/master/complete-radioerize-from-raw.txt
#  https://nerdynav.com/best-ai-voice-generators/
#  https://github.com/Smo-RBR/RBR-German-tts-Codriver

