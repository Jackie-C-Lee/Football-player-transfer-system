import json
import os
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv


load_dotenv()


def deploy_contract():
    # 安装Solidity编译器
    install_solc("0.8.19")

    # 读取合约源代码
    with open("./contracts/TransferContract.sol", "r", encoding='utf-8') as file:
        contract_source_code = file.read()

    # 编译合约
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"TransferContract.sol": {"content": contract_source_code}},
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            },
        },
        solc_version="0.8.19",
    )

    # 获取bytecode和ABI
    bytecode = compiled_sol["contracts"]["TransferContract.sol"]["TransferContract"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["TransferContract.sol"]["TransferContract"]["abi"]

    # 连接到Ganache
    w3 = Web3(Web3.HTTPProvider(os.getenv('GANACHE_URL')))
    chain_id = int(os.getenv('CHAIN_ID'))
    my_address = os.getenv('ACCOUNT_ADDRESS')
    private_key = os.getenv('PRIVATE_KEY')

    print(f"连接到Ganache: {w3.is_connected()}")
    print(f"账户地址: {my_address}")
    print(f"账户余额: {w3.from_wei(w3.eth.get_balance(my_address), 'ether')} ETH")

    if not w3.is_connected():
        print("无法连接到Ganache，请检查配置")
        return None, None

    # 创建合约实例
    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # 获取nonce
    nonce = w3.eth.get_transaction_count(my_address)

    # 估算gas
    try:
        gas_estimate = contract.constructor().estimate_gas({'from': my_address})
        print(f"预估Gas用量: {gas_estimate}")
    except Exception as e:
        print(f"Gas估算失败: {e}")
        gas_estimate = 2000000  # 使用默认值

    # 构建部署交易
    transaction = contract.constructor().build_transaction({
        "chainId": chain_id,
        "gas": gas_estimate + 100000,  # 添加一些余量
        "gasPrice": w3.eth.gas_price,
        "from": my_address,
        "nonce": nonce,
    })

    print(f"Gas Price: {w3.eth.gas_price}")
    print(f"Total Gas: {transaction['gas']}")

    # 签名交易
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=private_key)

    # 发送交易
    print("正在部署合约...")
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)  # 修复：使用raw_transaction
        print(f"交易哈希: {tx_hash.hex()}")

        # 等待交易确认
        print("等待交易确认...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if tx_receipt.status == 1:
            print(f"合约部署成功!")
            print(f"合约地址: {tx_receipt.contractAddress}")
            print(f"Gas Used: {tx_receipt.gasUsed}")
        else:
            print(f"合约部署失败，状态: {tx_receipt.status}")
            return None, None

    except Exception as e:
        print(f"部署过程出错: {e}")
        return None, None

    # 保存合约信息
    contract_data = {
        "address": tx_receipt.contractAddress,
        "abi": abi
    }

    with open("contract_info.json", "w") as f:
        json.dump(contract_data, f, indent=2)

    # 更新.env文件
    env_content = ""
    if os.path.exists(".env"):
        with open(".env", "r", encoding='utf-8') as f:
            env_content = f.read()

    # 更新或添加CONTRACT_ADDRESS
    lines = env_content.split('\n')
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('CONTRACT_ADDRESS='):
            lines[i] = f"CONTRACT_ADDRESS={tx_receipt.contractAddress}"
            updated = True
            break

    if not updated:
        lines.append(f"CONTRACT_ADDRESS={tx_receipt.contractAddress}")

    with open(".env", "w", encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print("合约信息已保存到 contract_info.json")
    print(".env 文件已更新")

    # 验证部署
    print("\n=== 验证部署 ===")
    try:
        deployed_contract = w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)
        owner = deployed_contract.functions.owner().call()
        transfer_count = deployed_contract.functions.transferCount().call()

        print(f"合约Owner: {owner}")
        print(f"当前账户: {my_address}")
        print(f"是否为Owner: {owner.lower() == my_address.lower()}")
        print(f"初始转会数量: {transfer_count}")

    except Exception as e:
        print(f"验证失败: {e}")

    return tx_receipt.contractAddress, abi


if __name__ == "__main__":
    deploy_contract()