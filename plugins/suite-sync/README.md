# suite-sync

Makes `suite` the list of everything enabled at user scope. On each session start it:

1. Sets `extraKnownMarketplaces.suite.autoUpdate = true` in user settings, so Claude Code pulls new commits.
2. Runs `claude plugin install <name>@suite --scope user` for every listed plugin not yet in `enabledPlugins`.

To opt out of one plugin, set `"<name>@suite": false` in `enabledPlugins`; suite-sync never re-enables it. Plugins installed mid-session load after `/reload-plugins`. Claude Code only.
