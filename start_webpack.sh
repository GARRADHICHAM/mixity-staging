rm -rf node_modules #in case of leftovers
rm -rf collaborator_evaluation/node_modules #in case of leftovers
ln -s /install/node_modules node_modules # link node_modules to the Docker directory
ln -s /install/collaborator_evaluation/node_modules collaborator_evaluation/node_modules # link node_modules to the Docker directory
while ! nc -z web 8000; do
  sleep 0.1 # wait for 1/10 of the second before check again
done
. $NVM_DIR/nvm.sh && yarn start
