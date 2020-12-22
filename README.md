# Python Miner to extract Code Quality data from Sonarqube server.

This tool is originated from a project, [Public Code Repositories Analysis](https://github.com/hungnguyen10897/Public-Code-Repositories-Analysis), to fetch data from a Sonarqube server, or the public Sonarcloud server. The data include analyses, issues and measures of projects.

## Usage

To run:
```
python3 sonar_miner_main.py
```

You can pass the server, organization or output path to write data to. These are exposed as options to the entry script. By default, the tool runs against Sonarcloud server (https://sonarcloud.io), _apache_ organization and creates a output folder name _sonar_data_ for output data in the working directory. Usually, you can ignore the `-o (organization)` option if the server is not Sonarcloud Server.

```
usage: sonar_miner_main.py [-h] [-p OUTPUT_PATH] [-s SERVER] [-o ORGANIZATION]

optional arguments:
  -h, --help            show this help message and exit
  -p OUTPUT_PATH, --output-path OUTPUT_PATH
                        Path to output file directory.
  -s SERVER, --server SERVER
                        Sonarqube Server.
  -o ORGANIZATION, --organization ORGANIZATION
                        Sonarcloud organization.
```

For example, to query against a local server and write output to a custom folder:

```
python3 sonar_miner_main.py -s http://localhost:9000 -p ./my_server_data

```

## Requirements