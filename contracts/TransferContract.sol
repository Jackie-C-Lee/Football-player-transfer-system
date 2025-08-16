// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransferContract {
    // 转会状态枚举
    enum TransferStatus {
        Proposed,    // 卖方已提议
        Accepted,    // 买方已接受
        Validated,   // 监管方已验证
        Completed,   // 转会完成
        Rejected     // 转会被拒绝
    }

    // 转会记录结构体
    struct Transfer {
        address sellingClub;        // 卖方地址
        address buyingClub;         // 买方地址
        uint256 playerId;           // 球员ID
        uint256 transferFee;        // 转会费
        uint256 proposalTimestamp;  // 提议时间
        uint256 acceptanceTimestamp; // 接受时间
        uint256 validationTimestamp; // 验证时间
        TransferStatus status;      // 转会状态
        string lshIncomeHash;       // LSH收入哈希
        string lshExpenseHash;      // LSH支出哈希
        bool isLegitimate;          // 是否合法
    }

    // 俱乐部结构体
    struct Club {
        string name;
        string country;
        bool isRegistered;
    }

    // 状态变量
    mapping(uint256 => Transfer) public transfers;
    mapping(address => Club) public clubs;
    mapping(address => bool) public registeredClubs;
    uint256 public transferCount;
    address public owner;

    // 事件
    event ClubRegistered(address indexed clubAddress, string name);
    event TransferProposed(uint256 indexed transferId, address indexed seller, address indexed buyer, uint256 playerId, uint256 transferFee);
    event TransferAccepted(uint256 indexed transferId, address indexed buyer);
    event TransferValidated(uint256 indexed transferId, bool isLegitimate);
    event TransferCompleted(uint256 indexed transferId);
    event TransferRejected(uint256 indexed transferId, string reason);

    // 修饰符
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier onlyRegisteredClub() {
        require(registeredClubs[msg.sender], "Only registered clubs can call this function");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // 注册俱乐部
    function registerClub(string memory _name, string memory _country) public {
        require(!registeredClubs[msg.sender], "Club already registered");

        clubs[msg.sender] = Club({
            name: _name,
            country: _country,
            isRegistered: true
        });

        registeredClubs[msg.sender] = true;
        emit ClubRegistered(msg.sender, _name);
    }

    // 步骤1：卖方发起转会提议
    function proposeTransfer(
        address _buyingClub,
        uint256 _playerId,
        uint256 _transferFee,
        string memory _lshIncomeHash
    ) public onlyRegisteredClub {
        require(registeredClubs[_buyingClub], "Buying club not registered");
        require(_transferFee > 0, "Transfer fee must be greater than 0");
        require(msg.sender != _buyingClub, "Cannot transfer to self");

        transferCount++;

        transfers[transferCount] = Transfer({
            sellingClub: msg.sender,
            buyingClub: _buyingClub,
            playerId: _playerId,
            transferFee: _transferFee,
            proposalTimestamp: block.timestamp,
            acceptanceTimestamp: 0,
            validationTimestamp: 0,
            status: TransferStatus.Proposed,
            lshIncomeHash: _lshIncomeHash,
            lshExpenseHash: "",
            isLegitimate: false
        });

        emit TransferProposed(transferCount, msg.sender, _buyingClub, _playerId, _transferFee);
    }

    // 步骤2：买方接受转会提议
    function acceptTransfer(
        uint256 _transferId,
        string memory _lshExpenseHash
    ) public onlyRegisteredClub {
        require(_transferId <= transferCount && _transferId > 0, "Invalid transfer ID");
        Transfer storage transfer = transfers[_transferId];

        require(transfer.buyingClub == msg.sender, "Only designated buying club can accept");
        require(transfer.status == TransferStatus.Proposed, "Transfer not in proposed status");

        transfer.lshExpenseHash = _lshExpenseHash;
        transfer.acceptanceTimestamp = block.timestamp;
        transfer.status = TransferStatus.Accepted;

        emit TransferAccepted(_transferId, msg.sender);
    }

    // 步骤3：监管方验证转会
    function validateTransfer(
        uint256 _transferId,
        bool _isLegitimate
    ) public onlyOwner {
        require(_transferId <= transferCount && _transferId > 0, "Invalid transfer ID");
        Transfer storage transfer = transfers[_transferId];

        require(transfer.status == TransferStatus.Accepted, "Transfer not accepted yet");

        transfer.validationTimestamp = block.timestamp;
        transfer.isLegitimate = _isLegitimate;
        transfer.status = TransferStatus.Validated;

        if (_isLegitimate) {
            transfer.status = TransferStatus.Completed;
            emit TransferCompleted(_transferId);
        } else {
            transfer.status = TransferStatus.Rejected;
            emit TransferRejected(_transferId, "Failed LSH validation");
        }

        emit TransferValidated(_transferId, _isLegitimate);
    }

    // 卖方可以取消还未被接受的转会提议
    function cancelTransfer(uint256 _transferId) public onlyRegisteredClub {
        require(_transferId <= transferCount && _transferId > 0, "Invalid transfer ID");
        Transfer storage transfer = transfers[_transferId];

        require(transfer.sellingClub == msg.sender, "Only selling club can cancel");
        require(transfer.status == TransferStatus.Proposed, "Can only cancel proposed transfers");

        transfer.status = TransferStatus.Rejected;
        emit TransferRejected(_transferId, "Cancelled by selling club");
    }

    // 查询函数：获取转会的完整状态
    function getTransferDetails(uint256 _transferId)
        public view returns (
            address sellingClub,
            address buyingClub,
            uint256 playerId,
            uint256 transferFee,
            TransferStatus status,
            uint256 proposalTime,
            uint256 acceptanceTime,
            uint256 validationTime,
            bool isLegitimate,
            string memory incomeHash,
            string memory expenseHash
        ) {
        require(_transferId <= transferCount && _transferId > 0, "Invalid transfer ID");
        Transfer storage transfer = transfers[_transferId];

        return (
            transfer.sellingClub,
            transfer.buyingClub,
            transfer.playerId,
            transfer.transferFee,
            transfer.status,
            transfer.proposalTimestamp,
            transfer.acceptanceTimestamp,
            transfer.validationTimestamp,
            transfer.isLegitimate,
            transfer.lshIncomeHash,
            transfer.lshExpenseHash
        );
    }

    // 获取俱乐部信息
    function getClub(address _clubAddress) public view returns (Club memory) {
        return clubs[_clubAddress];
    }

    // 检查俱乐部是否注册
    function isClubRegistered(address _clubAddress) public view returns (bool) {
        return registeredClubs[_clubAddress];
    }

    // 获取转会状态的字符串表示
    function getTransferStatusString(uint256 _transferId) public view returns (string memory) {
        require(_transferId <= transferCount && _transferId > 0, "Invalid transfer ID");

        TransferStatus status = transfers[_transferId].status;

        if (status == TransferStatus.Proposed) return "Proposed";
        if (status == TransferStatus.Accepted) return "Accepted";
        if (status == TransferStatus.Validated) return "Validated";
        if (status == TransferStatus.Completed) return "Completed";
        if (status == TransferStatus.Rejected) return "Rejected";

        return "Unknown";
    }

    // 获取俱乐部参与的所有转会（作为卖方）
    function getClubSales(address _clubAddress) public view returns (uint256[] memory) {
        uint256[] memory tempResults = new uint256[](transferCount);
        uint256 count = 0;

        for (uint256 i = 1; i <= transferCount; i++) {
            if (transfers[i].sellingClub == _clubAddress) {
                tempResults[count] = i;
                count++;
            }
        }

        uint256[] memory results = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            results[i] = tempResults[i];
        }

        return results;
    }

    // 获取俱乐部参与的所有转会（作为买方）
    function getClubPurchases(address _clubAddress) public view returns (uint256[] memory) {
        uint256[] memory tempResults = new uint256[](transferCount);
        uint256 count = 0;

        for (uint256 i = 1; i <= transferCount; i++) {
            if (transfers[i].buyingClub == _clubAddress) {
                tempResults[count] = i;
                count++;
            }
        }

        uint256[] memory results = new uint256[](count);
        for (uint256 i = 0; i < count; i++) {
            results[i] = tempResults[i];
        }

        return results;
    }
}