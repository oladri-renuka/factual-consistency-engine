import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, asdict
import numpy as np
from config import DB_PATH

@dataclass
class Claim:
    id: int = None
    text: str = None
    embedding: List[float] = None
    paragraph_number: int = None
    confidence: float = None
    document_id: str = None
    created_at: str = None

class FactLedger:
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                paragraph_number INTEGER NOT NULL,
                claim_text TEXT NOT NULL,
                embedding BLOB,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contradictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                claim_id_1 INTEGER NOT NULL,
                claim_id_2 INTEGER NOT NULL,
                contradiction_score REAL NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (claim_id_1) REFERENCES claims(id),
                FOREIGN KEY (claim_id_2) REFERENCES claims(id)
            )
        ''')

        self.conn.commit()

    def add_claim(self, document_id: str, claim_text: str, embedding: np.ndarray,
                  paragraph_number: int, confidence: float) -> int:
        cursor = self.conn.cursor()
        embedding_blob = embedding.tobytes() if isinstance(embedding, np.ndarray) else embedding

        cursor.execute('''
            INSERT INTO claims (document_id, paragraph_number, claim_text, embedding, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (document_id, paragraph_number, claim_text, embedding_blob, confidence))

        self.conn.commit()
        return cursor.lastrowid

    def add_document(self, doc_id: str, title: str, content: str = None):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO documents (id, title, content)
            VALUES (?, ?, ?)
        ''', (doc_id, title, content))
        self.conn.commit()

    def add_contradiction(self, document_id: str, claim_id_1: int, claim_id_2: int,
                         score: float):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO contradictions (document_id, claim_id_1, claim_id_2, contradiction_score)
            VALUES (?, ?, ?, ?)
        ''', (document_id, claim_id_1, claim_id_2, score))
        self.conn.commit()

    def get_claims_by_document(self, document_id: str) -> List[Claim]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, claim_text, embedding, paragraph_number, confidence, created_at
            FROM claims
            WHERE document_id = ?
            ORDER BY paragraph_number
        ''', (document_id,))

        claims = []
        for row in cursor.fetchall():
            claim = Claim(
                id=row[0],
                text=row[1],
                embedding=np.frombuffer(row[2], dtype=np.float32) if row[2] else None,
                paragraph_number=row[3],
                confidence=row[4],
                created_at=row[5]
            )
            claims.append(claim)

        return claims

    def get_contradictions_by_document(self, document_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT c.id, c.claim_id_1, c.claim_id_2, c.contradiction_score,
                   cl1.claim_text, cl2.claim_text
            FROM contradictions c
            JOIN claims cl1 ON c.claim_id_1 = cl1.id
            JOIN claims cl2 ON c.claim_id_2 = cl2.id
            WHERE c.document_id = ?
        ''', (document_id,))

        contradictions = []
        for row in cursor.fetchall():
            contradictions.append({
                'id': row[0],
                'claim_id_1': row[1],
                'claim_id_2': row[2],
                'score': row[3],
                'claim_1': row[4],
                'claim_2': row[5]
            })

        return contradictions

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
