#!/bin/bash
/pwd/test/prepare-test-repos.sh
/pwd/logic/subuser subuser --accept add foo foo  > /dev/null 2> /dev/null
/pwd/logic/subuser subuser remove foo > /dev/null 2> /dev/null
/pwd/logic/subuser $@
