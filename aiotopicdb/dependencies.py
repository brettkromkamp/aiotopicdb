import configparser
import os

from aiotopicdb.topics.core.store.topicstore import TopicStore

SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), "settings.ini")

config = configparser.ConfigParser()
config.read(SETTINGS_FILE_PATH)


def get_store(database_path=config["TOPICSTORE"]["DatabasePath"]):
    return TopicStore(database_path)
