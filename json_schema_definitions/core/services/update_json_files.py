import os
import shutil
import json


def update_definitions(
    json_data, src_directory, root_json_data, processed_refs, ref_to_key_map
):
    if isinstance(json_data, dict):
        for key, value in list(
            json_data.items()
        ):  # Convert to list to avoid RuntimeError
            if isinstance(value, dict):
                if "$ref" in value:
                    ref_value = value["$ref"]
                    if "properties" in ref_value:
                        # Replace 'properties' with 'definitions'
                        new_ref_value = ref_value.replace("properties", "definitions")
                        value["$ref"] = new_ref_value

                    ref_filename = ref_value.split("/")[-1]
                    if ref_filename.endswith(".json"):
                        if ref_filename in processed_refs:
                            # Use the correct key from the map
                            value[
                                "$ref"
                            ] = f"#/definitions/{ref_to_key_map[ref_filename]}"
                            continue  # Skip already processed refs to avoid infinite recursion
                        processed_refs.add(ref_filename)

                        # Read the referenced JSON file
                        with open(
                            os.path.join(src_directory, ref_filename), "r"
                        ) as ref_f:
                            ref_json_data = json.load(ref_f)

                        # Use the key from the referenced JSON file
                        if "properties" in ref_json_data:
                            ref_key = list(ref_json_data["properties"].keys())[0]
                            ref_to_key_map[ref_filename] = ref_key  # Store the mapping
                            root_json_data["definitions"][ref_key] = ref_json_data[
                                "properties"
                            ][ref_key]
                        else:
                            print(
                                f"Warning: No 'properties' key found in {ref_filename}"
                            )

                        # Update the $ref to point to 'definitions' with the correct key
                        value["$ref"] = f"#/definitions/{ref_key}"

                        # Recursively check the newly loaded definition for more $ref fields
                        update_definitions(
                            ref_json_data,
                            src_directory,
                            root_json_data,
                            processed_refs,
                            ref_to_key_map,
                        )
                else:
                    update_definitions(
                        value,
                        src_directory,
                        root_json_data,
                        processed_refs,
                        ref_to_key_map,
                    )
            elif isinstance(value, list):
                for item in value:
                    update_definitions(
                        item,
                        src_directory,
                        root_json_data,
                        processed_refs,
                        ref_to_key_map,
                    )


def update_json_files(src_directory, dest_directory):
    # Create the destination directory if it doesn't exist
    if not os.path.exists(dest_directory):
        os.makedirs(dest_directory)

    for filename in os.listdir(src_directory):
        if filename.endswith(".json"):
            src_filepath = os.path.join(src_directory, filename)
            dest_filepath = os.path.join(dest_directory, filename)

            # Copy the file to the destination directory
            shutil.copy(src_filepath, dest_filepath)

            # Read the copied JSON file
            with open(dest_filepath, "r") as f:
                json_data = json.load(f)

            # Update definitions recursively
            processed_refs = set()
            ref_to_key_map = {}
            update_definitions(
                json_data, src_directory, json_data, processed_refs, ref_to_key_map
            )

            # Write the updated JSON back to disk
            with open(dest_filepath, "w") as f:
                json.dump(json_data, f, indent=4)


if __name__ == "__main__":
    # Specify the source and destination directories
    src_directory = "../models"  # Current directory
    dest_directory = "../models/dist"  # Destination directory

    # Run the function
    update_json_files(src_directory, dest_directory)
