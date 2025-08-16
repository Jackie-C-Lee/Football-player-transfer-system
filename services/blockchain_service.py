import json
import os
import sqlite3
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()


class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('GANACHE_URL')))
        self.chain_id = int(os.getenv('CHAIN_ID'))

        # 默认管理员账户（用于部署合约和验证转会）
        self.admin_address = self._ensure_checksum_address(os.getenv('ACCOUNT_ADDRESS'))
        self.admin_private_key = os.getenv('PRIVATE_KEY')

        # 加载合约信息
        try:
            with open('contract_info.json', 'r') as f:
                contract_info = json.load(f)
                self.contract_address = self._ensure_checksum_address(contract_info['address'])
                self.contract_abi = contract_info['abi']
                self.contract = self.w3.eth.contract(
                    address=self.contract_address,
                    abi=self.contract_abi
                )
        except FileNotFoundError:
            print("合约未部署，请先运行 deploy_contract.py")
            self.contract = None

    def _ensure_checksum_address(self, address):
        """确保地址使用正确的EIP-55校验和格式，兼容不同版本的Web3.py"""
        if not address:
            return None

        try:
            if hasattr(Web3, 'to_checksum_address'):
                return Web3.to_checksum_address(address)
            elif hasattr(Web3, 'toChecksumAddress'):
                return Web3.toChecksumAddress(address)
            elif hasattr(self.w3, 'toChecksumAddress'):
                return self.w3.toChecksumAddress(address)
            elif hasattr(self.w3, 'to_checksum_address'):
                return self.w3.to_checksum_address(address)
            else:
                if self.w3.isAddress(address):
                    return address
                else:
                    print(f"警告: 地址格式可能不正确: {address}")
                    return address
        except Exception as e:
            print(f"地址格式化错误: {address}, 错误: {e}")
            return address

    def _send_raw_transaction(self, signed_txn):
        """发送原始交易，兼容不同版本的签名交易对象"""
        try:
            if hasattr(signed_txn, 'raw_transaction'):
                return self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            elif hasattr(signed_txn, 'rawTransaction'):
                return self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            else:
                return self.w3.eth.send_raw_transaction(signed_txn)
        except Exception as e:
            print(f"发送交易失败: {e}")
            print(f"签名交易对象属性: {dir(signed_txn)}")
            raise

    def _get_club_credentials(self, club_id):
        """从数据库获取俱乐部的钱包地址和私钥"""
        try:
            conn = sqlite3.connect('football_transfer_enhanced.db')
            cursor = conn.cursor()

            result = cursor.execute("""
                SELECT wallet_address, private_key, name 
                FROM clubs 
                WHERE club_id = ?
            """, (club_id,)).fetchone()

            conn.close()

            if result:
                address = self._ensure_checksum_address(result[0])
                return {
                    'address': address,
                    'private_key': result[1],
                    'name': result[2]
                }
            else:
                print(f"未找到俱乐部 {club_id} 的信息")
                return None

        except Exception as e:
            print(f"获取俱乐部凭据失败: {e}")
            return None

    def is_connected(self):
        """检查区块链连接状态"""
        return self.w3.is_connected()

    def get_balance(self, address=None):
        """获取账户余额"""
        if address is None:
            address = self.admin_address
        else:
            address = self._ensure_checksum_address(address)
            if not address:
                return 0
        return self.w3.eth.get_balance(address)

    def propose_transfer(self, selling_club_id: str, buying_club_id: str, player_id: int,
                         transfer_fee: int, income_hash: str):
        """步骤1：卖方发起转会提议 - 使用卖方俱乐部的账户"""
        if not self.contract:
            return {'success': False, 'error': 'Contract not available'}

        # 获取卖方俱乐部的账户信息
        selling_club = self._get_club_credentials(selling_club_id)
        if not selling_club:
            return {'success': False, 'error': f'Cannot find selling club {selling_club_id} credentials'}

        # 获取买方俱乐部的地址
        buying_club = self._get_club_credentials(buying_club_id)
        if not buying_club:
            return {'success': False, 'error': f'Cannot find buying club {buying_club_id} credentials'}

        try:
            print(f"步骤1 - 发起转会提议:")
            print(f"  卖方: {selling_club['name']} ({selling_club['address']})")
            print(f"  买方: {buying_club['name']} ({buying_club['address']})")
            print(f"  球员ID: {player_id}")
            print(f"  转会费: {transfer_fee}")

            # 检查两个俱乐部是否都已注册
            seller_registered = self.contract.functions.isClubRegistered(selling_club['address']).call()
            buyer_registered = self.contract.functions.isClubRegistered(buying_club['address']).call()

            if not seller_registered:
                return {'success': False, 'error': f'Selling club {selling_club["name"]} not registered on blockchain'}

            if not buyer_registered:
                return {'success': False, 'error': f'Buying club {buying_club["name"]} not registered on blockchain'}

            # 检查卖方账户余额
            balance = self.w3.eth.get_balance(selling_club['address'])
            if balance == 0:
                return {'success': False, 'error': f'Selling club has insufficient ETH balance'}

            # 估算gas
            gas_estimate = self.contract.functions.proposeTransfer(
                buying_club['address'],
                player_id,
                transfer_fee,
                income_hash
            ).estimate_gas({'from': selling_club['address']})

            nonce = self.w3.eth.get_transaction_count(selling_club['address'])

            transaction = self.contract.functions.proposeTransfer(
                buying_club['address'],
                player_id,
                transfer_fee,
                income_hash
            ).build_transaction({
                'chainId': self.chain_id,
                'gas': gas_estimate + 50000,
                'gasPrice': self.w3.eth.gas_price,
                'from': selling_club['address'],
                'nonce': nonce,
            })

            # 使用卖方俱乐部的私钥签名
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=selling_club['private_key'])
            tx_hash = self._send_raw_transaction(signed_txn)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if tx_receipt.status == 1:
                print("✅ 卖方转会提议已成功提交")
                current_transfer_count = self.get_transfer_count()
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'tx_receipt': tx_receipt,
                    'transfer_id': current_transfer_count
                }
            else:
                return {
                    'success': False,
                    'error': f'Transaction failed with status: {tx_receipt.status}'
                }

        except Exception as e:
            print(f"区块链发起转会提议错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def accept_transfer(self, transfer_id: int, buying_club_id: str, expense_hash: str):
        """步骤2：买方接受转会提议 - 使用买方俱乐部的账户"""
        if not self.contract:
            return {'success': False, 'error': 'Contract not available'}

        # 获取买方俱乐部的账户信息
        buying_club = self._get_club_credentials(buying_club_id)
        if not buying_club:
            return {'success': False, 'error': f'Cannot find buying club {buying_club_id} credentials'}

        try:
            print(f"步骤2 - 买方接受转会:")
            print(f"  买方: {buying_club['name']} ({buying_club['address']})")
            print(f"  转会ID: {transfer_id}")

            # 检查转会状态
            try:
                transfer_details = self.contract.functions.getTransferDetails(transfer_id).call()
                if transfer_details[4] != 0:  # status != Proposed
                    return {'success': False, 'error': 'Transfer is not in proposed status'}
            except Exception as e:
                return {'success': False, 'error': f'Invalid transfer ID or transfer not found: {e}'}

            # 检查买方账户余额
            balance = self.w3.eth.get_balance(buying_club['address'])
            if balance == 0:
                return {'success': False, 'error': f'Buying club has insufficient ETH balance'}

            # 估算gas
            gas_estimate = self.contract.functions.acceptTransfer(
                transfer_id,
                expense_hash
            ).estimate_gas({'from': buying_club['address']})

            nonce = self.w3.eth.get_transaction_count(buying_club['address'])

            transaction = self.contract.functions.acceptTransfer(
                transfer_id,
                expense_hash
            ).build_transaction({
                'chainId': self.chain_id,
                'gas': gas_estimate + 50000,
                'gasPrice': self.w3.eth.gas_price,
                'from': buying_club['address'],
                'nonce': nonce,
            })

            # 使用买方俱乐部的私钥签名
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=buying_club['private_key'])
            tx_hash = self._send_raw_transaction(signed_txn)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if tx_receipt.status == 1:
                print("✅ 买方转会接受已成功确认")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'tx_receipt': tx_receipt
                }
            else:
                return {
                    'success': False,
                    'error': f'Transaction failed with status: {tx_receipt.status}'
                }

        except Exception as e:
            print(f"区块链接受转会错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def validate_transfer(self, transfer_id: int, is_legitimate: bool):
        """步骤3：监管方验证转会 - 使用管理员账户"""
        if not self.contract:
            return {'success': False, 'error': 'Contract not available'}

        try:
            print(f"步骤3 - 监管方验证转会:")
            print(f"  转会ID: {transfer_id}")
            print(f"  验证结果: {'合法' if is_legitimate else '违法'}")

            # 检查是否为合约owner
            owner = self.contract.functions.owner().call()
            owner = self._ensure_checksum_address(owner)

            if owner.lower() != self.admin_address.lower():
                return {'success': False,
                        'error': f'Only contract owner ({owner}) can validate transfers. Current account: {self.admin_address}'}

            # 检查转会状态
            try:
                transfer_details = self.contract.functions.getTransferDetails(transfer_id).call()
                if transfer_details[4] != 1:  # status != Accepted
                    return {'success': False, 'error': 'Transfer is not in accepted status, cannot validate'}
            except Exception as e:
                return {'success': False, 'error': f'Invalid transfer ID or transfer not found: {e}'}

            # 估算gas
            gas_estimate = self.contract.functions.validateTransfer(
                transfer_id,
                is_legitimate
            ).estimate_gas({'from': self.admin_address})

            nonce = self.w3.eth.get_transaction_count(self.admin_address)

            transaction = self.contract.functions.validateTransfer(
                transfer_id,
                is_legitimate
            ).build_transaction({
                'chainId': self.chain_id,
                'gas': gas_estimate + 50000,
                'gasPrice': self.w3.eth.gas_price,
                'from': self.admin_address,
                'nonce': nonce,
            })

            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.admin_private_key)
            tx_hash = self._send_raw_transaction(signed_txn)
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

            if tx_receipt.status == 1:
                status_text = "完成" if is_legitimate else "拒绝"
                print(f"✅ 监管方验证完成，转会已被{status_text}")
                return {
                    'success': True,
                    'tx_hash': tx_hash.hex(),
                    'tx_receipt': tx_receipt,
                    'is_completed': is_legitimate
                }
            else:
                return {
                    'success': False,
                    'error': f'Transaction failed with status: {tx_receipt.status}'
                }

        except Exception as e:
            print(f"区块链验证转会错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_transfer_details(self, transfer_id: int):
        """获取转会详细信息"""
        if not self.contract:
            return None

        try:
            transfer = self.contract.functions.getTransferDetails(transfer_id).call()
            status_names = ["Proposed", "Accepted", "Validated", "Completed", "Rejected"]

            return {
                'sellingClub': self._ensure_checksum_address(transfer[0]),
                'buyingClub': self._ensure_checksum_address(transfer[1]),
                'playerId': transfer[2],
                'transferFee': transfer[3],
                'status': status_names[transfer[4]] if transfer[4] < len(status_names) else "Unknown",
                'statusCode': transfer[4],
                'proposalTimestamp': transfer[5],
                'acceptanceTimestamp': transfer[6],
                'validationTimestamp': transfer[7],
                'isLegitimate': transfer[8],
                'lshIncomeHash': transfer[9],
                'lshExpenseHash': transfer[10]
            }
        except Exception as e:
            print(f"获取转会详细信息错误: {e}")
            return None

    def get_transfer(self, transfer_id: int):
        """获取转会信息（保持向后兼容）"""
        details = self.get_transfer_details(transfer_id)
        if details:
            return {
                'sellingClub': details['sellingClub'],
                'buyingClub': details['buyingClub'],
                'playerId': details['playerId'],
                'transferFee': details['transferFee'],
                'timestamp': details['proposalTimestamp'],
                'isValidated': details['statusCode'] >= 2,  # Validated or above
                'isCompleted': details['statusCode'] == 3,  # Completed
                'lshIncomeHash': details['lshIncomeHash'],
                'lshExpenseHash': details['lshExpenseHash']
            }
        return None

    def get_club(self, club_address: str):
        """获取俱乐部信息"""
        if not self.contract:
            return None

        club_address = self._ensure_checksum_address(club_address)
        if not club_address:
            return None

        try:
            club = self.contract.functions.getClub(club_address).call()
            return {
                'name': club[0],
                'country': club[1],
                'isRegistered': club[2]
            }
        except Exception as e:
            print(f"获取俱乐部信息错误: {e}")
            return None

    def get_transfer_count(self):
        """获取转会总数"""
        if not self.contract:
            return 0

        try:
            return self.contract.functions.transferCount().call()
        except Exception as e:
            print(f"获取转会总数错误: {e}")
            return 0

    def is_club_registered(self, club_address: str):
        """检查俱乐部是否已注册"""
        if not self.contract:
            return False

        club_address = self._ensure_checksum_address(club_address)
        if not club_address:
            return False

        try:
            return self.contract.functions.isClubRegistered(club_address).call()
        except Exception as e:
            print(f"检查俱乐部注册状态错误: {e}")
            return False

    def check_all_clubs_registered(self):
        """检查数据库中所有俱乐部是否都已在区块链上注册"""
        try:
            conn = sqlite3.connect('football_transfer_enhanced.db')
            cursor = conn.cursor()

            clubs = cursor.execute("SELECT club_id, name, wallet_address FROM clubs").fetchall()
            conn.close()

            unregistered_clubs = []

            for club_id, name, address in clubs:
                address = self._ensure_checksum_address(address)
                if not self.is_club_registered(address):
                    unregistered_clubs.append({'id': club_id, 'name': name, 'address': address})

            return {
                'all_registered': len(unregistered_clubs) == 0,
                'unregistered_clubs': unregistered_clubs,
                'total_clubs': len(clubs)
            }

        except Exception as e:
            print(f"检查俱乐部注册状态失败: {e}")
            return {
                'all_registered': False,
                'unregistered_clubs': [],
                'total_clubs': 0,
                'error': str(e)
            }

    def get_transfer_status_summary(self):
        """获取转会状态汇总"""
        if not self.contract:
            return None

        try:
            total_transfers = self.get_transfer_count()
            status_counts = {"Proposed": 0, "Accepted": 0, "Validated": 0, "Completed": 0, "Rejected": 0}

            for i in range(1, total_transfers + 1):
                details = self.get_transfer_details(i)
                if details:
                    status_counts[details['status']] += 1

            return {
                'total_transfers': total_transfers,
                'status_counts': status_counts
            }
        except Exception as e:
            print(f"获取转会状态汇总错误: {e}")
            return None