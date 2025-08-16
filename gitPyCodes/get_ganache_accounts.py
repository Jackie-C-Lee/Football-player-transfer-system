# -*- coding: utf-8 -*-
"""
Ganache 账户信息获取工具
自动获取 Ganache 账户地址并生成 init_database_enhanced.py 的配置代码
"""

import os
from web3 import Web3
from dotenv import load_dotenv
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')  # 改变标准输出的默认编码

load_dotenv()


def get_ganache_accounts():
    """从 Ganache 获取账户信息"""
    print("正在连接 Ganache...")

    ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
    w3 = Web3(Web3.HTTPProvider(ganache_url))

    if not w3.is_connected():
        print("❌ 无法连接到 Ganache")
        print(f"   URL: {ganache_url}")
        print("请确保：")
        print("1. Ganache 正在运行")
        print("2. .env 文件中的 GANACHE_URL 配置正确")
        return None

    print("✅ 成功连接到 Ganache")

    # 获取前5个账户
    accounts = w3.eth.accounts[1:6]

    if len(accounts) < 5:
        print(f"⚠️ 只找到 {len(accounts)} 个账户，需要至少5个账户")
        return None

    print(f"\n📋 找到 {len(accounts)} 个账户：")
    print("=" * 80)

    account_info = []

    for i, account in enumerate(accounts):
        try:
            balance = w3.eth.get_balance(account)
            balance_eth = w3.from_wei(balance, 'ether')

            account_data = {
                'index': i + 1,
                'address': account,
                'balance': float(balance_eth)
            }
            account_info.append(account_data)

            print(f"账户 {i + 1}: {account}")
            print(f"        余额: {balance_eth:.2f} ETH")
            print()

        except Exception as e:
            print(f"❌ 获取账户 {i + 1} 信息失败: {e}")

    return account_info


def generate_config_code(account_info):
    """生成配置代码"""
    if not account_info or len(account_info) < 5:
        print("❌ 账户信息不足，无法生成配置")
        return

    print("🔧 生成配置代码...")
    print("=" * 80)

    # 生成 ganache_accounts 配置
    config_code = """# 请将以下代码替换到 init_database_enhanced.py 中的 ganache_accounts 部分
# 注意：私钥需要从 Ganache GUI 或启动日志中手动获取

ganache_accounts = ["""

    for i, account in enumerate(account_info):
        config_code += f"""
    {{
        'address': '{account['address']}',
        'private_key': '0x...'  # 请从 Ganache 获取第{account['index']}个账户的私钥
    }},"""

    config_code += """
]"""

    print(config_code)
    print()

    # 生成 .env 配置
    print("🔧 建议的 .env 配置：")
    print("-" * 50)
    print(f"GANACHE_URL={os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')}")
    print("CHAIN_ID=1337")
    print(f"ACCOUNT_ADDRESS={account_info[0]['address']}")
    print("PRIVATE_KEY=0x...  # 请从 Ganache 获取第1个账户的私钥")

    return True


def show_instructions():
    """显示后续操作指南"""
    print("\n📝 后续操作步骤：")
    print("=" * 80)
    print("1. 📋 从 Ganache 获取私钥：")
    print("   - 如果使用 Ganache GUI：点击每个账户右侧的 🔑 图标")
    print("   - 如果使用命令行：查看启动时显示的 'Private Keys' 部分")
    print()
    print("2. ✏️  更新代码：")
    print("   - 将生成的配置代码复制到 init_database_enhanced.py")
    print("   - 用实际私钥替换所有的 '0x...'")
    print("   - 更新 .env 文件中的 ACCOUNT_ADDRESS 和 PRIVATE_KEY")
    print()
    print("3. 🚀 运行系统：")
    print("   python init_database_enhanced.py")
    print("   python deploy_contract.py")
    print("   python register_clubs.py")
    print("   python enhanced_transfer_manager.py")
    print()
    print("💡 提示：如果您使用 ganache-cli --deterministic 启动，")
    print("   私钥是固定的，可以重复使用相同的配置。")


def main():
    """主函数"""
    print("⚽ 足球转会系统 - Ganache 账户信息获取工具")
    print("=" * 80)

    # 获取账户信息
    account_info = get_ganache_accounts()

    if not account_info:
        print("\n❌ 无法获取账户信息，请检查 Ganache 连接")
        return

    # 生成配置代码
    if generate_config_code(account_info):
        show_instructions()

    print("\n" + "=" * 80)
    print("✅ 账户信息获取完成！")


if __name__ == "__main__":
    main()