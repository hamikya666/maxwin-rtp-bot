# data/__init__.py
from . import cm8, a9play, ald99, u9play

# 所有商家及对应平台
MERCHANTS = {
    "CM8": cm8.PLATFORMS,
    "A9PLAY": a9play.PLATFORMS,
    "ALD99": ald99.PLATFORMS,
    "U9PLAY": u9play.PLATFORMS
}
