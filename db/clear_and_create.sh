#!/bin/bash

rm -f db.sqlite3

cat << EOF | sqlite3 db.sqlite3
CREATE TABLE readings (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	datetime TEXT NOT NULL,
	name TEXT NOT NULL,
	value REAL NOT NULL
);
EOF
