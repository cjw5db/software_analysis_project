# Software Analysis Project

## One-Time Setup
- Clone this repo into a folder on your machine.  Note the path of the folder for when you create the docker container.
- Download Docker Desktop (if you don't have it already): https://www.docker.com/products/docker-desktop
- Pull the klee container
```bash
docker pull klee/klee
```
- Create a container for the project and make sure the first argument to `--volumes` is the path to the folder that contains our git repo:
```bash
docker run -ti --name=software_analysis_project --volume=/Users/connerward/klee/test:/home/klee/shared --ulimit='stack=-1:-1' klee/klee
```
- Inside the docker container, add these two lines to the end of your `~/.bashrc` file:
```bash
alias compile="clang -emit-llvm -g -c -O0 -Xclang -disable-O0-optnone"
alias graph="compile -Xclang -analyze -Xclang -analyzer-checker=debug.DumpCFG"
```
You may have to restart your container for these aliases to take effect.
This will get you the CFG for a program:
```bash
graph large-data-constraint.c
```
This will get you a `.bc` file for your program that can be run on Klee:
```bash
compile large-data-constraint.c
klee large-data-constraint.bc
```

## Docker
#### Exiting the container:
`exit`

#### Restarting the container:
`docker start -ai software_analysis_project`
