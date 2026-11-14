import asyncio
import json
import time
import os
import urllib.request
import urllib.parse
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import RequestWebViewRequest

API_ID = 26569107
API_HASH = '8156cfc55db2ca6ec31fec793bf81d1e'

# ServerFn Hashes (TanStack Server Functions on eggsbuilder)
HASH_ME = 'a9c784d24056666befe02f417c418b4911322463ca471d010bf162e13d69082c'
HASH_HIT = '6a3b42c5de32d6a59c30367671349c238181cfa11631a30c94a3c8276f56b36f'
HASH_OPEN = '24261d72abf15b1ee6a4d26122c67d5e98c88f32c02d74e3d13b2b4d8708ade1'
HASH_COLLECT = 'b0a2104fb8328efc1522e6a2d639b326e0d0bbdd13c633bca43c450fade7ff6d'

def log(tag, msg):
    print(f"[{time.strftime('%X')}][{tag}] {msg}", flush=True)

def seroval_serialize(obj, refs=None):
    if refs is None:
        refs = {'count': 0}
    if obj is None:
        return {'t': 2, 's': 1}
    elif isinstance(obj, bool):
        return {'t': 2, 's': 3 if obj else 2}
    elif isinstance(obj, (int, float)):
        return {'t': 0, 's': obj}
    elif isinstance(obj, str):
        return {'t': 1, 's': obj}
    elif isinstance(obj, list):
        idx = refs['count']
        refs['count'] += 1
        return {'t': 9, 'i': idx, 'a': [seroval_serialize(x, refs) for x in obj], 'l': len(obj)}
    elif isinstance(obj, dict):
        idx = refs['count']
        refs['count'] += 1
        keys = list(obj.keys())
        values = [seroval_serialize(obj[k], refs) for k in keys]
        return {'t': 10, 'i': idx, 'p': {'k': keys, 'v': values}, 'o': 0}

def parse_seroval_node(node, refs_map=None):
    if refs_map is None: refs_map = {}
    if not isinstance(node, dict): return node
    t = node.get('t')
    i = node.get('i')
    if t == 1: return node.get('s')
    elif t == 0: return node.get('s')
    elif t == 2:
        s = node.get('s')
        if s == 1: return None
        elif s == 2: return False
        elif s == 3: return True
        return s
    elif t == 9:
        res = []
        if i is not None: refs_map[i] = res
        for item in node.get('a', []):
            res.append(parse_seroval_node(item, refs_map))
        return res
    elif t == 10 or t == 11:
        res = {}
        if i is not None: refs_map[i] = res
        p = node.get('p', {})
        keys = p.get('k', [])
        vals = p.get('v', [])
        for k, v in zip(keys, vals):
            res[k] = parse_seroval_node(v, refs_map)
        return res
    elif t == 4:
        return refs_map.get(i)
    elif t == 25:
        return {'error': parse_seroval_node(node.get('s', {}), refs_map)}
    return node

def call_server_fn(fn_hash, data_dict):
    url = f"https://eggsdigger.lovable.app/_serverFn/{fn_hash}"
    seroval_data = seroval_serialize({'data': data_dict})
    envelope = {
        't': seroval_data,
        'f': 127,
        'm': []
    }
    body = json.dumps(envelope).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            'Content-Type': 'application/json',
            'x-tsr-serverFn': 'true',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Origin': 'https://eggsdigger.lovable.app',
            'Referer': 'https://eggsdigger.lovable.app/'
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw_json = json.loads(resp.read().decode('utf-8'))
        return parse_seroval_node(raw_json.get('t', {}))

async def get_init_data(session_str):
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.connect()
    bot = await client.get_entity('EggsDiggerbot')
    res = await client(RequestWebViewRequest(
        peer=bot,
        bot=bot,
        platform='android',
        from_bot_menu=False,
        url='https://eggsdigger.lovable.app/'
    ))
    await client.disconnect()
    raw = res.url
    init_data = urllib.parse.unquote(raw.split('#tgWebAppData=')[1].split('&tgWebAppVersion=')[0])
    return init_data

async def process_account(acc_name, session_str):
    log(acc_name, "==================================================")
    log(acc_name, f"Đang kết nối Telethon lấy initData cho {acc_name}...")
    try:
        init_data = await get_init_data(session_str)
    except Exception as e:
        log(acc_name, f"Lỗi lấy session/initData: {e}")
        return

    # 1. Lấy thông tin user (me)
    try:
        me_resp = call_server_fn(HASH_ME, {'init': init_data})
        user_info = me_resp.get('result', {})
        balance = user_info.get('balance', 0)
        tg_id = user_info.get('tgId', 'N/A')
        username = user_info.get('username', 'N/A')
        cards = user_info.get('cards', [])
        drills = user_info.get('drills', {})
        log(acc_name, f"User: @{username} (TG ID: {tg_id}) | Số dư: {balance:.6f} TON/USD")
        log(acc_name, f"Gói trứng sở hữu: {len(cards)} | Máy đào: {drills}")
    except Exception as e:
        log(acc_name, f"Lỗi lấy thông tin: {e}")

    # 2. Thu hoạch máy đào (Periodic Mining Collection)
    try:
        col_resp = call_server_fn(HASH_COLLECT, {'init': init_data})
        log(acc_name, "✅ Thu hoạch máy đào tự động hoàn tất!")
    except Exception as e:
        log(acc_name, f"Lỗi thu hoạch máy đào: {e}")

    # 3. Đập vỡ trứng 100% (High-Speed Crack Loop)
    log(acc_name, "🔨 Bắt đầu cày đập vỡ vỏ trứng 100% bằng Hit Boost...")
    for round_idx in range(10):
        try:
            hit_res = call_server_fn(HASH_HIT, {'init': init_data, 'n': 100})
            log(acc_name, f"💥 Đập trứng đợt {round_idx + 1}: +100 hits sát thương thành công!")
            await asyncio.sleep(1)
        except Exception as e:
            log(acc_name, f"Lỗi đập trứng đợt {round_idx + 1}: {e}")

    # 4. Tự động mở trứng nhận phần thưởng TON (Open cracked egg)
    try:
        open_res = call_server_fn(HASH_OPEN, {'init': init_data})
        res_data = open_res.get('result', {})
        if res_data and res_data.get('ok'):
            amt = res_data.get('amount', 0)
            log(acc_name, f"🎉 MỞ TRỨNG THÀNH CÔNG! Nhận thưởng: +{amt:.6f} TON/USD")
        else:
            err = open_res.get('error')
            if err:
                log(acc_name, f"Thông báo mở trứng: {err}")
            else:
                log(acc_name, f"Kết quả mở trứng: {res_data}")
    except Exception as e:
        log(acc_name, f"Lỗi mở trứng: {e}")

    log(acc_name, f"Hoàn thành chu kỳ cho {acc_name}!\n")

async def main():
    print("=" * 65)
    print("🚀 EGGS DIGGER AUTO PRO - CÀY NHANH, ĐẬP TRỨNG 100%, AUTO MINING")
    print("=" * 65)
    
    sessions_env = os.environ.get('TELEGRAM_SESSIONS')
    if sessions_env:
        sessions = json.loads(sessions_env)
    else:
        sessions_path = os.path.join(os.path.dirname(__file__), 'sessions.json')
        if not os.path.exists(sessions_path):
            sessions_path = os.path.join(os.path.dirname(__file__), '..', 'sessions.json')
        with open(sessions_path, 'r') as f:
            sessions = json.load(f)

    for acc_name, session_str in sessions.items():
        await process_account(acc_name, session_str)
        await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(main())
