import os
import json
import re

def loadJsonFile(filepath: str) -> dict:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Check file format.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None
    
scriptDir = os.path.dirname(__file__)
galaxyJsonName = "Galaxy Data.json"
galaxyJsonPath = os.path.join(scriptDir, galaxyJsonName)

galaxyJson = loadJsonFile(galaxyJsonPath)

parsedClusters = {}

gatesRef = {}

#Create base structure and fill in cluster destinations for gates
for cluster in galaxyJson["data"]:
    clusterIDPattern = r"cluster_(\d+)_connection"
    clusterID = re.match(clusterIDPattern, cluster["name"].lower())
    
    clusterID = clusterID.group(1).zfill(3)
    
    clusterObject = {
        "id": clusterID,
        "name": cluster["qsnaAttributes"]["name"],
        "dlc": cluster["qsnaAttributes"].get("dlc", "base"),
        "sectors": {},
    }
    
    for sector in cluster["sectors"]:
        sectorIDPattern = r"cluster_\d+_sector(\d+)_macro"
        sectorID = re.match(sectorIDPattern, sector["name"].lower())
        
        sectorID = sectorID.group(1).zfill(3)
        
        sectorObject = {
            "id": sectorID,
            "name": sector["qsnaAttributes"]["name"],
            "gates": [],
            "superhighways": []
        }
        
        for zone in sector["zones"]:
            for item in zone["items"]:
                if item.get("ref", None) == "gates":
                    gateName = item["name"]
                    
                    if gateName == "connection_ClusterGate031To601b":
                        sectorObject["gates"].append({"destCluster": "601", "destSector": None})
                        gatesRef[(clusterID, "601")] = sectorID
                    else:
                        gatePattern = r"connection_clustergate(\d{3})to(\d{3})"
                        match = re.fullmatch(gatePattern, gateName.lower())
                        
                        if not match: continue
                        
                        sourceCluster = match.group(1)
                        destCluster = match.group(2)
                        
                        if 0 < int(sourceCluster) < 800 and 0 < int(destCluster) < 800:
                            sectorObject["gates"].append({"destCluster": destCluster, "destSector": None})
                            gatesRef[(clusterID, destCluster)] = sectorID
        
        clusterObject["sectors"][sectorID] = sectorObject
    
    parsedClusters[clusterID] = clusterObject

for clusterID, cluster in parsedClusters.items():
    sectorIDs = list(cluster["sectors"].keys())
    if cluster["name"] == "Savage Spur":
        cluster["sectors"]["001"]["superhighways"].append("002")
    elif len(sectorIDs) == 2:
        sector1ID = sectorIDs[0]
        sector2ID = sectorIDs[1]
        
        cluster["sectors"][sector1ID]["superhighways"].append(sector2ID)
        cluster["sectors"][sector2ID]["superhighways"].append(sector1ID)
    elif len(sectorIDs) == 3:
        print(f"Three sectors in: {cluster["name"]}, please fill in superhighways manually.")

for clusterID, cluster in parsedClusters.items():
    for sectorID, sector in cluster["sectors"].items():
        for gate in sector["gates"]:
            
            gate["destSector"] = gatesRef.get((gate["destCluster"], clusterID), None)

print(f"Parsed {len(parsedClusters)} clusters.")

outputPath = os.path.join(scriptDir, "Parsed Clusters 2.json")
#json.dump(parsedClusters, open(outputPath, 'w', encoding='utf-8'), indent=4)

print("Done")