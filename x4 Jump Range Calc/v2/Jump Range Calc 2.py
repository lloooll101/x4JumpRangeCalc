import json
import os
import collections
import networkx
import matplotlib

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

def createGraphClusters(dlc: dict, galaxyJson: dict) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    
    for clusterID, cluster in galaxyJson.items():
        if not dlc[cluster["dlc"]]: continue
            
        for sectorID, sector in cluster["sectors"].items():
            graph.add_node((clusterID, sectorID))
    
    for clusterID, cluster in galaxyJson.items():
        if not dlc[cluster["dlc"]]: continue
        
        for sectorID, sector in cluster["sectors"].items():
            for gate in sector["gates"]:
                if not dlc[galaxyJson[gate["destCluster"]]["dlc"]]: continue
                
                graph.add_edge((clusterID, sectorID), (gate["destCluster"], gate["destSector"]), weight=1)
            for superhighway in sector["superhighways"]:
                graph.add_edge((clusterID, sectorID), (clusterID, superhighway), weight=0)
                
    return graph

def createGraphSectors(dlc: dict, galaxyJson: dict) -> networkx.DiGraph:
    graph = networkx.DiGraph()
    
    for clusterID, cluster in galaxyJson.items():
        if not dlc[cluster["dlc"]]: continue
            
        for sectorID, sector in cluster["sectors"].items():
            graph.add_node((clusterID, sectorID))
    
    for clusterID, cluster in galaxyJson.items():
        if not dlc[cluster["dlc"]]: continue
        
        for sectorID, sector in cluster["sectors"].items():
            for gate in sector["gates"]:
                if not dlc[galaxyJson[gate["destCluster"]]["dlc"]]: continue
                
                graph.add_edge((clusterID, sectorID), (gate["destCluster"], gate["destSector"]), weight=1)
            for superhighway in sector["superhighways"]:
                graph.add_edge((clusterID, sectorID), (clusterID, superhighway), weight=1)
                
    return graph

def distanceBetweenSectors(graph: networkx.DiGraph, startNode, endNode) -> float:
    if startNode not in graph or endNode not in graph:
        raise networkx.NodeNotFound("Source or target node not in graph.")
    
    try:
        distance = networkx.dijkstra_path_length(graph, startNode, endNode, weight='weight')
        return distance
    except networkx.NetworkXNoPath:
        return -1

def pathLengths(graph: networkx.DiGraph, startNode: tuple) -> dict:
    if startNode not in graph:
        raise networkx.NodeNotFound(f"Node {startNode} not in graph.")
    
    output = networkx.single_source_dijkstra_path_length(graph, startNode, weight='weight')
    
    return dict(sorted(output.items(), key=lambda item: (item[1], item[0])))

def allPathLengths(graph: networkx.DiGraph) -> dict:
    output = {}
    for node in graph.nodes:
        output[node] = max(pathLengths(graph, node).values())
        
    return dict(sorted(output.items(), key=lambda item: item[1]))

def cutoffPathLengths(graph: networkx.DiGraph, startNode: tuple, maxDistance: float) -> dict:
    if startNode not in graph:
        raise networkx.NodeNotFound(f"Node {startNode} not in graph.")
    
    return networkx.single_source_dijkstra_path_length(graph, startNode, cutoff=maxDistance, weight='weight')

def findMaxClustersInRange(graph: networkx.DiGraph, maxDistance: float) -> dict:
    output = {}
    for node in graph.nodes:
        output[node] = len(cutoffPathLengths(graph, node, maxDistance))
        
    return dict(sorted(output.items(), key=lambda item: item[1], reverse=True))

def getSectorName(galaxyJson: dict, sectorTuple: tuple) -> str:
    return galaxyJson[sectorTuple[0]]["sectors"][sectorTuple[1]]["name"]

def getSectorTuple(galaxyJson: dict, sectorName: str) -> tuple:
    for clusterID, cluster in galaxyJson.items():
        for sectorID, sector in cluster["sectors"].items():
            if sector["name"] == sectorName:
                return (clusterID, sectorID)
            
    raise ValueError(f"Sector '{sectorName}' not found in galaxy JSON.")

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
    print("Loading files...")
    scriptDir = os.path.dirname(__file__)
    
    galaxyPath = os.path.join(scriptDir, "Parsed Clusters 2.json")
    galaxyJson = loadJsonFile(galaxyPath)
    
    dlcPath = os.path.join(scriptDir, "dlcData.json")
    dlcJson = loadJsonFile(dlcPath)
    
    if not galaxyJson or not dlcJson:
        print("Error: Required data files are missing. Exiting.")
        return
    
    print("Files Loaded.")
    
    countSuperhighways = False
    
    print("Creating galaxy network...")
    graphClusters = createGraphClusters(dlcJson, galaxyJson)
    graphSectors = createGraphSectors(dlcJson, galaxyJson)
    
    print("Galaxy network created.")
    
    while True:
        print("\nMenu:")
        print("1. Change DLC settings")
        print("2. Calculate distance between two sectors")
        print("3. Calculate distance to all sectors from a starting sector")
        print("4. Show the distance to the furthest sector using each sector as a starting point")
        print("5. Calculate the clusters within a certain range of a starting sector")
        print("6. Show the number of sectors within a certain range of a starting sector")
        print("exit. Exit the program")
        
        match input("Select an option or 'exit': ").strip().lower():
            case "1":
                dlcJson = changeDLC(dlcJson, dlcPath)
                graphClusters = createGraphClusters(dlcJson, galaxyJson)
                graphSectors = createGraphSectors(dlcJson, galaxyJson)
            
            case "2":
                print()
                
                startSector = ""
                endSector = ""
                
                while(True):
                    try:
                        startSector = getSectorTuple(galaxyJson, input("Please input the name of the starting sector: "))
                        break
                    except ValueError as e:
                        print(e)
                        
                while(True):
                    try:
                        endSector = getSectorTuple(galaxyJson, input("Please input the name of the ending sector: "))
                        break
                    except ValueError as e:
                        print(e)
                
                dist = distanceBetweenSectors(graphSectors if countSuperhighways else graphClusters, startSector, endSector)
                print(f"Distance from '{getSectorName(galaxyJson, startSector)}' to '{getSectorName(galaxyJson, endSector)}' is {dist}")
            
            case "3":
                print()
                
                startSector = ""
                
                while(True):
                    try:
                        startSector = getSectorTuple(galaxyJson, input("Please input the name of the starting sector: "))
                        break
                    except ValueError as e:
                        print(e)
                
                dist = pathLengths(graphSectors if countSuperhighways else graphClusters, startSector)
                
                length  = max([len(getSectorName(galaxyJson, sectorTuple)) for sectorTuple, distance in dist.items()])
                print("Distances to each sector:")
                
                for sectorTuple, distance in dist.items():
                    print(f"{str.ljust(getSectorName(galaxyJson, sectorTuple), length)}: {distance}")
                    
            case "4":
                print()
                
                dist = allPathLengths(graphSectors if countSuperhighways else graphClusters)
                
                length  = max([len(getSectorName(galaxyJson, sectorTuple)) for sectorTuple, distance in dist.items()])
                print("Distances to furthest sector from each sector:")
                
                for sectorTuple, distance in dist.items():
                    print(f"{str.ljust(getSectorName(galaxyJson, sectorTuple), length)}: {distance}")
                    
            case "5":
                print()
                
                startSector = ""
                maxDistance = 0
                
                while(True):
                    try:
                        startSector = getSectorTuple(galaxyJson, input("Please input the name of the starting sector: "))
                        break
                    except ValueError as e:
                        print(e)
                
                while(True):
                    try:
                        maxDistance = int(input("Please input the max range from the starting sector to check: "))
                        break
                    except ValueError as e:
                        print("Value was not an integer, please try again.")
                
                sectors = cutoffPathLengths(graphSectors if countSuperhighways else graphClusters, startSector, maxDistance)
                
                print(f"Number of sectors within a distance of {maxDistance} from '{getSectorName(galaxyJson, startSector)}':")
                
                for sectorTuple, distance in sectors.items():
                    print(f"{getSectorName(galaxyJson, sectorTuple)}")
                    
                print(f"\nTotal Number of sectors: {len(sectors)}")
            
            case "6":
                print()
                
                maxDistance = 0
                
                while(True):
                    try:
                        maxDistance = int(input("Please input the max range from the starting sector to check: "))
                        break
                    except ValueError as e:
                        print("Value was not an integer, please try again.")
                
                sectors = findMaxClustersInRange(graphSectors if countSuperhighways else graphClusters, maxDistance)
                
                length  = max([len(getSectorName(galaxyJson, sectorTuple)) for sectorTuple, distance in sectors.items()])
                print(f"Number of sectors within a range of {maxDistance} from the starting sector:")
                
                for sectorTuple, number in sectors.items():
                    print(f"{str.ljust(getSectorName(galaxyJson, sectorTuple), length)}: {number}")
            
            case "exit":
                print("Exiting program.")
                break
            case _:
                print("Invalid option. Please try again.")
    

if __name__ == "__main__":
    main()