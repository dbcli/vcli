Feature: manipulate schemas:
  create, drop, connect, disconnect

  Scenario: create and drop temporary schema
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we create schema
      then we see schema created
      when we drop schema
      then we see schema dropped
      when we send "ctrl + d"
      then vcli exits

  Scenario: connect and disconnect from test database
     Given we have vcli installed
      when we run vcli with url
      and we wait for prompt
      and we connect to database
      then we see database connected
      when we send "\q" command
      then vcli exits
