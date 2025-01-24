# environment-controller

## Docker
### Building the Docker Image
```bash
docker build -t environment-controller:latest .
```

### Create app dir
```bash
mkdir docker_temp
```

### Running the Docker Container
```bash
docker run --name environment-controller-container \
  --restart=always \
  -v /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77:/media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77 \
  -v /home/chris/docker_temp:/docker_temp \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  -d \
  environment-controller:latest \
  --directory /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77

```

### Explanation
1. <b>Volume Mapping(`-v`)</b>:
    * Maps the host directory `/media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77` to the same path inside the container.
    * This ensures the `P6*.csv` files are accessible to the container and any changes made by the script are saved back to the host directory.
2. <b>Script Argument</b>:
    * `--directory /media/chris/e110508e-b067-4ed5-87a8-5c548bdd8f77` tells the script to use the mounted directory for reading and writing CSV files.
3. <b>Other Flags</b>:
    * `--restart=always`: Ensures the container restarts if it crashes or the host reboots.
    * `-d`: Runs the container in detached mode, allowing it to run in the background.

### Verifying the Setup
1. Check if the container is running:
```bash
docker ps
```
2. View logs to confirm the script is running correctly:
```bash
docker logs -f environment-controller-container
```