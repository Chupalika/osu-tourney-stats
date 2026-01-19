# osu-tourney-stats
Some personal scripts I used for providing many tournament stats.

## Instructions
Note: data is stored in **tsv** (tab separated values) format, which is useful for copying and pasting into spreadsheets!

1. Fill out the `api_key` field in `config.json` and set the `game_mode` field.
2. Fill out a `mappool.txt` with the map id followed by the slot label, separated by a tab - one pick on each line. (ex. `5145470	NM1`)
3. If your tourney has teams, fill out a `teams.txt` with team names followed by their members' usernames, all separated by tabs - one team on each line.
    * If your tourney is 1v1 but you need to generate a bracket using `bracket.py`, then you will still need a `teams.txt`, just have it like `playerName\tplayerName` on each row (where \t is tab)
4. Fetch scores from a lobby using `python dumpmpscores.py 118324259`. Score info will be stored in `scores.txt`, `teamscores.txt`, and `attributes.txt`. Can be edited if needed. User data will also be stored in `users.txt`.
5. Calculate stats using `python calcranks.py` or `python calcteamranks.py`. A bunch of txt files will be created that are named by each pick label in the mappool, along with `overall.txt` and `rankings.txt`.
6. To copy the stats into a spreadsheet, you can combine the stats into one file named `stats.txt` using `python combinestats.py`, then copy and paste.
7. Create a `bracket.json` for lazer using these stats by running `python bracket.py`. The generated file only includes the teams (for now, might be improved later), but the lazer tourney client should load it fine. If you want, you can copy the `Rounds`, `Matches`, and `Progressions` from one of my templates:
     * [Round of 16](https://www.dropbox.com/scl/fi/qvhq96jvtc1j4kicx13py/template_bracket_16.json?rlkey=lnb39fg54uyeqidqgj4at8qk1&dl=0)
     * [Round of 24](https://www.dropbox.com/scl/fi/3zuxkoukklscxeb47voyl/template_bracket_24.json?rlkey=xxf68wxlym4wrp6a28tify775&dl=0)
     * [Round of 32](https://www.dropbox.com/scl/fi/1pfroc1ok4x24nx28kc7c/template_bracket_32.json?rlkey=gyzw2nzhrmom3beh8nt3lsrbn&dl=0)

## Extra info
* If you get an error message that says something like "No module named requests", try running `python -m pip install requests` and then try again
* About `config.json`:
  * `ignore_zero` ignores 0 and missing scores from players/teams when calculating stats. This will also change `overall.txt` to show average rank instead of rank sum.
  * the `include_*` fields change what kind of stats are included in the output when running `calcranks.py`.
  * `algorithm` determines which algorithm to use for calculating the rankings. The current possible values are `default`, `zscore`, `nscore`, and `cpmc`.
  * `bracket_ignore_scores` skips including the stats and just includes team info when running `bracket.py`.
* About `yadon.py`: A thing I made for myself back in college to store data in TSV format in text files 😂 It was mainly for [SobbleDex](https://github.com/Chupalika/SobbleDex) but I've been using it for a lot of my other things since it's extremely lightweight.
* One thing to look out for is username changes. Individual scores won't be affected since they are attributed by user ID, but team scores will. After calculating stats, double check any suspiciously low scores :)
* If any scores need to be manually edited/added, it can be done in `scores.txt` or `teamscores.txt`, just be sure to re-run `calcranks` or `calcteamranks` after editing. If you are including attributes, you will need to manually edit `attributes.txt` also.
