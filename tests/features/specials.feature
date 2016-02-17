Feature: Special commands

  Scenario: run refresh command
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we refresh completions
      and we wait for prompt
      then we see completions refresh started
