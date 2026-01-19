import sys, requests
import json
import yadon

with open("config.json", "r") as file:
    config = json.load(file)

mpid = sys.argv[1]
mappool = yadon.ReadTable("mappool")
teams = yadon.ReadTable("teams")
users = yadon.ReadTable("users", named_columns=True)
if not users:
    users = {}
scores = yadon.ReadTable("scores", named_columns=True)
attributes = yadon.ReadTable("attributes", named_columns=True)
if not scores:
    scores = {}
    attributes = {}
team_scores = yadon.ReadTable("teamscores", named_columns=True)
if not team_scores:
    team_scores = {}
if teams:
    users_to_teams = {}
    for team in teams.keys():
        for member in teams[team]:
            users_to_teams[member] = team

def calculate_accuracy(score_data, mode):
    if mode == "0":
        raw_score = (int(score_data["count300"]) * 300) + (int(score_data["count100"]) * 100) + (int(score_data["count50"]) * 50)
        total_hits = int(score_data["count300"]) + int(score_data["count100"]) + int(score_data["count50"]) + int(score_data["countmiss"])
        accuracy = (raw_score * 100) / (total_hits * 300)
    if mode == "1":
        raw_score = (int(score_data["count300"]) * 300) + (int(score_data["count100"]) * 150)
        total_hits = int(score_data["count300"]) + int(score_data["count100"]) + int(score_data["countmiss"])
        accuracy = (raw_score * 100) / (total_hits * 300)
    if mode == "2":
        raw_score = int(score_data["count300"]) + int(score_data["count100"]) + int(score_data["count50"])
        total_hits = raw_score + int(score_data["countmiss"]) + int(score_data["countkatu"])
        accuracy = (raw_score * 100) / total_hits
    if mode == "3":
        raw_score = (int(score_data["countgeki"]) * 300) + (int(score_data["count300"]) * 300) + (int(score_data["countkatu"]) * 200) + (int(score_data["count100"]) * 100) + (int(score_data["count50"]) * 50)
        total_hits = int(score_data["countgeki"]) + int(score_data["count300"]) + int(score_data["countkatu"]) + int(score_data["count100"]) + int(score_data["count50"]) + int(score_data["countmiss"])
        accuracy = (raw_score * 100) / (total_hits * 300)
    return accuracy

def get_mods_from_int(flag):
    if flag is None:
        return []
    mod_codes = ["", "EZ", "", "HD", "HR", "", "DT", "", "HT", "NC", "FL"]
    raw_mods = "{0:032b}".format(int(flag))
    ans = []
    for i in range(len(mod_codes)):
        if raw_mods[i*-1-1] == "1":
            ans.append(mod_codes[i])
    if "NC" in ans:
        ans.remove("DT")
    if "PF" in ans:
        ans.remove("SD")
    return ans

match = requests.get(url="https://osu.ppy.sh/api/get_match", params={"k": config["api_key"], "mp": mpid}).json()
for game in match["games"]:
    map_id = game["beatmap_id"]
    if map_id not in mappool.keys():
        continue
    pick = mappool[map_id][0]
    global_mods = get_mods_from_int(game["mods"])
    if teams:
        team_scores_for_game = {}
    
    for score in game["scores"]:
        user_id = score["user_id"]
        user_score = score["score"]
        
        #store user info
        if user_id not in scores.keys():
            scores[user_id] = {}
            attributes[user_id] = {}
        if user_id not in users.keys():
            user = requests.get(url="https://osu.ppy.sh/api/get_user", params={"k": config["api_key"], "u": user_id, "m": config["game_mode"]}).json()[0]
            users[user_id] = {"username": user["username"], "rank": user["pp_rank"], "country": user["country"]}
        
        #store individual score info
        user_scores = scores[user_id]
        user_attributes = attributes[user_id]
        if pick not in user_scores or not user_scores[pick] or int(user_scores[pick]) < int(user_score):
            user_scores[pick] = user_score
            count_300 = int(score["count300"])
            count_100 = int(score["count100"])
            count_50 = int(score["count50"])
            count_0 = int(score["countmiss"])
            count_katu = int(score["countkatu"])
            count_geki = int(score["countgeki"])
            combo = int(score["maxcombo"])
            acc = calculate_accuracy(score, game["play_mode"])
            mods = list(set(global_mods + get_mods_from_int(score["enabled_mods"])))
            user_attributes[pick] = "{:0.2f}/{}/{}/{}/{}/{}/{}/{}/{}".format(acc, count_geki, count_300, count_katu, count_100, count_50, count_0, combo, "".join(mods))
        
        #store team score info if applicable
        if teams:
            try:
                team_name = users_to_teams[users[user_id]["username"]]
                if team_name not in team_scores_for_game.keys():
                    team_scores_for_game[team_name] = int(user_score)
                else:
                    team_scores_for_game[team_name] += int(user_score)
            except KeyError:
                pass
    
    if teams:
        for team_name in team_scores_for_game.keys():
            if team_name not in team_scores.keys():
                team_scores[team_name] = {}
            team_scores_2 = team_scores[team_name]
            team_score = team_scores_for_game[team_name]
            if pick not in team_scores_2 or not team_scores_2[pick] or int(team_scores_2[pick]) < team_score:
                team_scores_2[pick] = team_score

yadon.WriteTable("users", users, named_columns=True)
yadon.WriteTable("scores", scores, named_columns=True)
yadon.WriteTable("attributes", attributes, named_columns=True)
if teams:
    yadon.WriteTable("teamscores", team_scores, named_columns=True)