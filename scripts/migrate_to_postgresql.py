#!/usr/bin/env python3
"""
Felix Automation - Database Migration Script (SQLite → PostgreSQL)
Migrates data from SQLite to PostgreSQL while maintaining integrity
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handles SQLite to PostgreSQL migration"""
    
    def __init__(self, sqlite_path, pg_connection_string):
        self.sqlite_path = sqlite_path
        self.pg_conn_string = pg_connection_string
        self.sqlite_conn = None
        self.pg_conn = None
        self.migration_stats = {
            'tables_migrated': 0,
            'total_rows_migrated': 0,
            'errors': 0
        }
    
    def connect(self):
        """Establish connections to both databases"""
        try:
            # SQLite connection
            self.sqlite_conn = sqlite3.connect(self.sqlite_path)
            self.sqlite_conn.row_factory = sqlite3.Row
            logger.info(f"✓ Connected to SQLite: {self.sqlite_path}")
            
            # PostgreSQL connection
            self.pg_conn = psycopg2.connect(self.pg_conn_string)
            logger.info("✓ Connected to PostgreSQL")
            
            return True
        except Exception as e:
            logger.error(f"✗ Connection error: {e}")
            return False
    
    def disconnect(self):
        """Close all connections"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.pg_conn:
            self.pg_conn.close()
        logger.info("Connections closed")
    
    def get_sqlite_tables(self):
        """Get list of tables from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
    
    def get_sqlite_schema(self, table_name):
        """Get CREATE TABLE statement from SQLite"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        schema = cursor.fetchone()[0]
        cursor.close()
        return schema
    
    def convert_sqlite_type_to_postgresql(self, sqlite_type):
        """Convert SQLite types to PostgreSQL types"""
        sqlite_type = sqlite_type.upper().strip()
        
        type_mapping = {
            'INTEGER': 'INTEGER',
            'INT': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'DOUBLE PRECISION',
            'BLOB': 'BYTEA',
            'NUMERIC': 'NUMERIC',
            'BOOLEAN': 'BOOLEAN',
            'DATE': 'DATE',
            'DATETIME': 'TIMESTAMP',
            'TIMESTAMP': 'TIMESTAMP'
        }
        
        for sqlite_t, pg_t in type_mapping.items():
            if sqlite_t in sqlite_type:
                return pg_t
        
        return 'TEXT'  # Default fallback
    
    def create_postgresql_table(self, sqlite_table):
        """Create equivalent table in PostgreSQL"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"PRAGMA table_info({sqlite_table})")
            columns = cursor.fetchall()
            cursor.close()
            
            pg_columns = []
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = 'NOT NULL' if col[3] else ''
                primary = 'PRIMARY KEY' if col[5] else ''
                
                pg_type = self.convert_sqlite_type_to_postgresql(col_type)
                col_def = f'"{col_name}" {pg_type} {not_null} {primary}'.strip()
                pg_columns.append(col_def)
            
            create_stmt = f"CREATE TABLE IF NOT EXISTS \"{sqlite_table}\" ({', '.join(pg_columns)})"
            
            pg_cursor = self.pg_conn.cursor()
            pg_cursor.execute(create_stmt)
            self.pg_conn.commit()
            pg_cursor.close()
            
            logger.info(f"✓ Created table: {sqlite_table}")
            return True
        except Exception as e:
            logger.error(f"✗ Error creating table {sqlite_table}: {e}")
            self.pg_conn.rollback()
            self.migration_stats['errors'] += 1
            return False
    
    def migrate_table_data(self, table_name):
        """Migrate data from SQLite table to PostgreSQL"""
        try:
            # Get all data from SQLite
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"SELECT * FROM \"{table_name}\"")
            rows = cursor.fetchall()
            cursor.close()
            
            if not rows:
                logger.info(f"  → No data to migrate for {table_name}")
                return 0
            
            # Get column names
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            columns = [row[1] for row in cursor.fetchall()]
            cursor.close()
            
            # Prepare data for PostgreSQL
            data = []
            for row in rows:
                data.append(tuple(row))
            
            # Insert data
            placeholders = ','.join(['%s'] * len(columns))
            insert_stmt = f'INSERT INTO "{table_name}" ({",".join([f\'"{c}\'' for c in columns])}) VALUES ({placeholders})'
            
            pg_cursor = self.pg_conn.cursor()
            execute_values(pg_cursor, insert_stmt, data, page_size=100)
            self.pg_conn.commit()
            pg_cursor.close()
            
            count = len(data)
            logger.info(f"  → Migrated {count} rows")
            return count
        except Exception as e:
            logger.error(f"✗ Error migrating data from {table_name}: {e}")
            self.pg_conn.rollback()
            self.migration_stats['errors'] += 1
            return 0
    
    def create_postgresql_indexes(self):
        """Create indexes in PostgreSQL for performance"""
        try:
            indexes = [
                ('clients', 'email'),
                ('clients', 'created_at'),
                ('pipeline', 'client_id'),
                ('pipeline', 'stage'),
                ('audits', 'client_id'),
                ('audits', 'platform'),
            ]
            
            pg_cursor = self.pg_conn.cursor()
            for table, column in indexes:
                try:
                    index_name = f"idx_{table}_{column}"
                    pg_cursor.execute(f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table}" ("{column}")')
                    logger.info(f"  ✓ Created index: {index_name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Index {index_name}: {e}")
            
            self.pg_conn.commit()
            pg_cursor.close()
            return True
        except Exception as e:
            logger.error(f"✗ Error creating indexes: {e}")
            return False
    
    def validate_migration(self):
        """Validate that migration was successful"""
        try:
            # Compare row counts
            sqlite_cursor = self.sqlite_conn.cursor()
            pg_cursor = self.pg_conn.cursor()
            
            sqlite_tables = self.get_sqlite_tables()
            validation_passed = True
            
            for table in sqlite_tables:
                sqlite_cursor.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                pg_cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                pg_count = pg_cursor.fetchone()[0]
                
                if sqlite_count == pg_count:
                    logger.info(f"  ✓ {table}: {sqlite_count} rows verified")
                else:
                    logger.error(f"  ✗ {table}: Mismatch! SQLite={sqlite_count}, PostgreSQL={pg_count}")
                    validation_passed = False
            
            sqlite_cursor.close()
            pg_cursor.close()
            
            return validation_passed
        except Exception as e:
            logger.error(f"✗ Validation error: {e}")
            return False
    
    def migrate(self):
        """Execute full migration"""
        logger.info("="*60)
        logger.info("FELIX AUTOMATION - DATABASE MIGRATION (SQLite → PostgreSQL)")
        logger.info("="*60)
        
        if not self.connect():
            return False
        
        try:
            # Get tables to migrate
            tables = self.get_sqlite_tables()
            logger.info(f"\nFound {len(tables)} tables to migrate:")
            for table in tables:
                logger.info(f"  • {table}")
            
            # Create tables
            logger.info("\n[1/4] Creating tables in PostgreSQL...")
            for table in tables:
                if self.create_postgresql_table(table):
                    self.migration_stats['tables_migrated'] += 1
            
            # Migrate data
            logger.info("\n[2/4] Migrating data...")
            for table in tables:
                rows = self.migrate_table_data(table)
                self.migration_stats['total_rows_migrated'] += rows
            
            # Create indexes
            logger.info("\n[3/4] Creating indexes...")
            self.create_postgresql_indexes()
            
            # Validate
            logger.info("\n[4/4] Validating migration...")
            if self.validate_migration():
                logger.info("\n✓ MIGRATION SUCCESSFUL!")
                logger.info("="*60)
                logger.info("SUMMARY:")
                logger.info(f"  Tables migrated: {self.migration_stats['tables_migrated']}")
                logger.info(f"  Total rows: {self.migration_stats['total_rows_migrated']}")
                logger.info(f"  Errors: {self.migration_stats['errors']}")
                logger.info("="*60)
                return True
            else:
                logger.error("\n✗ VALIDATION FAILED!")
                return False
        
        except Exception as e:
            logger.error(f"\n✗ MIGRATION FAILED: {e}")
            return False
        finally:
            self.disconnect()

def main():
    """Main entry point"""
    # Configuration
    SQLITE_PATH = "data/pipeline.db"
    PG_CONNECTION_STRING = "postgresql://felix_user:password@localhost:5432/felix_prod"
    
    # Allow override from command line
    if len(sys.argv) > 1:
        PG_CONNECTION_STRING = sys.argv[1]
    
    # Run migration
    migrator = DatabaseMigrator(SQLITE_PATH, PG_CONNECTION_STRING)
    success = migrator.migrate()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
