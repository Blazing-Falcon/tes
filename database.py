import sqlite3
from typing import Dict, List

FIRST_BLOOD_BONUS = 100
SECOND_SOLVE_BONUS = 50
THIRD_SOLVE_BONUS = 25

def init_db():
    conn = sqlite3.connect('ctf.db')
    c = conn.cursor()
    
    # Create challenges table with attachment_url
    c.execute('''
        CREATE TABLE IF NOT EXISTS challenges (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            points INTEGER,
            flag TEXT NOT NULL,
            attachment_url TEXT
        )
    ''')
    
    # Create scores table
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            points INTEGER DEFAULT 0
        )
    ''')
    
    # Create solved_challenges table
    c.execute('''
        CREATE TABLE IF NOT EXISTS solved_challenges (
            user_id TEXT,
            challenge_id INTEGER,
            solved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            solve_order INTEGER,
            bonus_points INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES scores (user_id),
            FOREIGN KEY (challenge_id) REFERENCES challenges (id),
            PRIMARY KEY (user_id, challenge_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_challenges() -> Dict:
    conn = sqlite3.connect('ctf.db')
    c = conn.cursor()
    results = c.execute('SELECT category, id, name, description, points, flag, attachment_url FROM challenges').fetchall()
    
    challenges = {}
    for row in results:
        category, id, name, description, points, flag, attachment_url = row
        if category not in challenges:
            challenges[category] = []
        challenges[category].append({
            'id': id,
            'name': name,
            'description': description,
            'points': points,
            'flag': flag,
            'attachment_url': attachment_url
        })
    
    conn.close()
    return challenges

def get_scores() -> Dict:
    conn = sqlite3.connect('ctf.db')
    c = conn.cursor()
    
    scores = {}
    for row in c.execute('SELECT user_id, username, points FROM scores').fetchall():
        user_id, username, points = row
        solved = [name for (name,) in c.execute('''
            SELECT challenges.name 
            FROM solved_challenges 
            JOIN challenges ON challenges.id = solved_challenges.challenge_id 
            WHERE user_id = ?
        ''', (user_id,)).fetchall()]
        
        scores[user_id] = {
            'name': username,
            'points': points,
            'solved': solved
        }
    
    conn.close()
    return scores

def get_solve_count(c, challenge_id: int) -> int:
    return c.execute('''
        SELECT COUNT(*) FROM solved_challenges 
        WHERE challenge_id = ?
    ''', (challenge_id,)).fetchone()[0]

def calculate_blood_bonus(solve_order: int) -> int:
    if solve_order == 1:
        return FIRST_BLOOD_BONUS
    elif solve_order == 2:
        return SECOND_SOLVE_BONUS
    elif solve_order == 3:
        return THIRD_SOLVE_BONUS
    return 0

def add_solved_challenge(user_id: str, username: str, challenge_id: int, points: int):
    conn = sqlite3.connect('ctf.db')
    c = conn.cursor()
    
    # Get solve order for this challenge
    solve_order = get_solve_count(c, challenge_id) + 1
    bonus_points = calculate_blood_bonus(solve_order)
    total_points = points + bonus_points
    
    # Insert or update user score with bonus
    c.execute('''
        INSERT INTO scores (user_id, username, points) 
        VALUES (?, ?, ?) 
        ON CONFLICT(user_id) DO UPDATE SET 
        points = points + ?
    ''', (user_id, username, total_points, total_points))
    
    # Record solved challenge with solve order and bonus
    c.execute('''
        INSERT INTO solved_challenges (user_id, challenge_id, solve_order, bonus_points)
        VALUES (?, ?, ?, ?)
    ''', (user_id, challenge_id, solve_order, bonus_points))
    
    conn.commit()
    conn.close()
    
    return solve_order, bonus_points
