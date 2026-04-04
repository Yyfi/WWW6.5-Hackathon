// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IoTIdentityAuth
 * @dev 结界 BoundChain V4 —— 去中心化设备主权协议
 *
 * V4 核心改动：彻底移除全局管理员（Admin）角色。
 * 任何人都可以注册自己的设备，注册者自动成为该设备的唯一主人。
 * 只有设备主人才能授权或撤销他人的访问权限。
 * 没有任何第三方可以越过设备主人做决定——这才是真正的空间主权。
 *
 * 「你的设备，你来注册，你来授权。」
 */
contract IoTIdentityAuth {

    // ==========================================
    // 1. 数据结构
    // ==========================================

    struct Device {
        string  name;         // 设备别名
        address owner;        // 设备主人（注册者）——V4 新增
        bool    isRegistered; // 是否已注册
        bool    isActive;     // 是否激活
    }

    // 设备注册表：设备地址 → 设备信息
    mapping(address => Device) public devices;

    // 访问控制列表：用户地址 → 设备地址 → 是否有权限
    mapping(address => mapping(address => bool)) public acl;

    // ==========================================
    // 2. 事件
    // ==========================================

    event DeviceRegistered(address indexed deviceAddress, address indexed owner, string name);
    event DeviceStatusChanged(address indexed deviceAddress, bool isActive);
    event AccessGranted(address indexed user, address indexed device);
    event AccessRevoked(address indexed user, address indexed device);

    /**
     * @dev 成功访问的链上审计日志
     * 谁在何时成功进入了你的空间，永久刻在链上，不可篡改，无法抵赖。
     */
    event AccessLogged(
        address indexed user,
        address indexed device,
        uint256 timestamp
    );

    // ==========================================
    // 3. 权限修饰符
    // ==========================================

    /**
     * @dev V4 核心：只有设备的主人才能管理该设备
     * 取代了原来的 onlyAdmin，权限粒度从「全局管理员」下放到「设备主人」
     */
    modifier onlyDeviceOwner(address _device) {
        require(devices[_device].isRegistered, "Error: Device not found!");
        require(devices[_device].owner == msg.sender, "Access Denied: You are not the owner of this device!");
        _;
    }

    // 仅限已注册且激活的设备调用（用于写入访问日志）
    modifier onlyActiveDevice() {
        require(devices[msg.sender].isRegistered, "Access Denied: Device not registered!");
        require(devices[msg.sender].isActive,     "Access Denied: Device is disabled!");
        _;
    }

    // ==========================================
    // 4. 核心函数
    // ==========================================

    /**
     * @dev 注册新设备（任何人均可调用）
     * 调用者自动成为该设备的主人，无需经过任何管理员审批。
     * @param _device 设备的公钥地址（由 Python 端生成）
     * @param _name   设备别名，如「卧室摄像头」
     */
    function registerDevice(address _device, string memory _name) public {
        require(!devices[_device].isRegistered, "Error: Device already registered!");

        devices[_device] = Device({
            name:         _name,
            owner:        msg.sender, // 注册者即主人
            isRegistered: true,
            isActive:     true
        });

        emit DeviceRegistered(_device, msg.sender, _name);
    }

    /**
     * @dev 更改设备状态（仅设备主人）
     * 如发现设备被物理劫持，可紧急禁用。
     */
    function setDeviceStatus(address _device, bool _isActive) public onlyDeviceOwner(_device) {
        devices[_device].isActive = _isActive;
        emit DeviceStatusChanged(_device, _isActive);
    }

    /**
     * @dev 授予用户访问权限（仅设备主人）
     */
    function grantAccess(address _user, address _device) public onlyDeviceOwner(_device) {
        acl[_user][_device] = true;
        emit AccessGranted(_user, _device);
    }

    /**
     * @dev 撤销用户访问权限（仅设备主人）
     */
    function revokeAccess(address _user, address _device) public onlyDeviceOwner(_device) {
        acl[_user][_device] = false;
        emit AccessRevoked(_user, _device);
    }

    /**
     * @dev 查询访问权限（不消耗 Gas）
     * 由 Python 设备端在链下验签成功后调用。
     */
    function checkAccess(address _user, address _device) public view returns (bool) {
        if (!devices[_device].isRegistered || !devices[_device].isActive) {
            return false;
        }
        return acl[_user][_device];
    }

    /**
     * @dev 查询设备主人（不消耗 Gas）
     * 前端可调用此函数验证当前钱包是否为设备主人。
     */
    function getDeviceOwner(address _device) public view returns (address) {
        return devices[_device].owner;
    }

    /**
     * @dev 写入成功访问日志（仅已注册且激活的设备调用）
     * 设备用自己的私钥签名发交易，调用者必须是设备本身。
     */
    function logAccess(address _user, uint256 _timestamp) public onlyActiveDevice {
        require(acl[_user][msg.sender], "Error: Cannot log access for unauthorized user!");
        emit AccessLogged(_user, msg.sender, _timestamp);
    }
}
