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

# exit on error
set -e

# Set up directories and environment
dir=`pwd`
tooldir=${dir}/tools
installdir=${tooldir}/install
bindir=${tooldir}/install/bin

nthreads=1
if [[ $# -ge 1 ]]; then
  nthreads=$1
fi

cd ${tooldir}
mkdir -p ${bindir}

echo "Make sure your BOOST_ROOT has been set if you want to use a non-default Boost installation"

export PATH=${tooldir}/install/bin:$PATH
export LD_LIBRARY_PATH=${tooldir}/install/lib:$LD_LIBRARY_PATH

# yaml-cpp
# dependency of pginfo, not standard available on most platforms
################################################################
cd ${tooldir}
wget http://yaml-cpp.googlecode.com/files/yaml-cpp-0.3.0.tar.gz
tar -zxvf yaml-cpp-0.3.0.tar.gz
mkdir yaml-build
cd yaml-build
cmake ../yaml-cpp -DCMAKE_INSTALL_PREFIX=${installdir} -DBUILD_SHARED_LIBS=ON
make -j${nthreads} install


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
  -DYAMLCPP_INCLUDE_DIR=${installdir}/include/yaml-cpp \
  -DYAMLCPP_LIBRARY=${installdir}/lib/libyaml-cpp.so 
make -j${nthreads}
cp pginfo ${tooldir}/install/bin

# mCRL2
#######
cd ${tooldir}
wget http://www.mcrl2.org/download/release/mcrl2-201210.1.tar.gz
tar -zxvf mcrl2-201210.1.tar.gz
#cd mcrl2-201210.1
mkdir mcrl2-build
cd mcrl2-build
cmake ../mcrl2-201210.1 -DCMAKE_INSTALL_PREFIX=${tooldir}/install \
  -DMCRL2_STAGE_ROOTDIR=`pwd`/stage \
  -DMCRL2_ENABLE_EXPERIMENTAL=ON \
  -DMCRL2_ENABLE_DEPRECATED=ON \
  -DMCRL2_ENABLE_GUI_TOOLS=OFF \
  -DMCRL2_MAN_PAGES=OFF
make install -j${nthreads}

## OCaml (needed for PGSolver)
##############################
systemocaml=1
if [[ ! `which ocamlc` ]]; then
  systemocaml=0
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
if [[ "${systemocaml}" -eq 1 ]]; then
  echo "OCAML_DIR=/usr/lib/ocaml" >> Config
else
  echo "OCAML_DIR=${tooldir}/install/lib/ocaml" >> Config
fi
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

## Scala (needed for Gist)
#
# Note that we use version 2.9.2 here. 2.10.0 is the latest version, but gist
# does not build with that version. Using 2.9.2 we need just two small patches.
##########################
if [[ ! `which scalac` ]]; then
  cd ${tooldir}
  wget http://www.scala-lang.org/downloads/distrib/files/scala-2.9.2.tgz
  tar -zxvf scala-2.9.2.tgz
  cd scala-2.9.2
  ln -s ${tooldir}/scala-2.9.2/bin/fsc ${bindir}
  ln -s ${tooldir}/scala-2.9.2/bin/scala ${bindir}
  ln -s ${tooldir}/scala-2.9.2/bin/scalac ${bindir}
  ln -s ${tooldir}/scala-2.9.2/bin/scaladoc ${bindir}
  ln -s ${tooldir}/scala-2.9.2/bin/scalap ${bindir}
fi

# gist - http://pub.ist.ac.at/gist/
###################################
cd ${tooldir}
wget https://www.dropbox.com/s/q9u1l0otcib038u/package.tar.gz
tar -zxvf package.tar.gz
mv ${tooldir}/tool ${tooldir}/gist
cd gist

sed -i "s|GOAL|${bindir}/goal_2009_04_19.jar|g" ${tooldir}/gist/src/specification/LTL.scala
sed -i "s/JAVA/java/g" ${tooldir}/gist/src/specification/LTL.scala
sed -i "s|TEMP|/tmp|g" ${tooldir}/gist/src/specification/LTL.scala

sed -i "s|GOAL|$bindir/goal_2009_04_19.jar|g" ${tooldir}/gist/src/specification/BuchiAutomaton.scala
sed -i "s/JAVA/java/g" ${tooldir}/gist/src/specification/BuchiAutomaton.scala
sed -i "s|TEMP|/tmp|g" ${tooldir}/gist/src/specification/BuchiAutomaton.scala

sed -i "s|PGSOLVER|${bindir}/pgsolver|g" ${tooldir}/gist/src/newgames/ParityGame.scala

patch -p1 < ${tooldir}/gist.patch
make

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

chmod +x ${bindir}/gist
