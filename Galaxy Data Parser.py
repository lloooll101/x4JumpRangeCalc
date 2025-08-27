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

pattern = r"connection_clustergate(\d{3})to(\d{3})"

parsedClusters = {}

for cluster in galaxyJson["data"]:
    clusterIDPattern = r"cluster_(\d+)_connection"
    clusterID = re.match(clusterIDPattern, cluster["name"].lower())
    
    if not clusterID:
        print(f"Warning: Cluster ID not found in cluster name '{cluster["qsnaAttributes"]["name"]}'")
        continue
    
    padClusterID = clusterID.group(1).zfill(3)
    
    clusterObject = {
        "id": padClusterID,
        "name": cluster["qsnaAttributes"]["name"],
        "dlc": cluster["qsnaAttributes"].get("dlc", "base"),
        "connections": [],
        "sectorNames": sorted([sector["qsnaAttributes"]["name"] for sector in cluster["sectors"]])
    }
    
    parsedClusters[padClusterID] = clusterObject
    
    for sector in cluster["sectors"]:
        for zone in sector["zones"]:
            for item in zone["items"]:
                if item["ref"] == "gates":
                    if item["name"] == "connection_ClusterGate031To601b":
                        clusterObject["connections"].append("601")
                    else:
                        match = re.fullmatch(pattern, item["name"].lower())
                        group1WithinRange = int(match.group(1)) > 0 and int(match.group(1)) < 800 if match else False
                        group2WithinRange = int(match.group(2)) > 0 and int(match.group(2)) < 800 if match else False
                        
                        if match and group1WithinRange and group2WithinRange:
                            clusterObject["connections"].append(match.group(2))
    
    clusterObject["connections"] = sorted(clusterObject["connections"])

print(f"Parsed {len(parsedClusters)} clusters.")

outputPath = os.path.join(scriptDir, "Parsed Clusters.json")
json.dump(parsedClusters, open(outputPath, 'w', encoding='utf-8'), indent=4)

print("Done")