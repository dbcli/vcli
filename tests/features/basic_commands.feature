Feature: run the cli,
  call the help command,
  exit the cli

  Scenario: run the cli
     Given we have vcli installed
      when we run vcli
      then we see vcli prompt

  Scenario: run "\?" command
     Given we have vcli installed
      when we run vcli
      and we wait for prompt
      and we send "\?" command
      then we see help output

  Scenario: run "\h" command
     Given we have vcli installed
      when we run vcli
      and we wait for prompt
      and we send "\h" command
      then we see help output

  Scenario: run the cli and exit using "ctrl + d"
     Given we have vcli installed
      when we run vcli
      and we wait for prompt
      and we send "ctrl + d"
      then vcli exits

  Scenario: run the cli and exit using "\q"
     Given we have vcli installed
      when we run vcli
      and we wait for prompt
      and we send "\q" command
      then vcli exits
