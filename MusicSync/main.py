import yaml
import os
import subprocess
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


class MusicSync:
    def __init__(self, config="config.yaml"):
        """
        Initialize the MusicSync Class
        :param config: location of the config.yaml file
        """
        with open(config, 'r') as stream:
            self._config = yaml.load(stream, Loader=yaml.FullLoader)
        self._source = self._config['source']
        self._destination = self._config['destination']
        self._formats = self._config['formats']
        self._converted = []

    @property
    def config(self):
        return self._config

    @property
    def source(self):
        return self._source

    @property
    def destination(self):
        return self._destination

    @property
    def formats(self):
        return self._formats

    @property
    def converted(self):
        return self._converted

    def add_converted(self, converted_file):
        """
        Append a converted file to the list of converted files
        :param converted_file: file to add
        :return: list of converted files
        """
        self._converted.append(converted_file)
        return self._converted

    def get_formats_list(self):
        """
        Get a list of the formats that should be synced
        :return: a list of formats
        """
        return list(self.formats.keys())

    def get_all_files(self, dir_path):
        """
        Get a list of all the files in a given path
        :param dir_path: the path to search for files
        :return: a list of all the files in the path
        """
        list_of_files = os.listdir(dir_path)
        all_files = list()
        for entry in list_of_files:
            full_path = os.path.join(dir_path, entry)
            if os.path.isdir(full_path):
                all_files = all_files + self.get_all_files(full_path)
            else:
                all_files.append(full_path)
        return all_files

    def convert(self, source_file):
        """
        Convert a specified file based on options set in the config
        This function is called by sync()
        :param source_file: the file that should be converted
        :return: None
        """
        formats_list = self.get_formats_list()
        if source_file.endswith(tuple(formats_list)):
            source_format = os.path.splitext(source_file[len(self.source):])[1].replace('.', '')
            destination_format = self.formats[source_format]['convert_to']
            basename = os.path.splitext(source_file[len(self.source):])[0]
            destination_file = str(self.destination + basename + '.' + destination_format)
            if os.path.exists(destination_file):
                print("Skipping file %s because it has been converted already" % source_file)
            else:
                print("Converting file: \n\tSource: %s \n\tDestination: %s" % (source_file, destination_file))
                convert_command = self.formats[source_format]['command']
                convert_command = convert_command.replace("$source", '"' + source_file + '"')
                convert_command = convert_command.replace("$destination", '"' + destination_file + '"')
                print("\t" + convert_command)
                if not os.path.exists(os.path.dirname(destination_file)):
                    os.makedirs(os.path.dirname(destination_file))
                subprocess.call(convert_command, shell=True)
            self.add_converted(destination_file)
        return

    def clean(self, files_to_keep):
        """
        Removes any files in the destination directory that aren't in files_to_keep
        :param files_to_keep: list of the files to keep
        :return: None
        """
        for file in self.get_all_files(self.destination):
            if file not in files_to_keep:
                print("Removing file %s" % file)
                os.remove(file)
        self.remove_empty_dirs(self.destination)

    def remove_empty_dirs(self, path, removeRoot=True):
        """
        Recursively remove empty directories given a directory
        :param path: path to recurse
        :param removeRoot: whether or not to remove the path passed in
        :return: None
        """
        if not os.path.isdir(path):
            return
        files = os.listdir(path)
        if len(files):
            for f in files:
                fullpath = os.path.join(path, f)
                if os.path.isdir(fullpath):
                    self.remove_empty_dirs(fullpath)
        files = os.listdir(path)
        if len(files) == 0 and removeRoot:
            print("Removing empty directory: " + path)
            os.rmdir(path)

    def sync(self):
        """
        Sync files from the configured source directory to the configured destination directory
        :return: None
        """
        with ThreadPool(self.config['threads']) as pool:
            pool.map(self.convert, self.get_all_files(self.source))


if __name__ == '__main__':
    sync = MusicSync()
    sync.sync()

