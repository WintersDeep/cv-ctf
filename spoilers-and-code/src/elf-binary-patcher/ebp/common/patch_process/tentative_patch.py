## Because sometimes we don't know where we are going.
#  Allows changes to the patch manifest to be "rolled back". Can extend this to the ELF bytes if we really need to.
class TentativePatch(object):

    def __init__(self, elf):
        self.elf = elf
        self.manifest = elf.manifest_snapshot()
        self.changes_confirmed = False

    def confirm(self):
        self.changes_confirmed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.changes_confirmed:
            self.elf.restore_manifest(self.manifest)