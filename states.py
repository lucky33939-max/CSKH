from aiogram.fsm.state import State, StatesGroup

class ShopFSM(StatesGroup):
    waiting_quantity = State()

class WalletFSM(StatesGroup):
    waiting_custom_amount = State()
