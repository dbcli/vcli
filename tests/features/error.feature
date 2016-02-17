Feature: Humanized error messages

  Scenario: select from non-existing table
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we select from non-existing table
      then we see table not exists

  Scenario: syntax error
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we execute a query having syntax error
      then we see syntax error message
