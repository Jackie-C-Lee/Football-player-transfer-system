# -*- coding: utf-8 -*-
import http.server
import socketserver
import json
import sqlite3
import os
import sys
from urllib.parse import urlparse, parse_qs
import webbrowser
from datetime import datetime
import uuid
from datetime import timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入现有模块
from enhanced_transfer_manager import EnhancedTransferManager


class CompleteTransferHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web", **kwargs)

    def get_transfer_manager(self):
        """获取转会管理器实例"""
        if not hasattr(self, '_transfer_manager'):
            self._transfer_manager = EnhancedTransferManager()
        return self._transfer_manager

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self.serve_main_page()
        elif parsed_path.path == '/api/clubs':
            self.serve_clubs_data()
        elif parsed_path.path == '/api/players':
            self.serve_players_data()
        elif parsed_path.path == '/api/offers':
            self.serve_offers_data()
        elif parsed_path.path == '/api/history':
            self.serve_history_data()
        elif parsed_path.path == '/api/notifications':
            self.serve_notifications_data()
        elif parsed_path.path == '/api/blockchain':
            self.serve_blockchain_data()
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}

        if parsed_path.path == '/api/set_status':
            self.handle_set_status(data)
        elif parsed_path.path == '/api/make_offer':
            self.handle_make_offer(data)
        elif parsed_path.path == '/api/handle_offer':
            self.handle_offer_response(data)
        elif parsed_path.path == '/api/process_transfer':
            self.handle_complete_transfer(data)
        else:
            self.send_error(404)

    def serve_main_page(self):
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>⚽ 足球转会系统 - 完整版</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            padding: 20px; 
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin-bottom: 20px; 
            text-align: center; 
        }
        .nav { 
            display: flex; 
            gap: 10px; 
            margin-bottom: 20px; 
            flex-wrap: wrap; 
            justify-content: center; 
        }
        .nav button { 
            background: white; 
            border: 2px solid #3498db; 
            color: #3498db; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer; 
            transition: all 0.3s; 
        }
        .nav button:hover, .nav button.active { 
            background: #3498db; 
            color: white; 
        }
        .content { 
            background: white; 
            padding: 20px; 
            border-radius: 10px; 
            min-height: 500px; 
        }
        .tab { display: none; }
        .tab.active { display: block; }
        .card { 
            background: #f8f9fa; 
            padding: 15px; 
            margin: 10px 0; 
            border-radius: 8px; 
            border-left: 4px solid #3498db; 
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 15px; 
        }
        .btn { 
            background: #27ae60; 
            color: white; 
            border: none; 
            padding: 8px 15px; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 5px; 
        }
        .btn:hover { background: #219a52; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .btn-warning { background: #f39c12; }
        .btn-warning:hover { background: #e67e22; }
        input, select, textarea { 
            width: 100%; 
            padding: 8px; 
            margin: 5px 0; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
        }
        .modal { 
            display: none; 
            position: fixed; 
            z-index: 1000; 
            left: 0; 
            top: 0; 
            width: 100%; 
            height: 100%; 
            background-color: rgba(0,0,0,0.5); 
        }
        .modal-content { 
            background-color: white; 
            margin: 10% auto; 
            padding: 20px; 
            border-radius: 10px; 
            width: 90%; 
            max-width: 600px; 
            max-height: 80vh;
            overflow-y: auto;
        }
        .modal-content.large {
            max-width: 800px;
        }
        .close { 
            color: #aaa; 
            float: right; 
            font-size: 28px; 
            font-weight: bold; 
            cursor: pointer; 
        }
        .close:hover { color: black; }
        .loading { 
            text-align: center; 
            padding: 50px; 
            color: #666; 
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 10px 0;
        }
        .form-group {
            margin: 10px 0;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .alert {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert-success {
            background: #d4edda;
            border-left-color: #27ae60;
            color: #155724;
        }
        .alert-error {
            background: #f8d7da;
            border-left-color: #e74c3c;
            color: #721c24;
        }
        .alert-warning {
            background: #fff3cd;
            border-left-color: #f39c12;
            color: #856404;
        }
        .status-badge {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-completed { background: #d4edda; color: #155724; }
        .status-legitimate { background: #d1ecf1; color: #0c5460; }
        .status-suspicious { background: #f8d7da; color: #721c24; }
        .financial-section {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        .financial-section h4 {
            color: #495057;
            margin-bottom: 15px;
        }
        @media (max-width: 768px) {
            .form-row { grid-template-columns: 1fr; }
            .nav { justify-content: flex-start; overflow-x: auto; }
            .modal-content { width: 95%; margin: 5% auto; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚽ 足球转会系统</h1>
            <p>基于区块链的透明转会平台 - 完整版</p>
        </div>

        <div class="nav">
            <button onclick="showTab('clubs')" class="active">俱乐部信息</button>
            <button onclick="showTab('players')">可转会球员</button>
            <button onclick="showTab('market')">转会市场</button>
            <button onclick="showTab('history')">转会历史</button>
            <button onclick="showTab('blockchain')">区块链详情</button>
            <button onclick="showTab('notifications')">通知中心 <span id="notif-count"></span></button>
        </div>

        <div class="content">
            <!-- 俱乐部信息标签页 -->
            <div id="clubs" class="tab active">
                <h2>俱乐部信息</h2>
                <button class="btn" onclick="loadClubs()">刷新数据</button>
                <div id="clubs-content" class="loading">正在加载...</div>
            </div>

            <!-- 可转会球员标签页 -->
            <div id="players" class="tab">
                <h2>可转会球员</h2>
                <button class="btn" onclick="loadPlayers()">刷新数据</button>
                <button class="btn" onclick="showSetStatusModal()">设置转会状态</button>
                <div id="players-content" class="loading">正在加载...</div>
            </div>

            <!-- 转会市场标签页 -->
            <div id="market" class="tab">
                <h2>转会市场</h2>
                <button class="btn" onclick="loadOffers()">刷新数据</button>
                <button class="btn" onclick="showMakeOfferModal()">发起报价</button>
                <div id="offers-content" class="loading">正在加载...</div>
            </div>

            <!-- 转会历史标签页 -->
            <div id="history" class="tab">
                <h2>转会历史</h2>
                <button class="btn" onclick="loadHistory()">刷新数据</button>
                <div id="history-content" class="loading">正在加载...</div>
            </div>

            <!-- 区块链详情标签页 -->
            <div id="blockchain" class="tab">
                <h2>区块链转会详情</h2>
                <button class="btn" onclick="loadBlockchain()">刷新数据</button>
                <div id="blockchain-content" class="loading">正在加载...</div>
            </div>

            <!-- 通知中心标签页 -->
            <div id="notifications" class="tab">
                <h2>通知中心</h2>
                <button class="btn" onclick="loadNotifications()">刷新数据</button>
                <div id="notifications-content" class="loading">正在加载...</div>
            </div>
        </div>
    </div>

    <!-- 设置转会状态模态框 -->
    <div id="setStatusModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('setStatusModal')">&times;</span>
            <h3>设置球员转会状态</h3>
            <form onsubmit="setPlayerStatus(event)">
                <div class="form-group">
                    <label>选择球员:</label>
                    <select id="statusPlayerId" required>
                        <option value="">选择球员</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>转会状态:</label>
                    <label><input type="radio" name="status" value="1"> 可转会</label>
                    <label><input type="radio" name="status" value="0"> 不可转会</label>
                </div>
                <button type="submit" class="btn">更新状态</button>
            </form>
        </div>
    </div>

    <!-- 发起报价模态框 -->
    <div id="makeOfferModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeModal('makeOfferModal')">&times;</span>
            <h3>发起转会报价</h3>
            <form onsubmit="makeOffer(event)">
                <div class="form-group">
                    <label>选择球员:</label>
                    <select id="offerPlayerId" required>
                        <option value="">选择球员</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>报价俱乐部:</label>
                    <select id="offerClubId" required>
                        <option value="">选择报价俱乐部</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>报价金额 (欧元):</label>
                    <input type="number" id="offerAmount" required>
                    <small id="marketValueHint"></small>
                </div>
                <div class="form-group">
                    <label>附加条款 (可选):</label>
                    <textarea id="offerTerms" rows="3"></textarea>
                </div>
                <button type="submit" class="btn">发送报价</button>
            </form>
        </div>
    </div>

    <!-- 完整转会处理模态框 -->
    <div id="transferModal" class="modal">
        <div class="modal-content large">
            <span class="close" onclick="closeModal('transferModal')">&times;</span>
            <h3>🔄 转会交易处理 - 三步确认流程</h3>

            <div id="transferInfo" class="alert alert-warning">
                <strong>转会详情将在这里显示</strong>
            </div>

            <form onsubmit="processCompleteTransfer(event)">
                <div class="financial-section">
                    <h4>📊 卖方收入数据</h4>
                    <div class="form-row">
                        <div class="form-group">
                            <label>转会费 (€):</label>
                            <input type="number" id="incomeTransferFee" readonly>
                        </div>
                        <div class="form-group">
                            <label>经纪人佣金 (€):</label>
                            <input type="number" id="incomeAgentCommission" min="0" step="0.01" value="0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>其他收入 (€):</label>
                            <input type="number" id="incomeOther" min="0" step="0.01" value="0">
                        </div>
                        <div class="form-group">
                            <label>总收入 (€):</label>
                            <input type="number" id="incomeTotal" readonly>
                        </div>
                    </div>
                </div>

                <div class="financial-section">
                    <h4>📊 买方支出数据</h4>
                    <div class="form-row">
                        <div class="form-group">
                            <label>转会费 (€):</label>
                            <input type="number" id="expenseTransferFee" readonly>
                        </div>
                        <div class="form-group">
                            <label>经纪人佣金 (€):</label>
                            <input type="number" id="expenseAgentCommission" min="0" step="0.01" value="0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>签字费 (€):</label>
                            <input type="number" id="expenseSigningBonus" min="0" step="0.01" value="0">
                        </div>
                        <div class="form-group">
                            <label>体检费用 (€):</label>
                            <input type="number" id="expenseMedical" min="0" step="0.01" value="0">
                        </div>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>其他费用 (€):</label>
                            <input type="number" id="expenseOther" min="0" step="0.01" value="0">
                        </div>
                        <div class="form-group">
                            <label>总支出 (€):</label>
                            <input type="number" id="expenseTotal" readonly>
                        </div>
                    </div>
                </div>

                <div class="alert alert-warning">
                    <strong>⚠️ 重要提示:</strong> 点击"执行转会"将进行LSH验证和区块链三步确认流程。
                </div>

                <div style="text-align: right; margin-top: 20px;">
                    <button type="button" class="btn btn-danger" onclick="closeModal('transferModal')">取消</button>
                    <button type="submit" class="btn">🔄 执行转会</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let allData = {};
        let currentOffer = null;

        // 标签页切换
        function showTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.nav button').forEach(btn => btn.classList.remove('active'));

            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');

            // 加载对应数据
            switch(tabName) {
                case 'clubs': loadClubs(); break;
                case 'players': loadPlayers(); break;
                case 'market': loadOffers(); break;
                case 'history': loadHistory(); break;
                case 'blockchain': loadBlockchain(); break;
                case 'notifications': loadNotifications(); break;
            }
        }

        // 财务数据自动计算
        function setupFinancialCalculators() {
            const incomeInputs = ['incomeAgentCommission', 'incomeOther'];
            incomeInputs.forEach(id => {
                document.getElementById(id).addEventListener('input', calculateIncomeTotal);
            });

            const expenseInputs = ['expenseAgentCommission', 'expenseSigningBonus', 'expenseMedical', 'expenseOther'];
            expenseInputs.forEach(id => {
                document.getElementById(id).addEventListener('input', calculateExpenseTotal);
            });
        }

        function calculateIncomeTotal() {
            const transferFee = parseFloat(document.getElementById('incomeTransferFee').value) || 0;
            const agentCommission = parseFloat(document.getElementById('incomeAgentCommission').value) || 0;
            const otherIncome = parseFloat(document.getElementById('incomeOther').value) || 0;

            const total = transferFee + otherIncome - agentCommission;
            document.getElementById('incomeTotal').value = total.toFixed(2);
        }

        function calculateExpenseTotal() {
            const transferFee = parseFloat(document.getElementById('expenseTransferFee').value) || 0;
            const agentCommission = parseFloat(document.getElementById('expenseAgentCommission').value) || 0;
            const signingBonus = parseFloat(document.getElementById('expenseSigningBonus').value) || 0;
            const medicalCosts = parseFloat(document.getElementById('expenseMedical').value) || 0;
            const otherCosts = parseFloat(document.getElementById('expenseOther').value) || 0;

            const total = transferFee + agentCommission + signingBonus + medicalCosts + otherCosts;
            document.getElementById('expenseTotal').value = total.toFixed(2);
        }

        // 加载俱乐部数据
        async function loadClubs() {
            try {
                const response = await fetch('/api/clubs');
                const data = await response.json();
                allData.clubs = data;

                let html = '<div class="grid">';
                data.forEach(club => {
                    html += `
                        <div class="card">
                            <h3>${club.name}</h3>
                            <p><strong>国家:</strong> ${club.country} | <strong>联赛:</strong> ${club.league}</p>
                            <p><strong>城市:</strong> ${club.city} | <strong>主场:</strong> ${club.stadium}</p>
                            <p><strong>余额:</strong> €${club.balance.toLocaleString()}</p>
                            <p><strong>转会预算:</strong> €${club.transfer_budget.toLocaleString()}</p>
                            <p><strong>球员数:</strong> ${club.player_count} (可转会: ${club.transferable_count})</p>
                        </div>
                    `;
                });
                html += '</div>';

                document.getElementById('clubs-content').innerHTML = html;
            } catch (error) {
                document.getElementById('clubs-content').innerHTML = `<div class="alert alert-error">加载失败: ${error.message}</div>`;
            }
        }

        // 加载球员数据
        async function loadPlayers() {
            try {
                const response = await fetch('/api/players');
                const data = await response.json();
                allData.players = data;

                if (data.length === 0) {
                    document.getElementById('players-content').innerHTML = '<div class="alert alert-warning">暂无可转会球员</div>';
                    return;
                }

                let html = '<div class="grid">';
                data.forEach(player => {
                    html += `
                        <div class="card">
                            <h3>${player.name} #${player.jersey_number}</h3>
                            <p><strong>俱乐部:</strong> ${player.club_name}</p>
                            <p><strong>位置:</strong> ${player.position} | <strong>国籍:</strong> ${player.nationality}</p>
                            <p><strong>市值:</strong> €${player.market_value.toLocaleString()}</p>
                            <p><strong>合约到期:</strong> ${player.contract_end}</p>
                        </div>
                    `;
                });
                html += '</div>';

                document.getElementById('players-content').innerHTML = html;
            } catch (error) {
                document.getElementById('players-content').innerHTML = `<div class="alert alert-error">加载失败: ${error.message}</div>`;
            }
        }

        // 加载报价数据
        async function loadOffers() {
            try {
                const response = await fetch('/api/offers');
                const data = await response.json();
                allData.offers = data;

                if (data.length === 0) {
                    document.getElementById('offers-content').innerHTML = '<div class="alert alert-warning">暂无转会报价</div>';
                    return;
                }

                let html = '';
                data.forEach(offer => {
                    html += `
                        <div class="card">
                            <h3>${offer.player_name} (${offer.position})</h3>
                            <p><strong>报价方:</strong> ${offer.offering_club_name}</p>
                            <p><strong>接收方:</strong> ${offer.receiving_club_name}</p>
                            <p><strong>报价金额:</strong> €${offer.offer_amount.toLocaleString()}</p>
                            <p><strong>球员市值:</strong> €${offer.market_value.toLocaleString()}</p>
                            <p><strong>报价时间:</strong> ${new Date(offer.offer_date).toLocaleString()}</p>
                            ${offer.additional_terms ? `<p><strong>附加条款:</strong> ${offer.additional_terms}</p>` : ''}
                            <div style="margin-top: 10px;">
                                <button class="btn" onclick="handleOffer('${offer.offer_id}', 'accept')">✅ 接受</button>
                                <button class="btn btn-danger" onclick="handleOffer('${offer.offer_id}', 'reject')">❌ 拒绝</button>
                            </div>
                        </div>
                    `;
                });

                document.getElementById('offers-content').innerHTML = html;
            } catch (error) {
                document.getElementById('offers-content').innerHTML = `<div class="alert alert-error">加载失败: ${error.message}</div>`;
            }
        }

        // 加载历史数据
        async function loadHistory() {
            try {
                const response = await fetch('/api/history');
                const data = await response.json();

                if (data.length === 0) {
                    document.getElementById('history-content').innerHTML = '<div class="alert alert-warning">暂无转会历史</div>';
                    return;
                }

                let html = '';
                data.forEach(transfer => {
                    const statusClass = transfer.is_completed ? 'status-completed' : 'status-warning';
                    const lshClass = transfer.is_legitimate === true ? 'status-legitimate' : 
                                   transfer.is_legitimate === false ? 'status-suspicious' : 'status-warning';

                    html += `
                        <div class="card">
                            <h3>${transfer.player_name} (${transfer.position})</h3>
                            <p><strong>转会方向:</strong> ${transfer.selling_club_name} → ${transfer.buying_club_name}</p>
                            <p><strong>转会费:</strong> €${transfer.transfer_fee.toLocaleString()}</p>
                            <p>
                                <span class="status-badge ${statusClass}">
                                    ${transfer.is_completed ? '✅ 已完成' : '🔄 进行中'}
                                </span>
                                <span class="status-badge ${lshClass}">
                                    ${transfer.is_legitimate === true ? '✅ 合法' : 
                                      transfer.is_legitimate === false ? '❌ 可疑' : '⏳ 待验证'}
                                </span>
                            </p>
                            ${transfer.similarity_score ? `<p><strong>LSH相似度分数:</strong> ${transfer.similarity_score.toFixed(4)}</p>` : ''}
                            <p><strong>完成时间:</strong> ${new Date(transfer.completed_at).toLocaleString()}</p>
                            ${transfer.transaction_hash ? `<p><strong>区块链哈希:</strong> <code>${transfer.transaction_hash}</code></p>` : ''}
                        </div>
                    `;
                });

                document.getElementById('history-content').innerHTML = html;
            } catch (error) {
                document.getElementById('history-content').innerHTML = `<div class="alert alert-error">加载失败: ${error.message}</div>`;
            }
        }

        // 加载区块链数据
        async function loadBlockchain() {
            try {
                const response = await fetch('/api/blockchain');
                const data = await response.json();

                if (!data.success) {
                    document.getElementById('blockchain-content').innerHTML = `<div class="alert alert-error">${data.error || '区块链未连接'}</div>`;
                    return;
                }

                let html = '<h3>📊 区块链状态概览</h3>';
                if (data.summary) {
                    html += `<div class="alert alert-success">总转会数: ${data.summary.total_transfers}</div>`;

                    if (data.recent_transfers && data.recent_transfers.length > 0) {
                        html += '<h4>最近的区块链转会记录</h4>';
                        data.recent_transfers.forEach((transfer, index) => {
                            html += `
                                <div class="card">
                                    <h4>转会 #${data.total_transfers - data.recent_transfers.length + index + 1}</h4>
                                    <p><strong>状态:</strong> ${transfer.status}</p>
                                    <p><strong>转会费:</strong> €${transfer.transferFee.toLocaleString()}</p>
                                    <p><strong>球员ID:</strong> ${transfer.playerId}</p>
                                    ${transfer.proposalTimestamp > 0 ? `<p><strong>提议时间:</strong> ${new Date(transfer.proposalTimestamp * 1000).toLocaleString()}</p>` : ''}
                                    ${transfer.acceptanceTimestamp > 0 ? `<p><strong>接受时间:</strong> ${new Date(transfer.acceptanceTimestamp * 1000).toLocaleString()}</p>` : ''}
                                    ${transfer.validationTimestamp > 0 ? `<p><strong>验证时间:</strong> ${new Date(transfer.validationTimestamp * 1000).toLocaleString()}</p>` : ''}
                                </div>
                            `;
                        });
                    }
                } else {
                    html += '<div class="alert alert-warning">暂无区块链数据</div>';
                }

                document.getElementById('blockchain-content').innerHTML = html;
            } catch (error) {
                document.getElementById('blockchain-content').innerHTML = `<div class="alert alert-error">加载失败: ${error.message}</div>`;
            }
        }

        // 加载通知数据
        async function loadNotifications() {
            try {
                const response = await fetch('/api/notifications');
                const data = await response.json();

                // 更新通知计数
                const count = data.length;
                const countEl = document.getElementById('notif-count');
                if (count > 0) {
                    countEl.textContent = `(${count})`;
                    countEl.style.color = '#e74c3c';
                } else {
                    countEl.textContent = '';
                }

                if (data.length === 0) {
                    document.getElementById('notifications-content').innerHTML = '<div class="alert alert-warning">暂无新通知</div>';
                    return;
                }

                let html = '';
                data.forEach(notif => {
                    const icon = {
                        'offer_received': '📥',
                        'offer_accepted': '✅',
                        'offer_rejected': '❌',
                        'transfer_completed': '🎉'
                    }[notif.message_type] || '📢';

                    html += `
                        <div class="card">
                            <h3>${icon} ${notif.title}</h3>
                            <p><strong>俱乐部:</strong> ${notif.club_name}</p>
                            <p>${notif.message}</p>
                            <p><small>${new Date(notif.created_at).toLocaleString()}</small></p>
                        </div>
                    `;
                });

                document.getElementById('notifications-content').innerHTML = html;
            } catch (error) {
                document.getElementById('notifications-content').innerHTML = `<div class="alert alert-error">加载失败: ${error.message}</div>`;
            }
        }

        // 显示设置状态模态框
        async function showSetStatusModal() {
            if (!allData.clubs) await loadClubs();

            let html = '<option value="">选择球员</option>';
            allData.clubs.forEach(club => {
                if (club.players) {
                    club.players.forEach(player => {
                        html += `<option value="${player.player_id}">${player.name} (${club.name}) - ${player.transfer_status ? '可转会' : '不可转会'}</option>`;
                    });
                }
            });

            document.getElementById('statusPlayerId').innerHTML = html;
            document.getElementById('setStatusModal').style.display = 'block';
        }

        // 显示发起报价模态框
        async function showMakeOfferModal() {
            if (!allData.players) await loadPlayers();
            if (!allData.clubs) await loadClubs();

            // 填充球员选项
            let playerHtml = '<option value="">选择球员</option>';
            allData.players.forEach(player => {
                playerHtml += `<option value="${player.player_id}" data-market-value="${player.market_value}">${player.name} (${player.club_name}) - €${player.market_value.toLocaleString()}</option>`;
            });
            document.getElementById('offerPlayerId').innerHTML = playerHtml;

            // 填充俱乐部选项
            let clubHtml = '<option value="">选择报价俱乐部</option>';
            allData.clubs.forEach(club => {
                clubHtml += `<option value="${club.club_id}">${club.name} - 预算: €${club.transfer_budget.toLocaleString()}</option>`;
            });
            document.getElementById('offerClubId').innerHTML = clubHtml;

            // 监听球员选择变化
            document.getElementById('offerPlayerId').onchange = function() {
                const option = this.options[this.selectedIndex];
                if (option.value) {
                    const marketValue = parseFloat(option.dataset.marketValue);
                    document.getElementById('marketValueHint').textContent = 
                        `球员市值: €${marketValue.toLocaleString()}, 建议报价: €${(marketValue * 0.8).toLocaleString()} - €${(marketValue * 1.2).toLocaleString()}`;
                }
            };

            document.getElementById('makeOfferModal').style.display = 'block';
        }

        // 设置球员状态
        async function setPlayerStatus(event) {
            event.preventDefault();

            const playerId = document.getElementById('statusPlayerId').value;
            const status = document.querySelector('input[name="status"]:checked').value;

            try {
                const response = await fetch('/api/set_status', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({player_id: playerId, status: parseInt(status)})
                });

                const result = await response.json();
                alert(result.success ? '状态更新成功!' : '更新失败: ' + result.error);

                if (result.success) {
                    closeModal('setStatusModal');
                    loadClubs();
                    loadPlayers();
                }
            } catch (error) {
                alert('请求失败: ' + error.message);
            }
        }

        // 发起报价
        async function makeOffer(event) {
            event.preventDefault();

            const data = {
                player_id: document.getElementById('offerPlayerId').value,
                offering_club_id: document.getElementById('offerClubId').value,
                offer_amount: parseFloat(document.getElementById('offerAmount').value),
                additional_terms: document.getElementById('offerTerms').value
            };

            try {
                const response = await fetch('/api/make_offer', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });

                const result = await response.json();
                alert(result.success ? '报价发送成功!' : '发送失败: ' + result.error);

                if (result.success) {
                    closeModal('makeOfferModal');
                    loadOffers();
                    loadNotifications();
                }
            } catch (error) {
                alert('请求失败: ' + error.message);
            }
        }

        // 处理报价
        async function handleOffer(offerId, action) {
            if (!confirm(`确定要${action === 'accept' ? '接受' : '拒绝'}这个报价吗？`)) return;

            try {
                const response = await fetch('/api/handle_offer', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({offer_id: offerId, action: action})
                });

                const result = await response.json();
                alert(result.success ? `报价${action === 'accept' ? '接受' : '拒绝'}成功!` : '操作失败: ' + result.error);

                if (result.success) {
                    loadOffers();
                    loadNotifications();

                    if (action === 'accept') {
                        // 显示转会处理模态框
                        showTransferModal(offerId);
                    }
                }
            } catch (error) {
                alert('请求失败: ' + error.message);
            }
        }

        // 显示转会处理模态框
        function showTransferModal(offerId) {
            // 从当前报价中找到对应信息
            const offer = allData.offers.find(o => o.offer_id === offerId);
            if (!offer) {
                alert('找不到报价信息');
                return;
            }

            currentOffer = offer;

            // 设置转会信息
            document.getElementById('transferInfo').innerHTML = `
                <strong>转会详情:</strong><br>
                球员: ${offer.player_name} (${offer.position})<br>
                卖方: ${offer.receiving_club_name}<br>
                买方: ${offer.offering_club_name}<br>
                转会费: €${offer.offer_amount.toLocaleString()}
            `;

            // 设置财务数据
            document.getElementById('incomeTransferFee').value = offer.offer_amount;
            document.getElementById('expenseTransferFee').value = offer.offer_amount;

            // 设置财务计算监听器
            setupFinancialCalculators();

            // 初始计算
            calculateIncomeTotal();
            calculateExpenseTotal();

            document.getElementById('transferModal').style.display = 'block';
        }

        // 处理完整转会
        async function processCompleteTransfer(event) {
            event.preventDefault();

            if (!currentOffer) {
                alert('转会信息丢失');
                return;
            }

            // 收集财务数据
            const incomeData = {
                transfer_fee: parseFloat(document.getElementById('incomeTransferFee').value),
                agent_commission: parseFloat(document.getElementById('incomeAgentCommission').value) || 0,
                other_income: parseFloat(document.getElementById('incomeOther').value) || 0,
                total_income: parseFloat(document.getElementById('incomeTotal').value)
            };

            const expenseData = {
                transfer_fee: parseFloat(document.getElementById('expenseTransferFee').value),
                agent_commission: parseFloat(document.getElementById('expenseAgentCommission').value) || 0,
                signing_bonus: parseFloat(document.getElementById('expenseSigningBonus').value) || 0,
                medical_costs: parseFloat(document.getElementById('expenseMedical').value) || 0,
                other_costs: parseFloat(document.getElementById('expenseOther').value) || 0,
                total_expense: parseFloat(document.getElementById('expenseTotal').value)
            };

            if (!confirm('确定要执行转会吗？这将进行LSH验证和区块链三步确认。')) return;

            // 显示处理中状态
            const submitBtn = event.target.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = '🔄 处理中...';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/api/process_transfer', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        offer_id: currentOffer.offer_id,
                        income_data: incomeData,
                        expense_data: expenseData
                    })
                });

                const result = await response.json();

                if (result.success) {
                    alert('🎉 转会交易成功完成！已完成LSH验证和区块链三步确认。');
                    closeModal('transferModal');
                    // 刷新数据
                    loadOffers();
                    loadHistory();
                    loadClubs();
                    loadBlockchain();
                    loadNotifications();
                } else {
                    alert('转会失败: ' + result.error);
                }

            } catch (error) {
                alert('请求失败: ' + error.message);
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        }

        // 关闭模态框
        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
            currentOffer = null;
        }

        // 点击模态框外部关闭
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        }

        // 页面加载时初始化
        window.onload = function() {
            loadClubs();
            loadNotifications();
            // 定期刷新通知
            setInterval(loadNotifications, 30000);
        }
    </script>
</body>
</html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

    def get_db_connection(self):
        conn = sqlite3.connect('football_transfer_enhanced.db')
        conn.row_factory = sqlite3.Row
        return conn

    def serve_clubs_data(self):
        try:
            conn = self.get_db_connection()

            clubs = conn.execute("""
                SELECT c.*, 
                       COUNT(p.player_id) as player_count,
                       COUNT(CASE WHEN p.transfer_status = 1 THEN 1 END) as transferable_count
                FROM clubs c
                LEFT JOIN players p ON c.club_id = p.current_club_id
                GROUP BY c.club_id
                ORDER BY c.name
            """).fetchall()

            clubs_data = []
            for club in clubs:
                club_dict = dict(club)

                players = conn.execute("""
                    SELECT * FROM players WHERE current_club_id = ? ORDER BY jersey_number
                """, (club['club_id'],)).fetchall()

                club_dict['players'] = [dict(player) for player in players]
                clubs_data.append(club_dict)

            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(clubs_data, default=str).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_players_data(self):
        try:
            conn = self.get_db_connection()

            players = conn.execute("""
                SELECT p.*, c.name as club_name
                FROM players p
                JOIN clubs c ON p.current_club_id = c.club_id
                WHERE p.transfer_status = 1
                ORDER BY p.market_value DESC
            """).fetchall()

            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([dict(player) for player in players], default=str).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_offers_data(self):
        try:
            conn = self.get_db_connection()

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

            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([dict(offer) for offer in offers], default=str).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_history_data(self):
        try:
            conn = self.get_db_connection()

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

            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([dict(transfer) for transfer in transfers], default=str).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_notifications_data(self):
        try:
            conn = self.get_db_connection()

            notifications = conn.execute("""
                SELECT n.*, c.name as club_name
                FROM notifications n
                JOIN clubs c ON n.club_id = c.club_id
                WHERE n.is_read = 0
                ORDER BY n.created_at DESC
            """).fetchall()

            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps([dict(notif) for notif in notifications], default=str).encode())

        except Exception as e:
            self.send_error(500, str(e))

    def serve_blockchain_data(self):
        try:
            transfer_manager = self.get_transfer_manager()
            if not transfer_manager.blockchain_service or not transfer_manager.blockchain_service.is_connected():
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': '区块链未连接'}).encode())
                return

            # 获取区块链数据
            summary = transfer_manager.blockchain_service.get_transfer_status_summary()
            total_transfers = transfer_manager.blockchain_service.get_transfer_count()

            recent_transfers = []
            if total_transfers > 0:
                for i in range(max(1, total_transfers - 4), total_transfers + 1):
                    details = transfer_manager.blockchain_service.get_transfer_details(i)
                    if details:
                        recent_transfers.append(details)

            result = {
                'success': True,
                'summary': summary,
                'recent_transfers': recent_transfers,
                'total_transfers': total_transfers
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, default=str).encode())

        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_set_status(self, data):
        try:
            conn = self.get_db_connection()

            conn.execute("""
                UPDATE players SET transfer_status = ? WHERE player_id = ?
            """, (data['status'], data['player_id']))

            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_make_offer(self, data):
        try:
            conn = self.get_db_connection()

            offer_id = f"offer_{uuid.uuid4().hex[:8]}"

            # 获取球员信息
            player = conn.execute("""
                SELECT * FROM players WHERE player_id = ?
            """, (data['player_id'],)).fetchone()

            if not player:
                raise Exception('球员不存在')

            # 获取报价俱乐部信息
            offering_club = conn.execute("""
                SELECT * FROM clubs WHERE club_id = ?
            """, (data['offering_club_id'],)).fetchone()

            if not offering_club:
                raise Exception('俱乐部不存在')

            # 检查预算
            if data['offer_amount'] > offering_club['transfer_budget']:
                raise Exception('报价金额超出俱乐部预算')

            # 检查是否是同一俱乐部
            if data['offering_club_id'] == player['current_club_id']:
                raise Exception('不能对自己俱乐部的球员报价')

            # 创建报价记录
            expiry_date = (datetime.now() + timedelta(days=7)).isoformat()

            conn.execute("""
                INSERT INTO transfer_offers 
                (offer_id, player_id, offering_club_id, receiving_club_id, offer_amount, 
                 additional_terms, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (offer_id, data['player_id'], data['offering_club_id'],
                  player['current_club_id'], data['offer_amount'],
                  data.get('additional_terms', ''), expiry_date))

            # 创建通知
            notification_id = f"notif_{uuid.uuid4().hex[:8]}"
            message = f"{offering_club['name']} 对球员 {player['name']} 报价 €{data['offer_amount']:,.2f}"

            conn.execute("""
                INSERT INTO notifications 
                (notification_id, club_id, message_type, title, message, related_offer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (notification_id, player['current_club_id'], 'offer_received',
                  '收到转会报价', message, offer_id))

            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'offer_id': offer_id}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_offer_response(self, data):
        try:
            conn = self.get_db_connection()

            # 获取报价信息
            offer = conn.execute("""
                SELECT o.*, p.name as player_name, oc.name as offering_club_name
                FROM transfer_offers o
                JOIN players p ON o.player_id = p.player_id
                JOIN clubs oc ON o.offering_club_id = oc.club_id
                WHERE o.offer_id = ?
            """, (data['offer_id'],)).fetchone()

            if not offer:
                raise Exception('报价不存在')

            # 更新报价状态
            new_status = 'accepted' if data['action'] == 'accept' else 'rejected'
            conn.execute("""
                UPDATE transfer_offers 
                SET offer_status = ?, response_date = CURRENT_TIMESTAMP
                WHERE offer_id = ?
            """, (new_status, data['offer_id']))

            # 创建通知给报价方
            notification_id = f"notif_{uuid.uuid4().hex[:8]}"
            message = f"您对球员 {offer['player_name']} 的报价已被{'接受' if data['action'] == 'accept' else '拒绝'}"
            title = '报价被接受' if data['action'] == 'accept' else '报价被拒绝'
            message_type = 'offer_accepted' if data['action'] == 'accept' else 'offer_rejected'

            conn.execute("""
                INSERT INTO notifications 
                (notification_id, club_id, message_type, title, message, related_offer_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (notification_id, offer['offering_club_id'], message_type, title, message, data['offer_id']))

            conn.commit()
            conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': True,
                'can_transfer': data['action'] == 'accept'
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

    def handle_complete_transfer(self, data):
        """处理完整的转会交易"""
        try:
            conn = self.get_db_connection()

            # 获取报价信息
            offer = conn.execute("""
                SELECT o.*, p.name as player_name, p.position, p.market_value,
                       oc.name as offering_club_name, rc.name as receiving_club_name
                FROM transfer_offers o
                JOIN players p ON o.player_id = p.player_id
                JOIN clubs oc ON o.offering_club_id = oc.club_id
                JOIN clubs rc ON o.receiving_club_id = rc.club_id
                WHERE o.offer_id = ?
            """, (data['offer_id'],)).fetchone()

            if not offer:
                raise Exception('报价不存在')

            conn.close()

            # 调用转会管理器的API方法处理完整转会
            transfer_manager = self.get_transfer_manager()
            result = transfer_manager.process_transfer_transaction_api(
                dict(offer),
                data['income_data'],
                data['expense_data']
            )

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, default=str).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())


def start_complete_web_interface():
    """启动完整的Web界面"""
    # 检查数据库是否存在
    if not os.path.exists('football_transfer_enhanced.db'):
        print("❌ 数据库不存在，请先运行 python init_database_enhanced.py")
        return False

    # 创建web目录（如果不存在）
    if not os.path.exists('web'):
        os.makedirs('web')

    PORT = 8000

    try:
        with socketserver.TCPServer(("", PORT), CompleteTransferHandler) as httpd:
            print("=" * 60)
            print("🚀 足球转会系统完整Web界面已启动!")
            print(f"📱 访问地址: http://localhost:{PORT}")
            print("=" * 60)
            print("完整功能清单:")
            print("✅ 查看俱乐部信息和球员")
            print("✅ 设置球员转会状态")
            print("✅ 发起和处理转会报价")
            print("✅ 完整转会交易处理 (包含LSH验证)")
            print("✅ 区块链三步确认流程")
            print("✅ 查看转会历史记录")
            print("✅ 区块链详情查看")
            print("✅ 实时通知系统")
            print("=" * 60)
            print("按 Ctrl+C 停止服务器")

            # 自动打开浏览器
            try:
                webbrowser.open(f'http://localhost:{PORT}')
            except:
                pass

            httpd.serve_forever()

    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False


if __name__ == "__main__":
    start_complete_web_interface()