# ampuole

Create OpenStack config drive ISOs for injecting into virtual machines.

Possibly useful for people who want to use [bhyve](http://bhyve.org/)
with [cloud-init](http://cloudinit.readthedocs.org/).  May find uses
with other hypervisors.

## Requirements

Python 2.7 plus:
* Jinja2
* YAML
  
``mkisofs`` from [cdrtools](http://sourceforge.net/projects/cdrtools/)

An understanding of the [OpenStack config drive format](http://docs.openstack.org/user-guide/cli_config_drive.html).

An understanding of [cloud-init cloud config data](http://cloudinit.readthedocs.org/en/latest/topcs/format.html#cloud-config-data) expressed as [YAML](http://yaml.org/).

An understanding of [Jinja2 templates](http://jinja.pocoo.org/docs/dev/templates/).


## Basic Usage

Create a work directory for yourself, we'll call it ``$workdir``.

Choose the name which your virtual machine will call itself.  Note
that this may be very different from any name it may get in DNS.
We'll call it ``$guestname``.

Create directory named ``$workdir/inject``.  Populate it as if from
the root of your yet-to-be-provisioned virtual machine.
e.g. ``$workdir/inject/foo/bar/baz`` will eventually be copied to
``/foo/bar/baz`` on your virtual machine.

Create a subdirectory named ``$workdir/ssh``.  Populate it with SSH
**public** key files.  (Not private!  Public!)  These key files will
be applied to the administrator's account.  (The account name may vary
depending on the specific operating system of your virtual machine.)

Create a file named ``$workdir/user_data.jinja`` that is a mixture of
Jinja and YAML.  When rendered it should produce cloud-init config
data.

Finally run this program to generate your config drive ISO image.

    $ cd $workdir
    $ ampuole.py $guestname

If everything goes well, ``$workdir/configdrive.iso`` will be created.

Make sure that the virtual machine image you use has cloud-init
installed.  Most images that can be downloaded from
[OpenStack](http://docs.openstack.org/image-guide/obtain-images.html)
come with it already.

Attach the config drive to your virtual machine as the first CD-ROM
device.  When it boots up it should copy the injected files into
place, add the SSH public keys to the administrator's account, and do
anything else specified in the user data YAML file.

## Advanced Usage

```
usage: ampuole.py [-h] [-i INJECT_DIRECTORY] [-o OUTPUT]
                  [-s SSH_KEY_DIRECTORY] [-u USER_DATA_TEMPLATE]
                  guestname

positional arguments:
  guestname             Hostname of guest machine

optional arguments:
  -h, --help            show this help message and exit
  -i INJECT_DIRECTORY, --inject-directory INJECT_DIRECTORY
                        Directory of files to inject into config drive
  -o OUTPUT, --output OUTPUT
                        Output ISO file name
  -s SSH_KEY_DIRECTORY, --ssh-key-directory SSH_KEY_DIRECTORY
                        Directory of SSH public key files for administrator
                        account
  -u USER_DATA_TEMPLATE, --user-data-template USER_DATA_TEMPLATE
```

## Warnings

### About This Software

Will not work with Python 3.

### About Related Software

Not all features of cloud-init are supported on all operating systems.
Be prepared to experiment a bit.

## Motivation

Get a small farm of virtual machines going quickly inside a
workstation.  Don't pay public cloud providers for the privilege of
having to figure out their APIs.  Move faster than the corporate IT
department when you need machines for research and experimentation.
Don't waste memory on management interfaces and APIs.
