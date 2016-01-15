#!/usr/bin/env python
# -*- python -*-

import argparse
import jinja2
import json
import logging
import os
import subprocess
import sys
import tempfile
import uuid
import yaml

logging.basicConfig(level=logging.DEBUG)

USER_DATA_JINJA = """
# Default user data YAML file does nothing
"""

class Ampuole:
    """
    Assemble an OpenStack config drive ISO image.
    """
    def __init__(self, args):
        self.guestname = args.guestname
        self.inject = args.inject_directory
        self.ssh_key_directory = args.ssh_key_directory
        self.output_iso = args.output
        self.user_data_template = args.user_data_template
        _cwd = os.getcwd()
        _ldr = jinja2.FileSystemLoader(_cwd)
        self._j2 = jinja2.Environment(loader=_ldr)
        self._cloudconfig = None
        self._uuid = uuid.uuid4()
        self._inject = list()
        self._mdfile = None
        self._udfile = None
        self._ssh_keys = list()
        self.values = {
            'guestname': self.guestname,
            'uuid': self._uuid,
            'sshkeys': self._ssh_keys,
            'inject': self._inject,
        }

    def explore_user_data(self):
        """
        Render the user data template and see if it is valid YAML.
        """
        template = self._j2.get_template(self.user_data_template)
        rawyaml = template.render(self.values)
        logging.debug(rawyaml)
        self._cloudconfig = yaml.load(rawyaml)

    def gather_ssh_keys(self):
        """
        Walk the indicated directory, assume all files in it (recursively)
        are SSH public keys.  Make available to both metadata and
        user data.

        """
        for dirpath, dirnames, filenames in os.walk(self.ssh_key_directory):
            for f in filenames:
                try:
                    kf = os.path.join(dirpath, f)
                    h = open(kf)
                    for l in h.readlines():
                        k = l.strip()
                        self._ssh_keys.append(k)
                    h.close()
                except IOError:
                    pass
        try:
            for k in self._cloudconfig['ssh_authorized_keys']:
                self._ssh_keys.append(k)
        except KeyError:
            pass
        except TypeError:
            pass

    def gather_injections(self):
        """
        Walk a directory structure and collect information needed to
        inject those files in the requested place on the config drive
        (and eventually to the running guest).

        """
        j = 0
        for dirpath, dirnames, filenames in os.walk(self.inject):
            for i in filenames:
                seq = '{:04d}'.format(j)
                local = os.path.join(dirpath, i)
                expanded = local.split(os.path.sep)[1:]
                remote = os.path.join(*expanded)
                mdpath = os.path.join('content', seq)
                isopath = os.path.join('openstack', mdpath)
                self._inject.append({
                    'local': local,
                    'remote': os.path.sep + remote,
                    'mdpath': os.path.sep + mdpath,
                    'isopath': isopath,
                })
                j = j + 1
        self.values['inject'] = self._inject

    def rewrite_cloudconfig(self):
        """
        Add SSH authorized keys to user data, mostly as insurance in case
        metadata doesn't observe them.

        """
        try:
            self._cloudconfig['ssh_authorized_keys'] = self._ssh_keys
        except TypeError:
            pass
        self.udfile = tempfile.NamedTemporaryFile(delete=False)
        print >>self.udfile, '#cloud-config'
        yaml.safe_dump(self._cloudconfig, stream=self.udfile)
        self.udfile.close()

    def write_metadata(self):
        """
        Create the metadata structure and render it out as JSON.
        """
        metadata = dict()
        if len(self._ssh_keys) > 0:
            metadata['public_keys'] = dict()
            i = 0
            for k in self._ssh_keys:
                metadata['public_keys'][str(i)] = k
                i = i + 1
        if len(self._inject) > 0:
            metadata['files'] = list()
            for f in self._inject:
                metadata['files'].append({
                    'content_path': f['mdpath'],
                    'path': f['remote'],
                })
        metadata['hostname'] = self.guestname
        metadata['name'] = self.guestname
        metadata['uuid'] = str(self._uuid)
        self.mdfile = tempfile.NamedTemporaryFile(delete=False)
        pretty = json.dumps(metadata, indent=2, separators=(',',': '))
        logging.debug(pretty)
        print >>self.mdfile, pretty
        self.mdfile.close()

    def make_configdrive(self):
        """
        Use the assembled data to create the ISO image.
        """
        prefix = os.path.join('openstack', 'latest')
        mdin = os.path.join(prefix, 'meta_data.json')
        udin = os.path.join(prefix, 'user_data')
        metadata = '{}={}'.format(mdin, self.mdfile.name)
        userdata = '{}={}'.format(udin, self.udfile.name)
        cmd = [
            'mkisofs',
            '-J', '-r', '-R',
            '-o', self.output_iso,
            '-graft-points',
            metadata,
            userdata,
        ]
        for i in self._inject:
            logging.debug(i)
            graft = '{}={}'.format(i['isopath'], i['local']))
            cmd.append(graft)
        logging.debug(cmd)
        subprocess.check_call(cmd)
        os.remove(self.mdfile.name)
        os.remove(self.udfile.name)

    def run(self):
        self.explore_user_data()
        self.gather_ssh_keys()
        self.gather_injections()
        self.rewrite_cloudconfig()
        self.write_metadata()
        self.make_configdrive()
        
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inject-directory', nargs=2, default='inject', help="Directory of files to inject into config drive")
    parser.add_argument('-o', '--output', default='configdrive.iso', help="Outpuit ISO file name")
    parser.add_argument('-s', '--ssh-key-directory', default='ssh', help="Directory of SSH public key files for administrator account")
    parser.add_argument('-u', '--user-data-template', default='user_data.jinja')
    parser.add_argument('guestname', default=None, help="Hostname of guest machine")
    args = parser.parse_args()
    ampuole = Ampuole(args)
    return ampuole.run()

if __name__ == '__main__':
    sys.exit(main())
