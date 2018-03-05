
import os
import os.path as osp
from sublime_plugin import WindowCommand


def package_installed(name):
    pf = os.extsep.join([name,'sublime-package'])
    pfp = osp.join(sublime.installed_packages_path(),pf)
    return osp.exists(pfp)


class SmartInstallCommand(WindowCommand):
	def run(self, name):
		self.window.run_command('advanced_install_package',args={"packages":name})

	def description(self, name):
		return name.split(',')[0]

	def is_enabled(self, name):
		return package_installed(name.split(',')[0])
