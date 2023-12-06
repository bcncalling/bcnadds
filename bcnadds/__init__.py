#blackcatuserbot addons

__version__ = "0.0.27"
__license__ = "GNU Lesser General Public License v3.0 (LGPL-3.0)"
__copyright__ = "Copyright (C) 2023-present bcncalling <https://github.com/bcncalling>"

from .funcs import generate_cover
from .TgGraph import TgGraph

def bcnadds():
  print(
    "Black cat installed successfully" + "\n"
    f"Version : {__version__}"
  )
