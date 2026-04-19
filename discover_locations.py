import asyncio
import json
import os
import sys

# Add the current directory to sys.path so we can import the travel package
sys.path.append(os.getcwd())

from travel.client import TravelClient
import logging

# Configure logging to see progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def discover_all():
    async with TravelClient() as client:
        # Load seeding provinces
        with open("provinces.json", "r", encoding="utf-8") as f:
            province_names = json.load(f)
        
        all_data = {
            "provinces": [],
            "districts": [],
            "airports": [],
            "train_stations": []
        }
        
        processed_ids = set()
        
        logger.info(f"Starting discovery for {len(province_names)} provinces...")
        
        for name in province_names:
            try:
                # Step 1: Search for the province
                areas = await client.search_areas(name)
                if not areas:
                    logger.warning(f"No results for province: {name}")
                    continue
                    
                # Filter for Type 3 (Province)
                province_area = None
                for a in areas:
                    if str(a.get("type")) == "3":
                        province_area = a
                        break
                
                if not province_area:
                    province_area = areas[0]
                    
                province_id = province_area["id"]
                
                if province_id in processed_ids:
                    continue
                
                logger.info(f"Processing Province: {province_area['name']} (ID: {province_id})")
                
                # Step 2: Get full details for this province
                details = await client.get_area_details(province_id)
                if not details:
                    continue
                    
                all_data["provinces"].append({
                    "id": details["id"],
                    "name": details["name"],
                    "code": details.get("code"),
                    "type": details.get("type")
                })
                processed_ids.add(province_id)
                
                # Step 3: Extract children (Districts)
                for child in details.get("children_areas", []):
                    child_id = child["id"]
                    if child_id not in processed_ids:
                        all_data["districts"].append({
                            "id": child_id,
                            "name": child["name"],
                            "parent_id": province_id,
                            "type": child.get("type")
                        })
                        processed_ids.add(child_id)
                
                # Step 4: Extract Airports
                for airport in details.get("airports", []):
                    # Airports in the API response are often GeoJSON features
                    props = airport.get("properties", {})
                    airport_id = props.get("VxrAreaId") or airport.get("id")
                    if airport_id and airport_id not in processed_ids:
                        all_data["airports"].append({
                            "id": airport_id,
                            "iata": props.get("IATA_FAA") or props.get("ICAO"),
                            "name": props.get("AirportName_Vi") or props.get("name"),
                            "city": props.get("CityName_Vi"),
                            "province_id": province_id
                        })
                        processed_ids.add(airport_id)
                
                # Step 5: Extract Train Stations
                for station in details.get("train_stations", []):
                    station_id = station["id"]
                    if station_id not in processed_ids:
                        all_data["train_stations"].append({
                            "id": station_id,
                            "code": station["code"],
                            "name": station["name"],
                            "province_id": province_id
                        })
                        processed_ids.add(station_id)
                        
                # Brief pause to be polite to the API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {name}: {e}")

        # Save the results
        output_file = "all_locations.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Discovery complete! Found:")
        logger.info(f"- {len(all_data['provinces'])} Provinces")
        logger.info(f"- {len(all_data['districts'])} Districts")
        logger.info(f"- {len(all_data['airports'])} Airports")
        logger.info(f"- {len(all_data['train_stations'])} Train Stations")
        logger.info(f"Results saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(discover_all())
