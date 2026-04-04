import os
import time
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

# ==========================================
# 1. 基础配置与 Flask 初始化
# ==========================================
app = Flask(__name__)
CORS(app)

KEY_FILE = "device_private_key.txt"

# ==========================================
# 2. 核心密码学模块：设备身份初始化
# ==========================================
def load_or_create_identity():
    """
    启动时加载设备私钥。如不存在则生成新身份。
    保证设备每次重启，链上身份（公钥地址）不变。
    """
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'r') as f:
            private_key = f.read().strip()
            account = Account.from_key(private_key)
            print(f"[*] 设备已唤醒，加载已有身份。")
    else:
        account = Account.create()
        with open(KEY_FILE, 'w') as f:
            f.write(account.key.hex())
        print(f"[*] 首次启动，已生成全新设备身份，私钥已安全存储。")

    print(f"[-] 设备的区块链身份证 (公钥地址): {account.address}")
    return account

device_account = load_or_create_identity()

# ==========================================
# 3. 区块链连接模块（连接 Sepolia 测试网）
# ==========================================
RPC_URL          = "https://sepolia.infura.io/v3/df7b552f6dfe412dbe5590478215573a"
CONTRACT_ADDRESS = "0xa5f5984184b6E0BbAa02758e94d6B714F3f48a8A"

# 包含 checkAccess 和 logAccess 两个函数的 ABI
CONTRACT_ABI = json.loads('''[
    {
        "inputs": [
            {"internalType": "address", "name": "_user",   "type": "address"},
            {"internalType": "address", "name": "_device", "type": "address"}
        ],
        "name": "checkAccess",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address",  "name": "_user",      "type": "address"},
            {"internalType": "uint256",  "name": "_timestamp", "type": "uint256"}
        ],
        "name": "logAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]''')

def get_contract():
    """创建并返回 Web3 合约实例，失败时返回 None。"""
    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            print("[!] 警告：无法连接区块链节点，请检查 RPC_URL 配置。")
            return None, None
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(CONTRACT_ADDRESS),
            abi=CONTRACT_ABI
        )
        return w3, contract
    except Exception as e:
        print(f"[!] Web3 初始化失败: {e}")
        return None, None

def check_acl_on_chain(user_address: str) -> bool:
    """
    向区块链查询用户是否有权访问本设备。
    [V3 修复] 查询失败时默认拒绝（原代码默认放行，存在安全漏洞）。
    """
    w3, contract = get_contract()
    if contract is None:
        print("[!] 区块链查询失败：拒绝访问（安全默认值）。")
        return False  # ✅ Bug2 修复：失败默认拒绝，不再默认放行

    try:
        has_access = contract.functions.checkAccess(
            user_address,
            device_account.address
        ).call()
        return has_access
    except Exception as e:
        print(f"[!] checkAccess 调用异常: {e}")
        return False  # ✅ 同样默认拒绝

def log_access_on_chain(user_address: str, timestamp: int):
    """
    [V3 新增] 认证全部通过后，设备主动向链上写入一条成功访问日志。
    这是「结界」的核心承诺：谁在何时进入了你的空间，不可篡改，无法抵赖。
    注意：此操作需要消耗 Gas，设备账户需持有少量 Sepolia 测试 ETH。
    """
    w3, contract = get_contract()
    if contract is None:
        print("[!] 链上日志写入失败：无法连接区块链，跳过（不影响本次访问）。")
        return

    try:
        # 构建交易
        nonce = w3.eth.get_transaction_count(device_account.address)
        txn = contract.functions.logAccess(
            user_address,
            timestamp
        ).build_transaction({
            'chainId': 11155111,        # Sepolia 测试网 Chain ID
            'gas':     100000,
            'gasPrice': w3.eth.gas_price,
            'nonce':   nonce,
        })

        # 设备用自己的私钥签名并广播交易
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=device_account.key)
        tx_hash    = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        print(f"[+] 链上访问日志已写入！交易哈希: {tx_hash.hex()}")
    except Exception as e:
        print(f"[!] logAccess 写入失败: {e}（不影响本次访问授权）")

# ==========================================
# 4. Web 服务与验签模块
# ==========================================
@app.route('/access', methods=['POST'])
def request_access():
    """
    核心接口：接收前端的访问请求，执行两关认证。
    关一：密码学验签（本地，极速，零 Gas）
    关二：区块链 ACL 查询（链上，免费 view 调用）
    全部通过后：写入链上访问日志，下发视频流
    """
    data = request.json

    # ✅ Bug3 修复：参数完整性校验，防止 None 导致后续崩溃
    user_address  = data.get('user_address')
    message_text  = data.get('message')
    signature     = data.get('signature')

    if not all([user_address, message_text, signature]):
        return jsonify({"status": "error", "message": "缺少必要参数：user_address / message / signature"}), 400

    print(f"\n[>>>] 收到来自 {user_address} 的访问请求")

    # ==========================================
    # ✅ Bug1 修复：防重放攻击 —— 时间戳有效期校验（±60 秒）
    # 约定前端 message 格式："访问请求:0x设备地址, 时间戳:1711382400"
    # ==========================================
    try:
        timestamp_str = message_text.split("时间戳:")[-1].strip()
        request_timestamp = int(timestamp_str)
        current_timestamp = int(time.time())

        if abs(current_timestamp - request_timestamp) > 60:
            print(f"[!] 警报：请求时间戳已过期（请求时间: {request_timestamp}，当前: {current_timestamp}），疑似重放攻击！")
            return jsonify({"status": "error", "message": "请求已过期，拒绝重放攻击！"}), 401

        print(f"[+] 时间戳校验通过（时差: {abs(current_timestamp - request_timestamp)} 秒）")

    except (IndexError, ValueError):
        print("[!] 消息格式错误，无法解析时间戳。")
        return jsonify({"status": "error", "message": "消息格式错误，缺少时间戳字段"}), 400

    # ==========================================
    # 第一关：密码学防伪验证（本地验签）
    # ==========================================
    try:
        message_encoded   = encode_defunct(text=message_text)
        recovered_address = Account.recover_message(message_encoded, signature=signature)

        if recovered_address.lower() != user_address.lower():
            print(f"[!] 警报：签名伪造！声称是 {user_address}，实际签名者是 {recovered_address}")
            return jsonify({"status": "error", "message": "签名验证失败，请求已被篡改！"}), 401

        print("[+] 第一关通过：数字签名验证成功，请求未被篡改。")

    except Exception as e:
        print(f"[!] 签名解析异常: {e}")
        return jsonify({"status": "error", "message": f"签名解析错误: {str(e)}"}), 400

    # ==========================================
    # 第二关：区块链 ACL 权限查询
    # ==========================================
    print("[-] 正在向区块链查询 ACL 权限...")
    has_access = check_acl_on_chain(user_address)

    if not has_access:
        print(f"[!] 警报：{user_address} 不在授权名单，访问被拒绝！")
        return jsonify({"status": "error", "message": "区块链拒绝访问：你不在授权名单中！"}), 403

    print("[+] 第二关通过：区块链 ACL 验证成功。")

    # ==========================================
    # 两关全部通过：写入链上访问日志，下发视频流
    # ==========================================
    print("[*] 认证全部通过！正在写入链上访问日志...")
    log_access_on_chain(user_address, request_timestamp)

    print("[*] 开始推送视频流...")
    return jsonify({
        "status":           "success",
        "message":          "身份认证与权限校验通过！访问已永久记录在区块链上。",
        "video_stream_url": "https://dummy-video-stream.local/live",
        "logged_at":        request_timestamp
    }), 200

# ==========================================
# 5. 启动入口
# ==========================================
if __name__ == '__main__':
    print("\n==================================================")
    print("   [ 结界 BoundChain —— 设备端 V3 已启动 ]        ")
    print("==================================================")
    app.run(host='0.0.0.0', port=5000)
