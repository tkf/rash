-- Copyright (C) 2013-  Takafumi Arakaki

-- This program is free software: you can redistribute it and/or modify
-- it under the terms of the GNU General Public License as published by
-- the Free Software Foundation, either version 3 of the License, or
-- (at your option) any later version.

-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.

-- You should have received a copy of the GNU General Public License
-- along with this program.  If not, see <http://www.gnu.org/licenses/>.


DROP TABLE IF EXISTS command_history;
CREATE TABLE command_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  command_id INTEGER,
  session_id INTEGER,
  directory_id INTEGER,
  -- SOMEDAY: Remove terminal_id or move this to session_history table.
  -- See the comment in record_run (./record.py).
  terminal_id INTEGER,
  start_time TIMESTAMP,
  stop_time TIMESTAMP,
  exit_code INTEGER,
  FOREIGN KEY(command_id) REFERENCES command_list(id),
  FOREIGN KEY(session_id) REFERENCES session_history(id),
  FOREIGN KEY(directory_id) REFERENCES directory_list(id),
  FOREIGN KEY(terminal_id) REFERENCES terminal_list(id)
);

DROP TABLE IF EXISTS session_history;
CREATE TABLE session_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_long_id TEXT NOT NULL UNIQUE,
  start_time TIMESTAMP,
  stop_time TIMESTAMP
);

DROP TABLE IF EXISTS command_list;
CREATE TABLE command_list (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  command TEXT NOT NULL UNIQUE
);

DROP TABLE IF EXISTS terminal_list;
CREATE TABLE terminal_list (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  terminal TEXT NOT NULL UNIQUE
);

DROP TABLE IF EXISTS environment_variable;
CREATE TABLE environment_variable (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  variable_name TEXT NOT NULL,
  variable_value TEXT NOT NULL
);

DROP TABLE IF EXISTS directory_list;
CREATE TABLE directory_list (
  id INTEGER PRIMARY KEY autoincrement,
  directory TEXT NOT NULL UNIQUE
);

DROP TABLE IF EXISTS command_environment_map;
CREATE TABLE command_environment_map (
  ch_id INTEGER NOT NULL,
  ev_id INTEGER NOT NULL,
  FOREIGN KEY(ch_id) REFERENCES command_history(id),
  FOREIGN KEY(ev_id) REFERENCES environment_variable(id)
);

DROP TABLE IF EXISTS session_environment_map;
CREATE TABLE session_environment_map (
  sh_id INTEGER NOT NULL,
  ev_id INTEGER NOT NULL,
  FOREIGN KEY(sh_id) REFERENCES session_history(id),
  FOREIGN KEY(ev_id) REFERENCES environment_variable(id)
);

DROP TABLE IF EXISTS pipe_status_map;
CREATE TABLE pipe_status_map (
  ch_id INTEGER NOT NULL,
  program_position INTEGER NOT NULL,
  exit_code INTEGER,
  FOREIGN KEY(ch_id) REFERENCES command_history(id)
);

DROP TABLE IF EXISTS rash_info;
CREATE TABLE rash_info (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rash_version TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
