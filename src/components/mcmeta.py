# Downloader for MC Metadata
# Allows us to reference vanilla namespaced files and images

from typing import Any
from util import LOG
from versions import MC_VERSION, FORGE_VERSION, LANGUAGES

import os
import json
import zipfile
import urllib.error
import urllib.request

import util

ENABLED = False

CACHE = '.cache'
CLIENT_JAR = 'client-{mc_version}.zip'.format(mc_version=MC_VERSION)
FORGE_JAR = 'forge-{forge_version}.zip'.format(forge_version=FORGE_VERSION)

VERSION_MANIFEST_URL = 'https://piston-meta.mojang.com/mc/game/version_manifest.json'
RESOURCES_URL = 'https://resources.download.minecraft.net/'
FORGE_JAR_URL = 'https://maven.creeperhost.net/net/minecraftforge/forge/{mc_version}-{forge_version}/forge-{mc_version}-{forge_version}-universal.jar'.format(mc_version=MC_VERSION, forge_version=FORGE_VERSION)
NEOFORGE_JAR_URL = 'https://maven.neoforged.net/releases/net/neoforged/neoforge/{forge_version}/neoforge-{forge_version}-universal.jar'.format(forge_version=FORGE_VERSION)

def getForgeURL():
    if MC_VERSION == '1.20.1' or MC_VERSION == '1.18.2':
        return FORGE_JAR_URL
    else:
        return NEOFORGE_JAR_URL

def load_from_mc(path: str, reader) -> Any:
    try:
        path = path.replace('\\', '/')
        for lang in LANGUAGES:
            if lang != 'en_us' and path == 'assets/minecraft/lang/%s.json' % lang:
                with open(util.path_join(CACHE, 'lang_%s.json' % lang), 'r', encoding='utf-8') as f:
                    return reader(f)
    except IOError:
        pass  # Fallthrough
    return load_from_source(CLIENT_JAR, path, reader)

def load_from_forge(path: str, reader) -> Any:
    return load_from_source(FORGE_JAR, path, reader)


def load_from_source(source: str, path: str, reader):
    if not ENABLED:
        util.error('mcmeta not enabled')
    try:
        path = path.replace('\\', '/')  # ZipFile paths always use forward slashes, even on windows
        client_jar = util.path_join(CACHE, source)
        with zipfile.ZipFile(client_jar, 'r') as zip:
            with zip.open(path) as f:
                data = reader(f)
        return data
    except Exception as e:
        util.error('Reading \'%s\' from \'%s\' : %s' % (path, source, e))


def load_cache():
    global ENABLED
    ENABLED = True

    LOG.info('Loading Cache')
    if not os.path.isdir(CACHE):
        os.makedirs(CACHE, exist_ok=True)

    client_jar_dir = util.path_join(CACHE, CLIENT_JAR)  
    if not os.path.isfile(client_jar_dir):
        # Load Manifest
        data = json.loads(download(VERSION_MANIFEST_URL).decode('utf-8'))
        for version in data['versions']:
            if version['id'] == MC_VERSION:
                break
        else:
            raise ValueError('Version %s not found in manifest' % MC_VERSION)
        

        # Load Version Manifest
        version_url = version['url']
        data = json.loads(download(version_url).decode('utf-8'))
        client_jar_url = data['downloads']['client']['url']
        client_jar = download(client_jar_url)

        # Load Languages
        asset_index_url = data['assetIndex']['url']
        asset_index = json.loads(download(asset_index_url).decode('utf-8'))

        for lang in LANGUAGES:
            if lang == 'en_us':
                continue  # This file is in the main client jar
            language_hash = asset_index['objects']['minecraft/lang/%s.json' % lang]['hash']
            language_url = RESOURCES_URL + language_hash[:2] + '/' + language_hash
            language_data = json.loads(download(language_url).decode('utf-8'))
            language_dir = util.path_join(CACHE, 'lang_%s.json' % lang) 
            with open(language_dir, 'w', encoding='utf-8') as f:
                json.dump(language_data, f, ensure_ascii=False)

        with open(client_jar_dir, 'wb') as f:
            f.write(client_jar)
    
    forge_jar_dir = util.path_join(CACHE, FORGE_JAR)
    if not os.path.isfile(forge_jar_dir):
        forge_jar = download(getForgeURL())

        with open(forge_jar_dir, 'wb') as f:
            f.write(forge_jar)
    
    LOG.debug('Cache Loaded')


def download(url: str) -> Any:
    LOG.debug('Downloading %s' % url)
    try:
        with urllib.request.urlopen(url) as request:
            res = request.read()
        return res
    except urllib.error.HTTPError as e:
        raise Exception('Requested %s' % url) from e
