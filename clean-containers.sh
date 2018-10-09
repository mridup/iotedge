docker ps --filter status=dead --filter status=exited -aq | xargs -r docker rm -v
