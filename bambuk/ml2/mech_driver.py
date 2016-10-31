#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from neutron.i18n import _LI

from neutron.plugins.ml2 import driver_api

from oslo_log import log

from bambuk.ml2 import hyper_switch_api

LOG = log.getLogger(__name__)


class BambukMechanismDriver(driver_api.MechanismDriver):
    """
        Bambuk ML2 mechanism driver
    """

    def initialize(self):
        LOG.info(_LI("Starting BambukMechanismDriver"))
        self._hyper_switch_api = hyper_switch_api.HyperSwitchAPI()
