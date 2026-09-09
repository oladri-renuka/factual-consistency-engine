import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from config import ANNOTATIONS_DB_PATH

class AnnotationManager:
    def __init__(self, db_path: str = str(ANNOTATIONS_DB_PATH)):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotation_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                document_id TEXT NOT NULL,
                label_studio_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                annotator_id TEXT NOT NULL,
                report_id TEXT NOT NULL,
                contradiction_id INTEGER,
                claim_1 TEXT,
                claim_2 TEXT,
                is_contradiction BOOLEAN,
                confidence REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES annotation_tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotator_agreement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                annotator_1 TEXT NOT NULL,
                annotator_2 TEXT NOT NULL,
                total_annotations INTEGER,
                agreed_count INTEGER,
                disagreed_count INTEGER,
                cohens_kappa REAL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self.conn.commit()

    def create_annotation_task(self, report_id: str, document_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO annotation_tasks (report_id, document_id)
            VALUES (?, ?)
        ''', (report_id, document_id))
        self.conn.commit()
        return cursor.lastrowid

    def add_annotation(self, task_id: int, annotator_id: str, report_id: str,
                      contradiction_id: int, claim_1: str, claim_2: str,
                      is_contradiction: bool, confidence: float,
                      notes: str = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO annotations
            (task_id, annotator_id, report_id, contradiction_id, claim_1, claim_2,
             is_contradiction, confidence, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, annotator_id, report_id, contradiction_id, claim_1, claim_2,
              is_contradiction, confidence, notes))
        self.conn.commit()
        return cursor.lastrowid

    def get_annotations_by_report(self, report_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, annotator_id, claim_1, claim_2, is_contradiction, confidence, notes
            FROM annotations
            WHERE report_id = ?
            ORDER BY annotator_id
        ''', (report_id,))

        annotations = []
        for row in cursor.fetchall():
            annotations.append({
                'id': row[0],
                'annotator_id': row[1],
                'claim_1': row[2],
                'claim_2': row[3],
                'is_contradiction': row[4],
                'confidence': row[5],
                'notes': row[6]
            })

        return annotations

    def get_annotator_pair_annotations(self, report_id: str,
                                      annotator_1: str, annotator_2: str) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, claim_1, claim_2, is_contradiction
            FROM annotations
            WHERE report_id = ? AND annotator_id = ?
        ''', (report_id, annotator_1))

        ann1 = {(row[1], row[2]): row[3] for row in cursor.fetchall()}

        cursor.execute('''
            SELECT id, claim_1, claim_2, is_contradiction
            FROM annotations
            WHERE report_id = ? AND annotator_id = ?
        ''', (report_id, annotator_2))

        ann2 = {(row[1], row[2]): row[3] for row in cursor.fetchall()}

        common_pairs = set(ann1.keys()) & set(ann2.keys())

        return {
            'annotator_1': annotator_1,
            'annotator_2': annotator_2,
            'common_annotations': len(common_pairs),
            'agree': sum(1 for pair in common_pairs if ann1[pair] == ann2[pair]),
            'disagree': sum(1 for pair in common_pairs if ann1[pair] != ann2[pair]),
            'annotator_1_total': len(ann1),
            'annotator_2_total': len(ann2)
        }

    def save_agreement_score(self, report_id: str, annotator_1: str,
                            annotator_2: str, agreed: int, total: int,
                            cohens_kappa: float):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO annotator_agreement
            (report_id, annotator_1, annotator_2, total_annotations, agreed_count,
             disagreed_count, cohens_kappa)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (report_id, annotator_1, annotator_2, total, agreed, total - agreed,
              cohens_kappa))
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
