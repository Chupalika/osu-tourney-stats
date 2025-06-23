import re, sys
import requests
import json
import yadon

with open("config.json", "r") as file:
    config = json.load(file)

bracket = {}
bracket["Teams"] = []

mappool = yadon.ReadTable("mappool")
users = yadon.ReadTable("users", named_columns=True)
teams = yadon.ReadTable("teams")
overall_ranking = yadon.ReadTable("overall")

mod_rankings = {}
mod_maps = {}
for map_id in mappool.keys():
    pick = mappool[map_id][0]
    mod = re.sub(r"\d+", "", pick)
    if mod not in mod_rankings:
        mod_rankings[mod] = {}
        mod_maps[mod] = []
    mod_rankings_2 = mod_rankings[mod]
    mod_maps[mod].append(map_id)
    
    pick_rankings = yadon.ReadTable(pick)
    for rank in pick_rankings.keys():
        team_name = pick_rankings[rank][0]
        team_score = pick_rankings[rank][1]
        if team_name not in mod_rankings_2.keys():
            mod_rankings_2[team_name] = 0
        mod_rankings_2[team_name] += int(team_score)

for mod in mod_rankings.keys():
    mod_rankings_2 = mod_rankings[mod]
    mod_rankings_3 = sorted(mod_rankings_2.items(), key=lambda item: item[1], reverse=True)
    mod_rankings[mod] = mod_rankings_3

if not config["bracket_ignore_scores"]:
    team_ranks = overall_ranking.keys()
    team_names = [overall_ranking[rank][0] for rank in team_ranks]
else:
    team_names = teams.keys()

for team_name in team_names:
    rank = next(team_rank for team_rank in overall_ranking.keys() if overall_ranking[team_rank][0] == team_name) if not config["bracket_ignore_scores"] else 1
    team = {}
    team["FullName"] = team_name
    team["Seed"] = rank
    team["Players"] = []
    for i in range(len(teams[team_name])):
        player_name = teams[team_name][i]
        found = False
        for user_id in users.keys():
            if users[user_id]["username"] == player_name:
                player = {}
                player["id"] = user_id
                team["Players"].append(player)
                if i == 0:
                    team["FlagName"] = users[user_id]["country"]
                found = True
                break
        if not found:
            user = requests.get(url="https://osu.ppy.sh/api/get_user", params={"k": "aff27d4aea449fc489789148b4757726a469550b", "u": player_name, "m": "1"}).json()[0]
            users[user["user_id"]] = {"username": user["username"], "rank": user["pp_rank"], "country": user["country"]}
            yadon.WriteTable("users", users, named_columns=True)
            player = {}
            player["id"] = user["user_id"]
            team["Players"].append(player)
            if i == 0:
                team["FlagName"] = user["country"]
    team["SeedingResults"] = []
    if not config["bracket_ignore_scores"]:
        for mod in mod_rankings.keys():
            mod_rankings_2 = mod_rankings[mod]
            mod_results = {}
            for index in range(len(mod_rankings_2)):
                item = mod_rankings_2[index]
                if item[0] == team_name:
                    mod_results["Mod"] = mod
                    mod_results["Seed"] = index + 1
                    mod_results["Beatmaps"] = []
                    for map_id in mod_maps[mod]:
                        map_result = {}
                        map_result["ID"] = map_id
                        pick = mappool[map_id][0]
                        pick_rankings = yadon.ReadTable(pick)
                        for key, value in pick_rankings.items():
                            if value[0] == team_name:
                                map_result["Score"] = value[1]
                                map_result["Seed"] = key
                                break
                        mod_results["Beatmaps"].append(map_result)
                    break
            team["SeedingResults"].append(mod_results)
    bracket["Teams"].append(team)

with open("bracket.json", "w", encoding='utf8') as file:
    json.dump(bracket, file, ensure_ascii=False)