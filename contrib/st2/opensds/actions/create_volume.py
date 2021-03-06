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

import requests
import json

from st2common.runners.base_action import Action


class CreateVolumeAction(Action):
    def run(self,
            ip_addr="",
            port="",
            tenant_id="",
            name="",
            description="Volume",
            availability_zone="default",
            profile_id="",
            snapshot_id="",
            snapshot_from_cloud="",
            auth_token="",
            size=1):
        data = {
            "name": name,
            "description": description if description else "Volume creation",
            "availabilityZone": availability_zone if availability_zone else "default",
            "profileId": profile_id,
            "snapshotId": snapshot_id if snapshot_id else "",
            "snapshotFromCloud": snapshot_from_cloud if snapshot_from_cloud else False,
            "size": size
            }
        if profile_id:
            data["ProfileId"] = profile_id

        url = "http://" + \
            ip_addr + ":" + \
            port + "/v1beta/" + \
            tenant_id + "/block/volumes"

        headers = {
            'content-type': 'application/json',
            'x-auth-token': auth_token
        }
        r = requests.post(url=url, data=json.dumps(data), headers=headers)
        r.raise_for_status()
        resp = r.json()
        return resp["id"]
