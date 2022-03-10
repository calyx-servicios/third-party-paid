cd /opt/odoo13/custom-addons/calyx/third-party-paid
eval `ssh-agent -s`
ssh-add ~/.ssh/third-party-paid
git fetch --all; git reset --hard HEAD; git merge @{u}
sleep 3
service odoo13 restart