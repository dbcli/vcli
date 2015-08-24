Feature: run the cli,
  call the help command,
  exit the cli

  Scenario: run the cli without arguments
     Given we have vcli installed
      when we run vcli without arguments
      then we see vcli prompt

  Scenario: run the cli with url
      Given we have vcli installed
       when we run vcli with url
       then we see vcli prompt

  Scenario: run the cli with arguments
      Given we have vcli installed
       when we run vcli with arguments
       then we see vcli prompt

  Scenario: run the cli help
      Given we have vcli installed
       when we run vcli help
       then we see vcli help

  Scenario: run "\?" command
     Given we have vcli installed
      when we run vcli with url
      and we wait for prompt
      and we send "\?" command
      then we see help output

  Scenario: run "\h" command
     Given we have vcli installed
      when we run vcli without arguments
      and we wait for prompt
      and we send "\h" command
      then we see help output

  Scenario: run the cli and exit using "ctrl + d"
     Given we have vcli installed
      when we run vcli with url
      and we wait for prompt
      and we send "ctrl + d"
      then vcli exits

  Scenario: run the cli and exit using "\q"
     Given we have vcli installed
      when we run vcli with arguments
      and we wait for prompt
      and we send "\q" command
      then vcli exits
