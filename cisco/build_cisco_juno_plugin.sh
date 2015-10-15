# clone the proper SOURCE_BRANCH
SOURCE_BRANCH=${1:-master}
TARGET_BRANCH=${2:-stable/juno}

if [ "$SOURCE_BRANCH" != "stable/EE-1.4" ] && [ "$SOURCE_BRANCH" != "dev/EE-1.6" ] && [ "$SOURCE_BRANCH" != "master" ]; then
    echo '********************************************************'
    echo '* The first parameter (SOURCE_BRANCH) must be one of:  *'
    echo '* stable/EE-1.4                                        *'
    echo '* dev/EE-1.6                                           *'
    echo '* master                                               *'
    echo '********************************************************'
fi

if [ "$TARGET_BRANCH" != "stable/juno" ]; then
    echo '********************************************************'
    echo '* The second parameter (TARGET_BRANCH) must be one of: *'
    echo '* stable/juno                                          *'
    echo '********************************************************'
fi

rm -rf cisco-artifacts
mkdir cisco-artifacts

rm -rf tmp-tesora-horizon
CLONE_CMD="git clone -b $SOURCE_BRANCH https://github.com/Tesora/tesora-horizon.git"
echo $CLONE_CMD tmp-tesora-horizon
$CLONE_CMD tmp-tesora-horizon

rm -rf tmp-tesora-python-troveclient
CLONE_CMD="git clone -b $SOURCE_BRANCH https://github.com/Tesora/tesora-python-troveclient.git"
echo $CLONE_CMD tmp-tesora-python-troveclient
$CLONE_CMD tmp-tesora-python-troveclient

CISCO_ARTIFACTS_HORIZON_DIR=cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/openstack_dashboard
CISCO_ARTIFACTS_CONFIG_DIR=cisco-artifacts/ccs-portal-tesora-horizon-config
SOURCE_HORIZON_BASE=tmp-tesora-horizon/openstack_dashboard

# create the target directory to contain the modified files
echo Creating cisco-artifacts directories
if [ "$SOURCE_BRANCH" == "stable/EE-1.4" ]; then
    mkdir -p $CISCO_ARTIFACTS_HORIZON_DIR/api
    mkdir -p $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project
    mkdir -p $CISCO_ARTIFACTS_HORIZON_DIR/test/test_data
    mkdir -p $CISCO_ARTIFACTS_CONFIG_DIR
elif [ "$SOURCE_BRANCH" == "dev/EE-1.6" ] || [ "$SOURCE_BRANCH" == "master" ]; then
    mkdir -p $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove
    mkdir -p $CISCO_ARTIFACTS_HORIZON_DIR/test/test_data
    mkdir -p $CISCO_ARTIFACTS_CONFIG_DIR
fi

# copy common files to the target
echo Copying files to target directory
cp files/dashboard.py.example cisco-artifacts/ccs-portal-tesora-horizon
cp files/setup.py cisco-artifacts/ccs-portal-tesora-horizon
cp files/MANIFEST.in cisco-artifacts/ccs-portal-tesora-horizon
cp files/overrides.py cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon

# copy the required supporting files to our target directory
echo Copying files from $SOURCE_BRANCH branch to target directory
if [ "$SOURCE_BRANCH" == "stable/EE-1.4" ]; then
    cp files/enabled/_900_project_add_tesora_panel_group.py $CISCO_ARTIFACTS_CONFIG_DIR
    cp files/enabled/juno/*.py $CISCO_ARTIFACTS_CONFIG_DIR
    cp -r $SOURCE_HORIZON_BASE/api/__init__.py $CISCO_ARTIFACTS_HORIZON_DIR/api
    cp -r $SOURCE_HORIZON_BASE/api/trove.py $CISCO_ARTIFACTS_HORIZON_DIR/api
    cp -r $SOURCE_HORIZON_BASE/dashboards/project/databases $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project
    cp -r $SOURCE_HORIZON_BASE/dashboards/project/database_backups $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project
    cp -r $SOURCE_HORIZON_BASE/dashboards/project/database_clusters $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project
    cp -r $SOURCE_HORIZON_BASE/dashboards/project/database_configurations $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project
    cp -r $SOURCE_HORIZON_BASE/dashboards/project/database_datastores $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project
    cp -r $SOURCE_HORIZON_BASE/test/test_data/__init__.py $CISCO_ARTIFACTS_HORIZON_DIR/test/test_data
    cp -r $SOURCE_HORIZON_BASE/test/test_data/trove_data.py $CISCO_ARTIFACTS_HORIZON_DIR/test/test_data
elif [ "$SOURCE_BRANCH" == "dev/EE-1.6" ] || [ "$SOURCE_BRANCH" == "master" ]; then
    cp files/enabled/*.py $CISCO_ARTIFACTS_CONFIG_DIR
    cp -r $SOURCE_HORIZON_BASE/contrib/trove/* $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove
    cp -r $SOURCE_HORIZON_BASE/test/test_data/trove_data.py $CISCO_ARTIFACTS_HORIZON_DIR/test/test_data
    cp -r tmp-tesora-python-troveclient/troveclient cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon
fi

# get rid of the temp horizon code
echo Deleting temporary repo
rm -rf tmp-tesora-horizon
rm -rf tmp-tesora-python-troveclient

# make the directories packages
echo Making directories python packages
if [ "$SOURCE_BRANCH" == "stable/EE-1.4" ]; then
    touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/test/__init__.py
elif [ "$SOURCE_BRANCH" == "dev/EE-1.6" ] || [ "$SOURCE_BRANCH" == "master" ]; then
    touch cisco-artifacts/ccs-portal-tesora-horizon/tesora_horizon/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/contrib/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/__init__.py
    touch $CISCO_ARTIFACTS_HORIZON_DIR/test/__init__.py
fi

# clean up some unneeded files
echo Clean up some unneeded files
find . -name '*.pyc' -delete

if [ "$TARGET_BRANCH" == "stable/juno" ]; then
    if [ "$SOURCE_BRANCH" == "stable/EE-1.4" ]; then
        # change api import for trove to tesora_horizon
        echo 'Modify api import of trove to prefix tesora_horizon'
        sed -i '' -e "s/from openstack_dashboard.api import trove/from tesora_horizon.openstack_dashboard.api import trove/g" $CISCO_ARTIFACTS_HORIZON_DIR/api/__init__.py

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
        sed -i '' -e "s/from oslo.serialization import jsonutils/from openstack_dashboard.openstack.common import jsonutils/g" $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/database_configurations/config_param_manager.py

        # remove the permission attribute from the datastore table
        echo 'Remove column permission code for datastore table'
        sed -i '' -e "s/permissions=\['openstack.roles.admin'\]//g" $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/database_datastores/tables.py

        # remove help attribute from manage root table
        sed -i '' -e 's/help_text=_("Status if root was ever enabled \"/)/' $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/databases/tables.py

        sed -i '' -e '/"for an instance."))/d' $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/databases/tables.py

        sed -i '' -e 's/help_text=_("Password is only visible "/)/' $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/databases/tables.py

        sed -i '' -e '/"immediately after the root is "/d' $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/databases/tables.py

        sed -i '' -e '/"enabled or reset.")/d' $CISCO_ARTIFACTS_HORIZON_DIR/dashboards/project/databases/tables.py
    elif [ "$SOURCE_BRANCH" == "dev/EE-1.6" ] || [ "$SOURCE_BRANCH" == "master" ]; then
        # change api import for trove to tesora_horizon
        echo 'Modify api import of trove to prefix tesora_horizon'
        sed -i '' -e "s/from openstack_dashboard.contrib.trove.api import trove/from tesora_horizon.openstack_dashboard.contrib.trove.api import trove/g" $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/api/__init__.py

        # change api import for trove to tesora_horizon
        echo 'Modify api import of trove to prefix tesora_horizon'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/ openstack_dashboard.contrib.trove import api/ tesora_horizon.openstack_dashboard.contrib.trove import api/g'

        echo 'Prefix tesora_horizon for path openstack_dashboard.contrib.trove.content.database*'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/ openstack_dashboard.contrib.trove.content.database/ tesora_horizon.openstack_dashboard.contrib.trove.content.database/g'

        # special one of to change the log views_mod to prefix tesora_horizon
        echo 'Prefix tesora_horizon for log file url path'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e "s/('openstack_dashboard.contrib.trove.content.databases.logs.views')/('tesora_horizon.openstack_dashboard.contrib.trove.content.databases.logs.views')/g"

        # database_configurations need to change the json utils package
        echo 'Modify code to use common for json utils'
        sed -i '' -e "s/from oslo.serialization import jsonutils/from openstack_dashboard.openstack.common import jsonutils/g" $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/database_configurations/config_param_manager.py

        # remove the permission attribute from the datastore table
        echo 'Remove column permission code for datastore table'
        sed -i '' -e "s/permissions=\['openstack.roles.admin'\]//g" $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/database_datastores/tables.py

        # remove help attribute from manage root table
        sed -i '' -e 's/help_text=_("Status if root was ever enabled \"/)/' $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/databases/tables.py

        sed -i '' -e '/"for an instance."))/d' $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/databases/tables.py

        sed -i '' -e 's/help_text=_("Password is only visible "/)/' $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/databases/tables.py

        sed -i '' -e '/"immediately after the root is "/d' $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/databases/tables.py

        sed -i '' -e '/"enabled or reset.")/d' $CISCO_ARTIFACTS_HORIZON_DIR/contrib/trove/content/databases/tables.py

        # changes for tesora-python-troveclient
        echo 'Prefix tesora_horizon for from troveclient'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/from troveclient/from tesora_horizon.troveclient/g'

        echo 'Prefix tesora_horizon for import troveclient'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/import troveclient/import tesora_horizon.troveclient/g'

        echo 'Change from oslo_utils import encodeutils to Juno path'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/from oslo_utils import encodeutils/from tesora_horizon.troveclient.openstack.common import strutils as encodeutils/g'

        echo 'Change from oslo_utils import importutils to Juno path'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/from oslo_utils import importutils/from tesora_horizon.troveclient.openstack.common import importutils/g'

        echo 'Change from oslo_utils import strutils to Juno path'
        find . -name '[^_]*.py' -type f -print0 | xargs -0 sed -i '' -e 's/from oslo_utils import strutils/from tesora_horizon.troveclient.openstack.common import strutils/g'
    fi
fi

# tar up the cisco artifacts
cd cisco-artifacts
tar zcvf ccs-portal-tesora-horizon.tar.gz ccs-portal-tesora-horizon ccs-portal-tesora-horizon-config
