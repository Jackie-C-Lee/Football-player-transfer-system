# -*- coding: utf-8 -*-
import sqlite3
import os
from datetime import datetime
import io
import sys
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='gb18030')  # 改变标准输出的默认编码


def init_enhanced_database():
    """初始化增强版SQLite数据库"""
    db_path = 'football_transfer_enhanced.db'

    # 如果数据库文件已存在，删除它以重新创建
    if os.path.exists(db_path):
        os.remove(db_path)
        print("已删除旧数据库文件")

    # 创建新数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建俱乐部表（增强版）
    cursor.execute('''
    CREATE TABLE clubs (
        club_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT,
        league TEXT,
        city TEXT,
        founded_year INTEGER,
        stadium TEXT,
        wallet_address TEXT UNIQUE,
        private_key TEXT,
        balance DECIMAL(15,2) DEFAULT 0,
        transfer_budget DECIMAL(15,2) DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 创建教练表
    cursor.execute('''
    CREATE TABLE coaches (
        coach_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        nationality TEXT,
        birth_place TEXT,
        birth_date DATE,
        current_club_id TEXT,
        coaching_style TEXT,
        major_achievements TEXT,
        contract_start DATE,
        contract_end DATE,
        salary DECIMAL(12,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_club_id) REFERENCES clubs(club_id)
    )
    ''')

    # 创建球员表（增强版）
    cursor.execute('''
    CREATE TABLE players (
        player_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        english_name TEXT,
        position TEXT,
        nationality TEXT,
        birth_place TEXT,
        birth_date DATE,
        height DECIMAL(3,2),
        weight DECIMAL(5,2),
        preferred_foot TEXT,
        current_club_id TEXT,
        market_value DECIMAL(12,2),
        transfer_status BOOLEAN DEFAULT 0,
        jersey_number INTEGER,
        contract_start DATE,
        contract_end DATE,
        salary DECIMAL(12,2),
        major_achievements TEXT,
        club_career_history TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (current_club_id) REFERENCES clubs(club_id)
    )
    ''')

    # 创建转会报价表
    cursor.execute('''
    CREATE TABLE transfer_offers (
        offer_id TEXT PRIMARY KEY,
        player_id TEXT,
        offering_club_id TEXT,
        receiving_club_id TEXT,
        offer_amount DECIMAL(12,2),
        additional_terms TEXT,
        offer_status TEXT DEFAULT 'pending',  -- pending, accepted, rejected, expired
        offer_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expiry_date TIMESTAMP,
        response_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (offering_club_id) REFERENCES clubs(club_id),
        FOREIGN KEY (receiving_club_id) REFERENCES clubs(club_id)
    )
    ''')

    # 创建转会记录表（增强版）
    cursor.execute('''
    CREATE TABLE transfers (
        transfer_id TEXT PRIMARY KEY,
        player_id TEXT,
        selling_club_id TEXT,
        buying_club_id TEXT,
        transfer_fee DECIMAL(12,2),
        additional_costs DECIMAL(12,2) DEFAULT 0,
        income_data TEXT,  -- JSON格式存储收入数据
        expense_data TEXT,  -- JSON格式存储支出数据
        transaction_hash TEXT,
        lsh_income_hash TEXT,
        lsh_expense_hash TEXT,
        is_validated BOOLEAN DEFAULT 0,
        is_completed BOOLEAN DEFAULT 0,
        transfer_window TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (selling_club_id) REFERENCES clubs(club_id),
        FOREIGN KEY (buying_club_id) REFERENCES clubs(club_id)
    )
    ''')

    # 创建消息通知表
    cursor.execute('''
    CREATE TABLE notifications (
        notification_id TEXT PRIMARY KEY,
        club_id TEXT,
        message_type TEXT,  -- offer_received, offer_accepted, offer_rejected, transfer_completed
        title TEXT,
        message TEXT,
        related_offer_id TEXT,
        related_transfer_id TEXT,
        is_read BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (club_id) REFERENCES clubs(club_id),
        FOREIGN KEY (related_offer_id) REFERENCES transfer_offers(offer_id),
        FOREIGN KEY (related_transfer_id) REFERENCES transfers(transfer_id)
    )
    ''')

    # 创建LSH验证记录表（增强版）
    cursor.execute('''
    CREATE TABLE lsh_validations (
        validation_id TEXT PRIMARY KEY,
        transfer_id TEXT,
        income_index TEXT,
        expense_index TEXT,
        similarity_score DECIMAL(5,4),
        is_legitimate BOOLEAN,
        validation_details TEXT,
        risk_level TEXT,  -- low, medium, high
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transfer_id) REFERENCES transfers(transfer_id)
    )
    ''')

    # 使用 Ganache 提供的前5个账户地址和私钥。（具体的地址和密钥请从自己的ganache账号数据中获取）
    ganache_accounts = [
        {
            'address': '0x',
            'private_key': '0x'  # 请从 Ganache 获取第1个账户的私钥
        },
        {
            'address': '0x',
            'private_key': '0x'  # 请从 Ganache 获取第2个账户的私钥
        },
        {
            'address': '0x',
            'private_key': '0x'  # 请从 Ganache 获取第3个账户的私钥
        },
        {
            'address': '0x',
            'private_key': '0x'  # 请从 Ganache 获取第4个账户的私钥
        },
        {
            'address': '0x',
            'private_key': '0x'  # 请从 Ganache 获取第5个账户的私钥
        },
    ]

    # 插入测试俱乐部数据（每个俱乐部使用不同账户）
    test_clubs = [
        ('club_001', 'Manchester United', 'England', 'Premier League', 'Manchester', 1878, 'Old Trafford',
         ganache_accounts[0]['address'], ganache_accounts[0]['private_key'], 15000.00, 100000.00),
        ('club_002', 'Real Madrid', 'Spain', 'La Liga', 'Madrid', 1902, 'Santiago Bernabéu',
         ganache_accounts[1]['address'], ganache_accounts[1]['private_key'], 18000.00, 120000.00),
        ('club_003', 'Bayern Munich', 'Germany', 'Bundesliga', 'Munich', 1900, 'Allianz Arena',
         ganache_accounts[2]['address'], ganache_accounts[2]['private_key'], 16000.00, 110000.00),
        ('club_004', 'Barcelona', 'Spain', 'La Liga', 'Barcelona', 1899, 'Camp Nou',
         ganache_accounts[3]['address'], ganache_accounts[3]['private_key'], 14000.00, 95000.00),
        ('club_005', 'Liverpool', 'England', 'Premier League', 'Liverpool', 1892, 'Anfield',
         ganache_accounts[4]['address'], ganache_accounts[4]['private_key'], 13000.00, 90000.00)
    ]

    try:
        cursor.executemany('''
        INSERT INTO clubs (club_id, name, country, league, city, founded_year, stadium, wallet_address, private_key, balance, transfer_budget) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_clubs)
        print("俱乐部数据插入成功")
    except Exception as e:
        print(f"俱乐部数据插入失败: {e}")
        return

    # 插入测试教练数据
    test_coaches = [
        ('coach_001', 'Erik ten Hag', 'Netherlands', 'Haaksbergen', '1970-02-02', 'club_001', 'Attacking', 'Eredivisie Champion', '2022-07-01', '2025-06-30', 12000.00),
        ('coach_002', 'Carlo Ancelotti', 'Italy', 'Reggiolo', '1959-06-10', 'club_002', 'Flexible', 'Champions League Winner', '2021-06-01', '2024-06-30', 15000.00),
        ('coach_003', 'Thomas Tuchel', 'Germany', 'Krumbach', '1973-08-29', 'club_003', 'Tactical', 'Champions League Winner', '2023-03-01', '2025-06-30', 13000.00),
        ('coach_004', 'Xavi Hernández', 'Spain', 'Terrassa', '1980-01-25', 'club_004', 'Possession', 'World Cup Winner', '2021-11-01', '2024-06-30', 11000.00),
        ('coach_005', 'Jürgen Klopp', 'Germany', 'Stuttgart', '1967-06-16', 'club_005', 'Gegenpressing', 'Premier League Champion', '2015-10-01', '2024-06-30', 14000.00)
    ]

    try:
        cursor.executemany('''
        INSERT INTO coaches (coach_id, name, nationality, birth_place, birth_date, current_club_id, coaching_style, major_achievements, contract_start, contract_end, salary) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_coaches)
        print("教练数据插入成功")
    except Exception as e:
        print(f"教练数据插入失败: {e}")

    # 插入测试球员数据（增强版）
    test_players = [
        ('player_001', 'Marcus Rashford', 'Marcus Rashford', 'Forward', 'England', 'Manchester', '1997-10-31', 1.85, 70.0, 'Right', 'club_001', 80000.00, 1, 10, '2016-07-01', '2025-06-30', 15000.00, 'Premier League Winner', 'Manchester United (2016-present)'),
        ('player_002', 'Karim Benzema', 'Karim Benzema', 'Forward', 'France', 'Lyon', '1987-12-19', 1.85, 81.0, 'Right', 'club_002', 50000.00, 0, 9, '2009-07-01', '2024-06-30', 20000.00, 'Ballon dOr Winner', 'Real Madrid (2009-present)'),
        ('player_003', 'Thomas Müller', 'Thomas Müller', 'Midfielder', 'Germany', 'Weilheim', '1989-09-13', 1.86, 75.0, 'Right', 'club_003', 45000.00, 1, 25, '2008-07-01', '2024-06-30', 18000.00, 'World Cup Winner', 'Bayern Munich (2008-present)'),
        ('player_004', 'Robert Lewandowski', 'Robert Lewandowski', 'Forward', 'Poland', 'Warsaw', '1988-08-21', 1.85, 81.0, 'Right', 'club_004', 70000.00, 0, 9, '2022-07-01', '2025-06-30', 25000.00, 'FIFA Best Player', 'Barcelona (2022-present)'),
        ('player_005', 'Mohamed Salah', 'Mohamed Salah', 'Forward', 'Egypt', 'Nagrig', '1992-06-15', 1.75, 71.0, 'Left', 'club_005', 85000.00, 1, 11, '2017-07-01', '2025-06-30', 22000.00, 'Premier League Golden Boot', 'Liverpool (2017-present)'),
        ('player_006', 'Paul Pogba', 'Paul Pogba', 'Midfielder', 'France', 'Lagny-sur-Marne', '1993-03-15', 1.91, 84.0, 'Right', 'club_001', 35000.00, 1, 6, '2016-07-01', '2024-06-30', 16000.00, 'World Cup Winner', 'Manchester United (2016-present)'),
        ('player_007', 'Pedri', 'Pedro González López', 'Midfielder', 'Spain', 'Tegueste', '2002-11-25', 1.74, 60.0, 'Right', 'club_004', 60000.00, 0, 8, '2020-07-01', '2026-06-30', 8000.00, 'Golden Boy Award', 'Barcelona (2020-present)'),
        ('player_008', 'Sadio Mané', 'Sadio Mané', 'Forward', 'Senegal', 'Sédhiou', '1992-04-10', 1.75, 69.0, 'Right', 'club_003', 55000.00, 1, 17, '2022-07-01', '2025-06-30', 17000.00, 'AFCON Winner', 'Bayern Munich (2022-present)'),
        ('player_009', 'Kylian Mbappé', 'Kylian Mbappé', 'Forward', 'France', 'Paris', '1998-12-20', 1.78, 73.0, 'Right', 'club_002', 75000.00, 1, 7, '2017-07-01', '2025-06-30', 23000.00, 'Champions League Winner', 'Real Madrid (2017-present)'),
    ]

    try:
        cursor.executemany('''
        INSERT INTO players (player_id, name, english_name, position, nationality, birth_place, birth_date, height, weight, preferred_foot, current_club_id, market_value, transfer_status, jersey_number, contract_start, contract_end, salary, major_achievements, club_career_history) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', test_players)
        print("球员数据插入成功")
    except Exception as e:
        print(f"球员数据插入失败: {e}")

    # 提交更改并关闭连接
    conn.commit()
    conn.close()

    print(f"\n增强版数据库初始化完成！数据库文件: {db_path}")
    print("测试数据已插入:")
    print("- 5个俱乐部（每个使用不同的Ganache账户）")
    print("- 5个教练")
    print("- 9个球员（包含消息系统）")
    print("- 支持转会报价系统")
    print("- 支持消息通知系统")

    # 验证数据插入
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM clubs")
        club_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM coaches")
        coach_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]

        conn.close()

        print(f"\n验证结果:")
        print(f"俱乐部数量: {club_count}")
        print(f"教练数量: {coach_count}")
        print(f"球员数量: {player_count}")

        if club_count == 5 and coach_count == 5 and player_count == 9:
            print("✅ 数据库初始化完全成功!")
        else:
            print("⚠️ 数据插入可能不完整")

    except Exception as e:
        print(f"数据验证失败: {e}")


if __name__ == "__main__":
    print("开始初始化增强版数据库...")
    print("=" * 60)

    try:
        init_enhanced_database()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        print("请检查:")
        print("1. 是否有足够的存储空间")
        print("2. 当前目录是否有写入权限")
        print("3. SQLite是否正确安装")

    print("\n下一步:")
    print("1. 运行: python register_clubs.py")
    print("2. 运行: python enhanced_transfer_manager.py")
    print("3. 按照提示进行转会操作")
