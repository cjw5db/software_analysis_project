# Software Analysis Project

## One-Time Setup
- Clone this repo unzip the submission zip file into a folder on your machine.  Note the path of the folder for when you create the docker container.
- Download Docker Desktop (if you don't have it already) and start it: https://www.docker.com/products/docker-desktop
- Pull the klee container
```bash
docker pull klee/klee
```

- Create a container for the project and make sure the first argument to `--volumes` is the path to the folder that contains the git repo or source code:
```bash
docker run -ti --name=software_analysis_project --volume=/path/to/this/git/repo/locally:/home/klee/shared --ulimit='stack=-1:-1' klee/klee
```

- Inside the docker container, add this line to the end of your `~/.bashrc` file:
```bash
alias klee_compile='clang -emit-llvm -g -c -O0 -Xclang -disable-O0-optnone'
```
__NOTE__: You may have to restart your container for the alias to take effect.

- Change into the working directory with the source code:
```bash
cd shared
```

## Usage

To get a `.bc` file for your program that can be run on Klee:
```bash
klee_compile examples/**/*.c
klee *.bc
```

Ways to run the tool:
```bash
#shows usage information
python3 tool.py --help 

#runs the tool with minimum output
python3 tool.py examples/**/*.c

#runs the tool with full data structure dumps and unnecessary/necessary klee_assume array indices
python3 tool.py examples/**/*.c --verbose 
```

## Docker
#### Exiting the container:
`exit`

#### Restarting the container:
`docker start -ai software_analysis_project`
