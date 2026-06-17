#!/usr/bin/env python3
"""
Database Toolkit
================

A comprehensive toolkit for database operations, query building, and data management.
Provides abstraction layers for SQLite with extensible patterns for other databases.

Author: Electroduction Security Team
Version: 1.0.0

Features:
---------
- Query Builder: Fluent interface for building SQL queries
- Connection Management: Connection pooling and lifecycle management
- ORM-like Features: Simple object-relational mapping
- Migration System: Schema versioning and migrations
- Data Validation: Input validation and sanitization
- Backup/Restore: Database backup utilities

Usage:
------
    from database_toolkit import Database, QueryBuilder, Table

    # Connect to database
    db = Database("myapp.db")

    # Build and execute queries
    users = (db.table("users")
             .select("id", "name", "email")
             .where("active", "=", True)
             .order_by("name")
             .all())

    # Define models
    class User(Model):
        __tablename__ = "users"

Note: Currently implements SQLite. Pattern supports extension to other databases.
"""

import os
import re
import json
import sqlite3
import hashlib
import threading
from datetime import datetime, date
from typing import Dict, List, Tuple, Optional, Any, Union, Type, Callable, Iterator, Set
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from contextlib import contextmanager
import copy


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

# SQL value types
SQLValue = Union[str, int, float, bool, None, bytes, datetime, date]

# Column type mapping
PYTHON_TO_SQL = {
    str: 'TEXT',
    int: 'INTEGER',
    float: 'REAL',
    bool: 'INTEGER',
    bytes: 'BLOB',
    datetime: 'TIMESTAMP',
    date: 'DATE',
}


# =============================================================================
# EXCEPTIONS
# =============================================================================

class DatabaseError(Exception):
    """Base exception for database errors."""
    pass


class QueryError(DatabaseError):
    """Error in query execution."""
    pass


class ValidationError(DatabaseError):
    """Data validation error."""
    pass


class MigrationError(DatabaseError):
    """Migration error."""
    pass


# =============================================================================
# CONNECTION MANAGER
# =============================================================================

class ConnectionManager:
    """
    Manage database connections with pooling support.

    Features:
    - Connection pooling
    - Thread-safe connections
    - Automatic connection recycling
    - Transaction management

    Example:
        >>> manager = ConnectionManager("mydb.db")
        >>> with manager.connection() as conn:
        ...     cursor = conn.execute("SELECT * FROM users")
    """

    def __init__(self, database: str, pool_size: int = 5):
        """
        Initialize connection manager.

        Args:
            database: Database path (or ":memory:" for in-memory)
            pool_size: Maximum number of pooled connections
        """
        self.database = database
        self.pool_size = pool_size
        self._pool: List[sqlite3.Connection] = []
        self._in_use: Dict[int, sqlite3.Connection] = {}
        self._lock = threading.Lock()
        self._local = threading.local()

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(
            self.database,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def connection(self):
        """
        Get a connection from the pool.

        Usage:
            with manager.connection() as conn:
                conn.execute(...)
        """
        conn = self._acquire()
        try:
            yield conn
        finally:
            self._release(conn)

    def _acquire(self) -> sqlite3.Connection:
        """Acquire a connection from the pool."""
        thread_id = threading.get_ident()

        with self._lock:
            # Check if thread already has a connection
            if thread_id in self._in_use:
                return self._in_use[thread_id]

            # Try to get from pool
            if self._pool:
                conn = self._pool.pop()
            else:
                conn = self._create_connection()

            self._in_use[thread_id] = conn
            return conn

    def _release(self, conn: sqlite3.Connection):
        """Release a connection back to the pool."""
        thread_id = threading.get_ident()

        with self._lock:
            if thread_id in self._in_use:
                del self._in_use[thread_id]

            if len(self._pool) < self.pool_size:
                self._pool.append(conn)
            else:
                conn.close()

    @contextmanager
    def transaction(self):
        """
        Context manager for transactions.

        Usage:
            with manager.transaction() as conn:
                conn.execute(...)  # Auto-commit on success
                # Auto-rollback on exception
        """
        with self.connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def close_all(self):
        """Close all connections."""
        with self._lock:
            for conn in self._pool:
                conn.close()
            self._pool.clear()

            for conn in self._in_use.values():
                conn.close()
            self._in_use.clear()


# =============================================================================
# QUERY BUILDER
# =============================================================================

class QueryBuilder:
    """
    Fluent interface for building SQL queries.

    Provides a chainable API for constructing SELECT, INSERT, UPDATE, and DELETE queries
    with proper parameter binding for security.

    Example:
        >>> qb = QueryBuilder("users")
        >>> query, params = (qb.select("id", "name")
        ...                   .where("active", "=", True)
        ...                   .where("age", ">", 18)
        ...                   .order_by("name")
        ...                   .limit(10)
        ...                   .build())
    """

    def __init__(self, table: str):
        """
        Initialize query builder for a table.

        Args:
            table: Table name
        """
        self.table = table
        self._select_columns: List[str] = []
        self._where_clauses: List[Tuple[str, str, Any]] = []
        self._where_raw: List[Tuple[str, List[Any]]] = []
        self._or_where: List[Tuple[str, str, Any]] = []
        self._joins: List[Tuple[str, str, str]] = []
        self._order_by: List[Tuple[str, str]] = []
        self._group_by: List[str] = []
        self._having: List[Tuple[str, str, Any]] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._distinct: bool = False

    def select(self, *columns: str) -> 'QueryBuilder':
        """
        Set columns to select.

        Args:
            *columns: Column names (or "*" for all)

        Returns:
            Self for chaining
        """
        self._select_columns = list(columns) if columns else ['*']
        return self

    def distinct(self) -> 'QueryBuilder':
        """Add DISTINCT to query."""
        self._distinct = True
        return self

    def where(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """
        Add WHERE clause.

        Args:
            column: Column name
            operator: Comparison operator (=, !=, <, >, <=, >=, LIKE, IN, etc.)
            value: Value to compare

        Returns:
            Self for chaining
        """
        self._where_clauses.append((column, operator.upper(), value))
        return self

    def where_raw(self, clause: str, params: Optional[List[Any]] = None) -> 'QueryBuilder':
        """
        Add raw WHERE clause.

        Args:
            clause: Raw SQL clause
            params: Parameters for the clause

        Returns:
            Self for chaining
        """
        self._where_raw.append((clause, params or []))
        return self

    def or_where(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """Add OR WHERE clause."""
        self._or_where.append((column, operator.upper(), value))
        return self

    def where_null(self, column: str) -> 'QueryBuilder':
        """Add WHERE column IS NULL."""
        return self.where_raw(f"{column} IS NULL")

    def where_not_null(self, column: str) -> 'QueryBuilder':
        """Add WHERE column IS NOT NULL."""
        return self.where_raw(f"{column} IS NOT NULL")

    def where_in(self, column: str, values: List[Any]) -> 'QueryBuilder':
        """Add WHERE column IN (...)."""
        return self.where(column, 'IN', values)

    def where_between(self, column: str, low: Any, high: Any) -> 'QueryBuilder':
        """Add WHERE column BETWEEN low AND high."""
        return self.where_raw(f"{column} BETWEEN ? AND ?", [low, high])

    def join(self, table: str, on: str, join_type: str = 'INNER') -> 'QueryBuilder':
        """
        Add JOIN clause.

        Args:
            table: Table to join
            on: Join condition
            join_type: Type of join (INNER, LEFT, RIGHT, FULL)

        Returns:
            Self for chaining
        """
        self._joins.append((join_type.upper(), table, on))
        return self

    def left_join(self, table: str, on: str) -> 'QueryBuilder':
        """Add LEFT JOIN."""
        return self.join(table, on, 'LEFT')

    def right_join(self, table: str, on: str) -> 'QueryBuilder':
        """Add RIGHT JOIN."""
        return self.join(table, on, 'RIGHT')

    def order_by(self, column: str, direction: str = 'ASC') -> 'QueryBuilder':
        """
        Add ORDER BY clause.

        Args:
            column: Column to sort by
            direction: Sort direction (ASC or DESC)

        Returns:
            Self for chaining
        """
        self._order_by.append((column, direction.upper()))
        return self

    def group_by(self, *columns: str) -> 'QueryBuilder':
        """Add GROUP BY clause."""
        self._group_by.extend(columns)
        return self

    def having(self, column: str, operator: str, value: Any) -> 'QueryBuilder':
        """Add HAVING clause."""
        self._having.append((column, operator.upper(), value))
        return self

    def limit(self, count: int) -> 'QueryBuilder':
        """Set LIMIT."""
        self._limit_value = count
        return self

    def offset(self, count: int) -> 'QueryBuilder':
        """Set OFFSET."""
        self._offset_value = count
        return self

    def build(self) -> Tuple[str, List[Any]]:
        """
        Build the SELECT query.

        Returns:
            Tuple of (SQL string, parameters list)
        """
        params = []

        # SELECT clause
        columns = ', '.join(self._select_columns) if self._select_columns else '*'
        distinct = 'DISTINCT ' if self._distinct else ''
        sql = f"SELECT {distinct}{columns} FROM {self.table}"

        # JOIN clauses
        for join_type, table, on in self._joins:
            sql += f" {join_type} JOIN {table} ON {on}"

        # WHERE clauses
        where_parts = []
        for column, operator, value in self._where_clauses:
            if operator == 'IN':
                placeholders = ', '.join('?' for _ in value)
                where_parts.append(f"{column} IN ({placeholders})")
                params.extend(value)
            else:
                where_parts.append(f"{column} {operator} ?")
                params.append(value)

        for clause, clause_params in self._where_raw:
            where_parts.append(clause)
            params.extend(clause_params)

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        # OR WHERE clauses
        for column, operator, value in self._or_where:
            sql += f" OR {column} {operator} ?"
            params.append(value)

        # GROUP BY
        if self._group_by:
            sql += " GROUP BY " + ", ".join(self._group_by)

        # HAVING
        for column, operator, value in self._having:
            if 'HAVING' not in sql:
                sql += f" HAVING {column} {operator} ?"
            else:
                sql += f" AND {column} {operator} ?"
            params.append(value)

        # ORDER BY
        if self._order_by:
            order_clauses = [f"{col} {dir}" for col, dir in self._order_by]
            sql += " ORDER BY " + ", ".join(order_clauses)

        # LIMIT and OFFSET
        if self._limit_value is not None:
            sql += f" LIMIT {self._limit_value}"
        if self._offset_value is not None:
            sql += f" OFFSET {self._offset_value}"

        return sql, params

    def build_insert(self, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build INSERT query."""
        columns = list(data.keys())
        placeholders = ', '.join('?' for _ in columns)
        params = list(data.values())

        sql = f"INSERT INTO {self.table} ({', '.join(columns)}) VALUES ({placeholders})"
        return sql, params

    def build_update(self, data: Dict[str, Any]) -> Tuple[str, List[Any]]:
        """Build UPDATE query."""
        set_clauses = [f"{col} = ?" for col in data.keys()]
        params = list(data.values())

        sql = f"UPDATE {self.table} SET {', '.join(set_clauses)}"

        # Add WHERE clauses
        where_parts = []
        for column, operator, value in self._where_clauses:
            where_parts.append(f"{column} {operator} ?")
            params.append(value)

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        return sql, params

    def build_delete(self) -> Tuple[str, List[Any]]:
        """Build DELETE query."""
        params = []
        sql = f"DELETE FROM {self.table}"

        # Add WHERE clauses
        where_parts = []
        for column, operator, value in self._where_clauses:
            where_parts.append(f"{column} {operator} ?")
            params.append(value)

        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        return sql, params

    def build_count(self) -> Tuple[str, List[Any]]:
        """Build COUNT query."""
        self._select_columns = ['COUNT(*) as count']
        return self.build()


# =============================================================================
# SCHEMA BUILDER
# =============================================================================

@dataclass
class Column:
    """Represents a table column definition."""
    name: str
    type: str
    primary_key: bool = False
    auto_increment: bool = False
    nullable: bool = True
    unique: bool = False
    default: Any = None
    foreign_key: Optional[Tuple[str, str]] = None  # (table, column)

    def to_sql(self) -> str:
        """Generate SQL column definition."""
        parts = [self.name, self.type]

        if self.primary_key:
            parts.append('PRIMARY KEY')
            if self.auto_increment:
                parts.append('AUTOINCREMENT')
        else:
            if not self.nullable:
                parts.append('NOT NULL')
            if self.unique:
                parts.append('UNIQUE')
            if self.default is not None:
                if isinstance(self.default, str):
                    parts.append(f"DEFAULT '{self.default}'")
                else:
                    parts.append(f"DEFAULT {self.default}")

        return ' '.join(parts)


class SchemaBuilder:
    """
    Build database schema definitions.

    Provides methods for creating and modifying tables.

    Example:
        >>> builder = SchemaBuilder("users")
        >>> builder.id()
        >>> builder.string("name", nullable=False)
        >>> builder.string("email", unique=True)
        >>> builder.timestamps()
        >>> create_sql = builder.to_sql()
    """

    def __init__(self, table_name: str):
        """Initialize schema builder for a table."""
        self.table_name = table_name
        self.columns: List[Column] = []
        self.indexes: List[Tuple[str, List[str], bool]] = []
        self.foreign_keys: List[Tuple[str, str, str]] = []

    def id(self, name: str = 'id') -> 'SchemaBuilder':
        """Add auto-incrementing primary key."""
        self.columns.append(Column(
            name=name,
            type='INTEGER',
            primary_key=True,
            auto_increment=True,
            nullable=False
        ))
        return self

    def integer(self, name: str, nullable: bool = True, default: Optional[int] = None) -> 'SchemaBuilder':
        """Add integer column."""
        self.columns.append(Column(name=name, type='INTEGER', nullable=nullable, default=default))
        return self

    def big_integer(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add big integer column."""
        self.columns.append(Column(name=name, type='BIGINT', nullable=nullable))
        return self

    def string(self, name: str, length: int = 255, nullable: bool = True,
               unique: bool = False, default: Optional[str] = None) -> 'SchemaBuilder':
        """Add string/varchar column."""
        self.columns.append(Column(
            name=name,
            type=f'VARCHAR({length})',
            nullable=nullable,
            unique=unique,
            default=default
        ))
        return self

    def text(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add text column."""
        self.columns.append(Column(name=name, type='TEXT', nullable=nullable))
        return self

    def boolean(self, name: str, default: Optional[bool] = None) -> 'SchemaBuilder':
        """Add boolean column (stored as integer in SQLite)."""
        self.columns.append(Column(
            name=name,
            type='INTEGER',
            nullable=True,
            default=1 if default else 0 if default is False else None
        ))
        return self

    def float(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add float column."""
        self.columns.append(Column(name=name, type='REAL', nullable=nullable))
        return self

    def decimal(self, name: str, precision: int = 10, scale: int = 2,
                nullable: bool = True) -> 'SchemaBuilder':
        """Add decimal column."""
        self.columns.append(Column(
            name=name,
            type=f'DECIMAL({precision},{scale})',
            nullable=nullable
        ))
        return self

    def datetime(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add datetime column."""
        self.columns.append(Column(name=name, type='DATETIME', nullable=nullable))
        return self

    def date(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add date column."""
        self.columns.append(Column(name=name, type='DATE', nullable=nullable))
        return self

    def timestamp(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add timestamp column."""
        self.columns.append(Column(name=name, type='TIMESTAMP', nullable=nullable))
        return self

    def timestamps(self) -> 'SchemaBuilder':
        """Add created_at and updated_at columns."""
        self.timestamp('created_at', nullable=True)
        self.timestamp('updated_at', nullable=True)
        return self

    def blob(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add blob column."""
        self.columns.append(Column(name=name, type='BLOB', nullable=nullable))
        return self

    def json(self, name: str, nullable: bool = True) -> 'SchemaBuilder':
        """Add JSON column (stored as TEXT in SQLite)."""
        self.columns.append(Column(name=name, type='TEXT', nullable=nullable))
        return self

    def foreign(self, column: str, references_table: str, references_column: str = 'id') -> 'SchemaBuilder':
        """Add foreign key constraint."""
        self.foreign_keys.append((column, references_table, references_column))
        return self

    def index(self, *columns: str, unique: bool = False, name: Optional[str] = None) -> 'SchemaBuilder':
        """Add index."""
        index_name = name or f"idx_{self.table_name}_{'_'.join(columns)}"
        self.indexes.append((index_name, list(columns), unique))
        return self

    def to_sql(self) -> str:
        """Generate CREATE TABLE SQL."""
        column_defs = [col.to_sql() for col in self.columns]

        # Add foreign keys
        for column, ref_table, ref_column in self.foreign_keys:
            column_defs.append(
                f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"
            )

        sql = f"CREATE TABLE IF NOT EXISTS {self.table_name} (\n  "
        sql += ",\n  ".join(column_defs)
        sql += "\n)"

        return sql

    def get_index_sql(self) -> List[str]:
        """Generate CREATE INDEX SQL statements."""
        statements = []
        for name, columns, unique in self.indexes:
            unique_str = "UNIQUE " if unique else ""
            columns_str = ", ".join(columns)
            statements.append(
                f"CREATE {unique_str}INDEX IF NOT EXISTS {name} ON {self.table_name} ({columns_str})"
            )
        return statements


# =============================================================================
# MIGRATION SYSTEM
# =============================================================================

@dataclass
class Migration:
    """Represents a database migration."""
    version: int
    name: str
    up_sql: str
    down_sql: str
    created_at: datetime = field(default_factory=datetime.now)


class MigrationManager:
    """
    Manage database migrations.

    Tracks schema versions and applies/reverts migrations.

    Example:
        >>> manager = MigrationManager(db)
        >>> manager.add_migration(Migration(
        ...     version=1,
        ...     name="create_users",
        ...     up_sql="CREATE TABLE users (...)",
        ...     down_sql="DROP TABLE users"
        ... ))
        >>> manager.migrate()  # Apply all pending
    """

    MIGRATION_TABLE = '_migrations'

    def __init__(self, connection_manager: ConnectionManager):
        """Initialize migration manager."""
        self.conn_manager = connection_manager
        self.migrations: Dict[int, Migration] = {}
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Create migrations tracking table if needed."""
        sql = f"""
        CREATE TABLE IF NOT EXISTS {self.MIGRATION_TABLE} (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self.conn_manager.connection() as conn:
            conn.execute(sql)
            conn.commit()

    def add_migration(self, migration: Migration):
        """Add a migration to the list."""
        self.migrations[migration.version] = migration

    def get_applied_versions(self) -> Set[int]:
        """Get set of applied migration versions."""
        with self.conn_manager.connection() as conn:
            cursor = conn.execute(
                f"SELECT version FROM {self.MIGRATION_TABLE}"
            )
            return {row[0] for row in cursor}

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        applied = self.get_applied_versions()
        pending = [
            m for v, m in sorted(self.migrations.items())
            if v not in applied
        ]
        return pending

    def migrate(self, target_version: Optional[int] = None):
        """
        Apply pending migrations.

        Args:
            target_version: Optional specific version to migrate to
        """
        pending = self.get_pending_migrations()

        if target_version is not None:
            pending = [m for m in pending if m.version <= target_version]

        with self.conn_manager.transaction() as conn:
            for migration in pending:
                try:
                    # Execute migration
                    conn.executescript(migration.up_sql)

                    # Record migration
                    conn.execute(
                        f"INSERT INTO {self.MIGRATION_TABLE} (version, name) VALUES (?, ?)",
                        (migration.version, migration.name)
                    )

                    print(f"Applied migration {migration.version}: {migration.name}")

                except Exception as e:
                    raise MigrationError(
                        f"Failed to apply migration {migration.version}: {e}"
                    )

    def rollback(self, steps: int = 1):
        """
        Rollback migrations.

        Args:
            steps: Number of migrations to rollback
        """
        applied = sorted(self.get_applied_versions(), reverse=True)

        with self.conn_manager.transaction() as conn:
            for version in applied[:steps]:
                migration = self.migrations.get(version)
                if not migration:
                    continue

                try:
                    # Execute rollback
                    conn.executescript(migration.down_sql)

                    # Remove migration record
                    conn.execute(
                        f"DELETE FROM {self.MIGRATION_TABLE} WHERE version = ?",
                        (version,)
                    )

                    print(f"Rolled back migration {version}: {migration.name}")

                except Exception as e:
                    raise MigrationError(
                        f"Failed to rollback migration {version}: {e}"
                    )

    def get_status(self) -> List[Dict[str, Any]]:
        """Get status of all migrations."""
        applied = self.get_applied_versions()
        status = []

        for version in sorted(self.migrations.keys()):
            migration = self.migrations[version]
            status.append({
                'version': version,
                'name': migration.name,
                'applied': version in applied
            })

        return status


# =============================================================================
# TABLE CLASS (ORM-LIKE INTERFACE)
# =============================================================================

class Table:
    """
    ORM-like interface for table operations.

    Provides CRUD operations with query builder support.

    Example:
        >>> users = Table(db, "users")
        >>> users.insert({"name": "John", "email": "john@example.com"})
        >>> user = users.find(1)
        >>> users.where("active", "=", True).all()
    """

    def __init__(self, database: 'Database', table_name: str):
        """Initialize table interface."""
        self.database = database
        self.table_name = table_name
        self._query_builder = QueryBuilder(table_name)

    def _reset_builder(self):
        """Reset query builder for new query."""
        self._query_builder = QueryBuilder(self.table_name)

    def select(self, *columns: str) -> 'Table':
        """Set columns to select."""
        self._query_builder.select(*columns)
        return self

    def where(self, column: str, operator: str, value: Any) -> 'Table':
        """Add WHERE clause."""
        self._query_builder.where(column, operator, value)
        return self

    def or_where(self, column: str, operator: str, value: Any) -> 'Table':
        """Add OR WHERE clause."""
        self._query_builder.or_where(column, operator, value)
        return self

    def where_null(self, column: str) -> 'Table':
        """Add WHERE IS NULL clause."""
        self._query_builder.where_null(column)
        return self

    def where_not_null(self, column: str) -> 'Table':
        """Add WHERE IS NOT NULL clause."""
        self._query_builder.where_not_null(column)
        return self

    def order_by(self, column: str, direction: str = 'ASC') -> 'Table':
        """Add ORDER BY clause."""
        self._query_builder.order_by(column, direction)
        return self

    def limit(self, count: int) -> 'Table':
        """Set LIMIT."""
        self._query_builder.limit(count)
        return self

    def offset(self, count: int) -> 'Table':
        """Set OFFSET."""
        self._query_builder.offset(count)
        return self

    def join(self, table: str, on: str, join_type: str = 'INNER') -> 'Table':
        """Add JOIN clause."""
        self._query_builder.join(table, on, join_type)
        return self

    def all(self) -> List[Dict[str, Any]]:
        """Execute query and return all results."""
        sql, params = self._query_builder.build()
        self._reset_builder()
        return self.database.fetch_all(sql, params)

    def first(self) -> Optional[Dict[str, Any]]:
        """Execute query and return first result."""
        self._query_builder.limit(1)
        sql, params = self._query_builder.build()
        self._reset_builder()
        return self.database.fetch_one(sql, params)

    def count(self) -> int:
        """Get count of matching records."""
        sql, params = self._query_builder.build_count()
        self._reset_builder()
        result = self.database.fetch_one(sql, params)
        return result['count'] if result else 0

    def exists(self) -> bool:
        """Check if any matching records exist."""
        return self.count() > 0

    def find(self, id: int) -> Optional[Dict[str, Any]]:
        """Find record by primary key."""
        return self.where('id', '=', id).first()

    def insert(self, data: Dict[str, Any]) -> int:
        """
        Insert a new record.

        Args:
            data: Column-value pairs

        Returns:
            ID of inserted record
        """
        sql, params = QueryBuilder(self.table_name).build_insert(data)
        return self.database.execute(sql, params)

    def insert_many(self, records: List[Dict[str, Any]]) -> int:
        """
        Insert multiple records.

        Args:
            records: List of column-value dictionaries

        Returns:
            Number of inserted records
        """
        if not records:
            return 0

        columns = list(records[0].keys())
        placeholders = ', '.join('?' for _ in columns)
        sql = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({placeholders})"

        with self.database.conn_manager.transaction() as conn:
            for record in records:
                params = [record.get(col) for col in columns]
                conn.execute(sql, params)

        return len(records)

    def update(self, data: Dict[str, Any]) -> int:
        """
        Update matching records.

        Args:
            data: Column-value pairs to update

        Returns:
            Number of updated records
        """
        sql, params = self._query_builder.build_update(data)
        self._reset_builder()
        return self.database.execute(sql, params)

    def delete(self) -> int:
        """
        Delete matching records.

        Returns:
            Number of deleted records
        """
        sql, params = self._query_builder.build_delete()
        self._reset_builder()
        return self.database.execute(sql, params)

    def truncate(self):
        """Delete all records from table."""
        self.database.execute(f"DELETE FROM {self.table_name}")

    def get_columns(self) -> List[Dict[str, Any]]:
        """Get table column information."""
        result = self.database.fetch_all(f"PRAGMA table_info({self.table_name})")
        return [
            {
                'name': row['name'],
                'type': row['type'],
                'nullable': not row['notnull'],
                'default': row['dflt_value'],
                'primary_key': bool(row['pk'])
            }
            for row in result
        ]


# =============================================================================
# MAIN DATABASE CLASS
# =============================================================================

class Database:
    """
    Main database interface.

    Provides high-level access to all database operations.

    Example:
        >>> db = Database("myapp.db")
        >>>
        >>> # Table operations
        >>> users = db.table("users")
        >>> users.insert({"name": "John"})
        >>>
        >>> # Raw queries
        >>> db.execute("UPDATE users SET active = ?", [True])
        >>> results = db.fetch_all("SELECT * FROM users")
        >>>
        >>> # Schema operations
        >>> db.create_table("posts", lambda t: (
        ...     t.id(),
        ...     t.string("title"),
        ...     t.text("body"),
        ...     t.timestamps()
        ... ))
    """

    def __init__(self, database: str = ":memory:", pool_size: int = 5):
        """
        Initialize database.

        Args:
            database: Database path or ":memory:"
            pool_size: Connection pool size
        """
        self.database = database
        self.conn_manager = ConnectionManager(database, pool_size)
        self.migrations = MigrationManager(self.conn_manager)

    def table(self, name: str) -> Table:
        """Get table interface."""
        return Table(self, name)

    def execute(self, sql: str, params: Optional[List[Any]] = None) -> int:
        """
        Execute SQL statement.

        Args:
            sql: SQL statement
            params: Query parameters

        Returns:
            Last row ID for INSERT, rows affected for UPDATE/DELETE
        """
        with self.conn_manager.transaction() as conn:
            cursor = conn.execute(sql, params or [])
            return cursor.lastrowid or cursor.rowcount

    def execute_many(self, sql: str, params_list: List[List[Any]]):
        """Execute SQL statement with multiple parameter sets."""
        with self.conn_manager.transaction() as conn:
            conn.executemany(sql, params_list)

    def fetch_one(self, sql: str, params: Optional[List[Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetch single result."""
        with self.conn_manager.connection() as conn:
            cursor = conn.execute(sql, params or [])
            row = cursor.fetchone()
            return dict(row) if row else None

    def fetch_all(self, sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """Fetch all results."""
        with self.conn_manager.connection() as conn:
            cursor = conn.execute(sql, params or [])
            return [dict(row) for row in cursor.fetchall()]

    def fetch_column(self, sql: str, params: Optional[List[Any]] = None) -> List[Any]:
        """Fetch first column of results."""
        with self.conn_manager.connection() as conn:
            cursor = conn.execute(sql, params or [])
            return [row[0] for row in cursor.fetchall()]

    def fetch_scalar(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        """Fetch single value."""
        with self.conn_manager.connection() as conn:
            cursor = conn.execute(sql, params or [])
            row = cursor.fetchone()
            return row[0] if row else None

    def create_table(self, name: str, definition: Callable[[SchemaBuilder], None]) -> bool:
        """
        Create a table using schema builder.

        Args:
            name: Table name
            definition: Function that defines schema

        Returns:
            True if successful
        """
        builder = SchemaBuilder(name)
        definition(builder)

        sql = builder.to_sql()
        self.execute(sql)

        # Create indexes
        for index_sql in builder.get_index_sql():
            self.execute(index_sql)

        return True

    def drop_table(self, name: str, if_exists: bool = True):
        """Drop a table."""
        exists = "IF EXISTS " if if_exists else ""
        self.execute(f"DROP TABLE {exists}{name}")

    def table_exists(self, name: str) -> bool:
        """Check if table exists."""
        result = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [name]
        )
        return result is not None

    def get_tables(self) -> List[str]:
        """Get list of all tables."""
        return self.fetch_column(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )

    def backup(self, filepath: str):
        """
        Backup database to file.

        Args:
            filepath: Backup file path
        """
        with self.conn_manager.connection() as conn:
            backup_conn = sqlite3.connect(filepath)
            conn.backup(backup_conn)
            backup_conn.close()

    def vacuum(self):
        """Vacuum database to reclaim space."""
        with self.conn_manager.connection() as conn:
            conn.execute("VACUUM")

    @contextmanager
    def transaction(self):
        """Transaction context manager."""
        with self.conn_manager.transaction() as conn:
            yield conn

    def close(self):
        """Close all connections."""
        self.conn_manager.close_all()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# =============================================================================
# DATA VALIDATION
# =============================================================================

class Validator:
    """
    Validate data before database operations.

    Example:
        >>> validator = Validator()
        >>> validator.add_rule("email", "required", "email")
        >>> validator.add_rule("age", "required", "integer", min=0, max=150)
        >>> errors = validator.validate({"email": "test", "age": -5})
    """

    def __init__(self):
        """Initialize validator."""
        self.rules: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}

    def add_rule(self, field: str, *rules: str, **options):
        """
        Add validation rules for a field.

        Args:
            field: Field name
            *rules: Rule names (required, email, integer, etc.)
            **options: Rule options (min, max, pattern, etc.)
        """
        if field not in self.rules:
            self.rules[field] = []

        for rule in rules:
            self.rules[field].append((rule, options))

    def validate(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate data against rules.

        Args:
            data: Data to validate

        Returns:
            Dictionary of field -> error messages
        """
        errors = {}

        for field, rules in self.rules.items():
            value = data.get(field)
            field_errors = []

            for rule_name, options in rules:
                error = self._check_rule(field, value, rule_name, options)
                if error:
                    field_errors.append(error)

            if field_errors:
                errors[field] = field_errors

        return errors

    def _check_rule(self, field: str, value: Any, rule: str, options: Dict[str, Any]) -> Optional[str]:
        """Check a single rule."""
        if rule == 'required':
            if value is None or value == '':
                return f"{field} is required"

        elif rule == 'email':
            if value and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(value)):
                return f"{field} must be a valid email"

        elif rule == 'integer':
            if value is not None:
                try:
                    int_val = int(value)
                    if 'min' in options and int_val < options['min']:
                        return f"{field} must be at least {options['min']}"
                    if 'max' in options and int_val > options['max']:
                        return f"{field} must be at most {options['max']}"
                except (ValueError, TypeError):
                    return f"{field} must be an integer"

        elif rule == 'string':
            if value is not None:
                str_val = str(value)
                if 'min' in options and len(str_val) < options['min']:
                    return f"{field} must be at least {options['min']} characters"
                if 'max' in options and len(str_val) > options['max']:
                    return f"{field} must be at most {options['max']} characters"

        elif rule == 'pattern':
            if value and 'pattern' in options:
                if not re.match(options['pattern'], str(value)):
                    return f"{field} format is invalid"

        elif rule == 'in':
            if value and 'values' in options:
                if value not in options['values']:
                    return f"{field} must be one of: {', '.join(map(str, options['values']))}"

        return None


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command-line interface for the Database Toolkit."""
    print("=" * 60)
    print("DATABASE TOOLKIT")
    print("=" * 60)
    print()

    # Create in-memory database for demo
    db = Database(":memory:")

    # Demo: Schema Builder
    print("1. SCHEMA BUILDER DEMO")
    print("-" * 40)

    db.create_table("users", lambda t: (
        t.id(),
        t.string("name", nullable=False),
        t.string("email", unique=True),
        t.integer("age"),
        t.boolean("active", default=True),
        t.timestamps(),
        t.index("name"),
        t.index("email", unique=True)
    ))

    db.create_table("posts", lambda t: (
        t.id(),
        t.integer("user_id", nullable=False),
        t.string("title"),
        t.text("body"),
        t.timestamps(),
        t.foreign("user_id", "users"),
        t.index("user_id")
    ))

    print("Created tables: users, posts")
    print(f"Tables in database: {db.get_tables()}")
    print()

    # Demo: Insert data
    print("2. INSERT DEMO")
    print("-" * 40)

    users = db.table("users")
    user1_id = users.insert({
        "name": "Alice",
        "email": "alice@example.com",
        "age": 30,
        "active": True,
        "created_at": datetime.now()
    })
    print(f"Inserted user with ID: {user1_id}")

    user2_id = users.insert({
        "name": "Bob",
        "email": "bob@example.com",
        "age": 25,
        "active": True
    })
    print(f"Inserted user with ID: {user2_id}")

    users.insert({"name": "Charlie", "email": "charlie@example.com", "age": 35, "active": False})
    print()

    # Demo: Query Builder
    print("3. QUERY BUILDER DEMO")
    print("-" * 40)

    # Select all
    all_users = users.all()
    print(f"All users ({len(all_users)}):")
    for user in all_users:
        print(f"  - {user['name']} ({user['email']})")

    # Select with conditions
    active_users = users.where("active", "=", True).all()
    print(f"\nActive users: {len(active_users)}")

    # Select with order and limit
    oldest = users.order_by("age", "DESC").limit(1).first()
    print(f"Oldest user: {oldest['name']} (age {oldest['age']})")

    # Count
    count = users.where("age", ">", 20).count()
    print(f"Users over 20: {count}")
    print()

    # Demo: Update
    print("4. UPDATE DEMO")
    print("-" * 40)

    updated = users.where("name", "=", "Bob").update({"age": 26})
    print(f"Updated {updated} record(s)")

    bob = users.where("name", "=", "Bob").first()
    print(f"Bob's new age: {bob['age']}")
    print()

    # Demo: Posts with foreign key
    print("5. FOREIGN KEY DEMO")
    print("-" * 40)

    posts = db.table("posts")
    posts.insert({
        "user_id": user1_id,
        "title": "First Post",
        "body": "This is Alice's first post"
    })
    posts.insert({
        "user_id": user1_id,
        "title": "Second Post",
        "body": "Another post by Alice"
    })
    posts.insert({
        "user_id": user2_id,
        "title": "Bob's Post",
        "body": "Hello from Bob"
    })

    # Join query
    qb = QueryBuilder("posts")
    sql, params = (qb
        .select("posts.title", "users.name as author")
        .join("users", "posts.user_id = users.id")
        .order_by("posts.id")
        .build())

    results = db.fetch_all(sql, params)
    print("Posts with authors:")
    for row in results:
        print(f"  '{row['title']}' by {row['author']}")
    print()

    # Demo: Raw SQL
    print("6. RAW SQL DEMO")
    print("-" * 40)

    result = db.fetch_all("""
        SELECT users.name, COUNT(posts.id) as post_count
        FROM users
        LEFT JOIN posts ON users.id = posts.user_id
        GROUP BY users.id
        ORDER BY post_count DESC
    """)
    print("Post counts per user:")
    for row in result:
        print(f"  {row['name']}: {row['post_count']} posts")
    print()

    # Demo: Validation
    print("7. VALIDATION DEMO")
    print("-" * 40)

    validator = Validator()
    validator.add_rule("email", "required", "email")
    validator.add_rule("age", "required", "integer", min=0, max=150)
    validator.add_rule("name", "required", "string", min=2, max=100)

    test_data = {"email": "invalid-email", "age": -5, "name": "A"}
    errors = validator.validate(test_data)
    print("Validation errors:")
    for field, field_errors in errors.items():
        for error in field_errors:
            print(f"  - {error}")
    print()

    # Demo: Delete
    print("8. DELETE DEMO")
    print("-" * 40)

    deleted = users.where("active", "=", False).delete()
    print(f"Deleted {deleted} inactive user(s)")
    print(f"Remaining users: {users.count()}")
    print()

    # Cleanup
    db.close()

    print("=" * 60)
    print("Database Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
