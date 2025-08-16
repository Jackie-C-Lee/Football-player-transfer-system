# -*- coding: utf-8 -*-
import uuid
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from services.lsh_service import LSHService
from services.blockchain_service import BlockchainService
import os
db_path = 'football_transfer_enhanced.db'
print(f"[DEBUG] 数据库路径: {os.path.abspath(db_path)}")
os.environ['FLASK_ENV'] = 'development'


class EnhancedTransferService:
    def __init__(self, db_path='football_transfer_enhanced.db'):
        self.db_path = db_path
        self.lsh_service = LSHService()
        try:
            self.blockchain_service = BlockchainService()
        except Exception as e:
            print(f"区块链连接失败: {e}")
            self.blockchain_service = None

    def get_connection(self):
        # """获取数据库连接"""
        # conn = sqlite3.connect(self.db_path)
        # conn.row_factory = sqlite3.Row
        # return conn
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(self.db_path)
            # 检验是否连接成功
            print("数据库连接成功")

            # 打印一些示例数据，观察是否连接成功
            cursor = conn.cursor()
            cursor.execute("SELECT sqlite_version();")
            data = cursor.fetchone()
            print(f"SQLite 版本: {data[0]}")

            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            print(f"数据库连接失败: {e}")
            return None

    def _ensure_checksum_address(self, address):
        """确保地址使用正确的EIP-55校验和格式"""
        if not address:
            return None

        try:
            from web3 import Web3
            if hasattr(Web3, 'to_checksum_address'):
                return Web3.to_checksum_address(address)
            elif hasattr(Web3, 'toChecksumAddress'):
                return Web3.toChecksumAddress(address)
            else:
                return address
        except Exception as e:
            print(f"地址格式化错误: {address}, 错误: {e}")
            return address

    def create_enhanced_club(self, name: str, country: str, league: str, city: str,
                             founded_year: int, stadium: str, wallet_address: str,
                             transfer_budget: float = 100000.0):
        """创建增强版俱乐部"""
        try:
            wallet_address = self._ensure_checksum_address(wallet_address)

            conn = self.get_connection()

            # 检查钱包地址是否已存在
            existing = conn.execute(
                "SELECT COUNT(*) as count FROM clubs WHERE wallet_address = ?",
                (wallet_address,)
            ).fetchone()

            if existing['count'] > 0:
                return {
                    'success': False,
                    'error': f'Wallet address {wallet_address} already exists'
                }

            club_id = f"club_{uuid.uuid4().hex[:8]}"

            conn.execute("""
                INSERT INTO clubs 
                (club_id, name, country, league, city, founded_year, stadium, 
                 wallet_address, balance, transfer_budget)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (club_id, name, country, league, city, founded_year, stadium,
                  wallet_address, 0.0, transfer_budget))

            conn.commit()
            conn.close()

            # 尝试在区块链上注册俱乐部
            blockchain_result = None
            if self.blockchain_service and self.blockchain_service.is_connected():
                try:
                    blockchain_result = self.blockchain_service.register_club(name, country, wallet_address)
                except Exception as e:
                    print(f"区块链注册失败: {e}")
                    blockchain_result = {'success': False, 'error': str(e)}

            return {
                'success': True,
                'club_id': club_id,
                'blockchain_result': blockchain_result
            }

        except Exception as e:
            print(f"创建俱乐部错误: {e}")
            return {'success': False, 'error': str(e)}

    def add_enhanced_player(self, name: str, english_name: str, position: str,
                            nationality: str, birth_place: str, birth_date: str,
                            height: float, weight: float, preferred_foot: str,
                            current_club_id: str, market_value: float,
                            jersey_number: int, contract_start: str, contract_end: str,
                            salary: float, major_achievements: str, club_career_history: str):
        """添加增强版球员"""
        try:
            conn = self.get_connection()

            # 检查球衣号码是否在同一俱乐部内重复
            existing = conn.execute("""
                SELECT COUNT(*) as count FROM players 
                WHERE current_club_id = ? AND jersey_number = ?
            """, (current_club_id, jersey_number)).fetchone()

            if existing['count'] > 0:
                return {
                    'success': False,
                    'error': f'Jersey number {jersey_number} already exists in this club'
                }

            player_id = f"player_{uuid.uuid4().hex[:8]}"

            conn.execute("""
                INSERT INTO players 
                (player_id, name, english_name, position, nationality, birth_place, 
                 birth_date, height, weight, preferred_foot, current_club_id, 
                 market_value, jersey_number, contract_start, contract_end, 
                 salary, major_achievements, club_career_history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (player_id, name, english_name, position, nationality, birth_place,
                  birth_date, height, weight, preferred_foot, current_club_id,
                  market_value, jersey_number, contract_start, contract_end,
                  salary, major_achievements, club_career_history))

            conn.commit()
            conn.close()

            return {'success': True, 'player_id': player_id}

        except Exception as e:
            print(f"添加球员错误: {e}")
            return {'success': False, 'error': str(e)}

    def add_coach(self, name: str, nationality: str, birth_place: str, birth_date: str,
                  current_club_id: str, coaching_style: str, major_achievements: str,
                  contract_start: str, contract_end: str, salary: float):
        """添加教练"""
        try:
            conn = self.get_connection()

            # 检查俱乐部是否已有主教练
            existing = conn.execute("""
                SELECT COUNT(*) as count FROM coaches WHERE current_club_id = ?
            """, (current_club_id,)).fetchone()

            if existing['count'] > 0:
                return {
                    'success': False,
                    'error': f'Club already has a head coach'
                }

            coach_id = f"coach_{uuid.uuid4().hex[:8]}"

            conn.execute("""
                INSERT INTO coaches 
                (coach_id, name, nationality, birth_place, birth_date, current_club_id,
                 coaching_style, major_achievements, contract_start, contract_end, salary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (coach_id, name, nationality, birth_place, birth_date, current_club_id,
                  coaching_style, major_achievements, contract_start, contract_end, salary))

            conn.commit()
            conn.close()

            return {'success': True, 'coach_id': coach_id}

        except Exception as e:
            print(f"添加教练错误: {e}")
            return {'success': False, 'error': str(e)}

    def create_transfer_offer(self, player_id: str, offering_club_id: str,
                              receiving_club_id: str, offer_amount: float,
                              additional_terms: str = "", expiry_days: int = 7):
        """创建转会报价"""
        try:
            conn = self.get_connection()

            # 检查球员是否可转会
            player = conn.execute("""
                SELECT * FROM players WHERE player_id = ? AND transfer_status = 1
            """, (player_id,)).fetchone()

            if not player:
                return {
                    'success': False,
                    'error': 'Player is not available for transfer'
                }

            # 检查是否是同一俱乐部
            if offering_club_id == receiving_club_id:
                return {
                    'success': False,
                    'error': 'Cannot make offer to own club'
                }

            # 检查俱乐部预算
            offering_club = conn.execute("""
                SELECT transfer_budget FROM clubs WHERE club_id = ?
            """, (offering_club_id,)).fetchone()

            if not offering_club or offering_club['transfer_budget'] < offer_amount:
                return {
                    'success': False,
                    'error': 'Insufficient transfer budget'
                }

            offer_id = f"offer_{uuid.uuid4().hex[:8]}"
            expiry_date = (datetime.now() + timedelta(days=expiry_days)).isoformat()

            conn.execute("""
                INSERT INTO transfer_offers 
                (offer_id, player_id, offering_club_id, receiving_club_id, 
                 offer_amount, additional_terms, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (offer_id, player_id, offering_club_id, receiving_club_id,
                  offer_amount, additional_terms, expiry_date))

            # 创建通知
            self._create_notification(
                receiving_club_id, 'offer_received', '收到转会报价',
                f'收到对球员的转会报价 €{offer_amount:,.2f}', offer_id
            )

            conn.commit()
            conn.close()

            return {'success': True, 'offer_id': offer_id}

        except Exception as e:
            print(f"创建转会报价错误: {e}")
            return {'success': False, 'error': str(e)}

    def respond_to_offer(self, offer_id: str, accept: bool, response_message: str = ""):
        """响应转会报价"""
        try:
            conn = self.get_connection()

            offer = conn.execute("""
                SELECT o.*, p.name as player_name
                FROM transfer_offers o
                JOIN players p ON o.player_id = p.player_id
                WHERE o.offer_id = ? AND o.offer_status = 'pending'
            """, (offer_id,)).fetchone()

            if not offer:
                return {
                    'success': False,
                    'error': 'Offer not found or already processed'
                }

            status = 'accepted' if accept else 'rejected'
            message_type = 'offer_accepted' if accept else 'offer_rejected'

            conn.execute("""
                UPDATE transfer_offers 
                SET offer_status = ?, response_date = CURRENT_TIMESTAMP
                WHERE offer_id = ?
            """, (status, offer_id))

            # 创建通知给报价方
            notification_message = f"您对球员 {offer['player_name']} 的报价已被{'接受' if accept else '拒绝'}"
            if response_message:
                notification_message += f": {response_message}"

            self._create_notification(
                offer['offering_club_id'], message_type,
                f"报价被{'接受' if accept else '拒绝'}",
                notification_message, offer_id
            )

            conn.commit()
            conn.close()

            return {
                'success': True,
                'status': status,
                'can_proceed_to_transfer': accept
            }

        except Exception as e:
            print(f"响应转会报价错误: {e}")
            return {'success': False, 'error': str(e)}

    def process_complete_transfer(self, offer_id: str, income_data: Dict, expense_data: Dict):
        """处理完整的转会交易"""
        try:
            conn = self.get_connection()

            # 获取报价信息
            offer = conn.execute("""
                SELECT o.*, p.name as player_name, p.market_value,
                       sc.name as selling_club_name, bc.name as buying_club_name,
                       sc.wallet_address as selling_address, bc.wallet_address as buying_address
                FROM transfer_offers o
                JOIN players p ON o.player_id = p.player_id
                JOIN clubs sc ON o.receiving_club_id = sc.club_id
                JOIN clubs bc ON o.offering_club_id = bc.club_id
                WHERE o.offer_id = ? AND o.offer_status = 'accepted'
            """, (offer_id,)).fetchone()

            if not offer:
                return {
                    'success': False,
                    'error': 'Accepted offer not found'
                }

            # 获取俱乐部转会历史进行LSH验证
            selling_history = self._get_club_transfer_history(offer['receiving_club_id'], 'selling')
            buying_history = self._get_club_transfer_history(offer['offering_club_id'], 'buying')

            # 准备LSH验证数据
            selling_data = self._prepare_lsh_data(selling_history, 'selling')
            buying_data = self._prepare_lsh_data(buying_history, 'buying')

            # 添加当前转会数据
            current_selling_data = {
                'transfer_fee': income_data['transfer_fee'],
                'player_market_value': offer['market_value'],
                'additional_costs': income_data.get('agent_commission', 0)
            }
            selling_data.append(current_selling_data)

            current_buying_data = {
                'transfer_fee': expense_data['transfer_fee'],
                'player_market_value': offer['market_value'],
                'additional_costs': expense_data.get('total_expense', expense_data['transfer_fee']) - expense_data[
                    'transfer_fee']
            }
            buying_data.append(current_buying_data)

            # 进行LSH验证
            validation_result = self.lsh_service.validate_transfer(selling_data, buying_data)

            if not validation_result['is_legitimate']:
                return {
                    'success': False,
                    'error': 'Transfer failed LSH validation - potential money laundering detected',
                    'lsh_result': validation_result
                }

            # 创建转会记录
            transfer_id = f"transfer_{uuid.uuid4().hex[:8]}"

            # 尝试区块链操作
            blockchain_result = None
            if self.blockchain_service and self.blockchain_service.is_connected():
                try:
                    blockchain_result = self.blockchain_service.propose_transfer(
                        self._ensure_checksum_address(offer['buying_address']),
                        int(offer['player_id'].replace('player_', ''), 16) % 1000000,
                        int(offer['offer_amount']),
                        validation_result['income_index'],
                        validation_result['expense_index']
                    )

                    if blockchain_result and blockchain_result['success']:
                        # 自动验证转会
                        transfer_count = self.blockchain_service.get_transfer_count()
                        validate_result = self.blockchain_service.validate_transfer(transfer_count, True)

                except Exception as e:
                    print(f"区块链操作失败: {e}")
                    blockchain_result = {'success': False, 'error': str(e)}

            # 保存转会记录
            conn.execute("""
                INSERT INTO transfers 
                (transfer_id, player_id, selling_club_id, buying_club_id, transfer_fee,
                 additional_costs, income_data, expense_data, lsh_income_hash, lsh_expense_hash,
                 is_validated, is_completed, transaction_hash, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (transfer_id, offer['player_id'], offer['receiving_club_id'],
                  offer['offering_club_id'], offer['offer_amount'],
                  expense_data.get('total_expense', 0) - expense_data['transfer_fee'],
                  json.dumps(income_data), json.dumps(expense_data),
                  validation_result['income_index'], validation_result['expense_index'],
                  1, 1, blockchain_result.get('tx_hash') if blockchain_result else None,
                  datetime.now().isoformat()))

            # 保存LSH验证记录
            validation_id = f"validation_{uuid.uuid4().hex[:8]}"
            conn.execute("""
                INSERT INTO lsh_validations 
                (validation_id, transfer_id, income_index, expense_index,
                 similarity_score, is_legitimate, validation_details, risk_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (validation_id, transfer_id, validation_result['income_index'],
                  validation_result['expense_index'], validation_result['similarity_score'],
                  1, validation_result['validation_details'], 'low'))

            # 更新球员信息
            conn.execute("""
                UPDATE players 
                SET current_club_id = ?, transfer_status = 0 
                WHERE player_id = ?
            """, (offer['offering_club_id'], offer['player_id']))

            # 更新俱乐部余额和预算
            selling_income = income_data.get('total_income', income_data['transfer_fee'])
            buying_expense = expense_data.get('total_expense', expense_data['transfer_fee'])

            conn.execute("""
                UPDATE clubs 
                SET balance = balance + ?, transfer_budget = transfer_budget + ?
                WHERE club_id = ?
            """, (selling_income, selling_income, offer['receiving_club_id']))

            conn.execute("""
                UPDATE clubs 
                SET balance = balance - ?, transfer_budget = transfer_budget - ?
                WHERE club_id = ?
            """, (buying_expense, buying_expense, offer['offering_club_id']))

            # 创建完成通知
            completion_message = f"球员 {offer['player_name']} 的转会已成功完成"
            for club_id in [offer['receiving_club_id'], offer['offering_club_id']]:
                self._create_notification(
                    club_id, 'transfer_completed', '转会完成',
                    completion_message, None, transfer_id
                )

            conn.commit()
            conn.close()

            return {
                'success': True,
                'transfer_id': transfer_id,
                'lsh_result': validation_result,
                'blockchain_result': blockchain_result
            }

        except Exception as e:
            print(f"处理转会交易错误: {e}")
            return {'success': False, 'error': str(e)}

    def _get_club_transfer_history(self, club_id: str, role: str):
        """获取俱乐部转会历史"""
        conn = self.get_connection()

        if role == 'selling':
            column = 'selling_club_id'
        else:
            column = 'buying_club_id'

        history = conn.execute(f"""
            SELECT transfer_fee, income_data, expense_data 
            FROM transfers 
            WHERE {column} = ? AND is_completed = 1
            ORDER BY created_at DESC LIMIT 10
        """, (club_id,)).fetchall()

        conn.close()
        return history

    def _prepare_lsh_data(self, history: List, role: str):
        """准备LSH验证数据"""
        data = []
        for record in history:
            try:
                if role == 'selling':
                    info = json.loads(record['income_data']) if record['income_data'] else {}
                    data.append({
                        'transfer_fee': record['transfer_fee'],
                        'player_market_value': record['transfer_fee'] * 1.1,
                        'additional_costs': info.get('agent_commission', record['transfer_fee'] * 0.05)
                    })
                else:
                    info = json.loads(record['expense_data']) if record['expense_data'] else {}
                    total_expense = info.get('total_expense', record['transfer_fee'] * 1.1)
                    data.append({
                        'transfer_fee': record['transfer_fee'],
                        'player_market_value': record['transfer_fee'] * 1.1,
                        'additional_costs': total_expense - record['transfer_fee']
                    })
            except:
                # 如果解析失败，使用默认值
                data.append({
                    'transfer_fee': record['transfer_fee'],
                    'player_market_value': record['transfer_fee'] * 1.1,
                    'additional_costs': record['transfer_fee'] * 0.05
                })
        return data

    def _create_notification(self, club_id: str, message_type: str, title: str,
                             message: str, offer_id: str = None, transfer_id: str = None):
        """创建通知"""
        conn = self.get_connection()
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"

        conn.execute("""
            INSERT INTO notifications 
            (notification_id, club_id, message_type, title, message, 
             related_offer_id, related_transfer_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (notification_id, club_id, message_type, title, message,
              offer_id, transfer_id))

        conn.commit()
        conn.close()

    def get_club_info(self, club_id: str):
        """获取俱乐部详细信息"""
        conn = self.get_connection()

        club = conn.execute("""
            SELECT c.*, 
                   COUNT(p.player_id) as player_count,
                   COUNT(CASE WHEN p.transfer_status = 1 THEN 1 END) as transferable_count
            FROM clubs c
            LEFT JOIN players p ON c.club_id = p.current_club_id
            WHERE c.club_id = ?
            GROUP BY c.club_id
        """, (club_id,)).fetchone()

        if not club:
            conn.close()
            return None

        # 获取教练信息
        coach = conn.execute("""
            SELECT * FROM coaches WHERE current_club_id = ?
        """, (club_id,)).fetchone()

        # 获取球员信息
        players = conn.execute("""
            SELECT * FROM players WHERE current_club_id = ? ORDER BY jersey_number
        """, (club_id,)).fetchall()

        conn.close()

        return {
            'club': dict(club),
            'coach': dict(coach) if coach else None,
            'players': [dict(player) for player in players]
        }

    def get_transfer_market_overview(self):
        """获取转会市场概览"""
        conn = self.get_connection()

        # 获取所有待处理报价
        offers = conn.execute("""
            SELECT o.*, p.name as player_name, p.position, p.market_value,
                   oc.name as offering_club_name, rc.name as receiving_club_name
            FROM transfer_offers o
            JOIN players p ON o.player_id = p.player_id
            JOIN clubs oc ON o.offering_club_id = oc.club_id
            JOIN clubs rc ON o.receiving_club_id = rc.club_id
            WHERE o.offer_status = 'pending'
            ORDER BY o.offer_date DESC
        """).fetchall()

        # 获取可转会球员
        transferable_players = conn.execute("""
            SELECT p.*, c.name as club_name
            FROM players p
            JOIN clubs c ON p.current_club_id = c.club_id
            WHERE p.transfer_status = 1
            ORDER BY p.market_value DESC
        """).fetchall()

        # 获取最近完成的转会
        recent_transfers = conn.execute("""
            SELECT t.*, p.name as player_name,
                   sc.name as selling_club_name, bc.name as buying_club_name
            FROM transfers t
            JOIN players p ON t.player_id = p.player_id
            JOIN clubs sc ON t.selling_club_id = sc.club_id
            JOIN clubs bc ON t.buying_club_id = bc.club_id
            WHERE t.is_completed = 1
            ORDER BY t.completed_at DESC LIMIT 10
        """).fetchall()

        conn.close()

        return {
            'pending_offers': [dict(offer) for offer in offers],
            'transferable_players': [dict(player) for player in transferable_players],
            'recent_transfers': [dict(transfer) for transfer in recent_transfers]
        }

    def get_club_notifications(self, club_id: str, unread_only: bool = True):
        """获取俱乐部通知"""
        conn = self.get_connection()

        query = """
            SELECT * FROM notifications 
            WHERE club_id = ?
        """
        params = [club_id]

        if unread_only:
            query += " AND is_read = 0"

        query += " ORDER BY created_at DESC"

        notifications = conn.execute(query, params).fetchall()
        conn.close()

        return [dict(notification) for notification in notifications]

    def mark_notification_read(self, notification_id: str):
        """标记通知为已读"""
        conn = self.get_connection()

        conn.execute("""
            UPDATE notifications SET is_read = 1 WHERE notification_id = ?
        """, (notification_id,))

        conn.commit()
        conn.close()

        return {'success': True}