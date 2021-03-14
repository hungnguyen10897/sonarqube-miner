# Python Miner to extract Code Quality data from Sonarqube server.

This tool is originated from a project, [Public Code Repositories Analysis](https://github.com/hungnguyen10897/Public-Code-Repositories-Analysis), to fetch data from a Sonarqube server, or the public Sonarcloud server. The data include analyses, issues and measures of projects.

## Usage

To run:
```
python3 main.py
```

You can pass the server, organization or output path to write data to. These are exposed as options to the entry script. By default, the tool runs against Sonarcloud server (https://sonarcloud.io), _apache_ organization and creates a output folder name _sonar_data_ for output data in the working directory. Usually, you can ignore the `-o (organization)` option if the server is not Sonarcloud Server.

```
usage: main.py [-h] [-p OUTPUT_PATH] [-s SERVER] [-o ORGANIZATION]

optional arguments:
  -h, --help            show this help message and exit
  -p OUTPUT_PATH, --output-path OUTPUT_PATH
                        Path to output file directory.
  -s SERVER, --server SERVER
                        Sonarqube Server.
  -o ORGANIZATION, --organization ORGANIZATION
                        Sonarcloud organization.
  -f FILE, --file FILE  File containing projects' sonarqube links.
```

### Examples

To query against a local server and write output to a custom folder:

```
python3 main.py -s http://localhost:9000 -p ./my_server_data
```

To fetch data from a file containing projects' links:
```
python3 main.py -f project_list.xt
```

Content of `project_list.txt`:
```
https://sonarcloud.io/dashboard?id=com.jiaochuan%3Ahazakura
https://course-sonar.rd.tuni.fi/dashboard?id=OHJ3-HARKKA-miko-ja-rope
https://course-sonar.rd.tuni.fi/dashboard?id=OHJ3-HARKKA-team-fda
https://course-sonar.rd.tuni.fi/dashboard?id=OHJ3-HARKKA-kivesmiehet
http://sonar63.rd.tut.fi/dashboard?id=org%3Aapache%3Aaccumulo
https://sonar.rd.tut.fi/sonar75/dashboard?id=CHangeDistiller
```

## Metrics

### Ordering of measures files

The script generates measures based on the metrics. There can be difference in the metrics between servers. However the output measures CSV files will have common schema, which is determined by the **sonar_src/all_metrics.txt** file. The columns of measures CSV files will be ordered by their appearance in the file.

### New metrics

When there are new metrics from the server, there will be a WARNING in stdout

```
WARNING: There are new metrics from the server. Please update to include those metrics:
        AXXg9E3o5xt5QjmKpG2t - Size - unanalyzed_c - INT - No Description
        AXXg9E3o5xt5QjmKpG2u - Size - unanalyzed_cpp - INT - No Description
```

To include certain metrics into the measures files in the next execution, copy wanted lines/metrics and paste them into **sonar_src/all_metrics.txt**.
