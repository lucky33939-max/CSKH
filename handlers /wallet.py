from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from config import PAYMENT_ADDRESS
from keyboards.wallet import topup_amounts_kb
from states import WalletFSM
from services.wallet_service import (
    build_topup_menu_text,
    validate_custom_amount,
    create_user_topup_order,
    build_topup_created_text,
    build_topup_orders_text,
)

router = Router()


@router.callback_query(F.data == "menu:topup")
async def menu_topup(c: types.CallbackQuery):
    await c.message.answer(
        build_topup_menu_text(c.from_user.id),
        parse_mode="HTML",
        reply_markup=topup_amounts_kb()
    )
    await c.answer()


@router.callback_query(F.data.startswith("topup:"))
async def topup_select(c: types.CallbackQuery, state: FSMContext):
    value = c.data.split(":")[1]

    if value == "custom":
        await state.set_state(WalletFSM.waiting_custom_amount)
        await c.message.answer(
            "💰 <b>Please enter custom amount in USDT:</b>",
            parse_mode="HTML"
        )
        await c.answer()
        return

    try:
        amount = float(value)
    except ValueError:
        await c.answer("❌ Invalid amount", show_alert=True)
        return

    order_id = create_user_topup_order(c.from_user.id, amount)

    await c.message.answer(
        build_topup_created_text(order_id, amount, PAYMENT_ADDRESS),
        parse_mode="HTML",
    )
    await c.answer()


@router.message(WalletFSM.waiting_custom_amount)
async def topup_custom_amount(message: types.Message, state: FSMContext):
    amount, error = validate_custom_amount(message.text)
    if error:
        await message.answer(error)
        return

    order_id = create_user_topup_order(message.from_user.id, amount)
    await state.clear()

    await message.answer(
        build_topup_created_text(order_id, amount, PAYMENT_ADDRESS),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "menu:topup_orders")
async def menu_topup_orders(c: types.CallbackQuery):
    await c.message.answer(
        build_topup_orders_text(c.from_user.id),
        parse_mode="HTML"
    )
    await c.answer()


@router.callback_query(F.data == "menu:energy")
async def menu_energy(c: types.CallbackQuery):
    await c.message.answer("⚡ Energy Rental coming soon")
    await c.answer()


@router.callback_query(F.data == "menu:lang")
async def menu_lang(c: types.CallbackQuery):
    await c.message.answer("🌐 Language setting coming soon")
    await c.answer()


@router.callback_query(F.data == "menu:support")
async def menu_support(c: types.CallbackQuery):
    await c.message.answer("👨‍💻 Contact support: @support")
    await c.answer()


@router.callback_query(F.data == "menu:notice")
async def menu_notice(c: types.CallbackQuery):
    await c.message.answer(
        "📢 <b>Notice</b>\n\n"
        "Please keep the account files you receive safe.\n"
        "We only keep your purchase records; the account files are automatically deleted from stock after delivery.",
        parse_mode="HTML"
    )
    await c.answer()


@router.callback_query(F.data == "menu:vip")
async def menu_vip(c: types.CallbackQuery):
    await c.message.answer(
        "💎 <b>Telegram Premium</b>\n\n"
        "请选择操作：\n"
        "1. 为此账号开通\n"
        "2. 赠送他人会员\n"
        "3. 余额充值",
        parse_mode="HTML"
    )
    await c.answer()
