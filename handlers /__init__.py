from aiogram import Dispatcher

from .start import router as start_router
from .profile import router as profile_router
from .shop import router as shop_router
from .wallet import router as wallet_router
from .orders import router as orders_router


def register_all_routers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(shop_router)
    dp.include_router(wallet_router)
    dp.include_router(orders_router)
