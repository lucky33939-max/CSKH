from db import (
    ...
    get_topup_orders,
    approve_topup_order,
    mark_topup_order_rejected,
)
def render_topup_orders_page(token: str | None = None, status: str | None = None):
    if status in ("pending", "paid", "rejected"):
        rows = get_topup_orders(status=status, limit=100)
        title = f"充值订单 - {status}"
    else:
        rows = get_topup_orders(limit=100)
        title = "充值订单"

    html_rows = ""
    for order_id, user_id, amount, st, created_at in rows:
        actions = "-"
        if st == "pending":
            approve_link = build_url(f"/topup/{order_id}/approve", token=token)
            reject_link = build_url(f"/topup/{order_id}/reject", token=token)
            actions = (
                f'<a class="btn" href="{approve_link}">确认到账</a> '
                f'<a class="btn" style="background:#dc2626;" href="{reject_link}">拒绝</a>'
            )

        html_rows += f"""
        <tr>
            <td><code>{order_id}</code></td>
            <td><code>{user_id}</code></td>
            <td>{fmt_num(amount)} USDT</td>
            <td>{st}</td>
            <td>{fmt_ts(created_at)}</td>
            <td>{actions}</td>
        </tr>
        """

    if not html_rows:
        html_rows = '<tr><td colspan="6" class="empty">暂无充值订单</td></tr>'

    body = f"""
    <div class="topbar">
        <div><h1>{escape(title)}</h1></div>
        <div><a class="btn secondary" href="{build_url('/dashboard', token=token)}">返回后台</a></div>
    </div>

    <div class="filters">
        <a class="btn secondary" href="{build_url('/topups', token=token)}">全部</a>
        <a class="btn secondary" href="{build_url('/topups', token=token, status='pending')}">待处理</a>
        <a class="btn secondary" href="{build_url('/topups', token=token, status='paid')}">已到账</a>
        <a class="btn secondary" href="{build_url('/topups', token=token, status='rejected')}">已拒绝</a>
    </div>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th>订单号</th>
                    <th>User ID</th>
                    <th>金额</th>
                    <th>状态</th>
                    <th>创建时间</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>{html_rows}</tbody>
        </table>
    </div>
    """
    return page_shell(title, body)

@app.get("/topups", response_class=HTMLResponse)
def topups_page(
    token: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    require_token(token)
    return render_topup_orders_page(token=token, status=status)


@app.get("/topup/{order_id}/approve")
def topup_approve_action(order_id: int, token: str | None = Query(default=None)):
    require_token(token)
    approve_topup_order(order_id)
    return RedirectResponse(url=build_url("/topups", token=token, status="pending"), status_code=303)


@app.get("/topup/{order_id}/reject")
def topup_reject_action(order_id: int, token: str | None = Query(default=None)):
    require_token(token)
    mark_topup_order_rejected(order_id)
    return RedirectResponse(url=build_url("/topups", token=token, status="pending"), status_code=303)
