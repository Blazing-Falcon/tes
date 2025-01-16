import sqlite3
from database import init_db

def setup_challenges():
    init_db()
    conn = sqlite3.connect('ctf.db')
    c = conn.cursor()
    
    challenges = [
        ('Crypto', 'Column Transposition', 'disini ada pesan dienkripsi pake column transposition, try to reverse the logic.', 500, 'Kaliber{C0lumn4l_Tr4nsp0s1t10n4l_C1ph3r}', 'https://github.com/Blazing-Falcon/ctf/blob/main/ctf/crypto/column%20transposition/chall.py'),
        ('Crypto', 'Random Not Random', 'Waduh ini enkrip pake random, gimana ya kembalikannya.', 500, 'Kaliber{15_17_7ru11y_r4nd0m_7h0?}', 'https://github.com/Blazing-Falcon/ctf/blob/main/ctf/crypto/random%20not%20random/chall.java'),
        ('Crypto', 'LSB???', 'Cari tahu deh LSB.', 500, 'Kaliber{st3g4n0gr4phy_1s_fun}', 'https://github.com/Blazing-Falcon/ctf/blob/main/ctf/crypto/lsb%20steganography/encoded_image.png')
    ]
    
    c.executemany('''
        INSERT INTO challenges (category, name, description, points, flag, attachment_url)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', challenges)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    setup_challenges()
