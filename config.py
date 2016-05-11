from configparser import ConfigParser

config_file = 'config.ini'

config = ConfigParser()
config.read(config_file)

shares = {
    drive_letter.upper() + ':': unc
    for drive_letter, unc in config['shares'].items()
}