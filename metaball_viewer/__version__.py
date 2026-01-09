# Copyright 2025 Xudong Han. All rights reserved.
# Licensed under the MIT License.
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Enable `metaball-viewer.__version__` to be imported.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("metaball-viewer")
except PackageNotFoundError:
    __version__ = "unknown"
