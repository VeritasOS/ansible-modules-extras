#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Veritas LLC
#
# This file is part of Ansible.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = """
---
module: artifactory_repository
short_description: Artifactory module to manage repositories
description:
    - Create local/remote/virtual repositories.
    - Delete local/remote/virtual repositories.
version_added: "2.2"
author: "Prathamesh Nevagi (@pratz)"
requirements:
    - python 2.x (2.4, 2.5, 2.6, 2.7)
    - https://github.com/veritasos/py-artifactory.git
options:
    action:
        description:
            - Operation on the artifactory repository
        required: true
        default: string
    type:
        description:
            - Type of artifactory repository
        required: false
        default: string
    artifactory_url:
        description:
            - Artifactory url
        required: false
        default: string
    artifactory_username:
        description:
            - Artifactory username
        required: false
        default: string
    artifactory_password:
        description:
            - Artifactory password
        required: false
        default: string
    path:
        description:
            - Path to external yml file
        required: false
        default: string

    # All artifactory repository options are loaded dynamically
    # Supported options:
    #     https://www.jfrog.com/confluence/display/RTF/Repository+Configuration+JSON
"""

EXAMPLES = """
---
- hosts: test
  tasks:
  - name: Create local repository
    artifactory_repository:
        artifactory_url: "http://localhost:8081"
        artifactory_username: "admin"
        artifactory_password: "password"
        action: "create"
        type: "local"
        key: "test-local-repo"
        package_type: "maven"

- hosts: test
  tasks:
  - name: Create remote repository
    artifactory_repository:
        artifactory_url: "http://localhost:8081"
        artifactory_username: "admin"
        artifactory_password: "password"
        action: "create"
        type: "remote"
        key: "test-remote-repo"
        package_type: "docker"
        url: "http://hub.docker.com"

- hosts: test
  tasks:
  - name: Create virtual repository
    artifactory_repository:
        artifactory_url: "http://localhost:8081"
        artifactory_username: "admin"
        artifactory_password: "password"
        action: "create"
        type: "virtual"
        key: "test-virtual-repo"
        package_type: "maven"
        repositories: ["test-remote-repo"]

- hosts: test
  tasks:
  - name: Delete local/remote/virtual repository
    artifactory_repository:
        artifactory_url: "http://localhost:8081"
        artifactory_username: "admin"
        artifactory_password: "password"
        action: "delete"
        key: "test-virtual-repo"

- hosts: test
  tasks:
  - name: Bulk create local/remote/virtual repositories
    artifactory_repository:
        artifactory_url: "http://localhost:8081"
        artifactory_username: "admin"
        artifactory_password: "password"
        action: "bulk_create"
        path: "samples/artifactory_repositories.yml"

- hosts: test
  tasks:
  - name: Bulk delete local/remote/virtual repositories
    artifactory_repository:
        artifactory_url: "http://localhost:8081"
        artifactory_username: "admin"
        artifactory_password: "password"
        action: "bulk_delete"
        path: "samples/artifactory_repositories.yml"

# Bulk repositories sample
---
projects:
  silicon_valley:
     artifactory:
         repositories:
             local:
                 - key: "silicon_valley-local1-repo"
                   package_type: "maven"
                   handle_snapshots: false
                 - key: "silicon_valley-local2-repo"
                   package_type: "docker"
             remote:
                 - key: "silicon_valley-remote1-repo"
                   package_type: "maven"
                   url: "http://hub.docker.com"
                 - key: "silicon_valley-remote2-repo"
                   package_type: "docker"
                   url: "http://hub.docker.com"
             virtual:
                 - key: "silicon_valley-virtual1-repo"
                   package_type: "maven"
                   repositories: ["silicon_valley-local1-repo"]

  mr_robot:
     artifactory:
         repositories:
             local:
                 - key: "mr_robot-local1-repo"
                   package_type: "maven"
                 - key: "mr_robot-local2-repo"
                   package_type: "docker"
             remote:
                 - key: "mr_robot-remote1-repo"
                   package_type: "maven"
                   url: "http://hub.docker.com"
                 - key: "mr_robot-remote2-repo"
                   package_type: "docker"
                   url: "http://hub.docker.com"
             virtual:
                 - key: "mr_robot-virtual1-repo"
                   package_type: "maven"
                   repositories: ["mr_robot-local1-repo"]
"""

RETURN = """
response:
    description: Response retured from Artifactory server
    type: string
"""

# stdlib imports
import os
import yaml

# 3rd-party imports
try:
    from artifactory import Artifactory
    HAS_ARTIFACTORY = True
except:
    HAS_ARTIFACTORY = False
    INSTALL_ARTIFACTORY_MSG = """
    Artifactory package is required
    pip install git+https://github.com/veritasos/py-artifactory.git
    """


class ArgumentSpecs(object):
    exclude_fields = ['rclass']

    @staticmethod
    def all():
        return dict(
                ArgumentSpecs.local().items() +
                ArgumentSpecs.remote().items() +
                ArgumentSpecs.virtual().items()
                )

    @staticmethod
    def local():
        from artifactory.repository.local import Local
        required_specs = ArgumentSpecs.get_specs(Local._required)
        optional_specs = ArgumentSpecs.get_specs(Local._optional)
        return dict(required_specs.items() + optional_specs.items())

    @staticmethod
    def remote():
        from artifactory.repository.remote import Remote
        required_specs = ArgumentSpecs.get_specs(Remote._required)
        optional_specs = ArgumentSpecs.get_specs(Remote._optional)
        return dict(required_specs.items() + optional_specs.items())

    @staticmethod
    def virtual():
        from artifactory.repository.virtual import Virtual
        required_specs = ArgumentSpecs.get_specs(Virtual._required)
        optional_specs = ArgumentSpecs.get_specs(Virtual._optional)
        return dict(required_specs.items() + optional_specs.items())

    @staticmethod
    def get_specs(fields, required=False):
        specs = {}
        for name, tag, default in fields:
            if name not in ArgumentSpecs.exclude_fields:

                specs[name] = {
                        "required": required,
                        "default": default,
                        "type": ArgumentSpecs.get_type(default)
                        }
        return specs

    @staticmethod
    def get_type(value):

        if isinstance(value, str):
            return "str"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, list):
            return "list"
        elif isinstance(value, dict):
            return "dict"
        else:
            return value


def create_local(artifactory, params):
    local_repo = artifactory.repository.local()

    for field, details in ArgumentSpecs.local().iteritems():
        setattr(local_repo, field, params.get(field,
            details.get("default")))

    return local_repo.create()


def create_remote(artifactory, params):
    remote_repo = artifactory.repository.remote()

    for field, details in ArgumentSpecs.remote().iteritems():
        setattr(remote_repo, field, params.get(field,
            details.get("default")))

    return remote_repo.create()


def create_virtual(artifactory, params):
    virtual_repo = artifactory.repository.virtual()

    for field, details in ArgumentSpecs.virtual().iteritems():
        setattr(virtual_repo, field, params.get(field,
            details.get("default")))

    return virtual_repo.create()


def main():
    argument_spec = ArgumentSpecs.all()

    argument_spec.update(
        artifactory_url = dict(required=False, type="str"),
        artifactory_username = dict(required=False, type="str"),
        artifactory_password = dict(required=False, type="str"),
        artifactory_redirect = dict(required=False, type="str", default="artifactory"),
        action = dict(required=True, type="str"),
        type = dict(required=False, type="str"),
        path = dict(required=False, type="str"),
        suffix = dict(required=False, type="str", default=""),
    )

    module = AnsibleModule(
        argument_spec = argument_spec,
        supports_check_mode=True
    )

    if not HAS_ARTIFACTORY:
        module.fail_json(msg=INSTALL_ARTIFACTORY_MSG)

    # get module params
    action = module.params.get("action")
    type = module.params.get("type")
    suffix = module.params.get("suffix")
    artifactory_url = os.environ.get("ARTIFACTORY_URL", module.params.get("artifactory_url"))
    artifactory_username = os.environ.get("ARTIFACTORY_USERNAME", module.params.get("artifactory_username"))
    artifactory_password = os.environ.get("ARTIFACTORY_PASSWORD", module.params.get("artifactory_password"))
    artifactory_redirect = os.environ.get("ARTIFACTORY_REDIRECT", module.params.get("artifactory_redirect"))

    # yml file path for bulk create/update/delete
    path = module.params.get("path")
    if path:
        path = os.path.abspath(path)

    # append suffix to repository name
    if suffix:
        module.params["key"]= "{0}{1}".format(
                module.params.get("key"), suffix)

    # create a artifactory client instance
    artifactory = Artifactory(
        url=artifactory_url,
        username=artifactory_username,
        password=artifactory_password,
        redirect=artifactory_redirect,
        )

    if action.lower() == "create":

        try:
            artifactory.repository.fetch(module.params.get("key"))
            module.exit_json(changed=False,
                    msg="Repository {0} already exists".format(module.params.get("key")))
        except Exception:
            if type.lower() == "local":
                response = create_local(artifactory, module.params)
                module.exit_json(changed=True, msg=response)

            elif type.lower() == "remote":
                response = create_remote(artifactory, module.params)
                module.exit_json(changed=True, msg=response)

            elif type.lower() == "virtual":
                response = create_virtual(artifactory, module.params)
                module.exit_json(changed=True, msg=response)
            else:
                module.fail_json(msg="Repository type {0} not found.".format(
                    type))

        except Exception, e:
            module.fail_json(msg=e)

    elif action.lower() == "delete":
        try:
            repo = artifactory.repository.fetch(module.params.get("key"))
            response = repo.remove()
            module.exit_json(changed=True, msg=response)
        except Exception:
            module.exit_json(changed=False,
                    msg="Repository {0} not found".format(module.params.get("key")))
        except Exception, e:
            module.fail_json(msg=e)

    elif action.lower() == "bulk_create":
        changed = False
        try:
            response = []
            params = yaml.load(open(path, 'r'))

            for project_name, services in params.get("projects").iteritems():

                if (services.get("artifactory")
                        and services.get("artifactory").get("repositories")):

                    # create local repo
                    if services.get("artifactory").get("repositories").get("local"):
                        for local_params in services.get("artifactory").get("repositories").get("local"):

                            if suffix:
                                local_params["key"] = "{0}{1}".format(
                                        local_params.get("key"), suffix)

                            try:
                                artifactory.repository.fetch(local_params.get("key"))
                                response.append("Repository {0} already exists".format(
                                    local_params.get("key")))
                            except Exception:
                                response.append(create_local(
                                    artifactory, local_params))
                                changed = True

                    # create remote repo
                    if services.get("artifactory").get("repositories").get("remote"):
                        for remote_params in services.get("artifactory").get("repositories").get("remote"):

                            if suffix:
                                remote_params["key"] = "{0}{1}".format(
                                        remote_params.get("key"), suffix)

                            try:
                                artifactory.repository.fetch(remote_params.get("key"))
                                response.append("Repository {0} already exists".format(
                                    remote_params.get("key")))
                            except Exception:
                                response.append(create_remote(
                                    artifactory, remote_params))
                                changed = True

                    # create virtual repo
                    if services.get("artifactory").get("repositories").get("virtual"):
                        for virtual_params in services.get("artifactory").get("repositories").get("virtual"):

                            if suffix:
                                virtual_params["key"] = "{0}{1}".format(
                                        virtual_params.get("key"), suffix)

                            try:
                                artifactory.repository.fetch(virtual_params.get("key"))
                                response.append("Repository {0} already exists".format(
                                    virtual_params.get("key")))
                            except Exception:
                                response.append(create_virtual(
                                    artifactory, virtual_params))
                                changed = True

            module.exit_json(changed=changed, msg=response)
        except Exception, e:
            module.fail_json(msg=e)

    elif action.lower() == "bulk_delete":
        changed = False
        try:
            response = []
            params = yaml.load(open(path, 'r'))

            for project_name, services in params.get("projects").iteritems():

                if (services.get("artifactory")
                        and services.get("artifactory").get("repositories")):

                    # create local repo
                    if services.get("artifactory").get("repositories").get("local"):
                        for local_params in services.get("artifactory").get("repositories").get("local"):

                            if suffix:
                                local_params["key"] = "{0}{1}".format(
                                        local_params.get("key"), suffix)

                            try:
                                repo = artifactory.repository.fetch(local_params.get("key"))
                                response.append(repo.remove())
                                changed = True
                            except Exception:
                                response.append("Repository {0} not found".format(
                                    local_params.get("key")))

                    # create remote repo
                    if services.get("artifactory").get("repositories").get("remote"):
                        for remote_params in services.get("artifactory").get("repositories").get("remote"):

                            if suffix:
                                remote_params["key"] = "{0}{1}".format(
                                        remote_params.get("key"), suffix)
                            try:
                                repo = artifactory.repository.fetch(remote_params.get("key"))
                                response.append(repo.remove())
                                changed = True
                            except Exception:
                                response.append("Repository {0} not found".format(
                                    remote_params.get("key")))

                    # create virtual repo
                    if services.get("artifactory").get("repositories").get("virtual"):
                        for virtual_params in services.get("artifactory").get("repositories").get("virtual"):

                            if suffix:
                                virtual_params["key"] = "{0}{1}".format(
                                        virtual_params.get("key"), suffix)

                            try:
                                repo = artifactory.repository.fetch(virtual_params.get("key"))
                                response.append(repo.remove())
                                changed = True
                            except Exception:
                                response.append("Repository {0} not found".format(
                                    virtual_params.get("key")))

            module.exit_json(changed=changed, msg=response)
        except Exception, e:
            module.fail_json(msg=e)

    else:
        module.fail_json(msg="Invalid action {0}".format(action))


from ansible.module_utils.basic import AnsibleModule
if __name__ == "__main__":
    main()
