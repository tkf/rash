DROP TABLE IF EXISTS command_history;
CREATE TABLE command_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  command_id INTEGER,
  start_time TIMESTAMP,
  stop_time TIMESTAMP,
  exit_code INTEGER,
  terminal_id INTEGER,
  FOREIGN KEY(command_id) REFERENCES command_list(id),
  FOREIGN KEY(terminal_id) REFERENCES terminal_list(id)
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

DROP TABLE IF EXISTS command_cwd_map;
CREATE TABLE command_cwd_map (
  ch_id INTEGER NOT NULL,
  dir_id INTEGER NOT NULL,
  FOREIGN KEY(ch_id) REFERENCES command_history(id),
  FOREIGN KEY(dir_id) REFERENCES directory_list(id)
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
  rash_version TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
