import json
import os
from pathlib import Path
import os
from typing import List
from django.conf import settings


class JsonLoader():
    # xxxPath.xxxFile without json return python object
    # xxxPath.xxxFile.json return file content
    data = {}

    def getConst(self, scan_path_list: List[str], key_ignore_pattern=''):
        """
        scan_path_list rel to src dir
        """
        scan_path_set = set(scan_path_list)

        if JsonLoader.data:
            return JsonLoader.data
        else:
            SRC_DIR = settings.BASE_DIR.parent
            src_path = Path(SRC_DIR)
            for scan_path in scan_path_set:
                for path in src_path.rglob(os.path.join(scan_path, '**/*.json')):
                    relpath = str(path.parent).replace(str(src_path), '')[1:]
                    config_key = relpath.replace(key_ignore_pattern, '').replace(os.path.sep, '.')+ '.' + path.stem
                    file_key = relpath.replace(key_ignore_pattern, '').replace(os.path.sep, '.')+ '.' + path.name
                    with open(path, 'r') as f:
                        JsonLoader.data[config_key] = json.loads(f.read())
                        JsonLoader.data[file_key] = json.dumps(JsonLoader.data[config_key])

            return JsonLoader.data

