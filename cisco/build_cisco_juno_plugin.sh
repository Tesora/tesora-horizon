# clone the proper branch
BRANCH=${1:-stable/EE-1.4}

if [ "$BRANCH" != "stable/EE-1.4" ]
then
    echo '****************************************************************'
    echo '* WARNING!!!!                                                  *'
    echo '* Specifying a branch may not work since the code to customize *'
    echo '* for Cisco was only tested with branch "stable/EE-1.4".       *'
    echo '* Roll the dice and see if it works...                         *'
    echo '****************************************************************'
fi

rm -rf cisco-artifacts
mkdir cisco-artifacts

rm -rf tmp-tesora-horizon
CLONE_CMD="git clone -b $BRANCH https://github.com/Tesora/tesora-horizon.git"
echo $CLONE_CMD tmp-tesora-horizon
$CLONE_CMD tmp-tesora-horizon

# create the target directory to contain the modified files
echo Creating cisco-artifacts directories
mkdir -p cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/api
mkdir -p cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project
mkdir -p cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/test/test_data
mkdir -p cisco-artifacts/ccs-portal-tesora-horizon-config

# copy the required supporting files to our target directory
echo Copying files to target directory
cp files/dashboard.py.example cisco-artifacts/ccs-portal-tesora-horizon
cp files/setup.py cisco-artifacts/ccs-portal-tesora-horizon
cp files/MANIFEST.in cisco-artifacts/ccs-portal-tesora-horizon
cp files/overrides.py cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon
cp files/enabled/*.py cisco-artifacts/ccs-portal-tesora-horizon-config
cp -r tmp-tesora-horizon/openstack_dashboard/api/__init__.py cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/api
cp -r tmp-tesora-horizon/openstack_dashboard/api/trove.py cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/api
cp -r tmp-tesora-horizon/openstack_dashboard/dashboards/project/databases cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project
cp -r tmp-tesora-horizon/openstack_dashboard/dashboards/project/database_backups cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project
cp -r tmp-tesora-horizon/openstack_dashboard/dashboards/project/database_clusters cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project
cp -r tmp-tesora-horizon/openstack_dashboard/dashboards/project/database_configurations cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project
cp -r tmp-tesora-horizon/openstack_dashboard/dashboards/project/database_datastores cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project
cp -r tmp-tesora-horizon/openstack_dashboard/test/test_data/__init__.py cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/test/test_data
cp -r tmp-tesora-horizon/openstack_dashboard/test/test_data/trove_data.py cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/test/test_data

# get rid of the temp horizon code
echo Deleting temporary repo
rm -rf tmp-tesora-horizon

# make the directories packages
echo Making directories python packages
touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/__init__.py
touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/__init__.py
touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/__init__.py
touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/__init__.py
touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/test/__init__.py

# clean up some unneeded files
echo Clean up some unneeded files
find . -name '*.pyc' -delete

# change the imports to prefix tesora_horizon
echo 'Prefix tesora_horizon path for api'
find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/from openstack_dashboard import api/from tesora_horizon.openstack_dashboard import api/g'

echo 'Prefix tesora_horizon for path openstack_dashboard.dashboards.project.database*'
find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/ openstack_dashboard.dashboards.project.database/ tesora_horizon.openstack_dashboard.dashboards.project.database/g'

# special one of to change the log views_mod to prefix tesora_horizon
echo 'Prefix tesora_horizon for log file url path'
find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e "s/('openstack_dashboard.dashboards.project.databases.logs.views')/('tesora_horizon.openstack_dashboard.dashboards.project.databases.logs.views')/g"

# database_configurations need to change the json utils package
echo 'Modify code to use common for json utils'
sed -i '' -e "s/from oslo.serialization import jsonutils/from openstack_dashboard.openstack.common import jsonutils/g" cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/database_configurations/config_param_manager.py

# remove the permission attribute from the datastore table
echo 'Remove column permission code for datastore table'
sed -i '' -e "s/permissions=\['openstack.roles.admin'\]//g" cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/database_datastores/tables.py

# remove help attribute from manage root table
sed -i '' -e 's/help_text=_("Status if root was ever enabled \"/)/' cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/databases/tables.py

sed -i '' -e '/"for an instance."))/d' cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/databases/tables.py

sed -i '' -e 's/help_text=_("Password is only visible "/)/' cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/databases/tables.py

sed -i '' -e '/"immediately after the root is "/d' cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/databases/tables.py

sed -i '' -e '/"enabled or reset.")/d' cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard/dashboards/project/databases/tables.py

# tar up the cisco artifacts
cd cisco-artifacts
tar cvf ccs-portal-tesora-horizon.tar ccs-portal-tesora-horizon ccs-portal-tesora-horizon-config
