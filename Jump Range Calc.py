import json
import os
import collections

class textColors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    END = '\033[0m'

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

    if start == end:
        return 0
    
    visited = set((start, 0))
    queue = collections.deque([(start, 0)])
    
    while queue:
        current, jumps = queue.popleft()
        if current == end:
            return jumps
        
        for neighbor in galaxyData[current]["connections"]:
            if not (neighbor in visited) and dlc.get(galaxyData[neighbor]["dlc"], False):
                visited.add(neighbor)
                queue.append((neighbor, jumps + 1))
    
    print(f"Error: Path between '{start}' and '{end}' was not found with current DLC settings.")
    return -1

def calculateJumpDistanceBidirectional(start: str, end: str, dlc: dict, galaxyData: dict) -> int:
    if start == end:
        return 0
    
    visitedF = {start: 0}
    queueF = collections.deque([(start, 0)])
    
    visitedB = {end: 0}
    queueB = collections.deque([(end, 0)])
    
    while queueF or queueB:
        if queueF and (queueF[0][1] <= queueB[0][1]):
            current, jumps = queueF.popleft()
        
            if current in visitedB:
                return jumps + visitedB[current]
            
            visitedF[current] = jumps
        
            for neighbor in galaxyData[current]["connections"]:
                if not (neighbor in visitedF) and dlc.get(galaxyData[neighbor]["dlc"], False):
                    if neighbor in visitedB:
                        return jumps + visitedB[neighbor] + 1
                    
                    visitedF[neighbor] = jumps + 1
                    queueF.append((neighbor, jumps + 1))
        
        elif queueB:
            current, jumps = queueB.popleft()
            
            if current in visitedF:
                return jumps + visitedF[current]
            
            visitedB[current] = jumps
            
            for neighbor in galaxyData[current]["connections"]:
                if not (neighbor in visitedB) and dlc.get(galaxyData[neighbor]["dlc"], False):
                    if neighbor in visitedF:
                        return jumps + visitedF[neighbor] + 1
                    
                    visitedB[neighbor] = jumps + 1
                    queueB.append((neighbor, jumps + 1))
    
    print(f"Error: Path between '{start}' and '{end}' was not found with current DLC settings.")
    return -1

def listClustersInRange(start: str, maxJumps: int, dlc: dict, galaxyData: dict) -> list:    
    visited = set()
    queue = collections.deque([(start, 0)])
    
    while queue:
        current, jumps = queue.popleft()
        
        visited.add(current)
        
        if jumps < maxJumps:
            for neighbor in galaxyData[current]["connections"]:
                if not (neighbor in visited) and dlc.get(galaxyData[neighbor]["dlc"], False):
                    queue.append((neighbor, jumps + 1))
        
    return list(visited)

def maxClustersInRange(maxJumps: int, dlc: dict, galaxyData: dict) -> dict:
    clustersInRange = {}
    
    for clusterID, clusterData in galaxyData.items():
        clustersInRange[clusterID] = len(listClustersInRange(clusterID, maxJumps, dlc, galaxyData))
    
    return dict(sorted(clustersInRange.items(), key=lambda item: item[1], reverse=True))

def allDistance(start: str, dlc: dict, galaxyData: dict) -> dict:
    distances = {start: 0}
    queue = collections.deque([(start, 0)])
    
    while queue:
        current, jumps = queue.popleft()
        
        for neighbor in galaxyData[current]["connections"]:
            if not (neighbor in distances) and dlc.get(galaxyData[neighbor]["dlc"], False):
                distances[neighbor] = jumps + 1
                queue.append((neighbor, jumps + 1))
    
    return distances
        
def findCenter(dlc: dict, galaxyData: dict) -> dict:
    maxDistances = {}
    
    for cluster in galaxyData.values():
        maxDistances[cluster["id"]] = max(allDistance(cluster["id"], dlc, galaxyData).values())
        
    return dict(sorted(maxDistances.items(), key=lambda item: item[1]))

def changeDLC(dlcJson: dict, savePath: object) -> dict:
    while True:
        print("Current DLC states:")
        for key, value in dlcJson.items():
            status = f"{textColors.GREEN}Enabled{textColors.END}" if value else f"{textColors.RED}Disabled{textColors.END}"
            print(f"{key.ljust(12)}: {status}")
            
        dlcInput = input("Enter DLC name to toggle or 'done': ").strip().lower()
        
        if dlcInput == "done":
            try:
                with open(savePath, 'w', encoding='utf-8') as f:
                    json.dump(dlcJson, f, indent=4)
                print("DLC settings saved.")
            except Exception as e:
                print(f"Error saving DLC settings: {e}")
            
            return dlcJson
        elif dlcInput in dlcJson:
            dlcJson[dlcInput] = not dlcJson[dlcInput]
        else:
            print("Invalid DLC. Please try again.")

def main():
    scriptDir = os.path.dirname(__file__)
    
    galaxyPath = os.path.join(scriptDir, "Parsed Clusters.json")
    galaxyJson = loadJsonFile(galaxyPath)
    
    dlcPath = os.path.join(scriptDir, "dlcData.json")
    dlcJson = loadJsonFile(dlcPath)
    
    if not galaxyJson or not dlcJson:
        print("Error: Required data files are missing. Exiting.")
        return
    
    clusterIDs = list(galaxyJson.keys())
    
    while True:
        print("\nMenu:")
        print("1. Change DLC settings")
        print("2. Calculate jump distance between two clusters")
        print("3. List clusters reachable within a certain number of jumps")
        print("4. Find clusters that can reach the most other clusters within a certain number of jumps")
        print("5. Calculate all distances from a starting cluster")
        print("6. Find the galaxy center (cluster with the smallest maximum distance to any other cluster)")
        print("exit. Exit the program")
        
        match input("Select an option or 'exit': ").strip().lower():
            case "1":
                dlcJson = changeDLC(dlcJson, dlcPath)
            
            case "2":
                startCluster = input("Enter start cluster ID: ").strip()
                endCluster = input("Enter end cluster ID: ").strip()
                if startCluster in clusterIDs and endCluster in clusterIDs:
                    dist = calculateJumpDistanceBidirectional(startCluster, endCluster, dlcJson, galaxyJson)
                    if dist != -1:
                        print(f"Jump distance from {startCluster} to {endCluster}: {dist} jumps.")
                    else:
                        print(f"Could not find a path between '{startCluster}' and '{endCluster}' with current DLC settings.")
                else:
                    print("Invalid cluster ID(s) entered. Please ensure both clusters exist.")
            
            case "3":
                startCluster = input("Enter start cluster ID: ").strip()
                try:
                    maxJumps = int(input("Enter maximum number of jumps: ").strip())
                    if maxJumps < 0:
                        raise ValueError
                except ValueError:
                    print("Invalid number of jumps. Please enter a non-negative integer.")
                    continue

                if startCluster in clusterIDs:
                    reachableClusters = listClustersInRange(startCluster, maxJumps, dlcJson, galaxyJson)
                    
                    if reachableClusters:
                        print(f"Found {len(reachableClusters)} clusters reachable from '{startCluster}' within {maxJumps} jumps.")
                        print("Reachable clusters:", ', '.join(sorted(reachableClusters)))
                    else:
                        print(f"No clusters reachable from '{startCluster}' within {maxJumps} jumps with current DLC settings.")
                else:
                    print("Invalid cluster ID entered.")
                
            case "4":
                try:
                    maxJumps = int(input("Enter maximum number of jumps for range calculation: ").strip())
                    if maxJumps < 0:
                        raise ValueError
                except ValueError:
                    print("Invalid number of jumps. Please enter a non-negative integer.")
                    continue
                
                result = maxClustersInRange(maxJumps, dlcJson, galaxyJson)
                
                if result:
                    print(f"Top clusters by reachability within {maxJumps} jumps (ID: count):")
                    
                    for clusterID, count in result.items():
                        print(f"{clusterID}: {count}")
                    print(f"(Total {len(result)} clusters processed)")
                else:
                    print("No clusters found or an error occurred with current DLC settings.")
            
            case "5":
                startCluster = input("Enter start cluster ID: ").strip()
                if startCluster in clusterIDs:
                    distances = allDistance(startCluster, dlcJson, galaxyJson)
                    
                    if distances:
                        sortedDistances = dict(sorted(distances.items(), key=lambda item: item[1]))
                        print(f"Distances from '{startCluster}' (Cluster ID: Jumps):")
                        for clusterID, dist in sortedDistances.items(): # Print top 10 closest
                             print(f"{clusterID}: {dist}")
                        if distances: # Check again if distances is not empty
                            print(f"(Total {len(sortedDistances)} clusters reached. Maximum distance: {max(distances.values())})")
                    else:
                        print(f"No reachable clusters from '{startCluster}' with current DLC settings.")
                else:
                    print("Invalid cluster ID entered.")
            
            case "6":
                centerResult = findCenter(dlcJson, galaxyJson)
                
                if centerResult:
                    print("Galaxy center(s) based on minimum maximum distance to any other cluster (ID: maxDistance):")
                    for clusterID, maxDist in centerResult.items():
                        print(f"{clusterID}: {maxDist}")
                    print(f"(Total {len(centerResult)} clusters analyzed)")
                else:
                    print("Could not determine the galaxy center with current DLC settings (perhaps no clusters are reachable).")
            case "exit":
                print("Exiting program.")
                break
            case _:
                print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()