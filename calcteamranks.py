import sys
import statistics
import json
import yadon

with open("config.json", "r") as file:
    config = json.load(file)

rank_by_zscore = config["algorithm"] == "zscore"
rank_by_nscore = config["algorithm"] == "nscore"
rank_by_cpmc = config["algorithm"] == "cpmc"

mappool = yadon.ReadTable("mappool")
users = yadon.ReadTable("users", named_columns=True)
scores = yadon.ReadTable("scores", named_columns=True)
team_scores = yadon.ReadTable("teamscores", named_columns=True)
teams = yadon.ReadTable("teams")
picks = [x[0] for x in mappool.values()]
pick_ranks_per_team = {} # team_name -> array of ranks on each pick
rank_sums = {} # team_name -> rank sum
zscore_sums = {} # team_name -> zscore sum
zscore_plays = {} # team_name -> # plays
nscore_sums = {} # team_name -> nscore sum
nscore_plays = {} # team_name -> # plays
max_scores = {}
cpmc_sums = {}
if rank_by_nscore:
    for map_id in mappool.keys():
        max_scores[map_id] = mappool[map_id][1]

for map_id in mappool.keys():
    pick = mappool[map_id][0]
    pick_rankings = {}
    
    try:
        ranking = sorted(team_scores.keys(), key=lambda team_name: int(team_scores[team_name][pick]) if team_scores[team_name][pick] else 0, reverse=True)
    except KeyError:
        print("sorting {} failed (it was never picked?)".format(pick))
        continue
    
    map_scores = [int(team_scores_2[pick]) if team_scores_2[pick] else 0 for team_scores_2 in team_scores.values()]
    if config["ignore_zero"]:
        map_scores = [map_score for map_score in map_scores if map_score != 0]
    if rank_by_zscore:
        mean = statistics.mean(map_scores)
        stdev = statistics.stdev(map_scores)
    
    current_score = 0
    current_rank = 1
    repeat = 1
    for i in range(len(ranking)):
        team_name = ranking[i]
        if team_name not in rank_sums.keys():
            rank_sums[team_name] = 0
            pick_ranks_per_team[team_name] = []
        score = team_scores[team_name][pick] if team_scores[team_name][pick] else 0
        if score == 0 and config["ignore_zero"]:
            pick_ranks_per_team[team_name].append(current_rank) # should be lowest rank
            continue
        zscore = (int(score) - mean) / stdev if rank_by_zscore else 0
        nscore = int(score) / int(max_scores[map_id]) if rank_by_nscore else 1000000
        cpmc = 0
        
        if int(score) == current_score:
            rank_sums[team_name] += current_rank
            pick_ranks_per_team[team_name].append(current_rank)
            key = str(current_rank) + "." + str(repeat)
            pick_rankings[key] = [team_name, score]
            if rank_by_zscore:
                pick_rankings[key].append("{:0.3f}".format(zscore))
            if rank_by_nscore:
                pick_rankings[key].append("{:0.3f}".format(nscore))
            if rank_by_cpmc:
                cpmc = 100 / (current_rank + (1.4 * len(mappool.keys())))
                #pick_rankings[key].append("{:0.3f}".format(cpmc))
            repeat += 1
        else:
            rank_sums[team_name] += i+1
            pick_ranks_per_team[team_name].append(i+1)
            key = str(i+1)
            pick_rankings[key] = [team_name, score]
            if rank_by_zscore:
                pick_rankings[key].append("{:0.3f}".format(zscore))
            if rank_by_nscore:
                pick_rankings[key].append("{:0.3f}".format(nscore))
            if rank_by_cpmc:
                cpmc = 100 / (i+1 + (1.4 * len(mappool.keys())))
                #pick_rankings[key].append("{:0.3f}".format(cpmc))
            current_score = int(score)
            current_rank = i+1
            repeat = 1
        
        if team_name not in zscore_sums.keys():
            zscore_sums[team_name] = 0
            zscore_plays[team_name] = 0
        zscore_sums[team_name] += zscore
        zscore_plays[team_name] += 1
        
        if team_name not in nscore_sums.keys():
            nscore_sums[team_name] = 0
            nscore_plays[team_name] = 0
        nscore_sums[team_name] += nscore
        nscore_plays[team_name] += 1
        
        if team_name not in cpmc_sums.keys():
            cpmc_sums[team_name] = 0
        cpmc_sums[team_name] += cpmc
    
    yadon.WriteTable(pick, pick_rankings)

def ranker(team_name):
    if rank_by_zscore:
        return zscore_sums[team_name] / zscore_plays[team_name]
    if rank_by_nscore:
        return nscore_sums[team_name] / nscore_plays[team_name]
    if rank_by_cpmc:
        return 1 / cpmc_sums[team_name]
    else:
        num_maps = len([x for x in team_scores[team_name].values() if x]) if config["ignore_zero"] else len(mappool.keys())
        avg = rank_sums[team_name] / num_maps
        total_score = sum([int(x) for x in team_scores[team_name].values() if x])
        return avg + 1 - (total_score / (10000000 * num_maps))

# array of team names sorted by their rank sum
overall_rankings = sorted(rank_sums.keys(), key=ranker, reverse=rank_by_zscore or rank_by_nscore)
# rank -> [team_name, rank_sum, total_score]
overall_rankings_2 = {}
# rank -> [team_name, rank_sum] + pick rankings
overall_rankings_3 = {}
for i in range(len(overall_rankings)):
    team_name = overall_rankings[i]
    num_maps = len([x for x in team_scores[team_name].values() if x]) if config["ignore_zero"] else len(mappool.keys())
    avg = rank_sums[team_name] / num_maps
    total_score = sum([int(x) for x in team_scores[team_name].values() if x])
    row = [team_name]
    if config["ignore_zero"]:
        avg_rank = rank_sums[team_name] / num_maps
        avg_score = total_score / num_maps
        row += [num_maps, "{:0.2f}".format(avg_rank), "{:0.2f}".format(avg_score)]
    else:
        row += [rank_sums[team_name], total_score]
    if rank_by_zscore:
        row += ["{:0.3f}".format(zscore_sums[team_name] / zscore_plays[team_name])]
    if rank_by_nscore:
        row += ["{:0.3f}".format(nscore_sums[team_name] / nscore_plays[team_name])]
    if rank_by_cpmc:
        row += ["{:0.3f}".format(cpmc_sums[team_name])]
    overall_rankings_2[str(i+1)] = row
    overall_rankings_3[str(i+1)] = [team_name, rank_sums[team_name]] + pick_ranks_per_team[team_name]

yadon.WriteTable("overall", overall_rankings_2)
yadon.WriteTable("rankings", overall_rankings_3)