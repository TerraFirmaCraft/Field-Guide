# [TerraFirmaCraft Field Guide](https://terrafirmacraft.github.io/Field-Guide/en_us/)

A transpilation of the TerraFirmaCraft Field Guide - the in-game documentation book - to an online format.

### Development

```bash
# Setup python dependencies
$ pip install -r requirements.txt

# Clone TerraFirmaCraft/TerraFirmaCraft into a folder /path/to/tfc
$ python src/main.py --tfc-dir /path/to/tfc [--debug]

# Launch a webserver with python for testing
# View the file at `localhost:8000`
# Viewing as a file will mostly work too
$ cd out
$ python -m http.server 8000

# New versions (1.20) require additional arguments:
$ python src/main.py ... --resource-pack-book --copy-existing-versions

# For 'old' local versions
# When generating an old version to commit
$ python src/main.py ... --out-dir assets/versions/ --root-dir "Field-Guide" --old-version-key "20"

# When generating an old version to test / view
$ python src/main.py ... --old-version-key "20"
```