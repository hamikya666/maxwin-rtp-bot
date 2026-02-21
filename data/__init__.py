# data/__init__.py

from . import cm8
from . import a9play
from . import ald99
from . import u9play

# 也可以统一做个字典导出方便bot引用
ALL_MERCHANTS = {
    "CM8": cm8.GAMES,
    "A9PLAY": a9play.GAMES,
    "ALD99": ald99.GAMES,
    "U9PLAY": u9play.GAMES
}
