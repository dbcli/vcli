Feature: manipulate tables:
  create, insert, update, select, delete from, drop

  @wip
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
