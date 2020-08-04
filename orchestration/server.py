# Copyright 2019 The OpenSDS Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#this is my first code

import sys
from flask import Flask
from orchestration.api.services import service
from orchestration.utils import config
from orchestration.api.instances import instance
from orchestration.api.tasks import task


class ServerManager:
    app = Flask(__name__)

    def __init__(self):
        self._init_server()
    def _init_server(self):
        self.app.url_map.strict_slashes = False

        # register router
        # self.app.register_blueprint(class_name)
        self.app.register_blueprint(service)
        self.app.register_blueprint(instance)
        self.app.register_blueprint(task)

    def start(self):
        self.app.run(config.HOST, config.PORT)


server_manager = ServerManager()

if __name__ == '__main__':
    # If config file is specified in command line, use that file
    # Else use default config file'orchestration.conf'
    if len(sys.argv) > 1:
        config.config_file = sys.argv[1]
        config.init_config(config.config_file)
    else:
        config.init_config(config.config_file)
    server_manager.start()
