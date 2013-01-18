#!/bin/bash

################################################################################
#
# (c) 2013 Jeroen Keiren
#
# Rudimentary script to install all tools that will be (indirectly) called from
# run.py. Before calling run.py make sure to:
# export PATH=$PATH:`pwd`/tools/install/bin
# export LD_LIBRARY_PATH=`pwd`/tools/install/lib:$LD_LIBRARY_PATH
################################################################################

# Set up directories and environment
dir=`pwd`
tooldir=${dir}/tools
bindir=${tooldir}/install/bin

nthreads=1
if [[ $# -ge 1 ]]; then
  nthreads=$1
fi

mkdir ${tooldir}
cd ${tooldir}
mkdir -p ${bindir}

export PATH=${tooldir}/install/bin:$PATH

# pginfo
########
cd ${tooldir}
git clone https://github.com/jkeiren/pginfo.git
cd pginfo
git submodule update --init
cd ${tooldir}
mkdir pginfo-build
cd pginfo-build
cmake ../pginfo \
  -DCMAKE_INSTALL_PREFIX=${tooldir}/install \
  -DYAMLCPP_INCLUDE_DIR=/scratch/jkeiren/local/include/yaml-cpp \
  -DYAMLCPP_LIBRARY=/scratch/jkeiren/local/lib/libyaml-cpp.so \
  -DBOOST_ROOT=/scratch/jkeiren/local/boost_1_52_0 \
  -DBoost_INCLUDE_DIRS=/scratch/jkeiren/local/boost_1_52_0/stage/lib
make -j${nthreads}
cp pginfo ${tooldir}/install/bin

# mCRL2
#######
cd ${tooldir}
wget http://www.mcrl2.org/download/release/mcrl2-201210.1.tar.gz
tar -zxvf mcrl2-201210.1.tar.gz
cd mcrl2-201210.1.tar.gz
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX=${tooldir}/install \
  -DMCRL2_STAGE_ROOTDIR=`pwd`/stage \
  -DMCRL2_ENABLE_EXPERIMENTAL=ON \
  -DMCRL2_ENABLE_DEPRECATED=ON \
  -DMCRL2_ENABLE_GUI_TOOLS=OFF \
  -DMCRL2_ENABLE_MAN_PAGES=OFF \
  -DBOOST_ROOT=/scratch/jkeiren/local/boost_1_52_0
make install -j${nthreads}

## OCaml (needed for PGSolver)
##############################
which ocamlc
if [[ $? -eq 1 ]]; then
  cd ${tooldir}
  wget http://caml.inria.fr/pub/distrib/ocaml-4.00/ocaml-4.00.1.tar.gz
  tar -zxvf ocaml-4.00.1.tar.gz
  cd ocaml-4.00.1
  ./configure -prefix ${tooldir}/install
  make world.opt
  umask 022
  make install
  make clean
fi

# PGSolver
##########
cd ${tooldir}
wget https://www.dropbox.com/s/ce4xwo055t4ffqr/pgsolver.tgz
tar -zxvf pgsolver.tgz

cd ${tooldir}/pgsolver
echo "TAR=tar" > Config
echo "GZIP=gzip" >> Config
echo "OCAML=ocaml" >> Config
echo "OCAMLOPT=ocamlopt" >> Config
echo "OCAMLLEX=ocamllex" >> Config
echo "OCAMLYACC=ocamlyacc" >> Config
echo "OCAMLDEP=ocamldep" >> Config
echo "CPP=g++" >> Config
echo "OCAMLOPTCPP=g++" >> Config
echo "" >> Config
echo "" >> Config
echo "#######" >> Config
echo "# change this to the OCaml installation directory" >> Config
echo "#######" >> Config
echo "OCAML_DIR=${tooldir}/install/lib/ocaml" >> Config
echo "" >> Config
echo "" >> Config
echo "#######" >> Config
echo "# DIRECTORIES" >> Config
echo "#######" >> Config
echo "OBJDIR=obj" >> Config
echo "SRCDIR=src" >> Config
echo "BINDIR=bin" >> Config
echo "SATSOLVERSROOT=satsolvers" >> Config
echo "TCSLIBROOT=TCSlib" >> Config
echo "" >> Config
echo "" >> Config
echo "#######" >> Config
echo "# CONFIG" >> Config
echo "#######" >> Config
echo "LINKGENERATORS=NO" >> Config
echo "" >> Config
echo "" >> Config
echo "#######" >> Config
echo "# Z3" >> Config
echo "#######" >> Config
echo "HASSMT=NO" >> Config
echo "Z3DIR=/usr/local/lib/z3" >> Config

cp Config satsolvers/Config
cp Config TCSlib/Config

make all

for f in ${tooldir}/pgsolver/bin/*; do
  ln -s ${f} ${tooldir}/install/bin
done

# This is for new version of GOAL
# However, gist seems to need an older version.
#cd $tooldir
# On Ubuntu systems make sure you are using java-6-openjdk
# Install GOAL
#wget https://www.dropbox.com/s/w3w80w63g15pkoh/GOAL-20120409-with-API.zip
#unzip GOAL-20120409-with-API.zip

#echo "#!/bin/bash" > ${bindir}/goal
#for jar in `pwd`/GOAL-20120409/lib/*.jar; do
#  echo "CLASSPATH=\$CLASSPATH:$jar" >> ${bindir}/goal
#done
#echo "`pwd`/GOAL-20120409/goal" >> ${bindir}/goal
#chmod +x ${bindir}/goal

# GOAL - http://goal.im.ntu.edu.tw/
###################################
cd ${bindir}
wget https://www.dropbox.com/s/uh4d6gqb6ko4dbj/goal_2009_04_19.jar

# gist - http://pub.ist.ac.at/gist/
###################################
cd ${tooldir}
wget https://www.dropbox.com/s/q9u1l0otcib038u/package.tar.gz
tar -zxvf package.tar.gz
mv ${tooldir}/tool ${tooldir}/gist

sed -i "s|GOAL|${bindir}/goal_2009_04_19.jar|g" ${tooldir}/gist/src/specification/LTL.scala
sed -i "s/JAVA/java/g" ${tooldir}/gist/src/specification/LTL.scala
sed -i "s|TEMP|/tmp|g" ${tooldir}/gist/src/specification/LTL.scala

sed -i "s|GOAL|$bindir/goal_2009_04_19.jar|g" ${tooldir}/gist/src/specification/BuchiAutomaton.scala
sed -i "s/JAVA/java/g" ${tooldir}/gist/src/specification/BuchiAutomaton.scala
sed -i "s|TEMP|/tmp|g" ${tooldir}/gist/src/specification/BuchiAutomaton.scala

sed -i "s|PGSOLVER|${bindir}/pgsolver|g" ${tooldir}/gist/src/newgames/ParityGame.scala

echo "#!/bin/bash" > ${bindir}/gist
for jar in ${tooldir}/gist/lib/*.jar; do
  echo "CLASSPATH=\$CLASSPATH:$jar" >> ${bindir}/gist
done
echo "cd ${tooldir}/gist/build" >> ${bindir}/gist
echo "if [ \"$@\" == \"cui\" ]; then" >> ${bindir}/gist
echo "  scala -howtorun:object cui.main" >> ${bindir}/gist
echo "else" >> ${bindir}/gist
echo "  scala -howtorun:object gui.main" >> ${bindir}/gist
echo "fi" >> ${bindir}/gist
echo "cd -" >> ${bindir}/gist

