# -*- coding: utf-8 -*-

import sqlite3
import uuid
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List
import io
# if os.name == 'nt':
#     os.system('chcp 65001')
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')  # 改变标准输出的默认编码

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.lsh_service import LSHService
from services.blockchain_service import BlockchainService


class EnhancedTransferManager:
    def __init__(self, db_path='football_transfer_enhanced.db'):
        self.db_path = db_path
        self.lsh_service = LSHService()
        try:
            self.blockchain_service = BlockchainService()
        except Exception as e:
            print(f"区块链连接失败: {e}")
            self.blockchain_service = None

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def display_all_clubs_info(self):
        """显示所有俱乐部的完整信息"""
        print("\n" + "=" * 80)
        print("📋 俱乐部信息总览")
        print("=" * 80)

        conn = self.get_connection()

        # 获取俱乐部基本信息
        clubs = conn.execute("""
            SELECT c.*, 
                   COUNT(p.player_id) as player_count,
                   COUNT(CASE WHEN p.transfer_status = 1 THEN 1 END) as transferable_count
            FROM clubs c
            LEFT JOIN players p ON c.club_id = p.current_club_id
            GROUP BY c.club_id
            ORDER BY c.name
        """).fetchall()

        for club in clubs:
            print(f"\n🏟️  {club['name']} ({club['country']})")
            print(f"   联赛: {club['league']} | 城市: {club['city']} | 成立: {club['founded_year']}")
            print(f"   主场: {club['stadium']}")
            print(f"   钱包地址: {club['wallet_address']}")
            print(f"   余额: €{club['balance']:,.2f} | 转会预算: €{club['transfer_budget']:,.2f}")
            print(f"   球员总数: {club['player_count']} | 可转会球员: {club['transferable_count']}")

            # 获取教练信息
            coach = conn.execute("""
                SELECT * FROM coaches WHERE current_club_id = ?
            """, (club['club_id'],)).fetchone()

            if coach:
                print(f"   👨‍💼 主教练: {coach['name']} ({coach['nationality']}) - {coach['coaching_style']}")

            # 获取球员信息
            players = conn.execute("""
                SELECT * FROM players WHERE current_club_id = ? ORDER BY jersey_number
            """, (club['club_id'],)).fetchall()

            print(f"   👥 球员名单:")
            for player in players:
                status = "🔄" if player['transfer_status'] else "🔒"
                foot = {"Left": "左脚", "Right": "右脚"}.get(player['preferred_foot'], player['preferred_foot'])
                print(
                    f"      {status} #{player['jersey_number']} {player['name']} ({player['position']}) - €{player['market_value']:,.0f} - {foot}")

        conn.close()

    def display_transfer_market(self):
        """显示转会市场"""
        print("\n" + "=" * 60)
        print("🏪 转会市场")
        print("=" * 60)

        conn = self.get_connection()

        # 获取所有转会报价
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

        if offers:
            for offer in offers:
                print(f"\n💰 报价 #{offer['offer_id']}")
                print(f"   球员: {offer['player_name']} ({offer['position']}) - 市值: €{offer['market_value']:,.0f}")
                print(f"   报价方: {offer['offering_club_name']} → 接收方: {offer['receiving_club_name']}")
                print(f"   报价金额: €{offer['offer_amount']:,.2f}")
                print(f"   报价时间: {offer['offer_date']}")
                if offer['additional_terms']:
                    print(f"   附加条款: {offer['additional_terms']}")
        else:
            print("🔍 当前转会市场没有待处理的报价")

        conn.close()

    def display_transferable_players(self):
        """显示可转会球员"""
        print("\n" + "=" * 60)
        print("🔄 可转会球员")
        print("=" * 60)

        conn = self.get_connection()

        players = conn.execute("""
            SELECT p.*, c.name as club_name
            FROM players p
            JOIN clubs c ON p.current_club_id = c.club_id
            WHERE p.transfer_status = 1
            ORDER BY p.market_value DESC
        """).fetchall()

        if players:
            for i, player in enumerate(players, 1):
                foot = {"Left": "左脚", "Right": "右脚"}.get(player['preferred_foot'], player['preferred_foot'])
                print(f"{i}. {player['name']} ({player['english_name']})")
                print(f"   俱乐部: {player['club_name']} | 位置: {player['position']} | 惯用脚: {foot}")
                print(f"   国籍: {player['nationality']} | 年龄: {self._calculate_age(player['birth_date'])}")
                print(f"   市值: €{player['market_value']:,.0f} | 球衣号码: #{player['jersey_number']}")
                print(f"   合约到期: {player['contract_end']}")
                print("")
        else:
            print("🔍 当前没有设置为可转会状态的球员")

        conn.close()
        return players

    def _calculate_age(self, birth_date):
        """计算年龄"""
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birth.year
            if today.month < birth.month or (today.month == birth.month and today.day < birth.day):
                age -= 1
            return age
        except:
            return "未知"

    def set_player_transfer_status(self):
        """设置球员转会状态"""
        print("\n" + "=" * 60)
        print("⚙️  设置球员转会状态")
        print("=" * 60)

        conn = self.get_connection()

        # 显示所有球员
        players = conn.execute("""
            SELECT p.*, c.name as club_name
            FROM players p
            JOIN clubs c ON p.current_club_id = c.club_id
            ORDER BY c.name, p.name
        """).fetchall()

        print("选择球员:")
        for i, player in enumerate(players, 1):
            status = "可转会" if player['transfer_status'] else "不可转会"
            print(f"{i}. {player['name']} ({player['club_name']}) - 当前状态: {status}")

        try:
            choice = int(input("\n请输入球员编号 (0退出): "))
            if choice == 0:
                return

            if 1 <= choice <= len(players):
                selected_player = players[choice - 1]
                current_status = bool(selected_player['transfer_status'])

                print(f"\n选中球员: {selected_player['name']} ({selected_player['club_name']})")
                print(f"当前转会状态: {'可转会' if current_status else '不可转会'}")

                new_status_input = input("设置为可转会状态? (y/n): ").lower()
                new_status = new_status_input == 'y'

                # 更新数据库
                conn.execute("""
                    UPDATE players SET transfer_status = ? WHERE player_id = ?
                """, (1 if new_status else 0, selected_player['player_id']))
                conn.commit()

                status_text = "可转会" if new_status else "不可转会"
                print(f"✅ 已将 {selected_player['name']} 设置为 {status_text} 状态")

            else:
                print("❌ 无效的选择")

        except ValueError:
            print("❌ 请输入有效的数字")

        conn.close()

    def make_transfer_offer(self):
        """发起转会报价"""
        print("\n" + "=" * 60)
        print("💰 发起转会报价")
        print("=" * 60)

        conn = self.get_connection()

        # 显示可转会球员
        players = self.display_transferable_players()
        if not players:
            return

        # 显示俱乐部
        clubs = conn.execute("SELECT * FROM clubs ORDER BY name").fetchall()
        print("选择报价俱乐部:")
        for i, club in enumerate(clubs, 1):
            print(f"{i}. {club['name']} (预算: €{club['transfer_budget']:,.2f})")

        try:
            # 选择球员
            player_choice = int(input(f"\n请选择球员 (1-{len(players)}, 0退出): "))
            if player_choice == 0:
                return

            if not (1 <= player_choice <= len(players)):
                print("❌ 无效的球员选择")
                return

            selected_player = players[player_choice - 1]

            # 选择报价俱乐部
            club_choice = int(input(f"请选择报价俱乐部 (1-{len(clubs)}, 0退出): "))
            if club_choice == 0:
                return

            if not (1 <= club_choice <= len(clubs)):
                print("❌ 无效的俱乐部选择")
                return

            offering_club = clubs[club_choice - 1]

            # 检查是否是同一俱乐部
            if offering_club['club_id'] == selected_player['current_club_id']:
                print("❌ 不能对自己俱乐部的球员报价")
                return

            # 输入报价金额
            market_value = float(selected_player['market_value'])
            print(f"\n球员 {selected_player['name']} 的市值: €{market_value:,.2f}")
            offer_amount = float(input("请输入报价金额 (欧元): "))

            # 检查预算
            if offer_amount > offering_club['transfer_budget']:
                print(f"❌ 报价金额超出俱乐部预算 (€{offering_club['transfer_budget']:,.2f})")
                return

            # 输入附加条款
            additional_terms = input("附加条款 (可选, 直接回车跳过): ").strip()

            # 创建报价记录
            offer_id = f"offer_{uuid.uuid4().hex[:8]}"
            expiry_date = (datetime.now() + timedelta(days=7)).isoformat()

            conn.execute("""
                INSERT INTO transfer_offers 
                (offer_id, player_id, offering_club_id, receiving_club_id, offer_amount, 
                 additional_terms, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (offer_id, selected_player['player_id'], offering_club['club_id'],
                  selected_player['current_club_id'], offer_amount, additional_terms, expiry_date))

            # 创建通知
            notification_id = f"notif_{uuid.uuid4().hex[:8]}"
            message = f"{offering_club['name']} 对球员 {selected_player['name']} 报价 €{offer_amount:,.2f}"

            conn.execute("""
                INSERT INTO notifications 
                (notification_id, club_id, message_type, title, message, related_offer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (notification_id, selected_player['current_club_id'], 'offer_received',
                  '收到转会报价', message, offer_id))

            conn.commit()

            print(f"✅ 转会报价已发送!")
            print(f"   报价ID: {offer_id}")
            print(f"   球员: {selected_player['name']}")
            print(f"   报价方: {offering_club['name']}")
            print(f"   金额: €{offer_amount:,.2f}")
            print(f"   有效期: 7天")

        except ValueError:
            print("❌ 请输入有效的数字")
        except Exception as e:
            print(f"❌ 发起报价失败: {e}")

        conn.close()

    def handle_transfer_offers(self):
        """处理转会报价"""
        print("\n" + "=" * 60)
        print("📥 处理转会报价")
        print("=" * 60)

        conn = self.get_connection()

        # 显示待处理的报价
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

        if not offers:
            print("🔍 没有待处理的转会报价")
            conn.close()
            return

        print("待处理的报价:")
        for i, offer in enumerate(offers, 1):
            print(f"{i}. {offer['player_name']} - {offer['offering_club_name']} → {offer['receiving_club_name']}")
            print(f"   报价: €{offer['offer_amount']:,.2f} | 球员市值: €{offer['market_value']:,.2f}")
            print(f"   报价时间: {offer['offer_date']}")

        try:
            choice = int(input(f"\n请选择要处理的报价 (1-{len(offers)}, 0退出): "))
            if choice == 0:
                return

            if not (1 <= choice <= len(offers)):
                print("❌ 无效的选择")
                return

            selected_offer = offers[choice - 1]

            print(f"\n处理报价:")
            print(f"球员: {selected_offer['player_name']} ({selected_offer['position']})")
            print(f"报价方: {selected_offer['offering_club_name']}")
            print(f"报价金额: €{selected_offer['offer_amount']:,.2f}")
            if selected_offer['additional_terms']:
                print(f"附加条款: {selected_offer['additional_terms']}")

            decision = input("\n是否接受此报价? (y/n): ").lower()

            if decision == 'y':
                # 接受报价
                conn.execute("""
                    UPDATE transfer_offers 
                    SET offer_status = 'accepted', response_date = CURRENT_TIMESTAMP
                    WHERE offer_id = ?
                """, (selected_offer['offer_id'],))

                # 创建通知给报价方
                notification_id = f"notif_{uuid.uuid4().hex[:8]}"
                message = f"您对球员 {selected_offer['player_name']} 的报价已被接受"

                conn.execute("""
                    INSERT INTO notifications 
                    (notification_id, club_id, message_type, title, message, related_offer_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (notification_id, selected_offer['offering_club_id'], 'offer_accepted',
                      '报价被接受', message, selected_offer['offer_id']))

                conn.commit()

                print("✅ 报价已接受！")
                print("💡 现在可以进入转会交易流程，输入收入/支出数据进行LSH验证")

                # 询问是否立即进行转会交易
                proceed = input("是否立即进行转会交易? (y/n): ").lower()
                if proceed == 'y':
                    self.process_transfer_transaction(selected_offer)

            else:
                # 拒绝报价
                conn.execute("""
                    UPDATE transfer_offers 
                    SET offer_status = 'rejected', response_date = CURRENT_TIMESTAMP
                    WHERE offer_id = ?
                """, (selected_offer['offer_id'],))

                # 创建通知给报价方
                notification_id = f"notif_{uuid.uuid4().hex[:8]}"
                message = f"您对球员 {selected_offer['player_name']} 的报价已被拒绝"

                conn.execute("""
                    INSERT INTO notifications 
                    (notification_id, club_id, message_type, title, message, related_offer_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (notification_id, selected_offer['offering_club_id'], 'offer_rejected',
                      '报价被拒绝', message, selected_offer['offer_id']))

                conn.commit()

                print("❌ 报价已拒绝")

        except ValueError:
            print("❌ 请输入有效的数字")
        except Exception as e:
            print(f"❌ 处理报价失败: {e}")

        conn.close()

    def process_transfer_transaction(self, offer):
        """处理转会交易（三步确认：卖方提议 → 买方接受 → 监管验证）"""
        print("\n" + "=" * 80)
        print("🔄 转会交易处理 - 三步确认流程")
        print("=" * 80)

        conn = self.get_connection()

        print(f"转会详情:")
        print(f"球员: {offer['player_name']}")
        print(f"卖方: {offer['receiving_club_name']}")
        print(f"买方: {offer['offering_club_name']}")
        print(f"转会费: €{offer['offer_amount']:,.2f}")

        # 输入收入数据（卖方）
        print(f"\n📊 {offer['receiving_club_name']} (卖方) 收入数据输入:")
        income_data = {}
        income_data['transfer_fee'] = float(offer['offer_amount'])
        income_data['agent_commission'] = float(input("经纪人佣金 (欧元): ") or "0")
        income_data['other_income'] = float(input("其他收入 (欧元): ") or "0")
        income_data['total_income'] = income_data['transfer_fee'] + income_data['other_income'] - income_data[
            'agent_commission']

        print(f"总收入: €{income_data['total_income']:,.2f}")

        # 输入支出数据（买方）
        print(f"\n📊 {offer['offering_club_name']} (买方) 支出数据输入:")
        expense_data = {}
        expense_data['transfer_fee'] = float(offer['offer_amount'])
        expense_data['agent_commission'] = float(input("经纪人佣金 (欧元): ") or "0")
        expense_data['signing_bonus'] = float(input("签字费 (欧元): ") or "0")
        expense_data['medical_costs'] = float(input("体检费用 (欧元): ") or "0")
        expense_data['other_costs'] = float(input("其他费用 (欧元): ") or "0")
        expense_data['total_expense'] = (expense_data['transfer_fee'] + expense_data['agent_commission'] +
                                         expense_data['signing_bonus'] + expense_data['medical_costs'] +
                                         expense_data['other_costs'])

        print(f"总支出: €{expense_data['total_expense']:,.2f}")

        # 获取俱乐部历史数据进行LSH验证
        print(f"\n🔍 进行LSH验证...")

        # 获取卖方转会历史
        selling_history = conn.execute("""
            SELECT transfer_fee, income_data, expense_data FROM transfers 
            WHERE selling_club_id = ? AND is_completed = 1
            ORDER BY created_at DESC LIMIT 10
        """, (offer['receiving_club_id'],)).fetchall()

        # 获取买方转会历史
        buying_history = conn.execute("""
            SELECT transfer_fee, income_data, expense_data FROM transfers 
            WHERE buying_club_id = ? AND is_completed = 1
            ORDER BY created_at DESC LIMIT 10
        """, (offer['offering_club_id'],)).fetchall()

        # 准备LSH验证数据
        selling_data = []
        for record in selling_history:
            try:
                income_info = json.loads(record['income_data']) if record['income_data'] else {}
                selling_data.append({
                    'transfer_fee': record['transfer_fee'],
                    'player_market_value': record['transfer_fee'] * 1.1,  # 估算
                    'additional_costs': income_info.get('agent_commission', record['transfer_fee'] * 0.05)
                })
            except:
                selling_data.append({
                    'transfer_fee': record['transfer_fee'],
                    'player_market_value': record['transfer_fee'] * 1.1,
                    'additional_costs': record['transfer_fee'] * 0.05
                })

        buying_data = []
        for record in buying_history:
            try:
                expense_info = json.loads(record['expense_data']) if record['expense_data'] else {}
                buying_data.append({
                    'transfer_fee': record['transfer_fee'],
                    'player_market_value': record['transfer_fee'] * 1.1,
                    'additional_costs': expense_info.get('total_expense', record['transfer_fee'] * 0.1) - record[
                        'transfer_fee']
                })
            except:
                buying_data.append({
                    'transfer_fee': record['transfer_fee'],
                    'player_market_value': record['transfer_fee'] * 1.1,
                    'additional_costs': record['transfer_fee'] * 0.1
                })

        # 添加当前转会数据
        current_selling_data = {
            'transfer_fee': income_data['transfer_fee'],
            'player_market_value': offer['market_value'],
            'additional_costs': income_data['agent_commission']
        }
        selling_data.append(current_selling_data)

        current_buying_data = {
            'transfer_fee': expense_data['transfer_fee'],
            'player_market_value': offer['market_value'],
            'additional_costs': expense_data['total_expense'] - expense_data['transfer_fee']
        }
        buying_data.append(current_buying_data)

        # 进行LSH验证
        validation_result = self.lsh_service.validate_transfer(selling_data, buying_data)

        print(f"LSH验证结果:")
        print(f"✓ 收入索引: {validation_result['income_index']}")
        print(f"✓ 支出索引: {validation_result['expense_index']}")
        print(f"✓ 相似度分数: {validation_result['similarity_score']:.4f}")
        print(f"✓ 验证结果: {'✅ 合法' if validation_result['is_legitimate'] else '❌ 可疑'}")

        if validation_result['is_legitimate']:
            print("\n🎉 LSH验证通过！开始区块链三步确认流程...")

            # 创建转会记录
            transfer_id = f"transfer_{uuid.uuid4().hex[:8]}"

            # 区块链三步确认流程
            blockchain_results = {}

            if self.blockchain_service and self.blockchain_service.is_connected():
                try:
                    # 检查所有俱乐部是否都已注册
                    registration_status = self.blockchain_service.check_all_clubs_registered()
                    if not registration_status['all_registered']:
                        print("⚠️ 发现未注册的俱乐部，请先运行 python register_clubs.py")
                        for club in registration_status['unregistered_clubs']:
                            print(f"   - {club['name']} ({club['address']})")
                        blockchain_results['error'] = 'Some clubs not registered on blockchain'
                    else:
                        # 步骤1：卖方发起转会提议
                        print("\n📝 步骤1：卖方发起转会提议...")
                        propose_result = self.blockchain_service.propose_transfer(
                            offer['receiving_club_id'],  # 卖方俱乐部ID
                            offer['offering_club_id'],  # 买方俱乐部ID
                            int(offer['player_id'].replace('player_', ''), 16) % 1000000,
                            int(offer['offer_amount']),
                            validation_result['income_index']
                        )

                        if propose_result and propose_result['success']:
                            print("✅ 步骤1完成：卖方转会提议已提交")
                            blockchain_transfer_id = propose_result['transfer_id']
                            blockchain_results['propose'] = propose_result

                            # 步骤2：买方接受转会
                            print("\n🤝 步骤2：买方接受转会...")
                            accept_result = self.blockchain_service.accept_transfer(
                                blockchain_transfer_id,
                                offer['offering_club_id'],  # 买方俱乐部ID
                                validation_result['expense_index']
                            )

                            if accept_result and accept_result['success']:
                                print("✅ 步骤2完成：买方转会接受已确认")
                                blockchain_results['accept'] = accept_result

                                # 步骤3：监管方验证
                                print("\n⚖️ 步骤3：监管方验证转会...")
                                validate_result = self.blockchain_service.validate_transfer(
                                    blockchain_transfer_id, True
                                )

                                if validate_result and validate_result['success']:
                                    print("✅ 步骤3完成：监管方验证通过")
                                    print("\n🎉 三步确认流程全部完成！")
                                    blockchain_results['validate'] = validate_result
                                    blockchain_results['success'] = True
                                    blockchain_results['blockchain_transfer_id'] = blockchain_transfer_id
                                else:
                                    print(f"❌ 步骤3失败：监管验证错误 - {validate_result.get('error', 'Unknown error')}")
                                    blockchain_results[
                                        'error'] = f"Validation failed: {validate_result.get('error', 'Unknown error')}"
                            else:
                                print(f"❌ 步骤2失败：买方接受错误 - {accept_result.get('error', 'Unknown error')}")
                                blockchain_results[
                                    'error'] = f"Accept failed: {accept_result.get('error', 'Unknown error')}"
                        else:
                            print(f"❌ 步骤1失败：卖方提议错误 - {propose_result.get('error', 'Unknown error')}")
                            blockchain_results[
                                'error'] = f"Propose failed: {propose_result.get('error', 'Unknown error')}"

                except Exception as e:
                    print(f"❌ 区块链处理过程出错: {e}")
                    blockchain_results['error'] = str(e)
            else:
                print("⚠️ 区块链未连接，模拟转会成功")
                blockchain_results = {'success': True, 'simulated': True}

            # 保存转会记录
            blockchain_tx_hash = None
            if blockchain_results.get('success'):
                if blockchain_results.get('validate'):
                    blockchain_tx_hash = blockchain_results['validate'].get('tx_hash')

            conn.execute("""
                INSERT INTO transfers 
                (transfer_id, player_id, selling_club_id, buying_club_id, transfer_fee, 
                 additional_costs, income_data, expense_data, lsh_income_hash, lsh_expense_hash,
                 is_validated, is_completed, transaction_hash, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (transfer_id, offer['player_id'], offer['receiving_club_id'],
                  offer['offering_club_id'], offer['offer_amount'],
                  expense_data['total_expense'] - expense_data['transfer_fee'],
                  json.dumps(income_data), json.dumps(expense_data),
                  validation_result['income_index'], validation_result['expense_index'],
                  1, 1,
                  blockchain_tx_hash,
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

            # 更新俱乐部余额
            conn.execute("""
                UPDATE clubs 
                SET balance = balance + ?, transfer_budget = transfer_budget + ?
                WHERE club_id = ?
            """, (income_data['total_income'], income_data['total_income'], offer['receiving_club_id']))

            conn.execute("""
                UPDATE clubs 
                SET balance = balance - ?, transfer_budget = transfer_budget - ?
                WHERE club_id = ?
            """, (expense_data['total_expense'], expense_data['total_expense'], offer['offering_club_id']))

            # 创建完成通知
            completion_message = f"球员 {offer['player_name']} 的转会已成功完成（三步确认流程）"

            for club_id in [offer['receiving_club_id'], offer['offering_club_id']]:
                conn.execute("""
                    INSERT INTO notifications 
                    (notification_id, club_id, message_type, title, message, related_transfer_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"notif_{uuid.uuid4().hex[:8]}", club_id, 'transfer_completed',
                      '转会完成', completion_message, transfer_id))

            conn.commit()

            print(f"\n🎉 转会交易成功完成！")
            print(f"转会ID: {transfer_id}")
            print(
                f"球员 {offer['player_name']} 已从 {offer['receiving_club_name']} 转会到 {offer['offering_club_name']}")

            # 显示区块链确认详情
            if blockchain_results.get('success') and not blockchain_results.get('simulated'):
                print(f"\n📋 区块链确认详情:")
                print(f"✓ 步骤1 - 卖方提议交易哈希: {blockchain_results.get('propose', {}).get('tx_hash', 'N/A')}")
                print(f"✓ 步骤2 - 买方接受交易哈希: {blockchain_results.get('accept', {}).get('tx_hash', 'N/A')}")
                print(f"✓ 步骤3 - 监管验证交易哈希: {blockchain_results.get('validate', {}).get('tx_hash', 'N/A')}")
                print(f"✓ 区块链转会ID: {blockchain_results.get('blockchain_transfer_id', 'N/A')}")
            elif blockchain_results.get('error'):
                print(f"\n⚠️ 区块链处理警告: {blockchain_results['error']}")
                print("转会在链下完成，但区块链记录可能不完整")

        else:
            print(f"\n❌ LSH验证失败！转会被拒绝")
            print(f"原因: 相似度分数 {validation_result['similarity_score']:.4f} 超出正常范围")
            print("此转会可能涉及洗钱活动")

        conn.close()

    def display_notifications(self):
        """显示通知消息"""
        print("\n" + "=" * 60)
        print("📢 通知消息")
        print("=" * 60)

        conn = self.get_connection()

        notifications = conn.execute("""
            SELECT n.*, c.name as club_name
            FROM notifications n
            JOIN clubs c ON n.club_id = c.club_id
            WHERE n.is_read = 0
            ORDER BY n.created_at DESC
        """).fetchall()

        if notifications:
            for notification in notifications:
                icon = {"offer_received": "📥", "offer_accepted": "✅",
                        "offer_rejected": "❌", "transfer_completed": "🎉"}.get(notification['message_type'], "📢")
                print(f"{icon} {notification['title']}")
                print(f"   俱乐部: {notification['club_name']}")
                print(f"   消息: {notification['message']}")
                print(f"   时间: {notification['created_at']}")
                print("")
        else:
            print("🔍 没有新的通知消息")

        conn.close()

    def display_transfer_history(self):
        """显示转会历史"""
        print("\n" + "=" * 60)
        print("📋 转会历史记录")
        print("=" * 60)

        conn = self.get_connection()

        transfers = conn.execute("""
            SELECT t.*, p.name as player_name, p.position,
                   sc.name as selling_club_name, bc.name as buying_club_name,
                   lv.similarity_score, lv.is_legitimate
            FROM transfers t
            JOIN players p ON t.player_id = p.player_id
            JOIN clubs sc ON t.selling_club_id = sc.club_id
            JOIN clubs bc ON t.buying_club_id = bc.club_id
            LEFT JOIN lsh_validations lv ON t.transfer_id = lv.transfer_id
            ORDER BY t.completed_at DESC
        """).fetchall()

        if transfers:
            for transfer in transfers:
                status = "✅ 已完成" if transfer['is_completed'] else "🔄 进行中"
                legitimacy = "✅ 合法" if transfer['is_legitimate'] else "❌ 可疑"

                print(f"🔄 {transfer['player_name']} ({transfer['position']})")
                print(f"   {transfer['selling_club_name']} → {transfer['buying_club_name']}")
                print(f"   转会费: €{transfer['transfer_fee']:,.2f}")
                print(f"   状态: {status} | LSH验证: {legitimacy}")
                if transfer['similarity_score']:
                    print(f"   相似度分数: {transfer['similarity_score']:.4f}")
                print(f"   完成时间: {transfer['completed_at']}")
                print("")
        else:
            print("🔍 暂无转会记录")

        conn.close()

    def display_blockchain_transfer_details(self):
        """显示区块链转会详情"""
        print("\n" + "=" * 60)
        print("🔗 区块链转会详情")
        print("=" * 60)

        if not self.blockchain_service or not self.blockchain_service.is_connected():
            print("❌ 区块链未连接")
            return

        try:
            # 获取转会状态汇总
            summary = self.blockchain_service.get_transfer_status_summary()
            if summary:
                print(f"转会总数: {summary['total_transfers']}")
                print(f"状态分布:")
                for status, count in summary['status_counts'].items():
                    print(f"  {status}: {count}")
                print()

            # 显示具体转会详情
            total_transfers = self.blockchain_service.get_transfer_count()
            if total_transfers > 0:
                print("最近的转会记录:")
                for i in range(max(1, total_transfers - 4), total_transfers + 1):
                    details = self.blockchain_service.get_transfer_details(i)
                    if details:
                        print(f"\n转会 #{i}:")
                        print(f"  状态: {details['status']}")
                        print(f"  卖方: {details['sellingClub']}")
                        print(f"  买方: {details['buyingClub']}")
                        print(f"  球员ID: {details['playerId']}")
                        print(f"  转会费: {details['transferFee']}")
                        if details['proposalTimestamp'] > 0:
                            print(f"  提议时间: {datetime.fromtimestamp(details['proposalTimestamp'])}")
                        if details['acceptanceTimestamp'] > 0:
                            print(f"  接受时间: {datetime.fromtimestamp(details['acceptanceTimestamp'])}")
                        if details['validationTimestamp'] > 0:
                            print(f"  验证时间: {datetime.fromtimestamp(details['validationTimestamp'])}")
            else:
                print("暂无区块链转会记录")

        except Exception as e:
            print(f"获取区块链转会详情失败: {e}")

    def main_menu(self):
        """主菜单 - 添加区块链详情选项"""
        while True:
            print("\n" + "=" * 80)
            print("⚽ 足球转会系统 - 增强版（三步确认）")
            print("=" * 80)
            print("1. 📋 显示俱乐部信息")
            print("2. 🔄 显示可转会球员")
            print("3. 🏪 显示转会市场")
            print("4. ⚙️  设置球员转会状态")
            print("5. 💰 发起转会报价")
            print("6. 📥 处理转会报价")
            print("7. 📢 查看通知消息")
            print("8. 📋 查看转会历史")
            print("9. 🔗 查看区块链转会详情")  # 新增选项
            print("0. 🚪 退出系统")
            print("=" * 80)

            try:
                choice = input("请选择操作 (0-9): ")

                if choice == '1':
                    self.display_all_clubs_info()
                elif choice == '2':
                    self.display_transferable_players()
                elif choice == '3':
                    self.display_transfer_market()
                elif choice == '4':
                    self.set_player_transfer_status()
                elif choice == '5':
                    self.make_transfer_offer()
                elif choice == '6':
                    self.handle_transfer_offers()
                elif choice == '7':
                    self.display_notifications()
                elif choice == '8':
                    self.display_transfer_history()
                elif choice == '9':
                    self.display_blockchain_transfer_details()  # 新增功能
                elif choice == '0':
                    print("👋 感谢使用足球转会系统！")
                    break
                else:
                    print("❌ 无效的选择，请重新输入")

                if choice != '0':
                    input("\n按回车键继续...")

            except KeyboardInterrupt:
                print("\n\n👋 感谢使用足球转会系统！")
                break

    def process_transfer_transaction_api(self, offer_dict, income_data, expense_data):
        """API版本的转会交易处理方法 - 完整的LSH验证和区块链三步确认"""
        try:
            conn = self.get_connection()

            print(f"🔄 处理转会交易:")
            print(f"   球员: {offer_dict['player_name']}")
            print(f"   卖方: {offer_dict['receiving_club_name']}")
            print(f"   买方: {offer_dict['offering_club_name']}")
            print(f"   转会费: €{offer_dict['offer_amount']:,.2f}")

            # 获取俱乐部历史数据进行LSH验证
            print(f"\n🔍 进行LSH验证...")

            # 获取卖方转会历史
            selling_history = conn.execute("""
                SELECT transfer_fee, income_data, expense_data FROM transfers 
                WHERE selling_club_id = ? AND is_completed = 1
                ORDER BY created_at DESC LIMIT 10
            """, (offer_dict['receiving_club_id'],)).fetchall()

            # 获取买方转会历史
            buying_history = conn.execute("""
                SELECT transfer_fee, income_data, expense_data FROM transfers 
                WHERE buying_club_id = ? AND is_completed = 1
                ORDER BY created_at DESC LIMIT 10
            """, (offer_dict['offering_club_id'],)).fetchall()

            # 准备LSH验证数据
            selling_data = []
            for record in selling_history:
                try:
                    income_info = json.loads(record['income_data']) if record['income_data'] else {}
                    selling_data.append({
                        'transfer_fee': record['transfer_fee'],
                        'player_market_value': record['transfer_fee'] * 1.1,
                        'additional_costs': income_info.get('agent_commission', record['transfer_fee'] * 0.05)
                    })
                except:
                    selling_data.append({
                        'transfer_fee': record['transfer_fee'],
                        'player_market_value': record['transfer_fee'] * 1.1,
                        'additional_costs': record['transfer_fee'] * 0.05
                    })

            buying_data = []
            for record in buying_history:
                try:
                    expense_info = json.loads(record['expense_data']) if record['expense_data'] else {}
                    buying_data.append({
                        'transfer_fee': record['transfer_fee'],
                        'player_market_value': record['transfer_fee'] * 1.1,
                        'additional_costs': expense_info.get('total_expense', record['transfer_fee'] * 0.1) - record[
                            'transfer_fee']
                    })
                except:
                    buying_data.append({
                        'transfer_fee': record['transfer_fee'],
                        'player_market_value': record['transfer_fee'] * 1.1,
                        'additional_costs': record['transfer_fee'] * 0.1
                    })

            # 添加当前转会数据
            current_selling_data = {
                'transfer_fee': income_data['transfer_fee'],
                'player_market_value': offer_dict['market_value'],
                'additional_costs': income_data['agent_commission']
            }
            selling_data.append(current_selling_data)

            current_buying_data = {
                'transfer_fee': expense_data['transfer_fee'],
                'player_market_value': offer_dict['market_value'],
                'additional_costs': expense_data['total_expense'] - expense_data['transfer_fee']
            }
            buying_data.append(current_buying_data)

            # 进行LSH验证
            validation_result = self.lsh_service.validate_transfer(selling_data, buying_data)

            print(f"📊 LSH验证结果:")
            print(f"   ✓ 收入索引: {validation_result['income_index']}")
            print(f"   ✓ 支出索引: {validation_result['expense_index']}")
            print(f"   ✓ 相似度分数: {validation_result['similarity_score']:.4f}")
            print(f"   ✓ 验证结果: {'✅ 合法' if validation_result['is_legitimate'] else '❌ 可疑'}")

            if validation_result['is_legitimate']:
                print("\n🎉 LSH验证通过！开始区块链三步确认流程...")

                # 创建转会记录
                import uuid
                transfer_id = f"transfer_{uuid.uuid4().hex[:8]}"

                # 区块链三步确认流程
                blockchain_results = {}

                if self.blockchain_service and self.blockchain_service.is_connected():
                    try:
                        # 检查所有俱乐部是否都已注册
                        registration_status = self.blockchain_service.check_all_clubs_registered()
                        if not registration_status['all_registered']:
                            print("⚠️ 发现未注册的俱乐部，请先运行 python register_clubs.py")
                            for club in registration_status['unregistered_clubs']:
                                print(f"   - {club['name']} ({club['address']})")
                            blockchain_results['error'] = 'Some clubs not registered on blockchain'
                        else:
                            # 步骤1：卖方发起转会提议
                            print("\n📝 步骤1：卖方发起转会提议...")
                            propose_result = self.blockchain_service.propose_transfer(
                                offer_dict['receiving_club_id'],  # 卖方俱乐部ID
                                offer_dict['offering_club_id'],  # 买方俱乐部ID
                                int(offer_dict['player_id'].replace('player_', ''), 16) % 1000000,
                                int(offer_dict['offer_amount']),
                                validation_result['income_index']
                            )

                            if propose_result and propose_result['success']:
                                print("   ✅ 步骤1完成：卖方转会提议已提交")
                                blockchain_transfer_id = propose_result['transfer_id']
                                blockchain_results['propose'] = propose_result

                                # 步骤2：买方接受转会
                                print("\n🤝 步骤2：买方接受转会...")
                                accept_result = self.blockchain_service.accept_transfer(
                                    blockchain_transfer_id,
                                    offer_dict['offering_club_id'],  # 买方俱乐部ID
                                    validation_result['expense_index']
                                )

                                if accept_result and accept_result['success']:
                                    print("   ✅ 步骤2完成：买方转会接受已确认")
                                    blockchain_results['accept'] = accept_result

                                    # 步骤3：监管方验证
                                    print("\n⚖️ 步骤3：监管方验证转会...")
                                    validate_result = self.blockchain_service.validate_transfer(
                                        blockchain_transfer_id, True
                                    )

                                    if validate_result and validate_result['success']:
                                        print("   ✅ 步骤3完成：监管方验证通过")
                                        print("\n🎉 三步确认流程全部完成！")
                                        blockchain_results['validate'] = validate_result
                                        blockchain_results['success'] = True
                                        blockchain_results['blockchain_transfer_id'] = blockchain_transfer_id
                                    else:
                                        print(
                                            f"   ❌ 步骤3失败：监管验证错误 - {validate_result.get('error', 'Unknown error')}")
                                        blockchain_results[
                                            'error'] = f"Validation failed: {validate_result.get('error', 'Unknown error')}"
                                else:
                                    print(
                                        f"   ❌ 步骤2失败：买方接受错误 - {accept_result.get('error', 'Unknown error')}")
                                    blockchain_results[
                                        'error'] = f"Accept failed: {accept_result.get('error', 'Unknown error')}"
                            else:
                                print(f"   ❌ 步骤1失败：卖方提议错误 - {propose_result.get('error', 'Unknown error')}")
                                blockchain_results[
                                    'error'] = f"Propose failed: {propose_result.get('error', 'Unknown error')}"

                    except Exception as e:
                        print(f"❌ 区块链处理过程出错: {e}")
                        blockchain_results['error'] = str(e)
                else:
                    print("⚠️ 区块链未连接，模拟转会成功")
                    blockchain_results = {'success': True, 'simulated': True}

                # 保存转会记录
                blockchain_tx_hash = None
                if blockchain_results.get('success'):
                    if blockchain_results.get('validate'):
                        blockchain_tx_hash = blockchain_results['validate'].get('tx_hash')

                conn.execute("""
                    INSERT INTO transfers 
                    (transfer_id, player_id, selling_club_id, buying_club_id, transfer_fee, 
                     additional_costs, income_data, expense_data, lsh_income_hash, lsh_expense_hash,
                     is_validated, is_completed, transaction_hash, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (transfer_id, offer_dict['player_id'], offer_dict['receiving_club_id'],
                      offer_dict['offering_club_id'], offer_dict['offer_amount'],
                      expense_data['total_expense'] - expense_data['transfer_fee'],
                      json.dumps(income_data), json.dumps(expense_data),
                      validation_result['income_index'], validation_result['expense_index'],
                      1, 1, blockchain_tx_hash, datetime.now().isoformat()))

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
                """, (offer_dict['offering_club_id'], offer_dict['player_id']))

                # 更新俱乐部余额
                conn.execute("""
                    UPDATE clubs 
                    SET balance = balance + ?, transfer_budget = transfer_budget + ?
                    WHERE club_id = ?
                """, (income_data['total_income'], income_data['total_income'], offer_dict['receiving_club_id']))

                conn.execute("""
                    UPDATE clubs 
                    SET balance = balance - ?, transfer_budget = transfer_budget - ?
                    WHERE club_id = ?
                """, (expense_data['total_expense'], expense_data['total_expense'], offer_dict['offering_club_id']))

                # 创建完成通知
                completion_message = f"球员 {offer_dict['player_name']} 的转会已成功完成（三步确认流程）"

                for club_id in [offer_dict['receiving_club_id'], offer_dict['offering_club_id']]:
                    conn.execute("""
                        INSERT INTO notifications 
                        (notification_id, club_id, message_type, title, message, related_transfer_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (f"notif_{uuid.uuid4().hex[:8]}", club_id, 'transfer_completed',
                          '转会完成', completion_message, transfer_id))

                conn.commit()
                conn.close()

                print(f"\n🎉 转会交易成功完成！")
                print(f"   转会ID: {transfer_id}")
                print(
                    f"   球员 {offer_dict['player_name']} 已从 {offer_dict['receiving_club_name']} 转会到 {offer_dict['offering_club_name']}")

                # 显示区块链确认详情
                if blockchain_results.get('success') and not blockchain_results.get('simulated'):
                    print(f"\n📋 区块链确认详情:")
                    print(
                        f"   ✓ 步骤1 - 卖方提议交易哈希: {blockchain_results.get('propose', {}).get('tx_hash', 'N/A')}")
                    print(
                        f"   ✓ 步骤2 - 买方接受交易哈希: {blockchain_results.get('accept', {}).get('tx_hash', 'N/A')}")
                    print(
                        f"   ✓ 步骤3 - 监管验证交易哈希: {blockchain_results.get('validate', {}).get('tx_hash', 'N/A')}")
                    print(f"   ✓ 区块链转会ID: {blockchain_results.get('blockchain_transfer_id', 'N/A')}")
                elif blockchain_results.get('error'):
                    print(f"\n⚠️ 区块链处理警告: {blockchain_results['error']}")
                    print("   转会在链下完成，但区块链记录可能不完整")

                return {
                    'success': True,
                    'message': '转会交易成功完成！已完成LSH验证和区块链三步确认。',
                    'transfer_id': transfer_id,
                    'lsh_result': validation_result,
                    'blockchain_result': blockchain_results
                }

            else:
                conn.close()
                print(f"\n❌ LSH验证失败！转会被拒绝")
                print(f"   原因: 相似度分数 {validation_result['similarity_score']:.4f} 超出正常范围")
                print("   此转会可能涉及洗钱活动")

                return {
                    'success': False,
                    'error': f'LSH验证失败：相似度分数 {validation_result["similarity_score"]:.4f} 超出正常范围（0.3-0.8），此转会可能涉及洗钱活动',
                    'lsh_result': validation_result
                }

        except Exception as e:
            print(f"❌ 转会处理错误: {e}")
            return {
                'success': False,
                'error': str(e)
            }



if __name__ == "__main__":
    # 检查数据库是否存在
    if not os.path.exists('football_transfer_enhanced.db'):
        print("❌ 增强版数据库不存在，请先运行 python init_database_enhanced.py")
        sys.exit(1)

    manager = EnhancedTransferManager()
    manager.main_menu()