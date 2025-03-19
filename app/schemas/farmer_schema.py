FARMER_DATA_SCHEMA = {
    "phone_number": str,
    "name": str,
    "taluka": str,
    "village": str,
    "total_land": str,
    "crops": [{"crop": str, "land_size": str}],
    "animals": [{"name": str, "count": int}],
    "milk_prod": str,
    "loan": str,
    "water_resource": list
}

DEFAULT_FARMER_DATA = {
    "phone_number": None,
    "name": None,
    "taluka": None,
    "village": None,
    "total_land": None,
    "crops": [],
    "animals": [],
    "milk_prod": None,
    "loan": None,
    "water_resource": []
}
