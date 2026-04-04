from web3 import Web3
import json

# ==========================================
# 填入你的信息（运行前必须完成）
# ==========================================
ADMIN_PRIVATE_KEY = "0x5b79a05ae53d23707f71eed37824dec776db9ce4eeadbf53f5a94adf5b0dd5be"  # ⚠️ 填完运行后记得删掉

RPC_URL           = "https://sepolia.infura.io/v3/df7b552f6dfe412dbe5590478215573a"
CONTRACT_ADDRESS  = "0xa5f5984184b6E0BbAa02758e94d6B714F3f48a8A"
DEVICE_ADDRESS    = "0x820f8965453eF402Cf7bB870d37D88120d03D1F3"  # camera_v3.py 打印的设备地址
USER_ADDRESS      = "0x89d1EcE69Fb3A7cE107bBe5ab848c9acb2F65452"  # 第二个钱包（普通用户）
DEVICE_NAME       = "客厅摄像头"

# 包含所有需要调用函数的 ABI
CONTRACT_ABI = json.loads('''[
    {
        "inputs": [
            {"internalType": "address", "name": "_device", "type": "address"},
            {"internalType": "string",  "name": "_name",   "type": "string"}
        ],
        "name": "registerDevice",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_user",   "type": "address"},
            {"internalType": "address", "name": "_device", "type": "address"}
        ],
        "name": "grantAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_user",   "type": "address"},
            {"internalType": "address", "name": "_device", "type": "address"}
        ],
        "name": "checkAccess",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]''')

# ==========================================
# 连接区块链
# ==========================================
print("\n[*] 正在连接 Sepolia 测试网...")
w3 = Web3(Web3.HTTPProvider(RPC_URL))

if not w3.is_connected():
    print("[!] 连接失败，请检查 RPC_URL 是否正确。")
    exit(1)

print("[+] 连接成功！")

admin_account = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
print(f"[-] 管理员地址：{admin_account.address}")

contract = w3.eth.contract(
    address=Web3.to_checksum_address(CONTRACT_ADDRESS),
    abi=CONTRACT_ABI
)

# ==========================================
# 工具函数：发送交易
# ==========================================
def send_transaction(fn):
    """构建、签名、广播一笔交易，等待上链确认。"""
    nonce = w3.eth.get_transaction_count(admin_account.address)
    txn   = fn.build_transaction({
        'chainId':  11155111,
        'gas':      200000,
        'gasPrice': w3.eth.gas_price,
        'nonce':    nonce,
    })
    signed = w3.eth.account.sign_transaction(txn, private_key=ADMIN_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"    交易已广播，等待上链... hash: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f"    ✅ 上链成功！区块号: {receipt['blockNumber']}")
    return receipt

# ==========================================
# 第一步：注册设备
# ==========================================
print(f"\n[1/3] 正在注册设备「{DEVICE_NAME}」...")
print(f"      设备地址：{DEVICE_ADDRESS}")
try:
    send_transaction(
        contract.functions.registerDevice(
            Web3.to_checksum_address(DEVICE_ADDRESS),
            DEVICE_NAME
        )
    )
except Exception as e:
    # 如果已经注册过，合约会 revert，这里捕获后继续执行
    if "already registered" in str(e):
        print("    ⚠️  设备已注册，跳过此步骤。")
    else:
        print(f"    [!] registerDevice 失败: {e}")
        exit(1)

# ==========================================
# 第二步：授权用户
# ==========================================
print(f"\n[2/3] 正在授权用户访问设备...")
print(f"      用户地址：{USER_ADDRESS}")
try:
    send_transaction(
        contract.functions.grantAccess(
            Web3.to_checksum_address(USER_ADDRESS),
            Web3.to_checksum_address(DEVICE_ADDRESS)
        )
    )
except Exception as e:
    print(f"    [!] grantAccess 失败: {e}")
    exit(1)

# ==========================================
# 第三步：验证结果
# ==========================================
print(f"\n[3/3] 验证权限配置...")
result = contract.functions.checkAccess(
    Web3.to_checksum_address(USER_ADDRESS),
    Web3.to_checksum_address(DEVICE_ADDRESS)
).call()

if result:
    print("    ✅ checkAccess 返回 True，配置成功！")
    print("\n================================================")
    print("  🎉 结界 BoundChain 初始化完成，可以开始测试！")
    print("================================================")
    print(f"  设备地址：{DEVICE_ADDRESS}")
    print(f"  用户地址：{USER_ADDRESS}")
    print(f"  合约地址：{CONTRACT_ADDRESS}")
    print("  下一步：用第二个钱包对消息签名，发请求给 camera_v3.py")
else:
    print("    ❌ checkAccess 返回 False，请检查以上步骤是否出错。")
