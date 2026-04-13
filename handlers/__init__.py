from .start import router as start_router
from .shop import router as shop_router
from .admin import router as admin_router

def register_all(dp):
    dp.include_router(start_router)
    dp.include_router(shop_router)
    dp.include_router(admin_router)
