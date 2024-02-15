import configparser
import logging
import os
from typing import Optional


class RbrPacenote:
    def __init__(self, name):
        self.name = name
        self.id = -1
        self.type = ''
        self.category = ''
        self.package = ''
        self.ini = ''
        self.sounds = []
        self.sound_count = 0
        self.translation = ''
        self.sounds_dir = ''

    def sound_as_wav(self, sound, prefix: Optional['RbrPacenote'] = None):
        ogg = os.path.join(self.sounds_dir, sound)
        if not os.path.exists(ogg):
            raise FileNotFoundError(f'Not found: {ogg}')

        # replace .ogg with .wav
        wave_filename = sound.replace('.ogg', '.wav')
        # check if the sound file exists
        wave_fullname = os.path.join(self.sounds_dir, wave_filename)
        if not os.path.exists(wave_fullname):
            # convert the sound file from .ogg to .wav
            # convert the sound file
            logging.debug(f'Converting {ogg} to {wave_fullname}')
            rv = os.system(f'ffmpeg -i "{ogg}" "{wave_fullname}"')
            if rv != 0:
                raise Exception(f'Error converting {ogg} to {wave_fullname}')

        if prefix:
            prefix_wave_filename = prefix.sound_as_wav(prefix.sounds[0])
            prefix_wave_fullname = os.path.join(prefix.sounds_dir, prefix_wave_filename)
            cmp_filename = f'{prefix.name}_{wave_filename}'
            cmp_fullname = os.path.join(self.sounds_dir, cmp_filename)
            if not os.path.exists(cmp_fullname):
                rv = os.system(f'sox "{prefix_wave_fullname}" "{wave_fullname}" "{cmp_fullname}"')
                if rv != 0:
                    raise Exception(f'Error merging {prefix_wave_filename} and {wave_filename} to {cmp_filename}')
            return cmp_filename

        return wave_filename

    def __str__(self):
        return f'{self.id}: {self.name} - T: {self.type} - C: {self.category} - P: {self.package} - Sounds: {self.sounds} - Translation: {self.translation} - Ini: {self.ini}'

    def __repr__(self):
        return f'{self.id}: {self.name} - T: {self.type} - C: {self.category} - P: {self.package} - Sounds: {self.sounds} - Translation: {self.translation} - Ini: {self.ini}'

    def __hash__(self) -> int:
        str = f'{self.id}: {self.name} - Sounds: {self.sounds.sort()} - Translation: {self.translation}'
        return hash(str)

    def __eq__(self, other):
        if not isinstance(other, RbrPacenote):
            return False

        if self.name != other.name:
            return False
        if self.id != other.id:
            return False
        # if self.type != other.type:
        #     return False
        # if self.category != other.category:
        #     return False
        # if self.package != other.package:
        #     return False
        if self.translation != other.translation:
            return False

        # compare the sounds as a set
        my_sounds = set(self.sounds)
        other_sounds = set(other.sounds)
        if my_sounds != other_sounds:
            return False

        return True

    def almost_equal(self, other):
        if not isinstance(other, RbrPacenote):
            return False

        if self.name != other.name:
            return False
        if self.id != other.id:
            return False
        if self.translation != other.translation:
            return False

        # compare the sounds as a set
        my_sounds = set(self.sounds)
        other_sounds = set(other.sounds)
        if my_sounds != other_sounds:
            return False

        return True


class RbrPacenotePlugin:
    def __init__(self, plugin_dir = "Pacenote/", ini_files = ["Rbr.ini", "Rbr-Enhanced.ini"]):
        self.pacenotes = set()
        # self.ini_file = ini_file
        # base_dir is the directory of this file + ini_file
        self.plugin_dir = plugin_dir

        # make sure the plugin_dir is a directory
        if not os.path.isdir(plugin_dir):
            logging.error(f'Not a directory: {plugin_dir}')
            return

        ini_file = os.path.join(plugin_dir, 'PaceNote.ini')
        # make sure the ini_file exists
        if not os.path.exists(ini_file):
            logging.error(f'Not found: {ini_file}')
            return

        config = configparser.ConfigParser()
        config.read(ini_file)
        # get the 'SETTINGS' section
        settings = config['SETTINGS']
        # get the sounds and language
        self.sounds = settings.get('sounds')
        self.language = settings.get('language')

        logging.debug(f'language: {self.language}')
        logging.debug(f'sounds: {self.sounds}')

        for ini_file in ini_files:
            ini_file = os.path.join(plugin_dir, 'config', 'pacenotes', ini_file)
            self.read_ini(ini_file)

        ini_file = os.path.join(plugin_dir, 'config', 'ranges', 'Rbr.ini')
        self.read_ini(ini_file)

    def sound_file(self, sound):
        return os.path.join(self.sounds_dir(), sound)

    def sounds_dir(self):
        return os.path.join(self.plugin_dir, 'sounds', self.sounds)

    def add_translation(self, note):
        # ; So, if the plugin searches for a string to translate, e.g. ONE_LEFT
        # ; initially defined in the "cat1.ini" file in the "packages/category1"
        # ; directory, it searches for a file with an identical name, "cat1.ini", in
        # ; the parallel folder located beneath the language specific directory.
        # ; If that file is not found, the "strings.ini" in that same directory is
        # ; searched.
        # ; If none applies, the search continues one level above the current folder.
        # ; Again, the search starts with the original file name ("cat1.ini").
        # ; And so on, until the top-level directory has been reached.
        # ;
        # ; Note:
        # ; The translation should only be defined in one file, preferably in the
        # ; category specific file ("cat1.ini"). The strings.ini file serves as an
        # ; alternative or for convenience.
        # ; The above structure should be seen as an example. No need to create all
        # ; those files.
        files = [
            os.path.join('pacenotes', 'packages', note.category.lower(), f'{note.ini}'),
            os.path.join('pacenotes', 'packages', note.category.lower(), 'strings.ini'),
            os.path.join('pacenotes', 'packages', 'strings.ini'),
            os.path.join('pacenotes', 'strings.ini'),
        ]
        for file in files:
            file = os.path.join(self.plugin_dir, 'language', self.language, file)
            strings = self.strings(file)
            if strings and note.name in strings:
                note.translation = strings[note.name]
                # logging.debug(f'Translation: {note.name} -> {note.translation}')
                return

        if not note.translation:
            if note.name.isnumeric():
                note.translation = note.name
            else:
                logging.error(f'No translation for: {note.name}')
            # exit(1)
        # logging.debug(f'add_translation: {note}')

    def strings(self, file):
        if not os.path.exists(file):
            # logging.debug(f'Not found: {file}')
            return

        config = configparser.ConfigParser(strict=False)
        try:
            config.read(file, encoding='utf-8')
        except Exception as e:
            # logging.error(f'Error reading {file}: {e}')
            # work around for configparser not handling utf-8
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            # remove the BOM
            content = content.replace('\ufeff', '')
            config.read_string(content)

        strings = {}
        for section in config.sections():
            if section == 'STRINGS':
                for english in config.options(section):
                    # logging.debug(f'{english} - {config.get(section, english)}')
                    translation = config.get(section, english, fallback=None)
                    if translation:
                        strings[english] = translation.strip()
        return strings


    def read_ini(self, ini_file = '', recursion = 0, category = '', package = ''):
        # make sure the ini_file exists
        if not os.path.exists(ini_file):
            logging.error(f'Not found: {ini_file}')
            return

        short_file = ini_file.replace(self.plugin_dir, '')
        # logging.debug("%sfile: %s" % (recursion * "\t", short_file))
        logging.debug("file: %s" % ( short_file))
        current_base_dir = os.path.dirname(ini_file)
        ini_filename = os.path.basename(ini_file)

        config = configparser.ConfigParser(strict=False)
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

            if section.startswith('PACENOTE') or section.startswith('RANGE'):
                (type, name) = section.split('::')
                note = RbrPacenote(name.lower())
                note.ini = ini_filename
                note.type = type
                note.category = category
                note.package = package
                note.id = config.getint(section, 'id', fallback=-1)
                note.sounds_dir = self.sounds_dir()
                if not note.id and note.type == 'PACENOTE':
                    logging.debug(f'No id in {section}')
                note.sound_count = config.getint(section, 'Sounds', fallback=-1)
                for option in config.options(section):
                    if option.startswith('snd'):
                        sound = config.get(section, option)
                        # check if the sound file exists
                        sound_file = self.sound_file(sound)
                        if not os.path.exists(sound_file):
                            logging.error(f'Not found: {sound_file}')
                        else:
                            note.sounds.append(sound)
                if note.sound_count != len(note.sounds):
                    logging.error(f'Invalid sound count: {note.sound_count} - {note}')
                # for i in range(int(sounds)):
                #     sound = config.get(section, 'Snd%d' % i)
                #     note.sounds.append(sound)
                #     # sound = os.path.join(current_base_dir, sound)

                self.add_translation(note)
                # only add the pacenote if it has sounds
                if len(note.sounds) > 0:
                    self.pacenotes.add(note)

                # if name not in self.pacenotes:
                #     # logging.debug('New pacenote id: %s - %s' % (id, section))
                #     self.pacenotes[name] = note
                # else:
                #     existing = self.pacenotes[name]
                #     if not existing.almost_equal(note):
                #         logging.error('Conflicting pacenote: \n%s\n%s' % (existing, note))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.basicConfig(level=logging.ERROR)
    basedir = os.path.dirname(os.path.abspath(__file__))
    pacenote_dir = os.path.join(basedir, "Pacenote")
    logging.debug(f'ini_file: {pacenote_dir}')
    rbr_pacenote_plugin = RbrPacenotePlugin(pacenote_dir)