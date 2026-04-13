from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from keyboards.shop import categories_kb, products_kb, product_action_kb
from keyboards.main import main_menu_kb
from states import ShopFSM
from services.shop_service import (
    fetch_categories,
    fetch_products_by_category,
    fetch_product,
    build_product_text,
    validate_quantity_text,
    create_product_order,
    build_order_success_text,
)

router = Router()

@router.callback_query(F.data == "menu:shop")
async def menu_shop(c: types.CallbackQuery):
    rows = fetch_categories()

    if not rows:
        await c.message.answer("❌ No categories available")
        await c.answer()
        return

    await c.message.answer(
        "🛒 <b>Please choose a category:</b>",
        parse_mode="HTML",
        reply_markup=categories_kb(rows)
    )
    await c.answer()


@router.callback_query(F.data.startswith("shop:cat:"))
async def shop_category(c: types.CallbackQuery):
    try:
        category_id = int(c.data.split(":")[2])
    except (IndexError, ValueError):
        await c.answer("❌ Invalid category", show_alert=True)
        return

    rows = fetch_products_by_category(category_id)
    if not rows:
        await c.message.answer("❌ No products found in this category")
        await c.answer()
        return

    await c.message.answer(
        "📦 <b>Please choose a product:</b>",
        parse_mode="HTML",
        reply_markup=products_kb(rows)
    )
    await c.answer()


@router.callback_query(F.data.startswith("shop:product:"))
async def shop_product(c: types.CallbackQuery):
    try:
        product_id = int(c.data.split(":")[2])
    except (IndexError, ValueError):
        await c.answer("❌ Invalid product", show_alert=True)
        return

    product = fetch_product(product_id)
    if not product:
        await c.answer("❌ Product not found", show_alert=True)
        return

    await c.message.answer(
        build_product_text(product),
        parse_mode="HTML",
        reply_markup=product_action_kb(product_id)
    )
    await c.answer()


@router.callback_query(F.data.startswith("shop:buy:"))
async def shop_buy(c: types.CallbackQuery, state: FSMContext):
    try:
        product_id = int(c.data.split(":")[2])
    except (IndexError, ValueError):
        await c.answer("❌ Invalid product", show_alert=True)
        return

    product = fetch_product(product_id)
    if not product:
        await c.answer("❌ Product not found", show_alert=True)
        return

    await state.set_state(ShopFSM.waiting_quantity)
    await state.update_data(product_id=product_id)

    await c.message.answer(
        "🔢 <b>Please enter quantity</b>\nExample: <code>10</code>",
        parse_mode="HTML"
    )
    await c.answer()


@router.message(ShopFSM.waiting_quantity)
async def shop_quantity(message: types.Message, state: FSMContext):
    qty, error = validate_quantity_text(message.text)
    if error:
        await message.answer(error)
        return

    data = await state.get_data()
    product_id = data.get("product_id")

    if not product_id:
        await state.clear()
        await message.answer("❌ Session expired, please try again")
        return

    order, db_error = create_product_order(message.from_user.id, product_id, qty)
    if db_error:
        await message.answer(db_error)
        return

    await state.clear()
    await message.answer(
        build_order_success_text(order),
        parse_mode="HTML"
    )
