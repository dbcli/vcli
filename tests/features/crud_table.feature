Feature: manipulate tables:
  create, insert, update, select, delete from, drop

  Scenario: create, insert, select from, update, drop table
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we create schema
      then we see schema created
      when we create table
      then we see table created
      when we insert into table
      then we see record inserted
      when we update table
      then we see record updated
      when we delete from table
      then we see record deleted
      when we drop table
      then we see table dropped

  Scenario: redirect output to file and stdout
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we create schema
      then we see schema created
      when we create table
      then we see table created

      when we insert into table
      then we see record inserted

      when we switch output verbosity
      and we redirect output to file
      and we select from table
      and we wait for time prompt
      and we wait for prompt
      then we see result in file

      when we switch output verbosity
      and we redirect output to stdout
      and we select from table
      then we see result in stdout

  Scenario: redirect unicode output to file
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we create schema
      then we see schema created
      when we create table
      then we see table created

      when we switch output verbosity
      and we redirect output to file
      and we select unicode data
      and we wait for time prompt
      and we wait for prompt
      then wee see unicode result in file
