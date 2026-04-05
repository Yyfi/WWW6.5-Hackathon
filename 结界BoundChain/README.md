BoundChain · Barrier Protocol

Your space, your rules.
A Trust Protocol for Women's Safe Spaces · Women's Spatial Sovereignty Protocol

In this world, the place where women need safety the most
is often the place most easily violated.

Not the street. Not the workplace—
but the bedroom, the living room,
the space you believed only you could see.

BoundChain redefines who can enter your space
using cryptography and blockchain.

Project Overview

BoundChain is a blockchain-based IoT identity authentication and access control protocol.

In traditional smart home systems, access permissions are controlled by centralized servers.
If the server is breached, an account is compromised, or someone retains access they shouldn’t (e.g., an ex-partner), users ultimately do not have real control over their own devices.

BoundChain returns that control to the user:

On-chain Device Identity
Each device has a unique blockchain identity generated via ECDSA, independent of any centralized platform
Smart Contract-based Permissions (ACL)
Access control is written into smart contracts; wallet addresses act as permission credentials
Immutable Access Logs
Every successful access triggers an on-chain event—timestamp, identity, and device are permanently recorded

Who accessed your space — is permanently on-chain.

Core Features
🔐 Decentralized Identity Authentication

Each device generates a private key using ECDSA upon first launch, deriving an Ethereum address as its on-chain identity.
The private key is stored locally and is never uploaded to any server.

📋 On-chain Access Control List (ACL)

Implemented via a nested mapping in Solidity:

User Address → Device Address → Access Permission (true/false)

Permissions are granted and revoked solely by the device owner and written directly to the blockchain.
No third party can interfere.

🛡️ Two-Layer Authentication Mechanism
Layer 1: Off-chain Signature Verification (local, fast, zero gas)
         ↓ Verify signature authenticity via ECDSA recovery

Layer 2: On-chain Authorization (Sepolia, free view call)
         ↓ Check ACL contract for user permission

If both pass → Write access log on-chain
🔒 Replay Attack Protection

Each access request includes a Unix timestamp.
The device validates it within a ±60 second window, preventing reuse of old signatures.

📝 Immutable Access Logs

Upon successful authentication, the device signs and sends a transaction to log access:

event AccessLogged(
    address indexed user,
    address indexed device,
    uint256 timestamp
);

Each record is permanently stored on-chain and publicly verifiable via Etherscan.

👑 Admin-less Architecture (V4)

Anyone can register their own device, and the registrant automatically becomes the sole owner.

There is:

No super admin
No centralized authority
No intermediary capable of overriding your decisions
Technical Architecture
┌─────────────────────────────────────────────────┐
│                Frontend (HTML/JS)                │
│  MetaMask Signing → Request → Display Logs      │
└───────────────────┬─────────────────────────────┘
                    │ HTTP POST (message + signature + address)
┌───────────────────▼─────────────────────────────┐
│          Device Layer (Python / Flask)          │
│  Layer 1: Local signature verification         │
│  Layer 2: Query on-chain ACL via Web3.py       │
│  If passed: Write AccessLogged event           │
└───────────────────┬─────────────────────────────┘
                    │ Web3.py RPC Call
┌───────────────────▼─────────────────────────────┐
│        Smart Contract (Solidity / Sepolia)      │
│  Device Registry · ACL · Access Log Events      │
└─────────────────────────────────────────────────┘
Project Structure
boundchain/
├── Identity_v4.sol      # Smart contract (admin-less architecture)
├── camera_v3.py         # Device (Flask server + verification + on-chain query)
├── setup.py             # Initialization script (register + authorize)
├── boundchain_v2.html   # Frontend (owner + guest interface)
└── README.md
Quick Start
Requirements
Python 3.8+
MetaMask browser extension
Sepolia testnet ETH (free from https://sepoliafaucet.com
)
Install Dependencies
pip install flask flask-cors web3 eth-account
Deploy Smart Contract
Open https://remix.ethereum.org
Import Identity_v4.sol
Connect MetaMask (Sepolia network)
Compile & deploy, then save contract address
Configuration

camera_v3.py

RPC_URL          = "https://sepolia.infura.io/v3/YOUR_KEY"
CONTRACT_ADDRESS = "0xYOUR_CONTRACT_ADDRESS"

setup.py

ADMIN_PRIVATE_KEY = "0xYOUR_PRIVATE_KEY"   # ⚠️ remove after use
RPC_URL           = "https://sepolia.infura.io/v3/YOUR_KEY"
CONTRACT_ADDRESS  = "0xYOUR_CONTRACT_ADDRESS"
USER_ADDRESS      = "0xAUTHORIZED_USER_ADDRESS"

boundchain_v2.html

const CONTRACT_ADDRESS = "0xYOUR_CONTRACT_ADDRESS";
Run the System

Terminal 1: Start Device

python camera_v3.py
# Generates device identity
# Prints device address

Terminal 2: Initialize Blockchain State

python setup.py
# Registers device + grants permission (~30s)

Terminal 3: Start Frontend

python -m http.server 8080
# Open http://localhost:8080/boundchain_v2.html
Test Workflow
Connect as device owner, confirm device is listed
Switch to guest wallet, click "Request Access"
Sign via MetaMask (no gas)
Wait for verification and check on-chain logs
Security Notes
Device Private Key
Stored locally in device_private_key.txt, ignored by .gitignore
Admin Private Key
Used only in setup.py, must be deleted after initialization
Testnet Only
Runs on Sepolia testnet, no real asset value
Design Decision: Why Remove Admin

In V3, a global admin approved device registration and permissions.

This meant:

"Who can enter your space" was still decided by a third party.

Which contradicts the core idea of user sovereignty.

V4 Redesign
V3: User → Admin Approval → Access Granted
V4: User → Direct Contract Interaction → Access Granted

The registrant is the owner.
The owner is the authority.
No intermediaries.

This is not just a technical upgrade—
it is our interpretation of true decentralization.

Roadmap
 ECDSA device identity
 On-chain ACL
 Off-chain verification + anti-replay
 On-chain access logging
 Admin-less architecture (V4)
 Time-limited access (e.g., cleaners)
 Dead Man’s Switch (inheritance mechanism)
 Multi-device management
 Mobile support
Hackathon Info

This project is submitted to Herstory Hackathon 2026
Track: Life & Co-existence · Body Autonomy
# 结界 BoundChain

**你的空间，只有你说了算。**  
*A Trust Protocol for Women's Safe Spaces · 女性空间主权协议*

> 在这个世界上，女性最需要安全感的地方，往往是最容易被侵犯的地方。  
> 不是街道，不是公司——是卧室，是客厅，是你以为只有自己能看见的地方。  
> 结界用密码学与区块链重新定义「谁能进入你的空间」。

---

## 项目简介

结界 BoundChain 是一个基于区块链的 IoT 设备身份认证与访问控制协议。

传统智能家居设备的访问权限由厂商服务器掌控——服务器被攻击、账号被盗、前任不归还密码，用户对自己家中的设备毫无真正的控制权。

结界将这一控制权还给用户：

- **设备身份上链**：每台设备拥有由 ECDSA 算法生成的唯一区块链身份，不依赖任何中心化平台
- **权限写入合约**：访问控制列表（ACL）写在智能合约里，用户的钱包地址即权限凭证
- **访问永久留痕**：每一次成功访问都触发链上事件，时间、身份、设备，不可篡改，无法抵赖

> **谁看了你，链上留着。**

---

## 核心特性

### 🔐 去中心化身份认证
设备在首次启动时通过 ECDSA 算法生成私钥，推导出以太坊地址作为链上身份。私钥本地存储，从不上传任何服务器。

### 📋 链上访问控制列表（ACL）
基于 Solidity 智能合约的双重映射结构：
```
用户地址 → 设备地址 → 是否有权限
```
权限的授予与撤销由设备主人发起，写入区块链，任何第三方无法干预。

### 🛡️ 两关认证机制
```
第一关：链下验签（本地，极速，零 Gas）
         ↓ ECDSA 反推签名者地址，验证请求未被篡改
第二关：链上鉴权（Sepolia，免费 view 调用）
         ↓ 查询 ACL 合约，确认用户在白名单
全部通过 → 写入链上访问日志
```

### 🔒 防重放攻击
每次访问请求携带 Unix 时间戳，设备端校验时效（±60 秒），历史签名无法被重用。

### 📝 不可篡改的访问日志
认证通过后，设备以自己的私钥签名，向合约写入 `AccessLogged` 事件：
```solidity
event AccessLogged(
    address indexed user,
    address indexed device,
    uint256 timestamp
);
```
每一条记录永久刻在区块链上，可通过 Etherscan 公开查阅。

### 👑 无管理员架构（V4）
任何人都可以注册自己的设备，注册者自动成为该设备的唯一主人。没有超级管理员，没有任何中间人可以越过你做决定。

---

## 技术架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (HTML/JS)                  │
│  MetaMask 签名 → 发送请求 → 展示链上日志          │
└───────────────────┬─────────────────────────────┘
                    │ HTTP POST (签名 + 明文 + 地址)
┌───────────────────▼─────────────────────────────┐
│              设备端 (Python/Flask)                │
│  第一关：eth_account 本地验签                     │
│  第二关：Web3.py 查询链上 ACL                     │
│  通过后：向合约写入 AccessLogged 事件             │
└───────────────────┬─────────────────────────────┘
                    │ Web3.py RPC 调用
┌───────────────────▼─────────────────────────────┐
│           智能合约 (Solidity/Sepolia)             │
│  设备注册表 · 访问控制列表 · 访问日志 Events      │
└─────────────────────────────────────────────────┘
```

---

## 文件结构

```
boundchain/
├── Identity_v4.sol      # 智能合约（无管理员架构）
├── camera_v3.py         # 设备端（Flask 服务 + 验签 + 链上查询）
├── setup.py             # 初始化脚本（注册设备 + 授权用户）
├── boundchain_v2.html   # 前端界面（设备主人 + 访客双视角）
└── README.md
```

---

## 快速开始

### 环境要求

- Python 3.8+
- MetaMask 浏览器插件
- Sepolia 测试网 ETH（从 [sepoliafaucet.com](https://sepoliafaucet.com) 免费领取）

### 安装依赖

```bash
pip install flask flask-cors web3 eth-account
```

### 部署智能合约

1. 打开 [remix.ethereum.org](https://remix.ethereum.org)
2. 导入 `Identity_v4.sol`
3. 连接 MetaMask（Sepolia 测试网）
4. 编译并部署，保存合约地址

### 配置文件

在以下文件中填入你的配置：

**`camera_v3.py`**
```python
RPC_URL          = "https://sepolia.infura.io/v3/你的KEY"
CONTRACT_ADDRESS = "0x你的合约地址"
```

**`setup.py`**
```python
ADMIN_PRIVATE_KEY = "0x你的管理员私钥"   # ⚠️ 运行后删除
RPC_URL           = "https://sepolia.infura.io/v3/你的KEY"
CONTRACT_ADDRESS  = "0x你的合约地址"
USER_ADDRESS      = "0x被授权的用户钱包地址"
```

**`boundchain_v2.html`**
```javascript
const CONTRACT_ADDRESS = "0x你的合约地址";
```

### 运行

**终端一：启动设备端**
```bash
python camera_v3.py
# 首次运行会生成设备密钥，打印设备地址
# [-] 设备的区块链身份证 (公钥地址): 0x...
```

**终端二：初始化链上数据（首次运行）**
```bash
python setup.py
# 完成设备注册 + 用户授权，约需 30 秒
```

**终端三：启动前端服务**
```bash
python -m http.server 8080
# 浏览器访问 http://localhost:8080/boundchain_v2.html
```

### 测试完整流程

1. 用**设备主人钱包**连接前端，切到「我是设备主人」，确认设备出现
2. 切换到**访客钱包**，切到「我是访客」，点击「请求访问」
3. MetaMask 弹出签名请求，确认（无 Gas 费）
4. 等待认证通过，查看页面底部链上访问日志

---

## 安全说明

- **私钥**：设备私钥保存在本地 `device_private_key.txt`，已加入 `.gitignore`，请勿上传
- **管理员私钥**：仅在 `setup.py` 中使用，运行完成后请立即删除该行
- **测试网**：本项目当前部署在 Sepolia 测试网，所有 ETH 均为测试代币，无真实价值

---

## 设计决策：为什么移除管理员

V3 版本存在一个全局管理员角色，负责审批所有设备注册和用户授权。

这意味着「谁能进入你家」这件事，本质上仍然由第三方来决定——与「女性空间主权」的核心直接矛盾。

V4 彻底移除了管理员角色：

```
V3：用户 → 管理员审批 → 权限生效
V4：用户 → 直接写入合约 → 权限生效
```

注册者即主人，主人即权威，没有任何中间人。这不只是一个技术改动，这是我们对「去中心化」的真正理解。

---

## 路线图

- [x] 设备 ECDSA 身份生成
- [x] 链上 ACL 访问控制
- [x] 链下验签 + 防重放攻击
- [x] 成功访问链上日志
- [x] 无管理员架构（V4）
- [ ] 时效授权（临时访问，如家政钟点工）
- [ ] Dead Man's Switch（长期未活跃自动继承权限）
- [ ] 多设备批量管理
- [ ] 移动端适配

---

## 参赛信息

本项目参加 **Herstory Hackathon 2026**  
赛道：赛道一 · 生命与共生 · 身体主权方向

---

## License

MIT
