import sys
import statistics
import json
import yadon

with open("config.json", "r") as file:
    config = json.load(file)

rank_by_zscore = config["algorithm"] == "zscore"

mappool = yadon.ReadTable("mappool")
users = yadon.ReadTable("users", named_columns=True)
scores = yadon.ReadTable("scores", named_columns=True)
attributes = yadon.ReadTable("attributes", named_columns=True)
rank_sums = {} # user_id -> rank sum
pick_ranks_per_player = {} # user_id -> array of ranks on each pick
if config["include_pp_rank"]:
    users_by_pp_rank = sorted(users.keys(), key=lambda user_id: int(users[user_id]["rank"]))
if config["include_team"]:
    team_by_player = {}
    teams = yadon.ReadTable("teams")
    for team_name, player_names in teams.items():
        for player_name in player_names:
            team_by_player[player_name] = team_name
zscore_sums = {} # user_id -> zscore sum
zscore_plays = {} # user_id -> # plays

for map_id in mappool.keys():
    pick = mappool[map_id][0]
    pick_rankings = {} # rank -> [username, score] + optional attributes
    
    try:
        # array of user IDs sorted by their scores on this pick
        ranking = sorted(scores.keys(), key=lambda user_id: int(scores[user_id][pick]) if scores[user_id][pick] else 0, reverse=True)
    except KeyError:
        print("sorting {} failed (it was never picked?)".format(pick))
        continue
    
    map_scores = [int(user_scores[pick]) if user_scores[pick] else 0 for user_scores in scores.values()]
    if config["ignore_zero"]:
        map_scores = [map_score for map_score in map_scores if map_score != 0]
    mean = statistics.mean(map_scores)
    stdev = statistics.stdev(map_scores) if rank_by_zscore else 1
    
    current_score = 0
    current_rank = 1
    repeat = 1
    for i in range(len(ranking)):
        user_id = ranking[i]
        user = users[user_id]
        username = user["username"]
        score = scores[user_id][pick] if scores[user_id][pick] else 0
        if attributes and attributes[user_id]:
            score_attributes = attributes[user_id][pick] if scores[user_id][pick] else "0/0/0/0/0/0/0/0/"
        else:
            score_attributes = "0/0/0/0/0/0/0/0/"
        if user_id not in rank_sums.keys():
            rank_sums[user_id] = 0
            pick_ranks_per_player[user_id] = []
        if int(score) == 0 and config["ignore_zero"]:
            pick_ranks_per_player[user_id].append(current_rank) # should be lowest rank
            continue
        initial_values = [username]
        if config["include_team"]:
            try:
                team_name = team_by_player[username]
                initial_values.append(team_name)
            except KeyError:
                initial_values.append("")
        zscore = (int(score) - mean) / stdev
        
        if int(score) == current_score:
            rank_sums[user_id] += current_rank
            pick_ranks_per_player[user_id].append(current_rank)
            key = str(current_rank) + "." + str(repeat)
            pick_rankings[key] = initial_values + [score]
            
            #include attributes
            acc, count_geki, count_300, count_katu, count100, count_50, count_miss, combo, mods = score_attributes.split("/")
            if config["include_geki_count"]:
                pick_rankings[key].append(count_geki)
            if config["include_300_count"]:
                pick_rankings[key].append(count_300)
            if config["include_katu_count"]:
                pick_rankings[key].append(count_katu)
            if config["include_100_count"]:
                pick_rankings[key].append(count_100)
            if config["include_50_count"]:
                pick_rankings[key].append(count_50)
            if config["include_miss_count"]:
                pick_rankings[key].append(count_miss)
            if config["include_combo"]:
                pick_rankings[key].append(combo)
            if config["include_mods"]:
                pick_rankings[key].append(mods)
            
            if rank_by_zscore:
                pick_rankings[key].append("{:0.3f}".format(zscore))
            if config["include_pp_rank"]:
                pick_rankings[key] += [user["rank"], user["country"], users_by_pp_rank.index(user_id) - current_rank + 1]
            
            repeat += 1
        else:
            rank_sums[user_id] += i+1
            pick_ranks_per_player[user_id].append(i+1)
            key = str(i+1)
            pick_rankings[key] = initial_values + [score]
            
            #include attributes
            acc, count_geki, count_300, count_katu, count_100, count_50, count_miss, combo, mods = score_attributes.split("/")
            if config["include_geki_count"]:
                pick_rankings[key].append(count_geki)
            if config["include_300_count"]:
                pick_rankings[key].append(count_300)
            if config["include_katu_count"]:
                pick_rankings[key].append(count_katu)
            if config["include_100_count"]:
                pick_rankings[key].append(count_100)
            if config["include_50_count"]:
                pick_rankings[key].append(count_50)
            if config["include_miss_count"]:
                pick_rankings[key].append(count_miss)
            if config["include_combo"]:
                pick_rankings[key].append(combo)
            if config["include_mods"]:
                pick_rankings[key].append(mods)

            if rank_by_zscore:
                pick_rankings[key].append("{:0.3f}".format(zscore))
            if config["include_pp_rank"]:
                pick_rankings[key] += [user["rank"], user["country"], users_by_pp_rank.index(user_id) - i]
            
            current_score = int(score)
            current_rank = i+1
            repeat = 1
        
        if user_id not in zscore_sums.keys():
            zscore_sums[user_id] = 0
            zscore_plays[user_id] = 0
        zscore_sums[user_id] += zscore
        zscore_plays[user_id] += 1
    
    yadon.WriteTable(pick, pick_rankings)

def ranker(user_id):
    if rank_by_zscore:
        return zscore_sums[user_id] / zscore_plays[user_id]
    num_maps = len([x for x in scores[user_id].values() if x]) if config["ignore_zero"] else len(mappool.keys())
    avg = rank_sums[user_id] / num_maps
    total_score = sum([int(x) for x in scores[user_id].values() if x])
    return avg + 1 - (total_score / 1000000000)

# array of user IDs sorted by their rank sum
overall_rankings = sorted(rank_sums.keys(), key=ranker, reverse=rank_by_zscore)
# rank -> [username, rank_sum, total_score] + optional attributes
overall_rankings_2 = {}
# rank -> [username, rank_sum] + pick rankings
overall_rankings_3 = {}

for i in range(len(overall_rankings)):
    user_id = overall_rankings[i]
    user = users[user_id]
    num_maps = len([x for x in scores[user_id].values() if x]) if config["ignore_zero"] else len(mappool.keys())
    total_score = sum([int(x) for x in scores[user_id].values() if x])
    row = [user["username"]]
    if config["include_team"]:
        try:
            team_name = team_by_player[user["username"]]
            row += [team_name]
        except KeyError:
            row += [""]
    if config["ignore_zero"]:
        avg_rank = rank_sums[user_id] / num_maps
        avg_score = total_score / num_maps
        row += [num_maps, "{:0.2f}".format(avg_rank), "{:0.2f}".format(avg_score)]
    else:
        row += [rank_sums[user_id], total_score]
    if rank_by_zscore:
        row += ["{:0.3f}".format(zscore_sums[user_id] / zscore_plays[user_id])]
    if config["include_pp_rank"]:
        row += [user["rank"], user["country"], users_by_pp_rank.index(user_id) + 1, users_by_pp_rank.index(user_id) - i]
    overall_rankings_2[str(i+1)] = row
    overall_rankings_3[str(i+1)] = [user["username"], rank_sums[user_id]] + pick_ranks_per_player[user_id]

yadon.WriteTable("overall", overall_rankings_2)
yadon.WriteTable("rankings", overall_rankings_3)