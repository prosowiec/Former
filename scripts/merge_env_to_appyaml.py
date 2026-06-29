from dotenv import dotenv_values
import yaml

env = dotenv_values(".env")

with open("app.yaml") as f:
    data = yaml.safe_load(f)

for container in data["template"]["containers"]:
    env_list = container.setdefault("env", [])

    # Keep existing variables
    existing = {item["name"] for item in env_list}

    for key, value in env.items():
        if key not in existing:
            env_list.append({
                "name": key,
                "value": str(value)
            })

with open("app.yaml", "w") as f:
    yaml.safe_dump(data, f, sort_keys=False)