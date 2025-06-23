# osu-tourney-stats
Some personal scripts I used for providing many tournament stats.

## Instructions
Note: data is stored in **tsv** (tab separated values) format, which is useful for copying and pasting into spreadsheets!

1. Fill out the `api_key` field in `config.json`.
2. Fill out a `mappool.txt` with the pick label followed by the map id, separated by a tab - one pick on each line. (ex. `NM1	5145470`)
3. If your tourney has teams, fill out a `teams.txt` with team names followed by their members' usernames, all separated by tabs - one team on each line.
4. Fetch scores from a lobby using `python dumpmpscores.py 118324259`. Score info will be stored in `scores.txt`, `teamscores.txt`, and `attributes.txt`. Can be edited if needed. User data will also be stored in `users.txt`.
5. Calculate stats using `python calcranks.py` or `python calcteamranks.py`. A bunch of txt files will be created that are named by each pick label in the mappool, along with `overall.txt` and `rankings.txt`.
6. Combine the stats into one file named `stats.txt` using `python combinestats.py` for copying into a spreadsheet.
7. Create a `bracket.json` for lazer using these stats by running `python bracket.py`.

## Extra info
* About `config.json`:
  * `ignore_zero` ignores 0 and missing scores from players/teams when calculating stats. This will also change `overall.txt` to show average rank instead of rank sum.
  * the `include_*` fields change what kind of stats are included in the output when running `calcranks.py`.
  * `algorithm` determines which algorithm to use for calculating the rankings. The current possible values are `default`, `zscore`, `nscore`, and `cpmc`.
  * `bracket_ignore_scores` skips including the stats and just includes team info when running `bracket.py`.
* About `yadon.py`: A thing I made for myself back in college to store data in TSV format in text files 😂 It was mainly for [SobbleDex](https://github.com/Chupalika/SobbleDex) but I've been using it for a lot of my other things since it's extremely lightweight.
