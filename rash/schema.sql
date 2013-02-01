drop table if exists command_history;
create table command_history (
  id integer primary key autoincrement,
  command string not null,
  start_time integer,
  stop_time integer,
  exit_code integer,
  program string
);

drop table if exists environment_variable;
create table environment_variable (
  id integer primary key autoincrement,
  variable_name string not null,
  variable_value string not null
);

drop table if exists directory;
create table directory (
  id integer primary key autoincrement,
  directory_path string not null
);

drop table if exists command_environment_map;
create table command_environment_map (
  ch_id integer not null,
  ev_id integer not null
);

drop table if exists command_cwd_map;
create table command_cwd_map (
  ch_id integer not null,
  dir_id integer not null
);

drop table if exists pipe_status_map;
create table pipe_status_map (
  ch_id integer not null,
  position integer not null,
  exit_code integer
);

drop table if exists rash_info;
create table rash_info (
  rash_version string not null,
  schema_version string not null,
  updated timestamp default current_timestamp
);
