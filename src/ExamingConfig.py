import sys,os
# assets/example_xi_configs/xi_crosslinking.conf
# assets/example_xi_configs/xi_linear.conf


# read in each of these files. comment lines starting with # and empty lines can be ignored. for each non-comment line, split on the first : to get a key and value. store these in a dictionary. print the resulting dictionary for each file.
config_files = [
    "assets/example_xi_configs/xi_crosslinking.conf",
    "assets/example_xi_configs/xi_linear.conf"
]
config_dict = {}
for config_file in config_files:
    config_dict[config_file] = {}
    with open(config_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key in config_dict[config_file]:
                config_dict[config_file][key] += [value]
            else:
                config_dict[config_file][key] = [value]


### print the resulting dictionary for each file
for config_file, config in config_dict.items():
    print(f"Config from {config_file}:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print("\n")

### chech which config params differ between the two files
print("Comparing config parameters between the two files:")
keys_crosslinking = set(config_dict["assets/example_xi_configs/xi_crosslinking.conf"].keys())
keys_linear = set(config_dict["assets/example_xi_configs/xi_linear.conf"].keys())
all_keys = keys_crosslinking.union(keys_linear)
for key in all_keys:
    value_crosslinking = config_dict["assets/example_xi_configs/xi_crosslinking.conf"].get(key, None)
    value_linear = config_dict["assets/example_xi_configs/xi_linear.conf"].get(key, None)
    if value_crosslinking != value_linear:
        print(f"  {key}:")
        print(f"    xi_crosslinking.conf: {value_crosslinking}")
        print(f"    xi_linear.conf: {value_linear}")