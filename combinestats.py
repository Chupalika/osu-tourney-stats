import yadon

mappool = yadon.ReadTable("mappool")
maprankings = []
rowcount = 0
columncount = 0
for id in mappool.keys():
    pick = mappool[id][0]
    pickrankings = yadon.ReadTable(pick) or {}
    if pickrankings:
        columncount = len(list(pickrankings.values())[0]) + 1
    maprankings.append([[k] + v for k,v in pickrankings.items()])
    rowcount = max(rowcount, len(pickrankings.keys()))
overallrankings = yadon.ReadTable("overall")
rowcount = max(rowcount, len(overallrankings.keys()))
overallrankings = [[k] + v for k,v in overallrankings.items()]

table = {}
counter = 1
while counter <= rowcount:
    key = overallrankings[counter-1][0] if len(overallrankings) >= counter else str(counter)
    value = overallrankings[counter-1][1:] if len(overallrankings) >= counter else ["" for x in overallrankings[0][1:]]
    for maprankings2 in maprankings:
        if len(maprankings2) > 0:
            value += maprankings2[counter-1] if len(maprankings2) >= counter else ["" for x in range(columncount)]
        else:
            value += ["" for x in range(columncount)]
    table[key] = value
    counter += 1
yadon.WriteTable("stats", table)